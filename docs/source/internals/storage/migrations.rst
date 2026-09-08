Storage schema migrations
=========================

AiiDA storage schema migrations use `Alembic <https://alembic.sqlalchemy.org>`_.
A revision identifier is stored in each migrated database and is therefore an immutable compatibility contract once released.

Revision identifiers and source files
-------------------------------------

Alembic keeps the branch label, revision identifier, and source filename as separate concepts.
Unlike a Git commit ID, an Alembic revision identifier may be chosen by the project and does not have to contain a branch name.
AiiDA's existing ``main`` migration lineage uses the convention of combining the branch name and sequence number into the revision identifier ``main_0003``.

The naming is therefore:

.. list-table::
   :header-rows: 1

   * - Item
     - Example
   * - Branch label
     - ``main``
   * - Sequence number
     - ``0003``
   * - Revision identifier
     - ``main_0003``
   * - Migration module
     - ``main_0003_aiida_v3_0_0.py``
   * - Branch-qualified Alembic target
     - ``main@main_0003``

Migration source files are located in ``src/aiida/storage/psql_dos/migrations/versions/`` and ``src/aiida/storage/sqlite_dos/migrations/versions/``.
Their filenames begin with the complete revision identifier and end with a concise description, following the pattern ``<revision_id>_<description>.py``.
For example, ``main_0003_aiida_v3_0_0.py`` contains ``revision = 'main_0003'`` and ``down_revision = 'main_0002'``.

The first ``main`` in ``main@main_0003`` is the Alembic branch label, while ``main_0003`` is the revision identifier.
This repetition is a consequence of AiiDA's established revision-ID convention and is not required by Alembic.
Existing revision identifiers must not be renamed after databases have been created with them, because they are stored in the ``alembic_version`` table.

Schema regression snapshots
---------------------------

The ``main``-branch migration schema tests name their regression snapshots as ``test_<revision_id>.yml``.
For example, revision ``main_0003`` uses ``test_main_0003.yml``.
