
echo 'y' | podman system prune --all
podman machine stop
echo 'y' | podman machine rm
podman machine init --cpus 10 --memory 16384 --disk-size=256  # memory in Mb, disk size in Gb
podman machine start

# run census loader container
podman run --name=censusloader --publish=5433:5432 minus34/censusloader:latest


## get census loader image pull count
#curl -s https://hub.docker.com/v2/repositories/minus34/censusloader/ | jq -r ".pull_count"
