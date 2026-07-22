{{ config(materialized='table') }}

/*
Fact table: Electricity consumption from all sources.

Combines:
  - Green Button hourly interval data
  - (Future: Power monitoring real-time data)
  - (Future: Manual readings)

Enriched with:
  - Home metadata (from dim_homes)
  - TOU period classification
  - Grid carbon intensity (when available)
  - Rate information (when available)
*/

with green_button as (
    select
        'green_button' as source,
        home_id,
        usage_point_idx as device_id,  -- Use usage_point as device identifier
        ts as timestamp,
        kwh,
        cost_cents as cost,
        quality,
        estimated,
        tou_period,
        meter_id
    from {{ ref('stg_green_button') }}
),

power_monitoring as (
    select
        'power_monitoring' as source,
        home_id,
        device_id || '_ch' || channel::text as device_id,  -- Combine device and channel
        timestamp,
        kwh,
        null::double as cost,  -- Cost not available from real-time monitoring
        quality,
        estimated,
        null::varchar as tou_period,  -- TOU classification would need to be joined
        null::varchar as meter_id  -- Not applicable for power monitoring
    from {{ ref('stg_home_assistant_power') }}
),

-- Union all sources
all_sources as (
    select * from green_button
    union all
    select * from power_monitoring
),

-- Join with home dimension
with_home_metadata as (
    select
        c.source,
        c.home_id,
        h.meter_id_hash,
        c.device_id,
        c.timestamp,
        c.kwh,
        c.cost,
        c.quality,
        c.estimated,
        c.tou_period
    from all_sources c
    left join {{ ref('stg_dim_homes') }} h
        on c.home_id = h.home_id
),

-- Add grid intensity (when available)
-- TODO: Join with grid_intensity table from ontario-grid-pipelines
enriched as (
    select
        *,
        null::double as co2_g_per_kwh,  -- Placeholder
        null::double as rate_cents_per_kwh  -- Placeholder
    from with_home_metadata
)

select
    source,
    home_id,
    meter_id_hash,
    device_id,
    timestamp,
    kwh,
    cost,
    quality,
    estimated,
    tou_period,
    co2_g_per_kwh,
    rate_cents_per_kwh,
    -- Calculated fields
    extract(year from timestamp) as year,
    extract(month from timestamp) as month,
    extract(day from timestamp) as day,
    extract(hour from timestamp) as hour,
    extract(dow from timestamp) as day_of_week  -- 0=Sunday, 6=Saturday
from enriched
