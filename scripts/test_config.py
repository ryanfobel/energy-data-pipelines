#!/usr/bin/env python3
"""Test configuration loading."""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pipelines.config import load_config


def test_config():
    """Test configuration loading."""
    print("="*80)
    print("CONFIGURATION SYSTEM TEST")
    print("="*80)

    try:
        config = load_config()
        print("\n✓ Configuration loaded successfully!\n")

        # Display key configuration values
        print("Paths:")
        print(f"  DuckDB: {config['paths']['duckdb']}")
        print(f"  Paimon warehouse: {config['paths']['paimon_warehouse']}")
        print(f"  Mock data: {config['paths']['mock_data']}")
        print(f"  Logs: {config['paths']['logs']}")
        print(f"  Data: {config['paths']['data']}")

        print("\nHome Assistant:")
        print(f"  Enabled: {config['home_assistant']['enabled']}")
        parquet_file = config['home_assistant'].get('parquet_file')
        print(f"  Parquet file: {parquet_file or 'Not configured (will use env var)'}")

        print("\nGreen Button:")
        print(f"  Enabled: {config['green_button']['enabled']}")
        xml_dir = config['green_button'].get('xml_directory')
        print(f"  XML directory: {xml_dir or 'Not configured (will use env var)'}")
        print(f"  Default home ID: {config['green_button']['default_home_id']}")

        print("\nPaimon Exports:")
        for i, export in enumerate(config['paimon']['exports'], 1):
            print(f"  {i}. {export['table']}")
            print(f"     -> {export['output_dir']}/")
            print(f"     Partitions: {', '.join(export['partition_cols'])}")

        print("\nDLT Configuration:")
        print(f"  Destination: {config['dlt']['destination']}")
        print(f"  Datasets: {config['dlt']['datasets']}")

        print("\nData Quality:")
        print(f"  Max watts: {config['quality']['max_watts']:,}")
        print(f"  Filter negative: {config['quality']['filter_negative']}")

        print("\nLogging:")
        print(f"  Level: {config['logging']['level']}")
        print(f"  Log to file: {config['logging']['log_to_file']}")

        print("\n" + "="*80)
        print("✅ CONFIGURATION TEST PASSED")
        print("="*80)
        print("\nNext steps:")
        print("  1. Copy config.example.yml to config.local.yml")
        print("  2. Copy .env.example to .env")
        print("  3. Edit config.local.yml and .env with your settings")
        print("  4. Run this script again to verify")

    except Exception as e:
        print(f"\n❌ Configuration test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    test_config()
