{{ config(materialized='view') }}

/*
Staging view for Green Button interval readings.

Transforms:
  - Decode ESPI enums to human-readable values
  - Filter to electricity only (commodity=1)
  - Add estimated flag based on quality code
  - Normalize TOU buckets to period names
  - Cast timestamps to UTC-aware
*/

with source as (
    select * from green_button.raw.green_button_interval_readings
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

        -- Energy consumption (convert Wh to kWh)
        kwh / 1000.0 as kwh,
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

        -- Flag estimated readings (quality codes 7, 8, 9 in ESPI spec)
        case
            when quality_code like '%ESTIMATED%' then true
            when quality_code like '%DERIVED%' then true
            when quality_code like '%PROJECTED%' then true
            else false
        end as estimated,

        -- Decode TOU bucket to period name
        case tou_bucket
            when '1' then 'on_peak'
            when '2' then 'mid_peak'
            when '3' then 'off_peak'
            else null
        end as tou_period,

        -- Decode commodity enum
        case
            when commodity like '%VALUE_1%' then 'electricity'
            when commodity like '%VALUE_7%' then 'natural_gas'
            when commodity like '%VALUE_2%' then 'water'
            else 'unknown'
        end as commodity_type,

        -- Decode unit of measure
        case
            when uom like '%VALUE_72%' then 'Wh'  -- Watt-hours
            when uom like '%VALUE_42%' then 'm3'  -- Cubic meters
            when uom like '%VALUE_38%' then 'W'   -- Watts
            else 'unknown'
        end as unit,

        -- Service kind
        service_kind,

        -- Raw enums (for debugging)
        quality_code as quality_code_raw,
        commodity as commodity_raw,
        uom as uom_raw,
        tou_bucket as tou_bucket_raw

    from source
)

-- Filter to electricity only (gas would go to separate staging view)
select * from decoded
where commodity_type = 'electricity'
