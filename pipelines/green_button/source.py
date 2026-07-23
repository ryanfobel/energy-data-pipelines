"""dlt source for Green Button ESPI XML data.

Parses Green Button (ESPI) XML files from Ontario utilities and loads
interval readings into DuckDB for downstream processing.

Data flow:
  1. Parse ESPI XML using greenbutton_objects library
  2. Extract interval readings (timestamp, kWh, cost, quality, TOU)
  3. Load to DuckDB with merge disposition (idempotent)

Supports:
  - Hourly electricity interval data (Hydro One, Elexicon, etc.)
  - Monthly natural gas data (Enbridge)
  - Multiple usage points per file (multi-meter homes)
  - Multiple meter readings per usage point

Usage:
  import dlt
  from pipelines.green_button import green_button_source

  # Parse single file
  pipeline = dlt.pipeline(
      pipeline_name="green_button",
      destination="duckdb",
      dataset_name="raw"
  )

  data = green_button_source(
      xml_file_path="/path/to/greenbutton.xml",
      home_id="beads-abc123"
  )

  info = pipeline.run(data)
  print(info)
"""
from __future__ import annotations

from datetime import timezone
from pathlib import Path
from typing import Iterator, Optional

import dlt
from greenbutton_objects.parse import parse_feed


@dlt.source(name="green_button")
def green_button_source(
    xml_file_path: str | Path,
    home_id: str,
) -> dlt.SourceReference:
    """Parse Green Button ESPI XML file and return dlt source.

    Args:
        xml_file_path: Path to Green Button XML file
        home_id: Unique home identifier (UUID or beads ID)

    Returns:
        dlt.SourceReference with interval_readings resource
    """
    return green_button_interval_readings(
        xml_file_path=xml_file_path,
        home_id=home_id,
    )


@dlt.resource(
    name="green_button_interval_readings",
    write_disposition="merge",
    primary_key=["home_id", "usage_point_idx", "meter_reading_idx", "timestamp"],
)
def green_button_interval_readings(
    xml_file_path: str | Path,
    home_id: str,
) -> Iterator[dict]:
    """Parse Green Button XML and yield interval readings.

    Each row represents one interval reading (typically 1 hour).

    Yields:
        dict with fields:
            - home_id: str - Unique home identifier
            - usage_point_idx: int - Index of usage point (0 for single-meter homes)
            - meter_reading_idx: int - Index of meter reading
            - timestamp: datetime - Interval start time (UTC)
            - duration_seconds: int - Interval duration (3600 for hourly)
            - kwh: float - Energy consumption (kWh or m³ for gas)
            - raw_value: int - Original value before scaling
            - cost: float|None - Cost in cents (if available)
            - quality_code: str - ESPI quality code (VALIDATED, ESTIMATED, etc.)
            - tou_bucket: str|None - Time-of-use bucket (1=on, 2=mid, 3=off)
            - commodity: str - Commodity type (electricity, gas)
            - uom: str - Unit of measure
            - meter_id: str|None - Meter identifier from usage point URI
    """
    xml_path = Path(xml_file_path)

    if not xml_path.exists():
        raise FileNotFoundError(f"Green Button XML file not found: {xml_path}")

    print(f"Green Button: Parsing {xml_path.name}")

    # Parse XML using greenbutton_objects
    feed = parse_feed(xml_path)
    usage_points = feed.usage_points if hasattr(feed, 'usage_points') else []

    if not usage_points:
        print(f"  WARNING: No usage points found in {xml_path.name}")
        return

    print(f"  Found {len(usage_points)} usage point(s)")

    total_readings = 0

    for up_idx, usage_point in enumerate(usage_points):
        # Get meter ID from URI if available
        meter_id = None
        if hasattr(usage_point, 'uri') and usage_point.uri:
            # Extract last part of URI as meter ID
            meter_id = usage_point.uri.split('/')[-1]

        # Get service kind
        service_kind = None
        if hasattr(usage_point, 'service_kind'):
            service_kind = str(usage_point.service_kind)

        # Get meter readings
        if not hasattr(usage_point, 'meter_readings'):
            continue

        meter_readings = usage_point.meter_readings
        print(f"    UsagePoint {up_idx}: {len(meter_readings)} meter reading(s)")

        for mr_idx, meter_reading in enumerate(meter_readings):
            # Get interval readings
            if not hasattr(meter_reading, 'interval_readings'):
                continue

            interval_readings = meter_reading.interval_readings

            # Get reading type metadata
            reading_type = None
            commodity = None
            uom = None
            multiplier_value = 0

            if hasattr(meter_reading, 'reading_type'):
                reading_type = meter_reading.reading_type

                if hasattr(reading_type, 'commodity'):
                    commodity = str(reading_type.commodity)

                if hasattr(reading_type, 'uom'):
                    uom = str(reading_type.uom)

                if hasattr(reading_type, 'power_of_ten_multiplier'):
                    mult = reading_type.power_of_ten_multiplier
                    multiplier_value = mult.value if hasattr(mult, 'value') else int(mult)

            # Process each interval reading
            for interval_reading in interval_readings:
                record = {
                    'home_id': home_id,
                    'usage_point_idx': up_idx,
                    'meter_reading_idx': mr_idx,
                }

                # Add meter ID if available
                if meter_id:
                    record['meter_id'] = meter_id

                # Get timestamp (convert to UTC)
                if hasattr(interval_reading, 'start'):
                    ts = interval_reading.start
                    # greenbutton_objects returns naive datetime, add UTC timezone
                    if ts.tzinfo is None:
                        ts = ts.replace(tzinfo=timezone.utc)
                    record['timestamp'] = ts

                # Get duration
                if hasattr(interval_reading, 'time_period'):
                    tp = interval_reading.time_period
                    if hasattr(tp, 'duration'):
                        record['duration_seconds'] = tp.duration

                # Get raw value and apply scaling
                if hasattr(interval_reading, 'raw_value') and interval_reading.raw_value is not None:
                    raw_value = int(interval_reading.raw_value)
                    record['raw_value'] = raw_value
                    record['kwh'] = raw_value * (10 ** multiplier_value)

                # Get cost
                if hasattr(interval_reading, 'cost'):
                    cost = interval_reading.cost
                    # Convert to float, handle empty strings
                    if cost and str(cost).strip():
                        record['cost'] = float(cost)

                # Get quality code
                if hasattr(interval_reading, 'quality_of_reading'):
                    record['quality_code'] = str(interval_reading.quality_of_reading)

                # Get TOU bucket
                if hasattr(interval_reading, 'tou'):
                    record['tou_bucket'] = str(interval_reading.tou)

                # Add metadata
                record['commodity'] = commodity
                record['uom'] = uom
                record['service_kind'] = service_kind

                # Only yield if we have required fields
                if 'timestamp' in record and 'kwh' in record:
                    yield record
                    total_readings += 1

    print(f"  Total interval readings extracted: {total_readings}")


# Convenience function for parsing multiple files
def parse_multiple_files(
    xml_files: list[str | Path],
    home_id: str,
) -> Iterator[dict]:
    """Parse multiple Green Button XML files for the same home.

    Args:
        xml_files: List of paths to Green Button XML files
        home_id: Unique home identifier

    Yields:
        Interval reading dicts from all files
    """
    for xml_file in xml_files:
        yield from green_button_interval_readings(xml_file, home_id)
