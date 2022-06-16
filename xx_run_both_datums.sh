#!/usr/bin/env bash

# get the directory this script is running from
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

. ${SCRIPT_DIR}/run.sh GDA94
. ${SCRIPT_DIR}/run.sh GDA2020
