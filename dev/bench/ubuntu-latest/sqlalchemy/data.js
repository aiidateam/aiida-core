window.BENCHMARK_DATA = {
  "lastUpdate": 1599657780358,
  "repoUrl": "https://github.com/aiidateam/aiida-core",
  "xAxis": "id",
  "oneChartGroups": [
    "node"
  ],
  "entries": {
    "Pytest Benchmarks": [
      {
        "cpu": {
          "speed": "2.30",
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
        "date": 1599657320821,
        "benches": [
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 277.30963279475134,
            "unit": "iter/sec",
            "range": "stddev: 0.00050196",
            "group": "node",
            "extra": "mean: 3.6061 msec\nrounds: 147"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 105.5632464244925,
            "unit": "iter/sec",
            "range": "stddev: 0.0012114",
            "group": "node",
            "extra": "mean: 9.4730 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 158.86399609927585,
            "unit": "iter/sec",
            "range": "stddev: 0.00068651",
            "group": "node",
            "extra": "mean: 6.2947 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 43.49906410785322,
            "unit": "iter/sec",
            "range": "stddev: 0.0022235",
            "group": "node",
            "extra": "mean: 22.989 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_calcfunction",
            "value": 6.36982615105199,
            "unit": "iter/sec",
            "range": "stddev: 0.018977",
            "group": "engine",
            "extra": "mean: 156.99 msec\nrounds: 50"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_workchain",
            "value": 2.971760755103968,
            "unit": "iter/sec",
            "range": "stddev: 0.023493",
            "group": "engine",
            "extra": "mean: 336.50 msec\nrounds: 50"
          }
        ]
      }
    ],
    "Pytest Benchmarks (ubuntu-latest, sqlalchemy)": [
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
        "date": 1599657779728,
        "benches": [
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 290.69009870098324,
            "unit": "iter/sec",
            "range": "stddev: 0.00061487",
            "group": "node",
            "extra": "mean: 3.4401 msec\nrounds: 143"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 116.39698776608058,
            "unit": "iter/sec",
            "range": "stddev: 0.00051693",
            "group": "node",
            "extra": "mean: 8.5913 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 173.21453222951612,
            "unit": "iter/sec",
            "range": "stddev: 0.00080764",
            "group": "node",
            "extra": "mean: 5.7732 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 45.532660832143215,
            "unit": "iter/sec",
            "range": "stddev: 0.0012603",
            "group": "node",
            "extra": "mean: 21.962 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_calcfunction",
            "value": 6.635717555237569,
            "unit": "iter/sec",
            "range": "stddev: 0.018398",
            "group": "engine",
            "extra": "mean: 150.70 msec\nrounds: 50"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_workchain",
            "value": 2.9627356908497093,
            "unit": "iter/sec",
            "range": "stddev: 0.025437",
            "group": "engine",
            "extra": "mean: 337.53 msec\nrounds: 50"
          }
        ]
      }
    ]
  }
}