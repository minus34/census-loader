#!/usr/bin/env bash

#!/usr/bin/env bash

SECONDS=0*

CENSUS_YEAR="2021"
OUTPUT_FOLDER="/Users/$(whoami)/tmp"

DATA_SCHEMA="census_${CENSUS_YEAR}_data"
BDYS_SCHEMA="census_${CENSUS_YEAR}_bdys"
WEB_SCHEMA="census_${CENSUS_YEAR}_web"

# dump schemas to backup files
#/Applications/Postgres.app/Contents/Versions/13/bin/pg_dump -Fc -d geo -n ${DATA_SCHEMA} -p 5432 -U postgres -f ${OUTPUT_FOLDER}/${DATA_SCHEMA}.dmp
/Applications/Postgres.app/Contents/Versions/13/bin/pg_dump -Fc -d geo -n ${BDYS_SCHEMA} -p 5432 -U postgres -f ${OUTPUT_FOLDER}/${BDYS_SCHEMA}.dmp
#/Applications/Postgres.app/Contents/Versions/13/bin/pg_dump -Fc -d geo -n ${WEB_SCHEMA} -p 5432 -U postgres -f ${OUTPUT_FOLDER}/${WEB_SCHEMA}.dmp


# OPTIONAL - copy files to AWS S3 and allow public read access (requires awscli installed)
cd ${OUTPUT_FOLDER}

for f in census_${CENSUS_YEAR}_*.dmp;
  do
    aws --profile=default s3 cp --storage-class REDUCED_REDUNDANCY ./${f} s3://minus34.com/opendata/census-${CENSUS_YEAR}/${f};
    aws --profile=default s3api put-object-acl --acl public-read --bucket minus34.com --key opendata/census-${CENSUS_YEAR}/${f}
  done
