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

   .. grid-item-card:: Install Docker on your warkstation or laptop

      To install Docker, please refer to the `official documentation <https://docs.docker.com/get-docker/>`__.

      .. note::

         If you are using Linux, you need to have root privileges to do `post-installation steps for the Docker Engine <https://docs.docker.com/engine/install/linux-postinstall/>`__.

   .. grid-item-card:: Start container and use AiiDA interactively

      First, pull the image:

      .. parsed-literal::

         $ docker pull aiidateam/aiida-core:latest

      Then start the container with:

      .. parsed-literal::

         $ docker run -it aiidateam/aiida-core:latest bash

      You can specify a name for the container with the ``--name`` option for easier reference later on:

      .. parsed-literal::

         $ docker run -it --name aiida-container aiidateam/aiida-core:latest bash

   .. grid-item-card:: Check setup

      The prfile named ``default`` is created under the ``aiida`` user.

      For example, to check the verdi status, execute the following command inside the container:

      .. code-block:: console

         $ verdi status
         ✓ config dir:  /home/aiida/.aiida
         ✓ profile:     On profile default
         ✓ repository:  /home/aiida/.aiida/repository/default
         ✓ postgres:    Connected as aiida_qs_aiida_477d3dfc78a2042156110cb00ae3618f@localhost:5432
         ✓ rabbitmq:    Connected as amqp://127.0.0.1?heartbeat=600
         ✓ daemon:      Daemon is running as PID 1795 since 2020-05-20 02:54:00

   .. grid-item-card:: Persist data across different containers

      If you stop the container (`docker stop` or simply `Ctrl+D` from container) and start it again, any data you created will persist.

      .. code-block:: console

         $ docker start -i aiida-container

      However, if you remove the container, **all data will be removed as well**.

      .. code-block:: console

         $ docker stop aiida-container
         $ docker rm aiida-container

      The preferred way to persistently store data is to `create a volume <https://docs.docker.com/storage/volumes/>`__.

      To create a simple volume, run:

      .. code-block:: console

         $ docker volume create container-home-data

      Then make sure to mount that volume when running the aiida container:

      .. parsed-literal::

         $ docker run -it --name aiida-container -v container-home-data:/home/aiida aiidateam/aiida-core:latest

      Starting the container with the above command, ensures that any data stored in the ``/home/aiida`` path within the container is stored in the ``conatiner-home-data`` volume and therefore persists even if the container is removed.

      To persistently store the python packages installed in the container, use `--user` flag when installing packages with pip, the packages will be installed in the ``/home/aiida/.local`` path which is mounted to the ``container-home-data`` volume.

      You can also mount a local directory instead of a volume and to other container path, please refer to the `Docker documentation <https://docs.docker.com/storage/bind-mounts/>`__ for more information.

      .. button-ref:: intro:get_started:next
         :ref-type: ref
         :expand:
         :color: primary
         :outline:
         :class: sd-font-weight-bold

         What's next?
