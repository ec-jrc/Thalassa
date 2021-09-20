#FROM continuumio/miniconda3 as base
FROM jupyter/minimal-notebook as base

# Create a non-root user
ARG username=thalassa
ARG uid=1001
ARG gid=101
ENV USER $username
ENV UID $uid
ENV GID $gid
ENV HOME /home/$USER

USER root

# New user
RUN adduser --disabled-password --gecos "Non-root user" --uid $UID --home $HOME $USER


# Create a project directory inside user home
ENV PROJECT_DIR $HOME/app
RUN mkdir $PROJECT_DIR
RUN chown $UID:$GID $PROJECT_DIR
WORKDIR $PROJECT_DIR


# Build the conda environment
ENV ENV_PREFIX $HOME/conda_thalassa

COPY binder/environment.yml /tmp/
RUN chown $UID:$GID /tmp/environment.yml

RUN conda update --name base --channel defaults conda && \
    conda env create --prefix $ENV_PREFIX --file /tmp/environment.yml --force && \
        conda clean --all --yes

ENV CONDA_DIR /opt/conda

# build and install Thalassa
COPY ./ $PROJECT_DIR/Thalassa

# FIXME: In tree build fails! For now using dev install
RUN source $CONDA_DIR/etc/profile.d/conda.sh && \
    conda activate $ENV_PREFIX && \
    pip install -e Thalassa && \
    conda deactivate

# Set default entry
COPY docker/entrypoint.sh /usr/local/bin/
RUN chown $UID:$GID /usr/local/bin/entrypoint.sh && \
    chmod u+x /usr/local/bin/entrypoint.sh

RUN chmod u+w $HOME/.conda/

USER $USER

RUN echo "source $CONDA_DIR/etc/profile.d/conda.sh" >> ~/.profile

ENTRYPOINT [ "/usr/local/bin/entrypoint.sh" ]
