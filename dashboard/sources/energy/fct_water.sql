SELECT
    timestamp,
    m3 as cubic_meters,
    cost,
    quality,
    home_id,
    source,
    meter_id_hash,
    estimated,
    gallons,
    liters,
    rate_cents_per_m3,
    rate_cents_per_gal,
    year,
    month,
    day
FROM main_marts.fct_water_consumption
ORDER BY timestamp
