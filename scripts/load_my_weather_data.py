#!/usr/bin/env python3
"""Load weather data for home location from Open-Meteo."""
import dlt
from pathlib import Path
import sys
import yaml

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pipelines.weather import weather_source


def load_weather_data():
    """Load weather data for configured home location."""
    # Load config
    config_file = Path(__file__).parent.parent / "config.local.yml"

    if not config_file.exists():
        print("Error: config.local.yml not found")
        return

    with open(config_file) as f:
        config = yaml.safe_load(f)

    # Get weather config
    weather_config = config.get('weather', {})
    location_config = config.get('location', {})
    home_config = config.get('home', {})

    latitude = weather_config.get('latitude') or location_config.get('latitude')
    longitude = weather_config.get('longitude') or location_config.get('longitude')

    if not latitude or not longitude:
        print("Error: latitude/longitude not configured")
        return

    print("Loading weather data from Open-Meteo...")
    print(f"  Location: {home_config.get('name', 'Home')}")
    print(f"  Coordinates: {latitude}, {longitude}")

    # Auto-detect date range from electricity data
    print("\n  Detecting date range from electricity data...")

    gb_pipeline = dlt.pipeline(
        pipeline_name="green_button",
        destination="duckdb",
        dataset_name="raw"
    )

    start_date = None
    end_date = None

    try:
        with gb_pipeline.sql_client() as client:
            with client.execute_query("""
                SELECT
                    MIN(timestamp) as first_reading,
                    MAX(timestamp) as last_reading
                FROM green_button_interval_readings
                WHERE home_id = ?
                  AND commodity = 'CommodityKindValue.VALUE_1'
            """, home_config.get('id', 'ryan-home-001')) as cursor:
                row = cursor.fetchone()
                if row and row[0]:
                    start_date = row[0].strftime('%Y-%m-%d')
                    end_date = row[1].strftime('%Y-%m-%d')
                    print(f"  Date range: {start_date} to {end_date}")
    except Exception as e:
        print(f"  Could not auto-detect dates: {e}")
        print("  Using default: 2022-12-25 to 2026-07-22")
        start_date = "2022-12-25"
        end_date = "2026-07-22"

    if not start_date or not end_date:
        print("  No electricity data found, using default dates")
        start_date = "2022-12-25"
        end_date = "2026-07-22"

    # Create weather pipeline
    pipeline = dlt.pipeline(
        pipeline_name="weather",
        destination="duckdb",
        dataset_name="raw",
        dev_mode=False
    )

    print(f"\n  Fetching weather data from Open-Meteo...")
    print(f"  API: https://archive-api.open-meteo.com/v1/archive")
    print()

    # Load weather data
    data = weather_source(
        latitude=latitude,
        longitude=longitude,
        start_date=start_date,
        end_date=end_date,
        location_name="kitchener"
    )

    info = pipeline.run(data)

    print("\n" + "="*60)
    print("Weather data loaded successfully!")
    print(f"  DuckDB: {pipeline.pipelines_dir}/weather.duckdb")

    # Show stats
    with pipeline.sql_client() as client:
        with client.execute_query("""
            SELECT
                COUNT(*) as hours,
                MIN(timestamp) as first,
                MAX(timestamp) as last,
                ROUND(AVG(temperature_2m), 1) as avg_temp,
                ROUND(MIN(temperature_2m), 1) as min_temp,
                ROUND(MAX(temperature_2m), 1) as max_temp
            FROM weather_hourly
            WHERE location_name = 'kitchener'
        """) as cursor:
            row = cursor.fetchone()
            print(f"\n  Statistics:")
            print(f"    Total hours: {row[0]:,}")
            print(f"    Date range: {row[1]} to {row[2]}")
            print(f"    Temperature: avg={row[3]}°C, min={row[4]}°C, max={row[5]}°C")

    print("\n" + "="*60)


if __name__ == "__main__":
    load_weather_data()
