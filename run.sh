#!/usr/bin/env bash
#

set -xeuo pipefail

## Resource Constraints
# - Memory: We should keep at least 10G for the host
# - CPU: Setting the cpu_share with a value lower than 1024 equals to increasing
#   the niceness of the containers' processes (i.e. less priority)
memory='240g'
cpu_shares=512

port=59823
container_name=panos_poseidon_test

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
  --mount type=bind,source="$(pwd)"/data,target=/data,readonly \
  --name "${container_name}" \
  --publish "${port}":8000 \
  docker.io/library/poseidon-panel:base \
  pv serve --websocket-origin localhost:59823 --port 8000 --no-show

