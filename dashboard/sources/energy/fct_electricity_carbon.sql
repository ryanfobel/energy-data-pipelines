-- Carbon data not yet available - need to run dbt transformations
-- For now, just return electricity data
SELECT
    timestamp,
    kwh,
    cost,
    tou_bucket,
    quality_code,
    meter_id,
    home_id,
    NULL as kg_co2e,
    NULL as grid_clean_pct
FROM raw.green_button_interval_readings
WHERE commodity = 'CommodityKindValue.VALUE_1'  -- Electricity
ORDER BY timestamp
