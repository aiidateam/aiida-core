window.BENCHMARK_DATA = {
  "lastUpdate": 1645038049171,
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
      },
      {
        "cpu": {
          "speed": "2.60",
          "cores": 2,
          "physicalCores": 2,
          "processors": 1
        },
        "extra": {
          "pythonVersion": "3.8.12",
          "metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "be8d0a9a3f1735c71b00661f13dd5ba3666f385c",
          "message": "⬆️ UPGRADE: psycopg2 allow v2.9 (#5104)\n\nEnsure databases are correctly created and destroyed",
          "timestamp": "2022-02-16T19:50:19+01:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/be8d0a9a3f1735c71b00661f13dd5ba3666f385c",
          "distinct": true,
          "tree_id": "0e0b1e122e9ecbe055914ba94a31f850b07b7b64"
        },
        "date": 1645038042295,
        "benches": [
          {
            "name": "tests/benchmark/test_archive.py::test_export[no-objects]",
            "value": 2.710495398951709,
            "unit": "iter/sec",
            "range": "stddev: 0.051967",
            "group": "import-export",
            "extra": "mean: 368.94 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_export[with-objects]",
            "value": 2.5810522431849026,
            "unit": "iter/sec",
            "range": "stddev: 0.081293",
            "group": "import-export",
            "extra": "mean: 387.44 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[no-objects]",
            "value": 3.7683334509639126,
            "unit": "iter/sec",
            "range": "stddev: 0.068979",
            "group": "import-export",
            "extra": "mean: 265.37 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[with-objects]",
            "value": 3.6014580301152574,
            "unit": "iter/sec",
            "range": "stddev: 0.077926",
            "group": "import-export",
            "extra": "mean: 277.67 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 2.682481678041853,
            "unit": "iter/sec",
            "range": "stddev: 0.031806",
            "group": "engine",
            "extra": "mean: 372.79 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.6418572411831873,
            "unit": "iter/sec",
            "range": "stddev: 0.12650",
            "group": "engine",
            "extra": "mean: 1.5580 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.7386107459592254,
            "unit": "iter/sec",
            "range": "stddev: 0.070680",
            "group": "engine",
            "extra": "mean: 1.3539 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.16498431473224606,
            "unit": "iter/sec",
            "range": "stddev: 0.23518",
            "group": "engine",
            "extra": "mean: 6.0612 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.1868110327871363,
            "unit": "iter/sec",
            "range": "stddev: 0.18432",
            "group": "engine",
            "extra": "mean: 5.3530 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.2596305087351616,
            "unit": "iter/sec",
            "range": "stddev: 0.084532",
            "group": "engine",
            "extra": "mean: 442.55 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.5240703709674038,
            "unit": "iter/sec",
            "range": "stddev: 0.092627",
            "group": "engine",
            "extra": "mean: 1.9081 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.5953201185503332,
            "unit": "iter/sec",
            "range": "stddev: 0.14920",
            "group": "engine",
            "extra": "mean: 1.6798 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.1469241926309028,
            "unit": "iter/sec",
            "range": "stddev: 0.25690",
            "group": "engine",
            "extra": "mean: 6.8062 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.16979727465641373,
            "unit": "iter/sec",
            "range": "stddev: 0.16482",
            "group": "engine",
            "extra": "mean: 5.8894 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 343.22837042519126,
            "unit": "iter/sec",
            "range": "stddev: 0.00097525",
            "group": "node",
            "extra": "mean: 2.9135 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 126.7829225663908,
            "unit": "iter/sec",
            "range": "stddev: 0.0011625",
            "group": "node",
            "extra": "mean: 7.8875 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 63.349211061330514,
            "unit": "iter/sec",
            "range": "stddev: 0.0019030",
            "group": "node",
            "extra": "mean: 15.786 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 197.11616565968626,
            "unit": "iter/sec",
            "range": "stddev: 0.00099959",
            "group": "node",
            "extra": "mean: 5.0732 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 49.543318901412334,
            "unit": "iter/sec",
            "range": "stddev: 0.0031509",
            "group": "node",
            "extra": "mean: 20.184 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 40.69955305081628,
            "unit": "iter/sec",
            "range": "stddev: 0.029042",
            "group": "node",
            "extra": "mean: 24.570 msec\nrounds: 100"
          }
        ]
      }
    ]
  }
}