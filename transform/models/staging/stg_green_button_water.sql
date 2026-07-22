{{ config(materialized='view') }}

/*
Staging view for Green Button water readings.

Transforms:
  - Decode ESPI enums to human-readable values
  - Filter to water only (commodity=2)
  - Convert to standard units (m³ or gallons depending on utility)
  - Add estimated flag based on quality code
  - Handle daily or monthly intervals (varies by utility)
*/

with source as (
    select * from {{ source('raw', 'green_button_interval_readings') }}
),

decoded as (
    select
        -- Identifiers
        home_id,
        usage_point_idx,
        meter_reading_idx,
        meter_id,

        -- Timestamp (ensure UTC)
        timestamp as ts,
        duration_seconds,

        -- Water consumption
        kwh as volume,  -- Field named 'kwh' in raw but contains volume for water
        raw_value,

        -- Cost
        cost as cost_cents,

        -- Decode quality code enum
        case
            when quality_code like '%VALIDATED%' then 'validated'
            when quality_code like '%ESTIMATED%' then 'estimated'
            when quality_code like '%DERIVED%' then 'derived'
            when quality_code like '%PROJECTED%' then 'projected'
            when quality_code like '%MANUAL%' then 'manual'
            else 'unknown'
        end as quality,

        -- Flag estimated readings
        case
            when quality_code like '%ESTIMATED%' then true
            when quality_code like '%DERIVED%' then true
            when quality_code like '%PROJECTED%' then true
            else false
        end as estimated,

        -- Decode commodity enum
        case
            when commodity like '%VALUE_1%' then 'electricity'
            when commodity like '%VALUE_7%' then 'natural_gas'
            when commodity like '%VALUE_2%' then 'water'
            else 'unknown'
        end as commodity_type,

        -- Decode unit of measure
        case
            when uom like '%VALUE_72%' then 'Wh'   -- Watt-hours (shouldn't appear for water)
            when uom like '%VALUE_42%' then 'm3'   -- Cubic meters
            when uom like '%VALUE_119%' then 'gal' -- Gallons (US)
            when uom like '%VALUE_38%' then 'W'    -- Watts (shouldn't appear for water)
            else 'unknown'
        end as unit,

        -- Service kind
        service_kind,

        -- Raw enums (for debugging)
        quality_code as quality_code_raw,
        commodity as commodity_raw,
        uom as uom_raw

    from source
)

-- Filter to water only
select * from decoded
where commodity_type = 'water'
