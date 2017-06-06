#!/usr/bin/env python
# -*- coding: utf-8 -*-

# *********************************************************************************************************************
# load-census.py
# *********************************************************************************************************************
#
# A script for loading Australian Bureau of Statistics Census 2016 data and boundaries
#
# Author: Hugh Saalmans
# GitHub: minus34
# Twitter: @minus34
#
# Copyright:
#  - Code is licensed under an Apache License, version 2.0
#  - Data is copyright ABS - licensed under a Creative Commons (By Attribution) license.
#    See http://abs.gov.au for the correct attribution

# Process:
#   1. 
#
# *********************************************************************************************************************

import io
import logging.config
import os
import pandas  # module needs to be installed (IMPORTANT: need to install 'xlrd' module for Pandas to read .xlsx files)
import psycopg2  # module needs to be installed
import utils

from datetime import datetime


def main():
    full_start_time = datetime.now()

    # set command line arguments
    args = utils.set_arguments()

    # get settings from arguments
    settings = utils.get_settings(args)

    if settings is None:
        logger.fatal("Invalid Census Year\nACTION: Set value to 2011 or 2016")
        return False

    # connect to Postgres
    try:
        pg_conn = psycopg2.connect(settings['pg_connect_string'])
    except psycopg2.Error:
        logger.fatal("Unable to connect to database\nACTION: Check your Postgres parameters and/or database security")
        return False

    pg_conn.autocommit = True
    pg_cur = pg_conn.cursor()

    # add postgis to database (in the public schema) - run this in a try to confirm db user has privileges
    try:
        pg_cur.execute("SET search_path = public, pg_catalog; CREATE EXTENSION IF NOT EXISTS postgis")
    except psycopg2.Error:
        logger.fatal("Unable to add PostGIS extension\nACTION: Check your Postgres user privileges or PostGIS install")
        return False

    # test if ST_SubDivide exists (only in PostGIS 2.2+). It's used to split boundaries for faster processing
    utils.check_postgis_version(pg_cur, settings, logger)

    # START LOADING DATA

    # test runtime parameters:
    # --census-year=2011
    # --data-schema=census_2011_data
    # --boundary-schema=census_2011_bdys
    # --web-schema=census_2011_web
    # --census-data-path=/Users/hugh.saalmans/tmp/abs_census_2011_data
    # --census-bdys-path=/Users/hugh.saalmans/minus34/data/abs_2011

    # # PART 1 - load census data from CSV files
    # logger.info("")
    # start_time = datetime.now()
    # logger.info("Part 1 of 2 : Start census data load : {0}".format(start_time))
    # create_metadata_tables(pg_cur, settings['metadata_file_prefix'], settings['metadata_file_type'], settings)
    # populate_data_tables(settings['data_file_prefix'], settings['data_file_type'],
    #                      settings['table_name_part'], settings['bdy_name_part'], settings)
    # logger.info("Part 1 of 2 : Census data loaded! : {0}".format(datetime.now() - start_time))

    # PART 2 - load census boundaries from Shapefiles
    logger.info("")
    start_time = datetime.now()
    logger.info("Part 2 of 2 : Start census boundary load : {0}".format(start_time))
    # load_boundaries(pg_cur, settings)
    create_display_boundaries(pg_cur, settings)
    logger.info("Part 2 of 2 : Census boundaries loaded! : {0}".format(datetime.now() - start_time))

    # close Postgres connection
    pg_cur.close()
    pg_conn.close()

    logger.info("")
    logger.info("Total time : : {0}".format(datetime.now() - full_start_time))

    return True


def create_metadata_tables(pg_cur, prefix, suffix, settings):
    # Step 1 of 2 : create metadata tables from Census Excel spreadsheets
    start_time = datetime.now()

    # create schema
    if settings['data_schema'] != "public":
        pg_cur.execute("CREATE SCHEMA IF NOT EXISTS {0} AUTHORIZATION {1}"
                       .format(settings['data_schema'], settings['pg_user']))

    # create metadata tables
    sql = "DROP TABLE IF EXISTS {0}.metadata_tables CASCADE;" \
          "CREATE TABLE {0}.metadata_tables (table_number text, table_name text, table_description text) " \
          "WITH (OIDS=FALSE);" \
          "ALTER TABLE {0}.metadata_tables OWNER TO {1}".format(settings['data_schema'], settings['pg_user'])
    pg_cur.execute(sql)

    sql = "DROP TABLE IF EXISTS {0}.metadata_stats CASCADE;" \
          "CREATE TABLE {0}.metadata_stats (sequential_id text, short_id text, long_id text, " \
          "table_number text, profile_table text, column_heading_description text) " \
          "WITH (OIDS=FALSE);" \
          "ALTER TABLE {0}.metadata_stats OWNER TO {1}".format(settings['data_schema'], settings['pg_user'])
    pg_cur.execute(sql)

    # get a list of all files matching the metadata filename prefix
    file_list = list()

    for root, dirs, files in os.walk(settings['data_directory']):
        for file_name in files:
            if file_name.lower().startswith(prefix.lower()):
                if file_name.lower().endswith(suffix.lower()):
                    file_path = os.path.join(root, file_name)

                    file_dict = dict()
                    file_dict["name"] = file_name
                    file_dict["path"] = file_path

                    file_list.append(file_dict)

    # are there any files to load?
    if len(file_list) == 0:
        logger.fatal("No Census metadata XLS files found\nACTION: Check your '--census-data-path' value")
        logger.fatal("\t- Step 1 of 4 : create metadata tables FAILED!")
    else:
        # read in excel worksheets into pandas dataframes
        for file_dict in file_list:

            xl = pandas.ExcelFile(file_dict["path"])

            sheets = xl.sheet_names
            i = 0

            for table_dict in settings["census_metadata_dicts"]:

                df = xl.parse(sheets[i])

                # drop unwanted rows at the top
                j = 0
                first_row = False

                while not first_row:
                    cell = df.iloc[j, 0]

                    if str(cell).lower() == table_dict["first_row"]:
                        df_clean = df.drop(df.index[0:j+1])
                        first_row = True

                        # drop excess columns in unclean Excel worksheets
                        if table_dict["table"] == "metadata_stats":
                            try:
                                df_clean.drop(df.columns[[6, 7, 8]], axis=1, inplace=True)
                            except:
                                pass

                        # export to in-memory tab delimited text file
                        tsv_file = io.StringIO()
                        df_clean.to_csv(tsv_file, sep="\t", index=False, header=False)
                        tsv_file.seek(0)  # move position back to beginning of file before reading

                        # # import into Postgres
                        # pg_cur.copy_from(tsv_file, "{0}.{1}"
                        #                  .format(settings['data_schema'], table_dict["table"]),
                        #                  sep="\t", null="")
                        sql = "COPY {0}.{1} FROM stdin WITH CSV DELIMITER as '\t' NULL as ''" \
                            .format(settings['data_schema'], table_dict["table"])
                        pg_cur.copy_expert(sql, tsv_file)

                    j += 1

                i += 1

            logger.info("\t\t- imported {0}".format(file_dict["name"]))

    # clean up invalid rows
    pg_cur.execute("DELETE FROM {0}.metadata_tables WHERE table_number IS NULL".format(settings['data_schema']))

    # # get rid of _Persons_Persons and replace with _Persons in metadata_stats - can't do this as it reorders the rows
    # pg_cur.execute("UPDATE {0}.metadata_stats "
    #                "SET long_id = replace(long_id, '_Persons_Persons', '_Persons') "
    #                "WHERE long_id LIKE '%_Persons_Persons'".format(settings['data_schema']))

    # add primary keys
    pg_cur.execute("ALTER TABLE {0}.metadata_tables ADD CONSTRAINT metadata_tables_pkey PRIMARY KEY (table_number)"
                   .format(settings['data_schema']))
    pg_cur.execute("ALTER TABLE {0}.metadata_stats ADD CONSTRAINT metadata_stats_pkey PRIMARY KEY (sequential_id)"
                   .format(settings['data_schema']))

    # cluster tables on primary key (for minor performance improvement)
    pg_cur.execute("ALTER TABLE {0}.metadata_tables CLUSTER ON metadata_tables_pkey".format(settings['data_schema']))
    pg_cur.execute("ALTER TABLE {0}.metadata_stats CLUSTER ON metadata_stats_pkey".format(settings['data_schema']))

    # # add cell type field to cells table
    # pg_cur.execute("ALTER TABLE {0}.metadata_stats ADD COLUMN stat_type text".format(settings['data_schema']))

    # populate cell type field
    # pg_cur.execute("UPDATE {0}.metadata_stats "
    #                "SET stat_type = 'double precision' "
    #                "WHERE lower(long_id) like '%median%' "
    #                "OR lower(long_id) like '%average%' "
    #                "OR lower(long_id) like '%percent%' "
    #                "OR lower(long_id) like '%proportion%' "
    #                .format(settings['data_schema']))
    #
    # pg_cur.execute("UPDATE {0}.metadata_stats "
    #                "SET stat_type = 'integer' "
    #                "WHERE stat_type IS NULL"
    #                .format(settings['data_schema']))

    # pg_cur.execute("UPDATE {0}.metadata_stats "
    #                "SET stat_type = 'double precision'".format(settings['data_schema']))

    # update stats
    pg_cur.execute("VACUUM ANALYZE {0}.metadata_tables".format(settings['data_schema']))
    pg_cur.execute("VACUUM ANALYZE {0}.metadata_stats".format(settings['data_schema']))

    logger.info("\t- Step 1 of 2 : metadata tables created : {0}".format(datetime.now() - start_time))


# create stats tables and import data from CSV files using multiprocessing
def populate_data_tables(prefix, suffix, table_name_part, bdy_name_part, settings):
    # Step 2 of 2 : create & populate stats tables with CSV files using multiprocessing
    start_time = datetime.now()

    # get the file list and create sql copy statements
    file_list = []
    # get a dictionary of all files matching the filename prefix
    for root, dirs, files in os.walk(settings['data_directory']):
        for file_name in files:
            if file_name.lower().startswith(prefix.lower()):
                if file_name.lower().endswith(suffix.lower()):

                    file_path = os.path.join(root, file_name)
                    file_name_components = file_name.lower().split("_")

                    table = file_name_components[table_name_part]
                    boundary = file_name_components[bdy_name_part]

                    # manual fix for the Australia wide data - has a different file name structure
                    if "." in boundary:
                        boundary = "aust"

                    file_dict = dict()
                    file_dict["path"] = file_path
                    file_dict["table"] = table
                    file_dict["boundary"] = boundary

                    # if boundary == "ced":  # for testing
                    file_list.append(file_dict)

    # are there any files to load?
    if len(file_list) == 0:
        logger.fatal("No Census data CSV files found\nACTION: Check your '--census-data-path' value")
        logger.fatal("\t- Step 2 of 2 : stats table create & populate FAILED!")
    else:
        # load all files using multiprocessing
        utils.multiprocess_csv_import(file_list, settings, logger)
        logger.info("\t- Step 2 of 2 : stats tables created & populated : {0}".format(datetime.now() - start_time))


# loads the admin bdy shapefiles using the shp2pgsql command line tool (part of PostGIS), using multiprocessing
def load_boundaries(pg_cur, settings):
    # Step 1 of 2 : load census boundaries
    start_time = datetime.now()

    # create schema
    if settings['boundary_schema'] != "public":
        pg_cur.execute("CREATE SCHEMA IF NOT EXISTS {0} AUTHORIZATION {1}"
                       .format(settings['boundary_schema'], settings['pg_user']))

    # get file list
    table_list = list()
    create_list = list()
    append_list = list()

    # get a dictionary of Shapefile paths
    for root, dirs, files in os.walk(settings['boundaries_local_directory']):
        for file_name in files:
            file_name = file_name.lower()

            if file_name.endswith(".shp"):
                file_dict = dict()
                file_dict['file_path'] = os.path.join(root, file_name)

                if file_name.startswith("mb_"):
                    for state in settings['states']:
                        state = state.lower()

                        if state in file_name:
                            file_dict['pg_table'] = file_name.replace("_" + state + ".shp", "_aust", 1)
                else:
                    file_dict['pg_table'] = file_name.replace(".shp", "")

                file_dict['pg_schema'] = settings['boundary_schema']

                # set to replace or append to table depending on whether this is the 1st state for that dataset
                # (only applies to meshblocks in Census 2016)
                table_list_add = False

                if file_dict['pg_table'] not in table_list:
                    table_list_add = True

                    file_dict['delete_table'] = True
                else:
                    file_dict['delete_table'] = False

                file_dict['spatial'] = True

                if table_list_add:
                    table_list.append(file_dict['pg_table'])
                    create_list.append(file_dict)
                else:
                    append_list.append(file_dict)

    # logger.info(create_list)
    # logger.info(append_list)

    # are there any files to load?
    if len(create_list) == 0:
        logger.fatal("No census boundary files found\nACTION: Check your 'census-bdys-path' argument")
    else:
        # load files in separate processes
        utils.multiprocess_shapefile_load(create_list, settings, logger)

        # Run the appends one at a time (Can't multi process as large sets of parallel INSERTs cause database deadlocks)
        # utils.multiprocess_shapefile_load(append_list, settings, logger)
        for shp in append_list:
            utils.import_shapefile_to_postgres(pg_cur, shp['file_path'], shp['pg_table'], shp['pg_schema'],
                                               shp['delete_table'], True)

        logger.info("\t- Step 1 of 2 : boundaries loaded : {0}".format(datetime.now() - start_time))


def create_display_boundaries(pg_cur, settings):
    # Step 2 of 2 : create web optimised versions of the census boundaries
    start_time = datetime.now()

    # create schema
    if settings['web_schema'] != "public":
        pg_cur.execute("CREATE SCHEMA IF NOT EXISTS {0} AUTHORIZATION {1}"
                       .format(settings['web_schema'], settings['pg_user']))

    # prepare boundaries for all tiled map zoom levels
    create_sql_list = list()
    insert_sql_list = list()
    vacuum_sql_list = list()

    for boundary_dict in settings['bdy_table_dicts']:
        boundary_name = boundary_dict["boundary"]

        if boundary_name != "mb":
            id_field = boundary_dict["id_field"]
            name_field = boundary_dict["name_field"]
            area_field = boundary_dict["area_field"]

            input_pg_table = "{0}_{1}_aust".format(boundary_name, settings["census_year"])
            pg_table = "{0}".format(boundary_name)

            # build create table statement
            create_table_list = list()
            create_table_list.append("DROP TABLE IF EXISTS {0}.{1} CASCADE;")
            create_table_list.append("CREATE TABLE {0}.{1} (")

            # build column list
            column_list = list()
            column_list.append("id text NOT NULL PRIMARY KEY")
            column_list.append("name text NOT NULL")
            column_list.append("area double precision NOT NULL")
            column_list.append("population double precision NOT NULL")
            column_list.append("geom geometry(MultiPolygon, 4283) NULL")

            for zoom_level in range(4, 18):
                display_zoom = str(zoom_level).zfill(2)
                column_list.append("geojson_{0} jsonb NOT NULL".format(display_zoom))

            # add columns to create table statement and finish it
            create_table_list.append(",".join(column_list))
            create_table_list.append(") WITH (OIDS=FALSE);")
            create_table_list.append("ALTER TABLE {0}.{1} OWNER TO {2};")
            create_table_list.append("CREATE INDEX {1}_geom_idx ON {0}.{1} USING gist (geom);")
            create_table_list.append("ALTER TABLE {0}.{1} CLUSTER ON {1}_geom_idx")

            sql = "".join(create_table_list).format(settings['web_schema'], pg_table, settings['pg_user'])
            create_sql_list.append(sql)

            # get population field and table
            if boundary_name[:1] == "i":
                pop_stat = "i3"
                pop_table = "i01a"
            elif settings["census_year"] == "2011":
                pop_stat = "b3"
                pop_table = "b01"
            else:
                pop_stat = "g3"
                pop_table = "g01"

            # build insert statement
            insert_into_list = list()
            insert_into_list.append("INSERT INTO {0}.{1}".format(settings['web_schema'], pg_table))
            insert_into_list.append("SELECT bdy.{0} AS id, {1} AS name, SUM(bdy.{2}) AS area, tab.{3} AS population,"
                                    .format(id_field, name_field, area_field, pop_stat))

            # thin geometry to make querying faster
            tolerance = utils.get_tolerance(10)
            insert_into_list.append(
                "ST_Transform(ST_Multi(ST_Union(ST_SimplifyVW(ST_Transform(geom, 3577), {0}))), 4283),"
                    .format(tolerance,))

            # create statements for geojson optimised for each zoom level
            geojson_list = list()

            for zoom_level in range(4, 18):
                # thin geometries to a default tolerance per zoom level
                tolerance = utils.get_tolerance(zoom_level)
                # trim coords to only the significant ones
                decimal_places = utils.get_decimal_places(zoom_level)

                geojson_list.append("ST_AsGeoJSON(ST_Transform(ST_Multi(ST_Union(ST_SimplifyVW(ST_Transform("
                                        "bdy.geom, 3577), {0}))), 4283), {1})::jsonb".format(tolerance, decimal_places))

            insert_into_list.append(",".join(geojson_list))
            insert_into_list.append("FROM {0}.{1} AS bdy".format(settings['boundary_schema'], input_pg_table))
            insert_into_list.append("INNER JOIN {0}.{1}_{2} AS tab".format(settings['data_schema'], boundary_name, pop_table))
            insert_into_list.append("ON bdy.{0} = tab.{1}".format(id_field, settings["region_id_field"]))
            insert_into_list.append("WHERE bdy.geom IS NOT NULL")
            insert_into_list.append("GROUP BY {0}, {1}, {2}".format(id_field, name_field, pop_stat))

            sql = " ".join(insert_into_list)
            insert_sql_list.append(sql)

            vacuum_sql_list.append("VACUUM ANALYZE {0}.{1}".format(settings['web_schema'], pg_table))

    utils.multiprocess_list("sql", create_sql_list, settings, logger)
    utils.multiprocess_list("sql", insert_sql_list, settings, logger)
    utils.multiprocess_list("sql", vacuum_sql_list, settings, logger)

    logger.info("\t- Step 2 of 2 : web optimised boundaries created : {0}".format(datetime.now() - start_time))


if __name__ == '__main__':
    logger = logging.getLogger()

    # set logger
    log_file = os.path.abspath(__file__).replace(".py", ".log")
    logging.basicConfig(filename=log_file, level=logging.DEBUG, format="%(asctime)s %(message)s",
                        datefmt="%m/%d/%Y %I:%M:%S %p")

    # setup logger to write to screen as well as writing to log file
    # define a Handler which writes INFO messages or higher to the sys.stderr
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    # set a format which is simpler for console use
    formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
    # tell the handler to use this format
    console.setFormatter(formatter)
    # add the handler to the root logger
    logging.getLogger('').addHandler(console)

    logger.info("")
    logger.info("Start census-loader")
    utils.check_python_version(logger)

    if main():
        logger.info("Finished successfully!")
    else:
        logger.fatal("Something bad happened!")

    logger.info("")
    logger.info("-------------------------------------------------------------------------------")
