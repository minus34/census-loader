#!/usr/bin/env bash

#
# downloads ABS Census DataPacks and unzips them
#

# function to download, unzip, and delete file
function getfile {
  filename="2021_$1_all_for_AUS_short-header.zip"
#  echo "  - Downloading ${filename}"
  # use insecure to enable downloading through man-in-the-middle proxy servers
  curl -O -L -s --insecure "https://www.abs.gov.au/census/find-census-data/datapacks/download/${filename}"
  unzip -o -q "${filename}" -d "$2"
  rm "${filename}"
}

SECONDS=0*

## WARNING: deletes the Census data directory
rm -rf "${DATA_PATH}"
mkdir -p "${DATA_PATH}"
cd "${DATA_PATH}"

echo "-------------------------------------------------------------------------"
echo "Downloading and unzipping DataPacks"
echo "-------------------------------------------------------------------------"

for datapack in "GCP" "IP" "TSP" "PEP" "WPP"
do
  echo "- processing ${datapack}"
  getfile "${datapack}" "${DATA_PATH}"
done

duration=$SECONDS
echo "DataPacks downloaded in $((duration / 60)) mins"
