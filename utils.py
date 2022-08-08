#!/usr/bin/env python
# -*- coding: utf-8 -*-

import io
import multiprocessing
import math
import os
import platform
import psycopg2
import subprocess
import sys


# calculates the area tolerance (in m2) for vector simplification using the Visvalingam-Whyatt algorithm
def get_tolerance(zoom_level):

    # pixels squared factor
    tolerance_square_pixels = 7

    # default Google/Bing map tile scales
    metres_per_pixel = 156543.03390625 / math.pow(2.0, float(zoom_level + 1))

    # the tolerance (metres) for vector simplification using the VW algorithm
    square_metres_per_pixel = math.pow(metres_per_pixel, 2.0)

    # tolerance to use
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

    # get the census fields to use in the create table statement
    field_list = list()

    # select the field ordered by sequential_id (required to match field names with the right data)
    sql = "SELECT sequential_id || ' double precision' AS field " \
          "FROM {0}.metadata_stats " \
          "WHERE lower(table_number) LIKE '{1}%' " \
          "ORDER BY table_number, right(sequential_id, length(sequential_id) - 1)::integer " \
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

        # clean whitespace and rogue non-ascii characters
        clean_string = raw_string.lstrip().rstrip().replace(" ", "").replace("\x1A", "")

        # convert to in memory stream
        csv_file = io.StringIO(clean_string)
        csv_file.seek(0)  # move position back to beginning of file before reading

        # import into Postgres
        sql = "COPY {0}.{1} FROM stdin WITH CSV HEADER DELIMITER as ',' NULL as '..'" \
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

            where_clause = " WHERE {0}.{3} > {1} AND {0}.{3} <= {2}" \
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
    settings['st_clusterkmeans_supported'] = False
    for lib_string in lib_strings:
        if lib_string[:8] == "POSTGIS=":
            postgis_version = lib_string.replace("POSTGIS=", "")
            postgis_version_num = float(postgis_version[:3])
        if lib_string[:5] == "GEOS=":
            geos_version = lib_string.replace("GEOS=", "")
            geos_version_num = float(geos_version[:3])
    if postgis_version_num >= 2.2 and geos_version_num >= 3.5:
        settings['st_clusterkmeans_supported'] = True
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
    shp2pgsql_cmd = "shp2pgsql {0} {1} -i \"{2}\" {3}.{4}" \
        .format(delete_append_flag, spatial_or_dbf_flags, file_path, pg_schema, pg_table)
    # print(shp2pgsql_cmd)

    # convert the Shapefile to SQL statements
    try:
        process = subprocess.Popen(shp2pgsql_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        sql_obj, err = process.communicate()
    except:
        return "Importing {0} - Couldn't convert Shapefile to SQL".format(file_path)

    # print("SQL object is this long: {}".format(len(sql_obj)))
    # print("Error is: {}".format(err))

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
        target = open(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'fail_{}.sql'.format(pg_table)), "w")
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


# print(get_tolerance(13))

