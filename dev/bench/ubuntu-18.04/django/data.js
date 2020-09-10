window.BENCHMARK_DATA = {
  "lastUpdate": 1599767967877,
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
          "id": "a5a84662acdae669f4d2310e45dec1b183ca1fcd",
          "message": "Pytest Benchmark",
          "timestamp": "2020-09-09T21:08:28Z",
          "url": "https://github.com/aiidateam/aiida-core/pull/4362/commits/a5a84662acdae669f4d2310e45dec1b183ca1fcd"
        },
        "date": 1599732259586,
        "benches": [
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 1116.788672356645,
            "unit": "iter/sec",
            "range": "stddev: 0.00010325",
            "group": "node",
            "extra": "mean: 895.42 usec\nrounds: 209"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 235.93455147894878,
            "unit": "iter/sec",
            "range": "stddev: 0.00021208",
            "group": "node",
            "extra": "mean: 4.2385 msec\nrounds: 140"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 141.49521606726998,
            "unit": "iter/sec",
            "range": "stddev: 0.023494",
            "group": "node",
            "extra": "mean: 7.0674 msec\nrounds: 131"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 238.2711201918703,
            "unit": "iter/sec",
            "range": "stddev: 0.00058487",
            "group": "node",
            "extra": "mean: 4.1969 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 47.35870002141336,
            "unit": "iter/sec",
            "range": "stddev: 0.0016020",
            "group": "node",
            "extra": "mean: 21.115 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 44.30592307866228,
            "unit": "iter/sec",
            "range": "stddev: 0.014101",
            "group": "node",
            "extra": "mean: 22.570 msec\nrounds: 100"
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
          "id": "5e6083547fb78d471ea2e54cf0868f2427cbdae3",
          "message": "Pytest Benchmark",
          "timestamp": "2020-09-09T21:08:28Z",
          "url": "https://github.com/aiidateam/aiida-core/pull/4362/commits/5e6083547fb78d471ea2e54cf0868f2427cbdae3"
        },
        "date": 1599733067311,
        "benches": [
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 1105.7716630766997,
            "unit": "iter/sec",
            "range": "stddev: 0.000091081",
            "group": "node",
            "extra": "mean: 904.35 usec\nrounds: 190"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 222.33896911496453,
            "unit": "iter/sec",
            "range": "stddev: 0.00060431",
            "group": "node",
            "extra": "mean: 4.4976 msec\nrounds: 137"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 194.6199876287364,
            "unit": "iter/sec",
            "range": "stddev: 0.0036731",
            "group": "node",
            "extra": "mean: 5.1382 msec\nrounds: 135"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 240.3411760279346,
            "unit": "iter/sec",
            "range": "stddev: 0.00037333",
            "group": "node",
            "extra": "mean: 4.1608 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 45.52705813834543,
            "unit": "iter/sec",
            "range": "stddev: 0.010361",
            "group": "node",
            "extra": "mean: 21.965 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 44.195053154096705,
            "unit": "iter/sec",
            "range": "stddev: 0.015048",
            "group": "node",
            "extra": "mean: 22.627 msec\nrounds: 100"
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
          "id": "fd27d6419c1cf01fdf8660f12a5d749cdbc50d41",
          "message": "Pytest Benchmark",
          "timestamp": "2020-09-09T21:08:28Z",
          "url": "https://github.com/aiidateam/aiida-core/pull/4362/commits/fd27d6419c1cf01fdf8660f12a5d749cdbc50d41"
        },
        "date": 1599753976395,
        "benches": [
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 1102.5274722285392,
            "unit": "iter/sec",
            "range": "stddev: 0.000083069",
            "group": "node",
            "extra": "mean: 907.01 usec\nrounds: 196"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 229.45165132616324,
            "unit": "iter/sec",
            "range": "stddev: 0.00048411",
            "group": "node",
            "extra": "mean: 4.3582 msec\nrounds: 139"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 216.8770398398261,
            "unit": "iter/sec",
            "range": "stddev: 0.00024128",
            "group": "node",
            "extra": "mean: 4.6109 msec\nrounds: 139"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 241.82923171231755,
            "unit": "iter/sec",
            "range": "stddev: 0.00057616",
            "group": "node",
            "extra": "mean: 4.1351 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 47.87630595630726,
            "unit": "iter/sec",
            "range": "stddev: 0.0016074",
            "group": "node",
            "extra": "mean: 20.887 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 45.63179269505632,
            "unit": "iter/sec",
            "range": "stddev: 0.015218",
            "group": "node",
            "extra": "mean: 21.915 msec\nrounds: 100"
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
          "id": "af1e5bbdc76f227c0f4b17b8a1fddc2053a44889",
          "message": "Pytest Benchmark",
          "timestamp": "2020-09-09T21:08:28Z",
          "url": "https://github.com/aiidateam/aiida-core/pull/4362/commits/af1e5bbdc76f227c0f4b17b8a1fddc2053a44889"
        },
        "date": 1599756061828,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.4230933763464417,
            "unit": "iter/sec",
            "range": "stddev: 0.013876",
            "group": "engine",
            "extra": "mean: 292.13 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.8118020122037132,
            "unit": "iter/sec",
            "range": "stddev: 0.056500",
            "group": "engine",
            "extra": "mean: 1.2318 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.9223326829589825,
            "unit": "iter/sec",
            "range": "stddev: 0.048760",
            "group": "engine",
            "extra": "mean: 1.0842 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.17412278513525872,
            "unit": "iter/sec",
            "range": "stddev: 0.18007",
            "group": "engine",
            "extra": "mean: 5.7431 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.20374746894490228,
            "unit": "iter/sec",
            "range": "stddev: 0.086164",
            "group": "engine",
            "extra": "mean: 4.9080 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 874.979814364268,
            "unit": "iter/sec",
            "range": "stddev: 0.00014235",
            "group": "node",
            "extra": "mean: 1.1429 msec\nrounds: 179"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 188.65741242129954,
            "unit": "iter/sec",
            "range": "stddev: 0.00050883",
            "group": "node",
            "extra": "mean: 5.3006 msec\nrounds: 132"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 177.11035017802436,
            "unit": "iter/sec",
            "range": "stddev: 0.00075437",
            "group": "node",
            "extra": "mean: 5.6462 msec\nrounds: 135"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 191.19033773606913,
            "unit": "iter/sec",
            "range": "stddev: 0.00057030",
            "group": "node",
            "extra": "mean: 5.2304 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 40.79661182606528,
            "unit": "iter/sec",
            "range": "stddev: 0.0031541",
            "group": "node",
            "extra": "mean: 24.512 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 39.334172927549545,
            "unit": "iter/sec",
            "range": "stddev: 0.014704",
            "group": "node",
            "extra": "mean: 25.423 msec\nrounds: 100"
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
          "id": "731c8eab83c252503528ce9a24e6161ac31f3c13",
          "message": "Pytest Benchmark",
          "timestamp": "2020-09-09T21:08:28Z",
          "url": "https://github.com/aiidateam/aiida-core/pull/4362/commits/731c8eab83c252503528ce9a24e6161ac31f3c13"
        },
        "date": 1599758335484,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.5608961844877904,
            "unit": "iter/sec",
            "range": "stddev: 0.0042169",
            "group": "engine",
            "extra": "mean: 280.83 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.8688814986200055,
            "unit": "iter/sec",
            "range": "stddev: 0.041742",
            "group": "engine",
            "extra": "mean: 1.1509 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.9666489803123582,
            "unit": "iter/sec",
            "range": "stddev: 0.054018",
            "group": "engine",
            "extra": "mean: 1.0345 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local_local[serial-calcjob-loop]",
            "value": 0.1833025321491672,
            "unit": "iter/sec",
            "range": "stddev: 0.12383",
            "group": "engine",
            "extra": "mean: 5.4555 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.2158158846097108,
            "unit": "iter/sec",
            "range": "stddev: 0.079425",
            "group": "engine",
            "extra": "mean: 4.6336 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 1011.5099010597272,
            "unit": "iter/sec",
            "range": "stddev: 0.00041477",
            "group": "node",
            "extra": "mean: 988.62 usec\nrounds: 202"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 230.97850677237403,
            "unit": "iter/sec",
            "range": "stddev: 0.00051002",
            "group": "node",
            "extra": "mean: 4.3294 msec\nrounds: 135"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 218.65976723099106,
            "unit": "iter/sec",
            "range": "stddev: 0.00016668",
            "group": "node",
            "extra": "mean: 4.5733 msec\nrounds: 132"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 240.98832183368177,
            "unit": "iter/sec",
            "range": "stddev: 0.00043976",
            "group": "node",
            "extra": "mean: 4.1496 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 44.037047714738215,
            "unit": "iter/sec",
            "range": "stddev: 0.015884",
            "group": "node",
            "extra": "mean: 22.708 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 44.14592050837919,
            "unit": "iter/sec",
            "range": "stddev: 0.0061400",
            "group": "node",
            "extra": "mean: 22.652 msec\nrounds: 100"
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
          "id": "f53bf967f1fb7b9201fa3937a21fe826fcce343d",
          "message": "Pytest Benchmark",
          "timestamp": "2020-09-10T17:18:54Z",
          "url": "https://github.com/aiidateam/aiida-core/pull/4362/commits/f53bf967f1fb7b9201fa3937a21fe826fcce343d"
        },
        "date": 1599764607193,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.1451347427728584,
            "unit": "iter/sec",
            "range": "stddev: 0.053798",
            "group": "engine",
            "extra": "mean: 317.95 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.7592884768274909,
            "unit": "iter/sec",
            "range": "stddev: 0.089579",
            "group": "engine",
            "extra": "mean: 1.3170 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.8423139738068088,
            "unit": "iter/sec",
            "range": "stddev: 0.070284",
            "group": "engine",
            "extra": "mean: 1.1872 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.16833719348041912,
            "unit": "iter/sec",
            "range": "stddev: 0.20179",
            "group": "engine",
            "extra": "mean: 5.9405 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.1775747143015169,
            "unit": "iter/sec",
            "range": "stddev: 0.22874",
            "group": "engine",
            "extra": "mean: 5.6314 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.246282676105141,
            "unit": "iter/sec",
            "range": "stddev: 0.034467",
            "group": "engine",
            "extra": "mean: 445.18 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.5270944548208711,
            "unit": "iter/sec",
            "range": "stddev: 0.071822",
            "group": "engine",
            "extra": "mean: 1.8972 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.5759794529531871,
            "unit": "iter/sec",
            "range": "stddev: 0.058907",
            "group": "engine",
            "extra": "mean: 1.7362 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.13152032097916463,
            "unit": "iter/sec",
            "range": "stddev: 0.19310",
            "group": "engine",
            "extra": "mean: 7.6034 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.15328558989422783,
            "unit": "iter/sec",
            "range": "stddev: 0.21732",
            "group": "engine",
            "extra": "mean: 6.5238 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 769.8085780989941,
            "unit": "iter/sec",
            "range": "stddev: 0.00040041",
            "group": "node",
            "extra": "mean: 1.2990 msec\nrounds: 178"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 172.94437930308302,
            "unit": "iter/sec",
            "range": "stddev: 0.00079065",
            "group": "node",
            "extra": "mean: 5.7822 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 163.80887673581586,
            "unit": "iter/sec",
            "range": "stddev: 0.00081813",
            "group": "node",
            "extra": "mean: 6.1047 msec\nrounds: 101"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 171.86982924235048,
            "unit": "iter/sec",
            "range": "stddev: 0.0010590",
            "group": "node",
            "extra": "mean: 5.8184 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 30.92661499021534,
            "unit": "iter/sec",
            "range": "stddev: 0.020590",
            "group": "node",
            "extra": "mean: 32.335 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 34.6696793480937,
            "unit": "iter/sec",
            "range": "stddev: 0.0033167",
            "group": "node",
            "extra": "mean: 28.844 msec\nrounds: 100"
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
          "id": "cbd44d0114d4e40c269ba789ed873ab50fff6d17",
          "message": "Pytest Benchmark",
          "timestamp": "2020-09-10T17:18:54Z",
          "url": "https://github.com/aiidateam/aiida-core/pull/4362/commits/cbd44d0114d4e40c269ba789ed873ab50fff6d17"
        },
        "date": 1599765253049,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.2161566195562528,
            "unit": "iter/sec",
            "range": "stddev: 0.010645",
            "group": "engine",
            "extra": "mean: 310.93 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.7799135066421767,
            "unit": "iter/sec",
            "range": "stddev: 0.045814",
            "group": "engine",
            "extra": "mean: 1.2822 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.8667985528113407,
            "unit": "iter/sec",
            "range": "stddev: 0.053737",
            "group": "engine",
            "extra": "mean: 1.1537 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.17119534777532622,
            "unit": "iter/sec",
            "range": "stddev: 0.12182",
            "group": "engine",
            "extra": "mean: 5.8413 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.19436922486101663,
            "unit": "iter/sec",
            "range": "stddev: 0.16336",
            "group": "engine",
            "extra": "mean: 5.1448 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.4642566485369364,
            "unit": "iter/sec",
            "range": "stddev: 0.013133",
            "group": "engine",
            "extra": "mean: 405.80 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.5926032851224212,
            "unit": "iter/sec",
            "range": "stddev: 0.094894",
            "group": "engine",
            "extra": "mean: 1.6875 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.6841900363762353,
            "unit": "iter/sec",
            "range": "stddev: 0.056618",
            "group": "engine",
            "extra": "mean: 1.4616 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.15228512926591314,
            "unit": "iter/sec",
            "range": "stddev: 0.14964",
            "group": "engine",
            "extra": "mean: 6.5666 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.1780839108177389,
            "unit": "iter/sec",
            "range": "stddev: 0.16267",
            "group": "engine",
            "extra": "mean: 5.6153 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 894.1555221654166,
            "unit": "iter/sec",
            "range": "stddev: 0.00011621",
            "group": "node",
            "extra": "mean: 1.1184 msec\nrounds: 177"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 184.93023488403625,
            "unit": "iter/sec",
            "range": "stddev: 0.00045416",
            "group": "node",
            "extra": "mean: 5.4074 msec\nrounds: 120"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 167.7880137921742,
            "unit": "iter/sec",
            "range": "stddev: 0.0012672",
            "group": "node",
            "extra": "mean: 5.9599 msec\nrounds: 110"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 191.750905204235,
            "unit": "iter/sec",
            "range": "stddev: 0.00048007",
            "group": "node",
            "extra": "mean: 5.2151 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 39.24626812092466,
            "unit": "iter/sec",
            "range": "stddev: 0.0025507",
            "group": "node",
            "extra": "mean: 25.480 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 39.294190380782894,
            "unit": "iter/sec",
            "range": "stddev: 0.0018043",
            "group": "node",
            "extra": "mean: 25.449 msec\nrounds: 100"
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
          "id": "33ead345827bed40819db28882b33e36035c83f6",
          "message": "update [skip ci]",
          "timestamp": "2020-09-10T20:14:41+01:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/33ead345827bed40819db28882b33e36035c83f6",
          "distinct": true,
          "tree_id": "76b476b599ba5230e2a87670f510167444c9726c"
        },
        "date": 1599765829213,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.521660867554699,
            "unit": "iter/sec",
            "range": "stddev: 0.0088719",
            "group": "engine",
            "extra": "mean: 283.96 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.832730089708117,
            "unit": "iter/sec",
            "range": "stddev: 0.066965",
            "group": "engine",
            "extra": "mean: 1.2009 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.89820175147389,
            "unit": "iter/sec",
            "range": "stddev: 0.048002",
            "group": "engine",
            "extra": "mean: 1.1133 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.16124351938653256,
            "unit": "iter/sec",
            "range": "stddev: 0.47461",
            "group": "engine",
            "extra": "mean: 6.2018 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.19897001387556276,
            "unit": "iter/sec",
            "range": "stddev: 0.085299",
            "group": "engine",
            "extra": "mean: 5.0259 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.5613470990743687,
            "unit": "iter/sec",
            "range": "stddev: 0.055360",
            "group": "engine",
            "extra": "mean: 390.42 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.6334783694983304,
            "unit": "iter/sec",
            "range": "stddev: 0.067546",
            "group": "engine",
            "extra": "mean: 1.5786 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.5165395198560613,
            "unit": "iter/sec",
            "range": "stddev: 1.7059",
            "group": "engine",
            "extra": "mean: 1.9360 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.14954497146084383,
            "unit": "iter/sec",
            "range": "stddev: 0.33249",
            "group": "engine",
            "extra": "mean: 6.6870 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.17343961821410026,
            "unit": "iter/sec",
            "range": "stddev: 0.59822",
            "group": "engine",
            "extra": "mean: 5.7657 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 925.0857518701001,
            "unit": "iter/sec",
            "range": "stddev: 0.00021115",
            "group": "node",
            "extra": "mean: 1.0810 msec\nrounds: 168"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 207.96898381961,
            "unit": "iter/sec",
            "range": "stddev: 0.00022262",
            "group": "node",
            "extra": "mean: 4.8084 msec\nrounds: 122"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 191.570972668472,
            "unit": "iter/sec",
            "range": "stddev: 0.00034547",
            "group": "node",
            "extra": "mean: 5.2200 msec\nrounds: 120"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 210.99388267569654,
            "unit": "iter/sec",
            "range": "stddev: 0.00034920",
            "group": "node",
            "extra": "mean: 4.7395 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 39.332178222251336,
            "unit": "iter/sec",
            "range": "stddev: 0.018085",
            "group": "node",
            "extra": "mean: 25.424 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 43.07518252675722,
            "unit": "iter/sec",
            "range": "stddev: 0.0015233",
            "group": "node",
            "extra": "mean: 23.215 msec\nrounds: 100"
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
          "metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "115342eae460f7c49f3fdf66e1f4cdc4fef5acbd",
          "message": "update [skip ci]",
          "timestamp": "2020-09-10T20:29:02+01:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/115342eae460f7c49f3fdf66e1f4cdc4fef5acbd",
          "distinct": true,
          "tree_id": "40a7f322fa263975cd99ecc0e4bb8c0c2b1c59ad"
        },
        "date": 1599766636763,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.60466577195624,
            "unit": "iter/sec",
            "range": "stddev: 0.044636",
            "group": "engine",
            "extra": "mean: 277.42 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.8713087425528202,
            "unit": "iter/sec",
            "range": "stddev: 0.034856",
            "group": "engine",
            "extra": "mean: 1.1477 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.9239398391345667,
            "unit": "iter/sec",
            "range": "stddev: 0.097017",
            "group": "engine",
            "extra": "mean: 1.0823 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.1887929471177875,
            "unit": "iter/sec",
            "range": "stddev: 0.072672",
            "group": "engine",
            "extra": "mean: 5.2968 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.2187756675427554,
            "unit": "iter/sec",
            "range": "stddev: 0.079024",
            "group": "engine",
            "extra": "mean: 4.5709 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.799813274181214,
            "unit": "iter/sec",
            "range": "stddev: 0.042104",
            "group": "engine",
            "extra": "mean: 357.17 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.6931874110762263,
            "unit": "iter/sec",
            "range": "stddev: 0.052749",
            "group": "engine",
            "extra": "mean: 1.4426 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.769624616813779,
            "unit": "iter/sec",
            "range": "stddev: 0.056943",
            "group": "engine",
            "extra": "mean: 1.2993 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.1689688883280173,
            "unit": "iter/sec",
            "range": "stddev: 0.089099",
            "group": "engine",
            "extra": "mean: 5.9182 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.1995384961042572,
            "unit": "iter/sec",
            "range": "stddev: 0.074474",
            "group": "engine",
            "extra": "mean: 5.0116 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 1018.3216827004559,
            "unit": "iter/sec",
            "range": "stddev: 0.000060407",
            "group": "node",
            "extra": "mean: 982.01 usec\nrounds: 209"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 216.20559392682475,
            "unit": "iter/sec",
            "range": "stddev: 0.00036176",
            "group": "node",
            "extra": "mean: 4.6252 msec\nrounds: 140"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 186.056904267417,
            "unit": "iter/sec",
            "range": "stddev: 0.0032250",
            "group": "node",
            "extra": "mean: 5.3747 msec\nrounds: 133"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 220.0177586893323,
            "unit": "iter/sec",
            "range": "stddev: 0.00021693",
            "group": "node",
            "extra": "mean: 4.5451 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 44.45906483756816,
            "unit": "iter/sec",
            "range": "stddev: 0.0014245",
            "group": "node",
            "extra": "mean: 22.493 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 41.52874601548919,
            "unit": "iter/sec",
            "range": "stddev: 0.016083",
            "group": "node",
            "extra": "mean: 24.080 msec\nrounds: 100"
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
          "id": "c2c29be9da141714834c22e3b87ba4c6be22fccd",
          "message": "update [skip ci]",
          "timestamp": "2020-09-10T20:48:26+01:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/c2c29be9da141714834c22e3b87ba4c6be22fccd",
          "distinct": true,
          "tree_id": "77b0a47016a3b3dc4bf37abb1f154b63a3b2aa0b"
        },
        "date": 1599767844163,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.318053540829413,
            "unit": "iter/sec",
            "range": "stddev: 0.014308",
            "group": "engine",
            "extra": "mean: 301.38 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.7882509990450803,
            "unit": "iter/sec",
            "range": "stddev: 0.035664",
            "group": "engine",
            "extra": "mean: 1.2686 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.8698340843926278,
            "unit": "iter/sec",
            "range": "stddev: 0.053566",
            "group": "engine",
            "extra": "mean: 1.1496 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.17198193283903881,
            "unit": "iter/sec",
            "range": "stddev: 0.094225",
            "group": "engine",
            "extra": "mean: 5.8146 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.1951321127747333,
            "unit": "iter/sec",
            "range": "stddev: 0.091341",
            "group": "engine",
            "extra": "mean: 5.1247 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.536008025392205,
            "unit": "iter/sec",
            "range": "stddev: 0.054961",
            "group": "engine",
            "extra": "mean: 394.32 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.6321416325388983,
            "unit": "iter/sec",
            "range": "stddev: 0.058244",
            "group": "engine",
            "extra": "mean: 1.5819 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.7233043741627224,
            "unit": "iter/sec",
            "range": "stddev: 0.056190",
            "group": "engine",
            "extra": "mean: 1.3825 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.1546841700490492,
            "unit": "iter/sec",
            "range": "stddev: 0.16288",
            "group": "engine",
            "extra": "mean: 6.4648 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.17976864898860676,
            "unit": "iter/sec",
            "range": "stddev: 0.088943",
            "group": "engine",
            "extra": "mean: 5.5627 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 871.2590956736811,
            "unit": "iter/sec",
            "range": "stddev: 0.00025816",
            "group": "node",
            "extra": "mean: 1.1478 msec\nrounds: 164"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 190.50111401173123,
            "unit": "iter/sec",
            "range": "stddev: 0.00064018",
            "group": "node",
            "extra": "mean: 5.2493 msec\nrounds: 126"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 180.34895151817366,
            "unit": "iter/sec",
            "range": "stddev: 0.00043815",
            "group": "node",
            "extra": "mean: 5.5448 msec\nrounds: 119"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 191.26154169685475,
            "unit": "iter/sec",
            "range": "stddev: 0.00095275",
            "group": "node",
            "extra": "mean: 5.2284 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 43.03408923259462,
            "unit": "iter/sec",
            "range": "stddev: 0.0016149",
            "group": "node",
            "extra": "mean: 23.237 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 38.58156356897101,
            "unit": "iter/sec",
            "range": "stddev: 0.017396",
            "group": "node",
            "extra": "mean: 25.919 msec\nrounds: 100"
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
          "id": "3b9d693bbcfbef0a9f681d0413050ee8e28f32f0",
          "message": "update [skip ci]",
          "timestamp": "2020-09-10T20:50:59+01:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/3b9d693bbcfbef0a9f681d0413050ee8e28f32f0",
          "distinct": true,
          "tree_id": "1bd3c6009554ef89e3b10f5dcd5b73b12fdec060"
        },
        "date": 1599767967356,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.578370919006883,
            "unit": "iter/sec",
            "range": "stddev: 0.0064388",
            "group": "engine",
            "extra": "mean: 279.46 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.8667690357071071,
            "unit": "iter/sec",
            "range": "stddev: 0.038927",
            "group": "engine",
            "extra": "mean: 1.1537 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.9619924296509845,
            "unit": "iter/sec",
            "range": "stddev: 0.046026",
            "group": "engine",
            "extra": "mean: 1.0395 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.18583779241813492,
            "unit": "iter/sec",
            "range": "stddev: 0.11428",
            "group": "engine",
            "extra": "mean: 5.3810 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.2146940068020528,
            "unit": "iter/sec",
            "range": "stddev: 0.059459",
            "group": "engine",
            "extra": "mean: 4.6578 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.8714233487238094,
            "unit": "iter/sec",
            "range": "stddev: 0.011636",
            "group": "engine",
            "extra": "mean: 348.26 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.6859058189174433,
            "unit": "iter/sec",
            "range": "stddev: 0.066153",
            "group": "engine",
            "extra": "mean: 1.4579 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.7703331188273732,
            "unit": "iter/sec",
            "range": "stddev: 0.040383",
            "group": "engine",
            "extra": "mean: 1.2981 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.16552935972483,
            "unit": "iter/sec",
            "range": "stddev: 0.086994",
            "group": "engine",
            "extra": "mean: 6.0412 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.19576260467205395,
            "unit": "iter/sec",
            "range": "stddev: 0.072403",
            "group": "engine",
            "extra": "mean: 5.1082 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 947.8668470931254,
            "unit": "iter/sec",
            "range": "stddev: 0.000088776",
            "group": "node",
            "extra": "mean: 1.0550 msec\nrounds: 199"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 199.40627388852698,
            "unit": "iter/sec",
            "range": "stddev: 0.00076642",
            "group": "node",
            "extra": "mean: 5.0149 msec\nrounds: 138"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 194.32530913203098,
            "unit": "iter/sec",
            "range": "stddev: 0.00079806",
            "group": "node",
            "extra": "mean: 5.1460 msec\nrounds: 134"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 200.00800111986624,
            "unit": "iter/sec",
            "range": "stddev: 0.00039966",
            "group": "node",
            "extra": "mean: 4.9998 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 42.033761623261206,
            "unit": "iter/sec",
            "range": "stddev: 0.014489",
            "group": "node",
            "extra": "mean: 23.790 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 42.43920251834241,
            "unit": "iter/sec",
            "range": "stddev: 0.0055300",
            "group": "node",
            "extra": "mean: 23.563 msec\nrounds: 100"
          }
        ]
      }
    ]
  }
}