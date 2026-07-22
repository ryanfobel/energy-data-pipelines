"""Open Data Coop pipelines package.

Contains dlt sources for ingesting energy data:
- home_assistant: Power monitoring data from Home Assistant
- green_button: Utility bill data from Green Button XML files

Configuration is managed via config.yml system (see pipelines/config.py).
"""

from pipelines.config import get_config, load_config, reset_config

__all__ = ['get_config', 'load_config', 'reset_config']
