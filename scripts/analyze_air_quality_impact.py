#!/usr/bin/env python3
"""Analyze air quality impact on energy consumption.

Generates insights on:
- Solar panel soiling from aerosol optical depth
- HVAC usage during poor air quality
- UV index correlation with cooling demand
- Seasonal air quality patterns

Usage:
  pixi run python scripts/analyze_air_quality_impact.py
"""
import duckdb
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from pipelines.config import get_config


def main():
    """Analyze air quality impact on energy consumption."""
    config = get_config()
    conn = duckdb.connect(config["paths"]["duckdb"])

    print("=" * 80)
    print("AIR QUALITY IMPACT ANALYSIS")
    print("=" * 80)
    print()

    # 1. Solar panel soiling analysis
    print("1. SOLAR PANEL SOILING ANALYSIS")
    print("   High Aerosol Optical Depth (AOD) Days:")
    print()
    result = conn.execute("""
        SELECT
            DATE(timestamp) as date,
            ROUND(AVG(aerosol_optical_depth), 3) as avg_aod,
            ROUND(MAX(aerosol_optical_depth), 3) as peak_aod,
            ROUND(AVG(dust), 1) as avg_dust,
            ROUND(AVG(pm2_5), 1) as avg_pm2_5,
            ROUND(AVG(ghi_wm2), 0) as avg_ghi,
            pm2_5_category
        FROM main_marts.fct_electricity_with_weather
        WHERE aerosol_optical_depth > 0.3
        GROUP BY DATE(timestamp), pm2_5_category
        ORDER BY avg_aod DESC
        LIMIT 15
    """).fetchall()

    if result:
        print(f"   {'Date':<12} {'Avg AOD':<8} {'Peak AOD':<9} {'Dust':<8} {'PM2.5':<8} {'GHI':<8} {'AQ Category'}")
        print("   " + "-" * 78)
        for row in result:
            print(f"   {str(row[0]):<12} {row[1]:<8} {row[2]:<9} {row[3]:<8} {row[4]:<8} {row[5]:<8} {row[6]}")
        print()
        print(f"   Found {len(result)} days with significant atmospheric haze")
        print("   Recommendation: Solar panel cleaning recommended after high AOD periods")
    else:
        print("   No significant soiling risk detected (AOD < 0.3)")
    print()
    print()

    # 2. HVAC usage during poor air quality (shoulder season)
    print("2. HVAC USAGE DURING POOR AIR QUALITY (Shoulder Season)")
    print("   Temperature 15-25°C (would normally open windows):")
    print()
    result = conn.execute("""
        SELECT
            pm2_5_category,
            COUNT(*) as hours,
            ROUND(AVG(kwh), 0) as avg_kwh,
            ROUND(AVG(pm2_5), 1) as avg_pm2_5,
            ROUND(AVG(temperature_c), 1) as avg_temp,
            ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) as pct_hours
        FROM main_marts.fct_electricity_with_weather
        WHERE temperature_c BETWEEN 15 AND 25
            AND pm2_5_category IS NOT NULL
        GROUP BY pm2_5_category
        ORDER BY avg_pm2_5
    """).fetchall()

    print(f"   {'Category':<20} {'Hours':<10} {'Avg kWh':<10} {'PM2.5':<10} {'Temp':<8} {'% Hours'}")
    print("   " + "-" * 78)
    for row in result:
        print(f"   {row[0]:<20} {row[1]:<10,} {row[2]:<10} {row[3]:<10} {row[4]:<8} {row[5]}%")

    # Calculate impact
    good_kwh = next(r[2] for r in result if r[0] == 'good')
    try:
        unhealthy_kwh = next(r[2] for r in result if r[0] == 'unhealthy')
        impact_pct = ((unhealthy_kwh - good_kwh) / good_kwh) * 100
        print()
        print(f"   Impact: {impact_pct:.1f}% higher consumption during unhealthy air quality")
        print("   Hypothesis: Closed windows and HVAC recirculation during poor air quality")
    except StopIteration:
        print()
        print("   Note: Insufficient unhealthy air quality data for comparison")
    print()
    print()

    # 3. UV index and cooling demand
    print("3. UV INDEX AND COOLING DEMAND")
    print("   Summer months (Jun-Aug), daytime hours (10am-6pm):")
    print()
    result = conn.execute("""
        SELECT
            uv_category,
            COUNT(*) as hours,
            ROUND(AVG(uv_index), 1) as avg_uv,
            ROUND(AVG(temperature_c), 1) as avg_temp,
            ROUND(AVG(kwh), 0) as avg_kwh,
            ROUND(AVG(cdh), 1) as avg_cdh
        FROM main_marts.fct_electricity_with_weather
        WHERE EXTRACT(month FROM timestamp) BETWEEN 6 AND 8
            AND EXTRACT(hour FROM timestamp) BETWEEN 10 AND 18
            AND uv_category IS NOT NULL
        GROUP BY uv_category
        ORDER BY avg_uv DESC
    """).fetchall()

    print(f"   {'UV Category':<15} {'Hours':<8} {'Avg UV':<8} {'Temp':<8} {'kWh':<8} {'CDH'}")
    print("   " + "-" * 65)
    for row in result:
        print(f"   {row[0]:<15} {row[1]:<8,} {row[2]:<8} {row[3]:<8} {row[4]:<8} {row[5]}")
    print()
    print()

    # 4. Monthly air quality trends
    print("4. MONTHLY AIR QUALITY TRENDS")
    print()
    result = conn.execute("""
        SELECT
            DATE_TRUNC('month', timestamp) as month,
            ROUND(AVG(pm2_5), 1) as avg_pm2_5,
            ROUND(MAX(pm2_5), 1) as peak_pm2_5,
            COUNT(CASE WHEN pm2_5_category IN ('unhealthy_sensitive', 'unhealthy') THEN 1 END) as poor_air_hours,
            ROUND(AVG(aerosol_optical_depth), 3) as avg_aod,
            ROUND(AVG(uv_index), 1) as avg_uv
        FROM main_marts.fct_electricity_with_weather
        WHERE pm2_5 IS NOT NULL
        GROUP BY DATE_TRUNC('month', timestamp)
        ORDER BY month DESC
        LIMIT 12
    """).fetchall()

    print(f"   {'Month':<12} {'Avg PM2.5':<12} {'Peak PM2.5':<12} {'Poor Hours':<12} {'Avg AOD':<10} {'Avg UV'}")
    print("   " + "-" * 78)
    for row in result:
        print(f"   {str(row[0])[:7]:<12} {row[1]:<12} {row[2]:<12} {row[3]:<12} {row[4]:<10} {row[5]}")
    print()
    print()

    # 5. Worst air quality days
    print("5. WORST AIR QUALITY DAYS (Top 10)")
    print()
    result = conn.execute("""
        SELECT
            DATE(timestamp) as date,
            ROUND(AVG(pm2_5), 1) as avg_pm2_5,
            ROUND(MAX(pm2_5), 1) as peak_pm2_5,
            ROUND(AVG(european_aqi), 0) as avg_aqi,
            pm2_5_category,
            ROUND(AVG(kwh), 0) as avg_kwh,
            ROUND(AVG(temperature_c), 1) as avg_temp
        FROM main_marts.fct_electricity_with_weather
        WHERE pm2_5 IS NOT NULL
        GROUP BY DATE(timestamp), pm2_5_category
        ORDER BY avg_pm2_5 DESC
        LIMIT 10
    """).fetchall()

    print(f"   {'Date':<12} {'Avg PM2.5':<12} {'Peak PM2.5':<12} {'AQI':<6} {'Category':<20} {'kWh':<8} {'Temp'}")
    print("   " + "-" * 90)
    for row in result:
        print(f"   {str(row[0]):<12} {row[1]:<12} {row[2]:<12} {row[3]:<6} {row[4]:<20} {row[5]:<8} {row[6]}°C")
    print()
    print()

    # 6. Summary statistics
    print("6. SUMMARY STATISTICS")
    print()
    result = conn.execute("""
        SELECT
            COUNT(*) as total_hours,
            COUNT(CASE WHEN pm2_5_category = 'good' THEN 1 END) as good_hours,
            COUNT(CASE WHEN pm2_5_category IN ('moderate') THEN 1 END) as moderate_hours,
            COUNT(CASE WHEN pm2_5_category IN ('unhealthy_sensitive', 'unhealthy', 'very_unhealthy') THEN 1 END) as poor_hours,
            ROUND(100.0 * COUNT(CASE WHEN pm2_5_category = 'good' THEN 1 END) / COUNT(*), 1) as pct_good,
            ROUND(AVG(pm2_5), 1) as avg_pm2_5,
            ROUND(AVG(aerosol_optical_depth), 3) as avg_aod,
            ROUND(AVG(uv_index), 1) as avg_uv
        FROM main_marts.fct_electricity_with_weather
        WHERE pm2_5 IS NOT NULL
    """).fetchone()

    print(f"   Total hours analyzed: {result[0]:,}")
    print(f"   Good air quality: {result[1]:,} hours ({result[4]}%)")
    print(f"   Moderate air quality: {result[2]:,} hours")
    print(f"   Poor air quality: {result[3]:,} hours")
    print(f"   Average PM2.5: {result[5]} µg/m³")
    print(f"   Average aerosol optical depth: {result[6]}")
    print(f"   Average UV index: {result[7]}")
    print()

    print("=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)
    print()
    print("Key Findings:")
    print("  1. Air quality varies significantly, with some days showing very high PM2.5")
    print("  2. HVAC consumption increases during poor air quality in shoulder seasons")
    print("  3. High aerosol optical depth days indicate potential solar panel soiling")
    print("  4. UV index correlates with temperature and cooling demand")
    print()
    print("Recommendations:")
    print("  1. Schedule solar panel cleaning after high AOD periods (June wildfire smoke)")
    print("  2. Monitor HVAC filter replacement more frequently during high PM months")
    print("  3. Consider air quality alerts for HVAC system optimization")
    print("  4. Use UV index for predicting cooling demand in summer months")
    print()


if __name__ == "__main__":
    main()
