#!/usr/bin/env python3
"""Test script for weather data pipeline.

Loads historical weather data from Open-Meteo API into DuckDB.

Usage:
  pixi run python scripts/test_weather_pipeline.py
"""
import dlt
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from pipelines.weather import weather_source
from pipelines.config import get_config


def main():
    """Run weather pipeline test."""
    print("=" * 80)
    print("WEATHER DATA PIPELINE TEST")
    print("=" * 80)
    print()

    # Load configuration
    config = get_config()

    # Create dlt pipeline
    pipeline = dlt.pipeline(
        pipeline_name="weather",
        destination=dlt.destinations.duckdb(config["paths"]["duckdb"]),
        dataset_name="raw",
    )

    # Run pipeline with config values
    print("Loading weather data from Open-Meteo API...")
    data = weather_source()

    info = pipeline.run(data)

    print()
    print("=" * 80)
    print("PIPELINE COMPLETED")
    print("=" * 80)
    print()
    print(f"Pipeline: {info.pipeline.pipeline_name}")
    print(f"Destination: {info.pipeline.destination}")
    print(f"Dataset: {info.pipeline.dataset_name}")
    print()

    # Show loaded data stats
    if hasattr(info, 'load_packages'):
        for package in info.load_packages:
            print(f"Load package: {package.load_id}")
            print(f"State: {package.state}")

    # Query loaded data
    print()
    print("Querying loaded data...")
    print()

    with pipeline.sql_client() as client:
        # Count total records
        with client.execute_query("SELECT COUNT(*) as count FROM raw.weather_hourly") as cursor:
            count = cursor.fetchone()[0]
            print(f"Total weather records: {count:,}")

        # Show date range
        with client.execute_query("""
            SELECT
                MIN(timestamp) as min_date,
                MAX(timestamp) as max_date,
                COUNT(DISTINCT location_name) as locations
            FROM raw.weather_hourly
        """) as cursor:
            row = cursor.fetchone()
            print(f"Date range: {row[0]} to {row[1]}")
            print(f"Locations: {row[2]}")

        # Show temperature stats
        with client.execute_query("""
            SELECT
                location_name,
                COUNT(*) as records,
                ROUND(MIN(temperature_c), 1) as min_temp,
                ROUND(MAX(temperature_c), 1) as max_temp,
                ROUND(AVG(temperature_c), 1) as avg_temp
            FROM raw.weather_hourly
            GROUP BY location_name
        """) as cursor:
            print()
            print("Temperature Statistics by Location:")
            for row in cursor.fetchall():
                print(f"  {row[0]}: {row[1]:,} records, "
                      f"temp range: {row[2]}°C to {row[3]}°C (avg: {row[4]}°C)")

        # Show sample records
        with client.execute_query("""
            SELECT
                timestamp,
                temperature_c,
                humidity_pct,
                precipitation_mm,
                windspeed_kmh
            FROM raw.weather_hourly
            ORDER BY timestamp DESC
            LIMIT 5
        """) as cursor:
            print()
            print("Most Recent Records:")
            for row in cursor.fetchall():
                print(f"  {row[0]}: {row[1]}°C, {row[2]}% humidity, "
                      f"{row[3]}mm precip, {row[4]} km/h wind")

    print()
    print("=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()
