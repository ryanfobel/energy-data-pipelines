"""Weather data pipeline for Open Data Coop.

This module provides dlt sources for loading historical weather and
air quality data from Open-Meteo API into DuckDB.
"""
from pipelines.weather.source import weather_source
from pipelines.weather.air_quality import air_quality_source

__all__ = ["weather_source", "air_quality_source"]
