window.BENCHMARK_DATA = {
  "lastUpdate": 1645080367724,
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
      }
    ]
  }
}