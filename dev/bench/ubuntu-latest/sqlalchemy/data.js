window.BENCHMARK_DATA = {
  "lastUpdate": 1599659397154,
  "repoUrl": "https://github.com/aiidateam/aiida-core",
  "xAxis": "id",
  "oneChartGroups": [
    "Node Manipulation"
  ],
  "entries": {
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
          "id": "92a4be5538ade572e34d7d9622e237b5ae52f8e4",
          "message": "Pytest Benchmark",
          "timestamp": "2020-09-08T05:32:02Z",
          "url": "https://github.com/aiidateam/aiida-core/pull/4362/commits/92a4be5538ade572e34d7d9622e237b5ae52f8e4"
        },
        "date": 1599658460615,
        "benches": [
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 278.6168501738215,
            "unit": "iter/sec",
            "range": "stddev: 0.00027110",
            "group": "Node Manipulation",
            "extra": "mean: 3.5892 msec\nrounds: 143"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 112.02227502892454,
            "unit": "iter/sec",
            "range": "stddev: 0.00056709",
            "group": "Node Manipulation",
            "extra": "mean: 8.9268 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 172.04236609331005,
            "unit": "iter/sec",
            "range": "stddev: 0.00020830",
            "group": "Node Manipulation",
            "extra": "mean: 5.8125 msec\nrounds: 100"
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
          "pythonVersion": "3.8.5"
        },
        "commit": {
          "id": "45b1114af9d1d9a2e3eef05c8ce3c89dd3313d85",
          "message": "Pytest Benchmark",
          "timestamp": "2020-09-08T05:32:02Z",
          "url": "https://github.com/aiidateam/aiida-core/pull/4362/commits/45b1114af9d1d9a2e3eef05c8ce3c89dd3313d85"
        },
        "date": 1599658803468,
        "benches": [
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 280.64130036895574,
            "unit": "iter/sec",
            "range": "stddev: 0.00031523",
            "group": "Node Manipulation",
            "extra": "mean: 3.5633 msec\nrounds: 153"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 113.19683345260059,
            "unit": "iter/sec",
            "range": "stddev: 0.00023226",
            "group": "Node Manipulation",
            "extra": "mean: 8.8342 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 164.89101550590803,
            "unit": "iter/sec",
            "range": "stddev: 0.00067391",
            "group": "Node Manipulation",
            "extra": "mean: 6.0646 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 43.04783120159674,
            "unit": "iter/sec",
            "range": "stddev: 0.0011965",
            "group": "Node Manipulation",
            "extra": "mean: 23.230 msec\nrounds: 100"
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
          "pythonVersion": "3.8.5"
        },
        "commit": {
          "id": "0b414aaffcca5feaf2cfc04e11361e6108d8aba4",
          "message": "Pytest Benchmark",
          "timestamp": "2020-09-08T05:32:02Z",
          "url": "https://github.com/aiidateam/aiida-core/pull/4362/commits/0b414aaffcca5feaf2cfc04e11361e6108d8aba4"
        },
        "date": 1599659396656,
        "benches": [
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 275.90188261337113,
            "unit": "iter/sec",
            "range": "stddev: 0.00044122",
            "group": "Node Manipulation",
            "extra": "mean: 3.6245 msec\nrounds: 139"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 109.51965484354514,
            "unit": "iter/sec",
            "range": "stddev: 0.00089424",
            "group": "Node Manipulation",
            "extra": "mean: 9.1308 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 165.2328238632959,
            "unit": "iter/sec",
            "range": "stddev: 0.00054169",
            "group": "Node Manipulation",
            "extra": "mean: 6.0521 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 42.6333862677085,
            "unit": "iter/sec",
            "range": "stddev: 0.0015744",
            "group": "Node Manipulation",
            "extra": "mean: 23.456 msec\nrounds: 100"
          }
        ]
      }
    ]
  }
}