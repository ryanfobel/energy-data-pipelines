"""dlt source for Home Assistant power monitoring data.

Loads power monitoring data from Home Assistant (via InfluxDB or direct parquet export)
into DuckDB for downstream processing.

Data flow:
  1. Read power monitoring data (parquet or InfluxDB query result)
  2. Validate measurements (watts >= 0, reasonable ranges)
  3. Load to DuckDB with merge disposition (idempotent)

Supports:
  - Real-time power monitoring (1-60 second intervals)
  - Multiple devices per home (Emporia Vue, IoTaWatt, Shelly)
  - Multiple channels per device (circuits, phases)
  - Incremental sync (only load new data)

Usage:
  import dlt
  from pipelines.home_assistant import home_assistant_source

  # From parquet file
  pipeline = dlt.pipeline(
      pipeline_name="home_assistant",
      destination="duckdb",
      dataset_name="raw"
  )

  data = home_assistant_source(
      parquet_file="/path/to/data.parquet"
  )

  info = pipeline.run(data)
"""
from __future__ import annotations

from pathlib import Path
from typing import Iterator, Optional
from datetime import datetime, timezone

import dlt
import pandas as pd


@dlt.source(name="home_assistant")
def home_assistant_source(
    parquet_file: Optional[str | Path] = None,
) -> dlt.SourceReference:
    """Load Home Assistant power monitoring data from parquet.

    Args:
        parquet_file: Path to parquet file with power monitoring data.
                     If None, will try to load from config.

    Returns:
        dlt.SourceReference with power_monitoring resource
    """
    # If no file specified, try to load from config
    if parquet_file is None:
        try:
            from pipelines.config import get_config
            config = get_config()

            if not config['home_assistant']['enabled']:
                raise ValueError(
                    "Home Assistant pipeline is disabled in config. "
                    "Set home_assistant.enabled=true in config.local.yml"
                )

            parquet_file = config['home_assistant'].get('parquet_file')
            if not parquet_file:
                raise ValueError(
                    "No parquet_file specified and none found in config. "
                    "Either pass parquet_file parameter or set home_assistant.parquet_file in config"
                )
        except Exception as e:
            raise ValueError(
                f"Failed to load parquet_file from config: {e}. "
                "Either pass parquet_file parameter or configure in config.local.yml"
            )

    return power_monitoring(parquet_file=parquet_file)


@dlt.resource(
    name="power_monitoring",
    write_disposition="merge",
    primary_key=["home_id", "device_id", "channel", "timestamp"],
)
def power_monitoring(
    parquet_file: str | Path,
    last_timestamp: dlt.sources.incremental[datetime] = dlt.sources.incremental(
        "timestamp",
        initial_value=datetime(2020, 1, 1, tzinfo=timezone.utc),
    ),
) -> Iterator[dict]:
    """Load power monitoring data with incremental sync.

    Each row represents one power measurement (typically 1-60 seconds).

    Yields:
        dict with fields:
            - home_id: str - Unique home identifier
            - device_id: str - Device identifier (e.g., "emporia_vue_main")
            - channel: int - Channel number (0 for whole-home, 1+ for circuits)
            - channel_name: str - Human-readable channel name
            - timestamp: datetime - Measurement timestamp (UTC)
            - watts: float - Instantaneous power (W)
            - volts: float - Voltage (V)
            - amps: float - Current (A)
            - power_factor: float - Power factor (0-1)
    """
    file_path = Path(parquet_file)

    if not file_path.exists():
        raise FileNotFoundError(f"Parquet file not found: {file_path}")

    print(f"Home Assistant: Loading {file_path.name}")

    # Read parquet file
    df = pd.read_parquet(file_path)

    # Filter to only new data (incremental)
    if last_timestamp.start_value:
        df = df[df["timestamp"] > last_timestamp.start_value]

    if df.empty:
        print("  No new data to load")
        return

    print(f"  Found {len(df):,} new records")
    print(f"  Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")

    # Validate data
    invalid_watts = (df["watts"] < 0).sum()
    if invalid_watts > 0:
        print(f"  WARNING: {invalid_watts} records with negative watts (will be filtered)")
        df = df[df["watts"] >= 0]

    # Check for unreasonably high values (> 50kW)
    high_watts = (df["watts"] > 50000).sum()
    if high_watts > 0:
        print(f"  WARNING: {high_watts} records with watts > 50kW (potential data quality issue)")

    # Yield records
    for record in df.to_dict(orient="records"):
        # Ensure timestamp is timezone-aware
        if isinstance(record["timestamp"], pd.Timestamp):
            ts = record["timestamp"].to_pydatetime()
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            record["timestamp"] = ts

        yield record

    print(f"  Loaded {len(df):,} valid records")
