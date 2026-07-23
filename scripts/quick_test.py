#!/usr/bin/env -S pixi run python
"""Quick test to load gas data and see dashboard."""
import dlt
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from pipelines.green_button import green_button_source


def main():
    gas_xml = Path("/Users/ryan/dev/greenbuttonengine/test_files/EGD_Gas_EnergyUsage_20221225_20241225.xml")

    if not gas_xml.exists():
        print(f"❌ Gas test file not found: {gas_xml}")
        return False

    print("Loading Green Button gas data...")

    pipeline = dlt.pipeline(
        pipeline_name="green_button",
        destination="duckdb",
        dataset_name="raw",
    )

    data = green_button_source(
        xml_file_path=gas_xml,
        home_id="test-home-001"
    )

    info = pipeline.run(data)
    print(f"✓ Loaded {info}")

    # Check what we got
    with pipeline.sql_client() as client:
        with client.execute_query("SELECT COUNT(*) FROM raw.green_button_interval_readings") as cursor:
            count = cursor.fetchone()[0]
            print(f"✓ Loaded {count} interval readings")

    print("\nNow run:")
    print("  pixi run dbt-run    # Build marts")
    print("  cd dashboard && npm run build && open build/index.html")

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
