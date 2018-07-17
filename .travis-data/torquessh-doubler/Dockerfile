FROM aiidateam/torquessh_base:1.0
MAINTAINER AiiDA Team <info@aiida.net>

# Use baseimage-docker's init system.
CMD ["/sbin/my_init"]

COPY doubler.sh /usr/local/bin/

# Use messed-up filename to test quoting robustness
RUN mv /usr/local/bin/doubler.sh /usr/local/bin/d\"o\'ub\ ler.sh
