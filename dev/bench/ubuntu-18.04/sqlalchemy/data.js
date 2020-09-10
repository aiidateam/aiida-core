window.BENCHMARK_DATA = {
  "lastUpdate": 1599756085509,
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
      }
    ]
  }
}