#!/usr/bin/env python
# -*- coding: utf-8 -*-

from psycopg2.extensions import AsIs


def get_min_max(data_table, boundary_table, stat_field, num_classes, min_val, map_type, pg_cur, settings):

    # query to get min and max values (filter small populations that overly influence the map visualisation)
    try:
        # if map_type == "values":
        sql = "SELECT MIN(%s) AS min, MAX(%s) AS max FROM %s AS tab " \
              "INNER JOIN %s AS bdy ON tab.{0} = bdy.id " \
              "WHERE %s > 0 " \
              "AND bdy.population > {1}" \
            .format(settings['region_id_field'], float(min_val))

        sql_string = pg_cur.mogrify(sql, (AsIs(stat_field), AsIs(stat_field), AsIs(data_table),
                                          AsIs(boundary_table), AsIs(stat_field)))

        pg_cur.execute(sql_string)
        row = pg_cur.fetchone()

    except Exception as ex:
        print("{0} - {1} Failed: {2}".format(data_table, stat_field, ex))
        return list()

    output_dict = {
        "min": row["min"],
        "max": row["max"]
    }

    return output_dict


def get_kmeans_bins(data_table, boundary_table, stat_field, num_classes, min_val, map_type, pg_cur, settings):

    # query to get min and max values (filter small populations that overly influence the map visualisation)
    try:
        if map_type == "values":
            sql = "WITH sub AS (" \
                  "WITH points AS (" \
                  "SELECT %s as val, ST_MakePoint(%s, 0) AS pnt " \
                  "FROM %s AS tab " \
                  "INNER JOIN %s AS bdy ON tab.{0} = bdy.id " \
                  "WHERE %s > 0.0 " \
                  "AND bdy.population > {1}" \
                  ") " \
                  "SELECT val, ST_ClusterKMeans(pnt, %s) OVER () AS cluster_id FROM points" \
                  ") " \
                  "SELECT MAX(val) AS val FROM sub GROUP BY cluster_id ORDER BY val" \
                .format(settings['region_id_field'], float(min_val))

            sql_string = pg_cur.mogrify(sql, (AsIs(stat_field), AsIs(stat_field), AsIs(data_table),
                                              AsIs(boundary_table), AsIs(stat_field), AsIs(num_classes)))

        else:  # map_type == "percent"
            sql = "WITH sub AS (" \
                  "WITH points AS (" \
                  "SELECT %s as val, ST_MakePoint(%s, 0) AS pnt " \
                  "FROM %s AS tab " \
                  "INNER JOIN %s AS bdy ON tab.{0} = bdy.id " \
                  "WHERE %s > 0.0 AND %s < 100.0 " \
                  "AND bdy.population > {1}" \
                  ") " \
                  "SELECT val, ST_ClusterKMeans(pnt, %s) OVER () AS cluster_id FROM points" \
                  ") " \
                  "SELECT MAX(val) AS val FROM sub GROUP BY cluster_id ORDER BY val" \
                .format(settings['region_id_field'], float(min_val))

            sql_string = pg_cur.mogrify(sql, (AsIs(stat_field), AsIs(stat_field), AsIs(data_table),
                                              AsIs(boundary_table), AsIs(stat_field), AsIs(stat_field),
                                              AsIs(num_classes)))

        pg_cur.execute(sql_string)
        rows = pg_cur.fetchall()

    except Exception as ex:
        print("{0} - {1} Failed: {2}".format(data_table, stat_field, ex))
        return list()

    # census_2011_data.ced_b23a - b4318

    output_list = list()

    for row in rows:
        output_list.append(row["val"])

    return output_list


def get_equal_interval_bins(data_table, boundary_table, stat_field, num_classes, min_val, map_type, pg_cur, settings):

    # query to get min and max values (filter small populations that overly influence the map visualisation)
    try:
        if map_type == "values":
            sql = "SELECT MIN(%s) AS min, MAX(%s) AS max FROM %s AS tab " \
                  "INNER JOIN %s AS bdy ON tab.{0} = bdy.id " \
                  "WHERE %s > 0 " \
                  "AND bdy.population > {1}" \
                .format(settings['region_id_field'], float(min_val))

            sql_string = pg_cur.mogrify(sql, (AsIs(stat_field), AsIs(stat_field), AsIs(data_table),
                                              AsIs(boundary_table), AsIs(stat_field)))

        else:  # map_type == "percent"
            sql = "SELECT MIN(%s) AS min, MAX(%s) AS max FROM %s AS tab " \
                  "INNER JOIN %s AS bdy ON tab.{0} = bdy.id " \
                  "WHERE %s > 0 AND %s < 100.0 " \
                  "AND bdy.population > {1}" \
                .format(settings['region_id_field'], float(min_val))

            sql_string = pg_cur.mogrify(sql, (AsIs(stat_field), AsIs(stat_field), AsIs(data_table),
                                              AsIs(boundary_table), AsIs(stat_field), AsIs(stat_field)))

        pg_cur.execute(sql_string)
        row = pg_cur.fetchone()

    except Exception as ex:
        print("{0} - {1} Failed: {2}".format(data_table, stat_field, ex))
        return list()

    output_list = list()

    min_val = row["min"]
    max_val = row["max"]
    delta = (max_val - min_val) / float(num_classes)
    curr_val = min_val

    # print("{0} : from {1} to {2}".format(boundary_table, min, max))

    for i in range(0, num_classes):
        output_list.append(curr_val)
        curr_val += delta

    return output_list


def get_equal_count_bins(data_table, boundary_table, stat_field, num_classes, min_val, map_type, pg_cur, settings):

    # query to get min and max values (filter small populations that overly influence the map visualisation)
    try:
        if map_type == "values":
            sql = "WITH classes AS (" \
                  "SELECT %s as val, ntile(%s) OVER (ORDER BY %s) AS class_id " \
                  "FROM %s AS tab " \
                  "INNER JOIN %s AS bdy ON tab.{0} = bdy.id " \
                  "WHERE %s > 0.0 " \
                  "AND bdy.population > {1}" \
                  ") " \
                  "SELECT MAX(val) AS val, class_id FROM classes GROUP BY class_id ORDER BY class_id" \
                .format(settings['region_id_field'], float(min_val))

            sql_string = pg_cur.mogrify(sql, (AsIs(stat_field), AsIs(num_classes), AsIs(stat_field), AsIs(data_table),
                                              AsIs(boundary_table), AsIs(stat_field)))

        else:  # map_type == "percent"
            sql = "WITH classes AS (" \
                  "SELECT %s as val, ntile(7) OVER (ORDER BY %s) AS class_id " \
                  "FROM %s AS tab " \
                  "INNER JOIN %s AS bdy ON tab.{0} = bdy.id " \
                  "WHERE %s > 0.0 AND %s < 100.0 " \
                  "AND bdy.population > {1}" \
                  ") " \
                  "SELECT MAX(val) AS val, class_id FROM classes GROUP BY class_id ORDER BY class_id" \
                .format(settings['region_id_field'], float(min_val))

            sql_string = pg_cur.mogrify(sql, (AsIs(stat_field), AsIs(stat_field), AsIs(data_table),
                                              AsIs(boundary_table), AsIs(stat_field), AsIs(stat_field)))

        # print(sql_string)

        pg_cur.execute(sql_string)
        rows = pg_cur.fetchall()

    except Exception as ex:
        print("{0} - {1} Failed: {2}".format(data_table, stat_field, ex))
        return list()

    output_list = list()

    for row in rows:
        output_list.append(row["val"])

    return output_list
