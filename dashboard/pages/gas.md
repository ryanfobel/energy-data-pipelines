---
title: Natural Gas Consumption
---

# Natural Gas Consumption

Monthly natural gas data from Green Button utility meter.

```sql monthly_consumption
SELECT
  timestamp,
  year,
  month,
  SUM(m3) as total_m3,
  SUM(cost) as total_cost_dollars,
  COUNT(*) as reading_count
FROM fct_gas
GROUP BY timestamp, year, month
ORDER BY timestamp DESC
```

```sql recent_readings
SELECT
  timestamp,
  m3,
  cost as cost_dollars,
  estimated,
  quality
FROM fct_gas
ORDER BY timestamp DESC
LIMIT 50
```

## Monthly Summary

<DataTable data={monthly_consumption}>
  <Column id=year/>
  <Column id=month/>
  <Column id=total_m3 fmt="#,##0.0"/>
  <Column id=total_cost_dollars fmt="$#,##0.00" contentType=colorscale/>
  <Column id=reading_count fmt="#,##0"/>
</DataTable>

## Monthly Trend

<LineChart
  data={monthly_consumption}
  x=timestamp
  y=total_m3
  yAxisTitle="Cubic Meters (m³)"
  title="Monthly Natural Gas Consumption"
/>

## Recent Readings

<DataTable data={recent_readings} rows=20>
  <Column id=timestamp/>
  <Column id=m3 fmt="#,##0.0"/>
  <Column id=cost_dollars fmt="$#,##0.00"/>
  <Column id=estimated/>
  <Column id=quality/>
</DataTable>

---

[← Back to Overview](/)
