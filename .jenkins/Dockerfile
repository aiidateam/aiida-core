FROM aiidateam/aiida-prerequisites:0.2.1

# to run the tests
RUN pip install ansible~=2.10.0 molecule~=3.1.0

RUN apt-get update && \
    apt-get install -y sudo && \
    apt-get autoclean

ARG uid=1000
ARG gid=1000

# add USER (no password); 1000 is the uid of the user in the jenkins docker
RUN groupadd -g ${gid} jenkins && useradd -m -s /bin/bash -u ${uid} -g ${gid} jenkins

# add to sudoers and don't ask password
RUN adduser jenkins sudo && adduser jenkins adm && adduser jenkins root
RUN echo "%sudo   ALL=(ALL:ALL) NOPASSWD:ALL" > /etc/sudoers.d/nopwd
RUN mkdir -p /scratch/jenkins/ && chown jenkins /scratch/jenkins/ && chmod o+rX /scratch/

# set $HOME to the directory where the repository is mounted
ENV HOME /home/jenkins

# this is added since otherwise jenkins prints /etc/profile contents for all sh commands
RUN echo 'set +x' | cat - /etc/profile > temp && mv temp /etc/profile
