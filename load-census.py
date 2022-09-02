#!/usr/bin/env python
# -*- coding: utf-8 -*-

# *********************************************************************************************************************
# load-census.py
# *********************************************************************************************************************
#
# A script for loading Australian Bureau of Statistics Census 2021 data and boundaries
#
# Author: Hugh Saalmans
# GitHub: minus34
# Twitter: @minus34
#
# Copyright:
#  - Code is licensed under an Apache License, version 2.0
#  - Data is copyright ABS - licensed under Creative Commons (By Attribution) license.
#    See http://abs.gov.au for correct attribution

# Process:
#   1. loads census metadata Excel files using Pandas dataframes
#   2. loads all census data CSV files
#   3. loads census boundary Shapefiles (if 2011 or 2016 Census, 2021 loaded using GDAL ogr2ogr command line)
#   4. creates web display optimised census boundaries using Visvalingam-Whyatt simplification
#   5. go to the web folder and fire up the map server
#   6. party on!
#
# *********************************************************************************************************************

import io
import logging.config
import os
import pandas  # module needs to be installed, along with openpyxl (for Excel file load)
import psycopg  # module needs to be installed
import settings
import utils

from datetime import datetime


def main():
    full_start_time = datetime.now()

    # log Python and OS versions
    logger.info(f"\t- running Python {settings.python_version} with Psycopg {settings.psycopg_version}")
    logger.info(f"\t- on {settings.os_version}")

    # get Postgres connection & cursor
    pg_conn = psycopg.connect(settings.pg_connect_string)
    pg_conn.autocommit = True
    pg_cur = pg_conn.cursor()

    # add postgis to database (in the public schema) - run this in a try to confirm db user has privileges
    try:
        pg_cur.execute("SET search_path = public, pg_catalog; CREATE EXTENSION IF NOT EXISTS postgis")
    except psycopg.Error:
        logger.fatal("Unable to add PostGIS extension\nACTION: Check your Postgres user privileges or PostGIS install")
        return False

    # test if ST_Subdivide exists (only in PostGIS 2.2+). It's used to split boundaries for faster processing
    logger.info(f"\t- using Postgres {settings.pg_version} and PostGIS {settings.postgis_version} "
                f"(with GEOS {settings.geos_version})")

    # # test if ST_ClusterKMeans exists (only in PostGIS 2.3+). It's used to create classes to display the data in the map
    # if not settings.st_clusterkmeans_supported:
    #     logger.warning("YOU NEED TO INSTALL POSTGIS 2.3 OR HIGHER FOR THE MAP SERVER TO WORK\n"
    #                    "it utilises the ST_ClusterKMeans() function in v2.3+")

    # log the user's input parameters
    logger.info("")
    logger.info("Arguments")
    for arg in vars(settings.args):
        value = getattr(settings.args, arg)

        if value is not None:
            if arg != "pgpassword":
                logger.info(f"\t- {arg} : {value}")
            else:
                logger.info(f"\t- {arg} : ************")

    # START LOADING DATA

    # PART 1 - load census data from CSV files
    logger.info(f"")
    start_time = datetime.now()
    logger.info(f"Part 1 of 2 : Start census data load : {start_time}")
    create_metadata_tables(pg_cur, settings.metadata_file_prefix, settings.metadata_file_type)
    populate_data_tables(settings.data_file_prefix, settings.data_file_type,
                         settings.table_name_part, settings.bdy_name_part)
    logger.info(f"Part 1 of 2 : Census data loaded! : {datetime.now() - start_time}")

    # PART 2 - load census boundaries from Shapefiles and optimise them for web visualisation
    logger.info(f"")
    start_time = datetime.now()
    logger.info(f"Part 2 of 2 : Start census boundary load : {start_time}")
    # load_boundaries(pg_cur)
    # add bdy type prefix to bdy id to enabled joins with stat data (Census 2016 data issue only)
    if settings.census_year != "2016":
        fix_boundary_ids()
    else:
        logger.info(f"\t- Step 2 of 3 : boundary id prefixes not required : {datetime.now() - start_time}")
    create_display_boundaries(pg_cur)
    logger.info(f"Part 2 of 2 : Census boundaries loaded! : {datetime.now() - start_time}")

    # close Postgres connection
    pg_cur.close()
    pg_conn.close()

    logger.info("")
    logger.info(f"Total time : : {datetime.now() - full_start_time}")

    return True


def create_metadata_tables(pg_cur, prefix, suffix):
    # Step 1 of 2 : create metadata tables from Census Excel spreadsheets
    start_time = datetime.now()

    # create schema
    if settings.data_schema != "public":
        pg_cur.execute(f"CREATE SCHEMA IF NOT EXISTS {settings.data_schema} AUTHORIZATION {settings.pg_user}")

    # create metadata tables
    sql = f"""DROP TABLE IF EXISTS {settings.data_schema}.metadata_tables CASCADE;
              CREATE TABLE {settings.data_schema}.metadata_tables (
                  table_number text,
                  table_name text,
                  table_description text
              ) WITH (OIDS=FALSE);
              ALTER TABLE {settings.data_schema}.metadata_tables OWNER TO {settings.pg_user}"""
    pg_cur.execute(sql)

    sql = f"""DROP TABLE IF EXISTS {settings.data_schema}.metadata_stats CASCADE;
              CREATE TABLE {settings.data_schema}.metadata_stats (
                  sequential_id text,
                  short_id text,
                  long_id text,
                  table_number text,
                  profile_table text,
                  column_heading_description text
              )
              WITH (OIDS=FALSE);
              ALTER TABLE {settings.data_schema}.metadata_stats OWNER TO {settings.pg_user}"""
    pg_cur.execute(sql)

    # get a list of all files matching the metadata filename prefix
    file_list = list()

    for root, dirs, files in os.walk(settings.data_directory):
        for file_name in files:
            if file_name.lower().startswith(prefix.lower()):
                # find all XLS and XLSX files (2016 data has a mix!)
                if file_name.lower().endswith(suffix.lower()) or file_name.lower().endswith(suffix.lower() + "x"):
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

            for table_dict in settings.census_metadata_dicts:

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

                        # # order what's left by sequential_id field
                        # df_clean.sort_values(by="Sequential", inplace=True)

                        # export to in-memory tab delimited text file
                        tsv_file = io.StringIO()
                        df_clean.to_csv(tsv_file, sep="\t", index=False, header=False)
                        tsv_file.seek(0)  # move position back to beginning of file before reading

                        # # output dataframe to test tsv file
                        # with open(file_dict["name"] + '.tsv', 'w') as fd:
                        #     shutil.copyfileobj(tsv_file, fd)
                        # tsv_file.seek(0)

                        # import into Postgres
                        sql = f"""COPY {settings.data_schema}.{table_dict['table']} 
                                      FROM stdin WITH CSV DELIMITER as '\t' NULL as ''"""

                        with pg_cur.copy(sql) as copy:
                            while data := tsv_file.read():
                                copy.write(data)

                    j += 1

                i += 1

            logger.info(f"\t\t- imported {file_dict['name']}")

    # clean up invalid rows
    pg_cur.execute(f"DELETE FROM {settings.data_schema}.metadata_tables WHERE table_number IS NULL")

    # add primary keys
    pg_cur.execute(f"""ALTER TABLE {settings.data_schema}.metadata_tables
                           ADD CONSTRAINT metadata_tables_pkey PRIMARY KEY (table_number)""")
    pg_cur.execute(f"""ALTER TABLE {settings.data_schema}.metadata_stats 
                           ADD CONSTRAINT metadata_stats_pkey PRIMARY KEY (sequential_id)""")

    # cluster tables on primary key (for minor performance improvement)
    pg_cur.execute(f"ALTER TABLE {settings.data_schema}.metadata_tables CLUSTER ON metadata_tables_pkey")
    pg_cur.execute(f"ALTER TABLE {settings.data_schema}.metadata_stats CLUSTER ON metadata_stats_pkey")

    # update stats
    pg_cur.execute(f"VACUUM ANALYZE {settings.data_schema}.metadata_tables")
    pg_cur.execute(f"VACUUM ANALYZE {settings.data_schema}.metadata_stats")

    logger.info(f"\t- Step 1 of 2 : metadata tables created : {datetime.now() - start_time}")


# create stats tables and import data from CSV files using multiprocessing
def populate_data_tables(prefix, suffix, table_name_part, bdy_name_part):
    # Step 2 of 2 : create & populate stats tables with CSV files using multiprocessing
    start_time = datetime.now()

    # get the file list and create sql copy statements
    file_list = []
    # get a dictionary of all files matching the filename prefix
    for root, dirs, files in os.walk(settings.data_directory):
        for file_name in files:
            if file_name.lower().startswith(prefix.lower()):
                if file_name.lower().endswith(suffix.lower()):

                    file_path = os.path.join(root, file_name)
                    file_name_components = file_name.lower().split(".")[0].split("_")

                    table = file_name_components[table_name_part]

                    # manual fix for the Australia wide data - has a different file name structure
                    if settings.census_year != '2011':
                        if "_aus." in file_name.lower():
                            boundary = "aust"
                        else:
                            boundary = file_name_components[bdy_name_part]
                    else:
                        boundary = file_name_components[bdy_name_part]

                        if "." in boundary:
                            boundary = "aust"

                    file_dict = {
                        "path": file_path,
                        "table": table,
                        "boundary": boundary,
                        "name": file_name
                    }

                    # if boundary == "ced":  # for testing
                    # print(file_dict)
                    file_list.append(file_dict)

    # are there any files to load?
    if len(file_list) == 0:
        logger.fatal("No Census data CSV files found\nACTION: Check your '--census-data-path' value")
        logger.fatal("\t- Step 2 of 2 : stats table create & populate FAILED!")
    else:
        # load all files using multiprocessing
        utils.multiprocess_csv_import(file_list, settings.max_concurrent_processes, settings.pg_connect_string,
                                      settings.data_schema, settings.pg_user, settings.region_id_field, logger)
        logger.info(f"\t- Step 2 of 2 : stats tables created & populated : {datetime.now() - start_time}")


# loads the admin bdy shapefiles using the shp2pgsql command line tool (part of PostGIS), using multiprocessing
def load_boundaries(pg_cur):
    # Step 1 of 2 : load census boundaries
    start_time = datetime.now()

    # create schema
    if settings.boundary_schema != "public":
        pg_cur.execute(f"CREATE SCHEMA IF NOT EXISTS {settings.boundary_schema} AUTHORIZATION {settings.pg_user}")

    # get file list
    table_list = list()
    create_list = list()
    append_list = list()

    # get a dictionary of Shapefile paths
    for root, dirs, files in os.walk(settings.boundaries_directory):
        for original_file_name in files:
            file_name = original_file_name.lower()

            if file_name.endswith(".shp") or file_name.endswith(".SHP"):
                file_dict = dict()
                file_dict['file_path'] = os.path.join(root, original_file_name)

                if file_name.startswith("mb_"):
                    for state in settings.states:
                        state = state.lower()

                        if state in file_name:
                            file_dict['pg_table'] = file_name.replace("_" + state + ".shp", "_aust", 1)
                else:
                    file_dict['pg_table'] = file_name.replace(".shp", "")

                file_dict['pg_schema'] = settings.boundary_schema

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
        utils.multiprocess_shapefile_load(create_list, settings.max_concurrent_processes,
                                          settings.pg_connect_string, logger)

        # Run the appends one at a time (Can't multiprocess as large sets of parallel INSERTs cause database deadlocks)
        # utils.multiprocess_shapefile_load(append_list, settings.max_concurrent_processes,
        #                                   settings.pg_connect_string, logger)
        for shp in append_list:
            utils.import_shapefile_to_postgres(pg_cur, shp['file_path'], shp['pg_table'], shp['pg_schema'],
                                               shp['delete_table'], True)

        logger.info(f"\t- Step 1 of 3 : boundaries loaded : {datetime.now() - start_time}")


def fix_boundary_ids():
    # Step 2 of 3 : add bdy type prefix to bdy id to enabled joins with stat data (Census 2016 data issue only)
    start_time = datetime.now()

    alter_sql_list = list()
    update_sql_list = list()
    vacuum_sql_list = list()

    for boundary_dict in settings.bdy_table_dicts:
        boundary_name = boundary_dict["boundary"]
        input_pg_table = f"{boundary_name}_{settings.census_year}_aust_{settings.datum}"

        if boundary_name in settings.bdy_prefix_list:
            id_field = boundary_dict["id_field"]

            sql = f"ALTER TABLE {settings.boundary_schema}.{input_pg_table} ALTER COLUMN {id_field} TYPE text"
            alter_sql_list.append(sql)

            # need the where clause to prevent prefix being added each time script is run
            sql = f"""UPDATE {settings.boundary_schema}.{input_pg_table} 
                          SET {id_field} = upper('{boundary_name}') || {id_field}
                      WHERE substring({id_field}, 1 , {len(boundary_name)}) <> upper('{boundary_name}')"""
            update_sql_list.append(sql)

            vacuum_sql_list.append(f"VACUUM ANALYZE {settings.boundary_schema}.{input_pg_table}")

    utils.multiprocess_list("sql", alter_sql_list,
                            settings.max_concurrent_processes, settings.pg_connect_string, logger)
    utils.multiprocess_list("sql", update_sql_list,
                            settings.max_concurrent_processes, settings.pg_connect_string, logger)
    utils.multiprocess_list("sql", vacuum_sql_list,
                            settings.max_concurrent_processes, settings.pg_connect_string, logger)

    logger.info(f"\t- Step 2 of 3 : boundary ids prefixed : {datetime.now() - start_time}")


def create_display_boundaries(pg_cur):
    # Step 3 of 3 : create web optimised versions of the census boundaries
    start_time = datetime.now()

    # create schema
    if settings.web_schema != "public":
        pg_cur.execute(f"CREATE SCHEMA IF NOT EXISTS {settings.web_schema} AUTHORIZATION {settings.pg_user}")

    # prepare boundaries for all tiled map zoom levels
    create_sql_list = list()
    insert_sql_list = list()
    vacuum_sql_list = list()

    for boundary_dict in settings.bdy_table_dicts:
        boundary_name = boundary_dict["boundary"]

        # these bdy types have no population data in the BCP/GCP profile
        if boundary_name not in settings.display_bdy_ignore_list:
            id_field = boundary_dict["id_field"]
            name_field = boundary_dict["name_field"]
            area_field = boundary_dict["area_field"]

            input_pg_table = f"{boundary_name}_{settings.census_year}_aust_{settings.datum}"
            pg_table = boundary_name

            # build create table statement
            create_table_list = list()
            create_table_list.append(f"DROP TABLE IF EXISTS {settings.web_schema}.{pg_table} CASCADE;")
            create_table_list.append(f"CREATE TABLE {settings.web_schema}.{pg_table} (")

            # build column list
            column_list = list()
            column_list.append("id text NOT NULL PRIMARY KEY")
            column_list.append("name text NOT NULL")
            column_list.append("area double precision NOT NULL")
            column_list.append("population double precision NOT NULL")
            column_list.append("geom geometry(MultiPolygon, 4283) NULL")

            for zoom_level in range(4, 18):
                display_zoom = str(zoom_level).zfill(2)
                column_list.append(f"geojson_{display_zoom} jsonb NOT NULL")

            # add columns to create table statement and finish it
            create_table_list.append(f"""{','.join(column_list)}) WITH (OIDS=FALSE);
                                         ALTER TABLE {settings.web_schema}.{pg_table} OWNER TO {settings.pg_user};
                                         CREATE INDEX {pg_table}_geom_idx ON {settings.web_schema}.{pg_table} 
                                             USING gist (geom);
                                         ALTER TABLE {settings.web_schema}.{pg_table} CLUSTER ON {pg_table}_geom_idx""")

            sql = "\n".join(create_table_list)
            create_sql_list.append(sql)

            # get population field and table
            if boundary_name[:1] == "i":
                pop_stat = settings.indigenous_population_stat
                pop_table = settings.indigenous_population_table
            else:
                pop_stat = settings.population_stat
                pop_table = settings.population_table

            # print(boundary_name)
            # print(pop_stat + " - " + pop_table)

            # build insert statement
            insert_into_list = list()
            insert_into_list.append(f"INSERT INTO {settings.web_schema}.{pg_table}")
            insert_into_list.append(f"""SELECT bdy.{id_field} AS id, 
                                               {name_field} AS name, 
                                               SUM(bdy.{area_field}) AS area, 
                                               tab.{pop_stat} AS population,""")

            # thin geometry to make querying faster
            tolerance = utils.get_tolerance(10)
            insert_into_list.append(f"""ST_Transform(ST_Multi(ST_Union(
                                             ST_SimplifyVW(ST_Transform(geom, 3577), {tolerance})
                                        )), 4283),""")

            # create statements for geojson optimised for each zoom level
            geojson_list = list()

            for zoom_level in range(4, 18):
                # thin geometries to a default tolerance per zoom level
                tolerance = utils.get_tolerance(zoom_level)
                # trim coords to only the significant ones
                decimal_places = utils.get_decimal_places(zoom_level)

                geojson_list.append(f"""ST_AsGeoJSON(ST_Transform(ST_Multi(ST_Union(ST_SimplifyVW(ST_Transform(
                                            bdy.geom, 3577), {tolerance}))), 4283), {decimal_places})::jsonb""")

            insert_into_list.append(f"""{','.join(geojson_list)}
                                        FROM {settings.boundary_schema}.{input_pg_table} AS bdy
                                        INNER JOIN {settings.data_schema}.{boundary_name}_{pop_table} AS tab
                                            ON bdy.{id_field} = tab.{settings.region_id_field}
                                        WHERE bdy.geom IS NOT NULL
                                        GROUP BY {id_field}, {name_field}, {pop_stat}""")

            sql = "\n".join(insert_into_list)
            insert_sql_list.append(sql)

            vacuum_sql_list.append(f"VACUUM ANALYZE {settings.web_schema}.{pg_table}")

    # print("\n".join(insert_sql_list))

    utils.multiprocess_list("sql", create_sql_list,
                            settings.max_concurrent_processes, settings.pg_connect_string, logger)
    utils.multiprocess_list("sql", insert_sql_list,
                            settings.max_concurrent_processes, settings.pg_connect_string, logger)
    utils.multiprocess_list("sql", vacuum_sql_list,
                            settings.max_concurrent_processes, settings.pg_connect_string, logger)

    logger.info(f"\t- Step 3 of 3 : web optimised boundaries created : {datetime.now() - start_time}")


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

    logger.info(f"")
    logger.info(f"Start census-loader")

    if main():
        logger.info(f"Finished successfully!")
    else:
        logger.fatal("Something bad happened!")

    logger.info(f"")
    logger.info(f"-------------------------------------------------------------------------------")
