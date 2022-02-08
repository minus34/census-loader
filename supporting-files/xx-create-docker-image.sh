#!/usr/bin/env bash

# get the directory this script is running from
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

echo "---------------------------------------------------------------------------------------------------------------------"
echo "build census-loader docker image"
echo "---------------------------------------------------------------------------------------------------------------------"

cd ${SCRIPT_DIR}/../docker
docker build --squash --tag minus34/censusloader:2016 --no-cache  --no-cache --build-arg CENSUS_YEAR="2016" --build-arg BASE_URL="https://minus34.com/opendata/census-2016" .
docker build --squash --tag minus34/censusloader:2011 --no-cache  --no-cache --build-arg CENSUS_YEAR="2011" --build-arg BASE_URL="https://minus34.com/opendata/census-2011" .


#echo "---------------------------------------------------------------------------------------------------------------------"
#echo "build census-loader GDA2020 docker image"
#echo "---------------------------------------------------------------------------------------------------------------------"
#
#docker build --squash --tag minus34/censusloader:latest-gda2020 --tag minus34/censusloader:2016-gda2020 --no-cache --build-arg CENSUS_YEAR="2016" --build-arg BASE_URL="https://minus34.com/opendata/census-2016-gda2020" .

echo "---------------------------------------------------------------------------------------------------------------------"
echo "push images to Docker Hub"
echo "---------------------------------------------------------------------------------------------------------------------"

docker push minus34/censusloader:2016
docker push minus34/censusloader:2011

echo "---------------------------------------------------------------------------------------------------------------------"
echo "clean up Docker locally - warning: this could accidentally destroy other Docker images"
echo "---------------------------------------------------------------------------------------------------------------------"

echo 'y' | docker system prune
