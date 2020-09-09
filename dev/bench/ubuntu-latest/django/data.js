window.BENCHMARK_DATA = {
  "lastUpdate": 1599663891064,
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
        "date": 1599659410824,
        "benches": [
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 975.1286509041493,
            "unit": "iter/sec",
            "range": "stddev: 0.00025352",
            "group": "Node Manipulation",
            "extra": "mean: 1.0255 msec\nrounds: 190"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 182.8526361105402,
            "unit": "iter/sec",
            "range": "stddev: 0.0018678",
            "group": "Node Manipulation",
            "extra": "mean: 5.4689 msec\nrounds: 113"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 209.01848591477287,
            "unit": "iter/sec",
            "range": "stddev: 0.00045438",
            "group": "Node Manipulation",
            "extra": "mean: 4.7843 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 39.194463471618405,
            "unit": "iter/sec",
            "range": "stddev: 0.0023900",
            "group": "Node Manipulation",
            "extra": "mean: 25.514 msec\nrounds: 100"
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
          "pythonVersion": "3.8.5"
        },
        "commit": {
          "id": "ef2b61d687a40047f36462c1cc7a7f1f99f63369",
          "message": "Pytest Benchmark",
          "timestamp": "2020-09-08T05:32:02Z",
          "url": "https://github.com/aiidateam/aiida-core/pull/4362/commits/ef2b61d687a40047f36462c1cc7a7f1f99f63369"
        },
        "date": 1599659819590,
        "benches": [
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 840.928803995565,
            "unit": "iter/sec",
            "range": "stddev: 0.000097722",
            "group": "Node Manipulation",
            "extra": "mean: 1.1892 msec\nrounds: 189"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 185.6188510187037,
            "unit": "iter/sec",
            "range": "stddev: 0.00033612",
            "group": "Node Manipulation",
            "extra": "mean: 5.3874 msec\nrounds: 119"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 185.59671117875624,
            "unit": "iter/sec",
            "range": "stddev: 0.00061245",
            "group": "Node Manipulation",
            "extra": "mean: 5.3880 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 39.92931484291115,
            "unit": "iter/sec",
            "range": "stddev: 0.0025803",
            "group": "Node Manipulation",
            "extra": "mean: 25.044 msec\nrounds: 100"
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
          "gh-metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "8c5ac9c469ec447733fdc87d29b2021efe5f233f",
          "message": "Pytest Benchmark",
          "timestamp": "2020-09-09T14:11:43Z",
          "url": "https://github.com/aiidateam/aiida-core/pull/4362/commits/8c5ac9c469ec447733fdc87d29b2021efe5f233f"
        },
        "date": 1599662031441,
        "benches": [
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 1028.1222875480562,
            "unit": "iter/sec",
            "range": "stddev: 0.00053574",
            "group": "Node Manipulation",
            "extra": "mean: 972.65 usec\nrounds: 228"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 210.61563144948025,
            "unit": "iter/sec",
            "range": "stddev: 0.0018761",
            "group": "Node Manipulation",
            "extra": "mean: 4.7480 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 225.90149952324458,
            "unit": "iter/sec",
            "range": "stddev: 0.00047594",
            "group": "Node Manipulation",
            "extra": "mean: 4.4267 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 49.38296479320641,
            "unit": "iter/sec",
            "range": "stddev: 0.0013282",
            "group": "Node Manipulation",
            "extra": "mean: 20.250 msec\nrounds: 100"
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
          "id": "ecf7da85874a49a4d3c136c04cf29b7007232963",
          "message": "Pytest Benchmark",
          "timestamp": "2020-09-09T14:11:43Z",
          "url": "https://github.com/aiidateam/aiida-core/pull/4362/commits/ecf7da85874a49a4d3c136c04cf29b7007232963"
        },
        "date": 1599662768279,
        "benches": [
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 914.5284568426085,
            "unit": "iter/sec",
            "range": "stddev: 0.00014746",
            "group": "Node Manipulation",
            "extra": "mean: 1.0935 msec\nrounds: 182"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 197.4432992555117,
            "unit": "iter/sec",
            "range": "stddev: 0.00038992",
            "group": "Node Manipulation",
            "extra": "mean: 5.0647 msec\nrounds: 127"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 202.78458931221144,
            "unit": "iter/sec",
            "range": "stddev: 0.0013491",
            "group": "Node Manipulation",
            "extra": "mean: 4.9313 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 44.563994489898995,
            "unit": "iter/sec",
            "range": "stddev: 0.0017453",
            "group": "Node Manipulation",
            "extra": "mean: 22.440 msec\nrounds: 100"
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
          "id": "1572d7806548c3aa2aeeabc6bdbbf54ea6fa82da",
          "message": "Pytest Benchmark",
          "timestamp": "2020-09-09T14:11:43Z",
          "url": "https://github.com/aiidateam/aiida-core/pull/4362/commits/1572d7806548c3aa2aeeabc6bdbbf54ea6fa82da"
        },
        "date": 1599663890572,
        "benches": [
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 902.7071475802869,
            "unit": "iter/sec",
            "range": "stddev: 0.00015555",
            "group": "Node Manipulation",
            "extra": "mean: 1.1078 msec\nrounds: 170"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 191.02582801614705,
            "unit": "iter/sec",
            "range": "stddev: 0.00094067",
            "group": "Node Manipulation",
            "extra": "mean: 5.2349 msec\nrounds: 132"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 211.60206504997876,
            "unit": "iter/sec",
            "range": "stddev: 0.00055397",
            "group": "Node Manipulation",
            "extra": "mean: 4.7259 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 46.66216038362447,
            "unit": "iter/sec",
            "range": "stddev: 0.0015692",
            "group": "Node Manipulation",
            "extra": "mean: 21.431 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_calcfunction",
            "value": 7.983196736316167,
            "unit": "iter/sec",
            "range": "stddev: 0.020632",
            "group": "Computations",
            "extra": "mean: 125.26 msec\nrounds: 50"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_workchain",
            "value": 4.141041335559523,
            "unit": "iter/sec",
            "range": "stddev: 0.027196",
            "group": "Computations",
            "extra": "mean: 241.49 msec\nrounds: 50"
          }
        ]
      }
    ]
  }
}