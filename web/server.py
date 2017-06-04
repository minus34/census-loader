

import ast
import json
# import math
# import os
import psycopg2
# import sys
import utils

from datetime import datetime

from contextlib import contextmanager

from flask import Flask
from flask import render_template
from flask import request
from flask import Response
from flask_compress import Compress

from psycopg2 import extras
from psycopg2.pool import ThreadedConnectionPool

app = Flask(__name__, static_url_path='')
Compress(app)

# set command line arguments
args = utils.set_arguments()

# get settings from arguments
settings = utils.get_settings(args)

# create database connection pool
pool = ThreadedConnectionPool(10, 30,
                              database=settings["pg_db"],
                              user=settings["pg_user"],
                              password=settings["pg_password"],
                              host=settings["pg_host"],
                              port=settings["pg_port"])


@contextmanager
def get_db_connection():
    """
    psycopg2 connection context manager.
    Fetch a connection from the connection pool and release it.
    """
    try:
        connection = pool.getconn()
        yield connection
    finally:
        pool.putconn(connection)


@contextmanager
def get_db_cursor(commit=False):
    """
    psycopg2 connection.cursor context manager.
    Creates a new cursor and closes it, committing changes if specified.
    """
    with get_db_connection() as connection:
        cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        try:
            yield cursor
            if commit:
                connection.commit()
        finally:
            cursor.close()


@app.route("/")
def homepage():
    return render_template('index.html')


@app.route("/get-bdy-names")
def get_boundary_name():

    # Get parameters from querystring
    min = int(request.args.get('min'))
    max = int(request.args.get('max'))

    boundary_zoom_dict = dict()

    for zoom_level in range(min, max + 1):
        boundary_zoom_dict["{0}".format(zoom_level)] = utils.get_boundary_name(zoom_level)

    return Response(json.dumps(boundary_zoom_dict), mimetype='application/json')


# @app.route("/get-metadata")
# def get_metadata():
#     # Get parameters from querystring
#     num_classes = int(request.args.get('n'))
#     raw_stats = request.args.get('stats')
#
#     # replace all maths operators to get list of all the stats we need
#     search_stats = raw_stats.upper().replace(" ", "").replace("(", "").replace(")", "")\
#         .replace("+", ",").replace("-", ",").replace("/", ",").replace("*", ",").split(",")
#
#     # TODO: add support for numbers in equations - need to strip them from search_stats list
#
#     # equation_stats = raw_stats.lower().split(",")
#
#     # print(equation_stats)
#     # print(search_stats)
#
#     # get stats tuple for query input
#     search_stats_tuple = tuple(search_stats)
#
#     # get percentile fraction
#     percentile_fraction = 1.0 / float(num_classes)
#
#     # get all boundary names in all zoom levels
#     boundary_names = list()
#
#     for zoom_level in range(0, 16):
#         bdy_name = utils.get_boundary_name(zoom_level)
#
#         if bdy_name not in boundary_names:
#             boundary_names.append(bdy_name)
#
#     # get stats metadata, including the all important table number
#     sql = "SELECT sequential_id AS id, lower(table_number) AS table, replace(long_id, '_', ' ') AS description, " \
#           "column_heading_description AS type " \
#           "FROM {0}.metadata_stats " \
#           "WHERE sequential_id IN %s " \
#           "ORDER BY sequential_id".format(settings["data_schema"],)
#
#     with get_db_cursor() as pg_cur:
#         try:
#             pg_cur.execute(sql, (search_stats_tuple,))
#         except psycopg2.Error:
#             return "I can't SELECT :\n\n" + sql
#
#         # Retrieve the results of the query
#         rows = pg_cur.fetchall()
#
#     # output is the main content, row_output is the content from each record returned
#     response_dict = dict()
#     response_dict["type"] = "StatsCollection"
#     response_dict["classes"] = num_classes
#
#     output_array = list()
#
#     # get metadata for all boundaries (done in one go for frontend performance)
#     for boundary_name in boundary_names:
#         output_dict = dict()
#         output_dict["boundary"] = boundary_name
#
#         # # get id and area fields for boundary
#         # boundary_id_field = ""
#         # boundary_area_field = ""
#         #
#         # for boundary_dict in settings['bdy_table_dicts']:
#         #     if boundary_dict["boundary"] == boundary_name:
#         #         boundary_id_field = boundary_dict["id_field"]
#         #         boundary_area_field = boundary_dict["area_field"]
#
#         i = 0
#         feature_array = list()
#
#         # For each row returned assemble a dictionary
#         for row in rows:
#             feature_dict = dict(row)
#
#             # get the values for the map classes
#
#             # 1 of 3 - values
#             field_array = list()
#             current_fraction = percentile_fraction
#
#             for j in range(0, num_classes):
#                 field_array.append("percentile_disc({0}) within group (order by {1}) as \"{2}\""
#                                    .format(current_fraction, feature_dict["id"], j + 1))
#
#                 current_fraction += percentile_fraction
#
#             sql = "SELECT {3} FROM {0}.{1}_{2}"\
#                 .format(settings["data_schema"], boundary_name, feature_dict["table"], ",".join(field_array))
#
#             with get_db_cursor() as pg_cur:
#                 pg_cur.execute(sql)
#                 values = pg_cur.fetchone()
#
#                 feature_dict["values"] = dict(values)
#
#             # 2 of 3 - densities
#             field_array = list()
#             current_fraction = percentile_fraction
#
#             for j in range(0, num_classes):
#                 the_field = "tab." + feature_dict["id"] + " / bdy.area"
#
#                 field_array.append("percentile_disc({0}) within group (order by {1}) as \"{2}\""
#                                    .format(current_fraction, the_field, j + 1))
#
#                 current_fraction += percentile_fraction
#
#             sql = "SELECT {0} FROM {1}.{2}_{3} AS tab " \
#                   "INNER JOIN {4}.{2}_zoom_10 AS bdy ON tab.{5} = bdy.id " \
#                   "WHERE geom IS NOT NULL" \
#                 .format(",".join(field_array), settings["data_schema"], boundary_name, feature_dict["table"],
#                         settings["boundary_schema"] + "_display", settings['region_id_field'])
#
#             with get_db_cursor() as pg_cur:
#                 pg_cur.execute(sql)
#                 values = pg_cur.fetchone()
#
#                 feature_dict["densities"] = dict(values)
#
#             # 3 of 3 - normalised
#             field_array = list()
#             current_fraction = percentile_fraction
#
#             for j in range(0, num_classes):
#                 the_field = "CASE WHEN bdy.population > 0 THEN tab.{0} / bdy.population * 100.0 ELSE 0 END"\
#                     .format(feature_dict["id"],)
#
#                 field_array.append("percentile_disc({0}) within group (order by {1}) as \"{2}\""
#                                    .format(current_fraction, the_field, j + 1))
#
#                 current_fraction += percentile_fraction
#
#             sql = "SELECT {0} FROM {1}.{2}_{3} AS tab " \
#                   "INNER JOIN {4}.{2}_zoom_10 AS bdy ON tab.{5} = bdy.id " \
#                   "WHERE bdy.geom IS NOT NULL " \
#                   "AND bdy.population > 0" \
#                 .format(",".join(field_array), settings["data_schema"], boundary_name, feature_dict["table"],
#                         settings["boundary_schema"] + "_display", settings['region_id_field'])
#
#             with get_db_cursor() as pg_cur:
#                 pg_cur.execute(sql)
#                 values = pg_cur.fetchone()
#
#                 feature_dict["normalised"] = dict(values)
#
#             # add dict to output array oif metadata
#             feature_array.append(feature_dict)
#
#             i += 1
#
#         output_dict["stats"] = feature_array
#         output_array.append(output_dict)
#
#     # Assemble the JSON
#     response_dict["boundaries"] = output_array
#
#     return Response(json.dumps(response_dict), mimetype='application/json')


@app.route("/get-metadata")
def get_metadata():
    # Get parameters from querystring
    num_classes = int(request.args.get('n'))
    raw_stats = request.args.get('stats')

    # replace all maths operators to get list of all the stats we need
    search_stats = raw_stats.upper().replace(" ", "").replace("(", "").replace(")", "")\
        .replace("+", ",").replace("-", ",").replace("/", ",").replace("*", ",").split(",")

    # TODO: add support for numbers in equations - need to strip them from search_stats list

    # equation_stats = raw_stats.lower().split(",")

    # print(equation_stats)
    # print(search_stats)

    # get stats tuple for query input
    search_stats_tuple = tuple(search_stats)

    # get all boundary names in all zoom levels
    boundary_names = list()

    for zoom_level in range(0, 16):
        bdy_name = utils.get_boundary_name(zoom_level)

        if bdy_name not in boundary_names:
            boundary_names.append(bdy_name)

    # get stats metadata, including the all important table number
    sql = "SELECT sequential_id AS id, lower(table_number) AS table, replace(long_id, '_', ' ') AS description, " \
          "column_heading_description AS type " \
          "FROM {0}.metadata_stats " \
          "WHERE sequential_id IN %s " \
          "ORDER BY sequential_id".format(settings["data_schema"],)

    with get_db_cursor() as pg_cur:
        try:
            pg_cur.execute(sql, (search_stats_tuple,))
        except psycopg2.Error:
            return "I can't SELECT :\n\n" + sql

        # Retrieve the results of the query
        rows = pg_cur.fetchall()

    # output is the main content, row_output is the content from each record returned
    response_dict = dict()
    response_dict["type"] = "StatsCollection"
    response_dict["classes"] = num_classes

    output_array = list()

    # get metadata for all boundaries (done in one go for frontend performance)
    for boundary_name in boundary_names:
        output_dict = dict()
        output_dict["boundary"] = boundary_name

        i = 0
        feature_array = list()

        # For each row returned assemble a dictionary
        for row in rows:
            feature_dict = dict(row)

            # get the values for the map classes

            # 1 of 3 - values
            stat_field = feature_dict["id"]
            feature_dict["values"] = get_bins(boundary_name, feature_dict, num_classes, stat_field)

            # 2 of 3 - densities
            stat_field = "tab." + feature_dict["id"] + " / bdy.area"
            feature_dict["densities"] = get_bins(boundary_name, feature_dict, num_classes, stat_field)

            # 3 of 3 - normalised
            stat_field = "CASE WHEN bdy.population > 0 THEN tab.{0} / bdy.population * 100.0 ELSE 0 END" \
                .format(feature_dict["id"], )
            feature_dict["normalised"] = get_bins(boundary_name, feature_dict, num_classes, stat_field)

            # add dict to output array oif metadata
            feature_array.append(feature_dict)

            i += 1

        output_dict["stats"] = feature_array
        output_array.append(output_dict)

    # Assemble the JSON
    response_dict["boundaries"] = output_array

    return Response(json.dumps(response_dict), mimetype='application/json')


def get_bins(boundary_name, feature_dict, num_classes, stat_field):
    value_dict = dict()

    sql = "SELECT MAX({0}) AS val FROM {1}.{2}_{3} AS tab " \
          "INNER JOIN {4}.{2}_zoom_10 AS bdy ON tab.{5} = bdy.id " \
          "WHERE geom IS NOT NULL" \
        .format(stat_field, settings["data_schema"], boundary_name, feature_dict["table"],
                settings["boundary_schema"] + "_display", settings['region_id_field'])

    print(sql)

    with get_db_cursor() as pg_cur:
        pg_cur.execute(sql)
        row = pg_cur.fetchone()
        max_value = row["val"]

    increment = max_value / float(num_classes)

    for j in range(0, num_classes):
        value_dict["{0}".format(j)] = increment * float(j + 1)

    return value_dict


@app.route("/get-data")
def get_data():
    full_start_time = datetime.now()
    start_time = datetime.now()

    # Get parameters from querystring

    map_left = request.args.get('ml')
    map_bottom = request.args.get('mb')
    map_right = request.args.get('mr')
    map_top = request.args.get('mt')

    stat_id = request.args.get('s')
    table_id = request.args.get('t')
    boundary_name = request.args.get('b')
    zoom_level = int(request.args.get('z'))

    # get the number of decimal places for the output GeoJSON to reduce response size & speed up rendering
    decimal_places = utils.get_decimal_places(zoom_level)

    # TODO: add support for equations

    # TODO: add support for density stats. eg B1 / areasqkm

    # get the boundary table name from zoom level
    if boundary_name is None:
        boundary_name = utils.get_boundary_name(zoom_level)

    # # get boundary primary key name
    # boundary_primary_key = ""
    # for boundary_dict in settings['bdy_table_dicts']:
    #     if boundary_dict["boundary"] == boundary_name:
    #         boundary_primary_key = boundary_dict["primary_key"]

    display_zoom = str(zoom_level).zfill(2)

    stat_table_name = boundary_name + "_" + table_id

    # TESTING - switch 1
    # boundary_table_name = "zoom_{0}_{1}_{2}_aust".format(display_zoom, boundary_name, settings["census_year"])
    boundary_table_name = "{0}_zoom_{1}".format(boundary_name, display_zoom)
    # boundary_table_name = "{0}".format(boundary_name)

    # TESTING - switch 3
    boundary_schema = "{0}_display".format(settings['boundary_schema'])
    # boundary_schema = "{0}_display_2".format(settings['boundary_schema'])

    # # thin geometries to a default tolerance based on zoom level 17
    # tolerance = utils.get_simplify_vw_tolerance(17)

    with get_db_cursor() as pg_cur:
        print("Connected to database in {0}".format(datetime.now() - start_time))
        start_time = datetime.now()

        envelope_sql = "ST_MakeEnvelope({0}, {1}, {2}, {3}, 4283)".format(map_left, map_bottom, map_right, map_top)

        # TESTING - switch 3
        geom_sql = "ST_AsGeoJSON(bdy.geom, {0})::jsonb".format(decimal_places)
        # geom_sql = "ST_AsGeoJSON(ST_Transform(ST_SimplifyVW(ST_Transform(bdy.geom, 3577), {0}), 4326), {1})::jsonb".format(tolerance, decimal_places)

        # TESTING - switch 4
        # sql = "SELECT bdy.id, bdy.name, bdy.area, tab.{0}, " \
        sql = "SELECT bdy.id, bdy.name, tab.{0} / bdy.area AS density, " \
              "CASE WHEN bdy.population > 0 THEN tab.{0} / bdy.population * 100.0 ELSE 0 END AS percent, " \
              "tab.{0}, {1} AS geometry " \
              "FROM {2}.{3} AS bdy " \
              "INNER JOIN {4}.{5} AS tab ON bdy.id = tab.{6} " \
              "WHERE bdy.geom && {7}" \
            .format(stat_id, geom_sql, boundary_schema, boundary_table_name, settings['data_schema'],
                    stat_table_name, settings['region_id_field'], envelope_sql)

        try:
            pg_cur.execute(sql)
        except psycopg2.Error:
            return "I can't SELECT : " + sql

        # print("Ran query in {0}".format(datetime.now() - start_time))
        # start_time = datetime.now()

        # Retrieve the results of the query
        rows = pg_cur.fetchall()
        # row_count = pg_cur.rowcount

        # Get the column names returned
        col_names = [desc[0] for desc in pg_cur.description]

    print("Got records from Postgres in {0}".format(datetime.now() - start_time))
    start_time = datetime.now()

    # # Find the index of the column that holds the geometry
    # geom_index = col_names.index("geometry")

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

    print("Parsed records into JSON in {1}".format(i, datetime.now() - start_time))
    print("Returned {0} records  {1}".format(i, datetime.now() - full_start_time))

    return Response(json.dumps(output_dict), mimetype='application/json')


if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=8081)
