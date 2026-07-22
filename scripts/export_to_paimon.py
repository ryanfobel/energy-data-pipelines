#!/usr/bin/env python3
"""Export DuckDB tables to Paimon warehouse with real Paimon tables."""
import duckdb
import pyarrow as pa
from pathlib import Path
import sys
import time

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pipelines.config import load_config


def _arrow_to_paimon_type(arrow_type: pa.DataType) -> str:
    """Map a PyArrow type to a Paimon SQL type string."""
    if pa.types.is_int8(arrow_type):
        return "TINYINT"
    if pa.types.is_int16(arrow_type):
        return "SMALLINT"
    if pa.types.is_int32(arrow_type):
        return "INT"
    if pa.types.is_int64(arrow_type):
        return "BIGINT"
    if pa.types.is_float32(arrow_type):
        return "FLOAT"
    if pa.types.is_float64(arrow_type):
        return "DOUBLE"
    if pa.types.is_date(arrow_type):
        return "DATE"
    if pa.types.is_timestamp(arrow_type):
        return "TIMESTAMP"
    if pa.types.is_boolean(arrow_type):
        return "BOOLEAN"
    if pa.types.is_decimal(arrow_type):
        return f"DECIMAL({arrow_type.precision},{arrow_type.scale})"
    return "STRING"


def export_to_paimon(
    duckdb_path: str | Path,
    table_name: str,
    warehouse_path: str | Path,
    database: str,
    paimon_table_name: str,
    primary_keys: list[str] | None = None
) -> dict:
    """Export DuckDB table to Paimon warehouse.

    Args:
        duckdb_path: Path to DuckDB database
        table_name: Fully qualified table name in DuckDB (e.g., main_marts.fct_electricity_consumption)
        warehouse_path: Paimon warehouse directory
        database: Paimon database name
        paimon_table_name: Paimon table name
        primary_keys: List of primary key columns (optional)

    Returns:
        dict with stats (rows_exported, write_time_s)
    """
    try:
        from pypaimon import CatalogFactory, Schema
        from pypaimon.schema.data_types import DataField, DataTypeParser
    except ImportError as exc:
        raise RuntimeError(
            "pypaimon requires Java 11+ on PATH. "
            "Run: pixi install  (openjdk is declared in pixi.toml)"
        ) from exc

    print(f"\nExporting {table_name} → {database}.{paimon_table_name}")
    print(f"  Warehouse: {warehouse_path}")

    # Read table from DuckDB as Arrow
    conn = duckdb.connect(str(duckdb_path), read_only=True)
    arrow_table = conn.execute(f"SELECT * FROM {table_name}").fetch_arrow_table()
    conn.close()

    row_count = len(arrow_table)
    print(f"  Source rows: {row_count:,}")

    # Create Paimon catalog and database
    catalog = CatalogFactory.create({"warehouse": str(warehouse_path)})
    catalog.create_database(database, ignore_if_exists=True)

    # Create Paimon schema from Arrow schema
    fields = [
        DataField(i, name, DataTypeParser.parse_atomic_type_sql_string(
            _arrow_to_paimon_type(arrow_table.schema.field(name).type)
        ))
        for i, name in enumerate(arrow_table.schema.names)
    ]

    paimon_schema = Schema(
        fields=fields,
        primary_keys=primary_keys or [],
        options={}
    )

    # Create or recreate table
    full_table_name = f"{database}.{paimon_table_name}"
    if catalog.table_exists(full_table_name):
        print(f"  Table exists, dropping and recreating...")
        catalog.drop_table(full_table_name)

    catalog.create_table(full_table_name, paimon_schema, ignore_if_exists=False)

    # Write data
    table = catalog.get_table(full_table_name)
    write_builder = table.new_batch_write_builder()
    writer = write_builder.new_write()
    committer = write_builder.new_commit()

    t0 = time.perf_counter()
    writer.write_arrow(arrow_table)
    committer.commit(writer.prepare_commit())
    elapsed = time.perf_counter() - t0

    print(f"  ✓ Wrote {row_count:,} rows in {elapsed:.2f}s")

    return {
        "table": full_table_name,
        "rows_exported": row_count,
        "write_time_s": elapsed
    }


def main():
    """Export energy data to Paimon warehouse."""
    # Load configuration
    config = load_config()

    warehouse_dir = Path(config['paths']['paimon_warehouse'])
    duckdb_path = config['paths']['duckdb']

    print("=" * 80)
    print("EXPORT TO PAIMON WAREHOUSE")
    print("=" * 80)
    print(f"DuckDB: {duckdb_path}")
    print(f"Warehouse: {warehouse_dir}")

    # Ensure warehouse directory exists
    warehouse_dir.mkdir(parents=True, exist_ok=True)

    # Export tables defined in config
    exports = config['paimon']['exports']
    results = []

    for i, export_config in enumerate(exports, 1):
        print(f"\n[{i}/{len(exports)}]")
        result = export_to_paimon(
            duckdb_path=duckdb_path,
            table_name=export_config['table'],
            warehouse_path=warehouse_dir,
            database=export_config.get('database', 'energy'),
            paimon_table_name=export_config['paimon_table'],
            primary_keys=export_config.get('primary_keys')
        )
        results.append(result)

    # Summary
    print("\n" + "=" * 80)
    print("✅ PAIMON EXPORT COMPLETE")
    print("=" * 80)
    print(f"\nWarehouse location: {warehouse_dir}")
    print(f"\nExported {len(results)} table(s):")

    total_rows = sum(r['rows_exported'] for r in results)
    total_time = sum(r['write_time_s'] for r in results)

    for r in results:
        print(f"  {r['table']}: {r['rows_exported']:,} rows ({r['write_time_s']:.2f}s)")

    print(f"\nTotal: {total_rows:,} rows in {total_time:.2f}s")
    print(f"\nSync with: rclone sync {warehouse_dir} remote:backup/energy-warehouse")


if __name__ == "__main__":
    main()
