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
    logger.info(f"Start census data load : {start_time}")
    create_metadata_tables(pg_cur, settings.metadata_file_prefix, settings.metadata_file_type)
    populate_data_tables(settings.data_file_prefix, settings.data_file_type,
                         settings.table_name_part, settings.bdy_name_part)
    logger.info(f"Census data loaded! : {datetime.now() - start_time}")

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
