window.BENCHMARK_DATA = {
  "lastUpdate": 1599775941985,
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
      }
    ]
  }
}