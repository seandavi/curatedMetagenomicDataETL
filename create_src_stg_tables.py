#!/usr/bin/env python3
"""
Create source views and staging tables for curatedMetagenomicData ETL pipeline.

Architecture:
- ext_* : External tables pointing to GCS (raw data)
- src_* : Views that add sample_id extraction (no cost, always fresh)
- stg_* : Materialized tables with proper types, clustered by sample_id (optimized for queries)
"""

from google.cloud import bigquery

# Configuration
PROJECT_ID = "curatedmetagenomicdata"
DATASET_ID = "curatedmetagenomicsdata"

# Source view definitions - minimal transformation, just add sample_id
SOURCE_VIEWS = {
    "src_marker_abundance": """
        SELECT
            REGEXP_EXTRACT(_FILE_NAME, r'/cMDv4/([^/]+)/') as sample_id,
            marker_id,
            abundance
        FROM `{project}.{dataset}.ext_marker_abundance`
    """,
    "src_marker_presence": """
        SELECT
            REGEXP_EXTRACT(_FILE_NAME, r'/cMDv4/([^/]+)/') as sample_id,
            marker_id,
            presence
        FROM `{project}.{dataset}.ext_marker_presence`
    """,
    "src_marker_rel_ab_w_read_stats": """
        SELECT
            REGEXP_EXTRACT(_FILE_NAME, r'/cMDv4/([^/]+)/') as sample_id,
            clade_name,
            clade_taxid,
            relative_abundance,
            coverage,
            estimated_reads
        FROM `{project}.{dataset}.ext_marker_rel_ab_w_read_stats`
    """,
    "src_metaphlan_unknown_list": """
        SELECT
            REGEXP_EXTRACT(_FILE_NAME, r'/cMDv4/([^/]+)/') as sample_id,
            clade_name,
            ncbi_tax_id,
            relative_abundance
        FROM `{project}.{dataset}.ext_metaphlan_unknown_list`
    """,
    "src_metaphlan_viruses_list": """
        SELECT
            REGEXP_EXTRACT(_FILE_NAME, r'/cMDv4/([^/]+)/') as sample_id,
            mv_group_cluster,
            genome_name,
            length,
            breadth_of_coverage,
            mapping_reads_count,
            rpkm,
            depth_of_coverage_mean,
            depth_of_coverage_median,
            mv_group_type,
            assigned_taxonomy,
            first_genome_in_cluster,
            other_genomes_in_cluster
        FROM `{project}.{dataset}.ext_metaphlan_viruses_list`
    """,
}

# Staging table queries - proper types, handle nulls/missing values
STAGING_QUERIES = {
    "stg_marker_abundance": """
        SELECT
            sample_id,
            marker_id,
            SAFE_CAST(abundance AS FLOAT64) as abundance
        FROM `{project}.{dataset}.src_marker_abundance`
        WHERE sample_id IS NOT NULL
    """,
    "stg_marker_presence": """
        SELECT
            sample_id,
            marker_id,
            SAFE_CAST(presence AS INT64) as presence
        FROM `{project}.{dataset}.src_marker_presence`
        WHERE sample_id IS NOT NULL
    """,
    "stg_marker_rel_ab_w_read_stats": """
        SELECT
            sample_id,
            clade_name,
            clade_taxid,
            SAFE_CAST(relative_abundance AS FLOAT64) as relative_abundance,
            SAFE_CAST(NULLIF(coverage, '-') AS FLOAT64) as coverage,
            SAFE_CAST(estimated_reads AS INT64) as estimated_reads
        FROM `{project}.{dataset}.src_marker_rel_ab_w_read_stats`
        WHERE sample_id IS NOT NULL
    """,
    "stg_metaphlan_unknown_list": """
        SELECT
            sample_id,
            clade_name,
            ncbi_tax_id,
            SAFE_CAST(relative_abundance AS FLOAT64) as relative_abundance
        FROM `{project}.{dataset}.src_metaphlan_unknown_list`
        WHERE sample_id IS NOT NULL
    """,
    "stg_metaphlan_viruses_list": """
        SELECT
            sample_id,
            mv_group_cluster,
            genome_name,
            SAFE_CAST(length AS INT64) as length,
            SAFE_CAST(breadth_of_coverage AS FLOAT64) as breadth_of_coverage,
            SAFE_CAST(mapping_reads_count AS INT64) as mapping_reads_count,
            SAFE_CAST(rpkm AS FLOAT64) as rpkm,
            SAFE_CAST(depth_of_coverage_mean AS FLOAT64) as depth_of_coverage_mean,
            SAFE_CAST(depth_of_coverage_median AS FLOAT64) as depth_of_coverage_median,
            mv_group_type,
            assigned_taxonomy,
            first_genome_in_cluster,
            other_genomes_in_cluster
        FROM `{project}.{dataset}.src_metaphlan_viruses_list`
        WHERE sample_id IS NOT NULL
    """,
}


def create_view(client: bigquery.Client, view_name: str, query: str):
    """Create or replace a BigQuery view."""
    view_id = f"{PROJECT_ID}.{DATASET_ID}.{view_name}"

    formatted_query = query.format(project=PROJECT_ID, dataset=DATASET_ID)

    view = bigquery.Table(view_id)
    view.view_query = formatted_query

    try:
        view = client.create_table(view, exists_ok=True)
        print(f"✓ Created view: {view_id}")
        return True
    except Exception as e:
        print(f"✗ Failed to create view {view_id}: {e}")
        return False


def create_staging_table(client: bigquery.Client, table_name: str, query: str):
    """Create or replace a staging table with clustering."""
    table_id = f"{PROJECT_ID}.{DATASET_ID}.{table_name}"

    formatted_query = query.format(project=PROJECT_ID, dataset=DATASET_ID)

    job_config = bigquery.QueryJobConfig(
        destination=table_id,
        write_disposition="WRITE_TRUNCATE",  # Full refresh
        clustering_fields=["sample_id"],
    )

    try:
        print(f"  Creating table: {table_id} (this may take a while...)")
        query_job = client.query(formatted_query, job_config=job_config)
        query_job.result()  # Wait for completion

        # Get table info
        table = client.get_table(table_id)
        print(f"✓ Created table: {table_id}")
        print(f"  Rows: {table.num_rows:,}")
        print(f"  Size: {table.num_bytes / (1024**3):.2f} GB")
        return True
    except Exception as e:
        print(f"✗ Failed to create table {table_id}: {e}")
        return False


def verify_counts(client: bigquery.Client):
    """Verify row counts across layers."""
    print("\n" + "="*80)
    print("Row Count Verification")
    print("="*80)

    tables_to_check = ["ext_marker_abundance", "src_marker_abundance", "stg_marker_abundance"]

    for table_name in tables_to_check:
        query = f"SELECT COUNT(*) as count FROM `{PROJECT_ID}.{DATASET_ID}.{table_name}`"
        try:
            result = client.query(query).result()
            count = list(result)[0].count
            print(f"{table_name:40s} {count:>15,} rows")
        except Exception as e:
            print(f"{table_name:40s} ERROR: {e}")


def main():
    """Main function to create source views and staging tables."""
    print(f"Creating source views and staging tables in {PROJECT_ID}.{DATASET_ID}\n")

    client = bigquery.Client(project=PROJECT_ID)

    # Step 1: Create source views
    print("="*80)
    print("STEP 1: Creating Source Views (src_*)")
    print("="*80)
    success_count = 0
    for view_name, query in SOURCE_VIEWS.items():
        if create_view(client, view_name, query):
            success_count += 1
    print(f"\nSource views: {success_count}/{len(SOURCE_VIEWS)} created successfully\n")

    # Step 2: Create staging tables
    print("="*80)
    print("STEP 2: Creating Staging Tables (stg_*)")
    print("="*80)
    print("Note: This will query all external data and materialize tables.")
    print("      This may take several minutes and incur BigQuery processing costs.\n")

    success_count = 0
    for table_name, query in STAGING_QUERIES.items():
        if create_staging_table(client, table_name, query):
            success_count += 1
        print()

    print(f"Staging tables: {success_count}/{len(STAGING_QUERIES)} created successfully\n")

    # Step 3: Verify counts
    if success_count > 0:
        verify_counts(client)

    # Print example queries
    print("\n" + "="*80)
    print("Example Queries")
    print("="*80)
    print("""
-- Query source view (reads from GCS each time)
SELECT sample_id, marker_id, abundance
FROM `{project}.{dataset}.src_marker_abundance`
LIMIT 10;

-- Query staging table (optimized, clustered by sample_id)
SELECT sample_id, marker_id, abundance
FROM `{project}.{dataset}.stg_marker_abundance`
WHERE sample_id = '00003b3459eb4248543210b603ecb1a9'
LIMIT 10;

-- Aggregate across all samples (use staging table for performance)
SELECT
    marker_id,
    COUNT(DISTINCT sample_id) as sample_count,
    AVG(abundance) as avg_abundance,
    MAX(abundance) as max_abundance
FROM `{project}.{dataset}.stg_marker_abundance`
GROUP BY marker_id
ORDER BY sample_count DESC
LIMIT 10;
""".format(project=PROJECT_ID, dataset=DATASET_ID))


if __name__ == "__main__":
    main()
