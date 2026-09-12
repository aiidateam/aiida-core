.. _topics:storage:

*******
Storage
*******

Each AiiDA profile defines a *storage* which is where all data in the provenance graph is stored.
Typically, a storage consists of a :ref:`database <topics:database>` and a :ref:`repository <topics:repository>`.
The provenance graph data itself is mostly persisted to the database, whereas files attached to nodes (or other binary content) are stored in the repository.

By default, the storage consists of a PostgreSQL database and a `disk-objectstore container <https://disk-objectstore.readthedocs.io/en/latest/>`_ for the file repository.
As of AiiDA 2.0, however, this storage can be customized through plugins, meaning other databases and file stores can be used if desired.
AiiDA ships itself with a number of storage plugins that each have their own strengths and weaknesses.
This section gives an overview of these storage plugins with suggestions of when to use them.

.. grid:: 1 2 2 2
   :gutter: 3

   .. grid-item-card:: ``core.psql_dos``
      :link: topics:storage:psql_dos
      :link-type: ref

      *Default storage for production projects that require performance.*

      :fa:`database;mr-1` PostgreSQL database

      :fa:`file;mr-1` ``disk-objectstore`` container

      :fa:`plus;mr-1` **Strengths**:

      - Supports all of AiiDA's functionality
      - Good performance
      - Automatic database migrations

      :fa:`minus;mr-1` **Weaknesses**:

      - Requires a service running (PostgreSQL)

   .. grid-item-card:: ``core.sqlite_dos``
      :link: topics:storage:sqlite_dos
      :link-type: ref

      *Easy to set up storage for tests, demos and experimenting.*

      :fa:`database;mr-1` SQLite database

      :fa:`file;mr-1` ``disk-objectstore`` container

      :fa:`plus;mr-1` **Strengths**:

      - Easy to set up and backup
      - Requires no running services

      :fa:`minus;mr-1` **Weaknesses**:

      - Performance of SQLite is inferior to PostgreSQL
      - Some ``QueryBuilder`` functionality is not supported :fa:`asterisk`

   .. grid-item-card:: ``core.sqlite_zip``
      :link: topics:storage:sqlite_zip
      :link-type: ref

      *Storage contained in single ZIP file used for export archives.*

      :fa:`database;mr-1` SQLite database

      :fa:`file;mr-1` ``disk-objectstore`` container

      :fa:`plus;mr-1` **Strengths**:

      - Easy to set up
      - Requires no running services

      :fa:`minus;mr-1` **Weaknesses**:

      - Read-only
      - Some ``QueryBuilder`` functionality is not supported :fa:`asterisk`

   .. grid-item-card:: ``core.sqlite_temp``
      :link: topics:storage:sqlite_temp
      :link-type: ref

      *Temporary storage mostly used for unit testing or demonstrations.*

      :fa:`database;mr-1` SQLite database

      :fa:`file;mr-1` Sandbox directory

      :fa:`plus;mr-1` **Strengths**:

      - Requires no running services
      - Automatic cleanup

      :fa:`minus;mr-1` **Weaknesses**:

      - Storage is deleted once session is closed
      - Some ``QueryBuilder`` functionality is not supported :fa:`asterisk`

.. _topics:storage:psql_dos:

``core.psql_dos``
=================

The ``core.psql_dos`` storage plugin is the default and is recommended for all production work.
It uses PostgreSQL for the database and the disk-objectstore for the file repository.
To create a profile using this storage plugin, run:

.. code-block:: console

    verdi profile setup core.psql_dos

The command requires the PostgreSQL database to already exist and to be able to connect to it.

.. tip::

    Try the ``verdi presto --use-postgres`` command to have the PostgreSQL database automatically created.
    Certain systems require root access to do so, causing the command to fail if it cannot obtain root access.
    In this case, the database should be created manually (see :ref:`installation:guide-complete:create-profile:core-psql-dos` for details).
    Once created, a profile can be created using the database with the command ``verdi profile setup core.psql_dos``.


.. _topics:storage:sqlite_dos:

``core.sqlite_dos``
===================

The ``core.sqlite_dos`` storage plugin is an alternative to the ``core.psql_dos`` storage for use cases where performance is not critical.
Instead of a PostgreSQL database, it uses SQLite.
This makes it easier to set up as it does not require a running service, as the SQLite database is just a file on disk.

A fully operational profile using this storage plugin can be created with a single command:

.. code-block:: console

    verdi profile setup core.sqlite_dos -n --profile-name <PROFILE_NAME> --email <EMAIL>

replacing ``<PROFILE_NAME>`` with the desired name for the profile and ``<EMAIL>`` with the email for the default user.

The SQLite database and disk-objectstore container are both stored in the directory specified by the ``--filepath`` option of the ``verdi profile setup core.sqlite_dos`` command.
By default, this is a folder inside the directory defined by the ``$AIIDA_PATH/repository`` of the form ``sqlite_dos_{UUID}``, where the suffix is randomly generated hexadecimal UUID.
An example of an automated generated directory is ``.aiida/repository/sqlite_dos_962e87af09b746c985335cb77acaa553``.

.. note::

    The ``$AIIDA_PATH`` environment variable :ref:`determines the location of the configuration directory <how-to:installation:configure:instance-isolation>`, and defaults to ``.aiida`` in the user's home folder


.. _topics:storage:sqlite_zip:

``core.sqlite_zip``
===================

The ``core.sqlite_zip`` is a storage plugin that is used to create export archives.
It functions more or less identical to the ``core.sqlite_dos`` plugin, as it uses an SQLite database and a disk-objectstore container, except everything is bundled up in a `zip archive <https://en.wikipedia.org/wiki/ZIP_(file_format)>`_.

The storage plugin is not suited for normal use, because once the archive is created, it becomes read-only.
However, since otherwise it functions like normal storage plugins, a profile can be created with it that make it easy to explore its contents:

.. code-block:: console

    verdi profile setup core.sqlite_zip -n --profile-name <PROFILE_NAME> --filepath <ARCHIVE>

replacing ``<PROFILE_NAME>`` with the desired name for the profile and ``<ARCHIVE>`` the path to the archive file.
The created profile can now be loaded like any other profile, and the contents of the provenance graph can be explored as usual.


.. _topics:storage:sqlite_temp:

``core.sqlite_temp``
====================

The ``core.sqlite_temp`` storage plugin utilises an in-memory SQLite database and sandbox folder to store data.
The data is automatically destroyed as soon as the profile is garbage collected, which is either when it is unloaded, or the Python interpreter is shut down.
This makes this storage plugin primarily useful for demonstration and testing purposes, whereby no persistent storage is required.

A new temporary profile can be created and loaded as follows:

.. code-block:: python

    from aiida import load_profile
    from aiida.storage.sqlite_temp import SqliteTempBackend

    temp_profile = SqliteTempBackend.create_profile('temp-profile')
    load_profile(temp_profile, allow_switch=True)
