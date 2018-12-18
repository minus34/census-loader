#!/usr/bin/env python
# -*- coding: utf-8 -*-

# import arguments
import ast
import json
import psycopg2
import psycopg2.extras
import os

# from datetime import datetime

from flask import Flask
from flask import render_template
from flask import request
from flask import Response
from flask_compress import Compress

from psycopg2.extensions import AsIs

app = Flask(__name__, static_url_path='')
Compress(app)

# # set command line arguments
# args = arguments.set_arguments()

# get settings from arguments
# settings = arguments.get_settings(args)

settings = dict()

settings['census_year'] = "2016"
settings['data_schema'] = "census_2016_data"
settings['web_schema'] = "census_2016_web"

# create postgres connect string
settings['pg_host'] = os.getenv("PGHOST", "localhost")
settings['pg_port'] = os.getenv("PGPORT", 5432)
settings['pg_db'] = os.getenv("PGDB", "geo")
settings['pg_user'] = os.getenv("PGUSER", "postgres")
settings['pg_password'] = os.getenv("PGPASSWORD", "password")

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
         {"boundary": "nrmr", "id_field": "nrm_code16", "name_field": "nrm_name16", "area_field": "areasqkm16"},
         {"boundary": "poa", "id_field": "poa_code16", "name_field": "'Postcode ' || poa_name16", "area_field": "areasqkm16"},
         {"boundary": "ra", "id_field": "ra_code16", "name_field": "ra_name16", "area_field": "areasqkm16"},
         {"boundary": "sa1", "id_field": "sa1_7dig16", "name_field": "'SA1 ' || sa1_7dig16", "area_field": "areasqkm16"},
         {"boundary": "sa2", "id_field": "sa2_main16", "name_field": "sa2_name16", "area_field": "areasqkm16"},
         {"boundary": "sa3", "id_field": "sa3_code16", "name_field": "sa3_name16", "area_field": "areasqkm16"},
         {"boundary": "sa4", "id_field": "sa4_code16", "name_field": "sa4_name16", "area_field": "areasqkm16"},
         {"boundary": "sed", "id_field": "sed_code16", "name_field": "sed_name16", "area_field": "areasqkm16"},
         {"boundary": "sos", "id_field": "sos_code16", "name_field": "sos_name16", "area_field": "areasqkm16"},
         {"boundary": "sosr", "id_field": "sosr_code16", "name_field": "sosr_name16", "area_field": "areasqkm16"},
         {"boundary": "ssc", "id_field": "ssc_code16", "name_field": "ssc_name16", "area_field": "areasqkm16"},
         {"boundary": "ste", "id_field": "ste_code16", "name_field": "ste_name16", "area_field": "areasqkm16"},
         {"boundary": "sua", "id_field": "sua_code16", "name_field": "sua_name16", "area_field": "areasqkm16"},
         {"boundary": "tr", "id_field": "tr_code16", "name_field": "tr_name16", "area_field": "areasqkm16"},
         {"boundary": "ucl", "id_field": "ucl_code16", "name_field": "ucl_name16", "area_field": "areasqkm16"}]
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

# connect to Postgres
pg_conn = psycopg2.connect(settings['pg_connect_string'])
pg_conn.autocommit = True
pg_cur = pg_conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)


# get the boundary name that suits each (tiled map) zoom level and its minimum value to colour in
def get_boundary(zoom_level):

    if zoom_level < 7:
        boundary_name = "ste"
        min_display_value = 2025
    elif zoom_level < 9:
        boundary_name = "sa4"
        min_display_value = 675
    elif zoom_level < 11:
        boundary_name = "sa3"
        min_display_value = 225
    elif zoom_level < 14:
        boundary_name = "sa2"
        min_display_value = 75
    elif zoom_level < 17:
        boundary_name = "sa1"
        min_display_value = 25
    else:
        boundary_name = "mb"
        min_display_value = 5

    return boundary_name, min_display_value


@app.route("/")
def homepage():
    return render_template('index.html')


@app.route("/dots/")
def dot_homepage():
    return render_template('density.html')


@app.route("/get-bdy-names")
def get_boundary_name():
    # Get parameters from querystring
    min_val = int(request.args.get('min'))
    max_val = int(request.args.get('max'))

    boundary_zoom_dict = dict()

    for zoom_level in range(min_val, max_val + 1):
        boundary_dict = dict()
        boundary_dict["name"], boundary_dict["min"] = get_boundary(zoom_level)
        boundary_zoom_dict["{0}".format(zoom_level)] = boundary_dict

    return Response(json.dumps(boundary_zoom_dict), mimetype='application/json')


@app.route("/get-metadata")
def get_metadata():
    # full_start_time = datetime.now()
    # start_time = datetime.now()

    # Get parameters from querystring

    # # census year
    # census_year = request.args.get('c')

    # comma separated list of stat ids (i.e. sequential_ids) AND/OR equations contains stat ids
    raw_stats = request.args.get('stats')

    # get number of map classes
    try:
        num_classes = int(request.args.get('n'))
    except TypeError:
        num_classes = 7

    # replace all maths operators to get list of all the stats we need to query for
    search_stats = raw_stats.upper().replace(" ", "").replace("(", "").replace(")", "") \
        .replace("+", ",").replace("-", ",").replace("/", ",").replace("*", ",").split(",")

    # TODO: add support for numbers in equations - need to strip them from search_stats list

    # equation_stats = raw_stats.lower().split(",")

    # print(equation_stats)
    # print(search_stats)

    # get stats tuple for query input (convert to lower case)
    search_stats_tuple = tuple([stat.lower() for stat in search_stats])

    # get all boundary names in all zoom levels
    boundary_names = list()
    test_names = list()

    for zoom_level in range(0, 16):
        bdy_name, min_val = get_boundary(zoom_level)

        # only add if bdy not in list
        if bdy_name not in test_names:
            bdy_dict = dict()
            bdy_dict["name"] = bdy_name
            bdy_dict["min"] = min_val
            boundary_names.append(bdy_dict)

            test_names.append(bdy_name)

    # get stats metadata, including the all important table number and map type (raw values based or normalised by pop)
    sql = "SELECT lower(sequential_id) AS id, " \
          "lower(table_number) AS \"table\", " \
          "replace(long_id, '_', ' ') AS description, " \
          "column_heading_description AS type, " \
          "CASE WHEN lower(sequential_id) = '{0}' " \
          "OR lower(long_id) LIKE '%%median%%' " \
          "OR lower(long_id) LIKE '%%average%%' " \
          "THEN 'values' " \
          "ELSE 'percent' END AS maptype " \
          "FROM {1}.metadata_stats " \
          "WHERE lower(sequential_id) IN %s " \
          "ORDER BY sequential_id".format(settings['population_stat'], settings["data_schema"])

    try:
        pg_cur.execute(sql, (search_stats_tuple,))
    except psycopg2.Error:
        return "I can't SELECT:<br/><br/>" + sql

    # Retrieve the results of the query
    rows = pg_cur.fetchall()

    # output is the main content, row_output is the content from each record returned
    response_dict = dict()
    response_dict["type"] = "StatsCollection"
    response_dict["classes"] = num_classes

    feature_array = list()

    # For each row returned assemble a dictionary
    for row in rows:
        feature_dict = dict(row)
        feature_dict["id"] = feature_dict["id"].lower()
        feature_dict["table"] = feature_dict["table"].lower()

        # # get ranges of stat values per boundary type
        # for boundary in boundary_names:
        #     boundary_table = "{0}.{1}".format(settings["web_schema"], boundary["name"])
        #
        #     data_table = "{0}.{1}_{2}".format(settings["data_schema"], boundary["name"], feature_dict["table"])
        #
        #     # get the values for the map classes
        #     with get_db_cursor() as pg_cur:
        #         if feature_dict["maptype"] == "values":
        #             stat_field = "tab.{0}" \
        #                 .format(feature_dict["id"], )
        #         else:  # feature_dict["maptype"] == "percent"
        #             stat_field = "CASE WHEN bdy.population > 0 THEN tab.{0} / bdy.population * 100.0 ELSE 0 END" \
        #                 .format(feature_dict["id"], )
        #
        #         # get range of stat values
        #         # feature_dict[boundary_name] = utils.get_equal_interval_bins(
        #         # feature_dict[boundary["name"]] = utils.get_kmeans_bins(
        #         feature_dict[boundary["name"]] = utils.get_min_max(
        #             data_table, boundary_table, stat_field, num_classes, boundary["min"], feature_dict["maptype"],
        #             pg_cur, settings)

        # add dict to output array of metadata
        feature_array.append(feature_dict)

    response_dict["stats"] = feature_array
    # output_array.append(output_dict)

    # print("Got metadata for {0} in {1}".format(boundary_name, datetime.now() - start_time))

    # # Assemble the JSON
    # response_dict["boundaries"] = output_array

    # print("Returned metadata in {0}".format(datetime.now() - full_start_time))

    return Response(json.dumps(response_dict), mimetype='application/json')


@app.route("/get-data")
def get_data():
    # full_start_time = datetime.now()
    # start_time = datetime.now()

    # # Get parameters from querystring
    # census_year = request.args.get('c')

    map_left = request.args.get('ml')
    map_bottom = request.args.get('mb')
    map_right = request.args.get('mr')
    map_top = request.args.get('mt')

    stat_id = request.args.get('s')
    table_id = request.args.get('t')
    boundary_name = request.args.get('b')
    zoom_level = int(request.args.get('z'))

    # TODO: add support for equations

    # get the boundary table name from zoom level
    if boundary_name is None:
        boundary_name, min_val = get_boundary(zoom_level)

    display_zoom = str(zoom_level).zfill(2)

    # build SQL with SQL injection protection
    # yes, this is ridiculous - if someone can find a shorthand way of doing this then fire up the pull requests!
    sql_template = "SELECT bdy.id, bdy.name, bdy.population, tab.%s / bdy.area AS density, " \
                   "CASE WHEN bdy.population > 0 THEN tab.%s / bdy.population * 100.0 ELSE 0 END AS percent, " \
                   "tab.%s, geojson_%s AS geometry " \
                   "FROM {0}.%s AS bdy " \
                   "INNER JOIN {1}.%s_%s AS tab ON bdy.id = tab.{2} " \
                   "WHERE bdy.geom && ST_MakeEnvelope(%s, %s, %s, %s, 4283)"\
        .format(settings['web_schema'], settings['data_schema'], settings['region_id_field'])

    sql = pg_cur.mogrify(sql_template, (AsIs(stat_id), AsIs(stat_id), AsIs(stat_id), AsIs(display_zoom),
                                        AsIs(boundary_name), AsIs(boundary_name), AsIs(table_id), AsIs(map_left),
                                        AsIs(map_bottom), AsIs(map_right), AsIs(map_top)))

    try:
        pg_cur.execute(sql)
    except psycopg2.Error:
        return "I can't SELECT:<br/><br/>" + str(sql)

    # Retrieve the results of the query
    rows = pg_cur.fetchall()

    # Get the column names returned
    col_names = [desc[0] for desc in pg_cur.description]

    # print("Got records from Postgres in {0}".format(datetime.now() - start_time))
    # start_time = datetime.now()

    # output is the main content, row_output is the content from each record returned
    output_dict = dict()
    output_dict["type"] = "FeatureCollection"

    i = 0
    feature_array = list()

    # For each row returned...
    for row in rows:
        feature_dict = dict()
        feature_dict["type"] = "Feature"

        properties_dict = dict()

        # For each field returned, assemble the feature and properties dictionaries
        for col in col_names:
            if col == 'geometry':
                feature_dict["geometry"] = ast.literal_eval(str(row[col]))
            elif col == 'id':
                feature_dict["id"] = row[col]
            else:
                properties_dict[col] = row[col]

        feature_dict["properties"] = properties_dict

        feature_array.append(feature_dict)

        # start over
        i += 1

    # Assemble the GeoJSON
    output_dict["features"] = feature_array

    # print("Parsed records into JSON in {1}".format(i, datetime.now() - start_time))
    # print("get-data: returned {0} records  {1}".format(i, datetime.now() - full_start_time))

    return Response(json.dumps(output_dict), mimetype='application/json')


@app.route("/get-dot-data")
def get_dot_data():
    # full_start_time = datetime.now()
    # start_time = datetime.now()

    # # Get parameters from querystring
    # census_year = request.args.get('c')

    map_left = request.args.get('ml')
    map_bottom = request.args.get('mb')
    map_right = request.args.get('mr')
    map_top = request.args.get('mt')

    stat_id = request.args.get('s')
    # table_id = request.args.get('t')
    # boundary_name = request.args.get('b')
    # boundary_name = 'sa1'
    # zoom_level = int(request.args.get('z'))

    # TODO: get rid of this hardcoding!

    schema_name = 'census_2016_sandpit'

    if stat_id == 'g5447':
        table_name = 'dots_non_religious'
    elif stat_id == 'g5423':
        table_name = 'dots_christian'
    elif stat_id == 'g5429':
        table_name = 'dots_islam'
    elif stat_id == 'g5363':
        table_name = 'dots_buddhism'
    elif stat_id == 'g5426':
        table_name = 'dots_hinduism'
    elif stat_id == 'g5432':
        table_name = 'dots_judaism'
    else:
        table_name = 'dots_non_religious'

    # # get the boundary table name from zoom level
    # if boundary_name is None:
    #     boundary_name, min_val = get_boundary(zoom_level)

    # display_zoom = str(zoom_level).zfill(2)

    # build SQL with SQL injection protection
    # yes, this is ridiculous - if someone can find a shorthand way of doing this then fire up the pull requests!
    sql_template = "SELECT gid AS id, ST_AsGeoJSON(geom) AS geometry " \
                   "FROM {0}.{1} " \
                   "WHERE geom && ST_MakeEnvelope(%s, %s, %s, %s, 4283)"\
        .format(schema_name, table_name)

    sql = pg_cur.mogrify(sql_template, (AsIs(map_left), AsIs(map_bottom), AsIs(map_right), AsIs(map_top)))

    try:
        pg_cur.execute(sql)
    except psycopg2.Error:
        return "I can't SELECT:<br/><br/>" + str(sql)

    # Retrieve the results of the query
    rows = pg_cur.fetchall()

    # Get the column names returned
    col_names = [desc[0] for desc in pg_cur.description]

    # print("Got records from Postgres in {0}".format(datetime.now() - start_time))
    # start_time = datetime.now()

    # output is the main content, row_output is the content from each record returned
    output_dict = dict()
    output_dict["type"] = "FeatureCollection"

    i = 0
    feature_array = list()

    # For each row returned...
    for row in rows:
        feature_dict = dict()
        feature_dict["type"] = "Feature"

        properties_dict = dict()

        # For each field returned, assemble the feature and properties dictionaries
        for col in col_names:
            if col == 'geometry':
                feature_dict["geometry"] = ast.literal_eval(str(row[col]))
            elif col == 'id':
                feature_dict["id"] = row[col]
            else:
                properties_dict[col] = row[col]

        feature_dict["properties"] = properties_dict

        feature_array.append(feature_dict)

        # start over
        i += 1

    # Assemble the GeoJSON
    output_dict["features"] = feature_array

    # print("Parsed records into JSON in {1}".format(i, datetime.now() - start_time))
    # print("get-data: returned {0} records  {1}".format(i, datetime.now() - full_start_time))

    return Response(json.dumps(output_dict), mimetype='application/json')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
