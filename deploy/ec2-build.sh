#!/usr/bin/env bash

# -------------------------------
# STEP 1 - install stuff
# -------------------------------

# update and upgrade Ubuntu
sudo DEBIAN_FRONTEND=noninteractive apt-get -q -y update
sudo DEBIAN_FRONTEND=noninteractive apt-get -q -y -o Dpkg::Options::="--force-confdef" -o Dpkg::Options::="--force-confold" dist-upgrade

# get code
sudo git clone https://github.com/minus34/census-loader.git ~/git/census-loader/

# copy Postgres dump files to server
sudo wget -q http://minus34.com/opendata/census-2016/census_2016_data.dmp -O ~/git/census-loader/data/data.zip
sudo wget -q http://minus34.com/opendata/census-2016/census_2016_web.dmp -O ~/git/census-loader/data/web.zip
sudo DEBIAN_FRONTEND=noninteractive apt-get -q -y install unzip
cd ~/git/census-loader/data
unzip data.zip -d ./data
unzip data.zip -d ./web

# install Postgres
sudo add-apt-repository -y "deb http://apt.postgresql.org/pub/repos/apt/ xenial-pgdg main"
wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -
sudo DEBIAN_FRONTEND=noninteractive apt-get -q -y update
sudo DEBIAN_FRONTEND=noninteractive apt-get -q -y install postgresql-9.6
sudo DEBIAN_FRONTEND=noninteractive apt-get -q -y install postgresql-9.6-postgis-2.3 postgresql-contrib-9.6
sudo DEBIAN_FRONTEND=noninteractive apt-get -q -y install postgis

# install python modules
sudo DEBIAN_FRONTEND=noninteractive apt-get -q -y install python3-setuptools
sudo easy_install3 pip
sudo pip3 install flask
sudo pip3 install flask-compress
sudo pip3 install psycopg2

# install gunicorn
sudo pip3 install gunicorn

# ---------------------------------------------------
# STEP 2 - restore data to Postgres and run server
# ---------------------------------------------------

# create user and database
sudo -u postgres psql -c "ALTER USER postgres PASSWORD 'password';"
#sudo -u postgres createuser -P censususer
sudo -u postgres createdb geo
#sudo -u postgres psql -c "GRANT postgres TO censususer; " geo
sudo -u postgres psql -c "CREATE EXTENSION adminpack;CREATE EXTENSION postgis;" geo

## import Postgres dump files into database
#sudo pg_restore -Fd -j 2 -v -d geo -p 5432 -U postgres -h localhost ~/git/census-loader/data/web
#sudo pg_restore -Fd -j 2 -v -d geo -p 5432 -U postgres -h localhost ~/git/census-loader/data/data

## delete dump files
cd ~/git/census-loader/data
sudo find . -name "*.dmp" -type f -delete

# ----------------------
# STEP 3 - run the app
# ----------------------

# run 2 Python/Flask map servers in the background
sudo gunicorn -w 2 -D --chdir /home/ubuntu/git/census-loader/web/ --pythonpath ~/git/census-loader/web/ -b 0.0.0.0:80 single_server:app

# TODO: Put NGINX in front of gunicorn as a reverse proxy
