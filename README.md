# curatedMetagenomicDataETL

This repository contains the code and data for the ETL (Extract, Transform, Load) process of the curatedMetagenomicData package. 

This ETL process starts with raw output data from the nextflow pipeline 
(curatedMetagenomicsDataNextflow) and transforms it into a set of hive-partitioned parquet files stored in an S3 bucket.

## Usage of resulting data

With any duckdb connection:

```sql
attach 'https://minio.cancerdatasci.org/cmgd-export/cmgd.duckdb' as cmgd;
use cmgd;
```

```
┌────────────────────────────────┐
│              name              │
│            varchar             │
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


```sql
select * from src_marker_presence where study_name='AsnicarF_2017';
```

```
┌──────────────────────┬─────────┬────────────────────────────────────────────────────────────┬──────────────────────────────────┬────────────┬───────────────┬───────────────┐
│       column0        │ column1 │                          filename                          │            sample_id             │  run_ids   │  sample_name  │  study_name   │
│       varchar        │  int64  │                          varchar                           │             varchar              │  varchar   │    varchar    │    varchar    │
├──────────────────────┼─────────┼────────────────────────────────────────────────────────────┼──────────────────────────────────┼────────────┼───────────────┼───────────────┤
│ UniRef90_Q04MU9|4_…  │       1 │ s3://gs-cmgd-mirror/results/cMDv4/8c7d6943ef53d11a4ec814…  │ 8c7d6943ef53d11a4ec814f6e6e69718 │ SRR4052021 │ MV_FEI1_t1Q14 │ AsnicarF_2017 │
│ UniRef90_A0A3R9H3X…  │       1 │ s3://gs-cmgd-mirror/results/cMDv4/0c8723e88d2e33c4e07845…  │ 0c8723e88d2e33c4e07845a8b4ca1c3c │ SRR4052022 │ MV_FEI2_t1Q14 │ AsnicarF_2017 │
│ UniRef90_A0A3R9H3X…  │       1 │ s3://gs-cmgd-mirror/results/cMDv4/4b3dcf31f4fe4ff2c685eb…  │ 4b3dcf31f4fe4ff2c685ebf0a86d79c3 │ SRR4052033 │ MV_FEI3_t1Q14 │ AsnicarF_2017 │
│ UniRef90_W1VA62|1_…  │       1 │ s3://gs-cmgd-mirror/results/cMDv4/9316170a7040cd75610fc0…  │ 9316170a7040cd75610fc094d04d8483 │ SRR4052038 │ MV_FEI4_t1Q14 │ AsnicarF_2017 │
│ UniRef90_F9PC74|1_…  │       1 │ s3://gs-cmgd-mirror/results/cMDv4/7f168837d7b0824c498d64…  │ 7f168837d7b0824c498d6498f94ee538 │ SRR4052039 │ MV_FEI4_t2Q15 │ AsnicarF_2017 │
│ UniRef90_A0A3R9H3X…  │       1 │ s3://gs-cmgd-mirror/results/cMDv4/1b4629b05cf10a5d977143…  │ 1b4629b05cf10a5d977143f84bacbf5a │ SRR4052040 │ MV_FEI5_t1Q14 │ AsnicarF_2017 │
│ UniRef90_F9PC74|1_…  │       1 │ s3://gs-cmgd-mirror/results/cMDv4/f55db659bf4e1e66a0213b…  │ f55db659bf4e1e66a0213b8663339033 │ SRR4052041 │ MV_FEI5_t2Q14 │ AsnicarF_2017 │
│ UniRef90_A8AW17|1_…  │       1 │ s3://gs-cmgd-mirror/results/cMDv4/8b446edf9f8416d6cafb6b…  │ 8b446edf9f8416d6cafb6bf1f8582b77 │ SRR4052042 │ MV_FEI5_t3Q15 │ AsnicarF_2017 │
│ UniRef90_I1ZJN9|1_…  │       1 │ s3://gs-cmgd-mirror/results/cMDv4/a2ab9d43cafcaf1eafdd95…  │ a2ab9d43cafcaf1eafdd95d958ba6d68 │ SRR4052043 │ MV_FEM1_t1Q14 │ AsnicarF_2017 │
│ UniRef90_A8AY59|1_…  │       1 │ s3://gs-cmgd-mirror/results/cMDv4/bcc911464b952176c57d39…  │ bcc911464b952176c57d39d67788796e │ SRR4052044 │ MV_FEM2_t1Q14 │ AsnicarF_2017 │
│ UniRef90_A8AZC3|1_…  │       1 │ s3://gs-cmgd-mirror/results/cMDv4/37bb2dc668b43d1dc48853…  │ 37bb2dc668b43d1dc488538c390101af │ SRR4052023 │ MV_FEM3_t1Q14 │ AsnicarF_2017 │
│ UniRef90_E8JXI6|2_…  │       1 │ s3://gs-cmgd-mirror/results/cMDv4/fdb38f9d001dd935b72eef…  │ fdb38f9d001dd935b72eef6db3ff79e4 │ SRR4052024 │ MV_FEM4_t1Q14 │ AsnicarF_2017 │
│ UniRef90_A0A1V0H2E…  │       1 │ s3://gs-cmgd-mirror/results/cMDv4/f0df1fc364a6c8c02da4a9…  │ f0df1fc364a6c8c02da4a94125940a63 │ SRR4052025 │ MV_FEM4_t2Q15 │ AsnicarF_2017 │
│ UniRef90_E8JWE5|1_…  │       1 │ s3://gs-cmgd-mirror/results/cMDv4/0b1fffdab081307046dccb…  │ 0b1fffdab081307046dccb55995f1db7 │ SRR4052026 │ MV_FEM5_t1Q14 │ AsnicarF_2017 │
│ UniRef90_A0A3R9LFF…  │       1 │ s3://gs-cmgd-mirror/results/cMDv4/51214bea337abd05b1cd73…  │ 51214bea337abd05b1cd73b26f1182ee │ SRR4052027 │ MV_FEM5_t2Q14 │ AsnicarF_2017 │
│ UniRef90_A0A139N93…  │       1 │ s3://gs-cmgd-mirror/results/cMDv4/60095cf2f7cf34a424c577…  │ 60095cf2f7cf34a424c577113cb36562 │ SRR4052028 │ MV_FEM5_t3Q15 │ AsnicarF_2017 │
│ UniRef90_A0A2I1TUV…  │       1 │ s3://gs-cmgd-mirror/results/cMDv4/56a9494139e07fd62d6764…  │ 56a9494139e07fd62d67641a19cd0419 │ SRR4052029 │ MV_MIM1_t1M14 │ AsnicarF_2017 │
│ UniRef90_J1SE68|5_…  │       1 │ s3://gs-cmgd-mirror/results/cMDv4/5304adab0f5e439a892d9c…  │ 5304adab0f5e439a892d9cce50ab8528 │ SRR4052030 │ MV_MIM2_t1M14 │ AsnicarF_2017 │
│ UniRef90_A0A3R9PB5…  │       1 │ s3://gs-cmgd-mirror/results/cMDv4/1d2fe98ec9d40a26cb8efd…  │ 1d2fe98ec9d40a26cb8efd006148f29f │ SRR4052031 │ MV_MIM3_t1M14 │ AsnicarF_2017 │
│ UniRef90_A0A0E1V9L…  │       1 │ s3://gs-cmgd-mirror/results/cMDv4/657aec2c86aae9a52442f0…  │ 657aec2c86aae9a52442f03cd6c86948 │ SRR4052032 │ MV_MIM4_t1M14 │ AsnicarF_2017 │
│          ·           │       · │                             ·                              │                ·                 │     ·      │       ·       │       ·       │
│          ·           │       · │                             ·                              │                ·                 │     ·      │       ·       │       ·       │
│          ·           │       · │                             ·                              │                ·                 │     ·      │       ·       │       ·       │
│ UniClust90_OMODNEG…  │       1 │ s3://gs-cmgd-mirror/results/cMDv4/60095cf2f7cf34a424c577…  │ 60095cf2f7cf34a424c577113cb36562 │ SRR4052028 │ MV_FEM5_t3Q15 │ AsnicarF_2017 │
│ UniClust90_NBKJELN…  │       1 │ s3://gs-cmgd-mirror/results/cMDv4/60095cf2f7cf34a424c577…  │ 60095cf2f7cf34a424c577113cb36562 │ SRR4052028 │ MV_FEM5_t3Q15 │ AsnicarF_2017 │
│ UniClust90_CGGELEK…  │       1 │ s3://gs-cmgd-mirror/results/cMDv4/60095cf2f7cf34a424c577…  │ 60095cf2f7cf34a424c577113cb36562 │ SRR4052028 │ MV_FEM5_t3Q15 │ AsnicarF_2017 │
│ UniClust90_JACPNGI…  │       1 │ s3://gs-cmgd-mirror/results/cMDv4/60095cf2f7cf34a424c577…  │ 60095cf2f7cf34a424c577113cb36562 │ SRR4052028 │ MV_FEM5_t3Q15 │ AsnicarF_2017 │
│ UniClust90_IMKJJHE…  │       1 │ s3://gs-cmgd-mirror/results/cMDv4/60095cf2f7cf34a424c577…  │ 60095cf2f7cf34a424c577113cb36562 │ SRR4052028 │ MV_FEM5_t3Q15 │ AsnicarF_2017 │
│ UniClust90_OMODNEG…  │       1 │ s3://gs-cmgd-mirror/results/cMDv4/60095cf2f7cf34a424c577…  │ 60095cf2f7cf34a424c577113cb36562 │ SRR4052028 │ MV_FEM5_t3Q15 │ AsnicarF_2017 │
│ UniClust90_CJMAPLI…  │       1 │ s3://gs-cmgd-mirror/results/cMDv4/60095cf2f7cf34a424c577…  │ 60095cf2f7cf34a424c577113cb36562 │ SRR4052028 │ MV_FEM5_t3Q15 │ AsnicarF_2017 │
│ UniClust90_CGGELEK…  │       1 │ s3://gs-cmgd-mirror/results/cMDv4/60095cf2f7cf34a424c577…  │ 60095cf2f7cf34a424c577113cb36562 │ SRR4052028 │ MV_FEM5_t3Q15 │ AsnicarF_2017 │
│ UniClust90_CJMAPLI…  │       1 │ s3://gs-cmgd-mirror/results/cMDv4/60095cf2f7cf34a424c577…  │ 60095cf2f7cf34a424c577113cb36562 │ SRR4052028 │ MV_FEM5_t3Q15 │ AsnicarF_2017 │
│ UniClust90_CJMAPLI…  │       1 │ s3://gs-cmgd-mirror/results/cMDv4/60095cf2f7cf34a424c577…  │ 60095cf2f7cf34a424c577113cb36562 │ SRR4052028 │ MV_FEM5_t3Q15 │ AsnicarF_2017 │
│ UniClust90_CJMAPLI…  │       1 │ s3://gs-cmgd-mirror/results/cMDv4/60095cf2f7cf34a424c577…  │ 60095cf2f7cf34a424c577113cb36562 │ SRR4052028 │ MV_FEM5_t3Q15 │ AsnicarF_2017 │
│ UniClust90_OMODNEG…  │       1 │ s3://gs-cmgd-mirror/results/cMDv4/60095cf2f7cf34a424c577…  │ 60095cf2f7cf34a424c577113cb36562 │ SRR4052028 │ MV_FEM5_t3Q15 │ AsnicarF_2017 │
│ UniClust90_CJMAPLI…  │       1 │ s3://gs-cmgd-mirror/results/cMDv4/60095cf2f7cf34a424c577…  │ 60095cf2f7cf34a424c577113cb36562 │ SRR4052028 │ MV_FEM5_t3Q15 │ AsnicarF_2017 │
│ UniClust90_CJMAPLI…  │       1 │ s3://gs-cmgd-mirror/results/cMDv4/60095cf2f7cf34a424c577…  │ 60095cf2f7cf34a424c577113cb36562 │ SRR4052028 │ MV_FEM5_t3Q15 │ AsnicarF_2017 │
│ UniClust90_CGGELEK…  │       1 │ s3://gs-cmgd-mirror/results/cMDv4/60095cf2f7cf34a424c577…  │ 60095cf2f7cf34a424c577113cb36562 │ SRR4052028 │ MV_FEM5_t3Q15 │ AsnicarF_2017 │
│ UniClust90_IMKJJHE…  │       1 │ s3://gs-cmgd-mirror/results/cMDv4/60095cf2f7cf34a424c577…  │ 60095cf2f7cf34a424c577113cb36562 │ SRR4052028 │ MV_FEM5_t3Q15 │ AsnicarF_2017 │
│ UniClust90_CGGELEK…  │       1 │ s3://gs-cmgd-mirror/results/cMDv4/60095cf2f7cf34a424c577…  │ 60095cf2f7cf34a424c577113cb36562 │ SRR4052028 │ MV_FEM5_t3Q15 │ AsnicarF_2017 │
│ UniClust90_NBKJELN…  │       1 │ s3://gs-cmgd-mirror/results/cMDv4/60095cf2f7cf34a424c577…  │ 60095cf2f7cf34a424c577113cb36562 │ SRR4052028 │ MV_FEM5_t3Q15 │ AsnicarF_2017 │
│ UniClust90_CGGELEK…  │       1 │ s3://gs-cmgd-mirror/results/cMDv4/60095cf2f7cf34a424c577…  │ 60095cf2f7cf34a424c577113cb36562 │ SRR4052028 │ MV_FEM5_t3Q15 │ AsnicarF_2017 │
│ UniClust90_JACPNGI…  │       1 │ s3://gs-cmgd-mirror/results/cMDv4/60095cf2f7cf34a424c577…  │ 60095cf2f7cf34a424c577113cb36562 │ SRR4052028 │ MV_FEM5_t3Q15 │ AsnicarF_2017 │
├──────────────────────┴─────────┴────────────────────────────────────────────────────────────┴──────────────────────────────────┴────────────┴───────────────┴───────────────┤
│ 328468 rows (40 shown)                                                                                                                                            7 columns │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

