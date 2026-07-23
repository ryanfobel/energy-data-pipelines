---
title: Weather Data
---

# Weather Data - Kitchener-Waterloo

Historical weather data from Open-Meteo for your home location.

```sql weather_summary
SELECT
  COUNT(*) as total_hours,
  MIN(timestamp) as first_reading,
  MAX(timestamp) as last_reading,
  ROUND(AVG(temperature_c), 1) as avg_temp_c,
  ROUND(MIN(temperature_c), 1) as min_temp_c,
  ROUND(MAX(temperature_c), 1) as max_temp_c,
  ROUND(AVG(humidity_pct), 0) as avg_humidity_pct,
  ROUND(SUM(precipitation_mm), 1) as total_precipitation_mm
FROM hourly_weather
```

## Summary

<BigValue
  data={weather_summary}
  value=total_hours
  title="Total Hours"
/>

<BigValue
  data={weather_summary}
  value=avg_temp_c
  title="Average Temperature"
  fmt="0.1°C"
/>

<BigValue
  data={weather_summary}
  value=total_precipitation_mm
  title="Total Precipitation"
  fmt="0.0mm"
/>

## Temperature Over Time

```sql daily_temp
SELECT
  DATE_TRUNC('day', timestamp) as date,
  ROUND(AVG(temperature_c), 1) as avg_temp,
  ROUND(MIN(temperature_c), 1) as min_temp,
  ROUND(MAX(temperature_c), 1) as max_temp
FROM hourly_weather
GROUP BY 1
ORDER BY 1
```

<LineChart
  data={daily_temp}
  x=date
  y={['min_temp', 'avg_temp', 'max_temp']}
  yAxisTitle="Temperature (°C)"
  title="Daily Temperature Range"
/>

## Monthly Averages

```sql monthly_weather
SELECT
  DATE_TRUNC('month', timestamp) as month,
  ROUND(AVG(temperature_c), 1) as avg_temp,
  ROUND(AVG(humidity_pct), 0) as avg_humidity,
  ROUND(SUM(precipitation_mm), 1) as total_precipitation,
  ROUND(AVG(windspeed_kmh), 1) as avg_windspeed
FROM hourly_weather
GROUP BY 1
ORDER BY 1
```

<DataTable data={monthly_weather} />

## Recent Conditions

```sql recent_weather
SELECT
  timestamp,
  temperature_c,
  humidity_pct,
  precipitation_mm,
  windspeed_kmh,
  cloud_cover_pct
FROM hourly_weather
ORDER BY timestamp DESC
LIMIT 168  -- Last week
```

<LineChart
  data={recent_weather}
  x=timestamp
  y=temperature_c
  yAxisTitle="Temperature (°C)"
  title="Last 7 Days - Temperature"
/>

<LineChart
  data={recent_weather}
  x=timestamp
  y=humidity_pct
  yAxisTitle="Humidity (0-100)"
  yFmt="#,##0"
  title="Last 7 Days - Humidity"
/>

## Air Quality

_Air quality data will be available once the air quality pipeline is loaded._

```sql air_quality_summary
SELECT
  COUNT(*) as total_readings,
  COUNT(pm2_5) as readings_with_pm25,
  ROUND(AVG(pm2_5), 1) as avg_pm25,
  ROUND(AVG(pm10), 1) as avg_pm10,
  ROUND(AVG(uv_index), 1) as avg_uv_index,
  ROUND(AVG(aerosol_optical_depth), 3) as avg_aod
FROM hourly_weather
```

```sql recent_air_quality
SELECT
  timestamp,
  pm2_5,
  pm10,
  uv_index,
  aerosol_optical_depth as aod
FROM hourly_weather
WHERE pm2_5 IS NOT NULL OR uv_index IS NOT NULL
ORDER BY timestamp DESC
LIMIT 168
```

{#if air_quality_summary[0].readings_with_pm25 > 0}

### Air Quality Metrics

<Grid cols=3>
  <BigValue
    data={air_quality_summary}
    value=avg_pm25
    title="Avg PM2.5"
    fmt="0.1 µg/m³"
  />
  <BigValue
    data={air_quality_summary}
    value=avg_pm10
    title="Avg PM10"
    fmt="0.1 µg/m³"
  />
  <BigValue
    data={air_quality_summary}
    value=avg_uv_index
    title="Avg UV Index"
    fmt="0.1"
  />
</Grid>

### PM2.5 Over Time

<LineChart
  data={recent_air_quality}
  x=timestamp
  y=pm2_5
  yAxisTitle="PM2.5 (µg/m³)"
  title="Last 7 Days - PM2.5 Concentration"
/>

### UV Index Over Time

<LineChart
  data={recent_air_quality}
  x=timestamp
  y=uv_index
  yAxisTitle="UV Index"
  title="Last 7 Days - UV Index"
/>

{:else}

_No air quality data available yet. Run the air quality pipeline to load data._

{/if}
