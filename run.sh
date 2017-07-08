#!/usr/bin/env bash

cd ~/git/minus34/census-loader

python.exe load-census.py --census-year=2011 --data-schema=census_2011_data --boundary-schema=census_2011_bdys --web-schema=census_2011_web --census-data-path=C:\minus34\data\abs_census_2011_data --census-bdys-path=C:\minus34\data\abs_census_2011_boundaries
#python.exe load-census.py --census-year=2016 --data-schema=census_2016_data --boundary-schema=census_2016_bdys --web-schema=census_2016_web --census-data-path=C:\minus34\data\abs_census_2016_data --census-bdys-path=C:\minus34\data\abs_census_2016_boundaries
