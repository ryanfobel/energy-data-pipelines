---
title: Weather & Energy Correlation
---

# Weather & Energy Correlation

How temperature affects your electricity usage.

```sql electricity_with_temp
SELECT * FROM energy.electricity_with_weather
```

## Daily Energy Usage vs Temperature

```sql daily_correlation
SELECT
  DATE_TRUNC('day', timestamp) as date,
  ROUND(SUM(kwh), 2) as total_kwh,
  ROUND(AVG(temperature_c), 1) as avg_temp
FROM energy.electricity_with_weather
GROUP BY 1
ORDER BY 1
```

<LineChart
  data={daily_correlation}
  x=date
  y=total_kwh
  y2=avg_temp
  yAxisTitle="Energy (kWh)"
  y2AxisTitle="Temperature (°C)"
  title="Daily Energy Usage vs Temperature"
/>

## Temperature vs Usage Scatter

<ScatterPlot
  data={daily_correlation}
  x=avg_temp
  y=total_kwh
  xAxisTitle="Average Temperature (°C)"
  yAxisTitle="Daily Energy (kWh)"
  title="Temperature Impact on Energy Usage"
/>

## Hourly Patterns

```sql hourly_by_temp_bucket
SELECT
  CASE
    WHEN temperature_c < -10 THEN 'Very Cold (< -10°C)'
    WHEN temperature_c < 0 THEN 'Cold (-10 to 0°C)'
    WHEN temperature_c < 10 THEN 'Cool (0 to 10°C)'
    WHEN temperature_c < 20 THEN 'Mild (10 to 20°C)'
    WHEN temperature_c < 25 THEN 'Warm (20 to 25°C)'
    ELSE 'Hot (> 25°C)'
  END as temp_range,
  ROUND(AVG(kwh), 2) as avg_kwh_per_hour,
  COUNT(*) as hours
FROM electricity_with_weather
WHERE temperature_c IS NOT NULL
GROUP BY 1
ORDER BY
  CASE temp_range
    WHEN 'Very Cold (< -10°C)' THEN 1
    WHEN 'Cold (-10 to 0°C)' THEN 2
    WHEN 'Cool (0 to 10°C)' THEN 3
    WHEN 'Mild (10 to 20°C)' THEN 4
    WHEN 'Warm (20 to 25°C)' THEN 5
    ELSE 6
  END
```

<BarChart
  data={hourly_by_temp_bucket}
  x=temp_range
  y=avg_kwh_per_hour
  yAxisTitle="Average kWh per Hour"
  title="Energy Usage by Temperature Range"
/>

<DataTable data={hourly_by_temp_bucket} />

## Heating vs Cooling Degree Days

```sql degree_days
SELECT
  DATE_TRUNC('month', timestamp) as month,
  -- Heating degree days (base 18°C)
  ROUND(SUM(GREATEST(18 - temperature_c, 0)) / 24, 1) as heating_degree_days,
  -- Cooling degree days (base 18°C)
  ROUND(SUM(GREATEST(temperature_c - 18, 0)) / 24, 1) as cooling_degree_days
FROM hourly_weather
GROUP BY 1
ORDER BY 1
```

<BarChart
  data={degree_days}
  x=month
  y={['heating_degree_days', 'cooling_degree_days']}
  yAxisTitle="Degree Days"
  title="Heating vs Cooling Degree Days"
  swapXY=false
/>

## Summary Statistics

```sql temp_usage_stats
SELECT
  ROUND(CORR(temperature_c, kwh), 3) as temperature_correlation,
  COUNT(DISTINCT DATE_TRUNC('day', timestamp)) as days_analyzed,
  ROUND(AVG(kwh), 2) as avg_hourly_kwh
FROM energy.electricity_with_weather
WHERE temperature_c IS NOT NULL
```

<BigValue
  data={temp_usage_stats}
  value=temperature_correlation
  title="Temperature-Usage Correlation"
  fmt="0.000"
/>

<BigValue
  data={temp_usage_stats}
  value=days_analyzed
  title="Days Analyzed"
/>

**Correlation Guide:**
- -1.0 to -0.5: Strong negative correlation (more heating in cold weather)
- -0.5 to 0.0: Weak negative correlation
- 0.0 to 0.5: Weak positive correlation
- 0.5 to 1.0: Strong positive correlation (more cooling in hot weather)
