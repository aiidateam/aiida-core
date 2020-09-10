window.BENCHMARK_DATA = {
  "lastUpdate": 1599730250887,
  "repoUrl": "https://github.com/aiidateam/aiida-core",
  "entries": {
    "pytest-benchmarks:ubuntu-18.04,django": [
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
            "group": "node",
            "extra": "mean: 1.2641 msec\nrounds: 126"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 169.66712572252993,
            "unit": "iter/sec",
            "range": "stddev: 0.0013330",
            "group": "node",
            "extra": "mean: 5.8939 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 183.18574836120615,
            "unit": "iter/sec",
            "range": "stddev: 0.0013803",
            "group": "node",
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
            "group": "node",
            "extra": "mean: 715.29 usec\nrounds: 215"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 293.8502929177761,
            "unit": "iter/sec",
            "range": "stddev: 0.00028604",
            "group": "node",
            "extra": "mean: 3.4031 msec\nrounds: 155"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 312.0641224866216,
            "unit": "iter/sec",
            "range": "stddev: 0.00028478",
            "group": "node",
            "extra": "mean: 3.2045 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 62.757650790073946,
            "unit": "iter/sec",
            "range": "stddev: 0.0010569",
            "group": "node",
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
            "group": "node",
            "extra": "mean: 1.0255 msec\nrounds: 190"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 182.8526361105402,
            "unit": "iter/sec",
            "range": "stddev: 0.0018678",
            "group": "node",
            "extra": "mean: 5.4689 msec\nrounds: 113"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 209.01848591477287,
            "unit": "iter/sec",
            "range": "stddev: 0.00045438",
            "group": "node",
            "extra": "mean: 4.7843 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 39.194463471618405,
            "unit": "iter/sec",
            "range": "stddev: 0.0023900",
            "group": "node",
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
            "group": "node",
            "extra": "mean: 1.1892 msec\nrounds: 189"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 185.6188510187037,
            "unit": "iter/sec",
            "range": "stddev: 0.00033612",
            "group": "node",
            "extra": "mean: 5.3874 msec\nrounds: 119"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 185.59671117875624,
            "unit": "iter/sec",
            "range": "stddev: 0.00061245",
            "group": "node",
            "extra": "mean: 5.3880 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 39.92931484291115,
            "unit": "iter/sec",
            "range": "stddev: 0.0025803",
            "group": "node",
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
            "group": "node",
            "extra": "mean: 972.65 usec\nrounds: 228"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 210.61563144948025,
            "unit": "iter/sec",
            "range": "stddev: 0.0018761",
            "group": "node",
            "extra": "mean: 4.7480 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 225.90149952324458,
            "unit": "iter/sec",
            "range": "stddev: 0.00047594",
            "group": "node",
            "extra": "mean: 4.4267 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 49.38296479320641,
            "unit": "iter/sec",
            "range": "stddev: 0.0013282",
            "group": "node",
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
            "group": "node",
            "extra": "mean: 1.0935 msec\nrounds: 182"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 197.4432992555117,
            "unit": "iter/sec",
            "range": "stddev: 0.00038992",
            "group": "node",
            "extra": "mean: 5.0647 msec\nrounds: 127"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 202.78458931221144,
            "unit": "iter/sec",
            "range": "stddev: 0.0013491",
            "group": "node",
            "extra": "mean: 4.9313 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 44.563994489898995,
            "unit": "iter/sec",
            "range": "stddev: 0.0017453",
            "group": "node",
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
            "group": "node",
            "extra": "mean: 1.1078 msec\nrounds: 170"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 191.02582801614705,
            "unit": "iter/sec",
            "range": "stddev: 0.00094067",
            "group": "node",
            "extra": "mean: 5.2349 msec\nrounds: 132"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 211.60206504997876,
            "unit": "iter/sec",
            "range": "stddev: 0.00055397",
            "group": "node",
            "extra": "mean: 4.7259 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 46.66216038362447,
            "unit": "iter/sec",
            "range": "stddev: 0.0015692",
            "group": "node",
            "extra": "mean: 21.431 msec\nrounds: 100"
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
        "date": 1599664288677,
        "benches": [
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 1084.1518923549907,
            "unit": "iter/sec",
            "range": "stddev: 0.000035929",
            "group": "node",
            "extra": "mean: 922.38 usec\nrounds: 193"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 157.24289791749663,
            "unit": "iter/sec",
            "range": "stddev: 0.020548",
            "group": "node",
            "extra": "mean: 6.3596 msec\nrounds: 128"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 233.59602241653775,
            "unit": "iter/sec",
            "range": "stddev: 0.00014569",
            "group": "node",
            "extra": "mean: 4.2809 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 44.65389943420907,
            "unit": "iter/sec",
            "range": "stddev: 0.0013234",
            "group": "node",
            "extra": "mean: 22.394 msec\nrounds: 100"
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
          "id": "b0750653ae327c1f7291c55c1a38f2dd035cbaa7",
          "message": "Pytest Benchmark",
          "timestamp": "2020-09-09T15:10:57Z",
          "url": "https://github.com/aiidateam/aiida-core/pull/4362/commits/b0750653ae327c1f7291c55c1a38f2dd035cbaa7"
        },
        "date": 1599664551850,
        "benches": [
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 979.5943825287989,
            "unit": "iter/sec",
            "range": "stddev: 0.00010348",
            "group": "node",
            "extra": "mean: 1.0208 msec\nrounds: 219"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 214.43706619303023,
            "unit": "iter/sec",
            "range": "stddev: 0.00029577",
            "group": "node",
            "extra": "mean: 4.6634 msec\nrounds: 139"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 212.38931391969584,
            "unit": "iter/sec",
            "range": "stddev: 0.00067352",
            "group": "node",
            "extra": "mean: 4.7083 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 46.238209545557226,
            "unit": "iter/sec",
            "range": "stddev: 0.0013785",
            "group": "node",
            "extra": "mean: 21.627 msec\nrounds: 100"
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
          "id": "957ae068c74712befb810d3cad1d815acbf8b9b5",
          "message": "Pytest Benchmark",
          "timestamp": "2020-09-09T15:10:57Z",
          "url": "https://github.com/aiidateam/aiida-core/pull/4362/commits/957ae068c74712befb810d3cad1d815acbf8b9b5"
        },
        "date": 1599665049232,
        "benches": [
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 734.2291652886513,
            "unit": "iter/sec",
            "range": "stddev: 0.00061971",
            "group": "node",
            "extra": "mean: 1.3620 msec\nrounds: 140"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 186.70755604730812,
            "unit": "iter/sec",
            "range": "stddev: 0.00071959",
            "group": "node",
            "extra": "mean: 5.3560 msec\nrounds: 111"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 182.55730656412427,
            "unit": "iter/sec",
            "range": "stddev: 0.0011717",
            "group": "node",
            "extra": "mean: 5.4777 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 40.51411225439273,
            "unit": "iter/sec",
            "range": "stddev: 0.0021451",
            "group": "node",
            "extra": "mean: 24.683 msec\nrounds: 100"
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
          "id": "be94c5e2ac3e4c75181f03e2a7b711af340bc761",
          "message": "Pytest Benchmark",
          "timestamp": "2020-09-09T15:10:57Z",
          "url": "https://github.com/aiidateam/aiida-core/pull/4362/commits/be94c5e2ac3e4c75181f03e2a7b711af340bc761"
        },
        "date": 1599673147719,
        "benches": [
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 884.951340078564,
            "unit": "iter/sec",
            "range": "stddev: 0.00012971",
            "group": "node",
            "extra": "mean: 1.1300 msec\nrounds: 183"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 186.71123453288064,
            "unit": "iter/sec",
            "range": "stddev: 0.00039131",
            "group": "node",
            "extra": "mean: 5.3559 msec\nrounds: 118"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 172.2368014773842,
            "unit": "iter/sec",
            "range": "stddev: 0.0013105",
            "group": "node",
            "extra": "mean: 5.8060 msec\nrounds: 120"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 198.5206704178543,
            "unit": "iter/sec",
            "range": "stddev: 0.00031438",
            "group": "node",
            "extra": "mean: 5.0373 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 39.118443913148525,
            "unit": "iter/sec",
            "range": "stddev: 0.0019487",
            "group": "node",
            "extra": "mean: 25.563 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 35.760627732961375,
            "unit": "iter/sec",
            "range": "stddev: 0.016754",
            "group": "node",
            "extra": "mean: 27.964 msec\nrounds: 100"
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
          "id": "c6120d5a55d50e60586a0cecb36ccd7db1efa190",
          "message": "Pytest Benchmark",
          "timestamp": "2020-09-09T15:10:57Z",
          "url": "https://github.com/aiidateam/aiida-core/pull/4362/commits/c6120d5a55d50e60586a0cecb36ccd7db1efa190"
        },
        "date": 1599673422180,
        "benches": [
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 719.9644353087076,
            "unit": "iter/sec",
            "range": "stddev: 0.00052515",
            "group": "node",
            "extra": "mean: 1.3890 msec\nrounds: 167"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 213.1628435776773,
            "unit": "iter/sec",
            "range": "stddev: 0.00077551",
            "group": "node",
            "extra": "mean: 4.6912 msec\nrounds: 156"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 207.02905062468128,
            "unit": "iter/sec",
            "range": "stddev: 0.00041391",
            "group": "node",
            "extra": "mean: 4.8302 msec\nrounds: 139"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 216.68472795271654,
            "unit": "iter/sec",
            "range": "stddev: 0.00053170",
            "group": "node",
            "extra": "mean: 4.6150 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 41.28531338403035,
            "unit": "iter/sec",
            "range": "stddev: 0.0086188",
            "group": "node",
            "extra": "mean: 24.222 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 44.908978688576106,
            "unit": "iter/sec",
            "range": "stddev: 0.013168",
            "group": "node",
            "extra": "mean: 22.267 msec\nrounds: 100"
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
          "id": "a883674a8379d12d72d1549af6d54e0b2c0a3d61",
          "message": "Pytest Benchmark",
          "timestamp": "2020-09-09T15:10:57Z",
          "url": "https://github.com/aiidateam/aiida-core/pull/4362/commits/a883674a8379d12d72d1549af6d54e0b2c0a3d61"
        },
        "date": 1599674456473,
        "benches": [
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 939.3046103435286,
            "unit": "iter/sec",
            "range": "stddev: 0.000065151",
            "group": "node",
            "extra": "mean: 1.0646 msec\nrounds: 205"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 205.22703365034147,
            "unit": "iter/sec",
            "range": "stddev: 0.00037257",
            "group": "node",
            "extra": "mean: 4.8727 msec\nrounds: 127"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 184.7402327751952,
            "unit": "iter/sec",
            "range": "stddev: 0.00069379",
            "group": "node",
            "extra": "mean: 5.4130 msec\nrounds: 112"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 173.797145265077,
            "unit": "iter/sec",
            "range": "stddev: 0.0023754",
            "group": "node",
            "extra": "mean: 5.7538 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 42.03256831768416,
            "unit": "iter/sec",
            "range": "stddev: 0.0020552",
            "group": "node",
            "extra": "mean: 23.791 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 39.150956754092526,
            "unit": "iter/sec",
            "range": "stddev: 0.014367",
            "group": "node",
            "extra": "mean: 25.542 msec\nrounds: 100"
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
          "id": "2a11abe84756827a76e1709f1727985a6d5e470f",
          "message": "Pytest Benchmark",
          "timestamp": "2020-09-09T15:10:57Z",
          "url": "https://github.com/aiidateam/aiida-core/pull/4362/commits/2a11abe84756827a76e1709f1727985a6d5e470f"
        },
        "date": 1599674650833,
        "benches": [
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 782.3485135512398,
            "unit": "iter/sec",
            "range": "stddev: 0.00055484",
            "group": "node",
            "extra": "mean: 1.2782 msec\nrounds: 173"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 165.71826977270945,
            "unit": "iter/sec",
            "range": "stddev: 0.0017835",
            "group": "node",
            "extra": "mean: 6.0343 msec\nrounds: 104"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 156.10492730059292,
            "unit": "iter/sec",
            "range": "stddev: 0.0010491",
            "group": "node",
            "extra": "mean: 6.4059 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 162.29184650644453,
            "unit": "iter/sec",
            "range": "stddev: 0.0015426",
            "group": "node",
            "extra": "mean: 6.1617 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 35.0342226917095,
            "unit": "iter/sec",
            "range": "stddev: 0.0030793",
            "group": "node",
            "extra": "mean: 28.544 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 32.12701990465496,
            "unit": "iter/sec",
            "range": "stddev: 0.016155",
            "group": "node",
            "extra": "mean: 31.126 msec\nrounds: 100"
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
          "id": "bc2d43a9ed2320c9dbd4a3b89f2e26f494a86d63",
          "message": "Pytest Benchmark",
          "timestamp": "2020-09-09T21:08:28Z",
          "url": "https://github.com/aiidateam/aiida-core/pull/4362/commits/bc2d43a9ed2320c9dbd4a3b89f2e26f494a86d63"
        },
        "date": 1599729472422,
        "benches": [
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 980.084525413532,
            "unit": "iter/sec",
            "range": "stddev: 0.00063556",
            "group": "node",
            "extra": "mean: 1.0203 msec\nrounds: 181"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 219.69640492657538,
            "unit": "iter/sec",
            "range": "stddev: 0.00057826",
            "group": "node",
            "extra": "mean: 4.5517 msec\nrounds: 118"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 158.39024482753214,
            "unit": "iter/sec",
            "range": "stddev: 0.010136",
            "group": "node",
            "extra": "mean: 6.3135 msec\nrounds: 118"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 220.0493478706398,
            "unit": "iter/sec",
            "range": "stddev: 0.00094170",
            "group": "node",
            "extra": "mean: 4.5444 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 43.610503464156125,
            "unit": "iter/sec",
            "range": "stddev: 0.0031994",
            "group": "node",
            "extra": "mean: 22.930 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 40.56270658518115,
            "unit": "iter/sec",
            "range": "stddev: 0.016153",
            "group": "node",
            "extra": "mean: 24.653 msec\nrounds: 100"
          }
        ]
      }
    ],
    "Pytest Benchmarks (ubuntu-latest, django)": [
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
          "id": "988b4e25cf168fb4e08fb3fcb9659fffa558dba3",
          "message": "Pytest Benchmark",
          "timestamp": "2020-09-09T21:08:28Z",
          "url": "https://github.com/aiidateam/aiida-core/pull/4362/commits/988b4e25cf168fb4e08fb3fcb9659fffa558dba3"
        },
        "date": 1599730250354,
        "benches": [
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 744.4197071053151,
            "unit": "iter/sec",
            "range": "stddev: 0.00090642",
            "group": "Single Node",
            "extra": "mean: 1.3433 msec\nrounds: 191"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 181.39784267336847,
            "unit": "iter/sec",
            "range": "stddev: 0.00043474",
            "group": "Single Node",
            "extra": "mean: 5.5127 msec\nrounds: 112"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 161.70548574239902,
            "unit": "iter/sec",
            "range": "stddev: 0.0017341",
            "group": "Single Node",
            "extra": "mean: 6.1841 msec\nrounds: 109"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 184.63951353419193,
            "unit": "iter/sec",
            "range": "stddev: 0.00044071",
            "group": "Single Node",
            "extra": "mean: 5.4160 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 38.080792012598316,
            "unit": "iter/sec",
            "range": "stddev: 0.0020144",
            "group": "Single Node",
            "extra": "mean: 26.260 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 36.361532300265765,
            "unit": "iter/sec",
            "range": "stddev: 0.015851",
            "group": "Single Node",
            "extra": "mean: 27.502 msec\nrounds: 100"
          }
        ]
      }
    ]
  }
}