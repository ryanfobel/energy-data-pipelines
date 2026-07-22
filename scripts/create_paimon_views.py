#!/usr/bin/env python3
"""Create DuckDB views that read from Paimon warehouse via pypaimon-rust."""
import duckdb
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pipelines.config import load_config


def create_paimon_view(
    conn: duckdb.DuckDBPyConnection,
    warehouse_path: str | Path,
    database: str,
    paimon_table_name: str,
    view_schema: str,
    view_name: str
) -> int:
    """Create a DuckDB view that reads from a Paimon table via pypaimon-rust.

    Args:
        conn: DuckDB connection
        warehouse_path: Paimon warehouse directory
        database: Paimon database name
        paimon_table_name: Paimon table name
        view_schema: DuckDB schema for the view
        view_name: DuckDB view name

    Returns:
        Row count from the Paimon table
    """
    try:
        from pypaimon_rust.datafusion import PaimonCatalog
    except ImportError as exc:
        raise RuntimeError(
            "pypaimon-rust not installed: pixi install"
        ) from exc

    print(f"\nCreating view {view_schema}.{view_name} → {database}.{paimon_table_name}")
    print(f"  Warehouse: {warehouse_path}")

    # Read from Paimon via pypaimon-rust
    catalog = PaimonCatalog({"warehouse": str(warehouse_path)})
    table = catalog.get_table(f"{database}.{paimon_table_name}")
    batches = table.new_read_builder().new_scan().read()

    if not batches:
        print(f"  ⚠ Table is empty")
        return 0

    # Convert to Arrow table
    import pyarrow as pa
    arrow_table = pa.Table.from_batches(batches)
    row_count = len(arrow_table)

    print(f"  Rows: {row_count:,}")

    # Register as temporary table
    temp_table_name = f"_paimon_{paimon_table_name}"
    conn.register(temp_table_name, arrow_table)

    # Create schema if needed
    conn.execute(f"CREATE SCHEMA IF NOT EXISTS {view_schema}")

    # Drop existing view
    conn.execute(f"DROP VIEW IF EXISTS {view_schema}.{view_name}")

    # Create view
    conn.execute(f"""
        CREATE VIEW {view_schema}.{view_name} AS
        SELECT * FROM {temp_table_name}
    """)

    print(f"  ✓ View created")

    return row_count


def main():
    """Create DuckDB views for all Paimon tables."""
    # Load configuration
    config = load_config()

    warehouse_dir = Path(config['paths']['paimon_warehouse'])
    duckdb_path = config['paths']['duckdb']

    print("=" * 80)
    print("CREATE DUCKDB VIEWS → PAIMON WAREHOUSE")
    print("=" * 80)
    print(f"DuckDB: {duckdb_path}")
    print(f"Warehouse: {warehouse_dir}")

    if not warehouse_dir.exists():
        print(f"\n❌ Warehouse not found: {warehouse_dir}")
        print("   Run: pixi run export-paimon  (to create Paimon tables first)")
        sys.exit(1)

    # Connect to DuckDB
    conn = duckdb.connect(str(duckdb_path))

    # Create views for each exported table
    exports = config['paimon']['exports']
    results = []

    for i, export_config in enumerate(exports, 1):
        print(f"\n[{i}/{len(exports)}]")

        # Extract schema and table name from DuckDB table
        parts = export_config['table'].split('.')
        if len(parts) == 2:
            view_schema, original_table = parts
        else:
            view_schema = "main_marts"
            original_table = parts[0]

        try:
            row_count = create_paimon_view(
                conn=conn,
                warehouse_path=warehouse_dir,
                database=export_config.get('database', 'energy'),
                paimon_table_name=export_config['paimon_table'],
                view_schema=view_schema,
                view_name=original_table
            )
            results.append({
                'view': f"{view_schema}.{original_table}",
                'paimon_table': export_config['paimon_table'],
                'rows': row_count
            })
        except Exception as e:
            print(f"  ❌ Error: {e}")
            results.append({
                'view': f"{view_schema}.{original_table}",
                'paimon_table': export_config['paimon_table'],
                'error': str(e)
            })

    conn.close()

    # Summary
    print("\n" + "=" * 80)
    print("✅ DUCKDB VIEWS CREATED")
    print("=" * 80)
    print(f"\nCreated {len(results)} view(s):")

    for r in results:
        if 'error' in r:
            print(f"  ❌ {r['view']} → {r['paimon_table']}: {r['error']}")
        else:
            print(f"  ✓ {r['view']} → {r['paimon_table']}: {r['rows']:,} rows")

    print(f"\nEvidence dashboard will now query these views from: {duckdb_path}")


if __name__ == "__main__":
    main()
