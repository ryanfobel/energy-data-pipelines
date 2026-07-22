#!/usr/bin/env -S pixi run python
"""Generate mock water consumption data for testing."""
import duckdb
from datetime import datetime, timedelta
import random

def main():
    conn = duckdb.connect('energy_warehouse.duckdb')

    # Generate 24 months of mock water data (monthly readings)
    start_date = datetime(2022, 12, 1, tzinfo=None)
    readings = []

    for i in range(24):
        reading_date = start_date + timedelta(days=30 * i)
        # Typical household: 10-15 m³ per month, with seasonal variation
        base_usage = 12.0
        seasonal_factor = 1.0 + 0.3 * (1 if reading_date.month in [6, 7, 8] else 0)  # More in summer
        volume = base_usage * seasonal_factor + random.uniform(-2, 2)

        readings.append({
            'home_id': 'test-home-001',
            'usage_point_idx': 0,
            'meter_reading_idx': i,
            'meter_id': 'water-meter-001',
            'timestamp': reading_date,
            'duration_seconds': 30 * 24 * 3600,  # ~30 days
            'raw_value': int(volume * 1000),  # Convert to liters
            'kwh': volume,  # m³
            'cost': None,  # No cost data for water
            'quality_code': 'QualityOfReadingValue.VALUE_14',  # VALIDATED
            'tou_bucket': None,
            'commodity': 'CommodityKindValue.VALUE_2',  # Water
            'uom': 'UomValue.VALUE_42',  # Cubic meters
            'service_kind': 'ServiceKindValue.VALUE_1',  # Electricity (reused)
            '_dlt_load_id': f'mock_water_{i}',
            '_dlt_id': f'mock_water_reading_{i}'
        })

    # Insert into raw table
    conn.execute('CREATE SCHEMA IF NOT EXISTS raw')

    # Insert the mock readings
    for reading in readings:
        conn.execute('''
            INSERT INTO raw.green_button_interval_readings
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', [
            reading['home_id'],
            reading['usage_point_idx'],
            reading['meter_reading_idx'],
            reading['meter_id'],
            reading['timestamp'],
            reading['duration_seconds'],
            reading['raw_value'],
            reading['kwh'],
            reading['cost'],
            reading['quality_code'],
            reading['tou_bucket'],
            reading['commodity'],
            reading['uom'],
            reading['service_kind'],
            reading['_dlt_load_id'],
            reading['_dlt_id']
        ])

    print(f"✓ Generated {len(readings)} mock water readings")

    # Verify
    result = conn.execute('''
        SELECT COUNT(*), MIN(timestamp), MAX(timestamp), SUM(kwh)
        FROM raw.green_button_interval_readings
        WHERE commodity LIKE '%VALUE_2%'
    ''').fetchone()

    print(f"  Date range: {result[1]} to {result[2]}")
    print(f"  Total volume: {result[3]:.1f} m³")

if __name__ == '__main__':
    main()
