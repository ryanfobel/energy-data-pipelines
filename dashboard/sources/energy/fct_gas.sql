SELECT
    timestamp,
    m3 as cubic_meters,
    cost,
    quality,
    home_id,
    source,
    meter_id_hash,
    estimated,
    avg_outdoor_temp_c,
    heating_degree_days,
    rate_cents_per_m3,
    year,
    month,
    day
FROM main_marts.fct_gas_consumption
ORDER BY timestamp
