# Weather and Air Quality Data Integration

This document describes the integration of historical weather and air quality data with electricity consumption data to enable temperature-normalized analysis, HVAC usage identification, and air quality impact analysis.

## Overview

Weather and air quality data are fetched from Open-Meteo APIs and joined with hourly electricity consumption data. This enables:

- Temperature vs consumption correlation analysis
- Heating/Cooling Degree Day (HDD/CDD) calculations
- Weather-normalized consumption metrics
- HVAC-related usage pattern identification
- Solar panel soiling analysis (aerosol optical depth)
- Air quality impact on HVAC usage (windows closed during poor air quality)
- UV index correlation with cooling demand
- Seasonal analysis

## Data Sources

### Open-Meteo Historical Weather API

- **API**: https://archive-api.open-meteo.com/v1/archive
- **Documentation**: https://open-meteo.com/en/docs/historical-weather-api
- **Cost**: Free, no API key required
- **Coverage**: Historical data from 1940 to near real-time
- **Rate Limits**: None for archive data
- **Update Frequency**: Daily (for historical data)

### Open-Meteo Air Quality API

- **API**: https://air-quality-api.open-meteo.com/v1/air-quality
- **Documentation**: https://open-meteo.com/en/docs/air-quality-api
- **Cost**: Free, no API key required
- **Coverage**: Historical data from 1940 to near real-time
- **Rate Limits**: None
- **Update Frequency**: Daily (for historical data)
- **Variables**: PM2.5, PM10, ozone, NO2, SO2, CO, UV index, aerosol optical depth, dust

### Data Quality

For Toronto area (2022-12-25 to 2024-12-23):
- **Total records**: 17,520 hours
- **Missing values**: 0%
- **Temperature range**: -25.1°C to 31.9°C
- **Average temperature**: 10.1°C

### Alternative Data Sources

**Environment Canada** (documented for future use):
- Official government weather data
- Historical climate data available via API or CSV download
- Requires identifying nearest weather station
- More authoritative for Canadian locations
- May have better local accuracy for specific stations

## Implementation

### Pipeline Architecture

```
Open-Meteo Weather API → dlt pipeline → DuckDB (raw.weather_hourly)
                                              ↓
                                       dbt staging (stg_weather_hourly)
                                              ↓
Open-Meteo Air Quality API → dlt pipeline → DuckDB (raw.air_quality_hourly)
                                              ↓
                                       dbt staging (stg_air_quality_hourly)
                                              ↓
                              dbt mart (fct_electricity_with_weather)
                              [joins weather + air quality + electricity]
```

### Files

**dlt Pipelines**:
- `/pipelines/weather/source.py` - Weather data fetching and loading
- `/pipelines/weather/air_quality.py` - Air quality data fetching and loading
- `/scripts/test_weather_pipeline.py` - Weather pipeline test script
- `/scripts/test_air_quality_pipeline.py` - Air quality pipeline test script

**dbt Models**:
- `/transform/models/staging/stg_weather_hourly.sql` - Weather staging view
- `/transform/models/staging/stg_air_quality_hourly.sql` - Air quality staging view
- `/transform/models/marts/fct_electricity_with_weather.sql` - Joined consumption + weather + air quality

**Configuration**:
- `config.example.yml` - Weather and air quality configuration section
- `config.local.yml` - Local overrides (git-ignored)

### Configuration

Add to `config.local.yml`:

```yaml
weather:
  enabled: true
  latitude: 43.65      # Toronto
  longitude: -79.38
  location_name: "toronto"
  start_date: "2022-12-25"
  end_date: "2024-12-23"
  source: "open_meteo"
```

### Running the Pipeline

```bash
# Load weather data
pixi run pipeline-weather

# Load air quality data
pixi run pipeline-air-quality

# Run dbt models
cd transform
pixi run dbt run --select stg_weather_hourly
pixi run dbt run --select stg_air_quality_hourly
pixi run dbt run --select fct_electricity_with_weather
```

## Data Models

### Raw Data: `raw.weather_hourly`

Loaded by dlt from Open-Meteo API.

#### Metadata Columns

| Column | Type | Description |
|--------|------|-------------|
| location_name | varchar | Location identifier (e.g., "toronto") |
| latitude | double | Actual latitude used by API |
| longitude | double | Actual longitude used by API |
| elevation_m | double | Elevation in meters |
| timezone | varchar | Timezone name (e.g., "America/Toronto") |
| timestamp | timestamp | Measurement timestamp (local timezone) |

#### Basic Meteorology

| Column | Type | Description |
|--------|------|-------------|
| temperature_c | double | Temperature in Celsius |
| humidity_pct | double | Relative humidity (0-100) |
| precipitation_mm | double | Precipitation in millimeters |
| windspeed_kmh | double | Wind speed in km/h |

#### Cloud Cover (%)

| Column | Type | Description |
|--------|------|-------------|
| cloud_cover_pct | integer | Total cloud cover (0-100%) |
| cloud_cover_low_pct | integer | Low clouds 0-2km altitude (0-100%) |
| cloud_cover_mid_pct | integer | Mid clouds 2-6km altitude (0-100%) |
| cloud_cover_high_pct | integer | High clouds 6km+ altitude (0-100%) |

#### Solar Radiation (W/m²)

| Column | Type | Description |
|--------|------|-------------|
| ghi_wm2 | double | Global Horizontal Irradiance (total solar on horizontal surface) |
| dni_wm2 | double | Direct Normal Irradiance (direct solar perpendicular to sun) |
| dhi_wm2 | double | Diffuse Horizontal Irradiance (scattered solar on horizontal surface) |
| direct_horizontal_wm2 | double | Direct solar radiation on horizontal plane |
| sunshine_duration_s | double | Sunshine seconds in preceding hour (0-3600s, calculated when DNI > 120 W/m²) |

### Staging: `stg_weather_hourly`

Adds date components, temperature categories, and quality flags.

Additional columns:
- `hour`, `date`, `year`, `month`, `day`, `hour_of_day`, `day_of_week`
- `temperature_category` - Categorizes temp as very_cold, cold, cool, mild, warm, hot
- `quality` - Data quality flag (valid, missing, out_of_range)
- `is_valid_temperature` - Boolean for reasonable range (-40°C to 40°C)

### Mart: `fct_electricity_with_weather`

Joins electricity consumption with weather data at hourly level.

Additional weather columns:
- `temperature_c`, `humidity_pct`, `precipitation_mm`, `windspeed_kmh`
- `temperature_category` - Temperature classification
- `hvac_season` - heating, cooling, or shoulder season
- `hdh` - Heating Degree Hours (base 18°C)
- `cdh` - Cooling Degree Hours (base 18°C)
- `missing_weather_data` - Boolean flag for missing weather

### Join Completeness

Current data (Toronto, 2022-2024):
- Total electricity records: 17,524
- Joined with weather: 17,519 (99.97%)
- Missing weather: 5 records (0.03%)

Missing records are typically at the boundary of the date range.

## Heating/Cooling Degree Days

### Base Temperature

We use 18°C (64.4°F) as the base temperature, which is the standard for Canadian residential buildings. This represents the outdoor temperature below which heating is typically needed (or above which cooling is needed).

### Calculation

**Heating Degree Hours (HDH)**:
```
HDH = max(0, 18°C - hourly_temperature)
```

**Cooling Degree Hours (CDH)**:
```
CDH = max(0, hourly_temperature - 18°C)
```

**Daily Degree Days**:
```sql
HDD = SUM(hdh) / 24.0  -- Average over 24 hours
CDD = SUM(cdh) / 24.0
```

### Usage

Degree days are useful for:
- Normalizing consumption across different weather conditions
- Comparing usage between years or locations
- Predicting HVAC-related consumption
- Benchmarking against similar homes

Example query:
```sql
SELECT
    DATE_TRUNC('day', timestamp) as date,
    SUM(hdh) / 24.0 as hdd,
    SUM(cdh) / 24.0 as cdd,
    SUM(kwh) as daily_kwh
FROM main_marts.fct_electricity_with_weather
GROUP BY date
ORDER BY date
```

## Temperature vs Consumption Analysis

### Sample Results (Toronto, 2022-2024)

Average consumption by temperature category:

| Category | Season | Records | Avg kWh/hour | Total kWh |
|----------|--------|---------|--------------|-----------|
| Hot (>25°C) | cooling | 646 | 1,122 | 724,973 |
| Warm (20-25°C) | cooling | 1,220 | 870 | 1,061,175 |
| Warm (20-25°C) | shoulder | 1,340 | 812 | 1,088,376 |
| Mild (10-20°C) | shoulder | 1,426 | 665 | 948,719 |
| Cold (0-10°C) | heating | 2,640 | 657 | 1,734,728 |
| Cool (0-10°C) | heating | 5,995 | 571 | 3,425,930 |
| Mild (10-20°C) | heating | 4,055 | 549 | 2,226,005 |
| Very Cold (<-10°C) | heating | 197 | 532 | 104,859 |

### Insights

1. **Highest usage**: Hot days (>25°C) with cooling = 1,122 kWh/hour average
2. **Heating season**: Most hours fall in cool/cold heating season (5,995 + 2,640 = 8,635 hours)
3. **Cooling season**: Warm/hot cooling days = 1,866 hours
4. **Base load**: Minimum average ~532-549 kWh/hour (very cold and mild heating days)

## Solar Modeling with PVLIB

### Available Solar Data

The weather pipeline now includes comprehensive solar radiation data suitable for PVLIB modeling:

- **GHI** (Global Horizontal Irradiance): Total solar radiation on a horizontal surface
- **DNI** (Direct Normal Irradiance): Direct solar radiation perpendicular to the sun
- **DHI** (Diffuse Horizontal Irradiance): Scattered solar radiation on a horizontal surface
- **Cloud Cover**: Total and layered (low/mid/high) for estimation and validation
- **Sunshine Duration**: Actual sunshine hours for validation

### Example: Daily Solar Summary

```sql
SELECT
    DATE(timestamp) as date,
    ROUND(AVG(cloud_cover_pct), 0) as avg_cloud_pct,
    ROUND(AVG(ghi_wm2), 0) as avg_ghi_wm2,
    ROUND(MAX(ghi_wm2), 0) as peak_ghi_wm2,
    ROUND(SUM(sunshine_duration_s) / 3600.0, 1) as sunshine_hours,
    ROUND(AVG(kwh), 0) as avg_consumption_kwh
FROM main_marts.fct_electricity_with_weather
WHERE DATE(timestamp) BETWEEN '2024-07-01' AND '2024-07-15'
    AND EXTRACT(hour FROM timestamp) BETWEEN 6 AND 20  -- Daylight hours
GROUP BY DATE(timestamp)
ORDER BY date;
```

### Integration with PVLIB

To model solar PV generation:

1. Install PVLIB: `pixi add pvlib-python`
2. Define PV system parameters (location, tilt, azimuth, panel specs)
3. Use GHI/DNI/DHI from `fct_electricity_with_weather`
4. Calculate plane-of-array irradiance
5. Model DC power output
6. Apply inverter efficiency for AC power

See `/docs/architecture/weather-data-source-evaluation.md` for detailed solar modeling guidance.

## Air Quality Integration

### Overview

Air quality data provides insights into:
- **Solar panel performance**: Aerosol optical depth indicates atmospheric opacity that reduces solar generation
- **HVAC usage patterns**: Poor air quality days may increase HVAC usage (windows closed, recirculation mode)
- **Health impacts**: PM2.5 and PM10 correlate with respiratory health
- **UV exposure**: UV index correlates with outdoor activity and cooling demand
- **Maintenance timing**: High particulate levels indicate air filter replacement needs

### Data Models

#### Raw Data: `raw.air_quality_hourly`

Loaded by dlt from Open-Meteo Air Quality API.

| Column | Type | Description |
|--------|------|-------------|
| location_name | varchar | Location identifier (e.g., "toronto") |
| timestamp | timestamp | Measurement timestamp (local timezone) |
| pm2_5 | double | PM2.5 particulate matter (µg/m³) - primary health metric |
| pm10 | double | PM10 particulate matter (µg/m³) - health and HVAC filter impact |
| dust | double | Dust concentration (µg/m³) - solar panel soiling |
| ozone | double | Ozone (O3) concentration (µg/m³) |
| nitrogen_dioxide | double | Nitrogen dioxide (NO2) concentration (µg/m³) |
| sulphur_dioxide | double | Sulphur dioxide (SO2) concentration (µg/m³) |
| carbon_monoxide | double | Carbon monoxide (CO) concentration (mg/m³) |
| uv_index | double | UV index (0-11+) |
| uv_index_clear_sky | double | UV index under clear sky conditions |
| aerosol_optical_depth | double | Aerosol optical depth (dimensionless) - solar impact |
| european_aqi | integer | European Air Quality Index (0-100+) |

#### Staging: `stg_air_quality_hourly`

Adds date components, air quality categories, and quality flags.

Additional columns:
- `hour`, `date`, `year`, `month`, `day`, `hour_of_day`, `day_of_week`
- `pm2_5_category` - Air quality category based on PM2.5 (good, moderate, unhealthy_sensitive, unhealthy, very_unhealthy)
- `aqi_category` - European AQI category (good, fair, moderate, poor, very_poor, extremely_poor)
- `uv_category` - UV index category (low, moderate, high, very_high, extreme)
- `is_high_pollution` - Boolean flag for PM2.5 > 35 or AQI > 60
- `is_high_soiling_risk` - Boolean flag for high aerosol or dust

#### Air Quality Categories

**PM2.5 Categories (µg/m³)**:
- Good: 0-12
- Moderate: 12-35
- Unhealthy for sensitive groups: 35-55
- Unhealthy: 55-150
- Very unhealthy: 150+

**European AQI Categories**:
- Good: 0-20
- Fair: 20-40
- Moderate: 40-60
- Poor: 60-80
- Very poor: 80-100
- Extremely poor: 100+

**UV Index Categories**:
- Low: 0-3
- Moderate: 3-6
- High: 6-8
- Very high: 8-11
- Extreme: 11+

### Use Cases

#### 1. Solar Panel Soiling Analysis

High aerosol optical depth (AOD) and dust levels indicate atmospheric conditions that can soil solar panels, reducing their efficiency.

```sql
SELECT
    DATE(timestamp) as date,
    ROUND(AVG(aerosol_optical_depth), 3) as avg_aod,
    ROUND(AVG(dust), 1) as avg_dust_ugm3,
    COUNT(CASE WHEN is_high_soiling_risk THEN 1 END) as high_risk_hours,
    ROUND(AVG(ghi_wm2), 0) as avg_solar_wm2
FROM main_marts.fct_electricity_with_weather
WHERE DATE(timestamp) BETWEEN '2024-06-01' AND '2024-08-31'
GROUP BY DATE(timestamp)
HAVING avg_aod > 0.2
ORDER BY avg_aod DESC
LIMIT 10;
```

**Interpretation**:
- AOD > 0.3: Significant atmospheric haze, consider panel cleaning
- AOD > 0.5: Heavy haze or smoke, solar generation significantly impacted
- High dust + high AOD: Optimal time to schedule panel cleaning

#### 2. HVAC Usage During Poor Air Quality

Poor air quality may increase HVAC usage as occupants close windows and run HVAC in recirculation mode.

```sql
SELECT
    pm2_5_category,
    COUNT(*) as hours,
    ROUND(AVG(kwh), 0) as avg_kwh_per_hour,
    ROUND(AVG(pm2_5), 1) as avg_pm2_5
FROM main_marts.fct_electricity_with_weather
WHERE temperature_c BETWEEN 15 AND 25  -- Shoulder season (would normally open windows)
GROUP BY pm2_5_category
ORDER BY avg_pm2_5;
```

**Expected pattern**: Higher consumption during poor air quality in shoulder seasons when windows would normally be open for natural ventilation.

#### 3. UV Index and Cooling Demand

High UV index correlates with increased cooling demand and outdoor activity patterns.

```sql
SELECT
    uv_category,
    COUNT(*) as hours,
    ROUND(AVG(temperature_c), 1) as avg_temp_c,
    ROUND(AVG(kwh), 0) as avg_kwh_per_hour,
    ROUND(AVG(cdh), 1) as avg_cooling_degree_hours
FROM main_marts.fct_electricity_with_weather
WHERE EXTRACT(month FROM timestamp) BETWEEN 6 AND 8  -- Summer months
    AND EXTRACT(hour FROM timestamp) BETWEEN 10 AND 18  -- Daytime
GROUP BY uv_category
ORDER BY avg_temp_c;
```

#### 4. Air Filter Replacement Timing

Track cumulative particulate exposure to optimize HVAC filter replacement.

```sql
SELECT
    DATE_TRUNC('month', timestamp) as month,
    COUNT(*) as hours,
    ROUND(AVG(pm2_5), 1) as avg_pm2_5,
    ROUND(AVG(pm10), 1) as avg_pm10,
    COUNT(CASE WHEN pm2_5_category IN ('unhealthy_sensitive', 'unhealthy', 'very_unhealthy') THEN 1 END) as poor_air_hours,
    ROUND(SUM(pm2_5) / 1000.0, 2) as cumulative_pm2_5_mg  -- Convert to mg
FROM main_marts.fct_electricity_with_weather
GROUP BY DATE_TRUNC('month', timestamp)
ORDER BY month DESC;
```

**Recommendation**: Replace filters more frequently during high pollution months.

#### 5. Health Impact Days

Identify days with poor air quality for health awareness and ventilation planning.

```sql
SELECT
    DATE(timestamp) as date,
    ROUND(AVG(pm2_5), 1) as avg_pm2_5,
    ROUND(MAX(pm2_5), 1) as peak_pm2_5,
    pm2_5_category,
    ROUND(AVG(temperature_c), 1) as avg_temp_c,
    COUNT(*) as hours
FROM main_marts.fct_electricity_with_weather
WHERE pm2_5_category IN ('unhealthy_sensitive', 'unhealthy', 'very_unhealthy')
GROUP BY DATE(timestamp), pm2_5_category
ORDER BY avg_pm2_5 DESC
LIMIT 20;
```

### Air Quality and Energy Correlations

Key hypotheses to test:
1. **Poor air quality + shoulder season → increased HVAC usage** (closed windows)
2. **High aerosol optical depth → reduced solar generation potential**
3. **High UV index + high temperature → increased cooling demand**
4. **High particulate matter → more frequent filter changes → increased HVAC resistance**

### Data Completeness

For Toronto (2022-12-25 to 2024-12-23):
- Air quality data coverage aligns with weather data
- Some variables may have NULL values depending on data availability
- European AQI is calculated from available pollutants

## Quick Start

To run the complete weather and air quality integration:

```bash
# 1. Load weather data
pixi run pipeline-weather

# 2. Load air quality data
pixi run pipeline-air-quality

# 3. Build dbt models
cd transform
pixi run dbt run --select stg_weather_hourly stg_air_quality_hourly fct_electricity_with_weather

# 4. Run analysis
cd ..
pixi run analyze-weather
pixi run analyze-air-quality
```

## Analysis Examples

### Example 1: Find High Solar Soiling Risk Days

```sql
SELECT
    DATE(timestamp) as date,
    ROUND(AVG(aerosol_optical_depth), 3) as avg_aod,
    ROUND(AVG(dust), 1) as avg_dust,
    ROUND(AVG(pm2_5), 1) as avg_pm2_5,
    COUNT(*) as hours,
    ROUND(AVG(ghi_wm2), 0) as avg_solar_wm2
FROM main_marts.fct_electricity_with_weather
WHERE aerosol_optical_depth > 0.3  -- High soiling risk
GROUP BY DATE(timestamp)
ORDER BY avg_aod DESC;
```

**Use case**: Schedule solar panel cleaning after high aerosol optical depth periods.

### Example 2: HVAC Usage by Air Quality (Shoulder Season)

```sql
SELECT
    pm2_5_category,
    COUNT(*) as hours,
    ROUND(AVG(kwh), 0) as avg_kwh,
    ROUND(AVG(pm2_5), 1) as avg_pm2_5,
    ROUND(AVG(temperature_c), 1) as avg_temp
FROM main_marts.fct_electricity_with_weather
WHERE temperature_c BETWEEN 15 AND 25  -- Shoulder season
    AND pm2_5_category IS NOT NULL
GROUP BY pm2_5_category
ORDER BY avg_pm2_5;
```

**Expected finding**: Higher HVAC consumption during poor air quality days when windows would normally be open.

### Example 3: UV Index and Cooling Demand

```sql
SELECT
    DATE(timestamp) as date,
    ROUND(AVG(uv_index), 1) as avg_uv,
    ROUND(MAX(uv_index), 1) as peak_uv,
    ROUND(AVG(temperature_c), 1) as avg_temp,
    ROUND(SUM(kwh), 0) as daily_kwh,
    ROUND(SUM(cdh) / 24.0, 1) as cooling_degree_days
FROM main_marts.fct_electricity_with_weather
WHERE EXTRACT(month FROM timestamp) IN (6, 7, 8)  -- Summer
GROUP BY DATE(timestamp)
ORDER BY avg_uv DESC
LIMIT 20;
```

**Use case**: Understand UV index correlation with cooling demand and outdoor activity patterns.

### Example 4: Monthly Air Filter Replacement Timing

```sql
SELECT
    DATE_TRUNC('month', timestamp) as month,
    ROUND(AVG(pm2_5), 1) as avg_pm2_5,
    ROUND(MAX(pm2_5), 1) as peak_pm2_5,
    COUNT(CASE WHEN pm2_5 > 35 THEN 1 END) as unhealthy_hours,
    ROUND(SUM(pm2_5) / 1000.0, 2) as cumulative_pm2_5_mg
FROM main_marts.fct_electricity_with_weather
GROUP BY DATE_TRUNC('month', timestamp)
ORDER BY month DESC;
```

**Use case**: Schedule more frequent HVAC filter replacements during high particulate months.

## Real-World Findings (Toronto 2022-2024)

Based on actual data analysis:

1. **2023 Canadian Wildfire Impact**:
   - June 2023 saw extreme aerosol optical depth (AOD up to 3.6)
   - PM2.5 levels reached 148.5 µg/m³ (very unhealthy)
   - Solar radiation significantly impacted (reduced GHI)
   - Recommendation: Solar panel cleaning was critical after this period

2. **Air Quality Impact on HVAC**:
   - 31% higher consumption during unhealthy air quality in shoulder season
   - Good air quality (15-25°C): 668 kWh/hour average
   - Unhealthy air quality (15-25°C): 875 kWh/hour average
   - Hypothesis confirmed: Closed windows increase HVAC usage

3. **Seasonal Air Quality Patterns**:
   - Best air quality: November-December (avg PM2.5: 4.6-5.5 µg/m³)
   - Worst air quality: May-August (avg PM2.5: 14.1-17.9 µg/m³)
   - Summer months have 40+ hours of unhealthy air per month

4. **UV Index Correlation**:
   - Summer daytime UV averages 2.4 (peaks at 8.3)
   - Very high UV days: 26.6°C average temperature
   - Clear correlation between UV, temperature, and cooling demand

## Future Enhancements

### Additional Weather Variables

Open-Meteo supports many more variables that could be useful:
- Dew point (affects humidity and comfort)
- Pressure (affects furnace efficiency)
- Snow depth and snowfall
- Soil temperature and moisture

### Weather-Normalized Metrics

Create calculated metrics:
- Baseline consumption (non-weather dependent)
- HVAC-specific consumption
- Efficiency metrics (kWh per degree day)
- Anomaly detection (unusual consumption for weather)

### Multi-Location Support

Currently configured for Toronto. To support multiple homes:
1. Add location coordinates to `stg_dim_homes`
2. Modify weather pipeline to fetch data for each unique location
3. Update join in `fct_electricity_with_weather` to match by location

### Environment Canada Integration

For more authoritative Canadian data:
1. Identify nearest weather station for each location
2. Fetch data via Environment Canada API or bulk CSV downloads
3. Compare data quality and coverage with Open-Meteo
4. Document station IDs and their coverage

### Dashboard Integration

Next steps for visualization:
- Temperature vs consumption scatter plots
- Seasonal consumption patterns
- HDD/CDD correlation charts
- Weather-normalized consumption metrics
- Year-over-year comparisons (weather-adjusted)

## References

- [Open-Meteo Historical Weather API](https://open-meteo.com/en/docs/historical-weather-api)
- [Environment Canada Historical Data](https://climate.weather.gc.ca/)
- [Degree Day Calculation Methods](https://www.nrcan.gc.ca/energy/efficiency/housing/science/heating-degree-days/17072)
- [Ontario Building Code - Heating Degree Days](https://www.ontario.ca/laws/regulation/120332)
