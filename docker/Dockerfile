FROM debian:bookworm-slim

# replaced the downloading of the Postgres dump files to use local files instead (for performance)
# ARG BASE_URL="https://minus34.com/opendata/geoscape-202502"
# ENV BASE_URL ${BASE_URL}

ENV DEBIAN_FRONTEND=noninteractive

ARG CENSUS_YEAR="2021"
ENV CENSUS_YEAR ${CENSUS_YEAR}

ARG DATUM="gda94"
ENV DATUM ${DATUM}

# Postgres user password - WARNING: change this to something a lot more secure
ARG pg_password="password"
ENV PGPASSWORD=${pg_password}

# update debian & get pre-requsities
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    lsb-release \
    sudo \
    && rm -rf /var/lib/apt/lists/*

# get postgres signing key, add Postgres repo to apt and install Postgres with PostGIS
RUN wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | gpg --dearmor -o /usr/share/keyrings/postgresql-archive-keyring.gpg
RUN echo "deb [signed-by=/usr/share/keyrings/postgresql-archive-keyring.gpg] http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list

RUN apt-get update && apt-get install -y \
    postgresql-16 \
    postgresql-client-16 \
    postgresql-16-postgis-3 \
    && rm -rf /var/lib/apt/lists/*

# start Postgres server and set the default user password
RUN /etc/init.d/postgresql start \
    && sudo -u postgres psql -c "ALTER USER postgres PASSWORD '${pg_password}';" \
    && sudo -u postgres psql -c "ALTER SYSTEM SET autovacuum = off;" \
    && sudo -u postgres psql -c "SELECT PG_RELOAD_CONF();" \
    && sudo -u postgres psql -c "CREATE EXTENSION postgis;" \
    && /etc/init.d/postgresql stop

# download and restore Census Postgres dump files
RUN mkdir -p /data
WORKDIR /data

# add local postgres dump files
ADD census_${CENSUS_YEAR}_data.dmp .
ADD census_${CENSUS_YEAR}_bdys_${DATUM}.dmp .

# replace the add statements above if wanting to download Postgres dump files
# RUN /data \
#     && wget --quiet ${BASE_URL}/census_${CENSUS_YEAR}_data.dmp \
#     && wget --quiet ${BASE_URL}/census_${CENSUS_YEAR}_bdys_${DATUM}.dmp

RUN /etc/init.d/postgresql start \
    && pg_restore -Fc -d postgres -h 127.0.0.1 -p 5432 -U postgres /data/census_${CENSUS_YEAR}_data.dmp \
    && pg_restore -Fc -d postgres -h 127.0.0.1 -p 5432 -U postgres /data/census_${CENSUS_YEAR}_bdys_${DATUM}.dmp \
    && /etc/init.d/postgresql stop \
    && rm /data/*.dmp

# enable external access to postgres - WARNING: these are insecure settings! Edit these to restrict access
RUN echo "host all  all    0.0.0.0/0  md5" >> /etc/postgresql/16/main/pg_hba.conf
RUN echo "listen_addresses='*'" >> /etc/postgresql/16/main/postgresql.conf

EXPOSE 5432

# set user for postgres startup
USER postgres

# # Add VOLUMEs to allow backup of config, logs and databases
# VOLUME  ["/etc/postgresql", "/var/log/postgresql", "/var/lib/postgresql"]

# Start postgres when starting the container
CMD ["/usr/lib/postgresql/16/bin/postgres", "-D", "/var/lib/postgresql/16/main", "-c", "config_file=/etc/postgresql/16/main/postgresql.conf"]