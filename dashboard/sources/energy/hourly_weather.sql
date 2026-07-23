SELECT
    ts as timestamp,
    location_name,
    temperature_c,
    humidity_pct,
    precipitation_mm,
    windspeed_kmh,
    cloud_cover_pct,
    cloud_cover_low_pct,
    cloud_cover_mid_pct,
    cloud_cover_high_pct,
    ghi_wm2,
    dni_wm2,
    dhi_wm2,
    sunshine_duration_s,
    temperature_category,
    year,
    month,
    day,
    hour_of_day,
    day_of_week
FROM main_staging.stg_weather_hourly
ORDER BY ts
