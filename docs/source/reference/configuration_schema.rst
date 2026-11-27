Configuration schema compatibility
==================================

The AiiDA configuration file is stored in ``<AIIDA_PATH>/config.json``.

AiiDA does not upgrade the configuration file automatically.
If the schema is outdated, run ``verdi config upgrade`` to upgrade it to the current schema and keep a backup of the original.
From Python, call ``aiida.manage.configuration.load_config(upgrade=True)``.

If a newer AiiDA version rewrites the configuration file to a schema that an older installation cannot read, run ``verdi config downgrade <SCHEMA_VERSION>`` with the newer installation before switching back.

The table below summarizes the released ``aiida-core`` version series and the configuration schema versions they write and read.

.. list-table:: Configuration schema compatibility by ``aiida-core`` version
   :header-rows: 1

   * - ``aiida-core`` version series
     - Compatible schema version(s)
   * - 1.0 - 1.3
     - 3
   * - 1.4 - 1.5
     - 3 - 4
   * - 1.6
     - 5
   * - 2.0
     - 8
   * - 2.1 - 2.8
     - 9
   * - 2.9
     - 9 - 10

Schema versions 6 and 7 were only used by development snapshots.
They were not part of a stable ``aiida-core`` release series.
