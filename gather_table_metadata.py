#!/usr/bin/env python3
"""
Gather metadata for all BigQuery tables and views in the curatedMetagenomicData ETL pipeline.

Collects:
- Schema (field names, types, modes)
- Row counts
- Size in bytes and GB
- Creation and modification timestamps
- Table type (TABLE, VIEW, EXTERNAL)
- Clustering fields
"""

from google.cloud import bigquery
import json
from datetime import datetime
from typing import Dict, List, Any

# Configuration
PROJECT_ID = "curatedmetagenomicdata"
DATASET_ID = "curatedmetagenomicsdata"
OUTPUT_FILE = "table_metadata.json"


def get_table_metadata(client: bigquery.Client, table_id: str) -> Dict[str, Any]:
    """Get comprehensive metadata for a single table or view."""

    try:
        table = client.get_table(table_id)

        # Basic metadata
        metadata = {
            "table_id": table.table_id,
            "full_table_id": f"{table.project}.{table.dataset_id}.{table.table_id}",
            "table_type": table.table_type,
            "created": table.created.isoformat() if table.created else None,
            "modified": table.modified.isoformat() if table.modified else None,
        }

        # Schema
        if table.schema:
            metadata["schema"] = [
                {
                    "name": field.name,
                    "type": field.field_type,
                    "mode": field.mode,
                    "description": field.description,
                }
                for field in table.schema
            ]
            metadata["num_fields"] = len(table.schema)
        else:
            metadata["schema"] = []
            metadata["num_fields"] = 0

        # Size and row count (only for tables, not views)
        if table.table_type in ["TABLE", "EXTERNAL"]:
            metadata["num_rows"] = table.num_rows
            metadata["num_bytes"] = table.num_bytes
            metadata["size_gb"] = round(table.num_bytes / (1024**3), 2) if table.num_bytes else 0
        else:
            metadata["num_rows"] = None
            metadata["num_bytes"] = None
            metadata["size_gb"] = None

        # Clustering fields
        if table.clustering_fields:
            metadata["clustering_fields"] = table.clustering_fields
        else:
            metadata["clustering_fields"] = []

        # View-specific metadata
        if table.table_type == "VIEW":
            metadata["view_query"] = table.view_query

        # External table metadata
        if table.table_type == "EXTERNAL" and table.external_data_configuration:
            ext_config = table.external_data_configuration
            metadata["external_config"] = {
                "source_format": ext_config.source_format,
                "source_uris": ext_config.source_uris[:3] if ext_config.source_uris else [],  # First 3 URIs
                "num_source_uris": len(ext_config.source_uris) if ext_config.source_uris else 0,
                "compression": ext_config.compression,
            }
            if ext_config.csv_options:
                metadata["external_config"]["csv_options"] = {
                    "skip_leading_rows": ext_config.csv_options.skip_leading_rows,
                    "field_delimiter": ext_config.csv_options.field_delimiter,
                }

        # Labels
        if table.labels:
            metadata["labels"] = table.labels

        return metadata

    except Exception as e:
        return {
            "table_id": table_id.split(".")[-1],
            "error": str(e),
        }


def gather_all_metadata(client: bigquery.Client) -> Dict[str, Any]:
    """Gather metadata for all tables in the dataset."""

    dataset_id = f"{PROJECT_ID}.{DATASET_ID}"

    # Get dataset metadata
    dataset = client.get_dataset(dataset_id)

    result = {
        "metadata_generated": datetime.utcnow().isoformat(),
        "project_id": PROJECT_ID,
        "dataset_id": DATASET_ID,
        "dataset_location": dataset.location,
        "dataset_created": dataset.created.isoformat() if dataset.created else None,
        "dataset_modified": dataset.modified.isoformat() if dataset.modified else None,
        "tables": {},
        "summary": {
            "total_tables": 0,
            "by_type": {},
            "by_prefix": {},
            "total_rows": 0,
            "total_size_gb": 0.0,
        }
    }

    # List all tables
    tables = list(client.list_tables(dataset_id))
    result["summary"]["total_tables"] = len(tables)

    # Gather metadata for each table
    for table_item in sorted(tables, key=lambda t: t.table_id):
        table_id = f"{dataset_id}.{table_item.table_id}"
        print(f"Gathering metadata for: {table_item.table_id}")

        metadata = get_table_metadata(client, table_id)
        result["tables"][table_item.table_id] = metadata

        # Update summary stats
        if "error" not in metadata:
            table_type = metadata.get("table_type", "UNKNOWN")
            result["summary"]["by_type"][table_type] = result["summary"]["by_type"].get(table_type, 0) + 1

            # Count by prefix (ext_, src_, stg_)
            prefix = table_item.table_id.split("_")[0] + "_"
            result["summary"]["by_prefix"][prefix] = result["summary"]["by_prefix"].get(prefix, 0) + 1

            # Aggregate size and rows (only for actual tables)
            if metadata.get("num_rows"):
                result["summary"]["total_rows"] += metadata["num_rows"]
            if metadata.get("size_gb"):
                result["summary"]["total_size_gb"] += metadata["size_gb"]

    result["summary"]["total_size_gb"] = round(result["summary"]["total_size_gb"], 2)

    return result


def main():
    """Main function to gather and save table metadata."""

    print(f"Gathering metadata for {PROJECT_ID}.{DATASET_ID}")
    print(f"Output will be saved to: {OUTPUT_FILE}\n")

    client = bigquery.Client(project=PROJECT_ID)

    # Gather all metadata
    metadata = gather_all_metadata(client)

    # Save to JSON file
    with open(OUTPUT_FILE, "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"\n{'='*80}")
    print("Metadata Collection Complete!")
    print(f"{'='*80}")
    print(f"Output saved to: {OUTPUT_FILE}")
    print(f"\nSummary:")
    print(f"  Total tables/views: {metadata['summary']['total_tables']}")
    print(f"  By type:")
    for table_type, count in sorted(metadata['summary']['by_type'].items()):
        print(f"    {table_type}: {count}")
    print(f"  By prefix:")
    for prefix, count in sorted(metadata['summary']['by_prefix'].items()):
        print(f"    {prefix}: {count}")
    print(f"  Total rows (tables only): {metadata['summary']['total_rows']:,}")
    print(f"  Total size (tables only): {metadata['summary']['total_size_gb']:.2f} GB")

    # List tables by category
    print(f"\n{'='*80}")
    print("Tables by Category:")
    print(f"{'='*80}")

    for prefix in ["ext_", "src_", "stg_"]:
        prefix_tables = [name for name in metadata["tables"].keys() if name.startswith(prefix)]
        if prefix_tables:
            print(f"\n{prefix}* tables/views ({len(prefix_tables)}):")
            for name in sorted(prefix_tables):
                table_meta = metadata["tables"][name]
                if "error" not in table_meta:
                    table_type = table_meta.get("table_type", "?")
                    rows = table_meta.get("num_rows")
                    size = table_meta.get("size_gb")
                    if rows is not None:
                        print(f"  {name:40s} [{table_type:8s}] {rows:>15,} rows, {size:>8.2f} GB")
                    else:
                        print(f"  {name:40s} [{table_type:8s}]")


if __name__ == "__main__":
    main()
