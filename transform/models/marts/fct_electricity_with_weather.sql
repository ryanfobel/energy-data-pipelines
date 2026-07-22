{{ config(materialized='table') }}

/*
Fact table: Electricity consumption enriched with weather and air quality data.

Joins hourly electricity consumption with weather and air quality data from Open-Meteo.

Features:
  - Hourly temperature correlation
  - Heating/Cooling degree days (base 18°C)
  - Humidity and precipitation context
  - Air quality metrics (PM2.5, UV, aerosol optical depth)
  - Weather-normalized metrics

Use cases:
  - Analyze temperature vs consumption
  - Calculate weather-normalized consumption
  - Identify HVAC-related usage patterns
  - Solar panel soiling impact from aerosol_optical_depth
  - HVAC load during poor air quality (windows closed)
  - UV index correlation with cooling demand
  - Seasonal analysis
*/

with electricity as (
    select * from {{ ref('fct_electricity_consumption') }}
),

weather as (
    select * from {{ ref('stg_weather_hourly') }}
),

air_quality as (
    select * from {{ ref('stg_air_quality_hourly') }}
),

-- Join electricity with weather and air quality by hour
-- Note: Weather and air quality data are timezone-aware, match timestamps
joined as (
    select
        e.*,
        w.location_name,
        w.temperature_c,
        w.humidity_pct,
        w.precipitation_mm,
        w.windspeed_kmh,
        w.temperature_category,
        -- Cloud cover
        w.cloud_cover_pct,
        w.cloud_cover_low_pct,
        w.cloud_cover_mid_pct,
        w.cloud_cover_high_pct,
        -- Solar radiation
        w.ghi_wm2,
        w.dni_wm2,
        w.dhi_wm2,
        w.direct_horizontal_wm2,
        w.sunshine_duration_s,
        -- Air quality - particulate matter
        aq.pm2_5,
        aq.pm10,
        aq.dust,
        -- Air quality - pollutants
        aq.ozone,
        aq.nitrogen_dioxide,
        aq.sulphur_dioxide,
        aq.carbon_monoxide,
        -- Air quality - UV and aerosols
        aq.uv_index,
        aq.uv_index_clear_sky,
        aq.aerosol_optical_depth,
        -- Air quality indices and categories
        aq.european_aqi,
        aq.pm2_5_category,
        aq.aqi_category,
        aq.uv_category,
        aq.is_high_pollution,
        aq.is_high_soiling_risk
    from electricity e
    left join weather w
        on DATE_TRUNC('hour', e.timestamp) = DATE_TRUNC('hour', w.ts)
    left join air_quality aq
        on DATE_TRUNC('hour', e.timestamp) = DATE_TRUNC('hour', aq.ts)
        and w.location_name = aq.location_name
),

-- Calculate degree days at hourly level
-- Then aggregate to daily for standard HDD/CDD metrics
with_degree_hours as (
    select
        *,
        -- Heating degree hours (base 18°C)
        CASE
            WHEN temperature_c < 18 THEN 18 - temperature_c
            ELSE 0
        END as hdh,  -- Heating Degree Hours

        -- Cooling degree hours (base 18°C)
        CASE
            WHEN temperature_c > 18 THEN temperature_c - 18
            ELSE 0
        END as cdh,  -- Cooling Degree Hours

        -- Flag HVAC season
        CASE
            WHEN temperature_c < 18 THEN 'heating'
            WHEN temperature_c > 22 THEN 'cooling'
            ELSE 'shoulder'
        END as hvac_season
    from joined
)

select
    -- Electricity fields
    source,
    home_id,
    meter_id_hash,
    device_id,
    timestamp,
    kwh,
    cost,
    quality,
    estimated,
    tou_period,
    co2_g_per_kwh,
    rate_cents_per_kwh,
    year,
    month,
    day,
    hour,
    day_of_week,

    -- Weather fields
    location_name,
    temperature_c,
    humidity_pct,
    precipitation_mm,
    windspeed_kmh,
    temperature_category,
    hvac_season,

    -- Cloud cover (%)
    cloud_cover_pct,
    cloud_cover_low_pct,
    cloud_cover_mid_pct,
    cloud_cover_high_pct,

    -- Solar radiation (W/m²) and sunshine (seconds)
    ghi_wm2,                    -- Global Horizontal Irradiance
    dni_wm2,                    -- Direct Normal Irradiance
    dhi_wm2,                    -- Diffuse Horizontal Irradiance
    direct_horizontal_wm2,      -- Direct radiation on horizontal plane
    sunshine_duration_s,        -- Sunshine seconds in preceding hour

    -- Degree hours (for aggregation to degree days)
    hdh,
    cdh,

    -- Air quality fields
    pm2_5,                      -- Primary health metric
    pm10,                       -- Health and HVAC filter impact
    dust,                       -- Solar panel soiling indicator
    uv_index,                   -- UV radiation and cooling correlation
    aerosol_optical_depth,      -- Solar panel performance impact
    european_aqi,               -- Overall air quality index
    pm2_5_category,             -- Air quality category
    aqi_category,               -- European AQI category
    uv_category,                -- UV index category
    is_high_pollution,          -- High pollution flag
    is_high_soiling_risk,       -- Solar panel soiling risk

    -- Convenience flags
    CASE WHEN temperature_c IS NULL THEN true ELSE false END as missing_weather_data,
    CASE WHEN pm2_5 IS NULL THEN true ELSE false END as missing_air_quality_data

from with_degree_hours
