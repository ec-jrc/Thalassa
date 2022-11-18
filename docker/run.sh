#!/usr/bin/env bash
#

set -xeuo pipefail

port="${1:-7777}"

docker container run \
  --rm \
  --interactive \
  --tty \
  --env NUMBA_CACHE_DIR=/tmp \
  --mount type=bind,source=$(pwd)/data,target=/data \
  --mount type=bind,source=$(pwd)/log_config.yml,target=/log_config.yml \
  --mount type=bind,source=$(pwd)/run.py,target=/run.py \
  --mount type=bind,source=$(pwd)/thalassa,target=/thalassa \
  --publish "${port}":"${port}" \
  pmav99/thalassa \
  python -mpanel serve /run.py --allow-websocket-origin "*" --port "${port}" --log-level trace
