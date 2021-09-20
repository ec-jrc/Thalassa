set -xeuo pipefail

registry_url='docker.io'
registry_namespace='smnoaa'
image_name='thalassa'
image_fqdn="${registry_url}"/"${registry_namespace}"/"${image_name}"

# Control docker build
progress_mode="${DOCKER_BUILD_PROGRESS_MODE:-auto}"
create_date_tags="${DOCKER_BUILD_CREATE_DATE_TAGS:-1}"

# runtime labels
creation_date=$(date -u +"%Y-%m-%dT%H:%M:%S%Z")
revision_hash=$(git rev-parse HEAD)

# Create wheel file and export requirements.txt

# Build docker image
sudo docker build \
  --label org.opencontainers.image.created="${creation_date}" \
  --label org.opencontainers.image.revision="${revision_hash}" \
  -t "${image_name}":runtime \
  -f ./docker/Dockerfile \
  .

# Create date tags
if [ "${create_date_tags}" -eq 1 ]; then
  creation_date_tag=$(date -u +"%Y%m%d")
  sudo docker tag "${image_name}":runtime "${image_fqdn}":runtime-"${creation_date_tag}"
fi
