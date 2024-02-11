.. _intro:get_started:docker:
.. _intro:install:docker:

****************************
Run AiiDA via a Docker image
****************************

The AiiDA team maintains a `Docker <https://www.docker.com/>`__ image on `Docker Hub <https://hub.docker.com/r/aiidateam/aiida-core-with-services>`__.
This image contains a fully pre-configured AiiDA environment which makes it particularly useful for learning and testing purposes.

.. caution::

    All data stored in a container will persist only over the lifetime of that particular container (i.e., removing the container will also purge the data) unless you use volumes (see instructions below).

.. grid:: 1
   :gutter: 3

   .. grid-item-card:: Install Docker on your workstation or laptop

      To install Docker, please refer to the `official documentation <https://docs.docker.com/get-docker/>`__.

   .. grid-item-card:: Start container and use AiiDA interactively

      Start the container with (replace ``latest`` with the version you want to use, check the `Docker Hub <https://hub.docker.com/r/aiidateam/aiida-core-with-services/tags>`__ for available tags/versions):

      .. parsed-literal::

         $ docker run -it aiidateam/aiida-core-with-services:latest bash

      You can specify a name for the container with the ``--name`` option for easier reference later on:

      .. parsed-literal::

         $ docker run -it --name aiida-container aiidateam/aiida-core-with-services:latest bash

      By default, an AiiDA profile is automatically set up inside the container.
      To disable this default profile being created, set the ``SETUP_DEFAULT_AIIDA_PROFILE`` environment variable to ``false``.

      The following environment variables can be set to configure the default AiiDA profile:

      * ``AIIDA_PROFILE_NAME``: the name of the profile to be created (default: ``default``)
      * ``AIIDA_USER_EMAIL``: the email of the default user to be created (default: ``aiida@localhost``)
      * ``AIIDA_USER_FIRST_NAME``: the first name of the default user to be created (default: ``Giuseppe``)
      * ``AIIDA_USER_LAST_NAME``: the last name of the default user to be created (default: ``Verdi``)
      * ``AIIDA_USER_INSTITUTION``: the institution of the default user to be created (default: ``Khedivial``)
      * ``AIIDA_CONFIG_FILE``: the path to the AiiDA configuration file used for other profile configuration parameters (default: ``/aiida/assets/config-quick-setup.yaml``).

      These environment variables can be set when starting the container with the ``-e`` option.

      Please note that the ``AIIDA_CONFIG_FILE`` variable points to a path inside the container.
      Therefore, if you want to use a custom configuration file, it needs to be mounted from the host path to the container path.

   .. grid-item-card:: Check setup

      The profile named ``default`` is created under the ``aiida`` user.

      For example, to check the verdi status, execute the following command inside the container:

      .. code-block:: console

         $ verdi status
         ✓ config dir:  /home/aiida/.aiida
         ✓ profile:     On profile default
         ✓ repository:  /home/aiida/.aiida/repository/default
         ✓ postgres:    Connected as aiida_qs_aiida_477d3dfc78a2042156110cb00ae3618f@localhost:5432
         ✓ rabbitmq:    Connected as amqp://127.0.0.1?heartbeat=600
         ✓ daemon:      Daemon is running as PID 1795 since 2020-05-20 02:54:00

   .. grid-item-card:: Copy files from your computer to the container

      To copy files from your computer to the container, use the ``docker cp`` command.

      For example, to copy a file named ``test.txt`` from your current working directory to the ``/home/aiida`` path in the container, run:

      .. code-block:: console

         $ docker cp test.txt aiida-container:/home/aiida

   .. grid-item-card:: Persist data across different containers

      If you stop the container (`docker stop` or simply `Ctrl+D` from the container) and start it again, any data you created will persist.

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

      To persistently store the Python packages installed in the container, use `--user` flag when installing packages with pip, the packages will be installed in the ``/home/aiida/.local`` path which is mounted to the ``container-home-data`` volume.

      You can also mount a local directory instead of a volume and to other container paths, please refer to the `Docker documentation <https://docs.docker.com/storage/bind-mounts/>`__ for more information.

      .. button-ref:: intro:get_started:next
         :ref-type: ref
         :expand:
         :color: primary
         :outline:
         :class: sd-font-weight-bold

         What's next?
