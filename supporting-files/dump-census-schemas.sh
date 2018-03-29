#!/usr/bin/env bash

# dump schemas to backup files
/Applications/Postgres.app/Contents/Versions/9.6/bin/pg_dump -Fc -d geo -n census_2016_data -p 5432 -U postgres -f ~/tmp/census_2016_data.dmp
/Applications/Postgres.app/Contents/Versions/9.6/bin/pg_dump -Fc -d geo -n census_2016_bdys -p 5432 -U postgres -f ~/tmp/census_2016_bdys.dmp
/Applications/Postgres.app/Contents/Versions/9.6/bin/pg_dump -Fc -d geo -n census_2016_web -p 5432 -U postgres -f ~/tmp/census_2016_web.dmp

# dump using multiple workers (not tested - doesn't necessarily work)
#/Applications/Postgres.app/Contents/Versions/9.6/bin/pg_dump -Fd -j 4 -d geo -n census_2016_data -p 5432 -U postgres -f ~/tmp/census_2016_data
#/Applications/Postgres.app/Contents/Versions/9.6/bin/pg_dump -Fd -j 4 -d geo -n census_2016_bdys -p 5432 -U postgres -f ~/tmp/census_2016_bdys
#/Applications/Postgres.app/Contents/Versions/9.6/bin/pg_dump -Fd -j 4 -d geo -n census_2016_web -p 5432 -U postgres -f ~/tmp/census_2016_web

# OPTIONAL - copy files to AWS S3 and allow public read access (requires awscli installed)
aws --profile=default s3 cp ~/tmp/census_2016_data.dmp s3://minus34.com/opendata/census-2016/census_2016_data.dmp
aws --profile=default s3api put-object-acl --acl public-read --bucket minus34.com --key opendata/census-2016/census_2016_data.dmp

aws --profile=default s3 cp ~/tmp/census_2016_bdys.dmp s3://minus34.com/opendata/census-2016/census_2016_bdys.dmp
aws --profile=default s3api put-object-acl --acl public-read --bucket minus34.com --key opendata/census-2016/census_2016_bdys.dmp

aws --profile=default s3 cp ~/tmp/census_2016_web.dmp s3://minus34.com/opendata/census-2016/census_2016_web.dmp
aws --profile=default s3api put-object-acl --acl public-read --bucket minus34.com --key opendata/census-2016/census_2016_web.dmp
