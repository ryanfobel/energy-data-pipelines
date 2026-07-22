{{ config(materialized='view') }}

/*
Dimension table for homes.

For MVP, this is a simple placeholder that generates home metadata
from the Green Button data itself. In production, this would come
from a homes registry (CSV seed or external table).
*/

with home_ids as (
    select distinct
        home_id,
        meter_id
    from {{ source('raw', 'green_button_interval_readings') }}
),

homes as (
    select
        home_id,
        meter_id,
        -- Generate anonymized meter ID hash (placeholder - should use HMAC in production)
        md5(meter_id) as meter_id_hash,
        -- Metadata (would come from registry in production)
        null as address_anonymized,
        null as vintage,
        null as sqft,
        null as heat_type,
        current_timestamp as created_at
    from home_ids
)

select * from homes
