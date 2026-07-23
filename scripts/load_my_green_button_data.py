#!/usr/bin/env python3
"""Load personal Green Button data into the pipeline.

Configure your data file paths in config.local.yml:

green_button:
  files:
    - path: ~/Downloads/Kitchener_Utilities_Water_12_Months_01-06-2025_21-07-2026.xml
      home_id: my-home
      commodity: water
    - path: ~/Downloads/Green_Button_Electricity.xml
      home_id: my-home
      commodity: electricity
"""
import dlt
from pathlib import Path
import sys
import yaml

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pipelines.green_button import green_button_source
from pipelines.canada.ontario import enova_csv_source


def load_config():
    """Load user configuration from config.local.yml."""
    config_file = Path(__file__).parent.parent / "config.local.yml"

    if not config_file.exists():
        print("Error: config.local.yml not found")
        print("\nCreate config.local.yml with your Green Button file paths:")
        print("""
green_button:
  files:
    - path: ~/Downloads/Kitchener_Utilities_Water_12_Months.xml
      home_id: my-home
      commodity: water
    - path: ~/Downloads/Green_Button_Electricity.xml
      home_id: my-home
      commodity: electricity
""")
        sys.exit(1)

    with open(config_file) as f:
        config = yaml.safe_load(f)

    if 'green_button' not in config or 'files' not in config['green_button']:
        print("Error: config.local.yml missing 'green_button.files' section")
        sys.exit(1)

    return config['green_button']['files']


def load_green_button_data():
    """Load all configured Green Button files."""
    files_config = load_config()

    if not files_config:
        print("No Green Button files configured in config.local.yml")
        return

    # Create dlt pipeline
    pipeline = dlt.pipeline(
        pipeline_name="green_button",
        destination="duckdb",
        dataset_name="raw",
        dev_mode=False,  # Persist state for production use
    )

    print("Loading Green Button data...")
    print(f"  Pipeline: {pipeline.pipeline_name}")
    print(f"  Destination: {pipeline.destination.destination_name}")
    print(f"  Dataset: {pipeline.dataset_name}")
    print()

    total_files = 0
    total_readings = 0

    for file_config in files_config:
        file_path = Path(file_config['path']).expanduser()
        home_id = file_config['home_id']
        commodity = file_config.get('commodity', 'unknown')
        file_format = file_config.get('format', 'greenbutton_xml')  # Default to Green Button

        if not file_path.exists():
            print(f"⚠️  SKIP: {file_path.name} (file not found)")
            print(f"     Expected at: {file_path}")
            continue

        if file_path.stat().st_size == 0:
            print(f"⚠️  SKIP: {file_path.name} (file is empty)")
            print(f"     Re-download from your utility portal")
            continue

        print(f"📁 Loading: {file_path.name}")
        print(f"   Format: {file_format}")
        print(f"   Commodity: {commodity}")
        print(f"   Home ID: {home_id}")

        # Load file based on format
        if file_format == 'enova_csv':
            data = enova_csv_source(
                csv_file_path=file_path,
                home_id=home_id
            )
        elif file_format == 'greenbutton_xml':
            data = green_button_source(
                xml_file_path=file_path,
                home_id=home_id
            )
        else:
            print(f"⚠️  SKIP: Unknown format '{file_format}'")
            print(f"     Supported formats: greenbutton_xml, enova_csv")
            continue

        info = pipeline.run(data)
        total_files += 1

        # Count readings loaded
        with pipeline.sql_client() as client:
            with client.execute_query("""
                SELECT COUNT(*)
                FROM green_button_interval_readings
                WHERE home_id = ?
            """, home_id) as cursor:
                count = cursor.fetchone()[0]
                print(f"   ✓ Loaded {count} interval readings")
                total_readings += count

        print()

    print(f"\n{'='*60}")
    print(f"Summary:")
    print(f"  Files loaded: {total_files}")
    print(f"  Total readings: {total_readings}")

    # Show overall stats
    if total_readings > 0:
        print(f"\n{'='*60}")
        print("Data summary:")
        with pipeline.sql_client() as client:
            with client.execute_query("""
                SELECT
                    commodity,
                    COUNT(*) as intervals,
                    MIN(timestamp) as first_reading,
                    MAX(timestamp) as last_reading,
                    SUM(kwh) as total_consumption
                FROM green_button_interval_readings
                GROUP BY commodity
                ORDER BY commodity
            """) as cursor:
                for row in cursor.fetchall():
                    print(f"\n  {row[0].upper()}:")
                    print(f"    Intervals: {row[1]:,}")
                    print(f"    Date range: {row[2]} to {row[3]}")
                    if row[4] is not None:
                        print(f"    Total consumption: {row[4]:,.2f} {get_uom(row[0])}")

        print(f"\n{'='*60}")
        print(f"✓ Data loaded to: {pipeline.pipelines_dir}")
        print(f"  DuckDB file: {pipeline.pipelines_dir}/green_button.duckdb")


def get_uom(commodity):
    """Get unit of measure for commodity."""
    return {
        'electricity': 'kWh',
        'gas': 'm³',
        'water': 'm³',
    }.get(commodity.lower() if commodity else '', 'units')


if __name__ == "__main__":
    load_green_button_data()
