.. _intro:get_started:docker:
.. _intro:install:docker:

****************************
Run AiiDA via a Docker image
****************************

AiiDA can deployed and run by using `Docker <https://www.docker.com/>`__.
The AiiDA team maintains a `Docker image <https://hub.docker.com/r/aiidalab/base-with-services>`__ on `Docker Hub <https://hub.docker.com/r/aiidalab>`__.
This image contains a fully pre-configured AiiDA environment which makes it particularly useful for developing, learning and testing purposes.

.. caution::

    All data stored in a container will persist only over the lifetime of that particular container unless you use volumes (see instructions below).

.. grid:: 1
   :gutter: 3

   .. grid-item-card:: Start container

      First, pull the image:

      .. parsed-literal::

         $ docker pull aiidalab/base-with-services:latest

      Then start the container with:

      .. parsed-literal::

         $ docker run -d --name aiida-container aiidalab/base-with-services:latest

   .. grid-item-card:: Check setup

      To check the verdi status, execute:

      .. code-block:: console

         $ docker exec -t aiida-container /bin/bash -l -c 'verdi status'
         ✔ version:     AiiDA v2.0.3
         ✔ config:      /home/jovyan/.aiida
         ✔ profile:     default
         ✔ storage:     Storage for 'default' [open] @ postgresql://aiida:***@localhost:5432/aiida_db / file:///home/jovyan/.aiida/repository/default
         ✔ rabbitmq:    Connected to RabbitMQ v3.8.14 as amqp://guest:guest@127.0.0.1:5672?heartbeat=600
         ✔ daemon:      Daemon is running as PID 372 since 2022-10-12 19:58:32

   .. grid-item-card:: Use container interactively

      To "enter" the container and run commands directly in the shell, use:

      .. code-block:: console

         $ docker exec -it aiida-container /bin/bash

      This will drop you into the shell within the container as the user "jovyan".

   .. grid-item-card:: Persist data across different containers

      If you stop the container and start it again, any data you created will persist.

      .. code-block:: console

         $ docker stop aiida-container
         $ docker start aiida-container

      However, if you remove the container, **all data will be removed as well**.

      .. code-block:: console

         $ docker stop aiida-container
         $ docker rm aiida-container

      The preferred way to persistently store data is to `create a volume <https://docs.docker.com/storage/volumes/>`__.
      To create a simple volume, run:

      .. code-block:: console

         $ docker volume create my-data

      Then make sure to mount that volume when running the aiida container:

      .. parsed-literal::

         $ docker run -d --name aiida-container --mount source=my-data,target=/tmp/my_data aiidateam/aiida-core:latest

      Starting the container with the above command, ensures that any data stored in the ``/tmp/my_data`` path within the container is stored in the ``my-data`` volume and therefore persists even if the container is removed.

.. note::

   Besides using docker command to start container, we provide `AiiDAlab launch <https://github.com/aiidalab/aiidalab-launch>`__ to launch an AiiDA(lab) container with all services on a local workstation.
   AiiDAlab launch also manage to create a docker volume to store data permanently.

      .. button-ref:: intro:get_started:next
         :ref-type: ref
         :expand:
         :color: primary
         :outline:
         :class: sd-font-weight-bold

         What's next?
