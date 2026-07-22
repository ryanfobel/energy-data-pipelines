# Energy Data Pipelines

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

**Privacy-first home energy data pipelines for electricity, natural gas, and water**

Fork this repository to run your own private energy data warehouse with multi-commodity support (electricity, gas, water) from Green Button data and Home Assistant real-time monitoring.

## Features

- **Multi-commodity support**: Electricity (hourly), natural gas (monthly), water (daily/monthly)
- **Multiple data sources**: Green Button + Home Assistant integration
- **Interactive dashboard**: Evidence.dev dashboard with visualizations
- **Local-first**: All data stays on your device
- **Powered by modern data stack**: dlt + dbt + DuckDB
- **Template repository**: Fork and configure with your own data

## Quick Start

### 1. Fork and Clone

```bash
git clone https://github.com/YOUR_USERNAME/energy-data-pipelines.git
cd energy-data-pipelines
```

### 2. Install Dependencies

```bash
# Install pixi (if needed)
curl -fsSL https://pixi.sh/install.sh | bash

# Install project dependencies
pixi install
```

### 3. Configure

Copy the example config and add your data sources:

```bash
cp config.example.yml config.local.yml
cp .env.example .env

# Edit config.local.yml with your file paths
# Edit .env with any credentials (e.g., InfluxDB tokens)
```

### 4. Run Pipelines

```bash
# Load Green Button data
pixi run pipeline-green-button

# Load Home Assistant data (if configured)
pixi run pipeline-home-assistant

# Run dbt transformations
pixi run dbt-build
```

### 5. View Dashboard

```bash
# Install dashboard dependencies
cd dashboard
npm install

# Start dev server
npm run dev
```

Open http://localhost:3000 to view your energy dashboard.

## What's Included

### Data Pipelines

**Green Button Pipeline** (`pipelines/green_button/`)
- Parses Green Button XML files (ESPI format)
- Supports electricity, natural gas, and water
- Extracts interval readings with quality codes
- Idempotent loads (merge on primary keys)

**Home Assistant Pipeline** (`pipelines/home_assistant/`)
- Connects to InfluxDB or reads Parquet exports
- Real-time electricity monitoring
- Temperature and sensor data
- Integrates with Green Button data in marts

### dbt Transformations

**Staging Models** (`transform/models/staging/`)
- `stg_green_button_electricity.sql` — Hourly electricity from utilities
- `stg_green_button_gas.sql` — Monthly natural gas
- `stg_green_button_water.sql` — Daily/monthly water
- `stg_home_assistant_power.sql` — Real-time power monitoring

**Mart Models** (`transform/models/marts/`)
- `fct_electricity_consumption.sql` — Combined electricity (Green Button + Home Assistant)
- `fct_gas_consumption.sql` — Natural gas consumption with placeholders for weather enrichment
- `fct_water_consumption.sql` — Water usage with unit normalization
- `fct_utility_consumption.sql` — Unified view of all commodities
- `dim_homes.sql` — Home dimension with meter IDs

### Evidence Dashboard

**Interactive visualizations** (`dashboard/`)
- Overview page with all commodities
- Electricity page (hourly patterns, daily/monthly summaries)
- Natural gas page (monthly consumption and costs)
- Water page (consumption with unit conversions)
- Powered by DuckDB queries on dbt marts

## Configuration

See [docs/configuration.md](docs/configuration.md) for detailed configuration options.

### Example: Green Button

```yaml
# config.local.yml
green_button:
  xml_file_path: ~/Downloads/GreenButtonData.xml
  home_id: my-home-001
```

### Example: Home Assistant

```yaml
# config.local.yml
home_assistant:
  influxdb:
    url: http://localhost:8086
    org: my-org
    bucket: home_assistant
    token: ${INFLUXDB_TOKEN}  # From .env
  entities:
    - entity_id: sensor.home_power
      measurement: power
      field: value
```

## Usage

See [docs/USAGE.md](docs/USAGE.md) for detailed usage instructions.

### Common Tasks

```bash
# Run specific pipeline
pixi run pipeline-green-button
pixi run pipeline-home-assistant

# Run dbt models
pixi run dbt-run           # Run all models
pixi run dbt-build         # Build + test
pixi run dbt-test          # Test only

# Export to Parquet
pixi run export-parquet

# Export to Paimon (if configured)
pixi run export-paimon

# Clean up
pixi run clean             # Remove DuckDB files
pixi run clean-all         # Remove DuckDB + dlt state
```

## Dashboard Deployment

The Evidence dashboard can be deployed as a static site:

### Local Static Build

```bash
cd dashboard
npm run build
python3 -m http.server 8000 --directory build
```

### GitHub Pages

```bash
cd dashboard
npm run build
cp -r build/* ../docs/dashboard/
git add docs/dashboard
git commit -m "docs: update dashboard"
git push
```

Enable GitHub Pages in repository settings (source: `docs/` folder).

See [dashboard/README.md](dashboard/README.md) for more deployment options.

## Data Schema

### Green Button Data

Commodities supported:
- **Electricity** (VALUE_1): Hourly intervals, kWh
- **Natural Gas** (VALUE_7): Monthly intervals, m³
- **Water** (VALUE_2): Daily/monthly intervals, m³ or gallons

Quality codes:
- `VALIDATED`: Meter-validated readings
- `ESTIMATED`: Utility estimates
- `MISSING`: Missing/incomplete data

### Home Assistant Data

Supports any InfluxDB measurement/field or Parquet export from Home Assistant.

Common entities:
- `sensor.home_power` — Real-time power (W)
- `sensor.outdoor_temperature` — Weather data
- `sensor.heat_pump_*` — Heat pump sensors

## Architecture

```
Green Button XML ──┐
                   ├──► dlt ──► DuckDB (raw) ──► dbt ──► DuckDB (marts) ──► Evidence
Home Assistant ────┘                                                      ──► Parquet exports
                                                                          ──► Paimon warehouse
```

- **dlt** (data load tool): Extracts and loads raw data
- **DuckDB**: Local data warehouse (single `.duckdb` file)
- **dbt**: Transforms raw data into analysis-ready marts
- **Evidence**: Dashboard queries marts directly
- **Parquet/Paimon**: Optional exports for sharing or backup

## Documentation

- [Setup Guide](docs/SETUP.md) — Detailed installation and configuration
- [Usage Guide](docs/USAGE.md) — Running pipelines and querying data
- [Configuration Reference](docs/configuration.md) — All config options
- [FAQ](docs/FAQ.md) — Common questions and troubleshooting
- [Deployment Options](docs/deployment-options.md) — Ways to deploy your fork

## Related Projects

This repository was extracted from the [Open Data Cooperative](https://github.com/ryanfobel/open-data-coop) for use as a standalone template.

Other related tools:
- [utility-bill-scraper](https://github.com/ryanfobel/utility-bill-scraper) — Automated bill downloads
- [homeassistant-helpers](https://github.com/ryanfobel/homeassistant-helpers) — IoT data hub
- [eemeter](https://github.com/openeemeter/eemeter) — CalTRACK energy calculations

## Use Cases

### For Homeowners

- **Solar sizing**: Use actual hourly load shape across seasons
- **Heat pump selection**: Compare performance against real heating load
- **Rate plan optimization**: Model TOU vs ULO savings
- **Energy audit validation**: Verify consumption against model predictions
- **Retrofit ROI**: Quantify savings from upgrades

### For Energy Cooperatives

- **Member benefits**: Offer data tools without building infrastructure
- **Community aggregation**: Privacy-preserving analysis across cohorts
- **Policy advocacy**: Evidence-based arguments for better rates/programs
- **Education**: Help members understand energy use patterns

### For Researchers

- **Heat pump field data**: Real-world COP measurements
- **Grid interaction**: Impact of electrification on demand curves
- **Model validation**: Test predictions against measured consumption
- **Program evaluation**: Assess retrofits with normalized savings

## Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

**Ways to contribute**:
- Bug fixes and improvements
- New data source integrations
- Dashboard enhancements
- Documentation updates
- Testing and feedback

## License

- **Code**: [Apache 2.0](LICENSE) — Use commercially with any data
- **This template**: Fork freely and run with your own data

## Contact

Questions or feedback? [Open an issue](https://github.com/ryanfobel/energy-data-pipelines/issues) or reach out:

**Ryan Fobel**
Data Engineer, Kitchener ON
GitHub: [@ryanfobel](https://github.com/ryanfobel)

---

*Privacy-first energy data infrastructure — fork, configure, and run your own.*
