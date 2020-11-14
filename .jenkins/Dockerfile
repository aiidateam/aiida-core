FROM quay.io/ansible/toolset:0.2

# install sudo and docker
RUN apt-get update && \
    apt-get install -y curl gnupg-agent sudo software-properties-common && \
    curl -fsSL https://download.docker.com/linux/debian/gpg | apt-key add - && \
    add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/debian stretch stable" && \
    apt-get update && \
    apt-get install -y docker-ce docker-ce-cli containerd.io && \
    apt-get autoclean

ARG uid=1000
ARG gid=1000

# add USER (no password); 1000 is the uid of the user in the jenkins docker
RUN groupadd -g ${gid} jenkins && useradd -m -s /bin/bash -u ${uid} -g ${gid} jenkins

# add to sudoers and don't ask password
RUN adduser jenkins sudo && adduser jenkins adm
RUN echo "%sudo   ALL=(ALL:ALL) NOPASSWD:ALL" > /etc/sudoers.d/nopwd
RUN mkdir -p /scratch/jenkins/ && chown jenkins /scratch/jenkins/ && chmod o+rX /scratch/

# install rest of the packages as normal user
USER jenkins

# set $HOME, create git directory
ENV HOME /home/jenkins
