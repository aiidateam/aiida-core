window.BENCHMARK_DATA = {
  "lastUpdate": 1612976442052,
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
          "id": "2c0f9a9b78aa9591bfa46c89a2fdd37563b4c747",
          "message": "CI: Add official support for Python 3.9 (#4301)\n\nUpdating of Conda in the `install-with-conda` job of the `test-install`\r\nworkflow is disabled because it fails for as of yet unknown reasons.",
          "timestamp": "2020-11-05T11:05:04+01:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/2c0f9a9b78aa9591bfa46c89a2fdd37563b4c747",
          "distinct": true,
          "tree_id": "13d0e32e8a0c18ff4bb8f7507945c5e99ceb7864"
        },
        "date": 1604571647214,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 2.707361937961574,
            "unit": "iter/sec",
            "range": "stddev: 0.0094791",
            "group": "engine",
            "extra": "mean: 369.36 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.5955731226322641,
            "unit": "iter/sec",
            "range": "stddev: 0.036756",
            "group": "engine",
            "extra": "mean: 1.6791 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.6494425538641684,
            "unit": "iter/sec",
            "range": "stddev: 0.046554",
            "group": "engine",
            "extra": "mean: 1.5398 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.1482259958504607,
            "unit": "iter/sec",
            "range": "stddev: 0.16627",
            "group": "engine",
            "extra": "mean: 6.7465 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.15415357377347907,
            "unit": "iter/sec",
            "range": "stddev: 0.13934",
            "group": "engine",
            "extra": "mean: 6.4870 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 1.5461190890565795,
            "unit": "iter/sec",
            "range": "stddev: 0.064291",
            "group": "engine",
            "extra": "mean: 646.78 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.3654691249286876,
            "unit": "iter/sec",
            "range": "stddev: 0.061304",
            "group": "engine",
            "extra": "mean: 2.7362 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.4041459701356534,
            "unit": "iter/sec",
            "range": "stddev: 0.093155",
            "group": "engine",
            "extra": "mean: 2.4744 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.1133171066123228,
            "unit": "iter/sec",
            "range": "stddev: 0.092080",
            "group": "engine",
            "extra": "mean: 8.8248 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.1256770249406661,
            "unit": "iter/sec",
            "range": "stddev: 0.13508",
            "group": "engine",
            "extra": "mean: 7.9569 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.557356292083614,
            "unit": "iter/sec",
            "range": "stddev: 0.053466",
            "group": "import-export",
            "extra": "mean: 391.03 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.27610976409898,
            "unit": "iter/sec",
            "range": "stddev: 0.053565",
            "group": "import-export",
            "extra": "mean: 439.35 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 0.12941243176023154,
            "unit": "iter/sec",
            "range": "stddev: 0.078985",
            "group": "import-export",
            "extra": "mean: 7.7272 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 0.1355044958443508,
            "unit": "iter/sec",
            "range": "stddev: 0.16873",
            "group": "import-export",
            "extra": "mean: 7.3798 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 98.70984261512876,
            "unit": "iter/sec",
            "range": "stddev: 0.00053665",
            "group": "node",
            "extra": "mean: 10.131 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 45.0181368326996,
            "unit": "iter/sec",
            "range": "stddev: 0.0011828",
            "group": "node",
            "extra": "mean: 22.213 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 43.123015901951284,
            "unit": "iter/sec",
            "range": "stddev: 0.0017999",
            "group": "node",
            "extra": "mean: 23.189 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 52.6018382832645,
            "unit": "iter/sec",
            "range": "stddev: 0.0012609",
            "group": "node",
            "extra": "mean: 19.011 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 27.995305759443998,
            "unit": "iter/sec",
            "range": "stddev: 0.0016519",
            "group": "node",
            "extra": "mean: 35.720 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 26.4028084263871,
            "unit": "iter/sec",
            "range": "stddev: 0.017151",
            "group": "node",
            "extra": "mean: 37.875 msec\nrounds: 100"
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
          "id": "64ae3c8027f5391e79797ef09b94076e4e0beb03",
          "message": "Merge remote-tracking branch 'origin/master' into develop",
          "timestamp": "2020-11-06T14:58:26+01:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/64ae3c8027f5391e79797ef09b94076e4e0beb03",
          "distinct": false,
          "tree_id": "f11e1b02d5c760e9f61cb07343a1a632cd84e650"
        },
        "date": 1604672416105,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 2.7921437342298168,
            "unit": "iter/sec",
            "range": "stddev: 0.010536",
            "group": "engine",
            "extra": "mean: 358.15 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.6093037385394796,
            "unit": "iter/sec",
            "range": "stddev: 0.036734",
            "group": "engine",
            "extra": "mean: 1.6412 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.6696771671556256,
            "unit": "iter/sec",
            "range": "stddev: 0.039915",
            "group": "engine",
            "extra": "mean: 1.4933 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.15207256057590376,
            "unit": "iter/sec",
            "range": "stddev: 0.15069",
            "group": "engine",
            "extra": "mean: 6.5758 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.15875162602714255,
            "unit": "iter/sec",
            "range": "stddev: 0.20493",
            "group": "engine",
            "extra": "mean: 6.2991 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 1.6933800186915284,
            "unit": "iter/sec",
            "range": "stddev: 0.048902",
            "group": "engine",
            "extra": "mean: 590.53 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.3889042782849007,
            "unit": "iter/sec",
            "range": "stddev: 0.064668",
            "group": "engine",
            "extra": "mean: 2.5713 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.4051970874390893,
            "unit": "iter/sec",
            "range": "stddev: 0.12804",
            "group": "engine",
            "extra": "mean: 2.4679 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.11194970900543194,
            "unit": "iter/sec",
            "range": "stddev: 0.10158",
            "group": "engine",
            "extra": "mean: 8.9326 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.12423581432795115,
            "unit": "iter/sec",
            "range": "stddev: 0.21869",
            "group": "engine",
            "extra": "mean: 8.0492 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.795315195783732,
            "unit": "iter/sec",
            "range": "stddev: 0.048454",
            "group": "import-export",
            "extra": "mean: 357.74 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.3015585086488195,
            "unit": "iter/sec",
            "range": "stddev: 0.061916",
            "group": "import-export",
            "extra": "mean: 434.49 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 0.13200035335253776,
            "unit": "iter/sec",
            "range": "stddev: 0.19194",
            "group": "import-export",
            "extra": "mean: 7.5757 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 0.1382880117188995,
            "unit": "iter/sec",
            "range": "stddev: 0.12440",
            "group": "import-export",
            "extra": "mean: 7.2313 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 106.65922930434786,
            "unit": "iter/sec",
            "range": "stddev: 0.0013714",
            "group": "node",
            "extra": "mean: 9.3757 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 50.00854673564998,
            "unit": "iter/sec",
            "range": "stddev: 0.0013907",
            "group": "node",
            "extra": "mean: 19.997 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 47.61820854084439,
            "unit": "iter/sec",
            "range": "stddev: 0.0018430",
            "group": "node",
            "extra": "mean: 21.000 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 55.76651706753071,
            "unit": "iter/sec",
            "range": "stddev: 0.0022853",
            "group": "node",
            "extra": "mean: 17.932 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 27.274366365443736,
            "unit": "iter/sec",
            "range": "stddev: 0.017050",
            "group": "node",
            "extra": "mean: 36.664 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 28.70072089917437,
            "unit": "iter/sec",
            "range": "stddev: 0.0032213",
            "group": "node",
            "extra": "mean: 34.842 msec\nrounds: 100"
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
          "id": "ac4c881ad12cca669d4b7b1745d6dd5f0553a1ba",
          "message": "Make process functions submittable (#4539)\n\nThe limitation that process functions were not submittable, meaning they\r\ncould not be sent to a daemon worker but could only be run by the current\r\ninterpreter, was a historical one. Before the introduction of the system\r\nof processes in v1.0, a `calcfunction` was nothing more than the\r\nexecution of a normal function. However, now, a process function creates\r\na `Process` instance in the background, just as any other process. This\r\nmeans it can also be serialized and deserialized by a daemon worker.\r\n\r\nHere we remove the limitation of process functions not being submittable\r\nsimply by removing the check. Note that there is no need to change the\r\nimplementation other than adding two attributes on the decorated function\r\nthat specify the corresponding process class and the method that allows\r\nto recreate the instance from the serialized instance.\r\n\r\nCo-authored-by: Sebastiaan Huber <mail@sphuber.net>",
          "timestamp": "2020-11-08T11:33:48+01:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/ac4c881ad12cca669d4b7b1745d6dd5f0553a1ba",
          "distinct": true,
          "tree_id": "2e9b791114f515b0a96484fcbffa0b77a6ed688f"
        },
        "date": 1604832462220,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.1840717599854815,
            "unit": "iter/sec",
            "range": "stddev: 0.0075193",
            "group": "engine",
            "extra": "mean: 314.06 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.6856776673453024,
            "unit": "iter/sec",
            "range": "stddev: 0.051078",
            "group": "engine",
            "extra": "mean: 1.4584 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.7169660999369576,
            "unit": "iter/sec",
            "range": "stddev: 0.059379",
            "group": "engine",
            "extra": "mean: 1.3948 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.16509512377580732,
            "unit": "iter/sec",
            "range": "stddev: 0.14818",
            "group": "engine",
            "extra": "mean: 6.0571 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.1738800879368099,
            "unit": "iter/sec",
            "range": "stddev: 0.13130",
            "group": "engine",
            "extra": "mean: 5.7511 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 1.7832093780657599,
            "unit": "iter/sec",
            "range": "stddev: 0.048894",
            "group": "engine",
            "extra": "mean: 560.79 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.42739598705032134,
            "unit": "iter/sec",
            "range": "stddev: 0.047903",
            "group": "engine",
            "extra": "mean: 2.3398 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.47520019981864403,
            "unit": "iter/sec",
            "range": "stddev: 0.059353",
            "group": "engine",
            "extra": "mean: 2.1044 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.1272421282712627,
            "unit": "iter/sec",
            "range": "stddev: 0.12164",
            "group": "engine",
            "extra": "mean: 7.8590 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.14097767231548342,
            "unit": "iter/sec",
            "range": "stddev: 0.14745",
            "group": "engine",
            "extra": "mean: 7.0933 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 3.1577263710269734,
            "unit": "iter/sec",
            "range": "stddev: 0.049492",
            "group": "import-export",
            "extra": "mean: 316.68 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.8729758730097994,
            "unit": "iter/sec",
            "range": "stddev: 0.047278",
            "group": "import-export",
            "extra": "mean: 348.07 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 0.15451371062050565,
            "unit": "iter/sec",
            "range": "stddev: 0.057897",
            "group": "import-export",
            "extra": "mean: 6.4719 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 0.15382853155920811,
            "unit": "iter/sec",
            "range": "stddev: 0.096637",
            "group": "import-export",
            "extra": "mean: 6.5007 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 108.60007171612085,
            "unit": "iter/sec",
            "range": "stddev: 0.00040646",
            "group": "node",
            "extra": "mean: 9.2081 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 48.95104885179242,
            "unit": "iter/sec",
            "range": "stddev: 0.00076328",
            "group": "node",
            "extra": "mean: 20.429 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 46.543254069783984,
            "unit": "iter/sec",
            "range": "stddev: 0.0012995",
            "group": "node",
            "extra": "mean: 21.485 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 56.974913914632516,
            "unit": "iter/sec",
            "range": "stddev: 0.00084641",
            "group": "node",
            "extra": "mean: 17.552 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 28.945627705652566,
            "unit": "iter/sec",
            "range": "stddev: 0.017373",
            "group": "node",
            "extra": "mean: 34.548 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 29.297588427751656,
            "unit": "iter/sec",
            "range": "stddev: 0.0025691",
            "group": "node",
            "extra": "mean: 34.133 msec\nrounds: 100"
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
          "id": "c42a86b9417cf2f1072df5c87a55d57023bc4fc4",
          "message": "`SlurmScheduler`: fix bug in validation of job resources (#4555)\n\nThe `SlurmJobResource` resource class used by the `SlurmScheduler`\r\nplugin contained a bug in the `validate_resources` methods that would\r\ncause a float value to be set for the `num_cores_per_mpiproc` field in\r\ncertain cases. This would cause the submit script to fail because SLURM\r\nonly accepts integers for the corresponding `--ncpus-per-task` flag.\r\n\r\nThe reason is that the code was incorrectly using `isinstance(_, int)`\r\nto check that the divison of `num_cores_per_machine` over\r\n`num_mpiprocs_per_machine` is an integer. In addition to the negation\r\nmissing in the conditional, this is not the correct way of checking\r\nwhether a division is an integer. Instead it should check that the value\r\nis identical after it is cast to `int`.",
          "timestamp": "2020-11-11T16:35:16+01:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/c42a86b9417cf2f1072df5c87a55d57023bc4fc4",
          "distinct": true,
          "tree_id": "78fdee327c130ffca7355f3ce68f1f20be140247"
        },
        "date": 1605109940588,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 2.4406060255740614,
            "unit": "iter/sec",
            "range": "stddev: 0.014991",
            "group": "engine",
            "extra": "mean: 409.73 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.5366803463528058,
            "unit": "iter/sec",
            "range": "stddev: 0.060426",
            "group": "engine",
            "extra": "mean: 1.8633 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.5864450475600014,
            "unit": "iter/sec",
            "range": "stddev: 0.095380",
            "group": "engine",
            "extra": "mean: 1.7052 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.13372830021750212,
            "unit": "iter/sec",
            "range": "stddev: 0.22152",
            "group": "engine",
            "extra": "mean: 7.4778 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.13830008298736174,
            "unit": "iter/sec",
            "range": "stddev: 0.22343",
            "group": "engine",
            "extra": "mean: 7.2307 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 1.4177764368555335,
            "unit": "iter/sec",
            "range": "stddev: 0.068103",
            "group": "engine",
            "extra": "mean: 705.33 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.32827267947430355,
            "unit": "iter/sec",
            "range": "stddev: 0.032323",
            "group": "engine",
            "extra": "mean: 3.0462 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.36498964222301167,
            "unit": "iter/sec",
            "range": "stddev: 0.092381",
            "group": "engine",
            "extra": "mean: 2.7398 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.10227854966722012,
            "unit": "iter/sec",
            "range": "stddev: 0.15088",
            "group": "engine",
            "extra": "mean: 9.7772 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.11123392106971876,
            "unit": "iter/sec",
            "range": "stddev: 0.24673",
            "group": "engine",
            "extra": "mean: 8.9901 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.45246829655768,
            "unit": "iter/sec",
            "range": "stddev: 0.059545",
            "group": "import-export",
            "extra": "mean: 407.75 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.1367496530089234,
            "unit": "iter/sec",
            "range": "stddev: 0.060160",
            "group": "import-export",
            "extra": "mean: 468.00 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 0.11706196681880236,
            "unit": "iter/sec",
            "range": "stddev: 0.084600",
            "group": "import-export",
            "extra": "mean: 8.5425 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 0.12464854526085903,
            "unit": "iter/sec",
            "range": "stddev: 0.17326",
            "group": "import-export",
            "extra": "mean: 8.0226 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 88.61465802977882,
            "unit": "iter/sec",
            "range": "stddev: 0.0011366",
            "group": "node",
            "extra": "mean: 11.285 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 39.564669514029525,
            "unit": "iter/sec",
            "range": "stddev: 0.0020929",
            "group": "node",
            "extra": "mean: 25.275 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 38.92934667092998,
            "unit": "iter/sec",
            "range": "stddev: 0.0033161",
            "group": "node",
            "extra": "mean: 25.688 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 49.14376237993823,
            "unit": "iter/sec",
            "range": "stddev: 0.0019905",
            "group": "node",
            "extra": "mean: 20.348 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 25.372244482843644,
            "unit": "iter/sec",
            "range": "stddev: 0.0030944",
            "group": "node",
            "extra": "mean: 39.413 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 24.45897004680553,
            "unit": "iter/sec",
            "range": "stddev: 0.0032753",
            "group": "node",
            "extra": "mean: 40.885 msec\nrounds: 100"
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
          "id": "008580e3316ad48b56f2385d245398ac0c78a49b",
          "message": "`verdi group delete`: deprecate and ignore the `--clear` option (#4357)\n\nNote that the option is still there but no longer makes a difference. It\r\nnow merely prints a deprecation warning, but is otherwise ignored. The\r\nreason is that otherwise, users would be forced to continue to use it\r\ndespite it raising a deprecation warning. The only danger is for users\r\nthat have come to depend on the slightly weird behavior that in order\r\nto delete non-empty groups, one would have to pass them `--clear` option\r\notherwise the command would fail. After this change, this would now\r\ndelete the group without complaining, which may break this use case.\r\nThis use case was estimate to be unlikely and so it was accepted to\r\nsimply ignore the option.",
          "timestamp": "2020-11-11T18:05:13+01:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/008580e3316ad48b56f2385d245398ac0c78a49b",
          "distinct": true,
          "tree_id": "1d7c58ee452f0c10fd2c90a385a73b83193f1b88"
        },
        "date": 1605115318484,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 2.4682220282797114,
            "unit": "iter/sec",
            "range": "stddev: 0.019620",
            "group": "engine",
            "extra": "mean: 405.15 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.5576266286553747,
            "unit": "iter/sec",
            "range": "stddev: 0.048183",
            "group": "engine",
            "extra": "mean: 1.7933 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.5872227808681616,
            "unit": "iter/sec",
            "range": "stddev: 0.090018",
            "group": "engine",
            "extra": "mean: 1.7029 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.13659287038615917,
            "unit": "iter/sec",
            "range": "stddev: 0.23198",
            "group": "engine",
            "extra": "mean: 7.3210 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.142112371964971,
            "unit": "iter/sec",
            "range": "stddev: 0.11743",
            "group": "engine",
            "extra": "mean: 7.0367 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 1.5002788922442776,
            "unit": "iter/sec",
            "range": "stddev: 0.058373",
            "group": "engine",
            "extra": "mean: 666.54 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.3421196008195662,
            "unit": "iter/sec",
            "range": "stddev: 0.087880",
            "group": "engine",
            "extra": "mean: 2.9230 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.3740269316281819,
            "unit": "iter/sec",
            "range": "stddev: 0.097597",
            "group": "engine",
            "extra": "mean: 2.6736 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.10462515365926454,
            "unit": "iter/sec",
            "range": "stddev: 0.12533",
            "group": "engine",
            "extra": "mean: 9.5579 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.11612086867136917,
            "unit": "iter/sec",
            "range": "stddev: 0.15211",
            "group": "engine",
            "extra": "mean: 8.6117 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.7494499933787266,
            "unit": "iter/sec",
            "range": "stddev: 0.053813",
            "group": "import-export",
            "extra": "mean: 363.71 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.3779671531765016,
            "unit": "iter/sec",
            "range": "stddev: 0.049919",
            "group": "import-export",
            "extra": "mean: 420.53 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 0.12644335206903096,
            "unit": "iter/sec",
            "range": "stddev: 0.21392",
            "group": "import-export",
            "extra": "mean: 7.9087 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 0.12583773190764896,
            "unit": "iter/sec",
            "range": "stddev: 0.13866",
            "group": "import-export",
            "extra": "mean: 7.9467 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 85.0790213482176,
            "unit": "iter/sec",
            "range": "stddev: 0.0017074",
            "group": "node",
            "extra": "mean: 11.754 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 39.026896433172034,
            "unit": "iter/sec",
            "range": "stddev: 0.0023067",
            "group": "node",
            "extra": "mean: 25.623 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 39.04865080112086,
            "unit": "iter/sec",
            "range": "stddev: 0.0014969",
            "group": "node",
            "extra": "mean: 25.609 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 46.185218579131,
            "unit": "iter/sec",
            "range": "stddev: 0.0024258",
            "group": "node",
            "extra": "mean: 21.652 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 24.181683078760777,
            "unit": "iter/sec",
            "range": "stddev: 0.0038269",
            "group": "node",
            "extra": "mean: 41.354 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 24.086067088442494,
            "unit": "iter/sec",
            "range": "stddev: 0.0048142",
            "group": "node",
            "extra": "mean: 41.518 msec\nrounds: 100"
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
          "id": "bd197f31eb4ccf9a84ed2634cece62a74065c54a",
          "message": "Archive export refactor (2) (#4534)\n\nThis PR builds on #4448,\r\nwith the goal of improving both the export writer API\r\n(allowing for \"streamed\" data writing)\r\nand performance of the export process (CPU and memory usage).\r\n\r\nThe writer is now used as a context manager,\r\nrather than passing all data to it after extraction of the data from the AiiDA database.\r\nThis means it is called throughout the export process,\r\nand will allow for less data to be kept in RAM when moving to a new archive format.\r\n\r\nThe number of database queries has also been reduced, resulting in a faster process.\r\n\r\nLastly, code for read/writes to the archive has been moved to the https://github.com/aiidateam/archive-path package.\r\nThis standardises the interface for both zip and tar, and\r\nespecially for export to tar, provides much improved performance,\r\nsince the data is now written directly to the archive\r\n(rather than writing to a folder then only compressing at the end).\r\n\r\nCo-authored-by: Leopold Talirz <leopold.talirz@gmail.com>",
          "timestamp": "2020-11-12T11:45:40+01:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/bd197f31eb4ccf9a84ed2634cece62a74065c54a",
          "distinct": true,
          "tree_id": "d064e44ee6075f0963c5e03671cecb3bc9e0346b"
        },
        "date": 1605178842539,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 2.8031220681366857,
            "unit": "iter/sec",
            "range": "stddev: 0.014582",
            "group": "engine",
            "extra": "mean: 356.75 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.6245186720619776,
            "unit": "iter/sec",
            "range": "stddev: 0.061695",
            "group": "engine",
            "extra": "mean: 1.6012 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.6809701875036723,
            "unit": "iter/sec",
            "range": "stddev: 0.059033",
            "group": "engine",
            "extra": "mean: 1.4685 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.15039823743998124,
            "unit": "iter/sec",
            "range": "stddev: 0.28098",
            "group": "engine",
            "extra": "mean: 6.6490 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.16857655318348308,
            "unit": "iter/sec",
            "range": "stddev: 0.23399",
            "group": "engine",
            "extra": "mean: 5.9320 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 1.5413271128881072,
            "unit": "iter/sec",
            "range": "stddev: 0.068007",
            "group": "engine",
            "extra": "mean: 648.79 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.3833293976246016,
            "unit": "iter/sec",
            "range": "stddev: 0.092203",
            "group": "engine",
            "extra": "mean: 2.6087 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.3909659783970735,
            "unit": "iter/sec",
            "range": "stddev: 0.10909",
            "group": "engine",
            "extra": "mean: 2.5578 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.11654374244141286,
            "unit": "iter/sec",
            "range": "stddev: 0.64500",
            "group": "engine",
            "extra": "mean: 8.5805 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.12977504600796078,
            "unit": "iter/sec",
            "range": "stddev: 0.22968",
            "group": "engine",
            "extra": "mean: 7.7056 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.3823983894722405,
            "unit": "iter/sec",
            "range": "stddev: 0.058849",
            "group": "import-export",
            "extra": "mean: 419.75 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.1133757418396724,
            "unit": "iter/sec",
            "range": "stddev: 0.055078",
            "group": "import-export",
            "extra": "mean: 473.18 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 0.14155943466263446,
            "unit": "iter/sec",
            "range": "stddev: 0.14710",
            "group": "import-export",
            "extra": "mean: 7.0642 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 0.14001791671432545,
            "unit": "iter/sec",
            "range": "stddev: 0.28747",
            "group": "import-export",
            "extra": "mean: 7.1419 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 95.02314997691848,
            "unit": "iter/sec",
            "range": "stddev: 0.00044427",
            "group": "node",
            "extra": "mean: 10.524 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 42.0910362812987,
            "unit": "iter/sec",
            "range": "stddev: 0.0010074",
            "group": "node",
            "extra": "mean: 23.758 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 42.18653442405432,
            "unit": "iter/sec",
            "range": "stddev: 0.00097585",
            "group": "node",
            "extra": "mean: 23.704 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 49.49970350196839,
            "unit": "iter/sec",
            "range": "stddev: 0.0016593",
            "group": "node",
            "extra": "mean: 20.202 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 26.123945700407546,
            "unit": "iter/sec",
            "range": "stddev: 0.0018587",
            "group": "node",
            "extra": "mean: 38.279 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 24.94354783114432,
            "unit": "iter/sec",
            "range": "stddev: 0.019141",
            "group": "node",
            "extra": "mean: 40.091 msec\nrounds: 100"
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
          "id": "520bdbf10b2f518717b14ba3a2e429d487c83c66",
          "message": "Improve mypy type checking (#4553)\n\nThis commit moves the mypy execution to run in the full aiida-core python environment.\r\n\r\nCurrently, the mypy in the pre-commit is used as a \"non-local\" import\r\nand adds the blanket `--ignore-missing-imports` flag.\r\nThis greatly reduces the effectiveness of the type checking, because it does not check any types from classes/functions imported from third-party packages.\r\n\r\nSimilarly, adding `check_untyped_defs = True` improves the checking coverage\r\n(see https://mypy.readthedocs.io/en/stable/common_issues.html#no-errors-reported-for-obviously-wrong-code).",
          "timestamp": "2020-11-12T13:58:05+01:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/520bdbf10b2f518717b14ba3a2e429d487c83c66",
          "distinct": true,
          "tree_id": "8287d3d98728798a9459e7bf74cda3d4053b1e3d"
        },
        "date": 1605186675820,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.3817969729583846,
            "unit": "iter/sec",
            "range": "stddev: 0.010039",
            "group": "engine",
            "extra": "mean: 295.70 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.7294465630708876,
            "unit": "iter/sec",
            "range": "stddev: 0.039921",
            "group": "engine",
            "extra": "mean: 1.3709 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.7986366529920753,
            "unit": "iter/sec",
            "range": "stddev: 0.038171",
            "group": "engine",
            "extra": "mean: 1.2521 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.17488916202431495,
            "unit": "iter/sec",
            "range": "stddev: 0.14891",
            "group": "engine",
            "extra": "mean: 5.7179 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.1845018557924053,
            "unit": "iter/sec",
            "range": "stddev: 0.12499",
            "group": "engine",
            "extra": "mean: 5.4200 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 1.9174996588629165,
            "unit": "iter/sec",
            "range": "stddev: 0.057478",
            "group": "engine",
            "extra": "mean: 521.51 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.44754783916424146,
            "unit": "iter/sec",
            "range": "stddev: 0.047760",
            "group": "engine",
            "extra": "mean: 2.2344 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.5011688142564336,
            "unit": "iter/sec",
            "range": "stddev: 0.072006",
            "group": "engine",
            "extra": "mean: 1.9953 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.13433663846832142,
            "unit": "iter/sec",
            "range": "stddev: 0.12008",
            "group": "engine",
            "extra": "mean: 7.4440 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.14999375500851003,
            "unit": "iter/sec",
            "range": "stddev: 0.15223",
            "group": "engine",
            "extra": "mean: 6.6669 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.7416778572836256,
            "unit": "iter/sec",
            "range": "stddev: 0.045858",
            "group": "import-export",
            "extra": "mean: 364.74 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.4135541935557367,
            "unit": "iter/sec",
            "range": "stddev: 0.049316",
            "group": "import-export",
            "extra": "mean: 414.33 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 0.16348882384508498,
            "unit": "iter/sec",
            "range": "stddev: 0.053017",
            "group": "import-export",
            "extra": "mean: 6.1166 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 0.16123486165007267,
            "unit": "iter/sec",
            "range": "stddev: 0.066488",
            "group": "import-export",
            "extra": "mean: 6.2021 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 110.73314272217182,
            "unit": "iter/sec",
            "range": "stddev: 0.00058858",
            "group": "node",
            "extra": "mean: 9.0307 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 49.76180214620857,
            "unit": "iter/sec",
            "range": "stddev: 0.0014171",
            "group": "node",
            "extra": "mean: 20.096 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 48.694561642703924,
            "unit": "iter/sec",
            "range": "stddev: 0.0013774",
            "group": "node",
            "extra": "mean: 20.536 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 58.77626579144911,
            "unit": "iter/sec",
            "range": "stddev: 0.0014998",
            "group": "node",
            "extra": "mean: 17.014 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 32.26416802246783,
            "unit": "iter/sec",
            "range": "stddev: 0.0015218",
            "group": "node",
            "extra": "mean: 30.994 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 31.45972070294572,
            "unit": "iter/sec",
            "range": "stddev: 0.0021109",
            "group": "node",
            "extra": "mean: 31.787 msec\nrounds: 100"
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
          "id": "def9a0300b92ea8a844ab4b11523e3721269aac4",
          "message": "Improve archive import memory usage (#4559)\n\nThis commit is a small iterative improvement to the archive import logic,\r\nadded to reduce memory overhead,\r\nby reducing the number of variables in memory at any one time",
          "timestamp": "2020-11-12T21:27:03+01:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/def9a0300b92ea8a844ab4b11523e3721269aac4",
          "distinct": true,
          "tree_id": "82c487e7d012a59fd2139dc8b505d82b71a0a560"
        },
        "date": 1605213691743,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.1038135096248016,
            "unit": "iter/sec",
            "range": "stddev: 0.016498",
            "group": "engine",
            "extra": "mean: 322.18 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.6676481225372113,
            "unit": "iter/sec",
            "range": "stddev: 0.058320",
            "group": "engine",
            "extra": "mean: 1.4978 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.7079259543754989,
            "unit": "iter/sec",
            "range": "stddev: 0.068827",
            "group": "engine",
            "extra": "mean: 1.4126 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.1589417429320002,
            "unit": "iter/sec",
            "range": "stddev: 0.16558",
            "group": "engine",
            "extra": "mean: 6.2916 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.1670208118450195,
            "unit": "iter/sec",
            "range": "stddev: 0.13240",
            "group": "engine",
            "extra": "mean: 5.9873 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 1.7286340387258117,
            "unit": "iter/sec",
            "range": "stddev: 0.045378",
            "group": "engine",
            "extra": "mean: 578.49 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.40176416239514917,
            "unit": "iter/sec",
            "range": "stddev: 0.056940",
            "group": "engine",
            "extra": "mean: 2.4890 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.44353922624296255,
            "unit": "iter/sec",
            "range": "stddev: 0.11648",
            "group": "engine",
            "extra": "mean: 2.2546 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.11974552280317297,
            "unit": "iter/sec",
            "range": "stddev: 0.17120",
            "group": "engine",
            "extra": "mean: 8.3510 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.13256718281853858,
            "unit": "iter/sec",
            "range": "stddev: 0.17269",
            "group": "engine",
            "extra": "mean: 7.5433 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.4254424126109853,
            "unit": "iter/sec",
            "range": "stddev: 0.053929",
            "group": "import-export",
            "extra": "mean: 412.30 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.125779048884854,
            "unit": "iter/sec",
            "range": "stddev: 0.050881",
            "group": "import-export",
            "extra": "mean: 470.42 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 0.14379896498549227,
            "unit": "iter/sec",
            "range": "stddev: 0.18349",
            "group": "import-export",
            "extra": "mean: 6.9542 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 0.14529909236670638,
            "unit": "iter/sec",
            "range": "stddev: 0.13263",
            "group": "import-export",
            "extra": "mean: 6.8824 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 100.81071808103678,
            "unit": "iter/sec",
            "range": "stddev: 0.00066178",
            "group": "node",
            "extra": "mean: 9.9196 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 46.81996652377535,
            "unit": "iter/sec",
            "range": "stddev: 0.0012539",
            "group": "node",
            "extra": "mean: 21.358 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 45.892241750673655,
            "unit": "iter/sec",
            "range": "stddev: 0.0018186",
            "group": "node",
            "extra": "mean: 21.790 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 53.01856929796526,
            "unit": "iter/sec",
            "range": "stddev: 0.0018689",
            "group": "node",
            "extra": "mean: 18.861 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 27.39875221485053,
            "unit": "iter/sec",
            "range": "stddev: 0.017843",
            "group": "node",
            "extra": "mean: 36.498 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 28.827196131233176,
            "unit": "iter/sec",
            "range": "stddev: 0.0027641",
            "group": "node",
            "extra": "mean: 34.689 msec\nrounds: 100"
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
          "id": "810dc566b8280721aab3e38fea89dda312a25a82",
          "message": "Update archive version: 0.9 -> 0.10 (#4561)\n\nFixes a bug whereby archives created with the latest code\r\nfail to import in the last v1.4.2 release (if they contain group extras).\r\nThis update imposes that these new archives are no longer compatible with v1.4.2",
          "timestamp": "2020-11-13T11:20:09+01:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/810dc566b8280721aab3e38fea89dda312a25a82",
          "distinct": true,
          "tree_id": "d9be65982e8d55efbb53de7291ce634fd8a22b78"
        },
        "date": 1605263839648,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 2.5317775021482762,
            "unit": "iter/sec",
            "range": "stddev: 0.0068873",
            "group": "engine",
            "extra": "mean: 394.98 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.544874097745494,
            "unit": "iter/sec",
            "range": "stddev: 0.073130",
            "group": "engine",
            "extra": "mean: 1.8353 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.6004137640618677,
            "unit": "iter/sec",
            "range": "stddev: 0.052600",
            "group": "engine",
            "extra": "mean: 1.6655 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.13432765439399716,
            "unit": "iter/sec",
            "range": "stddev: 0.23221",
            "group": "engine",
            "extra": "mean: 7.4445 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.14037986062781307,
            "unit": "iter/sec",
            "range": "stddev: 0.17422",
            "group": "engine",
            "extra": "mean: 7.1235 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 1.4404185926722597,
            "unit": "iter/sec",
            "range": "stddev: 0.059161",
            "group": "engine",
            "extra": "mean: 694.24 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.3394637044800194,
            "unit": "iter/sec",
            "range": "stddev: 0.082995",
            "group": "engine",
            "extra": "mean: 2.9458 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.3753496426353175,
            "unit": "iter/sec",
            "range": "stddev: 0.089820",
            "group": "engine",
            "extra": "mean: 2.6642 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.10402324395158584,
            "unit": "iter/sec",
            "range": "stddev: 0.12586",
            "group": "engine",
            "extra": "mean: 9.6132 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.11401374314953612,
            "unit": "iter/sec",
            "range": "stddev: 0.16025",
            "group": "engine",
            "extra": "mean: 8.7709 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 1.942054223177421,
            "unit": "iter/sec",
            "range": "stddev: 0.054459",
            "group": "import-export",
            "extra": "mean: 514.92 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 1.6806015438280222,
            "unit": "iter/sec",
            "range": "stddev: 0.058162",
            "group": "import-export",
            "extra": "mean: 595.03 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 0.11964562438774355,
            "unit": "iter/sec",
            "range": "stddev: 0.048692",
            "group": "import-export",
            "extra": "mean: 8.3580 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 0.1180150574088798,
            "unit": "iter/sec",
            "range": "stddev: 0.093871",
            "group": "import-export",
            "extra": "mean: 8.4735 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 81.24215669940037,
            "unit": "iter/sec",
            "range": "stddev: 0.0014065",
            "group": "node",
            "extra": "mean: 12.309 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 36.79747774308113,
            "unit": "iter/sec",
            "range": "stddev: 0.0038129",
            "group": "node",
            "extra": "mean: 27.176 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 38.212379476490355,
            "unit": "iter/sec",
            "range": "stddev: 0.0021223",
            "group": "node",
            "extra": "mean: 26.170 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 44.03887537008407,
            "unit": "iter/sec",
            "range": "stddev: 0.0018151",
            "group": "node",
            "extra": "mean: 22.707 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 22.777795202284967,
            "unit": "iter/sec",
            "range": "stddev: 0.0028984",
            "group": "node",
            "extra": "mean: 43.902 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 20.992858273285734,
            "unit": "iter/sec",
            "range": "stddev: 0.021949",
            "group": "node",
            "extra": "mean: 47.635 msec\nrounds: 100"
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
          "id": "62ed6437bd041b7fb5808566cf942f1b3865d37f",
          "message": "REST API: Add full_types_count as new entry point\n\nThis feature returns a namespace tree of the available node types in the\ndatabase (data node_types + process process_types) with the addition of\na count at each leaf / branch. It also has the option of doing so for a\nsingle user, if the pk is provided as an option.",
          "timestamp": "2020-11-13T15:34:26+01:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/62ed6437bd041b7fb5808566cf942f1b3865d37f",
          "distinct": true,
          "tree_id": "3ec2791c4d74d16692749f51444de6c0384a94c5"
        },
        "date": 1605279054973,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 2.566340019093718,
            "unit": "iter/sec",
            "range": "stddev: 0.0084851",
            "group": "engine",
            "extra": "mean: 389.66 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.559501887577109,
            "unit": "iter/sec",
            "range": "stddev: 0.062755",
            "group": "engine",
            "extra": "mean: 1.7873 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.6089618216391031,
            "unit": "iter/sec",
            "range": "stddev: 0.041577",
            "group": "engine",
            "extra": "mean: 1.6421 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.13807074583852302,
            "unit": "iter/sec",
            "range": "stddev: 0.21711",
            "group": "engine",
            "extra": "mean: 7.2427 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.14291729218840507,
            "unit": "iter/sec",
            "range": "stddev: 0.28911",
            "group": "engine",
            "extra": "mean: 6.9971 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 1.502134971892739,
            "unit": "iter/sec",
            "range": "stddev: 0.011479",
            "group": "engine",
            "extra": "mean: 665.72 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.3303013763626283,
            "unit": "iter/sec",
            "range": "stddev: 0.080310",
            "group": "engine",
            "extra": "mean: 3.0275 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.3768731203106412,
            "unit": "iter/sec",
            "range": "stddev: 0.071759",
            "group": "engine",
            "extra": "mean: 2.6534 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.10403905112350872,
            "unit": "iter/sec",
            "range": "stddev: 0.14870",
            "group": "engine",
            "extra": "mean: 9.6118 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.11600752144398538,
            "unit": "iter/sec",
            "range": "stddev: 0.14741",
            "group": "engine",
            "extra": "mean: 8.6201 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.0463645260877334,
            "unit": "iter/sec",
            "range": "stddev: 0.061851",
            "group": "import-export",
            "extra": "mean: 488.67 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 1.7964215994917387,
            "unit": "iter/sec",
            "range": "stddev: 0.058379",
            "group": "import-export",
            "extra": "mean: 556.66 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 0.12320193600936545,
            "unit": "iter/sec",
            "range": "stddev: 0.098784",
            "group": "import-export",
            "extra": "mean: 8.1168 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 0.12929377710348283,
            "unit": "iter/sec",
            "range": "stddev: 0.27163",
            "group": "import-export",
            "extra": "mean: 7.7343 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 95.74741045697441,
            "unit": "iter/sec",
            "range": "stddev: 0.00096127",
            "group": "node",
            "extra": "mean: 10.444 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 43.57669212911299,
            "unit": "iter/sec",
            "range": "stddev: 0.0014523",
            "group": "node",
            "extra": "mean: 22.948 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 43.17070551827347,
            "unit": "iter/sec",
            "range": "stddev: 0.0016575",
            "group": "node",
            "extra": "mean: 23.164 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 52.53263657417939,
            "unit": "iter/sec",
            "range": "stddev: 0.0011623",
            "group": "node",
            "extra": "mean: 19.036 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 26.480217800769783,
            "unit": "iter/sec",
            "range": "stddev: 0.0027207",
            "group": "node",
            "extra": "mean: 37.764 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 25.55554005952722,
            "unit": "iter/sec",
            "range": "stddev: 0.018102",
            "group": "node",
            "extra": "mean: 39.130 msec\nrounds: 100"
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
          "id": "425636023e85d237ca4f13d4591d2595e934e5c9",
          "message": "Merge remote-tracking branch 'origin/master' into develop",
          "timestamp": "2020-11-13T16:57:45+01:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/425636023e85d237ca4f13d4591d2595e934e5c9",
          "distinct": true,
          "tree_id": "156b008bbaf87baac6914c1e04b13be7b2c58c15"
        },
        "date": 1605283932874,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.171021858756155,
            "unit": "iter/sec",
            "range": "stddev: 0.015589",
            "group": "engine",
            "extra": "mean: 315.36 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.6975588274940188,
            "unit": "iter/sec",
            "range": "stddev: 0.074956",
            "group": "engine",
            "extra": "mean: 1.4336 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.7689161816070251,
            "unit": "iter/sec",
            "range": "stddev: 0.050215",
            "group": "engine",
            "extra": "mean: 1.3005 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.1724869970400007,
            "unit": "iter/sec",
            "range": "stddev: 0.18115",
            "group": "engine",
            "extra": "mean: 5.7975 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.18191596029735632,
            "unit": "iter/sec",
            "range": "stddev: 0.13826",
            "group": "engine",
            "extra": "mean: 5.4970 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 1.8600948833395652,
            "unit": "iter/sec",
            "range": "stddev: 0.048637",
            "group": "engine",
            "extra": "mean: 537.61 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.4323501487299889,
            "unit": "iter/sec",
            "range": "stddev: 0.061818",
            "group": "engine",
            "extra": "mean: 2.3129 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.47941842429805087,
            "unit": "iter/sec",
            "range": "stddev: 0.068226",
            "group": "engine",
            "extra": "mean: 2.0859 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.1313511065530258,
            "unit": "iter/sec",
            "range": "stddev: 0.16136",
            "group": "engine",
            "extra": "mean: 7.6132 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.14556093617569377,
            "unit": "iter/sec",
            "range": "stddev: 0.15885",
            "group": "engine",
            "extra": "mean: 6.8700 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.6847430697961356,
            "unit": "iter/sec",
            "range": "stddev: 0.047021",
            "group": "import-export",
            "extra": "mean: 372.48 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.3391369824745847,
            "unit": "iter/sec",
            "range": "stddev: 0.044393",
            "group": "import-export",
            "extra": "mean: 427.51 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 0.15958271731259913,
            "unit": "iter/sec",
            "range": "stddev: 0.11080",
            "group": "import-export",
            "extra": "mean: 6.2663 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 0.1569843329832566,
            "unit": "iter/sec",
            "range": "stddev: 0.084083",
            "group": "import-export",
            "extra": "mean: 6.3701 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 108.89708099842744,
            "unit": "iter/sec",
            "range": "stddev: 0.00054759",
            "group": "node",
            "extra": "mean: 9.1830 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 48.932063991153484,
            "unit": "iter/sec",
            "range": "stddev: 0.0010278",
            "group": "node",
            "extra": "mean: 20.436 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 47.341358001572345,
            "unit": "iter/sec",
            "range": "stddev: 0.0039878",
            "group": "node",
            "extra": "mean: 21.123 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 58.48324858607629,
            "unit": "iter/sec",
            "range": "stddev: 0.0013727",
            "group": "node",
            "extra": "mean: 17.099 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 31.643347896739176,
            "unit": "iter/sec",
            "range": "stddev: 0.0019197",
            "group": "node",
            "extra": "mean: 31.602 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 30.11907719028072,
            "unit": "iter/sec",
            "range": "stddev: 0.017372",
            "group": "node",
            "extra": "mean: 33.202 msec\nrounds: 100"
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
          "id": "29c54b59a2906a3315520786814234db63aee194",
          "message": "Dependencies: bump cryptography to 3.2 in `requirements` (#4520)\n\nBumps `cryptography` from 2.8 to 3.2.\r\n\r\nSigned-off-by: dependabot[bot] <support@github.com>\r\nCo-authored-by: Sebastiaan Huber <mail@sphuber.net>",
          "timestamp": "2020-11-16T08:16:44+01:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/29c54b59a2906a3315520786814234db63aee194",
          "distinct": true,
          "tree_id": "ba71cd220b10968e57d68599dbac2939c62c9980"
        },
        "date": 1605512089458,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 2.2610825393737253,
            "unit": "iter/sec",
            "range": "stddev: 0.015543",
            "group": "engine",
            "extra": "mean: 442.27 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.5000379627321196,
            "unit": "iter/sec",
            "range": "stddev: 0.067005",
            "group": "engine",
            "extra": "mean: 1.9998 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.5363819745421535,
            "unit": "iter/sec",
            "range": "stddev: 0.056625",
            "group": "engine",
            "extra": "mean: 1.8643 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.1278052240843423,
            "unit": "iter/sec",
            "range": "stddev: 0.21898",
            "group": "engine",
            "extra": "mean: 7.8244 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.13147436419288502,
            "unit": "iter/sec",
            "range": "stddev: 0.21774",
            "group": "engine",
            "extra": "mean: 7.6060 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 1.341780256176742,
            "unit": "iter/sec",
            "range": "stddev: 0.023865",
            "group": "engine",
            "extra": "mean: 745.28 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.3145878140826107,
            "unit": "iter/sec",
            "range": "stddev: 0.14305",
            "group": "engine",
            "extra": "mean: 3.1788 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.33876688756648254,
            "unit": "iter/sec",
            "range": "stddev: 0.12496",
            "group": "engine",
            "extra": "mean: 2.9519 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.0947126702737225,
            "unit": "iter/sec",
            "range": "stddev: 0.33319",
            "group": "engine",
            "extra": "mean: 10.558 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.10425718876577396,
            "unit": "iter/sec",
            "range": "stddev: 0.17592",
            "group": "engine",
            "extra": "mean: 9.5917 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 1.8239023369752487,
            "unit": "iter/sec",
            "range": "stddev: 0.059413",
            "group": "import-export",
            "extra": "mean: 548.27 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 1.7045900046347586,
            "unit": "iter/sec",
            "range": "stddev: 0.016745",
            "group": "import-export",
            "extra": "mean: 586.65 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 0.10949255032494806,
            "unit": "iter/sec",
            "range": "stddev: 0.44665",
            "group": "import-export",
            "extra": "mean: 9.1330 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 0.1170073275430233,
            "unit": "iter/sec",
            "range": "stddev: 0.10234",
            "group": "import-export",
            "extra": "mean: 8.5465 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 83.31377549386849,
            "unit": "iter/sec",
            "range": "stddev: 0.0015798",
            "group": "node",
            "extra": "mean: 12.003 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 39.51696957030645,
            "unit": "iter/sec",
            "range": "stddev: 0.0023692",
            "group": "node",
            "extra": "mean: 25.306 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 37.05210697977979,
            "unit": "iter/sec",
            "range": "stddev: 0.0031513",
            "group": "node",
            "extra": "mean: 26.989 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 44.48533684893514,
            "unit": "iter/sec",
            "range": "stddev: 0.0035475",
            "group": "node",
            "extra": "mean: 22.479 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 24.336008549133755,
            "unit": "iter/sec",
            "range": "stddev: 0.0034938",
            "group": "node",
            "extra": "mean: 41.091 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 23.65336425925759,
            "unit": "iter/sec",
            "range": "stddev: 0.0032921",
            "group": "node",
            "extra": "mean: 42.277 msec\nrounds: 100"
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
          "id": "49cd0e7562e9598e63b14538ea03c76ca823468e",
          "message": "CI: remove `run-on-comment` job in benchmark workflow (#4569)\n\nThis job is failing due to this change:\r\nhttps://github.blog/changelog/2020-10-01-github-actions-deprecating-set-env-and-add-path-commands/\r\nIt's not really used, so lets just remove it",
          "timestamp": "2020-11-17T08:15:23+01:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/49cd0e7562e9598e63b14538ea03c76ca823468e",
          "distinct": true,
          "tree_id": "802e7a7c893085b21e8ca9ed7e13cc0edac95264"
        },
        "date": 1605598231950,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 2.751364399060456,
            "unit": "iter/sec",
            "range": "stddev: 0.010846",
            "group": "engine",
            "extra": "mean: 363.46 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.6032337337097594,
            "unit": "iter/sec",
            "range": "stddev: 0.066437",
            "group": "engine",
            "extra": "mean: 1.6577 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.6548245355715411,
            "unit": "iter/sec",
            "range": "stddev: 0.043136",
            "group": "engine",
            "extra": "mean: 1.5271 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.15013903328126946,
            "unit": "iter/sec",
            "range": "stddev: 0.17013",
            "group": "engine",
            "extra": "mean: 6.6605 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.15717279977413864,
            "unit": "iter/sec",
            "range": "stddev: 0.16473",
            "group": "engine",
            "extra": "mean: 6.3624 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 1.6672462820578773,
            "unit": "iter/sec",
            "range": "stddev: 0.016804",
            "group": "engine",
            "extra": "mean: 599.79 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.37648221352415245,
            "unit": "iter/sec",
            "range": "stddev: 0.067135",
            "group": "engine",
            "extra": "mean: 2.6562 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.42281380918204936,
            "unit": "iter/sec",
            "range": "stddev: 0.060311",
            "group": "engine",
            "extra": "mean: 2.3651 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.11964863802346536,
            "unit": "iter/sec",
            "range": "stddev: 0.14161",
            "group": "engine",
            "extra": "mean: 8.3578 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.1329417505037766,
            "unit": "iter/sec",
            "range": "stddev: 0.10348",
            "group": "engine",
            "extra": "mean: 7.5221 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.2582266914681135,
            "unit": "iter/sec",
            "range": "stddev: 0.055460",
            "group": "import-export",
            "extra": "mean: 442.83 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 1.9686259944029632,
            "unit": "iter/sec",
            "range": "stddev: 0.057787",
            "group": "import-export",
            "extra": "mean: 507.97 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 0.13890289987006185,
            "unit": "iter/sec",
            "range": "stddev: 0.048147",
            "group": "import-export",
            "extra": "mean: 7.1993 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 0.13703944014141498,
            "unit": "iter/sec",
            "range": "stddev: 0.049137",
            "group": "import-export",
            "extra": "mean: 7.2972 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 99.52414589794861,
            "unit": "iter/sec",
            "range": "stddev: 0.00051704",
            "group": "node",
            "extra": "mean: 10.048 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 46.02807067643089,
            "unit": "iter/sec",
            "range": "stddev: 0.0011943",
            "group": "node",
            "extra": "mean: 21.726 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 45.15742584914865,
            "unit": "iter/sec",
            "range": "stddev: 0.00097211",
            "group": "node",
            "extra": "mean: 22.145 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 53.49473413592522,
            "unit": "iter/sec",
            "range": "stddev: 0.0012796",
            "group": "node",
            "extra": "mean: 18.693 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 27.19284164802869,
            "unit": "iter/sec",
            "range": "stddev: 0.018354",
            "group": "node",
            "extra": "mean: 36.774 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 28.504270376678893,
            "unit": "iter/sec",
            "range": "stddev: 0.0026163",
            "group": "node",
            "extra": "mean: 35.082 msec\nrounds: 100"
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
          "id": "4c8f1b07b9050f85f7b2c2c90caa1df6e78c2225",
          "message": "Docs: update citations with AiiDA workflows paper (#4568)\n\nCitation for the latest paper on the engine is added to the README and\r\nthe documentation index page. The paper in `aiida/__init__.py` is also\r\nupdated which was still referencing the original publication of 2016.",
          "timestamp": "2020-11-17T15:31:56+01:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/4c8f1b07b9050f85f7b2c2c90caa1df6e78c2225",
          "distinct": true,
          "tree_id": "b102900c9aeb98e7c03f8e009e1212be9be6d4c5"
        },
        "date": 1605624498298,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 2.6128058302157857,
            "unit": "iter/sec",
            "range": "stddev: 0.019432",
            "group": "engine",
            "extra": "mean: 382.73 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.5873925072181717,
            "unit": "iter/sec",
            "range": "stddev: 0.10681",
            "group": "engine",
            "extra": "mean: 1.7024 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.5942459722995044,
            "unit": "iter/sec",
            "range": "stddev: 0.089217",
            "group": "engine",
            "extra": "mean: 1.6828 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.13926421327631616,
            "unit": "iter/sec",
            "range": "stddev: 0.39577",
            "group": "engine",
            "extra": "mean: 7.1806 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.14512890514961974,
            "unit": "iter/sec",
            "range": "stddev: 0.21752",
            "group": "engine",
            "extra": "mean: 6.8904 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 1.6336507297247482,
            "unit": "iter/sec",
            "range": "stddev: 0.039072",
            "group": "engine",
            "extra": "mean: 612.13 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.34605157662368646,
            "unit": "iter/sec",
            "range": "stddev: 0.087251",
            "group": "engine",
            "extra": "mean: 2.8897 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.36844365627756803,
            "unit": "iter/sec",
            "range": "stddev: 0.099403",
            "group": "engine",
            "extra": "mean: 2.7141 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.10454271420169146,
            "unit": "iter/sec",
            "range": "stddev: 0.29580",
            "group": "engine",
            "extra": "mean: 9.5655 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.11556568749522615,
            "unit": "iter/sec",
            "range": "stddev: 0.27710",
            "group": "engine",
            "extra": "mean: 8.6531 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.1258480172493806,
            "unit": "iter/sec",
            "range": "stddev: 0.050911",
            "group": "import-export",
            "extra": "mean: 470.40 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 1.7986169707471045,
            "unit": "iter/sec",
            "range": "stddev: 0.046233",
            "group": "import-export",
            "extra": "mean: 555.98 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 0.12592632695145103,
            "unit": "iter/sec",
            "range": "stddev: 0.28078",
            "group": "import-export",
            "extra": "mean: 7.9412 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 0.1283840122166861,
            "unit": "iter/sec",
            "range": "stddev: 0.46162",
            "group": "import-export",
            "extra": "mean: 7.7891 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 90.16471885927116,
            "unit": "iter/sec",
            "range": "stddev: 0.0015595",
            "group": "node",
            "extra": "mean: 11.091 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 45.886263781022855,
            "unit": "iter/sec",
            "range": "stddev: 0.0018098",
            "group": "node",
            "extra": "mean: 21.793 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 39.74522702173161,
            "unit": "iter/sec",
            "range": "stddev: 0.0038930",
            "group": "node",
            "extra": "mean: 25.160 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 55.058533941463764,
            "unit": "iter/sec",
            "range": "stddev: 0.0019679",
            "group": "node",
            "extra": "mean: 18.162 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 28.056437053897948,
            "unit": "iter/sec",
            "range": "stddev: 0.0038494",
            "group": "node",
            "extra": "mean: 35.642 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 28.27936610573656,
            "unit": "iter/sec",
            "range": "stddev: 0.0037455",
            "group": "node",
            "extra": "mean: 35.361 msec\nrounds: 100"
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
          "id": "f04dbf13ed824f6e5724666d5bc39f7c2bad9cf4",
          "message": "Enforce verdi quicksetup --non-interactive (#4573)\n\nWhen in non-interactive mode, do not ask whether to use existing user/database",
          "timestamp": "2020-11-17T22:52:25+01:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/f04dbf13ed824f6e5724666d5bc39f7c2bad9cf4",
          "distinct": true,
          "tree_id": "bdb8af0519bb351a997d27e31083fedaa1435587"
        },
        "date": 1605650889576,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 2.7248557935604154,
            "unit": "iter/sec",
            "range": "stddev: 0.017329",
            "group": "engine",
            "extra": "mean: 366.99 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.5972672196045528,
            "unit": "iter/sec",
            "range": "stddev: 0.073829",
            "group": "engine",
            "extra": "mean: 1.6743 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.6538897694657503,
            "unit": "iter/sec",
            "range": "stddev: 0.052247",
            "group": "engine",
            "extra": "mean: 1.5293 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.14845291692159476,
            "unit": "iter/sec",
            "range": "stddev: 0.17801",
            "group": "engine",
            "extra": "mean: 6.7361 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.15600813163524616,
            "unit": "iter/sec",
            "range": "stddev: 0.15762",
            "group": "engine",
            "extra": "mean: 6.4099 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 1.657748050949127,
            "unit": "iter/sec",
            "range": "stddev: 0.010450",
            "group": "engine",
            "extra": "mean: 603.23 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.36760624362393474,
            "unit": "iter/sec",
            "range": "stddev: 0.074073",
            "group": "engine",
            "extra": "mean: 2.7203 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.41036678471228494,
            "unit": "iter/sec",
            "range": "stddev: 0.089793",
            "group": "engine",
            "extra": "mean: 2.4368 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.1103865952867059,
            "unit": "iter/sec",
            "range": "stddev: 0.32882",
            "group": "engine",
            "extra": "mean: 9.0591 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.11862313886892051,
            "unit": "iter/sec",
            "range": "stddev: 0.18104",
            "group": "engine",
            "extra": "mean: 8.4301 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.064984906718117,
            "unit": "iter/sec",
            "range": "stddev: 0.057068",
            "group": "import-export",
            "extra": "mean: 484.27 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 1.888171174045912,
            "unit": "iter/sec",
            "range": "stddev: 0.054017",
            "group": "import-export",
            "extra": "mean: 529.61 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 0.1308649705399588,
            "unit": "iter/sec",
            "range": "stddev: 0.056611",
            "group": "import-export",
            "extra": "mean: 7.6415 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 0.13139150812704403,
            "unit": "iter/sec",
            "range": "stddev: 0.10578",
            "group": "import-export",
            "extra": "mean: 7.6108 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 102.86250807144117,
            "unit": "iter/sec",
            "range": "stddev: 0.00062200",
            "group": "node",
            "extra": "mean: 9.7217 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 45.15148183314188,
            "unit": "iter/sec",
            "range": "stddev: 0.0016355",
            "group": "node",
            "extra": "mean: 22.148 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 44.794385109111154,
            "unit": "iter/sec",
            "range": "stddev: 0.0020357",
            "group": "node",
            "extra": "mean: 22.324 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 52.82976385617439,
            "unit": "iter/sec",
            "range": "stddev: 0.0017602",
            "group": "node",
            "extra": "mean: 18.929 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 27.575967327501953,
            "unit": "iter/sec",
            "range": "stddev: 0.0028683",
            "group": "node",
            "extra": "mean: 36.263 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 27.91616456421033,
            "unit": "iter/sec",
            "range": "stddev: 0.0030998",
            "group": "node",
            "extra": "mean: 35.822 msec\nrounds: 100"
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
          "id": "1c48d7147584dc3bcb5b8ee9190802fd0b701fe6",
          "message": "`SinglefileData`: add support for `pathlib.Path` for `file` argument (#3614)",
          "timestamp": "2020-11-18T09:59:17+01:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/1c48d7147584dc3bcb5b8ee9190802fd0b701fe6",
          "distinct": true,
          "tree_id": "efdbc3eaee626a05ed98d90d4859612d683060fe"
        },
        "date": 1605691065970,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 2.07817102920881,
            "unit": "iter/sec",
            "range": "stddev: 0.022376",
            "group": "engine",
            "extra": "mean: 481.19 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.45716596681455746,
            "unit": "iter/sec",
            "range": "stddev: 0.10691",
            "group": "engine",
            "extra": "mean: 2.1874 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.4901220872946172,
            "unit": "iter/sec",
            "range": "stddev: 0.15428",
            "group": "engine",
            "extra": "mean: 2.0403 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.11717482499320915,
            "unit": "iter/sec",
            "range": "stddev: 0.27663",
            "group": "engine",
            "extra": "mean: 8.5343 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.11976256606024918,
            "unit": "iter/sec",
            "range": "stddev: 0.33256",
            "group": "engine",
            "extra": "mean: 8.3499 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 1.14754398067163,
            "unit": "iter/sec",
            "range": "stddev: 0.092801",
            "group": "engine",
            "extra": "mean: 871.43 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.2812346766043469,
            "unit": "iter/sec",
            "range": "stddev: 0.21762",
            "group": "engine",
            "extra": "mean: 3.5557 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.31802647216391755,
            "unit": "iter/sec",
            "range": "stddev: 0.11713",
            "group": "engine",
            "extra": "mean: 3.1444 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.09228331563267061,
            "unit": "iter/sec",
            "range": "stddev: 0.25705",
            "group": "engine",
            "extra": "mean: 10.836 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.10416181244193211,
            "unit": "iter/sec",
            "range": "stddev: 0.22507",
            "group": "engine",
            "extra": "mean: 9.6004 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.1300229584363874,
            "unit": "iter/sec",
            "range": "stddev: 0.064907",
            "group": "import-export",
            "extra": "mean: 469.48 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 1.7738328172153772,
            "unit": "iter/sec",
            "range": "stddev: 0.060937",
            "group": "import-export",
            "extra": "mean: 563.75 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 0.11723248555413543,
            "unit": "iter/sec",
            "range": "stddev: 0.29293",
            "group": "import-export",
            "extra": "mean: 8.5301 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 0.12787276488987329,
            "unit": "iter/sec",
            "range": "stddev: 0.24063",
            "group": "import-export",
            "extra": "mean: 7.8203 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 82.30258637241322,
            "unit": "iter/sec",
            "range": "stddev: 0.0014044",
            "group": "node",
            "extra": "mean: 12.150 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 38.30120588671954,
            "unit": "iter/sec",
            "range": "stddev: 0.0015102",
            "group": "node",
            "extra": "mean: 26.109 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 36.34029422621231,
            "unit": "iter/sec",
            "range": "stddev: 0.0022466",
            "group": "node",
            "extra": "mean: 27.518 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 44.03470811995246,
            "unit": "iter/sec",
            "range": "stddev: 0.0019081",
            "group": "node",
            "extra": "mean: 22.709 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 24.02991465813734,
            "unit": "iter/sec",
            "range": "stddev: 0.0027559",
            "group": "node",
            "extra": "mean: 41.615 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 23.734495165408244,
            "unit": "iter/sec",
            "range": "stddev: 0.0035691",
            "group": "node",
            "extra": "mean: 42.133 msec\nrounds: 100"
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
          "id": "20996d1801d2e44f46f780fa162b823448bffee8",
          "message": "Fix `verdi --version` in editable mode (#4576)\n\nThis commit fixes a bug,\r\nwhereby click was using a version statically stored on install of the package.\r\nThis meant changes to `__version__` were not dynamically reflected.",
          "timestamp": "2020-11-18T11:37:27+01:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/20996d1801d2e44f46f780fa162b823448bffee8",
          "distinct": true,
          "tree_id": "0dc7341502b74de2a19923c70d33a1e636a2ada9"
        },
        "date": 1605696897293,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 2.439768899410044,
            "unit": "iter/sec",
            "range": "stddev: 0.019305",
            "group": "engine",
            "extra": "mean: 409.87 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.5297552666402044,
            "unit": "iter/sec",
            "range": "stddev: 0.090418",
            "group": "engine",
            "extra": "mean: 1.8877 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.5868797184464017,
            "unit": "iter/sec",
            "range": "stddev: 0.055778",
            "group": "engine",
            "extra": "mean: 1.7039 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.13053808872674094,
            "unit": "iter/sec",
            "range": "stddev: 0.22299",
            "group": "engine",
            "extra": "mean: 7.6606 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.13559108028887562,
            "unit": "iter/sec",
            "range": "stddev: 0.18859",
            "group": "engine",
            "extra": "mean: 7.3751 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 1.4228962329649135,
            "unit": "iter/sec",
            "range": "stddev: 0.021823",
            "group": "engine",
            "extra": "mean: 702.79 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.3274946428850438,
            "unit": "iter/sec",
            "range": "stddev: 0.081904",
            "group": "engine",
            "extra": "mean: 3.0535 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.36315898945438574,
            "unit": "iter/sec",
            "range": "stddev: 0.075909",
            "group": "engine",
            "extra": "mean: 2.7536 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.09987296362268659,
            "unit": "iter/sec",
            "range": "stddev: 0.15609",
            "group": "engine",
            "extra": "mean: 10.013 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.11119901733576941,
            "unit": "iter/sec",
            "range": "stddev: 0.14709",
            "group": "engine",
            "extra": "mean: 8.9929 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 1.8887607838985034,
            "unit": "iter/sec",
            "range": "stddev: 0.065301",
            "group": "import-export",
            "extra": "mean: 529.45 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 1.4356567154339352,
            "unit": "iter/sec",
            "range": "stddev: 0.061630",
            "group": "import-export",
            "extra": "mean: 696.55 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 0.11559597237652432,
            "unit": "iter/sec",
            "range": "stddev: 0.044733",
            "group": "import-export",
            "extra": "mean: 8.6508 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 0.11805916299224607,
            "unit": "iter/sec",
            "range": "stddev: 0.077311",
            "group": "import-export",
            "extra": "mean: 8.4703 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 88.3882077968852,
            "unit": "iter/sec",
            "range": "stddev: 0.00078041",
            "group": "node",
            "extra": "mean: 11.314 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 39.185509283298344,
            "unit": "iter/sec",
            "range": "stddev: 0.0023859",
            "group": "node",
            "extra": "mean: 25.520 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 39.52024748092041,
            "unit": "iter/sec",
            "range": "stddev: 0.0021173",
            "group": "node",
            "extra": "mean: 25.303 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 45.47400338786538,
            "unit": "iter/sec",
            "range": "stddev: 0.0016344",
            "group": "node",
            "extra": "mean: 21.991 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 23.577392401767213,
            "unit": "iter/sec",
            "range": "stddev: 0.0029447",
            "group": "node",
            "extra": "mean: 42.414 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 23.834095610115078,
            "unit": "iter/sec",
            "range": "stddev: 0.0030925",
            "group": "node",
            "extra": "mean: 41.957 msec\nrounds: 100"
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
          "id": "d29fb3be78c9b7be2e495b287c6dca8960bfe83d",
          "message": "Improve `verdi node delete` performance (#4575)\n\nThe `verdi node delete` process fully loaded all ORM objects at multiple stages\r\nduring the process, which is highly inefficient.\r\nThis commit ensures the process now only loads the PKs when possible.\r\nAs an example, the time to delete 100 \"empty\" nodes (no attributes/objects)\r\nis now reduced from ~32 seconds to ~5 seconds.",
          "timestamp": "2020-11-18T12:30:38+01:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/d29fb3be78c9b7be2e495b287c6dca8960bfe83d",
          "distinct": true,
          "tree_id": "ed6770a97de77ffa34675a9baa8f7f576b148652"
        },
        "date": 1605699986186,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 2.7457622863829605,
            "unit": "iter/sec",
            "range": "stddev: 0.0027557",
            "group": "engine",
            "extra": "mean: 364.20 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.5875564390116812,
            "unit": "iter/sec",
            "range": "stddev: 0.062656",
            "group": "engine",
            "extra": "mean: 1.7020 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.6445648883207483,
            "unit": "iter/sec",
            "range": "stddev: 0.050272",
            "group": "engine",
            "extra": "mean: 1.5514 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.14241169821745736,
            "unit": "iter/sec",
            "range": "stddev: 0.17774",
            "group": "engine",
            "extra": "mean: 7.0219 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.1494776715556423,
            "unit": "iter/sec",
            "range": "stddev: 0.16822",
            "group": "engine",
            "extra": "mean: 6.6900 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 1.5462381120619293,
            "unit": "iter/sec",
            "range": "stddev: 0.053817",
            "group": "engine",
            "extra": "mean: 646.73 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.3572669398937797,
            "unit": "iter/sec",
            "range": "stddev: 0.064028",
            "group": "engine",
            "extra": "mean: 2.7990 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.39822168548763887,
            "unit": "iter/sec",
            "range": "stddev: 0.064038",
            "group": "engine",
            "extra": "mean: 2.5112 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.10838748332149643,
            "unit": "iter/sec",
            "range": "stddev: 0.15764",
            "group": "engine",
            "extra": "mean: 9.2262 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.11887203986672606,
            "unit": "iter/sec",
            "range": "stddev: 0.16947",
            "group": "engine",
            "extra": "mean: 8.4124 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.1443353929197486,
            "unit": "iter/sec",
            "range": "stddev: 0.055597",
            "group": "import-export",
            "extra": "mean: 466.34 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 1.8996914615005458,
            "unit": "iter/sec",
            "range": "stddev: 0.055184",
            "group": "import-export",
            "extra": "mean: 526.40 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 0.13724962959026998,
            "unit": "iter/sec",
            "range": "stddev: 0.10044",
            "group": "import-export",
            "extra": "mean: 7.2860 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 0.13901734459023934,
            "unit": "iter/sec",
            "range": "stddev: 0.064657",
            "group": "import-export",
            "extra": "mean: 7.1933 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 95.78567218684132,
            "unit": "iter/sec",
            "range": "stddev: 0.00038986",
            "group": "node",
            "extra": "mean: 10.440 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 44.0232622527478,
            "unit": "iter/sec",
            "range": "stddev: 0.0011716",
            "group": "node",
            "extra": "mean: 22.715 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 43.02594338149722,
            "unit": "iter/sec",
            "range": "stddev: 0.0013102",
            "group": "node",
            "extra": "mean: 23.242 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 50.939740406203676,
            "unit": "iter/sec",
            "range": "stddev: 0.00090689",
            "group": "node",
            "extra": "mean: 19.631 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 26.056684294164747,
            "unit": "iter/sec",
            "range": "stddev: 0.017499",
            "group": "node",
            "extra": "mean: 38.378 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 27.365627475483443,
            "unit": "iter/sec",
            "range": "stddev: 0.0015416",
            "group": "node",
            "extra": "mean: 36.542 msec\nrounds: 100"
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
          "id": "17b77181d87abed9211fdaf1f432e00e276c1c11",
          "message": "`CalcJob`: add the `additional_retrieve_list` metadata option (#4437)\n\nThis new option allows one to specify additional files to be retrieved\r\non a per-instance basis, in addition to the files that are already\r\ndefined by the plugin to be retrieved. This was often implemented by\r\nplugin packages itself through a `settings` node that supported a key\r\nthat would allow a user to specify these additional files.\r\n\r\nSince this is a common use case, we implement this functionality on\r\n`aiida-core` instead to guarantee a consistent interface across plugins.",
          "timestamp": "2020-11-19T10:09:33+01:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/17b77181d87abed9211fdaf1f432e00e276c1c11",
          "distinct": true,
          "tree_id": "4ddaf98ee92f992d526af5998b66576f53d7b0bd"
        },
        "date": 1605777957675,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 2.6277863048859293,
            "unit": "iter/sec",
            "range": "stddev: 0.010334",
            "group": "engine",
            "extra": "mean: 380.55 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.5775456907698528,
            "unit": "iter/sec",
            "range": "stddev: 0.054015",
            "group": "engine",
            "extra": "mean: 1.7315 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.6435002831570477,
            "unit": "iter/sec",
            "range": "stddev: 0.049945",
            "group": "engine",
            "extra": "mean: 1.5540 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.13879960641026984,
            "unit": "iter/sec",
            "range": "stddev: 0.16765",
            "group": "engine",
            "extra": "mean: 7.2046 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.1429652383898499,
            "unit": "iter/sec",
            "range": "stddev: 0.25787",
            "group": "engine",
            "extra": "mean: 6.9947 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 1.4599513249366707,
            "unit": "iter/sec",
            "range": "stddev: 0.064024",
            "group": "engine",
            "extra": "mean: 684.95 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.3208062238185969,
            "unit": "iter/sec",
            "range": "stddev: 0.24308",
            "group": "engine",
            "extra": "mean: 3.1171 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.3753770561035982,
            "unit": "iter/sec",
            "range": "stddev: 0.075006",
            "group": "engine",
            "extra": "mean: 2.6640 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.0992578540408363,
            "unit": "iter/sec",
            "range": "stddev: 0.76620",
            "group": "engine",
            "extra": "mean: 10.075 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.11488434770884555,
            "unit": "iter/sec",
            "range": "stddev: 0.17793",
            "group": "engine",
            "extra": "mean: 8.7044 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.206149060952171,
            "unit": "iter/sec",
            "range": "stddev: 0.058458",
            "group": "import-export",
            "extra": "mean: 453.28 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 1.9340925923796997,
            "unit": "iter/sec",
            "range": "stddev: 0.063167",
            "group": "import-export",
            "extra": "mean: 517.04 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 0.12875769884961885,
            "unit": "iter/sec",
            "range": "stddev: 0.077675",
            "group": "import-export",
            "extra": "mean: 7.7665 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 0.13203645192108063,
            "unit": "iter/sec",
            "range": "stddev: 0.16950",
            "group": "import-export",
            "extra": "mean: 7.5737 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 94.21827208473545,
            "unit": "iter/sec",
            "range": "stddev: 0.0014685",
            "group": "node",
            "extra": "mean: 10.614 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 42.19458910302578,
            "unit": "iter/sec",
            "range": "stddev: 0.0015653",
            "group": "node",
            "extra": "mean: 23.700 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 42.056105060506844,
            "unit": "iter/sec",
            "range": "stddev: 0.0011741",
            "group": "node",
            "extra": "mean: 23.778 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 50.214004025832025,
            "unit": "iter/sec",
            "range": "stddev: 0.0013364",
            "group": "node",
            "extra": "mean: 19.915 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 26.262908099183274,
            "unit": "iter/sec",
            "range": "stddev: 0.0049371",
            "group": "node",
            "extra": "mean: 38.077 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 25.306896518978395,
            "unit": "iter/sec",
            "range": "stddev: 0.018363",
            "group": "node",
            "extra": "mean: 39.515 msec\nrounds: 100"
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
          "id": "a2d6c7673952ae48c0d5ae58aff2d2c808e3a982",
          "message": "Add options for transport tasks (#4583)\n\n* Add options for transport tasks\r\n\r\nWhen encountering failures during the execution of transport tasks, a runner\r\nwill wait for a time interval between transport task attempts. This time\r\ninterval between attempts is increased using an exponential backoff\r\nmechanism, i.e. the time interval is equal to:\r\n\r\n(TRANSPORT_TASK_RETRY_INITIAL_INTERVAL) * 2 ** (N_ATTEMPT - 1)\r\n\r\nwhere N_ATTEMPT is the number of failed attempts. This mechanism is\r\ninterrupted once the TRANSPORT_TASK_MAXIMUM_ATTEMPTS is reached.\r\n\r\nThe initial interval and maximum attempts are currently fixed to 20\r\nseconds and 5, respectively. This commit adds two configuration options\r\nthat use these defaults, but allow the user to adjust them using `verdi\r\nconfig`.",
          "timestamp": "2020-11-22T21:02:07+01:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/a2d6c7673952ae48c0d5ae58aff2d2c808e3a982",
          "distinct": true,
          "tree_id": "1f68e6180472a31d8620aeecbb57a55a8c7f469b"
        },
        "date": 1606076184517,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 2.86288238337627,
            "unit": "iter/sec",
            "range": "stddev: 0.010112",
            "group": "engine",
            "extra": "mean: 349.30 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.6655880989457137,
            "unit": "iter/sec",
            "range": "stddev: 0.069410",
            "group": "engine",
            "extra": "mean: 1.5024 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.7368709001146937,
            "unit": "iter/sec",
            "range": "stddev: 0.063815",
            "group": "engine",
            "extra": "mean: 1.3571 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.15919156627210213,
            "unit": "iter/sec",
            "range": "stddev: 0.28688",
            "group": "engine",
            "extra": "mean: 6.2817 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.16961296924401645,
            "unit": "iter/sec",
            "range": "stddev: 0.14517",
            "group": "engine",
            "extra": "mean: 5.8958 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 1.7465724203962778,
            "unit": "iter/sec",
            "range": "stddev: 0.061666",
            "group": "engine",
            "extra": "mean: 572.55 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.4158550345118914,
            "unit": "iter/sec",
            "range": "stddev: 0.078185",
            "group": "engine",
            "extra": "mean: 2.4047 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.46663828753968556,
            "unit": "iter/sec",
            "range": "stddev: 0.069635",
            "group": "engine",
            "extra": "mean: 2.1430 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.12230130416304258,
            "unit": "iter/sec",
            "range": "stddev: 0.25802",
            "group": "engine",
            "extra": "mean: 8.1765 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.1367702279678771,
            "unit": "iter/sec",
            "range": "stddev: 0.10134",
            "group": "engine",
            "extra": "mean: 7.3115 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.6220684566696684,
            "unit": "iter/sec",
            "range": "stddev: 0.050610",
            "group": "import-export",
            "extra": "mean: 381.38 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.3014738130825214,
            "unit": "iter/sec",
            "range": "stddev: 0.041806",
            "group": "import-export",
            "extra": "mean: 434.50 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 0.14964755573528066,
            "unit": "iter/sec",
            "range": "stddev: 0.095691",
            "group": "import-export",
            "extra": "mean: 6.6824 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 0.14786026396776952,
            "unit": "iter/sec",
            "range": "stddev: 0.15032",
            "group": "import-export",
            "extra": "mean: 6.7631 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 90.90308246322157,
            "unit": "iter/sec",
            "range": "stddev: 0.00066015",
            "group": "node",
            "extra": "mean: 11.001 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 46.3239143996011,
            "unit": "iter/sec",
            "range": "stddev: 0.0011658",
            "group": "node",
            "extra": "mean: 21.587 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 45.451190660850365,
            "unit": "iter/sec",
            "range": "stddev: 0.0017028",
            "group": "node",
            "extra": "mean: 22.002 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 55.69507245468375,
            "unit": "iter/sec",
            "range": "stddev: 0.0013697",
            "group": "node",
            "extra": "mean: 17.955 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 29.67729223148046,
            "unit": "iter/sec",
            "range": "stddev: 0.0031614",
            "group": "node",
            "extra": "mean: 33.696 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 27.982955382634515,
            "unit": "iter/sec",
            "range": "stddev: 0.017271",
            "group": "node",
            "extra": "mean: 35.736 msec\nrounds: 100"
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
          "id": "36cb1335d7c43e0fcca12cd38e09e0fbffaf226f",
          "message": "Fix command for getting EBM config options (#4587)\n\nCurrently the transport options for the EBM are obtained by using the\r\nget_config function, e.g.:\r\n\r\n`initial_interval = get_config_option(RETRY_INTERVAL_OPTION)`\r\n\r\nHowever, it seems that `get_config()` does not get you the current\r\nconfiguration (see #4586). \r\n\r\nReplacing `get_config().get_option()` with `get_config_option()` fixes this\r\nissue for the EBM options.",
          "timestamp": "2020-11-24T19:48:04+01:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/36cb1335d7c43e0fcca12cd38e09e0fbffaf226f",
          "distinct": true,
          "tree_id": "7aba0b76bbc89485ed8ec7c9792bacb2e16b0276"
        },
        "date": 1606244686569,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 2.463081507983411,
            "unit": "iter/sec",
            "range": "stddev: 0.015011",
            "group": "engine",
            "extra": "mean: 406.00 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.5419743490907089,
            "unit": "iter/sec",
            "range": "stddev: 0.043449",
            "group": "engine",
            "extra": "mean: 1.8451 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.5910950341807719,
            "unit": "iter/sec",
            "range": "stddev: 0.064241",
            "group": "engine",
            "extra": "mean: 1.6918 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.13454760402171126,
            "unit": "iter/sec",
            "range": "stddev: 0.21298",
            "group": "engine",
            "extra": "mean: 7.4323 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.13947556504725658,
            "unit": "iter/sec",
            "range": "stddev: 0.17290",
            "group": "engine",
            "extra": "mean: 7.1697 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 1.4297106499988528,
            "unit": "iter/sec",
            "range": "stddev: 0.061787",
            "group": "engine",
            "extra": "mean: 699.44 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.3263460435396103,
            "unit": "iter/sec",
            "range": "stddev: 0.14170",
            "group": "engine",
            "extra": "mean: 3.0642 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.3703768234046103,
            "unit": "iter/sec",
            "range": "stddev: 0.098772",
            "group": "engine",
            "extra": "mean: 2.7000 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.1034392393412796,
            "unit": "iter/sec",
            "range": "stddev: 0.15609",
            "group": "engine",
            "extra": "mean: 9.6675 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.11433938845496078,
            "unit": "iter/sec",
            "range": "stddev: 0.16395",
            "group": "engine",
            "extra": "mean: 8.7459 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 1.98723105678075,
            "unit": "iter/sec",
            "range": "stddev: 0.063054",
            "group": "import-export",
            "extra": "mean: 503.21 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 1.7449608009912063,
            "unit": "iter/sec",
            "range": "stddev: 0.058640",
            "group": "import-export",
            "extra": "mean: 573.08 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 0.12027449584150429,
            "unit": "iter/sec",
            "range": "stddev: 0.096706",
            "group": "import-export",
            "extra": "mean: 8.3143 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 0.13056492315327303,
            "unit": "iter/sec",
            "range": "stddev: 0.19075",
            "group": "import-export",
            "extra": "mean: 7.6590 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 100.17081528108191,
            "unit": "iter/sec",
            "range": "stddev: 0.00073702",
            "group": "node",
            "extra": "mean: 9.9829 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 43.5381381137263,
            "unit": "iter/sec",
            "range": "stddev: 0.0019400",
            "group": "node",
            "extra": "mean: 22.968 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 44.25148319687786,
            "unit": "iter/sec",
            "range": "stddev: 0.0017557",
            "group": "node",
            "extra": "mean: 22.598 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 52.09756687704797,
            "unit": "iter/sec",
            "range": "stddev: 0.0015483",
            "group": "node",
            "extra": "mean: 19.195 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 26.99490379920967,
            "unit": "iter/sec",
            "range": "stddev: 0.0029717",
            "group": "node",
            "extra": "mean: 37.044 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 26.502752316917952,
            "unit": "iter/sec",
            "range": "stddev: 0.0044559",
            "group": "node",
            "extra": "mean: 37.732 msec\nrounds: 100"
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
          "id": "af12a62d3509aa6d3ade250aff2230add49f5523",
          "message": "CI: Add workflow to run tests against various RabbitMQ versions\n\nThe main test workflow runs against a single version of RabbitMQ but\nexperience has shown that the code can break for different versions of\nthe RabbitMQ server. Here we add a new CI workflow that runs various\nunit tests through pytest that simulate the typical interaction with the\nRabbitMQ server in normal AiiDA operation. The difference is that these\nare tested against the currently available versions of RabbitMQ.\n\nThe current setup, still only tests part of the functionality that AiiDA\nuses, for example, the default credentials and virtual host are used.\nConnections over TLS are also not tested. These options would require\nthe RabbitMQ service that is running in a docker container to be\nconfigured differently. It is not clear how these various options can be\nparametrized in concert with the actual unit tests.",
          "timestamp": "2020-11-27T13:40:52+01:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/af12a62d3509aa6d3ade250aff2230add49f5523",
          "distinct": true,
          "tree_id": "213e4b703078ab0d16cb3ffe586119ae259e1fd5"
        },
        "date": 1606481796745,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 2.748438283085918,
            "unit": "iter/sec",
            "range": "stddev: 0.016613",
            "group": "engine",
            "extra": "mean: 363.84 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.5837848778206272,
            "unit": "iter/sec",
            "range": "stddev: 0.057005",
            "group": "engine",
            "extra": "mean: 1.7130 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.6431205950268786,
            "unit": "iter/sec",
            "range": "stddev: 0.048219",
            "group": "engine",
            "extra": "mean: 1.5549 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.14701294885865154,
            "unit": "iter/sec",
            "range": "stddev: 0.19422",
            "group": "engine",
            "extra": "mean: 6.8021 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.15315130897973436,
            "unit": "iter/sec",
            "range": "stddev: 0.17112",
            "group": "engine",
            "extra": "mean: 6.5295 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 1.5424534085948738,
            "unit": "iter/sec",
            "range": "stddev: 0.053172",
            "group": "engine",
            "extra": "mean: 648.32 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.3700066277218892,
            "unit": "iter/sec",
            "range": "stddev: 0.054688",
            "group": "engine",
            "extra": "mean: 2.7027 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.40228471401704785,
            "unit": "iter/sec",
            "range": "stddev: 0.095023",
            "group": "engine",
            "extra": "mean: 2.4858 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.11230222808252087,
            "unit": "iter/sec",
            "range": "stddev: 0.13124",
            "group": "engine",
            "extra": "mean: 8.9045 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.12404403702372685,
            "unit": "iter/sec",
            "range": "stddev: 0.20989",
            "group": "engine",
            "extra": "mean: 8.0617 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.0731564720355853,
            "unit": "iter/sec",
            "range": "stddev: 0.055094",
            "group": "import-export",
            "extra": "mean: 482.36 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 1.8221685686779199,
            "unit": "iter/sec",
            "range": "stddev: 0.045137",
            "group": "import-export",
            "extra": "mean: 548.80 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 0.12812284781492406,
            "unit": "iter/sec",
            "range": "stddev: 0.10940",
            "group": "import-export",
            "extra": "mean: 7.8050 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 0.12815600090701657,
            "unit": "iter/sec",
            "range": "stddev: 0.16168",
            "group": "import-export",
            "extra": "mean: 7.8030 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 94.21624291606614,
            "unit": "iter/sec",
            "range": "stddev: 0.0013599",
            "group": "node",
            "extra": "mean: 10.614 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 44.23519461405907,
            "unit": "iter/sec",
            "range": "stddev: 0.0014995",
            "group": "node",
            "extra": "mean: 22.606 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 43.471475066822734,
            "unit": "iter/sec",
            "range": "stddev: 0.0023617",
            "group": "node",
            "extra": "mean: 23.004 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 52.251284910585085,
            "unit": "iter/sec",
            "range": "stddev: 0.0010239",
            "group": "node",
            "extra": "mean: 19.138 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 27.124263280972247,
            "unit": "iter/sec",
            "range": "stddev: 0.0038343",
            "group": "node",
            "extra": "mean: 36.867 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 25.21154705969102,
            "unit": "iter/sec",
            "range": "stddev: 0.020314",
            "group": "node",
            "extra": "mean: 39.664 msec\nrounds: 100"
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
          "id": "9419068ffa8717c2470fe8774155d7006080540d",
          "message": "🧪 FIX: engine benchmark tests (#4652)\n\nThe `test_workchain_daemon` test group required updating to using asyncio (rather than tornado)",
          "timestamp": "2021-01-10T17:31:00Z",
          "url": "https://github.com/aiidateam/aiida-core/commit/9419068ffa8717c2470fe8774155d7006080540d",
          "distinct": true,
          "tree_id": "66d2d5cd697804c65a7769e849d40838416ddc0a"
        },
        "date": 1610300645609,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.0123057585232154,
            "unit": "iter/sec",
            "range": "stddev: 0.017273",
            "group": "engine",
            "extra": "mean: 331.97 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.6532771485326809,
            "unit": "iter/sec",
            "range": "stddev: 0.088710",
            "group": "engine",
            "extra": "mean: 1.5307 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.7029810258446861,
            "unit": "iter/sec",
            "range": "stddev: 0.057121",
            "group": "engine",
            "extra": "mean: 1.4225 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.1753939789769675,
            "unit": "iter/sec",
            "range": "stddev: 0.24678",
            "group": "engine",
            "extra": "mean: 5.7014 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.18723473089562637,
            "unit": "iter/sec",
            "range": "stddev: 0.30084",
            "group": "engine",
            "extra": "mean: 5.3409 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 1.9527444093517785,
            "unit": "iter/sec",
            "range": "stddev: 0.017030",
            "group": "engine",
            "extra": "mean: 512.10 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.4428185408966712,
            "unit": "iter/sec",
            "range": "stddev: 0.086413",
            "group": "engine",
            "extra": "mean: 2.2583 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.4969533457896612,
            "unit": "iter/sec",
            "range": "stddev: 0.095088",
            "group": "engine",
            "extra": "mean: 2.0123 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.13768477451652716,
            "unit": "iter/sec",
            "range": "stddev: 0.28859",
            "group": "engine",
            "extra": "mean: 7.2630 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.1577205101036379,
            "unit": "iter/sec",
            "range": "stddev: 0.17215",
            "group": "engine",
            "extra": "mean: 6.3403 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.446285362971211,
            "unit": "iter/sec",
            "range": "stddev: 0.0070950",
            "group": "import-export",
            "extra": "mean: 408.78 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.0745091776848605,
            "unit": "iter/sec",
            "range": "stddev: 0.052863",
            "group": "import-export",
            "extra": "mean: 482.04 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 0.14867249620273654,
            "unit": "iter/sec",
            "range": "stddev: 0.11705",
            "group": "import-export",
            "extra": "mean: 6.7262 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 0.14956536912463478,
            "unit": "iter/sec",
            "range": "stddev: 0.052299",
            "group": "import-export",
            "extra": "mean: 6.6860 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 199.31371806716282,
            "unit": "iter/sec",
            "range": "stddev: 0.00019088",
            "group": "node",
            "extra": "mean: 5.0172 msec\nrounds: 113"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 82.55450818679756,
            "unit": "iter/sec",
            "range": "stddev: 0.0033002",
            "group": "node",
            "extra": "mean: 12.113 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 83.40481765644219,
            "unit": "iter/sec",
            "range": "stddev: 0.00090273",
            "group": "node",
            "extra": "mean: 11.990 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 115.5618209475869,
            "unit": "iter/sec",
            "range": "stddev: 0.00032374",
            "group": "node",
            "extra": "mean: 8.6534 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 40.47489747668824,
            "unit": "iter/sec",
            "range": "stddev: 0.0016190",
            "group": "node",
            "extra": "mean: 24.707 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 37.739569067280144,
            "unit": "iter/sec",
            "range": "stddev: 0.018556",
            "group": "node",
            "extra": "mean: 26.497 msec\nrounds: 100"
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
          "pythonVersion": "3.8.7",
          "metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "8e80ac14d9e5372393528d9ba4107a7656d44923",
          "message": "Docs: clarify docstrings of `get_last_job_info` and `get_detailed_job_info` (#4657)\n\n`CalcJobNode`s contain two differente job infos, the `detailed_job_info` and\r\nthe `last_job_info`. The distinction between the two was not obvious,\r\nand not documented. The docstrings are improved to clarify the difference.",
          "timestamp": "2021-01-13T15:48:24+01:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/8e80ac14d9e5372393528d9ba4107a7656d44923",
          "distinct": true,
          "tree_id": "9f84b835ee52db74a662130062bdba7503ca2bc7"
        },
        "date": 1610550053673,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 2.9525004613326042,
            "unit": "iter/sec",
            "range": "stddev: 0.020540",
            "group": "engine",
            "extra": "mean: 338.70 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.6639377117296278,
            "unit": "iter/sec",
            "range": "stddev: 0.077694",
            "group": "engine",
            "extra": "mean: 1.5062 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.6792530818644086,
            "unit": "iter/sec",
            "range": "stddev: 0.37806",
            "group": "engine",
            "extra": "mean: 1.4722 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.1806472665862002,
            "unit": "iter/sec",
            "range": "stddev: 0.11846",
            "group": "engine",
            "extra": "mean: 5.5356 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.20944775495835746,
            "unit": "iter/sec",
            "range": "stddev: 0.20570",
            "group": "engine",
            "extra": "mean: 4.7745 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.057496979414371,
            "unit": "iter/sec",
            "range": "stddev: 0.011154",
            "group": "engine",
            "extra": "mean: 486.03 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.48295231776289055,
            "unit": "iter/sec",
            "range": "stddev: 0.12588",
            "group": "engine",
            "extra": "mean: 2.0706 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.5353842316511794,
            "unit": "iter/sec",
            "range": "stddev: 0.076978",
            "group": "engine",
            "extra": "mean: 1.8678 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.15233560556822004,
            "unit": "iter/sec",
            "range": "stddev: 0.19405",
            "group": "engine",
            "extra": "mean: 6.5645 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.17720481074898609,
            "unit": "iter/sec",
            "range": "stddev: 0.13123",
            "group": "engine",
            "extra": "mean: 5.6432 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.602737939200095,
            "unit": "iter/sec",
            "range": "stddev: 0.056826",
            "group": "import-export",
            "extra": "mean: 384.21 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.302245474268808,
            "unit": "iter/sec",
            "range": "stddev: 0.053430",
            "group": "import-export",
            "extra": "mean: 434.36 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 0.15832338500152646,
            "unit": "iter/sec",
            "range": "stddev: 0.060523",
            "group": "import-export",
            "extra": "mean: 6.3162 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 0.1577254420251481,
            "unit": "iter/sec",
            "range": "stddev: 0.091226",
            "group": "import-export",
            "extra": "mean: 6.3401 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 218.84326855553522,
            "unit": "iter/sec",
            "range": "stddev: 0.00028544",
            "group": "node",
            "extra": "mean: 4.5695 msec\nrounds: 118"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 95.19136933062802,
            "unit": "iter/sec",
            "range": "stddev: 0.00015122",
            "group": "node",
            "extra": "mean: 10.505 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 91.60401000466159,
            "unit": "iter/sec",
            "range": "stddev: 0.00045337",
            "group": "node",
            "extra": "mean: 10.917 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 126.64237253111358,
            "unit": "iter/sec",
            "range": "stddev: 0.00020578",
            "group": "node",
            "extra": "mean: 7.8963 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 39.32906436344093,
            "unit": "iter/sec",
            "range": "stddev: 0.021030",
            "group": "node",
            "extra": "mean: 25.426 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 42.4514044382473,
            "unit": "iter/sec",
            "range": "stddev: 0.0022395",
            "group": "node",
            "extra": "mean: 23.556 msec\nrounds: 100"
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
          "id": "2c5293ded4514c36a2754acbe67aa778e27c4886",
          "message": "Fix `run_get_node`/`run_get_pk` namedtuples (#4677)\n\nFix a regression made in #4669, whereby the namedtuple's were incorrectly named",
          "timestamp": "2021-01-26T10:10:20Z",
          "url": "https://github.com/aiidateam/aiida-core/commit/2c5293ded4514c36a2754acbe67aa778e27c4886",
          "distinct": true,
          "tree_id": "923ca9e8b12bb048c12c7d1a7dac915f45122725"
        },
        "date": 1611656501637,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.240712850505916,
            "unit": "iter/sec",
            "range": "stddev: 0.034494",
            "group": "engine",
            "extra": "mean: 308.57 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.7294429371992204,
            "unit": "iter/sec",
            "range": "stddev: 0.052077",
            "group": "engine",
            "extra": "mean: 1.3709 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.8435381734617372,
            "unit": "iter/sec",
            "range": "stddev: 0.062878",
            "group": "engine",
            "extra": "mean: 1.1855 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.20043206140925465,
            "unit": "iter/sec",
            "range": "stddev: 0.16060",
            "group": "engine",
            "extra": "mean: 4.9892 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.2257655441613168,
            "unit": "iter/sec",
            "range": "stddev: 0.15313",
            "group": "engine",
            "extra": "mean: 4.4294 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.3702558446644533,
            "unit": "iter/sec",
            "range": "stddev: 0.012881",
            "group": "engine",
            "extra": "mean: 421.90 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.5304080656098924,
            "unit": "iter/sec",
            "range": "stddev: 0.079155",
            "group": "engine",
            "extra": "mean: 1.8853 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.6184024014459069,
            "unit": "iter/sec",
            "range": "stddev: 0.060549",
            "group": "engine",
            "extra": "mean: 1.6171 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.1674270438778855,
            "unit": "iter/sec",
            "range": "stddev: 0.081607",
            "group": "engine",
            "extra": "mean: 5.9728 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.19474250944611723,
            "unit": "iter/sec",
            "range": "stddev: 0.13813",
            "group": "engine",
            "extra": "mean: 5.1350 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.776911916715314,
            "unit": "iter/sec",
            "range": "stddev: 0.052197",
            "group": "import-export",
            "extra": "mean: 360.11 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.5848855838190348,
            "unit": "iter/sec",
            "range": "stddev: 0.0072721",
            "group": "import-export",
            "extra": "mean: 386.86 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 0.17553529596275294,
            "unit": "iter/sec",
            "range": "stddev: 0.077939",
            "group": "import-export",
            "extra": "mean: 5.6969 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 0.17407141130208384,
            "unit": "iter/sec",
            "range": "stddev: 0.049193",
            "group": "import-export",
            "extra": "mean: 5.7448 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 217.77199266594408,
            "unit": "iter/sec",
            "range": "stddev: 0.00035410",
            "group": "node",
            "extra": "mean: 4.5920 msec\nrounds: 113"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 95.04776353993006,
            "unit": "iter/sec",
            "range": "stddev: 0.0018780",
            "group": "node",
            "extra": "mean: 10.521 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 96.54546594094613,
            "unit": "iter/sec",
            "range": "stddev: 0.00064300",
            "group": "node",
            "extra": "mean: 10.358 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 134.2790288436263,
            "unit": "iter/sec",
            "range": "stddev: 0.00055595",
            "group": "node",
            "extra": "mean: 7.4472 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 47.09600388523684,
            "unit": "iter/sec",
            "range": "stddev: 0.0015431",
            "group": "node",
            "extra": "mean: 21.233 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 42.926454584420334,
            "unit": "iter/sec",
            "range": "stddev: 0.020993",
            "group": "node",
            "extra": "mean: 23.296 msec\nrounds: 100"
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
          "id": "4c9d44af4d8c2550444d9d528dce1b890c7772f6",
          "message": "Use importlib in .ci folder",
          "timestamp": "2021-01-26T11:53:29+01:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/4c9d44af4d8c2550444d9d528dce1b890c7772f6",
          "distinct": true,
          "tree_id": "364d3b1c5ada0b94a3794230400e0f764503b7d5"
        },
        "date": 1611661528896,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 2.886592358986245,
            "unit": "iter/sec",
            "range": "stddev: 0.0093570",
            "group": "engine",
            "extra": "mean: 346.43 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.6396183182378613,
            "unit": "iter/sec",
            "range": "stddev: 0.074794",
            "group": "engine",
            "extra": "mean: 1.5634 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.7093635307337831,
            "unit": "iter/sec",
            "range": "stddev: 0.090293",
            "group": "engine",
            "extra": "mean: 1.4097 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.17980028422539437,
            "unit": "iter/sec",
            "range": "stddev: 0.16425",
            "group": "engine",
            "extra": "mean: 5.5617 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.2037967140497526,
            "unit": "iter/sec",
            "range": "stddev: 0.20510",
            "group": "engine",
            "extra": "mean: 4.9069 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.0354911808473046,
            "unit": "iter/sec",
            "range": "stddev: 0.013964",
            "group": "engine",
            "extra": "mean: 491.28 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.44189792561220964,
            "unit": "iter/sec",
            "range": "stddev: 0.076268",
            "group": "engine",
            "extra": "mean: 2.2630 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.5137407892896023,
            "unit": "iter/sec",
            "range": "stddev: 0.088208",
            "group": "engine",
            "extra": "mean: 1.9465 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.14667461056905065,
            "unit": "iter/sec",
            "range": "stddev: 0.17051",
            "group": "engine",
            "extra": "mean: 6.8178 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.1714742596682018,
            "unit": "iter/sec",
            "range": "stddev: 0.17463",
            "group": "engine",
            "extra": "mean: 5.8318 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.535006252545386,
            "unit": "iter/sec",
            "range": "stddev: 0.065144",
            "group": "import-export",
            "extra": "mean: 394.48 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.2400486509296536,
            "unit": "iter/sec",
            "range": "stddev: 0.060961",
            "group": "import-export",
            "extra": "mean: 446.42 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 0.15303382004240634,
            "unit": "iter/sec",
            "range": "stddev: 0.068673",
            "group": "import-export",
            "extra": "mean: 6.5345 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 0.1518467087538669,
            "unit": "iter/sec",
            "range": "stddev: 0.029799",
            "group": "import-export",
            "extra": "mean: 6.5856 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 217.2692928578734,
            "unit": "iter/sec",
            "range": "stddev: 0.00017129",
            "group": "node",
            "extra": "mean: 4.6026 msec\nrounds: 108"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 89.55361416244456,
            "unit": "iter/sec",
            "range": "stddev: 0.00054244",
            "group": "node",
            "extra": "mean: 11.166 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 85.14871587663373,
            "unit": "iter/sec",
            "range": "stddev: 0.00060023",
            "group": "node",
            "extra": "mean: 11.744 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 122.06817973401476,
            "unit": "iter/sec",
            "range": "stddev: 0.00036838",
            "group": "node",
            "extra": "mean: 8.1921 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 40.54236793299443,
            "unit": "iter/sec",
            "range": "stddev: 0.0016299",
            "group": "node",
            "extra": "mean: 24.666 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 40.55839212499346,
            "unit": "iter/sec",
            "range": "stddev: 0.0014289",
            "group": "node",
            "extra": "mean: 24.656 msec\nrounds: 100"
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
          "id": "dffff843e38ff6aa4819e521a1d51bb12e483ada",
          "message": "Merge pull request #4678 from ramirezfranciscof/negative_zero\n\nFix: pre-store hash for -0. and 0. is now the same",
          "timestamp": "2021-01-26T13:32:29+01:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/dffff843e38ff6aa4819e521a1d51bb12e483ada",
          "distinct": true,
          "tree_id": "5d2a232b45f9aac15e0547da9083cd62b210f650"
        },
        "date": 1611665116668,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 2.7294425087609686,
            "unit": "iter/sec",
            "range": "stddev: 0.025670",
            "group": "engine",
            "extra": "mean: 366.38 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.6400106136083289,
            "unit": "iter/sec",
            "range": "stddev: 0.050431",
            "group": "engine",
            "extra": "mean: 1.5625 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.7313791415262054,
            "unit": "iter/sec",
            "range": "stddev: 0.077674",
            "group": "engine",
            "extra": "mean: 1.3673 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.17525922441861846,
            "unit": "iter/sec",
            "range": "stddev: 0.15120",
            "group": "engine",
            "extra": "mean: 5.7058 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.20042202294971453,
            "unit": "iter/sec",
            "range": "stddev: 0.18110",
            "group": "engine",
            "extra": "mean: 4.9895 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 1.9782673836125917,
            "unit": "iter/sec",
            "range": "stddev: 0.054793",
            "group": "engine",
            "extra": "mean: 505.49 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.4579034323367056,
            "unit": "iter/sec",
            "range": "stddev: 0.059687",
            "group": "engine",
            "extra": "mean: 2.1839 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.5305038892274097,
            "unit": "iter/sec",
            "range": "stddev: 0.093302",
            "group": "engine",
            "extra": "mean: 1.8850 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.14563771758139543,
            "unit": "iter/sec",
            "range": "stddev: 0.14012",
            "group": "engine",
            "extra": "mean: 6.8664 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.16909443952412223,
            "unit": "iter/sec",
            "range": "stddev: 0.18134",
            "group": "engine",
            "extra": "mean: 5.9139 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.5481058901713443,
            "unit": "iter/sec",
            "range": "stddev: 0.056169",
            "group": "import-export",
            "extra": "mean: 392.45 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.194095858343573,
            "unit": "iter/sec",
            "range": "stddev: 0.060104",
            "group": "import-export",
            "extra": "mean: 455.77 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 0.1531724502014761,
            "unit": "iter/sec",
            "range": "stddev: 0.10672",
            "group": "import-export",
            "extra": "mean: 6.5286 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 0.15407743643010977,
            "unit": "iter/sec",
            "range": "stddev: 0.12367",
            "group": "import-export",
            "extra": "mean: 6.4902 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 209.03161629050575,
            "unit": "iter/sec",
            "range": "stddev: 0.00042970",
            "group": "node",
            "extra": "mean: 4.7840 msec\nrounds: 118"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 87.52948050884484,
            "unit": "iter/sec",
            "range": "stddev: 0.0020931",
            "group": "node",
            "extra": "mean: 11.425 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 86.84154149928264,
            "unit": "iter/sec",
            "range": "stddev: 0.00073489",
            "group": "node",
            "extra": "mean: 11.515 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 120.2846327982096,
            "unit": "iter/sec",
            "range": "stddev: 0.00051987",
            "group": "node",
            "extra": "mean: 8.3136 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 42.510666748857105,
            "unit": "iter/sec",
            "range": "stddev: 0.0014098",
            "group": "node",
            "extra": "mean: 23.524 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 41.818799906136455,
            "unit": "iter/sec",
            "range": "stddev: 0.0019909",
            "group": "node",
            "extra": "mean: 23.913 msec\nrounds: 100"
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
          "pythonVersion": "3.8.7",
          "metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "d304dfc796926bcbed3fbd4e68aae431ea891365",
          "message": "ci: update paramiko version (#4686)\n\nNow that the Github Action runners switched to Ubuntu 20.04, the default SSH\r\nkey format of OpenSSH changed and is no longer supported by paramiko\r\n<=2.7.1.",
          "timestamp": "2021-01-27T12:16:23+01:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/d304dfc796926bcbed3fbd4e68aae431ea891365",
          "distinct": true,
          "tree_id": "0bb0ddfdc7beacbd381ae790d0847482c30dd675"
        },
        "date": 1611746969325,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 2.855970109320859,
            "unit": "iter/sec",
            "range": "stddev: 0.0098412",
            "group": "engine",
            "extra": "mean: 350.14 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.6356656732296,
            "unit": "iter/sec",
            "range": "stddev: 0.039773",
            "group": "engine",
            "extra": "mean: 1.5732 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.731543648598559,
            "unit": "iter/sec",
            "range": "stddev: 0.087366",
            "group": "engine",
            "extra": "mean: 1.3670 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.17918731246395625,
            "unit": "iter/sec",
            "range": "stddev: 0.10244",
            "group": "engine",
            "extra": "mean: 5.5808 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.2015371888570349,
            "unit": "iter/sec",
            "range": "stddev: 0.21527",
            "group": "engine",
            "extra": "mean: 4.9619 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.068253049709934,
            "unit": "iter/sec",
            "range": "stddev: 0.0031712",
            "group": "engine",
            "extra": "mean: 483.50 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.4413925013591204,
            "unit": "iter/sec",
            "range": "stddev: 0.077311",
            "group": "engine",
            "extra": "mean: 2.2656 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.5021524492570776,
            "unit": "iter/sec",
            "range": "stddev: 0.091113",
            "group": "engine",
            "extra": "mean: 1.9914 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.1428726848804933,
            "unit": "iter/sec",
            "range": "stddev: 0.26410",
            "group": "engine",
            "extra": "mean: 6.9992 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.16851823186083045,
            "unit": "iter/sec",
            "range": "stddev: 0.19803",
            "group": "engine",
            "extra": "mean: 5.9341 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.3252824834400405,
            "unit": "iter/sec",
            "range": "stddev: 0.16076",
            "group": "import-export",
            "extra": "mean: 430.06 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.2886672305436537,
            "unit": "iter/sec",
            "range": "stddev: 0.052999",
            "group": "import-export",
            "extra": "mean: 436.94 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 0.15185842631630517,
            "unit": "iter/sec",
            "range": "stddev: 0.17684",
            "group": "import-export",
            "extra": "mean: 6.5851 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 0.14830312064138373,
            "unit": "iter/sec",
            "range": "stddev: 0.24762",
            "group": "import-export",
            "extra": "mean: 6.7429 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 199.8494422760571,
            "unit": "iter/sec",
            "range": "stddev: 0.00019216",
            "group": "node",
            "extra": "mean: 5.0038 msec\nrounds: 122"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 81.82929714545551,
            "unit": "iter/sec",
            "range": "stddev: 0.0010918",
            "group": "node",
            "extra": "mean: 12.221 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 78.94385712292141,
            "unit": "iter/sec",
            "range": "stddev: 0.00098630",
            "group": "node",
            "extra": "mean: 12.667 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 111.64710678956304,
            "unit": "iter/sec",
            "range": "stddev: 0.0014419",
            "group": "node",
            "extra": "mean: 8.9568 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 34.471566107320676,
            "unit": "iter/sec",
            "range": "stddev: 0.022302",
            "group": "node",
            "extra": "mean: 29.009 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 34.5209378732893,
            "unit": "iter/sec",
            "range": "stddev: 0.010068",
            "group": "node",
            "extra": "mean: 28.968 msec\nrounds: 100"
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
          "pythonVersion": "3.8.7",
          "metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "950d1a424ac5be54c4771f8aeb7dd7189bf23ec9",
          "message": "Fix: release signal handlers after run execution (#4682)\n\nAfter a process has executed (when running rather than submitting),\r\nreturn the signal handlers to their original state.\r\n\r\nThis fixes an issue whereby using `CTRL-C` after a process has run still calls the `process.kill`.\r\nIt also releases the `kill_process` function's reference to the process,\r\na step towards allowing the finished process to be garbage collected.",
          "timestamp": "2021-01-27T11:42:05Z",
          "url": "https://github.com/aiidateam/aiida-core/commit/950d1a424ac5be54c4771f8aeb7dd7189bf23ec9",
          "distinct": true,
          "tree_id": "8bd2bb11b95812035d980ab2e032f22d19c140e0"
        },
        "date": 1611748518886,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 2.6083399616990475,
            "unit": "iter/sec",
            "range": "stddev: 0.0094720",
            "group": "engine",
            "extra": "mean: 383.39 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.5862377726359382,
            "unit": "iter/sec",
            "range": "stddev: 0.061624",
            "group": "engine",
            "extra": "mean: 1.7058 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.6810544639971319,
            "unit": "iter/sec",
            "range": "stddev: 0.073541",
            "group": "engine",
            "extra": "mean: 1.4683 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.1686904402952352,
            "unit": "iter/sec",
            "range": "stddev: 0.30806",
            "group": "engine",
            "extra": "mean: 5.9280 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.1898487620039202,
            "unit": "iter/sec",
            "range": "stddev: 0.15562",
            "group": "engine",
            "extra": "mean: 5.2674 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 1.9618036037925901,
            "unit": "iter/sec",
            "range": "stddev: 0.012298",
            "group": "engine",
            "extra": "mean: 509.74 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.4790988591383871,
            "unit": "iter/sec",
            "range": "stddev: 0.12357",
            "group": "engine",
            "extra": "mean: 2.0873 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.5475316911552299,
            "unit": "iter/sec",
            "range": "stddev: 0.11057",
            "group": "engine",
            "extra": "mean: 1.8264 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.1439441618633706,
            "unit": "iter/sec",
            "range": "stddev: 0.29899",
            "group": "engine",
            "extra": "mean: 6.9471 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.16394368179906943,
            "unit": "iter/sec",
            "range": "stddev: 0.22529",
            "group": "engine",
            "extra": "mean: 6.0997 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.2586829787446026,
            "unit": "iter/sec",
            "range": "stddev: 0.060018",
            "group": "import-export",
            "extra": "mean: 442.74 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.02550270417387,
            "unit": "iter/sec",
            "range": "stddev: 0.067476",
            "group": "import-export",
            "extra": "mean: 493.70 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 0.14617110515032752,
            "unit": "iter/sec",
            "range": "stddev: 0.32999",
            "group": "import-export",
            "extra": "mean: 6.8413 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 0.15065038107793532,
            "unit": "iter/sec",
            "range": "stddev: 0.29332",
            "group": "import-export",
            "extra": "mean: 6.6379 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 282.76761141447463,
            "unit": "iter/sec",
            "range": "stddev: 0.00016755",
            "group": "node",
            "extra": "mean: 3.5365 msec\nrounds: 135"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 115.0983422565393,
            "unit": "iter/sec",
            "range": "stddev: 0.00027304",
            "group": "node",
            "extra": "mean: 8.6882 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 111.12498185477881,
            "unit": "iter/sec",
            "range": "stddev: 0.00039659",
            "group": "node",
            "extra": "mean: 8.9989 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 168.34877706370042,
            "unit": "iter/sec",
            "range": "stddev: 0.00095396",
            "group": "node",
            "extra": "mean: 5.9400 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 41.662092116889795,
            "unit": "iter/sec",
            "range": "stddev: 0.019357",
            "group": "node",
            "extra": "mean: 24.003 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 42.825857344759136,
            "unit": "iter/sec",
            "range": "stddev: 0.0013507",
            "group": "node",
            "extra": "mean: 23.350 msec\nrounds: 100"
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
          "pythonVersion": "3.8.7",
          "metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "02ebeb88e231172cfebc5a510a72671da4ef061b",
          "message": "Fix: `PluginVersionProvider` should cache process class (#4683)\n\nCurrently, the `PluginVersionProvider` is caching process instance, rather than class.\r\nThis commit fixes the bug, meaning the cache will now work correctly.\r\nRemoving the reference to the process instance also is a step towards allowing it to be garbage collected.",
          "timestamp": "2021-01-27T12:01:39Z",
          "url": "https://github.com/aiidateam/aiida-core/commit/02ebeb88e231172cfebc5a510a72671da4ef061b",
          "distinct": true,
          "tree_id": "0a4289af19491bc9e27acfde002e51ad774d3d75"
        },
        "date": 1611749591989,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 2.9867615248109023,
            "unit": "iter/sec",
            "range": "stddev: 0.011424",
            "group": "engine",
            "extra": "mean: 334.81 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.6789030773266973,
            "unit": "iter/sec",
            "range": "stddev: 0.026619",
            "group": "engine",
            "extra": "mean: 1.4730 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.8055657603014912,
            "unit": "iter/sec",
            "range": "stddev: 0.034899",
            "group": "engine",
            "extra": "mean: 1.2414 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.19821725845333782,
            "unit": "iter/sec",
            "range": "stddev: 0.068886",
            "group": "engine",
            "extra": "mean: 5.0450 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.22423218484944005,
            "unit": "iter/sec",
            "range": "stddev: 0.10605",
            "group": "engine",
            "extra": "mean: 4.4597 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.4532884645845505,
            "unit": "iter/sec",
            "range": "stddev: 0.0087781",
            "group": "engine",
            "extra": "mean: 407.62 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.5638721889841808,
            "unit": "iter/sec",
            "range": "stddev: 0.057403",
            "group": "engine",
            "extra": "mean: 1.7735 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.6402203858599048,
            "unit": "iter/sec",
            "range": "stddev: 0.054271",
            "group": "engine",
            "extra": "mean: 1.5620 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.17580608311708626,
            "unit": "iter/sec",
            "range": "stddev: 0.10899",
            "group": "engine",
            "extra": "mean: 5.6881 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.2051368268670324,
            "unit": "iter/sec",
            "range": "stddev: 0.073082",
            "group": "engine",
            "extra": "mean: 4.8748 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.640917600341694,
            "unit": "iter/sec",
            "range": "stddev: 0.040885",
            "group": "import-export",
            "extra": "mean: 378.66 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.3649840420169737,
            "unit": "iter/sec",
            "range": "stddev: 0.036902",
            "group": "import-export",
            "extra": "mean: 422.84 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 0.1704522264520046,
            "unit": "iter/sec",
            "range": "stddev: 0.12171",
            "group": "import-export",
            "extra": "mean: 5.8667 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 0.1663605774257223,
            "unit": "iter/sec",
            "range": "stddev: 0.12879",
            "group": "import-export",
            "extra": "mean: 6.0110 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 316.7972075003301,
            "unit": "iter/sec",
            "range": "stddev: 0.000067970",
            "group": "node",
            "extra": "mean: 3.1566 msec\nrounds: 158"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 129.64773921006764,
            "unit": "iter/sec",
            "range": "stddev: 0.00026940",
            "group": "node",
            "extra": "mean: 7.7132 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 124.71959029344708,
            "unit": "iter/sec",
            "range": "stddev: 0.00053001",
            "group": "node",
            "extra": "mean: 8.0180 msec\nrounds: 107"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 190.77936941860386,
            "unit": "iter/sec",
            "range": "stddev: 0.00011820",
            "group": "node",
            "extra": "mean: 5.2417 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 50.59492134393537,
            "unit": "iter/sec",
            "range": "stddev: 0.0011826",
            "group": "node",
            "extra": "mean: 19.765 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 47.80953624711866,
            "unit": "iter/sec",
            "range": "stddev: 0.013310",
            "group": "node",
            "extra": "mean: 20.916 msec\nrounds: 100"
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
          "pythonVersion": "3.8.7",
          "metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "cdb2e57906e10e31f04ccb58923643292f38b6c0",
          "message": "remove leftover use of Computer.name (#4681)\n\nRemove leftover use of deprecated Computer.name attribute in `verdi\r\ncomputer list`.\r\n\r\nAlso update minimum version of click dependency to 7.1, since click 7.1\r\nintroduces additional whitespace in the verdi autodocs (running with \r\nclick 7.0 locally resulted in pre-commit check failing on CI).\r\n\r\nCo-authored-by: Chris Sewell <chrisj_sewell@hotmail.com>",
          "timestamp": "2021-01-27T13:25:47+01:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/cdb2e57906e10e31f04ccb58923643292f38b6c0",
          "distinct": true,
          "tree_id": "10c3167904a028802c5cbc31aa834aef7786deab"
        },
        "date": 1611751150219,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 2.613785133217042,
            "unit": "iter/sec",
            "range": "stddev: 0.020472",
            "group": "engine",
            "extra": "mean: 382.59 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.6047525272238593,
            "unit": "iter/sec",
            "range": "stddev: 0.059026",
            "group": "engine",
            "extra": "mean: 1.6536 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.7012023330094701,
            "unit": "iter/sec",
            "range": "stddev: 0.047017",
            "group": "engine",
            "extra": "mean: 1.4261 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.16659654320788247,
            "unit": "iter/sec",
            "range": "stddev: 0.11502",
            "group": "engine",
            "extra": "mean: 6.0025 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.1935141265031076,
            "unit": "iter/sec",
            "range": "stddev: 0.092992",
            "group": "engine",
            "extra": "mean: 5.1676 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.2051153086074367,
            "unit": "iter/sec",
            "range": "stddev: 0.019375",
            "group": "engine",
            "extra": "mean: 453.49 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.4906855893579147,
            "unit": "iter/sec",
            "range": "stddev: 0.063614",
            "group": "engine",
            "extra": "mean: 2.0380 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.5572208895259688,
            "unit": "iter/sec",
            "range": "stddev: 0.073766",
            "group": "engine",
            "extra": "mean: 1.7946 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.1496415724668417,
            "unit": "iter/sec",
            "range": "stddev: 0.16910",
            "group": "engine",
            "extra": "mean: 6.6826 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.17603147243290557,
            "unit": "iter/sec",
            "range": "stddev: 0.11422",
            "group": "engine",
            "extra": "mean: 5.6808 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.3646589191836274,
            "unit": "iter/sec",
            "range": "stddev: 0.040735",
            "group": "import-export",
            "extra": "mean: 422.89 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 1.9921187505812443,
            "unit": "iter/sec",
            "range": "stddev: 0.065518",
            "group": "import-export",
            "extra": "mean: 501.98 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 0.14381235874195306,
            "unit": "iter/sec",
            "range": "stddev: 0.082838",
            "group": "import-export",
            "extra": "mean: 6.9535 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 0.1410658613376018,
            "unit": "iter/sec",
            "range": "stddev: 0.094687",
            "group": "import-export",
            "extra": "mean: 7.0889 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 259.1943840081827,
            "unit": "iter/sec",
            "range": "stddev: 0.00098906",
            "group": "node",
            "extra": "mean: 3.8581 msec\nrounds: 134"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 108.94601615846796,
            "unit": "iter/sec",
            "range": "stddev: 0.00028207",
            "group": "node",
            "extra": "mean: 9.1789 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 106.62002725688185,
            "unit": "iter/sec",
            "range": "stddev: 0.00067845",
            "group": "node",
            "extra": "mean: 9.3791 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 157.3802969316387,
            "unit": "iter/sec",
            "range": "stddev: 0.00083752",
            "group": "node",
            "extra": "mean: 6.3540 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 43.59544455260982,
            "unit": "iter/sec",
            "range": "stddev: 0.0013573",
            "group": "node",
            "extra": "mean: 22.938 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 43.17091678946156,
            "unit": "iter/sec",
            "range": "stddev: 0.0020858",
            "group": "node",
            "extra": "mean: 23.164 msec\nrounds: 100"
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
          "pythonVersion": "3.8.7",
          "metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "3cf1d2ef9f0300a0ed9ef7cfade7c4f49ba09d91",
          "message": "Add `to_aiida_type` to the public API (#4672)\n\nSince `to_aiida_type` is intended for public use,\r\nthis commit makes it part of the public API,\r\nvia `from aiida.orm import to_aiida_type`.",
          "timestamp": "2021-01-27T13:01:48Z",
          "url": "https://github.com/aiidateam/aiida-core/commit/3cf1d2ef9f0300a0ed9ef7cfade7c4f49ba09d91",
          "distinct": true,
          "tree_id": "91af0213f8085466ab3c1718a24051b6fe1532a9"
        },
        "date": 1611753288593,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 2.737259900963752,
            "unit": "iter/sec",
            "range": "stddev: 0.0082328",
            "group": "engine",
            "extra": "mean: 365.33 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.6034563112053892,
            "unit": "iter/sec",
            "range": "stddev: 0.11727",
            "group": "engine",
            "extra": "mean: 1.6571 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.6817500147343067,
            "unit": "iter/sec",
            "range": "stddev: 0.075211",
            "group": "engine",
            "extra": "mean: 1.4668 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.1714359647642322,
            "unit": "iter/sec",
            "range": "stddev: 0.14764",
            "group": "engine",
            "extra": "mean: 5.8331 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.1967110117745471,
            "unit": "iter/sec",
            "range": "stddev: 0.10408",
            "group": "engine",
            "extra": "mean: 5.0836 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.0365148961896034,
            "unit": "iter/sec",
            "range": "stddev: 0.073755",
            "group": "engine",
            "extra": "mean: 491.03 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.47774299386670105,
            "unit": "iter/sec",
            "range": "stddev: 0.12274",
            "group": "engine",
            "extra": "mean: 2.0932 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.5494497026338404,
            "unit": "iter/sec",
            "range": "stddev: 0.083945",
            "group": "engine",
            "extra": "mean: 1.8200 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.14996569965321893,
            "unit": "iter/sec",
            "range": "stddev: 0.12717",
            "group": "engine",
            "extra": "mean: 6.6682 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.17429682676386232,
            "unit": "iter/sec",
            "range": "stddev: 0.16325",
            "group": "engine",
            "extra": "mean: 5.7373 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.4385969656563544,
            "unit": "iter/sec",
            "range": "stddev: 0.072164",
            "group": "import-export",
            "extra": "mean: 410.07 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.1668106100322513,
            "unit": "iter/sec",
            "range": "stddev: 0.070791",
            "group": "import-export",
            "extra": "mean: 461.51 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 0.14763776901212478,
            "unit": "iter/sec",
            "range": "stddev: 0.13980",
            "group": "import-export",
            "extra": "mean: 6.7733 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 0.1429215295098151,
            "unit": "iter/sec",
            "range": "stddev: 0.29217",
            "group": "import-export",
            "extra": "mean: 6.9968 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 304.2123323394972,
            "unit": "iter/sec",
            "range": "stddev: 0.00040132",
            "group": "node",
            "extra": "mean: 3.2872 msec\nrounds: 120"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 117.52577139792285,
            "unit": "iter/sec",
            "range": "stddev: 0.0019776",
            "group": "node",
            "extra": "mean: 8.5088 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 101.75309253316473,
            "unit": "iter/sec",
            "range": "stddev: 0.0036040",
            "group": "node",
            "extra": "mean: 9.8277 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 170.43730978776424,
            "unit": "iter/sec",
            "range": "stddev: 0.00060129",
            "group": "node",
            "extra": "mean: 5.8673 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 43.84287712630474,
            "unit": "iter/sec",
            "range": "stddev: 0.0018246",
            "group": "node",
            "extra": "mean: 22.809 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 42.23392916985694,
            "unit": "iter/sec",
            "range": "stddev: 0.0030237",
            "group": "node",
            "extra": "mean: 23.678 msec\nrounds: 100"
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
          "pythonVersion": "3.8.7",
          "metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "e9f234ec256dd2f2b94c70be9826917bd9861ec0",
          "message": "Add .dockerignore (#4564)\n\nThis commit adds a `.dockerignore` file to inhibit any unecessary/unwanted files being copied into the Docker container,\r\nduring the `COPY . aiida-core` command,\r\nand also reduces the build time.",
          "timestamp": "2021-01-27T14:23:11Z",
          "url": "https://github.com/aiidateam/aiida-core/commit/e9f234ec256dd2f2b94c70be9826917bd9861ec0",
          "distinct": true,
          "tree_id": "d8bafef396f9ee1057066c92f20aae0c34b9ef24"
        },
        "date": 1611758191033,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 2.631231781954718,
            "unit": "iter/sec",
            "range": "stddev: 0.014589",
            "group": "engine",
            "extra": "mean: 380.05 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.5970298435984297,
            "unit": "iter/sec",
            "range": "stddev: 0.061168",
            "group": "engine",
            "extra": "mean: 1.6750 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.6955214139518552,
            "unit": "iter/sec",
            "range": "stddev: 0.061742",
            "group": "engine",
            "extra": "mean: 1.4378 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.17465647215703883,
            "unit": "iter/sec",
            "range": "stddev: 0.085148",
            "group": "engine",
            "extra": "mean: 5.7255 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.198973347817764,
            "unit": "iter/sec",
            "range": "stddev: 0.12134",
            "group": "engine",
            "extra": "mean: 5.0258 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.104470813557216,
            "unit": "iter/sec",
            "range": "stddev: 0.023911",
            "group": "engine",
            "extra": "mean: 475.18 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.4700941817503101,
            "unit": "iter/sec",
            "range": "stddev: 0.059346",
            "group": "engine",
            "extra": "mean: 2.1272 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.5540711443837449,
            "unit": "iter/sec",
            "range": "stddev: 0.046771",
            "group": "engine",
            "extra": "mean: 1.8048 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.1513266348053058,
            "unit": "iter/sec",
            "range": "stddev: 0.12646",
            "group": "engine",
            "extra": "mean: 6.6082 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.17710731412359115,
            "unit": "iter/sec",
            "range": "stddev: 0.12055",
            "group": "engine",
            "extra": "mean: 5.6463 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.1144593373648832,
            "unit": "iter/sec",
            "range": "stddev: 0.043477",
            "group": "import-export",
            "extra": "mean: 472.93 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 1.9044390612293196,
            "unit": "iter/sec",
            "range": "stddev: 0.035131",
            "group": "import-export",
            "extra": "mean: 525.09 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 0.135164768464141,
            "unit": "iter/sec",
            "range": "stddev: 0.21701",
            "group": "import-export",
            "extra": "mean: 7.3984 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 0.13507652410794033,
            "unit": "iter/sec",
            "range": "stddev: 0.16107",
            "group": "import-export",
            "extra": "mean: 7.4032 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 264.1538876896297,
            "unit": "iter/sec",
            "range": "stddev: 0.00043859",
            "group": "node",
            "extra": "mean: 3.7857 msec\nrounds: 145"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 103.18761867122663,
            "unit": "iter/sec",
            "range": "stddev: 0.0010737",
            "group": "node",
            "extra": "mean: 9.6911 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 96.76096435810797,
            "unit": "iter/sec",
            "range": "stddev: 0.00092677",
            "group": "node",
            "extra": "mean: 10.335 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 146.8332324060939,
            "unit": "iter/sec",
            "range": "stddev: 0.00088470",
            "group": "node",
            "extra": "mean: 6.8104 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 40.36616330805575,
            "unit": "iter/sec",
            "range": "stddev: 0.0028643",
            "group": "node",
            "extra": "mean: 24.773 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 37.510556943011096,
            "unit": "iter/sec",
            "range": "stddev: 0.015610",
            "group": "node",
            "extra": "mean: 26.659 msec\nrounds: 100"
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
          "pythonVersion": "3.8.7",
          "metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "d2b255b713a82230ad4f298b112d7095c31c1f24",
          "message": "CI: Remove `--use-feature=2020-resolver` pip feature flag tests. (#4689)\n\nThe feature is now on by default in the latest stable release.",
          "timestamp": "2021-01-27T14:51:33Z",
          "url": "https://github.com/aiidateam/aiida-core/commit/d2b255b713a82230ad4f298b112d7095c31c1f24",
          "distinct": true,
          "tree_id": "029884fba3c2bce87e30251f69307c449c98c7ad"
        },
        "date": 1611759960603,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 2.3466458627437268,
            "unit": "iter/sec",
            "range": "stddev: 0.024559",
            "group": "engine",
            "extra": "mean: 426.14 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.5160831623071409,
            "unit": "iter/sec",
            "range": "stddev: 0.058429",
            "group": "engine",
            "extra": "mean: 1.9377 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.6096898143521052,
            "unit": "iter/sec",
            "range": "stddev: 0.084985",
            "group": "engine",
            "extra": "mean: 1.6402 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.15096940433299513,
            "unit": "iter/sec",
            "range": "stddev: 0.097013",
            "group": "engine",
            "extra": "mean: 6.6239 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.17446008366294444,
            "unit": "iter/sec",
            "range": "stddev: 0.11696",
            "group": "engine",
            "extra": "mean: 5.7320 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 1.8872290914108585,
            "unit": "iter/sec",
            "range": "stddev: 0.017186",
            "group": "engine",
            "extra": "mean: 529.88 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.42506139958040406,
            "unit": "iter/sec",
            "range": "stddev: 0.062157",
            "group": "engine",
            "extra": "mean: 2.3526 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.4942493622845181,
            "unit": "iter/sec",
            "range": "stddev: 0.079042",
            "group": "engine",
            "extra": "mean: 2.0233 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.13504689735933276,
            "unit": "iter/sec",
            "range": "stddev: 0.13581",
            "group": "engine",
            "extra": "mean: 7.4048 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.158132811114986,
            "unit": "iter/sec",
            "range": "stddev: 0.10631",
            "group": "engine",
            "extra": "mean: 6.3238 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.139045195487096,
            "unit": "iter/sec",
            "range": "stddev: 0.047669",
            "group": "import-export",
            "extra": "mean: 467.50 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 1.9279378918959598,
            "unit": "iter/sec",
            "range": "stddev: 0.051936",
            "group": "import-export",
            "extra": "mean: 518.69 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 0.1313127768951933,
            "unit": "iter/sec",
            "range": "stddev: 0.10651",
            "group": "import-export",
            "extra": "mean: 7.6154 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 0.13113763823592806,
            "unit": "iter/sec",
            "range": "stddev: 0.11249",
            "group": "import-export",
            "extra": "mean: 7.6256 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 243.98466399841246,
            "unit": "iter/sec",
            "range": "stddev: 0.00075213",
            "group": "node",
            "extra": "mean: 4.0986 msec\nrounds: 125"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 95.60616275718618,
            "unit": "iter/sec",
            "range": "stddev: 0.0010795",
            "group": "node",
            "extra": "mean: 10.460 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 95.15371835796455,
            "unit": "iter/sec",
            "range": "stddev: 0.0015775",
            "group": "node",
            "extra": "mean: 10.509 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 138.0416010452663,
            "unit": "iter/sec",
            "range": "stddev: 0.0017761",
            "group": "node",
            "extra": "mean: 7.2442 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 37.91786138755706,
            "unit": "iter/sec",
            "range": "stddev: 0.0041114",
            "group": "node",
            "extra": "mean: 26.373 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 37.174445186612076,
            "unit": "iter/sec",
            "range": "stddev: 0.017974",
            "group": "node",
            "extra": "mean: 26.900 msec\nrounds: 100"
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
          "pythonVersion": "3.8.7",
          "metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "dcc80618368f405c02c9eaa6d122177e78d70a4b",
          "message": "CI: Notify slack on failure of the test-install workflow. (#4690)",
          "timestamp": "2021-01-27T16:02:48Z",
          "url": "https://github.com/aiidateam/aiida-core/commit/dcc80618368f405c02c9eaa6d122177e78d70a4b",
          "distinct": true,
          "tree_id": "c7d46b03e00e94b7fac292d93772a1c8d71cf772"
        },
        "date": 1611764154483,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 2.6461297656564713,
            "unit": "iter/sec",
            "range": "stddev: 0.018536",
            "group": "engine",
            "extra": "mean: 377.91 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.6076416260084848,
            "unit": "iter/sec",
            "range": "stddev: 0.073644",
            "group": "engine",
            "extra": "mean: 1.6457 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.6921121502611752,
            "unit": "iter/sec",
            "range": "stddev: 0.099819",
            "group": "engine",
            "extra": "mean: 1.4449 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.1680470353418529,
            "unit": "iter/sec",
            "range": "stddev: 0.14560",
            "group": "engine",
            "extra": "mean: 5.9507 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.19106799157529605,
            "unit": "iter/sec",
            "range": "stddev: 0.10525",
            "group": "engine",
            "extra": "mean: 5.2337 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.134166556575316,
            "unit": "iter/sec",
            "range": "stddev: 0.016099",
            "group": "engine",
            "extra": "mean: 468.57 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.48714688143694046,
            "unit": "iter/sec",
            "range": "stddev: 0.055298",
            "group": "engine",
            "extra": "mean: 2.0528 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.5602486733790298,
            "unit": "iter/sec",
            "range": "stddev: 0.099846",
            "group": "engine",
            "extra": "mean: 1.7849 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.1462997811810879,
            "unit": "iter/sec",
            "range": "stddev: 0.19638",
            "group": "engine",
            "extra": "mean: 6.8353 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.1718488663341756,
            "unit": "iter/sec",
            "range": "stddev: 0.13891",
            "group": "engine",
            "extra": "mean: 5.8191 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.338511247007893,
            "unit": "iter/sec",
            "range": "stddev: 0.038290",
            "group": "import-export",
            "extra": "mean: 427.62 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.1075096174700514,
            "unit": "iter/sec",
            "range": "stddev: 0.055839",
            "group": "import-export",
            "extra": "mean: 474.49 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 0.14505262318310014,
            "unit": "iter/sec",
            "range": "stddev: 0.10121",
            "group": "import-export",
            "extra": "mean: 6.8940 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 0.1450387080617885,
            "unit": "iter/sec",
            "range": "stddev: 0.11792",
            "group": "import-export",
            "extra": "mean: 6.8947 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 271.4167257171557,
            "unit": "iter/sec",
            "range": "stddev: 0.00015437",
            "group": "node",
            "extra": "mean: 3.6844 msec\nrounds: 125"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 108.41647480179543,
            "unit": "iter/sec",
            "range": "stddev: 0.00042277",
            "group": "node",
            "extra": "mean: 9.2237 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 100.54338895755774,
            "unit": "iter/sec",
            "range": "stddev: 0.0012949",
            "group": "node",
            "extra": "mean: 9.9460 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 157.74336854701372,
            "unit": "iter/sec",
            "range": "stddev: 0.00071472",
            "group": "node",
            "extra": "mean: 6.3394 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 42.27432246315317,
            "unit": "iter/sec",
            "range": "stddev: 0.0024160",
            "group": "node",
            "extra": "mean: 23.655 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 44.88350139813401,
            "unit": "iter/sec",
            "range": "stddev: 0.0016175",
            "group": "node",
            "extra": "mean: 22.280 msec\nrounds: 100"
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
          "pythonVersion": "3.8.7",
          "metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "97cecd2ef57946dd53a0ecd2005f3d2d0a94a2aa",
          "message": "Improve namedtuples in aiida/engine (#4688)\n\nThis commit replaces old-style namedtuples with `typing.NamedTuple` sub-classes.\r\nThis allows for typing of fields and better default value assignment.\r\n\r\nNote this feature requires python>=3.6.1,\r\nbut it is anyhow intended that python 3.6 be dropped for the next release.",
          "timestamp": "2021-01-27T16:27:28Z",
          "url": "https://github.com/aiidateam/aiida-core/commit/97cecd2ef57946dd53a0ecd2005f3d2d0a94a2aa",
          "distinct": true,
          "tree_id": "be611dfc75a388167d29fbdf7fc4afa02083c7bb"
        },
        "date": 1611765705077,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 2.5384104443793643,
            "unit": "iter/sec",
            "range": "stddev: 0.013706",
            "group": "engine",
            "extra": "mean: 393.95 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.5381412473593761,
            "unit": "iter/sec",
            "range": "stddev: 0.10201",
            "group": "engine",
            "extra": "mean: 1.8582 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.6186704880296218,
            "unit": "iter/sec",
            "range": "stddev: 0.061628",
            "group": "engine",
            "extra": "mean: 1.6164 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.1558239935801147,
            "unit": "iter/sec",
            "range": "stddev: 0.11603",
            "group": "engine",
            "extra": "mean: 6.4175 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.17678157651555157,
            "unit": "iter/sec",
            "range": "stddev: 0.086662",
            "group": "engine",
            "extra": "mean: 5.6567 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 1.9219393984804547,
            "unit": "iter/sec",
            "range": "stddev: 0.017756",
            "group": "engine",
            "extra": "mean: 520.31 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.43957708078939445,
            "unit": "iter/sec",
            "range": "stddev: 0.10150",
            "group": "engine",
            "extra": "mean: 2.2749 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.5002559672964652,
            "unit": "iter/sec",
            "range": "stddev: 0.092656",
            "group": "engine",
            "extra": "mean: 1.9990 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.13593751337843946,
            "unit": "iter/sec",
            "range": "stddev: 0.15447",
            "group": "engine",
            "extra": "mean: 7.3563 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.1604287360944831,
            "unit": "iter/sec",
            "range": "stddev: 0.17860",
            "group": "engine",
            "extra": "mean: 6.2333 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.0812196683175626,
            "unit": "iter/sec",
            "range": "stddev: 0.042058",
            "group": "import-export",
            "extra": "mean: 480.49 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 1.7939637677676232,
            "unit": "iter/sec",
            "range": "stddev: 0.052348",
            "group": "import-export",
            "extra": "mean: 557.42 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 0.1285723148667725,
            "unit": "iter/sec",
            "range": "stddev: 0.13125",
            "group": "import-export",
            "extra": "mean: 7.7777 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 0.12733895108273446,
            "unit": "iter/sec",
            "range": "stddev: 0.21207",
            "group": "import-export",
            "extra": "mean: 7.8531 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 244.03718716569378,
            "unit": "iter/sec",
            "range": "stddev: 0.00066053",
            "group": "node",
            "extra": "mean: 4.0977 msec\nrounds: 119"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 96.53937363608023,
            "unit": "iter/sec",
            "range": "stddev: 0.0010138",
            "group": "node",
            "extra": "mean: 10.358 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 95.01712305467565,
            "unit": "iter/sec",
            "range": "stddev: 0.0010380",
            "group": "node",
            "extra": "mean: 10.524 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 140.53368814818262,
            "unit": "iter/sec",
            "range": "stddev: 0.00072197",
            "group": "node",
            "extra": "mean: 7.1157 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 38.47854951749261,
            "unit": "iter/sec",
            "range": "stddev: 0.0025271",
            "group": "node",
            "extra": "mean: 25.989 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 37.0802748485906,
            "unit": "iter/sec",
            "range": "stddev: 0.014986",
            "group": "node",
            "extra": "mean: 26.969 msec\nrounds: 100"
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
          "pythonVersion": "3.8.7",
          "metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "a490fe07ab5752f04efaac338c1f1a9ef648426a",
          "message": "test AiiDA ipython magics and remove copy-paste in docs (#4548)\n\nAdds tests for the AiiDA IPython extension.\r\n\r\nAlso:\r\n * move some additional lines from the registration snippet to\r\n  aiida-core (where we can adapt it if the IPython API ever changes)\r\n * rename and deprecate misnomer `load_ipython_extension` to\r\n   `register_ipython_extension` (to be removed in aiida 3)\r\n * include the snippet to register the AiiDA ipython magics from the\r\n   aiida-core codebase instead of the (already outdated) copy-pasted\r\n  version.\r\n * revisit the corresponding section of the documentation, starting\r\n  with the setup, and removing some generic information about jupyter.",
          "timestamp": "2021-01-28T11:35:19+01:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/a490fe07ab5752f04efaac338c1f1a9ef648426a",
          "distinct": true,
          "tree_id": "df1a18e7bcad8e261d21edd143dfbcca29a10db4"
        },
        "date": 1611830890350,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 2.759663351372264,
            "unit": "iter/sec",
            "range": "stddev: 0.0056190",
            "group": "engine",
            "extra": "mean: 362.36 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.6172475198304247,
            "unit": "iter/sec",
            "range": "stddev: 0.062893",
            "group": "engine",
            "extra": "mean: 1.6201 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.7091996680965417,
            "unit": "iter/sec",
            "range": "stddev: 0.057059",
            "group": "engine",
            "extra": "mean: 1.4100 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.17301414850879965,
            "unit": "iter/sec",
            "range": "stddev: 0.12602",
            "group": "engine",
            "extra": "mean: 5.7799 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.20248009873355044,
            "unit": "iter/sec",
            "range": "stddev: 0.091915",
            "group": "engine",
            "extra": "mean: 4.9388 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.2290049455779433,
            "unit": "iter/sec",
            "range": "stddev: 0.016647",
            "group": "engine",
            "extra": "mean: 448.63 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.5158536030430053,
            "unit": "iter/sec",
            "range": "stddev: 0.054673",
            "group": "engine",
            "extra": "mean: 1.9385 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.5919359591380677,
            "unit": "iter/sec",
            "range": "stddev: 0.051980",
            "group": "engine",
            "extra": "mean: 1.6894 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.15504551817453952,
            "unit": "iter/sec",
            "range": "stddev: 0.065771",
            "group": "engine",
            "extra": "mean: 6.4497 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.18134805711962576,
            "unit": "iter/sec",
            "range": "stddev: 0.079350",
            "group": "engine",
            "extra": "mean: 5.5143 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.364643597334668,
            "unit": "iter/sec",
            "range": "stddev: 0.048020",
            "group": "import-export",
            "extra": "mean: 422.90 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.0870168270885063,
            "unit": "iter/sec",
            "range": "stddev: 0.042016",
            "group": "import-export",
            "extra": "mean: 479.15 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 0.14700597663371437,
            "unit": "iter/sec",
            "range": "stddev: 0.11331",
            "group": "import-export",
            "extra": "mean: 6.8024 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 0.14661870976982702,
            "unit": "iter/sec",
            "range": "stddev: 0.074852",
            "group": "import-export",
            "extra": "mean: 6.8204 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 269.90660996557546,
            "unit": "iter/sec",
            "range": "stddev: 0.00019474",
            "group": "node",
            "extra": "mean: 3.7050 msec\nrounds: 138"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 111.55277270803855,
            "unit": "iter/sec",
            "range": "stddev: 0.00023105",
            "group": "node",
            "extra": "mean: 8.9644 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 104.22396161828489,
            "unit": "iter/sec",
            "range": "stddev: 0.00086679",
            "group": "node",
            "extra": "mean: 9.5947 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 159.80198258772356,
            "unit": "iter/sec",
            "range": "stddev: 0.00075725",
            "group": "node",
            "extra": "mean: 6.2577 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 44.37719792107557,
            "unit": "iter/sec",
            "range": "stddev: 0.0010799",
            "group": "node",
            "extra": "mean: 22.534 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 44.10427610165761,
            "unit": "iter/sec",
            "range": "stddev: 0.0012501",
            "group": "node",
            "extra": "mean: 22.674 msec\nrounds: 100"
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
          "pythonVersion": "3.8.7",
          "metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "48fa47584c993cdac019c6199bc045a4c19da152",
          "message": "🐛 FIX: typing failure (#4700)\n\nAs of numpy v1.20, `numpy.inf` is no longer recognised as an integer type",
          "timestamp": "2021-02-01T16:58:01+01:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/48fa47584c993cdac019c6199bc045a4c19da152",
          "distinct": true,
          "tree_id": "b59c99e11366e8799e977e6ad12134514952c498"
        },
        "date": 1612195766180,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.1664371623512317,
            "unit": "iter/sec",
            "range": "stddev: 0.017428",
            "group": "engine",
            "extra": "mean: 315.81 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.6965555474386149,
            "unit": "iter/sec",
            "range": "stddev: 0.069021",
            "group": "engine",
            "extra": "mean: 1.4356 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.788302782033891,
            "unit": "iter/sec",
            "range": "stddev: 0.056680",
            "group": "engine",
            "extra": "mean: 1.2685 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.1973456404755011,
            "unit": "iter/sec",
            "range": "stddev: 0.24174",
            "group": "engine",
            "extra": "mean: 5.0673 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.22119834103708358,
            "unit": "iter/sec",
            "range": "stddev: 0.14679",
            "group": "engine",
            "extra": "mean: 4.5208 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.679346445798432,
            "unit": "iter/sec",
            "range": "stddev: 0.0075195",
            "group": "engine",
            "extra": "mean: 373.23 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.5704552558140804,
            "unit": "iter/sec",
            "range": "stddev: 0.085552",
            "group": "engine",
            "extra": "mean: 1.7530 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.6560672325176837,
            "unit": "iter/sec",
            "range": "stddev: 0.11000",
            "group": "engine",
            "extra": "mean: 1.5242 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.17432640844994224,
            "unit": "iter/sec",
            "range": "stddev: 0.15497",
            "group": "engine",
            "extra": "mean: 5.7364 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.2054875038306987,
            "unit": "iter/sec",
            "range": "stddev: 0.15323",
            "group": "engine",
            "extra": "mean: 4.8665 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.5806565528077545,
            "unit": "iter/sec",
            "range": "stddev: 0.018259",
            "group": "import-export",
            "extra": "mean: 387.50 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.52890864490116,
            "unit": "iter/sec",
            "range": "stddev: 0.052680",
            "group": "import-export",
            "extra": "mean: 395.43 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 0.17131842474129086,
            "unit": "iter/sec",
            "range": "stddev: 0.25713",
            "group": "import-export",
            "extra": "mean: 5.8371 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 0.16925878490513666,
            "unit": "iter/sec",
            "range": "stddev: 0.25586",
            "group": "import-export",
            "extra": "mean: 5.9081 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 313.6630056141039,
            "unit": "iter/sec",
            "range": "stddev: 0.00024446",
            "group": "node",
            "extra": "mean: 3.1881 msec\nrounds: 147"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 125.42010089890123,
            "unit": "iter/sec",
            "range": "stddev: 0.00016444",
            "group": "node",
            "extra": "mean: 7.9732 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 121.32860564452588,
            "unit": "iter/sec",
            "range": "stddev: 0.00017979",
            "group": "node",
            "extra": "mean: 8.2421 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 185.6476685945901,
            "unit": "iter/sec",
            "range": "stddev: 0.00011229",
            "group": "node",
            "extra": "mean: 5.3865 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 48.180854925640325,
            "unit": "iter/sec",
            "range": "stddev: 0.0028429",
            "group": "node",
            "extra": "mean: 20.755 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 51.29068671358622,
            "unit": "iter/sec",
            "range": "stddev: 0.0011191",
            "group": "node",
            "extra": "mean: 19.497 msec\nrounds: 100"
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
          "pythonVersion": "3.8.7",
          "metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "285ca45c41db75fbb0ed7eae5f6cdd3afd652da3",
          "message": "BUILD: drop support for python 3.6 (#4701)\n\nFollowing our support table, we drop python 3.6 support.",
          "timestamp": "2021-02-08T11:28:09+01:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/285ca45c41db75fbb0ed7eae5f6cdd3afd652da3",
          "distinct": true,
          "tree_id": "d2ac2f2e81d6c4a360b0643112b613ef08110a32"
        },
        "date": 1612780960870,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 2.2673309169314284,
            "unit": "iter/sec",
            "range": "stddev: 0.017956",
            "group": "engine",
            "extra": "mean: 441.05 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.530068971815018,
            "unit": "iter/sec",
            "range": "stddev: 0.049973",
            "group": "engine",
            "extra": "mean: 1.8865 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.6185763599615877,
            "unit": "iter/sec",
            "range": "stddev: 0.048682",
            "group": "engine",
            "extra": "mean: 1.6166 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.15905825989488823,
            "unit": "iter/sec",
            "range": "stddev: 0.087756",
            "group": "engine",
            "extra": "mean: 6.2870 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.17372988694118358,
            "unit": "iter/sec",
            "range": "stddev: 0.19068",
            "group": "engine",
            "extra": "mean: 5.7561 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 1.897210192575736,
            "unit": "iter/sec",
            "range": "stddev: 0.013732",
            "group": "engine",
            "extra": "mean: 527.09 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.4410130520344172,
            "unit": "iter/sec",
            "range": "stddev: 0.070372",
            "group": "engine",
            "extra": "mean: 2.2675 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.5219209549787812,
            "unit": "iter/sec",
            "range": "stddev: 0.068835",
            "group": "engine",
            "extra": "mean: 1.9160 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.13903930339936849,
            "unit": "iter/sec",
            "range": "stddev: 0.17086",
            "group": "engine",
            "extra": "mean: 7.1922 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.1614222452073494,
            "unit": "iter/sec",
            "range": "stddev: 0.17781",
            "group": "engine",
            "extra": "mean: 6.1949 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.0230598735945584,
            "unit": "iter/sec",
            "range": "stddev: 0.036555",
            "group": "import-export",
            "extra": "mean: 494.30 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 1.8390486626892528,
            "unit": "iter/sec",
            "range": "stddev: 0.011066",
            "group": "import-export",
            "extra": "mean: 543.76 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 0.12923044170675196,
            "unit": "iter/sec",
            "range": "stddev: 0.085681",
            "group": "import-export",
            "extra": "mean: 7.7381 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 0.12841082883548766,
            "unit": "iter/sec",
            "range": "stddev: 0.074170",
            "group": "import-export",
            "extra": "mean: 7.7875 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 254.22176318543075,
            "unit": "iter/sec",
            "range": "stddev: 0.00045386",
            "group": "node",
            "extra": "mean: 3.9336 msec\nrounds: 138"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 101.51652212818937,
            "unit": "iter/sec",
            "range": "stddev: 0.00078080",
            "group": "node",
            "extra": "mean: 9.8506 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 99.27881042662071,
            "unit": "iter/sec",
            "range": "stddev: 0.00082141",
            "group": "node",
            "extra": "mean: 10.073 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 151.7754793470533,
            "unit": "iter/sec",
            "range": "stddev: 0.00056243",
            "group": "node",
            "extra": "mean: 6.5887 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 39.98308450038394,
            "unit": "iter/sec",
            "range": "stddev: 0.0022693",
            "group": "node",
            "extra": "mean: 25.011 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 36.43450343365913,
            "unit": "iter/sec",
            "range": "stddev: 0.017814",
            "group": "node",
            "extra": "mean: 27.447 msec\nrounds: 100"
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
          "pythonVersion": "3.8.7",
          "metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "5d5fd4f4970743ddb2956a553db967e017fbbb0e",
          "message": "BUILD: bump jenkins dockerimage to 20.04 (#4714)\n\nDespite python3.7 being installed on the Jenkins dockerimage, pip\r\ninstall failed after dropping python 3.6 support (likely because pip\r\nfrom python 3.6 was being used).\r\n\r\nWe update ubuntu to 20.04, which comes with python 3.8.2 by default.",
          "timestamp": "2021-02-08T12:17:44+01:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/5d5fd4f4970743ddb2956a553db967e017fbbb0e",
          "distinct": true,
          "tree_id": "1efb6fa6841eb293d28aca1729fae41939ca1aab"
        },
        "date": 1612783950545,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 2.431130639508303,
            "unit": "iter/sec",
            "range": "stddev: 0.0059501",
            "group": "engine",
            "extra": "mean: 411.33 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.5280836512775153,
            "unit": "iter/sec",
            "range": "stddev: 0.086590",
            "group": "engine",
            "extra": "mean: 1.8936 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.6077619250307298,
            "unit": "iter/sec",
            "range": "stddev: 0.066716",
            "group": "engine",
            "extra": "mean: 1.6454 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.14697218707998058,
            "unit": "iter/sec",
            "range": "stddev: 0.13896",
            "group": "engine",
            "extra": "mean: 6.8040 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.16765973118494384,
            "unit": "iter/sec",
            "range": "stddev: 0.10370",
            "group": "engine",
            "extra": "mean: 5.9645 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 1.8158918418820749,
            "unit": "iter/sec",
            "range": "stddev: 0.018079",
            "group": "engine",
            "extra": "mean: 550.69 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.41255353875800554,
            "unit": "iter/sec",
            "range": "stddev: 0.097349",
            "group": "engine",
            "extra": "mean: 2.4239 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.4759327462341373,
            "unit": "iter/sec",
            "range": "stddev: 0.069192",
            "group": "engine",
            "extra": "mean: 2.1011 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.1282708481260884,
            "unit": "iter/sec",
            "range": "stddev: 0.11913",
            "group": "engine",
            "extra": "mean: 7.7960 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.1491734503624759,
            "unit": "iter/sec",
            "range": "stddev: 0.12625",
            "group": "engine",
            "extra": "mean: 6.7036 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.0433424496397397,
            "unit": "iter/sec",
            "range": "stddev: 0.055533",
            "group": "import-export",
            "extra": "mean: 489.39 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 1.8343506990836718,
            "unit": "iter/sec",
            "range": "stddev: 0.052194",
            "group": "import-export",
            "extra": "mean: 545.15 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 0.12544166688152772,
            "unit": "iter/sec",
            "range": "stddev: 0.23022",
            "group": "import-export",
            "extra": "mean: 7.9718 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 0.12340110710174662,
            "unit": "iter/sec",
            "range": "stddev: 0.14038",
            "group": "import-export",
            "extra": "mean: 8.1037 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 243.24400863985045,
            "unit": "iter/sec",
            "range": "stddev: 0.00041804",
            "group": "node",
            "extra": "mean: 4.1111 msec\nrounds: 120"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 96.23416494600022,
            "unit": "iter/sec",
            "range": "stddev: 0.00076962",
            "group": "node",
            "extra": "mean: 10.391 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 89.8057075340236,
            "unit": "iter/sec",
            "range": "stddev: 0.0012183",
            "group": "node",
            "extra": "mean: 11.135 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 142.34172043706138,
            "unit": "iter/sec",
            "range": "stddev: 0.00050111",
            "group": "node",
            "extra": "mean: 7.0253 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 34.681805575379386,
            "unit": "iter/sec",
            "range": "stddev: 0.019125",
            "group": "node",
            "extra": "mean: 28.834 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 37.645596013112524,
            "unit": "iter/sec",
            "range": "stddev: 0.0020594",
            "group": "node",
            "extra": "mean: 26.564 msec\nrounds: 100"
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
          "pythonVersion": "3.8.7",
          "metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "443dc01f0fdaba11060a2d6ddcd9cebf911d22c6",
          "message": "Switch matrix order in continuous-integration tests job. (#4713)\n\nTo harmonize with test-install workflow.",
          "timestamp": "2021-02-08T14:03:28+01:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/443dc01f0fdaba11060a2d6ddcd9cebf911d22c6",
          "distinct": true,
          "tree_id": "710f6ee960a33c7c0d2ec125e72daf2bfd969bc7"
        },
        "date": 1612790196465,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 2.749469689228755,
            "unit": "iter/sec",
            "range": "stddev: 0.0078120",
            "group": "engine",
            "extra": "mean: 363.71 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.5889122766317216,
            "unit": "iter/sec",
            "range": "stddev: 0.074992",
            "group": "engine",
            "extra": "mean: 1.6980 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.6899019135493609,
            "unit": "iter/sec",
            "range": "stddev: 0.076300",
            "group": "engine",
            "extra": "mean: 1.4495 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.16801567745011795,
            "unit": "iter/sec",
            "range": "stddev: 0.081040",
            "group": "engine",
            "extra": "mean: 5.9518 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.18934625534027855,
            "unit": "iter/sec",
            "range": "stddev: 0.097890",
            "group": "engine",
            "extra": "mean: 5.2813 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.124481722273901,
            "unit": "iter/sec",
            "range": "stddev: 0.0088070",
            "group": "engine",
            "extra": "mean: 470.70 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.4780202770340966,
            "unit": "iter/sec",
            "range": "stddev: 0.084703",
            "group": "engine",
            "extra": "mean: 2.0920 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.5462224841737267,
            "unit": "iter/sec",
            "range": "stddev: 0.073686",
            "group": "engine",
            "extra": "mean: 1.8308 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.14830288430391603,
            "unit": "iter/sec",
            "range": "stddev: 0.10492",
            "group": "engine",
            "extra": "mean: 6.7430 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.17444962697863026,
            "unit": "iter/sec",
            "range": "stddev: 0.10526",
            "group": "engine",
            "extra": "mean: 5.7323 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.3199409189461933,
            "unit": "iter/sec",
            "range": "stddev: 0.044862",
            "group": "import-export",
            "extra": "mean: 431.05 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.0251012084576114,
            "unit": "iter/sec",
            "range": "stddev: 0.046709",
            "group": "import-export",
            "extra": "mean: 493.80 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 0.144443818015145,
            "unit": "iter/sec",
            "range": "stddev: 0.11101",
            "group": "import-export",
            "extra": "mean: 6.9231 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 0.14516602893453268,
            "unit": "iter/sec",
            "range": "stddev: 0.063622",
            "group": "import-export",
            "extra": "mean: 6.8887 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 268.38024811322157,
            "unit": "iter/sec",
            "range": "stddev: 0.00012547",
            "group": "node",
            "extra": "mean: 3.7261 msec\nrounds: 134"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 109.51232965920643,
            "unit": "iter/sec",
            "range": "stddev: 0.00026539",
            "group": "node",
            "extra": "mean: 9.1314 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 106.43594577912584,
            "unit": "iter/sec",
            "range": "stddev: 0.00026903",
            "group": "node",
            "extra": "mean: 9.3953 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 161.14188854942566,
            "unit": "iter/sec",
            "range": "stddev: 0.00023254",
            "group": "node",
            "extra": "mean: 6.2057 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 42.23454172081453,
            "unit": "iter/sec",
            "range": "stddev: 0.0040817",
            "group": "node",
            "extra": "mean: 23.677 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 43.44452075918015,
            "unit": "iter/sec",
            "range": "stddev: 0.0015937",
            "group": "node",
            "extra": "mean: 23.018 msec\nrounds: 100"
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
          "pythonVersion": "3.8.7",
          "metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "a8e6b89e0765c120d3947c4b7165055d02f16d3e",
          "message": "♻️ REFACTOR: verdi export/import -> verdi archive (#4710)\n\nThis commit deprecates `verdi export` and `verdi import` and combines them into `verdi archive`.",
          "timestamp": "2021-02-08T16:31:26+01:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/a8e6b89e0765c120d3947c4b7165055d02f16d3e",
          "distinct": true,
          "tree_id": "7c831841596ab0aadda867ed5167c65f77078700"
        },
        "date": 1612799105997,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 2.660183326033867,
            "unit": "iter/sec",
            "range": "stddev: 0.013733",
            "group": "engine",
            "extra": "mean: 375.91 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.5997650836761539,
            "unit": "iter/sec",
            "range": "stddev: 0.061330",
            "group": "engine",
            "extra": "mean: 1.6673 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.6882458255208892,
            "unit": "iter/sec",
            "range": "stddev: 0.059549",
            "group": "engine",
            "extra": "mean: 1.4530 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.1747411878804926,
            "unit": "iter/sec",
            "range": "stddev: 0.078108",
            "group": "engine",
            "extra": "mean: 5.7227 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.19737450437248713,
            "unit": "iter/sec",
            "range": "stddev: 0.13377",
            "group": "engine",
            "extra": "mean: 5.0665 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.066817771011715,
            "unit": "iter/sec",
            "range": "stddev: 0.048819",
            "group": "engine",
            "extra": "mean: 483.84 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.4874046817147835,
            "unit": "iter/sec",
            "range": "stddev: 0.052434",
            "group": "engine",
            "extra": "mean: 2.0517 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.5591664152094843,
            "unit": "iter/sec",
            "range": "stddev: 0.067480",
            "group": "engine",
            "extra": "mean: 1.7884 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.15305637937765737,
            "unit": "iter/sec",
            "range": "stddev: 0.14398",
            "group": "engine",
            "extra": "mean: 6.5335 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.17901262974454257,
            "unit": "iter/sec",
            "range": "stddev: 0.11375",
            "group": "engine",
            "extra": "mean: 5.5862 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.197337610607103,
            "unit": "iter/sec",
            "range": "stddev: 0.056818",
            "group": "import-export",
            "extra": "mean: 455.10 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 1.9062258111458186,
            "unit": "iter/sec",
            "range": "stddev: 0.052223",
            "group": "import-export",
            "extra": "mean: 524.60 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 0.140238417783271,
            "unit": "iter/sec",
            "range": "stddev: 0.11407",
            "group": "import-export",
            "extra": "mean: 7.1307 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 0.13895035740061965,
            "unit": "iter/sec",
            "range": "stddev: 0.18169",
            "group": "import-export",
            "extra": "mean: 7.1968 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 286.4273849695586,
            "unit": "iter/sec",
            "range": "stddev: 0.00029258",
            "group": "node",
            "extra": "mean: 3.4913 msec\nrounds: 124"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 111.26820574558725,
            "unit": "iter/sec",
            "range": "stddev: 0.00066885",
            "group": "node",
            "extra": "mean: 8.9873 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 105.23100107304897,
            "unit": "iter/sec",
            "range": "stddev: 0.0010092",
            "group": "node",
            "extra": "mean: 9.5029 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 163.123113634769,
            "unit": "iter/sec",
            "range": "stddev: 0.00052257",
            "group": "node",
            "extra": "mean: 6.1303 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 41.69501236068061,
            "unit": "iter/sec",
            "range": "stddev: 0.017452",
            "group": "node",
            "extra": "mean: 23.984 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 44.61104793217834,
            "unit": "iter/sec",
            "range": "stddev: 0.0024340",
            "group": "node",
            "extra": "mean: 22.416 msec\nrounds: 100"
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
          "pythonVersion": "3.8.7",
          "metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "e6ba4657d1b77597afff333a172ef5379cb0786a",
          "message": "Dependencies: Require `ipython~=7.20` (#4715)\n\n* Dependencies: Require `ipython~=7.20`\r\n\r\nPackage jedi version 0.18 introduces backwards incompatible changes that\r\nbreak compatibility with ipython<7.20.\r\n\r\nFixes issue #4668.\r\n\r\n* Automated update of requirements/ files. (#4716)\r\n\r\nCo-authored-by: github-actions[bot] <41898282+github-actions[bot]@users.noreply.github.com>",
          "timestamp": "2021-02-08T17:08:33+01:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/e6ba4657d1b77597afff333a172ef5379cb0786a",
          "distinct": true,
          "tree_id": "c9ca6c8be723cc63e006f98ed63bca72a661e45c"
        },
        "date": 1612801204225,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.1427160165906716,
            "unit": "iter/sec",
            "range": "stddev: 0.0075434",
            "group": "engine",
            "extra": "mean: 318.20 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.7037910059569068,
            "unit": "iter/sec",
            "range": "stddev: 0.060616",
            "group": "engine",
            "extra": "mean: 1.4209 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.819989987025191,
            "unit": "iter/sec",
            "range": "stddev: 0.054908",
            "group": "engine",
            "extra": "mean: 1.2195 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.19832700421825117,
            "unit": "iter/sec",
            "range": "stddev: 0.055087",
            "group": "engine",
            "extra": "mean: 5.0422 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.2276489707927738,
            "unit": "iter/sec",
            "range": "stddev: 0.070161",
            "group": "engine",
            "extra": "mean: 4.3927 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.4779774953851343,
            "unit": "iter/sec",
            "range": "stddev: 0.045481",
            "group": "engine",
            "extra": "mean: 403.55 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.5725636880029061,
            "unit": "iter/sec",
            "range": "stddev: 0.070024",
            "group": "engine",
            "extra": "mean: 1.7465 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.6603233586292387,
            "unit": "iter/sec",
            "range": "stddev: 0.048210",
            "group": "engine",
            "extra": "mean: 1.5144 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.1748556135833956,
            "unit": "iter/sec",
            "range": "stddev: 0.099218",
            "group": "engine",
            "extra": "mean: 5.7190 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.20593372898443418,
            "unit": "iter/sec",
            "range": "stddev: 0.092464",
            "group": "engine",
            "extra": "mean: 4.8559 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.6394440762766274,
            "unit": "iter/sec",
            "range": "stddev: 0.040949",
            "group": "import-export",
            "extra": "mean: 378.87 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.33762063633184,
            "unit": "iter/sec",
            "range": "stddev: 0.038905",
            "group": "import-export",
            "extra": "mean: 427.79 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 0.16715841516131202,
            "unit": "iter/sec",
            "range": "stddev: 0.071683",
            "group": "import-export",
            "extra": "mean: 5.9823 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 0.1651036174250763,
            "unit": "iter/sec",
            "range": "stddev: 0.074312",
            "group": "import-export",
            "extra": "mean: 6.0568 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 312.37376714000493,
            "unit": "iter/sec",
            "range": "stddev: 0.00015898",
            "group": "node",
            "extra": "mean: 3.2013 msec\nrounds: 143"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 128.6748699604312,
            "unit": "iter/sec",
            "range": "stddev: 0.00017109",
            "group": "node",
            "extra": "mean: 7.7715 msec\nrounds: 103"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 124.44664291963734,
            "unit": "iter/sec",
            "range": "stddev: 0.00026546",
            "group": "node",
            "extra": "mean: 8.0356 msec\nrounds: 101"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 186.78165433442175,
            "unit": "iter/sec",
            "range": "stddev: 0.00023651",
            "group": "node",
            "extra": "mean: 5.3538 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 49.93349497615456,
            "unit": "iter/sec",
            "range": "stddev: 0.0011683",
            "group": "node",
            "extra": "mean: 20.027 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 50.23932474474069,
            "unit": "iter/sec",
            "range": "stddev: 0.00091756",
            "group": "node",
            "extra": "mean: 19.905 msec\nrounds: 100"
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
          "pythonVersion": "3.8.7",
          "metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "99f988b556c14c51dbc8ba37867fd67882730aae",
          "message": "♻️ REFACTOR: `ci/` folder (#4565)\n\nThis commit looks to address two issues:\r\n\r\n1. The `ci/` folder has become cluttered; \r\n   it contains configuration and scripts for both the GitHub Actions and Jenkins CI\r\n   and it is not easily clear which is for which.\r\n2. The Jenkins tests are somewhat of a black-box to most,\r\n   since it is certainly not trivial to set up and run them locally.\r\n   This has lead to them essentially not being touched since they were first written.\r\n\r\nThe changes are as follows:\r\n\r\n1. Moved the GH actions specific scripts to `.github/system_tests`\r\n2. Refactored the Jenkins setup/tests to use [molecule](https://molecule.readthedocs.io) in the `.molecule/` folder \r\n   (note we use molecule for testing all the quantum mobile code).\r\n   You can read about this setup in `.molecule/README.md`,\r\n   but essentially if you just run `tox -e molecule-django` locally it will create/launch a docker container, \r\n  setup and run the tests within that container, then destroy the container.\r\n  Locally, it additionally records and prints an analysis of queries made to the database during the workchain runs.\r\n3. Moved the Jenkins configuration to `.jenkins/`, which is now mainly a thin wrapper around (2).\r\n\r\nThis makes these tests more portable and easier to understand, modify or add to.",
          "timestamp": "2021-02-09T11:11:48+01:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/99f988b556c14c51dbc8ba37867fd67882730aae",
          "distinct": true,
          "tree_id": "725ab44c50018ccfffb8b66a5148d7982418c836"
        },
        "date": 1612866378725,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 2.2695643057803383,
            "unit": "iter/sec",
            "range": "stddev: 0.030121",
            "group": "engine",
            "extra": "mean: 440.61 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.4879231745940388,
            "unit": "iter/sec",
            "range": "stddev: 0.076251",
            "group": "engine",
            "extra": "mean: 2.0495 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.5956809520435437,
            "unit": "iter/sec",
            "range": "stddev: 0.072264",
            "group": "engine",
            "extra": "mean: 1.6788 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.15317424083124742,
            "unit": "iter/sec",
            "range": "stddev: 0.19129",
            "group": "engine",
            "extra": "mean: 6.5285 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.17117851746750065,
            "unit": "iter/sec",
            "range": "stddev: 0.19288",
            "group": "engine",
            "extra": "mean: 5.8419 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 1.8883633744829325,
            "unit": "iter/sec",
            "range": "stddev: 0.047161",
            "group": "engine",
            "extra": "mean: 529.56 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.432273951436679,
            "unit": "iter/sec",
            "range": "stddev: 0.10371",
            "group": "engine",
            "extra": "mean: 2.3133 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.49293881167852815,
            "unit": "iter/sec",
            "range": "stddev: 0.087590",
            "group": "engine",
            "extra": "mean: 2.0286 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.13913613307462747,
            "unit": "iter/sec",
            "range": "stddev: 0.15368",
            "group": "engine",
            "extra": "mean: 7.1872 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.15849563822376275,
            "unit": "iter/sec",
            "range": "stddev: 0.16939",
            "group": "engine",
            "extra": "mean: 6.3093 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.052234181998078,
            "unit": "iter/sec",
            "range": "stddev: 0.046468",
            "group": "import-export",
            "extra": "mean: 487.27 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 1.8852751276791453,
            "unit": "iter/sec",
            "range": "stddev: 0.041239",
            "group": "import-export",
            "extra": "mean: 530.43 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 0.12434485693663519,
            "unit": "iter/sec",
            "range": "stddev: 0.10515",
            "group": "import-export",
            "extra": "mean: 8.0422 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 0.12986651135482977,
            "unit": "iter/sec",
            "range": "stddev: 0.13526",
            "group": "import-export",
            "extra": "mean: 7.7002 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 250.6273353125786,
            "unit": "iter/sec",
            "range": "stddev: 0.00060353",
            "group": "node",
            "extra": "mean: 3.9900 msec\nrounds: 137"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 103.31525394553199,
            "unit": "iter/sec",
            "range": "stddev: 0.00082362",
            "group": "node",
            "extra": "mean: 9.6791 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 82.89908279167707,
            "unit": "iter/sec",
            "range": "stddev: 0.015780",
            "group": "node",
            "extra": "mean: 12.063 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 146.79831782498206,
            "unit": "iter/sec",
            "range": "stddev: 0.00059536",
            "group": "node",
            "extra": "mean: 6.8121 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 36.58739669955838,
            "unit": "iter/sec",
            "range": "stddev: 0.0047145",
            "group": "node",
            "extra": "mean: 27.332 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 39.59502629975674,
            "unit": "iter/sec",
            "range": "stddev: 0.0022996",
            "group": "node",
            "extra": "mean: 25.256 msec\nrounds: 100"
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
          "pythonVersion": "3.8.7",
          "metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "25d07d8fe0161c6f42067a906e50b617b7eb2f43",
          "message": "🔧 MAINTAIN: drop setuptools upper pinning (#4725)",
          "timestamp": "2021-02-09T13:31:48+01:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/25d07d8fe0161c6f42067a906e50b617b7eb2f43",
          "distinct": true,
          "tree_id": "57d30ec4d23dbd865847792ef36500d3f97b4a21"
        },
        "date": 1612874772558,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 2.2739746532543417,
            "unit": "iter/sec",
            "range": "stddev: 0.033793",
            "group": "engine",
            "extra": "mean: 439.76 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.5250498001728486,
            "unit": "iter/sec",
            "range": "stddev: 0.048209",
            "group": "engine",
            "extra": "mean: 1.9046 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.6130115643625709,
            "unit": "iter/sec",
            "range": "stddev: 0.065587",
            "group": "engine",
            "extra": "mean: 1.6313 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.1554759030958496,
            "unit": "iter/sec",
            "range": "stddev: 0.10297",
            "group": "engine",
            "extra": "mean: 6.4319 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.1762288377427032,
            "unit": "iter/sec",
            "range": "stddev: 0.094431",
            "group": "engine",
            "extra": "mean: 5.6744 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 1.8546987911407258,
            "unit": "iter/sec",
            "range": "stddev: 0.043874",
            "group": "engine",
            "extra": "mean: 539.17 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.4312064453240812,
            "unit": "iter/sec",
            "range": "stddev: 0.052109",
            "group": "engine",
            "extra": "mean: 2.3191 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.4999130076129825,
            "unit": "iter/sec",
            "range": "stddev: 0.049221",
            "group": "engine",
            "extra": "mean: 2.0003 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.13412769751308656,
            "unit": "iter/sec",
            "range": "stddev: 0.23680",
            "group": "engine",
            "extra": "mean: 7.4556 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.15844665942302,
            "unit": "iter/sec",
            "range": "stddev: 0.12190",
            "group": "engine",
            "extra": "mean: 6.3113 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 1.9904903266367673,
            "unit": "iter/sec",
            "range": "stddev: 0.038577",
            "group": "import-export",
            "extra": "mean: 502.39 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 1.771179765532892,
            "unit": "iter/sec",
            "range": "stddev: 0.035777",
            "group": "import-export",
            "extra": "mean: 564.60 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 0.12831315870817636,
            "unit": "iter/sec",
            "range": "stddev: 0.16873",
            "group": "import-export",
            "extra": "mean: 7.7934 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 0.13239259736197154,
            "unit": "iter/sec",
            "range": "stddev: 0.093894",
            "group": "import-export",
            "extra": "mean: 7.5533 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 250.6732379350908,
            "unit": "iter/sec",
            "range": "stddev: 0.00034767",
            "group": "node",
            "extra": "mean: 3.9893 msec\nrounds: 130"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 101.86506665619017,
            "unit": "iter/sec",
            "range": "stddev: 0.0010286",
            "group": "node",
            "extra": "mean: 9.8169 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 100.74759166055802,
            "unit": "iter/sec",
            "range": "stddev: 0.00044574",
            "group": "node",
            "extra": "mean: 9.9258 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 150.325494456974,
            "unit": "iter/sec",
            "range": "stddev: 0.00040773",
            "group": "node",
            "extra": "mean: 6.6522 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 39.266266970023885,
            "unit": "iter/sec",
            "range": "stddev: 0.0022297",
            "group": "node",
            "extra": "mean: 25.467 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 38.54856901721602,
            "unit": "iter/sec",
            "range": "stddev: 0.0020956",
            "group": "node",
            "extra": "mean: 25.941 msec\nrounds: 100"
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
          "pythonVersion": "3.8.7",
          "metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "e7223ae9596809efe44e50e371a67cdc9216120b",
          "message": "CI: Improve polish workchain failure debugging (#4729)",
          "timestamp": "2021-02-09T13:48:25+01:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/e7223ae9596809efe44e50e371a67cdc9216120b",
          "distinct": true,
          "tree_id": "8a468f37acc3a8d478d607c10191cbf28b6f6efb"
        },
        "date": 1612875796322,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 2.2491518678282225,
            "unit": "iter/sec",
            "range": "stddev: 0.017705",
            "group": "engine",
            "extra": "mean: 444.61 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.5064252057093278,
            "unit": "iter/sec",
            "range": "stddev: 0.082078",
            "group": "engine",
            "extra": "mean: 1.9746 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.5804795731929284,
            "unit": "iter/sec",
            "range": "stddev: 0.075040",
            "group": "engine",
            "extra": "mean: 1.7227 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.15055170574676718,
            "unit": "iter/sec",
            "range": "stddev: 0.12846",
            "group": "engine",
            "extra": "mean: 6.6422 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.17036258425813736,
            "unit": "iter/sec",
            "range": "stddev: 0.080685",
            "group": "engine",
            "extra": "mean: 5.8698 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 1.7740964286543435,
            "unit": "iter/sec",
            "range": "stddev: 0.050139",
            "group": "engine",
            "extra": "mean: 563.67 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.4093581254837413,
            "unit": "iter/sec",
            "range": "stddev: 0.051699",
            "group": "engine",
            "extra": "mean: 2.4428 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.46858005175533396,
            "unit": "iter/sec",
            "range": "stddev: 0.090386",
            "group": "engine",
            "extra": "mean: 2.1341 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.13247127161244907,
            "unit": "iter/sec",
            "range": "stddev: 0.11429",
            "group": "engine",
            "extra": "mean: 7.5488 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.15308168419038737,
            "unit": "iter/sec",
            "range": "stddev: 0.10764",
            "group": "engine",
            "extra": "mean: 6.5325 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 1.8925444605310286,
            "unit": "iter/sec",
            "range": "stddev: 0.057201",
            "group": "import-export",
            "extra": "mean: 528.39 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 1.6884208393466904,
            "unit": "iter/sec",
            "range": "stddev: 0.035299",
            "group": "import-export",
            "extra": "mean: 592.27 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 0.12453031721119824,
            "unit": "iter/sec",
            "range": "stddev: 0.19736",
            "group": "import-export",
            "extra": "mean: 8.0302 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 0.12634400080833583,
            "unit": "iter/sec",
            "range": "stddev: 0.091780",
            "group": "import-export",
            "extra": "mean: 7.9149 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 244.40734840946905,
            "unit": "iter/sec",
            "range": "stddev: 0.00059641",
            "group": "node",
            "extra": "mean: 4.0915 msec\nrounds: 139"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 97.82078140190772,
            "unit": "iter/sec",
            "range": "stddev: 0.0010685",
            "group": "node",
            "extra": "mean: 10.223 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 95.98410094781843,
            "unit": "iter/sec",
            "range": "stddev: 0.00070909",
            "group": "node",
            "extra": "mean: 10.418 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 142.75472837173234,
            "unit": "iter/sec",
            "range": "stddev: 0.00057924",
            "group": "node",
            "extra": "mean: 7.0050 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 36.87246113585813,
            "unit": "iter/sec",
            "range": "stddev: 0.0031909",
            "group": "node",
            "extra": "mean: 27.121 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 38.38107740422317,
            "unit": "iter/sec",
            "range": "stddev: 0.0018097",
            "group": "node",
            "extra": "mean: 26.055 msec\nrounds: 100"
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
          "pythonVersion": "3.8.7",
          "metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "b07841ad5503085913850c96aed85eb89b226d3b",
          "message": "fix: don't pass process stack via context (#4699)\n\nThis PR fixes a memory leak: when running `CalcJob`s over an SSH connection,\r\nthe first CalcJob that was run remained in memory indefinitely.\r\n\r\n`plumpy` uses the `contextvars` module to provide a reference to the\r\n`current_process` anywhere in a task launched by a process.  When using any of\r\n`asyncio`'s `call_soon`, `call_later` or `call_at` methods, each individual\r\nfunction execution gets their own copy of this context.  This means that as\r\nlong as a handle to these scheduled executions remains in memory, the copy of\r\nthe `'process stack'` context var (and thus the process itself) remain in\r\nmemory,\r\n\r\nIn this particular case, a handle to such a task (`do_open` a `transport`)\r\nremained in memory and caused the whole process to remain in memory as well via\r\nthe 'process stack' context variable.  This is fixed by explicitly passing an\r\nempty context to the execution of `do_open` (which anyhow does not need access\r\nto the `current_process`).  An explicit test is added to make sure that no\r\nreferences to processes are leaked after running process via the interpreter\r\nas well as in the daemon tests.\r\n\r\nThis PR adds the empty context in two other invocations of `call_later`, but\r\nthere are more places in the code where these methods are used. As such it is a\r\nbit of a workaround.  Eventually, this problem should likely be addressed by\r\nconverting any functions that use `call_soon`, `call_later` or `call_at` and\r\nall their parents in the call stack to coroutines.\r\n\r\nCo-authored-by: Chris Sewell <chrisj_sewell@hotmail.com>",
          "timestamp": "2021-02-09T14:43:59+01:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/b07841ad5503085913850c96aed85eb89b226d3b",
          "distinct": true,
          "tree_id": "2f09048b1303c15a5ae5fdf92fba1df932e47f43"
        },
        "date": 1612879085186,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 2.4398840369669825,
            "unit": "iter/sec",
            "range": "stddev: 0.011407",
            "group": "engine",
            "extra": "mean: 409.86 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.5476270200475264,
            "unit": "iter/sec",
            "range": "stddev: 0.079590",
            "group": "engine",
            "extra": "mean: 1.8261 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.6414678774098727,
            "unit": "iter/sec",
            "range": "stddev: 0.065707",
            "group": "engine",
            "extra": "mean: 1.5589 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.16350914480607254,
            "unit": "iter/sec",
            "range": "stddev: 0.13231",
            "group": "engine",
            "extra": "mean: 6.1159 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.18575179068320524,
            "unit": "iter/sec",
            "range": "stddev: 0.12382",
            "group": "engine",
            "extra": "mean: 5.3835 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 1.9356295506936758,
            "unit": "iter/sec",
            "range": "stddev: 0.046921",
            "group": "engine",
            "extra": "mean: 516.63 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.4518562297908002,
            "unit": "iter/sec",
            "range": "stddev: 0.044862",
            "group": "engine",
            "extra": "mean: 2.2131 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.5177702236481728,
            "unit": "iter/sec",
            "range": "stddev: 0.074858",
            "group": "engine",
            "extra": "mean: 1.9314 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.1423004556987462,
            "unit": "iter/sec",
            "range": "stddev: 0.14667",
            "group": "engine",
            "extra": "mean: 7.0274 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.16314570653008711,
            "unit": "iter/sec",
            "range": "stddev: 0.098504",
            "group": "engine",
            "extra": "mean: 6.1295 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 1.9284007436866404,
            "unit": "iter/sec",
            "range": "stddev: 0.044911",
            "group": "import-export",
            "extra": "mean: 518.56 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 1.729182742929714,
            "unit": "iter/sec",
            "range": "stddev: 0.050656",
            "group": "import-export",
            "extra": "mean: 578.31 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 0.13122360816276002,
            "unit": "iter/sec",
            "range": "stddev: 0.19293",
            "group": "import-export",
            "extra": "mean: 7.6206 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 0.1326972090471393,
            "unit": "iter/sec",
            "range": "stddev: 0.12793",
            "group": "import-export",
            "extra": "mean: 7.5360 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 264.54197550276524,
            "unit": "iter/sec",
            "range": "stddev: 0.00054116",
            "group": "node",
            "extra": "mean: 3.7801 msec\nrounds: 127"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 104.34301004909773,
            "unit": "iter/sec",
            "range": "stddev: 0.0011670",
            "group": "node",
            "extra": "mean: 9.5838 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 103.51221521457514,
            "unit": "iter/sec",
            "range": "stddev: 0.00072050",
            "group": "node",
            "extra": "mean: 9.6607 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 153.09758368196754,
            "unit": "iter/sec",
            "range": "stddev: 0.00079147",
            "group": "node",
            "extra": "mean: 6.5318 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 38.79758425986814,
            "unit": "iter/sec",
            "range": "stddev: 0.015782",
            "group": "node",
            "extra": "mean: 25.775 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 38.9807745373661,
            "unit": "iter/sec",
            "range": "stddev: 0.0059094",
            "group": "node",
            "extra": "mean: 25.654 msec\nrounds: 100"
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
          "pythonVersion": "3.8.7",
          "metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "b5cc416be182ae0801363fca793d07170cd23905",
          "message": "CI: Add retry for polish workchains (#4733)\n\nTo mitigate failures on Jenkins",
          "timestamp": "2021-02-09T15:46:14+01:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/b5cc416be182ae0801363fca793d07170cd23905",
          "distinct": true,
          "tree_id": "a73651cc1389ecf447f79753e227352b56bb38ed"
        },
        "date": 1612882728010,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.149654423948157,
            "unit": "iter/sec",
            "range": "stddev: 0.0058177",
            "group": "engine",
            "extra": "mean: 317.50 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.5923937068755174,
            "unit": "iter/sec",
            "range": "stddev: 0.23570",
            "group": "engine",
            "extra": "mean: 1.6881 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.7468080126095114,
            "unit": "iter/sec",
            "range": "stddev: 0.062494",
            "group": "engine",
            "extra": "mean: 1.3390 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.18422994446900595,
            "unit": "iter/sec",
            "range": "stddev: 0.16894",
            "group": "engine",
            "extra": "mean: 5.4280 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.21658340858960679,
            "unit": "iter/sec",
            "range": "stddev: 0.13339",
            "group": "engine",
            "extra": "mean: 4.6172 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.1525452582843796,
            "unit": "iter/sec",
            "range": "stddev: 0.066610",
            "group": "engine",
            "extra": "mean: 464.57 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.49766208034182396,
            "unit": "iter/sec",
            "range": "stddev: 0.092555",
            "group": "engine",
            "extra": "mean: 2.0094 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.5754388280001637,
            "unit": "iter/sec",
            "range": "stddev: 0.085103",
            "group": "engine",
            "extra": "mean: 1.7378 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.16338645789587822,
            "unit": "iter/sec",
            "range": "stddev: 0.21498",
            "group": "engine",
            "extra": "mean: 6.1205 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.12533617213747078,
            "unit": "iter/sec",
            "range": "stddev: 2.5012",
            "group": "engine",
            "extra": "mean: 7.9785 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.808299099822428,
            "unit": "iter/sec",
            "range": "stddev: 0.053221",
            "group": "import-export",
            "extra": "mean: 356.09 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.4959826535196488,
            "unit": "iter/sec",
            "range": "stddev: 0.054902",
            "group": "import-export",
            "extra": "mean: 400.64 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 0.1541210208424618,
            "unit": "iter/sec",
            "range": "stddev: 0.12342",
            "group": "import-export",
            "extra": "mean: 6.4884 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 0.1549679738252792,
            "unit": "iter/sec",
            "range": "stddev: 0.15355",
            "group": "import-export",
            "extra": "mean: 6.4529 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 343.1869368982559,
            "unit": "iter/sec",
            "range": "stddev: 0.000093949",
            "group": "node",
            "extra": "mean: 2.9139 msec\nrounds: 147"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 137.50814046518977,
            "unit": "iter/sec",
            "range": "stddev: 0.00015006",
            "group": "node",
            "extra": "mean: 7.2723 msec\nrounds: 103"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 134.18812156885548,
            "unit": "iter/sec",
            "range": "stddev: 0.00034225",
            "group": "node",
            "extra": "mean: 7.4522 msec\nrounds: 103"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 200.4939493240593,
            "unit": "iter/sec",
            "range": "stddev: 0.00011988",
            "group": "node",
            "extra": "mean: 4.9877 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 50.26386068958614,
            "unit": "iter/sec",
            "range": "stddev: 0.0012266",
            "group": "node",
            "extra": "mean: 19.895 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 49.88091627079439,
            "unit": "iter/sec",
            "range": "stddev: 0.0012284",
            "group": "node",
            "extra": "mean: 20.048 msec\nrounds: 100"
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
          "pythonVersion": "3.8.7",
          "metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "e99227b1b9c13df637cf8f9079134182a8c18102",
          "message": "🐛 FIX: Standardise transport task interrupt handling (#4692)\n\nFor all transport tasks (upload, submit, update, retrieve),\r\nboth `plumpy.futures.CancelledError` and `plumpy.process_states.Interruption` exceptions\r\nshould be ignored by the exponential backoff mechanism (i.e. the task should not be retried)\r\nand raised directly (as opposed to as a `TransportTaskException`),\r\nso that they can be correctly caught by the `Waiting.execute` method.\r\n\r\nAs an example, this fixes a known bug, whereby the upload task could not be\r\ncancelled via `CTRL-C` in an ipython shell.",
          "timestamp": "2021-02-09T16:21:25+01:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/e99227b1b9c13df637cf8f9079134182a8c18102",
          "distinct": true,
          "tree_id": "9199471365d4b98daec72685caf0bf82f129e53e"
        },
        "date": 1612884923943,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 2.2458642278300034,
            "unit": "iter/sec",
            "range": "stddev: 0.061835",
            "group": "engine",
            "extra": "mean: 445.26 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.5245867463394926,
            "unit": "iter/sec",
            "range": "stddev: 0.092866",
            "group": "engine",
            "extra": "mean: 1.9063 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.6244252429068432,
            "unit": "iter/sec",
            "range": "stddev: 0.064937",
            "group": "engine",
            "extra": "mean: 1.6015 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.16086527659415978,
            "unit": "iter/sec",
            "range": "stddev: 0.096875",
            "group": "engine",
            "extra": "mean: 6.2164 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.18590924622252572,
            "unit": "iter/sec",
            "range": "stddev: 0.12986",
            "group": "engine",
            "extra": "mean: 5.3790 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 1.9794818060467618,
            "unit": "iter/sec",
            "range": "stddev: 0.053893",
            "group": "engine",
            "extra": "mean: 505.18 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.4530440042365288,
            "unit": "iter/sec",
            "range": "stddev: 0.079527",
            "group": "engine",
            "extra": "mean: 2.2073 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.5377748772504956,
            "unit": "iter/sec",
            "range": "stddev: 0.060879",
            "group": "engine",
            "extra": "mean: 1.8595 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.14354539170313493,
            "unit": "iter/sec",
            "range": "stddev: 0.10630",
            "group": "engine",
            "extra": "mean: 6.9664 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.16892947493658003,
            "unit": "iter/sec",
            "range": "stddev: 0.091815",
            "group": "engine",
            "extra": "mean: 5.9196 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.1547570383222103,
            "unit": "iter/sec",
            "range": "stddev: 0.049424",
            "group": "import-export",
            "extra": "mean: 464.09 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 1.9417711741329713,
            "unit": "iter/sec",
            "range": "stddev: 0.055299",
            "group": "import-export",
            "extra": "mean: 514.99 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 0.13587906691192006,
            "unit": "iter/sec",
            "range": "stddev: 0.11704",
            "group": "import-export",
            "extra": "mean: 7.3595 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 0.13586281485066876,
            "unit": "iter/sec",
            "range": "stddev: 0.12623",
            "group": "import-export",
            "extra": "mean: 7.3604 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 261.6242895812196,
            "unit": "iter/sec",
            "range": "stddev: 0.00047088",
            "group": "node",
            "extra": "mean: 3.8223 msec\nrounds: 127"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 107.18987663310358,
            "unit": "iter/sec",
            "range": "stddev: 0.00045224",
            "group": "node",
            "extra": "mean: 9.3292 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 102.8057426646651,
            "unit": "iter/sec",
            "range": "stddev: 0.0013718",
            "group": "node",
            "extra": "mean: 9.7271 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 154.1615035347259,
            "unit": "iter/sec",
            "range": "stddev: 0.00052500",
            "group": "node",
            "extra": "mean: 6.4867 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 39.7888053818792,
            "unit": "iter/sec",
            "range": "stddev: 0.015199",
            "group": "node",
            "extra": "mean: 25.133 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 41.189871863278654,
            "unit": "iter/sec",
            "range": "stddev: 0.0023596",
            "group": "node",
            "extra": "mean: 24.278 msec\nrounds: 100"
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
          "pythonVersion": "3.8.7",
          "metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "6b6481d31f34cd07b0011651fad2c19f42739621",
          "message": "Update use of various deprecated APIs (#4719)\n\nThis replaces the use of various deprecated APIs pointed out by warnings\r\nthrown during runs of the test suite.\r\nIt also introduces one new feature and a bug fix.\r\n\r\nFeatures:\r\n\r\n * Add non-zero exit code for failure to most `verdi daemon` commands, \r\n    so tests will catch possible errors.\r\n\r\nBug fixes:\r\n\r\n* A couple of files were opened but not closed\r\n\r\nUpdates of deprecated APIs:\r\n\r\n* np.int is deprecated alias of int\r\n\r\n* np.float is deprecated alias of float\r\n\r\n* put_object_from_filelike: force is deprecated\r\n\r\n* archive import/export:  `silent` keyword is deprecated in favor of logger\r\n\r\n* computer name => label\r\n\r\n* Fix tests writing to the repository of nodes after they had been stored\r\n  by replacing all times we use `.open` with `'w'` or `'wb'` mode\r\n  with a correct call to `put_object_from_filelike` *before* the node is stored.\r\n\r\nIn one case, the data comes from a small archive file. In this case,\r\nI recreated the (zipped) .aiida file adding two additional (binary) files\r\nobtained by gzipping a short string.\r\nThis was used to ensure that `inputcat` and `outputcat` work also\r\nwhen binary data was requested. Actually, this is better than before,\r\nwhere the actual input or output of the calculation were overwritten\r\nand then replaced back.\r\n\r\n* communicator: replace deprecated stop() by close()\r\n\r\n* silence some deprecation warnings in tests of APIs that will be removed in 2.0\r\n\r\nNote that while unmuting the `ResourceWarning` was good to spot\r\nsome issues (bug fix above), the warning is raised in a couple more \r\nplaces where it's less obvious to fix (typically related to the daemon\r\nstarting some process in the background - or being started itself -\r\nand not being stopped before the test actually finished).\r\nI think this is an acceptable compromise - maybe we'll figure out\r\nhow to selectively silence those, and keeping warnings visible will\r\nhelp us figure out possible leaks in the future.\r\n\r\nCo-authored-by: Giovanni Pizzi <giovanni.pizzi@epfl.ch>",
          "timestamp": "2021-02-09T22:18:54+01:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/6b6481d31f34cd07b0011651fad2c19f42739621",
          "distinct": true,
          "tree_id": "a65c555bfa7b63172281cecdbf9234869025f05c"
        },
        "date": 1612906531426,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 2.101324747553605,
            "unit": "iter/sec",
            "range": "stddev: 0.015811",
            "group": "engine",
            "extra": "mean: 475.89 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.4546971106855174,
            "unit": "iter/sec",
            "range": "stddev: 0.11244",
            "group": "engine",
            "extra": "mean: 2.1993 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.5531640769745518,
            "unit": "iter/sec",
            "range": "stddev: 0.075355",
            "group": "engine",
            "extra": "mean: 1.8078 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.13815878160787473,
            "unit": "iter/sec",
            "range": "stddev: 0.17348",
            "group": "engine",
            "extra": "mean: 7.2380 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.15816385119812543,
            "unit": "iter/sec",
            "range": "stddev: 0.19878",
            "group": "engine",
            "extra": "mean: 6.3226 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 1.6420056255513444,
            "unit": "iter/sec",
            "range": "stddev: 0.059059",
            "group": "engine",
            "extra": "mean: 609.01 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.3721487325571084,
            "unit": "iter/sec",
            "range": "stddev: 0.12437",
            "group": "engine",
            "extra": "mean: 2.6871 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.43150519108909097,
            "unit": "iter/sec",
            "range": "stddev: 0.071010",
            "group": "engine",
            "extra": "mean: 2.3175 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.12281675158028893,
            "unit": "iter/sec",
            "range": "stddev: 0.18210",
            "group": "engine",
            "extra": "mean: 8.1422 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.14065196058778337,
            "unit": "iter/sec",
            "range": "stddev: 0.21681",
            "group": "engine",
            "extra": "mean: 7.1097 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 1.7618141502020117,
            "unit": "iter/sec",
            "range": "stddev: 0.053915",
            "group": "import-export",
            "extra": "mean: 567.60 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 1.3618434605079501,
            "unit": "iter/sec",
            "range": "stddev: 0.056058",
            "group": "import-export",
            "extra": "mean: 734.30 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 0.1073403595920067,
            "unit": "iter/sec",
            "range": "stddev: 0.20858",
            "group": "import-export",
            "extra": "mean: 9.3162 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 0.11480871692167421,
            "unit": "iter/sec",
            "range": "stddev: 0.20544",
            "group": "import-export",
            "extra": "mean: 8.7101 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 239.7219387899252,
            "unit": "iter/sec",
            "range": "stddev: 0.00069036",
            "group": "node",
            "extra": "mean: 4.1715 msec\nrounds: 124"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 92.7461923956442,
            "unit": "iter/sec",
            "range": "stddev: 0.00095682",
            "group": "node",
            "extra": "mean: 10.782 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 87.9323330659701,
            "unit": "iter/sec",
            "range": "stddev: 0.0014987",
            "group": "node",
            "extra": "mean: 11.372 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 133.760657972391,
            "unit": "iter/sec",
            "range": "stddev: 0.0012163",
            "group": "node",
            "extra": "mean: 7.4760 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 34.07902894779075,
            "unit": "iter/sec",
            "range": "stddev: 0.0049054",
            "group": "node",
            "extra": "mean: 29.344 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 32.55055299111665,
            "unit": "iter/sec",
            "range": "stddev: 0.016534",
            "group": "node",
            "extra": "mean: 30.721 msec\nrounds: 100"
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
          "pythonVersion": "3.8.7",
          "metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "11cb38cf14b4903ca8af53127ddf78c6034c9cae",
          "message": "✨ NEW: Add `verdi database summary` (#4737)\n\nPrints a summary of the count of each entity and,\r\nwith `-v` flag, additional summary of the unique identifiers for some entities.",
          "timestamp": "2021-02-10T14:23:17+01:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/11cb38cf14b4903ca8af53127ddf78c6034c9cae",
          "distinct": true,
          "tree_id": "b663fa4c67b17115a20bff0d2fa06e3b9b731db3"
        },
        "date": 1612964278485,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 2.267406584680789,
            "unit": "iter/sec",
            "range": "stddev: 0.035887",
            "group": "engine",
            "extra": "mean: 441.03 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.5263595838099933,
            "unit": "iter/sec",
            "range": "stddev: 0.065663",
            "group": "engine",
            "extra": "mean: 1.8998 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.6154290151605939,
            "unit": "iter/sec",
            "range": "stddev: 0.073220",
            "group": "engine",
            "extra": "mean: 1.6249 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.15509763109326682,
            "unit": "iter/sec",
            "range": "stddev: 0.12088",
            "group": "engine",
            "extra": "mean: 6.4476 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.17546453846149115,
            "unit": "iter/sec",
            "range": "stddev: 0.077158",
            "group": "engine",
            "extra": "mean: 5.6992 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 1.7778080261146472,
            "unit": "iter/sec",
            "range": "stddev: 0.056100",
            "group": "engine",
            "extra": "mean: 562.49 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.4250440821782251,
            "unit": "iter/sec",
            "range": "stddev: 0.054299",
            "group": "engine",
            "extra": "mean: 2.3527 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.49172564949269654,
            "unit": "iter/sec",
            "range": "stddev: 0.093170",
            "group": "engine",
            "extra": "mean: 2.0337 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.13247619227532348,
            "unit": "iter/sec",
            "range": "stddev: 0.24925",
            "group": "engine",
            "extra": "mean: 7.5485 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.15589367525387385,
            "unit": "iter/sec",
            "range": "stddev: 0.12171",
            "group": "engine",
            "extra": "mean: 6.4146 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 1.937624132457029,
            "unit": "iter/sec",
            "range": "stddev: 0.064686",
            "group": "import-export",
            "extra": "mean: 516.10 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 1.7236977823291886,
            "unit": "iter/sec",
            "range": "stddev: 0.047508",
            "group": "import-export",
            "extra": "mean: 580.15 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 0.12338220416189166,
            "unit": "iter/sec",
            "range": "stddev: 0.11401",
            "group": "import-export",
            "extra": "mean: 8.1049 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 0.12269061597191201,
            "unit": "iter/sec",
            "range": "stddev: 0.13200",
            "group": "import-export",
            "extra": "mean: 8.1506 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 232.28731221991217,
            "unit": "iter/sec",
            "range": "stddev: 0.0011191",
            "group": "node",
            "extra": "mean: 4.3050 msec\nrounds: 124"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 93.44605540372264,
            "unit": "iter/sec",
            "range": "stddev: 0.0011207",
            "group": "node",
            "extra": "mean: 10.701 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 91.59835017448327,
            "unit": "iter/sec",
            "range": "stddev: 0.0014213",
            "group": "node",
            "extra": "mean: 10.917 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 138.40970641140495,
            "unit": "iter/sec",
            "range": "stddev: 0.00083446",
            "group": "node",
            "extra": "mean: 7.2249 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 36.246042510734725,
            "unit": "iter/sec",
            "range": "stddev: 0.0025575",
            "group": "node",
            "extra": "mean: 27.589 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 32.705415968937125,
            "unit": "iter/sec",
            "range": "stddev: 0.017062",
            "group": "node",
            "extra": "mean: 30.576 msec\nrounds: 100"
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
          "pythonVersion": "3.8.7",
          "metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "7272b46dbd8aadb4be42dc6ce757a03126fedc4f",
          "message": "Upgrading dependency of sqlalchemy-utils (#4724)\n\n* Upgrading dependency of sqlalchemy-utils\r\n\r\nIn sqlalchemy-utils 0.35, imports from collections where correctly\r\nfixed to import from collections.abc (where this is needed).\r\nThis removes a few deprecation warnings (claiming that this will not\r\nwork in py 3.9, even if in reality this will stop working in py 3.10).\r\nThis partially addresses #4723.\r\n\r\nWe are actually pinning to >=0.36 since in 0.36 a feature was dropped\r\nthat we were planning to use (see #3845). In this way, we avoid relying\r\non a feature that is removed in later versions (risking to implement\r\nsomething that then we have to remove, or even worse remain \"pinned\"\r\nto an old version of sqlalchemy-utils because nobody has the time\r\nto fix it with a different implementation [which is tricky, requires\r\nsome knowledge of how SqlAlchemy and PosgreSQL work]).\r\n\r\n* Automated update of requirements/ files. (#4734)\r\n\r\nCo-authored-by: github-actions[bot] <41898282+github-actions[bot]@users.noreply.github.com>\r\nCo-authored-by: Carl Simon Adorf <simon.adorf@epfl.ch>",
          "timestamp": "2021-02-10T16:19:09+01:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/7272b46dbd8aadb4be42dc6ce757a03126fedc4f",
          "distinct": true,
          "tree_id": "57087669799d44a90aae9d3aca555d784995cbce"
        },
        "date": 1612971132320,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 2.2476516313238384,
            "unit": "iter/sec",
            "range": "stddev: 0.25156",
            "group": "engine",
            "extra": "mean: 444.91 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.6127033788709232,
            "unit": "iter/sec",
            "range": "stddev: 0.041827",
            "group": "engine",
            "extra": "mean: 1.6321 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.7072871865885052,
            "unit": "iter/sec",
            "range": "stddev: 0.053661",
            "group": "engine",
            "extra": "mean: 1.4139 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.1719312457704181,
            "unit": "iter/sec",
            "range": "stddev: 0.077416",
            "group": "engine",
            "extra": "mean: 5.8163 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.19770667147997378,
            "unit": "iter/sec",
            "range": "stddev: 0.061925",
            "group": "engine",
            "extra": "mean: 5.0580 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.1375089327513974,
            "unit": "iter/sec",
            "range": "stddev: 0.045598",
            "group": "engine",
            "extra": "mean: 467.83 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.4903655721616272,
            "unit": "iter/sec",
            "range": "stddev: 0.085813",
            "group": "engine",
            "extra": "mean: 2.0393 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.5704162698742467,
            "unit": "iter/sec",
            "range": "stddev: 0.055253",
            "group": "engine",
            "extra": "mean: 1.7531 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.15206026788370977,
            "unit": "iter/sec",
            "range": "stddev: 0.10168",
            "group": "engine",
            "extra": "mean: 6.5763 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.17911326281379134,
            "unit": "iter/sec",
            "range": "stddev: 0.093926",
            "group": "engine",
            "extra": "mean: 5.5831 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.3936133894775944,
            "unit": "iter/sec",
            "range": "stddev: 0.045601",
            "group": "import-export",
            "extra": "mean: 417.78 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.130493958699479,
            "unit": "iter/sec",
            "range": "stddev: 0.047270",
            "group": "import-export",
            "extra": "mean: 469.37 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 0.14841625590477708,
            "unit": "iter/sec",
            "range": "stddev: 0.056448",
            "group": "import-export",
            "extra": "mean: 6.7378 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 0.14489083500890046,
            "unit": "iter/sec",
            "range": "stddev: 0.082600",
            "group": "import-export",
            "extra": "mean: 6.9017 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 271.31380070790163,
            "unit": "iter/sec",
            "range": "stddev: 0.00013578",
            "group": "node",
            "extra": "mean: 3.6858 msec\nrounds: 133"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 112.29954185051832,
            "unit": "iter/sec",
            "range": "stddev: 0.00028759",
            "group": "node",
            "extra": "mean: 8.9048 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 109.21575338033597,
            "unit": "iter/sec",
            "range": "stddev: 0.00019557",
            "group": "node",
            "extra": "mean: 9.1562 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 160.0278348575127,
            "unit": "iter/sec",
            "range": "stddev: 0.00045897",
            "group": "node",
            "extra": "mean: 6.2489 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 42.515748466720176,
            "unit": "iter/sec",
            "range": "stddev: 0.0049473",
            "group": "node",
            "extra": "mean: 23.521 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 40.97499596424108,
            "unit": "iter/sec",
            "range": "stddev: 0.014653",
            "group": "node",
            "extra": "mean: 24.405 msec\nrounds: 100"
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
          "pythonVersion": "3.8.7",
          "metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "13358ed975614c0b033a37293382ed80326fe0fa",
          "message": "Bump aiida-prerequisites base image to 0.3.0 (#4738)\n\nChanges in the new image:\r\n- Updated conda (4.9.2)\r\n- Start ssh-agent at user's startup\r\n\r\nCo-authored-by: Chris Sewell <chrisj_sewell@hotmail.com>",
          "timestamp": "2021-02-10T16:53:52+01:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/13358ed975614c0b033a37293382ed80326fe0fa",
          "distinct": true,
          "tree_id": "5d67fac7cb734fd34d6bc140c64a0b1dcc9d5311"
        },
        "date": 1612973316487,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 2.3533943034397007,
            "unit": "iter/sec",
            "range": "stddev: 0.017208",
            "group": "engine",
            "extra": "mean: 424.92 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.5306974383512532,
            "unit": "iter/sec",
            "range": "stddev: 0.055961",
            "group": "engine",
            "extra": "mean: 1.8843 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.5957671637855309,
            "unit": "iter/sec",
            "range": "stddev: 0.059017",
            "group": "engine",
            "extra": "mean: 1.6785 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.15546437924033701,
            "unit": "iter/sec",
            "range": "stddev: 0.24013",
            "group": "engine",
            "extra": "mean: 6.4323 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.1755828200594443,
            "unit": "iter/sec",
            "range": "stddev: 0.19283",
            "group": "engine",
            "extra": "mean: 5.6953 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 1.7964161194105361,
            "unit": "iter/sec",
            "range": "stddev: 0.012131",
            "group": "engine",
            "extra": "mean: 556.66 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.41648431237707495,
            "unit": "iter/sec",
            "range": "stddev: 0.047283",
            "group": "engine",
            "extra": "mean: 2.4011 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.48167138603779375,
            "unit": "iter/sec",
            "range": "stddev: 0.079468",
            "group": "engine",
            "extra": "mean: 2.0761 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.13416583865186285,
            "unit": "iter/sec",
            "range": "stddev: 0.13271",
            "group": "engine",
            "extra": "mean: 7.4535 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.158731581426206,
            "unit": "iter/sec",
            "range": "stddev: 0.20641",
            "group": "engine",
            "extra": "mean: 6.2999 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 1.9158583223084193,
            "unit": "iter/sec",
            "range": "stddev: 0.045834",
            "group": "import-export",
            "extra": "mean: 521.96 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 1.8106515818944757,
            "unit": "iter/sec",
            "range": "stddev: 0.051054",
            "group": "import-export",
            "extra": "mean: 552.29 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 0.12319699709837743,
            "unit": "iter/sec",
            "range": "stddev: 0.29485",
            "group": "import-export",
            "extra": "mean: 8.1171 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 0.12537346685022935,
            "unit": "iter/sec",
            "range": "stddev: 0.14862",
            "group": "import-export",
            "extra": "mean: 7.9762 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 251.80505015207675,
            "unit": "iter/sec",
            "range": "stddev: 0.00069739",
            "group": "node",
            "extra": "mean: 3.9713 msec\nrounds: 136"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 100.55370490877992,
            "unit": "iter/sec",
            "range": "stddev: 0.00049198",
            "group": "node",
            "extra": "mean: 9.9449 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 92.80036857931836,
            "unit": "iter/sec",
            "range": "stddev: 0.00094161",
            "group": "node",
            "extra": "mean: 10.776 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 145.28185150652268,
            "unit": "iter/sec",
            "range": "stddev: 0.00034896",
            "group": "node",
            "extra": "mean: 6.8832 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 38.24580221704515,
            "unit": "iter/sec",
            "range": "stddev: 0.0018293",
            "group": "node",
            "extra": "mean: 26.147 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 38.13681319275182,
            "unit": "iter/sec",
            "range": "stddev: 0.0032698",
            "group": "node",
            "extra": "mean: 26.221 msec\nrounds: 100"
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
          "pythonVersion": "3.8.7",
          "metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "2e18f5bc092a7746c3d5cc151e59c52866354f10",
          "message": "Add CalcJob test over SSH (#4732)\n\nAdds a configuration for a remote computer (slurm docker container) and uses it\r\nto run a CalcJob test over SSH.\r\n\r\nThis is a follow-up on the memory leak tests, since the leak of the process\r\ninstance was discovered to occur only when running CalcJobs on a remote\r\ncomputer via an SSH connection.\r\n\r\nCo-authored-by: Chris Sewell <chrisj_sewell@hotmail.com>",
          "timestamp": "2021-02-10T17:47:50+01:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/2e18f5bc092a7746c3d5cc151e59c52866354f10",
          "distinct": true,
          "tree_id": "aa27b5b1d972f7d6a38b01a8f2b88abdb25281d5"
        },
        "date": 1612976441053,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 2.7463221401515168,
            "unit": "iter/sec",
            "range": "stddev: 0.0056947",
            "group": "engine",
            "extra": "mean: 364.12 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.6194590206354234,
            "unit": "iter/sec",
            "range": "stddev: 0.041996",
            "group": "engine",
            "extra": "mean: 1.6143 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.7209217222700139,
            "unit": "iter/sec",
            "range": "stddev: 0.047824",
            "group": "engine",
            "extra": "mean: 1.3871 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.17505679737353352,
            "unit": "iter/sec",
            "range": "stddev: 0.068111",
            "group": "engine",
            "extra": "mean: 5.7124 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.20089486669689943,
            "unit": "iter/sec",
            "range": "stddev: 0.097747",
            "group": "engine",
            "extra": "mean: 4.9777 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.1636868943054335,
            "unit": "iter/sec",
            "range": "stddev: 0.039955",
            "group": "engine",
            "extra": "mean: 462.17 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.500381055184952,
            "unit": "iter/sec",
            "range": "stddev: 0.063037",
            "group": "engine",
            "extra": "mean: 1.9985 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.5813175788534057,
            "unit": "iter/sec",
            "range": "stddev: 0.058049",
            "group": "engine",
            "extra": "mean: 1.7202 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.1541155902346223,
            "unit": "iter/sec",
            "range": "stddev: 0.087211",
            "group": "engine",
            "extra": "mean: 6.4886 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.18110886710930224,
            "unit": "iter/sec",
            "range": "stddev: 0.074746",
            "group": "engine",
            "extra": "mean: 5.5215 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.352923230586606,
            "unit": "iter/sec",
            "range": "stddev: 0.038419",
            "group": "import-export",
            "extra": "mean: 425.00 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.1036270324456945,
            "unit": "iter/sec",
            "range": "stddev: 0.038230",
            "group": "import-export",
            "extra": "mean: 475.37 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 0.14839345445663363,
            "unit": "iter/sec",
            "range": "stddev: 0.079993",
            "group": "import-export",
            "extra": "mean: 6.7388 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 0.1468587131449824,
            "unit": "iter/sec",
            "range": "stddev: 0.10978",
            "group": "import-export",
            "extra": "mean: 6.8093 sec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 282.8872463821354,
            "unit": "iter/sec",
            "range": "stddev: 0.00011323",
            "group": "node",
            "extra": "mean: 3.5350 msec\nrounds: 147"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 116.58517933888713,
            "unit": "iter/sec",
            "range": "stddev: 0.00028094",
            "group": "node",
            "extra": "mean: 8.5774 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 109.5583922406853,
            "unit": "iter/sec",
            "range": "stddev: 0.00078801",
            "group": "node",
            "extra": "mean: 9.1276 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 170.4323123657509,
            "unit": "iter/sec",
            "range": "stddev: 0.00016271",
            "group": "node",
            "extra": "mean: 5.8674 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 44.86364312769069,
            "unit": "iter/sec",
            "range": "stddev: 0.0012668",
            "group": "node",
            "extra": "mean: 22.290 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 45.05158876801173,
            "unit": "iter/sec",
            "range": "stddev: 0.0013677",
            "group": "node",
            "extra": "mean: 22.197 msec\nrounds: 100"
          }
        ]
      }
    ]
  }
}