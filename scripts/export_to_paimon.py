#!/usr/bin/env python3
"""Export DuckDB tables to Paimon format (Parquet with partitioning)."""
import duckdb
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pipelines.config import load_config

def export_to_paimon(
    duckdb_path: str | Path,
    table_name: str,
    output_dir: str | Path,
    partition_cols: list[str]
):
    """Export DuckDB table to Parquet files with Hive-style partitioning.

    Args:
        duckdb_path: Path to DuckDB database
        table_name: Fully qualified table name (e.g., main_marts.fct_electricity_consumption)
        output_dir: Output directory for Parquet files
        partition_cols: Columns to partition by (e.g., ['home_id', 'year', 'month'])
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    print(f"Exporting {table_name} to Paimon format...")
    print(f"  Source: {duckdb_path}")
    print(f"  Destination: {output_path}")
    print(f"  Partitions: {partition_cols}")

    # Connect to DuckDB
    conn = duckdb.connect(str(duckdb_path), read_only=True)

    # Use DuckDB's COPY TO with PARTITION_BY
    partition_by_clause = ", ".join(partition_cols)

    sql = f"""
    COPY (SELECT * FROM {table_name})
    TO '{output_path}'
    (FORMAT PARQUET, PARTITION_BY ({partition_by_clause}), OVERWRITE_OR_IGNORE)
    """

    print(f"\n  SQL: {sql}\n")

    # Execute export
    result = conn.execute(sql).fetchall()
    print(f"  ✓ Export complete: {result}")
    conn.close()

    # List created files
    parquet_files = list(output_path.rglob("*.parquet"))
    print(f"\n  Created {len(parquet_files)} Parquet file(s):")

    # Group by partition
    partitions = {}
    for f in parquet_files:
        # Get partition path (everything between output_dir and filename)
        rel_path = f.relative_to(output_path)
        partition_path = rel_path.parent
        if partition_path not in partitions:
            partitions[partition_path] = []
        partitions[partition_path].append(f.name)

    for partition, files in sorted(partitions.items()):
        print(f"    {partition}/")
        for file in sorted(files):
            file_path = output_path / partition / file
            size_kb = file_path.stat().st_size / 1024
            print(f"      {file} ({size_kb:.1f} KB)")


def main():
    """Export energy data to Paimon warehouse."""
    # Load configuration
    config = load_config()

    warehouse_dir = Path(config['paths']['paimon_warehouse'])
    duckdb_path = config['paths']['duckdb']

    print("="*80)
    print("EXPORT TO PAIMON WAREHOUSE")
    print("="*80)
    print(f"Config: DuckDB={duckdb_path}, Warehouse={warehouse_dir}")

    # Export tables defined in config
    exports = config['paimon']['exports']
    for i, export_config in enumerate(exports, 1):
        table_name = export_config['table']
        output_dir_name = export_config['output_dir']
        partition_cols = export_config['partition_cols']

        print(f"\n[{i}/{len(exports)}] Exporting {table_name}...")
        export_to_paimon(
            duckdb_path=duckdb_path,
            table_name=table_name,
            output_dir=warehouse_dir / output_dir_name,
            partition_cols=partition_cols
        )

    print("\n" + "="*80)
    print("✅ PAIMON EXPORT COMPLETE")
    print("="*80)
    print(f"\nWarehouse location: {warehouse_dir}")

    # Show summary for each export
    for export_config in exports:
        output_dir_name = export_config['output_dir']
        export_dir = warehouse_dir / output_dir_name
        if export_dir.exists():
            parquet_count = len(list(export_dir.rglob('*.parquet')))
            print(f"  {output_dir_name}/ - {parquet_count} parquet files")
        else:
            print(f"  {output_dir_name}/ - (not created)")


if __name__ == "__main__":
    main()
