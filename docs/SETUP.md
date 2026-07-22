# Setup Guide

Complete installation and configuration guide for Open Data Coop energy pipelines.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [First Pipeline Run](#first-pipeline-run)
- [Data Sources Setup](#data-sources-setup)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### Required

**Git**
```bash
# Check if git is installed
git --version
```

If not installed:
- **Mac**: Install Xcode Command Line Tools: `xcode-select --install`
- **Linux**: `sudo apt install git` (Ubuntu/Debian) or `sudo yum install git` (RHEL/CentOS)
- **Windows**: Download from [git-scm.com](https://git-scm.com/download/win)

**Pixi Package Manager**

Pixi manages all Python dependencies and environments for this project.

```bash
# Install pixi
curl -fsSL https://pixi.sh/install.sh | bash

# Verify installation
pixi --version
```

Alternative installation methods: [pixi.sh](https://pixi.sh/latest/)

### Optional

**DuckDB CLI** (for interactive queries)
```bash
# Mac (Homebrew)
brew install duckdb

# Linux
wget https://github.com/duckdb/duckdb/releases/download/v0.10.0/duckdb_cli-linux-amd64.zip
unzip duckdb_cli-linux-amd64.zip

# Or use Python version via pixi (included)
pixi run python -c "import duckdb; print(duckdb.__version__)"
```

**Home Assistant** (for real-time power monitoring)
- Only needed if you want to ingest live power monitoring data
- See [Home Assistant Installation Guide](https://www.home-assistant.io/installation/)

**Green Button Data Access** (for utility interval data)
- Request hourly consumption data from your electricity provider
- Ontario utilities: Hydro One, Elexicon, Toronto Hydro, etc.
- See [docs/data-sources/green-button.md](data-sources/green-button.md) for provider-specific guides

## Installation

### 1. Fork the Repository

1. Go to [github.com/ryanfobel/open-data-coop](https://github.com/ryanfobel/open-data-coop)
2. Click **Fork** in the top-right corner
3. Choose your GitHub account as the destination

### 2. Clone Your Fork

```bash
# Replace YOUR_USERNAME with your GitHub username
git clone https://github.com/YOUR_USERNAME/open-data-coop.git
cd open-data-coop
```

### 3. Install Dependencies

```bash
# Install all dependencies (Python, dbt, dlt, DuckDB, etc.)
pixi install

# Verify installation
pixi run python --version
pixi run dbt --version
```

This creates a `.pixi` directory with all dependencies isolated to this project.

### 4. Verify Installation

```bash
# Run a simple test to ensure everything works
pixi run python -c "import dlt, duckdb, pandas; print('All dependencies installed successfully!')"
```

Expected output: `All dependencies installed successfully!`

## Configuration

The pipelines use configuration files to specify data sources and warehouse settings.

### Option 1: Use Example Configurations

Choose a pre-built configuration based on your use case:

```bash
# Copy an example configuration
cp docs/examples/green-button-only.yml config.local.yml

# Or for Home Assistant only
cp docs/examples/home-assistant-only.yml config.local.yml

# Or for full setup
cp docs/examples/full-setup.yml config.local.yml
```

### Option 2: Create Custom Configuration

Create `config.local.yml` in the root directory:

```yaml
# config.local.yml
warehouse:
  database_path: "energy_warehouse.duckdb"
  export_path: "~/energy-data/warehouse"

homes:
  - id: "home-001"
    name: "My Home"
    sources:
      green_button:
        enabled: true
        file_path: "data/greenbutton/hydro_one_2024.xml"
      home_assistant:
        enabled: false  # Set to true if you have HA

# Optional: Grid data sources
grid:
  enabled: false
  sources:
    - ieso
    - gridwatch
```

### Configuration Fields

**warehouse**:
- `database_path`: DuckDB database file location (default: `energy_warehouse.duckdb`)
- `export_path`: Where to export Parquet files (default: `~/energy-data/warehouse`)

**homes**: List of homes to process
- `id`: Unique identifier (e.g., `home-001`, or use a UUID)
- `name`: Human-readable name
- `sources`: Data sources for this home

**sources.green_button**:
- `enabled`: true/false
- `file_path`: Path to Green Button XML file

**sources.home_assistant**:
- `enabled`: true/false
- `parquet_file`: Path to exported Home Assistant power monitoring data

## First Pipeline Run

### Test with Mock Data

Run a complete pipeline test with generated mock data:

```bash
# Generate 7 days of mock Home Assistant power monitoring data
pixi run python scripts/generate_mock_ha_data.py

# Run the full pipeline (dlt + dbt)
pixi run python scripts/test_full_pipeline.py
```

Expected output:
```
================================================================================
FULL PIPELINE TEST: Green Button → DuckDB → dbt → Paimon
================================================================================

[1/3] Running dlt pipeline...
Green Button: Parsing Hydro1_Electric_60_Minute_12-25-2022_12-23-2024.xml
  Found 1 usage point(s)
    UsagePoint 0: 1 meter reading(s)
  Total interval readings extracted: 18000
✓ dlt load complete

[2/3] Running dbt transformations...
✓ dbt transformations complete

[3/3] Validating results...
  Staging view (stg_green_button): 18,000 rows
  Marts table (fct_electricity_consumption): 18,000 rows

✅ FULL PIPELINE TEST PASSED
```

### Run with Real Data

Once you have real Green Button XML files:

```bash
# 1. Place your Green Button XML files in data/greenbutton/
mkdir -p data/greenbutton
cp ~/Downloads/myutility_data.xml data/greenbutton/

# 2. Update config.local.yml with the file path

# 3. Run the pipeline
pixi run python scripts/test_green_button_pipeline.py
```

## Data Sources Setup

### Green Button Data

**How to Get Your Data:**

1. **Ontario Utilities**:
   - Log in to your utility account (Hydro One, Elexicon, etc.)
   - Navigate to "Green Button" or "Download My Data"
   - Select date range and download XML file

2. **Other Provinces**:
   - Check with your electricity provider
   - Look for "Green Button", "My Data", or "Interval Data" options

3. **Place the file**:
```bash
mkdir -p data/greenbutton
mv ~/Downloads/greenbutton_export.xml data/greenbutton/
```

**File Format:**
- Must be Green Button XML (ESPI format)
- Typically ends in `.xml`
- Contains hourly consumption readings

See [docs/data-sources/green-button.md](data-sources/green-button.md) for detailed provider guides.

### Home Assistant Power Monitoring

**Prerequisites:**
- Home Assistant installed and running
- Power monitoring device configured (Emporia Vue, IoTaWatt, Shelly EM, etc.)
- Power sensors logging to Home Assistant

**Export Data:**

Option 1: **Generate Mock Data** (for testing)
```bash
pixi run python scripts/generate_mock_ha_data.py
```

Option 2: **Export from InfluxDB** (if using InfluxDB addon)
```bash
# Coming soon: InfluxDB export script
# For now, use the Parquet export feature in homeassistant-helpers
```

Option 3: **Manual Export**
- Export sensor history from Home Assistant
- Convert to Parquet format matching this schema:
  - `home_id`, `device_id`, `channel`, `timestamp`, `watts`, `volts`, `amps`, `power_factor`

See [docs/home-assistant-pipeline.md](home-assistant-pipeline.md) for detailed setup.

### Ontario Grid Data (Optional)

Add grid carbon intensity and pricing data:

```bash
# Run ontario-grid-pipelines
cd projects/ontario-grid-pipelines
pip install -e .
python pipeline.py --sources ieso gridwatch oeb
```

This downloads:
- **IESO fuel mix**: Hourly generation by source (nuclear, gas, hydro, wind, solar)
- **Gridwatch**: Live CO₂ intensity
- **OEB rates**: Historical electricity rate tables

## Troubleshooting

### Common Issues

**Issue: `pixi: command not found`**

Solution: Pixi installation didn't update your PATH. Either:
```bash
# Restart your terminal, or:
source ~/.bashrc  # or ~/.zshrc on Mac
```

**Issue: `ModuleNotFoundError: No module named 'dlt'`**

Solution: You're not using the pixi environment. Always prefix commands with `pixi run`:
```bash
# Wrong
python scripts/test_full_pipeline.py

# Correct
pixi run python scripts/test_full_pipeline.py
```

**Issue: `FileNotFoundError: Green Button XML file not found`**

Solution: Check the file path in your config:
```bash
# Verify the file exists
ls -la data/greenbutton/

# Update config.local.yml with correct path
```

**Issue: `dbt run` fails with "Compilation Error"**

Solution: Ensure DuckDB database exists and has raw data:
```bash
# Check if database exists
ls -la energy_warehouse.duckdb

# Verify raw tables exist
pixi run duckdb energy_warehouse.duckdb -c "SHOW TABLES;"

# Re-run dlt pipeline if tables are missing
pixi run python scripts/test_green_button_pipeline.py
```

**Issue: Out of disk space**

Solution: Energy data can grow large. Check disk usage:
```bash
# Check DuckDB database size
du -h energy_warehouse.duckdb

# Check Parquet export size
du -sh ~/energy-data/warehouse/

# Clean old test databases
rm -f *_test.duckdb
```

**Issue: Permission denied when running scripts**

Solution: Make scripts executable:
```bash
chmod +x scripts/*.py
```

### Performance Issues

**Slow dlt loading:**
- Green Button XML parsing is CPU-bound
- For files >100MB, expect 30-60 seconds processing time
- Consider splitting large files by year

**Slow dbt transformations:**
- First run is slower (table creation)
- Subsequent runs use incremental updates
- Use `dbt run --select model_name` to run specific models

**Large database files:**
- DuckDB compresses well but can still grow large
- Export to Parquet and archive old DuckDB files periodically:
```bash
pixi run python scripts/export_to_paimon.py
gzip energy_warehouse.duckdb
mv energy_warehouse.duckdb.gz archive/
```

### Getting Help

1. **Check FAQ**: See [docs/FAQ.md](FAQ.md) for common questions
2. **Search Issues**: [github.com/ryanfobel/open-data-coop/issues](https://github.com/ryanfobel/open-data-coop/issues)
3. **Ask for Help**: Open a new issue with:
   - Your operating system and version
   - Command you ran
   - Full error message
   - Contents of `config.local.yml` (remove sensitive paths)

### Platform-Specific Notes

**macOS:**
- Works on both Intel (osx-64) and Apple Silicon (osx-arm64)
- May need to allow Terminal in System Preferences → Privacy

**Linux:**
- Tested on Ubuntu 22.04 and Debian 12
- Should work on any modern distribution
- May need to install system dependencies for DuckDB:
  ```bash
  sudo apt install build-essential
  ```

**Windows:**
- **Experimental**: Not officially tested
- Consider using WSL2 (Windows Subsystem for Linux)
- Install Ubuntu 22.04 in WSL2 and follow Linux instructions

## Next Steps

Once setup is complete:

1. **Run Pipelines**: See [docs/USAGE.md](USAGE.md) for pipeline operations
2. **Query Data**: Explore your data warehouse with DuckDB
3. **Export Data**: Export to Parquet for long-term storage
4. **Schedule Pipelines**: Set up cron jobs for automated updates
5. **Contribute**: See [CONTRIBUTING.md](../CONTRIBUTING.md) to improve the project

---

**Need help?** Open an issue or check the [FAQ](FAQ.md).
