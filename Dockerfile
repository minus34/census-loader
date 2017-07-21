FROM mdillon/postgis:9.6
MAINTAINER Alex Leith <aleith@crcsi.com.au>

# Set up a PGDATA directory, for persistence
ENV PGDATA=/opt/data

# Override these if necessary.
ENV POSTGRES_USER=census
ENV POSTGRES_PASSWORD=census

# Get the data from Hugh (thanks, Hugh!)
RUN mkdir -p /tmp/dumps/
ADD http://minus34.com/opendata/census-2016/census_2016_data.dmp /tmp/dumps/
ADD http://minus34.com/opendata/census-2016/census_2016_bdys.dmp /tmp/dumps/
ADD http://minus34.com/opendata/census-2016/census_2016_web.dmp  /tmp/dumps/

ADD docker-pg-loader.sh /tmp/

# Launch the DB, wait until it is running and then restore the dumps
RUN /tmp/docker-pg-loader.sh

# Clean up
RUN rm -rf /tmp/dumps
