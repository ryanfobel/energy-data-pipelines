#!/usr/bin/env -S pixi run python
"""Load user's actual Green Button data and run full pipeline."""
import dlt
from pathlib import Path
import sys

# Add parent directory to path for pipeline imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from pipelines.green_button import green_button_source

def main():
    """Load all available Green Button XML files."""

    # Known Green Button files
    xml_files = [
        {
            'path': '/Users/ryan/dev/greenbuttonengine/test_files/Hydro1_Electric_60_Minute_12-25-2022_12-23-2024.xml',
            'type': 'electricity',
            'description': 'Hydro One Electricity (hourly, 2022-2024)'
        },
        {
            'path': '/Users/ryan/dev/greenbuttonengine/test_files/EGD_Gas_EnergyUsage_20221225_20241225.xml',
            'type': 'gas',
            'description': 'Enbridge Gas (monthly, 2022-2024)'
        },
        {
            'path': '/Users/ryan/dev/greenbuttonengine/test_files/EPC_Electricity_NonInterval_2022-12-26_2024-12-25.xml',
            'type': 'electricity_non_interval',
            'description': 'EPC Electricity (non-interval, 2022-2024)'
        }
    ]

    # Create pipeline
    pipeline = dlt.pipeline(
        pipeline_name="green_button",
        destination="duckdb",
        dataset_name="raw",
        dev_mode=False
    )

    print("=" * 80)
    print("LOADING YOUR GREEN BUTTON DATA")
    print("=" * 80)

    for file_info in xml_files:
        xml_path = Path(file_info['path'])

        if not xml_path.exists():
            print(f"\n⚠ Skipping {file_info['description']}")
            print(f"  File not found: {xml_path}")
            continue

        print(f"\n📊 Loading: {file_info['description']}")
        print(f"   File: {xml_path.name}")

        try:
            # Load the data
            data = green_button_source(
                xml_file_path=xml_path,
                home_id="ryan-home-001"  # Your home ID
            )

            info = pipeline.run(data)
            print(f"   ✓ Loaded successfully")

        except Exception as e:
            print(f"   ✗ Error loading: {e}")
            continue

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    with pipeline.sql_client() as client:
        # Check what we loaded
        with client.execute_query("""
            SELECT
                commodity,
                COUNT(*) as readings,
                MIN(timestamp) as earliest,
                MAX(timestamp) as latest
            FROM raw.green_button_interval_readings
            GROUP BY commodity
            ORDER BY commodity
        """) as cursor:
            results = cursor.fetchall()

            if results:
                print("\nData loaded:")
                for row in results:
                    print(f"  {row[0]}: {row[1]:,} readings")
                    print(f"    Date range: {row[2]} to {row[3]}")
            else:
                print("\n⚠ No data loaded - check errors above")

    print("\n" + "=" * 80)
    print("NEXT STEPS")
    print("=" * 80)
    print("""
1. Run dbt to build data models:
   cd transform
   pixi run dbt run

2. Load weather data (for your location):
   Edit config.local.yml with your coordinates
   pixi run pipeline-weather
   pixi run pipeline-air-quality

3. Rebuild dbt with weather:
   cd transform
   pixi run dbt run --select fct_electricity_with_weather

4. Build dashboard:
   cd dashboard
   npm run build
   python3 -m http.server 8000 --directory build
   open http://localhost:8000
    """)

    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
