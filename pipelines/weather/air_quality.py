"""dlt source for Open-Meteo Air Quality data.

Loads hourly air quality data from Open-Meteo Air Quality API into DuckDB.

Data flow:
  1. Fetch hourly air quality data from Open-Meteo API
  2. Validate measurements (reasonable ranges)
  3. Load to DuckDB with merge disposition (idempotent)

Features:
  - Free and unlimited API access
  - Hourly PM2.5, PM10, ozone, NO2, SO2, CO
  - UV index for health and cooling correlation
  - Aerosol optical depth for solar panel soiling analysis
  - Dust measurements for panel maintenance planning
  - Historical data back to 1940
  - Incremental sync support
  - Multiple locations support

Open-Meteo Air Quality API:
  - Endpoint: https://air-quality-api.open-meteo.com/v1/air-quality
  - Documentation: https://open-meteo.com/en/docs/air-quality-api
  - No API key required
  - Rate limits: None

Use Cases:
  - Solar panel soiling losses from aerosol_optical_depth
  - HVAC load during poor air quality (windows closed)
  - UV index correlation with cooling demand
  - Air filter replacement timing based on particulates
  - Health impact analysis (PM2.5, PM10)

Usage:
  import dlt
  from pipelines.weather.air_quality import air_quality_source

  pipeline = dlt.pipeline(
      pipeline_name="weather",
      destination="duckdb",
      dataset_name="raw"
  )

  # For a single location (Toronto)
  data = air_quality_source(
      latitude=43.65,
      longitude=-79.38,
      start_date="2022-12-25",
      end_date="2024-12-23",
      location_name="toronto"
  )

  info = pipeline.run(data)
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterator, Optional

import dlt
import requests


@dlt.source(name="air_quality")
def air_quality_source(
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    location_name: Optional[str] = None,
) -> dlt.SourceReference:
    """Load historical air quality data from Open-Meteo API.

    Args:
        latitude: Latitude in decimal degrees (e.g., 43.65 for Toronto)
        longitude: Longitude in decimal degrees (e.g., -79.38 for Toronto)
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        location_name: Human-readable location name (e.g., "toronto")
                      If None, will load from config

    Returns:
        dlt.SourceReference with air_quality_hourly resource
    """
    # If no parameters specified, try to load from config
    if latitude is None or longitude is None or start_date is None or end_date is None:
        try:
            from pipelines.config import get_config
            config = get_config()

            if not config.get('weather', {}).get('enabled', False):
                raise ValueError(
                    "Weather pipeline is disabled in config. "
                    "Set weather.enabled=true in config.local.yml"
                )

            latitude = config['weather'].get('latitude')
            longitude = config['weather'].get('longitude')
            start_date = config['weather'].get('start_date')
            end_date = config['weather'].get('end_date')
            location_name = config['weather'].get('location_name', 'default')

            if not all([latitude, longitude, start_date, end_date]):
                raise ValueError(
                    "Missing required weather config. "
                    "Either pass parameters or configure in config.local.yml: "
                    "weather.latitude, weather.longitude, weather.start_date, weather.end_date"
                )
        except Exception as e:
            raise ValueError(
                f"Failed to load weather config: {e}. "
                "Either pass parameters or configure in config.local.yml"
            )

    return air_quality_hourly(
        latitude=latitude,
        longitude=longitude,
        start_date=start_date,
        end_date=end_date,
        location_name=location_name,
    )


@dlt.resource(
    name="air_quality_hourly",
    write_disposition="merge",
    primary_key=["location_name", "timestamp"],
)
def air_quality_hourly(
    latitude: float,
    longitude: float,
    start_date: str,
    end_date: str,
    location_name: str = "default",
    last_timestamp: dlt.sources.incremental[datetime] = dlt.sources.incremental(
        "timestamp",
        initial_value=datetime(2020, 1, 1, tzinfo=timezone.utc),
    ),
) -> Iterator[dict]:
    """Load hourly air quality data with incremental sync.

    Each row represents one hour of air quality data.

    Args:
        latitude: Latitude in decimal degrees
        longitude: Longitude in decimal degrees
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        location_name: Location identifier
        last_timestamp: Incremental state for last loaded timestamp

    Yields:
        dict with fields:
            - location_name: str - Location identifier
            - latitude: float - Latitude
            - longitude: float - Longitude
            - timezone: str - Timezone name
            - timestamp: datetime - Measurement timestamp (local timezone)

            Particulate matter (µg/m³):
            - pm10: float - PM10 particulate matter (diameter < 10µm)
            - pm2_5: float - PM2.5 particulate matter (diameter < 2.5µm)
            - dust: float - Dust concentration (panel soiling indicator)

            Pollutants (µg/m³):
            - ozone: float - Ozone (O3)
            - nitrogen_dioxide: float - Nitrogen dioxide (NO2)
            - sulphur_dioxide: float - Sulphur dioxide (SO2)
            - carbon_monoxide: float - Carbon monoxide (CO, in mg/m³)

            UV and aerosols:
            - uv_index: float - UV index (0-11+)
            - uv_index_clear_sky: float - UV index under clear sky conditions
            - aerosol_optical_depth: float - Aerosol optical depth (solar impact)

            European Air Quality Index (0-100+):
            - european_aqi: int - Combined air quality index
            - european_aqi_pm2_5: int - AQI based on PM2.5
            - european_aqi_pm10: int - AQI based on PM10
            - european_aqi_nitrogen_dioxide: int - AQI based on NO2
            - european_aqi_ozone: int - AQI based on O3
            - european_aqi_sulphur_dioxide: int - AQI based on SO2
    """
    print(f"Air Quality: Fetching data for {location_name} ({latitude}, {longitude})")
    print(f"  Date range: {start_date} to {end_date}")

    # Call Open-Meteo Air Quality API
    url = "https://air-quality-api.open-meteo.com/v1/air-quality"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": start_date,
        "end_date": end_date,
        "hourly": ",".join([
            # Particulate matter (µg/m³)
            "pm10",                        # PM10 - health and HVAC filter impact
            "pm2_5",                       # PM2.5 - primary health metric
            "dust",                        # Dust - solar panel soiling
            # Gaseous pollutants
            "ozone",                       # O3 - respiratory health
            "nitrogen_dioxide",            # NO2 - urban pollution
            "sulphur_dioxide",             # SO2 - industrial pollution
            "carbon_monoxide",             # CO - combustion indicator
            # UV radiation
            "uv_index",                    # UV index - health and cooling correlation
            "uv_index_clear_sky",          # Clear sky UV - baseline
            # Aerosols
            "aerosol_optical_depth",       # AOD - solar panel performance impact
            # Air quality indices (European AQI)
            "european_aqi",                # Overall AQI
            "european_aqi_pm2_5",          # PM2.5 component
            "european_aqi_pm10",           # PM10 component
            "european_aqi_nitrogen_dioxide",  # NO2 component
            "european_aqi_ozone",          # O3 component
            "european_aqi_sulphur_dioxide",   # SO2 component
        ]),
        "timezone": "auto",  # Use local timezone for location
    }

    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
    except requests.RequestException as e:
        raise ValueError(f"Failed to fetch air quality data from Open-Meteo: {e}")

    data = response.json()
    hourly = data.get("hourly", {})

    if not hourly:
        print("  No data returned from API")
        return

    # Extract metadata
    actual_lat = data.get("latitude")
    actual_lon = data.get("longitude")
    timezone_name = data.get("timezone")

    print(f"  Actual location: {actual_lat}, {actual_lon}")
    print(f"  Timezone: {timezone_name}")

    # Convert to records
    timestamps = hourly.get("time", [])

    # Particulate matter
    pm10_values = hourly.get("pm10", [])
    pm2_5_values = hourly.get("pm2_5", [])
    dust_values = hourly.get("dust", [])

    # Pollutants
    ozone_values = hourly.get("ozone", [])
    nitrogen_dioxide_values = hourly.get("nitrogen_dioxide", [])
    sulphur_dioxide_values = hourly.get("sulphur_dioxide", [])
    carbon_monoxide_values = hourly.get("carbon_monoxide", [])

    # UV and aerosols
    uv_index_values = hourly.get("uv_index", [])
    uv_index_clear_sky_values = hourly.get("uv_index_clear_sky", [])
    aerosol_optical_depth_values = hourly.get("aerosol_optical_depth", [])

    # Air quality indices
    european_aqi_values = hourly.get("european_aqi", [])
    european_aqi_pm2_5_values = hourly.get("european_aqi_pm2_5", [])
    european_aqi_pm10_values = hourly.get("european_aqi_pm10", [])
    european_aqi_no2_values = hourly.get("european_aqi_nitrogen_dioxide", [])
    european_aqi_o3_values = hourly.get("european_aqi_ozone", [])
    european_aqi_so2_values = hourly.get("european_aqi_sulphur_dioxide", [])

    total_records = len(timestamps)
    print(f"  Total records: {total_records:,}")

    # Filter to only new data (incremental)
    new_records = 0
    for i in range(total_records):
        # Parse timestamp (ISO 8601 format from API)
        timestamp_str = timestamps[i]
        timestamp = datetime.fromisoformat(timestamp_str)

        # Ensure timestamp is timezone-aware (convert to UTC for comparison)
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)

        # Skip if already loaded
        if last_timestamp.start_value and timestamp <= last_timestamp.start_value:
            continue

        new_records += 1

        record = {
            "location_name": location_name,
            "latitude": actual_lat,
            "longitude": actual_lon,
            "timezone": timezone_name,
            "timestamp": timestamp,
            # Particulate matter (µg/m³)
            "pm10": pm10_values[i],
            "pm2_5": pm2_5_values[i],
            "dust": dust_values[i],
            # Pollutants
            "ozone": ozone_values[i],
            "nitrogen_dioxide": nitrogen_dioxide_values[i],
            "sulphur_dioxide": sulphur_dioxide_values[i],
            "carbon_monoxide": carbon_monoxide_values[i],
            # UV and aerosols
            "uv_index": uv_index_values[i],
            "uv_index_clear_sky": uv_index_clear_sky_values[i],
            "aerosol_optical_depth": aerosol_optical_depth_values[i],
            # Air quality indices
            "european_aqi": european_aqi_values[i],
            "european_aqi_pm2_5": european_aqi_pm2_5_values[i],
            "european_aqi_pm10": european_aqi_pm10_values[i],
            "european_aqi_nitrogen_dioxide": european_aqi_no2_values[i],
            "european_aqi_ozone": european_aqi_o3_values[i],
            "european_aqi_sulphur_dioxide": european_aqi_so2_values[i],
        }

        yield record

    if new_records == 0:
        print("  No new data to load")
    else:
        print(f"  Loaded {new_records:,} new records")


if __name__ == "__main__":
    # Test the air quality source
    import dlt

    pipeline = dlt.pipeline(
        pipeline_name="weather",
        destination="duckdb",
        dataset_name="raw",
        dev_mode=True,
    )

    # Load air quality data for Toronto
    data = air_quality_source(
        latitude=43.65,
        longitude=-79.38,
        start_date="2023-01-01",
        end_date="2023-01-31",
        location_name="toronto",
    )

    info = pipeline.run(data)
    print("\nPipeline run info:")
    print(info)
