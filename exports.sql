-- marker abundance
EXPORT DATA OPTIONS(
  uri = 'gs://cmgd-exports/cMDv4/marker_abundance/marker_abundance_*.parquet',
  format = 'PARQUET',
  overwrite = TRUE,
  compression = 'ZSTD'
) AS
SELECT
    a.sample_id,
    marker_id,
    abundance,
    study_name,
    sample_name
FROM `curatedmetagenomicsdata.stg_marker_abundance` a
join `curatedmetagenomicsdata.src_sample_id_map` b
on a.sample_id = b.sample_id
order by study_name, sample_name, marker_id;

-- marker presence
EXPORT DATA OPTIONS(
  uri = 'gs://cmgd-exports/cMDv4/marker_presence/marker_presence_*.parquet',
  format = 'PARQUET',
  overwrite = TRUE,
  compression = 'ZSTD'
) AS
SELECT 
    a.sample_id,
    marker_id,
    presence,
    study_name,
    sample_name
FROM `curatedmetagenomicsdata.stg_marker_presence` a
join `curatedmetagenomicsdata.src_sample_id_map` b
on a.sample_id = b.sample_id
order by study_name, sample_name, marker_id;

-- marker relative abundance with read stats
EXPORT DATA OPTIONS(
  uri = 'gs://cmgd-exports/cMDv4/marker_rel_ab_w_read_stats/marker_rel_ab_w_read_stats_*.parquet',
  format = 'PARQUET',
  overwrite = TRUE,
  compression = 'ZSTD'
) AS
SELECT 
    a.sample_id,
    clade_name,
    clade_taxid,
    relative_abundance,
    coverage,
    estimated_reads,
    study_name,
    sample_name
FROM `curatedmetagenomicsdata.stg_marker_rel_ab_w_read_stats` a
join `curatedmetagenomicsdata.src_sample_id_map` b
on a.sample_id = b.sample_id
order by study_name, sample_name, clade_name;

-- viruses list
EXPORT DATA OPTIONS(
  uri = 'gs://cmgd-exports/cMDv4/viruses_list/viruses_list_*.parquet',
  format = 'PARQUET',
  overwrite = TRUE,
  compression = 'ZSTD'
) AS
SELECT 
    a.sample_id,
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
    other_genomes_in_cluster,
    study_name,
    sample_name
FROM `curatedmetagenomicsdata.stg_metaphlan_viruses_list` a
join `curatedmetagenomicsdata.src_sample_id_map` b
on a.sample_id = b.sample_id
order by study_name, sample_name, mv_group_cluster;