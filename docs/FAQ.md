# Frequently Asked Questions

## General Questions

### What is the Open Data Coop?

The Open Data Coop is privacy-first, open-source infrastructure for residential energy data. It enables homeowners to:
- Process and analyze their own electricity consumption data
- Size solar installations accurately
- Optimize heat pump performance
- Understand time-of-use rate impacts
- Track their carbon footprint

The project uses local-first architecture: your data stays on your own devices unless you explicitly choose to share it.

### Who is this for?

**Homeowners** who want to:
- Understand their energy consumption patterns
- Make data-driven decisions about solar, heat pumps, or EVs
- Optimize their electricity rates
- Track retrofit performance

**Energy cooperatives** who want to:
- Provide member services without building infrastructure
- Run privacy-preserving community analysis
- Support policy advocacy with evidence

**Researchers** who need:
- Real-world heat pump field data
- Building energy model validation
- Grid interaction studies

### Is this free?

Yes! The code is open source under Apache 2.0 license. There are no subscription fees or usage limits.

You will need:
- Your own computer (Mac or Linux recommended)
- Green Button data from your utility (usually free)
- Optional: Home Assistant for real-time monitoring

### How is this different from utility websites?

Most utility portals only show:
- Monthly bills
- Basic usage graphs
- Limited historical data

Open Data Coop provides:
- Full control of your raw data
- Arbitrary time-range analysis
- Integration with other data sources (weather, carbon intensity, pricing)
- Privacy (data never leaves your computer)
- Reproducible analysis with open-source tools

## Privacy & Security

### Where is my data stored?

**By default, all data stays on your local computer.** The pipelines create:
- DuckDB database file in your project directory
- Optional Parquet exports in `~/energy-data/warehouse/`

Your data never goes to any cloud service or third-party server unless you explicitly configure that.

### What data is collected?

The pipelines only process data **you** provide:
- Green Button XML files you download from your utility
- Home Assistant sensor data you export
- Public grid data (carbon intensity, pricing)

No telemetry, analytics, or tracking is included.

### Can I share data with my energy cooperative?

Yes, but **only if you choose to**. The architecture supports optional cooperative backup:

1. **Local-first**: Data stays on your devices by default
2. **Opt-in sync**: You can sync encrypted backups to a cooperative server
3. **Aggregation**: Cooperatives can run privacy-preserving queries across members
4. **You control it**: You can stop syncing or delete backups at any time

This feature is still under development. See [docs/proposals/green-button-pilot.md](proposals/green-button-pilot.md) for details.

### What about Green Button OAuth?

Some utilities use OAuth for Green Button access, which means authorizing a third-party app to download your data.

**Current status**: This project focuses on **downloaded XML files** (no OAuth). You download data from your utility's website and process it locally.

**Future**: OAuth support is planned but requires:
- Registration as an authorized Green Button third party
- Secure credential storage
- Refresh token handling

For now, manual download + local processing is the most privacy-preserving approach.

### How do I delete my data?

All data is stored locally. To delete:

```bash
# Delete DuckDB database
rm energy_warehouse.duckdb

# Delete Parquet exports
rm -rf ~/energy-data/warehouse/

# Delete mock data
rm -rf mock_data/
```

If you opted into cooperative backup, contact your cooperative to request deletion from their servers.

## Platform Support

### What operating systems are supported?

**Fully supported:**
- macOS (Apple Silicon and Intel)
- Linux (Ubuntu 22.04+, Debian 12+, other modern distributions)

**Experimental:**
- Windows via WSL2 (Windows Subsystem for Linux)

**Not supported:**
- Native Windows (DuckDB and some dependencies have compatibility issues)

### I'm on Windows. Can I use this?

Yes, but use **WSL2** (Windows Subsystem for Linux):

1. Install WSL2: [microsoft.com/wsl](https://learn.microsoft.com/en-us/windows/wsl/install)
2. Install Ubuntu 22.04 from Microsoft Store
3. Open Ubuntu terminal and follow the Linux setup instructions

### Does this work on Raspberry Pi?

**Potentially**, but not tested. Requirements:
- Raspberry Pi 4 or newer (4GB+ RAM recommended)
- 64-bit Raspberry Pi OS
- At least 32GB SD card or USB storage

DuckDB and most dependencies support ARM64, but performance may be slower than x86 systems.

### Can I run this in the cloud?

Yes, but **it defeats the privacy-first purpose**. If you need cloud deployment:

- Use encrypted storage
- Don't store raw energy data long-term
- Follow data minimization principles
- Consider GDPR/PIPEDA compliance

For most users, running locally is simpler and more private.

## Installation & Setup

### Do I need to know Python?

**No programming required for basic use.** Just run the provided scripts:

```bash
pixi run python scripts/test_full_pipeline.py
```

**Python helpful for:**
- Custom queries beyond SQL
- Adding new data sources
- Modifying transformation logic
- Contributing to the project

### What is pixi?

**Pixi** is a fast, cross-platform package manager that handles all dependencies for this project (Python, DuckDB, dbt, etc.).

Think of it like:
- npm for Node.js
- poetry for Python
- conda but faster

You don't need to manage Python versions or virtual environments manually. Pixi does it all.

### Can I use my existing Python installation?

You can, but **not recommended**. Pixi ensures:
- Correct Python version (3.11 or 3.12)
- All dependencies at tested versions
- Isolated environment (no conflicts with other projects)

If you really want to use your own Python:

```bash
pip install dlt[duckdb] dbt-duckdb pandas polars pyarrow greenbutton-objects
```

But you're on your own for compatibility issues.

### Why DuckDB instead of PostgreSQL/MySQL?

**DuckDB** is perfect for this use case:
- **File-based**: No server to run, just a file
- **Fast analytics**: Optimized for OLAP queries
- **Parquet native**: Efficient storage and querying
- **Lightweight**: Runs on laptops without resource overhead
- **SQL standard**: Familiar query language

For production cooperative deployments, PostgreSQL or other databases might be used, but DuckDB is ideal for personal data warehouses.

### How much disk space do I need?

Depends on data volume:

**Minimal (testing with mock data):**
- ~100 MB (DuckDB database)
- ~50 MB (Parquet exports)

**Typical (1 home, 2 years hourly data):**
- ~500 MB (DuckDB database)
- ~200 MB (Parquet exports)

**Large (multiple homes, 5+ years, power monitoring):**
- 5-10 GB (DuckDB database)
- 2-5 GB (Parquet exports)

DuckDB compresses data efficiently, so actual disk usage is usually smaller than raw CSV equivalents.

## Data Sources

### How do I get Green Button data?

**Ontario residents:**
1. Log in to your utility account:
   - Hydro One: alectrautilities.com
   - Elexicon: elexiconenergy.com
   - Toronto Hydro: torontohydro.com
2. Find "Green Button" or "Download My Data"
3. Select date range (start with 1 year)
4. Download XML file
5. Move to `data/greenbutton/` in project directory

**Other provinces:**
- Check your utility website for "Green Button", "My Data", or "Interval Data"
- Contact customer service if you can't find it
- Some utilities may charge a fee for historical data

**USA:**
- Most utilities support Green Button
- See [greenbuttondata.org](https://www.greenbuttondata.org) for provider list

### What if my utility doesn't provide Green Button data?

Options:
1. **Request it**: Contact your utility and ask for Green Button access
2. **Bill scraping**: Use [utility-bill-scraper](https://github.com/ryanfobel/utility-bill-scraper) (Kitchener-Waterloo only)
3. **Manual entry**: Enter monthly bills manually
4. **Power monitoring only**: Use Home Assistant without Green Button

### Do I need Home Assistant?

**No.** Home Assistant is optional for:
- Real-time power monitoring (10-second intervals)
- Circuit-level analysis
- Appliance attribution

You can use Green Button data alone for:
- Hourly consumption analysis
- TOU rate optimization
- Solar sizing
- Monthly trends

### Can I use data from multiple utilities?

Yes! If you have multiple properties or switched utilities:

```yaml
homes:
  - id: "home-001"
    sources:
      green_button:
        files:
          - data/greenbutton/hydro_one_2022.xml
          - data/greenbutton/hydro_one_2023.xml
          - data/greenbutton/hydro_one_2024.xml
  - id: "cottage-001"
    sources:
      green_button:
        files:
          - data/greenbutton/cottage_utility_2024.xml
```

Each home gets a unique identifier in the database.

## Usage

### How often should I update data?

Depends on your needs:

**Monthly**: Good for trend analysis
- Download latest Green Button data monthly
- Run pipeline to update warehouse

**Weekly**: Better for rate optimization
- More responsive to consumption changes
- Useful if you're testing energy-saving measures

**Daily**: For real-time monitoring
- Requires automated Home Assistant export
- Set up cron job for daily updates

### Can I query data from Excel?

Not directly, but you can export to CSV:

```sql
-- In DuckDB CLI
COPY (
    SELECT * FROM main_marts.fct_electricity_consumption
    WHERE home_id = 'home-001'
) TO 'export.csv' (HEADER, DELIMITER ',');
```

Then open `export.csv` in Excel.

Alternatively, use Parquet exports and read them with:
- Power BI (has native Parquet support)
- Excel via Power Query (requires Parquet plugin)

### How do I visualize my data?

**Option 1: DuckDB CLI + SQL**
- Simple aggregations and summaries
- Good for quick checks

**Option 2: Jupyter Notebooks**
- Use pandas or polars for charts
- Full control over visualizations
- Requires Python knowledge

**Option 3: Evidence.dev (planned)**
- Interactive dashboard
- No-code visualization
- Shareable reports

**Option 4: Export to BI tools**
- Power BI, Tableau, Metabase, etc.
- Connect to DuckDB or read Parquet files

### Can I run this on a schedule?

Yes! Use cron (Mac/Linux) or Task Scheduler (Windows):

```bash
# Run daily at 2 AM
crontab -e
# Add this line:
0 2 * * * cd /path/to/open-data-coop && /usr/local/bin/pixi run python scripts/test_full_pipeline.py
```

See [docs/USAGE.md#scheduling-with-cron](USAGE.md#scheduling-with-cron) for details.

## Troubleshooting

### Pipeline fails with "ModuleNotFoundError"

**Problem**: You're not using the pixi environment.

**Solution**: Always prefix commands with `pixi run`:

```bash
# Wrong
python scripts/test_full_pipeline.py

# Correct
pixi run python scripts/test_full_pipeline.py
```

### Green Button parsing fails

**Problem**: XML file format not recognized.

**Check:**
1. File is valid XML (open in browser or text editor)
2. File contains `<feed>` and `<entry>` elements
3. File is ESPI format (Green Button standard)

**Solution**: Try a different utility file or open an issue with error details.

### dbt transformations fail

**Problem**: Raw data not loaded yet.

**Solution**: Run dlt pipeline first:

```bash
# Load data
pixi run python scripts/test_green_button_pipeline.py

# Then run dbt
cd transform
pixi run dbt run --profiles-dir . --project-dir .
```

### Out of memory errors

**Problem**: Dataset too large for available RAM.

**Solutions:**
1. Process data in chunks (split by year)
2. Increase swap space
3. Use a machine with more RAM
4. Export to Parquet and query incrementally

### Pixi installation fails

**Problem**: Installer can't write to default location.

**Solution**: Install to custom location:

```bash
curl -fsSL https://pixi.sh/install.sh | bash -s -- --prefix ~/.local
```

## Updates

### How do I update to the latest version?

```bash
# Pull latest changes
git pull origin main

# Update dependencies
pixi install

# Test that everything still works
pixi run python scripts/test_full_pipeline.py
```

### Will updates break my existing data?

**Probably not.** We aim for backward compatibility, but:

- **DuckDB database**: May require schema migrations (instructions provided)
- **Parquet exports**: Always forward-compatible
- **Configuration files**: May need new fields (documented in release notes)

**Best practice**: Backup your database before updating:

```bash
cp energy_warehouse.duckdb energy_warehouse.duckdb.backup
```

### How do I know when updates are available?

**Option 1: GitHub notifications**
- Watch the repository on GitHub
- Get notified of new releases

**Option 2: Periodic checks**
```bash
git fetch origin
git log HEAD..origin/main --oneline
```

**Option 3: Subscribe to discussions**
- Follow [GitHub Discussions](https://github.com/ryanfobel/open-data-coop/discussions)

## Contributing

### How can I contribute?

See [CONTRIBUTING.md](../CONTRIBUTING.md) for:
- Reporting bugs
- Suggesting features
- Contributing code
- Improving documentation
- Participating in pilots

### I found a bug. What should I do?

1. Check [existing issues](https://github.com/ryanfobel/open-data-coop/issues) to avoid duplicates
2. Open a new issue with:
   - Clear description of the problem
   - Steps to reproduce
   - Error messages (full text)
   - Your OS and Python version
3. Wait for response (usually within a few days)

### Can I add support for my utility?

Yes! If your utility provides Green Button data:

1. Test with your XML file
2. If it works, document it (open a PR)
3. If it doesn't work, open an issue with:
   - Utility name and location
   - Sample XML file (redact sensitive info)
   - Error message

We'll add support or provide a workaround.

## Advanced Questions

### Can I use this for commercial purposes?

**Code: Yes** (Apache 2.0 license)
- Use the pipeline code in commercial products
- Modify and distribute freely
- Attribution required

**Data: No** (CC BY-NC-SA 4.0 license)
- Data outputs are non-commercial
- Restricted by upstream data sources (IESO, utilities, etc.)
- Can be used for research and personal use

See [LICENSE](../LICENSE) and [LICENSE-DATA](../LICENSE-DATA) for details.

### How does this integrate with other tools?

**Data flows:**
- **Home Assistant** → Parquet → dlt → DuckDB
- **Green Button** → dlt → DuckDB → dbt
- **DuckDB** → Parquet → Paimon → Research/BI tools

**Compatible tools:**
- **eemeter**: CalTRACK-compliant savings calculations
- **eeweather**: Degree day normalization
- **electricitymap**: Grid carbon intensity
- **Evidence.dev**: Interactive dashboards

See [README.md#related-ecosystem-components](../README.md#related-ecosystem-components).

### Can I run this on a NAS?

Yes, if your NAS supports:
- Linux (most Synology/QNAP devices do)
- Python 3.11+
- Enough CPU for DuckDB queries

Advantages:
- Always-on for scheduled runs
- Centralized storage
- Accessible from multiple devices

Disadvantages:
- Setup more complex
- May be slower than a laptop
- Backup strategy required

### What's the performance like?

**Typical benchmarks:**

| Operation | Duration | Notes |
|-----------|----------|-------|
| Parse 1 year Green Button XML (8760 hours) | 5-10 seconds | CPU-bound |
| dlt load to DuckDB | 2-5 seconds | I/O-bound |
| dbt transformations (all models) | 5-15 seconds | First run slower |
| Export to Parquet | 10-30 seconds | Depends on data volume |
| Query 1 year of data | <1 second | DuckDB is fast! |

For 10+ years of data, expect proportionally longer times.

## Still Have Questions?

- **Check documentation**: [docs/](.)
- **Search issues**: [github.com/ryanfobel/open-data-coop/issues](https://github.com/ryanfobel/open-data-coop/issues)
- **Ask the community**: [GitHub Discussions](https://github.com/ryanfobel/open-data-coop/discussions)
- **Contact maintainer**: See [NOTICE](../NOTICE) for contact info

---

*Can't find your answer? Open an issue and we'll add it to this FAQ!*
