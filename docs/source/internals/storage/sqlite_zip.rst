.. _internal_architecture:storage:sqlite_zip:

``sqlite_zip`` (archive) format
*******************************

The :py:class:`~aiida.storage.sqlite_zip.backend.SqliteZipBackend` is the storage format used for the AiiDA archive,
whose design draws from consideration outlined in :doc:`aep:005_exportformat/readme`.

An AiiDA archive is a single file format (with canonical extension ``.aiida``), for long term storage of an AiiDA provenance graph.
It provides a data storage backend, integrating a database and file repository.

The standard format is a ZIP archive, containing the following files:

* ``metadata.json`` file containing information on the version of the archive.
* ``db.sqlite3`` file containing the AiiDA database.
* ``repo/`` directory containing the AiiDA file repository.

.. figure:: static/archive-file-structure.*
    :width: 60%
    :align: center

    ``sqlite_zip`` zip file format.

The central directory is written with the metadata and database records at the top of the file.
Zip files are read first from the bottom, which contains the byte position of the start of the central directory, then scanning down the central directory to extract records for each file.
When extracting the metadata/database only, one can simply scan for that record, then break and directly decompress the byte array for that file.
In this way, we do not have to scan through all the records of the repository files

As opposed to the :ref:`internal_architecture:storage:psql_dos`, this format is "read-only", since zip files cannot be modified once created.

.. _internal_architecture:storage:sqlite_zip:metadata:

metadata schema
---------------

This file contains important information, and it is necessary for the correct interpretation of ``db.sqlite3```.
This is used to avoid any incompatibilities among different versions of AiiDA.

Here is an example ``metadata.json``:

.. literalinclude :: static/metadata.json
   :language: json

At the beginning of the file, we see the version of the archive file (under ``export_version``) and the version of the AiiDA code.
New archive versions are introduced for several different reasons; this may generally be when:

* a change occurs in what can or cannot be exported for each entity,
* the database and/or archive schemes are updated or changed,
* or standardized exported property values are updated in AiiDA.

.. important::
    For archives of version 0.3 and older it is advisable that you manually try to convince yourself that the migration was completely successful.
    While all migrations are tested, trying to include reasonable edge-cases, the migrations involved from version 0.3 to 0.4 are intricate and the possibility of a missing edge-case test is quite real.
    It is worth noting that if you ever have an issue, please report it on `GitHub <https://www.github.com/aiidateam/aiida_core/issues/new>`.

.. note::
    If you have migrated an archive file to the newest version, there may be an extra entry in ``metadata.json``.
    This simply states from which archive version the file was migrated.

.. note::

    If you supply an old archive file that the current AiiDA code does not support, ``verdi archive import`` will automatically try to migrate the archive by calling ``verdi archive migrate``.

.. _internal_architecture:storage:sqlite_zip:data-json:

repository format
-----------------

The repository is read by the :py:class:`~aiida.storage.sqlite_zip.backend.ZipfileBackendRepository`.

The zip file should contain repository files with the key format: ``repo/<sha256 hash>``, i.e. files named by the sha256 hash of the file contents, inside a ``repo`` directory.


database schema
---------------

The database schema is intended to directly mirror that of the :ref:`internal_architecture:storage:psql_dos`.
The only differences are in the handling of certain data types by SQLite versus PostgreSQL:

- ``UUID`` -> ``CHAR(32)``
- ``DateTime`` -> ``TZDateTime``
- ``JSONB`` -> ``JSON``

Also, `varchar_pattern_ops` indexes are not possible in SQLite.

Tables
......

.. sqla-model:: ~aiida.storage.sqlite_zip.models.DbUser

.. sqla-model:: ~aiida.storage.sqlite_zip.models.DbNode

.. sqla-model:: ~aiida.storage.sqlite_zip.models.DbLink

.. sqla-model:: ~aiida.storage.sqlite_zip.models.DbGroup

.. sqla-model:: ~aiida.storage.sqlite_zip.models.DbGroupNodes

.. sqla-model:: ~aiida.storage.sqlite_zip.models.DbComputer

.. sqla-model:: ~aiida.storage.sqlite_zip.models.DbAuthInfo

.. sqla-model:: ~aiida.storage.sqlite_zip.models.DbComment

.. sqla-model:: ~aiida.storage.sqlite_zip.models.DbLog
