#!/usr/bin/env bash

# get the directory this script is running from
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

CENSUS_YEAR="2021"
BASE_URL="https://minus34.com/opendata/census-${CENSUS_YEAR}"
OUTPUT_FOLDER="/Users/$(whoami)/tmp/census-${CENSUS_YEAR}"

mkdir -p ${OUTPUT_FOLDER}

cd ${OUTPUT_FOLDER}


# required or Docker VM will run out of space
echo 'y' | docker builder prune --all
echo 'y' | docker system prune --all


echo "---------------------------------------------------------------------------------------------------------------------"
echo "build census-loader docker image"
echo "---------------------------------------------------------------------------------------------------------------------"

cd ${SCRIPT_DIR}/../docker
#docker build --tag minus34/censusloader:2016 --no-cache --build-arg CENSUS_YEAR="2016" --build-arg BASE_URL="https://minus34.com/opendata/census-2016" .
#docker build --tag minus34/censusloader:2011 --no-cache --build-arg CENSUS_YEAR="2011" --build-arg BASE_URL="https://minus34.com/opendata/census-2011" .

docker build --tag minus34/censusloader:2021 --no-cache --build-arg CENSUS_YEAR="2021" --build-arg BASE_URL="https://minus34.com/opendata/census-2021"  --build-arg DATUM="gda94" .
#docker build --tag minus34/censusloader:2021 --no-cache --build-arg CENSUS_YEAR="2021" --build-arg BASE_URL="https://minus34.com/opendata/census-2021"  --build-arg DATUM="gda2020" .









cd ${SCRIPT_DIR}/../../docker

echo "---------------------------------------------------------------------------------------------------------------------"
echo "start Docker desktop and wait 90 seconds for startup"
echo "---------------------------------------------------------------------------------------------------------------------"

open -a Docker
sleep 90

# required or Docker VM will run out of space
echo 'y' | docker builder prune --all
echo 'y' | docker system prune --all

echo "---------------------------------------------------------------------------------------------------------------------"
echo "build census-loader GDA94 docker image "
echo "---------------------------------------------------------------------------------------------------------------------"

# force platform to avoid Apple Silicon only images
cd ${OUTPUT_FOLDER}
docker build --platform linux/amd64 --no-cache --tag docker.io/minus34/censusloader:latest --tag docker.io/minus34/censusloader:2021 \
  -f /Users/$(whoami)/git/minus34/census-loader/docker/Dockerfile .

echo "---------------------------------------------------------------------------------------------------------------------"
echo "push image (with 2 tags) to Docker Hub"
echo "---------------------------------------------------------------------------------------------------------------------"

docker push minus34/censusloader --all-tags

echo "---------------------------------------------------------------------------------------------------------------------"
echo "clean up Docker locally - warning: this could accidentally destroy other Docker images"
echo "---------------------------------------------------------------------------------------------------------------------"

# required or Docker VM will run out of space
echo 'y' | docker builder prune --all
echo 'y' | docker system prune --all

echo "---------------------------------------------------------------------------------------------------------------------"
echo "build census-loader GDA2020 docker image"
echo "---------------------------------------------------------------------------------------------------------------------"

cd ${OUTPUT_FOLDER_2020}
docker build --platform linux/amd64 --no-cache --tag docker.io/minus34/censusloader:latest-gda2020 --tag docker.io/minus34/censusloader:2021-gda2020 \
  -f /Users/$(whoami)/git/minus34/census-loader/docker/Dockerfile .

echo "---------------------------------------------------------------------------------------------------------------------"
echo "push images (with 2 new tags) to Docker Hub"
echo "---------------------------------------------------------------------------------------------------------------------"

docker push minus34/censusloader --all-tags

echo "---------------------------------------------------------------------------------------------------------------------"
echo "clean up Docker locally - warning: this could accidentally destroy other Docker images"
echo "---------------------------------------------------------------------------------------------------------------------"

# required or Docker VM will run out of space
echo 'y' | docker builder prune --all
echo 'y' | docker system prune --all
