# Energy Data Pipelines

**Privacy-first energy data pipelines for homeowners and cooperatives**

Turn your energy data into a queryable data warehouse—no cloud services required, all data stays local.

## What is this?

A set of data pipelines that transforms energy data from various sources into a unified, queryable format:

- ⚡ **Green Button** - Utility meter data (hourly electricity consumption)
- 🏠 **Home Assistant** - Real-time power monitoring (10-second intervals from devices like Emporia Vue, IoTaWatt)
- 📊 **DuckDB** - Fast local analytics database
- 🗄️ **Parquet** - Efficient columnar storage (Paimon-compatible)

## Quick Start (5 minutes)

```bash
# 1. Clone this repository
git clone https://github.com/ryanfobel/energy-data-pipelines.git
cd energy-data-pipelines

# 2. Install dependencies (using pixi)
curl -fsSL https://pixi.sh/install.sh | bash
pixi install

# 3. Configure
cp config.example.yml config.local.yml
# Edit config.local.yml with your settings

# 4. Run with mock data
pixi run generate-mock-data
pixi run pipeline-all
pixi run export-paimon

# 5. Query your data
pixi run inspect-db
```

That's it! You now have a local data warehouse with your energy data.

## Features

### Privacy-First
- **All data stays local** - No cloud services, no external APIs
- **You own your data** - DuckDB files and Parquet exports on your machine
- **Offline-capable** - Works without internet connection
- **Open source** - Inspect the code, modify as needed

### Easy to Use
- **Simple configuration** - One YAML file for all settings
- **Automated pipelines** - Run manually or schedule with cron
- **Mock data included** - Test without real credentials
- **Comprehensive docs** - Setup guides and troubleshooting

### Flexible
- **Multiple data sources** - Combine utility and real-time data
- **Customizable** - Fork and modify for your use case
- **Extensible** - Add new data sources easily
- **Analysis-ready** - Query with SQL, export to Parquet

## Use Cases

### For Homeowners
- Track electricity consumption and costs
- Optimize time-of-use rate schedules
- Analyze heat pump performance (COP vs outdoor temperature)
- Size solar installations based on actual usage
- Monitor major loads (EV charging, water heater, HVAC)
- Calculate carbon footprint from grid carbon intensity

### For Cooperatives
- Aggregate member data (with opt-in consent)
- Benchmark consumption across cohorts
- Identify opportunities for collective action
- Support community solar or bulk purchasing

### For Researchers
- Analyze residential energy patterns
- Study appliance disaggregation
- Model demand response potential
- Validate building energy models

## Architecture

```
Data Sources → dlt (ingestion) → DuckDB → dbt (transformation) → Parquet (warehouse)
```

1. **dlt** loads raw data from Green Button XML or Home Assistant parquet exports
2. **DuckDB** stores data in a local database file
3. **dbt** transforms raw data into analytics-ready tables (staging → marts)
4. **Parquet** exports data to Hive-partitioned files for long-term storage

## Documentation

- **[Setup Guide](docs/SETUP.md)** - Detailed installation instructions
- **[Usage Guide](docs/USAGE.md)** - How to run pipelines and query data
- **[FAQ](docs/FAQ.md)** - Common questions and troubleshooting
- **[Configuration](docs/configuration.md)** - Config system reference
- **[Deployment Options](docs/deployment-options.md)** - Different ways to deploy

## Data Sources

### Green Button

Download XML files from your utility's website:
- **Ontario**: Hydro One, Hydro Ottawa, Toronto Hydro
- **US**: PG&E, ComEd, SCE (and 60+ others)
- **Format**: ESPI XML (Energy Services Provider Interface)

See [docs/SETUP.md](docs/SETUP.md#green-button) for utility-specific instructions.

### Home Assistant

Export power monitoring data from:
- **Emporia Vue** (3, 2, 1)
- **IoTaWatt**
- **Shelly EM / Pro**
- **Any Home Assistant power sensor**

Can export from InfluxDB or directly from Home Assistant database.

## Example Queries

Once data is loaded, query with DuckDB:

```sql
-- Daily consumption by source
SELECT
  date_trunc('day', timestamp) as date,
  source,
  SUM(kwh) as total_kwh,
  SUM(cost) as total_cost_cents
FROM fct_electricity_consumption
GROUP BY 1, 2
ORDER BY 1 DESC;

-- Time-of-use analysis
SELECT
  tou_period,
  COUNT(*) as hours,
  SUM(kwh) as total_kwh,
  AVG(cost) as avg_cost_cents
FROM fct_electricity_consumption
WHERE source = 'green_button'
GROUP BY 1;

-- Heat pump performance by temperature
SELECT
  FLOOR(outdoor_temp / 5) * 5 as temp_bin,
  AVG(heat_pump_power_kw) as avg_power,
  AVG(heat_delivered_btu) / AVG(heat_pump_power_kw * 3412) as cop
FROM fct_electricity_consumption
WHERE device_id LIKE '%heat_pump%'
GROUP BY 1
ORDER BY 1;
```

See [docs/USAGE.md](docs/USAGE.md#example-queries) for more examples.

## Project Status

**Status:** Production-ready (v1.0)

- ✅ Green Button pipeline (stable)
- ✅ Home Assistant pipeline (stable)
- ✅ dbt transformations (stable)
- ✅ Parquet export (stable)
- ✅ Documentation (comprehensive)
- 🚧 Evidence.dev dashboard (planned)
- 🚧 InfluxDB direct export (planned)

## Requirements

- **Python** 3.11 or 3.12
- **pixi** (dependency manager) or pip + Python venv
- **Operating System**: macOS, Linux, or Windows/WSL2
- **Disk space**: ~1GB for dependencies, ~100MB per year of data

See [docs/SETUP.md](docs/SETUP.md#prerequisites) for details.

## Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT License - see [LICENSE](LICENSE)

## Support

- **Documentation**: Start with [docs/FAQ.md](docs/FAQ.md)
- **Issues**: [GitHub Issues](https://github.com/ryanfobel/energy-data-pipelines/issues)
- **Discussions**: [GitHub Discussions](https://github.com/ryanfobel/energy-data-pipelines/discussions)

## Related Projects

- **[Open Data Coop](https://github.com/ryanfobel/open-data-coop)** - Research and experimental pipelines
- **[Green Button Alliance](https://www.greenbuttonalliance.org/)** - Standard for energy data exchange
- **[Home Assistant](https://www.home-assistant.io/)** - Open-source home automation
- **[DuckDB](https://duckdb.org/)** - Fast analytical database
- **[dbt](https://www.getdbt.com/)** - Analytics engineering framework
- **[Apache Paimon](https://paimon.apache.org/)** - Streaming data lakehouse

## Acknowledgments

Built with support from the open-source community and inspired by the vision of democratized energy data.
