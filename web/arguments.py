#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import os


# set the command line arguments for the script
def set_arguments():
    parser = argparse.ArgumentParser(
        description='A universal map visualisation of ABS Census statistics.')

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
        help='Schema name to store data tables in. Defaults to \'census_' + census_year + '_data\'.')
    parser.add_argument(
        '--web-schema', default='census_' + census_year + '_web',
        help='Schema name to store web optimised boundary tables in. Defaults to \'census_' + census_year + '_web\'.')

    return parser.parse_args()


# create the dictionary of settings
def get_settings(args):
    settings = dict()

    settings['census_year'] = args.census_year
    settings['states'] = ["ACT", "NSW", "NT", "OT", "QLD", "SA", "TAS", "VIC", "WA"]
    settings['data_schema'] = args.data_schema
    settings['web_schema'] = args.web_schema

    # create postgres connect string
    settings['pg_host'] = args.pghost or os.getenv("PGHOST", "localhost")
    settings['pg_port'] = args.pgport or os.getenv("PGPORT", 5432)
    settings['pg_db'] = args.pgdb or os.getenv("POSTGRES_USER", "geo")
    settings['pg_user'] = args.pguser or os.getenv("POSTGRES_USER", "postgres")
    settings['pg_password'] = args.pgpassword or os.getenv("POSTGRES_PASSWORD", "password")

    settings['pg_connect_string'] = "dbname='{0}' host='{1}' port='{2}' user='{3}' password='{4}'".format(
        settings['pg_db'], settings['pg_host'], settings['pg_port'], settings['pg_user'], settings['pg_password'])

    # set file name and field name defaults based on census year
    if settings['census_year'] == '2016':
        settings['metadata_file_prefix'] = "Metadata_"
        settings['metadata_file_type'] = ".xls"
        settings["census_metadata_dicts"] = [{"table": "metadata_tables", "first_row": "table number"},
                                             {"table": "metadata_stats", "first_row": "sequential"}]

        settings['data_file_prefix'] = "2016Census_"
        settings['data_file_type'] = ".csv"
        settings['table_name_part'] = 1  # position in the data file name that equals it's destination table name
        settings['bdy_name_part'] = 3  # position in the data file name that equals it's census boundary name
        settings['region_id_field'] = "region_id"

        settings['population_stat'] = "g3"
        settings['population_table'] = "g01"
        settings['indigenous_population_stat'] = "i3"
        settings['indigenous_population_table'] = "i01a"

        settings['bdy_table_dicts'] = \
             [{"boundary": "ced", "id_field": "ced_code16", "name_field": "ced_name16", "area_field": "areasqkm16"},
             {"boundary": "gccsa", "id_field": "gcc_code16", "name_field": "gcc_name16", "area_field": "areasqkm16"},
             {"boundary": "iare", "id_field": "iar_code16", "name_field": "iar_name16", "area_field": "areasqkm16"},
             {"boundary": "iloc", "id_field": "ilo_code16", "name_field": "ilo_name16", "area_field": "areasqkm16"},
             {"boundary": "ireg", "id_field": "ire_code16", "name_field": "ire_name16", "area_field": "areasqkm16"},
             {"boundary": "lga", "id_field": "lga_code16", "name_field": "lga_name16", "area_field": "areasqkm16"},
             {"boundary": "mb", "id_field": "mb_code16", "name_field": "'MB ' || mb_code16", "area_field": "areasqkm16"},
             # {"boundary": "nrmr", "id_field": "nrm_code16", "name_field": "nrm_name16", "area_field": "areasqkm16"},
             {"boundary": "poa", "id_field": "poa_code16", "name_field": "'Postcode ' || poa_name16", "area_field": "areasqkm16"},
             # {"boundary": "ra", "id_field": "ra_code16", "name_field": "ra_name16", "area_field": "areasqkm16"},
             {"boundary": "sa1", "id_field": "sa1_7dig16", "name_field": "'SA1 ' || sa1_7dig16", "area_field": "areasqkm16"},
             {"boundary": "sa2", "id_field": "sa2_main16", "name_field": "sa2_name16", "area_field": "areasqkm16"},
             {"boundary": "sa3", "id_field": "sa3_code16", "name_field": "sa3_name16", "area_field": "areasqkm16"},
             {"boundary": "sa4", "id_field": "sa4_code16", "name_field": "sa4_name16", "area_field": "areasqkm16"},
             {"boundary": "sed", "id_field": "sed_code16", "name_field": "sed_name16", "area_field": "areasqkm16"},
             # {"boundary": "sos", "id_field": "sos_code16", "name_field": "sos_name16", "area_field": "areasqkm16"},
             # {"boundary": "sosr", "id_field": "sosr_code16", "name_field": "sosr_name16", "area_field": "areasqkm16"},
             {"boundary": "ssc", "id_field": "ssc_code16", "name_field": "ssc_name16", "area_field": "areasqkm16"},
             {"boundary": "ste", "id_field": "ste_code16", "name_field": "ste_name16", "area_field": "areasqkm16"}]
             # {"boundary": "sua", "id_field": "sua_code16", "name_field": "sua_name16", "area_field": "areasqkm16"},
             # {"boundary": "tr", "id_field": "tr_code16", "name_field": "tr_name16", "area_field": "areasqkm16"},
             # {"boundary": "ucl", "id_field": "ucl_code16", "name_field": "ucl_name16", "area_field": "areasqkm16"},
             # {"boundary": "add", "id_field": "add_code16", "name_field": "add_name16", "area_field": "areasqkm16"},

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

        settings['population_stat'] = "b3"
        settings['population_table'] = "b01"
        settings['indigenous_population_stat'] = "i3"
        settings['indigenous_population_table'] = "i01a"

        settings['bdy_table_dicts'] = \
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
    else:
        return None

    return settings
