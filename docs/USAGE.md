# Usage Guide

How to run pipelines, query data, and export results.

## Table of Contents

- [Running Pipelines](#running-pipelines)
- [Querying Data](#querying-data)
- [Exporting to Paimon](#exporting-to-paimon)
- [Scheduling with Cron](#scheduling-with-cron)
- [Example Queries](#example-queries)

## Running Pipelines

### Manual Execution

**Run Complete Pipeline (dlt + dbt)**

```bash
# Test pipeline with all steps
pixi run python scripts/test_full_pipeline.py
```

This runs:
1. dlt load (Green Button XML → DuckDB raw tables)
2. dbt transformations (raw → staging → marts)
3. Data validation

**Run Individual Steps**

```bash
# Step 1: Load Green Button data only
pixi run python scripts/test_green_button_pipeline.py

# Step 2: Load Home Assistant data only
pixi run python scripts/test_ha_pipeline.py

# Step 3: Run dbt transformations only
cd transform
pixi run dbt run --profiles-dir . --project-dir .

# Step 4: Run specific dbt models
pixi run dbt run --select stg_green_button --profiles-dir . --project-dir .
pixi run dbt run --select fct_electricity_consumption --profiles-dir . --project-dir .
```

**Run Combined Pipeline (Multiple Sources)**

```bash
# Load both Green Button and Home Assistant, then transform
pixi run python scripts/test_combined_pipeline.py
```

### Pipeline Options

**Green Button Pipeline**

```bash
# Basic usage
pixi run python scripts/test_green_button_pipeline.py

# With custom XML file
pixi run python -c "
from pathlib import Path
from pipelines.green_button import green_button_source
import dlt

pipeline = dlt.pipeline(
    pipeline_name='green_button',
    destination='duckdb',
    dataset_name='raw'
)

data = green_button_source(
    xml_file_path='data/greenbutton/myfile.xml',
    home_id='home-001'
)

pipeline.run(data)
"
```

**Home Assistant Pipeline**

```bash
# Generate mock data first
pixi run python scripts/generate_mock_ha_data.py

# Run pipeline
pixi run python scripts/test_ha_pipeline.py
```

**Multiple Homes**

Load data for multiple homes:

```python
# Example: Load data for 3 homes
import dlt
from pipelines.green_button import green_button_source

pipeline = dlt.pipeline(
    pipeline_name='energy_warehouse',
    destination='duckdb',
    dataset_name='raw'
)

homes = [
    {'id': 'home-001', 'file': 'data/greenbutton/home1.xml'},
    {'id': 'home-002', 'file': 'data/greenbutton/home2.xml'},
    {'id': 'home-003', 'file': 'data/greenbutton/home3.xml'},
]

for home in homes:
    data = green_button_source(
        xml_file_path=home['file'],
        home_id=home['id']
    )
    pipeline.run(data)
```

### Data Quality Checks

**Run dbt Tests**

```bash
cd transform
pixi run dbt test --profiles-dir . --project-dir .
```

**Check for Data Issues**

```bash
# Idempotency test (verify re-running doesn't create duplicates)
pixi run python scripts/test_idempotency.py
```

## Querying Data

### Interactive DuckDB CLI

```bash
# Open DuckDB CLI
pixi run duckdb energy_warehouse.duckdb
```

```sql
-- List all tables
SHOW TABLES;

-- List schemas
SELECT DISTINCT schema_name FROM information_schema.schemata;

-- Show table structure
DESCRIBE main_marts.fct_electricity_consumption;

-- Count records
SELECT COUNT(*) FROM main_marts.fct_electricity_consumption;
```

### Python Queries

```python
import duckdb

# Connect to warehouse
con = duckdb.connect('energy_warehouse.duckdb')

# Simple query
result = con.execute("""
    SELECT
        home_id,
        DATE(timestamp) as date,
        SUM(kwh) as daily_kwh,
        SUM(cost) as daily_cost_cents
    FROM main_marts.fct_electricity_consumption
    WHERE source = 'green_button'
    GROUP BY home_id, DATE(timestamp)
    ORDER BY date DESC
    LIMIT 30
""").df()

print(result)

con.close()
```

### Common Query Patterns

**Daily Consumption Summary**

```sql
SELECT
    home_id,
    DATE(timestamp) as date,
    SUM(kwh) as daily_kwh,
    SUM(cost) / 100.0 as daily_cost_dollars,
    AVG(kwh) as avg_hourly_kwh,
    MAX(kwh) as peak_hourly_kwh
FROM main_marts.fct_electricity_consumption
GROUP BY home_id, DATE(timestamp)
ORDER BY date DESC;
```

**Time-of-Use Analysis**

```sql
SELECT
    home_id,
    tou_period,
    COUNT(*) as hours,
    SUM(kwh) as total_kwh,
    AVG(kwh) as avg_kwh,
    SUM(cost) / 100.0 as total_cost_dollars
FROM main_marts.fct_electricity_consumption
WHERE tou_period IS NOT NULL
GROUP BY home_id, tou_period
ORDER BY tou_period;
```

**Monthly Trends**

```sql
SELECT
    home_id,
    year,
    month,
    SUM(kwh) as monthly_kwh,
    SUM(cost) / 100.0 as monthly_cost_dollars,
    AVG(kwh) as avg_hourly_kwh
FROM main_marts.fct_electricity_consumption
GROUP BY home_id, year, month
ORDER BY year DESC, month DESC;
```

**Data Quality Check**

```sql
SELECT
    source,
    quality,
    estimated,
    COUNT(*) as record_count,
    SUM(kwh) as total_kwh
FROM main_marts.fct_electricity_consumption
GROUP BY source, quality, estimated
ORDER BY source, quality;
```

**Peak Usage Hours**

```sql
SELECT
    home_id,
    timestamp,
    kwh,
    tou_period,
    CASE
        WHEN EXTRACT(hour FROM timestamp) BETWEEN 0 AND 6 THEN 'Night'
        WHEN EXTRACT(hour FROM timestamp) BETWEEN 7 AND 11 THEN 'Morning'
        WHEN EXTRACT(hour FROM timestamp) BETWEEN 12 AND 17 THEN 'Afternoon'
        ELSE 'Evening'
    END as time_of_day
FROM main_marts.fct_electricity_consumption
WHERE kwh >= (
    SELECT PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY kwh)
    FROM main_marts.fct_electricity_consumption
)
ORDER BY kwh DESC
LIMIT 20;
```

## Exporting to Paimon

Export your DuckDB warehouse to Parquet files for long-term storage and portability.

### Basic Export

```bash
# Export all tables to Parquet
pixi run python scripts/export_to_paimon.py
```

This creates Hive-style partitioned Parquet files:

```
~/energy-data/warehouse/
├── electricity_consumption/
│   ├── home_id=home-001/
│   │   ├── year=2024/
│   │   │   ├── month=01/
│   │   │   │   └── data.parquet
│   │   │   ├── month=02/
│   │   │   └── ...
│   └── home_id=home-002/
│       └── ...
└── power_monitoring/
    ├── home_id=home-001/
    │   ├── device_id=emporia_vue_main/
    │   │   └── data.parquet
    │   └── device_id=iotawatt_001/
    └── ...
```

### Query Exported Parquet Files

**With DuckDB:**

```sql
-- Query Parquet files directly
SELECT * FROM read_parquet('~/energy-data/warehouse/electricity_consumption/**/*.parquet')
WHERE home_id = 'home-001'
LIMIT 10;

-- Aggregate across all partitions
SELECT
    DATE(timestamp) as date,
    SUM(kwh) as daily_kwh
FROM read_parquet('~/energy-data/warehouse/electricity_consumption/**/*.parquet')
GROUP BY DATE(timestamp)
ORDER BY date DESC;
```

**With Python (Pandas):**

```python
import pandas as pd

# Read specific partition
df = pd.read_parquet('~/energy-data/warehouse/electricity_consumption/home_id=home-001/year=2024/month=12/')

# Read all data for a home
df = pd.read_parquet('~/energy-data/warehouse/electricity_consumption/home_id=home-001/')

print(df.head())
```

**With Python (Polars - faster for large datasets):**

```python
import polars as pl

# Read Parquet files
df = pl.read_parquet('~/energy-data/warehouse/electricity_consumption/**/*.parquet')

# Filter and aggregate
result = (
    df
    .filter(pl.col('home_id') == 'home-001')
    .group_by(pl.col('timestamp').dt.date())
    .agg(pl.col('kwh').sum())
)

print(result)
```

### Backup and Sync

**Backup to External Drive:**

```bash
# Sync to external drive
rsync -av --progress ~/energy-data/warehouse/ /Volumes/Backup/energy-warehouse/

# Or use rclone for cloud backup (encrypted)
rclone sync ~/energy-data/warehouse/ gdrive-crypt:energy-warehouse
```

**Version Control Data:**

```bash
# Create timestamped snapshot
DATE=$(date +%Y%m%d)
cp -r ~/energy-data/warehouse ~/energy-data/snapshots/warehouse-$DATE
```

## Scheduling with Cron

Automate pipeline runs with cron jobs.

### Setup

**1. Make scripts executable:**

```bash
chmod +x scripts/test_full_pipeline.py
```

**2. Create wrapper script:**

Create `scripts/run_daily_pipeline.sh`:

```bash
#!/bin/bash
# Daily energy data pipeline
set -e

# Change to project directory
cd /Users/yourusername/open-data-coop

# Activate pixi environment and run pipeline
/usr/local/bin/pixi run python scripts/test_full_pipeline.py >> logs/pipeline.log 2>&1

# Export to Parquet
/usr/local/bin/pixi run python scripts/export_to_paimon.py >> logs/export.log 2>&1

# Send completion notification (optional)
echo "Energy pipeline completed at $(date)" | mail -s "Pipeline Success" you@example.com
```

**3. Make wrapper executable:**

```bash
chmod +x scripts/run_daily_pipeline.sh
```

**4. Edit crontab:**

```bash
crontab -e
```

Add this line to run daily at 2 AM:

```cron
0 2 * * * /Users/yourusername/open-data-coop/scripts/run_daily_pipeline.sh
```

### Cron Schedule Examples

```cron
# Every hour
0 * * * * /path/to/run_pipeline.sh

# Every 6 hours
0 */6 * * * /path/to/run_pipeline.sh

# Daily at 2 AM
0 2 * * * /path/to/run_pipeline.sh

# Weekly on Sunday at 3 AM
0 3 * * 0 /path/to/run_pipeline.sh

# Monthly on the 1st at 4 AM
0 4 1 * * /path/to/run_pipeline.sh
```

### Monitoring

**Check cron logs:**

```bash
# View recent pipeline runs
tail -f logs/pipeline.log

# Check for errors
grep -i error logs/pipeline.log

# View cron system logs (macOS)
log show --predicate 'process == "cron"' --last 1d
```

**Monitor disk usage:**

```bash
# Check DuckDB size
du -h energy_warehouse.duckdb

# Check Parquet exports
du -sh ~/energy-data/warehouse/

# Alert if database exceeds 10GB
SIZE=$(du -m energy_warehouse.duckdb | cut -f1)
if [ $SIZE -gt 10240 ]; then
    echo "WARNING: Database exceeds 10GB" | mail -s "Disk Alert" you@example.com
fi
```

## Example Queries

### Heat Pump Analysis

Calculate effective COP (Coefficient of Performance):

```sql
-- Requires temperature data from Home Assistant
WITH daily_stats AS (
    SELECT
        DATE(ec.timestamp) as date,
        SUM(ec.kwh) as hvac_kwh,
        AVG(temp.outdoor_temp) as avg_outdoor_temp,
        AVG(temp.indoor_temp) as avg_indoor_temp
    FROM main_marts.fct_electricity_consumption ec
    LEFT JOIN temperature_sensors temp ON DATE(temp.timestamp) = DATE(ec.timestamp)
    WHERE ec.device_id LIKE '%hvac%'
    GROUP BY DATE(ec.timestamp)
)
SELECT
    date,
    hvac_kwh,
    avg_outdoor_temp,
    avg_indoor_temp,
    CASE
        WHEN avg_outdoor_temp < 0 THEN hvac_kwh / (avg_indoor_temp - avg_outdoor_temp) * 100
        ELSE NULL
    END as estimated_cop
FROM daily_stats
WHERE avg_outdoor_temp IS NOT NULL
ORDER BY date DESC;
```

### Solar Sizing Analysis

Identify optimal hours for solar generation:

```sql
-- Find hours with highest consistent consumption
SELECT
    EXTRACT(hour FROM timestamp) as hour,
    EXTRACT(month FROM timestamp) as month,
    AVG(kwh) as avg_kwh,
    MIN(kwh) as min_kwh,
    MAX(kwh) as max_kwh,
    STDDEV(kwh) as stddev_kwh
FROM main_marts.fct_electricity_consumption
WHERE EXTRACT(hour FROM timestamp) BETWEEN 9 AND 17  -- Typical solar hours
GROUP BY EXTRACT(hour FROM timestamp), EXTRACT(month FROM timestamp)
ORDER BY month, hour;
```

### Rate Optimization

Compare TOU vs flat rate costs:

```sql
WITH tou_rates AS (
    SELECT
        CASE tou_period
            WHEN '1' THEN 0.187  -- On-peak
            WHEN '2' THEN 0.132  -- Mid-peak
            WHEN '3' THEN 0.092  -- Off-peak
        END as rate_per_kwh
    FROM main_marts.fct_electricity_consumption
),
costs AS (
    SELECT
        DATE(timestamp) as date,
        SUM(kwh) as daily_kwh,
        SUM(kwh * tou_rates.rate_per_kwh) as tou_cost,
        SUM(kwh) * 0.125 as flat_cost  -- Example flat rate
    FROM main_marts.fct_electricity_consumption
    JOIN tou_rates ON TRUE
    GROUP BY DATE(timestamp)
)
SELECT
    date,
    daily_kwh,
    tou_cost,
    flat_cost,
    (tou_cost - flat_cost) as tou_vs_flat_diff,
    CASE
        WHEN tou_cost < flat_cost THEN 'TOU Better'
        ELSE 'Flat Better'
    END as recommendation
FROM costs
ORDER BY date DESC;
```

### Carbon Footprint

Track emissions over time:

```sql
SELECT
    DATE(timestamp) as date,
    SUM(kwh) as daily_kwh,
    SUM(kwh * co2_g_per_kwh) / 1000.0 as daily_co2_kg,
    AVG(co2_g_per_kwh) as avg_grid_intensity
FROM main_marts.fct_electricity_consumption
WHERE co2_g_per_kwh IS NOT NULL
GROUP BY DATE(timestamp)
ORDER BY date DESC;
```

## Next Steps

- **Advanced Analytics**: Integrate with Jupyter notebooks for visualization
- **Dashboard**: Set up Evidence.dev for interactive dashboards
- **Alerts**: Configure notifications for anomalies
- **Research**: Export data for academic research or policy analysis

---

**Need help?** See [docs/FAQ.md](FAQ.md) or open an issue.
