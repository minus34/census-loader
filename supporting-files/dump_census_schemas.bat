
"C:\Program Files\PostgreSQL\9.6\bin\pg_dump" -Fc -d geo -n census_2016_data -p 5432 -U postgres > "C:\git\minus34\census_2016_data.dmp"
"C:\Program Files\PostgreSQL\9.6\bin\pg_dump" -Fc -d geo -n census_2016_bdys -p 5432 -U postgres > "C:\git\minus34\census_2016_bdys.dmp"
"C:\Program Files\PostgreSQL\9.6\bin\pg_dump" -Fc -d geo -n census_2016_web -p 5432 -U postgres > "C:\git\minus34\census_2016_web.dmp"

REM  OPTIONAL - copy files to AWS S3 and allow public read access (requires awscli installed)
REM aws --profile=default s3 cp "C:\git\minus34\census_2016_data.dmp" s3://minus34.com/opendata/census-2016/census_2016_data.dmp
REM aws --profile=default s3api put-object-acl --acl public-read --bucket minus34.com --key opendata/census-2016/census_2016_data.dmp

REM aws --profile=default s3 cp "C:\git\minus34\census_2016_bdys.dmp" s3://minus34.com/opendata/census-2016/census_2016_bdys.dmp
REM aws --profile=default s3api put-object-acl --acl public-read --bucket minus34.com --key opendata/census-2016/census_2016_bdys.dmp

REM aws --profile=default s3 cp "C:\git\minus34\census_2016_web.dmp" s3://minus34.com/opendata/census-2016/census_2016_web.dmp
REM aws --profile=default s3api put-object-acl --acl public-read --bucket minus34.com --key opendata/census-2016/census_2016_web.dmp

pause