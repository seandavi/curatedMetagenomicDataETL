# User Guide: Accessing curatedMetagenomicData in BigQuery

This guide shows you how to access and query the curatedMetagenomicData tables in BigQuery.

## Table of Contents
- [Quick Start](#quick-start)
- [Available Tables](#available-tables)
- [Setting Up Access](#setting-up-access)
- [Query Examples](#query-examples)
- [Best Practices](#best-practices)
- [API Access](#api-access)

## Quick Start

The fastest way to start querying the data is through the BigQuery Console:

1. Go to https://console.cloud.google.com/bigquery
2. Select project: `curatedmetagenomicdata`
3. Navigate to dataset: `curatedmetagenomicsdata`
4. Start querying the `stg_*` tables

## Available Tables

The data is organized in three layers:

### Staging Tables (stg_*) - **Recommended for Most Users**

These are optimized, materialized tables with proper data types and clustering. Use these for production queries.

| Table Name | Description | Rows | Size |
|------------|-------------|------|------|
| `stg_marker_abundance` | Taxonomic marker abundance profiles | 1.89B | 135 GB |
| `stg_marker_presence` | Taxonomic marker presence/absence | 1.82B | 129 GB |
| `stg_marker_rel_ab_w_read_stats` | Relative abundance with read statistics | 44.4M | 7.8 GB |
| `stg_metaphlan_unknown_list` | Unknown taxa profiles | TBD | TBD |
| `stg_metaphlan_viruses_list` | Viral taxa with detailed metrics | 1.59M | 0.33 GB |

**Key Features:**
- ✓ Proper data types (FLOAT64, INT64)
- ✓ Clustered by `sample_id` for fast queries
- ✓ Best query performance

### Source Views (src_*) - For Development

Lightweight views that add sample_id extraction. No storage cost but slower queries.

### External Tables (ext_*) - For Direct GCS Access

Point directly to raw gzipped TSV files in Google Cloud Storage. Useful for validating raw data.

## Setting Up Access

### Option 1: Web Console (Easiest)

1. **Access the BigQuery Console:**
   - Go to https://console.cloud.google.com/bigquery
   - You may need to request access to the `curatedmetagenomicdata` project

2. **Navigate to the dataset:**
   - In the left sidebar, find project `curatedmetagenomicdata`
   - Expand to see dataset `curatedmetagenomicsdata`
   - Click on any table to view its schema

3. **Run a query:**
   - Click "COMPOSE NEW QUERY"
   - Write your SQL query
   - Click "RUN"

### Option 2: Command Line (bq tool)

Install the Google Cloud SDK and authenticate:

```bash
# Install gcloud SDK (if not already installed)
# See: https://cloud.google.com/sdk/docs/install

# Authenticate
gcloud auth login

# Set the project
gcloud config set project curatedmetagenomicdata

# Run a query
bq query --use_legacy_sql=false \
  'SELECT sample_id, COUNT(*) as marker_count
   FROM `curatedmetagenomicdata.curatedmetagenomicsdata.stg_marker_abundance`
   GROUP BY sample_id
   LIMIT 10'
```

### Option 3: Python API

```bash
pip install google-cloud-bigquery pandas
```

```python
from google.cloud import bigquery
import pandas as pd

# Initialize client
client = bigquery.Client(project='curatedmetagenomicdata')

# Run a query
query = """
SELECT
    sample_id,
    marker_id,
    abundance
FROM `curatedmetagenomicdata.curatedmetagenomicsdata.stg_marker_abundance`
WHERE sample_id = 'YOUR_SAMPLE_ID'
LIMIT 100
"""

df = client.query(query).to_dataframe()
print(df.head())
```

### Option 4: R with bigrquery

```R
# Install package
install.packages("bigrquery")

library(bigrquery)

# Set up authentication
bq_auth()

# Run query
project <- "curatedmetagenomicdata"
sql <- "
SELECT
    sample_id,
    marker_id,
    abundance
FROM `curatedmetagenomicdata.curatedmetagenomicsdata.stg_marker_abundance`
LIMIT 100
"

df <- bq_project_query(project, sql) %>%
  bq_table_download()

head(df)
```

## Query Examples

### Example 1: Get Data for a Specific Sample

```sql
SELECT *
FROM `curatedmetagenomicdata.curatedmetagenomicsdata.stg_marker_abundance`
WHERE sample_id = '00003b3459eb4248543210b603ecb1a9'
LIMIT 100;
```

**Why this is fast:** The table is clustered by `sample_id`, so this query is very efficient.

### Example 2: Find Top Abundant Markers Across All Samples

```sql
SELECT
    marker_id,
    COUNT(DISTINCT sample_id) as sample_count,
    AVG(abundance) as avg_abundance,
    MAX(abundance) as max_abundance,
    MIN(abundance) as min_abundance
FROM `curatedmetagenomicdata.curatedmetagenomicsdata.stg_marker_abundance`
GROUP BY marker_id
ORDER BY avg_abundance DESC
LIMIT 20;
```

### Example 3: Get Taxonomic Profile for Multiple Samples

```sql
SELECT
    sample_id,
    clade_name,
    relative_abundance,
    coverage,
    estimated_reads
FROM `curatedmetagenomicdata.curatedmetagenomicsdata.stg_marker_rel_ab_w_read_stats`
WHERE
    sample_id IN ('sample1', 'sample2', 'sample3')
    AND clade_name LIKE 'k__%'  -- Kingdom level only
ORDER BY sample_id, relative_abundance DESC;
```

### Example 4: Find Samples with Specific Taxa

```sql
SELECT
    sample_id,
    clade_name,
    relative_abundance
FROM `curatedmetagenomicdata.curatedmetagenomicsdata.stg_marker_rel_ab_w_read_stats`
WHERE
    clade_name LIKE '%Bacteroides%'
    AND relative_abundance > 10.0  -- At least 10% abundance
ORDER BY relative_abundance DESC
LIMIT 100;
```

### Example 5: Viral Detection Summary

```sql
SELECT
    sample_id,
    COUNT(*) as viral_count,
    SUM(mapping_reads_count) as total_viral_reads,
    AVG(breadth_of_coverage) as avg_coverage
FROM `curatedmetagenomicdata.curatedmetagenomicsdata.stg_metaphlan_viruses_list`
GROUP BY sample_id
HAVING viral_count > 5  -- Samples with more than 5 viruses
ORDER BY total_viral_reads DESC
LIMIT 50;
```

### Example 6: Compare Marker Presence Across Samples

```sql
WITH sample_markers AS (
  SELECT
    sample_id,
    marker_id,
    presence
  FROM `curatedmetagenomicdata.curatedmetagenomicsdata.stg_marker_presence`
  WHERE sample_id IN ('sample1', 'sample2', 'sample3')
)
SELECT
    marker_id,
    COUNTIF(presence = 1) as present_in_samples,
    STRING_AGG(CASE WHEN presence = 1 THEN sample_id END) as samples_with_marker
FROM sample_markers
GROUP BY marker_id
HAVING present_in_samples > 1  -- Markers present in multiple samples
ORDER BY present_in_samples DESC;
```

### Example 7: Export Data to Google Cloud Storage

```sql
EXPORT DATA OPTIONS(
  uri='gs://your-bucket/export/marker_abundance_*.csv',
  format='CSV',
  overwrite=true,
  header=true
) AS
SELECT *
FROM `curatedmetagenomicdata.curatedmetagenomicsdata.stg_marker_abundance`
WHERE sample_id IN ('sample1', 'sample2');
```

## Best Practices

### 1. Use Staging Tables (stg_*)

Always query the `stg_*` tables instead of `ext_*` or `src_*` for:
- Better performance (data is materialized)
- Lower costs (no repeated GCS scans)
- Proper data types (FLOAT64 instead of STRING)

### 2. Filter by sample_id When Possible

The tables are clustered by `sample_id`, so filtering by sample ID is extremely efficient:

```sql
-- FAST ✓
WHERE sample_id = 'your_sample'
WHERE sample_id IN ('sample1', 'sample2', 'sample3')

-- SLOWER ✗ (full table scan)
WHERE marker_id = 'marker123'
```

### 3. Use LIMIT During Development

Always use `LIMIT` when developing queries to avoid scanning large amounts of data:

```sql
SELECT *
FROM `curatedmetagenomicdata.curatedmetagenomicsdata.stg_marker_abundance`
LIMIT 100;  -- Always add LIMIT during development
```

### 4. Check Query Costs Before Running

In the BigQuery Console, look at the "query validator" which shows estimated bytes processed before you run the query.

### 5. Use Approximate Aggregation for Large Datasets

For exploratory analysis on huge tables:

```sql
-- Exact count (expensive)
SELECT COUNT(*) FROM table;

-- Approximate count (fast, cheap)
SELECT APPROX_COUNT_DISTINCT(sample_id) FROM table;
```

### 6. Sample Data for Development

Use table sampling to work with a subset during development:

```sql
SELECT *
FROM `curatedmetagenomicdata.curatedmetagenomicsdata.stg_marker_abundance` TABLESAMPLE SYSTEM (1 PERCENT)
LIMIT 1000;
```

## Schema Reference

### Common Fields Across All Tables

- `sample_id` (STRING): Unique sample identifier extracted from GCS file path
  - Example: `00003b3459eb4248543210b603ecb1a9`
  - All tables are **clustered by this field** for fast lookups

### stg_marker_abundance

| Field | Type | Description |
|-------|------|-------------|
| sample_id | STRING | Sample identifier |
| marker_id | STRING | Taxonomic marker identifier |
| abundance | FLOAT64 | Marker abundance value |

### stg_marker_presence

| Field | Type | Description |
|-------|------|-------------|
| sample_id | STRING | Sample identifier |
| marker_id | STRING | Taxonomic marker identifier |
| presence | INT64 | Presence indicator (1 = present, 0 = absent) |

### stg_marker_rel_ab_w_read_stats

| Field | Type | Description |
|-------|------|-------------|
| sample_id | STRING | Sample identifier |
| clade_name | STRING | Taxonomic clade name (e.g., "k__Bacteria\|p__Firmicutes") |
| clade_taxid | STRING | NCBI taxonomy ID |
| relative_abundance | FLOAT64 | Relative abundance percentage |
| coverage | FLOAT64 | Coverage value (NULL for unclassified) |
| estimated_reads | INT64 | Estimated number of reads |

### stg_metaphlan_viruses_list

| Field | Type | Description |
|-------|------|-------------|
| sample_id | STRING | Sample identifier |
| mv_group_cluster | STRING | Virus group/cluster identifier |
| genome_name | STRING | Viral genome name |
| length | INT64 | Genome length |
| breadth_of_coverage | FLOAT64 | Breadth of coverage (0-1) |
| mapping_reads_count | INT64 | Number of mapped reads |
| rpkm | FLOAT64 | Reads per kilobase per million |
| depth_of_coverage_mean | FLOAT64 | Mean depth of coverage |
| depth_of_coverage_median | FLOAT64 | Median depth of coverage |
| mv_group_type | STRING | Virus type (known/unknown) |
| assigned_taxonomy | STRING | Taxonomic assignment |
| first_genome_in_cluster | STRING | Reference genome |
| other_genomes_in_cluster | STRING | Alternative genomes |

## Getting Help

- **Documentation Issues**: [GitHub Issues](https://github.com/seandavi/curatedMetagenomicDataETL/issues)
- **BigQuery Documentation**: https://cloud.google.com/bigquery/docs
- **MetaPhlAn Documentation**: https://github.com/biobakery/MetaPhlAn

## Cost Management

BigQuery charges for:
1. **Storage**: ~$0.02 per GB per month (very low for this data)
2. **Queries**: $6.25 per TB scanned

**Tips to reduce costs:**
- Use `stg_*` tables (not `src_*` views which scan GCS)
- Filter by `sample_id` early in your query
- Use `LIMIT` during development
- Export frequently-used subsets to your own tables
- Use the query validator to see costs before running

## Example: Complete Analysis Workflow

Here's a complete workflow to analyze taxonomic composition across samples:

```python
from google.cloud import bigquery
import pandas as pd
import matplotlib.pyplot as plt

# Initialize client
client = bigquery.Client(project='curatedmetagenomicdata')

# Step 1: Get list of samples
samples_query = """
SELECT DISTINCT sample_id
FROM `curatedmetagenomicdata.curatedmetagenomicsdata.stg_marker_rel_ab_w_read_stats`
LIMIT 10
"""
samples = [row.sample_id for row in client.query(samples_query).result()]

# Step 2: Get kingdom-level composition for these samples
composition_query = f"""
SELECT
    sample_id,
    clade_name,
    relative_abundance
FROM `curatedmetagenomicdata.curatedmetagenomicsdata.stg_marker_rel_ab_w_read_stats`
WHERE
    sample_id IN UNNEST({samples})
    AND clade_name LIKE 'k__%'
    AND clade_name NOT LIKE 'k__%|%'  -- Kingdom level only
ORDER BY sample_id, relative_abundance DESC
"""

df = client.query(composition_query).to_dataframe()

# Step 3: Visualize
pivot_df = df.pivot(index='sample_id', columns='clade_name', values='relative_abundance')
pivot_df.plot(kind='bar', stacked=True, figsize=(12, 6))
plt.title('Kingdom-Level Composition Across Samples')
plt.ylabel('Relative Abundance (%)')
plt.xlabel('Sample ID')
plt.legend(title='Kingdom', bbox_to_anchor=(1.05, 1))
plt.tight_layout()
plt.savefig('taxonomy_composition.png', dpi=300, bbox_inches='tight')
```

---

**Last Updated**: 2025-11-04
**Pipeline Version**: 1.0
**Data Version**: cMDv4
