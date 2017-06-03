import argparse
import io
import multiprocessing
import math
import os
import platform
import psycopg2
import subprocess
import sys


# set the command line arguments for the script
def set_arguments():
    parser = argparse.ArgumentParser(
        description='A quick way to load the complete GNAF and PSMA Admin Boundaries into Postgres, '
                    'simplified and ready to use as reference data for geocoding, analysis and visualisation.')

    parser.add_argument(
        '--max-processes', type=int, default=3,
        help='Maximum number of parallel processes to use for the data load. (Set it to the number of cores on the '
             'Postgres server minus 2, limit to 12 if 16+ cores - there is minimal benefit beyond 12). Defaults to 3.')

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
             'otherwise utils.')
    parser.add_argument(
        '--pguser',
        help='Username for Postgres server. Defaults to PGUSER environment variable if set, otherwise postgres.')
    parser.add_argument(
        '--pgpassword',
        help='Password for Postgres server. Defaults to PGPASSWORD environment variable if set, '
             'otherwise \'password\'.')

    # schema names for the census data & boundary tables
    census_year = '2016'

    parser.add_argument(
        '--census-year', default=census_year,
        help='Census year as YYYY. Valid values are \'2011\' or \'2016\'. '
             'Defaults to last census \'' + census_year + '\'.')

    parser.add_argument(
        '--data-schema', default='census_' + census_year + '_data',
        help='Schema name to store raw GNAF tables in. Defaults to \'census_' + census_year + '_data\'.')
    parser.add_argument(
        '--boundary-schema', default='census_' + census_year + '_bdys',
        help='Schema name to store raw admin boundary tables in. Defaults to \'census_' + census_year + '_bdys\'.')

    # directories
    parser.add_argument(
        '--census-data-path', required=True,
        help='Path to source census data tables (*.csv files). '
             'This directory must be accessible by the Postgres server, and the local path to the directory for the '
             'server must be set via the local-server-dir argument if it differs from this path.')
    # parser.add_argument(
    #     '--local-server-dir',
    #     help='Local path on server corresponding to census-data-path, if different to census-data-path.')
    parser.add_argument(
        '--census-bdys-path', required=True, help='Local path to source admin boundary files.')

    # # states to load
    # parser.add_argument('--states', nargs='+', choices=["ACT", "NSW", "NT", "OT", "QLD", "SA", "TAS", "VIC", "WA"],
    #                     default=["ACT", "NSW", "NT", "OT", "QLD", "SA", "TAS", "VIC", "WA"],
    #                     help='List of states to load data for. Defaults to all states.')

    return parser.parse_args()


# create the dictionary of settings
def get_settings(args):
    settings = dict()

    settings['max_concurrent_processes'] = args.max_processes
    settings['census_year'] = args.census_year
    # settings['states_to_load'] = args.states
    settings['states'] = ["ACT", "NSW", "NT", "OT", "QLD", "SA", "TAS", "VIC", "WA"]
    settings['data_schema'] = args.data_schema
    settings['boundary_schema'] = args.boundary_schema
    settings['data_directory'] = args.census_data_path.replace("\\", "/")
    # if args.local_server_dir:
    #     settings['data_pg_server_local_directory'] = args.local_server_dir.replace("\\", "/")
    # else:
    #     settings['data_pg_server_local_directory'] = settings['data_directory']
    settings['boundaries_local_directory'] = args.census_bdys_path.replace("\\", "/")

    # create postgres connect string
    settings['pg_host'] = args.pghost or os.getenv("PGHOST", "localhost")
    settings['pg_port'] = args.pgport or os.getenv("PGPORT", 5432)
    settings['pg_db'] = args.pgdb or os.getenv("PGDATABASE", "geo")
    settings['pg_user'] = args.pguser or os.getenv("PGUSER", "postgres")
    settings['pg_password'] = args.pgpassword or os.getenv("PGPASSWORD", "password")

    settings['pg_connect_string'] = "dbname='{0}' host='{1}' port='{2}' user='{3}' password='{4}'".format(
        settings['pg_db'], settings['pg_host'], settings['pg_port'], settings['pg_user'], settings['pg_password'])

    # set postgres script directory
    settings['sql_dir'] = os.path.join(os.path.dirname(os.path.realpath(__file__)), "postgres-scripts")

    # set file name and field name defaults based on census year
    if settings['census_year'] == '2016':
        settings['metadata_file_prefix'] = "Sample_Metadata_"
        settings['metadata_file_type'] = ".xls"
        settings["census_metadata_dicts"] = [{"table": "metadata_tables", "first_row": "table number"},
                                             {"table": "metadata_stats", "first_row": "sequential"}]

        settings['data_file_prefix'] = "2016_Sample_"
        settings['data_file_type'] = ".csv"
        settings['table_name_part'] = 2  # position in the data file name that equals it's destination table name
        settings['bdy_name_part'] = 3  # position in the data file name that equals it's census boundary name
        settings['region_id_field'] = "aus_code_2016"

        settings['bdy_table_dicts'] = \
            [{"boundary": "add", "id_field": "add_code16", "name_field": "add_name16", "area_field": "areasqkm16"},
             {"boundary": "ced", "id_field": "ced_code16", "name_field": "ced_name16", "area_field": "areasqkm16"},
             {"boundary": "gccsa", "id_field": "gcc_code16", "name_field": "gcc_name16", "area_field": "areasqkm16"},
             {"boundary": "iare", "id_field": "iar_code16", "name_field": "iar_name16", "area_field": "areasqkm16"},
             {"boundary": "iloc", "id_field": "ilo_code16", "name_field": "ilo_name16", "area_field": "areasqkm16"},
             {"boundary": "ireg", "id_field": "ire_code16", "name_field": "ire_name16", "area_field": "areasqkm16"},
             {"boundary": "lga", "id_field": "lga_code16", "name_field": "lga_name16", "area_field": "areasqkm16"},
             {"boundary": "mb", "id_field": "mb_code16", "name_field": "'MB ' || mb_code16", "area_field": "areasqkm16"},
             {"boundary": "nrmr", "id_field": "nrm_code16", "name_field": "nrm_name16", "area_field": "areasqkm16"},
             {"boundary": "poa", "id_field": "poa_code16", "name_field": "'POA ' || poa_name16", "area_field": "areasqkm16"},
             # {"boundary": "ra", "id_field": "ra_code16", "name_field": "ra_name16", "area_field": "areasqkm16"},
             {"boundary": "sa1", "id_field": "sa1_main16", "name_field": "'SA1 ' || sa1_main16", "area_field": "areasqkm16"},
             {"boundary": "sa2", "id_field": "sa2_main16", "name_field": "sa2_name16", "area_field": "areasqkm16"},
             {"boundary": "sa3", "id_field": "sa3_code16", "name_field": "sa3_name16", "area_field": "areasqkm16"},
             {"boundary": "sa4", "id_field": "sa4_code16", "name_field": "sa4_name16", "area_field": "areasqkm16"},
             {"boundary": "sed", "id_field": "sed_code16", "name_field": "sed_name16", "area_field": "areasqkm16"},
             # {"boundary": "sla", "id_field": "sla_main", "name_field": "sla_name16", "area_field": "areasqkm16"},
             # {"boundary": "sos", "id_field": "sos_code16", "name_field": "sos_name16", "area_field": "areasqkm16"},
             # {"boundary": "sosr", "id_field": "sosr_code16", "name_field": "sosr_name16", "area_field": "areasqkm16"},
             {"boundary": "ssc", "id_field": "ssc_code16", "name_field": "ssc_name16", "area_field": "areasqkm16"},
             {"boundary": "ste", "id_field": "state_code16", "name_field": "state_name16", "area_field": "areasqkm16"},
             # {"boundary": "sua", "id_field": "sua_code16", "name_field": "sua_name16", "area_field": "areasqkm16"},
             {"boundary": "tr", "id_field": "tr_code16", "name_field": "tr_name16", "area_field": "areasqkm16"}]
    # {"boundary": "ucl", "id_field": "ucl_code16", "name_field": "ucl_name16", "area_field": "areasqkm16"}]

    elif settings['census_year'] == '2011':
        settings['metadata_file_prefix'] = "Metadata_"
        settings['metadata_file_type'] = ".xlsx"
        settings["census_metadata_dicts"] = [{"table": "metadata_tables", "first_row": "table number"},
                                             {"table": "metadata_stats", "first_row": "sequential"}]

        settings['data_file_prefix'] = "2011Census_"
        settings['data_file_type'] = ".csv"
        settings['table_name_part'] = 1  # position in the data file name that equals it's destination table name
        settings['bdy_name_part'] = 3  # position in the data file name that equals it's census boundary name
        settings['region_id_field'] = "region_id"

        settings['bdy_table_dicts'] = \
            [{"boundary": "ced", "id_field": "ced_code", "name_field": "ced_name", "area_field": "area_sqkm", "thin_zoom": 10},
             {"boundary": "gccsa", "id_field": "gccsa_code", "name_field": "gccsa_name", "area_field": "area_sqkm", "thin_zoom": 10},
             {"boundary": "iare", "id_field": "iare_code", "name_field": "iare_name", "area_field": "area_sqkm", "thin_zoom": 10},
             {"boundary": "iloc", "id_field": "iloc_code", "name_field": "iloc_name", "area_field": "area_sqkm", "thin_zoom": 10},
             {"boundary": "ireg", "id_field": "ireg_code", "name_field": "ireg_name", "area_field": "area_sqkm", "thin_zoom": 10},
             {"boundary": "lga", "id_field": "lga_code", "name_field": "lga_name", "area_field": "area_sqkm", "thin_zoom": 12},
             {"boundary": "mb", "id_field": "mb_code11", "name_field": "'MB ' || mb_code11", "area_field": "albers_sqm / 1000000.0", "thin_zoom": 16},
             {"boundary": "poa", "id_field": "poa_code", "name_field": "'POA ' || poa_name", "area_field": "area_sqkm", "thin_zoom": 15},
             {"boundary": "ra", "id_field": "ra_code", "name_field": "ra_name", "area_field": "area_sqkm", "thin_zoom": 8},
             {"boundary": "sa1", "id_field": "sa1_7digit", "name_field": "'SA1 ' || sa1_7digit", "area_field": "area_sqkm", "thin_zoom": 15},
             {"boundary": "sa2", "id_field": "sa2_main", "name_field": "sa2_name", "area_field": "area_sqkm", "thin_zoom": 13},
             {"boundary": "sa3", "id_field": "sa3_code", "name_field": "sa3_name", "area_field": "area_sqkm", "thin_zoom": 11},
             {"boundary": "sa4", "id_field": "sa4_code", "name_field": "sa4_name", "area_field": "area_sqkm", "thin_zoom": 10},
             {"boundary": "sed", "id_field": "sed_code", "name_field": "sed_name", "area_field": "area_sqkm", "thin_zoom": 10},
             {"boundary": "sla", "id_field": "sla_main", "name_field": "sla_name", "area_field": "area_sqkm", "thin_zoom": 12},
             {"boundary": "sos", "id_field": "sos_code", "name_field": "sos_name", "area_field": "area_sqkm", "thin_zoom": 9},
             {"boundary": "sosr", "id_field": "sosr_code", "name_field": "sosr_name", "area_field": "area_sqkm", "thin_zoom": 8},
             {"boundary": "ssc", "id_field": "ssc_code", "name_field": "ssc_name", "area_field": "area_sqkm", "thin_zoom": 12},
             {"boundary": "ste", "id_field": "state_code", "name_field": "state_name", "area_field": "area_sqkm", "thin_zoom": 6},
             {"boundary": "sua", "id_field": "sua_code", "name_field": "sua_name", "area_field": "area_sqkm", "thin_zoom": 10},
             {"boundary": "ucl", "id_field": "ucl_code", "name_field": "ucl_name", "area_field": "area_sqkm", "thin_zoom": 13}]
    else:
        return None

    return settings


# get the boundary name that suits each (tiled map) zoom level
def get_boundary_name(zoom_level):

    if zoom_level < 7:
        boundary_name = "ste"
    elif zoom_level < 9:
        boundary_name = "sos"
    elif zoom_level < 10:
        boundary_name = "sa4"
    elif zoom_level < 12:
        boundary_name = "sa3"
    elif zoom_level < 14:
        boundary_name = "sa2"
    elif zoom_level < 17:
        boundary_name = "sa1"
    else:
        boundary_name = "mb"

    return boundary_name


# calculates the area tolerance (in m2) for vector simplification using the Visvalingam-Whyatt algorithm
def get_tolerance(zoom_level):

    # pixels squared factor
    tolerance_square_pixels = 10

    # # rough metres to degrees conversation, using spherical WGS84 datum radius for simplicity and speed
    # metres2degrees = (2.0 * math.pi * 6378137.0) / 360.0

    # default Google/Bing map tile scales
    metres_per_pixel = 156543.03390625 / math.pow(2.0, float(zoom_level))

    # the tolerance (metres) for vector simplification using the VW algorithm
    square_metres_per_pixel = math.pow(metres_per_pixel, 2.0)

    # # the tolerance for thinning data and limiting decimal places in GeoJSON responses
    # degrees_per_pixel = metres_per_pixel / metres2degrees

    # # the tolerance (degrees) for vector simplifcation using the VW algorithm
    # square_degrees_per_pixel = math.pow(degrees_per_pixel, 2.0)

    # tolerance to use
    # tolerance = square_degrees_per_pixel * tolerance_square_pixels
    tolerance = square_metres_per_pixel * tolerance_square_pixels

    return tolerance


# maximum number of decimal places for boundary coordinates - improves display performance
def get_decimal_places(zoom_level):

    # rough metres to degrees conversation, using spherical WGS84 datum radius for simplicity and speed
    metres2degrees = (2.0 * math.pi * 6378137.0) / 360.0

    # default Google/Bing map tile scales
    metres_per_pixel = 156543.03390625 / math.pow(2.0, float(zoom_level))

    # the tolerance for thinning data and limiting decimal places in GeoJSON responses
    degrees_per_pixel = metres_per_pixel / metres2degrees

    scale_string = "{:10.9f}".format(degrees_per_pixel).split(".")[1]
    places = 1

    trigger = "0"

    # find how many zero decimal places there are. e.g. 0.00001234 = 4 zeros
    for c in scale_string:
        if c == trigger:
            places += 1
        else:
            trigger = "don't do anything else"  # used to cleanly exit the loop

    return places


# # set tolerance for vector simplification
# def get_simplify_vw_tolerance(zoom_level):
#     reverse_zoom_level = 17 - zoom_level
#     tolerance = 75 * math.pow(2.75, float(reverse_zoom_level))
#     return tolerance


# takes a list of sql queries or command lines and runs them using multiprocessing
def multiprocess_csv_import(work_list, settings, logger):
    pool = multiprocessing.Pool(processes=settings['max_concurrent_processes'])

    num_jobs = len(work_list)

    results = pool.imap_unordered(run_csv_import_multiprocessing, [[w, settings] for w in work_list])

    pool.close()
    pool.join()

    result_list = list(results)
    num_results = len(result_list)

    if num_jobs > num_results:
        logger.warning("\t- A MULTIPROCESSING PROCESS FAILED WITHOUT AN ERROR\nACTION: Check the record counts")

    for result in result_list:
        if result != "SUCCESS":
            logger.info(result)


def run_csv_import_multiprocessing(args):
    file_dict = args[0]
    settings = args[1]

    pg_conn = psycopg2.connect(settings['pg_connect_string'])
    pg_conn.autocommit = True
    pg_cur = pg_conn.cursor()

    # CREATE TABLE

    # get the census fields for the table
    field_list = list()

    # sql = "SELECT sequential_id || ' ' || stat_type AS field " \
    #       "FROM {0}.metadata_stats " \
    #       "WHERE lower(table_number) LIKE '{1}%'" \
    #     .format(settings['data_schema'], table_number)
    sql = "SELECT sequential_id || ' double precision' AS field " \
          "FROM {0}.metadata_stats " \
          "WHERE lower(table_number) LIKE '{1}%'" \
        .format(settings['data_schema'], file_dict["table"])
    pg_cur.execute(sql)

    fields = pg_cur.fetchall()

    for field in fields:
        field_list.append(field[0].lower())

    fields_string = ",".join(field_list)

    # create the table
    table_name = file_dict["boundary"] + "_" + file_dict["table"]

    create_table_sql = "DROP TABLE IF EXISTS {0}.{1} CASCADE;" \
                       "CREATE TABLE {0}.{1} ({4} text, {2}) WITH (OIDS=FALSE);" \
                       "ALTER TABLE {0}.metadata_tables OWNER TO {3}" \
        .format(settings['data_schema'], table_name, fields_string,
                settings['pg_user'], settings['region_id_field'])

    pg_cur.execute(create_table_sql)

    # IMPORT CSV FILE

    try:
        # read CSV into a string
        raw_string = open(file_dict["path"], 'r').read()

        # clean whitespace and non-ascii characters
        clean_string = raw_string.lstrip().rstrip().replace(" ", "").replace("\x1A", "")

        # convert to in memory stream
        csv_file = io.StringIO(clean_string)
        csv_file.seek(0)  # move position back to beginning of file before reading

        # import into Postgres
        sql = "COPY {0}.{1} FROM stdin WITH CSV HEADER DELIMITER as ',' NULL as '..'"\
            .format(settings['data_schema'], table_name)
        pg_cur.copy_expert(sql, csv_file)

    except Exception as ex:
        return "IMPORT CSV INTO POSTGRES FAILED! : {0} : {1}".format(file_dict["path"], ex)

    # add primary key and vacuum index
    sql = "ALTER TABLE {0}.{1} ADD CONSTRAINT {1}_pkey PRIMARY KEY ({2});" \
          "ALTER TABLE {0}.{1} CLUSTER ON {1}_pkey" \
        .format(settings['data_schema'], table_name, settings['region_id_field'])
    pg_cur.execute(sql)

    pg_cur.execute("VACUUM ANALYSE {0}.{1}".format(settings['data_schema'], table_name))

    result = "SUCCESS"

    pg_cur.close()
    pg_conn.close()

    return result


# takes a list of sql queries or command lines and runs them using multiprocessing
def multiprocess_list(mp_type, work_list, settings, logger):
    pool = multiprocessing.Pool(processes=settings['max_concurrent_processes'])

    num_jobs = len(work_list)

    if mp_type == "sql":
        results = pool.imap_unordered(run_sql_multiprocessing, [[w, settings] for w in work_list])
    else:
        results = pool.imap_unordered(run_command_line, work_list)

    pool.close()
    pool.join()

    result_list = list(results)
    num_results = len(result_list)

    if num_jobs > num_results:
        logger.warning("\t- A MULTIPROCESSING PROCESS FAILED WITHOUT AN ERROR\nACTION: Check the record counts")

    for result in result_list:
        if result != "SUCCESS":
            logger.info(result)


def run_sql_multiprocessing(args):
    the_sql = args[0]
    settings = args[1]
    pg_conn = psycopg2.connect(settings['pg_connect_string'])
    pg_conn.autocommit = True
    pg_cur = pg_conn.cursor()

    # # set raw gnaf database schema (it's needed for the primary and foreign key creation)
    # if settings['raw_gnaf_schema'] != "public":
    #     pg_cur.execute("SET search_path = {0}, public, pg_catalog".format(settings['raw_gnaf_schema'],))

    try:
        pg_cur.execute(the_sql)
        result = "SUCCESS"
    except Exception as ex:
        result = "SQL FAILED! : {0} : {1}".format(the_sql, ex)

    pg_cur.close()
    pg_conn.close()

    return result


def run_command_line(cmd):
    # run the command line without any output (it'll still tell you if it fails miserably)
    try:
        fnull = open(os.devnull, "w")
        subprocess.call(cmd, shell=True, stdout=fnull, stderr=subprocess.STDOUT)
        result = "SUCCESS"
    except Exception as ex:
        result = "COMMAND FAILED! : {0} : {1}".format(cmd, ex)

    return result


# def open_sql_file(file_name, settings):
#     sql = open(os.path.join(settings['sql_dir'], file_name), "r").read()
#     return prep_sql(sql, settings)
#
#
# # change schema names in an array of SQL script if schemas not the default
# def prep_sql_list(sql_list, settings):
#     output_list = []
#     for sql in sql_list:
#         output_list.append(prep_sql(sql, settings))
#     return output_list


# # set schema names in the SQL script
# def prep_sql(sql, settings):
#
#     if settings['raw_gnaf_schema'] is not None:
#         sql = sql.replace(" raw_gnaf.", " {0}.".format(settings['raw_gnaf_schema'], ))
#     if settings['raw_admin_bdys_schema'] is not None:
#         sql = sql.replace(" raw_admin_bdys.", " {0}.".format(settings['raw_admin_bdys_schema'], ))
#     if settings['gnaf_schema'] is not None:
#         sql = sql.replace(" gnaf.", " {0}.".format(settings['gnaf_schema'], ))
#     if settings['admin_bdys_schema'] is not None:
#         sql = sql.replace(" admin_bdys.", " {0}.".format(settings['admin_bdys_schema'], ))
#
#     if settings['pg_user'] != "postgres":
#         # alter create table script to run with correct Postgres user name
#         sql = sql.replace(" postgres;", " {0};".format(settings['pg_user'], ))
#
#     return sql


def split_sql_into_list(pg_cur, the_sql, table_schema, table_name, table_alias, table_gid, settings, logger):
    # get min max gid values from the table to split
    min_max_sql = "SELECT MIN({2}) AS min, MAX({2}) AS max FROM {0}.{1}".format(table_schema, table_name, table_gid)

    pg_cur.execute(min_max_sql)

    try:
        result = pg_cur.fetchone()

        min_pkey = int(result[0])
        max_pkey = int(result[1])
        diff = max_pkey - min_pkey

        # Number of records in each query
        rows_per_request = int(math.floor(float(diff) / float(settings['max_concurrent_processes']))) + 1

        # If less records than processes or rows per request,
        # reduce both to allow for a minimum of 15 records each process
        if float(diff) / float(settings['max_concurrent_processes']) < 10.0:
            rows_per_request = 10
            processes = int(math.floor(float(diff) / 10.0)) + 1
            logger.info("\t\t- running {0} processes (adjusted due to low row count in table to split)"
                        .format(processes))
        else:
            processes = settings['max_concurrent_processes']

        # create list of sql statements to run with multiprocessing
        sql_list = []
        start_pkey = min_pkey - 1

        for i in range(0, processes):
            end_pkey = start_pkey + rows_per_request

            where_clause = " WHERE {0}.{3} > {1} AND {0}.{3} <= {2}"\
                .format(table_alias, start_pkey, end_pkey, table_gid)

            if "WHERE " in the_sql:
                mp_sql = the_sql.replace(" WHERE ", where_clause + " AND ")
            elif "GROUP BY " in the_sql:
                mp_sql = the_sql.replace("GROUP BY ", where_clause + " GROUP BY ")
            elif "ORDER BY " in the_sql:
                mp_sql = the_sql.replace("ORDER BY ", where_clause + " ORDER BY ")
            else:
                if ";" in the_sql:
                    mp_sql = the_sql.replace(";", where_clause + ";")
                else:
                    mp_sql = the_sql + where_clause
                    logger.warning("\t\t- NOTICE: no ; found at the end of the SQL statement")

            sql_list.append(mp_sql)
            start_pkey = end_pkey

        # logger.info('\n'.join(sql_list))

        return sql_list
    except Exception as ex:
        logger.fatal("Looks like the table in this query is empty: {0}\n{1}".format(min_max_sql, ex))
        return None


def check_python_version(logger):
    # get python and psycopg2 version
    python_version = sys.version.split("(")[0].strip()
    psycopg2_version = psycopg2.__version__.split("(")[0].strip()
    os_version = platform.system() + " " + platform.version().strip()

    # logger.info("")
    logger.info("\t- running Python {0} with Psycopg2 {1}"
                .format(python_version, psycopg2_version))
    logger.info("\t- on {0}".format(os_version))


def check_postgis_version(pg_cur, settings, logger):
    # get Postgres, PostGIS & GEOS versions
    pg_cur.execute("SELECT version()")
    pg_version = pg_cur.fetchone()[0].replace("PostgreSQL ", "").split(",")[0]
    pg_cur.execute("SELECT PostGIS_full_version()")
    lib_strings = pg_cur.fetchone()[0].replace("\"", "").split(" ")
    postgis_version = "UNKNOWN"
    postgis_version_num = 0.0
    geos_version = "UNKNOWN"
    geos_version_num = 0.0
    settings['st_subdivide_supported'] = False
    for lib_string in lib_strings:
        if lib_string[:8] == "POSTGIS=":
            postgis_version = lib_string.replace("POSTGIS=", "")
            postgis_version_num = float(postgis_version[:3])
        if lib_string[:5] == "GEOS=":
            geos_version = lib_string.replace("GEOS=", "")
            geos_version_num = float(geos_version[:3])
    if postgis_version_num >= 2.2 and geos_version_num >= 3.5:
        settings['st_subdivide_supported'] = True
    logger.info("\t- using Postgres {0} and PostGIS {1} (with GEOS {2})"
                .format(pg_version, postgis_version, geos_version))


def multiprocess_shapefile_load(work_list, settings, logger):
    pool = multiprocessing.Pool(processes=settings['max_concurrent_processes'])

    num_jobs = len(work_list)

    results = pool.imap_unordered(intermediate_shapefile_load_step, [[w, settings] for w in work_list])

    pool.close()
    pool.join()

    result_list = list(results)
    num_results = len(result_list)

    if num_jobs > num_results:
        logger.warning("\t- A MULTIPROCESSING PROCESS FAILED WITHOUT AN ERROR\nACTION: Check the record counts")

    for result in result_list:
        if result != "SUCCESS":
            logger.info(result)


def intermediate_shapefile_load_step(args):
    work_dict = args[0]
    settings = args[1]
    # logger = args[2]

    file_path = work_dict['file_path']
    pg_table = work_dict['pg_table']
    pg_schema = work_dict['pg_schema']
    delete_table = work_dict['delete_table']
    spatial = work_dict['spatial']

    pg_conn = psycopg2.connect(settings['pg_connect_string'])
    pg_conn.autocommit = True
    pg_cur = pg_conn.cursor()

    result = import_shapefile_to_postgres(pg_cur, file_path, pg_table, pg_schema, delete_table, spatial)

    return result


# imports a Shapefile into Postgres in 2 steps: SHP > SQL; SQL > Postgres
# overcomes issues trying to use psql with PGPASSWORD set at runtime
def import_shapefile_to_postgres(pg_cur, file_path, pg_table, pg_schema, delete_table, spatial):

    # delete target table or append to it?
    if delete_table:
        delete_append_flag = "-d"
    else:
        delete_append_flag = "-a"

    # assign coordinate system if spatial, otherwise flag as non-spatial
    if spatial:
        spatial_or_dbf_flags = "-s 4283 -I"
    else:
        spatial_or_dbf_flags = "-G -n"

    # build shp2pgsql command line
    shp2pgsql_cmd = "shp2pgsql {0} {1} -i \"{2}\" {3}.{4}"\
        .format(delete_append_flag, spatial_or_dbf_flags, file_path, pg_schema, pg_table)
    # print(shp2pgsql_cmd)

    # convert the Shapefile to SQL statements
    try:
        process = subprocess.Popen(shp2pgsql_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        sql_obj, err = process.communicate()
    except:
        return "Importing {0} - Couldn't convert Shapefile to SQL".format(file_path)

    # prep Shapefile SQL
    sql = sql_obj.decode("utf-8")  # this is required for Python 3
    sql = sql.replace("Shapefile type: ", "-- Shapefile type: ")
    sql = sql.replace("Postgis type: ", "-- Postgis type: ")
    sql = sql.replace("SELECT DropGeometryColumn", "-- SELECT DropGeometryColumn")

    # bug in shp2pgsql? - an append command will still create a spatial index if requested - disable it
    if not delete_table or not spatial:
        sql = sql.replace("CREATE INDEX ", "-- CREATE INDEX ")

    # this is required due to differing approaches by different versions of PostGIS
    sql = sql.replace("DROP TABLE ", "DROP TABLE IF EXISTS ")
    sql = sql.replace("DROP TABLE IF EXISTS IF EXISTS ", "DROP TABLE IF EXISTS ")

    # import data to Postgres
    try:
        pg_cur.execute(sql)
    except:
        # if import fails for some reason - output sql to file for debugging
        target = open(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'test.sql'), "w")
        target.write(sql)

        return "\tImporting {0} - Couldn't run Shapefile SQL\nshp2pgsql result was: {1} ".format(file_path, err)

    # Cluster table on spatial index for performance
    if delete_table and spatial:
        sql = "ALTER TABLE {0}.{1} CLUSTER ON {1}_geom_idx".format(pg_schema, pg_table)

        try:
            pg_cur.execute(sql)
        except:
            return "\tImporting {0} - Couldn't cluster on spatial index".format(pg_table)

    return "SUCCESS"
