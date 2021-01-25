#!/usr/bin/env bash
#

set -xeuo pipefail

## Resource Constraints
# - Memory: We should keep at least 10G for the host
# - CPU: Setting the cpu_share with a value lower than 1024 equals to increasing
#   the niceness of the containers' processes (i.e. less priority)
memory='240g'
cpu_shares=512

port=63999
image_fqdn='thalassa_panel:runtime'
container_name='thalassa_panel'

data_directory='/eos/jeodpp/data/projects/CRITECH/docker_mounts/thalassa_panel'
#data_directory="$(pwd)/data"

set +e
echo 'Removing container (if it exists):' "${container_name}"
docker rm -f "${container_name}"

echo 'check if port is available'
if (nc -z 127.0.0.1  "${port}"); then
  echo "Port is not available ${port}"
  exit 1
fi
set -e

docker run \
  -d \
  --restart=unless-stopped \
  --ulimit core=0 \
  --memory "${memory}" \
  --cpu-shares "${cpu_shares}" \
  --mount type=bind,source="${data_directory}",target=/data,readonly \
  --name "${container_name}" \
  --publish "${port}":8000 \
  "${image_fqdn}" \
  pv serve --websocket-origin 0.0.0.0:"${port}" --port 8000 --no-show
