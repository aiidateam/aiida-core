.. warning::

   This is work in progress and only available on the development branch

Postgres Database Manipulation API
==================================

This is the API for creating and dropping postgres users and databases used by the ``verdi quicksetup`` commandline tool. It allows convenient access to this functionality from within python without knowing details about how postgres is installed by default on various systems. If the postgres setup is not the default installation, additional information will have to be provided.

.. _controls.postgres:

The Postgres Class
------------------

.. autoclass:: aiida.control.postgres.Postgres
   :members:


Further utilities
-----------------

.. autofunction:: aiida.control.postgres.manual_setup_instructions

.. autofunction:: aiida.control.postgres.prompt_db_info
