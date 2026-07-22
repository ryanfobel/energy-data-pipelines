#!/usr/bin/env python3
"""Test script for air quality data pipeline.

Loads historical air quality data from Open-Meteo API into DuckDB.

Usage:
  pixi run python scripts/test_air_quality_pipeline.py
"""
import dlt
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from pipelines.weather.air_quality import air_quality_source
from pipelines.config import get_config


def main():
    """Run air quality pipeline test."""
    print("=" * 80)
    print("AIR QUALITY DATA PIPELINE TEST")
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
    print("Loading air quality data from Open-Meteo API...")
    data = air_quality_source()

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
        with client.execute_query("SELECT COUNT(*) as count FROM raw.air_quality_hourly") as cursor:
            count = cursor.fetchone()[0]
            print(f"Total air quality records: {count:,}")

        # Show date range
        with client.execute_query("""
            SELECT
                MIN(timestamp) as min_date,
                MAX(timestamp) as max_date,
                COUNT(DISTINCT location_name) as locations
            FROM raw.air_quality_hourly
        """) as cursor:
            row = cursor.fetchone()
            print(f"Date range: {row[0]} to {row[1]}")
            print(f"Locations: {row[2]}")

        # Show PM2.5 and air quality stats
        with client.execute_query("""
            SELECT
                location_name,
                COUNT(*) as records,
                ROUND(MIN(pm2_5), 1) as min_pm2_5,
                ROUND(MAX(pm2_5), 1) as max_pm2_5,
                ROUND(AVG(pm2_5), 1) as avg_pm2_5,
                ROUND(AVG(european_aqi), 0) as avg_aqi
            FROM raw.air_quality_hourly
            WHERE pm2_5 IS NOT NULL
            GROUP BY location_name
        """) as cursor:
            print()
            print("Air Quality Statistics by Location:")
            for row in cursor.fetchall():
                print(f"  {row[0]}: {row[1]:,} records, "
                      f"PM2.5 range: {row[2]}-{row[3]} µg/m³ (avg: {row[4]} µg/m³), "
                      f"avg AQI: {row[5]}")

        # Show UV and aerosol stats
        with client.execute_query("""
            SELECT
                location_name,
                ROUND(AVG(uv_index), 1) as avg_uv_index,
                ROUND(MAX(uv_index), 1) as max_uv_index,
                ROUND(AVG(aerosol_optical_depth), 3) as avg_aod
            FROM raw.air_quality_hourly
            WHERE uv_index IS NOT NULL
            GROUP BY location_name
        """) as cursor:
            print()
            print("UV and Aerosol Statistics by Location:")
            for row in cursor.fetchall():
                print(f"  {row[0]}: avg UV index: {row[1]}, "
                      f"max UV index: {row[2]}, "
                      f"avg aerosol optical depth: {row[3]}")

        # Air quality categories based on PM2.5
        # Good: 0-12, Moderate: 12-35, Unhealthy: 35+
        with client.execute_query("""
            SELECT
                CASE
                    WHEN pm2_5 < 12 THEN 'good'
                    WHEN pm2_5 < 35 THEN 'moderate'
                    ELSE 'unhealthy'
                END as air_quality_category,
                COUNT(*) as hours,
                ROUND(AVG(pm2_5), 1) as avg_pm2_5
            FROM raw.air_quality_hourly
            WHERE pm2_5 IS NOT NULL
            GROUP BY air_quality_category
            ORDER BY avg_pm2_5
        """) as cursor:
            print()
            print("Air Quality Categories (based on PM2.5):")
            for row in cursor.fetchall():
                print(f"  {row[0]}: {row[1]:,} hours (avg PM2.5: {row[2]} µg/m³)")

        # Show sample records
        with client.execute_query("""
            SELECT
                timestamp,
                pm2_5,
                pm10,
                uv_index,
                aerosol_optical_depth,
                european_aqi
            FROM raw.air_quality_hourly
            ORDER BY timestamp DESC
            LIMIT 5
        """) as cursor:
            print()
            print("Most Recent Records:")
            for row in cursor.fetchall():
                print(f"  {row[0]}: PM2.5={row[1]} µg/m³, PM10={row[2]} µg/m³, "
                      f"UV={row[3]}, AOD={row[4]}, AQI={row[5]}")

    print()
    print("=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()
