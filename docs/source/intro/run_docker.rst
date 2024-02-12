.. _intro:get_started:docker:
.. _intro:install:docker:

****************************
Run AiiDA via a Docker image
****************************

The AiiDA team maintains a `Docker <https://www.docker.com/>`__ image on `Docker Hub <https://hub.docker.com/r/aiidateam/aiida-core-with-services>`__.
This image contains a fully pre-configured AiiDA environment which makes it particularly useful for learning and developing purposes.

.. caution::

    All data stored in a container will persist only over the lifetime of that particular container (i.e., removing the container will also purge the data) unless you use volumes (see instructions below).

.. grid:: 1
   :gutter: 3

   .. grid-item-card:: Install Docker on your PC

      Docker is available for Windows, Mac and Linux and can be installed in different ways.

      .. tab-set::

         .. tab-item:: Colima on MacOS

            `Colima <https://github.com/abiosoft/colima>`_ is a new open-source project that makes it easy to run Docker on MacOS.
            It is a lightweight alternative to Docker Engine with a focus on simplicity and performance.

            If you need multiple Docker environments, Colima is the recommended way.
            With colima, you can have multiple Docker environments running at the same time, each with its own Docker daemon and resource allocation thus avoiding conflicts.

            To install the colima, on MacOS run:

            .. parsed-literal::

               $ brew install colima

            Or check Check `here <https://github.com/abiosoft/colima/blob/main/docs/INSTALL.md>`__ for other installation options.

            After installation, start the docker daemon by:

            .. parsed-literal::

               $ colima start

         .. tab-item:: Docker CE on Linux

            The bare minimum to run Docker on Linux is to install the `Docker Engine <https://docs.docker.com/engine/install/>`_.
            If you don't need a graphical user interface, this is the recommended way to install Docker.

            .. note::

               You will need `root` privileges to perform the `post-installation steps <https://docs.docker.com/engine/install/linux-postinstall/>`_.
               Otherwise, you will need to use `sudo` for every Docker command.



   .. grid-item-card:: Start/stop container and use AiiDA interactively

      Start the image with the `docker command line (docker CLI) <https://docs.docker.com/engine/reference/commandline/cli/>`_.

      The ``latest`` tag is the image with the most recent stable version of ``aiida-core`` installed in the container.
      You can replace the ``latest`` tag with the version you want to use, check the `Docker Hub <https://hub.docker.com/r/aiidateam/aiida-core-with-services/tags>`_ for available tags.

      .. tab-set::

         .. tab-item:: Docker CLI

            No matter how you installed Docker, you can always use the Docker CLI to run the image.

            .. parsed-literal::

               $ docker run -it aiidateam/aiida-core-with-services:latest bash

            The ``-it`` option is used to run the container in interactive mode and to allocate a pseudo-TTY.
            You will be dropped into a bash shell inside the container.

            You can specify a name for the container with the ``--name`` option for easier reference later on.
            For the quick test, you can also use the ``--rm`` option to remove the container when it exits.
            In the following examples, we will use the name ``aiida-container-demo`` for the container.


            To exit and stop the container, type ``exit`` or press ``Ctrl+D``, the container will be stopped.

            Please note ``run`` sub-command is used to create and start a container. 
            In order to start a container which is already created, you should use ``start``, by running:

            .. parsed-literal::

               $ docker start -i aiida-container-demo

            If you need another shell inside the container, run:

            .. parsed-literal::

               $ docker exec -it aiida-container-demo bash

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

      To check the status of AiiDA environment setup, execute the following command inside the container shell:

      .. code-block:: console

         $ verdi status
         ✓ config dir:  /home/aiida/.aiida
         ✓ profile:     On profile default
         ✓ repository:  /home/aiida/.aiida/repository/default
         ✓ postgres:    Connected as aiida_qs_aiida_477d3dfc78a2042156110cb00ae3618f@localhost:5432
         ✓ rabbitmq:    Connected as amqp://127.0.0.1?heartbeat=600
         ✓ daemon:      Daemon is running as PID 1795 since 2020-05-20 02:54:00


Advanced usage
==============

Congratulations! You have a working AiiDA environment, and can start using it.

If you use the Docker image for development or production, you will likely need additional settings such as clone the repository and install `aiida-core` in the editable mode to make it work as expected.
See `developement wiki <https://github.com/aiidateam/aiida-core/wiki/Development-environment>`_ for more detalis.

.. dropdown:: Copy files from your computer to the container

   .. tab-set::

      .. tab-item:: Docker CLI

         Use the ``docker cp`` command if you need to copy files from your computer to the container or vice versa.

         For example, to copy a file named ``test.txt`` from your current working directory to the ``/home/aiida`` path in the container, run:

         .. code-block:: console

            $ docker cp test.txt aiida-container-demo:/home/aiida


.. dropdown:: Persist data across different containers

   The lifetime of the data stored in a container is limited to the lifetime of that particular container.

   If you stop the container (`docker stop` or simply `Ctrl+D` from the container) and start it again, any data you created will persist.
   However, if you remove the container, **all data will be removed as well**.

   .. code-block:: console

      $ docker rm aiida-container-demo

   The preferred way to persistently store data is to `create a volume <https://docs.docker.com/storage/volumes/>`__.

   .. tab-set::

      .. tab-item:: Docker CLI

         To create a simple volume, run:

         .. code-block:: console

            $ docker volume create container-home-data

         In this case, one needs to specifically mount the volume very first time that the container is being created:

         .. parsed-literal::

            $ docker run -it --name aiida-container-demo -v container-home-data:/home/aiida aiidateam/aiida-core:latest bash

         Starting the container with the above command ensures that any data stored in the ``/home/aiida`` path within the container is stored in the ``conatiner-home-data`` volume and therefore persists even if the container is removed.

         When installing packages with pip, use the ``--user`` flag to store the Python packages installed in the mounted volume (if you mount the home specifically to a volume as mentioned above) permanently.
         The packages will be installed in the ``/home/aiida/.local`` directory, which is mounted on the ``container-home-data`` volume.

         You can mount a folder in container to a local directory, please refer to the `Docker documentation <https://docs.docker.com/storage/bind-mounts/>`__ for more information.

.. dropdown:: Backup the container

   To backup the data of AiiDA, you can still follow the instructions in the `Backup and restore <backup_and_restore>`__ section.
   However, Docker provides a convinient way to backup the container data by taking a snapshot of the entire container or the mounted volume(s).

   The following is adapted from the `Docker documentation <https://docs.docker.com/desktop/backup-and-restore/>`__.

   If you don't have a volume mounted to the container, you can backup the whole container by committing the container to an image:

   .. parsed-literal::

      $ docker container commit aiida-container-demo aiida-container-backup

   The above command will create a new image named ``aiida-container-backup`` containing all the data and modifications you made in the container.

   Then, you can export the container to a local tarball and store it permanently:

   .. parsed-literal::

      $ docker save -o aiida-container-backup.tar aiida-container-backup

   To restore the container, pull the image, or load from the tarball, run:

   .. parsed-literal::

      $ docker load -i aiida-container-backup.tar

   You'll find a container in the list and you can then start it with ``docker start``.

   If you used a `named volume <https://docs.docker.com/storage/volumes/#backup-a-containerhttps://docs.docker.com/storage/#more-details-about-mount-types>`__, you can backup the volume independently.

   .. tab-set::

      .. tab-item:: Docker CLI

         Please check `Backup, restore, or migrate data volumes <https://docs.docker.com/storage/volumes/#backup-restore-or-migrate-data-volumes>`__ for more information.

.. button-ref:: intro:get_started:next
   :ref-type: ref
   :expand:
   :color: primary
   :outline:
   :class: sd-font-weight-bold

   What's next?
