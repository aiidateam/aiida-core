FROM aiidateam/aiida-prerequisites:0.6.0

USER root

ENV SETUP_DEFAULT_PROFILE true

ENV PROFILE_NAME default
ENV USER_EMAIL aiida@localhost
ENV USER_FIRST_NAME Giuseppe
ENV USER_LAST_NAME Verdi
ENV USER_INSTITUTION Khedivial
ENV AIIDADB_BACKEND core.psql_dos

# Copy and install AiiDA
COPY . aiida-core
RUN pip install ./aiida-core[atomic_tools]

# Configure aiida for the user
COPY .docker/opt/configure-aiida.sh /opt/configure-aiida.sh
COPY .docker/my_init.d/configure-aiida.sh /etc/my_init.d/40_configure-aiida.sh

# Use phusion baseimage docker init system.
CMD ["/sbin/my_init"]
