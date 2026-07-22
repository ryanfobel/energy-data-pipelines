{{ config(materialized='table') }}

/*
Fact table: Natural gas consumption from Green Button data.

Source:
  - Green Button monthly gas readings (from utilities like Enbridge)

Enriched with:
  - Home metadata (from dim_homes)
  - Temperature data (for heating degree days analysis)
  - Rate information (when available)

Note: Gas data is typically monthly, not hourly like electricity.
*/

with green_button_gas as (
    select
        'green_button' as source,
        home_id,
        usage_point_idx as device_id,  -- Usage point identifier
        ts as timestamp,
        m3,  -- Cubic meters of natural gas
        cost_cents as cost,
        quality,
        estimated,
        meter_id
    from {{ ref('stg_green_button_gas') }}
),

-- Join with home dimension
with_home_metadata as (
    select
        g.source,
        g.home_id,
        h.meter_id_hash,
        g.device_id,
        g.timestamp,
        g.m3,
        g.cost,
        g.quality,
        g.estimated
    from green_button_gas g
    left join {{ ref('stg_dim_homes') }} h
        on g.home_id = h.home_id
),

-- Add enrichment placeholders
enriched as (
    select
        *,
        null::double as avg_outdoor_temp_c,  -- Placeholder for temperature data
        null::double as heating_degree_days,  -- Placeholder for HDD
        null::double as rate_cents_per_m3  -- Placeholder for gas rates
    from with_home_metadata
)

select
    source,
    home_id,
    meter_id_hash,
    device_id,
    timestamp,
    m3,
    cost,
    quality,
    estimated,
    avg_outdoor_temp_c,
    heating_degree_days,
    rate_cents_per_m3,
    -- Calculated fields
    extract(year from timestamp) as year,
    extract(month from timestamp) as month,
    extract(day from timestamp) as day
from enriched
