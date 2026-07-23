# Energy Data Pipelines - Setup Summary

## Configuration Status

✅ **Location**: Kitchener-Waterloo, Ontario
- Coordinates: 43.4516, -80.4925 (City Hall)
- Elevation: 321m
- Timezone: America/Toronto

✅ **Utilities**:
- Water: City of Kitchener
- Electricity: Enova Power (formerly Kitchener-Wilmot Hydro)
- Gas: Enbridge Gas
- Grid: Ontario (IESO)

✅ **Ontario Grid Integration**:
- Carbon intensity database: 25MB, updated July 7
- Path: `/Users/ryan/dev/open-data-coop/projects/ontario-grid-pipelines/`
- Features: Hourly CO₂ intensity, generation mix, TOU periods

## Data Loaded

### Current Status (as of 2026-07-22)

**Home: ryan-home-001**
- Total readings: 19,027
- Date range: Dec 2022 - Jul 2026

**Breakdown by commodity:**

1. **Electricity** (18,994 hourly readings)
   - Date range: Dec 25, 2022 → Jul 22, 2026
   - Source: Enova CSV export (meter 8493100000)
   - Total consumption: 80.35 GWh (likely includes historical test data)
   - TOU buckets: Properly classified (1=on, 2=mid, 3=off)
   - Cost data: Not in CSV (Green Button would have it)

2. **Water** (14 monthly readings)
   - Date range: Jun 12, 2025 → Jul 15, 2026
   - Source: Kitchener Utilities Green Button XML
   - Total cost: $1,150
   - Consumption values: 0 (typical for municipal billing format)

3. **Natural Gas** (19 monthly readings)
   - Date range: Dec 3, 2022 → Jul 4, 2024
   - Source: Previous test data
   - Total consumption: 990 m³

## Supported Data Formats

### 1. Green Button XML (Standard)
- **Format**: `greenbutton_xml`
- **Works with**: All utilities supporting Green Button Connect
- **Contains**: Hourly intervals, costs, TOU, quality codes
- **Status**: ✅ Working (water data loaded)

### 2. Enova Smart Meter CSV
- **Format**: `enova_csv`
- **Utility**: Enova Power (Kitchener-Waterloo)
- **Contains**: Daily rows with 24 hourly kWh columns + TOU summaries
- **Status**: ✅ Working (720 readings loaded)
- **Use when**: Green Button download is broken
- **Location**: `pipelines/canada/ontario/enova_csv/`

### 3. Utility-Bill-Scraper (Monthly)
- **Format**: TBD (see issue `energy-data-pipelines-qv4`)
- **Contains**: Monthly aggregates with TOU breakdown
- **Historical data**: 2017-2019 available
- **Status**: ⏳ Planned

## Regional Structure

```
pipelines/
├── green_button/          # Standard Green Button (universal)
└── canada/
    └── ontario/
        └── enova_csv/     # Enova-specific CSV format
```

This structure allows adding:
- `canada/ontario/hydro_one/` - Hydro One specific formats
- `canada/ontario/toronto_hydro/` - Toronto Hydro
- `canada/alberta/` - Alberta utilities
- etc.

## Configuration File

`config.local.yml`:

```yaml
green_button:
  files:
    # Water (Green Button XML)
    - path: ~/Downloads/Kitchener_Utilities_Water_12_Months.xml
      home_id: ryan-home-001
      commodity: water
      format: greenbutton_xml

    # Electricity (Enova CSV - fallback when Green Button broken)
    - path: ~/Downloads/SmartMeter8493100000_2026-07-2219.00.36.csv
      home_id: ryan-home-001
      commodity: electricity
      format: enova_csv
```

## Known Issues

### Enova Green Button Download
- **Issue**: Download produces 0-byte file
- **Workaround**: Use CSV export instead
- **CSV location**: Customer portal → Usage → Download CSV
- **Tracking**: See issue `energy-data-pipelines-2u5` for third-party research

### Data Quality Notes
1. **Electricity total seems high**: 80.35 GWh over 3.5 years = ~23 GWh/year
   - Likely includes old test data
   - Fresh download will have accurate numbers

2. **Water shows $0 consumption**: Normal for municipal billing
   - Actual usage tracked separately
   - Cost field shows fixed + variable charges

3. **Timezone handling**: Enova CSV uses EST (not EDT)
   - Parser converts to UTC for consistency
   - Ontario grid data also in UTC

## Next Steps

1. ✅ Water data loaded
2. ✅ Electricity CSV parser working
3. ⏳ Add utility-bill-scraper monthly data support
4. ⏳ Re-download fresh electricity data when Enova fixes Green Button
5. ⏳ Run dbt transforms to calculate carbon footprint
6. ⏳ Set up Evidence.dev dashboard

## Scripts

### Load Data
```bash
pixi run python scripts/load_my_green_button_data.py
```

### View Loaded Data
```bash
pixi run python scripts/view_loaded_data.py
```

### Run Transformations (includes carbon calculation)
```bash
pixi run dbt-run
```

## Data Pipeline Flow

```
Raw Data Sources
  ├─ Green Button XML (Kitchener water)
  ├─ Enova CSV (electricity)
  └─ [Future] Utility Bill Scraper (monthly aggregates)
       ↓
  DLT Load (idempotent merge)
       ↓
  DuckDB: raw.green_button_interval_readings
       ↓
  dbt Transform
    ├─ Attach Ontario grid database
    ├─ Join hourly consumption + carbon intensity
    └─ Calculate emissions (kg CO₂e)
       ↓
  DuckDB: analytics.fct_electricity_with_carbon
       ↓
  Evidence.dev Dashboard
```

## Data Privacy

All personal data is excluded from git:
- `config.local.yml` - Your configuration
- `**/Green_Button*.xml` - Downloaded XML files
- `**/SmartMeter*.csv` - Downloaded CSV files
- `~/.dlt/pipelines/*.duckdb` - Processed data

Safe to commit:
- Pipeline source code
- Documentation
- Schema definitions
- dbt transformations
