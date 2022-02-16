window.BENCHMARK_DATA = {
  "lastUpdate": 1645025041196,
  "repoUrl": "https://github.com/aiidateam/aiida-core",
  "xAxis": "id",
  "oneChartGroups": [],
  "entries": {
    "pytest-benchmarks:ubuntu-18.04,psql_dos": [
      {
        "cpu": {
          "speed": "2.30",
          "cores": 2,
          "physicalCores": 2,
          "processors": 1
        },
        "extra": {
          "pythonVersion": "3.8.12",
          "metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "842d47dcc441919adf052d7ecd794e189aa46ba4",
          "message": "🔧 MAINTAIN: Add `NotImplementedError` for migration downgrades\n\nDowngrading storage version is not explicitly supported in aiida-core,\nor exposed for the user.\nPrevious to #5330, some downgrade functionality was required for testing,\nsince migration tests involved migrating down the global profile,\nthen migrating it back up to the target version.\nThese migrations though were often incomplete,\nmigrating database schema but not the actual data.\n\nNow, migration tests are performed by starting with a separate, empty profile,\nand migrating up.\nSince these downgrades are no longer required and are un-tested,\nwe replace their content with an explicit `NotImplementedError`.",
          "timestamp": "2022-02-16T16:12:30+01:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/842d47dcc441919adf052d7ecd794e189aa46ba4",
          "distinct": true,
          "tree_id": "c2d36d6b93520a6528fdab05620c11eaf6c4cc4e"
        },
        "date": 1645025034018,
        "benches": [
          {
            "name": "tests/benchmark/test_archive.py::test_export[no-objects]",
            "value": 2.5946070700264072,
            "unit": "iter/sec",
            "range": "stddev: 0.054219",
            "group": "import-export",
            "extra": "mean: 385.41 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_export[with-objects]",
            "value": 2.8179836391913002,
            "unit": "iter/sec",
            "range": "stddev: 0.0066625",
            "group": "import-export",
            "extra": "mean: 354.86 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[no-objects]",
            "value": 3.6363045342939064,
            "unit": "iter/sec",
            "range": "stddev: 0.047117",
            "group": "import-export",
            "extra": "mean: 275.00 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[with-objects]",
            "value": 3.2335673191509002,
            "unit": "iter/sec",
            "range": "stddev: 0.067586",
            "group": "import-export",
            "extra": "mean: 309.26 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 2.427713072256826,
            "unit": "iter/sec",
            "range": "stddev: 0.024483",
            "group": "engine",
            "extra": "mean: 411.91 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.582683545755672,
            "unit": "iter/sec",
            "range": "stddev: 0.13993",
            "group": "engine",
            "extra": "mean: 1.7162 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.6776161125593224,
            "unit": "iter/sec",
            "range": "stddev: 0.044641",
            "group": "engine",
            "extra": "mean: 1.4758 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.15107082439610334,
            "unit": "iter/sec",
            "range": "stddev: 0.24569",
            "group": "engine",
            "extra": "mean: 6.6194 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.16696951055231152,
            "unit": "iter/sec",
            "range": "stddev: 0.40728",
            "group": "engine",
            "extra": "mean: 5.9891 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.075021252969379,
            "unit": "iter/sec",
            "range": "stddev: 0.033544",
            "group": "engine",
            "extra": "mean: 481.92 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.49166375963422,
            "unit": "iter/sec",
            "range": "stddev: 0.13826",
            "group": "engine",
            "extra": "mean: 2.0339 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.5409047792695654,
            "unit": "iter/sec",
            "range": "stddev: 0.048586",
            "group": "engine",
            "extra": "mean: 1.8488 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.13754107357841283,
            "unit": "iter/sec",
            "range": "stddev: 0.31272",
            "group": "engine",
            "extra": "mean: 7.2706 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.15399872990973604,
            "unit": "iter/sec",
            "range": "stddev: 0.32923",
            "group": "engine",
            "extra": "mean: 6.4936 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 305.72486471158305,
            "unit": "iter/sec",
            "range": "stddev: 0.00026962",
            "group": "node",
            "extra": "mean: 3.2709 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 114.80145674689119,
            "unit": "iter/sec",
            "range": "stddev: 0.0011330",
            "group": "node",
            "extra": "mean: 8.7107 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 68.20301389595856,
            "unit": "iter/sec",
            "range": "stddev: 0.0015481",
            "group": "node",
            "extra": "mean: 14.662 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 191.1539437143039,
            "unit": "iter/sec",
            "range": "stddev: 0.00037382",
            "group": "node",
            "extra": "mean: 5.2314 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 45.45770817458032,
            "unit": "iter/sec",
            "range": "stddev: 0.021902",
            "group": "node",
            "extra": "mean: 21.998 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 48.946801874706864,
            "unit": "iter/sec",
            "range": "stddev: 0.0020963",
            "group": "node",
            "extra": "mean: 20.430 msec\nrounds: 100"
          }
        ]
      }
    ]
  }
}