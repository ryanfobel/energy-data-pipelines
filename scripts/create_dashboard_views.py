#!/usr/bin/env -S pixi run python
"""Create views in main schema for Evidence dashboard."""
import duckdb

def main():
    conn = duckdb.connect('/Users/ryan/dev/energy-data-pipelines/energy_warehouse.duckdb')

    # Create views in main schema pointing to main_marts tables
    conn.execute('CREATE OR REPLACE VIEW fct_gas_consumption AS SELECT * FROM main_marts.fct_gas_consumption')
    conn.execute('CREATE OR REPLACE VIEW fct_water_consumption AS SELECT * FROM main_marts.fct_water_consumption')

    print('✓ Created views in main schema')

    # Verify
    result = conn.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'main'
        AND table_name LIKE 'fct_%'
        ORDER BY table_name
    """).fetchall()

    print('Views in main schema:')
    for row in result:
        print(f'  - {row[0]}')

if __name__ == '__main__':
    main()
