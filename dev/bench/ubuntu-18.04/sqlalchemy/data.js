window.BENCHMARK_DATA = {
  "lastUpdate": 1599732296395,
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
      }
    ]
  }
}