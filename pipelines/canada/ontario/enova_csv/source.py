"""dlt source for Enova Power smart meter CSV data.

Parses Enova Power (formerly Kitchener-Wilmot Hydro) smart meter CSV exports
and converts to the same schema as Green Button data for downstream compatibility.

CSV Format:
  - Wide format: 1 row per day, columns for each hour (1 am - 12 pm)
  - Time-of-use summary columns (on/mid/off peak totals)
  - All times in EST (not EDT) per Enova's note

Data flow:
  1. Parse CSV and pivot from wide to long format
  2. Create hourly interval readings with timestamps
  3. Map to TOU periods based on Ontario electricity pricing
  4. Load to DuckDB with merge disposition (idempotent)

Usage:
  import dlt
  from pipelines.enova_csv import enova_csv_source

  pipeline = dlt.pipeline(
      pipeline_name="green_button",
      destination="duckdb",
      dataset_name="raw"
  )

  data = enova_csv_source(
      csv_file_path="/path/to/SmartMeter.csv",
      home_id="my-home-001"
  )

  info = pipeline.run(data)
"""
from __future__ import annotations

import csv
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Iterator

import dlt


@dlt.source(name="enova_csv")
def enova_csv_source(
    csv_file_path: str | Path,
    home_id: str,
) -> dlt.SourceReference:
    """Parse Enova smart meter CSV file and return dlt source.

    Args:
        csv_file_path: Path to Enova CSV file
        home_id: Unique home identifier (UUID or beads ID)

    Returns:
        dlt.SourceReference with interval_readings resource
    """
    return enova_csv_interval_readings(
        csv_file_path=csv_file_path,
        home_id=home_id,
    )


@dlt.resource(
    name="green_button_interval_readings",  # Same table name as Green Button!
    write_disposition="merge",
    primary_key=["home_id", "usage_point_idx", "meter_reading_idx", "timestamp"],
)
def enova_csv_interval_readings(
    csv_file_path: str | Path,
    home_id: str,
) -> Iterator[dict]:
    """Parse Enova CSV and yield interval readings compatible with Green Button schema.

    Yields:
        dict with fields matching green_button_interval_readings:
            - home_id: str - Unique home identifier
            - usage_point_idx: int - Always 0 (single meter)
            - meter_reading_idx: int - Always 0 (single reading stream)
            - timestamp: datetime - Hour start time (EST, converted to UTC)
            - duration_seconds: int - Always 3600 (hourly)
            - kwh: float - Energy consumption
            - raw_value: int - Scaled raw value (kwh * 1000)
            - cost: None - Not in CSV
            - quality_code: str - "VALIDATED" (estimated if inferred)
            - tou_bucket: str - Time-of-use tier (1=on, 2=mid, 3=off)
            - commodity: str - "CommodityKindValue.VALUE_1" (electricity)
            - uom: str - "UnitSymbolKindValue.VALUE_72" (Wh)
            - service_kind: str - "ServiceKind.ELECTRICITY"
            - meter_id: str - Extracted from filename
    """
    csv_path = Path(csv_file_path)

    if not csv_path.exists():
        raise FileNotFoundError(f"Enova CSV file not found: {csv_path}")

    # Extract meter ID from filename (e.g., SmartMeter8493100000_2026-07-2219.00.36.csv)
    meter_id = None
    if csv_path.name.startswith("SmartMeter"):
        meter_id = csv_path.name.split("_")[0].replace("SmartMeter", "")

    print(f"Enova CSV: Parsing {csv_path.name}")
    if meter_id:
        print(f"  Meter ID: {meter_id}")

    total_readings = 0

    with open(csv_path, "r") as f:
        reader = csv.DictReader(f)

        for row in reader:
            # Skip empty rows or footer notes
            if not row.get("Reading Date") or row["Reading Date"].startswith("*"):
                continue

            reading_date = row["Reading Date"]

            # Parse date (format: YYYY-MM-DD)
            try:
                date = datetime.strptime(reading_date, "%Y-%m-%d")
            except ValueError:
                print(f"  WARNING: Could not parse date: {reading_date}")
                continue

            # Process each hour (1 am through 12 pm/midnight)
            hour_columns = [
                ("1 am kWh Usage", 1),
                ("2 am kWh Usage", 2),
                ("3 am kWh Usage", 3),
                ("4 am kWh Usage", 4),
                ("5 am kWh Usage", 5),
                ("6 am kWh Usage", 6),
                ("7 am kWh Usage", 7),
                ("8 am kWh Usage", 8),
                ("9 am kWh Usage", 9),
                ("10 am kWh Usage", 10),
                ("11 am kWh Usage", 11),
                ("12 pm kWh Usage", 12),  # Noon
                ("1 pm kWh Usage", 13),
                ("2 pm kWh Usage", 14),
                ("3 pm kWh Usage", 15),
                ("4 pm kWh Usage", 16),
                ("5 pm kWh Usage", 17),
                ("6 pm kWh Usage", 18),
                ("7 pm kWh Usage", 19),
                ("8 pm kWh Usage", 20),
                ("9 pm kWh Usage", 21),
                ("10 pm kWh Usage", 22),
                ("11 pm kWh Usage", 23),
                ("12 pm kWh Usage", 0),  # Midnight (start of next day)
            ]

            for col_name, hour in hour_columns:
                kwh_str = row.get(col_name, "").strip()

                # Skip empty or missing values
                if not kwh_str:
                    continue

                try:
                    kwh = float(kwh_str)
                except (ValueError, TypeError):
                    continue

                # Create timestamp for this hour (EST, as noted in CSV footer)
                # EST is UTC-5 (no daylight saving adjustment per Enova's note)
                timestamp = datetime(
                    date.year,
                    date.month,
                    date.day,
                    hour,
                    0,
                    0,
                    tzinfo=timezone(timedelta(hours=-5))  # EST
                )

                # Convert to UTC for storage
                timestamp_utc = timestamp.astimezone(timezone.utc)

                # Determine TOU bucket based on Ontario TOU schedule
                # Summer (May-Oct): On-peak 11am-5pm weekdays
                # Winter (Nov-Apr): On-peak 7am-11am and 5pm-7pm weekdays
                # Mid-peak: Shoulder hours on weekdays
                # Off-peak: Nights, weekends, holidays
                tou_bucket = get_ontario_tou_bucket(timestamp)

                # Build record matching Green Button schema
                record = {
                    "home_id": home_id,
                    "usage_point_idx": 0,
                    "meter_reading_idx": 0,
                    "timestamp": timestamp_utc,
                    "duration_seconds": 3600,
                    "kwh": kwh,
                    "raw_value": int(kwh * 1000),  # Convert to Wh
                    "cost": None,  # Not in CSV
                    "quality_code": "VALIDATED",
                    "tou_bucket": str(tou_bucket),
                    "commodity": "CommodityKindValue.VALUE_1",  # Electricity
                    "uom": "UnitSymbolKindValue.VALUE_72",  # Wh
                    "service_kind": "ServiceKind.ELECTRICITY",
                }

                if meter_id:
                    record["meter_id"] = meter_id

                yield record
                total_readings += 1

    print(f"  Total interval readings extracted: {total_readings}")


def get_ontario_tou_bucket(timestamp: datetime) -> int:
    """Determine Ontario TOU bucket for a given timestamp.

    Args:
        timestamp: Datetime in EST/EDT

    Returns:
        1 (on-peak), 2 (mid-peak), or 3 (off-peak)

    Ontario TOU Schedule (simplified - doesn't include holidays):
    - Summer (May 1 - Oct 31):
        - On-peak: 11am-5pm weekdays
        - Mid-peak: 7am-11am and 5pm-7pm weekdays
        - Off-peak: All other times
    - Winter (Nov 1 - Apr 30):
        - On-peak: 7am-11am and 5pm-7pm weekdays
        - Mid-peak: 11am-5pm weekdays
        - Off-peak: All other times
    """
    # Weekend = off-peak
    if timestamp.weekday() >= 5:  # Saturday=5, Sunday=6
        return 3

    month = timestamp.month
    hour = timestamp.hour

    # Summer schedule (May-Oct)
    if 5 <= month <= 10:
        if 11 <= hour < 17:  # 11am-5pm
            return 1  # On-peak
        elif (7 <= hour < 11) or (17 <= hour < 19):  # 7-11am or 5-7pm
            return 2  # Mid-peak
        else:
            return 3  # Off-peak

    # Winter schedule (Nov-Apr)
    else:
        if (7 <= hour < 11) or (17 <= hour < 19):  # 7-11am or 5-7pm
            return 1  # On-peak
        elif 11 <= hour < 17:  # 11am-5pm
            return 2  # Mid-peak
        else:
            return 3  # Off-peak
