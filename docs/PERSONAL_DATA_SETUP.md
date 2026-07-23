# Personal Green Button Data Setup

This guide explains how to load your personal utility data into the pipeline.

## Quick Start

1. **Download your Green Button data** from your utility portal
2. **Configure file paths** in `config.local.yml`
3. **Run the loader**: `pixi run python scripts/load_my_green_button_data.py`
4. **View loaded data**: `pixi run python scripts/view_loaded_data.py`

## Configuration

Edit `config.local.yml` to add your Green Button XML files:

```yaml
green_button:
  files:
    - path: ~/Downloads/Kitchener_Utilities_Water_12_Months.xml
      home_id: my-home-001
      commodity: water
    - path: ~/Downloads/Green_Button_Electricity.xml
      home_id: my-home-001
      commodity: electricity
    - path: ~/Downloads/Enbridge_Gas_Data.xml
      home_id: my-home-001
      commodity: gas
```

## Downloading Green Button Data

### City of Kitchener (Water)

1. Log into https://billing.kitchener.ca/
2. Navigate to Green Button section
3. Select date range (maximum 12 months)
4. Download XML file

**Note**: Kitchener's water data shows:
- Monthly billing intervals
- Costs in the `cost` field
- Consumption values may be 0 (actual usage tracked separately)

### Ontario Electricity Utilities

#### Hydro One
- Portal: MyAccount.HydroOne.com
- Download: "Green Button Download My Data"
- Format: Hourly interval data

#### Elexicon (formerly Whitby Hydro)
- Similar Green Button download available

#### Other LDCs
Most Ontario Local Distribution Companies support Green Button

### Enbridge Gas

- Portal: MyAccount.Enbridge.com
- Download: Green Button data
- Format: Monthly billing data

## Common Issues

### Empty XML File

**Problem**: Downloaded file is 0 bytes

**Solution**:
- Re-download from the utility portal
- Try a different browser
- Check if you selected a valid date range
- Ensure you're fully logged in before downloading

### No Data After Loading

**Problem**: Script runs but no readings extracted

**Possible causes**:
- XML file is malformed
- Date range has no actual readings
- File is for a different account

**Debug**: Check the console output - it shows how many usage points and meter readings were found

### Mixed Commodity Data

**Problem**: Loading one file brings in multiple commodities

**This is normal!** The pipeline uses merge disposition - previously loaded data persists. Each run adds new data without removing old data.

To start fresh:
```bash
rm ~/.dlt/pipelines/green_button.duckdb
```

## Data Privacy

### .gitignore Protection

Your personal data files are excluded from git via `.gitignore`:

```
# Personal Green Button data (keep private!)
**/Green_Button*.xml
**/Kitchener_Utilities*.xml
**/*_Green_Button_*.xml
```

### Local Storage

- Raw XML files: Keep in `~/Downloads` or a personal directory
- Processed data: Stored in `~/.dlt/pipelines/green_button.duckdb`
- Both are local-only and never committed to git

### config.local.yml

This file is also excluded from git (`.gitignore` entry: `config.local.yml`)

## Third-Party Data Sharing

When authorizing companies via Green Button Connect, research them first:

- Read their privacy policy
- Understand their business model
- Check reviews and reputation
- Know what data they access
- Verify you can revoke access

See issue `energy-data-pipelines-2u5` for research on companies appearing in Kitchener's portal.

## Scripts

### Load Data
```bash
pixi run python scripts/load_my_green_button_data.py
```

Loads all files configured in `config.local.yml`

### View Loaded Data
```bash
pixi run python scripts/view_loaded_data.py
```

Shows summary of all loaded data by home and commodity

### Query Custom Data
```bash
pixi run python

import dlt
pipeline = dlt.pipeline(
    pipeline_name="green_button",
    destination="duckdb",
    dataset_name="raw"
)

with pipeline.sql_client() as client:
    with client.execute_query("""
        SELECT * FROM green_button_interval_readings
        WHERE timestamp >= '2025-01-01'
        ORDER BY timestamp
    """) as cursor:
        for row in cursor.fetchall():
            print(row)
```

## Data Schema

Table: `green_button_interval_readings`

Key fields:
- `home_id` - Your configured home identifier
- `timestamp` - Reading timestamp (UTC)
- `kwh` - Consumption value (kWh for electricity, m³ for gas/water)
- `cost` - Cost in cents (divide by 100 for dollars)
- `commodity` - ESPI commodity code (decode with scripts)
- `service_kind` - Service type (electricity, gas, water)
- `quality_code` - Data quality (VALIDATED, ESTIMATED, etc.)
- `tou_bucket` - Time-of-use tier (1=on-peak, 2=mid-peak, 3=off-peak)

Primary key: `[home_id, usage_point_idx, meter_reading_idx, timestamp]`

## Next Steps

After loading your data:

1. **Transform with dbt**: `pixi run dbt-run` (see transform/ directory)
2. **Create dashboard**: Use Evidence.dev dashboard (see dashboard/ directory)
3. **Export to Paimon**: For long-term storage (see scripts/export_to_paimon.py)
