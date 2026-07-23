# Green Button ESPI XML Pipeline

dlt pipeline for loading Green Button (ESPI) XML data into DuckDB.

## Overview

Parses Green Button XML files from Ontario utilities using the `greenbutton_objects` library and loads interval readings into DuckDB with merge disposition for idempotent loads.

## Features

- ✅ **Idempotent loads** — Re-running with same file doesn't duplicate data
- ✅ **Multi-meter support** — Handles multiple usage points and meter readings
- ✅ **Full ESPI metadata** — Preserves quality codes, TOU buckets, costs
- ✅ **UTC timestamps** — All timestamps normalized to UTC
- ✅ **Type-safe** — Uses greenbutton_objects enums

## Usage

### Single File

```python
import dlt
from pipelines.green_button import green_button_source

pipeline = dlt.pipeline(
    pipeline_name="green_button",
    destination="duckdb",
    dataset_name="raw"
)

data = green_button_source(
    xml_file_path="/path/to/greenbutton.xml",
    home_id="beads-abc123"
)

info = pipeline.run(data)
```

### Multiple Files (Same Home)

```python
from pipelines.green_button.source import parse_multiple_files

xml_files = [
    "/path/to/file1.xml",
    "/path/to/file2.xml",
]

data = parse_multiple_files(xml_files, home_id="beads-abc123")
pipeline.run(data)
```

### Command Line

```bash
# Test with Hydro One file
pixi run python scripts/test_green_button_pipeline.py

# Test idempotency
pixi run python scripts/test_idempotency.py
```

## Schema

### Table: `green_button_interval_readings`

| Column | Type | Description |
|--------|------|-------------|
| `home_id` | VARCHAR | Unique home identifier (UUID or beads ID) |
| `usage_point_idx` | INTEGER | Usage point index (0 for single-meter homes) |
| `meter_reading_idx` | INTEGER | Meter reading index |
| `timestamp` | TIMESTAMP | Interval start time (UTC) |
| `duration_seconds` | INTEGER | Interval duration (3600 for hourly) |
| `kwh` | DOUBLE | Energy consumption (kWh or m³ for gas) |
| `raw_value` | INTEGER | Original value before scaling |
| `cost` | DOUBLE | Cost in cents (nullable) |
| `quality_code` | VARCHAR | ESPI quality enum (e.g., `QualityOfReading.VALIDATED`) |
| `tou_bucket` | VARCHAR | Time-of-use bucket (1=on, 2=mid, 3=off, nullable) |
| `commodity` | VARCHAR | Commodity enum (e.g., `CommodityKindValue.VALUE_1` = electricity) |
| `uom` | VARCHAR | Unit of measure enum (e.g., `UnitSymbolKindValue.VALUE_72` = Wh) |
| `service_kind` | VARCHAR | Service kind enum (e.g., `ServiceKind.ELECTRICITY`) |
| `meter_id` | VARCHAR | Meter identifier from URI (nullable) |

**Primary Key:** `(home_id, usage_point_idx, meter_reading_idx, timestamp)`

**Write Disposition:** `merge` (upsert on primary key)

## Data Quality

### Tested with Ontario Utilities

✅ **Hydro One** — 17,520 hourly electricity readings (2022-2024)
✅ **Elexicon/EPC** — 18,250 hourly electricity readings (2022-2024)
✅ **Enbridge Gas** — 20 monthly gas readings (2022-2024)

### Success Rate

- 100% of valid ESPI intervals extracted
- Recovers 24 more readings than stdlib XML parser (0.14% improvement on Hydro One)
- Handles missing values gracefully (no data loss)

## Enum Decoding

The pipeline preserves ESPI enums for data quality. To decode to human-readable values, use dbt staging models:

```sql
-- stg_green_button.sql
SELECT
    home_id,
    timestamp,
    kwh,
    CASE
        WHEN quality_code LIKE '%VALIDATED%' THEN 'validated'
        WHEN quality_code LIKE '%ESTIMATED%' THEN 'estimated'
        WHEN quality_code LIKE '%DERIVED%' THEN 'derived'
        WHEN quality_code LIKE '%PROJECTED%' THEN 'projected'
        ELSE 'unknown'
    END AS quality,
    CASE tou_bucket
        WHEN '1' THEN 'on_peak'
        WHEN '2' THEN 'mid_peak'
        WHEN '3' THEN 'off_peak'
        ELSE NULL
    END AS tou_period,
    CASE
        WHEN commodity LIKE '%VALUE_1%' THEN 'electricity'
        WHEN commodity LIKE '%VALUE_7%' THEN 'natural_gas'
        ELSE 'unknown'
    END AS commodity_type
FROM raw.green_button_interval_readings
```

## Testing

```bash
# Run all tests
pixi run python scripts/test_green_button_pipeline.py
pixi run python scripts/test_idempotency.py

# Expected output:
#   ✓ 17,520 rows loaded
#   ✓ Date range: 2022-12-25 to 2024-12-24
#   ✓ Total kWh: 11,315,321
#   ✓ Idempotent (no duplicates)
```

## Dependencies

- `dlt[duckdb]` — Data load tool
- `greenbutton-objects` — Green Button XML parser (forked to https://github.com/ryanfobel/greenbutton_objects)
- `pandas` — Data manipulation
- `pyarrow` — Parquet support

## Architecture

```
Green Button XML (ESPI)
    ↓
greenbutton_objects.parse_feed()
    ↓
Extract interval_readings
    ↓
dlt resource (merge on primary key)
    ↓
DuckDB: raw.green_button_interval_readings
    ↓
dbt staging models (enum decoding)
    ↓
Paimon warehouse: green_button/ (partitioned by home_id, date)
```

## Next Steps

1. ⬜ Create dbt staging model (`stg_green_button.sql`)
2. ⬜ Create dbt marts model (`fct_electricity_consumption.sql`)
3. ⬜ Add HMAC-based meter_id anonymization
4. ⬜ Export to Paimon with partitioning
5. ⬜ Add incremental loading (track last_processed_file)

## References

- Green Button Alliance: https://www.greenbuttondata.org/
- ESPI Spec: https://naesb.org/espi.xsd
- greenbutton_objects: https://github.com/ryanfobel/greenbutton_objects
- Evaluation: `docs/architecture/greenbutton-objects-test-results.md`
