#!/usr/bin/env -S pixi run python
"""Merge gas data from green_button.duckdb into main warehouse."""
import duckdb

def main():
    # Attach green_button.duckdb to the main warehouse
    conn = duckdb.connect('energy_warehouse.duckdb')

    # Attach the green_button database
    conn.execute("ATTACH IF NOT EXISTS 'green_button.duckdb' AS gb")

    # Create raw schema if it doesn't exist
    conn.execute('CREATE SCHEMA IF NOT EXISTS raw')

    # Insert new gas data (avoiding duplicates), adding NULL for cost column
    conn.execute('''
        INSERT INTO raw.green_button_interval_readings
        SELECT
            home_id, usage_point_idx, meter_reading_idx, meter_id,
            timestamp, duration_seconds, raw_value, kwh,
            NULL as cost,  -- Gas data doesn't have cost info
            quality_code, tou_bucket, commodity, uom, service_kind,
            _dlt_load_id, _dlt_id
        FROM gb.raw.green_button_interval_readings
        WHERE NOT EXISTS (
            SELECT 1 FROM raw.green_button_interval_readings AS existing
            WHERE existing.home_id = gb.raw.green_button_interval_readings.home_id
              AND existing.timestamp = gb.raw.green_button_interval_readings.timestamp
              AND existing.commodity = gb.raw.green_button_interval_readings.commodity
        )
    ''')

    # Verify
    result = conn.execute('SELECT COUNT(*) FROM raw.green_button_interval_readings').fetchone()
    print(f'✓ Total Green Button interval readings in warehouse: {result[0]}')

    # Show commodity breakdown
    result = conn.execute('''
        SELECT
            commodity,
            COUNT(*) as count,
            MIN(timestamp) as first_date,
            MAX(timestamp) as last_date
        FROM raw.green_button_interval_readings
        GROUP BY commodity
        ORDER BY commodity
    ''').fetchall()

    print('\nCommodity breakdown:')
    for row in result:
        print(f'  {row[0]}: {row[1]} readings ({row[2]} to {row[3]})')

if __name__ == '__main__':
    main()
