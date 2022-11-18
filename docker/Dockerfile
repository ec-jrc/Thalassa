# syntax = docker/dockerfile:1.4
# vim:foldmethod=marker:foldlevel=1:filetype=dockerfile
#
# https://jtreminio.com/blog/running-docker-containers-as-current-host-user/#ok-so-what-actually-works
# https://pythonspeed.com/articles/activate-virtualenv-dockerfile/
#
#-----------------------------------------------------------------------------------------

# {{{ base
FROM python:3.10.8-slim-bullseye@sha256:ac482ce5c90d9cbb5afd90d801f66a56d7d92c5f761b7e025fd0d7a702c1368e AS BASE

ARG created
ARG base_image
ARG base_digest
ARG git_commit
ARG version
ARG dockerfile_contents

# https://github.com/opencontainers/image-spec/blob/main/annotations.md
LABEL \
    org.opencontainers.image.created="${created}" \
    org.opencontainers.image.authors="Panagiotis Mavrogiorgos" \
    org.opencontainers.image.url="https://github.com/ec-jrc/thalassa" \
    org.opencontainers.image.documentation="https://github.com/ec-jrc/thalassa" \
    org.opencontainers.image.source="https://github.com/ec-jrc/thalassa" \
    org.opencontainers.image.version="${version}" \
    org.opencontainers.image.revision="${git_commit}" \
    org.opencontainers.image.vendor="JRC" \
    org.opencontainers.image.licenses="EUPL v1.2" \
    org.opencontainers.image.description="A docker image for running thalassa" \
    org.opencontainers.image.contents="${dockerfile_contents}" \
    org.opencontainers.image.base.digest="${base_digest}" \
    org.opencontainers.image.base.name="${base_image}"

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# redsymbol.net/articles/unofficial-bash-strict-mode/
SHELL ["/bin/bash", "-xeuo", "pipefail", "-c"]

# Configure apt
RUN echo 'APT::Install-Recommends "false";' | tee -a /etc/apt/apt.conf.d/99-install-suggests-recommends; \
    echo 'APT::Install-Suggests "false";' | tee -a /etc/apt/apt.conf.d/99-install-suggests-recommends; \
    echo 'Binary::apt::APT::Keep-Downloaded-Packages "true";' > /etc/apt/apt.conf.d/keep-cache; \
    rm -f /etc/apt/apt.conf.d/docker-clean; \
    echo 'Configuring apt: OK';

# Pre-populate the apt cache
RUN --mount=type=cache,target=/var/cache/apt,id=var_cache_apt --mount=type=cache,target=/var/lib/apt,id=var_lib_apt \
    apt update; \
    echo 'Pre-populating apt database: OK';

# Setup the locales
ENV LANG=en_US.UTF-8 \
    LC_ALL=en_US.UTF-8 \
    LANGUAGE=en_US:en
RUN --mount=type=cache,target=/var/cache/apt,id=var_cache_apt --mount=type=cache,target=/var/lib/apt,id=var_lib_apt \
    apt update; \
    apt install -yq locales; \
    sed -i -e "s/# ${LANG} UTF-8/${LANG} UTF-8/" /etc/locale.gen; \
    dpkg-reconfigure --frontend=${DEBIAN_FRONTEND} locales; \
    update-locale LANG=${LANG}; \
    apt autoremove -y; \
    echo 'Setting locales: OK';

# Setup the timezone
# ENV TZ=Etc/UTC
# ENV TZ=Europe/Rome
# RUN --mount=type=cache,target=/var/cache/apt,id=var_cache_apt --mount=type=cache,target=/var/lib/apt,id=var_lib_apt \
#     apt update; \
#     apt install -yq tzdata; \
#     ln -snf /usr/share/zoneinfo/"${TZ}" /etc/localtime; \
#     echo "${TZ}" | tee /etc/timezone; \
#     dpkg-reconfigure tzdata; \
#     apt autoremove -y; \
#     echo 'Setting timezone: OK';

# Install binary dependencies
RUN --mount=type=cache,target=/var/cache/apt,id=var_cache_apt --mount=type=cache,target=/var/lib/apt,id=var_lib_apt \
    apt update; \
    apt install -yq \
        # required by cartopy
        libgeos-dev \  
      ; \
    apt autoremove -y; \
    echo 'Installation of basic packages: OK';

# Create virtualenv
ENV VIRTUAL_ENV=/venv
ENV PATH="${VIRTUAL_ENV}/bin:$PATH"
RUN --mount=type=cache,target=/root/.cache/pip,uid=0,gid=0,id=pip_cache \
    python3 -m venv ${VIRTUAL_ENV}; \
    pip install -U pip wheel; \
    find ${VIRTUAL_ENV} -name *.pyc -delete; \
    echo 'Create virtualenv: OK';

# Install python dependencies
# We also install build-essential in order to be  able to build wheels for cartopy
# We remove it in the end to keep the image size small.
COPY requirements/requirements.txt /tmp/requirements.txt
RUN --mount=type=cache,target=/var/cache/apt,id=var_cache_apt --mount=type=cache,target=/var/lib/apt,id=var_lib_apt \
    --mount=type=cache,target=/root/.cache/pip,uid=0,gid=0,id=pip_cache \
    apt update; \
    apt install -yq \
        build-essential \
    ; \
    pip install --no-binary pygeos --no-binary shapely -r /tmp/requirements.txt; \
    apt remove -yq --purge build-essential; \
    apt autoremove -y; \
    echo 'Pip installation OK'

COPY run.py /run.py
COPY ./thalassa /thalassa
COPY config.yml /config.yml
