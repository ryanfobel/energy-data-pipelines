---
title: Carbon Footprint
---

# Carbon Footprint

Your electricity carbon emissions based on Ontario grid intensity (IESO + gridwatch data).

```sql carbon_summary
SELECT
  SUM(kwh) / 1000 as total_mwh,
  SUM(kg_co2e) as total_kg_co2e,
  SUM(kg_co2e) / 1000 as total_tonnes_co2e,
  AVG(co2e_intensity_gco2_per_kwh) as avg_grid_intensity,
  AVG(NULLIF(grid_clean_pct, 0)) as avg_grid_clean_pct,
  COUNT(*) as total_readings,
  COUNT(co2e_intensity_gco2_per_kwh) as readings_with_carbon
FROM fct_electricity_carbon
WHERE co2e_intensity_gco2_per_kwh IS NOT NULL
```

```sql daily_emissions
SELECT
  DATE_TRUNC('day', timestamp) as day,
  SUM(kwh) as kwh,
  SUM(kg_co2e) as kg_co2e,
  AVG(co2e_intensity_gco2_per_kwh) as avg_intensity,
  AVG(NULLIF(grid_clean_pct, 0)) as avg_clean_pct
FROM fct_electricity_carbon
WHERE co2e_intensity_gco2_per_kwh IS NOT NULL
GROUP BY DATE_TRUNC('day', timestamp)
ORDER BY day DESC
LIMIT 90
```

```sql monthly_emissions
SELECT
  year,
  month,
  SUM(kwh) as kwh,
  SUM(kg_co2e) as kg_co2e,
  SUM(kg_co2e) / 1000 as tonnes_co2e,
  AVG(co2e_intensity_gco2_per_kwh) as avg_intensity
FROM fct_electricity_carbon
WHERE co2e_intensity_gco2_per_kwh IS NOT NULL
GROUP BY year, month
ORDER BY year DESC, month DESC
```

```sql hourly_pattern
SELECT
  hour,
  AVG(co2e_intensity_gco2_per_kwh) as avg_intensity,
  AVG(grid_clean_pct) as avg_clean_pct,
  SUM(kg_co2e) as total_kg_co2e
FROM fct_electricity_carbon
WHERE co2e_intensity_gco2_per_kwh IS NOT NULL
GROUP BY hour
ORDER BY hour
```

## Summary

<Grid cols=3>
  <BigValue
    data={carbon_summary}
    value=total_tonnes_co2e
    title="Total Emissions"
    fmt="#,##0.0"
    comparison=total_mwh
    comparisonFmt="#,##0.0 MWh consumed"
  />
  <BigValue
    data={carbon_summary}
    value=avg_grid_intensity
    title="Avg Grid Intensity"
    fmt="#,##0"
    comparison=avg_grid_clean_pct
    comparisonFmt="#,##0% clean"
  />
  <BigValue
    data={carbon_summary}
    value=readings_with_carbon
    title="Data Coverage"
    fmt="#,##0"
    comparison=total_readings
    comparisonFmt="of #,##0 readings"
  />
</Grid>

## Monthly Emissions

<DataTable data={monthly_emissions}>
  <Column id=year/>
  <Column id=month/>
  <Column id=kwh fmt="#,##0"/>
  <Column id=tonnes_co2e fmt="#,##0.0" contentType=colorscale/>
  <Column id=avg_intensity fmt="#,##0"/>
</DataTable>

## Daily Emissions (Last 90 Days)

<LineChart
  data={daily_emissions}
  x=day
  y=kg_co2e
  yAxisTitle="kg CO2e"
  title="Daily Carbon Emissions"
/>

<LineChart
  data={daily_emissions}
  x=day
  y=avg_intensity
  yAxisTitle="gCO2/kWh"
  title="Grid Carbon Intensity"
/>

<LineChart
  data={daily_emissions}
  x=day
  y=avg_clean_pct
  yAxisTitle="% Clean Generation"
  yMax=100
  title="Grid Clean Generation Percentage"
/>

## Hourly Pattern

<BarChart
  data={hourly_pattern}
  x=hour
  y=avg_intensity
  yAxisTitle="Average gCO2/kWh"
  title="Average Grid Intensity by Hour of Day"
/>

<BarChart
  data={hourly_pattern}
  x=hour
  y=total_kg_co2e
  yAxisTitle="Total kg CO2e"
  title="Total Emissions by Hour of Day"
/>

---

**Data Source**: Ontario grid carbon intensity from IESO fuel mix and gridwatch.ca
**Calculation**: Emissions (kg CO2e) = Consumption (kWh) × Grid Intensity (gCO2/kWh) ÷ 1000

[← Back to Overview](/)
