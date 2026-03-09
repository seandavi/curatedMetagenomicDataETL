import os

import duckdb
from upath import UPath
from loguru import logger
import tenacity
from dotenv import load_dotenv


def create_duckdb_connection(
    duckdb_database: str = ':memory:',
    configure_s3: bool = True,
) -> duckdb.DuckDBPyConnection:
    logger.info(f"Creating DuckDB connection to database: {duckdb_database}")
    load_dotenv()
    con = duckdb.connect(database=duckdb_database)
    logger.debug(f"DuckDB connection established successfully")

    if not configure_s3:
        return con

    key_id = os.environ.get('AWS_ACCESS_KEY_ID')
    secret = os.environ.get('AWS_SECRET_ACCESS_KEY')
    endpoint_url = os.environ.get('AWS_ENDPOINT_URL', '').strip()
    region = os.environ.get('AWS_REGION')

    if not all([key_id, secret, endpoint_url, region]):
        logger.warning('Skipping S3 secret setup due to missing AWS_* environment variables')
        return con

    logger.info(f"Configuring S3 connection with endpoint: {endpoint_url}, region: {region}")
    # DuckDB expects the endpoint without protocol.
    endpoint = endpoint_url.replace('https://', '').replace('http://', '')

    secret_sql = f"""
    CREATE or replace SECRET s3 (
        TYPE s3,
        KEY_ID '{key_id}',
        SECRET '{secret}',
        ENDPOINT '{endpoint}',
        URL_STYLE 'path',
        REGION '{region}'
    );
    """
    con.sql(secret_sql)
    logger.debug("S3 secret configured successfully")
    return con

def get_file_list_sql(filename: str, study_name: str) -> str:
    return f"""with file_table AS
(SELECT
    file,
    split(file, '/')[7] AS sample_id,
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
    logger.info(f"Fetching file list for pattern: {filename_pattern}, study: {study_name}")
    sql = get_file_list_sql(filename_pattern, study_name)
    logger.debug(f"Executing SQL query: {sql}")
    fl = duckdb_conn.sql(sql).pl()
    fl = fl['file'].to_list()
    logger.info(f"Found {len(fl)} files matching pattern {filename_pattern} for study {study_name}")
    return fl

def main(
    duckdb_conn: duckdb.DuckDBPyConnection, 
    base_directory: UPath = UPath('s3://cmgd-export/'), 
    filename_pattern: str = '',  
    study_name: str = 'LiJ_2014'
) -> None:
    
    local_logger = logger.bind(filename_pattern=filename_pattern, study_name=study_name)
    
    dirname = filename_pattern.replace('.tsv.gz', '')
    local_logger.info(f"Starting processing for {filename_pattern} in study {study_name}")
    
    output_directory = UPath(base_directory) / dirname / f"study_name={study_name}"
    local_logger.debug(f"Output directory: {output_directory}")
   
    fl = get_file_list(filename_pattern, study_name, duckdb_conn=duckdb_conn)
    
    if len(fl) == 0:
        local_logger.warning(f"No files found for {filename_pattern} in study {study_name}, skipping")
        return
     
    # remove old directory if it exists
    local_logger.info(f"Cleaning output directory: {output_directory}")
    files_removed = 0
    dirs_removed = 0
    for d in output_directory.glob('**'):
        if d.is_dir():
            d.rmdir()
            dirs_removed += 1
        elif d.is_file():
            d.unlink()
            files_removed += 1
    if files_removed > 0 or dirs_removed > 0:
        local_logger.debug(f"Removed {files_removed} files and {dirs_removed} directories")
    
    (UPath(base_directory) / dirname).mkdir(parents=True, exist_ok=True)
    local_logger.debug(f"Created base directory: {base_directory / dirname}")

    # partitioned by study_name--nice!
    local_logger.info(f"Starting data export to parquet format")
    sql = f"""
    copy (
        SELECT 
            *
        FROM read_csv_auto({fl}, comment='#', delim='\t', header=false, null_padding=true, filename=true) a 
        join sample_id_map on split_part(a.filename, '/', 7) = sample_id
        where study_name = '{study_name}'
    ) to 
        '{output_directory}'
    (format parquet, compression zstd, file_size_bytes '512MB');
    """
    local_logger.debug(f"Executing export SQL query")
    duckdb_conn.sql(sql)
    local_logger.info(f"Data exported successfully to {output_directory}")
    
    entity_directory = UPath(base_directory) / dirname
    local_logger.debug(f"Creating view src_{dirname} for entity directory: {entity_directory}")
    duckdb_conn.sql(f"create or replace view src_{dirname} as (SELECT * FROM read_parquet('{entity_directory}/**/*.parquet'))")
    local_logger.info(f"Processing completed successfully for {filename_pattern} in study {study_name}")
        
        
        
def create_sample_id_map_parquet(base_directory: UPath, duckdb_database: str = ':memory:'):
    logger.info(f"Creating sample ID map parquet in {base_directory}")
    sample_id_map = 'sample_id_map.csv'
    logger.debug(f"Reading sample ID map from: {sample_id_map}")
    with create_duckdb_connection(duckdb_database=duckdb_database, configure_s3=True) as con:
        sql = f"""
        copy (
            select 
                *
            from read_csv_auto('{sample_id_map}') order by sample_id
        ) to 
        '{base_directory / "sample_id_map.parquet"}' (format parquet, compression zstd)"""
        logger.debug("Exporting sample ID map to parquet")
        con.execute(sql)
        logger.info(f"Sample ID map exported to {base_directory / 'sample_id_map.parquet'}")
        
        sql = f"""create or replace view sample_id_map as (SELECT * FROM read_parquet('{base_directory / "sample_id_map.parquet"}'))"""
        logger.debug("Creating sample_id_map view")
        con.execute(sql)
        logger.debug("Sample_id_map view created successfully")
        
        logger.debug("Verifying sample_id_map parquet file")
        con.execute(f"""SELECT * FROM read_parquet('{base_directory / "sample_id_map.parquet"}')""")
        logger.info("Sample ID map parquet creation completed successfully")
        


def create_file_list(cmgd_base_directory: UPath = UPath('s3://gs-cmgd-mirror/'), duckdb_database: str = ':memory:'):
    logger.info(f"Creating file list from directory: {cmgd_base_directory}")
    configure_s3 = str(cmgd_base_directory).startswith('s3://')
    logger.debug(f"S3 configuration required: {configure_s3}")
    
    with create_duckdb_connection(
        duckdb_database=duckdb_database,
        configure_s3=configure_s3,
    ) as con:
        sql = f"""
        copy (
            select 
                *
            from glob('{cmgd_base_directory / "**"}')
        ) to 
        '{cmgd_base_directory / "file_list.parquet"}' (format parquet, compression zstd)"""
        logger.debug(f"Executing glob query for {cmgd_base_directory}")
        con.sql(sql)
        logger.info(f"File list exported to {cmgd_base_directory / 'file_list.parquet'}")
        
        sql = f"""create or replace view file_list as (SELECT * FROM read_parquet('{cmgd_base_directory / "file_list.parquet"}'))"""
        logger.debug("Creating file_list view")
        con.sql(sql)
        logger.info("File list creation completed successfully")


if __name__ == "__main__":
    logger.info("Starting ETL pipeline")
    
    # TODO: rclone sync prior to running
    
    
    cmgd_base_directory = UPath('/data/davsean/gs-cmgd-mirror/')
    base_directory = UPath('s3://cmgd-export/')
    logger.info(f"Base directories - Source: {cmgd_base_directory}, Target: {base_directory}")
    #create_file_list(cmgd_base_directory=cmgd_base_directory, duckdb_database='cmgd.duckdb')
    
    create_sample_id_map_parquet(base_directory=base_directory, duckdb_database='cmgd.duckdb')
    
    
    filename_patters = [
        'metaphlan_viruses_list.tsv.gz',
        'metaphlan_unknown_list.tsv.gz',
        'marker_abundance.tsv.gz',
        'marker_presence.tsv.gz',
        'marker_rel_ab_w_read_stats.tsv.gz'
    ]    
            
    with create_duckdb_connection(duckdb_database='cmgd.duckdb', configure_s3=True) as duckdb_conn:
        logger.info("Fetching distinct study names from sample_id_map")
        sql = 'select distinct(study_name) from sample_id_map;'
        study_names = duckdb_conn.sql(sql).fetchall()
        study_names = [s[0] for s in study_names]
        logger.info(f"Found {len(study_names)} distinct studies to process")
        logger.debug(f"Study names: {study_names}")
        for study_name in study_names:
            for filename_pattern in filename_patters:
                logger.info(f"Processing {filename_pattern} for study {study_name}")
                main(
                    duckdb_conn=duckdb_conn,
                    base_directory=base_directory, 
                    filename_pattern=filename_pattern, 
                    study_name=study_name
                )

