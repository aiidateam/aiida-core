window.BENCHMARK_DATA = {
  "lastUpdate": 1599766799928,
  "repoUrl": "https://github.com/aiidateam/aiida-core",
  "xAxis": "id",
  "oneChartGroups": [],
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
          "id": "8328e07c352e3c84cb7f4a67fe1c4537eb983ce4",
          "message": "Pytest Benchmark",
          "timestamp": "2020-09-09T21:08:28Z",
          "url": "https://github.com/aiidateam/aiida-core/pull/4362/commits/8328e07c352e3c84cb7f4a67fe1c4537eb983ce4"
        },
        "date": 1599730639528,
        "benches": [
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 235.55095830643927,
            "unit": "iter/sec",
            "range": "stddev: 0.0011938",
            "group": "node",
            "extra": "mean: 4.2454 msec\nrounds: 135"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 96.39035360348915,
            "unit": "iter/sec",
            "range": "stddev: 0.00091497",
            "group": "node",
            "extra": "mean: 10.374 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 90.1248345941222,
            "unit": "iter/sec",
            "range": "stddev: 0.0022968",
            "group": "node",
            "extra": "mean: 11.096 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 145.35291892208164,
            "unit": "iter/sec",
            "range": "stddev: 0.0012039",
            "group": "node",
            "extra": "mean: 6.8798 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 38.85993137475699,
            "unit": "iter/sec",
            "range": "stddev: 0.0023754",
            "group": "node",
            "extra": "mean: 25.733 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 36.280067826372665,
            "unit": "iter/sec",
            "range": "stddev: 0.010904",
            "group": "node",
            "extra": "mean: 27.563 msec\nrounds: 100"
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
          "id": "ff194543ea0e2ccfe3eafcd61d563387a92847fb",
          "message": "Pytest Benchmark",
          "timestamp": "2020-09-09T21:08:28Z",
          "url": "https://github.com/aiidateam/aiida-core/pull/4362/commits/ff194543ea0e2ccfe3eafcd61d563387a92847fb"
        },
        "date": 1599731432975,
        "benches": [
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 348.661638358086,
            "unit": "iter/sec",
            "range": "stddev: 0.00044470",
            "group": "node",
            "extra": "mean: 2.8681 msec\nrounds: 158"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 143.44294025043433,
            "unit": "iter/sec",
            "range": "stddev: 0.00041967",
            "group": "node",
            "extra": "mean: 6.9714 msec\nrounds: 113"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 132.9248390090668,
            "unit": "iter/sec",
            "range": "stddev: 0.0019691",
            "group": "node",
            "extra": "mean: 7.5230 msec\nrounds: 124"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 217.155667788582,
            "unit": "iter/sec",
            "range": "stddev: 0.00043339",
            "group": "node",
            "extra": "mean: 4.6050 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 56.61198132882495,
            "unit": "iter/sec",
            "range": "stddev: 0.0013672",
            "group": "node",
            "extra": "mean: 17.664 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 53.34976164553003,
            "unit": "iter/sec",
            "range": "stddev: 0.010315",
            "group": "node",
            "extra": "mean: 18.744 msec\nrounds: 100"
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
          "id": "a5a84662acdae669f4d2310e45dec1b183ca1fcd",
          "message": "Pytest Benchmark",
          "timestamp": "2020-09-09T21:08:28Z",
          "url": "https://github.com/aiidateam/aiida-core/pull/4362/commits/a5a84662acdae669f4d2310e45dec1b183ca1fcd"
        },
        "date": 1599732295765,
        "benches": [
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 167.14841126325675,
            "unit": "iter/sec",
            "range": "stddev: 0.0015087",
            "group": "node",
            "extra": "mean: 5.9827 msec\nrounds: 123"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 66.65609309949048,
            "unit": "iter/sec",
            "range": "stddev: 0.0042908",
            "group": "node",
            "extra": "mean: 15.002 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 68.17987187889906,
            "unit": "iter/sec",
            "range": "stddev: 0.0020846",
            "group": "node",
            "extra": "mean: 14.667 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 114.86999981776576,
            "unit": "iter/sec",
            "range": "stddev: 0.0016033",
            "group": "node",
            "extra": "mean: 8.7055 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 29.325820283400144,
            "unit": "iter/sec",
            "range": "stddev: 0.0039416",
            "group": "node",
            "extra": "mean: 34.100 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 28.867148715238404,
            "unit": "iter/sec",
            "range": "stddev: 0.014607",
            "group": "node",
            "extra": "mean: 34.641 msec\nrounds: 100"
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
          "id": "5e6083547fb78d471ea2e54cf0868f2427cbdae3",
          "message": "Pytest Benchmark",
          "timestamp": "2020-09-09T21:08:28Z",
          "url": "https://github.com/aiidateam/aiida-core/pull/4362/commits/5e6083547fb78d471ea2e54cf0868f2427cbdae3"
        },
        "date": 1599733058614,
        "benches": [
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 277.77693158694524,
            "unit": "iter/sec",
            "range": "stddev: 0.00086137",
            "group": "node",
            "extra": "mean: 3.6000 msec\nrounds: 150"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 114.44964594178577,
            "unit": "iter/sec",
            "range": "stddev: 0.00099258",
            "group": "node",
            "extra": "mean: 8.7375 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 96.89972545477679,
            "unit": "iter/sec",
            "range": "stddev: 0.0024121",
            "group": "node",
            "extra": "mean: 10.320 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 153.39705423447504,
            "unit": "iter/sec",
            "range": "stddev: 0.0011925",
            "group": "node",
            "extra": "mean: 6.5190 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 43.00464595446003,
            "unit": "iter/sec",
            "range": "stddev: 0.0021638",
            "group": "node",
            "extra": "mean: 23.253 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 40.33098472794208,
            "unit": "iter/sec",
            "range": "stddev: 0.011252",
            "group": "node",
            "extra": "mean: 24.795 msec\nrounds: 100"
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
          "id": "fd27d6419c1cf01fdf8660f12a5d749cdbc50d41",
          "message": "Pytest Benchmark",
          "timestamp": "2020-09-09T21:08:28Z",
          "url": "https://github.com/aiidateam/aiida-core/pull/4362/commits/fd27d6419c1cf01fdf8660f12a5d749cdbc50d41"
        },
        "date": 1599753931429,
        "benches": [
          {
            "name": "tests/benchmark/test_engine_run.py::test_basic_loop",
            "value": 2.9301326163312877,
            "unit": "iter/sec",
            "range": "stddev: 0.019872",
            "group": "engine-run",
            "extra": "mean: 341.28 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine_run.py::test_wkchain_loop_serial",
            "value": 0.6077832343311941,
            "unit": "iter/sec",
            "range": "stddev: 0.076755",
            "group": "engine-run",
            "extra": "mean: 1.6453 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine_run.py::test_wkchain_loop_threaded",
            "value": 0.6690166412295143,
            "unit": "iter/sec",
            "range": "stddev: 0.051174",
            "group": "engine-run",
            "extra": "mean: 1.4947 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine_run.py::test_calc_loop_serial",
            "value": 0.14732901111503535,
            "unit": "iter/sec",
            "range": "stddev: 0.20350",
            "group": "engine-run",
            "extra": "mean: 6.7875 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine_run.py::test_calc_loop_threaded",
            "value": 0.15541737699561708,
            "unit": "iter/sec",
            "range": "stddev: 0.19271",
            "group": "engine-run",
            "extra": "mean: 6.4343 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 126.79146594283405,
            "unit": "iter/sec",
            "range": "stddev: 0.0011076",
            "group": "node",
            "extra": "mean: 7.8870 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 56.80350505118499,
            "unit": "iter/sec",
            "range": "stddev: 0.00098967",
            "group": "node",
            "extra": "mean: 17.605 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 55.37685984347161,
            "unit": "iter/sec",
            "range": "stddev: 0.0012162",
            "group": "node",
            "extra": "mean: 18.058 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 69.59372351299855,
            "unit": "iter/sec",
            "range": "stddev: 0.0011518",
            "group": "node",
            "extra": "mean: 14.369 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 29.63839720320636,
            "unit": "iter/sec",
            "range": "stddev: 0.017506",
            "group": "node",
            "extra": "mean: 33.740 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 30.543200195605444,
            "unit": "iter/sec",
            "range": "stddev: 0.0021627",
            "group": "node",
            "extra": "mean: 32.741 msec\nrounds: 100"
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
          "id": "af1e5bbdc76f227c0f4b17b8a1fddc2053a44889",
          "message": "Pytest Benchmark",
          "timestamp": "2020-09-09T21:08:28Z",
          "url": "https://github.com/aiidateam/aiida-core/pull/4362/commits/af1e5bbdc76f227c0f4b17b8a1fddc2053a44889"
        },
        "date": 1599756084948,
        "benches": [
          {
            "name": "tests/benchmark/test_engine_run.py::test_workchain[basic-loop]",
            "value": 2.931591245008137,
            "unit": "iter/sec",
            "range": "stddev: 0.029857",
            "group": "engine-run",
            "extra": "mean: 341.11 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine_run.py::test_workchain[serial-wc-loop]",
            "value": 0.6603018497286023,
            "unit": "iter/sec",
            "range": "stddev: 0.069931",
            "group": "engine-run",
            "extra": "mean: 1.5145 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine_run.py::test_workchain[threaded-wc-loop]",
            "value": 0.7031491523768526,
            "unit": "iter/sec",
            "range": "stddev: 0.056099",
            "group": "engine-run",
            "extra": "mean: 1.4222 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine_run.py::test_workchain[serial-calcjob-loop]",
            "value": 0.157091961512728,
            "unit": "iter/sec",
            "range": "stddev: 0.18449",
            "group": "engine-run",
            "extra": "mean: 6.3657 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine_run.py::test_workchain[threaded-calcjob-loop]",
            "value": 0.16193316311995862,
            "unit": "iter/sec",
            "range": "stddev: 0.25572",
            "group": "engine-run",
            "extra": "mean: 6.1754 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 123.32427666574101,
            "unit": "iter/sec",
            "range": "stddev: 0.00091594",
            "group": "node",
            "extra": "mean: 8.1087 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 57.02202844210811,
            "unit": "iter/sec",
            "range": "stddev: 0.0017945",
            "group": "node",
            "extra": "mean: 17.537 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 55.28896051200847,
            "unit": "iter/sec",
            "range": "stddev: 0.0019615",
            "group": "node",
            "extra": "mean: 18.087 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 71.50329334049052,
            "unit": "iter/sec",
            "range": "stddev: 0.0019103",
            "group": "node",
            "extra": "mean: 13.985 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 31.754298468553337,
            "unit": "iter/sec",
            "range": "stddev: 0.015215",
            "group": "node",
            "extra": "mean: 31.492 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 32.557863837927165,
            "unit": "iter/sec",
            "range": "stddev: 0.0030607",
            "group": "node",
            "extra": "mean: 30.715 msec\nrounds: 100"
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
          "id": "731c8eab83c252503528ce9a24e6161ac31f3c13",
          "message": "Pytest Benchmark",
          "timestamp": "2020-09-09T21:08:28Z",
          "url": "https://github.com/aiidateam/aiida-core/pull/4362/commits/731c8eab83c252503528ce9a24e6161ac31f3c13"
        },
        "date": 1599758493218,
        "benches": [
          {
            "name": "tests/benchmark/test_engine_run.py::test_workchain[basic-loop]",
            "value": 2.0392626331391686,
            "unit": "iter/sec",
            "range": "stddev: 0.047315",
            "group": "engine-run",
            "extra": "mean: 490.37 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine_run.py::test_workchain[serial-wc-loop]",
            "value": 0.45425920158161665,
            "unit": "iter/sec",
            "range": "stddev: 0.069730",
            "group": "engine-run",
            "extra": "mean: 2.2014 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine_run.py::test_workchain[threaded-wc-loop]",
            "value": 0.4895238507456362,
            "unit": "iter/sec",
            "range": "stddev: 0.074533",
            "group": "engine-run",
            "extra": "mean: 2.0428 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine_run.py::test_workchain[serial-calcjob-loop]",
            "value": 0.11514248307270203,
            "unit": "iter/sec",
            "range": "stddev: 0.31994",
            "group": "engine-run",
            "extra": "mean: 8.6849 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine_run.py::test_workchain[threaded-calcjob-loop]",
            "value": 0.11901495940309838,
            "unit": "iter/sec",
            "range": "stddev: 0.18976",
            "group": "engine-run",
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
      }
    ]
  }
}