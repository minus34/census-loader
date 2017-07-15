#!/usr/bin/env bash

# -------------------------------
# STEP 1 - install stuff
# -------------------------------

# update Ubuntu
sudo apt-get update

# insatll AWS CLI tools
sudo apt -y install awscli

# install Postgres
sudo add-apt-repository -y "deb http://apt.postgresql.org/pub/repos/apt/ xenial-pgdg main"
wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -
sudo apt -y update
sudo apt -y install postgresql-9.6 postgresql-contrib-9.6

# create user and database
sudo -u postgres createuser -P hugh
sudo -u postgres createdb -O hugh geo
sudo -u postgres psql -c "GRANT postgres TO hugh; " geo

# install and configure postgis
sudo add-apt-repository -y ppa:ubuntugis/ppa
sudo apt -y update
sudo apt -y install postgis postgresql-9.6-postgis-2.3
sudo -u postgres psql -c "CREATE EXTENSION postgis; " geo

#install python modules
sudo apt-get -y install python3-setuptools
sudo easy_install3 pip
sudo pip3.5 install flask
sudo pip3.5 install flask-compress
sudo pip3.5 install psycopg2

# install gunicorn
sudo apt -y install gunicorn

# get code
sudo git clone https://github.com/minus34/census-loader.git ~/git/census-loader/


# ----------------------------------------------
# STEP 2 - copy data and restore into Postgres
# ----------------------------------------------

# copy files
sudo aws s3 cp s3://minus34.com/opendata/census-2016 ~/git/census-loader/data --recursive

# need to set postgres settings, including autovacuum off
sudo vim

# import into database
sudo pg_restore -Fc -d geo -p 5432 -U hugh -h localhost ~/git/census-loader/data/census_2016_data.dmp
#sudo pg_restore -Fc -d geo -p 5432 -U hugh ~/git/census-loader/data/census_2016_bdys.dmp  # don't need this one
sudo pg_restore -Fc -d geo -p 5432 -U hugh -h localhost ~/git/census-loader/data/census_2016_web.dmp

# test data loaded ok
sudo -u postgres psql -c "SELECT Count(*) FROM census_2016_data.ste_t28b; " geo
sudo -u postgres psql -c "SELECT Count(*) FROM census_2016_web.ste; " geo

# set autovacuum off (need to change this to use sed to automate it)
sudo vim /etc/postgresql/9.6/main/postgresql.conf

## restart postgres - if needed
#sudo service postgresql restart

## look at log files - if needed
#vim /var/log/postgresql/postgresql-9.6-main.log

sudo -u postgres psql -c "SELECT Count(*) FROM census_2016_data.ste_t28b; " geo


# -------------------------------
# STEP 3 - run this thing
# -------------------------------

# run the app
sudo python3 ~/git/census-loader/deploy/web/server.py
sudo gunicorn -w 4 -b 0.0.0.0:80 server:app
