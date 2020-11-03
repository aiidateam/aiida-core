window.BENCHMARK_DATA = {
  "lastUpdate": 1604411505697,
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
          "id": "12be9ad0c5abae1cff3bc62f838432b5c5502aa3",
          "message": "Depedencies: remove upper limit and allow `numpy~=1.17` (#4378)\n\nThe limit was introduced in `f5d6cba2baf0e7ca69b742f7e76d8a8bbcca85ae`\r\nbecause of a broken pre-release. Now that a stable release is out, the\r\nrequirement is relax to allow newer versions as well. Note that we keep\r\nthe minimum requirement of `numpy==1.17` following AEP 003.\r\n\r\nOne change had to be applied in the code to make it compatible with newer\r\nversions of `numpy`. In the legacy kpoints implementation, the entries\r\nin `num_points` are of type `numpy.float64` for recent versions of\r\n`numpy`, but need to be integers so they can be used for indexing in\r\n`numpy.linspace()` calls.",
          "timestamp": "2020-09-19T11:16:21+02:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/12be9ad0c5abae1cff3bc62f838432b5c5502aa3",
          "distinct": true,
          "tree_id": "22e059003dee06efa0201a155395535159e1b1c4"
        },
        "date": 1600507859706,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 2.9164252302824334,
            "unit": "iter/sec",
            "range": "stddev: 0.0064841",
            "group": "engine",
            "extra": "mean: 342.89 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.6032704835475757,
            "unit": "iter/sec",
            "range": "stddev: 0.070169",
            "group": "engine",
            "extra": "mean: 1.6576 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.6696465312751425,
            "unit": "iter/sec",
            "range": "stddev: 0.063047",
            "group": "engine",
            "extra": "mean: 1.4933 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.15089780899385116,
            "unit": "iter/sec",
            "range": "stddev: 0.23816",
            "group": "engine",
            "extra": "mean: 6.6270 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.1554577452690727,
            "unit": "iter/sec",
            "range": "stddev: 0.12963",
            "group": "engine",
            "extra": "mean: 6.4326 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 1.6320470263409173,
            "unit": "iter/sec",
            "range": "stddev: 0.053119",
            "group": "engine",
            "extra": "mean: 612.73 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.37473445972833314,
            "unit": "iter/sec",
            "range": "stddev: 0.069784",
            "group": "engine",
            "extra": "mean: 2.6686 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.44292664875956284,
            "unit": "iter/sec",
            "range": "stddev: 0.074037",
            "group": "engine",
            "extra": "mean: 2.2577 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.1181738253693381,
            "unit": "iter/sec",
            "range": "stddev: 0.39902",
            "group": "engine",
            "extra": "mean: 8.4621 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.1279380277904391,
            "unit": "iter/sec",
            "range": "stddev: 0.22477",
            "group": "engine",
            "extra": "mean: 7.8163 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 3.146598693463886,
            "unit": "iter/sec",
            "range": "stddev: 0.0095342",
            "group": "import-export",
            "extra": "mean: 317.80 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.752140606305879,
            "unit": "iter/sec",
            "range": "stddev: 0.044924",
            "group": "import-export",
            "extra": "mean: 363.35 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 0.15539248842895342,
            "unit": "iter/sec",
            "range": "stddev: 0.23615",
            "group": "import-export",
            "extra": "mean: 6.4353 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 0.1579108043516371,
            "unit": "iter/sec",
            "range": "stddev: 0.15246",
            "group": "import-export",
            "extra": "mean: 6.3327 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 100.0879463777842,
            "unit": "iter/sec",
            "range": "stddev: 0.00068017",
            "group": "node",
            "extra": "mean: 9.9912 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 47.45745473708406,
            "unit": "iter/sec",
            "range": "stddev: 0.0010682",
            "group": "node",
            "extra": "mean: 21.072 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 45.65303499378265,
            "unit": "iter/sec",
            "range": "stddev: 0.0012654",
            "group": "node",
            "extra": "mean: 21.904 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 53.8157210683099,
            "unit": "iter/sec",
            "range": "stddev: 0.0012629",
            "group": "node",
            "extra": "mean: 18.582 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 28.21946476411565,
            "unit": "iter/sec",
            "range": "stddev: 0.0031750",
            "group": "node",
            "extra": "mean: 35.437 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 27.143586347938506,
            "unit": "iter/sec",
            "range": "stddev: 0.0022058",
            "group": "node",
            "extra": "mean: 36.841 msec\nrounds: 100"
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
          "id": "8dec3265835dd9f335aaa43cfe5537cb5409ccc3",
          "message": "ORM: move attributes/extras methods of frontend node to mixins\n\nMove all methods related to attributes and extras from the frontend\n`Node` class to separate mixin classes called `EntityAttributesMixin`\nand `EntityExtrasMixin`. This makes it easier to add these methods to\nother frontend entity classes and makes the code more maintainable.",
          "timestamp": "2020-09-22T11:12:38+02:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/8dec3265835dd9f335aaa43cfe5537cb5409ccc3",
          "distinct": true,
          "tree_id": "01ead6eb7a823398ea56eb35279fe29baed056bc"
        },
        "date": 1600767028545,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 2.2754223579534836,
            "unit": "iter/sec",
            "range": "stddev: 0.010942",
            "group": "engine",
            "extra": "mean: 439.48 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.5013313902348958,
            "unit": "iter/sec",
            "range": "stddev: 0.059617",
            "group": "engine",
            "extra": "mean: 1.9947 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.5420812921904857,
            "unit": "iter/sec",
            "range": "stddev: 0.068830",
            "group": "engine",
            "extra": "mean: 1.8447 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.1274630979970985,
            "unit": "iter/sec",
            "range": "stddev: 0.17096",
            "group": "engine",
            "extra": "mean: 7.8454 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.13251153919742578,
            "unit": "iter/sec",
            "range": "stddev: 0.15358",
            "group": "engine",
            "extra": "mean: 7.5465 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 1.327207619836067,
            "unit": "iter/sec",
            "range": "stddev: 0.054549",
            "group": "engine",
            "extra": "mean: 753.46 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.3029833013776615,
            "unit": "iter/sec",
            "range": "stddev: 0.068898",
            "group": "engine",
            "extra": "mean: 3.3005 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.3398983586323264,
            "unit": "iter/sec",
            "range": "stddev: 0.11028",
            "group": "engine",
            "extra": "mean: 2.9421 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.09596268399093096,
            "unit": "iter/sec",
            "range": "stddev: 0.19981",
            "group": "engine",
            "extra": "mean: 10.421 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.10628468660452768,
            "unit": "iter/sec",
            "range": "stddev: 0.25227",
            "group": "engine",
            "extra": "mean: 9.4087 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.399368518357561,
            "unit": "iter/sec",
            "range": "stddev: 0.0063495",
            "group": "import-export",
            "extra": "mean: 416.78 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.064720020000934,
            "unit": "iter/sec",
            "range": "stddev: 0.051538",
            "group": "import-export",
            "extra": "mean: 484.33 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 0.12108107009555902,
            "unit": "iter/sec",
            "range": "stddev: 0.18063",
            "group": "import-export",
            "extra": "mean: 8.2589 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 0.12587039009728085,
            "unit": "iter/sec",
            "range": "stddev: 0.10280",
            "group": "import-export",
            "extra": "mean: 7.9447 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 84.5436932544413,
            "unit": "iter/sec",
            "range": "stddev: 0.00088571",
            "group": "node",
            "extra": "mean: 11.828 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 36.09105807011269,
            "unit": "iter/sec",
            "range": "stddev: 0.0026745",
            "group": "node",
            "extra": "mean: 27.708 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 33.276040543466216,
            "unit": "iter/sec",
            "range": "stddev: 0.0013921",
            "group": "node",
            "extra": "mean: 30.052 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 42.32674552614294,
            "unit": "iter/sec",
            "range": "stddev: 0.0020651",
            "group": "node",
            "extra": "mean: 23.626 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 23.608634253217875,
            "unit": "iter/sec",
            "range": "stddev: 0.0023561",
            "group": "node",
            "extra": "mean: 42.357 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 22.252313575880653,
            "unit": "iter/sec",
            "range": "stddev: 0.017196",
            "group": "node",
            "extra": "mean: 44.939 msec\nrounds: 100"
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
          "id": "93bde426fd0f083d3b9750beaa926acb4827c098",
          "message": "`CalcJob`: improve logging in `parse_scheduler_output` (#4370)\n\nThe level of the log that is fired if no detailed job info is available\r\nis changed from `WARNING` to `INFO`. Since not all schedulers implement\r\nthe feature of retrieving this detailed job info, such as the often used\r\n`DirectScheduler`, using a warning is not very apt. If the information\r\nis missing, nothing is necessarily wrong, so `INFO` is better suited.\r\n\r\nOn the contrary, if the `Scheduler.parse_output` excepts, that is grave\r\nand so its level is changed from a warning to an error.\r\n\r\nFinally, a new condition is added where the scheduler does implement the\r\nmethod to retrieve the detailed job info, but the command fails. In this\r\ncase, the return value will be non-zero. This value is now checked\r\nexplicitly and if the case, a info log is fired and the detailed job\r\ninfo is set to `None`, which will cause the parsing to be skipped. This\r\ncase can for example arise when using the `SlurmScheduler` plugin, which\r\ndoes implement the detailed job info feature, however, not all SLURM\r\ninstallations have the job accounting feature enabled, which is required\r\nby the plugin.",
          "timestamp": "2020-09-22T17:46:41+02:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/93bde426fd0f083d3b9750beaa926acb4827c098",
          "distinct": true,
          "tree_id": "022ffb9297511577b5e0e96793fe5b2a8d625f3a"
        },
        "date": 1600790667732,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 2.116317597171819,
            "unit": "iter/sec",
            "range": "stddev: 0.053180",
            "group": "engine",
            "extra": "mean: 472.52 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.49645252264151823,
            "unit": "iter/sec",
            "range": "stddev: 0.034204",
            "group": "engine",
            "extra": "mean: 2.0143 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.530925025928328,
            "unit": "iter/sec",
            "range": "stddev: 0.060557",
            "group": "engine",
            "extra": "mean: 1.8835 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.12605239118098566,
            "unit": "iter/sec",
            "range": "stddev: 0.26006",
            "group": "engine",
            "extra": "mean: 7.9332 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.13088942306400264,
            "unit": "iter/sec",
            "range": "stddev: 0.24736",
            "group": "engine",
            "extra": "mean: 7.6400 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 1.2976725984099793,
            "unit": "iter/sec",
            "range": "stddev: 0.013877",
            "group": "engine",
            "extra": "mean: 770.61 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.2905186818893964,
            "unit": "iter/sec",
            "range": "stddev: 0.077707",
            "group": "engine",
            "extra": "mean: 3.4421 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.3249369588295225,
            "unit": "iter/sec",
            "range": "stddev: 0.10794",
            "group": "engine",
            "extra": "mean: 3.0775 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.09489939545365142,
            "unit": "iter/sec",
            "range": "stddev: 0.23619",
            "group": "engine",
            "extra": "mean: 10.537 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.10442004722144393,
            "unit": "iter/sec",
            "range": "stddev: 0.18477",
            "group": "engine",
            "extra": "mean: 9.5767 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.348659844505394,
            "unit": "iter/sec",
            "range": "stddev: 0.057357",
            "group": "import-export",
            "extra": "mean: 425.77 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.095211863451667,
            "unit": "iter/sec",
            "range": "stddev: 0.054768",
            "group": "import-export",
            "extra": "mean: 477.28 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 0.12624122256809203,
            "unit": "iter/sec",
            "range": "stddev: 0.13672",
            "group": "import-export",
            "extra": "mean: 7.9213 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 0.1254544121965835,
            "unit": "iter/sec",
            "range": "stddev: 0.049521",
            "group": "import-export",
            "extra": "mean: 7.9710 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 70.7744114299622,
            "unit": "iter/sec",
            "range": "stddev: 0.0011556",
            "group": "node",
            "extra": "mean: 14.129 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 33.24906256461898,
            "unit": "iter/sec",
            "range": "stddev: 0.0017370",
            "group": "node",
            "extra": "mean: 30.076 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 32.18583066621809,
            "unit": "iter/sec",
            "range": "stddev: 0.0025030",
            "group": "node",
            "extra": "mean: 31.070 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 41.04187530566633,
            "unit": "iter/sec",
            "range": "stddev: 0.0014417",
            "group": "node",
            "extra": "mean: 24.365 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 23.233649964549073,
            "unit": "iter/sec",
            "range": "stddev: 0.0019547",
            "group": "node",
            "extra": "mean: 43.041 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 22.806341473478607,
            "unit": "iter/sec",
            "range": "stddev: 0.0020993",
            "group": "node",
            "extra": "mean: 43.847 msec\nrounds: 100"
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
          "id": "aa3b009870a674b11e66e46c49b6246114773a32",
          "message": "`BaseRestartWorkChain`: do not run `process_handler` when `exit_codes=[]`. (#4380)\n\nWhen a `process_handler` explicitly gets passed an empty `exit_codes`\r\nlist, it would previously always run. This is now changed to not run the\r\nhandler instead.\r\n\r\nThe reason for this change is that it is more consistent with the\r\nsemantics of passing a list of exit codes, where it only triggers if the\r\nchild process has any of the listed exit codes.",
          "timestamp": "2020-09-23T08:59:19+02:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/aa3b009870a674b11e66e46c49b6246114773a32",
          "distinct": true,
          "tree_id": "cde9ac6e7706ddca3ce79243987469df56b25e4d"
        },
        "date": 1600845251937,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 2.797984982318038,
            "unit": "iter/sec",
            "range": "stddev: 0.0081872",
            "group": "engine",
            "extra": "mean: 357.40 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.6198762286575934,
            "unit": "iter/sec",
            "range": "stddev: 0.049187",
            "group": "engine",
            "extra": "mean: 1.6132 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.6725257766019268,
            "unit": "iter/sec",
            "range": "stddev: 0.051989",
            "group": "engine",
            "extra": "mean: 1.4869 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.1509066087577351,
            "unit": "iter/sec",
            "range": "stddev: 0.18800",
            "group": "engine",
            "extra": "mean: 6.6266 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.1573608407545232,
            "unit": "iter/sec",
            "range": "stddev: 0.15258",
            "group": "engine",
            "extra": "mean: 6.3548 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 1.6471358515855865,
            "unit": "iter/sec",
            "range": "stddev: 0.016462",
            "group": "engine",
            "extra": "mean: 607.11 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.37826613450319735,
            "unit": "iter/sec",
            "range": "stddev: 0.052634",
            "group": "engine",
            "extra": "mean: 2.6436 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.4219757518634751,
            "unit": "iter/sec",
            "range": "stddev: 0.060511",
            "group": "engine",
            "extra": "mean: 2.3698 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.11718270293288748,
            "unit": "iter/sec",
            "range": "stddev: 0.12336",
            "group": "engine",
            "extra": "mean: 8.5337 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.12985189149404128,
            "unit": "iter/sec",
            "range": "stddev: 0.11679",
            "group": "engine",
            "extra": "mean: 7.7011 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.839975522913684,
            "unit": "iter/sec",
            "range": "stddev: 0.046059",
            "group": "import-export",
            "extra": "mean: 352.12 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.54005357942043,
            "unit": "iter/sec",
            "range": "stddev: 0.046068",
            "group": "import-export",
            "extra": "mean: 393.69 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 0.15121535785209203,
            "unit": "iter/sec",
            "range": "stddev: 0.083688",
            "group": "import-export",
            "extra": "mean: 6.6131 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 0.1520557804514787,
            "unit": "iter/sec",
            "range": "stddev: 0.089226",
            "group": "import-export",
            "extra": "mean: 6.5765 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 97.15043162889572,
            "unit": "iter/sec",
            "range": "stddev: 0.00036251",
            "group": "node",
            "extra": "mean: 10.293 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 45.596486799809085,
            "unit": "iter/sec",
            "range": "stddev: 0.00053806",
            "group": "node",
            "extra": "mean: 21.932 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 44.56146556631643,
            "unit": "iter/sec",
            "range": "stddev: 0.0036830",
            "group": "node",
            "extra": "mean: 22.441 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 53.3706140593176,
            "unit": "iter/sec",
            "range": "stddev: 0.00060209",
            "group": "node",
            "extra": "mean: 18.737 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 28.427369901760887,
            "unit": "iter/sec",
            "range": "stddev: 0.0027691",
            "group": "node",
            "extra": "mean: 35.177 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 28.62485488387221,
            "unit": "iter/sec",
            "range": "stddev: 0.0012374",
            "group": "node",
            "extra": "mean: 34.935 msec\nrounds: 100"
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
          "id": "ac0d55995ef6620e61ba1bb25bc1df5d23ff1778",
          "message": "Prepare the code for the new repository implementation (#4344)\n\nIn `v2.0.0`, the new repository implementation will be shipped, that\r\ndespite our best efforts, requires some slight backwards-incompatible\r\nchanges to the interface. The envisioned changes are translated as\r\ndeprecation warnings:\r\n\r\n * `FileType`: `aiida.orm.utils.repository` ->`aiida.repository.common`\r\n * `File`: `aiida.orm.utils.repository` ->`aiida.repository.common`\r\n * `File`: changed from namedtuple to class\r\n * `File`: iteration is deprecated\r\n * `File`: `type` attribute -> `file_type`\r\n * `Node.put_object_from_tree`: `path` -> `filepath`\r\n * `Node.put_object_from_file`: `path` -> `filepath`\r\n * `Node.put_object_from_tree`: `key` -> `path`\r\n * `Node.put_object_from_file`: `key` -> `path`\r\n * `Node.put_object_from_filelike`: `key` -> `path`\r\n * `Node.get_object`: `key` -> `path`\r\n * `Node.get_object_content`: `key` -> `path`\r\n * `Node.open`: `key` -> `path`\r\n * `Node.list_objects`: `key` -> `path`\r\n * `Node.list_object_names`: `key` -> `path`\r\n * `SinglefileData.open`: `key` -> `path`\r\n * Deprecated use of `Node.open` without context manager\r\n * Deprecated any other mode than `r` and `rb` in the methods:\r\n    o `Node.open`\r\n    o `Node.get_object_content`\r\n * Deprecated `contents_only` in `put_object_from_tree`\r\n * Deprecated `force` argument in\r\n    o `Node.put_object_from_tree`\r\n    o `Node.put_object_from_file`\r\n    o `Node.put_object_from_filelike`\r\n    o `Node.delete_object`\r\n\r\nThe special case is the `Repository` class of the internal module\r\n`aiida.orm.utils.repository`. Even though it is not part of the public\r\nAPI, plugins may have been using it. To allow deprecation warnings to be\r\nprinted when the module or class is used, we move the content to a\r\nmirror module `aiida.orm.utils._repository`, that is then used\r\ninternally, and the original module has the deprecation warning. This\r\nway clients will see the warning if they use it, but use in `aiida-core`\r\nwill not trigger them. Since there won't be a replacement for this class\r\nin the new implementation, it can also not be replaced or forwarded.",
          "timestamp": "2020-09-23T11:33:51+02:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/ac0d55995ef6620e61ba1bb25bc1df5d23ff1778",
          "distinct": true,
          "tree_id": "51b4c19e8fbbe39ce6b68033fd9a518beb2868f5"
        },
        "date": 1600854522632,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 2.8493879506846103,
            "unit": "iter/sec",
            "range": "stddev: 0.0068212",
            "group": "engine",
            "extra": "mean: 350.95 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.6270440757046764,
            "unit": "iter/sec",
            "range": "stddev: 0.045563",
            "group": "engine",
            "extra": "mean: 1.5948 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.6841828055115153,
            "unit": "iter/sec",
            "range": "stddev: 0.054193",
            "group": "engine",
            "extra": "mean: 1.4616 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.151201838600096,
            "unit": "iter/sec",
            "range": "stddev: 0.17953",
            "group": "engine",
            "extra": "mean: 6.6137 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.15902789878180756,
            "unit": "iter/sec",
            "range": "stddev: 0.20995",
            "group": "engine",
            "extra": "mean: 6.2882 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 1.6426032879287802,
            "unit": "iter/sec",
            "range": "stddev: 0.013898",
            "group": "engine",
            "extra": "mean: 608.79 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.3697572667394055,
            "unit": "iter/sec",
            "range": "stddev: 0.062927",
            "group": "engine",
            "extra": "mean: 2.7045 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.41094550904236393,
            "unit": "iter/sec",
            "range": "stddev: 0.047156",
            "group": "engine",
            "extra": "mean: 2.4334 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.11703449476765618,
            "unit": "iter/sec",
            "range": "stddev: 0.18256",
            "group": "engine",
            "extra": "mean: 8.5445 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.13025067424563708,
            "unit": "iter/sec",
            "range": "stddev: 0.17285",
            "group": "engine",
            "extra": "mean: 7.6775 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.868693504689714,
            "unit": "iter/sec",
            "range": "stddev: 0.060036",
            "group": "import-export",
            "extra": "mean: 348.59 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.615203739042652,
            "unit": "iter/sec",
            "range": "stddev: 0.050302",
            "group": "import-export",
            "extra": "mean: 382.38 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 0.15178746914356123,
            "unit": "iter/sec",
            "range": "stddev: 0.10914",
            "group": "import-export",
            "extra": "mean: 6.5882 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 0.15029077084007628,
            "unit": "iter/sec",
            "range": "stddev: 0.075823",
            "group": "import-export",
            "extra": "mean: 6.6538 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 92.13301850853345,
            "unit": "iter/sec",
            "range": "stddev: 0.00085600",
            "group": "node",
            "extra": "mean: 10.854 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 42.354733895894086,
            "unit": "iter/sec",
            "range": "stddev: 0.0016752",
            "group": "node",
            "extra": "mean: 23.610 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 41.47670377813198,
            "unit": "iter/sec",
            "range": "stddev: 0.00092465",
            "group": "node",
            "extra": "mean: 24.110 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 49.581282179876354,
            "unit": "iter/sec",
            "range": "stddev: 0.0014000",
            "group": "node",
            "extra": "mean: 20.169 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 25.786601579449815,
            "unit": "iter/sec",
            "range": "stddev: 0.018605",
            "group": "node",
            "extra": "mean: 38.780 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 26.6413476179335,
            "unit": "iter/sec",
            "range": "stddev: 0.0021042",
            "group": "node",
            "extra": "mean: 37.536 msec\nrounds: 100"
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
          "id": "26f14ae0c352bfe7b7f3bd0282291831b71320ed",
          "message": "`Group`: add support for setting extras on groups (#4328)\n\nThe `DbGroup` database models get a new JSONB column `extras` which will\r\nfunction just like the extras of nodes. They will allow setting mutable\r\nextras as long as they are JSON-serializable.\r\n\r\nThe default is set to an empty dictionary that prevents the ORM from\r\nhaving to deal with null values. In addition, this keeps in line with\r\nthe current design of other database models. Since the default is one\r\ndefined on the ORM and not the database schema, we also explicitly mark\r\nthe column as non-nullable. Otherwise it would be possible to still\r\nstore rows in the database with null values.\r\n\r\nTo add the functionality of setting, getting and deleting the extras to\r\nthe backend end frontend `Group` ORM classes, the corresponding mixin\r\nclasses are added. The functionality for the `BackendGroup` was already\r\naccidentally added in a previous commit `65389f4958b9b111756450ea77e2`\r\nso only the frontend is touched here.",
          "timestamp": "2020-09-23T12:59:46+02:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/26f14ae0c352bfe7b7f3bd0282291831b71320ed",
          "distinct": true,
          "tree_id": "85a2405b0ee69ac87acfed101a8ec0bb72a6d3b8"
        },
        "date": 1600859809306,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 2.343018974052968,
            "unit": "iter/sec",
            "range": "stddev: 0.039866",
            "group": "engine",
            "extra": "mean: 426.80 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.5417852944803259,
            "unit": "iter/sec",
            "range": "stddev: 0.092899",
            "group": "engine",
            "extra": "mean: 1.8457 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.5825066476027093,
            "unit": "iter/sec",
            "range": "stddev: 0.084300",
            "group": "engine",
            "extra": "mean: 1.7167 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.133579856831014,
            "unit": "iter/sec",
            "range": "stddev: 0.22374",
            "group": "engine",
            "extra": "mean: 7.4862 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.13643076962361353,
            "unit": "iter/sec",
            "range": "stddev: 0.26370",
            "group": "engine",
            "extra": "mean: 7.3297 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 1.3407242838497087,
            "unit": "iter/sec",
            "range": "stddev: 0.085695",
            "group": "engine",
            "extra": "mean: 745.87 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.3167318837490225,
            "unit": "iter/sec",
            "range": "stddev: 0.082054",
            "group": "engine",
            "extra": "mean: 3.1572 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.36782929765830785,
            "unit": "iter/sec",
            "range": "stddev: 0.098023",
            "group": "engine",
            "extra": "mean: 2.7187 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.10629656037520342,
            "unit": "iter/sec",
            "range": "stddev: 0.31595",
            "group": "engine",
            "extra": "mean: 9.4076 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.10960029322650973,
            "unit": "iter/sec",
            "range": "stddev: 0.35493",
            "group": "engine",
            "extra": "mean: 9.1241 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.370228702561581,
            "unit": "iter/sec",
            "range": "stddev: 0.066279",
            "group": "import-export",
            "extra": "mean: 421.90 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.1543975650530824,
            "unit": "iter/sec",
            "range": "stddev: 0.058034",
            "group": "import-export",
            "extra": "mean: 464.17 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 0.1262750814632153,
            "unit": "iter/sec",
            "range": "stddev: 0.15666",
            "group": "import-export",
            "extra": "mean: 7.9192 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 0.12934745137630632,
            "unit": "iter/sec",
            "range": "stddev: 0.18930",
            "group": "import-export",
            "extra": "mean: 7.7311 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 80.17800787775766,
            "unit": "iter/sec",
            "range": "stddev: 0.0014222",
            "group": "node",
            "extra": "mean: 12.472 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 35.02904569587306,
            "unit": "iter/sec",
            "range": "stddev: 0.0040400",
            "group": "node",
            "extra": "mean: 28.548 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 34.59839787189071,
            "unit": "iter/sec",
            "range": "stddev: 0.0024344",
            "group": "node",
            "extra": "mean: 28.903 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 44.68680715632594,
            "unit": "iter/sec",
            "range": "stddev: 0.0019782",
            "group": "node",
            "extra": "mean: 22.378 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 22.44613918042197,
            "unit": "iter/sec",
            "range": "stddev: 0.020103",
            "group": "node",
            "extra": "mean: 44.551 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 23.28140556209555,
            "unit": "iter/sec",
            "range": "stddev: 0.0044629",
            "group": "node",
            "extra": "mean: 42.953 msec\nrounds: 100"
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
          "id": "f2f6e2f89580eb824c4175703718a07a2d4b0bee",
          "message": "`SshTransport` : refactor interface to simplify subclassing (#4363)\n\nThe `SshTransport` transport plugin is refactored slightly to make it\r\neasier for sublcasses to adapt its behavior. Specifically:\r\n\r\n * Add simple wrappers around SFTP calls (stat, lstat and symlink) such\r\n   that they can be overriden in subclasses, for example if SFTP is not\r\n   available and pure SSH needs to be used.\r\n * New method to initialize file transport separately. Also adds error\r\n   checking for SFTP initialization, with an explicit message if it\r\n   fails to launch, and a possible solution.\r\n * Add `_MAX_EXEC_COMMAND_LOG_SIZE` class attribute that can be used to\r\n   limit the length of the debug message containing the command that is\r\n   executed in `_exec_command_internal`, which can grow very large.",
          "timestamp": "2020-09-23T13:30:27+02:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/f2f6e2f89580eb824c4175703718a07a2d4b0bee",
          "distinct": true,
          "tree_id": "db0def820c8c26bed6a0d0758d5f32ae290709dd"
        },
        "date": 1600861653280,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 2.4079717092008006,
            "unit": "iter/sec",
            "range": "stddev: 0.060813",
            "group": "engine",
            "extra": "mean: 415.29 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.5064404149366438,
            "unit": "iter/sec",
            "range": "stddev: 0.080214",
            "group": "engine",
            "extra": "mean: 1.9746 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.5496681234966144,
            "unit": "iter/sec",
            "range": "stddev: 0.079480",
            "group": "engine",
            "extra": "mean: 1.8193 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.13270772344166112,
            "unit": "iter/sec",
            "range": "stddev: 0.14008",
            "group": "engine",
            "extra": "mean: 7.5354 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.14212933852195056,
            "unit": "iter/sec",
            "range": "stddev: 0.23731",
            "group": "engine",
            "extra": "mean: 7.0358 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 1.4379276699844326,
            "unit": "iter/sec",
            "range": "stddev: 0.087357",
            "group": "engine",
            "extra": "mean: 695.45 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.3203455404250237,
            "unit": "iter/sec",
            "range": "stddev: 0.21693",
            "group": "engine",
            "extra": "mean: 3.1216 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.34017120770280435,
            "unit": "iter/sec",
            "range": "stddev: 0.13726",
            "group": "engine",
            "extra": "mean: 2.9397 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.10181783513252618,
            "unit": "iter/sec",
            "range": "stddev: 0.23605",
            "group": "engine",
            "extra": "mean: 9.8215 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.11334721640462263,
            "unit": "iter/sec",
            "range": "stddev: 0.48223",
            "group": "engine",
            "extra": "mean: 8.8224 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.6117038058043764,
            "unit": "iter/sec",
            "range": "stddev: 0.0090029",
            "group": "import-export",
            "extra": "mean: 382.89 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.1738491957158224,
            "unit": "iter/sec",
            "range": "stddev: 0.054294",
            "group": "import-export",
            "extra": "mean: 460.01 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 0.13270678644868067,
            "unit": "iter/sec",
            "range": "stddev: 0.11496",
            "group": "import-export",
            "extra": "mean: 7.5354 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 0.1327671181238472,
            "unit": "iter/sec",
            "range": "stddev: 0.13765",
            "group": "import-export",
            "extra": "mean: 7.5320 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 85.84978630746916,
            "unit": "iter/sec",
            "range": "stddev: 0.0011357",
            "group": "node",
            "extra": "mean: 11.648 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 38.221896330081314,
            "unit": "iter/sec",
            "range": "stddev: 0.0028721",
            "group": "node",
            "extra": "mean: 26.163 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 36.726519254428624,
            "unit": "iter/sec",
            "range": "stddev: 0.0033661",
            "group": "node",
            "extra": "mean: 27.228 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 45.68987326513243,
            "unit": "iter/sec",
            "range": "stddev: 0.0023206",
            "group": "node",
            "extra": "mean: 21.887 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 22.50107339964856,
            "unit": "iter/sec",
            "range": "stddev: 0.021693",
            "group": "node",
            "extra": "mean: 44.442 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 23.450617782755504,
            "unit": "iter/sec",
            "range": "stddev: 0.0037638",
            "group": "node",
            "extra": "mean: 42.643 msec\nrounds: 100"
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
          "id": "0b155a518327b6e904e1424956bdb7d7103251fc",
          "message": "Remove duplicated migration for SqlAlchemy (#4390)\n\nThe `0edcdd5a30f0_add_extras_to_group.py` migration is a duplicate of\r\n`0edcdd5a30f0_dbgroup_extras.py` and was accidentally committed in\r\ncommit `26f14ae0c352bfe7b7f3bd0282291831b71320ed`. The migration is\r\nexactly the same, including the revision numbers, except the human\r\nreadable part was changed.",
          "timestamp": "2020-09-23T23:04:18+02:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/0b155a518327b6e904e1424956bdb7d7103251fc",
          "distinct": true,
          "tree_id": "372544ccca48d0d4cd8b60579682bbf526cea04c"
        },
        "date": 1600896099743,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 2.185983661760945,
            "unit": "iter/sec",
            "range": "stddev: 0.056954",
            "group": "engine",
            "extra": "mean: 457.46 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.5031129803983673,
            "unit": "iter/sec",
            "range": "stddev: 0.095615",
            "group": "engine",
            "extra": "mean: 1.9876 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.5446228973288003,
            "unit": "iter/sec",
            "range": "stddev: 0.090822",
            "group": "engine",
            "extra": "mean: 1.8361 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.12728613078741996,
            "unit": "iter/sec",
            "range": "stddev: 0.30603",
            "group": "engine",
            "extra": "mean: 7.8563 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.1336517237354941,
            "unit": "iter/sec",
            "range": "stddev: 0.17749",
            "group": "engine",
            "extra": "mean: 7.4821 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 1.3034391629435478,
            "unit": "iter/sec",
            "range": "stddev: 0.096227",
            "group": "engine",
            "extra": "mean: 767.20 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.300823372169539,
            "unit": "iter/sec",
            "range": "stddev: 0.15767",
            "group": "engine",
            "extra": "mean: 3.3242 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.3198355406264219,
            "unit": "iter/sec",
            "range": "stddev: 0.16025",
            "group": "engine",
            "extra": "mean: 3.1266 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.09094853969762799,
            "unit": "iter/sec",
            "range": "stddev: 0.14072",
            "group": "engine",
            "extra": "mean: 10.995 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.10496688648097292,
            "unit": "iter/sec",
            "range": "stddev: 0.38720",
            "group": "engine",
            "extra": "mean: 9.5268 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.521137462824367,
            "unit": "iter/sec",
            "range": "stddev: 0.011931",
            "group": "import-export",
            "extra": "mean: 396.65 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.1314225931200856,
            "unit": "iter/sec",
            "range": "stddev: 0.083515",
            "group": "import-export",
            "extra": "mean: 469.17 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 0.1351761491634576,
            "unit": "iter/sec",
            "range": "stddev: 0.18062",
            "group": "import-export",
            "extra": "mean: 7.3978 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 0.13605598300957036,
            "unit": "iter/sec",
            "range": "stddev: 0.19068",
            "group": "import-export",
            "extra": "mean: 7.3499 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 92.61819886598872,
            "unit": "iter/sec",
            "range": "stddev: 0.0013155",
            "group": "node",
            "extra": "mean: 10.797 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 40.63281249625243,
            "unit": "iter/sec",
            "range": "stddev: 0.0035736",
            "group": "node",
            "extra": "mean: 24.611 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 38.632122983831145,
            "unit": "iter/sec",
            "range": "stddev: 0.0042433",
            "group": "node",
            "extra": "mean: 25.885 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 48.77184441098502,
            "unit": "iter/sec",
            "range": "stddev: 0.0023839",
            "group": "node",
            "extra": "mean: 20.504 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 23.559477949166066,
            "unit": "iter/sec",
            "range": "stddev: 0.024751",
            "group": "node",
            "extra": "mean: 42.446 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 25.700991623032934,
            "unit": "iter/sec",
            "range": "stddev: 0.0025528",
            "group": "node",
            "extra": "mean: 38.909 msec\nrounds: 100"
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
          "id": "59ebaf478511c13fc3e2de55569004fb88ab1dc7",
          "message": "Merge pull request #4385 from aiidateam/release/1.4.0\n\nRelease `v1.4.0`",
          "timestamp": "2020-09-24T11:08:58+02:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/59ebaf478511c13fc3e2de55569004fb88ab1dc7",
          "distinct": false,
          "tree_id": "ca4353750bc03ffd3567c8273f8b3f0690c255c8"
        },
        "date": 1600944674053,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.4086437178885016,
            "unit": "iter/sec",
            "range": "stddev: 0.032853",
            "group": "engine",
            "extra": "mean: 293.37 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.7703761862928646,
            "unit": "iter/sec",
            "range": "stddev: 0.047776",
            "group": "engine",
            "extra": "mean: 1.2981 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.8358429680742541,
            "unit": "iter/sec",
            "range": "stddev: 0.057819",
            "group": "engine",
            "extra": "mean: 1.1964 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.1870478605837969,
            "unit": "iter/sec",
            "range": "stddev: 0.12591",
            "group": "engine",
            "extra": "mean: 5.3462 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.19648898522879715,
            "unit": "iter/sec",
            "range": "stddev: 0.10565",
            "group": "engine",
            "extra": "mean: 5.0893 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.0210974468065057,
            "unit": "iter/sec",
            "range": "stddev: 0.044487",
            "group": "engine",
            "extra": "mean: 494.78 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.4704711302254647,
            "unit": "iter/sec",
            "range": "stddev: 0.039831",
            "group": "engine",
            "extra": "mean: 2.1255 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.5260991263196986,
            "unit": "iter/sec",
            "range": "stddev: 0.069610",
            "group": "engine",
            "extra": "mean: 1.9008 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.14264939114908842,
            "unit": "iter/sec",
            "range": "stddev: 0.25872",
            "group": "engine",
            "extra": "mean: 7.0102 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.1605558955981623,
            "unit": "iter/sec",
            "range": "stddev: 0.12839",
            "group": "engine",
            "extra": "mean: 6.2284 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 3.716068492659833,
            "unit": "iter/sec",
            "range": "stddev: 0.0046675",
            "group": "import-export",
            "extra": "mean: 269.10 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 3.1930110565099095,
            "unit": "iter/sec",
            "range": "stddev: 0.045284",
            "group": "import-export",
            "extra": "mean: 313.18 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 0.18728682507310448,
            "unit": "iter/sec",
            "range": "stddev: 0.051215",
            "group": "import-export",
            "extra": "mean: 5.3394 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 0.18654984077862524,
            "unit": "iter/sec",
            "range": "stddev: 0.050824",
            "group": "import-export",
            "extra": "mean: 5.3605 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 114.88997924768927,
            "unit": "iter/sec",
            "range": "stddev: 0.00053477",
            "group": "node",
            "extra": "mean: 8.7040 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 52.149414055941406,
            "unit": "iter/sec",
            "range": "stddev: 0.0014346",
            "group": "node",
            "extra": "mean: 19.176 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 53.642463751503136,
            "unit": "iter/sec",
            "range": "stddev: 0.0011400",
            "group": "node",
            "extra": "mean: 18.642 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 62.796649606558525,
            "unit": "iter/sec",
            "range": "stddev: 0.0010293",
            "group": "node",
            "extra": "mean: 15.924 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 32.13136244860348,
            "unit": "iter/sec",
            "range": "stddev: 0.016591",
            "group": "node",
            "extra": "mean: 31.122 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 34.021705026519776,
            "unit": "iter/sec",
            "range": "stddev: 0.0019403",
            "group": "node",
            "extra": "mean: 29.393 msec\nrounds: 100"
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
          "id": "559abbaab690bc7f94c84ece63ad4810500592bf",
          "message": "Drop support for Python 3.5 (#4386)\n\nPython 3.5 is EOL as of September 13 2020. CI testing will now only be\r\ndone against Python 3.6 and 3.8.",
          "timestamp": "2020-09-24T14:51:59+02:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/559abbaab690bc7f94c84ece63ad4810500592bf",
          "distinct": true,
          "tree_id": "4978f4074832a728936394b0c29d7852548fb639"
        },
        "date": 1600952922036,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 2.419756116623578,
            "unit": "iter/sec",
            "range": "stddev: 0.049714",
            "group": "engine",
            "extra": "mean: 413.26 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.5451991060235716,
            "unit": "iter/sec",
            "range": "stddev: 0.055138",
            "group": "engine",
            "extra": "mean: 1.8342 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.5767282702357756,
            "unit": "iter/sec",
            "range": "stddev: 0.080406",
            "group": "engine",
            "extra": "mean: 1.7339 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.13700783502267092,
            "unit": "iter/sec",
            "range": "stddev: 0.16904",
            "group": "engine",
            "extra": "mean: 7.2989 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.14132124308161972,
            "unit": "iter/sec",
            "range": "stddev: 0.18863",
            "group": "engine",
            "extra": "mean: 7.0761 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 1.4190343208782932,
            "unit": "iter/sec",
            "range": "stddev: 0.055609",
            "group": "engine",
            "extra": "mean: 704.70 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.33184130763844927,
            "unit": "iter/sec",
            "range": "stddev: 0.096053",
            "group": "engine",
            "extra": "mean: 3.0135 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.36787051631822953,
            "unit": "iter/sec",
            "range": "stddev: 0.10201",
            "group": "engine",
            "extra": "mean: 2.7183 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.10396028242146288,
            "unit": "iter/sec",
            "range": "stddev: 0.25727",
            "group": "engine",
            "extra": "mean: 9.6191 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.11453553750761787,
            "unit": "iter/sec",
            "range": "stddev: 0.14182",
            "group": "engine",
            "extra": "mean: 8.7309 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.4297737777407495,
            "unit": "iter/sec",
            "range": "stddev: 0.013266",
            "group": "import-export",
            "extra": "mean: 411.56 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.04031872228862,
            "unit": "iter/sec",
            "range": "stddev: 0.062359",
            "group": "import-export",
            "extra": "mean: 490.12 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 0.12211535648909673,
            "unit": "iter/sec",
            "range": "stddev: 0.42524",
            "group": "import-export",
            "extra": "mean: 8.1890 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 0.13015313237332385,
            "unit": "iter/sec",
            "range": "stddev: 0.23317",
            "group": "import-export",
            "extra": "mean: 7.6833 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 71.71956053343031,
            "unit": "iter/sec",
            "range": "stddev: 0.0016693",
            "group": "node",
            "extra": "mean: 13.943 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 38.826461368239734,
            "unit": "iter/sec",
            "range": "stddev: 0.0040795",
            "group": "node",
            "extra": "mean: 25.756 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 39.23595872505469,
            "unit": "iter/sec",
            "range": "stddev: 0.0028266",
            "group": "node",
            "extra": "mean: 25.487 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 47.13028626205554,
            "unit": "iter/sec",
            "range": "stddev: 0.0033495",
            "group": "node",
            "extra": "mean: 21.218 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 25.307372226803132,
            "unit": "iter/sec",
            "range": "stddev: 0.0038589",
            "group": "node",
            "extra": "mean: 39.514 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 24.441344906600104,
            "unit": "iter/sec",
            "range": "stddev: 0.0038843",
            "group": "node",
            "extra": "mean: 40.914 msec\nrounds: 100"
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
          "id": "01845181740c2768ce3c31165a3f80e18d241a9f",
          "message": "`LinkManager`: fix inaccuracy in exception message for non-existent link  (#4388)\n\nThe link manager was always referring to an 'input link' while it should\r\ninstead refer on an 'input link label' or 'output link label' depending\r\non the value of the link direction, determined by the `self._incoming`\r\nattribute.",
          "timestamp": "2020-09-24T15:12:32+02:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/01845181740c2768ce3c31165a3f80e18d241a9f",
          "distinct": true,
          "tree_id": "c40d0d08cea7776aacbcd2ad9e998bd33e9532fc"
        },
        "date": 1600954086063,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 2.529441534655589,
            "unit": "iter/sec",
            "range": "stddev: 0.029594",
            "group": "engine",
            "extra": "mean: 395.34 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.5701563201197702,
            "unit": "iter/sec",
            "range": "stddev: 0.033380",
            "group": "engine",
            "extra": "mean: 1.7539 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.6270452069371927,
            "unit": "iter/sec",
            "range": "stddev: 0.049749",
            "group": "engine",
            "extra": "mean: 1.5948 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.14337229738583834,
            "unit": "iter/sec",
            "range": "stddev: 0.11869",
            "group": "engine",
            "extra": "mean: 6.9748 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.15020580529147642,
            "unit": "iter/sec",
            "range": "stddev: 0.18563",
            "group": "engine",
            "extra": "mean: 6.6575 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 1.5503887042853906,
            "unit": "iter/sec",
            "range": "stddev: 0.050112",
            "group": "engine",
            "extra": "mean: 645.00 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.358659809640334,
            "unit": "iter/sec",
            "range": "stddev: 0.061700",
            "group": "engine",
            "extra": "mean: 2.7882 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.39624989106268493,
            "unit": "iter/sec",
            "range": "stddev: 0.064848",
            "group": "engine",
            "extra": "mean: 2.5237 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.1113310524917529,
            "unit": "iter/sec",
            "range": "stddev: 0.12438",
            "group": "engine",
            "extra": "mean: 8.9822 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.1240247289056245,
            "unit": "iter/sec",
            "range": "stddev: 0.15535",
            "group": "engine",
            "extra": "mean: 8.0629 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.546429504867124,
            "unit": "iter/sec",
            "range": "stddev: 0.045288",
            "group": "import-export",
            "extra": "mean: 392.71 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.2536269515803244,
            "unit": "iter/sec",
            "range": "stddev: 0.043580",
            "group": "import-export",
            "extra": "mean: 443.73 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 0.1378052922697814,
            "unit": "iter/sec",
            "range": "stddev: 0.14086",
            "group": "import-export",
            "extra": "mean: 7.2566 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 0.14408668416411696,
            "unit": "iter/sec",
            "range": "stddev: 0.11890",
            "group": "import-export",
            "extra": "mean: 6.9403 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 100.32179207979435,
            "unit": "iter/sec",
            "range": "stddev: 0.00075388",
            "group": "node",
            "extra": "mean: 9.9679 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 43.94037672980567,
            "unit": "iter/sec",
            "range": "stddev: 0.0011576",
            "group": "node",
            "extra": "mean: 22.758 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 44.181602729114296,
            "unit": "iter/sec",
            "range": "stddev: 0.0012918",
            "group": "node",
            "extra": "mean: 22.634 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 52.15335660296505,
            "unit": "iter/sec",
            "range": "stddev: 0.0010098",
            "group": "node",
            "extra": "mean: 19.174 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 27.35270723270015,
            "unit": "iter/sec",
            "range": "stddev: 0.0024812",
            "group": "node",
            "extra": "mean: 36.559 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 27.3473903670992,
            "unit": "iter/sec",
            "range": "stddev: 0.0023282",
            "group": "node",
            "extra": "mean: 36.567 msec\nrounds: 100"
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
          "id": "5e1c6fd965bc8cdeea8bc0c37ee19a71de5986f3",
          "message": "Implement `next` and `iter` for the `Node.open` deprecation wrapper (#4399)\n\nThe return value of `Node.open` was wrapped in `WarnWhenNotEntered` in\r\n`aiida-core==1.4.0` in order to warn users that use the method without a\r\ncontext manager, which will start to raise in v2.0. Unfortunately, the\r\nraising came a little early as the wrapper does not implement the\r\n`__iter__` and `__next__` methods, which can be called by clients.\r\n\r\nAn example is `numpy.getfromtxt` which will notice the return value of\r\n`Node.open` is filelike and so will wrap it in `iter`. Without the\r\ncurrent fix, this raises a `TypeError`. The proper fix would be to\r\nforward all magic methods to the wrapped filelike object, but it is not\r\nclear how to do this.",
          "timestamp": "2020-09-25T15:56:53+02:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/5e1c6fd965bc8cdeea8bc0c37ee19a71de5986f3",
          "distinct": true,
          "tree_id": "0b57e939704231c31d3313b8a91d5065ed43c30f"
        },
        "date": 1601043224238,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 2.3962568535606104,
            "unit": "iter/sec",
            "range": "stddev: 0.039672",
            "group": "engine",
            "extra": "mean: 417.32 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.5260640328368698,
            "unit": "iter/sec",
            "range": "stddev: 0.14222",
            "group": "engine",
            "extra": "mean: 1.9009 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.562319503361094,
            "unit": "iter/sec",
            "range": "stddev: 0.099904",
            "group": "engine",
            "extra": "mean: 1.7783 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.13368943818574003,
            "unit": "iter/sec",
            "range": "stddev: 0.13263",
            "group": "engine",
            "extra": "mean: 7.4800 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.13960975791136418,
            "unit": "iter/sec",
            "range": "stddev: 0.38256",
            "group": "engine",
            "extra": "mean: 7.1628 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 1.375723228861953,
            "unit": "iter/sec",
            "range": "stddev: 0.059810",
            "group": "engine",
            "extra": "mean: 726.89 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.3154416086295351,
            "unit": "iter/sec",
            "range": "stddev: 0.10117",
            "group": "engine",
            "extra": "mean: 3.1702 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.36927209970033864,
            "unit": "iter/sec",
            "range": "stddev: 0.10229",
            "group": "engine",
            "extra": "mean: 2.7080 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.09732400894695685,
            "unit": "iter/sec",
            "range": "stddev: 0.27272",
            "group": "engine",
            "extra": "mean: 10.275 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.11315922499562606,
            "unit": "iter/sec",
            "range": "stddev: 0.39222",
            "group": "engine",
            "extra": "mean: 8.8371 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.2767286673422316,
            "unit": "iter/sec",
            "range": "stddev: 0.062607",
            "group": "import-export",
            "extra": "mean: 439.23 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.0663798728513,
            "unit": "iter/sec",
            "range": "stddev: 0.045134",
            "group": "import-export",
            "extra": "mean: 483.94 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 0.12486812625418073,
            "unit": "iter/sec",
            "range": "stddev: 0.32037",
            "group": "import-export",
            "extra": "mean: 8.0084 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 0.13212845731066986,
            "unit": "iter/sec",
            "range": "stddev: 0.29338",
            "group": "import-export",
            "extra": "mean: 7.5684 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 74.66620919174646,
            "unit": "iter/sec",
            "range": "stddev: 0.018082",
            "group": "node",
            "extra": "mean: 13.393 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 39.273966839107054,
            "unit": "iter/sec",
            "range": "stddev: 0.0032219",
            "group": "node",
            "extra": "mean: 25.462 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 38.83904427708181,
            "unit": "iter/sec",
            "range": "stddev: 0.0017032",
            "group": "node",
            "extra": "mean: 25.747 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 47.91921416990913,
            "unit": "iter/sec",
            "range": "stddev: 0.0015838",
            "group": "node",
            "extra": "mean: 20.868 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 24.443333803997017,
            "unit": "iter/sec",
            "range": "stddev: 0.0061225",
            "group": "node",
            "extra": "mean: 40.911 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 24.900332720574323,
            "unit": "iter/sec",
            "range": "stddev: 0.0039965",
            "group": "node",
            "extra": "mean: 40.160 msec\nrounds: 100"
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
          "id": "dac81560647b2ffaa170ee87f673bd9f89db2b41",
          "message": "Dependencies: increase minimum version requirement `plumpy~=0.15.1` (#4398)\n\nThe patch release of `plumpy` comes with a simple fix that will prevent\r\nthe printing of many warnings when running processes. So although not\r\ncritical, it does improve user experience.",
          "timestamp": "2020-09-25T16:20:33+02:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/dac81560647b2ffaa170ee87f673bd9f89db2b41",
          "distinct": true,
          "tree_id": "f656192bf7be5c9d1c2e9f660333cbecf1ad8430"
        },
        "date": 1601044575371,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 2.349315193098575,
            "unit": "iter/sec",
            "range": "stddev: 0.041542",
            "group": "engine",
            "extra": "mean: 425.66 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.539129339332736,
            "unit": "iter/sec",
            "range": "stddev: 0.063984",
            "group": "engine",
            "extra": "mean: 1.8548 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.5822432354711646,
            "unit": "iter/sec",
            "range": "stddev: 0.078017",
            "group": "engine",
            "extra": "mean: 1.7175 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.14312047590059074,
            "unit": "iter/sec",
            "range": "stddev: 0.19102",
            "group": "engine",
            "extra": "mean: 6.9871 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.15229412014030802,
            "unit": "iter/sec",
            "range": "stddev: 0.16067",
            "group": "engine",
            "extra": "mean: 6.5662 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 1.619264503797935,
            "unit": "iter/sec",
            "range": "stddev: 0.027897",
            "group": "engine",
            "extra": "mean: 617.56 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.36456219846457133,
            "unit": "iter/sec",
            "range": "stddev: 0.11341",
            "group": "engine",
            "extra": "mean: 2.7430 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.4088626971597722,
            "unit": "iter/sec",
            "range": "stddev: 0.076741",
            "group": "engine",
            "extra": "mean: 2.4458 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.11077178311526056,
            "unit": "iter/sec",
            "range": "stddev: 0.24484",
            "group": "engine",
            "extra": "mean: 9.0276 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.12390087581386869,
            "unit": "iter/sec",
            "range": "stddev: 0.16566",
            "group": "engine",
            "extra": "mean: 8.0710 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.6416220491346434,
            "unit": "iter/sec",
            "range": "stddev: 0.045143",
            "group": "import-export",
            "extra": "mean: 378.56 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.3193327259802015,
            "unit": "iter/sec",
            "range": "stddev: 0.064135",
            "group": "import-export",
            "extra": "mean: 431.16 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 0.13556147611950406,
            "unit": "iter/sec",
            "range": "stddev: 0.24083",
            "group": "import-export",
            "extra": "mean: 7.3767 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 0.14196935363629096,
            "unit": "iter/sec",
            "range": "stddev: 0.26266",
            "group": "import-export",
            "extra": "mean: 7.0438 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 92.37202820310395,
            "unit": "iter/sec",
            "range": "stddev: 0.0020248",
            "group": "node",
            "extra": "mean: 10.826 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 45.512743841339145,
            "unit": "iter/sec",
            "range": "stddev: 0.0025230",
            "group": "node",
            "extra": "mean: 21.972 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 44.62859195213363,
            "unit": "iter/sec",
            "range": "stddev: 0.0028349",
            "group": "node",
            "extra": "mean: 22.407 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 51.75027982581923,
            "unit": "iter/sec",
            "range": "stddev: 0.0022646",
            "group": "node",
            "extra": "mean: 19.324 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 23.992812288953484,
            "unit": "iter/sec",
            "range": "stddev: 0.018173",
            "group": "node",
            "extra": "mean: 41.679 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 25.907322485027606,
            "unit": "iter/sec",
            "range": "stddev: 0.0040194",
            "group": "node",
            "extra": "mean: 38.599 msec\nrounds: 100"
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
          "id": "ff30ebdb8860dc69bcbfec5e7a19e8b6e15a4f42",
          "message": "`verdi setup`: forward broker defaults to interactive mode (#4405)\n\nThe options for the message broker configuration do define defaults,\r\nhowever, the interactive clones for `verdi setup`, which are defined in\r\n`aiida.cmdline.params.options.commands.setup` override the default with\r\nthe `contextual_default` which sets an empty default, unless it is taken\r\nfrom an existing profile. The result is that for new profiles, the\r\nbroker options do not specify a default, even though for most usecases\r\nthe defaults will be required. After the changes of this commit, the\r\nprompt of `verdi setup` will provide a default for all broker parameters\r\nso most users will simply have to press enter each time.",
          "timestamp": "2020-09-26T20:24:20+02:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/ff30ebdb8860dc69bcbfec5e7a19e8b6e15a4f42",
          "distinct": true,
          "tree_id": "7bb1be28e3269247b969133b649361fe0a808875"
        },
        "date": 1601145592264,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 2.5951682438256056,
            "unit": "iter/sec",
            "range": "stddev: 0.037593",
            "group": "engine",
            "extra": "mean: 385.33 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.5822758662328607,
            "unit": "iter/sec",
            "range": "stddev: 0.047051",
            "group": "engine",
            "extra": "mean: 1.7174 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.6283064838409448,
            "unit": "iter/sec",
            "range": "stddev: 0.081228",
            "group": "engine",
            "extra": "mean: 1.5916 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.14524381152740895,
            "unit": "iter/sec",
            "range": "stddev: 0.15806",
            "group": "engine",
            "extra": "mean: 6.8850 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.15286824788228118,
            "unit": "iter/sec",
            "range": "stddev: 0.15541",
            "group": "engine",
            "extra": "mean: 6.5416 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 1.519044089798232,
            "unit": "iter/sec",
            "range": "stddev: 0.051408",
            "group": "engine",
            "extra": "mean: 658.31 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.3479722759071515,
            "unit": "iter/sec",
            "range": "stddev: 0.097757",
            "group": "engine",
            "extra": "mean: 2.8738 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.38865231296130914,
            "unit": "iter/sec",
            "range": "stddev: 0.085169",
            "group": "engine",
            "extra": "mean: 2.5730 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.11109464693010827,
            "unit": "iter/sec",
            "range": "stddev: 0.10372",
            "group": "engine",
            "extra": "mean: 9.0013 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.12313064623267053,
            "unit": "iter/sec",
            "range": "stddev: 0.11549",
            "group": "engine",
            "extra": "mean: 8.1215 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.530879221527781,
            "unit": "iter/sec",
            "range": "stddev: 0.053968",
            "group": "import-export",
            "extra": "mean: 395.12 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.2612510774692027,
            "unit": "iter/sec",
            "range": "stddev: 0.049550",
            "group": "import-export",
            "extra": "mean: 442.23 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 0.13646881295687216,
            "unit": "iter/sec",
            "range": "stddev: 0.066502",
            "group": "import-export",
            "extra": "mean: 7.3277 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 0.1384702654349807,
            "unit": "iter/sec",
            "range": "stddev: 0.16701",
            "group": "import-export",
            "extra": "mean: 7.2218 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 96.41821219039,
            "unit": "iter/sec",
            "range": "stddev: 0.00033480",
            "group": "node",
            "extra": "mean: 10.371 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 40.534177074611236,
            "unit": "iter/sec",
            "range": "stddev: 0.0019161",
            "group": "node",
            "extra": "mean: 24.671 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 40.499601316061984,
            "unit": "iter/sec",
            "range": "stddev: 0.0023904",
            "group": "node",
            "extra": "mean: 24.692 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 49.6622644207789,
            "unit": "iter/sec",
            "range": "stddev: 0.0015412",
            "group": "node",
            "extra": "mean: 20.136 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 25.071301678844296,
            "unit": "iter/sec",
            "range": "stddev: 0.019390",
            "group": "node",
            "extra": "mean: 39.886 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 25.982240181651136,
            "unit": "iter/sec",
            "range": "stddev: 0.0036753",
            "group": "node",
            "extra": "mean: 38.488 msec\nrounds: 100"
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
          "id": "1310abaa7f765866f636c9af2d3332e3eaf74ced",
          "message": "`verdi setup`: improve validation and help string of broker virtual host (#4408)\n\nThe help string of the `--broker-virtual-host` option of `verdi setup`\r\nincorrectly said that forward slashes have to be escaped but this is not\r\ntrue. The code will escape any characters necessary when constructing\r\nthe URL to connect to RabbitMQ. On top of that, slashes would fail the\r\nvalidation outright, even though these are common in virtual hosts. For\r\nexample the virtual host always starts with a leading forward slash, but\r\nour validation would reject it. Also the leading slash will be added by\r\nthe code and so does not have to be used in the setup phase. The help\r\nstring and the documentation now reflect this.\r\n\r\nThe exacti naming rules for virtual hosts, imposed by RabbitMQ or other\r\nimplemenatations of the AMQP protocol, are not fully clear. But instead\r\nof putting an explicit validation on AiiDA's side and running the risk\r\nthat we incorrectly reject valid virtual host names, we simply accept\r\nall strings. In any case, any non-default virtual host will have to be\r\ncreated through RabbitMQ's control interface, which will perform the\r\nvalidation itself.",
          "timestamp": "2020-09-28T08:30:05+02:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/1310abaa7f765866f636c9af2d3332e3eaf74ced",
          "distinct": true,
          "tree_id": "0950b812971ab426a8f4bb6ebd2ca7c471670dc4"
        },
        "date": 1601275529242,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 2.6319504139236605,
            "unit": "iter/sec",
            "range": "stddev: 0.035931",
            "group": "engine",
            "extra": "mean: 379.95 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.5841907483031008,
            "unit": "iter/sec",
            "range": "stddev: 0.059499",
            "group": "engine",
            "extra": "mean: 1.7118 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.6335538959715851,
            "unit": "iter/sec",
            "range": "stddev: 0.046474",
            "group": "engine",
            "extra": "mean: 1.5784 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.146017080498564,
            "unit": "iter/sec",
            "range": "stddev: 0.17363",
            "group": "engine",
            "extra": "mean: 6.8485 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.15373146525366768,
            "unit": "iter/sec",
            "range": "stddev: 0.12432",
            "group": "engine",
            "extra": "mean: 6.5048 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 1.5474070675327192,
            "unit": "iter/sec",
            "range": "stddev: 0.051966",
            "group": "engine",
            "extra": "mean: 646.24 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.36080483751695375,
            "unit": "iter/sec",
            "range": "stddev: 0.068838",
            "group": "engine",
            "extra": "mean: 2.7716 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.39885007092530256,
            "unit": "iter/sec",
            "range": "stddev: 0.070511",
            "group": "engine",
            "extra": "mean: 2.5072 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.11316751614162107,
            "unit": "iter/sec",
            "range": "stddev: 0.11636",
            "group": "engine",
            "extra": "mean: 8.8365 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.1247416289524884,
            "unit": "iter/sec",
            "range": "stddev: 0.13752",
            "group": "engine",
            "extra": "mean: 8.0166 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.575869727596877,
            "unit": "iter/sec",
            "range": "stddev: 0.057472",
            "group": "import-export",
            "extra": "mean: 388.22 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.286622278159212,
            "unit": "iter/sec",
            "range": "stddev: 0.048907",
            "group": "import-export",
            "extra": "mean: 437.33 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 0.14007330666374246,
            "unit": "iter/sec",
            "range": "stddev: 0.055377",
            "group": "import-export",
            "extra": "mean: 7.1391 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 0.1396646488810347,
            "unit": "iter/sec",
            "range": "stddev: 0.097339",
            "group": "import-export",
            "extra": "mean: 7.1600 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 95.80886009777609,
            "unit": "iter/sec",
            "range": "stddev: 0.00065398",
            "group": "node",
            "extra": "mean: 10.437 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 43.83838556385501,
            "unit": "iter/sec",
            "range": "stddev: 0.00095755",
            "group": "node",
            "extra": "mean: 22.811 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 42.96753952216405,
            "unit": "iter/sec",
            "range": "stddev: 0.0011187",
            "group": "node",
            "extra": "mean: 23.273 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 50.6064222998115,
            "unit": "iter/sec",
            "range": "stddev: 0.0023639",
            "group": "node",
            "extra": "mean: 19.760 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 25.882161282858572,
            "unit": "iter/sec",
            "range": "stddev: 0.016733",
            "group": "node",
            "extra": "mean: 38.637 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 26.8967083460895,
            "unit": "iter/sec",
            "range": "stddev: 0.0025653",
            "group": "node",
            "extra": "mean: 37.179 msec\nrounds: 100"
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
          "id": "e2b5385044076f135e5b769aa8fd24f7950738f5",
          "message": "Merge branch 'master' of github.com:aiidateam/aiida-core into develop\n\nMerge after release of `v1.4.0`.",
          "timestamp": "2020-09-28T11:12:09+02:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/e2b5385044076f135e5b769aa8fd24f7950738f5",
          "distinct": true,
          "tree_id": "036461f0e803060dbed684406dab0a1cb6834a0a"
        },
        "date": 1601288423575,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 2.7581684976311003,
            "unit": "iter/sec",
            "range": "stddev: 0.032993",
            "group": "engine",
            "extra": "mean: 362.56 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.5864127649484789,
            "unit": "iter/sec",
            "range": "stddev: 0.096023",
            "group": "engine",
            "extra": "mean: 1.7053 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.6342654902963576,
            "unit": "iter/sec",
            "range": "stddev: 0.062964",
            "group": "engine",
            "extra": "mean: 1.5766 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.145942580359998,
            "unit": "iter/sec",
            "range": "stddev: 0.16651",
            "group": "engine",
            "extra": "mean: 6.8520 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.15212529378106623,
            "unit": "iter/sec",
            "range": "stddev: 0.28587",
            "group": "engine",
            "extra": "mean: 6.5735 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 1.5734612342193273,
            "unit": "iter/sec",
            "range": "stddev: 0.038316",
            "group": "engine",
            "extra": "mean: 635.54 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.3580145443834022,
            "unit": "iter/sec",
            "range": "stddev: 0.038343",
            "group": "engine",
            "extra": "mean: 2.7932 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.38837395728156465,
            "unit": "iter/sec",
            "range": "stddev: 0.14746",
            "group": "engine",
            "extra": "mean: 2.5748 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.10789320500867908,
            "unit": "iter/sec",
            "range": "stddev: 0.15116",
            "group": "engine",
            "extra": "mean: 9.2684 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.11989461787555744,
            "unit": "iter/sec",
            "range": "stddev: 0.27453",
            "group": "engine",
            "extra": "mean: 8.3407 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.5213822321780306,
            "unit": "iter/sec",
            "range": "stddev: 0.057073",
            "group": "import-export",
            "extra": "mean: 396.61 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.2345661992951293,
            "unit": "iter/sec",
            "range": "stddev: 0.051246",
            "group": "import-export",
            "extra": "mean: 447.51 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 0.1343156447811141,
            "unit": "iter/sec",
            "range": "stddev: 0.14493",
            "group": "import-export",
            "extra": "mean: 7.4451 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 0.14036204290156232,
            "unit": "iter/sec",
            "range": "stddev: 0.12769",
            "group": "import-export",
            "extra": "mean: 7.1244 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 94.44824168346607,
            "unit": "iter/sec",
            "range": "stddev: 0.0013486",
            "group": "node",
            "extra": "mean: 10.588 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 42.580156995446075,
            "unit": "iter/sec",
            "range": "stddev: 0.0024108",
            "group": "node",
            "extra": "mean: 23.485 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 44.7673501672877,
            "unit": "iter/sec",
            "range": "stddev: 0.0019379",
            "group": "node",
            "extra": "mean: 22.338 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 53.37514927563365,
            "unit": "iter/sec",
            "range": "stddev: 0.0022828",
            "group": "node",
            "extra": "mean: 18.735 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 26.364718325172237,
            "unit": "iter/sec",
            "range": "stddev: 0.0037947",
            "group": "node",
            "extra": "mean: 37.929 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 25.79135134576699,
            "unit": "iter/sec",
            "range": "stddev: 0.0039700",
            "group": "node",
            "extra": "mean: 38.773 msec\nrounds: 100"
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
          "id": "65ad067b18cffeb639994efe9a372ec1475e1615",
          "message": "CI: move `pylint` configuration to `pyproject.toml` (#4411)\n\nThis is supported by `pylint` as of v2.5.",
          "timestamp": "2020-09-28T23:17:27+02:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/65ad067b18cffeb639994efe9a372ec1475e1615",
          "distinct": true,
          "tree_id": "636ba633d0ab1b287b1e6483de770bc7d9c6522f"
        },
        "date": 1601328798710,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 2.5278556043498845,
            "unit": "iter/sec",
            "range": "stddev: 0.040051",
            "group": "engine",
            "extra": "mean: 395.59 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.56236407709815,
            "unit": "iter/sec",
            "range": "stddev: 0.050232",
            "group": "engine",
            "extra": "mean: 1.7782 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.6027679794338296,
            "unit": "iter/sec",
            "range": "stddev: 0.093302",
            "group": "engine",
            "extra": "mean: 1.6590 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.14136856954704466,
            "unit": "iter/sec",
            "range": "stddev: 0.17878",
            "group": "engine",
            "extra": "mean: 7.0737 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.14796439392932925,
            "unit": "iter/sec",
            "range": "stddev: 0.14809",
            "group": "engine",
            "extra": "mean: 6.7584 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 1.516443453287281,
            "unit": "iter/sec",
            "range": "stddev: 0.054835",
            "group": "engine",
            "extra": "mean: 659.44 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.3465109798969541,
            "unit": "iter/sec",
            "range": "stddev: 0.084077",
            "group": "engine",
            "extra": "mean: 2.8859 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.3789546194376668,
            "unit": "iter/sec",
            "range": "stddev: 0.087397",
            "group": "engine",
            "extra": "mean: 2.6388 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.10854108840164904,
            "unit": "iter/sec",
            "range": "stddev: 0.10558",
            "group": "engine",
            "extra": "mean: 9.2131 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.12061387934570872,
            "unit": "iter/sec",
            "range": "stddev: 0.14028",
            "group": "engine",
            "extra": "mean: 8.2909 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.4916965991357327,
            "unit": "iter/sec",
            "range": "stddev: 0.047675",
            "group": "import-export",
            "extra": "mean: 401.33 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.3275437095602056,
            "unit": "iter/sec",
            "range": "stddev: 0.0081139",
            "group": "import-export",
            "extra": "mean: 429.64 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 0.13509758691663168,
            "unit": "iter/sec",
            "range": "stddev: 0.071879",
            "group": "import-export",
            "extra": "mean: 7.4021 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 0.13490658559820062,
            "unit": "iter/sec",
            "range": "stddev: 0.15221",
            "group": "import-export",
            "extra": "mean: 7.4125 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 97.09145704747407,
            "unit": "iter/sec",
            "range": "stddev: 0.00045121",
            "group": "node",
            "extra": "mean: 10.300 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 42.20189291206369,
            "unit": "iter/sec",
            "range": "stddev: 0.0040779",
            "group": "node",
            "extra": "mean: 23.696 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 41.04185128564632,
            "unit": "iter/sec",
            "range": "stddev: 0.0027853",
            "group": "node",
            "extra": "mean: 24.365 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 51.4114214538161,
            "unit": "iter/sec",
            "range": "stddev: 0.00096991",
            "group": "node",
            "extra": "mean: 19.451 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 25.332396161000048,
            "unit": "iter/sec",
            "range": "stddev: 0.018010",
            "group": "node",
            "extra": "mean: 39.475 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 26.43412400014882,
            "unit": "iter/sec",
            "range": "stddev: 0.0027278",
            "group": "node",
            "extra": "mean: 37.830 msec\nrounds: 100"
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
          "id": "91449241ff2e12dd836b29882e32201cc7841716",
          "message": "`verdi process show`: order called by ctime and use process label (#4407)\n\nThe command was showing the called subprocesses in a random order and\r\nused the node type, which is often uninformative. For example, all\r\nworkchains are always shown as `WorkChainNode`. By using the process\r\nlabel instead, which is more specific, and ordering the called nodes by\r\ncreation time, the list gives a more natural overview of the order in\r\nwhich the subprocesses were called.",
          "timestamp": "2020-09-29T14:29:57+02:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/91449241ff2e12dd836b29882e32201cc7841716",
          "distinct": true,
          "tree_id": "a9721615e95c90093d05e5801d20086ee303d99b"
        },
        "date": 1601383576618,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 2.512673468295721,
            "unit": "iter/sec",
            "range": "stddev: 0.038897",
            "group": "engine",
            "extra": "mean: 397.98 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.5689122167778176,
            "unit": "iter/sec",
            "range": "stddev: 0.046441",
            "group": "engine",
            "extra": "mean: 1.7577 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.6089045896404075,
            "unit": "iter/sec",
            "range": "stddev: 0.061526",
            "group": "engine",
            "extra": "mean: 1.6423 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.13716469802225573,
            "unit": "iter/sec",
            "range": "stddev: 0.20892",
            "group": "engine",
            "extra": "mean: 7.2905 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.14332607694985885,
            "unit": "iter/sec",
            "range": "stddev: 0.20045",
            "group": "engine",
            "extra": "mean: 6.9771 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 1.4764837107699997,
            "unit": "iter/sec",
            "range": "stddev: 0.013420",
            "group": "engine",
            "extra": "mean: 677.28 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.33356461995812514,
            "unit": "iter/sec",
            "range": "stddev: 0.047227",
            "group": "engine",
            "extra": "mean: 2.9979 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.3731399188435053,
            "unit": "iter/sec",
            "range": "stddev: 0.056591",
            "group": "engine",
            "extra": "mean: 2.6800 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.10434462494629723,
            "unit": "iter/sec",
            "range": "stddev: 0.15108",
            "group": "engine",
            "extra": "mean: 9.5836 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.11438842925025895,
            "unit": "iter/sec",
            "range": "stddev: 0.18060",
            "group": "engine",
            "extra": "mean: 8.7421 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.6400266302126925,
            "unit": "iter/sec",
            "range": "stddev: 0.059103",
            "group": "import-export",
            "extra": "mean: 378.78 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.3989786233360313,
            "unit": "iter/sec",
            "range": "stddev: 0.054355",
            "group": "import-export",
            "extra": "mean: 416.84 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 0.14231456170195156,
            "unit": "iter/sec",
            "range": "stddev: 0.16735",
            "group": "import-export",
            "extra": "mean: 7.0267 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 0.14522509425391306,
            "unit": "iter/sec",
            "range": "stddev: 0.042900",
            "group": "import-export",
            "extra": "mean: 6.8859 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 86.81760707527756,
            "unit": "iter/sec",
            "range": "stddev: 0.0010652",
            "group": "node",
            "extra": "mean: 11.518 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 40.9275188146556,
            "unit": "iter/sec",
            "range": "stddev: 0.0010657",
            "group": "node",
            "extra": "mean: 24.433 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 40.317836959011366,
            "unit": "iter/sec",
            "range": "stddev: 0.0014447",
            "group": "node",
            "extra": "mean: 24.803 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 47.48382309717409,
            "unit": "iter/sec",
            "range": "stddev: 0.0011998",
            "group": "node",
            "extra": "mean: 21.060 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 23.24842763607139,
            "unit": "iter/sec",
            "range": "stddev: 0.020329",
            "group": "node",
            "extra": "mean: 43.014 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 24.983622960324205,
            "unit": "iter/sec",
            "range": "stddev: 0.0021451",
            "group": "node",
            "extra": "mean: 40.026 msec\nrounds: 100"
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
          "id": "af91a8b10f2fe68360483a951d5c578863d38b76",
          "message": "Dependencies: update requirement `pytest~=6.0` and use `pyproject.toml` (#4410)\n\nStarting from v6.0, `pytest` supports using the `pyproject.toml` instead\r\nof a `pytest.ini` to define its configuration. Given that this is\r\nquickly becoming the Python packaging standard and allows us to reduce\r\nthe number of configuration files in the top level of the repository, we\r\nincrease the version requirement of `pytest`.\r\n\r\nNote that we also require `pytest-rerunfailures>=9.1.1` because lower\r\nversions are broken in combination with `pytest==6.1`. See the following:\r\n\r\n   https://github.com/pytest-dev/pytest-rerunfailures/issues/128\r\n\r\nfor details.",
          "timestamp": "2020-09-29T17:34:16+02:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/af91a8b10f2fe68360483a951d5c578863d38b76",
          "distinct": true,
          "tree_id": "3fc1f773a856d3b5ae5c8ecf03213deb0833cb71"
        },
        "date": 1601394997757,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 2.3788016372936274,
            "unit": "iter/sec",
            "range": "stddev: 0.010232",
            "group": "engine",
            "extra": "mean: 420.38 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.5203687675031248,
            "unit": "iter/sec",
            "range": "stddev: 0.066699",
            "group": "engine",
            "extra": "mean: 1.9217 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.5460495473808153,
            "unit": "iter/sec",
            "range": "stddev: 0.062659",
            "group": "engine",
            "extra": "mean: 1.8313 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.12903893897815824,
            "unit": "iter/sec",
            "range": "stddev: 0.18790",
            "group": "engine",
            "extra": "mean: 7.7496 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.13296075648972258,
            "unit": "iter/sec",
            "range": "stddev: 0.18639",
            "group": "engine",
            "extra": "mean: 7.5210 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 1.3130644434013772,
            "unit": "iter/sec",
            "range": "stddev: 0.064699",
            "group": "engine",
            "extra": "mean: 761.58 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.304922400208419,
            "unit": "iter/sec",
            "range": "stddev: 0.078807",
            "group": "engine",
            "extra": "mean: 3.2795 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.33722374396692684,
            "unit": "iter/sec",
            "range": "stddev: 0.070745",
            "group": "engine",
            "extra": "mean: 2.9654 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.09838710629284438,
            "unit": "iter/sec",
            "range": "stddev: 0.14323",
            "group": "engine",
            "extra": "mean: 10.164 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.10773371537586536,
            "unit": "iter/sec",
            "range": "stddev: 0.19055",
            "group": "engine",
            "extra": "mean: 9.2821 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.4203333272611416,
            "unit": "iter/sec",
            "range": "stddev: 0.066935",
            "group": "import-export",
            "extra": "mean: 413.17 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.2915678806765065,
            "unit": "iter/sec",
            "range": "stddev: 0.024796",
            "group": "import-export",
            "extra": "mean: 436.38 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 0.12690227275812874,
            "unit": "iter/sec",
            "range": "stddev: 0.19188",
            "group": "import-export",
            "extra": "mean: 7.8801 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 0.12969834618623813,
            "unit": "iter/sec",
            "range": "stddev: 0.10575",
            "group": "import-export",
            "extra": "mean: 7.7102 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 76.07691037546286,
            "unit": "iter/sec",
            "range": "stddev: 0.00060325",
            "group": "node",
            "extra": "mean: 13.145 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 34.17572566900354,
            "unit": "iter/sec",
            "range": "stddev: 0.0017848",
            "group": "node",
            "extra": "mean: 29.261 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 33.06790718478337,
            "unit": "iter/sec",
            "range": "stddev: 0.0025010",
            "group": "node",
            "extra": "mean: 30.241 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 41.133159611720465,
            "unit": "iter/sec",
            "range": "stddev: 0.0016673",
            "group": "node",
            "extra": "mean: 24.311 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 22.62486025349725,
            "unit": "iter/sec",
            "range": "stddev: 0.020320",
            "group": "node",
            "extra": "mean: 44.199 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 22.89794862931178,
            "unit": "iter/sec",
            "range": "stddev: 0.0023793",
            "group": "node",
            "extra": "mean: 43.672 msec\nrounds: 100"
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
          "id": "4544bc49a50c9aa3abebd2837efb5626958ee2b4",
          "message": "CI: add coverage patch threshold to prevent false positives (#4413)\n\nThe project diff percentage is the change in coverage w.r.t. all lines\r\nin the project, whereas the patch diff percentage is the change in\r\ncoverage w.r.t. only lines touched by the PR. The patch threshold is\r\ncurrently defaulting to 0%, hence it is very easy to fail. By raising it\r\nto 0.1% it should now only fail when there is a significant reduction\r\nin coverage. Number may need to be further tweaked.",
          "timestamp": "2020-09-30T10:24:15+02:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/4544bc49a50c9aa3abebd2837efb5626958ee2b4",
          "distinct": true,
          "tree_id": "e8cc6385b285fc53da873eb1a8b3b569fbfc567d"
        },
        "date": 1601455210106,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 2.6324374461813265,
            "unit": "iter/sec",
            "range": "stddev: 0.012432",
            "group": "engine",
            "extra": "mean: 379.88 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.5798333782431454,
            "unit": "iter/sec",
            "range": "stddev: 0.090934",
            "group": "engine",
            "extra": "mean: 1.7246 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.6241034306814143,
            "unit": "iter/sec",
            "range": "stddev: 0.070708",
            "group": "engine",
            "extra": "mean: 1.6023 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.14260730388370646,
            "unit": "iter/sec",
            "range": "stddev: 0.18185",
            "group": "engine",
            "extra": "mean: 7.0123 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.14789024337371942,
            "unit": "iter/sec",
            "range": "stddev: 0.17266",
            "group": "engine",
            "extra": "mean: 6.7618 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 1.4820099493234955,
            "unit": "iter/sec",
            "range": "stddev: 0.057665",
            "group": "engine",
            "extra": "mean: 674.76 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.34671340251089483,
            "unit": "iter/sec",
            "range": "stddev: 0.057524",
            "group": "engine",
            "extra": "mean: 2.8842 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.3875533148137904,
            "unit": "iter/sec",
            "range": "stddev: 0.078830",
            "group": "engine",
            "extra": "mean: 2.5803 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.10866367219533853,
            "unit": "iter/sec",
            "range": "stddev: 0.13599",
            "group": "engine",
            "extra": "mean: 9.2027 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.12065537735457103,
            "unit": "iter/sec",
            "range": "stddev: 0.15094",
            "group": "engine",
            "extra": "mean: 8.2881 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.708358750668805,
            "unit": "iter/sec",
            "range": "stddev: 0.058034",
            "group": "import-export",
            "extra": "mean: 369.23 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.511794309143921,
            "unit": "iter/sec",
            "range": "stddev: 0.0088517",
            "group": "import-export",
            "extra": "mean: 398.12 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 0.149027209149415,
            "unit": "iter/sec",
            "range": "stddev: 0.068834",
            "group": "import-export",
            "extra": "mean: 6.7102 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 0.1498360782815068,
            "unit": "iter/sec",
            "range": "stddev: 0.037629",
            "group": "import-export",
            "extra": "mean: 6.6740 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 96.39163365531823,
            "unit": "iter/sec",
            "range": "stddev: 0.00027955",
            "group": "node",
            "extra": "mean: 10.374 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 43.6991939624522,
            "unit": "iter/sec",
            "range": "stddev: 0.00069310",
            "group": "node",
            "extra": "mean: 22.884 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 43.241124886272154,
            "unit": "iter/sec",
            "range": "stddev: 0.0010325",
            "group": "node",
            "extra": "mean: 23.126 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 49.77320750893358,
            "unit": "iter/sec",
            "range": "stddev: 0.0019965",
            "group": "node",
            "extra": "mean: 20.091 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 25.593480625502217,
            "unit": "iter/sec",
            "range": "stddev: 0.017426",
            "group": "node",
            "extra": "mean: 39.072 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 26.93085885887169,
            "unit": "iter/sec",
            "range": "stddev: 0.0018068",
            "group": "node",
            "extra": "mean: 37.132 msec\nrounds: 100"
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
          "id": "02248cf3686a0ab89faf1625e0da24d9e33d8cde",
          "message": "Replace old format string interpolation with f-strings (#4400)\n\nSince Python 3.5 is no longer supported, format string interpolations\r\ncan now be replaced by f-strings, introduced in Python 3.6, which are\r\nmore readable, require less characters and are more efficient.\r\n\r\nNote that `pylint` issues a warning when using f-strings for log\r\nmessages, just as it does for format interpolated strings. The reasoning\r\nis that this is slightly inefficient as the strings are always\r\ninterpolated even if the log is discarded, but also by not passing the\r\nformatting parameters as arguments, the available metadata is reduced.\r\nI feel these inefficiencies are premature optimizations as they are\r\nreally minimal and don't weigh up against the improved readability and\r\nmaintainability of using f-strings. That is why the `pylint` config is\r\nupdate to ignore the warning `logging-fstring-interpolation` which\r\nreplaces `logging-format-interpolation` that was ignored before.\r\n\r\nThe majority of the conversions were done automatically with the linting\r\ntool `flynt` which is also added as a pre-commit hook. It is added\r\nbefore the `yapf` step because since `flynt` will touch formatting,\r\n`yapf` will then get a chance to check it.",
          "timestamp": "2020-09-30T15:14:45+02:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/02248cf3686a0ab89faf1625e0da24d9e33d8cde",
          "distinct": true,
          "tree_id": "34e646ac57896670e7d2081e1c7f91086b17fb4a"
        },
        "date": 1601472601381,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 2.7726655885680698,
            "unit": "iter/sec",
            "range": "stddev: 0.037712",
            "group": "engine",
            "extra": "mean: 360.66 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.627050373597023,
            "unit": "iter/sec",
            "range": "stddev: 0.077089",
            "group": "engine",
            "extra": "mean: 1.5948 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.6681543108143029,
            "unit": "iter/sec",
            "range": "stddev: 0.057868",
            "group": "engine",
            "extra": "mean: 1.4967 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.15068014442446231,
            "unit": "iter/sec",
            "range": "stddev: 0.10999",
            "group": "engine",
            "extra": "mean: 6.6366 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.15472880028346572,
            "unit": "iter/sec",
            "range": "stddev: 0.22530",
            "group": "engine",
            "extra": "mean: 6.4629 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 1.600039825375295,
            "unit": "iter/sec",
            "range": "stddev: 0.015500",
            "group": "engine",
            "extra": "mean: 624.98 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.3620096324131166,
            "unit": "iter/sec",
            "range": "stddev: 0.088549",
            "group": "engine",
            "extra": "mean: 2.7624 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.3999118558277694,
            "unit": "iter/sec",
            "range": "stddev: 0.095292",
            "group": "engine",
            "extra": "mean: 2.5006 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.11155868897039115,
            "unit": "iter/sec",
            "range": "stddev: 0.13856",
            "group": "engine",
            "extra": "mean: 8.9639 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.12214188082834226,
            "unit": "iter/sec",
            "range": "stddev: 0.17742",
            "group": "engine",
            "extra": "mean: 8.1872 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.9411678748810965,
            "unit": "iter/sec",
            "range": "stddev: 0.0041507",
            "group": "import-export",
            "extra": "mean: 340.00 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.553937445584284,
            "unit": "iter/sec",
            "range": "stddev: 0.048917",
            "group": "import-export",
            "extra": "mean: 391.55 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 0.14676604678456923,
            "unit": "iter/sec",
            "range": "stddev: 0.084841",
            "group": "import-export",
            "extra": "mean: 6.8136 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 0.1453804785009321,
            "unit": "iter/sec",
            "range": "stddev: 0.12661",
            "group": "import-export",
            "extra": "mean: 6.8785 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 99.10672512056615,
            "unit": "iter/sec",
            "range": "stddev: 0.00036317",
            "group": "node",
            "extra": "mean: 10.090 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 45.154336132415814,
            "unit": "iter/sec",
            "range": "stddev: 0.00064190",
            "group": "node",
            "extra": "mean: 22.146 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 42.88678039777215,
            "unit": "iter/sec",
            "range": "stddev: 0.00097149",
            "group": "node",
            "extra": "mean: 23.317 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 50.38844045640456,
            "unit": "iter/sec",
            "range": "stddev: 0.00080662",
            "group": "node",
            "extra": "mean: 19.846 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 24.80577917066225,
            "unit": "iter/sec",
            "range": "stddev: 0.018662",
            "group": "node",
            "extra": "mean: 40.313 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 26.95443690720298,
            "unit": "iter/sec",
            "range": "stddev: 0.0026294",
            "group": "node",
            "extra": "mean: 37.100 msec\nrounds: 100"
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
          "id": "29331b558b45ba74acf1ca633a2d8bfabc1bdd05",
          "message": "CI: use `-e` install for tox + add docker-compose for isolated RabbitMQ (#4375)\n\n* Using `pip install -e .` for tox runs improves startup time for tests\r\n   by preventing unnecessary copy of files.\r\n\r\n* The docker-compose yml file allows to set up an isolated RabbitMQ\r\n   instance for local CI testing.",
          "timestamp": "2020-10-01T11:54:31+02:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/29331b558b45ba74acf1ca633a2d8bfabc1bdd05",
          "distinct": true,
          "tree_id": "7fbd24fd833ead6688438d007d232a88fbca5f7f"
        },
        "date": 1601547047571,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 2.4500689592979112,
            "unit": "iter/sec",
            "range": "stddev: 0.048124",
            "group": "engine",
            "extra": "mean: 408.15 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.5733666466594768,
            "unit": "iter/sec",
            "range": "stddev: 0.079195",
            "group": "engine",
            "extra": "mean: 1.7441 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.6064971362707217,
            "unit": "iter/sec",
            "range": "stddev: 0.064602",
            "group": "engine",
            "extra": "mean: 1.6488 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.14328088695536775,
            "unit": "iter/sec",
            "range": "stddev: 0.17487",
            "group": "engine",
            "extra": "mean: 6.9793 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.14572723050262243,
            "unit": "iter/sec",
            "range": "stddev: 0.31903",
            "group": "engine",
            "extra": "mean: 6.8621 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 1.4067451030598277,
            "unit": "iter/sec",
            "range": "stddev: 0.021999",
            "group": "engine",
            "extra": "mean: 710.86 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.32097398737857863,
            "unit": "iter/sec",
            "range": "stddev: 0.13469",
            "group": "engine",
            "extra": "mean: 3.1155 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.38382623412832934,
            "unit": "iter/sec",
            "range": "stddev: 0.086012",
            "group": "engine",
            "extra": "mean: 2.6053 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.10800792786390488,
            "unit": "iter/sec",
            "range": "stddev: 0.20268",
            "group": "engine",
            "extra": "mean: 9.2586 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.11812802201961034,
            "unit": "iter/sec",
            "range": "stddev: 0.12903",
            "group": "engine",
            "extra": "mean: 8.4654 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.596114513271541,
            "unit": "iter/sec",
            "range": "stddev: 0.0089390",
            "group": "import-export",
            "extra": "mean: 385.19 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.256304385632951,
            "unit": "iter/sec",
            "range": "stddev: 0.052208",
            "group": "import-export",
            "extra": "mean: 443.20 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 0.13327626101464746,
            "unit": "iter/sec",
            "range": "stddev: 0.14075",
            "group": "import-export",
            "extra": "mean: 7.5032 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 0.13558160236679603,
            "unit": "iter/sec",
            "range": "stddev: 0.16066",
            "group": "import-export",
            "extra": "mean: 7.3756 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 94.26830502249129,
            "unit": "iter/sec",
            "range": "stddev: 0.00087256",
            "group": "node",
            "extra": "mean: 10.608 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 43.919291867889356,
            "unit": "iter/sec",
            "range": "stddev: 0.0018888",
            "group": "node",
            "extra": "mean: 22.769 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 43.84143106609029,
            "unit": "iter/sec",
            "range": "stddev: 0.0015068",
            "group": "node",
            "extra": "mean: 22.809 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 52.066264276359114,
            "unit": "iter/sec",
            "range": "stddev: 0.0011022",
            "group": "node",
            "extra": "mean: 19.206 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 25.465324954374253,
            "unit": "iter/sec",
            "range": "stddev: 0.018730",
            "group": "node",
            "extra": "mean: 39.269 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 25.89764294125544,
            "unit": "iter/sec",
            "range": "stddev: 0.0032003",
            "group": "node",
            "extra": "mean: 38.614 msec\nrounds: 100"
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
          "id": "1e1bdf2dee779970654ed9b22eb996b78e9c4149",
          "message": "Merge remote-tracking branch 'origin/master' into develop",
          "timestamp": "2020-10-04T20:05:09+02:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/1e1bdf2dee779970654ed9b22eb996b78e9c4149",
          "distinct": true,
          "tree_id": "9fcf7ff0a60efb37731c2839955f162d271763e3"
        },
        "date": 1601835654768,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 2.737259377981026,
            "unit": "iter/sec",
            "range": "stddev: 0.035214",
            "group": "engine",
            "extra": "mean: 365.33 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.6141096608061626,
            "unit": "iter/sec",
            "range": "stddev: 0.068588",
            "group": "engine",
            "extra": "mean: 1.6284 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.6656126959421458,
            "unit": "iter/sec",
            "range": "stddev: 0.054120",
            "group": "engine",
            "extra": "mean: 1.5024 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.14848215512433674,
            "unit": "iter/sec",
            "range": "stddev: 0.21266",
            "group": "engine",
            "extra": "mean: 6.7348 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.15655664704713215,
            "unit": "iter/sec",
            "range": "stddev: 0.17373",
            "group": "engine",
            "extra": "mean: 6.3875 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 1.5889304190421918,
            "unit": "iter/sec",
            "range": "stddev: 0.047686",
            "group": "engine",
            "extra": "mean: 629.35 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.36671800347474237,
            "unit": "iter/sec",
            "range": "stddev: 0.078027",
            "group": "engine",
            "extra": "mean: 2.7269 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.40729998296765757,
            "unit": "iter/sec",
            "range": "stddev: 0.081296",
            "group": "engine",
            "extra": "mean: 2.4552 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.11440823131875846,
            "unit": "iter/sec",
            "range": "stddev: 0.17422",
            "group": "engine",
            "extra": "mean: 8.7406 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.12664975433433812,
            "unit": "iter/sec",
            "range": "stddev: 0.11625",
            "group": "engine",
            "extra": "mean: 7.8958 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.824268237012944,
            "unit": "iter/sec",
            "range": "stddev: 0.050325",
            "group": "import-export",
            "extra": "mean: 354.07 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.171074598640243,
            "unit": "iter/sec",
            "range": "stddev: 0.0087292",
            "group": "import-export",
            "extra": "mean: 460.60 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 0.15052240691127394,
            "unit": "iter/sec",
            "range": "stddev: 0.073626",
            "group": "import-export",
            "extra": "mean: 6.6435 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 0.15311476003641447,
            "unit": "iter/sec",
            "range": "stddev: 0.12092",
            "group": "import-export",
            "extra": "mean: 6.5310 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 99.43558542047602,
            "unit": "iter/sec",
            "range": "stddev: 0.00036147",
            "group": "node",
            "extra": "mean: 10.057 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 45.87387794730697,
            "unit": "iter/sec",
            "range": "stddev: 0.00054641",
            "group": "node",
            "extra": "mean: 21.799 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 45.2074603810492,
            "unit": "iter/sec",
            "range": "stddev: 0.00071277",
            "group": "node",
            "extra": "mean: 22.120 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 54.3711257395671,
            "unit": "iter/sec",
            "range": "stddev: 0.00074965",
            "group": "node",
            "extra": "mean: 18.392 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 28.42284728456433,
            "unit": "iter/sec",
            "range": "stddev: 0.0028746",
            "group": "node",
            "extra": "mean: 35.183 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 27.45858055790458,
            "unit": "iter/sec",
            "range": "stddev: 0.016564",
            "group": "node",
            "extra": "mean: 36.418 msec\nrounds: 100"
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
          "pythonVersion": "3.8.6",
          "metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "bd6903d88a4d88077150763574784a1bc375c644",
          "message": "`ProcessBuilder`: allow unsetting of inputs through attribute deletion (#4419)\n\nThe builder object was already able to delete set inputs through the\r\n`__delitem__` method, but `__delattr__` was not implemented causing\r\n`del builder.input_name` to raise. This is not consistent with how these\r\ninputs can be set or accessed as both `__getattr__` and `__setattr__`\r\nare implemented. Implementing `__delattr__` brings the implementation\r\nup to par for all attribute methods.",
          "timestamp": "2020-10-07T10:17:47+02:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/bd6903d88a4d88077150763574784a1bc375c644",
          "distinct": true,
          "tree_id": "5995519297d8bf66e8d978c999c105c505301a92"
        },
        "date": 1602059771557,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 2.1683536049701724,
            "unit": "iter/sec",
            "range": "stddev: 0.045766",
            "group": "engine",
            "extra": "mean: 461.18 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.4855291802099479,
            "unit": "iter/sec",
            "range": "stddev: 0.077907",
            "group": "engine",
            "extra": "mean: 2.0596 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.5136128838292126,
            "unit": "iter/sec",
            "range": "stddev: 0.058932",
            "group": "engine",
            "extra": "mean: 1.9470 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.12200534878762077,
            "unit": "iter/sec",
            "range": "stddev: 0.23662",
            "group": "engine",
            "extra": "mean: 8.1964 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.12521630967079533,
            "unit": "iter/sec",
            "range": "stddev: 0.24972",
            "group": "engine",
            "extra": "mean: 7.9862 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 1.258945368173143,
            "unit": "iter/sec",
            "range": "stddev: 0.011843",
            "group": "engine",
            "extra": "mean: 794.32 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.28490278121683166,
            "unit": "iter/sec",
            "range": "stddev: 0.10170",
            "group": "engine",
            "extra": "mean: 3.5100 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.3249802823843934,
            "unit": "iter/sec",
            "range": "stddev: 0.083493",
            "group": "engine",
            "extra": "mean: 3.0771 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.09269618290813007,
            "unit": "iter/sec",
            "range": "stddev: 0.22529",
            "group": "engine",
            "extra": "mean: 10.788 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.10271825879145077,
            "unit": "iter/sec",
            "range": "stddev: 0.20941",
            "group": "engine",
            "extra": "mean: 9.7354 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.399527544064522,
            "unit": "iter/sec",
            "range": "stddev: 0.057926",
            "group": "import-export",
            "extra": "mean: 416.75 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.1987636116209317,
            "unit": "iter/sec",
            "range": "stddev: 0.059889",
            "group": "import-export",
            "extra": "mean: 454.80 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 0.1212061129442985,
            "unit": "iter/sec",
            "range": "stddev: 0.19100",
            "group": "import-export",
            "extra": "mean: 8.2504 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 0.12564678136377333,
            "unit": "iter/sec",
            "range": "stddev: 0.10165",
            "group": "import-export",
            "extra": "mean: 7.9588 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 72.65226721358249,
            "unit": "iter/sec",
            "range": "stddev: 0.00064568",
            "group": "node",
            "extra": "mean: 13.764 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 33.71254046153299,
            "unit": "iter/sec",
            "range": "stddev: 0.0014526",
            "group": "node",
            "extra": "mean: 29.663 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 33.14615632564283,
            "unit": "iter/sec",
            "range": "stddev: 0.0012939",
            "group": "node",
            "extra": "mean: 30.169 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 40.64771992112242,
            "unit": "iter/sec",
            "range": "stddev: 0.0012510",
            "group": "node",
            "extra": "mean: 24.602 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 22.780402642325303,
            "unit": "iter/sec",
            "range": "stddev: 0.0025123",
            "group": "node",
            "extra": "mean: 43.897 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 22.503720532241008,
            "unit": "iter/sec",
            "range": "stddev: 0.0033308",
            "group": "node",
            "extra": "mean: 44.437 msec\nrounds: 100"
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
          "pythonVersion": "3.8.6",
          "metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "16bc30548f7f1c686d200935174533535e850fd5",
          "message": "`CalcJob`: support nested directories in target of `remote_copy/symlink_list` (#4416)\n\nThe `upload_calculation` transport task would fail if either the\r\n`remote_copy_list` or `remote_symlink_list` contained a target filepath\r\nthat had a nested directory that did not exist yet in the remote working\r\ndirectory. Instead of inspecting the file system or creating the folders\r\nremotely each time a nested target path is encountered, which would incur\r\na potentially expensive operation over the transport each time, the\r\ndirectory hierarchy is first created in the local sandbox folder before\r\nit is copied recursively to the remote in a single shot.",
          "timestamp": "2020-10-16T23:32:42+02:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/16bc30548f7f1c686d200935174533535e850fd5",
          "distinct": true,
          "tree_id": "8c11369793f47e7c4081a6bf1a5317aac81963b4"
        },
        "date": 1602884891655,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 2.635712126855258,
            "unit": "iter/sec",
            "range": "stddev: 0.033255",
            "group": "engine",
            "extra": "mean: 379.40 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.5958344241693685,
            "unit": "iter/sec",
            "range": "stddev: 0.045849",
            "group": "engine",
            "extra": "mean: 1.6783 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.6443358534434449,
            "unit": "iter/sec",
            "range": "stddev: 0.065580",
            "group": "engine",
            "extra": "mean: 1.5520 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.14713564179084646,
            "unit": "iter/sec",
            "range": "stddev: 0.15764",
            "group": "engine",
            "extra": "mean: 6.7964 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.1535147065232323,
            "unit": "iter/sec",
            "range": "stddev: 0.17154",
            "group": "engine",
            "extra": "mean: 6.5140 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 1.5480640933409553,
            "unit": "iter/sec",
            "range": "stddev: 0.065208",
            "group": "engine",
            "extra": "mean: 645.97 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.3630682675231692,
            "unit": "iter/sec",
            "range": "stddev: 0.066584",
            "group": "engine",
            "extra": "mean: 2.7543 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.40063921502785665,
            "unit": "iter/sec",
            "range": "stddev: 0.071575",
            "group": "engine",
            "extra": "mean: 2.4960 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.11293699457896515,
            "unit": "iter/sec",
            "range": "stddev: 0.097897",
            "group": "engine",
            "extra": "mean: 8.8545 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.12473254936416908,
            "unit": "iter/sec",
            "range": "stddev: 0.13066",
            "group": "engine",
            "extra": "mean: 8.0172 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.6812805118076177,
            "unit": "iter/sec",
            "range": "stddev: 0.0063126",
            "group": "import-export",
            "extra": "mean: 372.96 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.263001613125996,
            "unit": "iter/sec",
            "range": "stddev: 0.051210",
            "group": "import-export",
            "extra": "mean: 441.89 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 0.13890092561225278,
            "unit": "iter/sec",
            "range": "stddev: 0.033243",
            "group": "import-export",
            "extra": "mean: 7.1994 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 0.1400248097136394,
            "unit": "iter/sec",
            "range": "stddev: 0.15368",
            "group": "import-export",
            "extra": "mean: 7.1416 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 97.07329980804249,
            "unit": "iter/sec",
            "range": "stddev: 0.00053876",
            "group": "node",
            "extra": "mean: 10.301 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 42.72007159550797,
            "unit": "iter/sec",
            "range": "stddev: 0.0022039",
            "group": "node",
            "extra": "mean: 23.408 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 43.738579927836504,
            "unit": "iter/sec",
            "range": "stddev: 0.00044868",
            "group": "node",
            "extra": "mean: 22.863 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 51.30087136187089,
            "unit": "iter/sec",
            "range": "stddev: 0.00096331",
            "group": "node",
            "extra": "mean: 19.493 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 26.725697882145166,
            "unit": "iter/sec",
            "range": "stddev: 0.0025900",
            "group": "node",
            "extra": "mean: 37.417 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 26.688095834079625,
            "unit": "iter/sec",
            "range": "stddev: 0.0023658",
            "group": "node",
            "extra": "mean: 37.470 msec\nrounds: 100"
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
          "pythonVersion": "3.8.6",
          "metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "0fb6f72333b0e553590326fc348acbee3ef0763b",
          "message": "Docs: Add docs live build to tox configuration (#4460)\n\nAdd docs live build using sphinx-autobuild. This dramatically speeds up the process of checking the rendered documentation while editing.\r\n\r\nCo-authored-by: Leopold Talirz <leopold.talirz@gmail.com>",
          "timestamp": "2020-10-19T12:44:28+02:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/0fb6f72333b0e553590326fc348acbee3ef0763b",
          "distinct": true,
          "tree_id": "e21a7951dbbbbaec12706dae8468366d5a22c251"
        },
        "date": 1603105153280,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 2.964204967479205,
            "unit": "iter/sec",
            "range": "stddev: 0.0065143",
            "group": "engine",
            "extra": "mean: 337.36 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.6304737737370346,
            "unit": "iter/sec",
            "range": "stddev: 0.055275",
            "group": "engine",
            "extra": "mean: 1.5861 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.6911309107873291,
            "unit": "iter/sec",
            "range": "stddev: 0.050518",
            "group": "engine",
            "extra": "mean: 1.4469 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.15369195725200044,
            "unit": "iter/sec",
            "range": "stddev: 0.17388",
            "group": "engine",
            "extra": "mean: 6.5065 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.16036281104064362,
            "unit": "iter/sec",
            "range": "stddev: 0.17865",
            "group": "engine",
            "extra": "mean: 6.2359 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 1.7137322128597237,
            "unit": "iter/sec",
            "range": "stddev: 0.017681",
            "group": "engine",
            "extra": "mean: 583.52 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.38691789801037413,
            "unit": "iter/sec",
            "range": "stddev: 0.091392",
            "group": "engine",
            "extra": "mean: 2.5845 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.42988633612468824,
            "unit": "iter/sec",
            "range": "stddev: 0.095232",
            "group": "engine",
            "extra": "mean: 2.3262 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.11730918188026015,
            "unit": "iter/sec",
            "range": "stddev: 0.25470",
            "group": "engine",
            "extra": "mean: 8.5245 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.12920430946051611,
            "unit": "iter/sec",
            "range": "stddev: 0.23484",
            "group": "engine",
            "extra": "mean: 7.7397 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.941369318439809,
            "unit": "iter/sec",
            "range": "stddev: 0.056632",
            "group": "import-export",
            "extra": "mean: 339.98 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.5481228490506616,
            "unit": "iter/sec",
            "range": "stddev: 0.055161",
            "group": "import-export",
            "extra": "mean: 392.45 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 0.15123556906502617,
            "unit": "iter/sec",
            "range": "stddev: 0.17904",
            "group": "import-export",
            "extra": "mean: 6.6122 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 0.15386434425310064,
            "unit": "iter/sec",
            "range": "stddev: 0.13055",
            "group": "import-export",
            "extra": "mean: 6.4992 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 84.23257148712081,
            "unit": "iter/sec",
            "range": "stddev: 0.0014863",
            "group": "node",
            "extra": "mean: 11.872 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 42.23755989198148,
            "unit": "iter/sec",
            "range": "stddev: 0.0014824",
            "group": "node",
            "extra": "mean: 23.676 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 43.2695772295701,
            "unit": "iter/sec",
            "range": "stddev: 0.0021420",
            "group": "node",
            "extra": "mean: 23.111 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 51.101866023843904,
            "unit": "iter/sec",
            "range": "stddev: 0.0018345",
            "group": "node",
            "extra": "mean: 19.569 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 25.943925548584854,
            "unit": "iter/sec",
            "range": "stddev: 0.018928",
            "group": "node",
            "extra": "mean: 38.545 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 27.636865568466067,
            "unit": "iter/sec",
            "range": "stddev: 0.0046176",
            "group": "node",
            "extra": "mean: 36.184 msec\nrounds: 100"
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
          "pythonVersion": "3.8.6",
          "metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "4791046a58a1dfd0948f02cea6cf4b13eb1be4a5",
          "message": "Docs: Add redirects from old documenation (#4457)\n\nUses the `sphinxext-rediraffe` Sphinx extension to automatically create\r\nredirects when documentation pages are moved and therefore their URLs\r\nchange. New redirect rules should be added to `docs/source/redirects.txt`",
          "timestamp": "2020-10-19T17:09:01+02:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/4791046a58a1dfd0948f02cea6cf4b13eb1be4a5",
          "distinct": true,
          "tree_id": "e9bff4879dfc7c948832867f69c6174ee69da38f"
        },
        "date": 1603121093576,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 2.5820342437396007,
            "unit": "iter/sec",
            "range": "stddev: 0.043481",
            "group": "engine",
            "extra": "mean: 387.29 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.5997342702553068,
            "unit": "iter/sec",
            "range": "stddev: 0.054342",
            "group": "engine",
            "extra": "mean: 1.6674 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.6413777263975065,
            "unit": "iter/sec",
            "range": "stddev: 0.051480",
            "group": "engine",
            "extra": "mean: 1.5591 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.1442161750731688,
            "unit": "iter/sec",
            "range": "stddev: 0.13172",
            "group": "engine",
            "extra": "mean: 6.9340 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.15015090863769054,
            "unit": "iter/sec",
            "range": "stddev: 0.17793",
            "group": "engine",
            "extra": "mean: 6.6600 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 1.5582386344072219,
            "unit": "iter/sec",
            "range": "stddev: 0.057460",
            "group": "engine",
            "extra": "mean: 641.75 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.36126191069157826,
            "unit": "iter/sec",
            "range": "stddev: 0.081663",
            "group": "engine",
            "extra": "mean: 2.7681 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.39255125390982565,
            "unit": "iter/sec",
            "range": "stddev: 0.10821",
            "group": "engine",
            "extra": "mean: 2.5474 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.11055167037996742,
            "unit": "iter/sec",
            "range": "stddev: 0.12894",
            "group": "engine",
            "extra": "mean: 9.0455 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.11974410439128792,
            "unit": "iter/sec",
            "range": "stddev: 0.19404",
            "group": "engine",
            "extra": "mean: 8.3511 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.773780637883507,
            "unit": "iter/sec",
            "range": "stddev: 0.056643",
            "group": "import-export",
            "extra": "mean: 360.52 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.5075806990785336,
            "unit": "iter/sec",
            "range": "stddev: 0.0084038",
            "group": "import-export",
            "extra": "mean: 398.79 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 0.14394341118244924,
            "unit": "iter/sec",
            "range": "stddev: 0.11538",
            "group": "import-export",
            "extra": "mean: 6.9472 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 0.14446705064679055,
            "unit": "iter/sec",
            "range": "stddev: 0.14212",
            "group": "import-export",
            "extra": "mean: 6.9220 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 89.89847537737737,
            "unit": "iter/sec",
            "range": "stddev: 0.0011777",
            "group": "node",
            "extra": "mean: 11.124 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 42.32134989401015,
            "unit": "iter/sec",
            "range": "stddev: 0.0016283",
            "group": "node",
            "extra": "mean: 23.629 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 41.688278478178745,
            "unit": "iter/sec",
            "range": "stddev: 0.0017811",
            "group": "node",
            "extra": "mean: 23.988 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 51.70851647618839,
            "unit": "iter/sec",
            "range": "stddev: 0.00098031",
            "group": "node",
            "extra": "mean: 19.339 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 26.58289648120098,
            "unit": "iter/sec",
            "range": "stddev: 0.0032752",
            "group": "node",
            "extra": "mean: 37.618 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 25.20423353373175,
            "unit": "iter/sec",
            "range": "stddev: 0.0034969",
            "group": "node",
            "extra": "mean: 39.676 msec\nrounds: 100"
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
          "pythonVersion": "3.8.6",
          "metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "eed191785da51b3c8ae105ee2073e3330deb0790",
          "message": "Docs: ⬆️ Update sphinx + extensions versions (#4470)\n\nThis commit primarily upgrades the sphinx dependency from sphinx v2 to v3, allowing for other upgrades of sphinx version pinning.\r\n\r\nIt also moved the `aiida/sphinxext` testing to the official sphinx testing infrastructure, and fixes an issue with the automodule writer. However, the automodule functionality cannot yet be re-instated, due to issues with referencing of these objects.",
          "timestamp": "2020-10-20T10:37:39+02:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/eed191785da51b3c8ae105ee2073e3330deb0790",
          "distinct": true,
          "tree_id": "0abf7ed2497d25d33c40df6f8bcd893107265ac3"
        },
        "date": 1603184052172,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 2.5176589036089023,
            "unit": "iter/sec",
            "range": "stddev: 0.025575",
            "group": "engine",
            "extra": "mean: 397.19 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.5595057200244812,
            "unit": "iter/sec",
            "range": "stddev: 0.057990",
            "group": "engine",
            "extra": "mean: 1.7873 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.5607058708938927,
            "unit": "iter/sec",
            "range": "stddev: 0.078436",
            "group": "engine",
            "extra": "mean: 1.7835 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.13615476936199483,
            "unit": "iter/sec",
            "range": "stddev: 0.26767",
            "group": "engine",
            "extra": "mean: 7.3446 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.13735413895640958,
            "unit": "iter/sec",
            "range": "stddev: 0.14415",
            "group": "engine",
            "extra": "mean: 7.2805 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 1.4153414305304446,
            "unit": "iter/sec",
            "range": "stddev: 0.063671",
            "group": "engine",
            "extra": "mean: 706.54 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.3315810931900563,
            "unit": "iter/sec",
            "range": "stddev: 0.090978",
            "group": "engine",
            "extra": "mean: 3.0159 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.37469637239627956,
            "unit": "iter/sec",
            "range": "stddev: 0.093760",
            "group": "engine",
            "extra": "mean: 2.6688 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.104198020177642,
            "unit": "iter/sec",
            "range": "stddev: 0.18858",
            "group": "engine",
            "extra": "mean: 9.5971 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.11511830309890092,
            "unit": "iter/sec",
            "range": "stddev: 0.17959",
            "group": "engine",
            "extra": "mean: 8.6867 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.4726913820764844,
            "unit": "iter/sec",
            "range": "stddev: 0.063873",
            "group": "import-export",
            "extra": "mean: 404.42 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.234076235693405,
            "unit": "iter/sec",
            "range": "stddev: 0.063064",
            "group": "import-export",
            "extra": "mean: 447.61 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 0.12983360272883018,
            "unit": "iter/sec",
            "range": "stddev: 0.11455",
            "group": "import-export",
            "extra": "mean: 7.7022 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 0.13650943906902963,
            "unit": "iter/sec",
            "range": "stddev: 0.16918",
            "group": "import-export",
            "extra": "mean: 7.3255 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 98.54669949919055,
            "unit": "iter/sec",
            "range": "stddev: 0.00079585",
            "group": "node",
            "extra": "mean: 10.147 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 43.21948120051019,
            "unit": "iter/sec",
            "range": "stddev: 0.0017169",
            "group": "node",
            "extra": "mean: 23.138 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 43.18862454609874,
            "unit": "iter/sec",
            "range": "stddev: 0.0011451",
            "group": "node",
            "extra": "mean: 23.154 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 50.78326861706755,
            "unit": "iter/sec",
            "range": "stddev: 0.0013233",
            "group": "node",
            "extra": "mean: 19.692 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 25.161797788804922,
            "unit": "iter/sec",
            "range": "stddev: 0.017647",
            "group": "node",
            "extra": "mean: 39.743 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 26.979501002660026,
            "unit": "iter/sec",
            "range": "stddev: 0.0023669",
            "group": "node",
            "extra": "mean: 37.065 msec\nrounds: 100"
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
          "pythonVersion": "3.8.6",
          "metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "db659ddf8a36db77963e2955df5066876c0d8017",
          "message": "REST API: list endpoints at base URL (#4412)\n\nThe base URL of the REST API was returning a 404 invalid URL response\r\nwithout providing any guidance to new users as to how to use the API.\r\nWe change this to return the list of endpoints formerly available only\r\nunder /server/endpoints.\r\n\r\nDocumentation of where to find the list of endpoints -- which seems\r\nto have been entirely deleted -- is added.\r\n\r\nCo-authored-by: Giovanni Pizzi <gio.piz@gmail.com>",
          "timestamp": "2020-10-20T11:14:33+02:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/db659ddf8a36db77963e2955df5066876c0d8017",
          "distinct": true,
          "tree_id": "f834d0346aa4f27cdf42c54cc1794dc566ff1ccb"
        },
        "date": 1603186129289,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 2.985943937648448,
            "unit": "iter/sec",
            "range": "stddev: 0.019046",
            "group": "engine",
            "extra": "mean: 334.90 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.6804903400124463,
            "unit": "iter/sec",
            "range": "stddev: 0.058305",
            "group": "engine",
            "extra": "mean: 1.4695 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.7354122704965202,
            "unit": "iter/sec",
            "range": "stddev: 0.071261",
            "group": "engine",
            "extra": "mean: 1.3598 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.1628808540866488,
            "unit": "iter/sec",
            "range": "stddev: 0.19538",
            "group": "engine",
            "extra": "mean: 6.1395 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.1641694182756195,
            "unit": "iter/sec",
            "range": "stddev: 0.26002",
            "group": "engine",
            "extra": "mean: 6.0913 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 1.721858084057242,
            "unit": "iter/sec",
            "range": "stddev: 0.044585",
            "group": "engine",
            "extra": "mean: 580.77 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.3982918217594,
            "unit": "iter/sec",
            "range": "stddev: 0.17447",
            "group": "engine",
            "extra": "mean: 2.5107 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.45343015396214864,
            "unit": "iter/sec",
            "range": "stddev: 0.13045",
            "group": "engine",
            "extra": "mean: 2.2054 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.12027672363612112,
            "unit": "iter/sec",
            "range": "stddev: 0.11140",
            "group": "engine",
            "extra": "mean: 8.3142 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.13659305477399275,
            "unit": "iter/sec",
            "range": "stddev: 0.33771",
            "group": "engine",
            "extra": "mean: 7.3210 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 3.108412139134065,
            "unit": "iter/sec",
            "range": "stddev: 0.058351",
            "group": "import-export",
            "extra": "mean: 321.71 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.9113930481495593,
            "unit": "iter/sec",
            "range": "stddev: 0.049973",
            "group": "import-export",
            "extra": "mean: 343.48 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 0.16034720439187553,
            "unit": "iter/sec",
            "range": "stddev: 0.27335",
            "group": "import-export",
            "extra": "mean: 6.2365 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 0.1562781669114008,
            "unit": "iter/sec",
            "range": "stddev: 0.19972",
            "group": "import-export",
            "extra": "mean: 6.3988 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 103.83310142224224,
            "unit": "iter/sec",
            "range": "stddev: 0.00055084",
            "group": "node",
            "extra": "mean: 9.6308 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 48.0237035780377,
            "unit": "iter/sec",
            "range": "stddev: 0.00093010",
            "group": "node",
            "extra": "mean: 20.823 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 47.52150730397157,
            "unit": "iter/sec",
            "range": "stddev: 0.0010040",
            "group": "node",
            "extra": "mean: 21.043 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 56.158844500961045,
            "unit": "iter/sec",
            "range": "stddev: 0.0015593",
            "group": "node",
            "extra": "mean: 17.807 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 29.862908343687,
            "unit": "iter/sec",
            "range": "stddev: 0.0021208",
            "group": "node",
            "extra": "mean: 33.486 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 27.947605790590384,
            "unit": "iter/sec",
            "range": "stddev: 0.0030657",
            "group": "node",
            "extra": "mean: 35.781 msec\nrounds: 100"
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
          "pythonVersion": "3.8.6",
          "metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "cb268d1dd90a2aaeb94e7fd0ddc4091a6bf9ebc9",
          "message": "replace all occurences of \"export file\"\n\nWe have agreed on the terms \"AiiDA archive (file)\" and \"AiiDA archive\nformat\".\n\nCo-authored-by: Casper Welzel Andersen <43357585+CasperWA@users.noreply.github.com>",
          "timestamp": "2020-10-20T14:46:44+02:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/cb268d1dd90a2aaeb94e7fd0ddc4091a6bf9ebc9",
          "distinct": true,
          "tree_id": "93ce3e19dd46ee92093c0764895ade003ccb554e"
        },
        "date": 1603198929399,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 2.809423179784874,
            "unit": "iter/sec",
            "range": "stddev: 0.022655",
            "group": "engine",
            "extra": "mean: 355.94 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.5962091814114736,
            "unit": "iter/sec",
            "range": "stddev: 0.066056",
            "group": "engine",
            "extra": "mean: 1.6773 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.6504182149772009,
            "unit": "iter/sec",
            "range": "stddev: 0.066720",
            "group": "engine",
            "extra": "mean: 1.5375 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.14599954842818552,
            "unit": "iter/sec",
            "range": "stddev: 0.19954",
            "group": "engine",
            "extra": "mean: 6.8493 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.15137757919732028,
            "unit": "iter/sec",
            "range": "stddev: 0.30795",
            "group": "engine",
            "extra": "mean: 6.6060 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 1.5795355909667446,
            "unit": "iter/sec",
            "range": "stddev: 0.061837",
            "group": "engine",
            "extra": "mean: 633.10 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.34366928436483674,
            "unit": "iter/sec",
            "range": "stddev: 0.15185",
            "group": "engine",
            "extra": "mean: 2.9098 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.37359601493995626,
            "unit": "iter/sec",
            "range": "stddev: 0.10347",
            "group": "engine",
            "extra": "mean: 2.6767 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.1051196679380109,
            "unit": "iter/sec",
            "range": "stddev: 0.14066",
            "group": "engine",
            "extra": "mean: 9.5130 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.11810784602874805,
            "unit": "iter/sec",
            "range": "stddev: 0.32144",
            "group": "engine",
            "extra": "mean: 8.4668 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.8256551374978356,
            "unit": "iter/sec",
            "range": "stddev: 0.050393",
            "group": "import-export",
            "extra": "mean: 353.90 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.5452044585235836,
            "unit": "iter/sec",
            "range": "stddev: 0.066944",
            "group": "import-export",
            "extra": "mean: 392.90 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 0.14419293029357796,
            "unit": "iter/sec",
            "range": "stddev: 0.14410",
            "group": "import-export",
            "extra": "mean: 6.9352 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 0.15358337249104395,
            "unit": "iter/sec",
            "range": "stddev: 0.10413",
            "group": "import-export",
            "extra": "mean: 6.5111 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 97.22974233505353,
            "unit": "iter/sec",
            "range": "stddev: 0.00084464",
            "group": "node",
            "extra": "mean: 10.285 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 40.71922880382838,
            "unit": "iter/sec",
            "range": "stddev: 0.0061690",
            "group": "node",
            "extra": "mean: 24.558 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 43.765988199640724,
            "unit": "iter/sec",
            "range": "stddev: 0.0037281",
            "group": "node",
            "extra": "mean: 22.849 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 53.14615049377766,
            "unit": "iter/sec",
            "range": "stddev: 0.0018129",
            "group": "node",
            "extra": "mean: 18.816 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 27.072652363175564,
            "unit": "iter/sec",
            "range": "stddev: 0.0031784",
            "group": "node",
            "extra": "mean: 36.938 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 26.74274492663476,
            "unit": "iter/sec",
            "range": "stddev: 0.019137",
            "group": "node",
            "extra": "mean: 37.393 msec\nrounds: 100"
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
          "pythonVersion": "3.8.6",
          "metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "09ac91654648adb684a58d5d2d7b1c11a503dae8",
          "message": "Docs: update REST API wsgi scripts (#4488)\n\nThe wsgi scripts for deploying the AiiDA REST in production were\r\noutdated and are updated.\r\nThe how-to on deploying your own REST API server is significantly\r\nstreamlined and now includes the wsgi files as well as the examplary\r\napache virtualhost configuration.\r\n\r\nCo-authored-by: Giovanni Pizzi <gio.piz@gmail.com>",
          "timestamp": "2020-10-20T22:08:45+02:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/09ac91654648adb684a58d5d2d7b1c11a503dae8",
          "distinct": true,
          "tree_id": "8e9ea5e84fc510fdf0655ace8e2a15bb5d6926d6"
        },
        "date": 1603225473474,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 2.7701240734722163,
            "unit": "iter/sec",
            "range": "stddev: 0.0091664",
            "group": "engine",
            "extra": "mean: 360.99 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.6021502339383186,
            "unit": "iter/sec",
            "range": "stddev: 0.073406",
            "group": "engine",
            "extra": "mean: 1.6607 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.6420081627867193,
            "unit": "iter/sec",
            "range": "stddev: 0.053108",
            "group": "engine",
            "extra": "mean: 1.5576 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.14321593376911684,
            "unit": "iter/sec",
            "range": "stddev: 0.16502",
            "group": "engine",
            "extra": "mean: 6.9825 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.1504084547535608,
            "unit": "iter/sec",
            "range": "stddev: 0.22455",
            "group": "engine",
            "extra": "mean: 6.6486 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 1.5457984732906334,
            "unit": "iter/sec",
            "range": "stddev: 0.070877",
            "group": "engine",
            "extra": "mean: 646.91 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.3624616010717054,
            "unit": "iter/sec",
            "range": "stddev: 0.089960",
            "group": "engine",
            "extra": "mean: 2.7589 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.40185851713466797,
            "unit": "iter/sec",
            "range": "stddev: 0.13026",
            "group": "engine",
            "extra": "mean: 2.4884 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.10991775510660319,
            "unit": "iter/sec",
            "range": "stddev: 0.15161",
            "group": "engine",
            "extra": "mean: 9.0977 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.12307872711112919,
            "unit": "iter/sec",
            "range": "stddev: 0.17954",
            "group": "engine",
            "extra": "mean: 8.1249 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.726658576553969,
            "unit": "iter/sec",
            "range": "stddev: 0.061112",
            "group": "import-export",
            "extra": "mean: 366.75 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.4410278315873466,
            "unit": "iter/sec",
            "range": "stddev: 0.058267",
            "group": "import-export",
            "extra": "mean: 409.66 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 0.14511129335633327,
            "unit": "iter/sec",
            "range": "stddev: 0.083659",
            "group": "import-export",
            "extra": "mean: 6.8913 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 0.15083373775023778,
            "unit": "iter/sec",
            "range": "stddev: 0.090036",
            "group": "import-export",
            "extra": "mean: 6.6298 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 99.75405338872632,
            "unit": "iter/sec",
            "range": "stddev: 0.00051701",
            "group": "node",
            "extra": "mean: 10.025 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 45.434636306688866,
            "unit": "iter/sec",
            "range": "stddev: 0.0015167",
            "group": "node",
            "extra": "mean: 22.010 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 43.82035942338156,
            "unit": "iter/sec",
            "range": "stddev: 0.0015762",
            "group": "node",
            "extra": "mean: 22.820 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 54.00103254186413,
            "unit": "iter/sec",
            "range": "stddev: 0.00050992",
            "group": "node",
            "extra": "mean: 18.518 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 27.106980928132717,
            "unit": "iter/sec",
            "range": "stddev: 0.019036",
            "group": "node",
            "extra": "mean: 36.891 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 28.11497028482641,
            "unit": "iter/sec",
            "range": "stddev: 0.0025185",
            "group": "node",
            "extra": "mean: 35.568 msec\nrounds: 100"
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
          "pythonVersion": "3.8.6",
          "metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "2eda24edd9eae3e34d57a4c039d3574a0ba064c6",
          "message": "Docs: serve a custom 404 page (#4478)\n\nRedirect to a helpful page when a document is not found.",
          "timestamp": "2020-10-21T16:34:13+02:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/2eda24edd9eae3e34d57a4c039d3574a0ba064c6",
          "distinct": true,
          "tree_id": "6cddcc1c30da8e88445ef06c8fa5d65367384efa"
        },
        "date": 1603291785580,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 2.6748760338331796,
            "unit": "iter/sec",
            "range": "stddev: 0.012310",
            "group": "engine",
            "extra": "mean: 373.85 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.5973190843162027,
            "unit": "iter/sec",
            "range": "stddev: 0.052239",
            "group": "engine",
            "extra": "mean: 1.6741 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.6402704622086125,
            "unit": "iter/sec",
            "range": "stddev: 0.043714",
            "group": "engine",
            "extra": "mean: 1.5618 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.14362355936525578,
            "unit": "iter/sec",
            "range": "stddev: 0.14433",
            "group": "engine",
            "extra": "mean: 6.9626 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.15238886033294521,
            "unit": "iter/sec",
            "range": "stddev: 0.16253",
            "group": "engine",
            "extra": "mean: 6.5622 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 1.495174612208777,
            "unit": "iter/sec",
            "range": "stddev: 0.062457",
            "group": "engine",
            "extra": "mean: 668.82 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.3541788290879675,
            "unit": "iter/sec",
            "range": "stddev: 0.072362",
            "group": "engine",
            "extra": "mean: 2.8234 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.39737216787187346,
            "unit": "iter/sec",
            "range": "stddev: 0.098701",
            "group": "engine",
            "extra": "mean: 2.5165 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.11107432869906339,
            "unit": "iter/sec",
            "range": "stddev: 0.14560",
            "group": "engine",
            "extra": "mean: 9.0030 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.12092447139730618,
            "unit": "iter/sec",
            "range": "stddev: 0.11987",
            "group": "engine",
            "extra": "mean: 8.2696 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.818638124902657,
            "unit": "iter/sec",
            "range": "stddev: 0.053616",
            "group": "import-export",
            "extra": "mean: 354.78 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.512678565111862,
            "unit": "iter/sec",
            "range": "stddev: 0.051775",
            "group": "import-export",
            "extra": "mean: 397.98 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 0.14545413170365648,
            "unit": "iter/sec",
            "range": "stddev: 0.033514",
            "group": "import-export",
            "extra": "mean: 6.8750 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 0.14588062698011064,
            "unit": "iter/sec",
            "range": "stddev: 0.057725",
            "group": "import-export",
            "extra": "mean: 6.8549 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 95.4777815697155,
            "unit": "iter/sec",
            "range": "stddev: 0.00031925",
            "group": "node",
            "extra": "mean: 10.474 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 45.182014627680644,
            "unit": "iter/sec",
            "range": "stddev: 0.00068504",
            "group": "node",
            "extra": "mean: 22.133 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 43.32013394266475,
            "unit": "iter/sec",
            "range": "stddev: 0.0019829",
            "group": "node",
            "extra": "mean: 23.084 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 52.68114891398542,
            "unit": "iter/sec",
            "range": "stddev: 0.00080913",
            "group": "node",
            "extra": "mean: 18.982 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 25.791664748979915,
            "unit": "iter/sec",
            "range": "stddev: 0.018718",
            "group": "node",
            "extra": "mean: 38.772 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 26.92077702829253,
            "unit": "iter/sec",
            "range": "stddev: 0.0025870",
            "group": "node",
            "extra": "mean: 37.146 msec\nrounds: 100"
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
          "pythonVersion": "3.8.6",
          "metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "c6d38c1657b65f540bea653f253920bb602c7ebc",
          "message": "Refactor the archive exporter (#4448)\n\nThis commit refactors the export process (in a back-compatible manner),\r\nsuch that the extraction of data from the database is fully decoupled\r\nfrom the writing of that data to an archive.\r\n\r\nIt allows for pluggable export writers, and is intended as a\r\npreliminary step toward the creation of a new archive format.\r\n\r\nThe original `export_tree` function is renamed to `_collect_archive_data`\r\nand its contents split into a number of separate, self-contained, functions.\r\n\r\nThe process control has then been inverted,\r\nsuch that the export data is parsed to the archive writer,\r\nrather than the export writer calling `export_tree` to generate that data.\r\n\r\nAn abstract writer class is provided,\r\nthen each concrete writer is identified and called for via a string\r\n(this could in fact be made into an entry point).\r\n\r\nData is parsed to the writers contained in a\r\n[dataclasses](https://pypi.org/project/dataclasses/) container.\r\nThis requires a backport for python 3.6,\r\nbut is included in python core from python 3.7 onwards.\r\n\r\nThe `extract_tree`, `extract_zip` and `extract_tar` functions are\r\nreimplemented, for backwards compatibility,\r\nbut are marked as deprecated and to be remove in v2.0.0.\r\n\r\nAdditional issues addressed:\r\n\r\n- fixes a bug, whereby, in python 3.8,\r\n  `logging.disable(level=` has changed to `logging.disable(lvl=`.\r\n- fixes a bug, whereby the traversal rules summary was returning incorrect\r\n  rule summaries.\r\n- adds mypy compliant typing (and adds the file to the pre-commit mypy list)\r\n\r\nCo-authored-by: Leopold Talirz <leopold.talirz@gmail.com>",
          "timestamp": "2020-10-23T02:12:16+02:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/c6d38c1657b65f540bea653f253920bb602c7ebc",
          "distinct": true,
          "tree_id": "31f1052077184e8d1dec6af13eebd5ffc500b960"
        },
        "date": 1603412862172,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 2.649632855345609,
            "unit": "iter/sec",
            "range": "stddev: 0.0086468",
            "group": "engine",
            "extra": "mean: 377.41 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.5857432376946425,
            "unit": "iter/sec",
            "range": "stddev: 0.053616",
            "group": "engine",
            "extra": "mean: 1.7072 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.6370407902746886,
            "unit": "iter/sec",
            "range": "stddev: 0.045909",
            "group": "engine",
            "extra": "mean: 1.5698 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.14612333735729632,
            "unit": "iter/sec",
            "range": "stddev: 0.18223",
            "group": "engine",
            "extra": "mean: 6.8435 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.15389263552570176,
            "unit": "iter/sec",
            "range": "stddev: 0.13763",
            "group": "engine",
            "extra": "mean: 6.4980 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 1.5601205925603239,
            "unit": "iter/sec",
            "range": "stddev: 0.050674",
            "group": "engine",
            "extra": "mean: 640.98 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.359595239048027,
            "unit": "iter/sec",
            "range": "stddev: 0.065050",
            "group": "engine",
            "extra": "mean: 2.7809 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.4077314552780749,
            "unit": "iter/sec",
            "range": "stddev: 0.056930",
            "group": "engine",
            "extra": "mean: 2.4526 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.11205535469368434,
            "unit": "iter/sec",
            "range": "stddev: 0.16431",
            "group": "engine",
            "extra": "mean: 8.9242 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.12374683647440077,
            "unit": "iter/sec",
            "range": "stddev: 0.15545",
            "group": "engine",
            "extra": "mean: 8.0810 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.5917756477098925,
            "unit": "iter/sec",
            "range": "stddev: 0.051880",
            "group": "import-export",
            "extra": "mean: 385.84 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.319752092114734,
            "unit": "iter/sec",
            "range": "stddev: 0.047446",
            "group": "import-export",
            "extra": "mean: 431.08 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 0.1396049570590494,
            "unit": "iter/sec",
            "range": "stddev: 0.058768",
            "group": "import-export",
            "extra": "mean: 7.1631 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 0.13945207386720535,
            "unit": "iter/sec",
            "range": "stddev: 0.10777",
            "group": "import-export",
            "extra": "mean: 7.1709 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 92.28280085357684,
            "unit": "iter/sec",
            "range": "stddev: 0.0010808",
            "group": "node",
            "extra": "mean: 10.836 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 42.5744424226609,
            "unit": "iter/sec",
            "range": "stddev: 0.0014617",
            "group": "node",
            "extra": "mean: 23.488 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 40.96502767493722,
            "unit": "iter/sec",
            "range": "stddev: 0.0016980",
            "group": "node",
            "extra": "mean: 24.411 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 48.728674676412105,
            "unit": "iter/sec",
            "range": "stddev: 0.0016236",
            "group": "node",
            "extra": "mean: 20.522 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 25.59276953567179,
            "unit": "iter/sec",
            "range": "stddev: 0.0025117",
            "group": "node",
            "extra": "mean: 39.074 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 24.878512018621215,
            "unit": "iter/sec",
            "range": "stddev: 0.017868",
            "group": "node",
            "extra": "mean: 40.195 msec\nrounds: 100"
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
          "pythonVersion": "3.8.6",
          "metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "1be12e1f97ce6373b1a85c7949fed869680df170",
          "message": "Pre-commit: reintroduce `pylint` rules (#4501)\n\nIn 65ad067b18cffeb639994efe9a372ec1475e1615 the following `pylint` rules\r\nwere accidentally disabled:\r\n\r\n * missing-class-docstring\r\n * missing-function-docstring\r\n * too-many-ancestors\r\n * too-many-locals\r\n\r\nThis commit reintroduces all but the \"too-many-ancestors\" rule, which\r\nis most likely never going to be addressed. Having to change the depth\r\nof the MRO is not trivial and usually not that effective.",
          "timestamp": "2020-10-23T15:32:51+02:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/1be12e1f97ce6373b1a85c7949fed869680df170",
          "distinct": true,
          "tree_id": "a58375e4e1ec24a2518317c566bab98f51f1f74d"
        },
        "date": 1603460951039,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 2.5164479061462446,
            "unit": "iter/sec",
            "range": "stddev: 0.0054284",
            "group": "engine",
            "extra": "mean: 397.39 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.5397376215157476,
            "unit": "iter/sec",
            "range": "stddev: 0.049700",
            "group": "engine",
            "extra": "mean: 1.8528 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.5899790959562476,
            "unit": "iter/sec",
            "range": "stddev: 0.064402",
            "group": "engine",
            "extra": "mean: 1.6950 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.1352658820893661,
            "unit": "iter/sec",
            "range": "stddev: 0.19967",
            "group": "engine",
            "extra": "mean: 7.3928 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.14346555246150783,
            "unit": "iter/sec",
            "range": "stddev: 0.16332",
            "group": "engine",
            "extra": "mean: 6.9703 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 1.4829871016026692,
            "unit": "iter/sec",
            "range": "stddev: 0.044214",
            "group": "engine",
            "extra": "mean: 674.31 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.34072979212434207,
            "unit": "iter/sec",
            "range": "stddev: 0.11936",
            "group": "engine",
            "extra": "mean: 2.9349 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.3796181991829455,
            "unit": "iter/sec",
            "range": "stddev: 0.078911",
            "group": "engine",
            "extra": "mean: 2.6342 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.10510266871619621,
            "unit": "iter/sec",
            "range": "stddev: 0.12525",
            "group": "engine",
            "extra": "mean: 9.5145 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.11625229456464099,
            "unit": "iter/sec",
            "range": "stddev: 0.14242",
            "group": "engine",
            "extra": "mean: 8.6020 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.50270130525285,
            "unit": "iter/sec",
            "range": "stddev: 0.050350",
            "group": "import-export",
            "extra": "mean: 399.57 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.2008022387062653,
            "unit": "iter/sec",
            "range": "stddev: 0.052368",
            "group": "import-export",
            "extra": "mean: 454.38 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 0.13301457448762244,
            "unit": "iter/sec",
            "range": "stddev: 0.080163",
            "group": "import-export",
            "extra": "mean: 7.5180 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 0.13539043961554587,
            "unit": "iter/sec",
            "range": "stddev: 0.12569",
            "group": "import-export",
            "extra": "mean: 7.3860 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 95.52539441210445,
            "unit": "iter/sec",
            "range": "stddev: 0.0013735",
            "group": "node",
            "extra": "mean: 10.468 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 44.347920800614226,
            "unit": "iter/sec",
            "range": "stddev: 0.00092288",
            "group": "node",
            "extra": "mean: 22.549 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 42.481961586657945,
            "unit": "iter/sec",
            "range": "stddev: 0.0036349",
            "group": "node",
            "extra": "mean: 23.539 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 51.259208785412675,
            "unit": "iter/sec",
            "range": "stddev: 0.0014104",
            "group": "node",
            "extra": "mean: 19.509 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 26.179582507161275,
            "unit": "iter/sec",
            "range": "stddev: 0.016234",
            "group": "node",
            "extra": "mean: 38.198 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 25.91188110574529,
            "unit": "iter/sec",
            "range": "stddev: 0.0040198",
            "group": "node",
            "extra": "mean: 38.592 msec\nrounds: 100"
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
          "pythonVersion": "3.8.6",
          "metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "33c9f41d029a22640646be295b9316c533685b19",
          "message": "Refactor archive progress bar (#4504)\n\nThis commit introduces a new generic progress reporter interface (in `aiida/common/progress_reporter.py`),\r\nthat can be used for adding progress reporting to any process.\r\nIt is intended to deprecate the existing `aiida/tools/importexport/common/progress_bar.py` module.\r\n\r\nThe reporter is designed to work similar to logging,\r\nsuch that its \"handler\" is set external to the actual function, e.g. by the CLI.\r\nIts default implementation is to do nothing (a null reporter),\r\nand there is convenience function to set a [tqdm](https://tqdm.github.io/) progress bar implementation (`set_progress_bar_tqdm`).\r\n\r\nThe reporter is intended to always be used as context manager,\r\ne.g. to allow the progress bar to be removed once the process is complete.\r\n\r\nThe reporter has been implemented in the archive export module,\r\nand it is intended that it will also be implemented in the archive import module.\r\nAt this point the existing `aiida/tools/importexport/common/progress_bar.py` module can be removed.",
          "timestamp": "2020-10-25T12:03:05+01:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/33c9f41d029a22640646be295b9316c533685b19",
          "distinct": true,
          "tree_id": "fb4fd93f189394c2b80a9ecc07f08f4394c14d35"
        },
        "date": 1603624738352,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 2.640753417449648,
            "unit": "iter/sec",
            "range": "stddev: 0.0089680",
            "group": "engine",
            "extra": "mean: 378.68 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.5906919241857518,
            "unit": "iter/sec",
            "range": "stddev: 0.053011",
            "group": "engine",
            "extra": "mean: 1.6929 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.6265055378375087,
            "unit": "iter/sec",
            "range": "stddev: 0.074974",
            "group": "engine",
            "extra": "mean: 1.5962 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.141786429694282,
            "unit": "iter/sec",
            "range": "stddev: 0.17820",
            "group": "engine",
            "extra": "mean: 7.0529 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.14749308478793638,
            "unit": "iter/sec",
            "range": "stddev: 0.18337",
            "group": "engine",
            "extra": "mean: 6.7800 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 1.5228725314945022,
            "unit": "iter/sec",
            "range": "stddev: 0.066505",
            "group": "engine",
            "extra": "mean: 656.65 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.35012949888245076,
            "unit": "iter/sec",
            "range": "stddev: 0.098818",
            "group": "engine",
            "extra": "mean: 2.8561 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.38549549340797423,
            "unit": "iter/sec",
            "range": "stddev: 0.086683",
            "group": "engine",
            "extra": "mean: 2.5941 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.10785838169051043,
            "unit": "iter/sec",
            "range": "stddev: 0.26575",
            "group": "engine",
            "extra": "mean: 9.2714 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.11604574332199756,
            "unit": "iter/sec",
            "range": "stddev: 0.19937",
            "group": "engine",
            "extra": "mean: 8.6173 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.6074206416187384,
            "unit": "iter/sec",
            "range": "stddev: 0.064226",
            "group": "import-export",
            "extra": "mean: 383.52 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.401336480147075,
            "unit": "iter/sec",
            "range": "stddev: 0.058382",
            "group": "import-export",
            "extra": "mean: 416.43 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 0.14026524452624187,
            "unit": "iter/sec",
            "range": "stddev: 0.053092",
            "group": "import-export",
            "extra": "mean: 7.1293 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 0.13949375181307885,
            "unit": "iter/sec",
            "range": "stddev: 0.086197",
            "group": "import-export",
            "extra": "mean: 7.1688 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 93.51593630364947,
            "unit": "iter/sec",
            "range": "stddev: 0.00045958",
            "group": "node",
            "extra": "mean: 10.693 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 42.6181923936814,
            "unit": "iter/sec",
            "range": "stddev: 0.00091962",
            "group": "node",
            "extra": "mean: 23.464 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 42.02853367247878,
            "unit": "iter/sec",
            "range": "stddev: 0.00091171",
            "group": "node",
            "extra": "mean: 23.793 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 48.539504013439874,
            "unit": "iter/sec",
            "range": "stddev: 0.0014487",
            "group": "node",
            "extra": "mean: 20.602 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 25.50208392535669,
            "unit": "iter/sec",
            "range": "stddev: 0.0019872",
            "group": "node",
            "extra": "mean: 39.212 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 24.220947179193676,
            "unit": "iter/sec",
            "range": "stddev: 0.019289",
            "group": "node",
            "extra": "mean: 41.287 msec\nrounds: 100"
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
          "pythonVersion": "3.8.6",
          "metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "e1421245cc8ac115d81dbd55e62af614a4233483",
          "message": "Fix `ZeroDivisionError` in worker slots check (#4513)\n\nThis was being raised if 0 slots were available",
          "timestamp": "2020-10-26T00:22:14+01:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/e1421245cc8ac115d81dbd55e62af614a4233483",
          "distinct": true,
          "tree_id": "67872a366fdb7d25fdc499885b0dc25e9efc6f75"
        },
        "date": 1603668879642,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.4933890180474347,
            "unit": "iter/sec",
            "range": "stddev: 0.022206",
            "group": "engine",
            "extra": "mean: 286.25 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.7756302949803566,
            "unit": "iter/sec",
            "range": "stddev: 0.052845",
            "group": "engine",
            "extra": "mean: 1.2893 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.8460694697542954,
            "unit": "iter/sec",
            "range": "stddev: 0.050558",
            "group": "engine",
            "extra": "mean: 1.1819 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.1853701142249545,
            "unit": "iter/sec",
            "range": "stddev: 0.15080",
            "group": "engine",
            "extra": "mean: 5.3946 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.19708845817238893,
            "unit": "iter/sec",
            "range": "stddev: 0.12713",
            "group": "engine",
            "extra": "mean: 5.0739 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.0449571473207526,
            "unit": "iter/sec",
            "range": "stddev: 0.054078",
            "group": "engine",
            "extra": "mean: 489.01 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.47874190419978435,
            "unit": "iter/sec",
            "range": "stddev: 0.060342",
            "group": "engine",
            "extra": "mean: 2.0888 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.518956426302197,
            "unit": "iter/sec",
            "range": "stddev: 0.099736",
            "group": "engine",
            "extra": "mean: 1.9269 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.14272562468669403,
            "unit": "iter/sec",
            "range": "stddev: 0.11418",
            "group": "engine",
            "extra": "mean: 7.0065 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.15943161703568282,
            "unit": "iter/sec",
            "range": "stddev: 0.16275",
            "group": "engine",
            "extra": "mean: 6.2723 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 3.3924908969609398,
            "unit": "iter/sec",
            "range": "stddev: 0.045520",
            "group": "import-export",
            "extra": "mean: 294.77 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.8278459735917623,
            "unit": "iter/sec",
            "range": "stddev: 0.050735",
            "group": "import-export",
            "extra": "mean: 353.63 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 0.1835871961292902,
            "unit": "iter/sec",
            "range": "stddev: 0.31069",
            "group": "import-export",
            "extra": "mean: 5.4470 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 0.18787268617094008,
            "unit": "iter/sec",
            "range": "stddev: 0.034790",
            "group": "import-export",
            "extra": "mean: 5.3228 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 117.24927644535927,
            "unit": "iter/sec",
            "range": "stddev: 0.00057575",
            "group": "node",
            "extra": "mean: 8.5288 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 54.229938923699514,
            "unit": "iter/sec",
            "range": "stddev: 0.00095724",
            "group": "node",
            "extra": "mean: 18.440 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 52.99837127469402,
            "unit": "iter/sec",
            "range": "stddev: 0.0010134",
            "group": "node",
            "extra": "mean: 18.869 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 64.05466357350078,
            "unit": "iter/sec",
            "range": "stddev: 0.00093591",
            "group": "node",
            "extra": "mean: 15.612 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 33.53607127015318,
            "unit": "iter/sec",
            "range": "stddev: 0.0054565",
            "group": "node",
            "extra": "mean: 29.819 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 34.451349301773824,
            "unit": "iter/sec",
            "range": "stddev: 0.0015953",
            "group": "node",
            "extra": "mean: 29.026 msec\nrounds: 100"
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
          "pythonVersion": "3.8.6",
          "metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "861a39f268954833385e699b3acbd092ccd04e5e",
          "message": "Fix `UnboundLocalError` in `aiida.cmdline.utils.edit_multiline_template` (#4436)\n\nIf `click.edit` returns a falsy value, the following conditional would\r\nbe skipped and the `value` variable would be undefined causing an\r\n`UnboundLocalError` to be raised. This bug was reported by @blokhin but\r\nthe exact conditions under which it occurred are not clear.",
          "timestamp": "2020-10-26T16:40:42+01:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/861a39f268954833385e699b3acbd092ccd04e5e",
          "distinct": true,
          "tree_id": "ef6a692a6eb97a9a9ef1631eae98fee3b083ec4a"
        },
        "date": 1603727821463,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 2.519862127185024,
            "unit": "iter/sec",
            "range": "stddev: 0.021526",
            "group": "engine",
            "extra": "mean: 396.85 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.5712206107639798,
            "unit": "iter/sec",
            "range": "stddev: 0.065395",
            "group": "engine",
            "extra": "mean: 1.7506 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.6054217401630568,
            "unit": "iter/sec",
            "range": "stddev: 0.063312",
            "group": "engine",
            "extra": "mean: 1.6517 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.1380325184215786,
            "unit": "iter/sec",
            "range": "stddev: 0.14586",
            "group": "engine",
            "extra": "mean: 7.2447 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.14354189803527914,
            "unit": "iter/sec",
            "range": "stddev: 0.17874",
            "group": "engine",
            "extra": "mean: 6.9666 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 1.4161378519271273,
            "unit": "iter/sec",
            "range": "stddev: 0.069940",
            "group": "engine",
            "extra": "mean: 706.15 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.3393077088712368,
            "unit": "iter/sec",
            "range": "stddev: 0.10364",
            "group": "engine",
            "extra": "mean: 2.9472 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.37669554182181236,
            "unit": "iter/sec",
            "range": "stddev: 0.091702",
            "group": "engine",
            "extra": "mean: 2.6547 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.1039761876575654,
            "unit": "iter/sec",
            "range": "stddev: 0.30853",
            "group": "engine",
            "extra": "mean: 9.6176 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.11426212263487617,
            "unit": "iter/sec",
            "range": "stddev: 0.21455",
            "group": "engine",
            "extra": "mean: 8.7518 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.647043490335292,
            "unit": "iter/sec",
            "range": "stddev: 0.060372",
            "group": "import-export",
            "extra": "mean: 377.78 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.3691213111183926,
            "unit": "iter/sec",
            "range": "stddev: 0.062760",
            "group": "import-export",
            "extra": "mean: 422.10 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 0.13722918879087206,
            "unit": "iter/sec",
            "range": "stddev: 0.10418",
            "group": "import-export",
            "extra": "mean: 7.2871 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 0.1400770916040949,
            "unit": "iter/sec",
            "range": "stddev: 0.20604",
            "group": "import-export",
            "extra": "mean: 7.1389 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 92.07482651547755,
            "unit": "iter/sec",
            "range": "stddev: 0.00053692",
            "group": "node",
            "extra": "mean: 10.861 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 40.583073345372945,
            "unit": "iter/sec",
            "range": "stddev: 0.0017985",
            "group": "node",
            "extra": "mean: 24.641 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 41.16454850200849,
            "unit": "iter/sec",
            "range": "stddev: 0.0011313",
            "group": "node",
            "extra": "mean: 24.293 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 47.49828506136119,
            "unit": "iter/sec",
            "range": "stddev: 0.00090726",
            "group": "node",
            "extra": "mean: 21.053 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 24.60611042245484,
            "unit": "iter/sec",
            "range": "stddev: 0.0028882",
            "group": "node",
            "extra": "mean: 40.640 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 24.200332612713844,
            "unit": "iter/sec",
            "range": "stddev: 0.019698",
            "group": "node",
            "extra": "mean: 41.322 msec\nrounds: 100"
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
          "pythonVersion": "3.8.6",
          "metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "7c49471b4ce5b6265ab488991567e08044d5baa3",
          "message": "`verdi migrate`: make `--in-place` work across different file systems (#4393)\n\nThe `verdi migrate` command assumed implicitly that the archive that is\r\nto be migrated, resides on the same file system as the one that is used\r\nby the `tempfile` module. If this is not the case, the `os.rename` call\r\nused to atomically move the migrated archive to the original will fail\r\nwith the exception:\r\n\r\n    OSError: [Errno 18] Invalid cross-device link\r\n\r\nChanging `os.rename` to `shutil.move` fixes this problem. The downside,\r\nhowever, is that the move is no longer atomic, but that is probably why\r\n`os.rename` is restricted to same filysystem operations.",
          "timestamp": "2020-10-26T20:08:41+01:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/7c49471b4ce5b6265ab488991567e08044d5baa3",
          "distinct": true,
          "tree_id": "bbb345572c784a08a95e5ba31fd1670c7bdc86d3"
        },
        "date": 1603740318574,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 2.499746571318009,
            "unit": "iter/sec",
            "range": "stddev: 0.0040077",
            "group": "engine",
            "extra": "mean: 400.04 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.5365380599132045,
            "unit": "iter/sec",
            "range": "stddev: 0.070617",
            "group": "engine",
            "extra": "mean: 1.8638 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.5710155973516836,
            "unit": "iter/sec",
            "range": "stddev: 0.051707",
            "group": "engine",
            "extra": "mean: 1.7513 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.13066427996669197,
            "unit": "iter/sec",
            "range": "stddev: 0.23614",
            "group": "engine",
            "extra": "mean: 7.6532 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.13576201677965577,
            "unit": "iter/sec",
            "range": "stddev: 0.19223",
            "group": "engine",
            "extra": "mean: 7.3658 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 1.4072772898611705,
            "unit": "iter/sec",
            "range": "stddev: 0.060929",
            "group": "engine",
            "extra": "mean: 710.59 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.31771546433067066,
            "unit": "iter/sec",
            "range": "stddev: 0.073642",
            "group": "engine",
            "extra": "mean: 3.1475 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.3446720402790519,
            "unit": "iter/sec",
            "range": "stddev: 0.093629",
            "group": "engine",
            "extra": "mean: 2.9013 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.09857501549877215,
            "unit": "iter/sec",
            "range": "stddev: 0.20861",
            "group": "engine",
            "extra": "mean: 10.145 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.1112166190935992,
            "unit": "iter/sec",
            "range": "stddev: 0.14355",
            "group": "engine",
            "extra": "mean: 8.9915 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.6275075817311015,
            "unit": "iter/sec",
            "range": "stddev: 0.060910",
            "group": "import-export",
            "extra": "mean: 380.59 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.357058573737017,
            "unit": "iter/sec",
            "range": "stddev: 0.058186",
            "group": "import-export",
            "extra": "mean: 424.26 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 0.1379969524371463,
            "unit": "iter/sec",
            "range": "stddev: 0.18103",
            "group": "import-export",
            "extra": "mean: 7.2465 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 0.14088967080067996,
            "unit": "iter/sec",
            "range": "stddev: 0.16548",
            "group": "import-export",
            "extra": "mean: 7.0978 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 89.82009880307946,
            "unit": "iter/sec",
            "range": "stddev: 0.00044874",
            "group": "node",
            "extra": "mean: 11.133 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 38.22063496069679,
            "unit": "iter/sec",
            "range": "stddev: 0.0019770",
            "group": "node",
            "extra": "mean: 26.164 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 39.83736378705663,
            "unit": "iter/sec",
            "range": "stddev: 0.0011978",
            "group": "node",
            "extra": "mean: 25.102 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 49.64329566956828,
            "unit": "iter/sec",
            "range": "stddev: 0.0010010",
            "group": "node",
            "extra": "mean: 20.144 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 25.517749693236233,
            "unit": "iter/sec",
            "range": "stddev: 0.0024289",
            "group": "node",
            "extra": "mean: 39.188 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 24.034125770619152,
            "unit": "iter/sec",
            "range": "stddev: 0.019685",
            "group": "node",
            "extra": "mean: 41.608 msec\nrounds: 100"
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
          "pythonVersion": "3.8.6",
          "metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "57c8afaa90ff7ac54e8eb2e2cded4b15d26eb8b0",
          "message": "Improve the deprecation warning for `Node.open` outside context manager (#4434)\n\nThe new warning now includes the offending line of code.",
          "timestamp": "2020-10-27T09:22:55+01:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/57c8afaa90ff7ac54e8eb2e2cded4b15d26eb8b0",
          "distinct": true,
          "tree_id": "bc508037eead843cfb6ed2736dc2386bb1327082"
        },
        "date": 1603787728954,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.3997438457560416,
            "unit": "iter/sec",
            "range": "stddev: 0.010161",
            "group": "engine",
            "extra": "mean: 294.14 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.7231310519181671,
            "unit": "iter/sec",
            "range": "stddev: 0.075734",
            "group": "engine",
            "extra": "mean: 1.3829 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.8278458985009716,
            "unit": "iter/sec",
            "range": "stddev: 0.056387",
            "group": "engine",
            "extra": "mean: 1.2080 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.18114409865600406,
            "unit": "iter/sec",
            "range": "stddev: 0.22956",
            "group": "engine",
            "extra": "mean: 5.5205 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.19275389710680654,
            "unit": "iter/sec",
            "range": "stddev: 0.16987",
            "group": "engine",
            "extra": "mean: 5.1880 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 1.9925519134762764,
            "unit": "iter/sec",
            "range": "stddev: 0.054219",
            "group": "engine",
            "extra": "mean: 501.87 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.4594314239556369,
            "unit": "iter/sec",
            "range": "stddev: 0.10723",
            "group": "engine",
            "extra": "mean: 2.1766 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.513371541586317,
            "unit": "iter/sec",
            "range": "stddev: 0.089865",
            "group": "engine",
            "extra": "mean: 1.9479 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.1408611825749571,
            "unit": "iter/sec",
            "range": "stddev: 0.15421",
            "group": "engine",
            "extra": "mean: 7.0992 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.15691486400706045,
            "unit": "iter/sec",
            "range": "stddev: 0.11007",
            "group": "engine",
            "extra": "mean: 6.3729 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 3.4661864863012575,
            "unit": "iter/sec",
            "range": "stddev: 0.046288",
            "group": "import-export",
            "extra": "mean: 288.50 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.8516196724590217,
            "unit": "iter/sec",
            "range": "stddev: 0.054475",
            "group": "import-export",
            "extra": "mean: 350.68 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 0.18634600783309246,
            "unit": "iter/sec",
            "range": "stddev: 0.10529",
            "group": "import-export",
            "extra": "mean: 5.3664 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 0.18427944339703173,
            "unit": "iter/sec",
            "range": "stddev: 0.096272",
            "group": "import-export",
            "extra": "mean: 5.4265 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 115.59971991985182,
            "unit": "iter/sec",
            "range": "stddev: 0.00054285",
            "group": "node",
            "extra": "mean: 8.6505 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 51.53235606537748,
            "unit": "iter/sec",
            "range": "stddev: 0.0024438",
            "group": "node",
            "extra": "mean: 19.405 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 52.06291295731955,
            "unit": "iter/sec",
            "range": "stddev: 0.0011174",
            "group": "node",
            "extra": "mean: 19.208 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 62.73049658379002,
            "unit": "iter/sec",
            "range": "stddev: 0.00097571",
            "group": "node",
            "extra": "mean: 15.941 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 31.639478950460166,
            "unit": "iter/sec",
            "range": "stddev: 0.0035847",
            "group": "node",
            "extra": "mean: 31.606 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 31.621472277164894,
            "unit": "iter/sec",
            "range": "stddev: 0.016856",
            "group": "node",
            "extra": "mean: 31.624 msec\nrounds: 100"
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
          "pythonVersion": "3.8.6",
          "metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "9460e4e456ada082354879a527e02b9e3c230528",
          "message": "Revert PR #4416 (#4519)\n\n\"`CalcJob`: support nested directories in target of `remote_copy/symlink_list` (#4416)\"\r\n\r\nThis reverts commit 16bc30548f7f1c686d200935174533535e850fd5.",
          "timestamp": "2020-10-27T16:02:28+01:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/9460e4e456ada082354879a527e02b9e3c230528",
          "distinct": true,
          "tree_id": "b73421c22b657e4c423ddbf911552cfd4149fa34"
        },
        "date": 1603812020315,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 2.213800832842326,
            "unit": "iter/sec",
            "range": "stddev: 0.046925",
            "group": "engine",
            "extra": "mean: 451.71 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.514063958588446,
            "unit": "iter/sec",
            "range": "stddev: 0.057656",
            "group": "engine",
            "extra": "mean: 1.9453 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.5334002463033068,
            "unit": "iter/sec",
            "range": "stddev: 0.075698",
            "group": "engine",
            "extra": "mean: 1.8748 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.1308291178484461,
            "unit": "iter/sec",
            "range": "stddev: 0.23939",
            "group": "engine",
            "extra": "mean: 7.6436 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.13255375556507457,
            "unit": "iter/sec",
            "range": "stddev: 0.15336",
            "group": "engine",
            "extra": "mean: 7.5441 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 1.369168021385187,
            "unit": "iter/sec",
            "range": "stddev: 0.022967",
            "group": "engine",
            "extra": "mean: 730.37 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.3014789470915667,
            "unit": "iter/sec",
            "range": "stddev: 0.12454",
            "group": "engine",
            "extra": "mean: 3.3170 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.338077817853911,
            "unit": "iter/sec",
            "range": "stddev: 0.088492",
            "group": "engine",
            "extra": "mean: 2.9579 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.09747553632697836,
            "unit": "iter/sec",
            "range": "stddev: 0.41431",
            "group": "engine",
            "extra": "mean: 10.259 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.10474393780242047,
            "unit": "iter/sec",
            "range": "stddev: 0.17721",
            "group": "engine",
            "extra": "mean: 9.5471 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.3579344883413507,
            "unit": "iter/sec",
            "range": "stddev: 0.0070140",
            "group": "import-export",
            "extra": "mean: 424.10 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.1038387723086234,
            "unit": "iter/sec",
            "range": "stddev: 0.010113",
            "group": "import-export",
            "extra": "mean: 475.32 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 0.12466198369823532,
            "unit": "iter/sec",
            "range": "stddev: 0.15988",
            "group": "import-export",
            "extra": "mean: 8.0217 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 0.13123887019800154,
            "unit": "iter/sec",
            "range": "stddev: 0.13358",
            "group": "import-export",
            "extra": "mean: 7.6197 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 80.01537927589249,
            "unit": "iter/sec",
            "range": "stddev: 0.0013704",
            "group": "node",
            "extra": "mean: 12.498 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 36.17736529277177,
            "unit": "iter/sec",
            "range": "stddev: 0.0035304",
            "group": "node",
            "extra": "mean: 27.642 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 35.86291458136002,
            "unit": "iter/sec",
            "range": "stddev: 0.0019192",
            "group": "node",
            "extra": "mean: 27.884 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 42.32302914956771,
            "unit": "iter/sec",
            "range": "stddev: 0.0019784",
            "group": "node",
            "extra": "mean: 23.628 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 23.971433877013048,
            "unit": "iter/sec",
            "range": "stddev: 0.0032809",
            "group": "node",
            "extra": "mean: 41.716 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 23.513076605220956,
            "unit": "iter/sec",
            "range": "stddev: 0.0038253",
            "group": "node",
            "extra": "mean: 42.530 msec\nrounds: 100"
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
          "pythonVersion": "3.8.6",
          "metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "02c8a0ccd59b4ee64dc82ead3646ff0283032633",
          "message": "FIX: Only remove temporary folder if it is present (#4379)\n\nThis was causing an error, when running the tests/engine/test_calc_job.py on OSX,\r\nsince here it is not guaranteed the temporary folder will be created.",
          "timestamp": "2020-10-27T19:53:31+01:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/02c8a0ccd59b4ee64dc82ead3646ff0283032633",
          "distinct": true,
          "tree_id": "2570908a36ef857fa13347b72628b847bf82c0f4"
        },
        "date": 1603825635494,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.015213933995112,
            "unit": "iter/sec",
            "range": "stddev: 0.035590",
            "group": "engine",
            "extra": "mean: 331.65 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.6841622653979629,
            "unit": "iter/sec",
            "range": "stddev: 0.067484",
            "group": "engine",
            "extra": "mean: 1.4616 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.7210476549004419,
            "unit": "iter/sec",
            "range": "stddev: 0.060746",
            "group": "engine",
            "extra": "mean: 1.3869 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.16248876119327293,
            "unit": "iter/sec",
            "range": "stddev: 0.16290",
            "group": "engine",
            "extra": "mean: 6.1543 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.1709411700255629,
            "unit": "iter/sec",
            "range": "stddev: 0.10610",
            "group": "engine",
            "extra": "mean: 5.8500 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 1.8237373528923364,
            "unit": "iter/sec",
            "range": "stddev: 0.021992",
            "group": "engine",
            "extra": "mean: 548.32 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.41104674755299014,
            "unit": "iter/sec",
            "range": "stddev: 0.060227",
            "group": "engine",
            "extra": "mean: 2.4328 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.46969500258156344,
            "unit": "iter/sec",
            "range": "stddev: 0.068065",
            "group": "engine",
            "extra": "mean: 2.1290 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.1253934533631499,
            "unit": "iter/sec",
            "range": "stddev: 0.11831",
            "group": "engine",
            "extra": "mean: 7.9749 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.14090342801825181,
            "unit": "iter/sec",
            "range": "stddev: 0.13791",
            "group": "engine",
            "extra": "mean: 7.0971 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 3.2720800778948504,
            "unit": "iter/sec",
            "range": "stddev: 0.014060",
            "group": "import-export",
            "extra": "mean: 305.62 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.854505599129458,
            "unit": "iter/sec",
            "range": "stddev: 0.0059172",
            "group": "import-export",
            "extra": "mean: 350.32 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 0.16633266667307228,
            "unit": "iter/sec",
            "range": "stddev: 0.10839",
            "group": "import-export",
            "extra": "mean: 6.0120 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 0.1662865630646653,
            "unit": "iter/sec",
            "range": "stddev: 0.090498",
            "group": "import-export",
            "extra": "mean: 6.0137 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 99.88831537406347,
            "unit": "iter/sec",
            "range": "stddev: 0.0014964",
            "group": "node",
            "extra": "mean: 10.011 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 46.38278040464703,
            "unit": "iter/sec",
            "range": "stddev: 0.0017836",
            "group": "node",
            "extra": "mean: 21.560 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 46.00544368337914,
            "unit": "iter/sec",
            "range": "stddev: 0.0023928",
            "group": "node",
            "extra": "mean: 21.737 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 57.10009957676647,
            "unit": "iter/sec",
            "range": "stddev: 0.0010398",
            "group": "node",
            "extra": "mean: 17.513 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 30.473451854348745,
            "unit": "iter/sec",
            "range": "stddev: 0.0032759",
            "group": "node",
            "extra": "mean: 32.815 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 29.50650229154968,
            "unit": "iter/sec",
            "range": "stddev: 0.0026911",
            "group": "node",
            "extra": "mean: 33.891 msec\nrounds: 100"
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
          "pythonVersion": "3.8.6",
          "metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "2f8e8454974f9b82d4d734e5e995bd51053e06da",
          "message": "Refactor Import Archive (#4510)\n\nThis commit builds on [c6d38c1](https://github.com/aiidateam/aiida-core/commit/c6d38c1657b65f540bea653f253920bb602c7ebc),\r\nto refactor the archive in order to decouple it from its export/import to the AiiDA database.\r\n\r\nThe `aiida/tools/importexport/archive` module has been created,\r\nwhich contains the readers and writers used to create and interact with an archive.\r\nEffectively archive formats are now defined by their associated\r\nreader and writer classes, which must inherit and implement the\r\n`ArchiveReaderAbstract` and `ArchiveWriterAbstract` interfaces respectively.\r\n\r\n`aiida/tools/importexport/dbimport` has been refactored,\r\nto interface with this new `ArchiveReaderAbstract` class,\r\nand also utilise the new `progress_reporter` context manager.\r\nBoth the django and sqlalchemy backends have been \"synchronized\",\r\nsuch that conform to exactly the same code structure, which in-turn\r\nhas allowed for the sharing of common code.\r\n\r\nThe commit is intended to be back-compatible,\r\nin that no public API elements have been removed.\r\nHowever, it does:\r\n\r\n- remove the `Archive` class, replaced by the `ReaderJsonZip`/`ReaderJsonTar` classes.\r\n- remove `aiida/tools/importexport/common/progress_bar.py`,\r\n  now replaced by `aiida/common/progress_reporter.py`\r\n- move `aiida/tools/importexport/dbexport/zip.py` → `aiida/tools/importexport/common/zip_folder.py`\r\n\r\nThe `aiida import --verbosity DEBUG` option has been added,\r\nwhich sets the log level of the process, and whether the progress bars are removed.\r\n\r\nThe `verdi export inspect` code has also been refactored, to utilize the `ArchiveReaderAbstract`.\r\nThe `verdi export inspect --data` option has been deprecated,\r\nsince access to the `data.json` file is only an implementation\r\ndetail of the current archive format.",
          "timestamp": "2020-10-27T22:18:15+01:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/2f8e8454974f9b82d4d734e5e995bd51053e06da",
          "distinct": true,
          "tree_id": "f6fc4b6ec56779fe7e3c1697030e876149013395"
        },
        "date": 1603834476675,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 2.5696809269515444,
            "unit": "iter/sec",
            "range": "stddev: 0.037114",
            "group": "engine",
            "extra": "mean: 389.15 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.5696015527706528,
            "unit": "iter/sec",
            "range": "stddev: 0.038850",
            "group": "engine",
            "extra": "mean: 1.7556 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.6131701373965275,
            "unit": "iter/sec",
            "range": "stddev: 0.077542",
            "group": "engine",
            "extra": "mean: 1.6309 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.1416962836287741,
            "unit": "iter/sec",
            "range": "stddev: 0.22460",
            "group": "engine",
            "extra": "mean: 7.0573 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.14716390279346092,
            "unit": "iter/sec",
            "range": "stddev: 0.17625",
            "group": "engine",
            "extra": "mean: 6.7951 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 1.5586148354419576,
            "unit": "iter/sec",
            "range": "stddev: 0.010837",
            "group": "engine",
            "extra": "mean: 641.60 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.34832885741445196,
            "unit": "iter/sec",
            "range": "stddev: 0.11147",
            "group": "engine",
            "extra": "mean: 2.8709 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.3851929570243193,
            "unit": "iter/sec",
            "range": "stddev: 0.071697",
            "group": "engine",
            "extra": "mean: 2.5961 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.1076351207505942,
            "unit": "iter/sec",
            "range": "stddev: 0.19050",
            "group": "engine",
            "extra": "mean: 9.2906 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.12021785771642687,
            "unit": "iter/sec",
            "range": "stddev: 0.16217",
            "group": "engine",
            "extra": "mean: 8.3182 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.469194054618142,
            "unit": "iter/sec",
            "range": "stddev: 0.053796",
            "group": "import-export",
            "extra": "mean: 404.99 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.200964485931205,
            "unit": "iter/sec",
            "range": "stddev: 0.061735",
            "group": "import-export",
            "extra": "mean: 454.35 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 0.12480114534553838,
            "unit": "iter/sec",
            "range": "stddev: 0.081744",
            "group": "import-export",
            "extra": "mean: 8.0127 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 0.12594378483018126,
            "unit": "iter/sec",
            "range": "stddev: 0.16641",
            "group": "import-export",
            "extra": "mean: 7.9401 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 95.12943658369903,
            "unit": "iter/sec",
            "range": "stddev: 0.00064523",
            "group": "node",
            "extra": "mean: 10.512 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 44.23186261348376,
            "unit": "iter/sec",
            "range": "stddev: 0.0010369",
            "group": "node",
            "extra": "mean: 22.608 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 42.6016832995341,
            "unit": "iter/sec",
            "range": "stddev: 0.0019944",
            "group": "node",
            "extra": "mean: 23.473 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 51.21143370885512,
            "unit": "iter/sec",
            "range": "stddev: 0.0012651",
            "group": "node",
            "extra": "mean: 19.527 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 26.515938293259726,
            "unit": "iter/sec",
            "range": "stddev: 0.0024568",
            "group": "node",
            "extra": "mean: 37.713 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 26.281580068824102,
            "unit": "iter/sec",
            "range": "stddev: 0.0026899",
            "group": "node",
            "extra": "mean: 38.049 msec\nrounds: 100"
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
          "pythonVersion": "3.8.6",
          "metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "485957229e931f3441fd1a6b7acb0ce4d3aecc7c",
          "message": "Add group extras to archive (#4521)\n\nGroup extras were introduced recently but not yet exported to AiiDA archives.\r\nThis commit adds group extras to the AiiDA archive.\r\n\r\nInstead of special-casing deserialization of attributes and extras based on the field name, a `convert_type: \"jsonb\"` is introduced, which is used to indicate JSON-binary fields.",
          "timestamp": "2020-10-28T00:49:55+01:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/485957229e931f3441fd1a6b7acb0ce4d3aecc7c",
          "distinct": true,
          "tree_id": "9d9440c23664b864137148e7b9711684afbf731f"
        },
        "date": 1603843556518,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 2.678549836589878,
            "unit": "iter/sec",
            "range": "stddev: 0.0096254",
            "group": "engine",
            "extra": "mean: 373.34 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.582459456005213,
            "unit": "iter/sec",
            "range": "stddev: 0.050701",
            "group": "engine",
            "extra": "mean: 1.7169 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.6274416650831661,
            "unit": "iter/sec",
            "range": "stddev: 0.063067",
            "group": "engine",
            "extra": "mean: 1.5938 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.14054032937770802,
            "unit": "iter/sec",
            "range": "stddev: 0.15487",
            "group": "engine",
            "extra": "mean: 7.1154 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.1469619013838989,
            "unit": "iter/sec",
            "range": "stddev: 0.21228",
            "group": "engine",
            "extra": "mean: 6.8045 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 1.5408946326590212,
            "unit": "iter/sec",
            "range": "stddev: 0.014645",
            "group": "engine",
            "extra": "mean: 648.97 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.3492735303699103,
            "unit": "iter/sec",
            "range": "stddev: 0.10940",
            "group": "engine",
            "extra": "mean: 2.8631 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.3893942816957624,
            "unit": "iter/sec",
            "range": "stddev: 0.071000",
            "group": "engine",
            "extra": "mean: 2.5681 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.10642500343589426,
            "unit": "iter/sec",
            "range": "stddev: 0.23195",
            "group": "engine",
            "extra": "mean: 9.3963 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.11882361441204127,
            "unit": "iter/sec",
            "range": "stddev: 0.15134",
            "group": "engine",
            "extra": "mean: 8.4158 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.8239326646980016,
            "unit": "iter/sec",
            "range": "stddev: 0.0073018",
            "group": "import-export",
            "extra": "mean: 354.12 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.542652032227163,
            "unit": "iter/sec",
            "range": "stddev: 0.0032976",
            "group": "import-export",
            "extra": "mean: 393.29 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 0.13331427356939374,
            "unit": "iter/sec",
            "range": "stddev: 0.051203",
            "group": "import-export",
            "extra": "mean: 7.5011 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 0.1316649791108145,
            "unit": "iter/sec",
            "range": "stddev: 0.082032",
            "group": "import-export",
            "extra": "mean: 7.5950 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 82.90109084532142,
            "unit": "iter/sec",
            "range": "stddev: 0.0011314",
            "group": "node",
            "extra": "mean: 12.063 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 39.8241886164667,
            "unit": "iter/sec",
            "range": "stddev: 0.0016085",
            "group": "node",
            "extra": "mean: 25.110 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 39.61753171494291,
            "unit": "iter/sec",
            "range": "stddev: 0.0011232",
            "group": "node",
            "extra": "mean: 25.241 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 49.13747054564881,
            "unit": "iter/sec",
            "range": "stddev: 0.0010579",
            "group": "node",
            "extra": "mean: 20.351 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 24.77216151873054,
            "unit": "iter/sec",
            "range": "stddev: 0.018704",
            "group": "node",
            "extra": "mean: 40.368 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 25.67790751750609,
            "unit": "iter/sec",
            "range": "stddev: 0.0036299",
            "group": "node",
            "extra": "mean: 38.944 msec\nrounds: 100"
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
          "pythonVersion": "3.8.6",
          "metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "55f8706e8ecfb37745efe6bc838719b8dceed1fa",
          "message": "Fix: Add missing entry point groups to the mapping (#4395)\n\nSome new entrypoints had been introduced, but they weren't in the mapping,\r\nso they couldn't be accessed for instance with `verdi plugin list`.",
          "timestamp": "2020-10-28T12:46:55+01:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/55f8706e8ecfb37745efe6bc838719b8dceed1fa",
          "distinct": true,
          "tree_id": "21b4ad14fbb4ea81ec05547e67f25347688b174b"
        },
        "date": 1603886447239,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.1925167825475707,
            "unit": "iter/sec",
            "range": "stddev: 0.011134",
            "group": "engine",
            "extra": "mean: 313.23 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.6876272614077598,
            "unit": "iter/sec",
            "range": "stddev: 0.060217",
            "group": "engine",
            "extra": "mean: 1.4543 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.7427778825912473,
            "unit": "iter/sec",
            "range": "stddev: 0.059090",
            "group": "engine",
            "extra": "mean: 1.3463 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.16494287524700815,
            "unit": "iter/sec",
            "range": "stddev: 0.13948",
            "group": "engine",
            "extra": "mean: 6.0627 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.17415285312914433,
            "unit": "iter/sec",
            "range": "stddev: 0.14156",
            "group": "engine",
            "extra": "mean: 5.7421 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 1.8470879350042906,
            "unit": "iter/sec",
            "range": "stddev: 0.012384",
            "group": "engine",
            "extra": "mean: 541.39 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.4159173585664281,
            "unit": "iter/sec",
            "range": "stddev: 0.087947",
            "group": "engine",
            "extra": "mean: 2.4043 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.4703783720322561,
            "unit": "iter/sec",
            "range": "stddev: 0.059593",
            "group": "engine",
            "extra": "mean: 2.1259 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.1272089794374544,
            "unit": "iter/sec",
            "range": "stddev: 0.10738",
            "group": "engine",
            "extra": "mean: 7.8611 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.1411130628472319,
            "unit": "iter/sec",
            "range": "stddev: 0.16245",
            "group": "engine",
            "extra": "mean: 7.0865 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 3.311703454613889,
            "unit": "iter/sec",
            "range": "stddev: 0.0078284",
            "group": "import-export",
            "extra": "mean: 301.96 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.945984139077743,
            "unit": "iter/sec",
            "range": "stddev: 0.0075107",
            "group": "import-export",
            "extra": "mean: 339.45 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 0.15611250984451502,
            "unit": "iter/sec",
            "range": "stddev: 0.24633",
            "group": "import-export",
            "extra": "mean: 6.4056 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 0.15798774352616823,
            "unit": "iter/sec",
            "range": "stddev: 0.21928",
            "group": "import-export",
            "extra": "mean: 6.3296 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 118.20939314486796,
            "unit": "iter/sec",
            "range": "stddev: 0.00048101",
            "group": "node",
            "extra": "mean: 8.4596 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 52.57280758441076,
            "unit": "iter/sec",
            "range": "stddev: 0.0014779",
            "group": "node",
            "extra": "mean: 19.021 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 52.387860583515675,
            "unit": "iter/sec",
            "range": "stddev: 0.0016941",
            "group": "node",
            "extra": "mean: 19.088 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 58.83549142857319,
            "unit": "iter/sec",
            "range": "stddev: 0.0013326",
            "group": "node",
            "extra": "mean: 16.997 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 31.660132429553393,
            "unit": "iter/sec",
            "range": "stddev: 0.016767",
            "group": "node",
            "extra": "mean: 31.585 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 33.50472153192223,
            "unit": "iter/sec",
            "range": "stddev: 0.0027823",
            "group": "node",
            "extra": "mean: 29.847 msec\nrounds: 100"
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
          "pythonVersion": "3.8.6",
          "metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "9ff07c166a559f98b5b2be71537814ec00d3f18d",
          "message": "Add `reset` method to`ProgressReporterAbstract` (#4522)\n\nThis PR adds the `update` method to the progress reporter.\r\nThis in-turn, allows for the implementation of a callback mechanism in `ArchiveReaderAbstract.iter_node_repos`.\r\nThe callback implementation is taken from the\r\n[disk-objectstore](https://github.com/aiidateam/disk-objectstore) package,\r\nand so facilitates a later migration to its use.\r\n\r\nThe PR also moves the (common) repository import code out of the backend specific modules,\r\nreducing code duplication.",
          "timestamp": "2020-10-28T20:17:44+01:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/9ff07c166a559f98b5b2be71537814ec00d3f18d",
          "distinct": true,
          "tree_id": "5145fa774377f62a8c24f72541ed35cae33ccfb2"
        },
        "date": 1603913780794,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 2.14731218448355,
            "unit": "iter/sec",
            "range": "stddev: 0.021126",
            "group": "engine",
            "extra": "mean: 465.70 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.4529858563012528,
            "unit": "iter/sec",
            "range": "stddev: 0.15573",
            "group": "engine",
            "extra": "mean: 2.2076 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.5061625130572847,
            "unit": "iter/sec",
            "range": "stddev: 0.077345",
            "group": "engine",
            "extra": "mean: 1.9757 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.11829087881389513,
            "unit": "iter/sec",
            "range": "stddev: 0.39898",
            "group": "engine",
            "extra": "mean: 8.4537 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.12660541824946223,
            "unit": "iter/sec",
            "range": "stddev: 0.15809",
            "group": "engine",
            "extra": "mean: 7.8986 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 1.310491516179702,
            "unit": "iter/sec",
            "range": "stddev: 0.021444",
            "group": "engine",
            "extra": "mean: 763.07 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.2924111635112417,
            "unit": "iter/sec",
            "range": "stddev: 0.087167",
            "group": "engine",
            "extra": "mean: 3.4198 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.3270077117340188,
            "unit": "iter/sec",
            "range": "stddev: 0.089759",
            "group": "engine",
            "extra": "mean: 3.0580 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.0924250694883663,
            "unit": "iter/sec",
            "range": "stddev: 0.25813",
            "group": "engine",
            "extra": "mean: 10.820 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.09814465788731222,
            "unit": "iter/sec",
            "range": "stddev: 0.20288",
            "group": "engine",
            "extra": "mean: 10.189 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.255325933020566,
            "unit": "iter/sec",
            "range": "stddev: 0.023117",
            "group": "import-export",
            "extra": "mean: 443.39 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 1.9166055070395056,
            "unit": "iter/sec",
            "range": "stddev: 0.040420",
            "group": "import-export",
            "extra": "mean: 521.76 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 0.11093535685490676,
            "unit": "iter/sec",
            "range": "stddev: 0.43106",
            "group": "import-export",
            "extra": "mean: 9.0143 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 0.11585469215529597,
            "unit": "iter/sec",
            "range": "stddev: 0.22084",
            "group": "import-export",
            "extra": "mean: 8.6315 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 73.20649066753802,
            "unit": "iter/sec",
            "range": "stddev: 0.0021842",
            "group": "node",
            "extra": "mean: 13.660 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 32.641477289120274,
            "unit": "iter/sec",
            "range": "stddev: 0.0042806",
            "group": "node",
            "extra": "mean: 30.636 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 34.6616299380808,
            "unit": "iter/sec",
            "range": "stddev: 0.0031485",
            "group": "node",
            "extra": "mean: 28.850 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 42.33947952524744,
            "unit": "iter/sec",
            "range": "stddev: 0.0029058",
            "group": "node",
            "extra": "mean: 23.619 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 22.4947884900698,
            "unit": "iter/sec",
            "range": "stddev: 0.0043113",
            "group": "node",
            "extra": "mean: 44.455 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 21.90174200851411,
            "unit": "iter/sec",
            "range": "stddev: 0.019618",
            "group": "node",
            "extra": "mean: 45.658 msec\nrounds: 100"
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
          "pythonVersion": "3.8.6",
          "metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "8326050c0ec8ecca1f5d463b5ecd4f4b236847ee",
          "message": "Refactor archive migrations (#4532)\n\nThis commit follows refactors to the archive writing and reading process,\r\nto provide an implementation agnostic interface for the migration of archives\r\n(i.e. independent of the internal structure of the archive).\r\nThis will allow for subsequent changes to the archive format.\r\n\r\nTo facilitate this:\r\n\r\n- `MIGRATE_FUNCTIONS` now includes both the to/from versions of the migration,\r\n- this allows for a change, from a recursive migration approach to pre-computing the migration pathway, then applying the migrations iteratively\r\n- this also allows for a progress bar of the migration steps\r\n- the signature of migration step functions has been changed, such that they now only receive the uncompressed archive folder,\r\n  and not also specifically the `data.json` and `metadata.json` dictionaries.\r\n- instead, the folder is wrapped in a new `CacheFolder` class,\r\n  which caches file writes in memory,\r\n  such that reading of the files from the file system only happen once,\r\n  and they are written after all the migrations have finished.\r\n- the `--verbose` flag has been added to `verdi export migrate`,\r\n  to allow for control of the stdout message verbosity.\r\n- the extracting/compressing of tar/zip has been generalised into `archive/common.py`;\r\n  `safe_extract_tar`, `safe_extract_zip`, `compress_folder_tar`, `compress_folder_zip`.\r\n  These include callbacks, to be used by the progress reporter to create progress bars.\r\n- all migration unit tests have been converted to pytest\r\n\r\nCo-authored-by: Leopold Talirz <leopold.talirz@gmail.com>",
          "timestamp": "2020-11-03T10:31:07+01:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/8326050c0ec8ecca1f5d463b5ecd4f4b236847ee",
          "distinct": true,
          "tree_id": "511789f7a2607a15e83d8d4d2dc2be79c8cb2f1d"
        },
        "date": 1604396901144,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 2.414679144564614,
            "unit": "iter/sec",
            "range": "stddev: 0.0089798",
            "group": "engine",
            "extra": "mean: 414.13 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.5319084372105568,
            "unit": "iter/sec",
            "range": "stddev: 0.047290",
            "group": "engine",
            "extra": "mean: 1.8800 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.5807490361723664,
            "unit": "iter/sec",
            "range": "stddev: 0.055496",
            "group": "engine",
            "extra": "mean: 1.7219 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.13405655181450962,
            "unit": "iter/sec",
            "range": "stddev: 0.21059",
            "group": "engine",
            "extra": "mean: 7.4595 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.13916737723388597,
            "unit": "iter/sec",
            "range": "stddev: 0.16263",
            "group": "engine",
            "extra": "mean: 7.1856 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 1.454589516230544,
            "unit": "iter/sec",
            "range": "stddev: 0.013129",
            "group": "engine",
            "extra": "mean: 687.48 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.33075206086772624,
            "unit": "iter/sec",
            "range": "stddev: 0.072237",
            "group": "engine",
            "extra": "mean: 3.0234 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.3649005753202094,
            "unit": "iter/sec",
            "range": "stddev: 0.087079",
            "group": "engine",
            "extra": "mean: 2.7405 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.1007485322171086,
            "unit": "iter/sec",
            "range": "stddev: 0.28944",
            "group": "engine",
            "extra": "mean: 9.9257 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.1128997282344194,
            "unit": "iter/sec",
            "range": "stddev: 0.13627",
            "group": "engine",
            "extra": "mean: 8.8574 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.386801346098881,
            "unit": "iter/sec",
            "range": "stddev: 0.056392",
            "group": "import-export",
            "extra": "mean: 418.97 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.074898984952051,
            "unit": "iter/sec",
            "range": "stddev: 0.066899",
            "group": "import-export",
            "extra": "mean: 481.95 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 0.11724075085780776,
            "unit": "iter/sec",
            "range": "stddev: 0.081154",
            "group": "import-export",
            "extra": "mean: 8.5295 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 0.1224221145709684,
            "unit": "iter/sec",
            "range": "stddev: 0.12412",
            "group": "import-export",
            "extra": "mean: 8.1685 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 88.42447927929203,
            "unit": "iter/sec",
            "range": "stddev: 0.0010202",
            "group": "node",
            "extra": "mean: 11.309 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 40.67836874858621,
            "unit": "iter/sec",
            "range": "stddev: 0.0013488",
            "group": "node",
            "extra": "mean: 24.583 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 39.53876962430518,
            "unit": "iter/sec",
            "range": "stddev: 0.0023116",
            "group": "node",
            "extra": "mean: 25.292 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 47.44838900418048,
            "unit": "iter/sec",
            "range": "stddev: 0.0016010",
            "group": "node",
            "extra": "mean: 21.076 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 25.172314524081578,
            "unit": "iter/sec",
            "range": "stddev: 0.0020517",
            "group": "node",
            "extra": "mean: 39.726 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 23.46701146827982,
            "unit": "iter/sec",
            "range": "stddev: 0.019518",
            "group": "node",
            "extra": "mean: 42.613 msec\nrounds: 100"
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
          "pythonVersion": "3.8.6",
          "metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "d675574bfa8518ca97275384779493520a0304e1",
          "message": "Simplify Hill notation for `get_formula()` and add test (#4536)\n\nSimplify hill notation sorting (@csadorf)\r\nAdd a test for `get_formula()` to test 'hill' and 'hill_compact' (@CasperWA)\r\n\r\nCo-authored-by: Carl Simon Adorf <csadorf@umich.edu>",
          "timestamp": "2020-11-03T14:35:22+01:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/d675574bfa8518ca97275384779493520a0304e1",
          "distinct": true,
          "tree_id": "16848932c7934e293ff72491e291ea596d988aec"
        },
        "date": 1604411504845,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 2.549147370759505,
            "unit": "iter/sec",
            "range": "stddev: 0.014444",
            "group": "engine",
            "extra": "mean: 392.29 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.5394277663148134,
            "unit": "iter/sec",
            "range": "stddev: 0.066870",
            "group": "engine",
            "extra": "mean: 1.8538 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.5960939253469434,
            "unit": "iter/sec",
            "range": "stddev: 0.12492",
            "group": "engine",
            "extra": "mean: 1.6776 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.13491630275901,
            "unit": "iter/sec",
            "range": "stddev: 0.21381",
            "group": "engine",
            "extra": "mean: 7.4120 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.14921681351123264,
            "unit": "iter/sec",
            "range": "stddev: 0.22347",
            "group": "engine",
            "extra": "mean: 6.7017 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 1.6384393267382387,
            "unit": "iter/sec",
            "range": "stddev: 0.062380",
            "group": "engine",
            "extra": "mean: 610.34 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.3478942850543896,
            "unit": "iter/sec",
            "range": "stddev: 0.11838",
            "group": "engine",
            "extra": "mean: 2.8744 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.36177339662537666,
            "unit": "iter/sec",
            "range": "stddev: 0.10112",
            "group": "engine",
            "extra": "mean: 2.7642 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.10264712589567027,
            "unit": "iter/sec",
            "range": "stddev: 0.20671",
            "group": "engine",
            "extra": "mean: 9.7421 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.11506051764528666,
            "unit": "iter/sec",
            "range": "stddev: 0.25176",
            "group": "engine",
            "extra": "mean: 8.6911 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.6451085319122116,
            "unit": "iter/sec",
            "range": "stddev: 0.063619",
            "group": "import-export",
            "extra": "mean: 378.06 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.395188991296618,
            "unit": "iter/sec",
            "range": "stddev: 0.056841",
            "group": "import-export",
            "extra": "mean: 417.50 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 0.12975296244091897,
            "unit": "iter/sec",
            "range": "stddev: 0.17909",
            "group": "import-export",
            "extra": "mean: 7.7070 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 0.1291869557712535,
            "unit": "iter/sec",
            "range": "stddev: 0.20690",
            "group": "import-export",
            "extra": "mean: 7.7407 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 77.88956631136199,
            "unit": "iter/sec",
            "range": "stddev: 0.0013482",
            "group": "node",
            "extra": "mean: 12.839 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 38.885816082022075,
            "unit": "iter/sec",
            "range": "stddev: 0.0012414",
            "group": "node",
            "extra": "mean: 25.716 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 37.022150567414656,
            "unit": "iter/sec",
            "range": "stddev: 0.0019026",
            "group": "node",
            "extra": "mean: 27.011 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 45.27962204194669,
            "unit": "iter/sec",
            "range": "stddev: 0.0022562",
            "group": "node",
            "extra": "mean: 22.085 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 25.84821002656574,
            "unit": "iter/sec",
            "range": "stddev: 0.0019785",
            "group": "node",
            "extra": "mean: 38.687 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 23.13267805724543,
            "unit": "iter/sec",
            "range": "stddev: 0.019626",
            "group": "node",
            "extra": "mean: 43.229 msec\nrounds: 100"
          }
        ]
      }
    ]
  }
}