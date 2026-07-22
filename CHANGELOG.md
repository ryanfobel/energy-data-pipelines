# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Evidence.dev dashboard with multi-commodity visualizations
- Dashboard pages for electricity, gas, and water
- Multi-commodity support: natural gas and water from Green Button
- Staging models for gas (`stg_green_button_gas`) and water (`stg_green_button_water`)
- Mart models: `fct_gas_consumption`, `fct_water_consumption`, `fct_utility_consumption`
- Dashboard README with deployment options

### Changed
- Updated README to focus on energy pipelines (removed open-data-coop content)
- Evidence.dev marked as implemented (moved from Planned)

### Planned
- Direct InfluxDB export (without parquet intermediate)
- Additional data sources (Sense, Curb, Neurio)
- Docker Compose deployment option
- Automated testing with GitHub Actions
- Rate optimization module
- Water test data and validation

## [1.0.0] - 2026-07-21

### Added
- Initial release of production-ready pipelines
- Green Button pipeline (ESPI XML → DuckDB)
- Home Assistant pipeline (Parquet → DuckDB, supports Emporia Vue, IoTaWatt, Shelly)
- dbt transformations (staging + marts)
- Parquet export with Hive partitioning (Paimon-compatible)
- Configuration system (config.yml + .env)
- Comprehensive documentation (SETUP, USAGE, FAQ)
- Example configurations (green-button-only, home-assistant-only, full-setup)
- Mock data generator for testing
- pixi tasks for common operations
- MIT License

### Features
- **Privacy-first**: All data stays local, no cloud services
- **Offline-capable**: Works without internet
- **Flexible**: Multiple data sources, customizable transformations
- **Analysis-ready**: Query with SQL, export to Parquet
- **Well-documented**: Setup guides, usage examples, troubleshooting

### Data Sources
- Green Button (60+ utilities in US/Canada)
- Home Assistant power monitoring
- Temperature sensors (for heat pump analysis)

### Transformations
- `stg_green_button` - Clean and validate utility data
- `stg_home_assistant_power` - Aggregate 10s → hourly kWh
- `stg_dim_homes` - Home metadata
- `fct_electricity_consumption` - Unified consumption table

### Exports
- Parquet with Hive partitioning
- DuckDB database files
- Compatible with Apache Paimon

[unreleased]: https://github.com/ryanfobel/energy-data-pipelines/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/ryanfobel/energy-data-pipelines/releases/tag/v1.0.0
