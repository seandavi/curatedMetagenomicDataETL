import duckdb
from upath import UPath
from loguru import logger
import tenacity

def get_file_list_sql(filename: str, study_name: str) -> str:
    return f"""with file_table AS
(SELECT
    file,
    split(file, '/')[6] AS sample_id,
    split(file, '/')[-1] AS filename
from 
    file_list
),
sample_table as (
select 
    sample_id,
    sample_name,
    study_name,
    run_ids
from 
    sample_id_map
),
sample_file_table AS (
SELECT
    s.sample_id,
    s.sample_name,
    s.study_name,
    s.run_ids,
    f.filename,
    f.file
FROM
    sample_table s
JOIN
    file_table f
ON
    s.sample_id = f.sample_id
)
SELECT file from sample_file_table where study_name = '{study_name}' AND filename='{filename}'""";
    return sql

def get_file_list(filename_pattern: str, study_name: str, duckdb_conn: duckdb.DuckDBPyConnection) -> list[str]:
    sql = get_file_list_sql(filename_pattern, study_name)
    fl = duckdb_conn.sql(sql).pl()
    fl = fl['file'].to_list()
    return fl

def main(
    duckdb_conn: duckdb.DuckDBPyConnection, 
    base_directory: UPath = UPath('s3://cmgd-export/'), 
    filename_pattern: str = '',  
    study_name: str = 'LiJ_2014'
) -> None:
    
    local_logger = logger.bind(filename_pattern=filename_pattern, study_name=study_name)
    
    dirname = filename_pattern.replace('.tsv.gz', '')
    local_logger.info(f"Processing...")
    
    output_directory = UPath(base_directory) / dirname / f"study_name={study_name}"
   
    fl = get_file_list(filename_pattern, study_name, duckdb_conn=duckdb_conn)
    
    if len(fl) == 0:
        local_logger.warning(f"No files found for {filename_pattern} in study {study_name}")
        return
     
    # remove old directory if it exists
    for d in output_directory.glob('**'):
        if d.is_dir():
            d.rmdir()
        elif d.is_file():
            d.unlink()
    
    (UPath(base_directory) / dirname).mkdir(parents=True, exist_ok=True)

    filelist_sql = f"""select file from file_list where file like '%{filename_pattern}'"""
    
    secret_sql = f"""
    CREATE or replace SECRET minio (
        TYPE s3,
        KEY_ID 'admin',
        SECRET 'this_password_is_good',
        ENDPOINT 'minio.cancerdatasci.org',
        URL_STYLE 'path',
        REGION 'us-east-1',
        USE_SSL True
    );
    """
    duckdb_conn.sql(secret_sql)
    
    # partitioned by study_name--nice! 
    sql = f"""
    copy (
        SELECT 
            *
        FROM read_csv_auto({fl}, comment='#', delim='\t', header=false, null_padding=true, filename=true) a 
        join read_csv_auto('sample_id_map.csv') on split_part(a.filename, '/', 6) = sample_id
        where study_name = '{study_name}'
    ) to 
        '{output_directory}'
    (format parquet, compression zstd, file_size_bytes '512MB');
    """
    #print(sql)
    duckdb_conn.sql(sql)
    entity_directory = UPath(base_directory) / dirname 
    duckdb_conn.sql(f"create or replace view src_{dirname} as (SELECT * FROM read_parquet('{entity_directory}/**/*.parquet'))")
    local_logger.info(f"Processed....")
        
        
        
def create_sample_id_map_parquet(base_directory: str = 's3://cmgd-export/', duckdb_database: str = ':memory:'):
    upath = UPath(base_directory)
    sample_id_map = upath / 'sample_id_map.csv'
    sample_id_map.unlink(missing_ok=True)
    with duckdb.connect(database=duckdb_database) as con:
        con.sql(f"""
        copy (
            select 
                *
            from read_csv_auto('sample_id_map.csv') order by sample_id
        ) to 
        '{base_directory}sample_id_map.parquet' (format parquet, compression zstd)""")
        
        sql = f"""create or replace view sample_id_map as (SELECT * FROM read_parquet('{base_directory}sample_id_map.parquet'))"""
        con.sql(sql)


def create_file_list(cmgd_base_directory: UPath = UPath('s3://gs-cmgd-mirror/'), duckdb_database: str = ':memory:'):
    
    with duckdb.connect(database=duckdb_database) as con:
        sql = f"""
        copy (
            select 
                *
            from glob('{cmgd_base_directory}**')
        ) to 
        '{cmgd_base_directory}file_list.parquet' (format parquet, compression zstd)"""
        print(sql)
        con.sql(sql)
        
        sql = f"""create or replace view file_list as (SELECT * FROM read_parquet('{cmgd_base_directory}file_list.parquet'))"""
        con.sql(sql)


if __name__ == "__main__":
    
    # TODO: rclone sync prior to running
    
    # create_file_list(duckdb_database='cmgd.duckdb')
    
    cmgd_base_directory = UPath('s3://gs-cmgd-mirror/')
    base_directory = UPath('s3://cmgd-export/')
    
    create_sample_id_map_parquet(duckdb_database='cmgd.duckdb')
    
    
    filename_patters = [
        'metaphlan_viruses_list.tsv.gz',
        'metaphlan_unknown_list.tsv.gz',
        'marker_abundance.tsv.gz',
        'marker_presence.tsv.gz',
        'marker_rel_ab_w_read_stats.tsv.gz'
    ]    
            
    with duckdb.connect(database='cmgd.duckdb') as duckdb_conn:
        sql = 'select distinct(study_name) from sample_id_map;'
        study_names = duckdb_conn.sql(sql).fetchall()
        study_names = [s[0] for s in study_names]
        print(study_names)
        for study_name in study_names:
            for filename_pattern in filename_patters:
                logger.info(f"Processing {filename_pattern} for study {study_name}")
                main(
                    duckdb_conn=duckdb_conn,
                    base_directory=base_directory, 
                    filename_pattern=filename_pattern, 
                    study_name=study_name
                )

