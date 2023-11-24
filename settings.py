#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import platform
import psycopg
import os
import sys

# default census year
census_year = '2021'

# get python, psycopg and OS versions
python_version = sys.version.split("(")[0].strip()
psycopg_version = psycopg.__version__.split("(")[0].strip()
os_version = platform.system() + " " + platform.version().strip()

# set the command line arguments for the script
parser = argparse.ArgumentParser(
    description='A quick way to load the complete ABS 2021 Census into Postgres, '
                'ready to use as reference data for analysis and visualisation.')

parser.add_argument(
    '--max-processes', type=int, default=4,
    help='Maximum number of parallel processes to use for the data load. (Set it to the number of cores on the '
         'Postgres server minus 2, limit to 12 if 16+ cores - there is minimal benefit beyond 12). Defaults to 4.')

# PG Options
parser.add_argument(
    '--pghost',
    help='Host name for Postgres server. Defaults to PGHOST environment variable if set, otherwise localhost.')
parser.add_argument(
    '--pgport', type=int,
    help='Port number for Postgres server. Defaults to PGPORT environment variable if set, otherwise 5432.')
parser.add_argument(
    '--pgdb',
    help='Database name for Postgres server. Defaults to PGDATABASE environment variable if set, '
         'otherwise geo.')
parser.add_argument(
    '--pguser',
    help='Username for Postgres server. Defaults to PGUSER environment variable if set, otherwise postgres.')
parser.add_argument(
    '--pgpassword',
    help='Password for Postgres server. Defaults to PGPASSWORD environment variable if set, '
         'otherwise \'password\'.')

# custom schema name?
parser.add_argument(
    '--data-schema',
    help='Schema name to store data tables in. Defaults to \'census_' + census_year + '_data\'.')

# input directories
parser.add_argument(
    '--census-data-path', help='Path to source census data tables (*.csv files).', required=True)

# global var containing all input parameters
args = parser.parse_args()

# create the dictionary of settings
census_data_path = args.census_data_path or ""

max_concurrent_processes = args.max_processes
states = ["ACT", "NSW", "NT", "OT", "QLD", "SA", "TAS", "VIC", "WA"]
data_schema = args.data_schema or 'census_' + census_year + '_data'
data_directory = census_data_path.replace("\\", "/")

# create postgres connect string
pg_host = args.pghost or os.getenv("PGHOST", "localhost")
pg_port = args.pgport or os.getenv("PGPORT", 5432)
pg_db = args.pgdb or os.getenv("POSTGRES_USER", "geo")
pg_user = args.pguser or os.getenv("POSTGRES_USER", "postgres")
pg_password = args.pgpassword or os.getenv("POSTGRES_PASSWORD", "password")

pg_connect_string = f"dbname='{pg_db}' host='{pg_host}' port='{pg_port}' user='{pg_user}' password='{pg_password}'"

# set postgres script directory
sql_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "postgres-scripts")

# set file name and field name defaults based on census year
metadata_file_prefix = "Metadata_"
metadata_file_type = ".xlsx"
census_metadata_dicts = [{"table": "metadata_tables", "first_row": "table number"},
                         {"table": "metadata_stats", "first_row": "sequential"}]

data_file_prefix = "2021Census_"
data_file_type = ".csv"
table_name_part = 1  # position in the data file name that equals its destination table name
bdy_name_part = 3  # position in the data file name that equals its census boundary name
region_id_field = "region_id"

# get Postgres, PostGIS & GEOS versions and flag if ST_Subdivide is supported

# get Postgres connection & cursor
temp_pg_conn = psycopg.connect(pg_connect_string)
temp_pg_cur = temp_pg_conn.cursor()

# get Postgres version
temp_pg_cur.execute("SELECT version()")
pg_version = temp_pg_cur.fetchone()[0].replace("PostgreSQL ", "").split(",")[0]

# get PostGIS version
temp_pg_cur.execute("SELECT PostGIS_full_version()")
lib_strings = temp_pg_cur.fetchone()[0].replace("\"", "").split(" ")

temp_pg_cur.close()
temp_pg_cur = None
temp_pg_conn.close()
temp_pg_conn = None

postgis_version = "UNKNOWN"
postgis_version_num = 0.0
geos_version = "UNKNOWN"
geos_version_num = 0.0

st_subdivide_supported = False
st_clusterkmeans_supported = False

for lib_string in lib_strings:
    if lib_string[:8] == "POSTGIS=":
        postgis_version = lib_string.replace("POSTGIS=", "")
        postgis_version_num = float(postgis_version[:3])
    if lib_string[:5] == "GEOS=":
        geos_version = lib_string.replace("GEOS=", "")
        geos_version_num = float(geos_version[:3])

if postgis_version_num >= 2.2 and geos_version_num >= 3.5:
    st_subdivide_supported = True

if postgis_version_num >= 2.3:
    st_clusterkmeans_supported = True
