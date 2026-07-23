SELECT
    timestamp,
    kwh as cubic_meters,
    cost,
    quality_code,
    home_id
FROM raw.green_button_interval_readings
WHERE commodity IN ('CommodityKindValue.VALUE_2', 'CommodityKindValue.VALUE_7')  -- Natural gas
ORDER BY timestamp
