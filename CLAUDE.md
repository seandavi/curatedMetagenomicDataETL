# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This repository contains the ETL (Extract, Transform, Load) pipeline for the curatedMetagenomicData project. The ETL process transforms per-sample CSV/TSV files from the curatedMetagenomicsNextflow pipeline into structured databases and parquet files for efficient querying and analysis.

**Key Challenge**: The pipeline processes 60,000+ metagenomic samples, requiring efficient parallel processing and optimized data storage.

**Data Flow**:
1. Source: Per-sample files in GCS bucket `gs://cmgd-data/results/cMDv4/{sample_id}/`
2. Processing: Combine multiple samples into unified tables by data type (taxonomic profiles, functional profiles, metadata)
3. Destination: BigQuery for initial loading/querying → Parquet files for distribution on Cloudflare R2

## Technology Stack

- **Python 3.11+**: Core language
- **uv**: Package manager (replaces pip/poetry)
- **DuckDB**: Local data processing and analytics
- **BigQuery**: Cloud data warehouse for initial loading and querying
- **Parquet**: Columnar storage format for distribution

## Development Commands

### Environment Setup
```bash
# Install dependencies (uv should already be installed)
uv sync

# Or use justfile
just install-deps
```

### Running the Pipeline
```bash
# See all available commands
just --list

# Run the complete pipeline
just run-etl-pipeline

# Run individual steps
just create-external-tables
just load-reference-tables
just create-src-stg-tables
just gather-metadata

# Validation and testing
just test-tables
just show-tables
```

### Manual Script Execution
```bash
# Run Python scripts directly if needed
uv run script_name.py
```

## Data Architecture

### Input Data Structure (Per Sample)

Each sample in `gs://cmgd-data/results/cMDv4/{sample_id}/` contains:

- **Taxonomic Markers**:
  - `metaphlan_markers/marker_abundance.tsv.gz`: Marker abundance values
  - `metaphlan_markers/marker_presence.tsv.gz`: Marker presence/absence
  - `metaphlan_markers/marker_rel_ab_w_read_stats.tsv.gz`: Relative abundance with read stats

- **Taxonomic Lists**:
  - `metaphlan_lists/metaphlan_unknown_list.tsv.gz`: Unknown taxa
  - `metaphlan_lists/metaphlan_viruses_list.tsv.gz`: Viral taxa

- **StrainPhlAn Markers**:
  - `strainphlan_markers/metaphlan.json.bz2`: Strain-level marker data (JSON format)

### ETL Design Considerations

The pipeline follows a three-layer approach inspired by dbt best practices:

1. **External Tables (ext_*)**: Point directly to raw gzipped TSV files in GCS
   - No data movement
   - Schema inference from files
   - Capture `_FILE_NAME` for sample_id extraction

2. **Source Views (src_*)**: Lightweight views that add computed columns
   - Extract `sample_id` from file path using REGEXP_EXTRACT
   - No data storage, just transformation logic
   - Fast to recreate, no storage cost

3. **Staging Tables (stg_*)**: Materialized tables with optimizations
   - Proper data types (FLOAT64, INT64 instead of STRING)
   - Clustered by `sample_id` for query performance
   - Handle NULL values and edge cases
   - Full refresh pattern for simplicity

4. **Reference Tables**: Lookup and metadata tables
   - `src_sample_id_map`: Maps MD5 hash sample_id to SRA accessions and study names
   - `sra_accessions`: Full NCBI SRA metadata for linking

**Design Principles**:
- **Scale**: 60,000+ samples require parallelization and batch processing
- **Memory**: Use streaming/chunked processing to avoid loading all samples into memory
- **Storage**: Leverage columnar formats (Parquet) for efficient compression and query performance
- **Cloud Integration**: GCS for source data, BigQuery for processing, R2 for distribution
- **Flexibility**: Easy to update transformations by recreating views
- **Performance**: Materialized staging tables for production queries
- **Cost Efficiency**: External tables avoid duplicate storage

## Pipeline Execution

The ETL pipeline has clear dependencies. Use the provided `justfile` to manage execution:

### Quick Start
```bash
# Run the entire pipeline from scratch
just run-etl-pipeline

# See all available commands
just --list
```

### Execution Order

**Step 1: Create External Tables** (Required first, ~1-2 min)
```bash
just create-external-tables
```

**Step 2: Load Reference Tables** (Required, 20-30 min total)
```bash
just load-reference-tables
# Runs: load-sample-id-map (~1 min) + load-sra-accessions (~20-30 min)
```

**Step 3: Create Source/Staging Tables** (30-60 min, processes ~400GB)
```bash
just create-src-stg-tables
```

**Step 4: Gather Metadata** (Optional, ~1-2 min)
```bash
just gather-metadata
```

### Pipeline Dependencies
```
create-external-tables
         ↓
load-reference-tables
    ↓            ↓
    (sample_id_map + sra_accessions)
         ↓
create-src-stg-tables
         ↓
gather-metadata
```

**Why this order matters:**
1. External tables must exist before source views can reference them
2. Reference tables enable JOINs for querying by study or SRA accession
3. Source/staging tables depend on external tables existing
4. Metadata gathering should run last to capture all created tables

## Project Context

- **Metadata Source**: [curatedMetagenomicDataCuration](https://github.com/waldronlab/curatedMetagenomicDataCuration) (CSV files in GitHub)
- **Processing Pipeline**: [curatedMetagenomicsNextflow](https://github.com/seandavi/curatedMetagenomicsNextflow)
- **Goal**: Provide curated, uniformly processed metagenomic datasets to the scientific community
