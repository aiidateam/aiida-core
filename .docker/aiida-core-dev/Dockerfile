# syntax=docker/dockerfile:1
FROM aiida-core-with-services

LABEL maintainer="AiiDA Team <developers@aiida.net>"

COPY aiida-clone-and-install.sh /etc/init/run-before-daemon-start/10-aiida-clone-and-install.sh

USER ${SYSTEM_UID}
WORKDIR "/home/${SYSTEM_USER}"
