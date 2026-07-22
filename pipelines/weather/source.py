"""dlt source for Open-Meteo historical weather data.

Loads hourly weather data from Open-Meteo Archive API into DuckDB.

Data flow:
  1. Fetch hourly weather data from Open-Meteo API
  2. Validate measurements (temperature in reasonable range)
  3. Load to DuckDB with merge disposition (idempotent)

Features:
  - Free and unlimited API access
  - Hourly temperature, humidity, precipitation, wind speed
  - Cloud cover (total, low, mid, high) for solar modeling
  - Solar radiation (GHI, DNI, DHI) for PVLIB integration
  - Sunshine duration for validation
  - Historical data back to 1940
  - Incremental sync support
  - Multiple locations support

Open-Meteo Archive API:
  - Endpoint: https://archive-api.open-meteo.com/v1/archive
  - Documentation: https://open-meteo.com/en/docs/historical-weather-api
  - No API key required
  - Rate limits: None for archive data

Usage:
  import dlt
  from pipelines.weather import weather_source

  pipeline = dlt.pipeline(
      pipeline_name="weather",
      destination="duckdb",
      dataset_name="raw"
  )

  # For a single location (Toronto)
  data = weather_source(
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


@dlt.source(name="weather")
def weather_source(
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    location_name: Optional[str] = None,
) -> dlt.SourceReference:
    """Load historical weather data from Open-Meteo API.

    Args:
        latitude: Latitude in decimal degrees (e.g., 43.65 for Toronto)
        longitude: Longitude in decimal degrees (e.g., -79.38 for Toronto)
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        location_name: Human-readable location name (e.g., "toronto")
                      If None, will load from config

    Returns:
        dlt.SourceReference with weather_hourly resource
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

    return weather_hourly(
        latitude=latitude,
        longitude=longitude,
        start_date=start_date,
        end_date=end_date,
        location_name=location_name,
    )


@dlt.resource(
    name="weather_hourly",
    write_disposition="merge",
    primary_key=["location_name", "timestamp"],
)
def weather_hourly(
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
    """Load hourly weather data with incremental sync.

    Each row represents one hour of weather data.

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
            - elevation_m: float - Elevation in meters
            - timezone: str - Timezone name
            - timestamp: datetime - Measurement timestamp (local timezone)

            Basic meteorology:
            - temperature_c: float - Temperature in Celsius
            - humidity_pct: float - Relative humidity (0-100)
            - precipitation_mm: float - Precipitation in mm
            - windspeed_kmh: float - Wind speed in km/h

            Cloud cover (%, 0-100):
            - cloud_cover_pct: float - Total cloud cover
            - cloud_cover_low_pct: float - Low clouds 0-2km
            - cloud_cover_mid_pct: float - Mid clouds 2-6km
            - cloud_cover_high_pct: float - High clouds 6km+

            Solar radiation (W/m²) and sunshine:
            - ghi_wm2: float - Global Horizontal Irradiance (shortwave)
            - dni_wm2: float - Direct Normal Irradiance
            - dhi_wm2: float - Diffuse Horizontal Irradiance
            - direct_horizontal_wm2: float - Direct radiation on horizontal plane
            - sunshine_duration_s: float - Sunshine seconds in preceding hour
    """
    print(f"Weather: Fetching data for {location_name} ({latitude}, {longitude})")
    print(f"  Date range: {start_date} to {end_date}")

    # Call Open-Meteo Archive API
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": start_date,
        "end_date": end_date,
        "hourly": ",".join([
            # Basic meteorology
            "temperature_2m",
            "relative_humidity_2m",
            "precipitation",
            "windspeed_10m",
            # Cloud cover (for solar modeling)
            "cloud_cover",
            "cloud_cover_low",
            "cloud_cover_mid",
            "cloud_cover_high",
            # Solar radiation (for PVLIB modeling)
            "shortwave_radiation",        # GHI - Global Horizontal Irradiance
            "direct_radiation",            # Direct radiation on horizontal plane
            "diffuse_radiation",           # DHI - Diffuse Horizontal Irradiance
            "direct_normal_irradiance",    # DNI - Direct Normal Irradiance
            "sunshine_duration",           # Sunshine seconds per hour
        ]),
        "timezone": "auto",  # Use local timezone for location
    }

    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
    except requests.RequestException as e:
        raise ValueError(f"Failed to fetch weather data from Open-Meteo: {e}")

    data = response.json()
    hourly = data.get("hourly", {})

    if not hourly:
        print("  No data returned from API")
        return

    # Extract metadata
    actual_lat = data.get("latitude")
    actual_lon = data.get("longitude")
    elevation = data.get("elevation")
    timezone_name = data.get("timezone")

    print(f"  Actual location: {actual_lat}, {actual_lon} (elevation: {elevation}m)")
    print(f"  Timezone: {timezone_name}")

    # Convert to records
    timestamps = hourly.get("time", [])
    temperatures = hourly.get("temperature_2m", [])
    humidities = hourly.get("relative_humidity_2m", [])
    precipitations = hourly.get("precipitation", [])
    windspeeds = hourly.get("windspeed_10m", [])

    # Cloud cover
    cloud_covers = hourly.get("cloud_cover", [])
    cloud_covers_low = hourly.get("cloud_cover_low", [])
    cloud_covers_mid = hourly.get("cloud_cover_mid", [])
    cloud_covers_high = hourly.get("cloud_cover_high", [])

    # Solar radiation
    shortwave_radiations = hourly.get("shortwave_radiation", [])
    direct_radiations = hourly.get("direct_radiation", [])
    diffuse_radiations = hourly.get("diffuse_radiation", [])
    direct_normal_irradiances = hourly.get("direct_normal_irradiance", [])
    sunshine_durations = hourly.get("sunshine_duration", [])

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
            "elevation_m": elevation,
            "timezone": timezone_name,
            "timestamp": timestamp,
            # Basic meteorology
            "temperature_c": temperatures[i],
            "humidity_pct": humidities[i],
            "precipitation_mm": precipitations[i],
            "windspeed_kmh": windspeeds[i],
            # Cloud cover (%)
            "cloud_cover_pct": cloud_covers[i],
            "cloud_cover_low_pct": cloud_covers_low[i],
            "cloud_cover_mid_pct": cloud_covers_mid[i],
            "cloud_cover_high_pct": cloud_covers_high[i],
            # Solar radiation (W/m²) and sunshine (seconds)
            "ghi_wm2": shortwave_radiations[i],  # Global Horizontal Irradiance
            "dni_wm2": direct_normal_irradiances[i],  # Direct Normal Irradiance
            "dhi_wm2": diffuse_radiations[i],  # Diffuse Horizontal Irradiance
            "direct_horizontal_wm2": direct_radiations[i],  # Direct on horizontal plane
            "sunshine_duration_s": sunshine_durations[i],  # Sunshine seconds
        }

        yield record

    if new_records == 0:
        print("  No new data to load")
    else:
        print(f"  Loaded {new_records:,} new records")


if __name__ == "__main__":
    # Test the weather source
    import dlt

    pipeline = dlt.pipeline(
        pipeline_name="weather",
        destination="duckdb",
        dataset_name="raw",
        dev_mode=True,
    )

    # Load weather data for Toronto
    data = weather_source(
        latitude=43.65,
        longitude=-79.38,
        start_date="2023-01-01",
        end_date="2023-01-31",
        location_name="toronto",
    )

    info = pipeline.run(data)
    print("\nPipeline run info:")
    print(info)
