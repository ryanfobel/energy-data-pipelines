#!/usr/bin/env python3
"""
Scrape utility bills for 2022-2024 using utility-bill-scraper.

This will attempt to login to utility portals and download bill data.
You'll need to provide your credentials.
"""
import sys
from pathlib import Path

# Add utility-bill-scraper to path
scraper_path = Path("/Users/ryan/dev/utility-bill-scraper/src")
sys.path.insert(0, str(scraper_path))

try:
    import utility_bill_scraper.canada.on.kitchener_utilities as ku
    import utility_bill_scraper.canada.on.kitchener_wilmot_hydro as kwh
except ImportError as e:
    print(f"Error importing utility-bill-scraper: {e}")
    print("Make sure the utility-bill-scraper dependencies are installed")
    sys.exit(1)

import os


def scrape_kitchener_utilities():
    """Scrape Kitchener Utilities (gas + water)."""
    print("="*60)
    print("Kitchener Utilities (Gas + Water)")
    print("="*60)

    username = os.getenv("KITCHENER_UTILITIES_USERNAME")
    password = os.getenv("KITCHENER_UTILITIES_PASSWORD")

    if not username or not password:
        print("⚠️  Set environment variables:")
        print("  export KITCHENER_UTILITIES_USERNAME='your_username'")
        print("  export KITCHENER_UTILITIES_PASSWORD='your_password'")
        return None

    print(f"Logging in as: {username}")

    try:
        api = ku.KitchenerUtilitiesAPI(username=username, password=password)
        updates = api.update()

        if updates is not None:
            print(f"✓ Downloaded {len(updates)} statements")
            df = api.history("monthly")
            print(f"✓ Total history: {len(df)} months")
            return df
        else:
            print("No new statements found")
            df = api.history("monthly")
            return df

    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def scrape_enova_power():
    """Scrape Enova Power (formerly Kitchener-Wilmot Hydro) for electricity."""
    print()
    print("="*60)
    print("Enova Power / Kitchener-Wilmot Hydro (Electricity)")
    print("="*60)

    username = os.getenv("ENOVA_USERNAME")
    password = os.getenv("ENOVA_PASSWORD")

    if not username or not password:
        print("⚠️  Set environment variables:")
        print("  export ENOVA_USERNAME='your_username'")
        print("  export ENOVA_PASSWORD='your_password'")
        return None

    print(f"Logging in as: {username}")

    try:
        api = kwh.KitchenerWilmotHydroAPI(username=username, password=password)
        updates = api.update()

        if updates is not None:
            print(f"✓ Downloaded {len(updates)} statements")
            df = api.history("monthly")
            print(f"✓ Total history: {len(df)} months")
            return df
        else:
            print("No new statements found")
            df = api.history("monthly")
            return df

    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def main():
    print("""
Utility Bill Scraper - 2022-2024 Data Collection
================================================

This script will attempt to scrape your utility bills from:
1. Kitchener Utilities (gas + water)
2. Enova Power (electricity)

Prerequisites:
- Chrome browser installed
- Selenium webdriver
- Valid credentials for utility portals

Set your credentials as environment variables before running:
  export KITCHENER_UTILITIES_USERNAME='your_username'
  export KITCHENER_UTILITIES_PASSWORD='your_password'
  export ENOVA_USERNAME='your_username'
  export ENOVA_PASSWORD='your_password'

The scrapers will:
- Login to the utility portal
- Download all available PDF bills
- Extract usage data and save to CSV
- Data saved to: ~/.utility-bill-scraper/

""")

    response = input("Continue? (y/n): ")
    if response.lower() != 'y':
        print("Cancelled")
        return

    # Try scraping
    ku_data = scrape_kitchener_utilities()
    enova_data = scrape_enova_power()

    print()
    print("="*60)
    print("Summary")
    print("="*60)

    if ku_data is not None:
        print(f"✓ Kitchener Utilities: {len(ku_data)} months")
        print(f"  Date range: {ku_data.index.min()} to {ku_data.index.max()}")
    else:
        print("❌ Kitchener Utilities: Failed")

    if enova_data is not None:
        print(f"✓ Enova Power: {len(enova_data)} months")
        print(f"  Date range: {enova_data.index.min()} to {enova_data.index.max()}")
    else:
        print("❌ Enova Power: Failed")

    print()
    print("Next steps:")
    print("1. Check ~/.utility-bill-scraper/ for downloaded data")
    print("2. Export to CSV if needed")
    print("3. Load into pipeline with load_historical_bills.py")


if __name__ == "__main__":
    main()
