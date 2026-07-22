#!/usr/bin/env -S pixi run python
"""Load gas data from Green Button XML file."""
import dlt
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from pipelines.green_button import green_button_source


def main():
    # Use the Enbridge Gas test file
    gas_xml = Path("/Users/ryan/dev/greenbuttonengine/test_files/EGD_Gas_EnergyUsage_20221225_20241225.xml")

    if not gas_xml.exists():
        print(f"❌ Gas test file not found: {gas_xml}")
        print("Please provide a Green Button gas XML file")
        return False

    print("=" * 80)
    print("LOADING GREEN BUTTON GAS DATA")
    print("=" * 80)
    print(f"Source: {gas_xml}")

    pipeline = dlt.pipeline(
        pipeline_name="green_button",
        destination="duckdb",
        dataset_name="raw",
        dev_mode=False
    )

    data = green_button_source(
        xml_file_path=gas_xml,
        home_id="test-home-001"
    )

    info = pipeline.run(data)
    print(f"\n✓ Pipeline complete: {info}")

    # Check what we loaded
    with pipeline.sql_client() as client:
        with client.execute_query("""
            SELECT
                COUNT(*) as count,
                MIN(timestamp) as min_date,
                MAX(timestamp) as max_date
            FROM raw.green_button_interval_readings
            WHERE commodity LIKE '%VALUE_7%'
        """) as cursor:
            row = cursor.fetchone()
            if row and row[0] > 0:
                print(f"\n✓ Loaded {row[0]} gas readings")
                print(f"  Date range: {row[1]} to {row[2]}")
            else:
                print("\n⚠ No gas readings found")

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
