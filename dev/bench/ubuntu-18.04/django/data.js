window.BENCHMARK_DATA = {
  "lastUpdate": 1599731463628,
  "repoUrl": "https://github.com/aiidateam/aiida-core",
  "xAxis": "id",
  "oneChartGroups": [],
  "entries": {
    "pytest-benchmarks:ubuntu-18.04,django": [
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
          "id": "8328e07c352e3c84cb7f4a67fe1c4537eb983ce4",
          "message": "Pytest Benchmark",
          "timestamp": "2020-09-09T21:08:28Z",
          "url": "https://github.com/aiidateam/aiida-core/pull/4362/commits/8328e07c352e3c84cb7f4a67fe1c4537eb983ce4"
        },
        "date": 1599730645026,
        "benches": [
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 892.6901124367348,
            "unit": "iter/sec",
            "range": "stddev: 0.00015383",
            "group": "node",
            "extra": "mean: 1.1202 msec\nrounds: 185"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 197.76403318878084,
            "unit": "iter/sec",
            "range": "stddev: 0.00053444",
            "group": "node",
            "extra": "mean: 5.0565 msec\nrounds: 117"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 109.341512234734,
            "unit": "iter/sec",
            "range": "stddev: 0.033367",
            "group": "node",
            "extra": "mean: 9.1457 msec\nrounds: 125"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 194.5271736632814,
            "unit": "iter/sec",
            "range": "stddev: 0.00053886",
            "group": "node",
            "extra": "mean: 5.1407 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 41.38858822769686,
            "unit": "iter/sec",
            "range": "stddev: 0.0020537",
            "group": "node",
            "extra": "mean: 24.161 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 35.70606477543619,
            "unit": "iter/sec",
            "range": "stddev: 0.017846",
            "group": "node",
            "extra": "mean: 28.006 msec\nrounds: 100"
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
          "id": "ff194543ea0e2ccfe3eafcd61d563387a92847fb",
          "message": "Pytest Benchmark",
          "timestamp": "2020-09-09T21:08:28Z",
          "url": "https://github.com/aiidateam/aiida-core/pull/4362/commits/ff194543ea0e2ccfe3eafcd61d563387a92847fb"
        },
        "date": 1599731463042,
        "benches": [
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 922.4784596837195,
            "unit": "iter/sec",
            "range": "stddev: 0.00012706",
            "group": "node",
            "extra": "mean: 1.0840 msec\nrounds: 197"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 156.7542814554267,
            "unit": "iter/sec",
            "range": "stddev: 0.015587",
            "group": "node",
            "extra": "mean: 6.3794 msec\nrounds: 137"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 192.27263176302935,
            "unit": "iter/sec",
            "range": "stddev: 0.00056928",
            "group": "node",
            "extra": "mean: 5.2009 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 199.30848605330493,
            "unit": "iter/sec",
            "range": "stddev: 0.00043136",
            "group": "node",
            "extra": "mean: 5.0173 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 43.42347190803886,
            "unit": "iter/sec",
            "range": "stddev: 0.0033667",
            "group": "node",
            "extra": "mean: 23.029 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 42.6518106065508,
            "unit": "iter/sec",
            "range": "stddev: 0.014287",
            "group": "node",
            "extra": "mean: 23.446 msec\nrounds: 100"
          }
        ]
      }
    ]
  }
}