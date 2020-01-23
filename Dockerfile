FROM aiidateam/aiida-prerequisites:latest

USER root

ENV SETUP_DEFAULT_PROFILE true

ENV PROFILE_NAME default
ENV USER_EMAIL some.body@xyz.com
ENV USER_FIRST_NAME Some
ENV USER_LAST_NAME Body
ENV USER_INSTITUTION XYZ
ENV AIIDADB_BACKEND django

# Copy and install AiiDA
COPY . aiida-core
RUN pip install ./aiida-core

# Configure aiida for the user
COPY .docker/opt/configure-aiida.sh /opt/configure-aiida.sh
COPY .docker/my_init.d/configure-aiida.sh /etc/my_init.d/40_configure-aiida.sh

# Use phusion baseimage docker init system.
CMD ["/sbin/my_init"]

#EOF
