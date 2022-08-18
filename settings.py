#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import platform
import psycopg2
import os
import sys


# default census year
temp_census_year = '2021'

# get python, psycopg2 and OS versions
python_version = sys.version.split("(")[0].strip()
psycopg2_version = psycopg2.__version__.split("(")[0].strip()
os_version = platform.system() + " " + platform.version().strip()

# set the command line arguments for the script
parser = argparse.ArgumentParser(
    description='A quick way to load the complete ABS 2021, 2016 or 2011 Census into Postgres, '
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

# schema names for the census data & boundary tables
parser.add_argument(
    '--census-year', default=temp_census_year,
    help='Census year as YYYY. Valid values are \'2011\', \'2016\' or \'2021\'. '
         'Defaults to \'' + temp_census_year + '\'.')
parser.add_argument(
    "--srid", type=int, default=4283,
    help="Sets the coordinate system (SRID aka EPSG number) of the input data. Valid values are 4283 (GDA94) and 7844 (GDA2020)")

parser.add_argument(
    '--data-schema',
    help='Schema name to store data tables in. Defaults to \'census_' + temp_census_year + '_data\'.')
parser.add_argument(
    '--boundary-schema',
    help='Schema name to store raw boundary tables in. Defaults to \'census_' + temp_census_year + '_bdys\'.')
parser.add_argument(
    '--web-schema',
    help='Schema name to store web optimised boundary tables in. Defaults to \'census_' + temp_census_year + '_web\'.')

# input directories
parser.add_argument(
    '--census-data-path', help='Path to source census data tables (*.csv files).', required=True)
parser.add_argument(
    '--census-bdys-path', help='Local path to source admin boundary files.', required=True)

# global var containing all input parameters
args = parser.parse_args()

# create the dictionary of settings
census_data_path = args.census_data_path or ""
census_bdys_path = args.census_bdys_path or ""

max_concurrent_processes = args.max_processes
census_year = args.census_year
states = ["ACT", "NSW", "NT", "OT", "QLD", "SA", "TAS", "VIC", "WA"]
data_schema = args.data_schema or 'census_' + census_year + '_data'
boundary_schema = args.boundary_schema or 'census_' + census_year + '_bdys'
web_schema = args.web_schema or 'census_' + census_year + '_web'
data_directory = census_data_path.replace("\\", "/")
boundaries_directory = census_bdys_path.replace("\\", "/")

srid = args.srid

if srid not in (4283, 7844):
    print("Invalid coordinate system (SRID) - EXITING!\nValid values are 4283 (GDA94) and 7844 (GDA2020)")
    exit()

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
if census_year == '2021':
    metadata_file_prefix = "Metadata_"
    metadata_file_type = ".xlsx"
    census_metadata_dicts = [{"table": "metadata_tables", "first_row": "table number"},
                             {"table": "metadata_stats", "first_row": "sequential"}]

    data_file_prefix = "2021Census_"
    data_file_type = ".csv"
    table_name_part = 1  # position in the data file name that equals its destination table name
    bdy_name_part = 3  # position in the data file name that equals its census boundary name
    region_id_field = "region_id"

    population_stat = "g3"
    population_table = "g01"
    indigenous_population_stat = "i3"

    # TODO: verify this
    indigenous_population_table = "i01a"

    bdy_table_dicts = \
        [{"boundary": "add", "id_field": "add_code_2021", "name_field": "add_name_2021", "area_field": "area_albers_sqkm"},
         {"boundary": "aus", "id_field": "aus_code_2021", "name_field": "aus_name_2021", "area_field": "area_albers_sqkm"},
         {"boundary": "ced", "id_field": "ced_code_2021", "name_field": "ced_name_2021", "area_field": "area_albers_sqkm"},
         {"boundary": "dzn", "id_field": "dzn_code_2021", "name_field": "dzn_name_2021", "area_field": "area_albers_sqkm"},
         {"boundary": "gccsa", "id_field": "gcc_code_2021", "name_field": "gcc_name_2021", "area_field": "area_albers_sqkm"},
         {"boundary": "iare", "id_field": "iar_code_2021", "name_field": "iar_name_2021", "area_field": "area_albers_sqkm"},
         {"boundary": "iloc", "id_field": "ilo_code_2021", "name_field": "ilo_name_2021", "area_field": "area_albers_sqkm"},
         {"boundary": "ireg", "id_field": "ire_code_2021", "name_field": "ire_name_2021", "area_field": "area_albers_sqkm"},
         {"boundary": "lga", "id_field": "lga_code_2021", "name_field": "lga_name_2021", "area_field": "area_albers_sqkm"},
         {"boundary": "mb", "id_field": "mb_code_2021", "name_field": "'MB ' || mb_code_2021", "area_field": "area_albers_sqkm"},
         # {"boundary": "nrmr", "id_field": "nrm_code_2021", "name_field": "nrm_name_2021", "area_field": "area_albers_sqkm"},
         {"boundary": "poa", "id_field": "poa_code_2021", "name_field": "'Postcode ' || poa_name_2021", "area_field": "area_albers_sqkm"},
         # {"boundary": "ra", "id_field": "ra_code_2021", "name_field": "ra_name_2021", "area_field": "area_albers_sqkm"},
         {"boundary": "sa1", "id_field": "sa1_code_2021", "name_field": "'SA1 ' || sa1_code_2021", "area_field": "area_albers_sqkm"},
         {"boundary": "sa2", "id_field": "sa2_code_2021", "name_field": "sa2_name_2021", "area_field": "area_albers_sqkm"},
         {"boundary": "sa3", "id_field": "sa3_code_2021", "name_field": "sa3_name_2021", "area_field": "area_albers_sqkm"},
         {"boundary": "sa4", "id_field": "sa4_code_2021", "name_field": "sa4_name_2021", "area_field": "area_albers_sqkm"},
         {"boundary": "sal", "id_field": "sal_code_2021", "name_field": "sal_name_2021", "area_field": "area_albers_sqkm"},
         {"boundary": "sed", "id_field": "sed_code_2021", "name_field": "sed_name_2021", "area_field": "area_albers_sqkm"},
         # {"boundary": "sos", "id_field": "sos_code_2021", "name_field": "sos_name_2021", "area_field": "area_albers_sqkm"},
         # {"boundary": "sosr", "id_field": "ssr_code_2021", "name_field": "ssr_name_2021", "area_field": "area_albers_sqkm"},
         # {"boundary": "ssc", "id_field": "ssc_code_2021", "name_field": "ssc_name_2021", "area_field": "area_albers_sqkm"},
         {"boundary": "ste", "id_field": "ste_code_2021", "name_field": "ste_name_2021", "area_field": "area_albers_sqkm"},
         # {"boundary": "sua", "id_field": "sua_code_2021", "name_field": "sua_name_2021", "area_field": "area_albers_sqkm"},
         {"boundary": "tr", "id_field": "tr_code_2021", "name_field": "tr_name_2021", "area_field": "area_albers_sqkm"}
         # {"boundary": "ucl", "id_field": "ucl_code_2021", "name_field": "ucl_name_2021", "area_field": "area_albers_sqkm"}
        ]

elif census_year == '2016':
    metadata_file_prefix = "Metadata_"
    metadata_file_type = ".xls"
    census_metadata_dicts = [{"table": "metadata_tables", "first_row": "table number"},
                             {"table": "metadata_stats", "first_row": "sequential"}]

    data_file_prefix = "2016Census_"
    data_file_type = ".csv"
    table_name_part = 1  # position in the data file name that equals it's destination table name
    bdy_name_part = 3  # position in the data file name that equals it's census boundary name
    region_id_field = "region_id"

    population_stat = "g3"
    population_table = "g01"
    indigenous_population_stat = "i3"
    indigenous_population_table = "i01a"

    bdy_table_dicts = \
         [{"boundary": "ced", "id_field": "ced_code16", "name_field": "ced_name16", "area_field": "areasqkm16"},
         {"boundary": "gccsa", "id_field": "gcc_code16", "name_field": "gcc_name16", "area_field": "areasqkm16"},
         {"boundary": "iare", "id_field": "iar_code16", "name_field": "iar_name16", "area_field": "areasqkm16"},
         {"boundary": "iloc", "id_field": "ilo_code16", "name_field": "ilo_name16", "area_field": "areasqkm16"},
         {"boundary": "ireg", "id_field": "ire_code16", "name_field": "ire_name16", "area_field": "areasqkm16"},
         {"boundary": "lga", "id_field": "lga_code16", "name_field": "lga_name16", "area_field": "areasqkm16"},
         {"boundary": "mb", "id_field": "mb_code16", "name_field": "'MB ' || mb_code16", "area_field": "areasqkm16"},
         {"boundary": "nrmr", "id_field": "nrm_code16", "name_field": "nrm_name16", "area_field": "areasqkm16"},
         {"boundary": "poa", "id_field": "poa_code16", "name_field": "'Postcode ' || poa_name16", "area_field": "areasqkm16"},
         {"boundary": "ra", "id_field": "ra_code16", "name_field": "ra_name16", "area_field": "areasqkm16"},
         {"boundary": "sa1", "id_field": "sa1_7dig16", "name_field": "'SA1 ' || sa1_7dig16", "area_field": "areasqkm16"},
         {"boundary": "sa2", "id_field": "sa2_main16", "name_field": "sa2_name16", "area_field": "areasqkm16"},
         {"boundary": "sa3", "id_field": "sa3_code16", "name_field": "sa3_name16", "area_field": "areasqkm16"},
         {"boundary": "sa4", "id_field": "sa4_code16", "name_field": "sa4_name16", "area_field": "areasqkm16"},
         {"boundary": "sed", "id_field": "sed_code16", "name_field": "sed_name16", "area_field": "areasqkm16"},
         {"boundary": "sos", "id_field": "sos_code16", "name_field": "sos_name16", "area_field": "areasqkm16"},
         {"boundary": "sosr", "id_field": "ssr_code16", "name_field": "ssr_name16", "area_field": "areasqkm16"},
         {"boundary": "ssc", "id_field": "ssc_code16", "name_field": "ssc_name16", "area_field": "areasqkm16"},
         {"boundary": "ste", "id_field": "ste_code16", "name_field": "ste_name16", "area_field": "areasqkm16"},
         {"boundary": "sua", "id_field": "sua_code16", "name_field": "sua_name16", "area_field": "areasqkm16"},
         {"boundary": "tr", "id_field": "tr_code16", "name_field": "tr_name16", "area_field": "areasqkm16"},
         {"boundary": "ucl", "id_field": "ucl_code16", "name_field": "ucl_name16", "area_field": "areasqkm16"}]

elif census_year == '2011':
    metadata_file_prefix = "Metadata_"
    metadata_file_type = ".xlsx"
    census_metadata_dicts = [{"table": "metadata_tables", "first_row": "table number"},
                             {"table": "metadata_stats", "first_row": "sequential"}]

    data_file_prefix = "2011Census_"
    data_file_type = ".csv"
    table_name_part = 1  # position in the data file name that equals it's destination table name
    bdy_name_part = 3  # position in the data file name that equals it's census boundary name
    region_id_field = "region_id"

    population_stat = "b3"
    population_table = "b01"
    indigenous_population_stat = "i3"
    indigenous_population_table = "i01a"

    bdy_table_dicts = \
        [{"boundary": "ced", "id_field": "ced_code", "name_field": "ced_name", "area_field": "area_sqkm"},
         {"boundary": "gccsa", "id_field": "gccsa_code", "name_field": "gccsa_name", "area_field": "area_sqkm"},
         {"boundary": "iare", "id_field": "iare_code", "name_field": "iare_name", "area_field": "area_sqkm"},
         {"boundary": "iloc", "id_field": "iloc_code", "name_field": "iloc_name", "area_field": "area_sqkm"},
         {"boundary": "ireg", "id_field": "ireg_code", "name_field": "ireg_name", "area_field": "area_sqkm"},
         {"boundary": "lga", "id_field": "lga_code", "name_field": "lga_name", "area_field": "area_sqkm"},
         {"boundary": "mb", "id_field": "mb_code11", "name_field": "'MB ' || mb_code11", "area_field": "albers_sqm / 1000000.0"},
         {"boundary": "poa", "id_field": "poa_code", "name_field": "'POA ' || poa_name", "area_field": "area_sqkm"},
         {"boundary": "ra", "id_field": "ra_code", "name_field": "ra_name", "area_field": "area_sqkm"},
         {"boundary": "sa1", "id_field": "sa1_7digit", "name_field": "'SA1 ' || sa1_7digit", "area_field": "area_sqkm"},
         {"boundary": "sa2", "id_field": "sa2_main", "name_field": "sa2_name", "area_field": "area_sqkm"},
         {"boundary": "sa3", "id_field": "sa3_code", "name_field": "sa3_name", "area_field": "area_sqkm"},
         {"boundary": "sa4", "id_field": "sa4_code", "name_field": "sa4_name", "area_field": "area_sqkm"},
         {"boundary": "sed", "id_field": "sed_code", "name_field": "sed_name", "area_field": "area_sqkm"},
         {"boundary": "sla", "id_field": "sla_main", "name_field": "sla_name", "area_field": "area_sqkm"},
         {"boundary": "sos", "id_field": "sos_code", "name_field": "sos_name", "area_field": "area_sqkm"},
         {"boundary": "sosr", "id_field": "sosr_code", "name_field": "sosr_name", "area_field": "area_sqkm"},
         {"boundary": "ssc", "id_field": "ssc_code", "name_field": "ssc_name", "area_field": "area_sqkm"},
         {"boundary": "ste", "id_field": "state_code", "name_field": "state_name", "area_field": "area_sqkm"},
         {"boundary": "sua", "id_field": "sua_code", "name_field": "sua_name", "area_field": "area_sqkm"},
         {"boundary": "ucl", "id_field": "ucl_code", "name_field": "ucl_name", "area_field": "area_sqkm"}]

# get Postgres, PostGIS & GEOS versions and flag if ST_Subdivide is supported

# get Postgres connection & cursor
temp_pg_conn = psycopg2.connect(pg_connect_string)
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
