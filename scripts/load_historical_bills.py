#!/usr/bin/env python3
"""Load historical monthly bill data from utility-bill-scraper."""
import dlt
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pipelines.canada.ontario.utility_bill_scraper import utility_bill_scraper_source


def load_historical_data():
    """Load historical utility bill data from CSV files."""

    # Path to utility-bill-scraper data
    scraper_data = Path("/Users/ryan/dev/utility-bill-scraper/notebooks/features/case_study_data")

    electricity_csv = scraper_data / "electricity.csv"
    gas_csv = scraper_data / "gas.csv"

    if not electricity_csv.exists():
        print(f"Error: {electricity_csv} not found")
        return

    if not gas_csv.exists():
        print(f"Error: {gas_csv} not found")
        return

    print("Loading historical utility bill data...")
    print(f"  Electricity: {electricity_csv}")
    print(f"  Gas: {gas_csv}")
    print()

    # Create pipeline (same as green_button for combined storage)
    pipeline = dlt.pipeline(
        pipeline_name="green_button",
        destination="duckdb",
        dataset_name="raw",
        dev_mode=False,
    )

    # Load data
    data = utility_bill_scraper_source(
        electricity_csv=electricity_csv,
        gas_csv=gas_csv,
        home_id="ryan-home-001"
    )

    info = pipeline.run(data)

    print("\n" + "="*60)
    print("Historical data loaded successfully!")
    print(f"  DuckDB: {pipeline.pipelines_dir}/green_button.duckdb")

    # Show stats
    with pipeline.sql_client() as client:
        # Electricity stats
        with client.execute_query("""
            SELECT
                COUNT(*) as months,
                MIN(month_end_date) as first_month,
                MAX(month_end_date) as last_month,
                ROUND(SUM(total_kwh), 1) as total_kwh,
                ROUND(SUM(total_cost), 2) as total_cost
            FROM utility_bill_monthly_electricity
            WHERE home_id = 'ryan-home-001'
        """) as cursor:
            row = cursor.fetchone()
            print(f"\n  Electricity (monthly aggregates):")
            print(f"    Months: {row[0]}")
            print(f"    Period: {row[1]} to {row[2]}")
            print(f"    Total consumption: {row[3]:,.1f} kWh")
            print(f"    Total cost: ${row[4]:,.2f}")

        # Gas stats
        with client.execute_query("""
            SELECT
                COUNT(*) as months,
                MIN(month_end_date) as first_month,
                MAX(month_end_date) as last_month,
                ROUND(SUM(gas_m3), 1) as total_m3,
                ROUND(SUM(gas_cost), 2) as total_cost
            FROM utility_bill_monthly_gas
            WHERE home_id = 'ryan-home-001'
        """) as cursor:
            row = cursor.fetchone()
            print(f"\n  Gas (monthly aggregates):")
            print(f"    Months: {row[0]}")
            print(f"    Period: {row[1]} to {row[2]}")
            print(f"    Total consumption: {row[3]:,.1f} m³")
            print(f"    Total cost: ${row[4]:,.2f}")

    print("\n" + "="*60)


if __name__ == "__main__":
    load_historical_data()
