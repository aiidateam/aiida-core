# Additions for dev container
FROM aiidateam/aiida-core:main

# Add test dependencies (not installed in image)
RUN pip install ./aiida-core[tests,rest,docs,pre-commit]
# the `locate` command is needed by many tests
RUN apt-get update \
    && apt-get install -y mlocate \
    && rm -rf /var/lib/apt/lists/*

# add aiida user
RUN /etc/my_init.d/10_create-system-user.sh

# copy updated aiida configuration script
# this line can be deleted after the new script has been merged
COPY configure-aiida.sh /opt/configure-aiida.sh
