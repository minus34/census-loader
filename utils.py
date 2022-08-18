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
def multiprocess_csv_import(work_list, max_concurrent_processes, pg_connect_string,
                            data_schema, pg_user, region_id_field, logger):

    pool = multiprocessing.Pool(processes=max_concurrent_processes)

    num_jobs = len(work_list)

    results = pool.imap_unordered(run_csv_import_multiprocessing,
                                  [[w, pg_connect_string, data_schema, pg_user, region_id_field] for w in work_list])

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
    pg_connect_string = args[1]
    data_schema = args[2]
    pg_user = args[3]
    region_id_field = args[4]

    pg_conn = psycopg2.connect(pg_connect_string)
    pg_conn.autocommit = True
    pg_cur = pg_conn.cursor()

    # CREATE TABLE

    # get the census fields to use in the create table statement
    field_list = list()

    # select the field ordered by sequential_id (required to match field names with the right data)
    sql = f"""SELECT sequential_id || ' double precision' AS field
              FROM {data_schema}.metadata_stats
              WHERE lower(table_number) LIKE '{file_dict["table"]}%'
              ORDER BY table_number, right(sequential_id, length(sequential_id) - 1)::integer"""
    pg_cur.execute(sql)

    fields = pg_cur.fetchall()

    for field in fields:
        field_list.append(field[0].lower())

    fields_string = ",".join(field_list)

    # create the table
    table_name = file_dict["boundary"] + "_" + file_dict["table"]

    create_table_sql = f"""DROP TABLE IF EXISTS {data_schema}.{table_name} CASCADE;
                           CREATE TABLE {data_schema}.{table_name} (
                               {region_id_field} text,
                               {fields_string}
                           ) WITH (OIDS=FALSE);
                           ALTER TABLE {data_schema}.{table_name} OWNER TO {pg_user}"""
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
        sql = f"COPY {data_schema}.{table_name} FROM stdin WITH CSV HEADER DELIMITER as ',' NULL as '..'"
        pg_cur.copy_expert(sql, csv_file)

    except Exception as ex:
        return f"IMPORT CSV INTO POSTGRES FAILED! : {file_dict['path']} : {ex}"

    # add primary key and vacuum index
    sql = f"""ALTER TABLE {data_schema}.{table_name} ADD CONSTRAINT {table_name}_pkey PRIMARY KEY ({region_id_field});
              ALTER TABLE {data_schema}.{table_name} CLUSTER ON {table_name}_pkey"""
    pg_cur.execute(sql)

    pg_cur.execute(f"VACUUM ANALYSE {data_schema}.{table_name}")

    result = "SUCCESS"

    pg_cur.close()
    pg_conn.close()

    return result


# takes a list of sql queries or command lines and runs them using multiprocessing
def multiprocess_list(mp_type, work_list, max_concurrent_processes, pg_connect_string, logger):
    pool = multiprocessing.Pool(processes=max_concurrent_processes)

    num_jobs = len(work_list)

    if mp_type == "sql":
        results = pool.imap_unordered(run_sql_multiprocessing, [[w, pg_connect_string] for w in work_list])
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
    pg_connect_string = args[1]

    pg_conn = psycopg2.connect(pg_connect_string)
    pg_conn.autocommit = True
    pg_cur = pg_conn.cursor()

    # # set raw gnaf database schema (it's needed for the primary and foreign key creation)
    # if raw_gnaf_schema != "public":
    #     pg_cur.execute(f"SET search_path = {raw_gnaf_schema}, public, pg_catalog")

    try:
        pg_cur.execute(the_sql)
        result = "SUCCESS"
    except Exception as ex:
        result = f"SQL FAILED! : {the_sql} : {ex}"

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
        result = f"COMMAND FAILED! : {cmd} : {ex}"

    return result


def split_sql_into_list(pg_cur, the_sql, table_schema, table_name, table_alias, table_gid,
                        max_concurrent_processes, logger):
    # get min max gid values from the table to split
    min_max_sql = f"SELECT MIN({table_gid}) AS min, MAX({table_gid}) AS max FROM {table_schema}.{table_name}"

    pg_cur.execute(min_max_sql)

    try:
        result = pg_cur.fetchone()

        min_pkey = int(result[0])
        max_pkey = int(result[1])
        diff = max_pkey - min_pkey

        # Number of records in each query
        rows_per_request = int(math.floor(float(diff) / float(max_concurrent_processes))) + 1

        # If less records than processes or rows per request,
        # reduce both to allow for a minimum of 15 records each process
        if float(diff) / float(max_concurrent_processes) < 10.0:
            rows_per_request = 10
            processes = int(math.floor(float(diff) / 10.0)) + 1
            logger.info(f"\t\t- running {processes} processes (adjusted due to low row count in table to split)")
        else:
            processes = max_concurrent_processes

        # create list of sql statements to run with multiprocessing
        sql_list = []
        start_pkey = min_pkey - 1

        for i in range(0, processes):
            end_pkey = start_pkey + rows_per_request

            where_clause = f""" WHERE {table_alias}.{table_gid} > {start_pkey} 
                                    AND {table_alias}.{table_gid} <= {end_pkey}"""

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
        logger.fatal(f"Looks like the table in this query is empty: {min_max_sql}\n{ex}")
        return None


def multiprocess_shapefile_load(work_list, max_concurrent_processes, pg_connect_string, logger):
    pool = multiprocessing.Pool(processes=max_concurrent_processes)

    num_jobs = len(work_list)

    results = pool.imap_unordered(intermediate_shapefile_load_step,
                                  [[w, pg_connect_string] for w in work_list])

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
    pg_connect_string = args[1]
    # logger = args[2]

    file_path = work_dict["file_path"]
    pg_table = work_dict["pg_table"]
    pg_schema = work_dict["pg_schema"]
    delete_table = work_dict["delete_table"]
    spatial = work_dict["spatial"]

    pg_conn = psycopg2.connect(pg_connect_string)
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
    shp2pgsql_cmd = f"shp2pgsql {delete_append_flag} {spatial_or_dbf_flags} -i \"{file_path}\" {pg_schema}.{pg_table}"
    # print(shp2pgsql_cmd)

    # convert the Shapefile to SQL statements
    try:
        process = subprocess.Popen(shp2pgsql_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        sql_obj, err = process.communicate()
    except:
        return f"Importing {file_path} - Couldn't convert Shapefile to SQL"

    # print(f"SQL object is this long: {len(sql_obj)}")
    # print(f"Error is: {err}")

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
        target = open(os.path.join(os.path.dirname(os.path.realpath(__file__)), f"fail_{pg_table}.sql"), "w")
        target.write(sql)

        return f"\tImporting {file_path} - Couldn't run Shapefile SQL\nshp2pgsql result was: {err} "

    # Cluster table on spatial index for performance
    if delete_table and spatial:
        sql = f"ALTER TABLE {pg_schema}.{pg_table} CLUSTER ON {pg_table}_geom_idx"

        try:
            pg_cur.execute(sql)
        except:
            return f"\tImporting {pg_table} - Couldn't cluster on spatial index"

    return "SUCCESS"


# print(get_tolerance(13))

