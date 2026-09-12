.. _installation:docker:

======
Docker
======

The AiiDA team maintains a number of `Docker <https://www.docker.com/>`_ images on `Docker Hub <https://hub.docker.com/r/aiidateam>`_.
These images contain a fully pre-configured AiiDA environment which make it easy to get started using AiiDA if you are familiar with Docker.

Currently, there are three image variants:

.. grid:: auto
   :gutter: 3

   .. grid-item-card:: :fa:`bullseye;mr-1` aiida-core-base
      :text-align: center
      :shadow: md

      This is the base image.
      It comes just with the ``aiida-core`` package installed.
      It expects that the RabbitMQ and PostgreSQL services are provided.


   .. grid-item-card:: :fa:`puzzle-piece;mr-1` aiida-core-with-services
      :text-align: center
      :shadow: md

      This images builds on top of ``aiida-core-base`` but also installs RabbitMQ and PostgreSQL as services inside the image.
      This image is therefore complete and ready to be used.


   .. grid-item-card:: :fa:`code;mr-1` aiida-core-dev
      :text-align: center
      :shadow: md

      This image builds on top of ``aiida-core-with-services`` with the only difference that the ``aiida-core`` package is installed from source in editable mode.
      This makes this image suitable for development of the ``aiida-core`` package.


Start a container
=================

To start a container from an image, run:

.. code-block:: console

    docker run -it --name aiida aiidateam/aiida-core-with-services:latest bash

In this example, the ``aiida-core-with-services`` image is started where ``latest`` refers to the latest tag.
The ``--name`` option is optional but is recommended as it makes it easier to restart the same container at a later point in time.
The ``-it`` option is used to run the container in interactive mode and to allocate a pseudo-TTY.
After the container start up has finished, a bash shell inside the container is opened.

An AiiDA profile is automatically created when the container is started.
By default the profile is created using the ``core.psql_dos`` storage plugin and a default user is created.
See section :ref:`container configuration <installation:docker:container-configuration>` how to customize certain parts of this setup.

To confirm that everything is up and running as required, run:

.. code-block:: console

    verdi status

which should show something like::

    ✔ version:     AiiDA v2.5.1
    ✔ config:      /home/aiida/.aiida
    ✔ profile:     default
    ✔ storage:     Storage for 'default' [open] @ postgresql+psycopg://aiida:***@localhost:5432
    ✔ rabbitmq:    Connected to RabbitMQ v3.10.18 as amqp://guest:guest@127.0.0.1:5672
    ✔ daemon:      Daemon is running with PID 324

If all checks show green check marks, the container is ready to go.
The container can be shut down by typing ``exit`` or pressing ``CTRL+d``.
The container can be restarted at a later time, see :ref:`restarting a container <installation:docker:restarting-container>` for details.
Any data that was created in a previous session is still available.

.. caution::

    When the container is not just stopped but *deleted*, any data stored in the container, including the data stored in the profile's storage, is permanently deleted.
    To ensure the data is not lost, it should be persisted on a volume that is mounted to the container.
    Refer to the section on :ref:`persisting data <installation:docker:persisting-data>` for more details.


.. _installation:docker:restarting-container:

Restarting a container
======================

After shutting down a container, it can be restarted with:

.. code-block:: console

    docker start -i aiida

The name ``aiida`` here is the reference given with the ``--name`` option when the container was originally created.
To open an interactive bash shell inside the container, run:

.. code-block:: console

    docker exec -it aiida bash


.. _installation:docker:persisting-data:

Persisting data
===============

The preferred way to persistently store data across Docker containers is to `create a volume <https://docs.docker.com/storage/volumes/>`__.
To create a simple volume, run:

.. code-block:: console

    docker volume create container-home-data

In this case, one needs to specifically mount the volume the very first time that the container is created:

.. code-block:: console

    docker run -it --name aiida -v container-home-data:/home/aiida aiidateam/aiida-core-with-services:latest bash

By mounting the volume, any data that gets stored in the ``/home/aiida`` path within the container is stored in the ``container-home-data`` volume and therefore persists even if the container is deleted.

When installing packages with pip, use the ``--user`` flag to store the Python packages installed in the mounted volume (if you mount the home specifically to a volume as mentioned above) permanently.
The packages will be installed in the ``/home/aiida/.local`` directory of the container, which is mounted on the ``container-home-data`` volume.

You can also mount a folder in the container to a local directory, please refer to the `Docker documentation <https://docs.docker.com/storage/bind-mounts/>`__ for more information.


.. _installation:docker:container-configuration:

Container configuration
=======================

Upon container creation, the following environment variables can be set to configure the default profile that is created:

* ``AIIDA_PROFILE_NAME``: the name of the profile to be created (default: ``default``)
* ``AIIDA_USER_EMAIL``: the email of the default user to be created (default: ``aiida@localhost``)
* ``AIIDA_USER_FIRST_NAME``: the first name of the default user to be created (default: ``Giuseppe``)
* ``AIIDA_USER_LAST_NAME``: the last name of the default user to be created (default: ``Verdi``)
* ``AIIDA_USER_INSTITUTION``: the institution of the default user to be created (default: ``Khedivial``)

These environment variables can be set when starting the container with the ``-e`` option.

.. note::

    The ``AIIDA_CONFIG_FILE`` variable points to a path inside the container.
    Therefore, if you want to use a custom configuration file, it needs to be mounted from the host path to the container path.

.. _installation:docker:container-backup:

Container backup
================

To backup the data of AiiDA, you can follow the instructions in the `Backup and restore <backup_and_restore>`__ section.
However, Docker provides a convenient way to backup the container data by taking a snapshot of the entire container or the mounted volume(s).

The following is adapted from the `Docker documentation <https://docs.docker.com/desktop/backup-and-restore/>`__.
If you don't have a volume mounted to the container, you can backup the whole container by committing the container to an image:

.. code-block:: console

    docker container commit aiida aiida-container-backup

The above command will create from the container ``aiida`` a new image named ``aiida-container-backup``, containing all the data and modifications made in the container.
The container can then be exported to a tarball and for it to be stored permanently:

.. code-block:: console

    docker save -o aiida-container-backup.tar aiida-container-backup

To restore the container, pull the image, or load from the tarball:

.. code-block:: console

    docker load -i aiida-container-backup.tar

This creates a container that can then be started with ``docker start``.

Any `named volumes <https://docs.docker.com/storage/volumes/#backup-a-containerhttps://docs.docker.com/storage/#more-details-about-mount-types>`__, can be backed up independently.
Refer to `Backup, restore, or migrate data volumes <https://docs.docker.com/storage/volumes/#backup-restore-or-migrate-data-volumes>`__ for more information.
