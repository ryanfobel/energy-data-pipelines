{{ config(materialized='view') }}

/*
Unified view: All utility consumption (electricity, gas, water).

Useful for:
  - Overview dashboards
  - Total household utility costs
  - Cross-commodity analysis

Note: Different commodities have different frequencies:
  - Electricity: hourly
  - Gas: monthly
  - Water: daily or monthly
*/

with electricity as (
    select
        home_id,
        timestamp,
        'electricity' as commodity,
        kwh as quantity,
        'kWh' as unit,
        cost,
        estimated,
        year,
        month
    from {{ ref('fct_electricity_consumption') }}
    where source = 'green_button'  -- Only utility data, not real-time monitoring
),

gas as (
    select
        home_id,
        timestamp,
        'natural_gas' as commodity,
        m3 as quantity,
        'm³' as unit,
        cost,
        estimated,
        year,
        month
    from {{ ref('fct_gas_consumption') }}
),

water as (
    select
        home_id,
        timestamp,
        'water' as commodity,
        m3 as quantity,
        'm³' as unit,
        cost,
        estimated,
        year,
        month
    from {{ ref('fct_water_consumption') }}
),

-- Union all commodities
all_utilities as (
    select * from electricity
    union all
    select * from gas
    union all
    select * from water
)

select
    home_id,
    timestamp,
    commodity,
    quantity,
    unit,
    cost,
    estimated,
    year,
    month,
    -- Useful aggregations
    date_trunc('month', timestamp) as month_start,
    date_trunc('year', timestamp) as year_start
from all_utilities
order by home_id, timestamp, commodity
