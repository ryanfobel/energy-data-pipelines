{{ config(materialized='view') }}

/*
Staging view for hourly air quality data from Open-Meteo.

Transforms:
  - Parse timestamp to date components
  - Categorize air quality based on PM2.5 and European AQI
  - Add quality flags
  - Calculate air quality categories

Data source: Open-Meteo Air Quality API
API: https://air-quality-api.open-meteo.com/v1/air-quality

Air Quality Categories (based on PM2.5 µg/m³):
  - Good: 0-12
  - Moderate: 12-35
  - Unhealthy for sensitive groups: 35-55
  - Unhealthy: 55-150
  - Very unhealthy: 150+

European AQI Categories:
  - Good: 0-20
  - Fair: 20-40
  - Moderate: 40-60
  - Poor: 60-80
  - Very poor: 80-100
  - Extremely poor: 100+
*/

with source as (
    -- Return empty result set with correct schema until air quality data is loaded
    select
        null::varchar as location_name,
        null::double as latitude,
        null::double as longitude,
        null::varchar as timezone,
        null::timestamp as timestamp,
        null::double as pm2_5,
        null::double as pm10,
        null::double as dust,
        null::double as ozone,
        null::double as nitrogen_dioxide,
        null::double as sulphur_dioxide,
        null::double as carbon_monoxide,
        null::double as uv_index,
        null::double as uv_index_clear_sky,
        null::double as aerosol_optical_depth,
        null::double as european_aqi,
        null::double as european_aqi_pm2_5,
        null::double as european_aqi_pm10,
        null::double as european_aqi_nitrogen_dioxide,
        null::double as european_aqi_ozone,
        null::double as european_aqi_sulphur_dioxide
    where false
),

transformed as (
    select
        -- Identifiers
        location_name,
        latitude,
        longitude,
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

        -- Particulate matter (µg/m³)
        pm10,
        pm2_5,
        dust,

        -- Pollutants
        ozone,
        nitrogen_dioxide,
        sulphur_dioxide,
        carbon_monoxide,

        -- UV and aerosols
        uv_index,
        uv_index_clear_sky,
        aerosol_optical_depth,

        -- Air quality indices
        european_aqi,
        european_aqi_pm2_5,
        european_aqi_pm10,
        european_aqi_nitrogen_dioxide,
        european_aqi_ozone,
        european_aqi_sulphur_dioxide,

        -- Air quality category based on PM2.5
        CASE
            WHEN pm2_5 IS NULL THEN 'unknown'
            WHEN pm2_5 < 12 THEN 'good'
            WHEN pm2_5 < 35 THEN 'moderate'
            WHEN pm2_5 < 55 THEN 'unhealthy_sensitive'
            WHEN pm2_5 < 150 THEN 'unhealthy'
            ELSE 'very_unhealthy'
        END as pm2_5_category,

        -- European AQI category
        CASE
            WHEN european_aqi IS NULL THEN 'unknown'
            WHEN european_aqi <= 20 THEN 'good'
            WHEN european_aqi <= 40 THEN 'fair'
            WHEN european_aqi <= 60 THEN 'moderate'
            WHEN european_aqi <= 80 THEN 'poor'
            WHEN european_aqi <= 100 THEN 'very_poor'
            ELSE 'extremely_poor'
        END as aqi_category,

        -- UV index category
        CASE
            WHEN uv_index IS NULL THEN 'unknown'
            WHEN uv_index < 3 THEN 'low'
            WHEN uv_index < 6 THEN 'moderate'
            WHEN uv_index < 8 THEN 'high'
            WHEN uv_index < 11 THEN 'very_high'
            ELSE 'extreme'
        END as uv_category,

        -- Quality flags
        CASE
            WHEN pm2_5 IS NULL AND pm10 IS NULL THEN 'missing_pm'
            WHEN pm2_5 < 0 OR pm10 < 0 THEN 'invalid_pm'
            WHEN european_aqi < 0 THEN 'invalid_aqi'
            ELSE 'valid'
        END as quality,

        -- Flag for high pollution (PM2.5 > 35 or AQI > 60)
        CASE
            WHEN pm2_5 > 35 OR european_aqi > 60 THEN true
            ELSE false
        END as is_high_pollution,

        -- Flag for solar panel soiling concern (high aerosol or dust)
        CASE
            WHEN aerosol_optical_depth > 0.3 OR dust > 20 THEN true
            ELSE false
        END as is_high_soiling_risk

    from source
)

select * from transformed
where quality IN ('valid', 'missing_pm')  -- Allow some missing PM data
