Configuration schema compatibility
==================================

The AiiDA configuration file is stored in ``<AIIDA_PATH>/.aiida/config.json``.

Whenever AiiDA accesses the configuration file, it automatically upgrades the configuration file for the newest schema version compatible with the current AiiDA version.

If an older AiiDA installation cannot read the configuration anymore, run ``verdi config downgrade <SCHEMA_VERSION>`` with the newer installation before switching back.

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

Schema versions 6 and 7 were only used by development snapshots.
They were not part of a stable ``aiida-core`` release series.
