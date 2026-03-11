# curatedMetagenomicDataETL

This repository contains the ETL (Extract, Transform, Load) pipeline for the curatedMetagenomicData project.

The pipeline starts with raw output files from the [curatedMetagenomicsDataNextflow](https://github.com/seandavi/curatedMetagenomicsDataNextflow) pipeline and transforms them into hive-partitioned Parquet files stored in an S3-compatible object store. A DuckDB database file is published alongside the Parquet data with pre-registered views, making the data immediately queryable without any local setup.

## Prerequisites

- Python 3.11+
- Access to an S3-compatible object store (e.g. MinIO) with write permissions for the export bucket
- `rclone` configured to sync the source data from Google Cloud Storage (see Step 1 below)

## Installation

Clone the repository and install the package:

```bash
git clone https://github.com/seandavi/curatedMetagenomicDataETL.git
cd curatedMetagenomicDataETL
uv sync
```

## Configuration

The pipeline reads credentials from environment variables, which can be placed in a `.env` file at the root of the repository. DuckDB picks these up automatically at runtime.

Create a `.env` file:

```bash
# S3-compatible object store credentials (for the export target)
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_ENDPOINT_URL=https://minio.example.org   # include protocol
AWS_REGION=us-east-1
```

All four variables are required for S3 access. If any are missing, the pipeline will log a warning and skip S3 secret configuration (useful for local-only runs with an in-memory DuckDB).

## Running the ETL Pipeline

### Step 1 — Sync source data from GCS

The raw pipeline output lives in Google Cloud Storage. Use `rclone` to mirror it locally before running the ETL:

```bash
rclone sync gcs:gs-cmgd-mirror /data/path/to/gs-cmgd-mirror/
```

Update the `cmgd_base_directory` path in `etl.py` to match your local mirror location.

### Step 2 — Build the file list

Glob all files in the source directory and write a `file_list.parquet` index. This only needs to be re-run when the source data changes.

```python
from upath import UPath
from cmgd_etl.etl import create_file_list

create_file_list(
    cmgd_base_directory=UPath('/data/path/to/gs-cmgd-mirror/'),
    duckdb_database='cmgd.duckdb',
)
```

### Step 3 — Export the sample ID map

Converts `sample_id_map.csv` (checked in to this repository) to Parquet in the export bucket and registers a DuckDB view:

```python
from upath import UPath
from cmgd_etl.etl import create_sample_id_map_parquet

create_sample_id_map_parquet(
    base_directory=UPath('s3://cmgd-export/'),
    duckdb_database='cmgd.duckdb',
)
```

### Step 4 — Run the full ETL

Iterates over every combination of study and data-file type, reads the gzipped TSV files, joins with the sample ID map, and writes hive-partitioned Parquet to the export bucket. A DuckDB view is registered for each dataset.

```bash
uv run python -m cmgd_etl.etl
```

Or run the script directly:

```bash
uv run python src/cmgd_etl/etl.py
```

The pipeline processes the following file types for every study found in `sample_id_map`:

| File pattern | DuckDB view |
|---|---|
| `marker_abundance.tsv.gz` | `src_marker_abundance` |
| `marker_presence.tsv.gz` | `src_marker_presence` |
| `marker_rel_ab_w_read_stats.tsv.gz` | `src_marker_rel_ab_w_read_stats` |
| `metaphlan_unknown_list.tsv.gz` | `src_metaphlan_unknown_list` |
| `metaphlan_viruses_list.tsv.gz` | `src_metaphlan_viruses_list` |

Output Parquet files are written under `s3://cmgd-export/<dataset>/study_name=<study>/` and are compressed with Zstandard. Files are capped at 512 MB each.

## Output data structure

The DuckDB file at `s3://cmgd-export/cmgd.duckdb` exposes the following views:

| View | Description |
|---|---|
| `file_list` | Index of all source files in the GCS mirror |
| `sample_id_map` | Maps sample IDs to SRA run IDs, sample names, and study names |
| `src_marker_abundance` | UniRef90/UniClust90 marker gene abundance per sample |
| `src_marker_presence` | UniRef90/UniClust90 marker gene presence/absence per sample |
| `src_marker_rel_ab_w_read_stats` | Marker relative abundance with read-level statistics |
| `src_metaphlan_unknown_list` | MetaPhlAn unknown clade profiles |
| `src_metaphlan_viruses_list` | MetaPhlAn viral profiles |

All data views share the columns `sample_id`, `run_ids`, `sample_name`, and `study_name`, enabling straightforward joins and filtering by study.

## Usage of the resulting data

Connect to the published DuckDB database from any DuckDB client — no credentials required for read access:

```sql
ATTACH 'https://minio.cancerdatasci.org/cmgd-export/cmgd.duckdb' AS cmgd;
USE cmgd;
SHOW ALL TABLES;
```

```
┌────────────────────────────────┐
│              name              │
├────────────────────────────────┤
│ file_list                      │
│ sample_id_map                  │
│ src_marker_abundance           │
│ src_marker_presence            │
│ src_marker_rel_ab_w_read_stats │
│ src_metaphlan_unknown_list     │
│ src_metaphlan_viruses_list     │
└────────────────────────────────┘
```

Query a specific study:

```sql
SELECT * FROM src_marker_presence WHERE study_name = 'AsnicarF_2017' LIMIT 5;
```
