#!/usr/bin/env bash

# -------------------------------
# STEP 1 - install stuff
# -------------------------------

# try to silence annoying message about not having a UI
export DEBIAN_FRONTEND=noninteractive

# update Ubuntu
sudo apt-get update -y
# sudo apt-get upgrade -y

# get code
sudo git clone https://github.com/minus34/census-loader.git ~/git/census-loader/

# copy Postgres dump files to server
#cd ~/git/census-loader/data/
sudo wget -q http://minus34.com/opendata/census-2016/census_2016_data.dmp -O ~/git/census-loader/data/data.dmp
sudo wget -q http://minus34.com/opendata/census-2016/census_2016_web.dmp -O ~/git/census-loader/data/web.dmp

# install Postgres
sudo add-apt-repository -y "deb http://apt.postgresql.org/pub/repos/apt/ xenial-pgdg main"
wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -
sudo apt-get update -y
sudo apt-get install -y postgresql-9.6
sudo apt-get install -y postgresql-9.6-postgis-2.3 postgresql-contrib-9.6
sudo apt-get install -y postgis

# install python modules
sudo apt-get install -y python3-setuptools
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

# import into database
sudo pg_restore -Fc -v -d geo -p 5432 -U postgres -h localhost ~/git/census-loader/data/web.dmp
# this hangs - don't know why
sudo pg_restore -Fc -v -d geo -p 5432 -U postgres -h localhost ~/git/census-loader/data/data.dmp

# delete files
cd ~/git/census-loader/data
rm *.dmp

# ----------------------
# STEP 3 - run the app
# ----------------------

# run 4 Python map servers in the background - these next 2 commands need to be run in the console

cd ~/git/census-loader/web
sudo gunicorn -D -w 4 -b 0.0.0.0:80 single_server:app

# TODO: Put NGINX in front of gunicorn as a reverse proxy
