window.BENCHMARK_DATA = {
  "lastUpdate": 1599730640065,
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
      }
    ]
  }
}