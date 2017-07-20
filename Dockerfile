FROM mdillon/postgis:9.6
MAINTAINER Alex Leith <aleith@crcsi.com.au>

# Do this first so it's cached
RUN apt-get update && \
	apt-get install -y python3 python3-pip \
	python3-pandas python3-xlrd python3-psycopg2

# Set the directory for the load process
ENV APPDIR=/app

# Set up a PGDATA directory, for persistence
ENV PGDATA=/opt/data

# Override these if necessary.
ENV POSTGRES_USER=census
ENV POSTGRES_PASSWORD=census

COPY data $APPDIR/data
WORKDIR $APPDIR

COPY docker-pg-loader.sh $APPDIR/docker-pg-loader.sh
COPY load-census.py $APPDIR/load-census.py
COPY web $APPDIR/web

# Launch the DB, wait until it is running and then run the load script
RUN $APPDIR/docker-pg-loader.sh

# Clean up
RUN rm $APPDIR/data
