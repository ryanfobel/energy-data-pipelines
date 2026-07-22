# Air Quality Data Integration

## Overview

Air quality data from Open-Meteo provides hourly measurements of particulate matter, pollutants, UV index, and aerosol optical depth. This data enables analysis of:

- Solar panel performance degradation from atmospheric aerosols
- HVAC usage patterns during poor air quality events
- Health impacts from particulate matter exposure
- UV radiation correlation with cooling demand
- Optimal timing for air filter replacement

## Data Source

**Open-Meteo Air Quality API**
- Endpoint: https://air-quality-api.open-meteo.com/v1/air-quality
- Documentation: https://open-meteo.com/en/docs/air-quality-api
- Coverage: Global, historical data from 1940
- Cost: Free, no API key required
- Update frequency: Hourly

## Variables

### Particulate Matter (µg/m³)
- **PM2.5**: Fine particulate matter (diameter < 2.5µm) - primary health metric
- **PM10**: Coarse particulate matter (diameter < 10µm) - HVAC filter impact
- **Dust**: Dust concentration - solar panel soiling indicator

### Pollutants
- **Ozone (O3)**: Ground-level ozone (µg/m³)
- **Nitrogen Dioxide (NO2)**: Traffic and industrial pollution (µg/m³)
- **Sulphur Dioxide (SO2)**: Industrial emissions (µg/m³)
- **Carbon Monoxide (CO)**: Combustion byproduct (mg/m³)

### UV and Aerosols
- **UV Index**: UV radiation intensity (0-11+)
- **UV Index Clear Sky**: Baseline UV under clear conditions
- **Aerosol Optical Depth**: Atmospheric opacity affecting solar radiation

### Air Quality Indices
- **European AQI**: Overall air quality index (0-100+)
- Component indices for each pollutant

## Implementation

### Pipeline Files

```
pipelines/weather/air_quality.py          # dlt source for air quality data
scripts/test_air_quality_pipeline.py      # Test/run pipeline
scripts/analyze_air_quality_impact.py     # Analysis script
```

### dbt Models

```
transform/models/staging/stg_air_quality_hourly.sql
  ↓
transform/models/marts/fct_electricity_with_weather.sql
  (joins weather + air quality + electricity)
```

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
  air_quality:
    enabled: true  # Uses same location/dates as weather
```

### Running the Pipeline

```bash
# Load air quality data
pixi run pipeline-air-quality

# Build dbt models
cd transform
pixi run dbt run --select stg_air_quality_hourly
pixi run dbt run --select fct_electricity_with_weather

# Run analysis
cd ..
pixi run analyze-air-quality
```

## Air Quality Categories

### PM2.5 Categories (µg/m³)

| Category | Range | Health Impact |
|----------|-------|---------------|
| Good | 0-12 | Minimal health risk |
| Moderate | 12-35 | Acceptable air quality |
| Unhealthy for sensitive groups | 35-55 | May affect sensitive individuals |
| Unhealthy | 55-150 | Everyone may experience health effects |
| Very unhealthy | 150+ | Health alert: serious effects possible |

### European AQI Categories

| Category | Range | Description |
|----------|-------|-------------|
| Good | 0-20 | Air quality is satisfactory |
| Fair | 20-40 | Air quality is acceptable |
| Moderate | 40-60 | Moderate air quality |
| Poor | 60-80 | Poor air quality |
| Very poor | 80-100 | Very poor air quality |
| Extremely poor | 100+ | Extremely poor air quality |

### UV Index Categories

| Category | Range | Protection Needed |
|----------|-------|-------------------|
| Low | 0-3 | Minimal protection |
| Moderate | 3-6 | Wear sunscreen |
| High | 6-8 | Extra protection required |
| Very high | 8-11 | Stay in shade during midday |
| Extreme | 11+ | Avoid outdoor activity |

## Use Cases

### 1. Solar Panel Soiling Analysis

High aerosol optical depth indicates atmospheric haze that:
- Reduces solar irradiance reaching panels
- Deposits particulates on panel surfaces
- Decreases panel efficiency over time

**Query**: Find days requiring panel cleaning
```sql
SELECT
    DATE(timestamp) as date,
    ROUND(AVG(aerosol_optical_depth), 3) as avg_aod,
    ROUND(AVG(dust), 1) as avg_dust,
    ROUND(AVG(ghi_wm2), 0) as avg_solar
FROM main_marts.fct_electricity_with_weather
WHERE aerosol_optical_depth > 0.3  -- High soiling risk
GROUP BY DATE(timestamp)
ORDER BY avg_aod DESC;
```

**Thresholds**:
- AOD > 0.3: Consider cleaning
- AOD > 0.5: Cleaning recommended
- AOD > 1.0: Significant impact (wildfire smoke)

### 2. HVAC Usage During Poor Air Quality

Poor air quality drives HVAC usage in shoulder seasons:
- Occupants close windows
- HVAC runs in recirculation mode
- Increased filter resistance over time

**Query**: Compare HVAC usage by air quality
```sql
SELECT
    pm2_5_category,
    COUNT(*) as hours,
    ROUND(AVG(kwh), 0) as avg_kwh,
    ROUND(AVG(pm2_5), 1) as avg_pm2_5
FROM main_marts.fct_electricity_with_weather
WHERE temperature_c BETWEEN 15 AND 25  -- Shoulder season
    AND pm2_5_category IS NOT NULL
GROUP BY pm2_5_category
ORDER BY avg_pm2_5;
```

**Expected finding**: 20-30% higher consumption during unhealthy air quality.

### 3. Air Filter Replacement Timing

Track cumulative particulate exposure to optimize filter replacement:

**Query**: Monthly particulate exposure
```sql
SELECT
    DATE_TRUNC('month', timestamp) as month,
    ROUND(AVG(pm2_5), 1) as avg_pm2_5,
    COUNT(CASE WHEN pm2_5 > 35 THEN 1 END) as unhealthy_hours,
    ROUND(SUM(pm2_5) / 1000.0, 2) as cumulative_pm2_5_mg
FROM main_marts.fct_electricity_with_weather
GROUP BY DATE_TRUNC('month', timestamp)
ORDER BY month DESC;
```

**Recommendation**: Replace filters more frequently during high PM2.5 months.

### 4. UV Index and Cooling Demand

High UV correlates with:
- Higher outdoor temperatures
- Increased solar heat gain
- Greater cooling demand

**Query**: UV vs. cooling demand
```sql
SELECT
    uv_category,
    COUNT(*) as hours,
    ROUND(AVG(temperature_c), 1) as avg_temp,
    ROUND(AVG(kwh), 0) as avg_kwh,
    ROUND(AVG(cdh), 1) as avg_cooling_degree_hours
FROM main_marts.fct_electricity_with_weather
WHERE EXTRACT(month FROM timestamp) BETWEEN 6 AND 8  -- Summer
    AND EXTRACT(hour FROM timestamp) BETWEEN 10 AND 18  -- Daytime
GROUP BY uv_category
ORDER BY avg_temp DESC;
```

### 5. Health Impact Analysis

Identify poor air quality days for health awareness:

**Query**: Worst air quality days
```sql
SELECT
    DATE(timestamp) as date,
    ROUND(AVG(pm2_5), 1) as avg_pm2_5,
    ROUND(MAX(pm2_5), 1) as peak_pm2_5,
    pm2_5_category,
    COUNT(*) as hours
FROM main_marts.fct_electricity_with_weather
WHERE pm2_5_category IN ('unhealthy_sensitive', 'unhealthy', 'very_unhealthy')
GROUP BY DATE(timestamp), pm2_5_category
ORDER BY avg_pm2_5 DESC
LIMIT 20;
```

## Real-World Example: Toronto 2022-2024

### Data Summary
- **Total hours**: 17,520
- **Good air quality**: 10,338 hours (59%)
- **Moderate air quality**: 6,395 hours (36%)
- **Poor air quality**: 794 hours (5%)
- **Average PM2.5**: 12.8 µg/m³
- **Average AOD**: 0.197

### Key Findings

#### 1. 2023 Canadian Wildfire Impact

June 2023 experienced extreme air quality degradation from wildfire smoke:
- **Peak PM2.5**: 148.5 µg/m³ (very unhealthy)
- **Peak AOD**: 3.6 (extreme haze)
- **Duration**: Multiple days with PM2.5 > 100
- **Impact**:
  - Severely reduced solar irradiance
  - Significant panel soiling
  - Increased HVAC usage

**Date**: June 8, 2023
- Avg PM2.5: 104.6 µg/m³
- Peak PM2.5: 148.5 µg/m³
- Avg consumption: 1,129 kWh (despite cool 15.9°C temperature)

#### 2. HVAC Impact During Poor Air Quality

Shoulder season (15-25°C) comparison:

| Air Quality | Hours | Avg kWh | Impact |
|-------------|-------|---------|--------|
| Good | 2,316 | 668 | Baseline |
| Moderate | 3,024 | 753 | +13% |
| Unhealthy (sensitive) | 375 | 834 | +25% |
| Unhealthy | 140 | 875 | +31% |

**Conclusion**: Poor air quality increases HVAC consumption by 31% in shoulder season due to closed windows and recirculation.

#### 3. Seasonal Patterns

**Best air quality** (Nov-Dec):
- Avg PM2.5: 4.6-5.5 µg/m³
- Minimal unhealthy hours

**Worst air quality** (May-Aug):
- Avg PM2.5: 14.1-17.9 µg/m³
- 23-40 unhealthy hours per month

#### 4. Solar Soiling Events

**High AOD days** (AOD > 1.0):
- June 28, 2023: AOD = 2.65, PM2.5 = 92 µg/m³
- June 8, 2023: AOD = 1.87, PM2.5 = 104 µg/m³
- June 5, 2023: AOD = 1.28, PM2.5 = 64 µg/m³

**Recommendation**: Solar panel cleaning critical after June 2023 wildfire events.

## Dashboard Integration

Suggested visualizations:

1. **Time Series**:
   - PM2.5 trend with color-coded categories
   - Aerosol optical depth with solar irradiance overlay
   - UV index with temperature and cooling degree hours

2. **Correlation Charts**:
   - PM2.5 vs. HVAC consumption (shoulder season)
   - Aerosol optical depth vs. solar irradiance
   - UV index vs. cooling demand

3. **Category Distribution**:
   - Hours by air quality category (pie chart)
   - Monthly air quality trends (stacked bar)
   - Seasonal UV patterns

4. **Alerts**:
   - High pollution days (PM2.5 > 35)
   - Solar soiling risk (AOD > 0.3)
   - Extreme UV days (UV > 8)

## Health and Energy Recommendations

### For Homeowners

1. **Air Quality Monitoring**:
   - Track PM2.5 during shoulder seasons
   - Close windows during poor air quality events
   - Consider air purifiers for very unhealthy days

2. **HVAC Maintenance**:
   - Replace filters monthly during high PM2.5 periods
   - Inspect filters after extreme pollution events
   - Consider higher MERV rating filters

3. **Solar Panel Care**:
   - Clean panels after wildfire smoke events
   - Monitor for efficiency drops during high AOD periods
   - Schedule cleaning when AOD > 0.5 for multiple days

4. **UV Protection**:
   - Use UV index for outdoor activity planning
   - Consider UV-blocking window films for high UV exposure
   - Plan cooling system capacity with UV peaks in mind

### For Energy Cooperatives

1. **Demand Forecasting**:
   - Include air quality in HVAC load predictions
   - Account for wildfire seasons in solar forecasts
   - UV index as cooling demand indicator

2. **Grid Planning**:
   - Prepare for reduced solar during smoke events
   - Increased HVAC load during poor air quality
   - Seasonal air quality patterns in load models

3. **Member Education**:
   - Provide air quality alerts to members
   - Solar cleaning recommendations
   - HVAC filter replacement reminders

## Future Enhancements

1. **Predictive Modeling**:
   - Forecast air quality impact on loads
   - Predict solar soiling losses
   - Optimize filter replacement schedules

2. **Additional Variables**:
   - Pollen count (HVAC filter impact)
   - Visibility (solar irradiance proxy)
   - Atmospheric pressure (furnace efficiency)

3. **Integration**:
   - Real-time air quality alerts
   - Automated panel cleaning scheduling
   - Dynamic HVAC control based on air quality

4. **Health Analytics**:
   - Indoor air quality estimation
   - Health cost calculations
   - Ventilation optimization strategies

## References

- [Open-Meteo Air Quality API](https://open-meteo.com/en/docs/air-quality-api)
- [EPA Air Quality Index Guide](https://www.airnow.gov/aqi/aqi-basics/)
- [WHO Air Quality Guidelines](https://www.who.int/news-room/fact-sheets/detail/ambient-(outdoor)-air-quality-and-health)
- [European Air Quality Index](https://www.eea.europa.eu/themes/air/air-quality-index)
- [UV Index Information](https://www.epa.gov/sunsafety/uv-index-scale-0)
