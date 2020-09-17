window.BENCHMARK_DATA = {
  "lastUpdate": 1600377046326,
  "repoUrl": "https://github.com/aiidateam/aiida-core",
  "entries": {
    "pytest-benchmarks:ubuntu-18.04,sqlalchemy": [
      {
        "cpu": {
          "speed": "2.30",
          "cores": 2,
          "physicalCores": 2,
          "processors": 1
        },
        "extra": {
          "pythonVersion": "3.8.5",
          "metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "731c8eab83c252503528ce9a24e6161ac31f3c13",
          "message": "Pytest Benchmark",
          "timestamp": "2020-09-09T21:08:28Z",
          "url": "https://github.com/aiidateam/aiida-core/pull/4362/commits/731c8eab83c252503528ce9a24e6161ac31f3c13"
        },
        "date": 1599758493218,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 2.0392626331391686,
            "unit": "iter/sec",
            "range": "stddev: 0.047315",
            "group": "engine",
            "extra": "mean: 490.37 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.45425920158161665,
            "unit": "iter/sec",
            "range": "stddev: 0.069730",
            "group": "engine",
            "extra": "mean: 2.2014 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.4895238507456362,
            "unit": "iter/sec",
            "range": "stddev: 0.074533",
            "group": "engine",
            "extra": "mean: 2.0428 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.11514248307270203,
            "unit": "iter/sec",
            "range": "stddev: 0.31994",
            "group": "engine",
            "extra": "mean: 8.6849 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.11901495940309838,
            "unit": "iter/sec",
            "range": "stddev: 0.18976",
            "group": "engine",
            "extra": "mean: 8.4023 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 87.23162167710244,
            "unit": "iter/sec",
            "range": "stddev: 0.0013315",
            "group": "node",
            "extra": "mean: 11.464 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 39.10448410164775,
            "unit": "iter/sec",
            "range": "stddev: 0.0021459",
            "group": "node",
            "extra": "mean: 25.573 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 38.03800680575806,
            "unit": "iter/sec",
            "range": "stddev: 0.0021152",
            "group": "node",
            "extra": "mean: 26.289 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 47.31205320102713,
            "unit": "iter/sec",
            "range": "stddev: 0.0017188",
            "group": "node",
            "extra": "mean: 21.136 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 21.919671456112553,
            "unit": "iter/sec",
            "range": "stddev: 0.019488",
            "group": "node",
            "extra": "mean: 45.621 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 22.133814342495445,
            "unit": "iter/sec",
            "range": "stddev: 0.0033080",
            "group": "node",
            "extra": "mean: 45.180 msec\nrounds: 100"
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
          "pythonVersion": "3.8.5",
          "metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "f53bf967f1fb7b9201fa3937a21fe826fcce343d",
          "message": "Pytest Benchmark",
          "timestamp": "2020-09-10T17:18:54Z",
          "url": "https://github.com/aiidateam/aiida-core/pull/4362/commits/f53bf967f1fb7b9201fa3937a21fe826fcce343d"
        },
        "date": 1599764686026,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 2.756003025816805,
            "unit": "iter/sec",
            "range": "stddev: 0.035486",
            "group": "engine",
            "extra": "mean: 362.84 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.629378237651267,
            "unit": "iter/sec",
            "range": "stddev: 0.072092",
            "group": "engine",
            "extra": "mean: 1.5889 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.6783702215530796,
            "unit": "iter/sec",
            "range": "stddev: 0.081151",
            "group": "engine",
            "extra": "mean: 1.4741 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.14743595273468163,
            "unit": "iter/sec",
            "range": "stddev: 0.24757",
            "group": "engine",
            "extra": "mean: 6.7826 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.157356657096493,
            "unit": "iter/sec",
            "range": "stddev: 0.21117",
            "group": "engine",
            "extra": "mean: 6.3550 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 1.6277239416096239,
            "unit": "iter/sec",
            "range": "stddev: 0.010803",
            "group": "engine",
            "extra": "mean: 614.35 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.3546804964353583,
            "unit": "iter/sec",
            "range": "stddev: 0.51526",
            "group": "engine",
            "extra": "mean: 2.8194 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.42405457454750983,
            "unit": "iter/sec",
            "range": "stddev: 0.084029",
            "group": "engine",
            "extra": "mean: 2.3582 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.11322759447902399,
            "unit": "iter/sec",
            "range": "stddev: 0.21555",
            "group": "engine",
            "extra": "mean: 8.8318 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.1278211087913815,
            "unit": "iter/sec",
            "range": "stddev: 0.32119",
            "group": "engine",
            "extra": "mean: 7.8234 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 91.93725709892495,
            "unit": "iter/sec",
            "range": "stddev: 0.00072600",
            "group": "node",
            "extra": "mean: 10.877 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 42.930182871993864,
            "unit": "iter/sec",
            "range": "stddev: 0.00097433",
            "group": "node",
            "extra": "mean: 23.294 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 42.815554439314674,
            "unit": "iter/sec",
            "range": "stddev: 0.00065092",
            "group": "node",
            "extra": "mean: 23.356 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 50.08698047429539,
            "unit": "iter/sec",
            "range": "stddev: 0.0010594",
            "group": "node",
            "extra": "mean: 19.965 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 27.024916045098884,
            "unit": "iter/sec",
            "range": "stddev: 0.0016549",
            "group": "node",
            "extra": "mean: 37.003 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 26.373656127749523,
            "unit": "iter/sec",
            "range": "stddev: 0.0020498",
            "group": "node",
            "extra": "mean: 37.917 msec\nrounds: 100"
          }
        ]
      },
      {
        "cpu": {
          "speed": "2.30",
          "cores": 2,
          "physicalCores": 2,
          "processors": 1
        },
        "extra": {
          "pythonVersion": "3.8.5",
          "metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "cbd44d0114d4e40c269ba789ed873ab50fff6d17",
          "message": "Pytest Benchmark",
          "timestamp": "2020-09-10T17:18:54Z",
          "url": "https://github.com/aiidateam/aiida-core/pull/4362/commits/cbd44d0114d4e40c269ba789ed873ab50fff6d17"
        },
        "date": 1599765555401,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 1.9769860891908226,
            "unit": "iter/sec",
            "range": "stddev: 0.058427",
            "group": "engine",
            "extra": "mean: 505.82 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.4661940131842296,
            "unit": "iter/sec",
            "range": "stddev: 0.081532",
            "group": "engine",
            "extra": "mean: 2.1450 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.49589439167314414,
            "unit": "iter/sec",
            "range": "stddev: 0.084564",
            "group": "engine",
            "extra": "mean: 2.0166 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.11924445095533401,
            "unit": "iter/sec",
            "range": "stddev: 0.20631",
            "group": "engine",
            "extra": "mean: 8.3861 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.12379522029236328,
            "unit": "iter/sec",
            "range": "stddev: 0.47479",
            "group": "engine",
            "extra": "mean: 8.0779 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 1.2696168007847903,
            "unit": "iter/sec",
            "range": "stddev: 0.029096",
            "group": "engine",
            "extra": "mean: 787.64 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.2970376600151341,
            "unit": "iter/sec",
            "range": "stddev: 0.14648",
            "group": "engine",
            "extra": "mean: 3.3666 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.3141356439545759,
            "unit": "iter/sec",
            "range": "stddev: 0.18851",
            "group": "engine",
            "extra": "mean: 3.1833 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.08573143173707033,
            "unit": "iter/sec",
            "range": "stddev: 0.52448",
            "group": "engine",
            "extra": "mean: 11.664 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.09096600662265804,
            "unit": "iter/sec",
            "range": "stddev: 0.22392",
            "group": "engine",
            "extra": "mean: 10.993 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 57.40768621316207,
            "unit": "iter/sec",
            "range": "stddev: 0.00099549",
            "group": "node",
            "extra": "mean: 17.419 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 28.19161322815218,
            "unit": "iter/sec",
            "range": "stddev: 0.0025423",
            "group": "node",
            "extra": "mean: 35.472 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 26.41122900044952,
            "unit": "iter/sec",
            "range": "stddev: 0.0030362",
            "group": "node",
            "extra": "mean: 37.863 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 33.36589857268057,
            "unit": "iter/sec",
            "range": "stddev: 0.0025967",
            "group": "node",
            "extra": "mean: 29.971 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 17.82304268202831,
            "unit": "iter/sec",
            "range": "stddev: 0.0058031",
            "group": "node",
            "extra": "mean: 56.107 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 17.946818545798173,
            "unit": "iter/sec",
            "range": "stddev: 0.0044665",
            "group": "node",
            "extra": "mean: 55.720 msec\nrounds: 100"
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
          "pythonVersion": "3.8.5",
          "metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "33ead345827bed40819db28882b33e36035c83f6",
          "message": "update [skip ci]",
          "timestamp": "2020-09-10T20:14:41+01:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/33ead345827bed40819db28882b33e36035c83f6",
          "distinct": true,
          "tree_id": "76b476b599ba5230e2a87670f510167444c9726c"
        },
        "date": 1599765912005,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 2.807230951723594,
            "unit": "iter/sec",
            "range": "stddev: 0.041306",
            "group": "engine",
            "extra": "mean: 356.22 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.653604895325344,
            "unit": "iter/sec",
            "range": "stddev: 0.057669",
            "group": "engine",
            "extra": "mean: 1.5300 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.704518129207774,
            "unit": "iter/sec",
            "range": "stddev: 0.044435",
            "group": "engine",
            "extra": "mean: 1.4194 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.15618620993517573,
            "unit": "iter/sec",
            "range": "stddev: 0.16725",
            "group": "engine",
            "extra": "mean: 6.4026 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.16621961215214312,
            "unit": "iter/sec",
            "range": "stddev: 0.17064",
            "group": "engine",
            "extra": "mean: 6.0161 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 1.6826634825342865,
            "unit": "iter/sec",
            "range": "stddev: 0.050884",
            "group": "engine",
            "extra": "mean: 594.30 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.39974905510018466,
            "unit": "iter/sec",
            "range": "stddev: 0.054461",
            "group": "engine",
            "extra": "mean: 2.5016 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.43966535036116233,
            "unit": "iter/sec",
            "range": "stddev: 0.081456",
            "group": "engine",
            "extra": "mean: 2.2745 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.11957761587933131,
            "unit": "iter/sec",
            "range": "stddev: 0.13713",
            "group": "engine",
            "extra": "mean: 8.3628 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.13509437250584577,
            "unit": "iter/sec",
            "range": "stddev: 0.11542",
            "group": "engine",
            "extra": "mean: 7.4022 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 98.82617666969725,
            "unit": "iter/sec",
            "range": "stddev: 0.00087361",
            "group": "node",
            "extra": "mean: 10.119 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 44.023085639198186,
            "unit": "iter/sec",
            "range": "stddev: 0.0015493",
            "group": "node",
            "extra": "mean: 22.715 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 41.84148691929428,
            "unit": "iter/sec",
            "range": "stddev: 0.0037067",
            "group": "node",
            "extra": "mean: 23.900 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 51.989023592811286,
            "unit": "iter/sec",
            "range": "stddev: 0.0013483",
            "group": "node",
            "extra": "mean: 19.235 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 26.816295495720777,
            "unit": "iter/sec",
            "range": "stddev: 0.017839",
            "group": "node",
            "extra": "mean: 37.291 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 28.33178385390476,
            "unit": "iter/sec",
            "range": "stddev: 0.0039963",
            "group": "node",
            "extra": "mean: 35.296 msec\nrounds: 100"
          }
        ]
      },
      {
        "cpu": {
          "speed": "2.30",
          "cores": 2,
          "physicalCores": 2,
          "processors": 1
        },
        "extra": {
          "pythonVersion": "3.8.5",
          "metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "115342eae460f7c49f3fdf66e1f4cdc4fef5acbd",
          "message": "update [skip ci]",
          "timestamp": "2020-09-10T20:29:02+01:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/115342eae460f7c49f3fdf66e1f4cdc4fef5acbd",
          "distinct": true,
          "tree_id": "40a7f322fa263975cd99ecc0e4bb8c0c2b1c59ad"
        },
        "date": 1599766799435,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 2.6868918502756602,
            "unit": "iter/sec",
            "range": "stddev: 0.024119",
            "group": "engine",
            "extra": "mean: 372.18 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.6065182549244819,
            "unit": "iter/sec",
            "range": "stddev: 0.085393",
            "group": "engine",
            "extra": "mean: 1.6488 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.6655065121462032,
            "unit": "iter/sec",
            "range": "stddev: 0.057012",
            "group": "engine",
            "extra": "mean: 1.5026 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.15187498592783327,
            "unit": "iter/sec",
            "range": "stddev: 0.15230",
            "group": "engine",
            "extra": "mean: 6.5844 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.15868598590418648,
            "unit": "iter/sec",
            "range": "stddev: 0.16220",
            "group": "engine",
            "extra": "mean: 6.3018 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 1.646529091729727,
            "unit": "iter/sec",
            "range": "stddev: 0.054519",
            "group": "engine",
            "extra": "mean: 607.34 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.3829999384700249,
            "unit": "iter/sec",
            "range": "stddev: 0.081114",
            "group": "engine",
            "extra": "mean: 2.6110 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.42083078721851985,
            "unit": "iter/sec",
            "range": "stddev: 0.056512",
            "group": "engine",
            "extra": "mean: 2.3763 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.11345195409870949,
            "unit": "iter/sec",
            "range": "stddev: 0.31248",
            "group": "engine",
            "extra": "mean: 8.8143 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.12457383649929096,
            "unit": "iter/sec",
            "range": "stddev: 0.27423",
            "group": "engine",
            "extra": "mean: 8.0274 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 92.21471377231796,
            "unit": "iter/sec",
            "range": "stddev: 0.0017262",
            "group": "node",
            "extra": "mean: 10.844 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 39.031467467660775,
            "unit": "iter/sec",
            "range": "stddev: 0.0043306",
            "group": "node",
            "extra": "mean: 25.620 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 43.11651733831051,
            "unit": "iter/sec",
            "range": "stddev: 0.0012388",
            "group": "node",
            "extra": "mean: 23.193 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 43.67269455393042,
            "unit": "iter/sec",
            "range": "stddev: 0.0034559",
            "group": "node",
            "extra": "mean: 22.898 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 21.70077997668201,
            "unit": "iter/sec",
            "range": "stddev: 0.019520",
            "group": "node",
            "extra": "mean: 46.081 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 25.361104678611017,
            "unit": "iter/sec",
            "range": "stddev: 0.0031129",
            "group": "node",
            "extra": "mean: 39.430 msec\nrounds: 100"
          }
        ]
      },
      {
        "cpu": {
          "speed": "2.30",
          "cores": 2,
          "physicalCores": 2,
          "processors": 1
        },
        "extra": {
          "pythonVersion": "3.8.5",
          "metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "c2c29be9da141714834c22e3b87ba4c6be22fccd",
          "message": "update [skip ci]",
          "timestamp": "2020-09-10T20:48:26+01:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/c2c29be9da141714834c22e3b87ba4c6be22fccd",
          "distinct": true,
          "tree_id": "77b0a47016a3b3dc4bf37abb1f154b63a3b2aa0b"
        },
        "date": 1599768056974,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 2.324372316870854,
            "unit": "iter/sec",
            "range": "stddev: 0.037270",
            "group": "engine",
            "extra": "mean: 430.22 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.5200494667266808,
            "unit": "iter/sec",
            "range": "stddev: 0.10649",
            "group": "engine",
            "extra": "mean: 1.9229 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.5558143802793624,
            "unit": "iter/sec",
            "range": "stddev: 0.064944",
            "group": "engine",
            "extra": "mean: 1.7992 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.13196781023135476,
            "unit": "iter/sec",
            "range": "stddev: 0.18503",
            "group": "engine",
            "extra": "mean: 7.5776 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.13593305350541987,
            "unit": "iter/sec",
            "range": "stddev: 0.27310",
            "group": "engine",
            "extra": "mean: 7.3566 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 1.369582627489939,
            "unit": "iter/sec",
            "range": "stddev: 0.044165",
            "group": "engine",
            "extra": "mean: 730.15 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.30602509748094453,
            "unit": "iter/sec",
            "range": "stddev: 0.089157",
            "group": "engine",
            "extra": "mean: 3.2677 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.35168829510327276,
            "unit": "iter/sec",
            "range": "stddev: 0.068737",
            "group": "engine",
            "extra": "mean: 2.8434 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.09805020797396977,
            "unit": "iter/sec",
            "range": "stddev: 0.20030",
            "group": "engine",
            "extra": "mean: 10.199 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.10705028225405941,
            "unit": "iter/sec",
            "range": "stddev: 0.16457",
            "group": "engine",
            "extra": "mean: 9.3414 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 86.99490366370833,
            "unit": "iter/sec",
            "range": "stddev: 0.0011469",
            "group": "node",
            "extra": "mean: 11.495 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 34.92613479784596,
            "unit": "iter/sec",
            "range": "stddev: 0.0035197",
            "group": "node",
            "extra": "mean: 28.632 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 33.67757505426463,
            "unit": "iter/sec",
            "range": "stddev: 0.0040486",
            "group": "node",
            "extra": "mean: 29.693 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 41.55703296284225,
            "unit": "iter/sec",
            "range": "stddev: 0.0027748",
            "group": "node",
            "extra": "mean: 24.063 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 22.095441949552338,
            "unit": "iter/sec",
            "range": "stddev: 0.0047714",
            "group": "node",
            "extra": "mean: 45.258 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 22.071949352532368,
            "unit": "iter/sec",
            "range": "stddev: 0.0033741",
            "group": "node",
            "extra": "mean: 45.306 msec\nrounds: 100"
          }
        ]
      },
      {
        "cpu": {
          "speed": "2.40",
          "cores": 2,
          "physicalCores": 2,
          "processors": 1
        },
        "extra": {
          "pythonVersion": "3.8.5",
          "metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "3b9d693bbcfbef0a9f681d0413050ee8e28f32f0",
          "message": "update [skip ci]",
          "timestamp": "2020-09-10T20:50:59+01:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/3b9d693bbcfbef0a9f681d0413050ee8e28f32f0",
          "distinct": true,
          "tree_id": "1bd3c6009554ef89e3b10f5dcd5b73b12fdec060"
        },
        "date": 1599768149410,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 2.6455277948137046,
            "unit": "iter/sec",
            "range": "stddev: 0.037404",
            "group": "engine",
            "extra": "mean: 378.00 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.5983221187129178,
            "unit": "iter/sec",
            "range": "stddev: 0.041875",
            "group": "engine",
            "extra": "mean: 1.6713 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.6569058986833438,
            "unit": "iter/sec",
            "range": "stddev: 0.051352",
            "group": "engine",
            "extra": "mean: 1.5223 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.1514294350669826,
            "unit": "iter/sec",
            "range": "stddev: 0.18071",
            "group": "engine",
            "extra": "mean: 6.6037 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.15710725748848517,
            "unit": "iter/sec",
            "range": "stddev: 0.11370",
            "group": "engine",
            "extra": "mean: 6.3651 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 1.675513830965864,
            "unit": "iter/sec",
            "range": "stddev: 0.010306",
            "group": "engine",
            "extra": "mean: 596.83 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.36981468012056984,
            "unit": "iter/sec",
            "range": "stddev: 0.074877",
            "group": "engine",
            "extra": "mean: 2.7041 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.41650792149270965,
            "unit": "iter/sec",
            "range": "stddev: 0.073031",
            "group": "engine",
            "extra": "mean: 2.4009 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.1156477696756397,
            "unit": "iter/sec",
            "range": "stddev: 0.17034",
            "group": "engine",
            "extra": "mean: 8.6469 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.12831358237028076,
            "unit": "iter/sec",
            "range": "stddev: 0.12942",
            "group": "engine",
            "extra": "mean: 7.7934 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 90.56827991938958,
            "unit": "iter/sec",
            "range": "stddev: 0.0014717",
            "group": "node",
            "extra": "mean: 11.041 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 42.31515523631427,
            "unit": "iter/sec",
            "range": "stddev: 0.00099902",
            "group": "node",
            "extra": "mean: 23.632 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 42.14701235570128,
            "unit": "iter/sec",
            "range": "stddev: 0.00093799",
            "group": "node",
            "extra": "mean: 23.726 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 49.78896732106217,
            "unit": "iter/sec",
            "range": "stddev: 0.0011927",
            "group": "node",
            "extra": "mean: 20.085 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 26.22067162748943,
            "unit": "iter/sec",
            "range": "stddev: 0.0018030",
            "group": "node",
            "extra": "mean: 38.138 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 25.32315971744902,
            "unit": "iter/sec",
            "range": "stddev: 0.0030613",
            "group": "node",
            "extra": "mean: 39.490 msec\nrounds: 100"
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
          "pythonVersion": "3.8.5",
          "metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "7d521c5e049b2ccb1fa2aaf303fedb1850d9da87",
          "message": "add import-export [skip ci]",
          "timestamp": "2020-09-10T22:15:43+01:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/7d521c5e049b2ccb1fa2aaf303fedb1850d9da87",
          "distinct": true,
          "tree_id": "fcf2b1e721e078dfca86cee6645c3e6784bb43d1"
        },
        "date": 1599773422844,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 2.8101385274873043,
            "unit": "iter/sec",
            "range": "stddev: 0.031714",
            "group": "engine",
            "extra": "mean: 355.85 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.6370690076477097,
            "unit": "iter/sec",
            "range": "stddev: 0.056221",
            "group": "engine",
            "extra": "mean: 1.5697 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.6720630312303606,
            "unit": "iter/sec",
            "range": "stddev: 0.079351",
            "group": "engine",
            "extra": "mean: 1.4880 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.15326945583448576,
            "unit": "iter/sec",
            "range": "stddev: 0.19778",
            "group": "engine",
            "extra": "mean: 6.5245 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.1598327646256341,
            "unit": "iter/sec",
            "range": "stddev: 0.19442",
            "group": "engine",
            "extra": "mean: 6.2565 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 1.6544859911517655,
            "unit": "iter/sec",
            "range": "stddev: 0.051893",
            "group": "engine",
            "extra": "mean: 604.42 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.38271228042887334,
            "unit": "iter/sec",
            "range": "stddev: 0.048911",
            "group": "engine",
            "extra": "mean: 2.6129 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.4315552804716326,
            "unit": "iter/sec",
            "range": "stddev: 0.058965",
            "group": "engine",
            "extra": "mean: 2.3172 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.11725233364826872,
            "unit": "iter/sec",
            "range": "stddev: 0.12353",
            "group": "engine",
            "extra": "mean: 8.5286 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.13072593633429652,
            "unit": "iter/sec",
            "range": "stddev: 0.11311",
            "group": "engine",
            "extra": "mean: 7.6496 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 3.0693730252854388,
            "unit": "iter/sec",
            "range": "stddev: 0.0037589",
            "group": "import-export",
            "extra": "mean: 325.80 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.5697930815053054,
            "unit": "iter/sec",
            "range": "stddev: 0.047302",
            "group": "import-export",
            "extra": "mean: 389.14 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 0.15463169040640584,
            "unit": "iter/sec",
            "range": "stddev: 0.059006",
            "group": "import-export",
            "extra": "mean: 6.4670 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 0.15114226206267115,
            "unit": "iter/sec",
            "range": "stddev: 0.11763",
            "group": "import-export",
            "extra": "mean: 6.6163 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 92.13523507723524,
            "unit": "iter/sec",
            "range": "stddev: 0.0012539",
            "group": "node",
            "extra": "mean: 10.854 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 42.886292002024,
            "unit": "iter/sec",
            "range": "stddev: 0.0013557",
            "group": "node",
            "extra": "mean: 23.317 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 43.22946813817903,
            "unit": "iter/sec",
            "range": "stddev: 0.00057513",
            "group": "node",
            "extra": "mean: 23.132 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 50.85246139727081,
            "unit": "iter/sec",
            "range": "stddev: 0.0013712",
            "group": "node",
            "extra": "mean: 19.665 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 27.21355200012586,
            "unit": "iter/sec",
            "range": "stddev: 0.0044962",
            "group": "node",
            "extra": "mean: 36.746 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 26.89219964078143,
            "unit": "iter/sec",
            "range": "stddev: 0.0022700",
            "group": "node",
            "extra": "mean: 37.186 msec\nrounds: 100"
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
          "pythonVersion": "3.8.5",
          "metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "0f46f3c38d57ccaaa0513e1f86621a5f23f5ed95",
          "message": "Merge branch 'develop' into benchmark-test-cjs",
          "timestamp": "2020-09-10T22:26:04+01:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/0f46f3c38d57ccaaa0513e1f86621a5f23f5ed95",
          "distinct": true,
          "tree_id": "9468ef71b969b3c838364960ab1c0947b6b85fb8"
        },
        "date": 1599774161496,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 2.4893343034179383,
            "unit": "iter/sec",
            "range": "stddev: 0.013196",
            "group": "engine",
            "extra": "mean: 401.71 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.5554156833417785,
            "unit": "iter/sec",
            "range": "stddev: 0.066317",
            "group": "engine",
            "extra": "mean: 1.8005 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.5983423624430386,
            "unit": "iter/sec",
            "range": "stddev: 0.078217",
            "group": "engine",
            "extra": "mean: 1.6713 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.1371362224228295,
            "unit": "iter/sec",
            "range": "stddev: 0.16123",
            "group": "engine",
            "extra": "mean: 7.2920 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.14187979815788385,
            "unit": "iter/sec",
            "range": "stddev: 0.14708",
            "group": "engine",
            "extra": "mean: 7.0482 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 1.463302234618181,
            "unit": "iter/sec",
            "range": "stddev: 0.057194",
            "group": "engine",
            "extra": "mean: 683.39 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.3265142138108297,
            "unit": "iter/sec",
            "range": "stddev: 0.092871",
            "group": "engine",
            "extra": "mean: 3.0627 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.359138820222826,
            "unit": "iter/sec",
            "range": "stddev: 0.087018",
            "group": "engine",
            "extra": "mean: 2.7844 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.1023910077825111,
            "unit": "iter/sec",
            "range": "stddev: 0.15427",
            "group": "engine",
            "extra": "mean: 9.7665 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.11304767263809552,
            "unit": "iter/sec",
            "range": "stddev: 0.16420",
            "group": "engine",
            "extra": "mean: 8.8458 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.665916673215402,
            "unit": "iter/sec",
            "range": "stddev: 0.058277",
            "group": "import-export",
            "extra": "mean: 375.11 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.321089469168484,
            "unit": "iter/sec",
            "range": "stddev: 0.056576",
            "group": "import-export",
            "extra": "mean: 430.83 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 0.13714576737917566,
            "unit": "iter/sec",
            "range": "stddev: 0.092181",
            "group": "import-export",
            "extra": "mean: 7.2915 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 0.14130182311435438,
            "unit": "iter/sec",
            "range": "stddev: 0.068946",
            "group": "import-export",
            "extra": "mean: 7.0770 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 82.11038401093548,
            "unit": "iter/sec",
            "range": "stddev: 0.00053603",
            "group": "node",
            "extra": "mean: 12.179 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 38.485081162268465,
            "unit": "iter/sec",
            "range": "stddev: 0.0017150",
            "group": "node",
            "extra": "mean: 25.984 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 36.93515623748952,
            "unit": "iter/sec",
            "range": "stddev: 0.0022545",
            "group": "node",
            "extra": "mean: 27.074 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 45.785721905783745,
            "unit": "iter/sec",
            "range": "stddev: 0.00095856",
            "group": "node",
            "extra": "mean: 21.841 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 23.32871415616602,
            "unit": "iter/sec",
            "range": "stddev: 0.019066",
            "group": "node",
            "extra": "mean: 42.866 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 24.25726727896464,
            "unit": "iter/sec",
            "range": "stddev: 0.0047857",
            "group": "node",
            "extra": "mean: 41.225 msec\nrounds: 100"
          }
        ]
      },
      {
        "cpu": {
          "speed": "2.40",
          "cores": 2,
          "physicalCores": 2,
          "processors": 1
        },
        "extra": {
          "pythonVersion": "3.8.5",
          "metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "4157b5d541a31001f7525b6063cdf8f8ceef7a7c",
          "message": "update [skip ci]",
          "timestamp": "2020-09-10T22:56:39+01:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/4157b5d541a31001f7525b6063cdf8f8ceef7a7c",
          "distinct": true,
          "tree_id": "03712bbb07262b60ed8f2e90dad5d3c90608666e"
        },
        "date": 1599775941437,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 2.6746400217708186,
            "unit": "iter/sec",
            "range": "stddev: 0.014088",
            "group": "engine",
            "extra": "mean: 373.88 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.5854076823453259,
            "unit": "iter/sec",
            "range": "stddev: 0.067804",
            "group": "engine",
            "extra": "mean: 1.7082 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.6292335824899747,
            "unit": "iter/sec",
            "range": "stddev: 0.075467",
            "group": "engine",
            "extra": "mean: 1.5892 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.14526043686543827,
            "unit": "iter/sec",
            "range": "stddev: 0.17398",
            "group": "engine",
            "extra": "mean: 6.8842 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.15175328404688437,
            "unit": "iter/sec",
            "range": "stddev: 0.14826",
            "group": "engine",
            "extra": "mean: 6.5896 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 1.5245586211764406,
            "unit": "iter/sec",
            "range": "stddev: 0.061193",
            "group": "engine",
            "extra": "mean: 655.93 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.3548650514292389,
            "unit": "iter/sec",
            "range": "stddev: 0.067230",
            "group": "engine",
            "extra": "mean: 2.8180 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.38363144994817855,
            "unit": "iter/sec",
            "range": "stddev: 0.079910",
            "group": "engine",
            "extra": "mean: 2.6067 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.10940122196881005,
            "unit": "iter/sec",
            "range": "stddev: 0.18165",
            "group": "engine",
            "extra": "mean: 9.1407 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.12227361174598396,
            "unit": "iter/sec",
            "range": "stddev: 0.15327",
            "group": "engine",
            "extra": "mean: 8.1784 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.5646427145743407,
            "unit": "iter/sec",
            "range": "stddev: 0.013689",
            "group": "import-export",
            "extra": "mean: 389.92 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.2337762511792802,
            "unit": "iter/sec",
            "range": "stddev: 0.048692",
            "group": "import-export",
            "extra": "mean: 447.67 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 0.13628540676689305,
            "unit": "iter/sec",
            "range": "stddev: 0.059875",
            "group": "import-export",
            "extra": "mean: 7.3375 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 0.14291993810417905,
            "unit": "iter/sec",
            "range": "stddev: 0.088909",
            "group": "import-export",
            "extra": "mean: 6.9969 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 94.64073642981887,
            "unit": "iter/sec",
            "range": "stddev: 0.0018037",
            "group": "node",
            "extra": "mean: 10.566 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 43.32838953375864,
            "unit": "iter/sec",
            "range": "stddev: 0.0018031",
            "group": "node",
            "extra": "mean: 23.080 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 43.65527204593333,
            "unit": "iter/sec",
            "range": "stddev: 0.0013809",
            "group": "node",
            "extra": "mean: 22.907 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 51.13576209385785,
            "unit": "iter/sec",
            "range": "stddev: 0.0012881",
            "group": "node",
            "extra": "mean: 19.556 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 25.36596250944434,
            "unit": "iter/sec",
            "range": "stddev: 0.018845",
            "group": "node",
            "extra": "mean: 39.423 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 26.575503674648132,
            "unit": "iter/sec",
            "range": "stddev: 0.0024391",
            "group": "node",
            "extra": "mean: 37.629 msec\nrounds: 100"
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
          "pythonVersion": "3.8.5",
          "metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "9cadcb33cad0e04103fcce3260ec6e3715c30482",
          "message": "update [skip ci]",
          "timestamp": "2020-09-10T23:23:29+01:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/9cadcb33cad0e04103fcce3260ec6e3715c30482",
          "distinct": true,
          "tree_id": "861b48080809a6669428d5d0974bd25e84439b24"
        },
        "date": 1599777507013,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 2.789687436992142,
            "unit": "iter/sec",
            "range": "stddev: 0.012034",
            "group": "engine",
            "extra": "mean: 358.46 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.6162820814562815,
            "unit": "iter/sec",
            "range": "stddev: 0.039128",
            "group": "engine",
            "extra": "mean: 1.6226 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.666735683233083,
            "unit": "iter/sec",
            "range": "stddev: 0.053123",
            "group": "engine",
            "extra": "mean: 1.4998 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.1489157937985533,
            "unit": "iter/sec",
            "range": "stddev: 0.15487",
            "group": "engine",
            "extra": "mean: 6.7152 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.1567057818663946,
            "unit": "iter/sec",
            "range": "stddev: 0.16893",
            "group": "engine",
            "extra": "mean: 6.3814 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 1.6286265067375874,
            "unit": "iter/sec",
            "range": "stddev: 0.053953",
            "group": "engine",
            "extra": "mean: 614.01 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.3757762923006151,
            "unit": "iter/sec",
            "range": "stddev: 0.065097",
            "group": "engine",
            "extra": "mean: 2.6612 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.4150828462918952,
            "unit": "iter/sec",
            "range": "stddev: 0.070086",
            "group": "engine",
            "extra": "mean: 2.4092 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.11398203441993464,
            "unit": "iter/sec",
            "range": "stddev: 0.11823",
            "group": "engine",
            "extra": "mean: 8.7733 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.12666687096259593,
            "unit": "iter/sec",
            "range": "stddev: 0.11877",
            "group": "engine",
            "extra": "mean: 7.8947 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.8029792009150083,
            "unit": "iter/sec",
            "range": "stddev: 0.050537",
            "group": "import-export",
            "extra": "mean: 356.76 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.443830344544901,
            "unit": "iter/sec",
            "range": "stddev: 0.047955",
            "group": "import-export",
            "extra": "mean: 409.19 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 0.14876402995942106,
            "unit": "iter/sec",
            "range": "stddev: 0.11539",
            "group": "import-export",
            "extra": "mean: 6.7221 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 0.14863030268850821,
            "unit": "iter/sec",
            "range": "stddev: 0.12886",
            "group": "import-export",
            "extra": "mean: 6.7281 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 99.18750869643942,
            "unit": "iter/sec",
            "range": "stddev: 0.00050658",
            "group": "node",
            "extra": "mean: 10.082 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 45.3768353757577,
            "unit": "iter/sec",
            "range": "stddev: 0.0012165",
            "group": "node",
            "extra": "mean: 22.038 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 44.8871328597817,
            "unit": "iter/sec",
            "range": "stddev: 0.0011958",
            "group": "node",
            "extra": "mean: 22.278 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 53.639256925192086,
            "unit": "iter/sec",
            "range": "stddev: 0.0012009",
            "group": "node",
            "extra": "mean: 18.643 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 26.683506848425143,
            "unit": "iter/sec",
            "range": "stddev: 0.016924",
            "group": "node",
            "extra": "mean: 37.476 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 28.411046743294712,
            "unit": "iter/sec",
            "range": "stddev: 0.0018344",
            "group": "node",
            "extra": "mean: 35.198 msec\nrounds: 100"
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
          "pythonVersion": "3.8.5",
          "metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "bee0be5d391cd20c841fdbd6133eab755c8733e8",
          "message": "use logarithmic y-axes",
          "timestamp": "2020-09-11T14:37:54+01:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/bee0be5d391cd20c841fdbd6133eab755c8733e8",
          "distinct": true,
          "tree_id": "29f5d8c65fc9aed4a37c3b9607fda9ee078fa26b"
        },
        "date": 1599832422300,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 2.636227046466372,
            "unit": "iter/sec",
            "range": "stddev: 0.0081378",
            "group": "engine",
            "extra": "mean: 379.33 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.5773694856521582,
            "unit": "iter/sec",
            "range": "stddev: 0.053065",
            "group": "engine",
            "extra": "mean: 1.7320 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.6267451540191317,
            "unit": "iter/sec",
            "range": "stddev: 0.052414",
            "group": "engine",
            "extra": "mean: 1.5955 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.14040081887564,
            "unit": "iter/sec",
            "range": "stddev: 0.15811",
            "group": "engine",
            "extra": "mean: 7.1225 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.14635646910924158,
            "unit": "iter/sec",
            "range": "stddev: 0.18741",
            "group": "engine",
            "extra": "mean: 6.8326 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 1.4746969206981029,
            "unit": "iter/sec",
            "range": "stddev: 0.064466",
            "group": "engine",
            "extra": "mean: 678.11 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.34354078680852584,
            "unit": "iter/sec",
            "range": "stddev: 0.048733",
            "group": "engine",
            "extra": "mean: 2.9109 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.37960958106875786,
            "unit": "iter/sec",
            "range": "stddev: 0.088538",
            "group": "engine",
            "extra": "mean: 2.6343 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.10734907277707818,
            "unit": "iter/sec",
            "range": "stddev: 0.14349",
            "group": "engine",
            "extra": "mean: 9.3154 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.11744176545146447,
            "unit": "iter/sec",
            "range": "stddev: 0.11192",
            "group": "engine",
            "extra": "mean: 8.5149 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.8458960588685387,
            "unit": "iter/sec",
            "range": "stddev: 0.0021110",
            "group": "import-export",
            "extra": "mean: 351.38 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.4375769996295964,
            "unit": "iter/sec",
            "range": "stddev: 0.054422",
            "group": "import-export",
            "extra": "mean: 410.24 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 0.14106910844294332,
            "unit": "iter/sec",
            "range": "stddev: 0.059946",
            "group": "import-export",
            "extra": "mean: 7.0887 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 0.14358862296203082,
            "unit": "iter/sec",
            "range": "stddev: 0.11365",
            "group": "import-export",
            "extra": "mean: 6.9643 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 86.29651146168635,
            "unit": "iter/sec",
            "range": "stddev: 0.00041013",
            "group": "node",
            "extra": "mean: 11.588 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 41.370806395811655,
            "unit": "iter/sec",
            "range": "stddev: 0.00083950",
            "group": "node",
            "extra": "mean: 24.172 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 40.63624079312036,
            "unit": "iter/sec",
            "range": "stddev: 0.00079586",
            "group": "node",
            "extra": "mean: 24.609 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 48.960077117358004,
            "unit": "iter/sec",
            "range": "stddev: 0.00099204",
            "group": "node",
            "extra": "mean: 20.425 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 25.473805295569477,
            "unit": "iter/sec",
            "range": "stddev: 0.0028537",
            "group": "node",
            "extra": "mean: 39.256 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 26.11792840581729,
            "unit": "iter/sec",
            "range": "stddev: 0.0016562",
            "group": "node",
            "extra": "mean: 38.288 msec\nrounds: 100"
          }
        ]
      },
      {
        "cpu": {
          "speed": "2.30",
          "cores": 2,
          "physicalCores": 2,
          "processors": 1
        },
        "extra": {
          "pythonVersion": "3.8.5",
          "metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "b002a9a9a898a05338ff522b46686657fb468f66",
          "message": "CI: add `pytest` benchmark workflows (#4362)\n\nThe basic steps of the workflow are:\r\n\r\n 1. Run `pytest` to generate JSON data.\r\n\r\nBy default, these tests are switched off (see `pytest.ini`) but to run\r\nthem locally, simply use `pytest tests/benchmark --benchmark-only`. This\r\nruns each test, marked as a benchmark, n-times and records the timing\r\nstatistics (see pytest-benchmark).\r\n\r\nWhen run also with `--benchmark-json benchmark.json`, a JSON file will\r\nalso be created, with all the details about each test.\r\n\r\n 2. Extract information from the above JSON, and also data about the\r\n    system (number of CPUs, etc) and created a \"simplified\" JSON object.\r\n\r\n 3. Read the JSON object from the specified `gh-pages` folder (data.js),\r\n    which contains a list of all these JSON objects.\r\n\r\nThese are split OS and backend.\r\n\r\n 4. If available, compare the new JSON section against the last one to\r\n    be added `data.js`, and comment in the PR and/or fail the workflow\r\n    if the timings have sufficiently degraded, depending on GH action\r\n    configuration.\r\n\r\n 5. If configured, add the new data to `data.js`, update the other\r\n    website assets (HTML/CSS/JS) and commit the updates to `gh-pages`.\r\n\r\nSince at ~7/8 minutes, these tests are slower than standard unit tests,\r\neven with the current fairly conservative tests/# of repetitions, they\r\nare not run by default on each commit. The current solution for this is\r\nto have two workflow jobs:\r\n\r\n  * One runs on every commit to develop, unless it is just updating\r\n    documentation, and will actually update the `gh-pages` data.\r\n  * The second is triggered by a commit to a branch with an open PR to\r\n    `develop`, but only if it includes `[run bench]` in the title of the\r\n    commit message. This will report back the timing data but not update\r\n    `gh-pages`. The idea is that this is run on the final commit of a PR\r\n    that may affect performance.\r\n\r\nOn to the actual tests. They are split into three categories:\r\n\r\n 1. Basic node storage/deletion, i.e. interactions with the ORM\r\n\r\n 2. Runs of workchains with internal (looped) calls to workchains and\r\n    calcjobs. These are duplicated using both a local runner and a\r\n    daemon runner. The daemon runner code is a bit tricky and may break\r\n    once we finalize the move to `asyncio`.\r\n\r\n 3. Expoting/importing archives.",
          "timestamp": "2020-09-16T12:08:59+02:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/b002a9a9a898a05338ff522b46686657fb468f66",
          "distinct": true,
          "tree_id": "8e03787cb2e4a4c359b79b5f53220a496897f0ff"
        },
        "date": 1600251731377,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.208166384966415,
            "unit": "iter/sec",
            "range": "stddev: 0.015365",
            "group": "engine",
            "extra": "mean: 311.70 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.695855839323653,
            "unit": "iter/sec",
            "range": "stddev: 0.043988",
            "group": "engine",
            "extra": "mean: 1.4371 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.7659952274858857,
            "unit": "iter/sec",
            "range": "stddev: 0.057427",
            "group": "engine",
            "extra": "mean: 1.3055 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.17551715654788608,
            "unit": "iter/sec",
            "range": "stddev: 0.12618",
            "group": "engine",
            "extra": "mean: 5.6974 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.18568784311180533,
            "unit": "iter/sec",
            "range": "stddev: 0.14858",
            "group": "engine",
            "extra": "mean: 5.3854 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 1.8403548097774196,
            "unit": "iter/sec",
            "range": "stddev: 0.038919",
            "group": "engine",
            "extra": "mean: 543.37 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.4477685885939377,
            "unit": "iter/sec",
            "range": "stddev: 0.057213",
            "group": "engine",
            "extra": "mean: 2.2333 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.494439535872049,
            "unit": "iter/sec",
            "range": "stddev: 0.064450",
            "group": "engine",
            "extra": "mean: 2.0225 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.13694166034141725,
            "unit": "iter/sec",
            "range": "stddev: 0.17220",
            "group": "engine",
            "extra": "mean: 7.3024 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.15070354514221548,
            "unit": "iter/sec",
            "range": "stddev: 0.14456",
            "group": "engine",
            "extra": "mean: 6.6355 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 3.151688901322415,
            "unit": "iter/sec",
            "range": "stddev: 0.040983",
            "group": "import-export",
            "extra": "mean: 317.29 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.9424974868050664,
            "unit": "iter/sec",
            "range": "stddev: 0.011047",
            "group": "import-export",
            "extra": "mean: 339.85 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 0.16488234310467934,
            "unit": "iter/sec",
            "range": "stddev: 0.29442",
            "group": "import-export",
            "extra": "mean: 6.0649 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 0.1659896080097009,
            "unit": "iter/sec",
            "range": "stddev: 0.090055",
            "group": "import-export",
            "extra": "mean: 6.0245 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 117.05195114287119,
            "unit": "iter/sec",
            "range": "stddev: 0.00075793",
            "group": "node",
            "extra": "mean: 8.5432 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 52.67713957175596,
            "unit": "iter/sec",
            "range": "stddev: 0.0014493",
            "group": "node",
            "extra": "mean: 18.984 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 51.8004084326585,
            "unit": "iter/sec",
            "range": "stddev: 0.0014114",
            "group": "node",
            "extra": "mean: 19.305 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 63.42420096621498,
            "unit": "iter/sec",
            "range": "stddev: 0.0013569",
            "group": "node",
            "extra": "mean: 15.767 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 31.93940201135384,
            "unit": "iter/sec",
            "range": "stddev: 0.013097",
            "group": "node",
            "extra": "mean: 31.309 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 32.96433579972487,
            "unit": "iter/sec",
            "range": "stddev: 0.0023522",
            "group": "node",
            "extra": "mean: 30.336 msec\nrounds: 100"
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
          "pythonVersion": "3.8.5",
          "metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "ff7b9e630967a4aece8f7dd75c052366920cd94e",
          "message": "CI: skip the code tests if only docs have been touched (#4377)\n\nThis requires splitting the `pre-commit` and `tests` steps in separate workflows.",
          "timestamp": "2020-09-17T16:29:39+02:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/ff7b9e630967a4aece8f7dd75c052366920cd94e",
          "distinct": true,
          "tree_id": "b8041b87e944622fd71abeba4dd0bea3ad0a62e8"
        },
        "date": 1600353821863,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.1646098620844207,
            "unit": "iter/sec",
            "range": "stddev: 0.0077790",
            "group": "engine",
            "extra": "mean: 315.99 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.6734505703284605,
            "unit": "iter/sec",
            "range": "stddev: 0.067709",
            "group": "engine",
            "extra": "mean: 1.4849 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.7353955210650946,
            "unit": "iter/sec",
            "range": "stddev: 0.055673",
            "group": "engine",
            "extra": "mean: 1.3598 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.1634149439192963,
            "unit": "iter/sec",
            "range": "stddev: 0.10570",
            "group": "engine",
            "extra": "mean: 6.1194 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.170777429587037,
            "unit": "iter/sec",
            "range": "stddev: 0.12526",
            "group": "engine",
            "extra": "mean: 5.8556 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 1.7730707845435671,
            "unit": "iter/sec",
            "range": "stddev: 0.043044",
            "group": "engine",
            "extra": "mean: 563.99 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.4114955582346236,
            "unit": "iter/sec",
            "range": "stddev: 0.062536",
            "group": "engine",
            "extra": "mean: 2.4302 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.4555048316787933,
            "unit": "iter/sec",
            "range": "stddev: 0.068851",
            "group": "engine",
            "extra": "mean: 2.1954 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.12481963832808131,
            "unit": "iter/sec",
            "range": "stddev: 0.17221",
            "group": "engine",
            "extra": "mean: 8.0116 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.1402395131333822,
            "unit": "iter/sec",
            "range": "stddev: 0.13791",
            "group": "engine",
            "extra": "mean: 7.1307 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 3.1056348390325006,
            "unit": "iter/sec",
            "range": "stddev: 0.039223",
            "group": "import-export",
            "extra": "mean: 322.00 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.853504710653694,
            "unit": "iter/sec",
            "range": "stddev: 0.010464",
            "group": "import-export",
            "extra": "mean: 350.45 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 0.162933127934741,
            "unit": "iter/sec",
            "range": "stddev: 0.097152",
            "group": "import-export",
            "extra": "mean: 6.1375 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 0.1636741726968612,
            "unit": "iter/sec",
            "range": "stddev: 0.13339",
            "group": "import-export",
            "extra": "mean: 6.1097 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 101.01100368114903,
            "unit": "iter/sec",
            "range": "stddev: 0.00051369",
            "group": "node",
            "extra": "mean: 9.8999 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 47.056841406679986,
            "unit": "iter/sec",
            "range": "stddev: 0.0023545",
            "group": "node",
            "extra": "mean: 21.251 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 47.489824662763375,
            "unit": "iter/sec",
            "range": "stddev: 0.0010519",
            "group": "node",
            "extra": "mean: 21.057 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 55.44144514155707,
            "unit": "iter/sec",
            "range": "stddev: 0.00087677",
            "group": "node",
            "extra": "mean: 18.037 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 27.82960229508994,
            "unit": "iter/sec",
            "range": "stddev: 0.016740",
            "group": "node",
            "extra": "mean: 35.933 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 29.736545975353657,
            "unit": "iter/sec",
            "range": "stddev: 0.0017830",
            "group": "node",
            "extra": "mean: 33.629 msec\nrounds: 100"
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
          "pythonVersion": "3.8.5",
          "metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "9dfad2efbe9603957a54d0123a3cec2ee48b54bd",
          "message": "`CalcJob`: allow nested target paths for `local_copy_list` (#4373)\n\nIf a `CalcJob` would specify a `local_copy_list` containing an entry\r\nwhere the target remote path contains nested subdirectories, the\r\n`upload_calculation` would except unless all subdirectories would\r\nalready exist. To solve this, one could have added a transport call that\r\nwould create the directories if the target path is nested. However, this\r\nwould risk being very inefficient if there are many local copy list\r\ninstructions with relative path, where each would incurr a command over\r\nthe transport.\r\n\r\nInstead, we change the design and simply apply the local copy list\r\ninstructions to the sandbox folder on the local file system. This also\r\nat the same time allows us to get rid of the inefficient workaround of\r\nwriting the file to a temporary file, because the transport interface\r\ndoesn't accept filelike objects and the file repository does not expose\r\nfilepaths on the local file system.\r\n\r\nThe only additional thing to take care of is to make sure the files from\r\nthe local copy list do not end up in the repository of the node, which\r\nwas the whole point of the `local_copy_list`'s existence in the first\r\nplace. But this is solved by simply adding each file, that is added to\r\nthe sandbox, also to the `provenance_exclude_list`.",
          "timestamp": "2020-09-17T21:24:38+02:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/9dfad2efbe9603957a54d0123a3cec2ee48b54bd",
          "distinct": true,
          "tree_id": "34c4cb969fd8157bfee60e0c77a0fb2e9eceeb11"
        },
        "date": 1600371531127,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.0251499486285054,
            "unit": "iter/sec",
            "range": "stddev: 0.011695",
            "group": "engine",
            "extra": "mean: 330.56 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.6663742375728977,
            "unit": "iter/sec",
            "range": "stddev: 0.049606",
            "group": "engine",
            "extra": "mean: 1.5007 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.7318433719681752,
            "unit": "iter/sec",
            "range": "stddev: 0.069338",
            "group": "engine",
            "extra": "mean: 1.3664 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.16717844468968512,
            "unit": "iter/sec",
            "range": "stddev: 0.23610",
            "group": "engine",
            "extra": "mean: 5.9816 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.17731973129550552,
            "unit": "iter/sec",
            "range": "stddev: 0.21800",
            "group": "engine",
            "extra": "mean: 5.6395 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 1.8310311146507445,
            "unit": "iter/sec",
            "range": "stddev: 0.063009",
            "group": "engine",
            "extra": "mean: 546.14 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.416064529619422,
            "unit": "iter/sec",
            "range": "stddev: 0.090446",
            "group": "engine",
            "extra": "mean: 2.4035 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.4499792029601938,
            "unit": "iter/sec",
            "range": "stddev: 0.12852",
            "group": "engine",
            "extra": "mean: 2.2223 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.12457169387741693,
            "unit": "iter/sec",
            "range": "stddev: 0.27774",
            "group": "engine",
            "extra": "mean: 8.0275 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.11544118821358862,
            "unit": "iter/sec",
            "range": "stddev: 0.36507",
            "group": "engine",
            "extra": "mean: 8.6624 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.723736272666573,
            "unit": "iter/sec",
            "range": "stddev: 0.046314",
            "group": "import-export",
            "extra": "mean: 367.14 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.488991351997488,
            "unit": "iter/sec",
            "range": "stddev: 0.046353",
            "group": "import-export",
            "extra": "mean: 401.77 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 0.14178807194194346,
            "unit": "iter/sec",
            "range": "stddev: 0.14555",
            "group": "import-export",
            "extra": "mean: 7.0528 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 0.1675199437416369,
            "unit": "iter/sec",
            "range": "stddev: 0.29238",
            "group": "import-export",
            "extra": "mean: 5.9694 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 100.45400276958367,
            "unit": "iter/sec",
            "range": "stddev: 0.0013581",
            "group": "node",
            "extra": "mean: 9.9548 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 46.46221279363876,
            "unit": "iter/sec",
            "range": "stddev: 0.0015855",
            "group": "node",
            "extra": "mean: 21.523 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 47.44275157416958,
            "unit": "iter/sec",
            "range": "stddev: 0.00070455",
            "group": "node",
            "extra": "mean: 21.078 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 57.201441126459635,
            "unit": "iter/sec",
            "range": "stddev: 0.00085495",
            "group": "node",
            "extra": "mean: 17.482 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 27.957114857124484,
            "unit": "iter/sec",
            "range": "stddev: 0.017628",
            "group": "node",
            "extra": "mean: 35.769 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 29.10821654432727,
            "unit": "iter/sec",
            "range": "stddev: 0.0031130",
            "group": "node",
            "extra": "mean: 34.355 msec\nrounds: 100"
          }
        ]
      },
      {
        "cpu": {
          "speed": "2.30",
          "cores": 2,
          "physicalCores": 2,
          "processors": 1
        },
        "extra": {
          "pythonVersion": "3.8.5",
          "metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "c6bca066106c8ee92178923ea3a0b6ab0b3657e2",
          "message": "Update citations in `README.md` and documentation landing page (#4371)\n\nThe second AiiDA paper was published in Scientific Data on September 8,\r\n2020. The suggested citations are updated, where the original AiiDA\r\npaper is kept to be cited when people use AiiDA with version before v1.0\r\nor if they reference the original ADES model.",
          "timestamp": "2020-09-17T22:54:58+02:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/c6bca066106c8ee92178923ea3a0b6ab0b3657e2",
          "distinct": true,
          "tree_id": "addd54026c8c291ac762ce912658ed8020e88a10"
        },
        "date": 1600377045756,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 2.600734826390024,
            "unit": "iter/sec",
            "range": "stddev: 0.014063",
            "group": "engine",
            "extra": "mean: 384.51 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.574104869405862,
            "unit": "iter/sec",
            "range": "stddev: 0.066471",
            "group": "engine",
            "extra": "mean: 1.7418 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.5968238660195483,
            "unit": "iter/sec",
            "range": "stddev: 0.10218",
            "group": "engine",
            "extra": "mean: 1.6755 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.1404050894089827,
            "unit": "iter/sec",
            "range": "stddev: 0.21969",
            "group": "engine",
            "extra": "mean: 7.1222 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.14204301602803004,
            "unit": "iter/sec",
            "range": "stddev: 0.28379",
            "group": "engine",
            "extra": "mean: 7.0401 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 1.4257281413037193,
            "unit": "iter/sec",
            "range": "stddev: 0.044391",
            "group": "engine",
            "extra": "mean: 701.40 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.35588353977447257,
            "unit": "iter/sec",
            "range": "stddev: 0.17276",
            "group": "engine",
            "extra": "mean: 2.8099 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.3841792957224767,
            "unit": "iter/sec",
            "range": "stddev: 0.13204",
            "group": "engine",
            "extra": "mean: 2.6030 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.11050620597311425,
            "unit": "iter/sec",
            "range": "stddev: 0.18223",
            "group": "engine",
            "extra": "mean: 9.0493 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.12744720515954236,
            "unit": "iter/sec",
            "range": "stddev: 0.41925",
            "group": "engine",
            "extra": "mean: 7.8464 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.6282049431639476,
            "unit": "iter/sec",
            "range": "stddev: 0.052372",
            "group": "import-export",
            "extra": "mean: 380.49 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.4684751694371383,
            "unit": "iter/sec",
            "range": "stddev: 0.018775",
            "group": "import-export",
            "extra": "mean: 405.11 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 0.13900992407198115,
            "unit": "iter/sec",
            "range": "stddev: 0.17825",
            "group": "import-export",
            "extra": "mean: 7.1937 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 0.13679992884321612,
            "unit": "iter/sec",
            "range": "stddev: 0.28867",
            "group": "import-export",
            "extra": "mean: 7.3099 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 104.61210566648343,
            "unit": "iter/sec",
            "range": "stddev: 0.00091732",
            "group": "node",
            "extra": "mean: 9.5591 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 44.2870727720585,
            "unit": "iter/sec",
            "range": "stddev: 0.0024589",
            "group": "node",
            "extra": "mean: 22.580 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 46.00474461378254,
            "unit": "iter/sec",
            "range": "stddev: 0.0017426",
            "group": "node",
            "extra": "mean: 21.737 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 53.04608856571689,
            "unit": "iter/sec",
            "range": "stddev: 0.0017384",
            "group": "node",
            "extra": "mean: 18.852 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 27.18474338614957,
            "unit": "iter/sec",
            "range": "stddev: 0.0052071",
            "group": "node",
            "extra": "mean: 36.785 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 26.347590807780747,
            "unit": "iter/sec",
            "range": "stddev: 0.0029791",
            "group": "node",
            "extra": "mean: 37.954 msec\nrounds: 100"
          }
        ]
      }
    ]
  }
}