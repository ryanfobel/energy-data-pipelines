SELECT
    timestamp,
    kwh as cubic_meters,
    cost,
    quality_code,
    home_id
FROM raw.green_button_interval_readings
WHERE commodity = 'CommodityKindValue.VALUE_9'  -- Water
ORDER BY timestamp
