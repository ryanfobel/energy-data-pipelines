---
title: Natural Gas Consumption
---

# Natural Gas Consumption

Monthly natural gas consumption from Green Button utility data.

```sql monthly_gas
SELECT
  year,
  month,
  timestamp,
  m3,
  cost / 100.0 as cost_dollars,
  estimated,
  quality
FROM energy.fct_gas_consumption
ORDER BY timestamp DESC
```

```sql yearly_summary
SELECT
  year,
  COUNT(*) as billing_cycles,
  SUM(m3) as total_m3,
  SUM(cost) / 100.0 as total_cost_dollars,
  AVG(m3) as avg_m3_per_month
FROM energy.fct_gas_consumption
GROUP BY year
ORDER BY year DESC
```

## Yearly Summary

<DataTable data={yearly_summary}>
  <Column id=year/>
  <Column id=billing_cycles/>
  <Column id=total_m3 fmt="#,##0"/>
  <Column id=total_cost_dollars fmt="$#,##0.00" contentType=colorscale/>
  <Column id=avg_m3_per_month fmt="#,##0.0"/>
</DataTable>

## Monthly Consumption Trend

<BarChart
  data={monthly_gas}
  x=timestamp
  y=m3
  yAxisTitle="Cubic Meters (m³)"
  title="Monthly Gas Consumption"
  swapXY=false
/>

## Cost Over Time

<LineChart
  data={monthly_gas}
  x=timestamp
  y=cost_dollars
  yAxisTitle="Cost ($)"
  title="Monthly Gas Cost"
/>

## All Billing Periods

<DataTable data={monthly_gas}>
  <Column id=year/>
  <Column id=month/>
  <Column id=timestamp/>
  <Column id=m3 fmt="#,##0.0"/>
  <Column id=cost_dollars fmt="$#,##0.00" contentType=colorscale/>
  <Column id=estimated/>
  <Column id=quality/>
</DataTable>

---

**Note:** Gas data is typically recorded monthly by utilities like Enbridge Gas. Frequency depends on billing cycles (28-34 days).

[← Back to Overview](/)
