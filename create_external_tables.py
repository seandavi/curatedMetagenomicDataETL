#!/usr/bin/env python3
"""
Create BigQuery external tables for curatedMetagenomicData ETL pipeline.

This script creates external tables that reference gzipped TSV files in GCS,
automatically extracting sample IDs from the file path using _FILE_NAME.
"""

from google.cloud import bigquery
import json
from pathlib import Path

# Configuration
PROJECT_ID = "curatedmetagenomicdata"
DATASET_ID = "curatedmetagenomicsdata"
GCS_BUCKET = "gs://cmgd-data/results/cMDv4"

# Table definitions: name -> (path_pattern, schema, skip_leading_rows)
TABLE_DEFINITIONS = {
    "ext_marker_abundance": {
        "path": f"{GCS_BUCKET}/*/metaphlan_markers/marker_abundance.tsv.gz",
        "skip_rows": 4,
        "schema": [
            bigquery.SchemaField("marker_id", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("abundance", "FLOAT", mode="NULLABLE"),
        ],
    },
    "ext_marker_presence": {
        "path": f"{GCS_BUCKET}/*/metaphlan_markers/marker_presence.tsv.gz",
        "skip_rows": 4,
        "schema": [
            bigquery.SchemaField("marker_id", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("presence", "INTEGER", mode="NULLABLE"),
        ],
    },
    "ext_marker_rel_ab_w_read_stats": {
        "path": f"{GCS_BUCKET}/*/metaphlan_markers/marker_rel_ab_w_read_stats.tsv.gz",
        "skip_rows": 6,
        "schema": [
            bigquery.SchemaField("clade_name", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("clade_taxid", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("relative_abundance", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("coverage", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("estimated_reads", "STRING", mode="NULLABLE"),
        ],
    },
    "ext_metaphlan_unknown_list": {
        "path": f"{GCS_BUCKET}/*/metaphlan_lists/metaphlan_unknown_list.tsv.gz",
        "skip_rows": 5,
        "schema": [
            bigquery.SchemaField("clade_name", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("ncbi_tax_id", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("relative_abundance", "STRING", mode="NULLABLE"),
        ],
    },
    "ext_metaphlan_viruses_list": {
        "path": f"{GCS_BUCKET}/*/metaphlan_lists/metaphlan_viruses_list.tsv.gz",
        "skip_rows": 4,
        "schema": [
            bigquery.SchemaField("mv_group_cluster", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("genome_name", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("length", "INTEGER", mode="NULLABLE"),
            bigquery.SchemaField("breadth_of_coverage", "FLOAT", mode="NULLABLE"),
            bigquery.SchemaField("mapping_reads_count", "INTEGER", mode="NULLABLE"),
            bigquery.SchemaField("rpkm", "FLOAT", mode="NULLABLE"),
            bigquery.SchemaField("depth_of_coverage_mean", "FLOAT", mode="NULLABLE"),
            bigquery.SchemaField("depth_of_coverage_median", "FLOAT", mode="NULLABLE"),
            bigquery.SchemaField("mv_group_type", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("assigned_taxonomy", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("first_genome_in_cluster", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("other_genomes_in_cluster", "STRING", mode="NULLABLE"),
        ],
    },
}


def create_external_table(client: bigquery.Client, table_name: str, definition: dict):
    """Create a BigQuery external table."""

    table_id = f"{PROJECT_ID}.{DATASET_ID}.{table_name}"

    # Create external config
    external_config = bigquery.ExternalConfig("CSV")
    external_config.source_uris = [definition["path"]]
    external_config.compression = "GZIP"
    external_config.options.skip_leading_rows = definition["skip_rows"]
    external_config.options.field_delimiter = "\t"
    external_config.schema = definition["schema"]

    # Create table object
    table = bigquery.Table(table_id)
    table.external_data_configuration = external_config

    # Create or update the table
    try:
        table = client.create_table(table, exists_ok=True)
        print(f"✓ Created external table: {table_id}")
        return True
    except Exception as e:
        print(f"✗ Failed to create {table_id}: {e}")
        return False


def verify_table(client: bigquery.Client, table_name: str):
    """Verify table by running a test query."""

    table_id = f"{PROJECT_ID}.{DATASET_ID}.{table_name}"

    query = f"""
    SELECT
        _FILE_NAME,
        REGEXP_EXTRACT(_FILE_NAME, r'/cMDv4/([^/]+)/') as sample_id,
        *
    FROM `{table_id}`
    LIMIT 3
    """

    try:
        results = client.query(query).result()
        print(f"  Sample rows from {table_name}:")
        for row in results:
            print(f"    Sample ID: {row.sample_id}")
        return True
    except Exception as e:
        print(f"  ✗ Verification failed: {e}")
        return False


def main():
    """Main function to create all external tables."""

    print(f"Creating external tables in {PROJECT_ID}.{DATASET_ID}\n")

    # Initialize BigQuery client
    client = bigquery.Client(project=PROJECT_ID)

    # Ensure dataset exists
    dataset_id = f"{PROJECT_ID}.{DATASET_ID}"
    try:
        client.get_dataset(dataset_id)
        print(f"✓ Dataset {dataset_id} exists\n")
    except Exception:
        print(f"✗ Dataset {dataset_id} not found. Create it first with:")
        print(f"  bq mk --dataset --location=US {dataset_id}")
        return

    # Create all tables
    success_count = 0
    for table_name, definition in TABLE_DEFINITIONS.items():
        if create_external_table(client, table_name, definition):
            success_count += 1
            # Optionally verify each table
            # verify_table(client, table_name)
        print()

    print(f"Summary: {success_count}/{len(TABLE_DEFINITIONS)} tables created successfully")

    # Show example query to extract sample IDs
    print("\n" + "="*80)
    print("Example query to extract sample_id from _FILE_NAME:")
    print("="*80)
    example_table = list(TABLE_DEFINITIONS.keys())[0]
    print(f"""
SELECT
    REGEXP_EXTRACT(_FILE_NAME, r'/cMDv4/([^/]+)/') as sample_id,
    *
FROM `{PROJECT_ID}.{DATASET_ID}.{example_table}`
LIMIT 10
""")


if __name__ == "__main__":
    main()
