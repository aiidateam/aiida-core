# Additions for dev container
FROM aiidateam/aiida-core:main

# Add test dependencies (not installed in image)
RUN pip install ./aiida-core[tests,rest,docs,pre-commit]

# add aiida user
RUN /etc/my_init.d/10_create-system-user.sh