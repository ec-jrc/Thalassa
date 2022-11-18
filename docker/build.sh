#!/usr/bin/env bash
#

set -xeuo pipefail

export DOCKER_BUILDKIT=1

# REGISTRY_URL='registry.gitlab.com'
REGISTRY_URL='docker.io'
REGISTRY_NAMESPACE='pmav99'
IMAGE_NAME='thalassa'
REGISTRY_FQDN="${REGISTRY_URL}"/"${REGISTRY_NAMESPACE}"/"${IMAGE_NAME}"

echo "Building: ${REGISTRY_FQDN}"

created=$(date --utc --rfc-3339=seconds)
date_tag=$(date --utc +"%Y%m%d")
base_digest=sha256:"$(sha256sum docker/Dockerfile | cut -d ' ' -f 1)"
base_image='python:3.10.8-slim-bullseye@sha256:ac482ce5c90d9cbb5afd90d801f66a56d7d92c5f761b7e025fd0d7a702c1368e'
git_commit="$(git rev-parse HEAD)"
version="$(git tag)"
dockerfile_contents="$(cat ./docker/Dockerfile | base64)"

docker build \
  --pull \
  --build-arg created="${created}" \
  --build-arg base_digest="${base_digest}" \
  --build-arg base_image="${base_image}" \
  --build-arg git_commit="${git_commit}" \
  --build-arg version="${version}" \
  --build-arg dockerfile_contents="${dockerfile_contents}" \
  --tag "${REGISTRY_FQDN}":"${date_tag}" \
  --tag "${REGISTRY_FQDN}":"${git_commit}" \
  --tag "${REGISTRY_FQDN}":latest \
  --file docker/Dockerfile \
  ./
