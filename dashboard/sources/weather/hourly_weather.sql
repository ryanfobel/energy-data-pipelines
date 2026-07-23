SELECT
    timestamp,
    temperature_c,
    humidity_pct,
    precipitation_mm,
    windspeed_kmh,
    cloud_cover_pct,
    ghi_wm2 as solar_radiation_wm2,
    sunshine_duration_s
FROM raw.weather_hourly
WHERE location_name = 'kitchener'
ORDER BY timestamp
