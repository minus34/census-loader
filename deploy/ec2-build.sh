#!/usr/bin/env bash

# install pre-reqs
sudo apt-get -y update
sudo apt-get install postgresql-9.6-postgis-2.3 pgadmin3 postgresql-contrib postgresql-server-dev-9.6 python-dev
sudo pip install flask
sudo pip install flask-compress
sudo pip install psycopg2

# config postgres



#
## Wait for Postgres to start.
#CHECK_CMD="psql -h localhost -U postgres -c \dt"
#echo "Starting PostGIS to import data..."
#(docker-entrypoint.sh postgres && sleep 5 &)
#n=0
#nchecks=10
#until [ $n -ge $nchecks ]
#do
#    let n+=1
#    echo "Checking ${n} of ${nchecks} if PostGIS is up..."
#    $CHECK_CMD > /dev/null && break
#    sleep 5
#done
#$CHECK_CMD > /dev/null
#if [ $? == 0 ]; then
#    echo "PostGIS is up and running"
#    $CHECK_CMD
#else
#    echo "PostGIS failed to start"
#    exit 1
#fi


## load data into pg
#
#
## get code
#sudo git clone https://github.com/minus34/locate16-hack.git ~/git/census-loader/
#
## run the app
#sudo python ~/git/census-loader/deploy/web/server.py
#sudo gunicorn -w 4 -b 0.0.0.0:80 server:app








