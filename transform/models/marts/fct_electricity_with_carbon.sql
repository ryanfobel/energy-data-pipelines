{{
    config(
        materialized='table',
        pre_hook="{{ attach_ontario_grid() }}"
    )
}}

/*
Electricity consumption enriched with Ontario grid carbon intensity.

Joins hourly electricity consumption with IESO/gridwatch carbon intensity data
to calculate emissions for each reading.
*/

with electricity as (
    select * from {{ ref('fct_electricity_consumption') }}
),

ontario_grid as (
    select
        hour as timestamp_hour,
        co2e_intensity_gco2_per_kwh,
        clean_pct,
        total_mw,
        nuclear_mw,
        gas_mw,
        hydro_mw,
        wind_mw,
        solar_mw,
        biofuel_mw,
        has_ieso,
        has_gridwatch
    from ontario_grid.main.fct_co2_intensity
    where co2e_intensity_gco2_per_kwh is not null
),

joined as (
    select
        -- Original electricity fields
        e.source,
        e.home_id,
        e.meter_id_hash,
        e.device_id,
        e.timestamp,
        e.kwh,
        e.cost,
        e.quality,
        e.estimated,
        e.tou_period,
        e.year,
        e.month,
        e.day,
        e.hour,
        e.day_of_week,

        -- Grid carbon intensity
        g.co2e_intensity_gco2_per_kwh,
        g.clean_pct as grid_clean_pct,

        -- Calculate emissions
        e.kwh * g.co2e_intensity_gco2_per_kwh / 1000 as kg_co2e,
        e.kwh * g.co2e_intensity_gco2_per_kwh as g_co2e,

        -- Grid generation mix at time of consumption
        g.total_mw as grid_total_mw,
        g.nuclear_mw as grid_nuclear_mw,
        g.gas_mw as grid_gas_mw,
        g.hydro_mw as grid_hydro_mw,
        g.wind_mw as grid_wind_mw,
        g.solar_mw as grid_solar_mw,
        g.biofuel_mw as grid_biofuel_mw,

        -- Data quality flags
        g.has_ieso as grid_has_ieso_data,
        g.has_gridwatch as grid_has_gridwatch_data

    from electricity e
    left join ontario_grid g
        on date_trunc('hour', e.timestamp) = g.timestamp_hour
)

select * from joined
