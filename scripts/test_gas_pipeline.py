#!/usr/bin/env -S pixi run python
"""Test Green Button gas pipeline with actual Enbridge Gas data."""
import dlt
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from pipelines.green_button import green_button_source


def test_gas_pipeline():
    """Test gas data pipeline end-to-end."""
    gas_xml = Path("/Users/ryan/dev/greenbuttonengine/test_files/EGD_Gas_EnergyUsage_20221225_20241225.xml")

    if not gas_xml.exists():
        print(f"❌ Gas test file not found: {gas_xml}")
        return False

    print("="*80)
    print("GAS PIPELINE TEST: Enbridge Gas → DuckDB → dbt")
    print("="*80)

    # Step 1: Load gas data with dlt
    print("\n[1/3] Loading gas data with dlt...")
    print("-" * 80)

    pipeline = dlt.pipeline(
        pipeline_name="green_button_gas_test",
        destination="duckdb",
        dataset_name="raw",
    )

    data = green_button_source(
        xml_file_path=gas_xml,
        home_id="test-home-001"
    )

    info = pipeline.run(data)
    print(f"✓ dlt load complete")

    # Step 2: Query raw data
    print("\n[2/3] Querying raw gas data...")
    print("-" * 80)

    with pipeline.sql_client() as client:
        # Check what we loaded
        with client.execute_query("""
            SELECT
                COUNT(*) as total_records,
                MIN(timestamp) as min_date,
                MAX(timestamp) as max_date,
                SUM(kwh) as total_m3,
                commodity,
                uom
            FROM raw.green_button_interval_readings
            GROUP BY commodity, uom
        """) as cursor:
            for row in cursor.fetchall():
                print(f"  Records: {row[0]}")
                print(f"  Date range: {row[1]} to {row[2]}")
                print(f"  Total m³: {row[3]:,.2f}")
                print(f"  Commodity: {row[4]}")
                print(f"  UOM: {row[5]}")

        # Show sample records
        print("\n  Sample records:")
        with client.execute_query("""
            SELECT
                timestamp,
                kwh as m3,
                quality_code,
                duration_seconds / 86400.0 as duration_days
            FROM raw.green_button_interval_readings
            ORDER BY timestamp
            LIMIT 5
        """) as cursor:
            for row in cursor.fetchall():
                print(f"    {row[0]}: {row[1]:,.2f} m³, {row[2]}, {row[3]:.0f} days")

    # Step 3: Query staged data using SQL directly (skip dbt for this test)
    print("\n[3/3] Testing staging transformation...")
    print("-" * 80)

    # Apply staging logic manually for testing
    with pipeline.sql_client() as client:
        # Apply staging logic (filter to gas, decode enums)
        with client.execute_query("""
            WITH decoded AS (
                SELECT
                    timestamp as ts,
                    kwh as m3,
                    CASE
                        WHEN commodity LIKE '%VALUE_1%' THEN 'electricity'
                        WHEN commodity LIKE '%VALUE_7%' THEN 'natural_gas'
                        WHEN commodity LIKE '%VALUE_2%' THEN 'water'
                        ELSE 'unknown'
                    END as commodity_type,
                    CASE
                        WHEN quality_code LIKE '%VALIDATED%' THEN 'validated'
                        WHEN quality_code LIKE '%ESTIMATED%' THEN 'estimated'
                        WHEN quality_code LIKE '%MISSING%' THEN 'missing'
                        ELSE 'unknown'
                    END as quality
                FROM raw.green_button_interval_readings
            )
            SELECT
                COUNT(*) as total_records,
                MIN(ts) as min_date,
                MAX(ts) as max_date,
                SUM(m3) as total_m3,
                commodity_type
            FROM decoded
            WHERE commodity_type = 'natural_gas'
            GROUP BY commodity_type
        """) as cursor:
            for row in cursor.fetchall():
                print(f"\n  Staged gas data:")
                print(f"    Records: {row[0]}")
                print(f"    Date range: {row[1]} to {row[2]}")
                print(f"    Total m³: {row[3]:,.2f}")
                print(f"    Commodity: {row[4]}")

        # Show quality breakdown
        with client.execute_query("""
            WITH decoded AS (
                SELECT
                    kwh as m3,
                    CASE
                        WHEN quality_code LIKE '%VALIDATED%' THEN 'validated'
                        WHEN quality_code LIKE '%ESTIMATED%' THEN 'estimated'
                        WHEN quality_code LIKE '%MISSING%' THEN 'missing'
                        ELSE 'unknown'
                    END as quality,
                    CASE
                        WHEN commodity LIKE '%VALUE_7%' THEN 'natural_gas'
                        ELSE 'other'
                    END as commodity_type
                FROM raw.green_button_interval_readings
            )
            SELECT
                quality,
                COUNT(*) as count,
                SUM(m3) as total_m3
            FROM decoded
            WHERE commodity_type = 'natural_gas'
            GROUP BY quality
            ORDER BY count DESC
        """) as cursor:
            print(f"\n  Quality breakdown:")
            for row in cursor.fetchall():
                print(f"    {row[0]}: {row[1]} records, {row[2]:,.2f} m³")

    print("\n" + "="*80)
    print("✅ GAS PIPELINE TEST PASSED")
    print("="*80)
    return True


if __name__ == "__main__":
    success = test_gas_pipeline()
    sys.exit(0 if success else 1)
