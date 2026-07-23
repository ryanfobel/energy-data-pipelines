SELECT
    timestamp,
    kwh,
    cost,
    tou_period,
    quality,
    meter_id_hash,
    home_id,
    source,
    estimated,
    co2_g_per_kwh,
    rate_cents_per_kwh,
    year,
    month,
    day,
    hour,
    day_of_week
FROM main_marts.fct_electricity_consumption
ORDER BY timestamp
