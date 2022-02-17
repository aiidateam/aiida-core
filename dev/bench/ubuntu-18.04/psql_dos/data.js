window.BENCHMARK_DATA = {
  "lastUpdate": 1645113608078,
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
          "id": "5d2f15380417ce963544e209346b31eb37b0490d",
          "message": "CI: move time consuming tests to separate workflow that runs nightly (#5354)\n\nThe test that runs the Reverse Polish Notation (RPN) workchains and the\r\nmigrations tests are relatively time consuming and they should not be\r\naffected by most commits. That's why we can afford to have them just run\r\nnightly instead of on every PR.\r\n\r\nA `nightly` GHA workflow is added that runs every day at midnight. It\r\nruns a bash script `tests_nightly.sh` that in turns runs the script\r\n`test_polish_workchains.sh` as well as the unit test using `pytest`. The\r\nlatter is called with the option `-m 'nightly'` which will select only\r\ntests that are marked as nightly.\r\n\r\nMost tests under `tests/backends/aiida_sqlalchemy/migrations` are marked\r\nas nightly. This is done by applying the `@pytest.mark.nightly` decorator\r\ndirectly to the test functions. For the tests under the `django_branch`\r\nand `sqlalchemy_branch` this is instead done dynamically through the\r\n`pytest_collection_modifyitems` function in the `conftest.py` module\r\nsince having to manually apply this to all test would be too tedious.",
          "timestamp": "2022-02-16T21:29:06+01:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/5d2f15380417ce963544e209346b31eb37b0490d",
          "distinct": true,
          "tree_id": "3b4a2afd93d37b7233ba4416ac2ceb2b76da3067"
        },
        "date": 1645043940481,
        "benches": [
          {
            "name": "tests/benchmark/test_archive.py::test_export[no-objects]",
            "value": 3.1701031393954473,
            "unit": "iter/sec",
            "range": "stddev: 0.052487",
            "group": "import-export",
            "extra": "mean: 315.45 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_export[with-objects]",
            "value": 3.138115808139239,
            "unit": "iter/sec",
            "range": "stddev: 0.062125",
            "group": "import-export",
            "extra": "mean: 318.66 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[no-objects]",
            "value": 3.9549640087909497,
            "unit": "iter/sec",
            "range": "stddev: 0.068536",
            "group": "import-export",
            "extra": "mean: 252.85 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[with-objects]",
            "value": 3.642978700599368,
            "unit": "iter/sec",
            "range": "stddev: 0.080402",
            "group": "import-export",
            "extra": "mean: 274.50 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.1697230488719152,
            "unit": "iter/sec",
            "range": "stddev: 0.0066537",
            "group": "engine",
            "extra": "mean: 315.48 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.7086376034557312,
            "unit": "iter/sec",
            "range": "stddev: 0.066622",
            "group": "engine",
            "extra": "mean: 1.4112 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.8239377794065551,
            "unit": "iter/sec",
            "range": "stddev: 0.080778",
            "group": "engine",
            "extra": "mean: 1.2137 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.17467563628942318,
            "unit": "iter/sec",
            "range": "stddev: 0.18706",
            "group": "engine",
            "extra": "mean: 5.7249 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.20023076948990295,
            "unit": "iter/sec",
            "range": "stddev: 0.12972",
            "group": "engine",
            "extra": "mean: 4.9942 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.323034737184233,
            "unit": "iter/sec",
            "range": "stddev: 0.079613",
            "group": "engine",
            "extra": "mean: 430.47 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.541400490837474,
            "unit": "iter/sec",
            "range": "stddev: 0.092722",
            "group": "engine",
            "extra": "mean: 1.8471 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.6372251458642222,
            "unit": "iter/sec",
            "range": "stddev: 0.10094",
            "group": "engine",
            "extra": "mean: 1.5693 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.15500062040308057,
            "unit": "iter/sec",
            "range": "stddev: 0.21821",
            "group": "engine",
            "extra": "mean: 6.4516 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.18252847129605382,
            "unit": "iter/sec",
            "range": "stddev: 0.17237",
            "group": "engine",
            "extra": "mean: 5.4786 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 403.0266089259273,
            "unit": "iter/sec",
            "range": "stddev: 0.00015443",
            "group": "node",
            "extra": "mean: 2.4812 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 148.75965545571552,
            "unit": "iter/sec",
            "range": "stddev: 0.0012695",
            "group": "node",
            "extra": "mean: 6.7223 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 76.95895678710839,
            "unit": "iter/sec",
            "range": "stddev: 0.0012788",
            "group": "node",
            "extra": "mean: 12.994 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 239.4705470960342,
            "unit": "iter/sec",
            "range": "stddev: 0.00037625",
            "group": "node",
            "extra": "mean: 4.1759 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 59.49193615243202,
            "unit": "iter/sec",
            "range": "stddev: 0.0017637",
            "group": "node",
            "extra": "mean: 16.809 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 49.90088197790537,
            "unit": "iter/sec",
            "range": "stddev: 0.026309",
            "group": "node",
            "extra": "mean: 20.040 msec\nrounds: 100"
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
          "id": "2f97069bba22a2979faa94fa991987f823236d02",
          "message": "🔧 MAINTAIN: Drop typing-extensions dependency (#5357)\n\nThis was only required for python < 3.8, which we no longer support",
          "timestamp": "2022-02-16T23:06:34+01:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/2f97069bba22a2979faa94fa991987f823236d02",
          "distinct": true,
          "tree_id": "afe99527247a5cbe6138a0d2992a6c1b422ce4d6"
        },
        "date": 1645049755248,
        "benches": [
          {
            "name": "tests/benchmark/test_archive.py::test_export[no-objects]",
            "value": 2.2333343327008386,
            "unit": "iter/sec",
            "range": "stddev: 0.53262",
            "group": "import-export",
            "extra": "mean: 447.76 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_export[with-objects]",
            "value": 3.0942889070128308,
            "unit": "iter/sec",
            "range": "stddev: 0.057382",
            "group": "import-export",
            "extra": "mean: 323.18 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[no-objects]",
            "value": 4.178898399499416,
            "unit": "iter/sec",
            "range": "stddev: 0.056141",
            "group": "import-export",
            "extra": "mean: 239.30 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[with-objects]",
            "value": 3.977917685223745,
            "unit": "iter/sec",
            "range": "stddev: 0.057067",
            "group": "import-export",
            "extra": "mean: 251.39 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.3473766607435786,
            "unit": "iter/sec",
            "range": "stddev: 0.0045730",
            "group": "engine",
            "extra": "mean: 298.74 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.7402415354477448,
            "unit": "iter/sec",
            "range": "stddev: 0.075678",
            "group": "engine",
            "extra": "mean: 1.3509 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.8737244562411166,
            "unit": "iter/sec",
            "range": "stddev: 0.072354",
            "group": "engine",
            "extra": "mean: 1.1445 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.18333095710716074,
            "unit": "iter/sec",
            "range": "stddev: 0.14775",
            "group": "engine",
            "extra": "mean: 5.4546 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.20910030396072266,
            "unit": "iter/sec",
            "range": "stddev: 0.17386",
            "group": "engine",
            "extra": "mean: 4.7824 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.720852113635188,
            "unit": "iter/sec",
            "range": "stddev: 0.0074983",
            "group": "engine",
            "extra": "mean: 367.53 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.6004993360713009,
            "unit": "iter/sec",
            "range": "stddev: 0.095133",
            "group": "engine",
            "extra": "mean: 1.6653 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.6992421076529872,
            "unit": "iter/sec",
            "range": "stddev: 0.058584",
            "group": "engine",
            "extra": "mean: 1.4301 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.16606511370791752,
            "unit": "iter/sec",
            "range": "stddev: 0.15063",
            "group": "engine",
            "extra": "mean: 6.0217 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.1964356062257517,
            "unit": "iter/sec",
            "range": "stddev: 0.15764",
            "group": "engine",
            "extra": "mean: 5.0907 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 404.63312535683394,
            "unit": "iter/sec",
            "range": "stddev: 0.00012711",
            "group": "node",
            "extra": "mean: 2.4714 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 154.0146812124185,
            "unit": "iter/sec",
            "range": "stddev: 0.00079658",
            "group": "node",
            "extra": "mean: 6.4929 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 78.87710384585264,
            "unit": "iter/sec",
            "range": "stddev: 0.00081103",
            "group": "node",
            "extra": "mean: 12.678 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 247.16666487492648,
            "unit": "iter/sec",
            "range": "stddev: 0.00057157",
            "group": "node",
            "extra": "mean: 4.0459 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 59.923423533492205,
            "unit": "iter/sec",
            "range": "stddev: 0.0015877",
            "group": "node",
            "extra": "mean: 16.688 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 51.21302062126826,
            "unit": "iter/sec",
            "range": "stddev: 0.026020",
            "group": "node",
            "extra": "mean: 19.526 msec\nrounds: 100"
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
          "id": "cb8a8016c633002f20956b33e7b887bf2f30d0e9",
          "message": "Pre-commit: update requirement for `flynt` to `v0.76` (#5355)\n\nCo-authored-by: Chris Sewell <chrisj_sewell@hotmail.com>",
          "timestamp": "2022-02-17T07:37:03+01:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/cb8a8016c633002f20956b33e7b887bf2f30d0e9",
          "distinct": true,
          "tree_id": "f5188689065798a95ef40b10f151f5fd8bcf948a"
        },
        "date": 1645080360891,
        "benches": [
          {
            "name": "tests/benchmark/test_archive.py::test_export[no-objects]",
            "value": 3.2283744777123653,
            "unit": "iter/sec",
            "range": "stddev: 0.024393",
            "group": "import-export",
            "extra": "mean: 309.75 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_export[with-objects]",
            "value": 3.2149918938574364,
            "unit": "iter/sec",
            "range": "stddev: 0.050606",
            "group": "import-export",
            "extra": "mean: 311.04 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[no-objects]",
            "value": 4.27235877469474,
            "unit": "iter/sec",
            "range": "stddev: 0.061334",
            "group": "import-export",
            "extra": "mean: 234.06 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[with-objects]",
            "value": 4.143606323454927,
            "unit": "iter/sec",
            "range": "stddev: 0.062708",
            "group": "import-export",
            "extra": "mean: 241.34 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.3563351855511714,
            "unit": "iter/sec",
            "range": "stddev: 0.0047744",
            "group": "engine",
            "extra": "mean: 297.94 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.7834184526399974,
            "unit": "iter/sec",
            "range": "stddev: 0.083341",
            "group": "engine",
            "extra": "mean: 1.2765 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.9252345516891208,
            "unit": "iter/sec",
            "range": "stddev: 0.068878",
            "group": "engine",
            "extra": "mean: 1.0808 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.18876548135784788,
            "unit": "iter/sec",
            "range": "stddev: 0.12383",
            "group": "engine",
            "extra": "mean: 5.2976 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.21867308901318705,
            "unit": "iter/sec",
            "range": "stddev: 0.10924",
            "group": "engine",
            "extra": "mean: 4.5730 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.502018042058528,
            "unit": "iter/sec",
            "range": "stddev: 0.086850",
            "group": "engine",
            "extra": "mean: 399.68 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.6080335491198331,
            "unit": "iter/sec",
            "range": "stddev: 0.10309",
            "group": "engine",
            "extra": "mean: 1.6446 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.7046726613960629,
            "unit": "iter/sec",
            "range": "stddev: 0.097226",
            "group": "engine",
            "extra": "mean: 1.4191 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.17142737021641716,
            "unit": "iter/sec",
            "range": "stddev: 0.20830",
            "group": "engine",
            "extra": "mean: 5.8334 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.20307001773895422,
            "unit": "iter/sec",
            "range": "stddev: 0.14723",
            "group": "engine",
            "extra": "mean: 4.9244 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 402.4951365802448,
            "unit": "iter/sec",
            "range": "stddev: 0.00099824",
            "group": "node",
            "extra": "mean: 2.4845 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 161.0094605343398,
            "unit": "iter/sec",
            "range": "stddev: 0.00014918",
            "group": "node",
            "extra": "mean: 6.2108 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 85.02718908901099,
            "unit": "iter/sec",
            "range": "stddev: 0.00073190",
            "group": "node",
            "extra": "mean: 11.761 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 286.0488476294994,
            "unit": "iter/sec",
            "range": "stddev: 0.00036000",
            "group": "node",
            "extra": "mean: 3.4959 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 67.61607872326545,
            "unit": "iter/sec",
            "range": "stddev: 0.0015675",
            "group": "node",
            "extra": "mean: 14.789 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 62.71916038533166,
            "unit": "iter/sec",
            "range": "stddev: 0.0014482",
            "group": "node",
            "extra": "mean: 15.944 msec\nrounds: 100"
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
          "id": "a7603903adbd39491e0c7ec9629d595dd048c5fa",
          "message": "✨ NEW: Allow for CLI usage via `python -m aiida` (#5356)\n\nThis allows for advanced use-cases, where one may wish to directly specify the python interpreter to use.",
          "timestamp": "2022-02-17T14:23:48+01:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/a7603903adbd39491e0c7ec9629d595dd048c5fa",
          "distinct": true,
          "tree_id": "08150dfb6d10c9f13aaae166d5e414855ad6e573"
        },
        "date": 1645104783476,
        "benches": [
          {
            "name": "tests/benchmark/test_archive.py::test_export[no-objects]",
            "value": 3.4659264610757146,
            "unit": "iter/sec",
            "range": "stddev: 0.017251",
            "group": "import-export",
            "extra": "mean: 288.52 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_export[with-objects]",
            "value": 3.1540229611757438,
            "unit": "iter/sec",
            "range": "stddev: 0.055464",
            "group": "import-export",
            "extra": "mean: 317.06 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[no-objects]",
            "value": 4.1234753229646985,
            "unit": "iter/sec",
            "range": "stddev: 0.049872",
            "group": "import-export",
            "extra": "mean: 242.51 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[with-objects]",
            "value": 4.015036548762351,
            "unit": "iter/sec",
            "range": "stddev: 0.054103",
            "group": "import-export",
            "extra": "mean: 249.06 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.3084252374630743,
            "unit": "iter/sec",
            "range": "stddev: 0.0055206",
            "group": "engine",
            "extra": "mean: 302.26 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.7596734648628507,
            "unit": "iter/sec",
            "range": "stddev: 0.076123",
            "group": "engine",
            "extra": "mean: 1.3164 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.8446968215304248,
            "unit": "iter/sec",
            "range": "stddev: 0.094352",
            "group": "engine",
            "extra": "mean: 1.1839 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.1806061934379535,
            "unit": "iter/sec",
            "range": "stddev: 0.24141",
            "group": "engine",
            "extra": "mean: 5.5369 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.2079849542452831,
            "unit": "iter/sec",
            "range": "stddev: 0.17798",
            "group": "engine",
            "extra": "mean: 4.8080 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.434248339192897,
            "unit": "iter/sec",
            "range": "stddev: 0.076065",
            "group": "engine",
            "extra": "mean: 410.80 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.576998325616006,
            "unit": "iter/sec",
            "range": "stddev: 0.057999",
            "group": "engine",
            "extra": "mean: 1.7331 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.6809500585527489,
            "unit": "iter/sec",
            "range": "stddev: 0.12792",
            "group": "engine",
            "extra": "mean: 1.4685 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.16331721362308305,
            "unit": "iter/sec",
            "range": "stddev: 0.19114",
            "group": "engine",
            "extra": "mean: 6.1231 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.19138599900359438,
            "unit": "iter/sec",
            "range": "stddev: 0.13772",
            "group": "engine",
            "extra": "mean: 5.2250 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 453.14842473032,
            "unit": "iter/sec",
            "range": "stddev: 0.00017221",
            "group": "node",
            "extra": "mean: 2.2068 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 116.06205100643137,
            "unit": "iter/sec",
            "range": "stddev: 0.0040968",
            "group": "node",
            "extra": "mean: 8.6161 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 62.27365441533657,
            "unit": "iter/sec",
            "range": "stddev: 0.0058712",
            "group": "node",
            "extra": "mean: 16.058 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 256.06893490461204,
            "unit": "iter/sec",
            "range": "stddev: 0.00021336",
            "group": "node",
            "extra": "mean: 3.9052 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 61.50240678382678,
            "unit": "iter/sec",
            "range": "stddev: 0.0025094",
            "group": "node",
            "extra": "mean: 16.260 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 51.98323411989952,
            "unit": "iter/sec",
            "range": "stddev: 0.023996",
            "group": "node",
            "extra": "mean: 19.237 msec\nrounds: 100"
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
          "id": "ca4c47a9f0e042168f0d3432cb63e20739ffee94",
          "message": "Docs: minor fixes in migration docstrings (#5360)\n\nSome of the SqlAlchemy migrations referenced the incorrect analog Django\r\nrevisions, which could cause confusion.\r\n\r\nAlso corrects a small typo in the recently added changes to the bash\r\nscript `.github/workflows/verdi.sh` used in the test workflows.",
          "timestamp": "2022-02-17T15:39:42+01:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/ca4c47a9f0e042168f0d3432cb63e20739ffee94",
          "distinct": true,
          "tree_id": "948a62d5f1a37827ab20ea106cb5b8ab90ce9730"
        },
        "date": 1645109347882,
        "benches": [
          {
            "name": "tests/benchmark/test_archive.py::test_export[no-objects]",
            "value": 3.3219653299003093,
            "unit": "iter/sec",
            "range": "stddev: 0.030793",
            "group": "import-export",
            "extra": "mean: 301.03 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_export[with-objects]",
            "value": 3.1655224004440523,
            "unit": "iter/sec",
            "range": "stddev: 0.060561",
            "group": "import-export",
            "extra": "mean: 315.90 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[no-objects]",
            "value": 4.148208637633789,
            "unit": "iter/sec",
            "range": "stddev: 0.062447",
            "group": "import-export",
            "extra": "mean: 241.07 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[with-objects]",
            "value": 3.991973025801766,
            "unit": "iter/sec",
            "range": "stddev: 0.061740",
            "group": "import-export",
            "extra": "mean: 250.50 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.2280482592788133,
            "unit": "iter/sec",
            "range": "stddev: 0.0075086",
            "group": "engine",
            "extra": "mean: 309.78 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.7327254963744622,
            "unit": "iter/sec",
            "range": "stddev: 0.098435",
            "group": "engine",
            "extra": "mean: 1.3648 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.8531813650144271,
            "unit": "iter/sec",
            "range": "stddev: 0.070423",
            "group": "engine",
            "extra": "mean: 1.1721 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.18056088053165473,
            "unit": "iter/sec",
            "range": "stddev: 0.11363",
            "group": "engine",
            "extra": "mean: 5.5383 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.20780923155900177,
            "unit": "iter/sec",
            "range": "stddev: 0.17849",
            "group": "engine",
            "extra": "mean: 4.8121 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.448156987906198,
            "unit": "iter/sec",
            "range": "stddev: 0.077376",
            "group": "engine",
            "extra": "mean: 408.47 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.5683938111495975,
            "unit": "iter/sec",
            "range": "stddev: 0.093092",
            "group": "engine",
            "extra": "mean: 1.7593 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.652064662642775,
            "unit": "iter/sec",
            "range": "stddev: 0.12643",
            "group": "engine",
            "extra": "mean: 1.5336 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.15437335171223868,
            "unit": "iter/sec",
            "range": "stddev: 0.21745",
            "group": "engine",
            "extra": "mean: 6.4778 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.1790111143278565,
            "unit": "iter/sec",
            "range": "stddev: 0.17903",
            "group": "engine",
            "extra": "mean: 5.5862 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 405.73334321790617,
            "unit": "iter/sec",
            "range": "stddev: 0.0012750",
            "group": "node",
            "extra": "mean: 2.4647 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 145.05894092195138,
            "unit": "iter/sec",
            "range": "stddev: 0.0010227",
            "group": "node",
            "extra": "mean: 6.8937 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 69.62198330609142,
            "unit": "iter/sec",
            "range": "stddev: 0.0020077",
            "group": "node",
            "extra": "mean: 14.363 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 234.05153310141114,
            "unit": "iter/sec",
            "range": "stddev: 0.00066216",
            "group": "node",
            "extra": "mean: 4.2726 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 59.434733909764006,
            "unit": "iter/sec",
            "range": "stddev: 0.0020996",
            "group": "node",
            "extra": "mean: 16.825 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 48.67886727379514,
            "unit": "iter/sec",
            "range": "stddev: 0.027822",
            "group": "node",
            "extra": "mean: 20.543 msec\nrounds: 100"
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
          "id": "092919d5d160f00beb5cea5c9467ac5037f89222",
          "message": "🔧 MAINTAIN: Rename `_dbmodel -> model` and `dbmodel -> bare_model` (#5358)\n\nThis fixes a confusing naming, since `_dbmodel` pointed to the `ModelWrapper`,\r\nwhich wraps together the SQLA ORM model and storage backend,\r\nand `dbmodel` pointed to the \"bare\" SQLA ORM model.\r\n\r\nWhen getting/setting fields, the behaviour of both is very different, and so there should be a clear distinction.",
          "timestamp": "2022-02-17T16:49:15+01:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/092919d5d160f00beb5cea5c9467ac5037f89222",
          "distinct": true,
          "tree_id": "dca3d52a321f3c11f3edfc6611e657b78b28cdcb"
        },
        "date": 1645113599404,
        "benches": [
          {
            "name": "tests/benchmark/test_archive.py::test_export[no-objects]",
            "value": 2.6956863217734854,
            "unit": "iter/sec",
            "range": "stddev: 0.061935",
            "group": "import-export",
            "extra": "mean: 370.96 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_export[with-objects]",
            "value": 2.7170246918254866,
            "unit": "iter/sec",
            "range": "stddev: 0.057016",
            "group": "import-export",
            "extra": "mean: 368.05 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[no-objects]",
            "value": 3.6177710416193336,
            "unit": "iter/sec",
            "range": "stddev: 0.054728",
            "group": "import-export",
            "extra": "mean: 276.41 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[with-objects]",
            "value": 3.4902853284375173,
            "unit": "iter/sec",
            "range": "stddev: 0.054170",
            "group": "import-export",
            "extra": "mean: 286.51 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 2.897185973693628,
            "unit": "iter/sec",
            "range": "stddev: 0.0063666",
            "group": "engine",
            "extra": "mean: 345.16 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.6594572328131637,
            "unit": "iter/sec",
            "range": "stddev: 0.078578",
            "group": "engine",
            "extra": "mean: 1.5164 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.7532347992344034,
            "unit": "iter/sec",
            "range": "stddev: 0.077985",
            "group": "engine",
            "extra": "mean: 1.3276 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.15833785815852827,
            "unit": "iter/sec",
            "range": "stddev: 0.18969",
            "group": "engine",
            "extra": "mean: 6.3156 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.18094105338243502,
            "unit": "iter/sec",
            "range": "stddev: 0.14391",
            "group": "engine",
            "extra": "mean: 5.5267 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.328066119202834,
            "unit": "iter/sec",
            "range": "stddev: 0.0078403",
            "group": "engine",
            "extra": "mean: 429.54 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.520186801908303,
            "unit": "iter/sec",
            "range": "stddev: 0.063807",
            "group": "engine",
            "extra": "mean: 1.9224 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.6039852274558223,
            "unit": "iter/sec",
            "range": "stddev: 0.082776",
            "group": "engine",
            "extra": "mean: 1.6557 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.13968182939786555,
            "unit": "iter/sec",
            "range": "stddev: 0.13087",
            "group": "engine",
            "extra": "mean: 7.1591 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.1664718636086052,
            "unit": "iter/sec",
            "range": "stddev: 0.13536",
            "group": "engine",
            "extra": "mean: 6.0070 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 353.08876508221704,
            "unit": "iter/sec",
            "range": "stddev: 0.00018649",
            "group": "node",
            "extra": "mean: 2.8321 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 134.6924091948946,
            "unit": "iter/sec",
            "range": "stddev: 0.00077697",
            "group": "node",
            "extra": "mean: 7.4243 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 73.72982960886304,
            "unit": "iter/sec",
            "range": "stddev: 0.00080380",
            "group": "node",
            "extra": "mean: 13.563 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 223.46632929663494,
            "unit": "iter/sec",
            "range": "stddev: 0.00044061",
            "group": "node",
            "extra": "mean: 4.4749 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 54.58257866800555,
            "unit": "iter/sec",
            "range": "stddev: 0.0017188",
            "group": "node",
            "extra": "mean: 18.321 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 47.34403388163901,
            "unit": "iter/sec",
            "range": "stddev: 0.022677",
            "group": "node",
            "extra": "mean: 21.122 msec\nrounds: 100"
          }
        ]
      }
    ]
  }
}