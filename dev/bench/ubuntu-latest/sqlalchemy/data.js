window.BENCHMARK_DATA = {
  "lastUpdate": 1599665026987,
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
          "id": "ef2b61d687a40047f36462c1cc7a7f1f99f63369",
          "message": "Pytest Benchmark",
          "timestamp": "2020-09-08T05:32:02Z",
          "url": "https://github.com/aiidateam/aiida-core/pull/4362/commits/ef2b61d687a40047f36462c1cc7a7f1f99f63369"
        },
        "date": 1599659819567,
        "benches": [
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 252.85638435865295,
            "unit": "iter/sec",
            "range": "stddev: 0.0012069",
            "group": "Node Manipulation",
            "extra": "mean: 3.9548 msec\nrounds: 138"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 100.80734688781786,
            "unit": "iter/sec",
            "range": "stddev: 0.00074417",
            "group": "Node Manipulation",
            "extra": "mean: 9.9199 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 143.960266160331,
            "unit": "iter/sec",
            "range": "stddev: 0.00088786",
            "group": "Node Manipulation",
            "extra": "mean: 6.9464 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 39.17588618587511,
            "unit": "iter/sec",
            "range": "stddev: 0.0025299",
            "group": "Node Manipulation",
            "extra": "mean: 25.526 msec\nrounds: 100"
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
          "gh-metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "8c5ac9c469ec447733fdc87d29b2021efe5f233f",
          "message": "Pytest Benchmark",
          "timestamp": "2020-09-09T14:11:43Z",
          "url": "https://github.com/aiidateam/aiida-core/pull/4362/commits/8c5ac9c469ec447733fdc87d29b2021efe5f233f"
        },
        "date": 1599662057955,
        "benches": [
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 279.53893197465845,
            "unit": "iter/sec",
            "range": "stddev: 0.00060954",
            "group": "Node Manipulation",
            "extra": "mean: 3.5773 msec\nrounds: 141"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 115.94465572009577,
            "unit": "iter/sec",
            "range": "stddev: 0.00021024",
            "group": "Node Manipulation",
            "extra": "mean: 8.6248 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 167.91031371489777,
            "unit": "iter/sec",
            "range": "stddev: 0.00089288",
            "group": "Node Manipulation",
            "extra": "mean: 5.9556 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 43.24957110903272,
            "unit": "iter/sec",
            "range": "stddev: 0.0017942",
            "group": "Node Manipulation",
            "extra": "mean: 23.122 msec\nrounds: 100"
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
          "gh-metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "ecf7da85874a49a4d3c136c04cf29b7007232963",
          "message": "Pytest Benchmark",
          "timestamp": "2020-09-09T14:11:43Z",
          "url": "https://github.com/aiidateam/aiida-core/pull/4362/commits/ecf7da85874a49a4d3c136c04cf29b7007232963"
        },
        "date": 1599662782177,
        "benches": [
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 275.0269019529207,
            "unit": "iter/sec",
            "range": "stddev: 0.00042257",
            "group": "Node Manipulation",
            "extra": "mean: 3.6360 msec\nrounds: 140"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 109.68912132996901,
            "unit": "iter/sec",
            "range": "stddev: 0.00068077",
            "group": "Node Manipulation",
            "extra": "mean: 9.1167 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 164.3118702590499,
            "unit": "iter/sec",
            "range": "stddev: 0.0011872",
            "group": "Node Manipulation",
            "extra": "mean: 6.0860 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 41.997440608774504,
            "unit": "iter/sec",
            "range": "stddev: 0.0047195",
            "group": "Node Manipulation",
            "extra": "mean: 23.811 msec\nrounds: 100"
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
          "gh-metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "1572d7806548c3aa2aeeabc6bdbbf54ea6fa82da",
          "message": "Pytest Benchmark",
          "timestamp": "2020-09-09T14:11:43Z",
          "url": "https://github.com/aiidateam/aiida-core/pull/4362/commits/1572d7806548c3aa2aeeabc6bdbbf54ea6fa82da"
        },
        "date": 1599663928667,
        "benches": [
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 271.89959677711937,
            "unit": "iter/sec",
            "range": "stddev: 0.00025999",
            "group": "Node Manipulation",
            "extra": "mean: 3.6778 msec\nrounds: 142"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 109.3597720789329,
            "unit": "iter/sec",
            "range": "stddev: 0.00057484",
            "group": "Node Manipulation",
            "extra": "mean: 9.1441 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 161.37672107430546,
            "unit": "iter/sec",
            "range": "stddev: 0.00056699",
            "group": "Node Manipulation",
            "extra": "mean: 6.1967 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 40.17519409011924,
            "unit": "iter/sec",
            "range": "stddev: 0.0018783",
            "group": "Node Manipulation",
            "extra": "mean: 24.891 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_calcfunction",
            "value": 5.861962450991259,
            "unit": "iter/sec",
            "range": "stddev: 0.020436",
            "group": "Computations",
            "extra": "mean: 170.59 msec\nrounds: 50"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_workchain",
            "value": 2.6360788835854527,
            "unit": "iter/sec",
            "range": "stddev: 0.034067",
            "group": "Computations",
            "extra": "mean: 379.35 msec\nrounds: 50"
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
          "gh-metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "97558ec3114ddb678011452e6dcce6c5976df600",
          "message": "Pytest Benchmark",
          "timestamp": "2020-09-09T14:11:43Z",
          "url": "https://github.com/aiidateam/aiida-core/pull/4362/commits/97558ec3114ddb678011452e6dcce6c5976df600"
        },
        "date": 1599664303575,
        "benches": [
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 249.94331702138393,
            "unit": "iter/sec",
            "range": "stddev: 0.00064230",
            "group": "Node Manipulation",
            "extra": "mean: 4.0009 msec\nrounds: 120"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 95.20973914817678,
            "unit": "iter/sec",
            "range": "stddev: 0.0016125",
            "group": "Node Manipulation",
            "extra": "mean: 10.503 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 150.423787733799,
            "unit": "iter/sec",
            "range": "stddev: 0.00055966",
            "group": "Node Manipulation",
            "extra": "mean: 6.6479 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 39.12679989779814,
            "unit": "iter/sec",
            "range": "stddev: 0.0033777",
            "group": "Node Manipulation",
            "extra": "mean: 25.558 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_calcfunction",
            "value": 5.490948023323996,
            "unit": "iter/sec",
            "range": "stddev: 0.028584",
            "group": "Computations",
            "extra": "mean: 182.12 msec\nrounds: 50"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_workchain",
            "value": 2.4952542506212763,
            "unit": "iter/sec",
            "range": "stddev: 0.033677",
            "group": "Computations",
            "extra": "mean: 400.76 msec\nrounds: 51"
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
          "gh-metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "b0750653ae327c1f7291c55c1a38f2dd035cbaa7",
          "message": "Pytest Benchmark",
          "timestamp": "2020-09-09T15:10:57Z",
          "url": "https://github.com/aiidateam/aiida-core/pull/4362/commits/b0750653ae327c1f7291c55c1a38f2dd035cbaa7"
        },
        "date": 1599664575175,
        "benches": [
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 283.53557544627023,
            "unit": "iter/sec",
            "range": "stddev: 0.00020490",
            "group": "Node Manipulation",
            "extra": "mean: 3.5269 msec\nrounds: 145"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 113.60063404240984,
            "unit": "iter/sec",
            "range": "stddev: 0.00044948",
            "group": "Node Manipulation",
            "extra": "mean: 8.8028 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 172.34410962557357,
            "unit": "iter/sec",
            "range": "stddev: 0.00019128",
            "group": "Node Manipulation",
            "extra": "mean: 5.8023 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 43.79075389795758,
            "unit": "iter/sec",
            "range": "stddev: 0.0014769",
            "group": "Node Manipulation",
            "extra": "mean: 22.836 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_calcfunction",
            "value": 6.207044698042412,
            "unit": "iter/sec",
            "range": "stddev: 0.026362",
            "group": "Computations",
            "extra": "mean: 161.11 msec\nrounds: 50"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_workchain",
            "value": 2.850818260629759,
            "unit": "iter/sec",
            "range": "stddev: 0.031827",
            "group": "Computations",
            "extra": "mean: 350.78 msec\nrounds: 50"
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
          "gh-metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "957ae068c74712befb810d3cad1d815acbf8b9b5",
          "message": "Pytest Benchmark",
          "timestamp": "2020-09-09T15:10:57Z",
          "url": "https://github.com/aiidateam/aiida-core/pull/4362/commits/957ae068c74712befb810d3cad1d815acbf8b9b5"
        },
        "date": 1599665024382,
        "benches": [
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 271.1073100457292,
            "unit": "iter/sec",
            "range": "stddev: 0.00043483",
            "group": "Node Manipulation",
            "extra": "mean: 3.6886 msec\nrounds: 154"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 104.81741917169553,
            "unit": "iter/sec",
            "range": "stddev: 0.0010802",
            "group": "Node Manipulation",
            "extra": "mean: 9.5404 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 169.4734874125115,
            "unit": "iter/sec",
            "range": "stddev: 0.00059144",
            "group": "Node Manipulation",
            "extra": "mean: 5.9006 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 42.04252726330431,
            "unit": "iter/sec",
            "range": "stddev: 0.0017684",
            "group": "Node Manipulation",
            "extra": "mean: 23.785 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_calcfunction",
            "value": 6.297441960057521,
            "unit": "iter/sec",
            "range": "stddev: 0.015956",
            "group": "Computations",
            "extra": "mean: 158.79 msec\nrounds: 50"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_workchain",
            "value": 2.851330088699317,
            "unit": "iter/sec",
            "range": "stddev: 0.028438",
            "group": "Computations",
            "extra": "mean: 350.71 msec\nrounds: 50"
          }
        ]
      }
    ]
  }
}