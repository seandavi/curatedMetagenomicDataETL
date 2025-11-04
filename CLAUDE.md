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

# Activate virtual environment
source .venv/bin/activate
```

### Running Code
```bash
# The project is in early development - no main.py exists yet
# Python scripts will be run directly as they are developed
python your_script.py
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

- **Scale**: 60,000+ samples require parallelization and batch processing
- **Memory**: Use streaming/chunked processing to avoid loading all samples into memory
- **Storage**: Leverage columnar formats (Parquet) for efficient compression and query performance
- **Cloud Integration**: GCS for source data, BigQuery for processing, R2 for distribution

## Project Context

- **Metadata Source**: [curatedMetagenomicDataCuration](https://github.com/waldronlab/curatedMetagenomicDataCuration) (CSV files in GitHub)
- **Processing Pipeline**: [curatedMetagenomicsNextflow](https://github.com/seandavi/curatedMetagenomicsNextflow)
- **Goal**: Provide curated, uniformly processed metagenomic datasets to the scientific community
