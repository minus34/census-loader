#!/usr/bin/env bash

# --------------------------------------------
# STEP 1 - update, upgrade and install stuff
# --------------------------------------------

# update and upgrade Ubuntu
sudo DEBIAN_FRONTEND=noninteractive apt-get -q -y update
sudo DEBIAN_FRONTEND=noninteractive apt-get -q -y -o Dpkg::Options::="--force-confdef" -o Dpkg::Options::="--force-confold" dist-upgrade

# get census-loader code (note: creates the folder to download the PG dump file into)
sudo git clone https://github.com/minus34/census-loader.git ~/git/census-loader/

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

# alter postgres user and create database
sudo -u postgres psql -c "ALTER USER postgres PASSWORD '<postgres-password>';"
sudo -u postgres createdb geo
sudo -u postgres psql -c "CREATE EXTENSION adminpack;CREATE EXTENSION postgis;" geo

# create read only user and grant access to all tables & sequences
sudo -u postgres psql -c "CREATE USER rouser WITH ENCRYPTED PASSWORD '<rouser-password>';" geo
sudo -u postgres psql -c "GRANT CONNECT ON DATABASE geo TO rouser;" geo
sudo -u postgres psql -c "GRANT USAGE ON SCHEMA public TO rouser;" geo
sudo -u postgres psql -c "GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO rouser;" geo
sudo -u postgres psql -c "GRANT SELECT ON ALL TABLES IN SCHEMA public to rouser;" geo
sudo -u postgres psql -c "GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO rouser;" geo  # for PostGIS functions

## copy Postgres dump files to server
#sudo wget -q http://minus34.com/opendata/census-2016/census_2016_data.dmp -O ~/git/census-loader/data/data.dmp
#sudo wget -q http://minus34.com/opendata/census-2016/census_2016_web.dmp -O ~/git/census-loader/data/web.dmp
#
## import Postgres dump files into database
#sudo pg_restore -Fc -v -d geo -p 5432 -U postgres -h localhost ~/git/census-loader/data/web.dmp
#sudo pg_restore -Fc -v -d geo -p 5432 -U postgres -h localhost ~/git/census-loader/data/data.dmp
#
## census_2016_data schema
#sudo -u postgres psql -c "GRANT USAGE ON SCHEMA census_2016_data TO rouser;" geo
#sudo -u postgres psql -c "GRANT SELECT ON ALL SEQUENCES IN SCHEMA census_2016_data TO rouser;" geo
#sudo -u postgres psql -c "GRANT SELECT ON ALL TABLES IN SCHEMA census_2016_data to rouser;" geo
#sudo -u postgres psql -c "ALTER DEFAULT PRIVILEGES IN SCHEMA census_2016_data GRANT SELECT ON SEQUENCES TO rouser;" geo
#sudo -u postgres psql -c "ALTER DEFAULT PRIVILEGES IN SCHEMA census_2016_data GRANT SELECT ON TABLES TO rouser;" geo
## census_2016_web schema
#sudo -u postgres psql -c "GRANT USAGE ON SCHEMA census_2016_web TO rouser;" geo
#sudo -u postgres psql -c "GRANT SELECT ON ALL SEQUENCES IN SCHEMA census_2016_web TO rouser;" geo
#sudo -u postgres psql -c "GRANT SELECT ON ALL TABLES IN SCHEMA census_2016_web to rouser;" geo
#sudo -u postgres psql -c "ALTER DEFAULT PRIVILEGES IN SCHEMA census_2016_web GRANT SELECT ON SEQUENCES TO rouser;" geo
#sudo -u postgres psql -c "ALTER DEFAULT PRIVILEGES IN SCHEMA census_2016_web GRANT SELECT ON TABLES TO rouser;" geo

# stuff for Zappa and AWS Lambda testing
sudo wget -q http://minus34.com/test/zappa/admin_bdys_201705_display.dmp -O ~/git/census-loader/data/admin_bdys_201705_display.dmp
sudo pg_restore -Fc -v -d geo -p 5432 -U postgres -h localhost ~/git/census-loader/data/admin_bdys_201705_display.dmp

sudo -u postgres psql -c "GRANT USAGE ON SCHEMA admin_bdys_201705_display TO rouser;" geo
sudo -u postgres psql -c "GRANT SELECT ON ALL SEQUENCES IN SCHEMA admin_bdys_201705_display TO rouser;" geo
sudo -u postgres psql -c "GRANT SELECT ON ALL TABLES IN SCHEMA admin_bdys_201705_display to rouser;" geo
sudo -u postgres psql -c "ALTER DEFAULT PRIVILEGES IN SCHEMA admin_bdys_201705_display GRANT SELECT ON SEQUENCES TO rouser;" geo
sudo -u postgres psql -c "ALTER DEFAULT PRIVILEGES IN SCHEMA admin_bdys_201705_display GRANT SELECT ON TABLES TO rouser;" geo

# alter whitelisted postgres clients (the AWS Lamdba and the test client)
#export HBAFILE=$(pg_conftool -s 9.6 main show hba_file)
#echo $HBAFILE
sudo sed -i -e "s/#listen_addresses = 'localhost'/listen_addresses = '*'/g" /etc/postgresql/9.6/main/postgresql.conf
echo -e "host\t geo\t rouser\t 0.0.0.0/0\t md5" | sudo tee -a /etc/postgresql/9.6/main/pg_hba.conf
#echo -e "host\t geo\t rouser\t 859uppjni0.execute-api.ap-southeast-2.amazonaws.com\t md5" | sudo tee -a /etc/postgresql/9.6/main/pg_hba.conf
echo -e "host\t geo\t rouser\t 101.164.227.2/22\t md5" | sudo tee -a /etc/postgresql/9.6/main/pg_hba.conf
#echo -e "host\t all\t all\t 101.164.227.2/22\t md5" | sudo tee -a /etc/postgresql/9.6/main/pg_hba.conf
sudo service postgresql restart

# delete dump files
cd ~/git/census-loader/data
sudo find . -name "*.dmp" -type f -delete


