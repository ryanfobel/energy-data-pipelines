-- Get hourly weather data from electricity_with_weather mart
-- This avoids needing to attach the weather database in Evidence
SELECT DISTINCT
    timestamp,
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
    hour,
    day_of_week
FROM main_marts.fct_electricity_with_weather
WHERE temperature_c IS NOT NULL
ORDER BY timestamp
