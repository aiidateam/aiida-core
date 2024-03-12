.. _intro:get_started:

****************
Getting started
****************

An AiiDA installation consists of three core components (plus any external codes you wish to run):

* |aiida-core|: The main Python package and the associated ``verdi`` command line interface
* |PostgreSQL|: The service that manages the database that AiiDA uses to store data.
* |RabbitMQ|: The message broker used for communication within AiiDA.

.. toctree::
   :maxdepth: 1
   :hidden:

   install_system
   install_conda
   run_docker
   installation

.. _intro:install:setup:
.. _intro:get_started:setup:

Setup
=====

There are multiple routes to setting up a working AiiDA environment.
Which of those is optimal depends on your environment and use case.
If you are unsure, use the :ref:`system-wide installation <intro:get_started:system-wide-install>` method.

.. grid:: 1 2 2 2
   :gutter: 3

   .. grid-item-card:: :fa:`desktop;mr-1` System-wide installation

      .. button-ref:: intro:get_started:system-wide-install
         :ref-type: ref
         :click-parent:
         :class: btn-link

         Install all software directly on your workstation or laptop.

      Install the prerequisite services using standard package managers (apt, homebrew, etc.) with administrative privileges.

   .. grid-item-card:: :fa:`folder;mr-1` Installation into Conda environment

      .. button-ref:: intro:get_started:conda-install
         :ref-type: ref
         :click-parent:
         :class: btn-link

         Install all software into an isolated conda environment.

      This method does not require administrative privileges, but involves manual management of start-up and shut-down of services.

   .. grid-item-card:: :fa:`cube;mr-1` Run via docker container

      .. button-ref:: intro:get_started:docker
         :ref-type: ref
         :click-parent:
         :class: btn-link

         Run AiiDA and prerequisite services as a single docker container.

      Does not require the separate installation of prerequisite services.
      Especially well-suited to get directly started on the **tutorials**.

   .. grid-item-card:: :fa:`cloud;mr-1` Run via virtual machine

      .. button-link:: https://quantum-mobile.readthedocs.io/
         :click-parent:
         :class: btn-link

         Use a virtual machine with all the required software pre-installed.

      `Materials Cloud <https://www.materialscloud.org>`__ provides both downloadable and web based VMs,
      also incorporating pre-installed Materials Science codes.

.. _intro:get_started:next:

What's next?
============

After successfully completing one of the above outlined setup routes, if you are new to AiiDA, we recommed you go through the :ref:`Basic Tutorial <tutorial:basic>`,
or see our :ref:`Next steps guide <tutorial:next-steps>`.

If however, you encountered some issues, proceed to the :ref:`troubleshooting section <intro:troubleshooting>`.

.. admonition:: In-depth instructions
    :class: seealso title-icon-read-more

    For more detailed instructions on configuring AiiDA, :ref:`see the configuration how-to <how-to:installation:configure>`.

.. |aiida-core| replace:: `aiida-core <https://aiida.readthedocs.io/>`__
.. |PostgreSQL| replace:: `PostgreSQL <https://www.postgresql.org>`__
.. |RabbitMQ| replace:: `RabbitMQ <https://www.rabbitmq.com>`__
.. |Homebrew| replace:: `Homebrew <https://brew.sh>`__
