#!/usr/bin/env python3
"""Generate mock Home Assistant power monitoring data for testing.

Simulates data from devices like Emporia Vue, IoTaWatt, or Shelly EM.
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone
from pathlib import Path


def generate_power_monitoring_data(
    home_id: str = "test-home-001",
    device_count: int = 2,
    start_date: datetime = None,
    days: int = 7,
    interval_seconds: int = 10,  # 10-second intervals (common for power monitors)
) -> pd.DataFrame:
    """Generate realistic power monitoring data.

    Simulates:
    - Emporia Vue 3 (whole-home + 16 circuits)
    - IoTaWatt (14 channels)
    - Shelly EM (2 channels)

    Args:
        home_id: Unique home identifier
        device_count: Number of monitoring devices
        start_date: Start datetime (default: 7 days ago)
        days: Number of days to generate
        interval_seconds: Seconds between readings

    Returns:
        DataFrame with power monitoring data
    """
    if start_date is None:
        start_date = datetime.now(timezone.utc) - timedelta(days=days)

    # Generate timestamps
    intervals_per_day = (24 * 3600) // interval_seconds
    total_intervals = days * intervals_per_day

    timestamps = [
        start_date + timedelta(seconds=i * interval_seconds)
        for i in range(total_intervals)
    ]

    records = []

    # Device types and their channels
    devices = [
        {
            "device_id": "emporia_vue_main",
            "device_name": "Emporia Vue 3",
            "channels": [
                {"channel": 0, "name": "Whole Home", "base_watts": 1500, "variation": 800},
                {"channel": 1, "name": "HVAC", "base_watts": 2000, "variation": 1500},
                {"channel": 2, "name": "Water Heater", "base_watts": 400, "variation": 3500},  # Cycles on/off
                {"channel": 3, "name": "Kitchen", "base_watts": 150, "variation": 200},
                {"channel": 4, "name": "Living Room", "base_watts": 100, "variation": 150},
                {"channel": 5, "name": "Bedrooms", "base_watts": 50, "variation": 100},
            ]
        },
        {
            "device_id": "iotawatt_001",
            "device_name": "IoTaWatt",
            "channels": [
                {"channel": 0, "name": "Main 1", "base_watts": 800, "variation": 400},
                {"channel": 1, "name": "Main 2", "base_watts": 700, "variation": 300},
                {"channel": 2, "name": "Dryer", "base_watts": 100, "variation": 4500},
                {"channel": 3, "name": "Stove", "base_watts": 50, "variation": 2500},
            ]
        }
    ]

    # Limit to requested device count
    devices = devices[:device_count]

    for device in devices:
        for channel_info in device["channels"]:
            channel = channel_info["channel"]
            base_watts = channel_info["base_watts"]
            variation = channel_info["variation"]

            # Generate realistic power patterns
            np.random.seed(hash(f"{device['device_id']}-{channel}") % 2**32)

            for ts in timestamps:
                hour = ts.hour

                # Time-of-day patterns
                if 0 <= hour < 6:
                    multiplier = 0.3  # Night (low usage)
                elif 6 <= hour < 9:
                    multiplier = 0.8  # Morning (medium)
                elif 9 <= hour < 17:
                    multiplier = 0.5  # Day (low-medium)
                elif 17 <= hour < 22:
                    multiplier = 1.0  # Evening (high)
                else:
                    multiplier = 0.6  # Late evening

                # Add random variation
                watts = max(0, base_watts * multiplier + np.random.normal(0, variation * 0.3))

                # Simulate on/off cycles for some devices (water heater, dryer)
                if channel_info["name"] in ["Water Heater", "Dryer", "Stove"]:
                    if np.random.random() > 0.9:  # 10% chance of being on
                        watts += variation

                # Calculate derived values
                volts = 120.0 + np.random.normal(0, 2)  # Standard US voltage with variation
                amps = watts / volts if volts > 0 else 0
                pf = 0.85 + np.random.normal(0, 0.05)  # Power factor
                pf = np.clip(pf, 0.7, 1.0)

                record = {
                    "home_id": home_id,
                    "device_id": device["device_id"],
                    "channel": channel,
                    "channel_name": channel_info["name"],
                    "timestamp": ts,
                    "watts": round(watts, 2),
                    "volts": round(volts, 2),
                    "amps": round(amps, 3),
                    "power_factor": round(pf, 3),
                }

                records.append(record)

    df = pd.DataFrame(records)
    df = df.sort_values(["device_id", "channel", "timestamp"]).reset_index(drop=True)

    print(f"Generated {len(df):,} power monitoring records")
    print(f"  Home: {home_id}")
    print(f"  Devices: {len(devices)}")
    print(f"  Channels: {sum(len(d['channels']) for d in devices)}")
    print(f"  Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
    print(f"  Total readings: {len(df):,}")

    return df


def main():
    """Generate mock data and save to parquet."""
    output_dir = Path("mock_data")
    output_dir.mkdir(exist_ok=True)

    # Generate 7 days of 10-second interval data
    df = generate_power_monitoring_data(
        home_id="test-home-001",
        device_count=2,
        days=7,
        interval_seconds=10
    )

    # Save to parquet
    output_file = output_dir / "home_assistant_power_monitoring.parquet"
    df.to_parquet(output_file, index=False)

    print(f"\n✓ Saved to {output_file}")
    print(f"  Size: {output_file.stat().st_size / 1024 / 1024:.2f} MB")

    # Show statistics
    print(f"\n  Statistics by device:")
    summary = df.groupby(["device_id", "channel", "channel_name"]).agg({
        "watts": ["mean", "min", "max"],
        "timestamp": "count"
    }).round(2)
    print(summary)


if __name__ == "__main__":
    main()
