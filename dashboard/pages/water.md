---
title: Water Consumption
---

# Water Consumption

Daily/monthly water usage from Green Button utility data.

```sql water_readings
SELECT
  timestamp,
  year,
  month,
  m3,
  gallons,
  raw_volume,
  raw_unit,
  cost / 100.0 as cost_dollars,
  estimated,
  quality
FROM fct_water
ORDER BY timestamp DESC
```

```sql monthly_summary
SELECT
  year,
  month,
  COUNT(*) as reading_count,
  SUM(m3) as total_m3,
  SUM(gallons) as total_gallons,
  SUM(cost) / 100.0 as total_cost_dollars,
  AVG(m3) as avg_m3_per_reading
FROM fct_water
GROUP BY year, month
ORDER BY year DESC, month DESC
```

```sql yearly_summary
SELECT
  year,
  COUNT(*) as reading_count,
  SUM(m3) as total_m3,
  SUM(gallons) as total_gallons,
  SUM(cost) / 100.0 as total_cost_dollars
FROM fct_water
GROUP BY year
ORDER BY year DESC
```

## Yearly Summary

<DataTable data={yearly_summary}>
  <Column id=year/>
  <Column id=reading_count/>
  <Column id=total_m3 fmt="#,##0"/>
  <Column id=total_gallons fmt="#,##0"/>
  <Column id=total_cost_dollars fmt="$#,##0.00" contentType=colorscale/>
</DataTable>

## Monthly Summary

<DataTable data={monthly_summary}>
  <Column id=year/>
  <Column id=month/>
  <Column id=reading_count/>
  <Column id=total_m3 fmt="#,##0.0"/>
  <Column id=total_gallons fmt="#,##0"/>
  <Column id=total_cost_dollars fmt="$#,##0.00" contentType=colorscale/>
  <Column id=avg_m3_per_reading fmt="#,##0.00"/>
</DataTable>

## Consumption Over Time

<AreaChart
  data={water_readings}
  x=timestamp
  y=m3
  yAxisTitle="Cubic Meters (m³)"
  title="Water Consumption"
/>

## All Water Readings

<DataTable data={water_readings}>
  <Column id=timestamp/>
  <Column id=m3 fmt="#,##0.00"/>
  <Column id=gallons fmt="#,##0"/>
  <Column id=raw_volume fmt="#,##0.00"/>
  <Column id=raw_unit/>
  <Column id=cost_dollars fmt="$#,##0.00"/>
  <Column id=estimated/>
  <Column id=quality/>
</DataTable>

---

**Note:** Water data frequency varies by utility. Some utilities report daily, others weekly or monthly. The raw_unit field shows the original unit from the utility (m³ or gallons).

[← Back to Overview](/)
