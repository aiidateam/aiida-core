window.BENCHMARK_DATA = {
  "lastUpdate": 1599658807583,
  "repoUrl": "https://github.com/aiidateam/aiida-core",
  "xAxis": "id",
  "oneChartGroups": [
    "Node Manipulation"
  ],
  "entries": {
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
          "id": "92a4be5538ade572e34d7d9622e237b5ae52f8e4",
          "message": "Pytest Benchmark",
          "timestamp": "2020-09-08T05:32:02Z",
          "url": "https://github.com/aiidateam/aiida-core/pull/4362/commits/92a4be5538ade572e34d7d9622e237b5ae52f8e4"
        },
        "date": 1599658488755,
        "benches": [
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 791.0466328581188,
            "unit": "iter/sec",
            "range": "stddev: 0.00079685",
            "group": "Node Manipulation",
            "extra": "mean: 1.2641 msec\nrounds: 126"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 169.66712572252993,
            "unit": "iter/sec",
            "range": "stddev: 0.0013330",
            "group": "Node Manipulation",
            "extra": "mean: 5.8939 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 183.18574836120615,
            "unit": "iter/sec",
            "range": "stddev: 0.0013803",
            "group": "Node Manipulation",
            "extra": "mean: 5.4589 msec\nrounds: 100"
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
          "pythonVersion": "3.8.5"
        },
        "commit": {
          "id": "45b1114af9d1d9a2e3eef05c8ce3c89dd3313d85",
          "message": "Pytest Benchmark",
          "timestamp": "2020-09-08T05:32:02Z",
          "url": "https://github.com/aiidateam/aiida-core/pull/4362/commits/45b1114af9d1d9a2e3eef05c8ce3c89dd3313d85"
        },
        "date": 1599658803865,
        "benches": [
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 1398.0350909389886,
            "unit": "iter/sec",
            "range": "stddev: 0.000087799",
            "group": "Node Manipulation",
            "extra": "mean: 715.29 usec\nrounds: 215"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 293.8502929177761,
            "unit": "iter/sec",
            "range": "stddev: 0.00028604",
            "group": "Node Manipulation",
            "extra": "mean: 3.4031 msec\nrounds: 155"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 312.0641224866216,
            "unit": "iter/sec",
            "range": "stddev: 0.00028478",
            "group": "Node Manipulation",
            "extra": "mean: 3.2045 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 62.757650790073946,
            "unit": "iter/sec",
            "range": "stddev: 0.0010569",
            "group": "Node Manipulation",
            "extra": "mean: 15.934 msec\nrounds: 100"
          }
        ]
      }
    ]
  }
}