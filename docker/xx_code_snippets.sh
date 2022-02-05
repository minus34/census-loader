
cd /Users/$(whoami)/git/minus34/census-loader/docker

# run census loader container
docker run --name=censusloader --publish=5433:5432 minus34/censusloader:latest


# get census loader image pull count
curl -s https://hub.docker.com/v2/repositories/minus34/censusloader/ | jq -r ".pull_count"
