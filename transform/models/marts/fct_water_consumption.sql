{{ config(materialized='table') }}

/*
Fact table: Water consumption from Green Button data.

Source:
  - Green Button water readings (typically daily or monthly)

Enriched with:
  - Home metadata (from dim_homes)
  - Rate information (when available)

Note: Water data frequency varies by utility (daily, weekly, or monthly).
*/

with green_button_water as (
    select
        'green_button' as source,
        home_id,
        usage_point_idx as device_id,  -- Usage point identifier
        ts as timestamp,
        volume,  -- Cubic meters or gallons depending on utility
        unit,    -- 'm3' or 'gal'
        cost_cents as cost,
        quality,
        estimated,
        meter_id
    from {{ ref('stg_green_button_water') }}
),

-- Normalize to standard units (cubic meters)
normalized as (
    select
        source,
        home_id,
        device_id,
        timestamp,
        -- Convert gallons to m³ if needed (1 m³ = 264.172 gallons)
        case
            when unit = 'gal' then volume / 264.172
            else volume
        end as m3,
        volume as raw_volume,
        unit as raw_unit,
        cost,
        quality,
        estimated,
        meter_id
    from green_button_water
),

-- Join with home dimension
with_home_metadata as (
    select
        w.source,
        w.home_id,
        h.meter_id_hash,
        w.device_id,
        w.timestamp,
        w.m3,
        w.raw_volume,
        w.raw_unit,
        w.cost,
        w.quality,
        w.estimated
    from normalized w
    left join {{ ref('stg_dim_homes') }} h
        on w.home_id = h.home_id
),

-- Add enrichment placeholders
enriched as (
    select
        *,
        null::double as rate_cents_per_m3,  -- Placeholder for water rates
        null::double as rate_cents_per_gal  -- Placeholder for water rates (gallons)
    from with_home_metadata
)

select
    source,
    home_id,
    meter_id_hash,
    device_id,
    timestamp,
    m3,  -- Standardized to cubic meters
    raw_volume,  -- Original value from utility
    raw_unit,    -- Original unit (m3 or gal)
    cost,
    quality,
    estimated,
    rate_cents_per_m3,
    rate_cents_per_gal,
    -- Calculated fields
    extract(year from timestamp) as year,
    extract(month from timestamp) as month,
    extract(day from timestamp) as day,
    -- Useful conversions
    m3 * 264.172 as gallons,  -- For US users
    m3 * 1000 as liters        -- Alternative metric
from enriched
