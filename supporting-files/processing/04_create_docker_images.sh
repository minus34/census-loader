#!/usr/bin/env bash

# get the directory this script is running from
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

CENSUS_YEAR="2021"
OUTPUT_FOLDER = "/Users/$(whoami)/tmp/census_${CENSUS_YEAR}"

cd ${OUTPUT_FOLDER}

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
docker build --platform linux/amd64 --no-cache --tag docker.io/minus34/censusloader:latest --tag docker.io/minus34/censusloader:${CENSUS_YEAR} \
  -f /Users/$(whoami)/git/minus34/census-loader/docker/Dockerfile --build-arg DATUM="gda94" .

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
docker build --platform linux/amd64 --no-cache --tag docker.io/minus34/censusloader:latest-gda2020 --tag docker.io/minus34/censusloader:${CENSUS_YEAR}-gda2020 \
  -f /Users/$(whoami)/git/minus34/census-loader/docker/Dockerfile  --build-arg DATUM="gda2020" .

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
