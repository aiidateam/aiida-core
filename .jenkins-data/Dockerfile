FROM ubuntu:16.04
MAINTAINER AiiDA Team <info@aiida.net>

ARG uid=1000
ARG gid=1000

## Set correct locale
## For something more complex, as reported by https://hub.docker.com/_/ubuntu/
## and taken from postgres:
# make the "en_US.UTF-8" locale so postgres will be utf-8 enabled by default
RUN apt-get update && apt-get install -y locales && rm -rf /var/lib/apt/lists/* \
    && localedef -i en_US -c -f UTF-8 -A /usr/share/locale/locale.alias en_US.UTF-8
ENV LANG en_US.utf8

# Putting the LANG also in the root .bashrc, so that the DB is later
# Created with the UTF8 locale
RUN sed -i '/interactively/iexport LANG=en_US.utf8' /root/.bashrc
# This is probably the right command to issue to make sure all users see it as the default locale
RUN update-locale LANG=en_US.utf8

# I don't define it for now (should use the one of ubuntu by default, anyway
# jenkins will replace it with 'cat')
#CMD ["/bin/true"]

# install required software
RUN apt-get update \
    && apt-get -y install \
    git \
    openssh-client \
    postgresql-client-9.5 \
    postgresql-9.5 \
    postgresql-server-dev-9.5 \
    python2.7 \
    && apt-get -y install \
    python-pip \
    ipython \
    python2.7-dev \
    && apt-get -y install \
    texlive-base \
    texlive-generic-recommended \
    texlive-fonts-recommended \
    texlive-latex-base \
    texlive-latex-recommended \
    texlive-latex-extra \
    dvipng \
    dvidvi \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean all

# Disable password requests for requests coming from localhost
# Of course insecure, but ok for testing
RUN cp /etc/postgresql/9.5/main/pg_hba.conf /etc/postgresql/9.5/main/pg_hba.conf~ && \
    perl -npe 's/^([^#]*)md5$/$1trust/' /etc/postgresql/9.5/main/pg_hba.conf~ > /etc/postgresql/9.5/main/pg_hba.conf

# install sudo otherwise tests for quicksetup fail,
# see #1382. I think this part should be removed in the
# future and AiiDA should work also without sudo.
## Also install openssh-server needed for AiiDA tests,
## and openmpi-bin to have 'mpirun',
## and rabbitmq-server needed by AiiDA as the event queue
## and libkrb5-dev for gssapi.h
RUN apt-get update \
    && apt-get -y install \
    sudo \
    locate \
    openssh-server \
    openmpi-bin \
    rabbitmq-server \
    libkrb5-dev \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean all

# locate will not find anything if the DB is not updated.
# Should take ~3-4 secs, so ok
RUN updatedb

# update pip and setuptools to get a relatively-recent version
# This can be updated in the future
RUN pip install pip==10.0.1 setuptools==39.0.1

# Put the doubler script
COPY doubler.sh /usr/local/bin/

# add USER (no password); 1000 is the uid of the user in the jenkins docker
RUN groupadd -g ${gid} jenkins && useradd -m -s /bin/bash -u ${uid} -g ${gid} jenkins

# add to sudoers and don't ask password
RUN adduser jenkins sudo && adduser jenkins adm
RUN echo "%sudo   ALL=(ALL:ALL) NOPASSWD:ALL" > /etc/sudoers.d/nopwd
RUN mkdir -p /scratch/jenkins/ && chown jenkins /scratch/jenkins/ && chmod o+rX /scratch/

##########################################
############ Installation Setup ##########
##########################################

# install rest of the packages as normal user
USER jenkins

# set $HOME, create git directory
ENV HOME /home/jenkins
