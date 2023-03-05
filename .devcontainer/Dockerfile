FROM aiidateam/aiida-core:main

# Add test dependencies (not installed in image)
RUN pip install .[tests,pre-commit]

# add aiida user
RUN /etc/my_init.d/10_create-system-user.sh