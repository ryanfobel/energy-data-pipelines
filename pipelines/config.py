"""Configuration management for Open Data Coop pipelines.

Loads configuration from:
1. config.example.yml (defaults)
2. config.local.yml (user overrides, if exists)
3. Environment variables (for secrets and paths)

Features:
- Environment variable expansion: ${VAR_NAME}
- Home directory expansion: ~/path/to/file
- Validation of required fields
- Type-safe access to config values
"""
from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any, Dict, Optional

import yaml


class ConfigError(Exception):
    """Configuration error."""
    pass


class Config:
    """Configuration container with dict-like access."""

    def __init__(self, data: dict):
        self._data = data

    def __getitem__(self, key: str) -> Any:
        return self._data[key]

    def __contains__(self, key: str) -> bool:
        return key in self._data

    def get(self, key: str, default: Any = None) -> Any:
        """Get config value with optional default."""
        return self._data.get(key, default)

    def get_path(self, key: str, default: Optional[str | Path] = None) -> Path:
        """Get config value as Path, with expansion."""
        value = self.get(key, default)
        if value is None:
            raise ConfigError(f"Required path config '{key}' not found")
        return Path(str(value))

    def __repr__(self) -> str:
        return f"Config({self._data})"


def expand_env_vars(value: Any) -> Any:
    """Recursively expand environment variables in config values.

    Supports ${VAR_NAME} syntax.
    Missing variables raise ConfigError.

    Args:
        value: Config value (str, dict, list, or other)

    Returns:
        Value with environment variables expanded

    Raises:
        ConfigError: If referenced environment variable is not set
    """
    if isinstance(value, str):
        # Find all ${VAR} patterns
        pattern = r'\$\{([^}]+)\}'
        matches = re.findall(pattern, value)

        for var_name in matches:
            env_value = os.getenv(var_name)
            if env_value is None:
                # Check if the entire value is just the env var reference
                if value == f"${{{var_name}}}":
                    # Return None for missing optional env vars
                    return None
                raise ConfigError(
                    f"Environment variable '{var_name}' referenced in config but not set. "
                    f"Add it to your .env file or set it in your environment."
                )
            value = value.replace(f"${{{var_name}}}", env_value)

        return value

    elif isinstance(value, dict):
        return {k: expand_env_vars(v) for k, v in value.items()}

    elif isinstance(value, list):
        return [expand_env_vars(item) for item in value]

    else:
        return value


def expand_home_dir(value: Any) -> Any:
    """Recursively expand ~ to home directory in config values.

    Args:
        value: Config value (str, dict, list, or other)

    Returns:
        Value with ~ expanded to home directory
    """
    if isinstance(value, str):
        if value.startswith("~"):
            return str(Path(value).expanduser())
        return value

    elif isinstance(value, dict):
        return {k: expand_home_dir(v) for k, v in value.items()}

    elif isinstance(value, list):
        return [expand_home_dir(item) for item in value]

    else:
        return value


def load_yaml_file(file_path: Path) -> dict:
    """Load YAML file and return parsed dict.

    Args:
        file_path: Path to YAML file

    Returns:
        Parsed YAML as dict

    Raises:
        ConfigError: If file doesn't exist or can't be parsed
    """
    if not file_path.exists():
        raise ConfigError(f"Config file not found: {file_path}")

    try:
        with open(file_path) as f:
            data = yaml.safe_load(f)
            return data if data is not None else {}
    except yaml.YAMLError as e:
        raise ConfigError(f"Error parsing YAML file {file_path}: {e}")


def merge_configs(base: dict, override: dict) -> dict:
    """Deep merge two config dictionaries.

    Override values replace base values at all levels.

    Args:
        base: Base configuration
        override: Override configuration

    Returns:
        Merged configuration
    """
    result = base.copy()

    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            # Recursively merge nested dicts
            result[key] = merge_configs(result[key], value)
        else:
            # Override value
            result[key] = value

    return result


def load_config(
    config_dir: Optional[Path] = None,
    env_file: Optional[Path] = None,
) -> Config:
    """Load configuration from files and environment.

    Loading order:
    1. config.example.yml (defaults)
    2. config.local.yml (user overrides, optional)
    3. Environment variables (for secrets)

    Args:
        config_dir: Directory containing config files (default: project root)
        env_file: Path to .env file (default: project root/.env)

    Returns:
        Config object with merged configuration

    Raises:
        ConfigError: If config files can't be loaded or are invalid
    """
    # Determine config directory
    if config_dir is None:
        # Assume we're in pipelines/ directory, go up one level
        config_dir = Path(__file__).parent.parent

    # Load .env file if it exists
    if env_file is None:
        env_file = config_dir / ".env"

    if env_file.exists():
        load_env_file(env_file)

    # Load base config (required)
    example_config_path = config_dir / "config.example.yml"
    base_config = load_yaml_file(example_config_path)

    # Load local config (optional)
    local_config_path = config_dir / "config.local.yml"
    if local_config_path.exists():
        local_config = load_yaml_file(local_config_path)
        merged_config = merge_configs(base_config, local_config)
    else:
        merged_config = base_config

    # Expand environment variables
    merged_config = expand_env_vars(merged_config)

    # Expand home directory
    merged_config = expand_home_dir(merged_config)

    # Validate required fields
    validate_config(merged_config)

    return Config(merged_config)


def load_env_file(env_file: Path) -> None:
    """Load environment variables from .env file.

    Only loads variables that aren't already set in the environment.

    Args:
        env_file: Path to .env file
    """
    if not env_file.exists():
        return

    with open(env_file) as f:
        for line in f:
            line = line.strip()

            # Skip comments and empty lines
            if not line or line.startswith("#"):
                continue

            # Parse KEY=VALUE
            if "=" not in line:
                continue

            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip()

            # Remove quotes if present
            if value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
            elif value.startswith("'") and value.endswith("'"):
                value = value[1:-1]

            # Only set if not already in environment
            if key not in os.environ:
                os.environ[key] = value


def validate_config(config: dict) -> None:
    """Validate configuration has required fields.

    Args:
        config: Configuration dict

    Raises:
        ConfigError: If required fields are missing
    """
    required_fields = [
        "paths",
        "dlt",
    ]

    for field in required_fields:
        if field not in config:
            raise ConfigError(f"Required config field '{field}' is missing")

    # Validate paths section
    required_paths = ["duckdb"]
    paths = config.get("paths", {})

    for path_field in required_paths:
        if path_field not in paths:
            raise ConfigError(f"Required path config 'paths.{path_field}' is missing")


# Global config instance (lazy loaded)
_config: Optional[Config] = None


def get_config() -> Config:
    """Get global config instance (lazy loaded).

    Returns:
        Global Config instance
    """
    global _config
    if _config is None:
        _config = load_config()
    return _config


def reset_config() -> None:
    """Reset global config instance (for testing)."""
    global _config
    _config = None


if __name__ == "__main__":
    # Test config loading
    config = load_config()
    print("Configuration loaded successfully!")
    print(f"\nDuckDB path: {config['paths']['duckdb']}")
    print(f"Paimon warehouse: {config['paths']['paimon_warehouse']}")
    print(f"\nHome Assistant enabled: {config['home_assistant']['enabled']}")
    print(f"Green Button enabled: {config['green_button']['enabled']}")
