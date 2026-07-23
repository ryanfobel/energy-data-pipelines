#!/usr/bin/env python3
"""View data currently loaded in the Green Button pipeline."""
import dlt
from datetime import datetime


def view_data():
    """Show summary of loaded Green Button data."""
    pipeline = dlt.pipeline(
        pipeline_name="green_button",
        destination="duckdb",
        dataset_name="raw"
    )

    print("Green Button Data Pipeline")
    print(f"DuckDB file: {pipeline.pipelines_dir}/green_button.duckdb")
    print()

    with pipeline.sql_client() as client:
        # Total count
        with client.execute_query("SELECT COUNT(*) FROM green_button_interval_readings") as cursor:
            total = cursor.fetchone()[0]
            print(f"Total readings: {total:,}")
            print()

        if total == 0:
            print("No data loaded yet. Run: pixi run python scripts/load_my_green_button_data.py")
            return

        # By home
        with client.execute_query("""
            SELECT
                home_id,
                COUNT(*) as intervals,
                MIN(timestamp) as first_reading,
                MAX(timestamp) as last_reading
            FROM green_button_interval_readings
            GROUP BY home_id
            ORDER BY home_id
        """) as cursor:
            print("By home:")
            for row in cursor.fetchall():
                print(f"\n  {row[0]}")
                print(f"    Intervals: {row[1]:,}")
                print(f"    Date range: {row[2]} to {row[3]}")

        # By commodity
        print("\n" + "="*60)
        with client.execute_query("""
            SELECT
                home_id,
                commodity,
                service_kind,
                uom,
                COUNT(*) as intervals,
                MIN(timestamp) as first_reading,
                MAX(timestamp) as last_reading,
                SUM(kwh) as total_consumption,
                SUM(cost) as total_cost
            FROM green_button_interval_readings
            GROUP BY home_id, commodity, service_kind, uom
            ORDER BY home_id, last_reading DESC
        """) as cursor:
            print("\nBy commodity:")
            current_home = None
            for row in cursor.fetchall():
                if row[0] != current_home:
                    current_home = row[0]
                    print(f"\n  Home: {current_home}")

                # Decode commodity name
                commodity_name = decode_commodity(row[1])
                unit_name = decode_uom(row[3])

                print(f"\n    {commodity_name.upper()}")
                print(f"      Intervals: {row[4]:,}")
                print(f"      Date range: {row[5]} to {row[6]}")
                if row[7]:
                    print(f"      Total consumption: {row[7]:,.2f} {unit_name}")
                if row[8] and row[8] > 0:
                    print(f"      Total cost: ${row[8]/100:,.2f}")

        # Recent readings
        print("\n" + "="*60)
        print("\nRecent readings (last 10):")
        with client.execute_query("""
            SELECT
                timestamp,
                commodity,
                kwh,
                cost,
                quality_code,
                tou_bucket
            FROM green_button_interval_readings
            ORDER BY timestamp DESC
            LIMIT 10
        """) as cursor:
            print()
            for row in cursor.fetchall():
                commodity = decode_commodity(row[1])
                cost_str = f"${row[3]/100:6.2f}" if row[3] else "   n/a "
                tou_str = f"TOU={row[5]}" if row[5] else ""
                print(f"  {row[0]} | {commodity:12} | {row[2]:8.2f} | {cost_str} | {tou_str}")


def decode_commodity(value):
    """Decode ESPI commodity code."""
    mapping = {
        'CommodityKindValue.VALUE_0': 'not-applicable',
        'CommodityKindValue.VALUE_1': 'electricity',
        'CommodityKindValue.VALUE_2': 'natural-gas',
        'CommodityKindValue.VALUE_7': 'natural-gas',  # Another gas code
        'CommodityKindValue.VALUE_9': 'water',
    }
    return mapping.get(value, value)


def decode_uom(value):
    """Decode ESPI unit of measure code."""
    mapping = {
        'UnitSymbolKindValue.VALUE_42': 'm³',  # cubic meters
        'UnitSymbolKindValue.VALUE_72': 'Wh',   # watt-hours
    }
    return mapping.get(value, value)


if __name__ == "__main__":
    view_data()
