#!/usr/bin/env python3
"""
Scrape hourly electricity data for 2022-2024 using utility-bill-scraper.

This uses Selenium to automate CSV downloads from the Enova Power portal.

Run with:
  cd /Users/ryan/dev/utility-bill-scraper
  export ENOVA_USERNAME='your_username'
  export ENOVA_PASSWORD='your_password'
  pixi run python ../energy-data-pipelines/scripts/scrape_hourly_electricity.py
"""
import sys
from pathlib import Path
import os
from datetime import datetime

# Add utility-bill-scraper to path
scraper_path = Path(__file__).parent.parent.parent / "utility-bill-scraper" / "src"
if not scraper_path.exists():
    scraper_path = Path("/Users/ryan/dev/utility-bill-scraper/src")
sys.path.insert(0, str(scraper_path))

try:
    import utility_bill_scraper.canada.on.kitchener_wilmot_hydro as kwh
except ImportError as e:
    print(f"Error importing utility-bill-scraper: {e}")
    print("Make sure the utility-bill-scraper dependencies are installed:")
    print("  cd /Users/ryan/dev/utility-bill-scraper")
    print("  pixi install")
    sys.exit(1)


def scrape_hourly_electricity(start_date="2022-01-01", end_date="2024-12-31"):
    """Scrape hourly electricity data from Enova Power portal.

    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
    """
    print("="*60)
    print("Enova Power - Hourly Electricity Data Scraper")
    print("="*60)
    print()
    print(f"Date range: {start_date} to {end_date}")
    print()

    username = os.getenv("ENOVA_USERNAME")
    password = os.getenv("ENOVA_PASSWORD")

    if not username or not password:
        print("⚠️  Set environment variables:")
        print("  export ENOVA_USERNAME='your_username'")
        print("  export ENOVA_PASSWORD='your_password'")
        print()
        print("These are your credentials for https://myaccount.enovapower.com")
        return None

    print(f"Logging in as: {username}")
    print()
    print("NOTE: This will use Selenium to automate browser interactions.")
    print("You'll see a browser window open and navigate the portal.")
    print("This may take several minutes depending on the date range.")
    print()

    try:
        # Initialize API with headless=False so we can see what's happening
        # Change to headless=True once we know it works
        api = kwh.KitchenerWilmotHydroAPI(
            user=username,
            password=password,
            headless=False,  # Set to True to hide browser
            browser="Chrome",  # or "Firefox"
        )

        print(f"Downloading hourly data from {start_date} to {end_date}...")
        print("This will download one CSV per month...")
        print()

        df = api.download_hourly_data(start_date=start_date, end_date=end_date)

        if df is not None and len(df) > 0:
            print()
            print("="*60)
            print("✓ Success!")
            print("="*60)
            print(f"Downloaded {len(df)} hourly readings")
            print(f"Date range: {df.index.min()} to {df.index.max()}")
            print(f"Total kWh: {df['kWh'].sum():.1f}")
            print()
            print("Data saved to: ~/.utility-bill-scraper/")
            print()
            print("Next steps:")
            print("1. Export hourly history to CSV:")
            print("   df = api.history('hourly')")
            print("   df.to_csv('enova_hourly_2022_2024.csv')")
            print()
            print("2. Load into pipeline with Enova CSV source")

            return df
        else:
            print("❌ No data downloaded")
            return None

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    print("""
Enova Power Hourly Data Scraper
================================

This script will use Selenium to automate downloading hourly electricity
data from the Enova Power portal for the 2022-2024 period.

Prerequisites:
- Chrome browser installed (or Firefox if you prefer)
- ChromeDriver installed (brew install chromedriver on Mac)
- utility-bill-scraper dependencies installed:
    cd /Users/ryan/dev/utility-bill-scraper
    poetry install

Set your credentials as environment variables:
  export ENOVA_USERNAME='your_username'
  export ENOVA_PASSWORD='your_password'

WARNING: The old portal URL (www3.kwhydro.on.ca) may no longer work
after the Enova rebrand. If you get login errors, we'll need to update
the scraper code to use the new portal URL.

""")

    response = input("Continue? (y/n): ")
    if response.lower() != 'y':
        print("Cancelled")
        return

    # Try scraping 2022-2024
    df = scrape_hourly_electricity(start_date="2022-01-01", end_date="2024-12-31")

    if df is not None:
        print()
        save = input("Save to CSV? (y/n): ")
        if save.lower() == 'y':
            output_file = "enova_hourly_2022_2024.csv"
            df.to_csv(output_file)
            print(f"✓ Saved to {output_file}")
            print()
            print("You can now load this with the Enova CSV pipeline:")
            print("  python scripts/load_my_green_button_data.py")


if __name__ == "__main__":
    main()
