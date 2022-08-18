#!/usr/bin/env bash

# get the directory this script is running from
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

# load both sets of census boundaries
. ${SCRIPT_DIR}/run.sh 2021 GDA94
. ${SCRIPT_DIR}/run.sh 2021 GDA2020

## load census data
#python.exe load-census.py --census-data-path=/Users/$(whoami)/tmp/census_2021_data --census-bdys-path=/Users/$(whoami)/tmp/census_2021_boundaries
