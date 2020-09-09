window.BENCHMARK_DATA = {
  "lastUpdate": 1599657777169,
  "repoUrl": "https://github.com/aiidateam/aiida-core",
  "xAxis": "id",
  "oneChartGroups": [
    "node"
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
    ],
    "Pytest Benchmarks (ubuntu-latest, django)": [
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
          "id": "ce1cb761c21615168a9086e0159c7f32bc9776db",
          "message": "Pytest Benchmark",
          "timestamp": "2020-09-08T05:32:02Z",
          "url": "https://github.com/aiidateam/aiida-core/pull/4362/commits/ce1cb761c21615168a9086e0159c7f32bc9776db"
        },
        "date": 1599657776661,
        "benches": [
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 1049.2889719555128,
            "unit": "iter/sec",
            "range": "stddev: 0.00019245",
            "group": "node",
            "extra": "mean: 953.03 usec\nrounds: 211"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 207.61873692407238,
            "unit": "iter/sec",
            "range": "stddev: 0.0013739",
            "group": "node",
            "extra": "mean: 4.8165 msec\nrounds: 130"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 224.96949014383756,
            "unit": "iter/sec",
            "range": "stddev: 0.00055193",
            "group": "node",
            "extra": "mean: 4.4450 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 43.30106273569051,
            "unit": "iter/sec",
            "range": "stddev: 0.0032062",
            "group": "node",
            "extra": "mean: 23.094 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_calcfunction",
            "value": 7.865679447022188,
            "unit": "iter/sec",
            "range": "stddev: 0.023949",
            "group": "engine",
            "extra": "mean: 127.13 msec\nrounds: 50"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_workchain",
            "value": 3.7864204669679724,
            "unit": "iter/sec",
            "range": "stddev: 0.033381",
            "group": "engine",
            "extra": "mean: 264.10 msec\nrounds: 50"
          }
        ]
      }
    ]
  }
}