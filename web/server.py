
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
from psycopg2.extensions import AsIs
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


@app.route("/get-metadata")
def get_metadata():
    full_start_time = datetime.now()
    start_time = datetime.now()

    # Get parameters from querystring
    num_classes = int(request.args.get('n'))
    raw_stats = request.args.get('stats')

    # replace all maths operators to get list of all the stats we need
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

    for zoom_level in range(0, 16):
        bdy_name = utils.get_boundary_name(zoom_level)

        if bdy_name not in boundary_names:
            boundary_names.append(bdy_name)

    # get stats metadata, including the all important table number and map type (raw values based or normalised by pop)
    sql = "SELECT lower(sequential_id) AS id, " \
          "lower(table_number) AS \"table\", " \
          "replace(long_id, '_', ' ') AS description, " \
          "column_heading_description AS type, " \
          "CASE WHEN lower(long_id) LIKE '%%median%%' OR lower(long_id) LIKE '%%average%%' THEN 'values' " \
          "ELSE 'normalised' END AS maptype " \
          "FROM {0}.metadata_stats " \
          "WHERE lower(sequential_id) IN %s " \
          "ORDER BY sequential_id".format(settings["data_schema"], )

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

    # output_array = list()

    # # get metadata for all boundaries (done in one go for frontend performance)
    # for boundary_name in boundary_names:
    #     output_dict = dict()
    #     output_dict["boundary"] = boundary_name
    #
    #     boundary_table = "{0}.{1}".format(settings["web_schema"], boundary_name)

    feature_array = list()

    # For each row returned assemble a dictionary
    for row in rows:
        feature_dict = dict(row)
        feature_dict["id"] = feature_dict["id"].lower()
        feature_dict["table"] = feature_dict["table"].lower()

        for boundary_name in boundary_names:
            boundary_table = "{0}.{1}".format(settings["web_schema"], boundary_name)

            data_table = "{0}.{1}_{2}".format(settings["data_schema"], boundary_name, feature_dict["table"])

            # get the values for the map classes
            with get_db_cursor() as pg_cur:
                stat_field = "CASE WHEN bdy.population > 0 THEN tab.{0} / bdy.population * 100.0 ELSE 0 END" \
                    .format(feature_dict["id"], )
                feature_dict[boundary_name] = utils.get_equal_interval_bins(
                    data_table, boundary_table, stat_field, pg_cur, settings)

        # add dict to output array of metadata
        feature_array.append(feature_dict)

    response_dict["stats"] = feature_array
    # output_array.append(output_dict)

    # print("Got metadata for {0} in {1}".format(boundary_name, datetime.now() - start_time))

    # # Assemble the JSON
    # response_dict["boundaries"] = output_array

    print("Returned metadata in {0}".format(datetime.now() - full_start_time))

    return Response(json.dumps(response_dict), mimetype='application/json')


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

    # # get the number of decimal places for the output GeoJSON to reduce response size & speed up rendering
    # decimal_places = utils.get_decimal_places(zoom_level)

    # TODO: add support for equations

    # get the boundary table name from zoom level
    if boundary_name is None:
        boundary_name = utils.get_boundary_name(zoom_level)

    display_zoom = str(zoom_level).zfill(2)

    # stat_table_name = boundary_name + "_" + table_id
    #
    # boundary_table_name = "{0}".format(boundary_name)

    with get_db_cursor() as pg_cur:
        print("Connected to database in {0}".format(datetime.now() - start_time))
        start_time = datetime.now()

        # envelope_sql = "ST_MakeEnvelope({0}, {1}, {2}, {3}, 4283)".format(map_left, map_bottom, map_right, map_top)
        # geom_sql = "geojson_{0}".format(display_zoom)

        # build SQL with SQL injection protection
        sql = "SELECT bdy.id, bdy.name, bdy.population, tab.%s / bdy.area AS density, " \
              "CASE WHEN bdy.population > 0 THEN tab.%s / bdy.population * 100.0 ELSE 0 END AS percent, " \
              "tab.%s, geojson_%s AS geometry " \
              "FROM {0}.%s AS bdy " \
              "INNER JOIN {1}.%s_%s AS tab ON bdy.id = tab.{2} " \
              "WHERE bdy.geom && ST_MakeEnvelope(%s, %s, %s, %s, 4283) LIMIT ALL" \
            .format(settings['web_schema'], settings['data_schema'], settings['region_id_field'])

        try:
            # print(pg_cur.mogrify(sql, (AsIs(stat_id), AsIs(stat_id), AsIs(stat_id), AsIs(display_zoom), AsIs(boundary_name), AsIs(boundary_name), AsIs(table_id), AsIs(map_left), AsIs(map_bottom), AsIs(map_right), AsIs(map_top))))

            # yes, this is ridiculous - if someone can find a shorthand way of doing this then great!
            pg_cur.execute(sql, (AsIs(stat_id), AsIs(stat_id), AsIs(stat_id), AsIs(display_zoom),
                                 AsIs(boundary_name), AsIs(boundary_name), AsIs(table_id), AsIs(map_left),
                                 AsIs(map_bottom), AsIs(map_right), AsIs(map_top)))
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
    # import threading, webbrowser
    # # url = "http://127.0.0.1:8081?stats=B2712,B2772,B2775,B2778,B2781,B2793"
    # url = "http://127.0.0.1:8081/?stats=B2793&z=12"
    # threading.Timer(5, lambda: webbrowser.open(url)).start()

    app.run(host='0.0.0.0', port=8081, debug=True)

