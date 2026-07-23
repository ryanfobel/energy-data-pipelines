"""dlt source for utility-bill-scraper monthly aggregated data.

Loads monthly electricity and gas consumption data from utility-bill-scraper
CSV exports. This complements hourly Green Button data with historical monthly
aggregates that include TOU breakdowns.

Data format (electricity.csv):
  - Date: Month end date
  - Total: Total cost
  - Off/Mid/On Peak Consumption: kWh by TOU period
  - Off/Mid/On Peak Rate: $/kWh rates
  - Total Consumption: Total kWh

Data format (gas.csv):
  - Date: Month end date
  - Gas Charges: Monthly gas cost
  - Gas Consumption: m³
  - Water Charges: Monthly water cost
  - Water Consumption: m³

Usage:
  import dlt
  from pipelines.canada.ontario.utility_bill_scraper import utility_bill_scraper_source

  pipeline = dlt.pipeline(
      pipeline_name="green_button",
      destination="duckdb",
      dataset_name="raw"
  )

  data = utility_bill_scraper_source(
      electricity_csv="/path/to/electricity.csv",
      gas_csv="/path/to/gas.csv",
      home_id="my-home-001"
  )

  info = pipeline.run(data)
"""
from __future__ import annotations

import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator, Optional

import dlt


@dlt.source(name="utility_bill_scraper")
def utility_bill_scraper_source(
    electricity_csv: Optional[str | Path] = None,
    gas_csv: Optional[str | Path] = None,
    home_id: str = "default-home",
) -> list:
    """Load utility bill scraper data.

    Args:
        electricity_csv: Path to electricity.csv file
        gas_csv: Path to gas.csv file
        home_id: Unique home identifier

    Returns:
        List of dlt resources
    """
    resources = []

    if electricity_csv:
        resources.append(
            electricity_monthly_readings(
                csv_file_path=electricity_csv,
                home_id=home_id,
            )
        )

    if gas_csv:
        resources.append(
            gas_monthly_readings(
                csv_file_path=gas_csv,
                home_id=home_id,
            )
        )

    return resources


@dlt.resource(
    name="utility_bill_monthly_electricity",
    write_disposition="merge",
    primary_key=["home_id", "month_end_date"],
)
def electricity_monthly_readings(
    csv_file_path: str | Path,
    home_id: str,
) -> Iterator[dict]:
    """Parse electricity CSV and yield monthly aggregated readings.

    Yields:
        dict with fields:
            - home_id: str
            - month_end_date: date
            - total_kwh: float
            - off_peak_kwh: float
            - mid_peak_kwh: float
            - on_peak_kwh: float
            - total_cost: float
            - off_peak_rate: float
            - mid_peak_rate: float
            - on_peak_rate: float
    """
    csv_path = Path(csv_file_path)

    if not csv_path.exists():
        raise FileNotFoundError(f"Electricity CSV not found: {csv_path}")

    print(f"Utility Bill Scraper: Parsing {csv_path.name}")

    total_months = 0

    with open(csv_path, "r") as f:
        reader = csv.DictReader(f)

        for row in reader:
            try:
                # Parse date (YYYY-MM-DD format)
                date = datetime.strptime(row["Date"], "%Y-%m-%d").date()

                record = {
                    "home_id": home_id,
                    "month_end_date": date,
                    "total_kwh": float(row["Total Consumption"]),
                    "off_peak_kwh": float(row["Off Peak Consumption"]),
                    "mid_peak_kwh": float(row["Mid Peak Consumption"]),
                    "on_peak_kwh": float(row["On Peak Consumption"]),
                    "total_cost": float(row["Total"]),
                    "off_peak_rate": float(row["Off Peak Rate"]),
                    "mid_peak_rate": float(row["Mid Peak Rate"]),
                    "on_peak_rate": float(row["On Peak Rate"]),
                }

                yield record
                total_months += 1

            except (ValueError, KeyError) as e:
                print(f"  WARNING: Skipping row due to error: {e}")
                continue

    print(f"  Loaded {total_months} months of electricity data")


@dlt.resource(
    name="utility_bill_monthly_gas",
    write_disposition="merge",
    primary_key=["home_id", "month_end_date"],
)
def gas_monthly_readings(
    csv_file_path: str | Path,
    home_id: str,
) -> Iterator[dict]:
    """Parse gas CSV and yield monthly aggregated readings.

    Yields:
        dict with fields:
            - home_id: str
            - month_end_date: date
            - gas_m3: float
            - gas_cost: float
            - water_m3: float (if available)
            - water_cost: float (if available)
    """
    csv_path = Path(csv_file_path)

    if not csv_path.exists():
        raise FileNotFoundError(f"Gas CSV not found: {csv_path}")

    print(f"Utility Bill Scraper: Parsing {csv_path.name}")

    total_months = 0

    with open(csv_path, "r") as f:
        reader = csv.DictReader(f)

        for row in reader:
            try:
                # Parse date
                date = datetime.strptime(row["Date"], "%Y-%m-%d").date()

                record = {
                    "home_id": home_id,
                    "month_end_date": date,
                    "gas_m3": float(row["Gas Consumption"]),
                    "gas_cost": float(row["Gas Charges"]),
                }

                # Add water if available
                if "Water Consumption" in row and row["Water Consumption"]:
                    record["water_m3"] = float(row["Water Consumption"])
                if "Water Charges" in row and row["Water Charges"]:
                    record["water_cost"] = float(row["Water Charges"])

                yield record
                total_months += 1

            except (ValueError, KeyError) as e:
                print(f"  WARNING: Skipping row due to error: {e}")
                continue

    print(f"  Loaded {total_months} months of gas data")
