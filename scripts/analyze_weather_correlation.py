#!/usr/bin/env python3
"""Analyze correlation between weather and electricity consumption.

This script demonstrates basic weather vs consumption analysis:
- Temperature vs consumption correlation
- Degree day calculations
- HVAC season analysis
- Daily/monthly aggregations

Usage:
  pixi run python scripts/analyze_weather_correlation.py
"""
import duckdb
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from pipelines.config import get_config


def main():
    """Run weather correlation analysis."""
    print("=" * 80)
    print("WEATHER vs ELECTRICITY CONSUMPTION ANALYSIS")
    print("=" * 80)
    print()

    # Load config and connect to database
    config = get_config()
    conn = duckdb.connect(config["paths"]["duckdb"])

    # Check data availability
    result = conn.execute("""
        SELECT
            COUNT(*) as total,
            MIN(timestamp) as start_date,
            MAX(timestamp) as end_date,
            COUNT(DISTINCT home_id) as homes
        FROM main_marts.fct_electricity_with_weather
        WHERE NOT missing_weather_data
    """).fetchone()

    print(f"Data Summary:")
    print(f"  Total records: {result[0]:,}")
    print(f"  Date range: {result[1]} to {result[2]}")
    print(f"  Homes: {result[3]}")
    print()

    # Temperature vs consumption correlation
    print("=" * 80)
    print("1. TEMPERATURE vs CONSUMPTION")
    print("=" * 80)
    print()

    result = conn.execute("""
        SELECT
            temperature_category,
            COUNT(*) as hours,
            ROUND(AVG(kwh), 2) as avg_kwh_per_hour,
            ROUND(AVG(temperature_c), 1) as avg_temp_c,
            ROUND(MIN(temperature_c), 1) as min_temp,
            ROUND(MAX(temperature_c), 1) as max_temp
        FROM main_marts.fct_electricity_with_weather
        WHERE NOT missing_weather_data
        GROUP BY temperature_category
        ORDER BY avg_temp_c
    """).fetchall()

    print(f"{'Category':<15} {'Hours':<8} {'Avg kWh/hr':<12} {'Avg Temp':<10} {'Temp Range'}")
    print("-" * 80)
    for row in result:
        print(f"{row[0]:<15} {row[1]:<8} {row[2]:<12.2f} {row[3]:<10.1f} {row[4]:.1f}°C to {row[5]:.1f}°C")

    print()

    # HVAC season analysis
    print("=" * 80)
    print("2. HVAC SEASON ANALYSIS")
    print("=" * 80)
    print()

    result = conn.execute("""
        SELECT
            hvac_season,
            COUNT(*) as hours,
            ROUND(AVG(kwh), 2) as avg_kwh_per_hour,
            ROUND(SUM(kwh), 0) as total_kwh,
            ROUND(AVG(temperature_c), 1) as avg_temp_c
        FROM main_marts.fct_electricity_with_weather
        WHERE NOT missing_weather_data
        GROUP BY hvac_season
        ORDER BY
            CASE hvac_season
                WHEN 'cooling' THEN 1
                WHEN 'shoulder' THEN 2
                WHEN 'heating' THEN 3
            END
    """).fetchall()

    print(f"{'Season':<15} {'Hours':<8} {'Avg kWh/hr':<12} {'Total kWh':<12} {'Avg Temp'}")
    print("-" * 80)
    for row in result:
        print(f"{row[0]:<15} {row[1]:<8} {row[2]:<12.2f} {row[3]:<12,.0f} {row[4]:.1f}°C")

    print()

    # Monthly degree days and consumption
    print("=" * 80)
    print("3. MONTHLY DEGREE DAYS & CONSUMPTION")
    print("=" * 80)
    print()

    result = conn.execute("""
        SELECT
            year,
            month,
            ROUND(SUM(hdh) / 24.0, 0) as total_hdd,
            ROUND(SUM(cdh) / 24.0, 0) as total_cdd,
            ROUND(SUM(kwh), 0) as total_kwh,
            ROUND(AVG(temperature_c), 1) as avg_temp_c,
            COUNT(*) as hours
        FROM main_marts.fct_electricity_with_weather
        WHERE NOT missing_weather_data
        GROUP BY year, month
        ORDER BY year, month
    """).fetchall()

    print(f"{'Year-Month':<12} {'HDD':<8} {'CDD':<8} {'Total kWh':<12} {'Avg Temp':<10} {'Hours'}")
    print("-" * 80)
    for row in result:
        print(f"{row[0]}-{row[1]:02d}       {row[2]:<8.0f} {row[3]:<8.0f} {row[4]:<12,.0f} {row[5]:<10.1f} {row[6]}")

    print()

    # Daily patterns - last 30 days
    print("=" * 80)
    print("4. RECENT DAILY PATTERNS (Last 30 Days)")
    print("=" * 80)
    print()

    result = conn.execute("""
        SELECT
            DATE_TRUNC('day', timestamp) as date,
            ROUND(SUM(hdh) / 24.0, 1) as hdd,
            ROUND(SUM(cdh) / 24.0, 1) as cdd,
            ROUND(SUM(kwh), 0) as daily_kwh,
            ROUND(AVG(temperature_c), 1) as avg_temp_c,
            ROUND(MIN(temperature_c), 1) as min_temp,
            ROUND(MAX(temperature_c), 1) as max_temp
        FROM main_marts.fct_electricity_with_weather
        WHERE NOT missing_weather_data
        GROUP BY date
        ORDER BY date DESC
        LIMIT 30
    """).fetchall()

    print(f"{'Date':<12} {'HDD':<7} {'CDD':<7} {'Daily kWh':<11} {'Temp (avg/min/max)'}")
    print("-" * 80)
    for row in result:
        date_str = str(row[0])[:10]
        print(f"{date_str:<12} {row[1]:<7.1f} {row[2]:<7.1f} {row[3]:<11,.0f} {row[4]:.1f}°C / {row[5]:.1f}°C / {row[6]:.1f}°C")

    print()

    # Consumption vs temperature scatter (binned)
    print("=" * 80)
    print("5. CONSUMPTION vs TEMPERATURE (5°C bins)")
    print("=" * 80)
    print()

    result = conn.execute("""
        SELECT
            FLOOR(temperature_c / 5) * 5 as temp_bin,
            COUNT(*) as hours,
            ROUND(AVG(kwh), 2) as avg_kwh,
            ROUND(STDDEV(kwh), 2) as stddev_kwh
        FROM main_marts.fct_electricity_with_weather
        WHERE NOT missing_weather_data
        GROUP BY temp_bin
        ORDER BY temp_bin
    """).fetchall()

    print(f"{'Temp Range':<15} {'Hours':<8} {'Avg kWh/hr':<12} {'Std Dev'}")
    print("-" * 80)
    for row in result:
        temp_min = int(row[0])
        temp_max = temp_min + 4
        print(f"{temp_min}°C to {temp_max}°C  {row[1]:<8} {row[2]:<12.2f} ±{row[3]:.2f}")

    print()

    # Correlation coefficient
    print("=" * 80)
    print("6. CORRELATION STATISTICS")
    print("=" * 80)
    print()

    result = conn.execute("""
        SELECT
            ROUND(CORR(temperature_c, kwh), 3) as temp_kwh_corr,
            ROUND(CORR(hdh, kwh), 3) as hdh_kwh_corr,
            ROUND(CORR(cdh, kwh), 3) as cdh_kwh_corr
        FROM main_marts.fct_electricity_with_weather
        WHERE NOT missing_weather_data
    """).fetchone()

    print(f"Correlation coefficients (Pearson):")
    print(f"  Temperature vs kWh:     {result[0]:+.3f}")
    print(f"  Heating Degree Hours vs kWh:  {result[1]:+.3f}")
    print(f"  Cooling Degree Hours vs kWh:  {result[2]:+.3f}")
    print()
    print("Interpretation:")
    print("  +1.0 = perfect positive correlation")
    print("   0.0 = no correlation")
    print("  -1.0 = perfect negative correlation")
    print()

    conn.close()

    print("=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)
    print()
    print("Next steps:")
    print("  - Create dashboard visualizations in Evidence")
    print("  - Calculate weather-normalized consumption metrics")
    print("  - Identify HVAC equipment efficiency patterns")
    print("  - Compare year-over-year usage (weather-adjusted)")


if __name__ == "__main__":
    main()
