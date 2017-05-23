

import ast
import json
import math
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


@app.route("/get-data")
def bdys():
    full_start_time = datetime.now()
    start_time = datetime.now()

    # Get parameters from querystring
    stats = request.args.get('stats')
    map_left = request.args.get('ml')
    map_bottom = request.args.get('mb')
    map_right = request.args.get('mr')
    map_top = request.args.get('mt')
    zoom_level = int(request.args.get('z'))

    # get the number of decimal places for the output GeoJSON to reduce response size & speed up rendering
    decimal_places = utils.get_decimal_places(zoom_level)

    # get the boundary table name
    table_name = utils.get_boundary_name(zoom_level)

    with get_db_cursor() as pg_cur:
        print("Connected to database in {0}".format(datetime.now() - start_time))
        start_time = datetime.now()

        sql = "SELECT bdy.gid AS id, " \
              "ST_AsGeoJSON(bdy.geom, {0}) AS geometry FROM {1}.{2} " \
              "WHERE bdy.geom && ST_MakeEnvelope({3}, {4}, {5}, {6}, 4283)" \
            .format(decimal_places, settings['boundary_schema'], table_name, map_left, map_bottom, map_right, map_top)

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
                feature_dict["geometry"] = ast.literal_eval(row[col])
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