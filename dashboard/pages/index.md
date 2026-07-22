---
title: Home Energy Dashboard
---

# Home Energy Dashboard

Multi-commodity utility consumption from Green Button data.

```sql total_by_commodity
SELECT
  commodity,
  unit,
  SUM(quantity) as total_consumption,
  SUM(cost) as total_cost_cents,
  COUNT(*) as reading_count,
  MIN(timestamp) as first_reading,
  MAX(timestamp) as last_reading
FROM energy.fct_utility_consumption
GROUP BY commodity, unit
ORDER BY commodity
```

```sql recent_readings
SELECT
  commodity,
  timestamp,
  quantity,
  unit,
  cost,
  estimated
FROM energy.fct_utility_consumption
ORDER BY timestamp DESC
LIMIT 100
```

## Overview

<Grid cols=3>
  <BigValue
    data={total_by_commodity.filter(d => d.commodity === 'electricity')}
    value=total_consumption
    title="Total Electricity"
    fmt="#,##0"
  />
  <BigValue
    data={total_by_commodity.filter(d => d.commodity === 'natural_gas')}
    value=total_consumption
    title="Total Natural Gas"
    fmt="#,##0"
  />
  <BigValue
    data={total_by_commodity.filter(d => d.commodity === 'water')}
    value=total_consumption
    title="Total Water"
    fmt="#,##0"
  />
</Grid>

## Consumption by Commodity

<DataTable data={total_by_commodity}>
  <Column id=commodity/>
  <Column id=total_consumption fmt="#,##0.0"/>
  <Column id=unit/>
  <Column id=total_cost_cents fmt="$#,##0.00" contentType=colorscale/>
  <Column id=reading_count fmt="#,##0"/>
  <Column id=first_reading/>
  <Column id=last_reading/>
</DataTable>

## Recent Readings

<DataTable data={recent_readings} rows=20>
  <Column id=timestamp/>
  <Column id=commodity/>
  <Column id=quantity fmt="#,##0.00"/>
  <Column id=unit/>
  <Column id=cost fmt="$#,##0.00"/>
  <Column id=estimated/>
</DataTable>

---

## Navigation

- [Electricity](/electricity) — Hourly consumption from Green Button and real-time monitoring
- [Natural Gas](/gas) — Monthly gas consumption
- [Water](/water) — Daily/monthly water usage
