#!/bin/bash -l
set -e
conda activate $ENV_PREFIX
#exec "$@"
thalassa serve --websocket-origin="*" --port 8000 /data
