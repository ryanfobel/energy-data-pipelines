-- Attach weather database and join with electricity data
ATTACH '../weather.duckdb' AS weather_db (READ_ONLY);

SELECT
  e.timestamp,
  e.kwh,
  e.tou_bucket,
  e.quality_code,
  e.meter_id,
  e.home_id,
  w.temperature_c,
  w.humidity_pct,
  w.precipitation_mm,
  w.windspeed_kmh,
  w.cloud_cover_pct,
  DATE_PART('hour', e.timestamp) as hour_of_day,
  DATE_PART('dow', e.timestamp) as day_of_week
FROM green_button_interval_readings e
LEFT JOIN weather_db.raw.weather_hourly w
  ON DATE_TRUNC('hour', e.timestamp) = DATE_TRUNC('hour', w.timestamp)
  AND w.location_name = 'kitchener'
WHERE e.commodity = 'CommodityKindValue.VALUE_1'  -- Electricity
  AND e.home_id = 'ryan-home-001'
ORDER BY e.timestamp
