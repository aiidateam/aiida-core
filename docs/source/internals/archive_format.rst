.. _internal_architecture:orm:archive:

********************
AiiDA archive format
********************

An AiiDA archive is a single file format (with canonical extension ``.aiida``), for long term storage of an AiiDA provenance graph.
It provides a data storage backend, integrating a database and file repository.

The standard format is a ZIP archive, containing the following files:

* ``metadata.json`` file containing information on the version of the archive.
* ``db.sqlite3`` file containing the AiiDA database.
* ``repo/`` directory containing the AiiDA file repository.

.. image:: include/images/archive-file-structure.*
    :width: 60%
    :align: center

The central directory is written with the metadata and database records at the top of the file.
Zip files are read first from the bottom, which contains the byte position of the start of the central directory, then scanning down the central directory to extract records for each file.
When extracting the metadata/database only, one can simply scan for that record, then break and directly decompress the byte array for that file.
In this way, we do not have to scan through all the records of the repository files


.. _internal_architecture:orm:archive:metadata:

metadata
--------

This file contains important information, and it is necessary for the correct interpretation of ``db.sqlite3```.
This is used to avoid any incompatibilities among different versions of AiiDA.

Hre is an example ``metadata.json``:

.. literalinclude :: includes/metadata.json
   :language: json

At the beginning of the file, we see the version of the archive file (under ``export_version``) and the version of the AiiDA code.
New archive versions are introduced for several different reasons; this may generally be when:

* a change occurs in what can or cannot be exported for each entity,
* the database and/or archive schemes are updated or changed,
* or standardized exported property values are updated in AiiDA.

.. note::
    For archives of version 0.3 and older it is advisable that you manually try to convince yourself that the migration was completely successful.
    While all migrations are tested, trying to include reasonable edge-cases, the migrations involved from version 0.3 to 0.4 are intricate and the possibility of a missing edge-case test is quite real.
    It is worth noting that if you ever have an issue, please report it on `GitHub <https://www.github.com/aiidateam/aiida_core/issues/new>`_, join the `AiiDA mailing list <http://www.aiida.net/mailing-list/>`_, or use the `contact form <http://www.aiida.net/contact-new/>`_.

.. note::

    If you have migrated an archive file to the newest version, there may be an extra entry in ``metadata.json``.
    This simply states from which archive version the file was migrated.

.. note::

    If you supply an old archive file that the current AiiDA code does not support, ``verdi archive import`` will automatically try to migrate the archive by calling ``verdi archive migrate``.

.. _internal_architecture:orm:archive:data-json:

database
--------

The database is in sqlite format.

The schema is dynamically generated from the SQLAlchemy ORM classes for the "main" database (converting `JSONB` -> `JSON`, and `UUID` -> `String`).

.. seealso::

    :ref:`internal_architecture:database`
