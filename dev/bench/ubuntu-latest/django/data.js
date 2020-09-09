window.BENCHMARK_DATA = {
  "lastUpdate": 1599657298313,
  "repoUrl": "https://github.com/aiidateam/aiida-core",
  "xAxis": "id",
  "oneChartGroups": [
    ""
  ],
  "entries": {
    "Pytest Benchmarks": [
      {
        "cpu": {
          "speed": "2.60",
          "cores": 2,
          "physicalCores": 2,
          "processors": 1
        },
        "extra": {
          "pythonVersion": "3.8.5"
        },
        "commit": {
          "id": "21d419fb35c0bc99c544126e5d26f1360a2cafc2",
          "message": "Pytest Benchmark",
          "timestamp": "2020-09-08T05:32:02Z",
          "url": "https://github.com/aiidateam/aiida-core/pull/4362/commits/21d419fb35c0bc99c544126e5d26f1360a2cafc2"
        },
        "date": 1599657297751,
        "benches": [
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 1169.1812565165624,
            "unit": "iter/sec",
            "range": "stddev: 0.000042364",
            "group": "node",
            "extra": "mean: 855.30 usec\nrounds: 215"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 229.25277040508436,
            "unit": "iter/sec",
            "range": "stddev: 0.00037059",
            "group": "node",
            "extra": "mean: 4.3620 msec\nrounds: 131"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 238.31281485811587,
            "unit": "iter/sec",
            "range": "stddev: 0.00047366",
            "group": "node",
            "extra": "mean: 4.1962 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 44.16946658608508,
            "unit": "iter/sec",
            "range": "stddev: 0.0041956",
            "group": "node",
            "extra": "mean: 22.640 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_calcfunction",
            "value": 7.705466336137128,
            "unit": "iter/sec",
            "range": "stddev: 0.023063",
            "group": "engine",
            "extra": "mean: 129.78 msec\nrounds: 50"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_workchain",
            "value": 3.8084107026224063,
            "unit": "iter/sec",
            "range": "stddev: 0.033257",
            "group": "engine",
            "extra": "mean: 262.58 msec\nrounds: 50"
          }
        ]
      }
    ]
  }
}