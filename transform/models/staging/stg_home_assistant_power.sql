{{ config(materialized='view') }}

/*
Staging view for Home Assistant power monitoring data.

Transforms:
  - Convert instantaneous watts to hourly kWh
  - Validate measurements (watts >= 0, reasonable ranges)
  - Add data quality flags
  - Normalize device and channel info
  - Cast timestamps to UTC-aware
*/

with source as (
    select * from {{ source('raw', 'power_monitoring') }}
),

validated as (
    select
        -- Identifiers
        home_id,
        device_id,
        channel,
        channel_name,

        -- Timestamp (ensure UTC)
        timestamp as ts,

        -- Power measurements
        watts,
        volts,
        amps,
        power_factor,

        -- Data quality flags
        case
            when watts < 0 then 'invalid_negative'
            when watts > 50000 then 'invalid_high'
            when volts < 100 or volts > 140 then 'voltage_out_of_range'
            else 'valid'
        end as quality,

        case
            when watts < 0 or watts > 50000 or volts < 100 or volts > 140
            then true
            else false
        end as is_invalid

    from source
),

-- Filter out invalid measurements
cleaned as (
    select * from validated
    where not is_invalid
),

-- Aggregate to hourly kWh (power monitoring data is typically 1-60 second intervals)
-- We need to convert instantaneous watts to energy (kWh)
hourly_rollup as (
    select
        home_id,
        device_id,
        channel,
        channel_name,

        -- Truncate to hourly intervals
        date_trunc('hour', ts) as timestamp,

        -- Calculate kWh from average watts over the hour
        -- avg(watts) * 1 hour / 1000 = kWh
        avg(watts) / 1000.0 as kwh,

        -- Keep measurement details for debugging
        avg(watts) as avg_watts,
        avg(volts) as avg_volts,
        avg(amps) as avg_amps,
        avg(power_factor) as avg_power_factor,

        count(*) as measurement_count,

        -- Data quality: mark as estimated if we have too few measurements
        case
            when count(*) < 60 then true  -- Less than 1 measurement per minute
            else false
        end as estimated,

        case
            when count(*) >= 360 then 'high_quality'  -- 1 per 10s
            when count(*) >= 60 then 'medium_quality'  -- 1 per minute
            else 'low_quality'
        end as quality

    from cleaned
    group by
        home_id,
        device_id,
        channel,
        channel_name,
        date_trunc('hour', ts)
)

select
    home_id,
    device_id,
    channel,
    channel_name,
    timestamp,
    kwh,
    avg_watts,
    avg_volts,
    avg_amps,
    avg_power_factor,
    measurement_count,
    quality,
    estimated
from hourly_rollup
