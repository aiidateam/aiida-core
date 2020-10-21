.. _intro:get_started:docker:
.. _intro:install:docker:

****************************
Run AiiDA via a Docker image
****************************

The AiiDA team maintains a `Docker <https://www.docker.com/>`__ image on `Docker Hub <https://hub.docker.com/r/aiidateam/aiida-core>`__.
This image contains a fully pre-configured AiiDA environment which makes it particularly useful for learning and testing purposes.

.. panels::
   :container: container-lg pb-3
   :column: col-lg-12 p-2

   **Start container**

   First, pull the image:

   .. parsed-literal::

      $ docker pull aiidateam/aiida-core:\ |release|\

   Then start the container with:

   .. parsed-literal::

      $ docker run -d --name aiida-container aiidateam/aiida-core:\ |release|\

   You can use the following command to block until all services have started up:

   .. code-block:: console

      $ docker exec -t aiida-container wait-for-services

   ---

   **Check setup**

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

   .. link-button:: intro:get_started:next
       :type: ref
       :text: What's next?
       :classes: btn-outline-primary btn-block font-weight-bold

.. caution::

    All data stored in the container will persist as long as you restart the same container, e.g., with (``docker start aiida-container``), however if you remove the container, all data will be lost.
    Use `volumes <https://docs.docker.com/storage/volumes/>`__ to share data between containers and ensure its persistency on the host machine.
