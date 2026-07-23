SELECT
    timestamp,
    kwh,
    cost,
    tou_bucket,
    quality_code,
    meter_id,
    home_id
FROM raw.green_button_interval_readings
WHERE commodity = 'CommodityKindValue.VALUE_1'  -- Electricity
ORDER BY timestamp
