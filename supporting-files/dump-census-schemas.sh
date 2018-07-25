#!/usr/bin/env bash

# set this to taste - NOTE: can't use "~" for your home folder
output_folder="/Users/hugh.saalmans/tmp"

# set to 2011 or 2016
census_year="2016"

# dump schemas to backup files
/Applications/Postgres.app/Contents/Versions/10/bin/pg_dump -Fc -d geo -n census_${census_year}_data -p 5432 -U postgres -f ${output_folder}/census_${census_year}_data.dmp
/Applications/Postgres.app/Contents/Versions/10/bin/pg_dump -Fc -d geo -n census_${census_year}_bdys -p 5432 -U postgres -f ${output_folder}/census_${census_year}_bdys.dmp
/Applications/Postgres.app/Contents/Versions/10/bin/pg_dump -Fc -d geo -n census_${census_year}_web -p 5432 -U postgres -f ${output_folder}/census_${census_year}_web.dmp

# dump using multiple workers (not tested - doesn't necessarily work)
#/Applications/Postgres.app/Contents/Versions/9.6/bin/pg_dump -Fd -j 4 -d geo -n census_2016_data -p 5432 -U postgres -f ~/tmp/census_2016_data
#/Applications/Postgres.app/Contents/Versions/9.6/bin/pg_dump -Fd -j 4 -d geo -n census_2016_bdys -p 5432 -U postgres -f ~/tmp/census_2016_bdys
#/Applications/Postgres.app/Contents/Versions/9.6/bin/pg_dump -Fd -j 4 -d geo -n census_2016_web -p 5432 -U postgres -f ~/tmp/census_2016_web

## OPTIONAL - copy files to AWS S3 and allow public read access (requires awscli installed)
#cd ${output_folder}
#
#for f in census_${census_year}_*.dmp;
#  do
#    aws --profile=default s3 cp --storage-class REDUCED_REDUNDANCY ./${f} s3://minus34.com/opendata/census-${census_year}/${f};
#    aws --profile=default s3api put-object-acl --acl public-read --bucket minus34.com --key opendata/census-${census_year}/${f}
#  done
