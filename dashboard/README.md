# Energy Data Dashboard

Evidence.dev dashboard for visualizing home energy consumption across all utilities.

## Features

- **Multi-commodity support**: Electricity, natural gas, and water
- **Multiple data sources**: Green Button utility data + Home Assistant real-time monitoring
- **Interactive visualizations**: Charts, tables, and summary statistics
- **Powered by DuckDB**: Queries dbt marts directly from the warehouse

## Pages

- **Overview** (`/`) — Summary of all commodities with total consumption and costs
- **Electricity** (`/electricity`) — Hourly consumption from Green Button and Home Assistant
- **Natural Gas** (`/gas`) — Monthly gas consumption and costs
- **Water** (`/water`) — Daily/monthly water usage

## Setup

### Prerequisites

- Node.js 18+ and npm
- DuckDB warehouse at `../energy_warehouse.duckdb` (created by running the pipelines)
- dbt models built (run `pixi run dbt-build`)

### Installation

```bash
cd dashboard
npm install
```

### Development

Start the dev server:

```bash
npm run dev
```

The dashboard will be available at http://localhost:3000

Evidence watches for changes to the DuckDB warehouse and automatically updates.

### Build Static Site

Generate a static site for deployment:

```bash
npm run build
```

The build output is in `build/`.

## Data Sources

The dashboard queries these dbt marts from `energy_warehouse.duckdb`:

- `fct_utility_consumption` — Unified view of all commodities
- `fct_electricity_consumption` — Hourly electricity (Green Button + Home Assistant)
- `fct_gas_consumption` — Monthly natural gas
- `fct_water_consumption` — Daily/monthly water

## Deployment Options

### 1. Local Static Files

Serve the `build/` directory with any web server:

```bash
npm run build
cd build
python3 -m http.server 8000
```

### 2. GitHub Pages

Copy the build to your docs folder:

```bash
npm run build
cp -r build/* ../docs/energy-dashboard/
git add docs/energy-dashboard
git commit -m "docs: update energy dashboard"
git push
```

Enable GitHub Pages in repository settings (source: `docs/` folder).

### 3. Evidence Cloud

Deploy to Evidence's managed hosting:

```bash
npm install -g @evidence-dev/cli
evidence deploy
```

See https://docs.evidence.dev/deployment for more options.

## Updating Data

The dashboard reflects the latest data in `energy_warehouse.duckdb`. To update:

```bash
# Run pipelines to load new data
cd ..
pixi run pipeline-green-button
pixi run pipeline-home-assistant

# Rebuild dbt models
pixi run dbt-build

# Restart dashboard dev server (if running)
cd dashboard
npm run dev
```

## Customization

### Adding New Pages

Create a new `.md` file in `pages/`:

```markdown
---
title: My Custom Page
---

# My Custom Page

\`\`\`sql my_query
SELECT * FROM energy.fct_utility_consumption
LIMIT 10
\`\`\`

<DataTable data={my_query}/>
```

Evidence automatically adds it to the navigation.

### Styling

Evidence uses Tailwind CSS. Add custom styles in component blocks or modify the theme in `evidence.config.yaml`.

## Resources

- Evidence Docs: https://docs.evidence.dev
- DuckDB Connector: https://docs.evidence.dev/core-concepts/data-sources/duckdb
- Component Library: https://docs.evidence.dev/components
- SQL Reference: https://docs.evidence.dev/core-concepts/queries
