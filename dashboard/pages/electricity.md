---
title: Electricity Consumption
---

# Electricity Consumption

Hourly electricity data from Green Button utility meter and Home Assistant real-time monitoring.

```sql daily_consumption
SELECT
  DATE_TRUNC('day', timestamp) as day,
  source,
  SUM(kwh) as total_kwh,
  SUM(cost) as total_cost_cents,
  COUNT(*) as reading_count
FROM energy.fct_electricity
GROUP BY 1, 2
ORDER BY day DESC
LIMIT 90
```

```sql hourly_recent
SELECT
  timestamp,
  source,
  kwh,
  cost,
  estimated
FROM energy.fct_electricity
ORDER BY timestamp DESC
LIMIT 168  -- Last week
```

```sql monthly_summary
SELECT
  year,
  month,
  source,
  SUM(kwh) as total_kwh,
  SUM(cost) / 100.0 as total_cost_dollars,
  AVG(kwh) as avg_kwh_per_reading
FROM energy.fct_electricity
GROUP BY year, month, source
ORDER BY year DESC, month DESC
```

## Monthly Summary

<DataTable data={monthly_summary}>
  <Column id=year/>
  <Column id=month/>
  <Column id=source/>
  <Column id=total_kwh fmt="#,##0"/>
  <Column id=total_cost_dollars fmt="$#,##0.00" contentType=colorscale/>
  <Column id=avg_kwh_per_reading fmt="#,##0.00"/>
</DataTable>

## Daily Consumption (Last 90 Days)

<LineChart
  data={daily_consumption}
  x=day
  y=total_kwh
  series=source
  yAxisTitle="kWh"
  title="Daily Electricity Consumption by Source"
/>

## Hourly Pattern (Last Week)

<AreaChart
  data={hourly_recent}
  x=timestamp
  y=kwh
  series=source
  yAxisTitle="kWh"
  title="Hourly Electricity Usage"
/>

## Recent Hourly Readings

<DataTable data={hourly_recent} rows=24>
  <Column id=timestamp/>
  <Column id=source/>
  <Column id=kwh fmt="#,##0.000"/>
  <Column id=cost fmt="$#,##0.00"/>
  <Column id=estimated/>
</DataTable>

---

[← Back to Overview](/)
