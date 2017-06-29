FROM mdillon/postgis:9.6
MAINTAINER Alex Leith <aleith@crcsi.com.au>

# Do this first so it's cached
RUN apt-get update && \
	apt-get install -y python3 python3-pip \
	python3-pandas python3-xlrd python3-psycopg2

# Override these if necessary.
ENV POSTGRES_USER=census
ENV POSTGRES_PASSWORD=census

COPY . /app
WORKDIR /app

# Launch the DB and wait until it is running
RUN ls 
RUN /app/docker-pg-loader.sh
