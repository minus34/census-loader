#!/usr/bin/env bash

# NOTE: requires GDAL to be installed

# set this to taste - NOTE: you can't use "~" for your home folder
output_folder="/Users/$(whoami)/tmp/census_2021_bdys"


docker run --rm -it -v ${output_folder}:/data osgeo/gdal:latest \
  ogr2ogr -f Parquet \
    /data/sa1_2021_aust_gda94.parquet \
    /data/sa1_2021_aust_gda94.gpkg \
    -dialect SQLite \
    -sql "SELECT * FROM 'sql_statement'" \
    -lco COMPRESSION=BROTLI \
    -lco GEOMETRY_ENCODING=GEOARROW \
    -lco POLYGON_ORIENTATION=COUNTERCLOCKWISE \
    -lco ROW_GROUP_SIZE=9999999


#apt update
#apt install -y -V ca-certificates lsb-release wget
#wget https://apache.jfrog.io/artifactory/arrow/$(lsb_release --id --short | tr 'A-Z' 'a-z')/apache-arrow-apt-source-latest-$(lsb_release --codename --short).deb
#apt install -y -V ./apache-arrow-apt-source-latest-$(lsb_release --codename --short).deb
#apt update
#apt install -y -V libarrow-dev # For C++
#apt install -y -V libarrow-glib-dev # For GLib (C)
#apt install -y -V libarrow-dataset-dev # For Apache Arrow Dataset C++
#apt install -y -V libarrow-dataset-glib-dev # For Apache Arrow Dataset GLib (C)
#apt install -y -V libarrow-flight-dev # For Apache Arrow Flight C++
#apt install -y -V libarrow-flight-glib-dev # For Apache Arrow Flight GLib (C)
## Notes for Plasma related packages:
##   * You need to enable "non-free" component on Debian GNU/Linux
##   * You need to enable "multiverse" component on Ubuntu
##   * You can use Plasma related packages only on amd64
#apt install -y -V libplasma-dev # For Plasma C++
#apt install -y -V libplasma-glib-dev # For Plasma GLib (C)
#apt install -y -V libgandiva-dev # For Gandiva C++
#apt install -y -V libgandiva-glib-dev # For Gandiva GLib (C)
#apt install -y -V libparquet-dev # For Apache Parquet C++
#apt install -y -V libparquet-glib-dev # For Apache Parquet GLib (C)


# full addresses
ogr2ogr -f FlatGeobuf ${output_folder}/address-principals-202205.fgb \
PG:"host=localhost dbname=geo user=postgres password=password port=5432" "gnaf_202205.address_principals(geom)"

# just GNAF PIDs and point geometries
ogr2ogr -f FlatGeobuf ${output_folder}/address-principals-lite-202102.fgb \
PG:"host=localhost dbname=geo user=postgres password=password port=5432" -sql "select gnaf_pid, ST_Transform(geom, 4326) as geom from gnaf_202102.address_principals"

# display locality boundaries
ogr2ogr -f FlatGeobuf ${output_folder}/address-principals-202205.fgb \
PG:"host=localhost dbname=geo user=postgres password=password port=5432" "admin_bdys_202205.locality_bdys_display(geom)"

# OPTIONAL - copy files to AWS S3 and allow public read access (requires AWSCLI installed and your AWS credentials setup)
cd ${output_folder}

for f in *-202205.fgb;
  do
    aws --profile=default s3 cp --storage-class REDUCED_REDUNDANCY ./${f} s3://minus34.com/opendata/geoscape-202205/flatgeobuf/${f};
    aws --profile=default s3api put-object-acl --acl public-read --bucket minus34.com --key opendata/geoscape-202205/flatgeobuf/${f}
    echo "${f} uploaded to AWS S3"
  done
