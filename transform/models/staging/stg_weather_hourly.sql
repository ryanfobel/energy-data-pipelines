{{ config(materialized='view') }}

/*
Staging view for hourly weather data from Open-Meteo.

Transforms:
  - Parse timestamp to date components
  - Calculate daily average temperature for degree days
  - Add quality flags
  - Normalize units

Data source: Open-Meteo Historical Weather API
API: https://archive-api.open-meteo.com/v1/archive
*/

with source as (
    select * from weather.raw.weather_hourly
),

transformed as (
    select
        -- Identifiers
        location_name,
        latitude,
        longitude,
        elevation_m,
        timezone,

        -- Timestamp fields
        timestamp as ts,
        DATE_TRUNC('hour', timestamp) as hour,
        DATE_TRUNC('day', timestamp) as date,
        EXTRACT(year FROM timestamp) as year,
        EXTRACT(month FROM timestamp) as month,
        EXTRACT(day FROM timestamp) as day,
        EXTRACT(hour FROM timestamp) as hour_of_day,
        EXTRACT(dow FROM timestamp) as day_of_week,

        -- Weather measurements
        temperature_c,
        humidity_pct,
        precipitation_mm,
        windspeed_kmh,

        -- Cloud cover (%)
        cloud_cover_pct,
        cloud_cover_low_pct,
        cloud_cover_mid_pct,
        cloud_cover_high_pct,

        -- Solar radiation (W/m²)
        ghi_wm2,                    -- Global Horizontal Irradiance
        dni_wm2,                    -- Direct Normal Irradiance
        dhi_wm2,                    -- Diffuse Horizontal Irradiance
        direct_horizontal_wm2,      -- Direct radiation on horizontal plane
        sunshine_duration_s,        -- Sunshine seconds in preceding hour

        -- Derived fields
        CASE
            WHEN temperature_c IS NULL THEN 'missing'
            WHEN temperature_c < -50 OR temperature_c > 60 THEN 'out_of_range'
            ELSE 'valid'
        END as quality,

        -- Flag for reasonable temperature range (Southern Ontario)
        CASE
            WHEN temperature_c >= -40 AND temperature_c <= 40 THEN true
            ELSE false
        END as is_valid_temperature,

        -- Categorize temperature
        CASE
            WHEN temperature_c < -10 THEN 'very_cold'
            WHEN temperature_c < 0 THEN 'cold'
            WHEN temperature_c < 10 THEN 'cool'
            WHEN temperature_c < 20 THEN 'mild'
            WHEN temperature_c < 25 THEN 'warm'
            ELSE 'hot'
        END as temperature_category

    from source
)

select * from transformed
where quality = 'valid'
