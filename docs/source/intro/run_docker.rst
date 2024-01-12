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

         .. tab-item:: Docker Desktop

            Docker Desktop is available for Windows and Mac and includes everything you need to run Docker on your computer.
            It is a virtual machine + Graphical user interface with some extra features like the new extensions.

            `Docker Desktop <https://www.docker.com/products/docker-desktop/>`_ is the easiest way to get started with Docker.
            You just need to download the installer and follow the instructions.

         .. tab-item:: Colima on MacOS and Linux

            `Colima <https://github.com/abiosoft/colima>`_ is a new open-source project that makes it easy to run Docker on MacOS and Linux.
            It is a lightweight alternative to Docker Desktop with a focus on simplicity and performance.

            If you need multiple Docker environments, Colima is the recommended way.
            With colima, you can have multiple Docker environments running at the same time, each with its own Docker daemon and resource allocation thus avoiding conflicts.

         .. tab-item:: Docker CE on Linux

            The bare minimum to run Docker on Linux is to install the `Docker Engine <https://docs.docker.com/engine/install/>`_.
            If you don't need a graphical user interface, this is the recommended way to install Docker.

            .. note::

               You will need `root` privileges to perform the `post-installation steps <https://docs.docker.com/engine/install/linux-postinstall/>`_.
               Otherwise, you will need to use `sudo` for every Docker command.



   .. grid-item-card:: Start/stop container and use AiiDA interactively

      Start the image within Docker desktop or with docker CLI.
      The ``latest`` tag is the most recent stable version.
      You can replace ``latest`` tag with the version you want to use, check the `Docker Hub <https://hub.docker.com/r/aiidateam/aiida-core-with-services/tags>`__ for available tags/versions.

      .. tab-set::

         .. tab-item:: Docker Desktop

            #. Open Docker Desktop
            #. Click on the ``+`` button on the top left corner
            #. Select ``Image`` tab
            #. Search for ``aiidateam/aiida-core-with-services``
            #. Select the ``latest`` tag
            #. Click on ``Run``

         .. tab-item:: Docker CLI

            No matter how you installed Docker, you can always use the Docker CLI to run the image.

            .. parsed-literal::

               $ docker run -it aiidateam/aiida-core-with-services:latest bash

            You can specify a name for the container with the ``--name`` option for easier reference later on:

            .. parsed-literal::

               $ docker run -it --name aiida-container aiidateam/aiida-core-with-services:latest bash

            The ``-it`` option is used to run the container in interactive mode and to allocate a pseudo-TTY.
            You will be dropped into a bash shell inside the container.

            To exit the container, type ``exit`` or press ``Ctrl+D``, the container will be stopped.

            To start the container again, run:

            .. parsed-literal::

               $ docker start -i aiida-container

            If you need another shell inside the container, run:

            .. parsed-literal::

               $ docker exec -it aiida-container bash

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

      To check the verdi status, execute the following command inside the container:

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

Congratulations! You have a working AiiDA environment, you can start using it.

If you use the Docker image for the development or for the production environment, you are likely to need some extra settings to make it work as you expect.

.. dropdown:: Copy files from your computer to the container

   .. tab-set::

      .. tab-item:: Docker Desktop

         #. !!! test me in windows !!!
         #. Open Docker Desktop
         #. Click on the ``Containers/Apps`` button on the left sidebar
         #. Click on the ``aiida-container`` container
         #. Click on the ``CLI`` button on the top right corner
         #. Click on the ``+`` button on the top left corner
         #. Select ``File/Folder`` tab
         #. Select the file/folder you want to copy
         #. Select the destination path in the container
         #. Click on ``Copy``

      .. tab-item:: Docker CLI

         Use the ``docker cp`` command if you need to copy files from your computer to the container or vice versa.

         For example, to copy a file named ``test.txt`` from your current working directory to the ``/home/aiida`` path in the container, run:

         .. code-block:: console

            $ docker cp test.txt aiida-container:/home/aiida


.. dropdown:: Persist data across different containers

   The lifetime of the data stored in a container is limited to the lifetime of that particular container.

   If you stop the container (`docker stop` or simply `Ctrl+D` from the container) and start it again, any data you created will persist.
   However, if you remove the container, **all data will be removed as well**.

   .. code-block:: console

      $ docker rm aiida-container

   The preferred way to persistently store data is to `create a volume <https://docs.docker.com/storage/volumes/>`__.

   .. tab-set::

      .. tab-item:: Docker Desktop

         1. Open Docker Desktop
         1. ???

      .. tab-item:: Docker CLI

         To create a simple volume, run:

         .. code-block:: console

            $ docker volume create container-home-data

         Then make sure to mount that volume when the first time launching the aiida container:

         .. parsed-literal::

            $ docker run -it --name aiida-container -v container-home-data:/home/aiida aiidateam/aiida-core:latest bash

         Starting the container with the above command, ensures that any data stored in the ``/home/aiida`` path within the container is stored in the ``conatiner-home-data`` volume and therefore persists even if the container is removed.

         To persistently store the Python packages installed in the container, use `--user` flag when installing packages with pip, the packages will be installed in the ``/home/aiida/.local`` path which is mounted to the ``container-home-data`` volume.

         You can also mount a local directory instead of a volume and to other container paths, please refer to the `Docker documentation <https://docs.docker.com/storage/bind-mounts/>`__ for more information.

.. dropdown:: Backup the container

   To backup the data of AiiDA, you can still follow the instructions in the `Backup and restore <backup_and_restore>`__ section.
   However, the container provide a more convinient way if you just want to take a snapshot of the data by backup the whole container or the volume mounted to the container.

   This part is adapt from the `Docker documentation <https://docs.docker.com/desktop/backup-and-restore/>`__.

   If you don't have a volume mounted to the container, you can backup the whole container by commit the container to an image:

   .. parsed-literal::

      $ docker container commit aiida-container aiida-container-backup

   The above command will create a new image named ``aiida-container-backup`` which contains all the data and modifications you made in the container.

   Use `docker push` to push the ``aiida-container-backup`` image to a registry if you want to share it with others.

   Alternatively, you can also export the container to a local tarball:

   .. parsed-literal::

      $ docker save -o aiida-container-backup.tar aiida-container-backup

   To restore the container, pull the image or load from the tarball, run:

   .. parsed-literal::

      $ docker load -i aiida-container-backup.tar

   If you used a `named volume <https://docs.docker.com/storage/volumes/#backup-a-containerhttps://docs.docker.com/storage/#more-details-about-mount-types>`__, you can backup the volume.

   .. tab-set::

      .. tab-item:: Docker Desktop

         Docker Desktop provides a `Volumes Backup & Share extension <https://hub.docker.com/extensions/docker/volumes-backup-extension>`__ which allows you to backup and restore volumes effortlessly.

         The extension can be found from the Marketplace in the Docker Desktop GUI.
         Install the extension and follow the instructions to backup and restore volumes.

      .. tab-item:: Docker CLI

         Please check `Backup, restore, or migrate data volumes <https://docs.docker.com/storage/volumes/#backup-restore-or-migrate-data-volumes>`__ for more information.

.. button-ref:: intro:get_started:next
   :ref-type: ref
   :expand:
   :color: primary
   :outline:
   :class: sd-font-weight-bold

   What's next?
