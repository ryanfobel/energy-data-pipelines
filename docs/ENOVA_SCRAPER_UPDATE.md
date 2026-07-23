# Enova Power Scraper Update

## Portal URL Changes

The utility-bill-scraper code uses the old Kitchener-Wilmot Hydro portal URL:
- **Old**: `https://www3.kwhydro.on.ca/app/login.jsp`
- **New**: `https://myaccount.enovapower.com/app/login.jsp`

Good news: The old URL redirects to the new one (301 redirect), so the scraper should still work without changes.

## Testing the Scraper

1. **Install dependencies**:
   ```bash
   cd /Users/ryan/dev/utility-bill-scraper
   poetry install
   ```

2. **Set credentials**:
   ```bash
   export ENOVA_USERNAME='your_username'
   export ENOVA_PASSWORD='your_password'
   ```

3. **Run the scraper**:
   ```bash
   cd /Users/ryan/dev/energy-data-pipelines
   python scripts/scrape_hourly_electricity.py
   ```

## What to Expect

The scraper will:
1. Open a Chrome browser window (use `headless=False` to see progress)
2. Login to the Enova portal
3. Iterate through each month in the date range (2022-2024)
4. Download CSV file for each month
5. Parse and combine into hourly DataFrame
6. Save to `~/.utility-bill-scraper/` directory

Expected downloads:
- **2022**: 12 months × ~730 hours = ~8,760 readings
- **2023**: 12 months × ~730 hours = ~8,760 readings
- **2024**: 12 months × ~730 hours = ~8,760 readings
- **Total**: ~26,280 hourly readings

## Potential Issues

### 1. Portal Changes
If Enova redesigned their portal after the rebrand, the Selenium selectors might not work:
- Login form IDs might have changed
- Download button selectors might be different
- Page structure might be updated

**Solution**: Run with `headless=False` first to see where it fails, then update the scraper code.

### 2. Rate Limiting
The scraper adds random delays (5-10 seconds) between requests to avoid being blocked:
```python
time.sleep(5 + random.random() * 5)
```

If you get blocked, increase these delays.

### 3. Download Limits
The portal might limit how far back you can download. The code checks for:
```python
"You are not authorized for this date range."
```

If this happens, we'll need to request historical data directly from Enova.

### 4. Authentication
If login fails:
- Verify credentials work on the portal manually
- Check if 2FA/MFA is enabled (scraper doesn't support this)
- Check if account is locked or requires password reset

## Updating the Scraper for New Portal

If we need to update for the new portal structure:

1. **Update login URL** in `kitchener_wilmot_hydro.py:274`:
   ```python
   self._driver.get("https://myaccount.enovapower.com/app/login.jsp")
   ```

2. **Update download URL** in `kitchener_wilmot_hydro.py:325`:
   ```python
   url = (
       "https://myaccount.enovapower.com/app/capricorn?para=smartMeterConsum&inquiryType=hydro"
       "&fromYear=%d&fromMonth=%02d&fromDay=%02d&toYear=%d&toMonth=%02d&toDay=%02d"
       % (date.year, date.month, 1, date.year, date.month, date.day)
   )
   ```

3. **Test with short date range first**:
   ```python
   df = api.download_hourly_data(start_date="2024-11-01", end_date="2024-11-30")
   ```

4. **Expand to full range once working**:
   ```python
   df = api.download_hourly_data(start_date="2022-01-01", end_date="2024-12-31")
   ```

## Alternative: Manual Download

If automation fails, you can manually download CSV files:

1. Login to https://myaccount.enovapower.com
2. Navigate to smart meter data / usage history
3. Download CSV for each month manually
4. Combine CSVs and load with our Enova CSV pipeline

This is tedious (36 months × manual clicks) but guaranteed to work.
