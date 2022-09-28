.. _intro:get_started:docker:
.. _intro:install:docker:

****************************
Run AiiDA via a Docker image
****************************

The AiiDA team maintains a `Docker <https://www.docker.com/>`__ image on `Docker Hub <https://hub.docker.com/r/aiidateam/aiida-core>`__.
This image contains a fully pre-configured AiiDA environment which makes it particularly useful for learning and testing purposes.

.. caution::

    All data stored in a container will persist only over the lifetime of that particular container unless you use volumes (see instructions below).

.. grid:: 1
   :gutter: 3

   .. grid-item-card:: Start container

      First, pull the image:

      .. parsed-literal::

         $ docker pull aiidateam/aiida-core:latest

      Then start the container with:

      .. parsed-literal::

         $ docker run -d --name aiida-container aiidateam/aiida-core:latest

      You can use the following command to block until all services have started up:

      .. code-block:: console

         $ docker exec -t aiida-container wait-for-services

   .. grid-item-card:: Check setup

      The default profile is created under the ``aiida`` user, so to execute commands you must add the ``--user aiida`` option.

      For example, to check the verdi status, execute:

      .. code-block:: console

         $ docker exec -t --user aiida aiida-container /bin/bash -l -c 'verdi status'
         ✓ config dir:  /home/aiida/.aiida
         ✓ profile:     On profile default
         ✓ repository:  /home/aiida/.aiida/repository/default
         ✓ postgres:    Connected as aiida_qs_aiida_477d3dfc78a2042156110cb00ae3618f@localhost:5432
         ✓ rabbitmq:    Connected as amqp://127.0.0.1?heartbeat=600
         ✓ daemon:      Daemon is running as PID 1795 since 2020-05-20 02:54:00

   .. grid-item-card:: Use container interactively

      To "enter" the container and run commands directly in the shell, use:

      .. code-block:: console

         $ docker exec -it --user aiida aiida-container /bin/bash

      This will drop you into the shell within the container as the user "aiida".

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

      .. button-ref:: intro:get_started:next
         :ref-type: ref
         :expand:
         :color: primary
         :outline:
         :class: sd-font-weight-bold

         What's next?
