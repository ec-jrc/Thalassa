# syntax=docker/dockerfile:1.1.7-experimental@sha256:8c69d118cfcd040a222bea7f7d57c6156faa938cb61b47657cd65343babc3664
# vim:foldmethod=marker:foldlevel=0:
#
###------------------------------------------------------------------------------------###

# base {

FROM ubuntu:bionic-20200921@sha256:45c6f8f1b2fe15adaa72305616d69a6cd641169bc8b16886756919e7c01fa48b AS base

# redsymbol.net/articles/unofficial-bash-strict-mode/
SHELL ["/bin/bash", "-xeuo", "pipefail", "-c"]

# Configure apt
ENV DEBIAN_FRONTEND=noninteractive
RUN echo 'APT::Install-Recommends "false";' | tee -a /etc/apt/apt.conf.d/docker-install-suggests-recommends; \
    echo 'APT::Install-Suggests "false";' | tee -a /etc/apt/apt.conf.d/docker-install-suggests-recommends; \
    echo 'Configuring apt: OK';

# Setup the locales
ENV LANG=en_US.UTF-8 \
    LC_ALL=en_US.UTF-8 \
    LANGUAGE=en_US:en
RUN set -xeu; \
    apt update; \
    apt upgrade -yq; \
    apt install -yq locales; \
    sed -i -e "s/# ${LANG} UTF-8/${LANG} UTF-8/" /etc/locale.gen; \
    dpkg-reconfigure --frontend=noninteractive locales; \
    update-locale LANG="${LANG}"; \
    apt autoremove --purge -y; \
    find / -xdev -name *.pyc -delete; \
    rm -rf /var/lib/apt/lists/*; \
    echo 'Setting locales: OK';

# Create normal user
ENV USER_NAME=critechproc \
    GROUP_NAME=EC_JRC_P_CRITECH \
    USER_ID=35435 \
    GROUP_ID=50008
RUN groupadd --gid "${GROUP_ID}" "${GROUP_NAME}"; \
    useradd -u "${USER_ID}" -g "${GROUP_ID}" -m -s /bin/bash "${USER_NAME}"; \
    echo "user ${USER_NAME} creation: OK";

# Install tini
ENV TINI_VERSION v0.19.0
RUN apt update; \
    apt install -yq \
        ca-certificates \
        wget \
    ; \
    wget https://github.com/krallin/tini/releases/download/${TINI_VERSION}/tini -O /usr/bin/tini; \
    chmod +x /usr/bin/tini; \
    apt purge -yq wget; \
    apt autoremove --purge -yq; \
    find / -xdev -name *.pyc -delete; \
    rm -rf /var/lib/apt/lists/*; \
    echo 'tini installation: OK'

# Install ppas
RUN set -xeu; \
    apt update; \
    apt install -yq software-properties-common; \
    add-apt-repository -y ppa:ubuntugis/ppa; \
    add-apt-repository -y ppa:deadsnakes/ppa; \
    apt purge -yq software-properties-common; \
    apt autoremove -y; \
    find / -xdev -name *.pyc -delete; \
    rm -rf /var/lib/apt/lists/*; \
    echo 'ppa installation: OK'

# Install python
ENV PYTHON_VERSION=3.8
RUN apt update -yq; \
    apt install -yq \
        python3-dev \
        python3-pip \
        python3-venv \
        python"${PYTHON_VERSION}" \
        python"${PYTHON_VERSION}"-dev \
        python"${PYTHON_VERSION}"-venv \
    ; \
    cd /usr/bin; \
    ln -sf idle3 idle; \
    ln -sf pip3 pip; \
    ln -sf pydoc3 pydoc; \
    ln -sf python3.8 python; \
    ln -sf python3-config python-config; \
    apt autoremove -y --purge; \
    find / -xdev -name *.pyc -delete; \
    rm -rf /var/lib/apt/lists/*; \
    echo 'Python installation: OK'

# Install dependencies
RUN apt update -yq; \
    apt install -yq \
        gosu \
        #libgdal-dev \
        libgeos-dev \
        libproj-dev \
        proj-bin \
        #libshp-dev \
        gcc \
        g++ \
    ; \
    apt autoremove -y; \
    find / -xdev -name *.pyc -delete; \
    rm -rf /var/lib/apt/lists/*; \
    echo 'Installing requirements: OK';

# Install python packages
COPY requirements.txt /tmp/
RUN python3.8 -mpip install -U --no-cache-dir --no-compile pip setuptools; \
    # cartopy requires that numpy is already installed installed...
    python3.8 -mpip install --no-cache-dir --no-compile numpy; \
    python3.8 -mpip install --no-cache-dir --no-compile -r /tmp/requirements.txt; \
    find / -xdev -name *.pyc -delete; \
    echo 'Requirements installation: OK'

COPY dist/poseidon_viz-0.1.0-py3-none-any.whl  /tmp/
RUN python3.8 -mpip install -U --no-cache-dir --no-compile /tmp/poseidon_viz-0.1.0-py3-none-any.whl; \
    find / -xdev -name *.pyc -delete; \
    echo 'Poseidon-viz installation: OK'

USER "${USER_NAME}"

COPY docker-entrypoint.sh /usr/local/bin/entrypoint.sh
ENTRYPOINT ["/usr/bin/tini", "--", "/usr/local/bin/entrypoint.sh"]


#ENV SCRIPTS_DIR=/home/"${USER_NAME}"/scripts/
#COPY --chown="${USER_NAME}":"${GROUP_NAME}" med.py "${SCRIPTS_DIR}"

#WORKDIR "${SCRIPTS_DIR}"
#CMD ["/usr/local/bin/panel", "serve", "--log-level", "trace", "--num-procs", "4", "--show", "--allow-websocket-origin", "193.37.152.219:59823", "--port", "8000", "med.py"]
#CMD ["/usr/local/bin/panel", "serve", "--log-level", "debug", "--num-procs", "4", "--show", "--allow-websocket-origin", "0.0.0.0:59823", "--port", "8000", "med.py"]

# base }
