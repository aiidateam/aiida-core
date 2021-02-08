window.BENCHMARK_DATA = {
  "lastUpdate": 1612783632524,
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
          "id": "7d521c5e049b2ccb1fa2aaf303fedb1850d9da87",
          "message": "add import-export [skip ci]",
          "timestamp": "2020-09-10T22:15:43+01:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/7d521c5e049b2ccb1fa2aaf303fedb1850d9da87",
          "distinct": true,
          "tree_id": "fcf2b1e721e078dfca86cee6645c3e6784bb43d1"
        },
        "date": 1599773156496,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.3272953470311233,
            "unit": "iter/sec",
            "range": "stddev: 0.0087980",
            "group": "engine",
            "extra": "mean: 300.54 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.7994446861505959,
            "unit": "iter/sec",
            "range": "stddev: 0.051461",
            "group": "engine",
            "extra": "mean: 1.2509 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.8831482147151971,
            "unit": "iter/sec",
            "range": "stddev: 0.063960",
            "group": "engine",
            "extra": "mean: 1.1323 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.16742790917122718,
            "unit": "iter/sec",
            "range": "stddev: 0.12029",
            "group": "engine",
            "extra": "mean: 5.9727 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.19234573605271618,
            "unit": "iter/sec",
            "range": "stddev: 0.12979",
            "group": "engine",
            "extra": "mean: 5.1990 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.5029292982984463,
            "unit": "iter/sec",
            "range": "stddev: 0.022755",
            "group": "engine",
            "extra": "mean: 399.53 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.5973820721505938,
            "unit": "iter/sec",
            "range": "stddev: 0.046581",
            "group": "engine",
            "extra": "mean: 1.6740 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.6802341653817906,
            "unit": "iter/sec",
            "range": "stddev: 0.054567",
            "group": "engine",
            "extra": "mean: 1.4701 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.14860119612850206,
            "unit": "iter/sec",
            "range": "stddev: 0.12376",
            "group": "engine",
            "extra": "mean: 6.7294 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.17125839684685026,
            "unit": "iter/sec",
            "range": "stddev: 0.099992",
            "group": "engine",
            "extra": "mean: 5.8391 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.52881833471687,
            "unit": "iter/sec",
            "range": "stddev: 0.058665",
            "group": "import-export",
            "extra": "mean: 395.44 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.242522770482318,
            "unit": "iter/sec",
            "range": "stddev: 0.052380",
            "group": "import-export",
            "extra": "mean: 445.93 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 1.4245633042236248,
            "unit": "iter/sec",
            "range": "stddev: 0.073275",
            "group": "import-export",
            "extra": "mean: 701.97 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 1.3661976299125687,
            "unit": "iter/sec",
            "range": "stddev: 0.047620",
            "group": "import-export",
            "extra": "mean: 731.96 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 987.106662053939,
            "unit": "iter/sec",
            "range": "stddev: 0.00034160",
            "group": "node",
            "extra": "mean: 1.0131 msec\nrounds: 198"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 192.22706841240486,
            "unit": "iter/sec",
            "range": "stddev: 0.0011044",
            "group": "node",
            "extra": "mean: 5.2022 msec\nrounds: 129"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 191.87382208094513,
            "unit": "iter/sec",
            "range": "stddev: 0.00074320",
            "group": "node",
            "extra": "mean: 5.2118 msec\nrounds: 116"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 216.03954258187696,
            "unit": "iter/sec",
            "range": "stddev: 0.00099146",
            "group": "node",
            "extra": "mean: 4.6288 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 37.80312279492947,
            "unit": "iter/sec",
            "range": "stddev: 0.015649",
            "group": "node",
            "extra": "mean: 26.453 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 37.76979747700348,
            "unit": "iter/sec",
            "range": "stddev: 0.0075738",
            "group": "node",
            "extra": "mean: 26.476 msec\nrounds: 100"
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
          "id": "0f46f3c38d57ccaaa0513e1f86621a5f23f5ed95",
          "message": "Merge branch 'develop' into benchmark-test-cjs",
          "timestamp": "2020-09-10T22:26:04+01:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/0f46f3c38d57ccaaa0513e1f86621a5f23f5ed95",
          "distinct": true,
          "tree_id": "9468ef71b969b3c838364960ab1c0947b6b85fb8"
        },
        "date": 1599773745066,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.4477871275437275,
            "unit": "iter/sec",
            "range": "stddev: 0.049237",
            "group": "engine",
            "extra": "mean: 290.04 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.8512906090411139,
            "unit": "iter/sec",
            "range": "stddev: 0.044038",
            "group": "engine",
            "extra": "mean: 1.1747 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.9686873552188137,
            "unit": "iter/sec",
            "range": "stddev: 0.062629",
            "group": "engine",
            "extra": "mean: 1.0323 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.18494720294017336,
            "unit": "iter/sec",
            "range": "stddev: 0.084179",
            "group": "engine",
            "extra": "mean: 5.4069 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.2120609259715305,
            "unit": "iter/sec",
            "range": "stddev: 0.10512",
            "group": "engine",
            "extra": "mean: 4.7156 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.8947300501544695,
            "unit": "iter/sec",
            "range": "stddev: 0.0047424",
            "group": "engine",
            "extra": "mean: 345.46 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.6800207467611233,
            "unit": "iter/sec",
            "range": "stddev: 0.059608",
            "group": "engine",
            "extra": "mean: 1.4705 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.7554761497641681,
            "unit": "iter/sec",
            "range": "stddev: 0.049380",
            "group": "engine",
            "extra": "mean: 1.3237 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.16449940531319057,
            "unit": "iter/sec",
            "range": "stddev: 0.089104",
            "group": "engine",
            "extra": "mean: 6.0790 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.19565743875655545,
            "unit": "iter/sec",
            "range": "stddev: 0.10034",
            "group": "engine",
            "extra": "mean: 5.1110 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.590741027801775,
            "unit": "iter/sec",
            "range": "stddev: 0.051077",
            "group": "import-export",
            "extra": "mean: 385.99 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.3642818036847726,
            "unit": "iter/sec",
            "range": "stddev: 0.0079880",
            "group": "import-export",
            "extra": "mean: 422.96 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 1.414861234727211,
            "unit": "iter/sec",
            "range": "stddev: 0.068921",
            "group": "import-export",
            "extra": "mean: 706.78 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 1.3150745370170793,
            "unit": "iter/sec",
            "range": "stddev: 0.059396",
            "group": "import-export",
            "extra": "mean: 760.41 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 1005.7574076503867,
            "unit": "iter/sec",
            "range": "stddev: 0.00029845",
            "group": "node",
            "extra": "mean: 994.28 usec\nrounds: 149"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 206.69912053425136,
            "unit": "iter/sec",
            "range": "stddev: 0.00061059",
            "group": "node",
            "extra": "mean: 4.8379 msec\nrounds: 142"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 199.70013144043696,
            "unit": "iter/sec",
            "range": "stddev: 0.00043909",
            "group": "node",
            "extra": "mean: 5.0075 msec\nrounds: 138"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 195.6267300201361,
            "unit": "iter/sec",
            "range": "stddev: 0.0011431",
            "group": "node",
            "extra": "mean: 5.1118 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 43.60549858620737,
            "unit": "iter/sec",
            "range": "stddev: 0.0017232",
            "group": "node",
            "extra": "mean: 22.933 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 42.98649519631049,
            "unit": "iter/sec",
            "range": "stddev: 0.0031770",
            "group": "node",
            "extra": "mean: 23.263 msec\nrounds: 100"
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
          "id": "4157b5d541a31001f7525b6063cdf8f8ceef7a7c",
          "message": "update [skip ci]",
          "timestamp": "2020-09-10T22:56:39+01:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/4157b5d541a31001f7525b6063cdf8f8ceef7a7c",
          "distinct": true,
          "tree_id": "03712bbb07262b60ed8f2e90dad5d3c90608666e"
        },
        "date": 1599775574675,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.2785449565690428,
            "unit": "iter/sec",
            "range": "stddev: 0.048969",
            "group": "engine",
            "extra": "mean: 305.01 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.8253399774831284,
            "unit": "iter/sec",
            "range": "stddev: 0.052175",
            "group": "engine",
            "extra": "mean: 1.2116 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.8961069014183451,
            "unit": "iter/sec",
            "range": "stddev: 0.060937",
            "group": "engine",
            "extra": "mean: 1.1159 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.17975353941663863,
            "unit": "iter/sec",
            "range": "stddev: 0.13387",
            "group": "engine",
            "extra": "mean: 5.5632 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.20809223162176027,
            "unit": "iter/sec",
            "range": "stddev: 0.080310",
            "group": "engine",
            "extra": "mean: 4.8056 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.7888515900873814,
            "unit": "iter/sec",
            "range": "stddev: 0.019326",
            "group": "engine",
            "extra": "mean: 358.57 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.6614235937636112,
            "unit": "iter/sec",
            "range": "stddev: 0.069993",
            "group": "engine",
            "extra": "mean: 1.5119 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.7407476104889513,
            "unit": "iter/sec",
            "range": "stddev: 0.045373",
            "group": "engine",
            "extra": "mean: 1.3500 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.16106714832700386,
            "unit": "iter/sec",
            "range": "stddev: 0.054783",
            "group": "engine",
            "extra": "mean: 6.2086 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.19051355012893895,
            "unit": "iter/sec",
            "range": "stddev: 0.096667",
            "group": "engine",
            "extra": "mean: 5.2490 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.7205011532025085,
            "unit": "iter/sec",
            "range": "stddev: 0.051083",
            "group": "import-export",
            "extra": "mean: 367.58 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.427641659098375,
            "unit": "iter/sec",
            "range": "stddev: 0.041558",
            "group": "import-export",
            "extra": "mean: 411.92 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 1.3732064173636884,
            "unit": "iter/sec",
            "range": "stddev: 0.058344",
            "group": "import-export",
            "extra": "mean: 728.22 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 1.2908845615480202,
            "unit": "iter/sec",
            "range": "stddev: 0.044753",
            "group": "import-export",
            "extra": "mean: 774.66 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 909.3830989809305,
            "unit": "iter/sec",
            "range": "stddev: 0.00011747",
            "group": "node",
            "extra": "mean: 1.0996 msec\nrounds: 188"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 204.97352386737208,
            "unit": "iter/sec",
            "range": "stddev: 0.00039283",
            "group": "node",
            "extra": "mean: 4.8787 msec\nrounds: 124"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 187.90261703050484,
            "unit": "iter/sec",
            "range": "stddev: 0.00056838",
            "group": "node",
            "extra": "mean: 5.3219 msec\nrounds: 133"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 202.87565899963323,
            "unit": "iter/sec",
            "range": "stddev: 0.00046196",
            "group": "node",
            "extra": "mean: 4.9291 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 39.36210421030053,
            "unit": "iter/sec",
            "range": "stddev: 0.015324",
            "group": "node",
            "extra": "mean: 25.405 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 42.356999760398324,
            "unit": "iter/sec",
            "range": "stddev: 0.0022175",
            "group": "node",
            "extra": "mean: 23.609 msec\nrounds: 100"
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
          "id": "9cadcb33cad0e04103fcce3260ec6e3715c30482",
          "message": "update [skip ci]",
          "timestamp": "2020-09-10T23:23:29+01:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/9cadcb33cad0e04103fcce3260ec6e3715c30482",
          "distinct": true,
          "tree_id": "861b48080809a6669428d5d0974bd25e84439b24"
        },
        "date": 1599777201540,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.2804408145357553,
            "unit": "iter/sec",
            "range": "stddev: 0.060653",
            "group": "engine",
            "extra": "mean: 304.84 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.7965151437822415,
            "unit": "iter/sec",
            "range": "stddev: 0.047410",
            "group": "engine",
            "extra": "mean: 1.2555 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.8775715743003427,
            "unit": "iter/sec",
            "range": "stddev: 0.079826",
            "group": "engine",
            "extra": "mean: 1.1395 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.17249502621885993,
            "unit": "iter/sec",
            "range": "stddev: 0.20441",
            "group": "engine",
            "extra": "mean: 5.7973 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.20122671764805347,
            "unit": "iter/sec",
            "range": "stddev: 0.11732",
            "group": "engine",
            "extra": "mean: 4.9695 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.693201414209122,
            "unit": "iter/sec",
            "range": "stddev: 0.018867",
            "group": "engine",
            "extra": "mean: 371.31 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.6325336572767238,
            "unit": "iter/sec",
            "range": "stddev: 0.063758",
            "group": "engine",
            "extra": "mean: 1.5809 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.7153563094871224,
            "unit": "iter/sec",
            "range": "stddev: 0.060499",
            "group": "engine",
            "extra": "mean: 1.3979 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.15780786003291863,
            "unit": "iter/sec",
            "range": "stddev: 0.077744",
            "group": "engine",
            "extra": "mean: 6.3368 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.1805021020431139,
            "unit": "iter/sec",
            "range": "stddev: 0.17552",
            "group": "engine",
            "extra": "mean: 5.5401 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.6500467892812347,
            "unit": "iter/sec",
            "range": "stddev: 0.052382",
            "group": "import-export",
            "extra": "mean: 377.35 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.4189676522122077,
            "unit": "iter/sec",
            "range": "stddev: 0.047137",
            "group": "import-export",
            "extra": "mean: 413.40 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 1.5130558338616247,
            "unit": "iter/sec",
            "range": "stddev: 0.065517",
            "group": "import-export",
            "extra": "mean: 660.91 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 1.4066203752879152,
            "unit": "iter/sec",
            "range": "stddev: 0.058128",
            "group": "import-export",
            "extra": "mean: 710.92 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 1095.6284786891001,
            "unit": "iter/sec",
            "range": "stddev: 0.000097635",
            "group": "node",
            "extra": "mean: 912.72 usec\nrounds: 178"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 221.2725201815654,
            "unit": "iter/sec",
            "range": "stddev: 0.00048405",
            "group": "node",
            "extra": "mean: 4.5193 msec\nrounds: 128"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 204.62517367367124,
            "unit": "iter/sec",
            "range": "stddev: 0.00030247",
            "group": "node",
            "extra": "mean: 4.8870 msec\nrounds: 114"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 214.39264981719234,
            "unit": "iter/sec",
            "range": "stddev: 0.00043624",
            "group": "node",
            "extra": "mean: 4.6643 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 42.994983847894346,
            "unit": "iter/sec",
            "range": "stddev: 0.0018828",
            "group": "node",
            "extra": "mean: 23.259 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 41.0516020082219,
            "unit": "iter/sec",
            "range": "stddev: 0.0044687",
            "group": "node",
            "extra": "mean: 24.360 msec\nrounds: 100"
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
          "id": "bee0be5d391cd20c841fdbd6133eab755c8733e8",
          "message": "use logarithmic y-axes",
          "timestamp": "2020-09-11T14:37:54+01:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/bee0be5d391cd20c841fdbd6133eab755c8733e8",
          "distinct": true,
          "tree_id": "29f5d8c65fc9aed4a37c3b9607fda9ee078fa26b"
        },
        "date": 1599832059631,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.4147902918753883,
            "unit": "iter/sec",
            "range": "stddev: 0.047286",
            "group": "engine",
            "extra": "mean: 292.84 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.8454569718453486,
            "unit": "iter/sec",
            "range": "stddev: 0.048822",
            "group": "engine",
            "extra": "mean: 1.1828 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.9446744728412709,
            "unit": "iter/sec",
            "range": "stddev: 0.055062",
            "group": "engine",
            "extra": "mean: 1.0586 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.1752453000336919,
            "unit": "iter/sec",
            "range": "stddev: 0.13416",
            "group": "engine",
            "extra": "mean: 5.7063 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.20841203608340972,
            "unit": "iter/sec",
            "range": "stddev: 0.13855",
            "group": "engine",
            "extra": "mean: 4.7982 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.895513875274814,
            "unit": "iter/sec",
            "range": "stddev: 0.0086310",
            "group": "engine",
            "extra": "mean: 345.36 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.6796273487818733,
            "unit": "iter/sec",
            "range": "stddev: 0.067547",
            "group": "engine",
            "extra": "mean: 1.4714 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.7530156909628805,
            "unit": "iter/sec",
            "range": "stddev: 0.070779",
            "group": "engine",
            "extra": "mean: 1.3280 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.16230280267559066,
            "unit": "iter/sec",
            "range": "stddev: 0.081575",
            "group": "engine",
            "extra": "mean: 6.1613 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.19141387591580566,
            "unit": "iter/sec",
            "range": "stddev: 0.092410",
            "group": "engine",
            "extra": "mean: 5.2243 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.776146241772248,
            "unit": "iter/sec",
            "range": "stddev: 0.050627",
            "group": "import-export",
            "extra": "mean: 360.21 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.4729083156939815,
            "unit": "iter/sec",
            "range": "stddev: 0.047293",
            "group": "import-export",
            "extra": "mean: 404.38 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 1.5223719894064385,
            "unit": "iter/sec",
            "range": "stddev: 0.076361",
            "group": "import-export",
            "extra": "mean: 656.87 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 1.4459198357144416,
            "unit": "iter/sec",
            "range": "stddev: 0.060025",
            "group": "import-export",
            "extra": "mean: 691.60 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 1075.3560871898069,
            "unit": "iter/sec",
            "range": "stddev: 0.00012963",
            "group": "node",
            "extra": "mean: 929.92 usec\nrounds: 190"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 224.04122007952833,
            "unit": "iter/sec",
            "range": "stddev: 0.00039825",
            "group": "node",
            "extra": "mean: 4.4635 msec\nrounds: 135"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 208.11434413398447,
            "unit": "iter/sec",
            "range": "stddev: 0.00037334",
            "group": "node",
            "extra": "mean: 4.8051 msec\nrounds: 128"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 237.3490477270387,
            "unit": "iter/sec",
            "range": "stddev: 0.00016817",
            "group": "node",
            "extra": "mean: 4.2132 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 45.47150576814014,
            "unit": "iter/sec",
            "range": "stddev: 0.0016497",
            "group": "node",
            "extra": "mean: 21.992 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 45.103615808173664,
            "unit": "iter/sec",
            "range": "stddev: 0.0013234",
            "group": "node",
            "extra": "mean: 22.171 msec\nrounds: 100"
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
          "id": "b002a9a9a898a05338ff522b46686657fb468f66",
          "message": "CI: add `pytest` benchmark workflows (#4362)\n\nThe basic steps of the workflow are:\r\n\r\n 1. Run `pytest` to generate JSON data.\r\n\r\nBy default, these tests are switched off (see `pytest.ini`) but to run\r\nthem locally, simply use `pytest tests/benchmark --benchmark-only`. This\r\nruns each test, marked as a benchmark, n-times and records the timing\r\nstatistics (see pytest-benchmark).\r\n\r\nWhen run also with `--benchmark-json benchmark.json`, a JSON file will\r\nalso be created, with all the details about each test.\r\n\r\n 2. Extract information from the above JSON, and also data about the\r\n    system (number of CPUs, etc) and created a \"simplified\" JSON object.\r\n\r\n 3. Read the JSON object from the specified `gh-pages` folder (data.js),\r\n    which contains a list of all these JSON objects.\r\n\r\nThese are split OS and backend.\r\n\r\n 4. If available, compare the new JSON section against the last one to\r\n    be added `data.js`, and comment in the PR and/or fail the workflow\r\n    if the timings have sufficiently degraded, depending on GH action\r\n    configuration.\r\n\r\n 5. If configured, add the new data to `data.js`, update the other\r\n    website assets (HTML/CSS/JS) and commit the updates to `gh-pages`.\r\n\r\nSince at ~7/8 minutes, these tests are slower than standard unit tests,\r\neven with the current fairly conservative tests/# of repetitions, they\r\nare not run by default on each commit. The current solution for this is\r\nto have two workflow jobs:\r\n\r\n  * One runs on every commit to develop, unless it is just updating\r\n    documentation, and will actually update the `gh-pages` data.\r\n  * The second is triggered by a commit to a branch with an open PR to\r\n    `develop`, but only if it includes `[run bench]` in the title of the\r\n    commit message. This will report back the timing data but not update\r\n    `gh-pages`. The idea is that this is run on the final commit of a PR\r\n    that may affect performance.\r\n\r\nOn to the actual tests. They are split into three categories:\r\n\r\n 1. Basic node storage/deletion, i.e. interactions with the ORM\r\n\r\n 2. Runs of workchains with internal (looped) calls to workchains and\r\n    calcjobs. These are duplicated using both a local runner and a\r\n    daemon runner. The daemon runner code is a bit tricky and may break\r\n    once we finalize the move to `asyncio`.\r\n\r\n 3. Expoting/importing archives.",
          "timestamp": "2020-09-16T12:08:59+02:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/b002a9a9a898a05338ff522b46686657fb468f66",
          "distinct": true,
          "tree_id": "8e03787cb2e4a4c359b79b5f53220a496897f0ff"
        },
        "date": 1600251474671,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 4.253485522007583,
            "unit": "iter/sec",
            "range": "stddev: 0.0096440",
            "group": "engine",
            "extra": "mean: 235.10 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.9819955856340673,
            "unit": "iter/sec",
            "range": "stddev: 0.045769",
            "group": "engine",
            "extra": "mean: 1.0183 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 1.096031425821652,
            "unit": "iter/sec",
            "range": "stddev: 0.073202",
            "group": "engine",
            "extra": "mean: 912.38 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.19155063291137733,
            "unit": "iter/sec",
            "range": "stddev: 0.19108",
            "group": "engine",
            "extra": "mean: 5.2206 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.2411928118654648,
            "unit": "iter/sec",
            "range": "stddev: 0.15721",
            "group": "engine",
            "extra": "mean: 4.1461 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 3.4545656087324113,
            "unit": "iter/sec",
            "range": "stddev: 0.014122",
            "group": "engine",
            "extra": "mean: 289.47 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.7156299195341463,
            "unit": "iter/sec",
            "range": "stddev: 0.092180",
            "group": "engine",
            "extra": "mean: 1.3974 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.8507450849998501,
            "unit": "iter/sec",
            "range": "stddev: 0.087754",
            "group": "engine",
            "extra": "mean: 1.1754 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.17757080452479693,
            "unit": "iter/sec",
            "range": "stddev: 0.21586",
            "group": "engine",
            "extra": "mean: 5.6316 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.20646189015520153,
            "unit": "iter/sec",
            "range": "stddev: 0.21376",
            "group": "engine",
            "extra": "mean: 4.8435 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.9377776231679587,
            "unit": "iter/sec",
            "range": "stddev: 0.052414",
            "group": "import-export",
            "extra": "mean: 340.39 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.9455826926544897,
            "unit": "iter/sec",
            "range": "stddev: 0.023082",
            "group": "import-export",
            "extra": "mean: 339.49 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 1.8159879943495707,
            "unit": "iter/sec",
            "range": "stddev: 0.091071",
            "group": "import-export",
            "extra": "mean: 550.66 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 1.7370794416730717,
            "unit": "iter/sec",
            "range": "stddev: 0.063497",
            "group": "import-export",
            "extra": "mean: 575.68 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 1298.479572323654,
            "unit": "iter/sec",
            "range": "stddev: 0.00012266",
            "group": "node",
            "extra": "mean: 770.13 usec\nrounds: 219"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 271.55205458948456,
            "unit": "iter/sec",
            "range": "stddev: 0.00048660",
            "group": "node",
            "extra": "mean: 3.6825 msec\nrounds: 159"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 244.43934796008858,
            "unit": "iter/sec",
            "range": "stddev: 0.00047707",
            "group": "node",
            "extra": "mean: 4.0910 msec\nrounds: 161"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 260.3268552570303,
            "unit": "iter/sec",
            "range": "stddev: 0.00048508",
            "group": "node",
            "extra": "mean: 3.8413 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 57.29628224625742,
            "unit": "iter/sec",
            "range": "stddev: 0.0013926",
            "group": "node",
            "extra": "mean: 17.453 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 53.79799901720639,
            "unit": "iter/sec",
            "range": "stddev: 0.0022363",
            "group": "node",
            "extra": "mean: 18.588 msec\nrounds: 100"
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
          "id": "ff7b9e630967a4aece8f7dd75c052366920cd94e",
          "message": "CI: skip the code tests if only docs have been touched (#4377)\n\nThis requires splitting the `pre-commit` and `tests` steps in separate workflows.",
          "timestamp": "2020-09-17T16:29:39+02:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/ff7b9e630967a4aece8f7dd75c052366920cd94e",
          "distinct": true,
          "tree_id": "b8041b87e944622fd71abeba4dd0bea3ad0a62e8"
        },
        "date": 1600353601753,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.052405369009012,
            "unit": "iter/sec",
            "range": "stddev: 0.059174",
            "group": "engine",
            "extra": "mean: 327.61 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.747493912702228,
            "unit": "iter/sec",
            "range": "stddev: 0.056818",
            "group": "engine",
            "extra": "mean: 1.3378 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.850002949786485,
            "unit": "iter/sec",
            "range": "stddev: 0.069062",
            "group": "engine",
            "extra": "mean: 1.1765 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.16472566455837992,
            "unit": "iter/sec",
            "range": "stddev: 0.12551",
            "group": "engine",
            "extra": "mean: 6.0707 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.19237622944704902,
            "unit": "iter/sec",
            "range": "stddev: 0.11696",
            "group": "engine",
            "extra": "mean: 5.1981 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.4664510400619792,
            "unit": "iter/sec",
            "range": "stddev: 0.015685",
            "group": "engine",
            "extra": "mean: 405.44 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.5815126219805515,
            "unit": "iter/sec",
            "range": "stddev: 0.082375",
            "group": "engine",
            "extra": "mean: 1.7197 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.6689434022017837,
            "unit": "iter/sec",
            "range": "stddev: 0.083968",
            "group": "engine",
            "extra": "mean: 1.4949 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.1488323377427367,
            "unit": "iter/sec",
            "range": "stddev: 0.18649",
            "group": "engine",
            "extra": "mean: 6.7190 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.17283093167484256,
            "unit": "iter/sec",
            "range": "stddev: 0.20175",
            "group": "engine",
            "extra": "mean: 5.7860 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.4785726531795005,
            "unit": "iter/sec",
            "range": "stddev: 0.047006",
            "group": "import-export",
            "extra": "mean: 403.46 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.2411517962782486,
            "unit": "iter/sec",
            "range": "stddev: 0.052841",
            "group": "import-export",
            "extra": "mean: 446.20 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 1.333923890193002,
            "unit": "iter/sec",
            "range": "stddev: 0.051356",
            "group": "import-export",
            "extra": "mean: 749.67 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 1.1955050683138466,
            "unit": "iter/sec",
            "range": "stddev: 0.068772",
            "group": "import-export",
            "extra": "mean: 836.47 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 863.1522040271751,
            "unit": "iter/sec",
            "range": "stddev: 0.00012213",
            "group": "node",
            "extra": "mean: 1.1585 msec\nrounds: 170"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 182.04592429154616,
            "unit": "iter/sec",
            "range": "stddev: 0.0010625",
            "group": "node",
            "extra": "mean: 5.4931 msec\nrounds: 115"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 171.84186285721626,
            "unit": "iter/sec",
            "range": "stddev: 0.0011531",
            "group": "node",
            "extra": "mean: 5.8193 msec\nrounds: 112"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 186.35474619194733,
            "unit": "iter/sec",
            "range": "stddev: 0.0012926",
            "group": "node",
            "extra": "mean: 5.3661 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 38.570897339961164,
            "unit": "iter/sec",
            "range": "stddev: 0.0023479",
            "group": "node",
            "extra": "mean: 25.926 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 39.8278047728269,
            "unit": "iter/sec",
            "range": "stddev: 0.0015426",
            "group": "node",
            "extra": "mean: 25.108 msec\nrounds: 100"
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
          "id": "9dfad2efbe9603957a54d0123a3cec2ee48b54bd",
          "message": "`CalcJob`: allow nested target paths for `local_copy_list` (#4373)\n\nIf a `CalcJob` would specify a `local_copy_list` containing an entry\r\nwhere the target remote path contains nested subdirectories, the\r\n`upload_calculation` would except unless all subdirectories would\r\nalready exist. To solve this, one could have added a transport call that\r\nwould create the directories if the target path is nested. However, this\r\nwould risk being very inefficient if there are many local copy list\r\ninstructions with relative path, where each would incurr a command over\r\nthe transport.\r\n\r\nInstead, we change the design and simply apply the local copy list\r\ninstructions to the sandbox folder on the local file system. This also\r\nat the same time allows us to get rid of the inefficient workaround of\r\nwriting the file to a temporary file, because the transport interface\r\ndoesn't accept filelike objects and the file repository does not expose\r\nfilepaths on the local file system.\r\n\r\nThe only additional thing to take care of is to make sure the files from\r\nthe local copy list do not end up in the repository of the node, which\r\nwas the whole point of the `local_copy_list`'s existence in the first\r\nplace. But this is solved by simply adding each file, that is added to\r\nthe sandbox, also to the `provenance_exclude_list`.",
          "timestamp": "2020-09-17T21:24:38+02:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/9dfad2efbe9603957a54d0123a3cec2ee48b54bd",
          "distinct": true,
          "tree_id": "34c4cb969fd8157bfee60e0c77a0fb2e9eceeb11"
        },
        "date": 1600371213400,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.5455546923220993,
            "unit": "iter/sec",
            "range": "stddev: 0.011465",
            "group": "engine",
            "extra": "mean: 282.04 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.8301167835386116,
            "unit": "iter/sec",
            "range": "stddev: 0.052039",
            "group": "engine",
            "extra": "mean: 1.2046 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.9184419849982657,
            "unit": "iter/sec",
            "range": "stddev: 0.052723",
            "group": "engine",
            "extra": "mean: 1.0888 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.18820800896578022,
            "unit": "iter/sec",
            "range": "stddev: 0.21967",
            "group": "engine",
            "extra": "mean: 5.3133 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.22276980710592312,
            "unit": "iter/sec",
            "range": "stddev: 0.079354",
            "group": "engine",
            "extra": "mean: 4.4889 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 3.011984989169322,
            "unit": "iter/sec",
            "range": "stddev: 0.0096648",
            "group": "engine",
            "extra": "mean: 332.01 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.6941568585359182,
            "unit": "iter/sec",
            "range": "stddev: 0.059039",
            "group": "engine",
            "extra": "mean: 1.4406 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.7885806318147882,
            "unit": "iter/sec",
            "range": "stddev: 0.060858",
            "group": "engine",
            "extra": "mean: 1.2681 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.1736456951142886,
            "unit": "iter/sec",
            "range": "stddev: 0.17612",
            "group": "engine",
            "extra": "mean: 5.7589 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.20675621390918036,
            "unit": "iter/sec",
            "range": "stddev: 0.11764",
            "group": "engine",
            "extra": "mean: 4.8366 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.9050800836924666,
            "unit": "iter/sec",
            "range": "stddev: 0.040693",
            "group": "import-export",
            "extra": "mean: 344.22 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.548746504740905,
            "unit": "iter/sec",
            "range": "stddev: 0.041815",
            "group": "import-export",
            "extra": "mean: 392.35 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 1.4747681562207522,
            "unit": "iter/sec",
            "range": "stddev: 0.053779",
            "group": "import-export",
            "extra": "mean: 678.07 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 1.404932341397106,
            "unit": "iter/sec",
            "range": "stddev: 0.034949",
            "group": "import-export",
            "extra": "mean: 711.78 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 948.4507739428419,
            "unit": "iter/sec",
            "range": "stddev: 0.00022510",
            "group": "node",
            "extra": "mean: 1.0544 msec\nrounds: 216"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 214.37453120620197,
            "unit": "iter/sec",
            "range": "stddev: 0.00049472",
            "group": "node",
            "extra": "mean: 4.6647 msec\nrounds: 146"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 198.40293242549149,
            "unit": "iter/sec",
            "range": "stddev: 0.00091640",
            "group": "node",
            "extra": "mean: 5.0402 msec\nrounds: 143"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 214.29977847396896,
            "unit": "iter/sec",
            "range": "stddev: 0.00077403",
            "group": "node",
            "extra": "mean: 4.6664 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 44.012183440297626,
            "unit": "iter/sec",
            "range": "stddev: 0.013871",
            "group": "node",
            "extra": "mean: 22.721 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 45.967644831061044,
            "unit": "iter/sec",
            "range": "stddev: 0.0043839",
            "group": "node",
            "extra": "mean: 21.754 msec\nrounds: 100"
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
          "id": "c6bca066106c8ee92178923ea3a0b6ab0b3657e2",
          "message": "Update citations in `README.md` and documentation landing page (#4371)\n\nThe second AiiDA paper was published in Scientific Data on September 8,\r\n2020. The suggested citations are updated, where the original AiiDA\r\npaper is kept to be cited when people use AiiDA with version before v1.0\r\nor if they reference the original ADES model.",
          "timestamp": "2020-09-17T22:54:58+02:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/c6bca066106c8ee92178923ea3a0b6ab0b3657e2",
          "distinct": true,
          "tree_id": "addd54026c8c291ac762ce912658ed8020e88a10"
        },
        "date": 1600376760010,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.2028089085083016,
            "unit": "iter/sec",
            "range": "stddev: 0.051854",
            "group": "engine",
            "extra": "mean: 312.23 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.7816444990930592,
            "unit": "iter/sec",
            "range": "stddev: 0.057633",
            "group": "engine",
            "extra": "mean: 1.2794 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.8777224506620797,
            "unit": "iter/sec",
            "range": "stddev: 0.057412",
            "group": "engine",
            "extra": "mean: 1.1393 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.16734201213002464,
            "unit": "iter/sec",
            "range": "stddev: 0.17991",
            "group": "engine",
            "extra": "mean: 5.9758 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.17931749201026376,
            "unit": "iter/sec",
            "range": "stddev: 0.26867",
            "group": "engine",
            "extra": "mean: 5.5767 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.2184465592851392,
            "unit": "iter/sec",
            "range": "stddev: 0.0099670",
            "group": "engine",
            "extra": "mean: 450.77 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.5210386847741257,
            "unit": "iter/sec",
            "range": "stddev: 0.062579",
            "group": "engine",
            "extra": "mean: 1.9192 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.5759746453049014,
            "unit": "iter/sec",
            "range": "stddev: 0.067281",
            "group": "engine",
            "extra": "mean: 1.7362 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.1349526267765222,
            "unit": "iter/sec",
            "range": "stddev: 0.54675",
            "group": "engine",
            "extra": "mean: 7.4100 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.16406929663790668,
            "unit": "iter/sec",
            "range": "stddev: 0.20675",
            "group": "engine",
            "extra": "mean: 6.0950 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.376770548902688,
            "unit": "iter/sec",
            "range": "stddev: 0.075646",
            "group": "import-export",
            "extra": "mean: 420.74 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.2243247144933167,
            "unit": "iter/sec",
            "range": "stddev: 0.011483",
            "group": "import-export",
            "extra": "mean: 449.57 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 1.2626605311587074,
            "unit": "iter/sec",
            "range": "stddev: 0.062371",
            "group": "import-export",
            "extra": "mean: 791.98 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 1.1383251510492631,
            "unit": "iter/sec",
            "range": "stddev: 0.074461",
            "group": "import-export",
            "extra": "mean: 878.48 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 852.6912189222295,
            "unit": "iter/sec",
            "range": "stddev: 0.00025554",
            "group": "node",
            "extra": "mean: 1.1728 msec\nrounds: 173"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 174.70754747703987,
            "unit": "iter/sec",
            "range": "stddev: 0.0012948",
            "group": "node",
            "extra": "mean: 5.7239 msec\nrounds: 106"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 157.62516150110454,
            "unit": "iter/sec",
            "range": "stddev: 0.0012624",
            "group": "node",
            "extra": "mean: 6.3442 msec\nrounds: 106"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 169.3372815472662,
            "unit": "iter/sec",
            "range": "stddev: 0.0011863",
            "group": "node",
            "extra": "mean: 5.9054 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 34.42463165676325,
            "unit": "iter/sec",
            "range": "stddev: 0.011567",
            "group": "node",
            "extra": "mean: 29.049 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 33.64746073286811,
            "unit": "iter/sec",
            "range": "stddev: 0.0038957",
            "group": "node",
            "extra": "mean: 29.720 msec\nrounds: 100"
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
          "id": "12be9ad0c5abae1cff3bc62f838432b5c5502aa3",
          "message": "Depedencies: remove upper limit and allow `numpy~=1.17` (#4378)\n\nThe limit was introduced in `f5d6cba2baf0e7ca69b742f7e76d8a8bbcca85ae`\r\nbecause of a broken pre-release. Now that a stable release is out, the\r\nrequirement is relax to allow newer versions as well. Note that we keep\r\nthe minimum requirement of `numpy==1.17` following AEP 003.\r\n\r\nOne change had to be applied in the code to make it compatible with newer\r\nversions of `numpy`. In the legacy kpoints implementation, the entries\r\nin `num_points` are of type `numpy.float64` for recent versions of\r\n`numpy`, but need to be integers so they can be used for indexing in\r\n`numpy.linspace()` calls.",
          "timestamp": "2020-09-19T11:16:21+02:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/12be9ad0c5abae1cff3bc62f838432b5c5502aa3",
          "distinct": true,
          "tree_id": "22e059003dee06efa0201a155395535159e1b1c4"
        },
        "date": 1600507556191,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.344800629974165,
            "unit": "iter/sec",
            "range": "stddev: 0.059721",
            "group": "engine",
            "extra": "mean: 298.97 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.8150232322841078,
            "unit": "iter/sec",
            "range": "stddev: 0.093079",
            "group": "engine",
            "extra": "mean: 1.2270 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.9344990177515895,
            "unit": "iter/sec",
            "range": "stddev: 0.065640",
            "group": "engine",
            "extra": "mean: 1.0701 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.18147474362099522,
            "unit": "iter/sec",
            "range": "stddev: 0.099536",
            "group": "engine",
            "extra": "mean: 5.5104 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.21063003020702353,
            "unit": "iter/sec",
            "range": "stddev: 0.12854",
            "group": "engine",
            "extra": "mean: 4.7477 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.696189056075647,
            "unit": "iter/sec",
            "range": "stddev: 0.0090902",
            "group": "engine",
            "extra": "mean: 370.89 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.6470522574638561,
            "unit": "iter/sec",
            "range": "stddev: 0.075124",
            "group": "engine",
            "extra": "mean: 1.5455 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.7389230067288999,
            "unit": "iter/sec",
            "range": "stddev: 0.064028",
            "group": "engine",
            "extra": "mean: 1.3533 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.15829912205053331,
            "unit": "iter/sec",
            "range": "stddev: 0.12401",
            "group": "engine",
            "extra": "mean: 6.3172 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.1882210115246498,
            "unit": "iter/sec",
            "range": "stddev: 0.098882",
            "group": "engine",
            "extra": "mean: 5.3129 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.842851159372997,
            "unit": "iter/sec",
            "range": "stddev: 0.0085140",
            "group": "import-export",
            "extra": "mean: 351.76 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.450170263577049,
            "unit": "iter/sec",
            "range": "stddev: 0.059245",
            "group": "import-export",
            "extra": "mean: 408.13 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 1.5353854103269027,
            "unit": "iter/sec",
            "range": "stddev: 0.058613",
            "group": "import-export",
            "extra": "mean: 651.30 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 1.435866097739431,
            "unit": "iter/sec",
            "range": "stddev: 0.065159",
            "group": "import-export",
            "extra": "mean: 696.44 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 1056.322600629029,
            "unit": "iter/sec",
            "range": "stddev: 0.00027044",
            "group": "node",
            "extra": "mean: 946.68 usec\nrounds: 205"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 230.05346958141845,
            "unit": "iter/sec",
            "range": "stddev: 0.00022683",
            "group": "node",
            "extra": "mean: 4.3468 msec\nrounds: 137"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 208.95354931707183,
            "unit": "iter/sec",
            "range": "stddev: 0.00061886",
            "group": "node",
            "extra": "mean: 4.7858 msec\nrounds: 119"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 232.45866614676513,
            "unit": "iter/sec",
            "range": "stddev: 0.00018041",
            "group": "node",
            "extra": "mean: 4.3018 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 43.49050620776782,
            "unit": "iter/sec",
            "range": "stddev: 0.0020977",
            "group": "node",
            "extra": "mean: 22.994 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 42.8729603029972,
            "unit": "iter/sec",
            "range": "stddev: 0.0045629",
            "group": "node",
            "extra": "mean: 23.325 msec\nrounds: 100"
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
          "id": "8dec3265835dd9f335aaa43cfe5537cb5409ccc3",
          "message": "ORM: move attributes/extras methods of frontend node to mixins\n\nMove all methods related to attributes and extras from the frontend\n`Node` class to separate mixin classes called `EntityAttributesMixin`\nand `EntityExtrasMixin`. This makes it easier to add these methods to\nother frontend entity classes and makes the code more maintainable.",
          "timestamp": "2020-09-22T11:12:38+02:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/8dec3265835dd9f335aaa43cfe5537cb5409ccc3",
          "distinct": true,
          "tree_id": "01ead6eb7a823398ea56eb35279fe29baed056bc"
        },
        "date": 1600766439347,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.7030295562010602,
            "unit": "iter/sec",
            "range": "stddev: 0.062427",
            "group": "engine",
            "extra": "mean: 270.05 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 1.120622577274643,
            "unit": "iter/sec",
            "range": "stddev: 0.050711",
            "group": "engine",
            "extra": "mean: 892.36 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 1.218439677266332,
            "unit": "iter/sec",
            "range": "stddev: 0.045220",
            "group": "engine",
            "extra": "mean: 820.72 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.22309614567820368,
            "unit": "iter/sec",
            "range": "stddev: 0.15745",
            "group": "engine",
            "extra": "mean: 4.4824 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.2491372171634877,
            "unit": "iter/sec",
            "range": "stddev: 0.29888",
            "group": "engine",
            "extra": "mean: 4.0139 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 3.579066792084533,
            "unit": "iter/sec",
            "range": "stddev: 0.015163",
            "group": "engine",
            "extra": "mean: 279.40 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.8584676159402337,
            "unit": "iter/sec",
            "range": "stddev: 0.038263",
            "group": "engine",
            "extra": "mean: 1.1649 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.9690061138634571,
            "unit": "iter/sec",
            "range": "stddev: 0.052048",
            "group": "engine",
            "extra": "mean: 1.0320 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.19550823954641414,
            "unit": "iter/sec",
            "range": "stddev: 0.26278",
            "group": "engine",
            "extra": "mean: 5.1149 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.24091053173311136,
            "unit": "iter/sec",
            "range": "stddev: 0.089288",
            "group": "engine",
            "extra": "mean: 4.1509 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 3.5130177538369587,
            "unit": "iter/sec",
            "range": "stddev: 0.038747",
            "group": "import-export",
            "extra": "mean: 284.66 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.940944946859705,
            "unit": "iter/sec",
            "range": "stddev: 0.043883",
            "group": "import-export",
            "extra": "mean: 340.03 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 1.8597952638711188,
            "unit": "iter/sec",
            "range": "stddev: 0.056986",
            "group": "import-export",
            "extra": "mean: 537.69 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 1.413553046221311,
            "unit": "iter/sec",
            "range": "stddev: 0.32421",
            "group": "import-export",
            "extra": "mean: 707.44 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 1309.6910835772603,
            "unit": "iter/sec",
            "range": "stddev: 0.00013147",
            "group": "node",
            "extra": "mean: 763.54 usec\nrounds: 220"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 272.8825225344187,
            "unit": "iter/sec",
            "range": "stddev: 0.00043824",
            "group": "node",
            "extra": "mean: 3.6646 msec\nrounds: 178"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 266.4244854430115,
            "unit": "iter/sec",
            "range": "stddev: 0.00039161",
            "group": "node",
            "extra": "mean: 3.7534 msec\nrounds: 169"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 285.1663816940715,
            "unit": "iter/sec",
            "range": "stddev: 0.00047007",
            "group": "node",
            "extra": "mean: 3.5067 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 55.888049646260384,
            "unit": "iter/sec",
            "range": "stddev: 0.0023618",
            "group": "node",
            "extra": "mean: 17.893 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 55.96813395189252,
            "unit": "iter/sec",
            "range": "stddev: 0.0021034",
            "group": "node",
            "extra": "mean: 17.867 msec\nrounds: 100"
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
          "id": "93bde426fd0f083d3b9750beaa926acb4827c098",
          "message": "`CalcJob`: improve logging in `parse_scheduler_output` (#4370)\n\nThe level of the log that is fired if no detailed job info is available\r\nis changed from `WARNING` to `INFO`. Since not all schedulers implement\r\nthe feature of retrieving this detailed job info, such as the often used\r\n`DirectScheduler`, using a warning is not very apt. If the information\r\nis missing, nothing is necessarily wrong, so `INFO` is better suited.\r\n\r\nOn the contrary, if the `Scheduler.parse_output` excepts, that is grave\r\nand so its level is changed from a warning to an error.\r\n\r\nFinally, a new condition is added where the scheduler does implement the\r\nmethod to retrieve the detailed job info, but the command fails. In this\r\ncase, the return value will be non-zero. This value is now checked\r\nexplicitly and if the case, a info log is fired and the detailed job\r\ninfo is set to `None`, which will cause the parsing to be skipped. This\r\ncase can for example arise when using the `SlurmScheduler` plugin, which\r\ndoes implement the detailed job info feature, however, not all SLURM\r\ninstallations have the job accounting feature enabled, which is required\r\nby the plugin.",
          "timestamp": "2020-09-22T17:46:41+02:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/93bde426fd0f083d3b9750beaa926acb4827c098",
          "distinct": true,
          "tree_id": "022ffb9297511577b5e0e96793fe5b2a8d625f3a"
        },
        "date": 1600790214347,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.0156967107280144,
            "unit": "iter/sec",
            "range": "stddev: 0.053084",
            "group": "engine",
            "extra": "mean: 331.60 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.7479718598101721,
            "unit": "iter/sec",
            "range": "stddev: 0.041173",
            "group": "engine",
            "extra": "mean: 1.3369 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.8396441525914063,
            "unit": "iter/sec",
            "range": "stddev: 0.050649",
            "group": "engine",
            "extra": "mean: 1.1910 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.1673596092825779,
            "unit": "iter/sec",
            "range": "stddev: 0.082263",
            "group": "engine",
            "extra": "mean: 5.9752 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.18985153517643355,
            "unit": "iter/sec",
            "range": "stddev: 0.098723",
            "group": "engine",
            "extra": "mean: 5.2673 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.460516457788508,
            "unit": "iter/sec",
            "range": "stddev: 0.013842",
            "group": "engine",
            "extra": "mean: 406.42 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.5948234862732077,
            "unit": "iter/sec",
            "range": "stddev: 0.084459",
            "group": "engine",
            "extra": "mean: 1.6812 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.7062916898240174,
            "unit": "iter/sec",
            "range": "stddev: 0.054010",
            "group": "engine",
            "extra": "mean: 1.4158 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.15466720013800928,
            "unit": "iter/sec",
            "range": "stddev: 0.12108",
            "group": "engine",
            "extra": "mean: 6.4655 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.17493542815401686,
            "unit": "iter/sec",
            "range": "stddev: 0.11452",
            "group": "engine",
            "extra": "mean: 5.7164 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.3740988596851635,
            "unit": "iter/sec",
            "range": "stddev: 0.050302",
            "group": "import-export",
            "extra": "mean: 421.21 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.153937420427235,
            "unit": "iter/sec",
            "range": "stddev: 0.057080",
            "group": "import-export",
            "extra": "mean: 464.27 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 1.3004999254256309,
            "unit": "iter/sec",
            "range": "stddev: 0.065728",
            "group": "import-export",
            "extra": "mean: 768.94 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 1.235735172737607,
            "unit": "iter/sec",
            "range": "stddev: 0.059276",
            "group": "import-export",
            "extra": "mean: 809.23 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 895.8183303361661,
            "unit": "iter/sec",
            "range": "stddev: 0.00016324",
            "group": "node",
            "extra": "mean: 1.1163 msec\nrounds: 200"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 198.27100817629213,
            "unit": "iter/sec",
            "range": "stddev: 0.00038466",
            "group": "node",
            "extra": "mean: 5.0436 msec\nrounds: 130"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 188.86150629328972,
            "unit": "iter/sec",
            "range": "stddev: 0.00036439",
            "group": "node",
            "extra": "mean: 5.2949 msec\nrounds: 131"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 198.7673735506204,
            "unit": "iter/sec",
            "range": "stddev: 0.00048060",
            "group": "node",
            "extra": "mean: 5.0310 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 39.59031573875069,
            "unit": "iter/sec",
            "range": "stddev: 0.0054481",
            "group": "node",
            "extra": "mean: 25.259 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 38.40221877574525,
            "unit": "iter/sec",
            "range": "stddev: 0.0018626",
            "group": "node",
            "extra": "mean: 26.040 msec\nrounds: 100"
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
          "id": "aa3b009870a674b11e66e46c49b6246114773a32",
          "message": "`BaseRestartWorkChain`: do not run `process_handler` when `exit_codes=[]`. (#4380)\n\nWhen a `process_handler` explicitly gets passed an empty `exit_codes`\r\nlist, it would previously always run. This is now changed to not run the\r\nhandler instead.\r\n\r\nThe reason for this change is that it is more consistent with the\r\nsemantics of passing a list of exit codes, where it only triggers if the\r\nchild process has any of the listed exit codes.",
          "timestamp": "2020-09-23T08:59:19+02:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/aa3b009870a674b11e66e46c49b6246114773a32",
          "distinct": true,
          "tree_id": "cde9ac6e7706ddca3ce79243987469df56b25e4d"
        },
        "date": 1600845072352,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 2.7400321362806497,
            "unit": "iter/sec",
            "range": "stddev: 0.026817",
            "group": "engine",
            "extra": "mean: 364.96 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.6395450825166159,
            "unit": "iter/sec",
            "range": "stddev: 0.074271",
            "group": "engine",
            "extra": "mean: 1.5636 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.7101962135972236,
            "unit": "iter/sec",
            "range": "stddev: 0.10311",
            "group": "engine",
            "extra": "mean: 1.4081 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.14521332559232478,
            "unit": "iter/sec",
            "range": "stddev: 0.17071",
            "group": "engine",
            "extra": "mean: 6.8864 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.16146232502822705,
            "unit": "iter/sec",
            "range": "stddev: 0.18342",
            "group": "engine",
            "extra": "mean: 6.1934 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 1.9794551079575964,
            "unit": "iter/sec",
            "range": "stddev: 0.061633",
            "group": "engine",
            "extra": "mean: 505.19 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.4941873150085818,
            "unit": "iter/sec",
            "range": "stddev: 0.085180",
            "group": "engine",
            "extra": "mean: 2.0235 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.5590773274170094,
            "unit": "iter/sec",
            "range": "stddev: 0.098706",
            "group": "engine",
            "extra": "mean: 1.7887 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.12653535806505994,
            "unit": "iter/sec",
            "range": "stddev: 0.18258",
            "group": "engine",
            "extra": "mean: 7.9029 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.14760305277484023,
            "unit": "iter/sec",
            "range": "stddev: 0.24395",
            "group": "engine",
            "extra": "mean: 6.7749 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.1195282283983152,
            "unit": "iter/sec",
            "range": "stddev: 0.044057",
            "group": "import-export",
            "extra": "mean: 471.80 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.0407826258515156,
            "unit": "iter/sec",
            "range": "stddev: 0.024443",
            "group": "import-export",
            "extra": "mean: 490.01 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 1.153345480362809,
            "unit": "iter/sec",
            "range": "stddev: 0.076998",
            "group": "import-export",
            "extra": "mean: 867.04 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 1.0737893335187132,
            "unit": "iter/sec",
            "range": "stddev: 0.056197",
            "group": "import-export",
            "extra": "mean: 931.28 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 707.1480155975796,
            "unit": "iter/sec",
            "range": "stddev: 0.00071814",
            "group": "node",
            "extra": "mean: 1.4141 msec\nrounds: 183"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 171.32282001936946,
            "unit": "iter/sec",
            "range": "stddev: 0.0010015",
            "group": "node",
            "extra": "mean: 5.8369 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 163.47907791027353,
            "unit": "iter/sec",
            "range": "stddev: 0.0010944",
            "group": "node",
            "extra": "mean: 6.1170 msec\nrounds: 105"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 162.6524804383577,
            "unit": "iter/sec",
            "range": "stddev: 0.0015725",
            "group": "node",
            "extra": "mean: 6.1481 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 33.88994732974318,
            "unit": "iter/sec",
            "range": "stddev: 0.0044131",
            "group": "node",
            "extra": "mean: 29.507 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 32.832168481427644,
            "unit": "iter/sec",
            "range": "stddev: 0.018752",
            "group": "node",
            "extra": "mean: 30.458 msec\nrounds: 100"
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
          "id": "ac0d55995ef6620e61ba1bb25bc1df5d23ff1778",
          "message": "Prepare the code for the new repository implementation (#4344)\n\nIn `v2.0.0`, the new repository implementation will be shipped, that\r\ndespite our best efforts, requires some slight backwards-incompatible\r\nchanges to the interface. The envisioned changes are translated as\r\ndeprecation warnings:\r\n\r\n * `FileType`: `aiida.orm.utils.repository` ->`aiida.repository.common`\r\n * `File`: `aiida.orm.utils.repository` ->`aiida.repository.common`\r\n * `File`: changed from namedtuple to class\r\n * `File`: iteration is deprecated\r\n * `File`: `type` attribute -> `file_type`\r\n * `Node.put_object_from_tree`: `path` -> `filepath`\r\n * `Node.put_object_from_file`: `path` -> `filepath`\r\n * `Node.put_object_from_tree`: `key` -> `path`\r\n * `Node.put_object_from_file`: `key` -> `path`\r\n * `Node.put_object_from_filelike`: `key` -> `path`\r\n * `Node.get_object`: `key` -> `path`\r\n * `Node.get_object_content`: `key` -> `path`\r\n * `Node.open`: `key` -> `path`\r\n * `Node.list_objects`: `key` -> `path`\r\n * `Node.list_object_names`: `key` -> `path`\r\n * `SinglefileData.open`: `key` -> `path`\r\n * Deprecated use of `Node.open` without context manager\r\n * Deprecated any other mode than `r` and `rb` in the methods:\r\n    o `Node.open`\r\n    o `Node.get_object_content`\r\n * Deprecated `contents_only` in `put_object_from_tree`\r\n * Deprecated `force` argument in\r\n    o `Node.put_object_from_tree`\r\n    o `Node.put_object_from_file`\r\n    o `Node.put_object_from_filelike`\r\n    o `Node.delete_object`\r\n\r\nThe special case is the `Repository` class of the internal module\r\n`aiida.orm.utils.repository`. Even though it is not part of the public\r\nAPI, plugins may have been using it. To allow deprecation warnings to be\r\nprinted when the module or class is used, we move the content to a\r\nmirror module `aiida.orm.utils._repository`, that is then used\r\ninternally, and the original module has the deprecation warning. This\r\nway clients will see the warning if they use it, but use in `aiida-core`\r\nwill not trigger them. Since there won't be a replacement for this class\r\nin the new implementation, it can also not be replaced or forwarded.",
          "timestamp": "2020-09-23T11:33:51+02:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/ac0d55995ef6620e61ba1bb25bc1df5d23ff1778",
          "distinct": true,
          "tree_id": "51b4c19e8fbbe39ce6b68033fd9a518beb2868f5"
        },
        "date": 1600854231119,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.2661096035416692,
            "unit": "iter/sec",
            "range": "stddev: 0.051293",
            "group": "engine",
            "extra": "mean: 306.17 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.8231333598993732,
            "unit": "iter/sec",
            "range": "stddev: 0.044388",
            "group": "engine",
            "extra": "mean: 1.2149 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.9124880027959416,
            "unit": "iter/sec",
            "range": "stddev: 0.071459",
            "group": "engine",
            "extra": "mean: 1.0959 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.17395258584157772,
            "unit": "iter/sec",
            "range": "stddev: 0.10657",
            "group": "engine",
            "extra": "mean: 5.7487 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.19968134656624675,
            "unit": "iter/sec",
            "range": "stddev: 0.12060",
            "group": "engine",
            "extra": "mean: 5.0080 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.6677996448936363,
            "unit": "iter/sec",
            "range": "stddev: 0.020160",
            "group": "engine",
            "extra": "mean: 374.84 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.6404791588344926,
            "unit": "iter/sec",
            "range": "stddev: 0.067057",
            "group": "engine",
            "extra": "mean: 1.5613 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.7337289373824082,
            "unit": "iter/sec",
            "range": "stddev: 0.053662",
            "group": "engine",
            "extra": "mean: 1.3629 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.1547052148724866,
            "unit": "iter/sec",
            "range": "stddev: 0.11792",
            "group": "engine",
            "extra": "mean: 6.4639 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.17983024048927493,
            "unit": "iter/sec",
            "range": "stddev: 0.12186",
            "group": "engine",
            "extra": "mean: 5.5608 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.4698600025205897,
            "unit": "iter/sec",
            "range": "stddev: 0.044540",
            "group": "import-export",
            "extra": "mean: 404.88 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.197152625322471,
            "unit": "iter/sec",
            "range": "stddev: 0.051664",
            "group": "import-export",
            "extra": "mean: 455.13 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 1.3251625051556375,
            "unit": "iter/sec",
            "range": "stddev: 0.068518",
            "group": "import-export",
            "extra": "mean: 754.62 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 1.2266824630329332,
            "unit": "iter/sec",
            "range": "stddev: 0.050193",
            "group": "import-export",
            "extra": "mean: 815.21 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 918.9177475541755,
            "unit": "iter/sec",
            "range": "stddev: 0.00029877",
            "group": "node",
            "extra": "mean: 1.0882 msec\nrounds: 182"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 189.4843943629555,
            "unit": "iter/sec",
            "range": "stddev: 0.00060897",
            "group": "node",
            "extra": "mean: 5.2775 msec\nrounds: 125"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 184.164390772691,
            "unit": "iter/sec",
            "range": "stddev: 0.0011616",
            "group": "node",
            "extra": "mean: 5.4299 msec\nrounds: 121"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 193.69155364651922,
            "unit": "iter/sec",
            "range": "stddev: 0.00050026",
            "group": "node",
            "extra": "mean: 5.1628 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 39.84844066392351,
            "unit": "iter/sec",
            "range": "stddev: 0.0040007",
            "group": "node",
            "extra": "mean: 25.095 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 40.45460645548725,
            "unit": "iter/sec",
            "range": "stddev: 0.0020732",
            "group": "node",
            "extra": "mean: 24.719 msec\nrounds: 100"
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
          "id": "26f14ae0c352bfe7b7f3bd0282291831b71320ed",
          "message": "`Group`: add support for setting extras on groups (#4328)\n\nThe `DbGroup` database models get a new JSONB column `extras` which will\r\nfunction just like the extras of nodes. They will allow setting mutable\r\nextras as long as they are JSON-serializable.\r\n\r\nThe default is set to an empty dictionary that prevents the ORM from\r\nhaving to deal with null values. In addition, this keeps in line with\r\nthe current design of other database models. Since the default is one\r\ndefined on the ORM and not the database schema, we also explicitly mark\r\nthe column as non-nullable. Otherwise it would be possible to still\r\nstore rows in the database with null values.\r\n\r\nTo add the functionality of setting, getting and deleting the extras to\r\nthe backend end frontend `Group` ORM classes, the corresponding mixin\r\nclasses are added. The functionality for the `BackendGroup` was already\r\naccidentally added in a previous commit `65389f4958b9b111756450ea77e2`\r\nso only the frontend is touched here.",
          "timestamp": "2020-09-23T12:59:46+02:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/26f14ae0c352bfe7b7f3bd0282291831b71320ed",
          "distinct": true,
          "tree_id": "85a2405b0ee69ac87acfed101a8ec0bb72a6d3b8"
        },
        "date": 1600859396143,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.4302356248300923,
            "unit": "iter/sec",
            "range": "stddev: 0.0074944",
            "group": "engine",
            "extra": "mean: 291.53 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.8126340660318903,
            "unit": "iter/sec",
            "range": "stddev: 0.050270",
            "group": "engine",
            "extra": "mean: 1.2306 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.9230971927007113,
            "unit": "iter/sec",
            "range": "stddev: 0.037813",
            "group": "engine",
            "extra": "mean: 1.0833 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.17445626391222777,
            "unit": "iter/sec",
            "range": "stddev: 0.11566",
            "group": "engine",
            "extra": "mean: 5.7321 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.1993606040121676,
            "unit": "iter/sec",
            "range": "stddev: 0.099712",
            "group": "engine",
            "extra": "mean: 5.0160 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.65641547293452,
            "unit": "iter/sec",
            "range": "stddev: 0.013526",
            "group": "engine",
            "extra": "mean: 376.45 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.6370538281894426,
            "unit": "iter/sec",
            "range": "stddev: 0.050883",
            "group": "engine",
            "extra": "mean: 1.5697 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.7097488931014659,
            "unit": "iter/sec",
            "range": "stddev: 0.077810",
            "group": "engine",
            "extra": "mean: 1.4089 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.1539842450645789,
            "unit": "iter/sec",
            "range": "stddev: 0.13163",
            "group": "engine",
            "extra": "mean: 6.4942 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.18303375403833308,
            "unit": "iter/sec",
            "range": "stddev: 0.12381",
            "group": "engine",
            "extra": "mean: 5.4635 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.6893293540883456,
            "unit": "iter/sec",
            "range": "stddev: 0.052074",
            "group": "import-export",
            "extra": "mean: 371.84 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 1.6775155171530458,
            "unit": "iter/sec",
            "range": "stddev: 0.050146",
            "group": "import-export",
            "extra": "mean: 596.12 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 1.431096357192478,
            "unit": "iter/sec",
            "range": "stddev: 0.078892",
            "group": "import-export",
            "extra": "mean: 698.76 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 1.409257767457854,
            "unit": "iter/sec",
            "range": "stddev: 0.044240",
            "group": "import-export",
            "extra": "mean: 709.59 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 957.5756900250685,
            "unit": "iter/sec",
            "range": "stddev: 0.00049994",
            "group": "node",
            "extra": "mean: 1.0443 msec\nrounds: 194"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 211.24479736188977,
            "unit": "iter/sec",
            "range": "stddev: 0.0019472",
            "group": "node",
            "extra": "mean: 4.7338 msec\nrounds: 124"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 204.3716865320632,
            "unit": "iter/sec",
            "range": "stddev: 0.00030712",
            "group": "node",
            "extra": "mean: 4.8930 msec\nrounds: 113"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 212.0378775731471,
            "unit": "iter/sec",
            "range": "stddev: 0.00075805",
            "group": "node",
            "extra": "mean: 4.7161 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 39.4515760975371,
            "unit": "iter/sec",
            "range": "stddev: 0.016583",
            "group": "node",
            "extra": "mean: 25.348 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 40.167882193845465,
            "unit": "iter/sec",
            "range": "stddev: 0.0084700",
            "group": "node",
            "extra": "mean: 24.896 msec\nrounds: 100"
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
          "id": "f2f6e2f89580eb824c4175703718a07a2d4b0bee",
          "message": "`SshTransport` : refactor interface to simplify subclassing (#4363)\n\nThe `SshTransport` transport plugin is refactored slightly to make it\r\neasier for sublcasses to adapt its behavior. Specifically:\r\n\r\n * Add simple wrappers around SFTP calls (stat, lstat and symlink) such\r\n   that they can be overriden in subclasses, for example if SFTP is not\r\n   available and pure SSH needs to be used.\r\n * New method to initialize file transport separately. Also adds error\r\n   checking for SFTP initialization, with an explicit message if it\r\n   fails to launch, and a possible solution.\r\n * Add `_MAX_EXEC_COMMAND_LOG_SIZE` class attribute that can be used to\r\n   limit the length of the debug message containing the command that is\r\n   executed in `_exec_command_internal`, which can grow very large.",
          "timestamp": "2020-09-23T13:30:27+02:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/f2f6e2f89580eb824c4175703718a07a2d4b0bee",
          "distinct": true,
          "tree_id": "db0def820c8c26bed6a0d0758d5f32ae290709dd"
        },
        "date": 1600861204942,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.4872328112254065,
            "unit": "iter/sec",
            "range": "stddev: 0.0054087",
            "group": "engine",
            "extra": "mean: 286.76 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.8227769238410116,
            "unit": "iter/sec",
            "range": "stddev: 0.051610",
            "group": "engine",
            "extra": "mean: 1.2154 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.9362135514457747,
            "unit": "iter/sec",
            "range": "stddev: 0.043865",
            "group": "engine",
            "extra": "mean: 1.0681 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.18191158975152025,
            "unit": "iter/sec",
            "range": "stddev: 0.078793",
            "group": "engine",
            "extra": "mean: 5.4972 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.20921866364499264,
            "unit": "iter/sec",
            "range": "stddev: 0.090692",
            "group": "engine",
            "extra": "mean: 4.7797 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.6373847869895197,
            "unit": "iter/sec",
            "range": "stddev: 0.061960",
            "group": "engine",
            "extra": "mean: 379.16 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.6580874415136518,
            "unit": "iter/sec",
            "range": "stddev: 0.055066",
            "group": "engine",
            "extra": "mean: 1.5196 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.725290342608955,
            "unit": "iter/sec",
            "range": "stddev: 0.068233",
            "group": "engine",
            "extra": "mean: 1.3788 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.16127534684847522,
            "unit": "iter/sec",
            "range": "stddev: 0.10272",
            "group": "engine",
            "extra": "mean: 6.2006 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.18878305092412084,
            "unit": "iter/sec",
            "range": "stddev: 0.095174",
            "group": "engine",
            "extra": "mean: 5.2971 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.59009895731433,
            "unit": "iter/sec",
            "range": "stddev: 0.014467",
            "group": "import-export",
            "extra": "mean: 386.09 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.247592987770113,
            "unit": "iter/sec",
            "range": "stddev: 0.054102",
            "group": "import-export",
            "extra": "mean: 444.92 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 1.3706415969569177,
            "unit": "iter/sec",
            "range": "stddev: 0.060172",
            "group": "import-export",
            "extra": "mean: 729.59 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 1.2787441324977595,
            "unit": "iter/sec",
            "range": "stddev: 0.053294",
            "group": "import-export",
            "extra": "mean: 782.02 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 967.5848461275376,
            "unit": "iter/sec",
            "range": "stddev: 0.00014306",
            "group": "node",
            "extra": "mean: 1.0335 msec\nrounds: 206"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 192.03040818484325,
            "unit": "iter/sec",
            "range": "stddev: 0.0028007",
            "group": "node",
            "extra": "mean: 5.2075 msec\nrounds: 129"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 194.42336703016406,
            "unit": "iter/sec",
            "range": "stddev: 0.00046126",
            "group": "node",
            "extra": "mean: 5.1434 msec\nrounds: 131"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 204.23494140345483,
            "unit": "iter/sec",
            "range": "stddev: 0.00053720",
            "group": "node",
            "extra": "mean: 4.8963 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 41.759398317365644,
            "unit": "iter/sec",
            "range": "stddev: 0.0031873",
            "group": "node",
            "extra": "mean: 23.947 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 38.98115193944446,
            "unit": "iter/sec",
            "range": "stddev: 0.016571",
            "group": "node",
            "extra": "mean: 25.653 msec\nrounds: 100"
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
          "id": "0b155a518327b6e904e1424956bdb7d7103251fc",
          "message": "Remove duplicated migration for SqlAlchemy (#4390)\n\nThe `0edcdd5a30f0_add_extras_to_group.py` migration is a duplicate of\r\n`0edcdd5a30f0_dbgroup_extras.py` and was accidentally committed in\r\ncommit `26f14ae0c352bfe7b7f3bd0282291831b71320ed`. The migration is\r\nexactly the same, including the revision numbers, except the human\r\nreadable part was changed.",
          "timestamp": "2020-09-23T23:04:18+02:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/0b155a518327b6e904e1424956bdb7d7103251fc",
          "distinct": true,
          "tree_id": "372544ccca48d0d4cd8b60579682bbf526cea04c"
        },
        "date": 1600895593277,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.965658631946454,
            "unit": "iter/sec",
            "range": "stddev: 0.0094131",
            "group": "engine",
            "extra": "mean: 252.16 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.9289019242789848,
            "unit": "iter/sec",
            "range": "stddev: 0.052339",
            "group": "engine",
            "extra": "mean: 1.0765 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 1.0268713452659728,
            "unit": "iter/sec",
            "range": "stddev: 0.062703",
            "group": "engine",
            "extra": "mean: 973.83 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.19347979944031996,
            "unit": "iter/sec",
            "range": "stddev: 0.068984",
            "group": "engine",
            "extra": "mean: 5.1685 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.22366130297262857,
            "unit": "iter/sec",
            "range": "stddev: 0.084774",
            "group": "engine",
            "extra": "mean: 4.4710 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 3.0379137213066425,
            "unit": "iter/sec",
            "range": "stddev: 0.0059169",
            "group": "engine",
            "extra": "mean: 329.17 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.730076908821802,
            "unit": "iter/sec",
            "range": "stddev: 0.040879",
            "group": "engine",
            "extra": "mean: 1.3697 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.8100441224609842,
            "unit": "iter/sec",
            "range": "stddev: 0.047923",
            "group": "engine",
            "extra": "mean: 1.2345 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.17164555804352033,
            "unit": "iter/sec",
            "range": "stddev: 0.10961",
            "group": "engine",
            "extra": "mean: 5.8260 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.2045254388139894,
            "unit": "iter/sec",
            "range": "stddev: 0.089551",
            "group": "engine",
            "extra": "mean: 4.8894 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.9980358458098855,
            "unit": "iter/sec",
            "range": "stddev: 0.048602",
            "group": "import-export",
            "extra": "mean: 333.55 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.6909017313419152,
            "unit": "iter/sec",
            "range": "stddev: 0.018972",
            "group": "import-export",
            "extra": "mean: 371.62 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 1.6525996366492535,
            "unit": "iter/sec",
            "range": "stddev: 0.056203",
            "group": "import-export",
            "extra": "mean: 605.11 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 1.5552085926369592,
            "unit": "iter/sec",
            "range": "stddev: 0.044867",
            "group": "import-export",
            "extra": "mean: 643.00 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 1073.3231126720789,
            "unit": "iter/sec",
            "range": "stddev: 0.00015188",
            "group": "node",
            "extra": "mean: 931.69 usec\nrounds: 210"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 237.70444273728404,
            "unit": "iter/sec",
            "range": "stddev: 0.00041168",
            "group": "node",
            "extra": "mean: 4.2069 msec\nrounds: 137"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 213.12737543159813,
            "unit": "iter/sec",
            "range": "stddev: 0.00077463",
            "group": "node",
            "extra": "mean: 4.6920 msec\nrounds: 130"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 237.6710744513611,
            "unit": "iter/sec",
            "range": "stddev: 0.0010273",
            "group": "node",
            "extra": "mean: 4.2075 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 49.49853648937095,
            "unit": "iter/sec",
            "range": "stddev: 0.0015236",
            "group": "node",
            "extra": "mean: 20.203 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 47.79136404746673,
            "unit": "iter/sec",
            "range": "stddev: 0.0017095",
            "group": "node",
            "extra": "mean: 20.924 msec\nrounds: 100"
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
          "id": "59ebaf478511c13fc3e2de55569004fb88ab1dc7",
          "message": "Merge pull request #4385 from aiidateam/release/1.4.0\n\nRelease `v1.4.0`",
          "timestamp": "2020-09-24T11:08:58+02:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/59ebaf478511c13fc3e2de55569004fb88ab1dc7",
          "distinct": false,
          "tree_id": "ca4353750bc03ffd3567c8273f8b3f0690c255c8"
        },
        "date": 1600944451125,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.9516141725862104,
            "unit": "iter/sec",
            "range": "stddev: 0.013294",
            "group": "engine",
            "extra": "mean: 253.06 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.9385662880603617,
            "unit": "iter/sec",
            "range": "stddev: 0.047312",
            "group": "engine",
            "extra": "mean: 1.0655 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 1.0838041426216145,
            "unit": "iter/sec",
            "range": "stddev: 0.041602",
            "group": "engine",
            "extra": "mean: 922.68 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.20404479687895558,
            "unit": "iter/sec",
            "range": "stddev: 0.10597",
            "group": "engine",
            "extra": "mean: 4.9009 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.2348628931834495,
            "unit": "iter/sec",
            "range": "stddev: 0.094046",
            "group": "engine",
            "extra": "mean: 4.2578 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 3.1256301065177006,
            "unit": "iter/sec",
            "range": "stddev: 0.018899",
            "group": "engine",
            "extra": "mean: 319.94 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.7424044266613524,
            "unit": "iter/sec",
            "range": "stddev: 0.059148",
            "group": "engine",
            "extra": "mean: 1.3470 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.8392139282799628,
            "unit": "iter/sec",
            "range": "stddev: 0.045431",
            "group": "engine",
            "extra": "mean: 1.1916 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.18028360847057062,
            "unit": "iter/sec",
            "range": "stddev: 0.10216",
            "group": "engine",
            "extra": "mean: 5.5468 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.2146763101481509,
            "unit": "iter/sec",
            "range": "stddev: 0.072429",
            "group": "engine",
            "extra": "mean: 4.6582 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.737864500816126,
            "unit": "iter/sec",
            "range": "stddev: 0.044253",
            "group": "import-export",
            "extra": "mean: 365.25 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.4050570186337987,
            "unit": "iter/sec",
            "range": "stddev: 0.040713",
            "group": "import-export",
            "extra": "mean: 415.79 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 1.521400112492957,
            "unit": "iter/sec",
            "range": "stddev: 0.045769",
            "group": "import-export",
            "extra": "mean: 657.29 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 1.4108645119137342,
            "unit": "iter/sec",
            "range": "stddev: 0.049555",
            "group": "import-export",
            "extra": "mean: 708.79 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 993.0907216387504,
            "unit": "iter/sec",
            "range": "stddev: 0.00087580",
            "group": "node",
            "extra": "mean: 1.0070 msec\nrounds: 218"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 222.55021679851427,
            "unit": "iter/sec",
            "range": "stddev: 0.00092443",
            "group": "node",
            "extra": "mean: 4.4934 msec\nrounds: 148"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 208.96714748387123,
            "unit": "iter/sec",
            "range": "stddev: 0.00040965",
            "group": "node",
            "extra": "mean: 4.7854 msec\nrounds: 140"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 222.1033914787397,
            "unit": "iter/sec",
            "range": "stddev: 0.00056732",
            "group": "node",
            "extra": "mean: 4.5024 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 49.436483974974244,
            "unit": "iter/sec",
            "range": "stddev: 0.0010423",
            "group": "node",
            "extra": "mean: 20.228 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 48.36910806883929,
            "unit": "iter/sec",
            "range": "stddev: 0.0014076",
            "group": "node",
            "extra": "mean: 20.674 msec\nrounds: 100"
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
          "id": "559abbaab690bc7f94c84ece63ad4810500592bf",
          "message": "Drop support for Python 3.5 (#4386)\n\nPython 3.5 is EOL as of September 13 2020. CI testing will now only be\r\ndone against Python 3.6 and 3.8.",
          "timestamp": "2020-09-24T14:51:59+02:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/559abbaab690bc7f94c84ece63ad4810500592bf",
          "distinct": true,
          "tree_id": "4978f4074832a728936394b0c29d7852548fb639"
        },
        "date": 1600952465709,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.8681304328258252,
            "unit": "iter/sec",
            "range": "stddev: 0.0014731",
            "group": "engine",
            "extra": "mean: 258.52 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.9043850754464667,
            "unit": "iter/sec",
            "range": "stddev: 0.040908",
            "group": "engine",
            "extra": "mean: 1.1057 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 1.027099357984297,
            "unit": "iter/sec",
            "range": "stddev: 0.044097",
            "group": "engine",
            "extra": "mean: 973.62 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.18863337340147926,
            "unit": "iter/sec",
            "range": "stddev: 0.066686",
            "group": "engine",
            "extra": "mean: 5.3013 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.21826287262824348,
            "unit": "iter/sec",
            "range": "stddev: 0.088448",
            "group": "engine",
            "extra": "mean: 4.5816 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.908154626276631,
            "unit": "iter/sec",
            "range": "stddev: 0.048141",
            "group": "engine",
            "extra": "mean: 343.86 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.706228755935879,
            "unit": "iter/sec",
            "range": "stddev: 0.041721",
            "group": "engine",
            "extra": "mean: 1.4160 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.7892061667262048,
            "unit": "iter/sec",
            "range": "stddev: 0.070545",
            "group": "engine",
            "extra": "mean: 1.2671 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.1671465367992935,
            "unit": "iter/sec",
            "range": "stddev: 0.12675",
            "group": "engine",
            "extra": "mean: 5.9828 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.2002230963185479,
            "unit": "iter/sec",
            "range": "stddev: 0.083352",
            "group": "engine",
            "extra": "mean: 4.9944 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.866243775534499,
            "unit": "iter/sec",
            "range": "stddev: 0.042947",
            "group": "import-export",
            "extra": "mean: 348.89 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.623446278862129,
            "unit": "iter/sec",
            "range": "stddev: 0.0056094",
            "group": "import-export",
            "extra": "mean: 381.18 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 1.5712611204101221,
            "unit": "iter/sec",
            "range": "stddev: 0.049938",
            "group": "import-export",
            "extra": "mean: 636.43 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 1.4990370193682627,
            "unit": "iter/sec",
            "range": "stddev: 0.042624",
            "group": "import-export",
            "extra": "mean: 667.09 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 1052.2145430782216,
            "unit": "iter/sec",
            "range": "stddev: 0.000084884",
            "group": "node",
            "extra": "mean: 950.38 usec\nrounds: 208"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 231.53023304626313,
            "unit": "iter/sec",
            "range": "stddev: 0.00035847",
            "group": "node",
            "extra": "mean: 4.3191 msec\nrounds: 135"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 212.32859589479642,
            "unit": "iter/sec",
            "range": "stddev: 0.00048500",
            "group": "node",
            "extra": "mean: 4.7097 msec\nrounds: 138"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 237.80412225201053,
            "unit": "iter/sec",
            "range": "stddev: 0.00022202",
            "group": "node",
            "extra": "mean: 4.2051 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 47.32826799169289,
            "unit": "iter/sec",
            "range": "stddev: 0.0011849",
            "group": "node",
            "extra": "mean: 21.129 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 47.21004710777873,
            "unit": "iter/sec",
            "range": "stddev: 0.0012577",
            "group": "node",
            "extra": "mean: 21.182 msec\nrounds: 100"
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
          "id": "01845181740c2768ce3c31165a3f80e18d241a9f",
          "message": "`LinkManager`: fix inaccuracy in exception message for non-existent link  (#4388)\n\nThe link manager was always referring to an 'input link' while it should\r\ninstead refer on an 'input link label' or 'output link label' depending\r\non the value of the link direction, determined by the `self._incoming`\r\nattribute.",
          "timestamp": "2020-09-24T15:12:32+02:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/01845181740c2768ce3c31165a3f80e18d241a9f",
          "distinct": true,
          "tree_id": "c40d0d08cea7776aacbcd2ad9e998bd33e9532fc"
        },
        "date": 1600953784900,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.037073629162336,
            "unit": "iter/sec",
            "range": "stddev: 0.0081183",
            "group": "engine",
            "extra": "mean: 329.26 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.721144011777738,
            "unit": "iter/sec",
            "range": "stddev: 0.041535",
            "group": "engine",
            "extra": "mean: 1.3867 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.8051608776812673,
            "unit": "iter/sec",
            "range": "stddev: 0.050671",
            "group": "engine",
            "extra": "mean: 1.2420 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.1606729893147609,
            "unit": "iter/sec",
            "range": "stddev: 0.083215",
            "group": "engine",
            "extra": "mean: 6.2238 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.1865277648867661,
            "unit": "iter/sec",
            "range": "stddev: 0.11048",
            "group": "engine",
            "extra": "mean: 5.3611 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.521798580125874,
            "unit": "iter/sec",
            "range": "stddev: 0.014764",
            "group": "engine",
            "extra": "mean: 396.54 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.5687201252551628,
            "unit": "iter/sec",
            "range": "stddev: 0.055734",
            "group": "engine",
            "extra": "mean: 1.7583 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.6356642701370856,
            "unit": "iter/sec",
            "range": "stddev: 0.082456",
            "group": "engine",
            "extra": "mean: 1.5732 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.14476408564768992,
            "unit": "iter/sec",
            "range": "stddev: 0.11032",
            "group": "engine",
            "extra": "mean: 6.9078 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.17253939495577097,
            "unit": "iter/sec",
            "range": "stddev: 0.13045",
            "group": "engine",
            "extra": "mean: 5.7958 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.4727164240661157,
            "unit": "iter/sec",
            "range": "stddev: 0.054428",
            "group": "import-export",
            "extra": "mean: 404.41 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.198605661731646,
            "unit": "iter/sec",
            "range": "stddev: 0.058064",
            "group": "import-export",
            "extra": "mean: 454.83 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 1.240343633461937,
            "unit": "iter/sec",
            "range": "stddev: 0.086047",
            "group": "import-export",
            "extra": "mean: 806.23 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 1.207394798470984,
            "unit": "iter/sec",
            "range": "stddev: 0.050105",
            "group": "import-export",
            "extra": "mean: 828.23 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 898.1103629602962,
            "unit": "iter/sec",
            "range": "stddev: 0.00011277",
            "group": "node",
            "extra": "mean: 1.1134 msec\nrounds: 189"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 191.68751922404604,
            "unit": "iter/sec",
            "range": "stddev: 0.00051227",
            "group": "node",
            "extra": "mean: 5.2168 msec\nrounds: 117"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 173.50641039060153,
            "unit": "iter/sec",
            "range": "stddev: 0.00053406",
            "group": "node",
            "extra": "mean: 5.7635 msec\nrounds: 108"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 177.841471265698,
            "unit": "iter/sec",
            "range": "stddev: 0.0014515",
            "group": "node",
            "extra": "mean: 5.6230 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 35.327317345548984,
            "unit": "iter/sec",
            "range": "stddev: 0.017155",
            "group": "node",
            "extra": "mean: 28.307 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 39.79246190558662,
            "unit": "iter/sec",
            "range": "stddev: 0.0019673",
            "group": "node",
            "extra": "mean: 25.130 msec\nrounds: 100"
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
          "id": "5e1c6fd965bc8cdeea8bc0c37ee19a71de5986f3",
          "message": "Implement `next` and `iter` for the `Node.open` deprecation wrapper (#4399)\n\nThe return value of `Node.open` was wrapped in `WarnWhenNotEntered` in\r\n`aiida-core==1.4.0` in order to warn users that use the method without a\r\ncontext manager, which will start to raise in v2.0. Unfortunately, the\r\nraising came a little early as the wrapper does not implement the\r\n`__iter__` and `__next__` methods, which can be called by clients.\r\n\r\nAn example is `numpy.getfromtxt` which will notice the return value of\r\n`Node.open` is filelike and so will wrap it in `iter`. Without the\r\ncurrent fix, this raises a `TypeError`. The proper fix would be to\r\nforward all magic methods to the wrapped filelike object, but it is not\r\nclear how to do this.",
          "timestamp": "2020-09-25T15:56:53+02:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/5e1c6fd965bc8cdeea8bc0c37ee19a71de5986f3",
          "distinct": true,
          "tree_id": "0b57e939704231c31d3313b8a91d5065ed43c30f"
        },
        "date": 1601042771228,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 4.0243489077534775,
            "unit": "iter/sec",
            "range": "stddev: 0.0060400",
            "group": "engine",
            "extra": "mean: 248.49 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.8857906621182167,
            "unit": "iter/sec",
            "range": "stddev: 0.061550",
            "group": "engine",
            "extra": "mean: 1.1289 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 1.0262598767668643,
            "unit": "iter/sec",
            "range": "stddev: 0.041946",
            "group": "engine",
            "extra": "mean: 974.41 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.18862336085051715,
            "unit": "iter/sec",
            "range": "stddev: 0.11492",
            "group": "engine",
            "extra": "mean: 5.3016 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.22212874665956672,
            "unit": "iter/sec",
            "range": "stddev: 0.093918",
            "group": "engine",
            "extra": "mean: 4.5019 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.978710434189509,
            "unit": "iter/sec",
            "range": "stddev: 0.0039816",
            "group": "engine",
            "extra": "mean: 335.72 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.6751731902549416,
            "unit": "iter/sec",
            "range": "stddev: 0.092206",
            "group": "engine",
            "extra": "mean: 1.4811 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.76272278694613,
            "unit": "iter/sec",
            "range": "stddev: 0.072398",
            "group": "engine",
            "extra": "mean: 1.3111 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.1626590659762098,
            "unit": "iter/sec",
            "range": "stddev: 0.21807",
            "group": "engine",
            "extra": "mean: 6.1478 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.19699480108873185,
            "unit": "iter/sec",
            "range": "stddev: 0.087317",
            "group": "engine",
            "extra": "mean: 5.0763 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.847627880804877,
            "unit": "iter/sec",
            "range": "stddev: 0.047539",
            "group": "import-export",
            "extra": "mean: 351.17 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.521513689807495,
            "unit": "iter/sec",
            "range": "stddev: 0.050582",
            "group": "import-export",
            "extra": "mean: 396.59 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 1.5749717714166889,
            "unit": "iter/sec",
            "range": "stddev: 0.067028",
            "group": "import-export",
            "extra": "mean: 634.93 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 1.4667808625973713,
            "unit": "iter/sec",
            "range": "stddev: 0.054907",
            "group": "import-export",
            "extra": "mean: 681.77 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 799.5555558544725,
            "unit": "iter/sec",
            "range": "stddev: 0.00055682",
            "group": "node",
            "extra": "mean: 1.2507 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 204.01097521806844,
            "unit": "iter/sec",
            "range": "stddev: 0.0013623",
            "group": "node",
            "extra": "mean: 4.9017 msec\nrounds: 124"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 209.96058141449026,
            "unit": "iter/sec",
            "range": "stddev: 0.00041905",
            "group": "node",
            "extra": "mean: 4.7628 msec\nrounds: 129"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 234.24965849779701,
            "unit": "iter/sec",
            "range": "stddev: 0.00037981",
            "group": "node",
            "extra": "mean: 4.2689 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 45.37737466983685,
            "unit": "iter/sec",
            "range": "stddev: 0.0013616",
            "group": "node",
            "extra": "mean: 22.037 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 43.28335076589106,
            "unit": "iter/sec",
            "range": "stddev: 0.010774",
            "group": "node",
            "extra": "mean: 23.104 msec\nrounds: 100"
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
          "id": "dac81560647b2ffaa170ee87f673bd9f89db2b41",
          "message": "Dependencies: increase minimum version requirement `plumpy~=0.15.1` (#4398)\n\nThe patch release of `plumpy` comes with a simple fix that will prevent\r\nthe printing of many warnings when running processes. So although not\r\ncritical, it does improve user experience.",
          "timestamp": "2020-09-25T16:20:33+02:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/dac81560647b2ffaa170ee87f673bd9f89db2b41",
          "distinct": true,
          "tree_id": "f656192bf7be5c9d1c2e9f660333cbecf1ad8430"
        },
        "date": 1601044222671,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.669905829654885,
            "unit": "iter/sec",
            "range": "stddev: 0.0056207",
            "group": "engine",
            "extra": "mean: 272.49 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.8417478626861179,
            "unit": "iter/sec",
            "range": "stddev: 0.089953",
            "group": "engine",
            "extra": "mean: 1.1880 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.9807331042073577,
            "unit": "iter/sec",
            "range": "stddev: 0.036057",
            "group": "engine",
            "extra": "mean: 1.0196 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.18704750621962976,
            "unit": "iter/sec",
            "range": "stddev: 0.088809",
            "group": "engine",
            "extra": "mean: 5.3462 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.21036057521658738,
            "unit": "iter/sec",
            "range": "stddev: 0.13603",
            "group": "engine",
            "extra": "mean: 4.7537 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.824128220509228,
            "unit": "iter/sec",
            "range": "stddev: 0.016226",
            "group": "engine",
            "extra": "mean: 354.09 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.6853108626018104,
            "unit": "iter/sec",
            "range": "stddev: 0.049738",
            "group": "engine",
            "extra": "mean: 1.4592 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.7456851553555938,
            "unit": "iter/sec",
            "range": "stddev: 0.063956",
            "group": "engine",
            "extra": "mean: 1.3410 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.16416547114191093,
            "unit": "iter/sec",
            "range": "stddev: 0.083491",
            "group": "engine",
            "extra": "mean: 6.0914 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.19593079376218764,
            "unit": "iter/sec",
            "range": "stddev: 0.12428",
            "group": "engine",
            "extra": "mean: 5.1038 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.499458306981134,
            "unit": "iter/sec",
            "range": "stddev: 0.044125",
            "group": "import-export",
            "extra": "mean: 400.09 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.275993574383098,
            "unit": "iter/sec",
            "range": "stddev: 0.045165",
            "group": "import-export",
            "extra": "mean: 439.37 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 1.4483398561663727,
            "unit": "iter/sec",
            "range": "stddev: 0.063412",
            "group": "import-export",
            "extra": "mean: 690.45 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 1.3158064190201906,
            "unit": "iter/sec",
            "range": "stddev: 0.067660",
            "group": "import-export",
            "extra": "mean: 759.99 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 972.0163346964948,
            "unit": "iter/sec",
            "range": "stddev: 0.00027615",
            "group": "node",
            "extra": "mean: 1.0288 msec\nrounds: 149"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 210.8694352641828,
            "unit": "iter/sec",
            "range": "stddev: 0.00073664",
            "group": "node",
            "extra": "mean: 4.7423 msec\nrounds: 138"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 197.9439340323539,
            "unit": "iter/sec",
            "range": "stddev: 0.00080545",
            "group": "node",
            "extra": "mean: 5.0519 msec\nrounds: 133"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 216.44201133013462,
            "unit": "iter/sec",
            "range": "stddev: 0.00045787",
            "group": "node",
            "extra": "mean: 4.6202 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 43.30620779141131,
            "unit": "iter/sec",
            "range": "stddev: 0.0026809",
            "group": "node",
            "extra": "mean: 23.091 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 38.38871422905097,
            "unit": "iter/sec",
            "range": "stddev: 0.017859",
            "group": "node",
            "extra": "mean: 26.049 msec\nrounds: 100"
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
          "id": "ff30ebdb8860dc69bcbfec5e7a19e8b6e15a4f42",
          "message": "`verdi setup`: forward broker defaults to interactive mode (#4405)\n\nThe options for the message broker configuration do define defaults,\r\nhowever, the interactive clones for `verdi setup`, which are defined in\r\n`aiida.cmdline.params.options.commands.setup` override the default with\r\nthe `contextual_default` which sets an empty default, unless it is taken\r\nfrom an existing profile. The result is that for new profiles, the\r\nbroker options do not specify a default, even though for most usecases\r\nthe defaults will be required. After the changes of this commit, the\r\nprompt of `verdi setup` will provide a default for all broker parameters\r\nso most users will simply have to press enter each time.",
          "timestamp": "2020-09-26T20:24:20+02:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/ff30ebdb8860dc69bcbfec5e7a19e8b6e15a4f42",
          "distinct": true,
          "tree_id": "7bb1be28e3269247b969133b649361fe0a808875"
        },
        "date": 1601145217578,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.658629669381976,
            "unit": "iter/sec",
            "range": "stddev: 0.0083069",
            "group": "engine",
            "extra": "mean: 273.33 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.8719311995927755,
            "unit": "iter/sec",
            "range": "stddev: 0.038544",
            "group": "engine",
            "extra": "mean: 1.1469 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.9895277734464488,
            "unit": "iter/sec",
            "range": "stddev: 0.034678",
            "group": "engine",
            "extra": "mean: 1.0106 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.18429473344770958,
            "unit": "iter/sec",
            "range": "stddev: 0.094902",
            "group": "engine",
            "extra": "mean: 5.4261 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.2128084300883462,
            "unit": "iter/sec",
            "range": "stddev: 0.087895",
            "group": "engine",
            "extra": "mean: 4.6991 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.9090599203035934,
            "unit": "iter/sec",
            "range": "stddev: 0.0083076",
            "group": "engine",
            "extra": "mean: 343.75 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.6809036788274678,
            "unit": "iter/sec",
            "range": "stddev: 0.061067",
            "group": "engine",
            "extra": "mean: 1.4686 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.7700768138260954,
            "unit": "iter/sec",
            "range": "stddev: 0.055037",
            "group": "engine",
            "extra": "mean: 1.2986 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.16384459664590859,
            "unit": "iter/sec",
            "range": "stddev: 0.11983",
            "group": "engine",
            "extra": "mean: 6.1033 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.193006433938456,
            "unit": "iter/sec",
            "range": "stddev: 0.11748",
            "group": "engine",
            "extra": "mean: 5.1812 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.852608965958365,
            "unit": "iter/sec",
            "range": "stddev: 0.055974",
            "group": "import-export",
            "extra": "mean: 350.56 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.609905259290595,
            "unit": "iter/sec",
            "range": "stddev: 0.0083688",
            "group": "import-export",
            "extra": "mean: 383.16 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 1.5506407880914364,
            "unit": "iter/sec",
            "range": "stddev: 0.058830",
            "group": "import-export",
            "extra": "mean: 644.89 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 1.469185452163126,
            "unit": "iter/sec",
            "range": "stddev: 0.052262",
            "group": "import-export",
            "extra": "mean: 680.65 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 1045.8837803516979,
            "unit": "iter/sec",
            "range": "stddev: 0.00039044",
            "group": "node",
            "extra": "mean: 956.13 usec\nrounds: 179"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 232.0200487212111,
            "unit": "iter/sec",
            "range": "stddev: 0.00039611",
            "group": "node",
            "extra": "mean: 4.3100 msec\nrounds: 134"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 209.25843687145277,
            "unit": "iter/sec",
            "range": "stddev: 0.00038371",
            "group": "node",
            "extra": "mean: 4.7788 msec\nrounds: 127"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 241.57050415305682,
            "unit": "iter/sec",
            "range": "stddev: 0.00022914",
            "group": "node",
            "extra": "mean: 4.1396 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 43.82075871838796,
            "unit": "iter/sec",
            "range": "stddev: 0.0077696",
            "group": "node",
            "extra": "mean: 22.820 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 46.613686644300564,
            "unit": "iter/sec",
            "range": "stddev: 0.0016732",
            "group": "node",
            "extra": "mean: 21.453 msec\nrounds: 100"
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
          "id": "1310abaa7f765866f636c9af2d3332e3eaf74ced",
          "message": "`verdi setup`: improve validation and help string of broker virtual host (#4408)\n\nThe help string of the `--broker-virtual-host` option of `verdi setup`\r\nincorrectly said that forward slashes have to be escaped but this is not\r\ntrue. The code will escape any characters necessary when constructing\r\nthe URL to connect to RabbitMQ. On top of that, slashes would fail the\r\nvalidation outright, even though these are common in virtual hosts. For\r\nexample the virtual host always starts with a leading forward slash, but\r\nour validation would reject it. Also the leading slash will be added by\r\nthe code and so does not have to be used in the setup phase. The help\r\nstring and the documentation now reflect this.\r\n\r\nThe exacti naming rules for virtual hosts, imposed by RabbitMQ or other\r\nimplemenatations of the AMQP protocol, are not fully clear. But instead\r\nof putting an explicit validation on AiiDA's side and running the risk\r\nthat we incorrectly reject valid virtual host names, we simply accept\r\nall strings. In any case, any non-default virtual host will have to be\r\ncreated through RabbitMQ's control interface, which will perform the\r\nvalidation itself.",
          "timestamp": "2020-09-28T08:30:05+02:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/1310abaa7f765866f636c9af2d3332e3eaf74ced",
          "distinct": true,
          "tree_id": "0950b812971ab426a8f4bb6ebd2ca7c471670dc4"
        },
        "date": 1601275187303,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.5754218477198707,
            "unit": "iter/sec",
            "range": "stddev: 0.012532",
            "group": "engine",
            "extra": "mean: 279.69 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.8190664001247299,
            "unit": "iter/sec",
            "range": "stddev: 0.041156",
            "group": "engine",
            "extra": "mean: 1.2209 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.943986451182987,
            "unit": "iter/sec",
            "range": "stddev: 0.037817",
            "group": "engine",
            "extra": "mean: 1.0593 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.1788318790646238,
            "unit": "iter/sec",
            "range": "stddev: 0.079741",
            "group": "engine",
            "extra": "mean: 5.5918 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.20691641738407834,
            "unit": "iter/sec",
            "range": "stddev: 0.088286",
            "group": "engine",
            "extra": "mean: 4.8329 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.8295941492144823,
            "unit": "iter/sec",
            "range": "stddev: 0.012809",
            "group": "engine",
            "extra": "mean: 353.41 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.6535139364799202,
            "unit": "iter/sec",
            "range": "stddev: 0.065560",
            "group": "engine",
            "extra": "mean: 1.5302 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.7456387820278485,
            "unit": "iter/sec",
            "range": "stddev: 0.056247",
            "group": "engine",
            "extra": "mean: 1.3411 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.16040717494476878,
            "unit": "iter/sec",
            "range": "stddev: 0.14452",
            "group": "engine",
            "extra": "mean: 6.2341 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.18868534480023666,
            "unit": "iter/sec",
            "range": "stddev: 0.096107",
            "group": "engine",
            "extra": "mean: 5.2998 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.783958378040638,
            "unit": "iter/sec",
            "range": "stddev: 0.051336",
            "group": "import-export",
            "extra": "mean: 359.20 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.456554501975293,
            "unit": "iter/sec",
            "range": "stddev: 0.050164",
            "group": "import-export",
            "extra": "mean: 407.07 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 1.5240525199044954,
            "unit": "iter/sec",
            "range": "stddev: 0.061673",
            "group": "import-export",
            "extra": "mean: 656.15 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 1.4490944691260963,
            "unit": "iter/sec",
            "range": "stddev: 0.052097",
            "group": "import-export",
            "extra": "mean: 690.09 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 1105.5533292425353,
            "unit": "iter/sec",
            "range": "stddev: 0.00014093",
            "group": "node",
            "extra": "mean: 904.52 usec\nrounds: 191"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 225.14169160496635,
            "unit": "iter/sec",
            "range": "stddev: 0.00047598",
            "group": "node",
            "extra": "mean: 4.4416 msec\nrounds: 128"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 213.44648556191558,
            "unit": "iter/sec",
            "range": "stddev: 0.00029872",
            "group": "node",
            "extra": "mean: 4.6850 msec\nrounds: 127"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 225.15807233775556,
            "unit": "iter/sec",
            "range": "stddev: 0.00035532",
            "group": "node",
            "extra": "mean: 4.4413 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 41.48466345717491,
            "unit": "iter/sec",
            "range": "stddev: 0.0070692",
            "group": "node",
            "extra": "mean: 24.105 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 44.784583976784376,
            "unit": "iter/sec",
            "range": "stddev: 0.0014757",
            "group": "node",
            "extra": "mean: 22.329 msec\nrounds: 100"
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
          "id": "e2b5385044076f135e5b769aa8fd24f7950738f5",
          "message": "Merge branch 'master' of github.com:aiidateam/aiida-core into develop\n\nMerge after release of `v1.4.0`.",
          "timestamp": "2020-09-28T11:12:09+02:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/e2b5385044076f135e5b769aa8fd24f7950738f5",
          "distinct": true,
          "tree_id": "036461f0e803060dbed684406dab0a1cb6834a0a"
        },
        "date": 1601288139267,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.07950049850299,
            "unit": "iter/sec",
            "range": "stddev: 0.025381",
            "group": "engine",
            "extra": "mean: 324.73 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.7235582769742596,
            "unit": "iter/sec",
            "range": "stddev: 0.082410",
            "group": "engine",
            "extra": "mean: 1.3821 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.7848468943921648,
            "unit": "iter/sec",
            "range": "stddev: 0.12465",
            "group": "engine",
            "extra": "mean: 1.2741 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.15756342407146498,
            "unit": "iter/sec",
            "range": "stddev: 0.16948",
            "group": "engine",
            "extra": "mean: 6.3467 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.17920123029047752,
            "unit": "iter/sec",
            "range": "stddev: 0.21127",
            "group": "engine",
            "extra": "mean: 5.5803 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.4727636190074915,
            "unit": "iter/sec",
            "range": "stddev: 0.034722",
            "group": "engine",
            "extra": "mean: 404.41 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.5733611721480836,
            "unit": "iter/sec",
            "range": "stddev: 0.084771",
            "group": "engine",
            "extra": "mean: 1.7441 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.6260014749686602,
            "unit": "iter/sec",
            "range": "stddev: 0.10412",
            "group": "engine",
            "extra": "mean: 1.5974 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.141429565469121,
            "unit": "iter/sec",
            "range": "stddev: 0.15162",
            "group": "engine",
            "extra": "mean: 7.0707 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.1648281874886317,
            "unit": "iter/sec",
            "range": "stddev: 0.11046",
            "group": "engine",
            "extra": "mean: 6.0669 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.267539730182589,
            "unit": "iter/sec",
            "range": "stddev: 0.049290",
            "group": "import-export",
            "extra": "mean: 441.01 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.164520054588404,
            "unit": "iter/sec",
            "range": "stddev: 0.030784",
            "group": "import-export",
            "extra": "mean: 462.00 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 1.1803632815698015,
            "unit": "iter/sec",
            "range": "stddev: 0.093048",
            "group": "import-export",
            "extra": "mean: 847.20 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 1.157403252901267,
            "unit": "iter/sec",
            "range": "stddev: 0.050210",
            "group": "import-export",
            "extra": "mean: 864.00 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 787.9343921706115,
            "unit": "iter/sec",
            "range": "stddev: 0.0010500",
            "group": "node",
            "extra": "mean: 1.2691 msec\nrounds: 165"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 157.2119312666463,
            "unit": "iter/sec",
            "range": "stddev: 0.0036759",
            "group": "node",
            "extra": "mean: 6.3608 msec\nrounds: 117"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 156.01157812831624,
            "unit": "iter/sec",
            "range": "stddev: 0.0033345",
            "group": "node",
            "extra": "mean: 6.4098 msec\nrounds: 114"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 188.6787048787464,
            "unit": "iter/sec",
            "range": "stddev: 0.0014366",
            "group": "node",
            "extra": "mean: 5.3000 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 36.047716860253374,
            "unit": "iter/sec",
            "range": "stddev: 0.0069493",
            "group": "node",
            "extra": "mean: 27.741 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 38.12050220029947,
            "unit": "iter/sec",
            "range": "stddev: 0.0059683",
            "group": "node",
            "extra": "mean: 26.233 msec\nrounds: 100"
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
          "id": "65ad067b18cffeb639994efe9a372ec1475e1615",
          "message": "CI: move `pylint` configuration to `pyproject.toml` (#4411)\n\nThis is supported by `pylint` as of v2.5.",
          "timestamp": "2020-09-28T23:17:27+02:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/65ad067b18cffeb639994efe9a372ec1475e1615",
          "distinct": true,
          "tree_id": "636ba633d0ab1b287b1e6483de770bc7d9c6522f"
        },
        "date": 1601328433626,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.39484866098712,
            "unit": "iter/sec",
            "range": "stddev: 0.012971",
            "group": "engine",
            "extra": "mean: 294.56 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.8239874467463725,
            "unit": "iter/sec",
            "range": "stddev: 0.046972",
            "group": "engine",
            "extra": "mean: 1.2136 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.9313009780692192,
            "unit": "iter/sec",
            "range": "stddev: 0.045025",
            "group": "engine",
            "extra": "mean: 1.0738 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.18056844096991156,
            "unit": "iter/sec",
            "range": "stddev: 0.094625",
            "group": "engine",
            "extra": "mean: 5.5381 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.20522307779955998,
            "unit": "iter/sec",
            "range": "stddev: 0.11800",
            "group": "engine",
            "extra": "mean: 4.8727 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.827059766040088,
            "unit": "iter/sec",
            "range": "stddev: 0.0044021",
            "group": "engine",
            "extra": "mean: 353.72 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.6423571023154523,
            "unit": "iter/sec",
            "range": "stddev: 0.066519",
            "group": "engine",
            "extra": "mean: 1.5568 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.7358840843585123,
            "unit": "iter/sec",
            "range": "stddev: 0.084641",
            "group": "engine",
            "extra": "mean: 1.3589 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.15977598434278975,
            "unit": "iter/sec",
            "range": "stddev: 0.11115",
            "group": "engine",
            "extra": "mean: 6.2588 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.18897377480954605,
            "unit": "iter/sec",
            "range": "stddev: 0.14604",
            "group": "engine",
            "extra": "mean: 5.2917 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.5884442529287757,
            "unit": "iter/sec",
            "range": "stddev: 0.047257",
            "group": "import-export",
            "extra": "mean: 386.33 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.3149415533994278,
            "unit": "iter/sec",
            "range": "stddev: 0.051589",
            "group": "import-export",
            "extra": "mean: 431.98 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 1.3494422176403695,
            "unit": "iter/sec",
            "range": "stddev: 0.055606",
            "group": "import-export",
            "extra": "mean: 741.05 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 1.2520741018333854,
            "unit": "iter/sec",
            "range": "stddev: 0.067223",
            "group": "import-export",
            "extra": "mean: 798.67 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 860.2547448945278,
            "unit": "iter/sec",
            "range": "stddev: 0.00039338",
            "group": "node",
            "extra": "mean: 1.1624 msec\nrounds: 165"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 199.68552622475664,
            "unit": "iter/sec",
            "range": "stddev: 0.00026170",
            "group": "node",
            "extra": "mean: 5.0079 msec\nrounds: 133"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 186.98259686864716,
            "unit": "iter/sec",
            "range": "stddev: 0.00077714",
            "group": "node",
            "extra": "mean: 5.3481 msec\nrounds: 129"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 193.95352372403,
            "unit": "iter/sec",
            "range": "stddev: 0.00027119",
            "group": "node",
            "extra": "mean: 5.1559 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 38.930923242591376,
            "unit": "iter/sec",
            "range": "stddev: 0.0086760",
            "group": "node",
            "extra": "mean: 25.687 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 40.210600009796345,
            "unit": "iter/sec",
            "range": "stddev: 0.0020491",
            "group": "node",
            "extra": "mean: 24.869 msec\nrounds: 100"
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
          "id": "91449241ff2e12dd836b29882e32201cc7841716",
          "message": "`verdi process show`: order called by ctime and use process label (#4407)\n\nThe command was showing the called subprocesses in a random order and\r\nused the node type, which is often uninformative. For example, all\r\nworkchains are always shown as `WorkChainNode`. By using the process\r\nlabel instead, which is more specific, and ordering the called nodes by\r\ncreation time, the list gives a more natural overview of the order in\r\nwhich the subprocesses were called.",
          "timestamp": "2020-09-29T14:29:57+02:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/91449241ff2e12dd836b29882e32201cc7841716",
          "distinct": true,
          "tree_id": "a9721615e95c90093d05e5801d20086ee303d99b"
        },
        "date": 1601383185246,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.4477202048922604,
            "unit": "iter/sec",
            "range": "stddev: 0.0082148",
            "group": "engine",
            "extra": "mean: 290.05 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.7997143879562119,
            "unit": "iter/sec",
            "range": "stddev: 0.032961",
            "group": "engine",
            "extra": "mean: 1.2504 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.9180724246411056,
            "unit": "iter/sec",
            "range": "stddev: 0.035054",
            "group": "engine",
            "extra": "mean: 1.0892 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.17873072613550792,
            "unit": "iter/sec",
            "range": "stddev: 0.067847",
            "group": "engine",
            "extra": "mean: 5.5950 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.20559959979972106,
            "unit": "iter/sec",
            "range": "stddev: 0.086505",
            "group": "engine",
            "extra": "mean: 4.8638 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.755652687511781,
            "unit": "iter/sec",
            "range": "stddev: 0.0093504",
            "group": "engine",
            "extra": "mean: 362.89 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.6498637988545973,
            "unit": "iter/sec",
            "range": "stddev: 0.071184",
            "group": "engine",
            "extra": "mean: 1.5388 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.7394208674268108,
            "unit": "iter/sec",
            "range": "stddev: 0.039575",
            "group": "engine",
            "extra": "mean: 1.3524 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.15781056772280241,
            "unit": "iter/sec",
            "range": "stddev: 0.13543",
            "group": "engine",
            "extra": "mean: 6.3367 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.1883420297173608,
            "unit": "iter/sec",
            "range": "stddev: 0.10319",
            "group": "engine",
            "extra": "mean: 5.3095 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.6320809186778167,
            "unit": "iter/sec",
            "range": "stddev: 0.044395",
            "group": "import-export",
            "extra": "mean: 379.93 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.283070890573823,
            "unit": "iter/sec",
            "range": "stddev: 0.051785",
            "group": "import-export",
            "extra": "mean: 438.01 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 1.3261529905417098,
            "unit": "iter/sec",
            "range": "stddev: 0.055170",
            "group": "import-export",
            "extra": "mean: 754.06 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 1.2257071487472362,
            "unit": "iter/sec",
            "range": "stddev: 0.045707",
            "group": "import-export",
            "extra": "mean: 815.86 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 878.0724777915393,
            "unit": "iter/sec",
            "range": "stddev: 0.00037579",
            "group": "node",
            "extra": "mean: 1.1389 msec\nrounds: 203"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 194.64721535319163,
            "unit": "iter/sec",
            "range": "stddev: 0.00085278",
            "group": "node",
            "extra": "mean: 5.1375 msec\nrounds: 130"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 184.70378490249234,
            "unit": "iter/sec",
            "range": "stddev: 0.00060381",
            "group": "node",
            "extra": "mean: 5.4141 msec\nrounds: 105"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 188.8994439391033,
            "unit": "iter/sec",
            "range": "stddev: 0.0011399",
            "group": "node",
            "extra": "mean: 5.2938 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 42.9417778315351,
            "unit": "iter/sec",
            "range": "stddev: 0.0015273",
            "group": "node",
            "extra": "mean: 23.287 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 41.86138188443538,
            "unit": "iter/sec",
            "range": "stddev: 0.0022244",
            "group": "node",
            "extra": "mean: 23.888 msec\nrounds: 100"
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
          "id": "af91a8b10f2fe68360483a951d5c578863d38b76",
          "message": "Dependencies: update requirement `pytest~=6.0` and use `pyproject.toml` (#4410)\n\nStarting from v6.0, `pytest` supports using the `pyproject.toml` instead\r\nof a `pytest.ini` to define its configuration. Given that this is\r\nquickly becoming the Python packaging standard and allows us to reduce\r\nthe number of configuration files in the top level of the repository, we\r\nincrease the version requirement of `pytest`.\r\n\r\nNote that we also require `pytest-rerunfailures>=9.1.1` because lower\r\nversions are broken in combination with `pytest==6.1`. See the following:\r\n\r\n   https://github.com/pytest-dev/pytest-rerunfailures/issues/128\r\n\r\nfor details.",
          "timestamp": "2020-09-29T17:34:16+02:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/af91a8b10f2fe68360483a951d5c578863d38b76",
          "distinct": true,
          "tree_id": "3fc1f773a856d3b5ae5c8ecf03213deb0833cb71"
        },
        "date": 1601394178103,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.6896585987198365,
            "unit": "iter/sec",
            "range": "stddev: 0.055407",
            "group": "engine",
            "extra": "mean: 271.03 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.9359720067455561,
            "unit": "iter/sec",
            "range": "stddev: 0.056063",
            "group": "engine",
            "extra": "mean: 1.0684 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 1.0629932099945947,
            "unit": "iter/sec",
            "range": "stddev: 0.055067",
            "group": "engine",
            "extra": "mean: 940.74 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.20357134450584208,
            "unit": "iter/sec",
            "range": "stddev: 0.096772",
            "group": "engine",
            "extra": "mean: 4.9123 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.23373155441266014,
            "unit": "iter/sec",
            "range": "stddev: 0.11126",
            "group": "engine",
            "extra": "mean: 4.2784 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 3.0975241976019103,
            "unit": "iter/sec",
            "range": "stddev: 0.013459",
            "group": "engine",
            "extra": "mean: 322.84 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.7356127905709452,
            "unit": "iter/sec",
            "range": "stddev: 0.059240",
            "group": "engine",
            "extra": "mean: 1.3594 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.7833731379038117,
            "unit": "iter/sec",
            "range": "stddev: 0.064819",
            "group": "engine",
            "extra": "mean: 1.2765 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.17767403382098784,
            "unit": "iter/sec",
            "range": "stddev: 0.10190",
            "group": "engine",
            "extra": "mean: 5.6283 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.21314368699289526,
            "unit": "iter/sec",
            "range": "stddev: 0.092814",
            "group": "engine",
            "extra": "mean: 4.6917 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 3.1114214464756724,
            "unit": "iter/sec",
            "range": "stddev: 0.050856",
            "group": "import-export",
            "extra": "mean: 321.40 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.7686206712941854,
            "unit": "iter/sec",
            "range": "stddev: 0.049577",
            "group": "import-export",
            "extra": "mean: 361.19 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 1.742833842276622,
            "unit": "iter/sec",
            "range": "stddev: 0.066237",
            "group": "import-export",
            "extra": "mean: 573.78 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 1.663170184680389,
            "unit": "iter/sec",
            "range": "stddev: 0.043891",
            "group": "import-export",
            "extra": "mean: 601.26 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 1251.300131352632,
            "unit": "iter/sec",
            "range": "stddev: 0.000034214",
            "group": "node",
            "extra": "mean: 799.17 usec\nrounds: 205"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 251.4724743334726,
            "unit": "iter/sec",
            "range": "stddev: 0.0010425",
            "group": "node",
            "extra": "mean: 3.9766 msec\nrounds: 141"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 242.1330661976241,
            "unit": "iter/sec",
            "range": "stddev: 0.000075402",
            "group": "node",
            "extra": "mean: 4.1300 msec\nrounds: 141"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 273.5496612381178,
            "unit": "iter/sec",
            "range": "stddev: 0.00010492",
            "group": "node",
            "extra": "mean: 3.6556 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 47.56497579985233,
            "unit": "iter/sec",
            "range": "stddev: 0.015472",
            "group": "node",
            "extra": "mean: 21.024 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 46.20762713287542,
            "unit": "iter/sec",
            "range": "stddev: 0.012484",
            "group": "node",
            "extra": "mean: 21.641 msec\nrounds: 100"
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
          "id": "4544bc49a50c9aa3abebd2837efb5626958ee2b4",
          "message": "CI: add coverage patch threshold to prevent false positives (#4413)\n\nThe project diff percentage is the change in coverage w.r.t. all lines\r\nin the project, whereas the patch diff percentage is the change in\r\ncoverage w.r.t. only lines touched by the PR. The patch threshold is\r\ncurrently defaulting to 0%, hence it is very easy to fail. By raising it\r\nto 0.1% it should now only fail when there is a significant reduction\r\nin coverage. Number may need to be further tweaked.",
          "timestamp": "2020-09-30T10:24:15+02:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/4544bc49a50c9aa3abebd2837efb5626958ee2b4",
          "distinct": true,
          "tree_id": "e8cc6385b285fc53da873eb1a8b3b569fbfc567d"
        },
        "date": 1601454822743,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.4325211286393724,
            "unit": "iter/sec",
            "range": "stddev: 0.058586",
            "group": "engine",
            "extra": "mean: 291.33 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.8749542577960603,
            "unit": "iter/sec",
            "range": "stddev: 0.042648",
            "group": "engine",
            "extra": "mean: 1.1429 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.9774846086737325,
            "unit": "iter/sec",
            "range": "stddev: 0.059268",
            "group": "engine",
            "extra": "mean: 1.0230 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.1830068346474011,
            "unit": "iter/sec",
            "range": "stddev: 0.10260",
            "group": "engine",
            "extra": "mean: 5.4643 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.21286543035463648,
            "unit": "iter/sec",
            "range": "stddev: 0.098291",
            "group": "engine",
            "extra": "mean: 4.6978 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.8673932752481335,
            "unit": "iter/sec",
            "range": "stddev: 0.0094069",
            "group": "engine",
            "extra": "mean: 348.75 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.6962799893085728,
            "unit": "iter/sec",
            "range": "stddev: 0.049088",
            "group": "engine",
            "extra": "mean: 1.4362 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.767289874022034,
            "unit": "iter/sec",
            "range": "stddev: 0.056031",
            "group": "engine",
            "extra": "mean: 1.3033 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.1626074846423067,
            "unit": "iter/sec",
            "range": "stddev: 0.10925",
            "group": "engine",
            "extra": "mean: 6.1498 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.19081452236464183,
            "unit": "iter/sec",
            "range": "stddev: 0.10986",
            "group": "engine",
            "extra": "mean: 5.2407 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.768685425096151,
            "unit": "iter/sec",
            "range": "stddev: 0.052573",
            "group": "import-export",
            "extra": "mean: 361.18 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.48346086720649,
            "unit": "iter/sec",
            "range": "stddev: 0.048739",
            "group": "import-export",
            "extra": "mean: 402.66 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 1.593714590039935,
            "unit": "iter/sec",
            "range": "stddev: 0.043957",
            "group": "import-export",
            "extra": "mean: 627.46 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 1.4447797493567822,
            "unit": "iter/sec",
            "range": "stddev: 0.057530",
            "group": "import-export",
            "extra": "mean: 692.15 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 1130.2757881661962,
            "unit": "iter/sec",
            "range": "stddev: 0.000067784",
            "group": "node",
            "extra": "mean: 884.74 usec\nrounds: 197"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 213.4167874447888,
            "unit": "iter/sec",
            "range": "stddev: 0.0028211",
            "group": "node",
            "extra": "mean: 4.6857 msec\nrounds: 117"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 217.98800364114572,
            "unit": "iter/sec",
            "range": "stddev: 0.00014032",
            "group": "node",
            "extra": "mean: 4.5874 msec\nrounds: 131"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 244.49684364965955,
            "unit": "iter/sec",
            "range": "stddev: 0.000094011",
            "group": "node",
            "extra": "mean: 4.0900 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 45.827170510710154,
            "unit": "iter/sec",
            "range": "stddev: 0.0014468",
            "group": "node",
            "extra": "mean: 21.821 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 44.61570388604439,
            "unit": "iter/sec",
            "range": "stddev: 0.0016850",
            "group": "node",
            "extra": "mean: 22.414 msec\nrounds: 100"
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
          "id": "02248cf3686a0ab89faf1625e0da24d9e33d8cde",
          "message": "Replace old format string interpolation with f-strings (#4400)\n\nSince Python 3.5 is no longer supported, format string interpolations\r\ncan now be replaced by f-strings, introduced in Python 3.6, which are\r\nmore readable, require less characters and are more efficient.\r\n\r\nNote that `pylint` issues a warning when using f-strings for log\r\nmessages, just as it does for format interpolated strings. The reasoning\r\nis that this is slightly inefficient as the strings are always\r\ninterpolated even if the log is discarded, but also by not passing the\r\nformatting parameters as arguments, the available metadata is reduced.\r\nI feel these inefficiencies are premature optimizations as they are\r\nreally minimal and don't weigh up against the improved readability and\r\nmaintainability of using f-strings. That is why the `pylint` config is\r\nupdate to ignore the warning `logging-fstring-interpolation` which\r\nreplaces `logging-format-interpolation` that was ignored before.\r\n\r\nThe majority of the conversions were done automatically with the linting\r\ntool `flynt` which is also added as a pre-commit hook. It is added\r\nbefore the `yapf` step because since `flynt` will touch formatting,\r\n`yapf` will then get a chance to check it.",
          "timestamp": "2020-09-30T15:14:45+02:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/02248cf3686a0ab89faf1625e0da24d9e33d8cde",
          "distinct": true,
          "tree_id": "34e646ac57896670e7d2081e1c7f91086b17fb4a"
        },
        "date": 1601472149408,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 4.971928261839674,
            "unit": "iter/sec",
            "range": "stddev: 0.0067556",
            "group": "engine",
            "extra": "mean: 201.13 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 1.1682050194519478,
            "unit": "iter/sec",
            "range": "stddev: 0.051622",
            "group": "engine",
            "extra": "mean: 856.01 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 1.3132741962495793,
            "unit": "iter/sec",
            "range": "stddev: 0.047668",
            "group": "engine",
            "extra": "mean: 761.46 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.2291220084329937,
            "unit": "iter/sec",
            "range": "stddev: 0.22890",
            "group": "engine",
            "extra": "mean: 4.3645 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.27843856172971454,
            "unit": "iter/sec",
            "range": "stddev: 0.10687",
            "group": "engine",
            "extra": "mean: 3.5915 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 3.8871467856665656,
            "unit": "iter/sec",
            "range": "stddev: 0.0065101",
            "group": "engine",
            "extra": "mean: 257.26 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.8795447564435638,
            "unit": "iter/sec",
            "range": "stddev: 0.057122",
            "group": "engine",
            "extra": "mean: 1.1370 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.908897718832037,
            "unit": "iter/sec",
            "range": "stddev: 0.053276",
            "group": "engine",
            "extra": "mean: 1.1002 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.20949545363659075,
            "unit": "iter/sec",
            "range": "stddev: 0.17160",
            "group": "engine",
            "extra": "mean: 4.7734 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.244504258580196,
            "unit": "iter/sec",
            "range": "stddev: 0.12853",
            "group": "engine",
            "extra": "mean: 4.0899 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 3.82006030349109,
            "unit": "iter/sec",
            "range": "stddev: 0.038649",
            "group": "import-export",
            "extra": "mean: 261.78 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 3.2374499211079137,
            "unit": "iter/sec",
            "range": "stddev: 0.0093059",
            "group": "import-export",
            "extra": "mean: 308.89 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 2.032192563590057,
            "unit": "iter/sec",
            "range": "stddev: 0.037982",
            "group": "import-export",
            "extra": "mean: 492.08 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 1.8259334298558174,
            "unit": "iter/sec",
            "range": "stddev: 0.058185",
            "group": "import-export",
            "extra": "mean: 547.67 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 1349.504104656007,
            "unit": "iter/sec",
            "range": "stddev: 0.000083695",
            "group": "node",
            "extra": "mean: 741.01 usec\nrounds: 222"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 293.0932530946282,
            "unit": "iter/sec",
            "range": "stddev: 0.00028443",
            "group": "node",
            "extra": "mean: 3.4119 msec\nrounds: 180"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 267.1094343050502,
            "unit": "iter/sec",
            "range": "stddev: 0.00032406",
            "group": "node",
            "extra": "mean: 3.7438 msec\nrounds: 172"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 301.64169639529354,
            "unit": "iter/sec",
            "range": "stddev: 0.00043187",
            "group": "node",
            "extra": "mean: 3.3152 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 59.74751178304155,
            "unit": "iter/sec",
            "range": "stddev: 0.0014611",
            "group": "node",
            "extra": "mean: 16.737 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 56.020195804951385,
            "unit": "iter/sec",
            "range": "stddev: 0.0017074",
            "group": "node",
            "extra": "mean: 17.851 msec\nrounds: 100"
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
          "id": "29331b558b45ba74acf1ca633a2d8bfabc1bdd05",
          "message": "CI: use `-e` install for tox + add docker-compose for isolated RabbitMQ (#4375)\n\n* Using `pip install -e .` for tox runs improves startup time for tests\r\n   by preventing unnecessary copy of files.\r\n\r\n* The docker-compose yml file allows to set up an isolated RabbitMQ\r\n   instance for local CI testing.",
          "timestamp": "2020-10-01T11:54:31+02:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/29331b558b45ba74acf1ca633a2d8bfabc1bdd05",
          "distinct": true,
          "tree_id": "7fbd24fd833ead6688438d007d232a88fbca5f7f"
        },
        "date": 1601546722186,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 2.877351163554159,
            "unit": "iter/sec",
            "range": "stddev: 0.060562",
            "group": "engine",
            "extra": "mean: 347.54 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.7246107507383279,
            "unit": "iter/sec",
            "range": "stddev: 0.057957",
            "group": "engine",
            "extra": "mean: 1.3801 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.7841218369777461,
            "unit": "iter/sec",
            "range": "stddev: 0.073947",
            "group": "engine",
            "extra": "mean: 1.2753 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.15561649195761287,
            "unit": "iter/sec",
            "range": "stddev: 0.10861",
            "group": "engine",
            "extra": "mean: 6.4261 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.18067808869000182,
            "unit": "iter/sec",
            "range": "stddev: 0.13197",
            "group": "engine",
            "extra": "mean: 5.5347 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.310430617085707,
            "unit": "iter/sec",
            "range": "stddev: 0.057329",
            "group": "engine",
            "extra": "mean: 432.82 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.5644724864686874,
            "unit": "iter/sec",
            "range": "stddev: 0.069308",
            "group": "engine",
            "extra": "mean: 1.7716 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.6230174063242654,
            "unit": "iter/sec",
            "range": "stddev: 0.067095",
            "group": "engine",
            "extra": "mean: 1.6051 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.138653754957909,
            "unit": "iter/sec",
            "range": "stddev: 0.18171",
            "group": "engine",
            "extra": "mean: 7.2122 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.16361702088213229,
            "unit": "iter/sec",
            "range": "stddev: 0.11362",
            "group": "engine",
            "extra": "mean: 6.1118 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.5094013157145487,
            "unit": "iter/sec",
            "range": "stddev: 0.016312",
            "group": "import-export",
            "extra": "mean: 398.50 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.0561409510022703,
            "unit": "iter/sec",
            "range": "stddev: 0.063272",
            "group": "import-export",
            "extra": "mean: 486.35 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 1.2268765094001004,
            "unit": "iter/sec",
            "range": "stddev: 0.066224",
            "group": "import-export",
            "extra": "mean: 815.08 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 1.1610744616468125,
            "unit": "iter/sec",
            "range": "stddev: 0.054571",
            "group": "import-export",
            "extra": "mean: 861.27 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 799.915451051654,
            "unit": "iter/sec",
            "range": "stddev: 0.00058753",
            "group": "node",
            "extra": "mean: 1.2501 msec\nrounds: 189"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 174.81248616822413,
            "unit": "iter/sec",
            "range": "stddev: 0.0010504",
            "group": "node",
            "extra": "mean: 5.7204 msec\nrounds: 104"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 154.64096184258113,
            "unit": "iter/sec",
            "range": "stddev: 0.0020954",
            "group": "node",
            "extra": "mean: 6.4666 msec\nrounds: 115"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 183.97166244730076,
            "unit": "iter/sec",
            "range": "stddev: 0.00078987",
            "group": "node",
            "extra": "mean: 5.4356 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 35.409402011786554,
            "unit": "iter/sec",
            "range": "stddev: 0.014940",
            "group": "node",
            "extra": "mean: 28.241 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 37.47005517778447,
            "unit": "iter/sec",
            "range": "stddev: 0.0032067",
            "group": "node",
            "extra": "mean: 26.688 msec\nrounds: 100"
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
          "id": "1e1bdf2dee779970654ed9b22eb996b78e9c4149",
          "message": "Merge remote-tracking branch 'origin/master' into develop",
          "timestamp": "2020-10-04T20:05:09+02:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/1e1bdf2dee779970654ed9b22eb996b78e9c4149",
          "distinct": true,
          "tree_id": "9fcf7ff0a60efb37731c2839955f162d271763e3"
        },
        "date": 1601835377568,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.07478157481184,
            "unit": "iter/sec",
            "range": "stddev: 0.0096018",
            "group": "engine",
            "extra": "mean: 325.23 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.735005617943775,
            "unit": "iter/sec",
            "range": "stddev: 0.12847",
            "group": "engine",
            "extra": "mean: 1.3605 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.827184274018874,
            "unit": "iter/sec",
            "range": "stddev: 0.11196",
            "group": "engine",
            "extra": "mean: 1.2089 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.16093154495584697,
            "unit": "iter/sec",
            "range": "stddev: 0.18899",
            "group": "engine",
            "extra": "mean: 6.2138 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.18480725031990022,
            "unit": "iter/sec",
            "range": "stddev: 0.18097",
            "group": "engine",
            "extra": "mean: 5.4110 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.4291508742649435,
            "unit": "iter/sec",
            "range": "stddev: 0.013182",
            "group": "engine",
            "extra": "mean: 411.67 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.5875038290415199,
            "unit": "iter/sec",
            "range": "stddev: 0.10712",
            "group": "engine",
            "extra": "mean: 1.7021 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.6527637653386461,
            "unit": "iter/sec",
            "range": "stddev: 0.063235",
            "group": "engine",
            "extra": "mean: 1.5319 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.14365572385629163,
            "unit": "iter/sec",
            "range": "stddev: 0.096037",
            "group": "engine",
            "extra": "mean: 6.9611 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.16856357373645328,
            "unit": "iter/sec",
            "range": "stddev: 0.13473",
            "group": "engine",
            "extra": "mean: 5.9325 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.7167856131139816,
            "unit": "iter/sec",
            "range": "stddev: 0.011638",
            "group": "import-export",
            "extra": "mean: 368.08 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.3391401856223784,
            "unit": "iter/sec",
            "range": "stddev: 0.060705",
            "group": "import-export",
            "extra": "mean: 427.51 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 1.4575072780519829,
            "unit": "iter/sec",
            "range": "stddev: 0.059203",
            "group": "import-export",
            "extra": "mean: 686.10 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 1.333452498945687,
            "unit": "iter/sec",
            "range": "stddev: 0.068556",
            "group": "import-export",
            "extra": "mean: 749.93 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 869.9378681857237,
            "unit": "iter/sec",
            "range": "stddev: 0.00027291",
            "group": "node",
            "extra": "mean: 1.1495 msec\nrounds: 184"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 170.1842695258331,
            "unit": "iter/sec",
            "range": "stddev: 0.0012680",
            "group": "node",
            "extra": "mean: 5.8760 msec\nrounds: 114"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 172.58305061129013,
            "unit": "iter/sec",
            "range": "stddev: 0.00096393",
            "group": "node",
            "extra": "mean: 5.7943 msec\nrounds: 130"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 186.6869911051632,
            "unit": "iter/sec",
            "range": "stddev: 0.0014772",
            "group": "node",
            "extra": "mean: 5.3566 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 37.250146490954016,
            "unit": "iter/sec",
            "range": "stddev: 0.0032234",
            "group": "node",
            "extra": "mean: 26.846 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 42.02296827861773,
            "unit": "iter/sec",
            "range": "stddev: 0.0031034",
            "group": "node",
            "extra": "mean: 23.797 msec\nrounds: 100"
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
          "pythonVersion": "3.8.6",
          "metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "bd6903d88a4d88077150763574784a1bc375c644",
          "message": "`ProcessBuilder`: allow unsetting of inputs through attribute deletion (#4419)\n\nThe builder object was already able to delete set inputs through the\r\n`__delitem__` method, but `__delattr__` was not implemented causing\r\n`del builder.input_name` to raise. This is not consistent with how these\r\ninputs can be set or accessed as both `__getattr__` and `__setattr__`\r\nare implemented. Implementing `__delattr__` brings the implementation\r\nup to par for all attribute methods.",
          "timestamp": "2020-10-07T10:17:47+02:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/bd6903d88a4d88077150763574784a1bc375c644",
          "distinct": true,
          "tree_id": "5995519297d8bf66e8d978c999c105c505301a92"
        },
        "date": 1602059175526,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.9898467560744972,
            "unit": "iter/sec",
            "range": "stddev: 0.043553",
            "group": "engine",
            "extra": "mean: 250.64 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 1.0367719671763007,
            "unit": "iter/sec",
            "range": "stddev: 0.043725",
            "group": "engine",
            "extra": "mean: 964.53 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 1.150070228497975,
            "unit": "iter/sec",
            "range": "stddev: 0.047826",
            "group": "engine",
            "extra": "mean: 869.51 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.21220276591071294,
            "unit": "iter/sec",
            "range": "stddev: 0.091601",
            "group": "engine",
            "extra": "mean: 4.7125 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.24264083464472883,
            "unit": "iter/sec",
            "range": "stddev: 0.091888",
            "group": "engine",
            "extra": "mean: 4.1213 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 3.396916004297207,
            "unit": "iter/sec",
            "range": "stddev: 0.0067952",
            "group": "engine",
            "extra": "mean: 294.38 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.7897377159117851,
            "unit": "iter/sec",
            "range": "stddev: 0.078925",
            "group": "engine",
            "extra": "mean: 1.2662 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.90327261134599,
            "unit": "iter/sec",
            "range": "stddev: 0.036382",
            "group": "engine",
            "extra": "mean: 1.1071 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.18666798128513423,
            "unit": "iter/sec",
            "range": "stddev: 0.13509",
            "group": "engine",
            "extra": "mean: 5.3571 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.22612680789360312,
            "unit": "iter/sec",
            "range": "stddev: 0.10086",
            "group": "engine",
            "extra": "mean: 4.4223 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 3.3892976764124008,
            "unit": "iter/sec",
            "range": "stddev: 0.043731",
            "group": "import-export",
            "extra": "mean: 295.05 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 3.047243872501279,
            "unit": "iter/sec",
            "range": "stddev: 0.015144",
            "group": "import-export",
            "extra": "mean: 328.17 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 1.8230000733905447,
            "unit": "iter/sec",
            "range": "stddev: 0.038502",
            "group": "import-export",
            "extra": "mean: 548.55 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 1.7153585593211196,
            "unit": "iter/sec",
            "range": "stddev: 0.044153",
            "group": "import-export",
            "extra": "mean: 582.97 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 1320.1134679889938,
            "unit": "iter/sec",
            "range": "stddev: 0.000070427",
            "group": "node",
            "extra": "mean: 757.51 usec\nrounds: 212"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 263.2885756131087,
            "unit": "iter/sec",
            "range": "stddev: 0.00020739",
            "group": "node",
            "extra": "mean: 3.7981 msec\nrounds: 147"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 244.14066213848142,
            "unit": "iter/sec",
            "range": "stddev: 0.00028193",
            "group": "node",
            "extra": "mean: 4.0960 msec\nrounds: 130"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 277.8372372621403,
            "unit": "iter/sec",
            "range": "stddev: 0.00020950",
            "group": "node",
            "extra": "mean: 3.5992 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 51.0757316237662,
            "unit": "iter/sec",
            "range": "stddev: 0.012216",
            "group": "node",
            "extra": "mean: 19.579 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 49.963420780389164,
            "unit": "iter/sec",
            "range": "stddev: 0.014214",
            "group": "node",
            "extra": "mean: 20.015 msec\nrounds: 100"
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
          "pythonVersion": "3.8.6",
          "metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "16bc30548f7f1c686d200935174533535e850fd5",
          "message": "`CalcJob`: support nested directories in target of `remote_copy/symlink_list` (#4416)\n\nThe `upload_calculation` transport task would fail if either the\r\n`remote_copy_list` or `remote_symlink_list` contained a target filepath\r\nthat had a nested directory that did not exist yet in the remote working\r\ndirectory. Instead of inspecting the file system or creating the folders\r\nremotely each time a nested target path is encountered, which would incur\r\na potentially expensive operation over the transport each time, the\r\ndirectory hierarchy is first created in the local sandbox folder before\r\nit is copied recursively to the remote in a single shot.",
          "timestamp": "2020-10-16T23:32:42+02:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/16bc30548f7f1c686d200935174533535e850fd5",
          "distinct": true,
          "tree_id": "8c11369793f47e7c4081a6bf1a5317aac81963b4"
        },
        "date": 1602884678796,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 2.553119010767381,
            "unit": "iter/sec",
            "range": "stddev: 0.074639",
            "group": "engine",
            "extra": "mean: 391.68 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.6342985367437229,
            "unit": "iter/sec",
            "range": "stddev: 0.055446",
            "group": "engine",
            "extra": "mean: 1.5765 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.7123638168517129,
            "unit": "iter/sec",
            "range": "stddev: 0.091302",
            "group": "engine",
            "extra": "mean: 1.4038 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.14227403341006228,
            "unit": "iter/sec",
            "range": "stddev: 0.17218",
            "group": "engine",
            "extra": "mean: 7.0287 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.16308581404325823,
            "unit": "iter/sec",
            "range": "stddev: 0.11407",
            "group": "engine",
            "extra": "mean: 6.1317 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.1930396156017644,
            "unit": "iter/sec",
            "range": "stddev: 0.016193",
            "group": "engine",
            "extra": "mean: 455.99 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.501727980490811,
            "unit": "iter/sec",
            "range": "stddev: 0.076875",
            "group": "engine",
            "extra": "mean: 1.9931 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.5431828491353354,
            "unit": "iter/sec",
            "range": "stddev: 0.077903",
            "group": "engine",
            "extra": "mean: 1.8410 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.1231324695933604,
            "unit": "iter/sec",
            "range": "stddev: 0.20566",
            "group": "engine",
            "extra": "mean: 8.1213 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.1444484949116894,
            "unit": "iter/sec",
            "range": "stddev: 0.22843",
            "group": "engine",
            "extra": "mean: 6.9229 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.0272307017313307,
            "unit": "iter/sec",
            "range": "stddev: 0.066454",
            "group": "import-export",
            "extra": "mean: 493.28 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 1.8117445500714884,
            "unit": "iter/sec",
            "range": "stddev: 0.053513",
            "group": "import-export",
            "extra": "mean: 551.95 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 1.1232262780027764,
            "unit": "iter/sec",
            "range": "stddev: 0.056120",
            "group": "import-export",
            "extra": "mean: 890.29 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 1.048904260027605,
            "unit": "iter/sec",
            "range": "stddev: 0.074679",
            "group": "import-export",
            "extra": "mean: 953.38 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 667.9473887314313,
            "unit": "iter/sec",
            "range": "stddev: 0.00055435",
            "group": "node",
            "extra": "mean: 1.4971 msec\nrounds: 171"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 166.24130725028084,
            "unit": "iter/sec",
            "range": "stddev: 0.00070011",
            "group": "node",
            "extra": "mean: 6.0154 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 152.46419655470035,
            "unit": "iter/sec",
            "range": "stddev: 0.0012477",
            "group": "node",
            "extra": "mean: 6.5589 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 153.8999757455256,
            "unit": "iter/sec",
            "range": "stddev: 0.0010481",
            "group": "node",
            "extra": "mean: 6.4977 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 32.16696258325676,
            "unit": "iter/sec",
            "range": "stddev: 0.0033843",
            "group": "node",
            "extra": "mean: 31.088 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 30.005037410714085,
            "unit": "iter/sec",
            "range": "stddev: 0.018677",
            "group": "node",
            "extra": "mean: 33.328 msec\nrounds: 100"
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
          "pythonVersion": "3.8.6",
          "metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "0fb6f72333b0e553590326fc348acbee3ef0763b",
          "message": "Docs: Add docs live build to tox configuration (#4460)\n\nAdd docs live build using sphinx-autobuild. This dramatically speeds up the process of checking the rendered documentation while editing.\r\n\r\nCo-authored-by: Leopold Talirz <leopold.talirz@gmail.com>",
          "timestamp": "2020-10-19T12:44:28+02:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/0fb6f72333b0e553590326fc348acbee3ef0763b",
          "distinct": true,
          "tree_id": "e21a7951dbbbbaec12706dae8468366d5a22c251"
        },
        "date": 1603104853659,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.5569888873857947,
            "unit": "iter/sec",
            "range": "stddev: 0.0075586",
            "group": "engine",
            "extra": "mean: 281.14 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.8464500738520947,
            "unit": "iter/sec",
            "range": "stddev: 0.046478",
            "group": "engine",
            "extra": "mean: 1.1814 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.9174442372025519,
            "unit": "iter/sec",
            "range": "stddev: 0.073297",
            "group": "engine",
            "extra": "mean: 1.0900 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.17655434648653798,
            "unit": "iter/sec",
            "range": "stddev: 0.10091",
            "group": "engine",
            "extra": "mean: 5.6640 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.20660350484409126,
            "unit": "iter/sec",
            "range": "stddev: 0.10491",
            "group": "engine",
            "extra": "mean: 4.8402 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.7868341589369243,
            "unit": "iter/sec",
            "range": "stddev: 0.0099862",
            "group": "engine",
            "extra": "mean: 358.83 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.6479581748627554,
            "unit": "iter/sec",
            "range": "stddev: 0.080591",
            "group": "engine",
            "extra": "mean: 1.5433 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.7433063925855974,
            "unit": "iter/sec",
            "range": "stddev: 0.060900",
            "group": "engine",
            "extra": "mean: 1.3453 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.160557861330802,
            "unit": "iter/sec",
            "range": "stddev: 0.11627",
            "group": "engine",
            "extra": "mean: 6.2283 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.18868494769458777,
            "unit": "iter/sec",
            "range": "stddev: 0.14999",
            "group": "engine",
            "extra": "mean: 5.2998 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.8214477217445735,
            "unit": "iter/sec",
            "range": "stddev: 0.046072",
            "group": "import-export",
            "extra": "mean: 354.43 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.439974704351104,
            "unit": "iter/sec",
            "range": "stddev: 0.049257",
            "group": "import-export",
            "extra": "mean: 409.84 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 1.504387180774938,
            "unit": "iter/sec",
            "range": "stddev: 0.072207",
            "group": "import-export",
            "extra": "mean: 664.72 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 1.4472931744078732,
            "unit": "iter/sec",
            "range": "stddev: 0.058972",
            "group": "import-export",
            "extra": "mean: 690.95 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 1137.7723704820348,
            "unit": "iter/sec",
            "range": "stddev: 0.000069914",
            "group": "node",
            "extra": "mean: 878.91 usec\nrounds: 185"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 230.80368202776324,
            "unit": "iter/sec",
            "range": "stddev: 0.00033127",
            "group": "node",
            "extra": "mean: 4.3327 msec\nrounds: 127"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 213.15301737334354,
            "unit": "iter/sec",
            "range": "stddev: 0.00042179",
            "group": "node",
            "extra": "mean: 4.6915 msec\nrounds: 137"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 224.7689286067131,
            "unit": "iter/sec",
            "range": "stddev: 0.00091396",
            "group": "node",
            "extra": "mean: 4.4490 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 44.712265229730804,
            "unit": "iter/sec",
            "range": "stddev: 0.0025456",
            "group": "node",
            "extra": "mean: 22.365 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 41.73373894084583,
            "unit": "iter/sec",
            "range": "stddev: 0.011834",
            "group": "node",
            "extra": "mean: 23.961 msec\nrounds: 100"
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
          "pythonVersion": "3.8.6",
          "metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "4791046a58a1dfd0948f02cea6cf4b13eb1be4a5",
          "message": "Docs: Add redirects from old documenation (#4457)\n\nUses the `sphinxext-rediraffe` Sphinx extension to automatically create\r\nredirects when documentation pages are moved and therefore their URLs\r\nchange. New redirect rules should be added to `docs/source/redirects.txt`",
          "timestamp": "2020-10-19T17:09:01+02:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/4791046a58a1dfd0948f02cea6cf4b13eb1be4a5",
          "distinct": true,
          "tree_id": "e9bff4879dfc7c948832867f69c6174ee69da38f"
        },
        "date": 1603120706047,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.566956802528725,
            "unit": "iter/sec",
            "range": "stddev: 0.011754",
            "group": "engine",
            "extra": "mean: 280.35 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.8609427533132704,
            "unit": "iter/sec",
            "range": "stddev: 0.050468",
            "group": "engine",
            "extra": "mean: 1.1615 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.9650966593369903,
            "unit": "iter/sec",
            "range": "stddev: 0.060559",
            "group": "engine",
            "extra": "mean: 1.0362 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.18179817646918833,
            "unit": "iter/sec",
            "range": "stddev: 0.10670",
            "group": "engine",
            "extra": "mean: 5.5006 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.21102811875337163,
            "unit": "iter/sec",
            "range": "stddev: 0.079821",
            "group": "engine",
            "extra": "mean: 4.7387 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.9714348538908144,
            "unit": "iter/sec",
            "range": "stddev: 0.0081066",
            "group": "engine",
            "extra": "mean: 336.54 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.6777095876051877,
            "unit": "iter/sec",
            "range": "stddev: 0.067964",
            "group": "engine",
            "extra": "mean: 1.4756 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.7704621545611969,
            "unit": "iter/sec",
            "range": "stddev: 0.074048",
            "group": "engine",
            "extra": "mean: 1.2979 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.16157626726459107,
            "unit": "iter/sec",
            "range": "stddev: 0.14190",
            "group": "engine",
            "extra": "mean: 6.1890 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.19226507801766235,
            "unit": "iter/sec",
            "range": "stddev: 0.11683",
            "group": "engine",
            "extra": "mean: 5.2012 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.8745098159493088,
            "unit": "iter/sec",
            "range": "stddev: 0.049384",
            "group": "import-export",
            "extra": "mean: 347.89 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.6353456214363855,
            "unit": "iter/sec",
            "range": "stddev: 0.0055422",
            "group": "import-export",
            "extra": "mean: 379.46 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 1.589732426968564,
            "unit": "iter/sec",
            "range": "stddev: 0.073108",
            "group": "import-export",
            "extra": "mean: 629.04 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 1.5046462690610771,
            "unit": "iter/sec",
            "range": "stddev: 0.052722",
            "group": "import-export",
            "extra": "mean: 664.61 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 1126.9465348863066,
            "unit": "iter/sec",
            "range": "stddev: 0.000063005",
            "group": "node",
            "extra": "mean: 887.35 usec\nrounds: 188"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 235.94657628743803,
            "unit": "iter/sec",
            "range": "stddev: 0.00022963",
            "group": "node",
            "extra": "mean: 4.2382 msec\nrounds: 137"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 218.3555664129983,
            "unit": "iter/sec",
            "range": "stddev: 0.00022046",
            "group": "node",
            "extra": "mean: 4.5797 msec\nrounds: 132"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 232.56838173829814,
            "unit": "iter/sec",
            "range": "stddev: 0.00076293",
            "group": "node",
            "extra": "mean: 4.2998 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 44.61340014958419,
            "unit": "iter/sec",
            "range": "stddev: 0.0089995",
            "group": "node",
            "extra": "mean: 22.415 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 44.995555204062924,
            "unit": "iter/sec",
            "range": "stddev: 0.0017817",
            "group": "node",
            "extra": "mean: 22.224 msec\nrounds: 100"
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
          "pythonVersion": "3.8.6",
          "metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "eed191785da51b3c8ae105ee2073e3330deb0790",
          "message": "Docs: ⬆️ Update sphinx + extensions versions (#4470)\n\nThis commit primarily upgrades the sphinx dependency from sphinx v2 to v3, allowing for other upgrades of sphinx version pinning.\r\n\r\nIt also moved the `aiida/sphinxext` testing to the official sphinx testing infrastructure, and fixes an issue with the automodule writer. However, the automodule functionality cannot yet be re-instated, due to issues with referencing of these objects.",
          "timestamp": "2020-10-20T10:37:39+02:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/eed191785da51b3c8ae105ee2073e3330deb0790",
          "distinct": true,
          "tree_id": "0abf7ed2497d25d33c40df6f8bcd893107265ac3"
        },
        "date": 1603183602316,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.9212951870798602,
            "unit": "iter/sec",
            "range": "stddev: 0.017468",
            "group": "engine",
            "extra": "mean: 255.02 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.9048327882810496,
            "unit": "iter/sec",
            "range": "stddev: 0.090479",
            "group": "engine",
            "extra": "mean: 1.1052 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 1.0741984002134677,
            "unit": "iter/sec",
            "range": "stddev: 0.028623",
            "group": "engine",
            "extra": "mean: 930.93 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.19268810706244768,
            "unit": "iter/sec",
            "range": "stddev: 0.10391",
            "group": "engine",
            "extra": "mean: 5.1897 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.22523303022440666,
            "unit": "iter/sec",
            "range": "stddev: 0.091809",
            "group": "engine",
            "extra": "mean: 4.4398 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 3.1377634125753566,
            "unit": "iter/sec",
            "range": "stddev: 0.015707",
            "group": "engine",
            "extra": "mean: 318.70 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.7393097048370452,
            "unit": "iter/sec",
            "range": "stddev: 0.049715",
            "group": "engine",
            "extra": "mean: 1.3526 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.8369580017537956,
            "unit": "iter/sec",
            "range": "stddev: 0.056867",
            "group": "engine",
            "extra": "mean: 1.1948 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.1769921667283663,
            "unit": "iter/sec",
            "range": "stddev: 0.12674",
            "group": "engine",
            "extra": "mean: 5.6500 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.2068572829019351,
            "unit": "iter/sec",
            "range": "stddev: 0.18132",
            "group": "engine",
            "extra": "mean: 4.8343 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 3.052443012272102,
            "unit": "iter/sec",
            "range": "stddev: 0.041835",
            "group": "import-export",
            "extra": "mean: 327.61 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.580511288249418,
            "unit": "iter/sec",
            "range": "stddev: 0.055828",
            "group": "import-export",
            "extra": "mean: 387.52 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 1.5477054609282905,
            "unit": "iter/sec",
            "range": "stddev: 0.041977",
            "group": "import-export",
            "extra": "mean: 646.12 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 1.400610984141017,
            "unit": "iter/sec",
            "range": "stddev: 0.048709",
            "group": "import-export",
            "extra": "mean: 713.97 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 1042.7007262794848,
            "unit": "iter/sec",
            "range": "stddev: 0.00014466",
            "group": "node",
            "extra": "mean: 959.05 usec\nrounds: 226"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 218.0434146133394,
            "unit": "iter/sec",
            "range": "stddev: 0.0012962",
            "group": "node",
            "extra": "mean: 4.5862 msec\nrounds: 161"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 213.28364060116502,
            "unit": "iter/sec",
            "range": "stddev: 0.00048932",
            "group": "node",
            "extra": "mean: 4.6886 msec\nrounds: 140"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 231.50431895362874,
            "unit": "iter/sec",
            "range": "stddev: 0.00046692",
            "group": "node",
            "extra": "mean: 4.3196 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 48.339433087402575,
            "unit": "iter/sec",
            "range": "stddev: 0.0020057",
            "group": "node",
            "extra": "mean: 20.687 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 49.149523888204826,
            "unit": "iter/sec",
            "range": "stddev: 0.0016240",
            "group": "node",
            "extra": "mean: 20.346 msec\nrounds: 100"
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
          "pythonVersion": "3.8.6",
          "metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "db659ddf8a36db77963e2955df5066876c0d8017",
          "message": "REST API: list endpoints at base URL (#4412)\n\nThe base URL of the REST API was returning a 404 invalid URL response\r\nwithout providing any guidance to new users as to how to use the API.\r\nWe change this to return the list of endpoints formerly available only\r\nunder /server/endpoints.\r\n\r\nDocumentation of where to find the list of endpoints -- which seems\r\nto have been entirely deleted -- is added.\r\n\r\nCo-authored-by: Giovanni Pizzi <gio.piz@gmail.com>",
          "timestamp": "2020-10-20T11:14:33+02:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/db659ddf8a36db77963e2955df5066876c0d8017",
          "distinct": true,
          "tree_id": "f834d0346aa4f27cdf42c54cc1794dc566ff1ccb"
        },
        "date": 1603185832560,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.841170521306563,
            "unit": "iter/sec",
            "range": "stddev: 0.014822",
            "group": "engine",
            "extra": "mean: 260.34 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.9093552807435544,
            "unit": "iter/sec",
            "range": "stddev: 0.050854",
            "group": "engine",
            "extra": "mean: 1.0997 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 1.036340633419068,
            "unit": "iter/sec",
            "range": "stddev: 0.048651",
            "group": "engine",
            "extra": "mean: 964.93 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.1875640884662516,
            "unit": "iter/sec",
            "range": "stddev: 0.11380",
            "group": "engine",
            "extra": "mean: 5.3315 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.2143873816211087,
            "unit": "iter/sec",
            "range": "stddev: 0.11461",
            "group": "engine",
            "extra": "mean: 4.6645 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 3.0183238189247925,
            "unit": "iter/sec",
            "range": "stddev: 0.0060705",
            "group": "engine",
            "extra": "mean: 331.31 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.6967180141003632,
            "unit": "iter/sec",
            "range": "stddev: 0.060998",
            "group": "engine",
            "extra": "mean: 1.4353 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.782029875077294,
            "unit": "iter/sec",
            "range": "stddev: 0.053637",
            "group": "engine",
            "extra": "mean: 1.2787 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.1667008006421159,
            "unit": "iter/sec",
            "range": "stddev: 0.093064",
            "group": "engine",
            "extra": "mean: 5.9988 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.1969519921497083,
            "unit": "iter/sec",
            "range": "stddev: 0.13009",
            "group": "engine",
            "extra": "mean: 5.0774 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.9488531390161286,
            "unit": "iter/sec",
            "range": "stddev: 0.052629",
            "group": "import-export",
            "extra": "mean: 339.11 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.6150781477718956,
            "unit": "iter/sec",
            "range": "stddev: 0.048679",
            "group": "import-export",
            "extra": "mean: 382.40 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 1.636284841513379,
            "unit": "iter/sec",
            "range": "stddev: 0.059726",
            "group": "import-export",
            "extra": "mean: 611.14 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 1.4859338391610946,
            "unit": "iter/sec",
            "range": "stddev: 0.052632",
            "group": "import-export",
            "extra": "mean: 672.98 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 1150.7403214127635,
            "unit": "iter/sec",
            "range": "stddev: 0.000059199",
            "group": "node",
            "extra": "mean: 869.01 usec\nrounds: 203"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 238.70379156629383,
            "unit": "iter/sec",
            "range": "stddev: 0.00022460",
            "group": "node",
            "extra": "mean: 4.1893 msec\nrounds: 128"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 215.1076146552886,
            "unit": "iter/sec",
            "range": "stddev: 0.00049647",
            "group": "node",
            "extra": "mean: 4.6488 msec\nrounds: 141"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 238.32907182661344,
            "unit": "iter/sec",
            "range": "stddev: 0.00020380",
            "group": "node",
            "extra": "mean: 4.1959 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 48.123638335331776,
            "unit": "iter/sec",
            "range": "stddev: 0.0013882",
            "group": "node",
            "extra": "mean: 20.780 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 47.90518320241348,
            "unit": "iter/sec",
            "range": "stddev: 0.0017231",
            "group": "node",
            "extra": "mean: 20.875 msec\nrounds: 100"
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
          "pythonVersion": "3.8.6",
          "metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "cb268d1dd90a2aaeb94e7fd0ddc4091a6bf9ebc9",
          "message": "replace all occurences of \"export file\"\n\nWe have agreed on the terms \"AiiDA archive (file)\" and \"AiiDA archive\nformat\".\n\nCo-authored-by: Casper Welzel Andersen <43357585+CasperWA@users.noreply.github.com>",
          "timestamp": "2020-10-20T14:46:44+02:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/cb268d1dd90a2aaeb94e7fd0ddc4091a6bf9ebc9",
          "distinct": true,
          "tree_id": "93ce3e19dd46ee92093c0764895ade003ccb554e"
        },
        "date": 1603198618647,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.178768576434357,
            "unit": "iter/sec",
            "range": "stddev: 0.016106",
            "group": "engine",
            "extra": "mean: 314.59 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.7680118140222141,
            "unit": "iter/sec",
            "range": "stddev: 0.082553",
            "group": "engine",
            "extra": "mean: 1.3021 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.8697669910052301,
            "unit": "iter/sec",
            "range": "stddev: 0.038362",
            "group": "engine",
            "extra": "mean: 1.1497 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.16688311663059227,
            "unit": "iter/sec",
            "range": "stddev: 0.12114",
            "group": "engine",
            "extra": "mean: 5.9922 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.1925381180284517,
            "unit": "iter/sec",
            "range": "stddev: 0.11401",
            "group": "engine",
            "extra": "mean: 5.1938 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.6300121729850647,
            "unit": "iter/sec",
            "range": "stddev: 0.016287",
            "group": "engine",
            "extra": "mean: 380.23 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.6099688827509758,
            "unit": "iter/sec",
            "range": "stddev: 0.073891",
            "group": "engine",
            "extra": "mean: 1.6394 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.700432163997558,
            "unit": "iter/sec",
            "range": "stddev: 0.057754",
            "group": "engine",
            "extra": "mean: 1.4277 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.14854743381750965,
            "unit": "iter/sec",
            "range": "stddev: 0.092487",
            "group": "engine",
            "extra": "mean: 6.7319 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.17491692648370993,
            "unit": "iter/sec",
            "range": "stddev: 0.16042",
            "group": "engine",
            "extra": "mean: 5.7170 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.642599874213761,
            "unit": "iter/sec",
            "range": "stddev: 0.045828",
            "group": "import-export",
            "extra": "mean: 378.42 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.337517310954462,
            "unit": "iter/sec",
            "range": "stddev: 0.052812",
            "group": "import-export",
            "extra": "mean: 427.80 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 1.4837150569695676,
            "unit": "iter/sec",
            "range": "stddev: 0.054156",
            "group": "import-export",
            "extra": "mean: 673.98 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 1.3733702113128556,
            "unit": "iter/sec",
            "range": "stddev: 0.073965",
            "group": "import-export",
            "extra": "mean: 728.14 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 938.1848792699355,
            "unit": "iter/sec",
            "range": "stddev: 0.00041447",
            "group": "node",
            "extra": "mean: 1.0659 msec\nrounds: 204"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 214.79469057076827,
            "unit": "iter/sec",
            "range": "stddev: 0.00090177",
            "group": "node",
            "extra": "mean: 4.6556 msec\nrounds: 134"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 186.31354128707258,
            "unit": "iter/sec",
            "range": "stddev: 0.0013125",
            "group": "node",
            "extra": "mean: 5.3673 msec\nrounds: 129"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 217.51104512416174,
            "unit": "iter/sec",
            "range": "stddev: 0.00083640",
            "group": "node",
            "extra": "mean: 4.5975 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 41.012575453876735,
            "unit": "iter/sec",
            "range": "stddev: 0.0060868",
            "group": "node",
            "extra": "mean: 24.383 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 41.61004886141302,
            "unit": "iter/sec",
            "range": "stddev: 0.0026596",
            "group": "node",
            "extra": "mean: 24.033 msec\nrounds: 100"
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
          "pythonVersion": "3.8.6",
          "metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "09ac91654648adb684a58d5d2d7b1c11a503dae8",
          "message": "Docs: update REST API wsgi scripts (#4488)\n\nThe wsgi scripts for deploying the AiiDA REST in production were\r\noutdated and are updated.\r\nThe how-to on deploying your own REST API server is significantly\r\nstreamlined and now includes the wsgi files as well as the examplary\r\napache virtualhost configuration.\r\n\r\nCo-authored-by: Giovanni Pizzi <gio.piz@gmail.com>",
          "timestamp": "2020-10-20T22:08:45+02:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/09ac91654648adb684a58d5d2d7b1c11a503dae8",
          "distinct": true,
          "tree_id": "8e9ea5e84fc510fdf0655ace8e2a15bb5d6926d6"
        },
        "date": 1603225127662,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.446362550913625,
            "unit": "iter/sec",
            "range": "stddev: 0.0096438",
            "group": "engine",
            "extra": "mean: 290.16 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.8153958998353865,
            "unit": "iter/sec",
            "range": "stddev: 0.072999",
            "group": "engine",
            "extra": "mean: 1.2264 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.9199092566221442,
            "unit": "iter/sec",
            "range": "stddev: 0.043355",
            "group": "engine",
            "extra": "mean: 1.0871 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.17153532579851047,
            "unit": "iter/sec",
            "range": "stddev: 0.087037",
            "group": "engine",
            "extra": "mean: 5.8297 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.19823299740798037,
            "unit": "iter/sec",
            "range": "stddev: 0.10737",
            "group": "engine",
            "extra": "mean: 5.0446 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.592641607058313,
            "unit": "iter/sec",
            "range": "stddev: 0.054156",
            "group": "engine",
            "extra": "mean: 385.71 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.6438967739338809,
            "unit": "iter/sec",
            "range": "stddev: 0.062161",
            "group": "engine",
            "extra": "mean: 1.5530 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.7192385916901666,
            "unit": "iter/sec",
            "range": "stddev: 0.068524",
            "group": "engine",
            "extra": "mean: 1.3904 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.15296583007437908,
            "unit": "iter/sec",
            "range": "stddev: 0.10355",
            "group": "engine",
            "extra": "mean: 6.5374 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.18075063526219734,
            "unit": "iter/sec",
            "range": "stddev: 0.088714",
            "group": "engine",
            "extra": "mean: 5.5325 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.5234473995645827,
            "unit": "iter/sec",
            "range": "stddev: 0.051921",
            "group": "import-export",
            "extra": "mean: 396.28 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.203078274508467,
            "unit": "iter/sec",
            "range": "stddev: 0.050487",
            "group": "import-export",
            "extra": "mean: 453.91 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 1.3338302550553136,
            "unit": "iter/sec",
            "range": "stddev: 0.051174",
            "group": "import-export",
            "extra": "mean: 749.72 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 1.2111704060386175,
            "unit": "iter/sec",
            "range": "stddev: 0.072843",
            "group": "import-export",
            "extra": "mean: 825.65 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 931.2767524869583,
            "unit": "iter/sec",
            "range": "stddev: 0.00015826",
            "group": "node",
            "extra": "mean: 1.0738 msec\nrounds: 186"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 196.80690289502851,
            "unit": "iter/sec",
            "range": "stddev: 0.00045831",
            "group": "node",
            "extra": "mean: 5.0811 msec\nrounds: 129"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 187.88317054903882,
            "unit": "iter/sec",
            "range": "stddev: 0.00045803",
            "group": "node",
            "extra": "mean: 5.3225 msec\nrounds: 121"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 192.75144877083082,
            "unit": "iter/sec",
            "range": "stddev: 0.00095402",
            "group": "node",
            "extra": "mean: 5.1880 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 42.1439421049305,
            "unit": "iter/sec",
            "range": "stddev: 0.0015777",
            "group": "node",
            "extra": "mean: 23.728 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 41.137327748169795,
            "unit": "iter/sec",
            "range": "stddev: 0.0021288",
            "group": "node",
            "extra": "mean: 24.309 msec\nrounds: 100"
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
          "pythonVersion": "3.8.6",
          "metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "2eda24edd9eae3e34d57a4c039d3574a0ba064c6",
          "message": "Docs: serve a custom 404 page (#4478)\n\nRedirect to a helpful page when a document is not found.",
          "timestamp": "2020-10-21T16:34:13+02:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/2eda24edd9eae3e34d57a4c039d3574a0ba064c6",
          "distinct": true,
          "tree_id": "6cddcc1c30da8e88445ef06c8fa5d65367384efa"
        },
        "date": 1603291446023,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.6086110136775678,
            "unit": "iter/sec",
            "range": "stddev: 0.0043694",
            "group": "engine",
            "extra": "mean: 277.11 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.8072450302166758,
            "unit": "iter/sec",
            "range": "stddev: 0.067689",
            "group": "engine",
            "extra": "mean: 1.2388 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.9229430087320639,
            "unit": "iter/sec",
            "range": "stddev: 0.048361",
            "group": "engine",
            "extra": "mean: 1.0835 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.17373203248754754,
            "unit": "iter/sec",
            "range": "stddev: 0.17098",
            "group": "engine",
            "extra": "mean: 5.7560 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.19322703158705024,
            "unit": "iter/sec",
            "range": "stddev: 0.18198",
            "group": "engine",
            "extra": "mean: 5.1753 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.7377480089613497,
            "unit": "iter/sec",
            "range": "stddev: 0.011083",
            "group": "engine",
            "extra": "mean: 365.26 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.6441298020100286,
            "unit": "iter/sec",
            "range": "stddev: 0.10186",
            "group": "engine",
            "extra": "mean: 1.5525 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.7343998703529454,
            "unit": "iter/sec",
            "range": "stddev: 0.088462",
            "group": "engine",
            "extra": "mean: 1.3617 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.15999923403118724,
            "unit": "iter/sec",
            "range": "stddev: 0.11496",
            "group": "engine",
            "extra": "mean: 6.2500 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.19018380976609908,
            "unit": "iter/sec",
            "range": "stddev: 0.11373",
            "group": "engine",
            "extra": "mean: 5.2581 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.7477160991225085,
            "unit": "iter/sec",
            "range": "stddev: 0.054959",
            "group": "import-export",
            "extra": "mean: 363.94 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.4695929048062957,
            "unit": "iter/sec",
            "range": "stddev: 0.054504",
            "group": "import-export",
            "extra": "mean: 404.93 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 1.595986329947774,
            "unit": "iter/sec",
            "range": "stddev: 0.050462",
            "group": "import-export",
            "extra": "mean: 626.57 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 1.4401579080148224,
            "unit": "iter/sec",
            "range": "stddev: 0.062235",
            "group": "import-export",
            "extra": "mean: 694.37 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 1105.0499354400265,
            "unit": "iter/sec",
            "range": "stddev: 0.00012890",
            "group": "node",
            "extra": "mean: 904.94 usec\nrounds: 185"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 232.88720061492197,
            "unit": "iter/sec",
            "range": "stddev: 0.00020581",
            "group": "node",
            "extra": "mean: 4.2939 msec\nrounds: 132"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 214.17841835102172,
            "unit": "iter/sec",
            "range": "stddev: 0.00029374",
            "group": "node",
            "extra": "mean: 4.6690 msec\nrounds: 117"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 221.88006098034677,
            "unit": "iter/sec",
            "range": "stddev: 0.00096070",
            "group": "node",
            "extra": "mean: 4.5069 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 43.820193401437486,
            "unit": "iter/sec",
            "range": "stddev: 0.0013614",
            "group": "node",
            "extra": "mean: 22.821 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 43.90745203244228,
            "unit": "iter/sec",
            "range": "stddev: 0.0015419",
            "group": "node",
            "extra": "mean: 22.775 msec\nrounds: 100"
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
          "pythonVersion": "3.8.6",
          "metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "c6d38c1657b65f540bea653f253920bb602c7ebc",
          "message": "Refactor the archive exporter (#4448)\n\nThis commit refactors the export process (in a back-compatible manner),\r\nsuch that the extraction of data from the database is fully decoupled\r\nfrom the writing of that data to an archive.\r\n\r\nIt allows for pluggable export writers, and is intended as a\r\npreliminary step toward the creation of a new archive format.\r\n\r\nThe original `export_tree` function is renamed to `_collect_archive_data`\r\nand its contents split into a number of separate, self-contained, functions.\r\n\r\nThe process control has then been inverted,\r\nsuch that the export data is parsed to the archive writer,\r\nrather than the export writer calling `export_tree` to generate that data.\r\n\r\nAn abstract writer class is provided,\r\nthen each concrete writer is identified and called for via a string\r\n(this could in fact be made into an entry point).\r\n\r\nData is parsed to the writers contained in a\r\n[dataclasses](https://pypi.org/project/dataclasses/) container.\r\nThis requires a backport for python 3.6,\r\nbut is included in python core from python 3.7 onwards.\r\n\r\nThe `extract_tree`, `extract_zip` and `extract_tar` functions are\r\nreimplemented, for backwards compatibility,\r\nbut are marked as deprecated and to be remove in v2.0.0.\r\n\r\nAdditional issues addressed:\r\n\r\n- fixes a bug, whereby, in python 3.8,\r\n  `logging.disable(level=` has changed to `logging.disable(lvl=`.\r\n- fixes a bug, whereby the traversal rules summary was returning incorrect\r\n  rule summaries.\r\n- adds mypy compliant typing (and adds the file to the pre-commit mypy list)\r\n\r\nCo-authored-by: Leopold Talirz <leopold.talirz@gmail.com>",
          "timestamp": "2020-10-23T02:12:16+02:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/c6d38c1657b65f540bea653f253920bb602c7ebc",
          "distinct": true,
          "tree_id": "31f1052077184e8d1dec6af13eebd5ffc500b960"
        },
        "date": 1603412620778,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 2.947578620020206,
            "unit": "iter/sec",
            "range": "stddev: 0.010587",
            "group": "engine",
            "extra": "mean: 339.26 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.6920283577653131,
            "unit": "iter/sec",
            "range": "stddev: 0.059490",
            "group": "engine",
            "extra": "mean: 1.4450 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.7638635337597318,
            "unit": "iter/sec",
            "range": "stddev: 0.061081",
            "group": "engine",
            "extra": "mean: 1.3091 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.15875657033754145,
            "unit": "iter/sec",
            "range": "stddev: 0.12646",
            "group": "engine",
            "extra": "mean: 6.2990 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.17623688576123914,
            "unit": "iter/sec",
            "range": "stddev: 0.10086",
            "group": "engine",
            "extra": "mean: 5.6742 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.224105382134164,
            "unit": "iter/sec",
            "range": "stddev: 0.014407",
            "group": "engine",
            "extra": "mean: 449.62 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.5243363647243221,
            "unit": "iter/sec",
            "range": "stddev: 0.070190",
            "group": "engine",
            "extra": "mean: 1.9072 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.5903059867504576,
            "unit": "iter/sec",
            "range": "stddev: 0.081043",
            "group": "engine",
            "extra": "mean: 1.6940 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.1369393535302348,
            "unit": "iter/sec",
            "range": "stddev: 0.18165",
            "group": "engine",
            "extra": "mean: 7.3025 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.16605819125498977,
            "unit": "iter/sec",
            "range": "stddev: 0.18469",
            "group": "engine",
            "extra": "mean: 6.0220 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.4607496234484207,
            "unit": "iter/sec",
            "range": "stddev: 0.011807",
            "group": "import-export",
            "extra": "mean: 406.38 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.1226998621527358,
            "unit": "iter/sec",
            "range": "stddev: 0.018303",
            "group": "import-export",
            "extra": "mean: 471.10 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 1.2724084945499166,
            "unit": "iter/sec",
            "range": "stddev: 0.046666",
            "group": "import-export",
            "extra": "mean: 785.91 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 1.1901803358497656,
            "unit": "iter/sec",
            "range": "stddev: 0.066465",
            "group": "import-export",
            "extra": "mean: 840.21 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 849.9737880645903,
            "unit": "iter/sec",
            "range": "stddev: 0.00076678",
            "group": "node",
            "extra": "mean: 1.1765 msec\nrounds: 183"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 195.14837263210418,
            "unit": "iter/sec",
            "range": "stddev: 0.00051940",
            "group": "node",
            "extra": "mean: 5.1243 msec\nrounds: 126"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 180.82134001426644,
            "unit": "iter/sec",
            "range": "stddev: 0.00038275",
            "group": "node",
            "extra": "mean: 5.5303 msec\nrounds: 114"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 182.4880456642678,
            "unit": "iter/sec",
            "range": "stddev: 0.00082283",
            "group": "node",
            "extra": "mean: 5.4798 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 36.24492289319682,
            "unit": "iter/sec",
            "range": "stddev: 0.016436",
            "group": "node",
            "extra": "mean: 27.590 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 36.47877948214215,
            "unit": "iter/sec",
            "range": "stddev: 0.012527",
            "group": "node",
            "extra": "mean: 27.413 msec\nrounds: 100"
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
          "pythonVersion": "3.8.6",
          "metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "1be12e1f97ce6373b1a85c7949fed869680df170",
          "message": "Pre-commit: reintroduce `pylint` rules (#4501)\n\nIn 65ad067b18cffeb639994efe9a372ec1475e1615 the following `pylint` rules\r\nwere accidentally disabled:\r\n\r\n * missing-class-docstring\r\n * missing-function-docstring\r\n * too-many-ancestors\r\n * too-many-locals\r\n\r\nThis commit reintroduces all but the \"too-many-ancestors\" rule, which\r\nis most likely never going to be addressed. Having to change the depth\r\nof the MRO is not trivial and usually not that effective.",
          "timestamp": "2020-10-23T15:32:51+02:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/1be12e1f97ce6373b1a85c7949fed869680df170",
          "distinct": true,
          "tree_id": "a58375e4e1ec24a2518317c566bab98f51f1f74d"
        },
        "date": 1603460522055,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.843112661030593,
            "unit": "iter/sec",
            "range": "stddev: 0.0057167",
            "group": "engine",
            "extra": "mean: 260.21 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.9058900363306427,
            "unit": "iter/sec",
            "range": "stddev: 0.050466",
            "group": "engine",
            "extra": "mean: 1.1039 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 1.019204154725238,
            "unit": "iter/sec",
            "range": "stddev: 0.041880",
            "group": "engine",
            "extra": "mean: 981.16 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.18764807182333315,
            "unit": "iter/sec",
            "range": "stddev: 0.092366",
            "group": "engine",
            "extra": "mean: 5.3291 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.21798963263358956,
            "unit": "iter/sec",
            "range": "stddev: 0.066403",
            "group": "engine",
            "extra": "mean: 4.5874 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.9762899321073926,
            "unit": "iter/sec",
            "range": "stddev: 0.011482",
            "group": "engine",
            "extra": "mean: 335.99 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.7090455765636351,
            "unit": "iter/sec",
            "range": "stddev: 0.060371",
            "group": "engine",
            "extra": "mean: 1.4103 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.7876119306317061,
            "unit": "iter/sec",
            "range": "stddev: 0.072164",
            "group": "engine",
            "extra": "mean: 1.2697 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.16784152818752698,
            "unit": "iter/sec",
            "range": "stddev: 0.082951",
            "group": "engine",
            "extra": "mean: 5.9580 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.19952435183457984,
            "unit": "iter/sec",
            "range": "stddev: 0.099776",
            "group": "engine",
            "extra": "mean: 5.0119 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.8980462692835127,
            "unit": "iter/sec",
            "range": "stddev: 0.047670",
            "group": "import-export",
            "extra": "mean: 345.06 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.56001957902975,
            "unit": "iter/sec",
            "range": "stddev: 0.066499",
            "group": "import-export",
            "extra": "mean: 390.62 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 1.6316063333726334,
            "unit": "iter/sec",
            "range": "stddev: 0.050849",
            "group": "import-export",
            "extra": "mean: 612.89 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 1.5189012285321652,
            "unit": "iter/sec",
            "range": "stddev: 0.051091",
            "group": "import-export",
            "extra": "mean: 658.37 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 1145.5685937829107,
            "unit": "iter/sec",
            "range": "stddev: 0.000038910",
            "group": "node",
            "extra": "mean: 872.93 usec\nrounds: 195"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 238.13619045328625,
            "unit": "iter/sec",
            "range": "stddev: 0.000075085",
            "group": "node",
            "extra": "mean: 4.1993 msec\nrounds: 138"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 219.32612502862028,
            "unit": "iter/sec",
            "range": "stddev: 0.00010306",
            "group": "node",
            "extra": "mean: 4.5594 msec\nrounds: 136"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 244.96177142479883,
            "unit": "iter/sec",
            "range": "stddev: 0.00010305",
            "group": "node",
            "extra": "mean: 4.0823 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 45.0750624580407,
            "unit": "iter/sec",
            "range": "stddev: 0.014426",
            "group": "node",
            "extra": "mean: 22.185 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 44.71208624330143,
            "unit": "iter/sec",
            "range": "stddev: 0.012451",
            "group": "node",
            "extra": "mean: 22.365 msec\nrounds: 100"
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
          "pythonVersion": "3.8.6",
          "metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "33c9f41d029a22640646be295b9316c533685b19",
          "message": "Refactor archive progress bar (#4504)\n\nThis commit introduces a new generic progress reporter interface (in `aiida/common/progress_reporter.py`),\r\nthat can be used for adding progress reporting to any process.\r\nIt is intended to deprecate the existing `aiida/tools/importexport/common/progress_bar.py` module.\r\n\r\nThe reporter is designed to work similar to logging,\r\nsuch that its \"handler\" is set external to the actual function, e.g. by the CLI.\r\nIts default implementation is to do nothing (a null reporter),\r\nand there is convenience function to set a [tqdm](https://tqdm.github.io/) progress bar implementation (`set_progress_bar_tqdm`).\r\n\r\nThe reporter is intended to always be used as context manager,\r\ne.g. to allow the progress bar to be removed once the process is complete.\r\n\r\nThe reporter has been implemented in the archive export module,\r\nand it is intended that it will also be implemented in the archive import module.\r\nAt this point the existing `aiida/tools/importexport/common/progress_bar.py` module can be removed.",
          "timestamp": "2020-10-25T12:03:05+01:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/33c9f41d029a22640646be295b9316c533685b19",
          "distinct": true,
          "tree_id": "fb4fd93f189394c2b80a9ecc07f08f4394c14d35"
        },
        "date": 1603624351472,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.5209624444367056,
            "unit": "iter/sec",
            "range": "stddev: 0.010461",
            "group": "engine",
            "extra": "mean: 284.01 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.8304691420121911,
            "unit": "iter/sec",
            "range": "stddev: 0.049064",
            "group": "engine",
            "extra": "mean: 1.2041 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.9540490580936465,
            "unit": "iter/sec",
            "range": "stddev: 0.054093",
            "group": "engine",
            "extra": "mean: 1.0482 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.1801780909746345,
            "unit": "iter/sec",
            "range": "stddev: 0.087086",
            "group": "engine",
            "extra": "mean: 5.5501 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.20752304256647947,
            "unit": "iter/sec",
            "range": "stddev: 0.11629",
            "group": "engine",
            "extra": "mean: 4.8187 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.8741868285596768,
            "unit": "iter/sec",
            "range": "stddev: 0.0091850",
            "group": "engine",
            "extra": "mean: 347.92 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.6696871362882691,
            "unit": "iter/sec",
            "range": "stddev: 0.053885",
            "group": "engine",
            "extra": "mean: 1.4932 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.743637966929282,
            "unit": "iter/sec",
            "range": "stddev: 0.074192",
            "group": "engine",
            "extra": "mean: 1.3447 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.16106295471726356,
            "unit": "iter/sec",
            "range": "stddev: 0.11252",
            "group": "engine",
            "extra": "mean: 6.2088 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.18889043347660517,
            "unit": "iter/sec",
            "range": "stddev: 0.11241",
            "group": "engine",
            "extra": "mean: 5.2941 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.8442301753965413,
            "unit": "iter/sec",
            "range": "stddev: 0.0072389",
            "group": "import-export",
            "extra": "mean: 351.59 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.419652589644507,
            "unit": "iter/sec",
            "range": "stddev: 0.055883",
            "group": "import-export",
            "extra": "mean: 413.28 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 1.5554978133739792,
            "unit": "iter/sec",
            "range": "stddev: 0.066264",
            "group": "import-export",
            "extra": "mean: 642.88 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 1.4594940579100386,
            "unit": "iter/sec",
            "range": "stddev: 0.068244",
            "group": "import-export",
            "extra": "mean: 685.17 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 1044.762818165264,
            "unit": "iter/sec",
            "range": "stddev: 0.00022110",
            "group": "node",
            "extra": "mean: 957.16 usec\nrounds: 210"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 222.78680358899965,
            "unit": "iter/sec",
            "range": "stddev: 0.00079697",
            "group": "node",
            "extra": "mean: 4.4886 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 215.3880197082694,
            "unit": "iter/sec",
            "range": "stddev: 0.00011798",
            "group": "node",
            "extra": "mean: 4.6428 msec\nrounds: 125"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 233.04132144921724,
            "unit": "iter/sec",
            "range": "stddev: 0.00037050",
            "group": "node",
            "extra": "mean: 4.2911 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 45.754778389865194,
            "unit": "iter/sec",
            "range": "stddev: 0.0012392",
            "group": "node",
            "extra": "mean: 21.856 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 44.295860712667896,
            "unit": "iter/sec",
            "range": "stddev: 0.0016305",
            "group": "node",
            "extra": "mean: 22.575 msec\nrounds: 100"
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
          "pythonVersion": "3.8.6",
          "metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "e1421245cc8ac115d81dbd55e62af614a4233483",
          "message": "Fix `ZeroDivisionError` in worker slots check (#4513)\n\nThis was being raised if 0 slots were available",
          "timestamp": "2020-10-26T00:22:14+01:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/e1421245cc8ac115d81dbd55e62af614a4233483",
          "distinct": true,
          "tree_id": "67872a366fdb7d25fdc499885b0dc25e9efc6f75"
        },
        "date": 1603668630420,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 4.524929909706895,
            "unit": "iter/sec",
            "range": "stddev: 0.0072400",
            "group": "engine",
            "extra": "mean: 221.00 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 1.0254675506085364,
            "unit": "iter/sec",
            "range": "stddev: 0.050296",
            "group": "engine",
            "extra": "mean: 975.16 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 1.1744569553945379,
            "unit": "iter/sec",
            "range": "stddev: 0.035177",
            "group": "engine",
            "extra": "mean: 851.46 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.21200926426100236,
            "unit": "iter/sec",
            "range": "stddev: 0.10932",
            "group": "engine",
            "extra": "mean: 4.7168 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.2451367790100129,
            "unit": "iter/sec",
            "range": "stddev: 0.095322",
            "group": "engine",
            "extra": "mean: 4.0794 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 3.470583227242605,
            "unit": "iter/sec",
            "range": "stddev: 0.015539",
            "group": "engine",
            "extra": "mean: 288.14 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.8253857634248439,
            "unit": "iter/sec",
            "range": "stddev: 0.050179",
            "group": "engine",
            "extra": "mean: 1.2116 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.8967674586072322,
            "unit": "iter/sec",
            "range": "stddev: 0.055327",
            "group": "engine",
            "extra": "mean: 1.1151 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.19165331711507416,
            "unit": "iter/sec",
            "range": "stddev: 0.073855",
            "group": "engine",
            "extra": "mean: 5.2178 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.21532650830925643,
            "unit": "iter/sec",
            "range": "stddev: 0.25203",
            "group": "engine",
            "extra": "mean: 4.6441 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 3.147975301811716,
            "unit": "iter/sec",
            "range": "stddev: 0.047581",
            "group": "import-export",
            "extra": "mean: 317.66 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.8016322509344236,
            "unit": "iter/sec",
            "range": "stddev: 0.050928",
            "group": "import-export",
            "extra": "mean: 356.93 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 1.7364441426077057,
            "unit": "iter/sec",
            "range": "stddev: 0.059254",
            "group": "import-export",
            "extra": "mean: 575.89 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 1.6888139803188424,
            "unit": "iter/sec",
            "range": "stddev: 0.058728",
            "group": "import-export",
            "extra": "mean: 592.13 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 1267.7251406590308,
            "unit": "iter/sec",
            "range": "stddev: 0.000091449",
            "group": "node",
            "extra": "mean: 788.81 usec\nrounds: 211"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 269.98624537466844,
            "unit": "iter/sec",
            "range": "stddev: 0.00030341",
            "group": "node",
            "extra": "mean: 3.7039 msec\nrounds: 138"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 243.59606693771522,
            "unit": "iter/sec",
            "range": "stddev: 0.00034044",
            "group": "node",
            "extra": "mean: 4.1052 msec\nrounds: 152"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 279.624417430592,
            "unit": "iter/sec",
            "range": "stddev: 0.00031737",
            "group": "node",
            "extra": "mean: 3.5762 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 52.54389794927694,
            "unit": "iter/sec",
            "range": "stddev: 0.0057226",
            "group": "node",
            "extra": "mean: 19.032 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 54.71620861146989,
            "unit": "iter/sec",
            "range": "stddev: 0.0013888",
            "group": "node",
            "extra": "mean: 18.276 msec\nrounds: 100"
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
          "pythonVersion": "3.8.6",
          "metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "861a39f268954833385e699b3acbd092ccd04e5e",
          "message": "Fix `UnboundLocalError` in `aiida.cmdline.utils.edit_multiline_template` (#4436)\n\nIf `click.edit` returns a falsy value, the following conditional would\r\nbe skipped and the `value` variable would be undefined causing an\r\n`UnboundLocalError` to be raised. This bug was reported by @blokhin but\r\nthe exact conditions under which it occurred are not clear.",
          "timestamp": "2020-10-26T16:40:42+01:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/861a39f268954833385e699b3acbd092ccd04e5e",
          "distinct": true,
          "tree_id": "ef6a692a6eb97a9a9ef1631eae98fee3b083ec4a"
        },
        "date": 1603727498299,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.0181148153634534,
            "unit": "iter/sec",
            "range": "stddev: 0.012407",
            "group": "engine",
            "extra": "mean: 331.33 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.7176036282151419,
            "unit": "iter/sec",
            "range": "stddev: 0.066037",
            "group": "engine",
            "extra": "mean: 1.3935 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.815845242458245,
            "unit": "iter/sec",
            "range": "stddev: 0.057507",
            "group": "engine",
            "extra": "mean: 1.2257 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.1569936007566327,
            "unit": "iter/sec",
            "range": "stddev: 0.11648",
            "group": "engine",
            "extra": "mean: 6.3697 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.17785985261541712,
            "unit": "iter/sec",
            "range": "stddev: 0.082067",
            "group": "engine",
            "extra": "mean: 5.6224 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.3637496078716453,
            "unit": "iter/sec",
            "range": "stddev: 0.010045",
            "group": "engine",
            "extra": "mean: 423.06 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.5529060062600276,
            "unit": "iter/sec",
            "range": "stddev: 0.053711",
            "group": "engine",
            "extra": "mean: 1.8086 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.6152343416517783,
            "unit": "iter/sec",
            "range": "stddev: 0.082631",
            "group": "engine",
            "extra": "mean: 1.6254 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.1386638371364824,
            "unit": "iter/sec",
            "range": "stddev: 0.10118",
            "group": "engine",
            "extra": "mean: 7.2117 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.162329422801846,
            "unit": "iter/sec",
            "range": "stddev: 0.12941",
            "group": "engine",
            "extra": "mean: 6.1603 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.285908858792907,
            "unit": "iter/sec",
            "range": "stddev: 0.0079167",
            "group": "import-export",
            "extra": "mean: 437.46 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.046798164132481,
            "unit": "iter/sec",
            "range": "stddev: 0.060845",
            "group": "import-export",
            "extra": "mean: 488.57 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 1.2281597354680278,
            "unit": "iter/sec",
            "range": "stddev: 0.050841",
            "group": "import-export",
            "extra": "mean: 814.23 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 1.1524715093225366,
            "unit": "iter/sec",
            "range": "stddev: 0.047697",
            "group": "import-export",
            "extra": "mean: 867.70 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 807.7811400134342,
            "unit": "iter/sec",
            "range": "stddev: 0.00016181",
            "group": "node",
            "extra": "mean: 1.2380 msec\nrounds: 179"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 177.00229751455234,
            "unit": "iter/sec",
            "range": "stddev: 0.00055332",
            "group": "node",
            "extra": "mean: 5.6496 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 167.2636275663857,
            "unit": "iter/sec",
            "range": "stddev: 0.00060683",
            "group": "node",
            "extra": "mean: 5.9786 msec\nrounds: 112"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 181.2404567725672,
            "unit": "iter/sec",
            "range": "stddev: 0.00047263",
            "group": "node",
            "extra": "mean: 5.5175 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 35.884091851346525,
            "unit": "iter/sec",
            "range": "stddev: 0.0025385",
            "group": "node",
            "extra": "mean: 27.868 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 33.54601285196238,
            "unit": "iter/sec",
            "range": "stddev: 0.018343",
            "group": "node",
            "extra": "mean: 29.810 msec\nrounds: 100"
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
          "pythonVersion": "3.8.6",
          "metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "7c49471b4ce5b6265ab488991567e08044d5baa3",
          "message": "`verdi migrate`: make `--in-place` work across different file systems (#4393)\n\nThe `verdi migrate` command assumed implicitly that the archive that is\r\nto be migrated, resides on the same file system as the one that is used\r\nby the `tempfile` module. If this is not the case, the `os.rename` call\r\nused to atomically move the migrated archive to the original will fail\r\nwith the exception:\r\n\r\n    OSError: [Errno 18] Invalid cross-device link\r\n\r\nChanging `os.rename` to `shutil.move` fixes this problem. The downside,\r\nhowever, is that the move is no longer atomic, but that is probably why\r\n`os.rename` is restricted to same filysystem operations.",
          "timestamp": "2020-10-26T20:08:41+01:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/7c49471b4ce5b6265ab488991567e08044d5baa3",
          "distinct": true,
          "tree_id": "bbb345572c784a08a95e5ba31fd1670c7bdc86d3"
        },
        "date": 1603739808357,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 4.2072027531591445,
            "unit": "iter/sec",
            "range": "stddev: 0.011957",
            "group": "engine",
            "extra": "mean: 237.69 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 1.0122005893601063,
            "unit": "iter/sec",
            "range": "stddev: 0.058832",
            "group": "engine",
            "extra": "mean: 987.95 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 1.1284453108684152,
            "unit": "iter/sec",
            "range": "stddev: 0.044041",
            "group": "engine",
            "extra": "mean: 886.17 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.2112320619821577,
            "unit": "iter/sec",
            "range": "stddev: 0.11122",
            "group": "engine",
            "extra": "mean: 4.7341 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.2588446211464616,
            "unit": "iter/sec",
            "range": "stddev: 0.096224",
            "group": "engine",
            "extra": "mean: 3.8633 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 3.4971289201049673,
            "unit": "iter/sec",
            "range": "stddev: 0.018770",
            "group": "engine",
            "extra": "mean: 285.95 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.8426003967215826,
            "unit": "iter/sec",
            "range": "stddev: 0.077250",
            "group": "engine",
            "extra": "mean: 1.1868 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.9236581931712265,
            "unit": "iter/sec",
            "range": "stddev: 0.053969",
            "group": "engine",
            "extra": "mean: 1.0827 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.19448535557186575,
            "unit": "iter/sec",
            "range": "stddev: 0.11390",
            "group": "engine",
            "extra": "mean: 5.1418 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.2111498962163967,
            "unit": "iter/sec",
            "range": "stddev: 0.29384",
            "group": "engine",
            "extra": "mean: 4.7360 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 3.376406290946383,
            "unit": "iter/sec",
            "range": "stddev: 0.011832",
            "group": "import-export",
            "extra": "mean: 296.17 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 3.0973804736033945,
            "unit": "iter/sec",
            "range": "stddev: 0.0046463",
            "group": "import-export",
            "extra": "mean: 322.85 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 1.891704851321572,
            "unit": "iter/sec",
            "range": "stddev: 0.045735",
            "group": "import-export",
            "extra": "mean: 528.62 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 1.7288350399655408,
            "unit": "iter/sec",
            "range": "stddev: 0.060042",
            "group": "import-export",
            "extra": "mean: 578.42 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 1344.464501701857,
            "unit": "iter/sec",
            "range": "stddev: 0.000090266",
            "group": "node",
            "extra": "mean: 743.79 usec\nrounds: 221"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 249.3725565514318,
            "unit": "iter/sec",
            "range": "stddev: 0.0010166",
            "group": "node",
            "extra": "mean: 4.0101 msec\nrounds: 158"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 241.63165811706597,
            "unit": "iter/sec",
            "range": "stddev: 0.00074401",
            "group": "node",
            "extra": "mean: 4.1385 msec\nrounds: 175"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 269.4337498404589,
            "unit": "iter/sec",
            "range": "stddev: 0.00069493",
            "group": "node",
            "extra": "mean: 3.7115 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 57.246731664591096,
            "unit": "iter/sec",
            "range": "stddev: 0.0013284",
            "group": "node",
            "extra": "mean: 17.468 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 54.223324265768944,
            "unit": "iter/sec",
            "range": "stddev: 0.0025358",
            "group": "node",
            "extra": "mean: 18.442 msec\nrounds: 100"
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
          "pythonVersion": "3.8.6",
          "metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "57c8afaa90ff7ac54e8eb2e2cded4b15d26eb8b0",
          "message": "Improve the deprecation warning for `Node.open` outside context manager (#4434)\n\nThe new warning now includes the offending line of code.",
          "timestamp": "2020-10-27T09:22:55+01:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/57c8afaa90ff7ac54e8eb2e2cded4b15d26eb8b0",
          "distinct": true,
          "tree_id": "bc508037eead843cfb6ed2736dc2386bb1327082"
        },
        "date": 1603787472330,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 4.277123698042203,
            "unit": "iter/sec",
            "range": "stddev: 0.0070270",
            "group": "engine",
            "extra": "mean: 233.80 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 1.0141225563263767,
            "unit": "iter/sec",
            "range": "stddev: 0.044804",
            "group": "engine",
            "extra": "mean: 986.07 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 1.1634943575507608,
            "unit": "iter/sec",
            "range": "stddev: 0.034849",
            "group": "engine",
            "extra": "mean: 859.48 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.20887277082745465,
            "unit": "iter/sec",
            "range": "stddev: 0.085352",
            "group": "engine",
            "extra": "mean: 4.7876 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.24517201709563183,
            "unit": "iter/sec",
            "range": "stddev: 0.075833",
            "group": "engine",
            "extra": "mean: 4.0788 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 3.188734322046798,
            "unit": "iter/sec",
            "range": "stddev: 0.049893",
            "group": "engine",
            "extra": "mean: 313.60 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.790237004598981,
            "unit": "iter/sec",
            "range": "stddev: 0.048870",
            "group": "engine",
            "extra": "mean: 1.2654 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.8831603640974778,
            "unit": "iter/sec",
            "range": "stddev: 0.055932",
            "group": "engine",
            "extra": "mean: 1.1323 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.18758326460135125,
            "unit": "iter/sec",
            "range": "stddev: 0.098150",
            "group": "engine",
            "extra": "mean: 5.3310 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.2202491341658651,
            "unit": "iter/sec",
            "range": "stddev: 0.11046",
            "group": "engine",
            "extra": "mean: 4.5403 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 3.166990239467046,
            "unit": "iter/sec",
            "range": "stddev: 0.042660",
            "group": "import-export",
            "extra": "mean: 315.76 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.8181742884683825,
            "unit": "iter/sec",
            "range": "stddev: 0.053281",
            "group": "import-export",
            "extra": "mean: 354.84 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 1.7721470970007251,
            "unit": "iter/sec",
            "range": "stddev: 0.056361",
            "group": "import-export",
            "extra": "mean: 564.29 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 1.6287607175577092,
            "unit": "iter/sec",
            "range": "stddev: 0.059240",
            "group": "import-export",
            "extra": "mean: 613.96 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 1261.9059511984499,
            "unit": "iter/sec",
            "range": "stddev: 0.000066785",
            "group": "node",
            "extra": "mean: 792.45 usec\nrounds: 204"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 260.9976482711421,
            "unit": "iter/sec",
            "range": "stddev: 0.00018990",
            "group": "node",
            "extra": "mean: 3.8315 msec\nrounds: 149"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 236.3570743800076,
            "unit": "iter/sec",
            "range": "stddev: 0.00043022",
            "group": "node",
            "extra": "mean: 4.2309 msec\nrounds: 145"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 268.0492216640021,
            "unit": "iter/sec",
            "range": "stddev: 0.00022226",
            "group": "node",
            "extra": "mean: 3.7307 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 46.89234062637598,
            "unit": "iter/sec",
            "range": "stddev: 0.015543",
            "group": "node",
            "extra": "mean: 21.325 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 52.57644734002463,
            "unit": "iter/sec",
            "range": "stddev: 0.0011189",
            "group": "node",
            "extra": "mean: 19.020 msec\nrounds: 100"
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
          "pythonVersion": "3.8.6",
          "metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "9460e4e456ada082354879a527e02b9e3c230528",
          "message": "Revert PR #4416 (#4519)\n\n\"`CalcJob`: support nested directories in target of `remote_copy/symlink_list` (#4416)\"\r\n\r\nThis reverts commit 16bc30548f7f1c686d200935174533535e850fd5.",
          "timestamp": "2020-10-27T16:02:28+01:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/9460e4e456ada082354879a527e02b9e3c230528",
          "distinct": true,
          "tree_id": "b73421c22b657e4c423ddbf911552cfd4149fa34"
        },
        "date": 1603811578598,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.1359082391704676,
            "unit": "iter/sec",
            "range": "stddev: 0.059190",
            "group": "engine",
            "extra": "mean: 318.89 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.7955015602928159,
            "unit": "iter/sec",
            "range": "stddev: 0.064091",
            "group": "engine",
            "extra": "mean: 1.2571 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.8898546079921652,
            "unit": "iter/sec",
            "range": "stddev: 0.072335",
            "group": "engine",
            "extra": "mean: 1.1238 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.16964194163997767,
            "unit": "iter/sec",
            "range": "stddev: 0.064432",
            "group": "engine",
            "extra": "mean: 5.8948 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.1958337509473388,
            "unit": "iter/sec",
            "range": "stddev: 0.10900",
            "group": "engine",
            "extra": "mean: 5.1064 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.607110723367184,
            "unit": "iter/sec",
            "range": "stddev: 0.016723",
            "group": "engine",
            "extra": "mean: 383.57 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.6330178103913535,
            "unit": "iter/sec",
            "range": "stddev: 0.080667",
            "group": "engine",
            "extra": "mean: 1.5797 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.6963592308687354,
            "unit": "iter/sec",
            "range": "stddev: 0.061403",
            "group": "engine",
            "extra": "mean: 1.4360 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.1508111116622673,
            "unit": "iter/sec",
            "range": "stddev: 0.13285",
            "group": "engine",
            "extra": "mean: 6.6308 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.1773258467797161,
            "unit": "iter/sec",
            "range": "stddev: 0.096796",
            "group": "engine",
            "extra": "mean: 5.6393 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.6134881428736447,
            "unit": "iter/sec",
            "range": "stddev: 0.064092",
            "group": "import-export",
            "extra": "mean: 382.63 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.2916737216797944,
            "unit": "iter/sec",
            "range": "stddev: 0.072801",
            "group": "import-export",
            "extra": "mean: 436.36 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 1.4487919574844494,
            "unit": "iter/sec",
            "range": "stddev: 0.074734",
            "group": "import-export",
            "extra": "mean: 690.23 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 1.3608513769634185,
            "unit": "iter/sec",
            "range": "stddev: 0.077120",
            "group": "import-export",
            "extra": "mean: 734.83 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 1004.9673178360745,
            "unit": "iter/sec",
            "range": "stddev: 0.00046767",
            "group": "node",
            "extra": "mean: 995.06 usec\nrounds: 209"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 176.85188225459197,
            "unit": "iter/sec",
            "range": "stddev: 0.0033143",
            "group": "node",
            "extra": "mean: 5.6544 msec\nrounds: 107"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 189.7368315414838,
            "unit": "iter/sec",
            "range": "stddev: 0.0012600",
            "group": "node",
            "extra": "mean: 5.2705 msec\nrounds: 112"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 214.62198508527325,
            "unit": "iter/sec",
            "range": "stddev: 0.00051634",
            "group": "node",
            "extra": "mean: 4.6594 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 41.32589690239227,
            "unit": "iter/sec",
            "range": "stddev: 0.0025296",
            "group": "node",
            "extra": "mean: 24.198 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 40.987441436466035,
            "unit": "iter/sec",
            "range": "stddev: 0.0022192",
            "group": "node",
            "extra": "mean: 24.398 msec\nrounds: 100"
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
          "pythonVersion": "3.8.6",
          "metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "02c8a0ccd59b4ee64dc82ead3646ff0283032633",
          "message": "FIX: Only remove temporary folder if it is present (#4379)\n\nThis was causing an error, when running the tests/engine/test_calc_job.py on OSX,\r\nsince here it is not guaranteed the temporary folder will be created.",
          "timestamp": "2020-10-27T19:53:31+01:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/02c8a0ccd59b4ee64dc82ead3646ff0283032633",
          "distinct": true,
          "tree_id": "2570908a36ef857fa13347b72628b847bf82c0f4"
        },
        "date": 1603825356517,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.7920075616210487,
            "unit": "iter/sec",
            "range": "stddev: 0.010754",
            "group": "engine",
            "extra": "mean: 263.71 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.8996426908646976,
            "unit": "iter/sec",
            "range": "stddev: 0.053979",
            "group": "engine",
            "extra": "mean: 1.1116 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 1.0364643254072912,
            "unit": "iter/sec",
            "range": "stddev: 0.048790",
            "group": "engine",
            "extra": "mean: 964.82 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.18765830809246237,
            "unit": "iter/sec",
            "range": "stddev: 0.085213",
            "group": "engine",
            "extra": "mean: 5.3288 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.21329409720274933,
            "unit": "iter/sec",
            "range": "stddev: 0.089971",
            "group": "engine",
            "extra": "mean: 4.6884 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.9042180898969328,
            "unit": "iter/sec",
            "range": "stddev: 0.014373",
            "group": "engine",
            "extra": "mean: 344.33 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.7063117277677972,
            "unit": "iter/sec",
            "range": "stddev: 0.057842",
            "group": "engine",
            "extra": "mean: 1.4158 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.7638786547874795,
            "unit": "iter/sec",
            "range": "stddev: 0.049585",
            "group": "engine",
            "extra": "mean: 1.3091 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.16463193101123474,
            "unit": "iter/sec",
            "range": "stddev: 0.14514",
            "group": "engine",
            "extra": "mean: 6.0742 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.19447376133533506,
            "unit": "iter/sec",
            "range": "stddev: 0.11416",
            "group": "engine",
            "extra": "mean: 5.1421 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.829953811767409,
            "unit": "iter/sec",
            "range": "stddev: 0.048262",
            "group": "import-export",
            "extra": "mean: 353.36 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.5117678747741956,
            "unit": "iter/sec",
            "range": "stddev: 0.052647",
            "group": "import-export",
            "extra": "mean: 398.13 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 1.431626732376254,
            "unit": "iter/sec",
            "range": "stddev: 0.046042",
            "group": "import-export",
            "extra": "mean: 698.51 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 1.352330208770035,
            "unit": "iter/sec",
            "range": "stddev: 0.055590",
            "group": "import-export",
            "extra": "mean: 739.46 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 876.1105650549055,
            "unit": "iter/sec",
            "range": "stddev: 0.00048196",
            "group": "node",
            "extra": "mean: 1.1414 msec\nrounds: 210"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 206.1066227358361,
            "unit": "iter/sec",
            "range": "stddev: 0.00053683",
            "group": "node",
            "extra": "mean: 4.8519 msec\nrounds: 118"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 197.40436744545906,
            "unit": "iter/sec",
            "range": "stddev: 0.00091113",
            "group": "node",
            "extra": "mean: 5.0657 msec\nrounds: 118"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 217.46794525239662,
            "unit": "iter/sec",
            "range": "stddev: 0.00060841",
            "group": "node",
            "extra": "mean: 4.5984 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 46.62037326694197,
            "unit": "iter/sec",
            "range": "stddev: 0.0019005",
            "group": "node",
            "extra": "mean: 21.450 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 46.06639005492651,
            "unit": "iter/sec",
            "range": "stddev: 0.0023194",
            "group": "node",
            "extra": "mean: 21.708 msec\nrounds: 100"
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
          "pythonVersion": "3.8.6",
          "metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "2f8e8454974f9b82d4d734e5e995bd51053e06da",
          "message": "Refactor Import Archive (#4510)\n\nThis commit builds on [c6d38c1](https://github.com/aiidateam/aiida-core/commit/c6d38c1657b65f540bea653f253920bb602c7ebc),\r\nto refactor the archive in order to decouple it from its export/import to the AiiDA database.\r\n\r\nThe `aiida/tools/importexport/archive` module has been created,\r\nwhich contains the readers and writers used to create and interact with an archive.\r\nEffectively archive formats are now defined by their associated\r\nreader and writer classes, which must inherit and implement the\r\n`ArchiveReaderAbstract` and `ArchiveWriterAbstract` interfaces respectively.\r\n\r\n`aiida/tools/importexport/dbimport` has been refactored,\r\nto interface with this new `ArchiveReaderAbstract` class,\r\nand also utilise the new `progress_reporter` context manager.\r\nBoth the django and sqlalchemy backends have been \"synchronized\",\r\nsuch that conform to exactly the same code structure, which in-turn\r\nhas allowed for the sharing of common code.\r\n\r\nThe commit is intended to be back-compatible,\r\nin that no public API elements have been removed.\r\nHowever, it does:\r\n\r\n- remove the `Archive` class, replaced by the `ReaderJsonZip`/`ReaderJsonTar` classes.\r\n- remove `aiida/tools/importexport/common/progress_bar.py`,\r\n  now replaced by `aiida/common/progress_reporter.py`\r\n- move `aiida/tools/importexport/dbexport/zip.py` → `aiida/tools/importexport/common/zip_folder.py`\r\n\r\nThe `aiida import --verbosity DEBUG` option has been added,\r\nwhich sets the log level of the process, and whether the progress bars are removed.\r\n\r\nThe `verdi export inspect` code has also been refactored, to utilize the `ArchiveReaderAbstract`.\r\nThe `verdi export inspect --data` option has been deprecated,\r\nsince access to the `data.json` file is only an implementation\r\ndetail of the current archive format.",
          "timestamp": "2020-10-27T22:18:15+01:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/2f8e8454974f9b82d4d734e5e995bd51053e06da",
          "distinct": true,
          "tree_id": "f6fc4b6ec56779fe7e3c1697030e876149013395"
        },
        "date": 1603834078515,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.13387295506372,
            "unit": "iter/sec",
            "range": "stddev: 0.055776",
            "group": "engine",
            "extra": "mean: 319.09 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.8000303680647272,
            "unit": "iter/sec",
            "range": "stddev: 0.042324",
            "group": "engine",
            "extra": "mean: 1.2500 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.8872977065087381,
            "unit": "iter/sec",
            "range": "stddev: 0.069981",
            "group": "engine",
            "extra": "mean: 1.1270 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.175808550658791,
            "unit": "iter/sec",
            "range": "stddev: 0.12824",
            "group": "engine",
            "extra": "mean: 5.6880 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.204408165879301,
            "unit": "iter/sec",
            "range": "stddev: 0.15770",
            "group": "engine",
            "extra": "mean: 4.8922 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.788886010693493,
            "unit": "iter/sec",
            "range": "stddev: 0.011147",
            "group": "engine",
            "extra": "mean: 358.57 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.6489662163868735,
            "unit": "iter/sec",
            "range": "stddev: 0.081922",
            "group": "engine",
            "extra": "mean: 1.5409 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.699648449336812,
            "unit": "iter/sec",
            "range": "stddev: 0.089867",
            "group": "engine",
            "extra": "mean: 1.4293 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.15806580581996293,
            "unit": "iter/sec",
            "range": "stddev: 0.10930",
            "group": "engine",
            "extra": "mean: 6.3265 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.18663759423611528,
            "unit": "iter/sec",
            "range": "stddev: 0.10880",
            "group": "engine",
            "extra": "mean: 5.3580 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.7511281079903043,
            "unit": "iter/sec",
            "range": "stddev: 0.042014",
            "group": "import-export",
            "extra": "mean: 363.49 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.407123336058988,
            "unit": "iter/sec",
            "range": "stddev: 0.049679",
            "group": "import-export",
            "extra": "mean: 415.43 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 1.388930115517666,
            "unit": "iter/sec",
            "range": "stddev: 0.047716",
            "group": "import-export",
            "extra": "mean: 719.98 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 1.2630156573701852,
            "unit": "iter/sec",
            "range": "stddev: 0.049509",
            "group": "import-export",
            "extra": "mean: 791.76 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 890.2404866391207,
            "unit": "iter/sec",
            "range": "stddev: 0.00048685",
            "group": "node",
            "extra": "mean: 1.1233 msec\nrounds: 213"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 201.81339654882714,
            "unit": "iter/sec",
            "range": "stddev: 0.00072278",
            "group": "node",
            "extra": "mean: 4.9551 msec\nrounds: 142"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 188.25309213517778,
            "unit": "iter/sec",
            "range": "stddev: 0.0014243",
            "group": "node",
            "extra": "mean: 5.3120 msec\nrounds: 127"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 197.01224585376815,
            "unit": "iter/sec",
            "range": "stddev: 0.0015694",
            "group": "node",
            "extra": "mean: 5.0758 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 40.35819260040347,
            "unit": "iter/sec",
            "range": "stddev: 0.012285",
            "group": "node",
            "extra": "mean: 24.778 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 40.81221392545687,
            "unit": "iter/sec",
            "range": "stddev: 0.010875",
            "group": "node",
            "extra": "mean: 24.502 msec\nrounds: 100"
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
          "pythonVersion": "3.8.6",
          "metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "485957229e931f3441fd1a6b7acb0ce4d3aecc7c",
          "message": "Add group extras to archive (#4521)\n\nGroup extras were introduced recently but not yet exported to AiiDA archives.\r\nThis commit adds group extras to the AiiDA archive.\r\n\r\nInstead of special-casing deserialization of attributes and extras based on the field name, a `convert_type: \"jsonb\"` is introduced, which is used to indicate JSON-binary fields.",
          "timestamp": "2020-10-28T00:49:55+01:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/485957229e931f3441fd1a6b7acb0ce4d3aecc7c",
          "distinct": true,
          "tree_id": "9d9440c23664b864137148e7b9711684afbf731f"
        },
        "date": 1603843148425,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.7035797832958615,
            "unit": "iter/sec",
            "range": "stddev: 0.0098304",
            "group": "engine",
            "extra": "mean: 270.01 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.854129147298245,
            "unit": "iter/sec",
            "range": "stddev: 0.055391",
            "group": "engine",
            "extra": "mean: 1.1708 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.9679818327946071,
            "unit": "iter/sec",
            "range": "stddev: 0.058075",
            "group": "engine",
            "extra": "mean: 1.0331 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.18386536624197594,
            "unit": "iter/sec",
            "range": "stddev: 0.13171",
            "group": "engine",
            "extra": "mean: 5.4388 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.2133677226524225,
            "unit": "iter/sec",
            "range": "stddev: 0.18439",
            "group": "engine",
            "extra": "mean: 4.6867 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.802192450841638,
            "unit": "iter/sec",
            "range": "stddev: 0.0092052",
            "group": "engine",
            "extra": "mean: 356.86 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.6603486175458606,
            "unit": "iter/sec",
            "range": "stddev: 0.057584",
            "group": "engine",
            "extra": "mean: 1.5144 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.7759209946132009,
            "unit": "iter/sec",
            "range": "stddev: 0.049020",
            "group": "engine",
            "extra": "mean: 1.2888 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.16662565876181737,
            "unit": "iter/sec",
            "range": "stddev: 0.092294",
            "group": "engine",
            "extra": "mean: 6.0015 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.1982905160733166,
            "unit": "iter/sec",
            "range": "stddev: 0.091852",
            "group": "engine",
            "extra": "mean: 5.0431 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.970361385817524,
            "unit": "iter/sec",
            "range": "stddev: 0.0062381",
            "group": "import-export",
            "extra": "mean: 336.66 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.4965786916816124,
            "unit": "iter/sec",
            "range": "stddev: 0.054411",
            "group": "import-export",
            "extra": "mean: 400.55 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 1.6241985970643547,
            "unit": "iter/sec",
            "range": "stddev: 0.063085",
            "group": "import-export",
            "extra": "mean: 615.69 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 1.5571176486853422,
            "unit": "iter/sec",
            "range": "stddev: 0.042469",
            "group": "import-export",
            "extra": "mean: 642.21 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 1171.0753469677727,
            "unit": "iter/sec",
            "range": "stddev: 0.000049694",
            "group": "node",
            "extra": "mean: 853.92 usec\nrounds: 195"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 241.37531895610618,
            "unit": "iter/sec",
            "range": "stddev: 0.000078189",
            "group": "node",
            "extra": "mean: 4.1429 msec\nrounds: 134"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 223.18751522993657,
            "unit": "iter/sec",
            "range": "stddev: 0.00011265",
            "group": "node",
            "extra": "mean: 4.4805 msec\nrounds: 131"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 248.5109336686721,
            "unit": "iter/sec",
            "range": "stddev: 0.00013894",
            "group": "node",
            "extra": "mean: 4.0240 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 44.54597513565894,
            "unit": "iter/sec",
            "range": "stddev: 0.014564",
            "group": "node",
            "extra": "mean: 22.449 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 47.144873750675366,
            "unit": "iter/sec",
            "range": "stddev: 0.0014713",
            "group": "node",
            "extra": "mean: 21.211 msec\nrounds: 100"
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
          "pythonVersion": "3.8.6",
          "metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "55f8706e8ecfb37745efe6bc838719b8dceed1fa",
          "message": "Fix: Add missing entry point groups to the mapping (#4395)\n\nSome new entrypoints had been introduced, but they weren't in the mapping,\r\nso they couldn't be accessed for instance with `verdi plugin list`.",
          "timestamp": "2020-10-28T12:46:55+01:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/55f8706e8ecfb37745efe6bc838719b8dceed1fa",
          "distinct": true,
          "tree_id": "21b4ad14fbb4ea81ec05547e67f25347688b174b"
        },
        "date": 1603886261038,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 2.932439013253493,
            "unit": "iter/sec",
            "range": "stddev: 0.056728",
            "group": "engine",
            "extra": "mean: 341.01 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.7431684090717607,
            "unit": "iter/sec",
            "range": "stddev: 0.051177",
            "group": "engine",
            "extra": "mean: 1.3456 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.8116819310909106,
            "unit": "iter/sec",
            "range": "stddev: 0.077199",
            "group": "engine",
            "extra": "mean: 1.2320 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.15471318990503163,
            "unit": "iter/sec",
            "range": "stddev: 0.14256",
            "group": "engine",
            "extra": "mean: 6.4636 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.17763563717677677,
            "unit": "iter/sec",
            "range": "stddev: 0.098638",
            "group": "engine",
            "extra": "mean: 5.6295 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.3554625433856713,
            "unit": "iter/sec",
            "range": "stddev: 0.019691",
            "group": "engine",
            "extra": "mean: 424.55 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.5620920996315294,
            "unit": "iter/sec",
            "range": "stddev: 0.069351",
            "group": "engine",
            "extra": "mean: 1.7791 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.6338753518069808,
            "unit": "iter/sec",
            "range": "stddev: 0.053205",
            "group": "engine",
            "extra": "mean: 1.5776 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.136902316069182,
            "unit": "iter/sec",
            "range": "stddev: 0.14899",
            "group": "engine",
            "extra": "mean: 7.3045 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.1614309139482974,
            "unit": "iter/sec",
            "range": "stddev: 0.13275",
            "group": "engine",
            "extra": "mean: 6.1946 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.596118193213423,
            "unit": "iter/sec",
            "range": "stddev: 0.012191",
            "group": "import-export",
            "extra": "mean: 385.19 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.3022781349498653,
            "unit": "iter/sec",
            "range": "stddev: 0.017340",
            "group": "import-export",
            "extra": "mean: 434.35 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 1.3555958169596722,
            "unit": "iter/sec",
            "range": "stddev: 0.088213",
            "group": "import-export",
            "extra": "mean: 737.68 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 1.2709954287798815,
            "unit": "iter/sec",
            "range": "stddev: 0.079308",
            "group": "import-export",
            "extra": "mean: 786.78 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 836.3233646166008,
            "unit": "iter/sec",
            "range": "stddev: 0.00071519",
            "group": "node",
            "extra": "mean: 1.1957 msec\nrounds: 171"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 193.58166787947087,
            "unit": "iter/sec",
            "range": "stddev: 0.00095696",
            "group": "node",
            "extra": "mean: 5.1658 msec\nrounds: 108"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 177.11407841044044,
            "unit": "iter/sec",
            "range": "stddev: 0.00069711",
            "group": "node",
            "extra": "mean: 5.6461 msec\nrounds: 108"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 193.08125229399155,
            "unit": "iter/sec",
            "range": "stddev: 0.00075375",
            "group": "node",
            "extra": "mean: 5.1792 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 36.3945278933365,
            "unit": "iter/sec",
            "range": "stddev: 0.0029342",
            "group": "node",
            "extra": "mean: 27.477 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 37.40733340807274,
            "unit": "iter/sec",
            "range": "stddev: 0.0030189",
            "group": "node",
            "extra": "mean: 26.733 msec\nrounds: 100"
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
          "pythonVersion": "3.8.6",
          "metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "9ff07c166a559f98b5b2be71537814ec00d3f18d",
          "message": "Add `reset` method to`ProgressReporterAbstract` (#4522)\n\nThis PR adds the `update` method to the progress reporter.\r\nThis in-turn, allows for the implementation of a callback mechanism in `ArchiveReaderAbstract.iter_node_repos`.\r\nThe callback implementation is taken from the\r\n[disk-objectstore](https://github.com/aiidateam/disk-objectstore) package,\r\nand so facilitates a later migration to its use.\r\n\r\nThe PR also moves the (common) repository import code out of the backend specific modules,\r\nreducing code duplication.",
          "timestamp": "2020-10-28T20:17:44+01:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/9ff07c166a559f98b5b2be71537814ec00d3f18d",
          "distinct": true,
          "tree_id": "5145fa774377f62a8c24f72541ed35cae33ccfb2"
        },
        "date": 1603913200811,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.6370586795998237,
            "unit": "iter/sec",
            "range": "stddev: 0.056315",
            "group": "engine",
            "extra": "mean: 274.95 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.8955789075900864,
            "unit": "iter/sec",
            "range": "stddev: 0.055579",
            "group": "engine",
            "extra": "mean: 1.1166 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 1.0186259164271385,
            "unit": "iter/sec",
            "range": "stddev: 0.067051",
            "group": "engine",
            "extra": "mean: 981.71 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.1953597849930124,
            "unit": "iter/sec",
            "range": "stddev: 0.089317",
            "group": "engine",
            "extra": "mean: 5.1188 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.2221159491237313,
            "unit": "iter/sec",
            "range": "stddev: 0.17806",
            "group": "engine",
            "extra": "mean: 4.5022 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 3.1095900049922203,
            "unit": "iter/sec",
            "range": "stddev: 0.0052773",
            "group": "engine",
            "extra": "mean: 321.59 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.7266102909384575,
            "unit": "iter/sec",
            "range": "stddev: 0.082059",
            "group": "engine",
            "extra": "mean: 1.3763 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.7966466483047688,
            "unit": "iter/sec",
            "range": "stddev: 0.092243",
            "group": "engine",
            "extra": "mean: 1.2553 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.1732957367765649,
            "unit": "iter/sec",
            "range": "stddev: 0.10167",
            "group": "engine",
            "extra": "mean: 5.7705 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.20413556277329273,
            "unit": "iter/sec",
            "range": "stddev: 0.13394",
            "group": "engine",
            "extra": "mean: 4.8987 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.783983453472346,
            "unit": "iter/sec",
            "range": "stddev: 0.060376",
            "group": "import-export",
            "extra": "mean: 359.20 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.4756449576857054,
            "unit": "iter/sec",
            "range": "stddev: 0.055595",
            "group": "import-export",
            "extra": "mean: 403.94 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 1.4649038060490116,
            "unit": "iter/sec",
            "range": "stddev: 0.068450",
            "group": "import-export",
            "extra": "mean: 682.64 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 1.3814116038256365,
            "unit": "iter/sec",
            "range": "stddev: 0.050244",
            "group": "import-export",
            "extra": "mean: 723.90 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 989.5703024308455,
            "unit": "iter/sec",
            "range": "stddev: 0.00020508",
            "group": "node",
            "extra": "mean: 1.0105 msec\nrounds: 212"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 214.12311804124346,
            "unit": "iter/sec",
            "range": "stddev: 0.00053785",
            "group": "node",
            "extra": "mean: 4.6702 msec\nrounds: 141"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 204.00500691547882,
            "unit": "iter/sec",
            "range": "stddev: 0.00068285",
            "group": "node",
            "extra": "mean: 4.9018 msec\nrounds: 120"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 223.00528396743684,
            "unit": "iter/sec",
            "range": "stddev: 0.00069383",
            "group": "node",
            "extra": "mean: 4.4842 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 48.01981961582165,
            "unit": "iter/sec",
            "range": "stddev: 0.0012281",
            "group": "node",
            "extra": "mean: 20.825 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 44.87809920332677,
            "unit": "iter/sec",
            "range": "stddev: 0.0025285",
            "group": "node",
            "extra": "mean: 22.283 msec\nrounds: 100"
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
          "pythonVersion": "3.8.6",
          "metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "8326050c0ec8ecca1f5d463b5ecd4f4b236847ee",
          "message": "Refactor archive migrations (#4532)\n\nThis commit follows refactors to the archive writing and reading process,\r\nto provide an implementation agnostic interface for the migration of archives\r\n(i.e. independent of the internal structure of the archive).\r\nThis will allow for subsequent changes to the archive format.\r\n\r\nTo facilitate this:\r\n\r\n- `MIGRATE_FUNCTIONS` now includes both the to/from versions of the migration,\r\n- this allows for a change, from a recursive migration approach to pre-computing the migration pathway, then applying the migrations iteratively\r\n- this also allows for a progress bar of the migration steps\r\n- the signature of migration step functions has been changed, such that they now only receive the uncompressed archive folder,\r\n  and not also specifically the `data.json` and `metadata.json` dictionaries.\r\n- instead, the folder is wrapped in a new `CacheFolder` class,\r\n  which caches file writes in memory,\r\n  such that reading of the files from the file system only happen once,\r\n  and they are written after all the migrations have finished.\r\n- the `--verbose` flag has been added to `verdi export migrate`,\r\n  to allow for control of the stdout message verbosity.\r\n- the extracting/compressing of tar/zip has been generalised into `archive/common.py`;\r\n  `safe_extract_tar`, `safe_extract_zip`, `compress_folder_tar`, `compress_folder_zip`.\r\n  These include callbacks, to be used by the progress reporter to create progress bars.\r\n- all migration unit tests have been converted to pytest\r\n\r\nCo-authored-by: Leopold Talirz <leopold.talirz@gmail.com>",
          "timestamp": "2020-11-03T10:31:07+01:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/8326050c0ec8ecca1f5d463b5ecd4f4b236847ee",
          "distinct": true,
          "tree_id": "511789f7a2607a15e83d8d4d2dc2be79c8cb2f1d"
        },
        "date": 1604396472963,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.213664406445895,
            "unit": "iter/sec",
            "range": "stddev: 0.059448",
            "group": "engine",
            "extra": "mean: 311.17 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.8025129642504542,
            "unit": "iter/sec",
            "range": "stddev: 0.048956",
            "group": "engine",
            "extra": "mean: 1.2461 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.8958494236680363,
            "unit": "iter/sec",
            "range": "stddev: 0.059772",
            "group": "engine",
            "extra": "mean: 1.1163 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.1715204885379928,
            "unit": "iter/sec",
            "range": "stddev: 0.18741",
            "group": "engine",
            "extra": "mean: 5.8302 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.19990974716625734,
            "unit": "iter/sec",
            "range": "stddev: 0.13904",
            "group": "engine",
            "extra": "mean: 5.0023 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.5927496865278816,
            "unit": "iter/sec",
            "range": "stddev: 0.011850",
            "group": "engine",
            "extra": "mean: 385.69 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.6165756785269892,
            "unit": "iter/sec",
            "range": "stddev: 0.078984",
            "group": "engine",
            "extra": "mean: 1.6219 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.6988705761301917,
            "unit": "iter/sec",
            "range": "stddev: 0.058907",
            "group": "engine",
            "extra": "mean: 1.4309 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.1536209989336415,
            "unit": "iter/sec",
            "range": "stddev: 0.18165",
            "group": "engine",
            "extra": "mean: 6.5095 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.17938434288753388,
            "unit": "iter/sec",
            "range": "stddev: 0.20799",
            "group": "engine",
            "extra": "mean: 5.5746 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.6486606267512065,
            "unit": "iter/sec",
            "range": "stddev: 0.050885",
            "group": "import-export",
            "extra": "mean: 377.55 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.379127740087249,
            "unit": "iter/sec",
            "range": "stddev: 0.018818",
            "group": "import-export",
            "extra": "mean: 420.32 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 1.4900897381771723,
            "unit": "iter/sec",
            "range": "stddev: 0.047776",
            "group": "import-export",
            "extra": "mean: 671.10 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 1.3879934425906437,
            "unit": "iter/sec",
            "range": "stddev: 0.061434",
            "group": "import-export",
            "extra": "mean: 720.46 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 1018.015803173921,
            "unit": "iter/sec",
            "range": "stddev: 0.00026860",
            "group": "node",
            "extra": "mean: 982.30 usec\nrounds: 181"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 209.21885422592786,
            "unit": "iter/sec",
            "range": "stddev: 0.00091184",
            "group": "node",
            "extra": "mean: 4.7797 msec\nrounds: 125"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 197.64958317608068,
            "unit": "iter/sec",
            "range": "stddev: 0.00052504",
            "group": "node",
            "extra": "mean: 5.0595 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 211.5978956436487,
            "unit": "iter/sec",
            "range": "stddev: 0.00068683",
            "group": "node",
            "extra": "mean: 4.7259 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 38.60111799599948,
            "unit": "iter/sec",
            "range": "stddev: 0.016901",
            "group": "node",
            "extra": "mean: 25.906 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 44.529349941342446,
            "unit": "iter/sec",
            "range": "stddev: 0.0021199",
            "group": "node",
            "extra": "mean: 22.457 msec\nrounds: 100"
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
          "pythonVersion": "3.8.6",
          "metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "d675574bfa8518ca97275384779493520a0304e1",
          "message": "Simplify Hill notation for `get_formula()` and add test (#4536)\n\nSimplify hill notation sorting (@csadorf)\r\nAdd a test for `get_formula()` to test 'hill' and 'hill_compact' (@CasperWA)\r\n\r\nCo-authored-by: Carl Simon Adorf <csadorf@umich.edu>",
          "timestamp": "2020-11-03T14:35:22+01:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/d675574bfa8518ca97275384779493520a0304e1",
          "distinct": true,
          "tree_id": "16848932c7934e293ff72491e291ea596d988aec"
        },
        "date": 1604411131651,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.390006881914106,
            "unit": "iter/sec",
            "range": "stddev: 0.019713",
            "group": "engine",
            "extra": "mean: 294.98 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.8144781972081758,
            "unit": "iter/sec",
            "range": "stddev: 0.053662",
            "group": "engine",
            "extra": "mean: 1.2278 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.9277239513238069,
            "unit": "iter/sec",
            "range": "stddev: 0.067806",
            "group": "engine",
            "extra": "mean: 1.0779 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.17615421034327178,
            "unit": "iter/sec",
            "range": "stddev: 0.078583",
            "group": "engine",
            "extra": "mean: 5.6768 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.2018429597863731,
            "unit": "iter/sec",
            "range": "stddev: 0.082452",
            "group": "engine",
            "extra": "mean: 4.9543 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.807846529710429,
            "unit": "iter/sec",
            "range": "stddev: 0.017737",
            "group": "engine",
            "extra": "mean: 356.14 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.6474945644728478,
            "unit": "iter/sec",
            "range": "stddev: 0.068983",
            "group": "engine",
            "extra": "mean: 1.5444 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.722123513799117,
            "unit": "iter/sec",
            "range": "stddev: 0.074253",
            "group": "engine",
            "extra": "mean: 1.3848 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.15621101078369187,
            "unit": "iter/sec",
            "range": "stddev: 0.11100",
            "group": "engine",
            "extra": "mean: 6.4016 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.18733201262042712,
            "unit": "iter/sec",
            "range": "stddev: 0.10430",
            "group": "engine",
            "extra": "mean: 5.3381 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.8751757141472294,
            "unit": "iter/sec",
            "range": "stddev: 0.011060",
            "group": "import-export",
            "extra": "mean: 347.80 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.5133845213552206,
            "unit": "iter/sec",
            "range": "stddev: 0.0071411",
            "group": "import-export",
            "extra": "mean: 397.87 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 1.5512203589269133,
            "unit": "iter/sec",
            "range": "stddev: 0.052569",
            "group": "import-export",
            "extra": "mean: 644.65 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 1.4219978859818636,
            "unit": "iter/sec",
            "range": "stddev: 0.078148",
            "group": "import-export",
            "extra": "mean: 703.24 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 1041.3285613494202,
            "unit": "iter/sec",
            "range": "stddev: 0.00035035",
            "group": "node",
            "extra": "mean: 960.31 usec\nrounds: 206"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 229.7109290036041,
            "unit": "iter/sec",
            "range": "stddev: 0.00079714",
            "group": "node",
            "extra": "mean: 4.3533 msec\nrounds: 133"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 203.7389391908914,
            "unit": "iter/sec",
            "range": "stddev: 0.0010415",
            "group": "node",
            "extra": "mean: 4.9082 msec\nrounds: 122"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 227.92424042596357,
            "unit": "iter/sec",
            "range": "stddev: 0.00055121",
            "group": "node",
            "extra": "mean: 4.3874 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 44.23964575404449,
            "unit": "iter/sec",
            "range": "stddev: 0.0020054",
            "group": "node",
            "extra": "mean: 22.604 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 42.48642716063657,
            "unit": "iter/sec",
            "range": "stddev: 0.0030417",
            "group": "node",
            "extra": "mean: 23.537 msec\nrounds: 100"
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
          "pythonVersion": "3.8.6",
          "metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "2c0f9a9b78aa9591bfa46c89a2fdd37563b4c747",
          "message": "CI: Add official support for Python 3.9 (#4301)\n\nUpdating of Conda in the `install-with-conda` job of the `test-install`\r\nworkflow is disabled because it fails for as of yet unknown reasons.",
          "timestamp": "2020-11-05T11:05:04+01:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/2c0f9a9b78aa9591bfa46c89a2fdd37563b4c747",
          "distinct": true,
          "tree_id": "13d0e32e8a0c18ff4bb8f7507945c5e99ceb7864"
        },
        "date": 1604571268071,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.4458839777528634,
            "unit": "iter/sec",
            "range": "stddev: 0.060998",
            "group": "engine",
            "extra": "mean: 290.20 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.8691291386478714,
            "unit": "iter/sec",
            "range": "stddev: 0.065690",
            "group": "engine",
            "extra": "mean: 1.1506 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.9728472802209206,
            "unit": "iter/sec",
            "range": "stddev: 0.062739",
            "group": "engine",
            "extra": "mean: 1.0279 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.18608155872027762,
            "unit": "iter/sec",
            "range": "stddev: 0.13247",
            "group": "engine",
            "extra": "mean: 5.3740 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.21356736648124888,
            "unit": "iter/sec",
            "range": "stddev: 0.098166",
            "group": "engine",
            "extra": "mean: 4.6824 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.9228117386612626,
            "unit": "iter/sec",
            "range": "stddev: 0.0089023",
            "group": "engine",
            "extra": "mean: 342.14 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.6800070066317214,
            "unit": "iter/sec",
            "range": "stddev: 0.075739",
            "group": "engine",
            "extra": "mean: 1.4706 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.7566545881090269,
            "unit": "iter/sec",
            "range": "stddev: 0.058980",
            "group": "engine",
            "extra": "mean: 1.3216 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.16203641501187202,
            "unit": "iter/sec",
            "range": "stddev: 0.12523",
            "group": "engine",
            "extra": "mean: 6.1715 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.195547962100709,
            "unit": "iter/sec",
            "range": "stddev: 0.17829",
            "group": "engine",
            "extra": "mean: 5.1138 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.9265871446000475,
            "unit": "iter/sec",
            "range": "stddev: 0.0098452",
            "group": "import-export",
            "extra": "mean: 341.69 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.5119445348982974,
            "unit": "iter/sec",
            "range": "stddev: 0.055111",
            "group": "import-export",
            "extra": "mean: 398.10 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 1.600773655188249,
            "unit": "iter/sec",
            "range": "stddev: 0.067930",
            "group": "import-export",
            "extra": "mean: 624.70 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 1.4883691408372879,
            "unit": "iter/sec",
            "range": "stddev: 0.043706",
            "group": "import-export",
            "extra": "mean: 671.88 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 1051.2602477562002,
            "unit": "iter/sec",
            "range": "stddev: 0.00036072",
            "group": "node",
            "extra": "mean: 951.24 usec\nrounds: 191"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 231.53211753314528,
            "unit": "iter/sec",
            "range": "stddev: 0.00044666",
            "group": "node",
            "extra": "mean: 4.3191 msec\nrounds: 134"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 216.76657781732848,
            "unit": "iter/sec",
            "range": "stddev: 0.00033144",
            "group": "node",
            "extra": "mean: 4.6133 msec\nrounds: 122"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 233.92233214323076,
            "unit": "iter/sec",
            "range": "stddev: 0.00053212",
            "group": "node",
            "extra": "mean: 4.2749 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 42.575517057816064,
            "unit": "iter/sec",
            "range": "stddev: 0.016248",
            "group": "node",
            "extra": "mean: 23.488 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 46.53839499518985,
            "unit": "iter/sec",
            "range": "stddev: 0.0018445",
            "group": "node",
            "extra": "mean: 21.488 msec\nrounds: 100"
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
          "pythonVersion": "3.8.6",
          "metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "64ae3c8027f5391e79797ef09b94076e4e0beb03",
          "message": "Merge remote-tracking branch 'origin/master' into develop",
          "timestamp": "2020-11-06T14:58:26+01:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/64ae3c8027f5391e79797ef09b94076e4e0beb03",
          "distinct": false,
          "tree_id": "f11e1b02d5c760e9f61cb07343a1a632cd84e650"
        },
        "date": 1604672088179,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.1785097386467367,
            "unit": "iter/sec",
            "range": "stddev: 0.050276",
            "group": "engine",
            "extra": "mean: 314.61 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.8052421752620043,
            "unit": "iter/sec",
            "range": "stddev: 0.068457",
            "group": "engine",
            "extra": "mean: 1.2419 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.9261600374014674,
            "unit": "iter/sec",
            "range": "stddev: 0.078906",
            "group": "engine",
            "extra": "mean: 1.0797 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.17427143386705424,
            "unit": "iter/sec",
            "range": "stddev: 0.13775",
            "group": "engine",
            "extra": "mean: 5.7382 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.19768566822642722,
            "unit": "iter/sec",
            "range": "stddev: 0.11226",
            "group": "engine",
            "extra": "mean: 5.0585 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.6955975715839586,
            "unit": "iter/sec",
            "range": "stddev: 0.0096431",
            "group": "engine",
            "extra": "mean: 370.98 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.6431299572160434,
            "unit": "iter/sec",
            "range": "stddev: 0.092301",
            "group": "engine",
            "extra": "mean: 1.5549 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.7212749216508517,
            "unit": "iter/sec",
            "range": "stddev: 0.069534",
            "group": "engine",
            "extra": "mean: 1.3864 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.154884684737514,
            "unit": "iter/sec",
            "range": "stddev: 0.13585",
            "group": "engine",
            "extra": "mean: 6.4564 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.18648257986282002,
            "unit": "iter/sec",
            "range": "stddev: 0.093730",
            "group": "engine",
            "extra": "mean: 5.3624 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.8669298470996467,
            "unit": "iter/sec",
            "range": "stddev: 0.0074479",
            "group": "import-export",
            "extra": "mean: 348.81 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.496579617787849,
            "unit": "iter/sec",
            "range": "stddev: 0.049160",
            "group": "import-export",
            "extra": "mean: 400.55 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 1.5284215029914188,
            "unit": "iter/sec",
            "range": "stddev: 0.068491",
            "group": "import-export",
            "extra": "mean: 654.27 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 1.4346475554970615,
            "unit": "iter/sec",
            "range": "stddev: 0.043236",
            "group": "import-export",
            "extra": "mean: 697.04 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 1134.6836301280314,
            "unit": "iter/sec",
            "range": "stddev: 0.000066768",
            "group": "node",
            "extra": "mean: 881.30 usec\nrounds: 195"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 235.54554509183623,
            "unit": "iter/sec",
            "range": "stddev: 0.00019277",
            "group": "node",
            "extra": "mean: 4.2455 msec\nrounds: 132"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 206.3827428613278,
            "unit": "iter/sec",
            "range": "stddev: 0.00059192",
            "group": "node",
            "extra": "mean: 4.8454 msec\nrounds: 127"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 224.82899955993852,
            "unit": "iter/sec",
            "range": "stddev: 0.00048598",
            "group": "node",
            "extra": "mean: 4.4478 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 43.53170836294881,
            "unit": "iter/sec",
            "range": "stddev: 0.014123",
            "group": "node",
            "extra": "mean: 22.972 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 42.8165635874502,
            "unit": "iter/sec",
            "range": "stddev: 0.012629",
            "group": "node",
            "extra": "mean: 23.355 msec\nrounds: 100"
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
          "pythonVersion": "3.8.6",
          "metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "ac4c881ad12cca669d4b7b1745d6dd5f0553a1ba",
          "message": "Make process functions submittable (#4539)\n\nThe limitation that process functions were not submittable, meaning they\r\ncould not be sent to a daemon worker but could only be run by the current\r\ninterpreter, was a historical one. Before the introduction of the system\r\nof processes in v1.0, a `calcfunction` was nothing more than the\r\nexecution of a normal function. However, now, a process function creates\r\na `Process` instance in the background, just as any other process. This\r\nmeans it can also be serialized and deserialized by a daemon worker.\r\n\r\nHere we remove the limitation of process functions not being submittable\r\nsimply by removing the check. Note that there is no need to change the\r\nimplementation other than adding two attributes on the decorated function\r\nthat specify the corresponding process class and the method that allows\r\nto recreate the instance from the serialized instance.\r\n\r\nCo-authored-by: Sebastiaan Huber <mail@sphuber.net>",
          "timestamp": "2020-11-08T11:33:48+01:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/ac4c881ad12cca669d4b7b1745d6dd5f0553a1ba",
          "distinct": true,
          "tree_id": "2e9b791114f515b0a96484fcbffa0b77a6ed688f"
        },
        "date": 1604832168849,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.758547287015132,
            "unit": "iter/sec",
            "range": "stddev: 0.055565",
            "group": "engine",
            "extra": "mean: 266.06 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.9457513683246962,
            "unit": "iter/sec",
            "range": "stddev: 0.044715",
            "group": "engine",
            "extra": "mean: 1.0574 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 1.0831217373514488,
            "unit": "iter/sec",
            "range": "stddev: 0.063910",
            "group": "engine",
            "extra": "mean: 923.26 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.19317438338076187,
            "unit": "iter/sec",
            "range": "stddev: 0.074964",
            "group": "engine",
            "extra": "mean: 5.1767 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.22313658751241564,
            "unit": "iter/sec",
            "range": "stddev: 0.063568",
            "group": "engine",
            "extra": "mean: 4.4816 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 3.0068369973815634,
            "unit": "iter/sec",
            "range": "stddev: 0.025617",
            "group": "engine",
            "extra": "mean: 332.58 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.7511980186755663,
            "unit": "iter/sec",
            "range": "stddev: 0.061216",
            "group": "engine",
            "extra": "mean: 1.3312 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.8357493845838844,
            "unit": "iter/sec",
            "range": "stddev: 0.050446",
            "group": "engine",
            "extra": "mean: 1.1965 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.17028710488728702,
            "unit": "iter/sec",
            "range": "stddev: 0.12660",
            "group": "engine",
            "extra": "mean: 5.8724 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.20415785108276485,
            "unit": "iter/sec",
            "range": "stddev: 0.096139",
            "group": "engine",
            "extra": "mean: 4.8982 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 3.1247089358038194,
            "unit": "iter/sec",
            "range": "stddev: 0.016605",
            "group": "import-export",
            "extra": "mean: 320.03 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.854356732448767,
            "unit": "iter/sec",
            "range": "stddev: 0.013853",
            "group": "import-export",
            "extra": "mean: 350.34 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 1.7273138666024135,
            "unit": "iter/sec",
            "range": "stddev: 0.033905",
            "group": "import-export",
            "extra": "mean: 578.93 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 1.5686673845357357,
            "unit": "iter/sec",
            "range": "stddev: 0.061481",
            "group": "import-export",
            "extra": "mean: 637.48 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 1075.8326309340976,
            "unit": "iter/sec",
            "range": "stddev: 0.00018092",
            "group": "node",
            "extra": "mean: 929.51 usec\nrounds: 199"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 212.14044944579857,
            "unit": "iter/sec",
            "range": "stddev: 0.0056157",
            "group": "node",
            "extra": "mean: 4.7139 msec\nrounds: 150"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 217.41361024898802,
            "unit": "iter/sec",
            "range": "stddev: 0.00038960",
            "group": "node",
            "extra": "mean: 4.5995 msec\nrounds: 126"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 253.52487035888876,
            "unit": "iter/sec",
            "range": "stddev: 0.00062368",
            "group": "node",
            "extra": "mean: 3.9444 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 50.10189274535041,
            "unit": "iter/sec",
            "range": "stddev: 0.0017959",
            "group": "node",
            "extra": "mean: 19.959 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 49.80756151304888,
            "unit": "iter/sec",
            "range": "stddev: 0.0018903",
            "group": "node",
            "extra": "mean: 20.077 msec\nrounds: 100"
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
          "pythonVersion": "3.8.6",
          "metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "c42a86b9417cf2f1072df5c87a55d57023bc4fc4",
          "message": "`SlurmScheduler`: fix bug in validation of job resources (#4555)\n\nThe `SlurmJobResource` resource class used by the `SlurmScheduler`\r\nplugin contained a bug in the `validate_resources` methods that would\r\ncause a float value to be set for the `num_cores_per_mpiproc` field in\r\ncertain cases. This would cause the submit script to fail because SLURM\r\nonly accepts integers for the corresponding `--ncpus-per-task` flag.\r\n\r\nThe reason is that the code was incorrectly using `isinstance(_, int)`\r\nto check that the divison of `num_cores_per_machine` over\r\n`num_mpiprocs_per_machine` is an integer. In addition to the negation\r\nmissing in the conditional, this is not the correct way of checking\r\nwhether a division is an integer. Instead it should check that the value\r\nis identical after it is cast to `int`.",
          "timestamp": "2020-11-11T16:35:16+01:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/c42a86b9417cf2f1072df5c87a55d57023bc4fc4",
          "distinct": true,
          "tree_id": "78fdee327c130ffca7355f3ce68f1f20be140247"
        },
        "date": 1605109449270,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.8237288310318895,
            "unit": "iter/sec",
            "range": "stddev: 0.050252",
            "group": "engine",
            "extra": "mean: 261.52 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.9736415533758869,
            "unit": "iter/sec",
            "range": "stddev: 0.042293",
            "group": "engine",
            "extra": "mean: 1.0271 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 1.0755579418667944,
            "unit": "iter/sec",
            "range": "stddev: 0.055547",
            "group": "engine",
            "extra": "mean: 929.75 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.19706715455194881,
            "unit": "iter/sec",
            "range": "stddev: 0.14302",
            "group": "engine",
            "extra": "mean: 5.0744 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.22965021371532557,
            "unit": "iter/sec",
            "range": "stddev: 0.093832",
            "group": "engine",
            "extra": "mean: 4.3544 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 3.2050080573886457,
            "unit": "iter/sec",
            "range": "stddev: 0.0058233",
            "group": "engine",
            "extra": "mean: 312.01 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.746801879556078,
            "unit": "iter/sec",
            "range": "stddev: 0.052953",
            "group": "engine",
            "extra": "mean: 1.3390 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.861522054606416,
            "unit": "iter/sec",
            "range": "stddev: 0.046749",
            "group": "engine",
            "extra": "mean: 1.1607 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.17653102104884363,
            "unit": "iter/sec",
            "range": "stddev: 0.11573",
            "group": "engine",
            "extra": "mean: 5.6647 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.20898788841992758,
            "unit": "iter/sec",
            "range": "stddev: 0.11508",
            "group": "engine",
            "extra": "mean: 4.7850 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 3.1138059398151126,
            "unit": "iter/sec",
            "range": "stddev: 0.047881",
            "group": "import-export",
            "extra": "mean: 321.15 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.694911402466653,
            "unit": "iter/sec",
            "range": "stddev: 0.045470",
            "group": "import-export",
            "extra": "mean: 371.07 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 1.7315535571832026,
            "unit": "iter/sec",
            "range": "stddev: 0.047701",
            "group": "import-export",
            "extra": "mean: 577.52 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 1.5607049115544072,
            "unit": "iter/sec",
            "range": "stddev: 0.045169",
            "group": "import-export",
            "extra": "mean: 640.74 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 1190.5087943340186,
            "unit": "iter/sec",
            "range": "stddev: 0.000056727",
            "group": "node",
            "extra": "mean: 839.98 usec\nrounds: 215"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 243.6583262900322,
            "unit": "iter/sec",
            "range": "stddev: 0.00015427",
            "group": "node",
            "extra": "mean: 4.1041 msec\nrounds: 147"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 221.70484522637298,
            "unit": "iter/sec",
            "range": "stddev: 0.00040769",
            "group": "node",
            "extra": "mean: 4.5105 msec\nrounds: 135"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 231.36479221949594,
            "unit": "iter/sec",
            "range": "stddev: 0.0011425",
            "group": "node",
            "extra": "mean: 4.3222 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 47.109171062488436,
            "unit": "iter/sec",
            "range": "stddev: 0.013386",
            "group": "node",
            "extra": "mean: 21.227 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 50.031240632347156,
            "unit": "iter/sec",
            "range": "stddev: 0.0011187",
            "group": "node",
            "extra": "mean: 19.988 msec\nrounds: 100"
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
          "pythonVersion": "3.8.6",
          "metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "008580e3316ad48b56f2385d245398ac0c78a49b",
          "message": "`verdi group delete`: deprecate and ignore the `--clear` option (#4357)\n\nNote that the option is still there but no longer makes a difference. It\r\nnow merely prints a deprecation warning, but is otherwise ignored. The\r\nreason is that otherwise, users would be forced to continue to use it\r\ndespite it raising a deprecation warning. The only danger is for users\r\nthat have come to depend on the slightly weird behavior that in order\r\nto delete non-empty groups, one would have to pass them `--clear` option\r\notherwise the command would fail. After this change, this would now\r\ndelete the group without complaining, which may break this use case.\r\nThis use case was estimate to be unlikely and so it was accepted to\r\nsimply ignore the option.",
          "timestamp": "2020-11-11T18:05:13+01:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/008580e3316ad48b56f2385d245398ac0c78a49b",
          "distinct": true,
          "tree_id": "1d7c58ee452f0c10fd2c90a385a73b83193f1b88"
        },
        "date": 1605114960899,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 2.8840267650131386,
            "unit": "iter/sec",
            "range": "stddev: 0.063434",
            "group": "engine",
            "extra": "mean: 346.74 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.7362590257569682,
            "unit": "iter/sec",
            "range": "stddev: 0.057180",
            "group": "engine",
            "extra": "mean: 1.3582 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.8076489312756253,
            "unit": "iter/sec",
            "range": "stddev: 0.069535",
            "group": "engine",
            "extra": "mean: 1.2382 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.159485674518106,
            "unit": "iter/sec",
            "range": "stddev: 0.077665",
            "group": "engine",
            "extra": "mean: 6.2702 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.1820158337221002,
            "unit": "iter/sec",
            "range": "stddev: 0.13773",
            "group": "engine",
            "extra": "mean: 5.4940 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.426574661328346,
            "unit": "iter/sec",
            "range": "stddev: 0.0096897",
            "group": "engine",
            "extra": "mean: 412.10 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.5671896030516651,
            "unit": "iter/sec",
            "range": "stddev: 0.074845",
            "group": "engine",
            "extra": "mean: 1.7631 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.6500063775148228,
            "unit": "iter/sec",
            "range": "stddev: 0.066705",
            "group": "engine",
            "extra": "mean: 1.5384 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.14015778681838773,
            "unit": "iter/sec",
            "range": "stddev: 0.085535",
            "group": "engine",
            "extra": "mean: 7.1348 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.16465273452408627,
            "unit": "iter/sec",
            "range": "stddev: 0.14522",
            "group": "engine",
            "extra": "mean: 6.0734 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.3921452337219016,
            "unit": "iter/sec",
            "range": "stddev: 0.060452",
            "group": "import-export",
            "extra": "mean: 418.03 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.0860745994180165,
            "unit": "iter/sec",
            "range": "stddev: 0.059218",
            "group": "import-export",
            "extra": "mean: 479.37 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 1.2203439429836598,
            "unit": "iter/sec",
            "range": "stddev: 0.073863",
            "group": "import-export",
            "extra": "mean: 819.44 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 1.1514355549792525,
            "unit": "iter/sec",
            "range": "stddev: 0.059406",
            "group": "import-export",
            "extra": "mean: 868.48 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 745.5619559582864,
            "unit": "iter/sec",
            "range": "stddev: 0.00051007",
            "group": "node",
            "extra": "mean: 1.3413 msec\nrounds: 181"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 182.56759498526716,
            "unit": "iter/sec",
            "range": "stddev: 0.00082975",
            "group": "node",
            "extra": "mean: 5.4774 msec\nrounds: 117"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 172.62499424905022,
            "unit": "iter/sec",
            "range": "stddev: 0.00066173",
            "group": "node",
            "extra": "mean: 5.7929 msec\nrounds: 114"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 183.84159421399153,
            "unit": "iter/sec",
            "range": "stddev: 0.00078683",
            "group": "node",
            "extra": "mean: 5.4395 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 38.2671217021319,
            "unit": "iter/sec",
            "range": "stddev: 0.0027910",
            "group": "node",
            "extra": "mean: 26.132 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 34.1795811510953,
            "unit": "iter/sec",
            "range": "stddev: 0.021461",
            "group": "node",
            "extra": "mean: 29.257 msec\nrounds: 100"
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
          "pythonVersion": "3.8.6",
          "metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "bd197f31eb4ccf9a84ed2634cece62a74065c54a",
          "message": "Archive export refactor (2) (#4534)\n\nThis PR builds on #4448,\r\nwith the goal of improving both the export writer API\r\n(allowing for \"streamed\" data writing)\r\nand performance of the export process (CPU and memory usage).\r\n\r\nThe writer is now used as a context manager,\r\nrather than passing all data to it after extraction of the data from the AiiDA database.\r\nThis means it is called throughout the export process,\r\nand will allow for less data to be kept in RAM when moving to a new archive format.\r\n\r\nThe number of database queries has also been reduced, resulting in a faster process.\r\n\r\nLastly, code for read/writes to the archive has been moved to the https://github.com/aiidateam/archive-path package.\r\nThis standardises the interface for both zip and tar, and\r\nespecially for export to tar, provides much improved performance,\r\nsince the data is now written directly to the archive\r\n(rather than writing to a folder then only compressing at the end).\r\n\r\nCo-authored-by: Leopold Talirz <leopold.talirz@gmail.com>",
          "timestamp": "2020-11-12T11:45:40+01:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/bd197f31eb4ccf9a84ed2634cece62a74065c54a",
          "distinct": true,
          "tree_id": "d064e44ee6075f0963c5e03671cecb3bc9e0346b"
        },
        "date": 1605178568738,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.090960460817338,
            "unit": "iter/sec",
            "range": "stddev: 0.067371",
            "group": "engine",
            "extra": "mean: 323.52 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.7632265273741694,
            "unit": "iter/sec",
            "range": "stddev: 0.068640",
            "group": "engine",
            "extra": "mean: 1.3102 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.8527197484010851,
            "unit": "iter/sec",
            "range": "stddev: 0.063892",
            "group": "engine",
            "extra": "mean: 1.1727 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.165015549592135,
            "unit": "iter/sec",
            "range": "stddev: 0.10766",
            "group": "engine",
            "extra": "mean: 6.0600 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.1899941985402569,
            "unit": "iter/sec",
            "range": "stddev: 0.11958",
            "group": "engine",
            "extra": "mean: 5.2633 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.5636799421214578,
            "unit": "iter/sec",
            "range": "stddev: 0.011262",
            "group": "engine",
            "extra": "mean: 390.06 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.6034497310238685,
            "unit": "iter/sec",
            "range": "stddev: 0.064249",
            "group": "engine",
            "extra": "mean: 1.6571 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.6800705310342324,
            "unit": "iter/sec",
            "range": "stddev: 0.075896",
            "group": "engine",
            "extra": "mean: 1.4704 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.14565155961828166,
            "unit": "iter/sec",
            "range": "stddev: 0.13530",
            "group": "engine",
            "extra": "mean: 6.8657 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.17197362612999376,
            "unit": "iter/sec",
            "range": "stddev: 0.10338",
            "group": "engine",
            "extra": "mean: 5.8148 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.010101096039698,
            "unit": "iter/sec",
            "range": "stddev: 0.0096165",
            "group": "import-export",
            "extra": "mean: 497.49 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 1.7488377941407716,
            "unit": "iter/sec",
            "range": "stddev: 0.0048878",
            "group": "import-export",
            "extra": "mean: 571.81 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 1.2506275559186772,
            "unit": "iter/sec",
            "range": "stddev: 0.063507",
            "group": "import-export",
            "extra": "mean: 799.60 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 1.1450311935189665,
            "unit": "iter/sec",
            "range": "stddev: 0.064488",
            "group": "import-export",
            "extra": "mean: 873.34 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 939.6956409145877,
            "unit": "iter/sec",
            "range": "stddev: 0.00013901",
            "group": "node",
            "extra": "mean: 1.0642 msec\nrounds: 176"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 193.55247681858702,
            "unit": "iter/sec",
            "range": "stddev: 0.00059216",
            "group": "node",
            "extra": "mean: 5.1666 msec\nrounds: 129"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 183.16874603897608,
            "unit": "iter/sec",
            "range": "stddev: 0.00042053",
            "group": "node",
            "extra": "mean: 5.4594 msec\nrounds: 120"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 198.62272263140198,
            "unit": "iter/sec",
            "range": "stddev: 0.00047126",
            "group": "node",
            "extra": "mean: 5.0347 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 39.539483133840385,
            "unit": "iter/sec",
            "range": "stddev: 0.0058085",
            "group": "node",
            "extra": "mean: 25.291 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 37.490481312068255,
            "unit": "iter/sec",
            "range": "stddev: 0.019455",
            "group": "node",
            "extra": "mean: 26.673 msec\nrounds: 100"
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
          "pythonVersion": "3.8.6",
          "metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "520bdbf10b2f518717b14ba3a2e429d487c83c66",
          "message": "Improve mypy type checking (#4553)\n\nThis commit moves the mypy execution to run in the full aiida-core python environment.\r\n\r\nCurrently, the mypy in the pre-commit is used as a \"non-local\" import\r\nand adds the blanket `--ignore-missing-imports` flag.\r\nThis greatly reduces the effectiveness of the type checking, because it does not check any types from classes/functions imported from third-party packages.\r\n\r\nSimilarly, adding `check_untyped_defs = True` improves the checking coverage\r\n(see https://mypy.readthedocs.io/en/stable/common_issues.html#no-errors-reported-for-obviously-wrong-code).",
          "timestamp": "2020-11-12T13:58:05+01:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/520bdbf10b2f518717b14ba3a2e429d487c83c66",
          "distinct": true,
          "tree_id": "8287d3d98728798a9459e7bf74cda3d4053b1e3d"
        },
        "date": 1605186446324,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.494401480834563,
            "unit": "iter/sec",
            "range": "stddev: 0.055976",
            "group": "engine",
            "extra": "mean: 286.17 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.8765169679757135,
            "unit": "iter/sec",
            "range": "stddev: 0.050314",
            "group": "engine",
            "extra": "mean: 1.1409 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.962517923201454,
            "unit": "iter/sec",
            "range": "stddev: 0.071898",
            "group": "engine",
            "extra": "mean: 1.0389 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.18357032327235237,
            "unit": "iter/sec",
            "range": "stddev: 0.074091",
            "group": "engine",
            "extra": "mean: 5.4475 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.21291886718345157,
            "unit": "iter/sec",
            "range": "stddev: 0.11054",
            "group": "engine",
            "extra": "mean: 4.6966 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.8630981429998275,
            "unit": "iter/sec",
            "range": "stddev: 0.0075612",
            "group": "engine",
            "extra": "mean: 349.27 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.6770655188085758,
            "unit": "iter/sec",
            "range": "stddev: 0.056737",
            "group": "engine",
            "extra": "mean: 1.4770 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.7572697436676018,
            "unit": "iter/sec",
            "range": "stddev: 0.047453",
            "group": "engine",
            "extra": "mean: 1.3205 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.16305169230268046,
            "unit": "iter/sec",
            "range": "stddev: 0.080113",
            "group": "engine",
            "extra": "mean: 6.1330 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.1943228382081982,
            "unit": "iter/sec",
            "range": "stddev: 0.087966",
            "group": "engine",
            "extra": "mean: 5.1461 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.2763487906031594,
            "unit": "iter/sec",
            "range": "stddev: 0.058182",
            "group": "import-export",
            "extra": "mean: 439.30 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.008488687636135,
            "unit": "iter/sec",
            "range": "stddev: 0.053408",
            "group": "import-export",
            "extra": "mean: 497.89 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 1.5452611477219629,
            "unit": "iter/sec",
            "range": "stddev: 0.068486",
            "group": "import-export",
            "extra": "mean: 647.14 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 1.4655624999918468,
            "unit": "iter/sec",
            "range": "stddev: 0.055981",
            "group": "import-export",
            "extra": "mean: 682.33 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 1048.3300322412074,
            "unit": "iter/sec",
            "range": "stddev: 0.000047141",
            "group": "node",
            "extra": "mean: 953.90 usec\nrounds: 186"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 240.19142462884074,
            "unit": "iter/sec",
            "range": "stddev: 0.00012626",
            "group": "node",
            "extra": "mean: 4.1633 msec\nrounds: 138"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 219.6510910937749,
            "unit": "iter/sec",
            "range": "stddev: 0.00014356",
            "group": "node",
            "extra": "mean: 4.5527 msec\nrounds: 134"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 239.94582426400518,
            "unit": "iter/sec",
            "range": "stddev: 0.00034614",
            "group": "node",
            "extra": "mean: 4.1676 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 46.581704578369596,
            "unit": "iter/sec",
            "range": "stddev: 0.0013075",
            "group": "node",
            "extra": "mean: 21.468 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 43.03454088670933,
            "unit": "iter/sec",
            "range": "stddev: 0.012625",
            "group": "node",
            "extra": "mean: 23.237 msec\nrounds: 100"
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
          "pythonVersion": "3.8.6",
          "metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "def9a0300b92ea8a844ab4b11523e3721269aac4",
          "message": "Improve archive import memory usage (#4559)\n\nThis commit is a small iterative improvement to the archive import logic,\r\nadded to reduce memory overhead,\r\nby reducing the number of variables in memory at any one time",
          "timestamp": "2020-11-12T21:27:03+01:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/def9a0300b92ea8a844ab4b11523e3721269aac4",
          "distinct": true,
          "tree_id": "82c487e7d012a59fd2139dc8b505d82b71a0a560"
        },
        "date": 1605213424483,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.122594202175938,
            "unit": "iter/sec",
            "range": "stddev: 0.065361",
            "group": "engine",
            "extra": "mean: 320.25 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.7846161230055491,
            "unit": "iter/sec",
            "range": "stddev: 0.057559",
            "group": "engine",
            "extra": "mean: 1.2745 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.8866424112867308,
            "unit": "iter/sec",
            "range": "stddev: 0.058459",
            "group": "engine",
            "extra": "mean: 1.1279 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.1661954217338102,
            "unit": "iter/sec",
            "range": "stddev: 0.13914",
            "group": "engine",
            "extra": "mean: 6.0170 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.19571477421109323,
            "unit": "iter/sec",
            "range": "stddev: 0.11403",
            "group": "engine",
            "extra": "mean: 5.1095 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.564649212506236,
            "unit": "iter/sec",
            "range": "stddev: 0.018071",
            "group": "engine",
            "extra": "mean: 389.92 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.6189425839370251,
            "unit": "iter/sec",
            "range": "stddev: 0.074449",
            "group": "engine",
            "extra": "mean: 1.6157 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.6896178607583433,
            "unit": "iter/sec",
            "range": "stddev: 0.069030",
            "group": "engine",
            "extra": "mean: 1.4501 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.15115179793939312,
            "unit": "iter/sec",
            "range": "stddev: 0.085222",
            "group": "engine",
            "extra": "mean: 6.6159 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.18111410579978757,
            "unit": "iter/sec",
            "range": "stddev: 0.12449",
            "group": "engine",
            "extra": "mean: 5.5214 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.189946748915456,
            "unit": "iter/sec",
            "range": "stddev: 0.0053958",
            "group": "import-export",
            "extra": "mean: 456.63 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 1.936528941299581,
            "unit": "iter/sec",
            "range": "stddev: 0.015794",
            "group": "import-export",
            "extra": "mean: 516.39 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 1.4764426648310247,
            "unit": "iter/sec",
            "range": "stddev: 0.046843",
            "group": "import-export",
            "extra": "mean: 677.30 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 1.3458855937059673,
            "unit": "iter/sec",
            "range": "stddev: 0.054916",
            "group": "import-export",
            "extra": "mean: 743.01 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 1051.589141888396,
            "unit": "iter/sec",
            "range": "stddev: 0.00044608",
            "group": "node",
            "extra": "mean: 950.94 usec\nrounds: 209"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 224.17827437071244,
            "unit": "iter/sec",
            "range": "stddev: 0.00047028",
            "group": "node",
            "extra": "mean: 4.4607 msec\nrounds: 136"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 203.05819298921736,
            "unit": "iter/sec",
            "range": "stddev: 0.00045056",
            "group": "node",
            "extra": "mean: 4.9247 msec\nrounds: 132"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 219.9806255147008,
            "unit": "iter/sec",
            "range": "stddev: 0.00055829",
            "group": "node",
            "extra": "mean: 4.5459 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 43.33231364311135,
            "unit": "iter/sec",
            "range": "stddev: 0.0018474",
            "group": "node",
            "extra": "mean: 23.077 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 39.58426049320337,
            "unit": "iter/sec",
            "range": "stddev: 0.016492",
            "group": "node",
            "extra": "mean: 25.263 msec\nrounds: 100"
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
          "pythonVersion": "3.8.6",
          "metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "810dc566b8280721aab3e38fea89dda312a25a82",
          "message": "Update archive version: 0.9 -> 0.10 (#4561)\n\nFixes a bug whereby archives created with the latest code\r\nfail to import in the last v1.4.2 release (if they contain group extras).\r\nThis update imposes that these new archives are no longer compatible with v1.4.2",
          "timestamp": "2020-11-13T11:20:09+01:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/810dc566b8280721aab3e38fea89dda312a25a82",
          "distinct": true,
          "tree_id": "d9be65982e8d55efbb53de7291ce634fd8a22b78"
        },
        "date": 1605263394164,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.3002674194148893,
            "unit": "iter/sec",
            "range": "stddev: 0.050449",
            "group": "engine",
            "extra": "mean: 303.01 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.8252114778428424,
            "unit": "iter/sec",
            "range": "stddev: 0.049580",
            "group": "engine",
            "extra": "mean: 1.2118 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.9230078004427532,
            "unit": "iter/sec",
            "range": "stddev: 0.054573",
            "group": "engine",
            "extra": "mean: 1.0834 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.17879558145019864,
            "unit": "iter/sec",
            "range": "stddev: 0.097075",
            "group": "engine",
            "extra": "mean: 5.5930 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.20492101594137185,
            "unit": "iter/sec",
            "range": "stddev: 0.068211",
            "group": "engine",
            "extra": "mean: 4.8799 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.756421659037541,
            "unit": "iter/sec",
            "range": "stddev: 0.011423",
            "group": "engine",
            "extra": "mean: 362.79 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.6514403907669456,
            "unit": "iter/sec",
            "range": "stddev: 0.050548",
            "group": "engine",
            "extra": "mean: 1.5351 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.7266786936539422,
            "unit": "iter/sec",
            "range": "stddev: 0.066256",
            "group": "engine",
            "extra": "mean: 1.3761 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.15916454700157906,
            "unit": "iter/sec",
            "range": "stddev: 0.10539",
            "group": "engine",
            "extra": "mean: 6.2828 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.1868511710532809,
            "unit": "iter/sec",
            "range": "stddev: 0.11302",
            "group": "engine",
            "extra": "mean: 5.3519 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.0406247864777876,
            "unit": "iter/sec",
            "range": "stddev: 0.054967",
            "group": "import-export",
            "extra": "mean: 490.05 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 1.8421282956192055,
            "unit": "iter/sec",
            "range": "stddev: 0.049976",
            "group": "import-export",
            "extra": "mean: 542.85 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 1.3314403998112985,
            "unit": "iter/sec",
            "range": "stddev: 0.066246",
            "group": "import-export",
            "extra": "mean: 751.07 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 1.234650441173152,
            "unit": "iter/sec",
            "range": "stddev: 0.056526",
            "group": "import-export",
            "extra": "mean: 809.95 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 941.5724627365136,
            "unit": "iter/sec",
            "range": "stddev: 0.000089042",
            "group": "node",
            "extra": "mean: 1.0621 msec\nrounds: 200"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 206.4114024864282,
            "unit": "iter/sec",
            "range": "stddev: 0.00045979",
            "group": "node",
            "extra": "mean: 4.8447 msec\nrounds: 139"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 189.90889583723595,
            "unit": "iter/sec",
            "range": "stddev: 0.00080357",
            "group": "node",
            "extra": "mean: 5.2657 msec\nrounds: 137"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 203.15924696700844,
            "unit": "iter/sec",
            "range": "stddev: 0.00025700",
            "group": "node",
            "extra": "mean: 4.9222 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 38.985043662453585,
            "unit": "iter/sec",
            "range": "stddev: 0.014620",
            "group": "node",
            "extra": "mean: 25.651 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 39.55268080747471,
            "unit": "iter/sec",
            "range": "stddev: 0.016212",
            "group": "node",
            "extra": "mean: 25.283 msec\nrounds: 100"
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
          "pythonVersion": "3.8.6",
          "metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "62ed6437bd041b7fb5808566cf942f1b3865d37f",
          "message": "REST API: Add full_types_count as new entry point\n\nThis feature returns a namespace tree of the available node types in the\ndatabase (data node_types + process process_types) with the addition of\na count at each leaf / branch. It also has the option of doing so for a\nsingle user, if the pk is provided as an option.",
          "timestamp": "2020-11-13T15:34:26+01:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/62ed6437bd041b7fb5808566cf942f1b3865d37f",
          "distinct": true,
          "tree_id": "3ec2791c4d74d16692749f51444de6c0384a94c5"
        },
        "date": 1605278644985,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.2924331375559595,
            "unit": "iter/sec",
            "range": "stddev: 0.058223",
            "group": "engine",
            "extra": "mean: 303.73 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.83848132948207,
            "unit": "iter/sec",
            "range": "stddev: 0.048550",
            "group": "engine",
            "extra": "mean: 1.1926 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.942770466964676,
            "unit": "iter/sec",
            "range": "stddev: 0.047909",
            "group": "engine",
            "extra": "mean: 1.0607 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.18163057995128382,
            "unit": "iter/sec",
            "range": "stddev: 0.094319",
            "group": "engine",
            "extra": "mean: 5.5057 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.20846563166434792,
            "unit": "iter/sec",
            "range": "stddev: 0.12927",
            "group": "engine",
            "extra": "mean: 4.7970 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.8281562994268397,
            "unit": "iter/sec",
            "range": "stddev: 0.010922",
            "group": "engine",
            "extra": "mean: 353.59 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.6656225879376699,
            "unit": "iter/sec",
            "range": "stddev: 0.055445",
            "group": "engine",
            "extra": "mean: 1.5024 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.7464051811867898,
            "unit": "iter/sec",
            "range": "stddev: 0.068607",
            "group": "engine",
            "extra": "mean: 1.3398 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.1617240341711301,
            "unit": "iter/sec",
            "range": "stddev: 0.10930",
            "group": "engine",
            "extra": "mean: 6.1834 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.19085477883115315,
            "unit": "iter/sec",
            "range": "stddev: 0.13277",
            "group": "engine",
            "extra": "mean: 5.2396 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.09820778696835,
            "unit": "iter/sec",
            "range": "stddev: 0.0094796",
            "group": "import-export",
            "extra": "mean: 476.60 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 1.76614605134705,
            "unit": "iter/sec",
            "range": "stddev: 0.053363",
            "group": "import-export",
            "extra": "mean: 566.20 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 1.3510191699693719,
            "unit": "iter/sec",
            "range": "stddev: 0.068621",
            "group": "import-export",
            "extra": "mean: 740.18 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 1.256836705043989,
            "unit": "iter/sec",
            "range": "stddev: 0.054045",
            "group": "import-export",
            "extra": "mean: 795.65 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 961.0353872394652,
            "unit": "iter/sec",
            "range": "stddev: 0.00021292",
            "group": "node",
            "extra": "mean: 1.0405 msec\nrounds: 200"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 186.422456355675,
            "unit": "iter/sec",
            "range": "stddev: 0.0040893",
            "group": "node",
            "extra": "mean: 5.3642 msec\nrounds: 136"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 197.04707150323745,
            "unit": "iter/sec",
            "range": "stddev: 0.00048400",
            "group": "node",
            "extra": "mean: 5.0749 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 205.8803190858679,
            "unit": "iter/sec",
            "range": "stddev: 0.00035561",
            "group": "node",
            "extra": "mean: 4.8572 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 40.40482624934372,
            "unit": "iter/sec",
            "range": "stddev: 0.017180",
            "group": "node",
            "extra": "mean: 24.750 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 42.88827033662778,
            "unit": "iter/sec",
            "range": "stddev: 0.0019133",
            "group": "node",
            "extra": "mean: 23.316 msec\nrounds: 100"
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
          "pythonVersion": "3.8.6",
          "metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "425636023e85d237ca4f13d4591d2595e934e5c9",
          "message": "Merge remote-tracking branch 'origin/master' into develop",
          "timestamp": "2020-11-13T16:57:45+01:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/425636023e85d237ca4f13d4591d2595e934e5c9",
          "distinct": true,
          "tree_id": "156b008bbaf87baac6914c1e04b13be7b2c58c15"
        },
        "date": 1605283580916,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 4.134645863872967,
            "unit": "iter/sec",
            "range": "stddev: 0.0099444",
            "group": "engine",
            "extra": "mean: 241.86 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.9945779605803435,
            "unit": "iter/sec",
            "range": "stddev: 0.034472",
            "group": "engine",
            "extra": "mean: 1.0055 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 1.0706758628568345,
            "unit": "iter/sec",
            "range": "stddev: 0.063004",
            "group": "engine",
            "extra": "mean: 933.99 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.2028692143379526,
            "unit": "iter/sec",
            "range": "stddev: 0.15746",
            "group": "engine",
            "extra": "mean: 4.9293 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.23296849151988266,
            "unit": "iter/sec",
            "range": "stddev: 0.10490",
            "group": "engine",
            "extra": "mean: 4.2924 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 3.281453471906197,
            "unit": "iter/sec",
            "range": "stddev: 0.011982",
            "group": "engine",
            "extra": "mean: 304.74 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.7788055278609213,
            "unit": "iter/sec",
            "range": "stddev: 0.051676",
            "group": "engine",
            "extra": "mean: 1.2840 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.8586103495007241,
            "unit": "iter/sec",
            "range": "stddev: 0.079013",
            "group": "engine",
            "extra": "mean: 1.1647 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.18100638968703164,
            "unit": "iter/sec",
            "range": "stddev: 0.16940",
            "group": "engine",
            "extra": "mean: 5.5247 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.21485967451445726,
            "unit": "iter/sec",
            "range": "stddev: 0.13076",
            "group": "engine",
            "extra": "mean: 4.6542 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.461548350146306,
            "unit": "iter/sec",
            "range": "stddev: 0.050261",
            "group": "import-export",
            "extra": "mean: 406.25 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.2675777878118213,
            "unit": "iter/sec",
            "range": "stddev: 0.044107",
            "group": "import-export",
            "extra": "mean: 441.00 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 1.6647591941369857,
            "unit": "iter/sec",
            "range": "stddev: 0.061973",
            "group": "import-export",
            "extra": "mean: 600.69 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 1.5774574048986878,
            "unit": "iter/sec",
            "range": "stddev: 0.047508",
            "group": "import-export",
            "extra": "mean: 633.93 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 1265.4665665679913,
            "unit": "iter/sec",
            "range": "stddev: 0.000091007",
            "group": "node",
            "extra": "mean: 790.22 usec\nrounds: 222"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 256.02524469955955,
            "unit": "iter/sec",
            "range": "stddev: 0.00034693",
            "group": "node",
            "extra": "mean: 3.9059 msec\nrounds: 151"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 246.90490443892025,
            "unit": "iter/sec",
            "range": "stddev: 0.00040715",
            "group": "node",
            "extra": "mean: 4.0501 msec\nrounds: 171"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 248.95505100631766,
            "unit": "iter/sec",
            "range": "stddev: 0.00055413",
            "group": "node",
            "extra": "mean: 4.0168 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 49.67837566324695,
            "unit": "iter/sec",
            "range": "stddev: 0.0019319",
            "group": "node",
            "extra": "mean: 20.129 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 47.021654515772994,
            "unit": "iter/sec",
            "range": "stddev: 0.015188",
            "group": "node",
            "extra": "mean: 21.267 msec\nrounds: 100"
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
          "pythonVersion": "3.8.6",
          "metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "29c54b59a2906a3315520786814234db63aee194",
          "message": "Dependencies: bump cryptography to 3.2 in `requirements` (#4520)\n\nBumps `cryptography` from 2.8 to 3.2.\r\n\r\nSigned-off-by: dependabot[bot] <support@github.com>\r\nCo-authored-by: Sebastiaan Huber <mail@sphuber.net>",
          "timestamp": "2020-11-16T08:16:44+01:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/29c54b59a2906a3315520786814234db63aee194",
          "distinct": true,
          "tree_id": "ba71cd220b10968e57d68599dbac2939c62c9980"
        },
        "date": 1605511569867,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.669256410595769,
            "unit": "iter/sec",
            "range": "stddev: 0.0084922",
            "group": "engine",
            "extra": "mean: 272.53 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.8869524731990623,
            "unit": "iter/sec",
            "range": "stddev: 0.028693",
            "group": "engine",
            "extra": "mean: 1.1275 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.9668971007519149,
            "unit": "iter/sec",
            "range": "stddev: 0.069537",
            "group": "engine",
            "extra": "mean: 1.0342 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.18529472106149752,
            "unit": "iter/sec",
            "range": "stddev: 0.11575",
            "group": "engine",
            "extra": "mean: 5.3968 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.2117140255403054,
            "unit": "iter/sec",
            "range": "stddev: 0.12552",
            "group": "engine",
            "extra": "mean: 4.7234 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.882363921100854,
            "unit": "iter/sec",
            "range": "stddev: 0.013417",
            "group": "engine",
            "extra": "mean: 346.94 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.6937986918901313,
            "unit": "iter/sec",
            "range": "stddev: 0.066363",
            "group": "engine",
            "extra": "mean: 1.4413 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.7724517640279094,
            "unit": "iter/sec",
            "range": "stddev: 0.065023",
            "group": "engine",
            "extra": "mean: 1.2946 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.16513119660739792,
            "unit": "iter/sec",
            "range": "stddev: 0.078518",
            "group": "engine",
            "extra": "mean: 6.0558 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.1968420408482783,
            "unit": "iter/sec",
            "range": "stddev: 0.12618",
            "group": "engine",
            "extra": "mean: 5.0802 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.333884160659852,
            "unit": "iter/sec",
            "range": "stddev: 0.051396",
            "group": "import-export",
            "extra": "mean: 428.47 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.021744916536922,
            "unit": "iter/sec",
            "range": "stddev: 0.056691",
            "group": "import-export",
            "extra": "mean: 494.62 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 1.4044966140279216,
            "unit": "iter/sec",
            "range": "stddev: 0.057962",
            "group": "import-export",
            "extra": "mean: 712.00 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 1.2884162420515068,
            "unit": "iter/sec",
            "range": "stddev: 0.066084",
            "group": "import-export",
            "extra": "mean: 776.15 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 941.429192513635,
            "unit": "iter/sec",
            "range": "stddev: 0.00022937",
            "group": "node",
            "extra": "mean: 1.0622 msec\nrounds: 202"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 206.2805798642347,
            "unit": "iter/sec",
            "range": "stddev: 0.00058967",
            "group": "node",
            "extra": "mean: 4.8478 msec\nrounds: 134"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 194.88959351964712,
            "unit": "iter/sec",
            "range": "stddev: 0.0013038",
            "group": "node",
            "extra": "mean: 5.1311 msec\nrounds: 145"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 218.40566763055878,
            "unit": "iter/sec",
            "range": "stddev: 0.00073295",
            "group": "node",
            "extra": "mean: 4.5786 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 46.620356400900164,
            "unit": "iter/sec",
            "range": "stddev: 0.0021637",
            "group": "node",
            "extra": "mean: 21.450 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 45.206906622934184,
            "unit": "iter/sec",
            "range": "stddev: 0.0023790",
            "group": "node",
            "extra": "mean: 22.121 msec\nrounds: 100"
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
          "pythonVersion": "3.8.6",
          "metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "49cd0e7562e9598e63b14538ea03c76ca823468e",
          "message": "CI: remove `run-on-comment` job in benchmark workflow (#4569)\n\nThis job is failing due to this change:\r\nhttps://github.blog/changelog/2020-10-01-github-actions-deprecating-set-env-and-add-path-commands/\r\nIt's not really used, so lets just remove it",
          "timestamp": "2020-11-17T08:15:23+01:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/49cd0e7562e9598e63b14538ea03c76ca823468e",
          "distinct": true,
          "tree_id": "802e7a7c893085b21e8ca9ed7e13cc0edac95264"
        },
        "date": 1605597886020,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.363813670897092,
            "unit": "iter/sec",
            "range": "stddev: 0.051032",
            "group": "engine",
            "extra": "mean: 297.28 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.8634579417525576,
            "unit": "iter/sec",
            "range": "stddev: 0.053594",
            "group": "engine",
            "extra": "mean: 1.1581 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.9581836652045357,
            "unit": "iter/sec",
            "range": "stddev: 0.065397",
            "group": "engine",
            "extra": "mean: 1.0436 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.18155435972153655,
            "unit": "iter/sec",
            "range": "stddev: 0.088003",
            "group": "engine",
            "extra": "mean: 5.5080 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.21171486103664572,
            "unit": "iter/sec",
            "range": "stddev: 0.070289",
            "group": "engine",
            "extra": "mean: 4.7233 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.97648928382364,
            "unit": "iter/sec",
            "range": "stddev: 0.0079194",
            "group": "engine",
            "extra": "mean: 335.97 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.6905466664457173,
            "unit": "iter/sec",
            "range": "stddev: 0.056151",
            "group": "engine",
            "extra": "mean: 1.4481 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.7709357586568507,
            "unit": "iter/sec",
            "range": "stddev: 0.077950",
            "group": "engine",
            "extra": "mean: 1.2971 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.16367037090920528,
            "unit": "iter/sec",
            "range": "stddev: 0.13087",
            "group": "engine",
            "extra": "mean: 6.1098 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.1922525739014427,
            "unit": "iter/sec",
            "range": "stddev: 0.11125",
            "group": "engine",
            "extra": "mean: 5.2015 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.20051143725688,
            "unit": "iter/sec",
            "range": "stddev: 0.059950",
            "group": "import-export",
            "extra": "mean: 454.44 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 1.9849904628553279,
            "unit": "iter/sec",
            "range": "stddev: 0.0085683",
            "group": "import-export",
            "extra": "mean: 503.78 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 1.392206147461505,
            "unit": "iter/sec",
            "range": "stddev: 0.048490",
            "group": "import-export",
            "extra": "mean: 718.28 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 1.2332603744785997,
            "unit": "iter/sec",
            "range": "stddev: 0.059268",
            "group": "import-export",
            "extra": "mean: 810.86 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 901.194527860291,
            "unit": "iter/sec",
            "range": "stddev: 0.00012319",
            "group": "node",
            "extra": "mean: 1.1096 msec\nrounds: 197"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 202.0610360383155,
            "unit": "iter/sec",
            "range": "stddev: 0.00029841",
            "group": "node",
            "extra": "mean: 4.9490 msec\nrounds: 132"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 188.56819299130623,
            "unit": "iter/sec",
            "range": "stddev: 0.00043798",
            "group": "node",
            "extra": "mean: 5.3031 msec\nrounds: 125"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 206.60762677436176,
            "unit": "iter/sec",
            "range": "stddev: 0.00048736",
            "group": "node",
            "extra": "mean: 4.8401 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 42.53619996083867,
            "unit": "iter/sec",
            "range": "stddev: 0.0087608",
            "group": "node",
            "extra": "mean: 23.509 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 45.02383427614512,
            "unit": "iter/sec",
            "range": "stddev: 0.0012497",
            "group": "node",
            "extra": "mean: 22.210 msec\nrounds: 100"
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
          "pythonVersion": "3.8.6",
          "metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "4c8f1b07b9050f85f7b2c2c90caa1df6e78c2225",
          "message": "Docs: update citations with AiiDA workflows paper (#4568)\n\nCitation for the latest paper on the engine is added to the README and\r\nthe documentation index page. The paper in `aiida/__init__.py` is also\r\nupdated which was still referencing the original publication of 2016.",
          "timestamp": "2020-11-17T15:31:56+01:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/4c8f1b07b9050f85f7b2c2c90caa1df6e78c2225",
          "distinct": true,
          "tree_id": "b102900c9aeb98e7c03f8e009e1212be9be6d4c5"
        },
        "date": 1605624029163,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 4.17583903979211,
            "unit": "iter/sec",
            "range": "stddev: 0.0087553",
            "group": "engine",
            "extra": "mean: 239.47 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.9535026127166322,
            "unit": "iter/sec",
            "range": "stddev: 0.056981",
            "group": "engine",
            "extra": "mean: 1.0488 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 1.0733445419598315,
            "unit": "iter/sec",
            "range": "stddev: 0.056680",
            "group": "engine",
            "extra": "mean: 931.67 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.20249959895713826,
            "unit": "iter/sec",
            "range": "stddev: 0.11721",
            "group": "engine",
            "extra": "mean: 4.9383 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.23783543930625817,
            "unit": "iter/sec",
            "range": "stddev: 0.077925",
            "group": "engine",
            "extra": "mean: 4.2046 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 3.165824047033914,
            "unit": "iter/sec",
            "range": "stddev: 0.012918",
            "group": "engine",
            "extra": "mean: 315.87 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.7590057198669542,
            "unit": "iter/sec",
            "range": "stddev: 0.042737",
            "group": "engine",
            "extra": "mean: 1.3175 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.8528501320099371,
            "unit": "iter/sec",
            "range": "stddev: 0.047125",
            "group": "engine",
            "extra": "mean: 1.1725 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.17899364498526704,
            "unit": "iter/sec",
            "range": "stddev: 0.13554",
            "group": "engine",
            "extra": "mean: 5.5868 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.2150911139989293,
            "unit": "iter/sec",
            "range": "stddev: 0.10644",
            "group": "engine",
            "extra": "mean: 4.6492 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.4983788914625458,
            "unit": "iter/sec",
            "range": "stddev: 0.043109",
            "group": "import-export",
            "extra": "mean: 400.26 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.065565157525303,
            "unit": "iter/sec",
            "range": "stddev: 0.040463",
            "group": "import-export",
            "extra": "mean: 484.13 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 1.5511246167669457,
            "unit": "iter/sec",
            "range": "stddev: 0.038161",
            "group": "import-export",
            "extra": "mean: 644.69 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 1.3938024564944569,
            "unit": "iter/sec",
            "range": "stddev: 0.052650",
            "group": "import-export",
            "extra": "mean: 717.46 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 1015.4110364386638,
            "unit": "iter/sec",
            "range": "stddev: 0.00022969",
            "group": "node",
            "extra": "mean: 984.82 usec\nrounds: 227"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 224.8089416556789,
            "unit": "iter/sec",
            "range": "stddev: 0.00048223",
            "group": "node",
            "extra": "mean: 4.4482 msec\nrounds: 146"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 210.0647739475679,
            "unit": "iter/sec",
            "range": "stddev: 0.00054973",
            "group": "node",
            "extra": "mean: 4.7604 msec\nrounds: 146"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 225.30893358340103,
            "unit": "iter/sec",
            "range": "stddev: 0.00055267",
            "group": "node",
            "extra": "mean: 4.4384 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 49.71104708216113,
            "unit": "iter/sec",
            "range": "stddev: 0.0018321",
            "group": "node",
            "extra": "mean: 20.116 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 48.393128852794476,
            "unit": "iter/sec",
            "range": "stddev: 0.0023162",
            "group": "node",
            "extra": "mean: 20.664 msec\nrounds: 100"
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
          "pythonVersion": "3.8.6",
          "metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "f04dbf13ed824f6e5724666d5bc39f7c2bad9cf4",
          "message": "Enforce verdi quicksetup --non-interactive (#4573)\n\nWhen in non-interactive mode, do not ask whether to use existing user/database",
          "timestamp": "2020-11-17T22:52:25+01:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/f04dbf13ed824f6e5724666d5bc39f7c2bad9cf4",
          "distinct": true,
          "tree_id": "bdb8af0519bb351a997d27e31083fedaa1435587"
        },
        "date": 1605650504191,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.7572027064674516,
            "unit": "iter/sec",
            "range": "stddev: 0.0093396",
            "group": "engine",
            "extra": "mean: 266.16 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.8738710336245336,
            "unit": "iter/sec",
            "range": "stddev: 0.062593",
            "group": "engine",
            "extra": "mean: 1.1443 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.985853025838719,
            "unit": "iter/sec",
            "range": "stddev: 0.065464",
            "group": "engine",
            "extra": "mean: 1.0143 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.18531113639454655,
            "unit": "iter/sec",
            "range": "stddev: 0.11172",
            "group": "engine",
            "extra": "mean: 5.3963 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.21658404579950885,
            "unit": "iter/sec",
            "range": "stddev: 0.12573",
            "group": "engine",
            "extra": "mean: 4.6171 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.9013123770874363,
            "unit": "iter/sec",
            "range": "stddev: 0.0089987",
            "group": "engine",
            "extra": "mean: 344.67 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.6925697687473189,
            "unit": "iter/sec",
            "range": "stddev: 0.054777",
            "group": "engine",
            "extra": "mean: 1.4439 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.7925438828966284,
            "unit": "iter/sec",
            "range": "stddev: 0.070623",
            "group": "engine",
            "extra": "mean: 1.2618 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.16524480286360776,
            "unit": "iter/sec",
            "range": "stddev: 0.14299",
            "group": "engine",
            "extra": "mean: 6.0516 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.198519824393276,
            "unit": "iter/sec",
            "range": "stddev: 0.095227",
            "group": "engine",
            "extra": "mean: 5.0373 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.2788725897487696,
            "unit": "iter/sec",
            "range": "stddev: 0.053880",
            "group": "import-export",
            "extra": "mean: 438.81 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.0480011146369086,
            "unit": "iter/sec",
            "range": "stddev: 0.0080318",
            "group": "import-export",
            "extra": "mean: 488.28 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 1.5374688957166855,
            "unit": "iter/sec",
            "range": "stddev: 0.041153",
            "group": "import-export",
            "extra": "mean: 650.42 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 1.39644095795962,
            "unit": "iter/sec",
            "range": "stddev: 0.064921",
            "group": "import-export",
            "extra": "mean: 716.11 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 1135.4531475969939,
            "unit": "iter/sec",
            "range": "stddev: 0.00017423",
            "group": "node",
            "extra": "mean: 880.71 usec\nrounds: 213"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 234.92505917323098,
            "unit": "iter/sec",
            "range": "stddev: 0.00032103",
            "group": "node",
            "extra": "mean: 4.2567 msec\nrounds: 132"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 209.62568508820095,
            "unit": "iter/sec",
            "range": "stddev: 0.00059371",
            "group": "node",
            "extra": "mean: 4.7704 msec\nrounds: 130"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 229.2594116987563,
            "unit": "iter/sec",
            "range": "stddev: 0.00045409",
            "group": "node",
            "extra": "mean: 4.3619 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 46.35046537705726,
            "unit": "iter/sec",
            "range": "stddev: 0.0019202",
            "group": "node",
            "extra": "mean: 21.575 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 45.24525646658626,
            "unit": "iter/sec",
            "range": "stddev: 0.0018155",
            "group": "node",
            "extra": "mean: 22.102 msec\nrounds: 100"
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
          "pythonVersion": "3.8.6",
          "metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "1c48d7147584dc3bcb5b8ee9190802fd0b701fe6",
          "message": "`SinglefileData`: add support for `pathlib.Path` for `file` argument (#3614)",
          "timestamp": "2020-11-18T09:59:17+01:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/1c48d7147584dc3bcb5b8ee9190802fd0b701fe6",
          "distinct": true,
          "tree_id": "efdbc3eaee626a05ed98d90d4859612d683060fe"
        },
        "date": 1605690548823,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.3602102347522607,
            "unit": "iter/sec",
            "range": "stddev: 0.053960",
            "group": "engine",
            "extra": "mean: 297.60 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.7937968544770059,
            "unit": "iter/sec",
            "range": "stddev: 0.064760",
            "group": "engine",
            "extra": "mean: 1.2598 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.9200675559234909,
            "unit": "iter/sec",
            "range": "stddev: 0.053922",
            "group": "engine",
            "extra": "mean: 1.0869 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.1798364624628549,
            "unit": "iter/sec",
            "range": "stddev: 0.12587",
            "group": "engine",
            "extra": "mean: 5.5606 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.20444104935535962,
            "unit": "iter/sec",
            "range": "stddev: 0.028285",
            "group": "engine",
            "extra": "mean: 4.8914 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.712267883382268,
            "unit": "iter/sec",
            "range": "stddev: 0.015045",
            "group": "engine",
            "extra": "mean: 368.70 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.654889377536926,
            "unit": "iter/sec",
            "range": "stddev: 0.069826",
            "group": "engine",
            "extra": "mean: 1.5270 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.7352540135412684,
            "unit": "iter/sec",
            "range": "stddev: 0.059715",
            "group": "engine",
            "extra": "mean: 1.3601 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.16211431396816672,
            "unit": "iter/sec",
            "range": "stddev: 0.13494",
            "group": "engine",
            "extra": "mean: 6.1685 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.19088079365187194,
            "unit": "iter/sec",
            "range": "stddev: 0.13603",
            "group": "engine",
            "extra": "mean: 5.2389 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.305354981870228,
            "unit": "iter/sec",
            "range": "stddev: 0.022372",
            "group": "import-export",
            "extra": "mean: 433.77 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 1.9922455659815852,
            "unit": "iter/sec",
            "range": "stddev: 0.021441",
            "group": "import-export",
            "extra": "mean: 501.95 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 1.3902587919750684,
            "unit": "iter/sec",
            "range": "stddev: 0.053412",
            "group": "import-export",
            "extra": "mean: 719.29 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 1.267132487201358,
            "unit": "iter/sec",
            "range": "stddev: 0.032467",
            "group": "import-export",
            "extra": "mean: 789.18 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 902.1892982896771,
            "unit": "iter/sec",
            "range": "stddev: 0.00025950",
            "group": "node",
            "extra": "mean: 1.1084 msec\nrounds: 215"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 205.88820971306052,
            "unit": "iter/sec",
            "range": "stddev: 0.00053000",
            "group": "node",
            "extra": "mean: 4.8570 msec\nrounds: 119"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 193.3864028180735,
            "unit": "iter/sec",
            "range": "stddev: 0.00085648",
            "group": "node",
            "extra": "mean: 5.1710 msec\nrounds: 103"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 201.20445250762782,
            "unit": "iter/sec",
            "range": "stddev: 0.00086903",
            "group": "node",
            "extra": "mean: 4.9701 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 43.02288164345614,
            "unit": "iter/sec",
            "range": "stddev: 0.0031147",
            "group": "node",
            "extra": "mean: 23.243 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 38.42958495632776,
            "unit": "iter/sec",
            "range": "stddev: 0.020254",
            "group": "node",
            "extra": "mean: 26.022 msec\nrounds: 100"
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
          "pythonVersion": "3.8.6",
          "metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "20996d1801d2e44f46f780fa162b823448bffee8",
          "message": "Fix `verdi --version` in editable mode (#4576)\n\nThis commit fixes a bug,\r\nwhereby click was using a version statically stored on install of the package.\r\nThis meant changes to `__version__` were not dynamically reflected.",
          "timestamp": "2020-11-18T11:37:27+01:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/20996d1801d2e44f46f780fa162b823448bffee8",
          "distinct": true,
          "tree_id": "0dc7341502b74de2a19923c70d33a1e636a2ada9"
        },
        "date": 1605696376640,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.969731681969085,
            "unit": "iter/sec",
            "range": "stddev: 0.013585",
            "group": "engine",
            "extra": "mean: 251.91 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.9778398628124223,
            "unit": "iter/sec",
            "range": "stddev: 0.048619",
            "group": "engine",
            "extra": "mean: 1.0227 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 1.0844979088687463,
            "unit": "iter/sec",
            "range": "stddev: 0.051850",
            "group": "engine",
            "extra": "mean: 922.09 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.20755940996881675,
            "unit": "iter/sec",
            "range": "stddev: 0.11482",
            "group": "engine",
            "extra": "mean: 4.8179 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.23934053560372226,
            "unit": "iter/sec",
            "range": "stddev: 0.13181",
            "group": "engine",
            "extra": "mean: 4.1781 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.9471057205158915,
            "unit": "iter/sec",
            "range": "stddev: 0.056076",
            "group": "engine",
            "extra": "mean: 339.32 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.7762670372133673,
            "unit": "iter/sec",
            "range": "stddev: 0.047435",
            "group": "engine",
            "extra": "mean: 1.2882 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.8612706425472993,
            "unit": "iter/sec",
            "range": "stddev: 0.052531",
            "group": "engine",
            "extra": "mean: 1.1611 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.1762393400688754,
            "unit": "iter/sec",
            "range": "stddev: 0.24289",
            "group": "engine",
            "extra": "mean: 5.6741 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.21638176999265082,
            "unit": "iter/sec",
            "range": "stddev: 0.099970",
            "group": "engine",
            "extra": "mean: 4.6215 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.47449819841258,
            "unit": "iter/sec",
            "range": "stddev: 0.040056",
            "group": "import-export",
            "extra": "mean: 404.12 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.203759611877744,
            "unit": "iter/sec",
            "range": "stddev: 0.026988",
            "group": "import-export",
            "extra": "mean: 453.77 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 1.5352923008972712,
            "unit": "iter/sec",
            "range": "stddev: 0.040685",
            "group": "import-export",
            "extra": "mean: 651.34 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 1.3966662449184644,
            "unit": "iter/sec",
            "range": "stddev: 0.044411",
            "group": "import-export",
            "extra": "mean: 715.99 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 1090.8952725802403,
            "unit": "iter/sec",
            "range": "stddev: 0.00023801",
            "group": "node",
            "extra": "mean: 916.68 usec\nrounds: 205"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 228.34012394001732,
            "unit": "iter/sec",
            "range": "stddev: 0.00074327",
            "group": "node",
            "extra": "mean: 4.3794 msec\nrounds: 150"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 219.54782874414238,
            "unit": "iter/sec",
            "range": "stddev: 0.00053364",
            "group": "node",
            "extra": "mean: 4.5548 msec\nrounds: 131"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 227.26278400967246,
            "unit": "iter/sec",
            "range": "stddev: 0.00059719",
            "group": "node",
            "extra": "mean: 4.4002 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 50.957420735438845,
            "unit": "iter/sec",
            "range": "stddev: 0.0015704",
            "group": "node",
            "extra": "mean: 19.624 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 44.42891634071538,
            "unit": "iter/sec",
            "range": "stddev: 0.016961",
            "group": "node",
            "extra": "mean: 22.508 msec\nrounds: 100"
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
          "pythonVersion": "3.8.6",
          "metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "d29fb3be78c9b7be2e495b287c6dca8960bfe83d",
          "message": "Improve `verdi node delete` performance (#4575)\n\nThe `verdi node delete` process fully loaded all ORM objects at multiple stages\r\nduring the process, which is highly inefficient.\r\nThis commit ensures the process now only loads the PKs when possible.\r\nAs an example, the time to delete 100 \"empty\" nodes (no attributes/objects)\r\nis now reduced from ~32 seconds to ~5 seconds.",
          "timestamp": "2020-11-18T12:30:38+01:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/d29fb3be78c9b7be2e495b287c6dca8960bfe83d",
          "distinct": true,
          "tree_id": "ed6770a97de77ffa34675a9baa8f7f576b148652"
        },
        "date": 1605699642590,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.327562940995398,
            "unit": "iter/sec",
            "range": "stddev: 0.020241",
            "group": "engine",
            "extra": "mean: 300.52 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.8096068383329081,
            "unit": "iter/sec",
            "range": "stddev: 0.067689",
            "group": "engine",
            "extra": "mean: 1.2352 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.8731182941643094,
            "unit": "iter/sec",
            "range": "stddev: 0.078854",
            "group": "engine",
            "extra": "mean: 1.1453 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.1726235431700341,
            "unit": "iter/sec",
            "range": "stddev: 0.10594",
            "group": "engine",
            "extra": "mean: 5.7930 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.19870452894162846,
            "unit": "iter/sec",
            "range": "stddev: 0.14719",
            "group": "engine",
            "extra": "mean: 5.0326 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.7400141800498483,
            "unit": "iter/sec",
            "range": "stddev: 0.014089",
            "group": "engine",
            "extra": "mean: 364.96 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.6318156230533679,
            "unit": "iter/sec",
            "range": "stddev: 0.056272",
            "group": "engine",
            "extra": "mean: 1.5827 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.714639315368767,
            "unit": "iter/sec",
            "range": "stddev: 0.071501",
            "group": "engine",
            "extra": "mean: 1.3993 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.15387762804721525,
            "unit": "iter/sec",
            "range": "stddev: 0.083763",
            "group": "engine",
            "extra": "mean: 6.4987 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.18199977098113426,
            "unit": "iter/sec",
            "range": "stddev: 0.13963",
            "group": "engine",
            "extra": "mean: 5.4945 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.080071954209674,
            "unit": "iter/sec",
            "range": "stddev: 0.056839",
            "group": "import-export",
            "extra": "mean: 480.75 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 1.8787467967724774,
            "unit": "iter/sec",
            "range": "stddev: 0.011047",
            "group": "import-export",
            "extra": "mean: 532.27 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 1.2722064687362717,
            "unit": "iter/sec",
            "range": "stddev: 0.042641",
            "group": "import-export",
            "extra": "mean: 786.04 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 1.1390242978903473,
            "unit": "iter/sec",
            "range": "stddev: 0.067656",
            "group": "import-export",
            "extra": "mean: 877.94 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 839.0350438381353,
            "unit": "iter/sec",
            "range": "stddev: 0.00026743",
            "group": "node",
            "extra": "mean: 1.1918 msec\nrounds: 187"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 182.98048165036474,
            "unit": "iter/sec",
            "range": "stddev: 0.0012288",
            "group": "node",
            "extra": "mean: 5.4651 msec\nrounds: 132"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 175.89622181960564,
            "unit": "iter/sec",
            "range": "stddev: 0.00066618",
            "group": "node",
            "extra": "mean: 5.6852 msec\nrounds: 124"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 191.52967666197264,
            "unit": "iter/sec",
            "range": "stddev: 0.00060697",
            "group": "node",
            "extra": "mean: 5.2211 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 40.947743349014054,
            "unit": "iter/sec",
            "range": "stddev: 0.0018379",
            "group": "node",
            "extra": "mean: 24.421 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 38.525588482246505,
            "unit": "iter/sec",
            "range": "stddev: 0.0075107",
            "group": "node",
            "extra": "mean: 25.957 msec\nrounds: 100"
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
          "pythonVersion": "3.8.6",
          "metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "17b77181d87abed9211fdaf1f432e00e276c1c11",
          "message": "`CalcJob`: add the `additional_retrieve_list` metadata option (#4437)\n\nThis new option allows one to specify additional files to be retrieved\r\non a per-instance basis, in addition to the files that are already\r\ndefined by the plugin to be retrieved. This was often implemented by\r\nplugin packages itself through a `settings` node that supported a key\r\nthat would allow a user to specify these additional files.\r\n\r\nSince this is a common use case, we implement this functionality on\r\n`aiida-core` instead to guarantee a consistent interface across plugins.",
          "timestamp": "2020-11-19T10:09:33+01:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/17b77181d87abed9211fdaf1f432e00e276c1c11",
          "distinct": true,
          "tree_id": "4ddaf98ee92f992d526af5998b66576f53d7b0bd"
        },
        "date": 1605777658749,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.1344447019190906,
            "unit": "iter/sec",
            "range": "stddev: 0.012835",
            "group": "engine",
            "extra": "mean: 319.04 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.7371365401847263,
            "unit": "iter/sec",
            "range": "stddev: 0.069434",
            "group": "engine",
            "extra": "mean: 1.3566 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.797830564722807,
            "unit": "iter/sec",
            "range": "stddev: 0.078729",
            "group": "engine",
            "extra": "mean: 1.2534 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.15385633763264747,
            "unit": "iter/sec",
            "range": "stddev: 0.16462",
            "group": "engine",
            "extra": "mean: 6.4996 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.17798020338332432,
            "unit": "iter/sec",
            "range": "stddev: 0.082013",
            "group": "engine",
            "extra": "mean: 5.6186 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.4570342505426725,
            "unit": "iter/sec",
            "range": "stddev: 0.012237",
            "group": "engine",
            "extra": "mean: 406.99 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.5679642786659455,
            "unit": "iter/sec",
            "range": "stddev: 0.068490",
            "group": "engine",
            "extra": "mean: 1.7607 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.644681422537566,
            "unit": "iter/sec",
            "range": "stddev: 0.068574",
            "group": "engine",
            "extra": "mean: 1.5512 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.13874309984019648,
            "unit": "iter/sec",
            "range": "stddev: 0.16271",
            "group": "engine",
            "extra": "mean: 7.2076 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.16314561124033403,
            "unit": "iter/sec",
            "range": "stddev: 0.11486",
            "group": "engine",
            "extra": "mean: 6.1295 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 1.904795026728629,
            "unit": "iter/sec",
            "range": "stddev: 0.065794",
            "group": "import-export",
            "extra": "mean: 524.99 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 1.6682790991961505,
            "unit": "iter/sec",
            "range": "stddev: 0.058135",
            "group": "import-export",
            "extra": "mean: 599.42 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 1.1575535377118367,
            "unit": "iter/sec",
            "range": "stddev: 0.079320",
            "group": "import-export",
            "extra": "mean: 863.89 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 1.040398465461256,
            "unit": "iter/sec",
            "range": "stddev: 0.062583",
            "group": "import-export",
            "extra": "mean: 961.17 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 812.6225440943829,
            "unit": "iter/sec",
            "range": "stddev: 0.00029703",
            "group": "node",
            "extra": "mean: 1.2306 msec\nrounds: 181"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 171.1220299895529,
            "unit": "iter/sec",
            "range": "stddev: 0.00079457",
            "group": "node",
            "extra": "mean: 5.8438 msec\nrounds: 105"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 166.0509257565677,
            "unit": "iter/sec",
            "range": "stddev: 0.00073024",
            "group": "node",
            "extra": "mean: 6.0222 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 179.4459719745159,
            "unit": "iter/sec",
            "range": "stddev: 0.00086063",
            "group": "node",
            "extra": "mean: 5.5727 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 36.627669208010296,
            "unit": "iter/sec",
            "range": "stddev: 0.017506",
            "group": "node",
            "extra": "mean: 27.302 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 38.02738679235002,
            "unit": "iter/sec",
            "range": "stddev: 0.0034136",
            "group": "node",
            "extra": "mean: 26.297 msec\nrounds: 100"
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
          "pythonVersion": "3.8.6",
          "metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "a2d6c7673952ae48c0d5ae58aff2d2c808e3a982",
          "message": "Add options for transport tasks (#4583)\n\n* Add options for transport tasks\r\n\r\nWhen encountering failures during the execution of transport tasks, a runner\r\nwill wait for a time interval between transport task attempts. This time\r\ninterval between attempts is increased using an exponential backoff\r\nmechanism, i.e. the time interval is equal to:\r\n\r\n(TRANSPORT_TASK_RETRY_INITIAL_INTERVAL) * 2 ** (N_ATTEMPT - 1)\r\n\r\nwhere N_ATTEMPT is the number of failed attempts. This mechanism is\r\ninterrupted once the TRANSPORT_TASK_MAXIMUM_ATTEMPTS is reached.\r\n\r\nThe initial interval and maximum attempts are currently fixed to 20\r\nseconds and 5, respectively. This commit adds two configuration options\r\nthat use these defaults, but allow the user to adjust them using `verdi\r\nconfig`.",
          "timestamp": "2020-11-22T21:02:07+01:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/a2d6c7673952ae48c0d5ae58aff2d2c808e3a982",
          "distinct": true,
          "tree_id": "1f68e6180472a31d8620aeecbb57a55a8c7f469b"
        },
        "date": 1606075883971,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.7385545675375873,
            "unit": "iter/sec",
            "range": "stddev: 0.0060681",
            "group": "engine",
            "extra": "mean: 267.48 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.8898397745986099,
            "unit": "iter/sec",
            "range": "stddev: 0.041554",
            "group": "engine",
            "extra": "mean: 1.1238 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 1.007223993189591,
            "unit": "iter/sec",
            "range": "stddev: 0.068612",
            "group": "engine",
            "extra": "mean: 992.83 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.18607586955695765,
            "unit": "iter/sec",
            "range": "stddev: 0.092932",
            "group": "engine",
            "extra": "mean: 5.3742 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.21722897806252014,
            "unit": "iter/sec",
            "range": "stddev: 0.095600",
            "group": "engine",
            "extra": "mean: 4.6034 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 3.0520952884733643,
            "unit": "iter/sec",
            "range": "stddev: 0.0076088",
            "group": "engine",
            "extra": "mean: 327.64 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.7157141636573193,
            "unit": "iter/sec",
            "range": "stddev: 0.042839",
            "group": "engine",
            "extra": "mean: 1.3972 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.7903208949824715,
            "unit": "iter/sec",
            "range": "stddev: 0.082958",
            "group": "engine",
            "extra": "mean: 1.2653 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.166338496089301,
            "unit": "iter/sec",
            "range": "stddev: 0.077416",
            "group": "engine",
            "extra": "mean: 6.0118 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.19880823521487143,
            "unit": "iter/sec",
            "range": "stddev: 0.089970",
            "group": "engine",
            "extra": "mean: 5.0300 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.3441501093385066,
            "unit": "iter/sec",
            "range": "stddev: 0.049130",
            "group": "import-export",
            "extra": "mean: 426.59 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.0754999913551853,
            "unit": "iter/sec",
            "range": "stddev: 0.050847",
            "group": "import-export",
            "extra": "mean: 481.81 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 1.5342629350970995,
            "unit": "iter/sec",
            "range": "stddev: 0.066201",
            "group": "import-export",
            "extra": "mean: 651.78 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 1.4742224556107368,
            "unit": "iter/sec",
            "range": "stddev: 0.047660",
            "group": "import-export",
            "extra": "mean: 678.32 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 1126.518153637094,
            "unit": "iter/sec",
            "range": "stddev: 0.00039937",
            "group": "node",
            "extra": "mean: 887.69 usec\nrounds: 214"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 230.8431371600644,
            "unit": "iter/sec",
            "range": "stddev: 0.00032217",
            "group": "node",
            "extra": "mean: 4.3319 msec\nrounds: 149"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 219.0701685291292,
            "unit": "iter/sec",
            "range": "stddev: 0.00022062",
            "group": "node",
            "extra": "mean: 4.5647 msec\nrounds: 133"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 255.62019664899358,
            "unit": "iter/sec",
            "range": "stddev: 0.00021304",
            "group": "node",
            "extra": "mean: 3.9121 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 45.97375019038764,
            "unit": "iter/sec",
            "range": "stddev: 0.013621",
            "group": "node",
            "extra": "mean: 21.752 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 45.329412580893596,
            "unit": "iter/sec",
            "range": "stddev: 0.012642",
            "group": "node",
            "extra": "mean: 22.061 msec\nrounds: 100"
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
          "pythonVersion": "3.8.6",
          "metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "36cb1335d7c43e0fcca12cd38e09e0fbffaf226f",
          "message": "Fix command for getting EBM config options (#4587)\n\nCurrently the transport options for the EBM are obtained by using the\r\nget_config function, e.g.:\r\n\r\n`initial_interval = get_config_option(RETRY_INTERVAL_OPTION)`\r\n\r\nHowever, it seems that `get_config()` does not get you the current\r\nconfiguration (see #4586). \r\n\r\nReplacing `get_config().get_option()` with `get_config_option()` fixes this\r\nissue for the EBM options.",
          "timestamp": "2020-11-24T19:48:04+01:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/36cb1335d7c43e0fcca12cd38e09e0fbffaf226f",
          "distinct": true,
          "tree_id": "7aba0b76bbc89485ed8ec7c9792bacb2e16b0276"
        },
        "date": 1606244296351,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.388095103192596,
            "unit": "iter/sec",
            "range": "stddev: 0.0078535",
            "group": "engine",
            "extra": "mean: 295.15 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.7941932122351391,
            "unit": "iter/sec",
            "range": "stddev: 0.076667",
            "group": "engine",
            "extra": "mean: 1.2591 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.8811398913856994,
            "unit": "iter/sec",
            "range": "stddev: 0.063353",
            "group": "engine",
            "extra": "mean: 1.1349 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.16822212816168658,
            "unit": "iter/sec",
            "range": "stddev: 0.17436",
            "group": "engine",
            "extra": "mean: 5.9445 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.19281744908548742,
            "unit": "iter/sec",
            "range": "stddev: 0.21329",
            "group": "engine",
            "extra": "mean: 5.1863 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.436464891007049,
            "unit": "iter/sec",
            "range": "stddev: 0.053186",
            "group": "engine",
            "extra": "mean: 410.43 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.6078343299607185,
            "unit": "iter/sec",
            "range": "stddev: 0.061799",
            "group": "engine",
            "extra": "mean: 1.6452 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.6770116087770937,
            "unit": "iter/sec",
            "range": "stddev: 0.081353",
            "group": "engine",
            "extra": "mean: 1.4771 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.15464180108906572,
            "unit": "iter/sec",
            "range": "stddev: 0.15523",
            "group": "engine",
            "extra": "mean: 6.4666 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.1785502453607536,
            "unit": "iter/sec",
            "range": "stddev: 0.16483",
            "group": "engine",
            "extra": "mean: 5.6007 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.286538842107959,
            "unit": "iter/sec",
            "range": "stddev: 0.0081575",
            "group": "import-export",
            "extra": "mean: 437.34 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 1.9288812274598297,
            "unit": "iter/sec",
            "range": "stddev: 0.027592",
            "group": "import-export",
            "extra": "mean: 518.44 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 1.4046779849763278,
            "unit": "iter/sec",
            "range": "stddev: 0.073919",
            "group": "import-export",
            "extra": "mean: 711.91 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 1.32912648423278,
            "unit": "iter/sec",
            "range": "stddev: 0.065093",
            "group": "import-export",
            "extra": "mean: 752.37 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 1141.7326380522516,
            "unit": "iter/sec",
            "range": "stddev: 0.00012190",
            "group": "node",
            "extra": "mean: 875.86 usec\nrounds: 197"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 195.93222054463558,
            "unit": "iter/sec",
            "range": "stddev: 0.0028581",
            "group": "node",
            "extra": "mean: 5.1038 msec\nrounds: 119"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 195.7084533556602,
            "unit": "iter/sec",
            "range": "stddev: 0.0014887",
            "group": "node",
            "extra": "mean: 5.1096 msec\nrounds: 128"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 214.23375448978425,
            "unit": "iter/sec",
            "range": "stddev: 0.00080390",
            "group": "node",
            "extra": "mean: 4.6678 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 43.62139569837932,
            "unit": "iter/sec",
            "range": "stddev: 0.0014554",
            "group": "node",
            "extra": "mean: 22.925 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 39.59944527512242,
            "unit": "iter/sec",
            "range": "stddev: 0.0094969",
            "group": "node",
            "extra": "mean: 25.253 msec\nrounds: 100"
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
          "pythonVersion": "3.8.6",
          "metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "af12a62d3509aa6d3ade250aff2230add49f5523",
          "message": "CI: Add workflow to run tests against various RabbitMQ versions\n\nThe main test workflow runs against a single version of RabbitMQ but\nexperience has shown that the code can break for different versions of\nthe RabbitMQ server. Here we add a new CI workflow that runs various\nunit tests through pytest that simulate the typical interaction with the\nRabbitMQ server in normal AiiDA operation. The difference is that these\nare tested against the currently available versions of RabbitMQ.\n\nThe current setup, still only tests part of the functionality that AiiDA\nuses, for example, the default credentials and virtual host are used.\nConnections over TLS are also not tested. These options would require\nthe RabbitMQ service that is running in a docker container to be\nconfigured differently. It is not clear how these various options can be\nparametrized in concert with the actual unit tests.",
          "timestamp": "2020-11-27T13:40:52+01:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/af12a62d3509aa6d3ade250aff2230add49f5523",
          "distinct": true,
          "tree_id": "213e4b703078ab0d16cb3ffe586119ae259e1fd5"
        },
        "date": 1606481461491,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.289481537847626,
            "unit": "iter/sec",
            "range": "stddev: 0.055710",
            "group": "engine",
            "extra": "mean: 304.00 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.825038468214742,
            "unit": "iter/sec",
            "range": "stddev: 0.044491",
            "group": "engine",
            "extra": "mean: 1.2121 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.9121799239755567,
            "unit": "iter/sec",
            "range": "stddev: 0.068304",
            "group": "engine",
            "extra": "mean: 1.0963 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.1721451588319587,
            "unit": "iter/sec",
            "range": "stddev: 0.060250",
            "group": "engine",
            "extra": "mean: 5.8091 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.20011704887012272,
            "unit": "iter/sec",
            "range": "stddev: 0.094349",
            "group": "engine",
            "extra": "mean: 4.9971 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.685360263637783,
            "unit": "iter/sec",
            "range": "stddev: 0.012663",
            "group": "engine",
            "extra": "mean: 372.39 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.6440947506130598,
            "unit": "iter/sec",
            "range": "stddev: 0.065236",
            "group": "engine",
            "extra": "mean: 1.5526 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.7392851207023367,
            "unit": "iter/sec",
            "range": "stddev: 0.052882",
            "group": "engine",
            "extra": "mean: 1.3527 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.15396975610936553,
            "unit": "iter/sec",
            "range": "stddev: 0.093434",
            "group": "engine",
            "extra": "mean: 6.4948 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.1816455929951898,
            "unit": "iter/sec",
            "range": "stddev: 0.10138",
            "group": "engine",
            "extra": "mean: 5.5052 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 1.978305010424093,
            "unit": "iter/sec",
            "range": "stddev: 0.059226",
            "group": "import-export",
            "extra": "mean: 505.48 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 1.7542716897565767,
            "unit": "iter/sec",
            "range": "stddev: 0.053997",
            "group": "import-export",
            "extra": "mean: 570.04 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 1.3227100367603104,
            "unit": "iter/sec",
            "range": "stddev: 0.059363",
            "group": "import-export",
            "extra": "mean: 756.02 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 1.1835931028323294,
            "unit": "iter/sec",
            "range": "stddev: 0.063751",
            "group": "import-export",
            "extra": "mean: 844.88 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 970.4004226805722,
            "unit": "iter/sec",
            "range": "stddev: 0.00013190",
            "group": "node",
            "extra": "mean: 1.0305 msec\nrounds: 197"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 187.55538045293636,
            "unit": "iter/sec",
            "range": "stddev: 0.0020884",
            "group": "node",
            "extra": "mean: 5.3318 msec\nrounds: 124"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 188.93583931388602,
            "unit": "iter/sec",
            "range": "stddev: 0.00052915",
            "group": "node",
            "extra": "mean: 5.2928 msec\nrounds: 128"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 188.30993078107383,
            "unit": "iter/sec",
            "range": "stddev: 0.0011238",
            "group": "node",
            "extra": "mean: 5.3104 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 42.63700270083209,
            "unit": "iter/sec",
            "range": "stddev: 0.0019731",
            "group": "node",
            "extra": "mean: 23.454 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 42.64242291865178,
            "unit": "iter/sec",
            "range": "stddev: 0.0018162",
            "group": "node",
            "extra": "mean: 23.451 msec\nrounds: 100"
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
          "pythonVersion": "3.8.6",
          "metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "9419068ffa8717c2470fe8774155d7006080540d",
          "message": "🧪 FIX: engine benchmark tests (#4652)\n\nThe `test_workchain_daemon` test group required updating to using asyncio (rather than tornado)",
          "timestamp": "2021-01-10T17:31:00Z",
          "url": "https://github.com/aiidateam/aiida-core/commit/9419068ffa8717c2470fe8774155d7006080540d",
          "distinct": true,
          "tree_id": "66d2d5cd697804c65a7769e849d40838416ddc0a"
        },
        "date": 1610300404166,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.4804360622053703,
            "unit": "iter/sec",
            "range": "stddev: 0.056253",
            "group": "engine",
            "extra": "mean: 287.32 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.88515187437321,
            "unit": "iter/sec",
            "range": "stddev: 0.036243",
            "group": "engine",
            "extra": "mean: 1.1297 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.9941763884134323,
            "unit": "iter/sec",
            "range": "stddev: 0.072351",
            "group": "engine",
            "extra": "mean: 1.0059 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.20073313347624971,
            "unit": "iter/sec",
            "range": "stddev: 0.080945",
            "group": "engine",
            "extra": "mean: 4.9817 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.2347913174602542,
            "unit": "iter/sec",
            "range": "stddev: 0.10512",
            "group": "engine",
            "extra": "mean: 4.2591 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.9587376156357,
            "unit": "iter/sec",
            "range": "stddev: 0.0038301",
            "group": "engine",
            "extra": "mean: 337.98 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.6702614559828673,
            "unit": "iter/sec",
            "range": "stddev: 0.073847",
            "group": "engine",
            "extra": "mean: 1.4920 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.7588492593225722,
            "unit": "iter/sec",
            "range": "stddev: 0.057853",
            "group": "engine",
            "extra": "mean: 1.3178 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.17814851215386976,
            "unit": "iter/sec",
            "range": "stddev: 0.084237",
            "group": "engine",
            "extra": "mean: 5.6133 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.2120089030241088,
            "unit": "iter/sec",
            "range": "stddev: 0.084200",
            "group": "engine",
            "extra": "mean: 4.7168 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.400933278779426,
            "unit": "iter/sec",
            "range": "stddev: 0.053199",
            "group": "import-export",
            "extra": "mean: 416.50 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.1322953164311826,
            "unit": "iter/sec",
            "range": "stddev: 0.051228",
            "group": "import-export",
            "extra": "mean: 468.98 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 1.6060002451821827,
            "unit": "iter/sec",
            "range": "stddev: 0.065215",
            "group": "import-export",
            "extra": "mean: 622.66 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 1.5125003335252434,
            "unit": "iter/sec",
            "range": "stddev: 0.050426",
            "group": "import-export",
            "extra": "mean: 661.16 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 1182.049856635335,
            "unit": "iter/sec",
            "range": "stddev: 0.00016430",
            "group": "node",
            "extra": "mean: 845.99 usec\nrounds: 201"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 239.39694428453743,
            "unit": "iter/sec",
            "range": "stddev: 0.00027831",
            "group": "node",
            "extra": "mean: 4.1772 msec\nrounds: 128"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 223.45370304109534,
            "unit": "iter/sec",
            "range": "stddev: 0.00020084",
            "group": "node",
            "extra": "mean: 4.4752 msec\nrounds: 132"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 240.15001133714986,
            "unit": "iter/sec",
            "range": "stddev: 0.00035824",
            "group": "node",
            "extra": "mean: 4.1641 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 48.82585168932527,
            "unit": "iter/sec",
            "range": "stddev: 0.0013561",
            "group": "node",
            "extra": "mean: 20.481 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 49.38690640034372,
            "unit": "iter/sec",
            "range": "stddev: 0.0013410",
            "group": "node",
            "extra": "mean: 20.248 msec\nrounds: 100"
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
          "pythonVersion": "3.8.7",
          "metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "8e80ac14d9e5372393528d9ba4107a7656d44923",
          "message": "Docs: clarify docstrings of `get_last_job_info` and `get_detailed_job_info` (#4657)\n\n`CalcJobNode`s contain two differente job infos, the `detailed_job_info` and\r\nthe `last_job_info`. The distinction between the two was not obvious,\r\nand not documented. The docstrings are improved to clarify the difference.",
          "timestamp": "2021-01-13T15:48:24+01:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/8e80ac14d9e5372393528d9ba4107a7656d44923",
          "distinct": true,
          "tree_id": "9f84b835ee52db74a662130062bdba7503ca2bc7"
        },
        "date": 1610549902435,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.167037355615457,
            "unit": "iter/sec",
            "range": "stddev: 0.017548",
            "group": "engine",
            "extra": "mean: 315.75 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.7427545212822351,
            "unit": "iter/sec",
            "range": "stddev: 0.056209",
            "group": "engine",
            "extra": "mean: 1.3463 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.8405742759979172,
            "unit": "iter/sec",
            "range": "stddev: 0.069466",
            "group": "engine",
            "extra": "mean: 1.1897 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.17868864174083948,
            "unit": "iter/sec",
            "range": "stddev: 0.13153",
            "group": "engine",
            "extra": "mean: 5.5963 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.20808792658418762,
            "unit": "iter/sec",
            "range": "stddev: 0.12071",
            "group": "engine",
            "extra": "mean: 4.8057 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.414116314747189,
            "unit": "iter/sec",
            "range": "stddev: 0.052760",
            "group": "engine",
            "extra": "mean: 414.23 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.5861052335188861,
            "unit": "iter/sec",
            "range": "stddev: 0.043429",
            "group": "engine",
            "extra": "mean: 1.7062 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.664912458801237,
            "unit": "iter/sec",
            "range": "stddev: 0.071854",
            "group": "engine",
            "extra": "mean: 1.5040 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.15762768170083313,
            "unit": "iter/sec",
            "range": "stddev: 0.12130",
            "group": "engine",
            "extra": "mean: 6.3441 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.19027752460134845,
            "unit": "iter/sec",
            "range": "stddev: 0.10042",
            "group": "engine",
            "extra": "mean: 5.2555 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.3165729569469,
            "unit": "iter/sec",
            "range": "stddev: 0.0099969",
            "group": "import-export",
            "extra": "mean: 431.67 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 1.9863305074608724,
            "unit": "iter/sec",
            "range": "stddev: 0.050825",
            "group": "import-export",
            "extra": "mean: 503.44 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 1.4691624403325052,
            "unit": "iter/sec",
            "range": "stddev: 0.059185",
            "group": "import-export",
            "extra": "mean: 680.66 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 1.368431355191124,
            "unit": "iter/sec",
            "range": "stddev: 0.078855",
            "group": "import-export",
            "extra": "mean: 730.76 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 1083.2498008456753,
            "unit": "iter/sec",
            "range": "stddev: 0.00026885",
            "group": "node",
            "extra": "mean: 923.15 usec\nrounds: 192"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 215.27166339661377,
            "unit": "iter/sec",
            "range": "stddev: 0.00056130",
            "group": "node",
            "extra": "mean: 4.6453 msec\nrounds: 132"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 190.6746617241505,
            "unit": "iter/sec",
            "range": "stddev: 0.0012667",
            "group": "node",
            "extra": "mean: 5.2445 msec\nrounds: 109"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 195.13421288236472,
            "unit": "iter/sec",
            "range": "stddev: 0.0028464",
            "group": "node",
            "extra": "mean: 5.1247 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 43.878698135841844,
            "unit": "iter/sec",
            "range": "stddev: 0.0024712",
            "group": "node",
            "extra": "mean: 22.790 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 42.73665505753365,
            "unit": "iter/sec",
            "range": "stddev: 0.0029275",
            "group": "node",
            "extra": "mean: 23.399 msec\nrounds: 100"
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
          "pythonVersion": "3.8.6",
          "metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "2c5293ded4514c36a2754acbe67aa778e27c4886",
          "message": "Fix `run_get_node`/`run_get_pk` namedtuples (#4677)\n\nFix a regression made in #4669, whereby the namedtuple's were incorrectly named",
          "timestamp": "2021-01-26T10:10:20Z",
          "url": "https://github.com/aiidateam/aiida-core/commit/2c5293ded4514c36a2754acbe67aa778e27c4886",
          "distinct": true,
          "tree_id": "923ca9e8b12bb048c12c7d1a7dac915f45122725"
        },
        "date": 1611656401262,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.2651751038996855,
            "unit": "iter/sec",
            "range": "stddev: 0.0092838",
            "group": "engine",
            "extra": "mean: 306.26 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.7874293837088654,
            "unit": "iter/sec",
            "range": "stddev: 0.040564",
            "group": "engine",
            "extra": "mean: 1.2700 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.8758966287844768,
            "unit": "iter/sec",
            "range": "stddev: 0.060747",
            "group": "engine",
            "extra": "mean: 1.1417 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.1908439302080704,
            "unit": "iter/sec",
            "range": "stddev: 0.14527",
            "group": "engine",
            "extra": "mean: 5.2399 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.21990629612926568,
            "unit": "iter/sec",
            "range": "stddev: 0.083231",
            "group": "engine",
            "extra": "mean: 4.5474 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.497715565615389,
            "unit": "iter/sec",
            "range": "stddev: 0.054467",
            "group": "engine",
            "extra": "mean: 400.37 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.599530051438614,
            "unit": "iter/sec",
            "range": "stddev: 0.056686",
            "group": "engine",
            "extra": "mean: 1.6680 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.6683662909541437,
            "unit": "iter/sec",
            "range": "stddev: 0.092272",
            "group": "engine",
            "extra": "mean: 1.4962 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.1670736545443903,
            "unit": "iter/sec",
            "range": "stddev: 0.12486",
            "group": "engine",
            "extra": "mean: 5.9854 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.1980762388898248,
            "unit": "iter/sec",
            "range": "stddev: 0.11407",
            "group": "engine",
            "extra": "mean: 5.0486 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.1183447008849523,
            "unit": "iter/sec",
            "range": "stddev: 0.0059196",
            "group": "import-export",
            "extra": "mean: 472.07 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 1.800934617711628,
            "unit": "iter/sec",
            "range": "stddev: 0.056840",
            "group": "import-export",
            "extra": "mean: 555.27 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 1.3938836772901984,
            "unit": "iter/sec",
            "range": "stddev: 0.043817",
            "group": "import-export",
            "extra": "mean: 717.42 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 1.242084869802228,
            "unit": "iter/sec",
            "range": "stddev: 0.059028",
            "group": "import-export",
            "extra": "mean: 805.10 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 1019.7560377751472,
            "unit": "iter/sec",
            "range": "stddev: 0.00018481",
            "group": "node",
            "extra": "mean: 980.63 usec\nrounds: 218"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 208.92561145132578,
            "unit": "iter/sec",
            "range": "stddev: 0.00070513",
            "group": "node",
            "extra": "mean: 4.7864 msec\nrounds: 139"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 201.27033607734168,
            "unit": "iter/sec",
            "range": "stddev: 0.00055616",
            "group": "node",
            "extra": "mean: 4.9684 msec\nrounds: 136"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 211.668236066386,
            "unit": "iter/sec",
            "range": "stddev: 0.00036162",
            "group": "node",
            "extra": "mean: 4.7244 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 42.6310136610213,
            "unit": "iter/sec",
            "range": "stddev: 0.0021322",
            "group": "node",
            "extra": "mean: 23.457 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 40.15233888921912,
            "unit": "iter/sec",
            "range": "stddev: 0.012329",
            "group": "node",
            "extra": "mean: 24.905 msec\nrounds: 100"
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
          "pythonVersion": "3.8.6",
          "metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "4c9d44af4d8c2550444d9d528dce1b890c7772f6",
          "message": "Use importlib in .ci folder",
          "timestamp": "2021-01-26T11:53:29+01:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/4c9d44af4d8c2550444d9d528dce1b890c7772f6",
          "distinct": true,
          "tree_id": "364d3b1c5ada0b94a3794230400e0f764503b7d5"
        },
        "date": 1611661326174,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.5308818523498644,
            "unit": "iter/sec",
            "range": "stddev: 0.0069060",
            "group": "engine",
            "extra": "mean: 283.22 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.8339667226500244,
            "unit": "iter/sec",
            "range": "stddev: 0.045284",
            "group": "engine",
            "extra": "mean: 1.1991 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.9385371128976928,
            "unit": "iter/sec",
            "range": "stddev: 0.055322",
            "group": "engine",
            "extra": "mean: 1.0655 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.1916052154014025,
            "unit": "iter/sec",
            "range": "stddev: 0.11389",
            "group": "engine",
            "extra": "mean: 5.2191 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.22130416719198706,
            "unit": "iter/sec",
            "range": "stddev: 0.13452",
            "group": "engine",
            "extra": "mean: 4.5187 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.6559294055833824,
            "unit": "iter/sec",
            "range": "stddev: 0.0099994",
            "group": "engine",
            "extra": "mean: 376.52 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.6248982936627516,
            "unit": "iter/sec",
            "range": "stddev: 0.056399",
            "group": "engine",
            "extra": "mean: 1.6003 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.7005173994612588,
            "unit": "iter/sec",
            "range": "stddev: 0.080478",
            "group": "engine",
            "extra": "mean: 1.4275 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.16818174148521067,
            "unit": "iter/sec",
            "range": "stddev: 0.16120",
            "group": "engine",
            "extra": "mean: 5.9459 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.20229434842776978,
            "unit": "iter/sec",
            "range": "stddev: 0.13460",
            "group": "engine",
            "extra": "mean: 4.9433 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.3325182254444647,
            "unit": "iter/sec",
            "range": "stddev: 0.0051758",
            "group": "import-export",
            "extra": "mean: 428.72 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.0152681355786073,
            "unit": "iter/sec",
            "range": "stddev: 0.050101",
            "group": "import-export",
            "extra": "mean: 496.21 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 1.5121892261959264,
            "unit": "iter/sec",
            "range": "stddev: 0.061595",
            "group": "import-export",
            "extra": "mean: 661.29 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 1.4278137960657704,
            "unit": "iter/sec",
            "range": "stddev: 0.046547",
            "group": "import-export",
            "extra": "mean: 700.37 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 1134.6813630158101,
            "unit": "iter/sec",
            "range": "stddev: 0.000045882",
            "group": "node",
            "extra": "mean: 881.30 usec\nrounds: 193"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 227.95140796784202,
            "unit": "iter/sec",
            "range": "stddev: 0.00035288",
            "group": "node",
            "extra": "mean: 4.3869 msec\nrounds: 137"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 180.80144943293,
            "unit": "iter/sec",
            "range": "stddev: 0.0015149",
            "group": "node",
            "extra": "mean: 5.5309 msec\nrounds: 126"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 235.40414388237687,
            "unit": "iter/sec",
            "range": "stddev: 0.00024794",
            "group": "node",
            "extra": "mean: 4.2480 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 46.58261294088168,
            "unit": "iter/sec",
            "range": "stddev: 0.0014472",
            "group": "node",
            "extra": "mean: 21.467 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 41.673994083485816,
            "unit": "iter/sec",
            "range": "stddev: 0.018677",
            "group": "node",
            "extra": "mean: 23.996 msec\nrounds: 100"
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
          "pythonVersion": "3.8.6",
          "metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "dffff843e38ff6aa4819e521a1d51bb12e483ada",
          "message": "Merge pull request #4678 from ramirezfranciscof/negative_zero\n\nFix: pre-store hash for -0. and 0. is now the same",
          "timestamp": "2021-01-26T13:32:29+01:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/dffff843e38ff6aa4819e521a1d51bb12e483ada",
          "distinct": true,
          "tree_id": "5d2a232b45f9aac15e0547da9083cd62b210f650"
        },
        "date": 1611664949424,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.0179319356014704,
            "unit": "iter/sec",
            "range": "stddev: 0.0099928",
            "group": "engine",
            "extra": "mean: 331.35 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.7277897928618925,
            "unit": "iter/sec",
            "range": "stddev: 0.059081",
            "group": "engine",
            "extra": "mean: 1.3740 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.8353728152394193,
            "unit": "iter/sec",
            "range": "stddev: 0.086884",
            "group": "engine",
            "extra": "mean: 1.1971 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.18551849498973175,
            "unit": "iter/sec",
            "range": "stddev: 0.15454",
            "group": "engine",
            "extra": "mean: 5.3903 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.2140611040241909,
            "unit": "iter/sec",
            "range": "stddev: 0.18828",
            "group": "engine",
            "extra": "mean: 4.6716 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.5842927714930757,
            "unit": "iter/sec",
            "range": "stddev: 0.015657",
            "group": "engine",
            "extra": "mean: 386.95 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.6293332979047233,
            "unit": "iter/sec",
            "range": "stddev: 0.11294",
            "group": "engine",
            "extra": "mean: 1.5890 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.685404226059771,
            "unit": "iter/sec",
            "range": "stddev: 0.10413",
            "group": "engine",
            "extra": "mean: 1.4590 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.17204733974791186,
            "unit": "iter/sec",
            "range": "stddev: 0.44092",
            "group": "engine",
            "extra": "mean: 5.8124 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.16972325497569762,
            "unit": "iter/sec",
            "range": "stddev: 0.78743",
            "group": "engine",
            "extra": "mean: 5.8919 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.0283629253516593,
            "unit": "iter/sec",
            "range": "stddev: 0.015747",
            "group": "import-export",
            "extra": "mean: 493.01 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 1.6813747046360799,
            "unit": "iter/sec",
            "range": "stddev: 0.054042",
            "group": "import-export",
            "extra": "mean: 594.75 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 1.2508824433588792,
            "unit": "iter/sec",
            "range": "stddev: 0.054044",
            "group": "import-export",
            "extra": "mean: 799.44 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 1.1380998885746263,
            "unit": "iter/sec",
            "range": "stddev: 0.052768",
            "group": "import-export",
            "extra": "mean: 878.66 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 840.1335865091335,
            "unit": "iter/sec",
            "range": "stddev: 0.00090159",
            "group": "node",
            "extra": "mean: 1.1903 msec\nrounds: 185"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 189.84762415798593,
            "unit": "iter/sec",
            "range": "stddev: 0.0014261",
            "group": "node",
            "extra": "mean: 5.2674 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 173.7022279953314,
            "unit": "iter/sec",
            "range": "stddev: 0.0013663",
            "group": "node",
            "extra": "mean: 5.7570 msec\nrounds: 119"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 185.76289609582122,
            "unit": "iter/sec",
            "range": "stddev: 0.00099720",
            "group": "node",
            "extra": "mean: 5.3832 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 39.180176205289925,
            "unit": "iter/sec",
            "range": "stddev: 0.0042934",
            "group": "node",
            "extra": "mean: 25.523 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 39.13082872456251,
            "unit": "iter/sec",
            "range": "stddev: 0.0049965",
            "group": "node",
            "extra": "mean: 25.555 msec\nrounds: 100"
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
          "pythonVersion": "3.8.7",
          "metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "d304dfc796926bcbed3fbd4e68aae431ea891365",
          "message": "ci: update paramiko version (#4686)\n\nNow that the Github Action runners switched to Ubuntu 20.04, the default SSH\r\nkey format of OpenSSH changed and is no longer supported by paramiko\r\n<=2.7.1.",
          "timestamp": "2021-01-27T12:16:23+01:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/d304dfc796926bcbed3fbd4e68aae431ea891365",
          "distinct": true,
          "tree_id": "0bb0ddfdc7beacbd381ae790d0847482c30dd675"
        },
        "date": 1611746708505,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.946800867452743,
            "unit": "iter/sec",
            "range": "stddev: 0.0065947",
            "group": "engine",
            "extra": "mean: 253.37 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.9407053813584422,
            "unit": "iter/sec",
            "range": "stddev: 0.044947",
            "group": "engine",
            "extra": "mean: 1.0630 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 1.0340813150607373,
            "unit": "iter/sec",
            "range": "stddev: 0.076152",
            "group": "engine",
            "extra": "mean: 967.04 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.20787146869728834,
            "unit": "iter/sec",
            "range": "stddev: 0.13115",
            "group": "engine",
            "extra": "mean: 4.8107 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.24108413349840474,
            "unit": "iter/sec",
            "range": "stddev: 0.11406",
            "group": "engine",
            "extra": "mean: 4.1479 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.7977282450007683,
            "unit": "iter/sec",
            "range": "stddev: 0.056697",
            "group": "engine",
            "extra": "mean: 357.43 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.7015273181625261,
            "unit": "iter/sec",
            "range": "stddev: 0.049489",
            "group": "engine",
            "extra": "mean: 1.4255 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.7832605448838983,
            "unit": "iter/sec",
            "range": "stddev: 0.10564",
            "group": "engine",
            "extra": "mean: 1.2767 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.18604936160990915,
            "unit": "iter/sec",
            "range": "stddev: 0.12394",
            "group": "engine",
            "extra": "mean: 5.3749 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.22102202766593881,
            "unit": "iter/sec",
            "range": "stddev: 0.13398",
            "group": "engine",
            "extra": "mean: 4.5244 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.6175540057537177,
            "unit": "iter/sec",
            "range": "stddev: 0.0081345",
            "group": "import-export",
            "extra": "mean: 382.04 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.195111440651233,
            "unit": "iter/sec",
            "range": "stddev: 0.012062",
            "group": "import-export",
            "extra": "mean: 455.56 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 1.6819221455352555,
            "unit": "iter/sec",
            "range": "stddev: 0.051637",
            "group": "import-export",
            "extra": "mean: 594.56 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 1.5381286533060479,
            "unit": "iter/sec",
            "range": "stddev: 0.059438",
            "group": "import-export",
            "extra": "mean: 650.14 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 1230.4179659352385,
            "unit": "iter/sec",
            "range": "stddev: 0.000067903",
            "group": "node",
            "extra": "mean: 812.73 usec\nrounds: 204"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 253.1862976529415,
            "unit": "iter/sec",
            "range": "stddev: 0.00024509",
            "group": "node",
            "extra": "mean: 3.9497 msec\nrounds: 150"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 238.0843743398221,
            "unit": "iter/sec",
            "range": "stddev: 0.00032950",
            "group": "node",
            "extra": "mean: 4.2002 msec\nrounds: 141"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 255.6313849421383,
            "unit": "iter/sec",
            "range": "stddev: 0.00031240",
            "group": "node",
            "extra": "mean: 3.9119 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 50.61687565868885,
            "unit": "iter/sec",
            "range": "stddev: 0.0012318",
            "group": "node",
            "extra": "mean: 19.756 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 49.69084534966099,
            "unit": "iter/sec",
            "range": "stddev: 0.0012970",
            "group": "node",
            "extra": "mean: 20.124 msec\nrounds: 100"
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
          "pythonVersion": "3.8.7",
          "metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "950d1a424ac5be54c4771f8aeb7dd7189bf23ec9",
          "message": "Fix: release signal handlers after run execution (#4682)\n\nAfter a process has executed (when running rather than submitting),\r\nreturn the signal handlers to their original state.\r\n\r\nThis fixes an issue whereby using `CTRL-C` after a process has run still calls the `process.kill`.\r\nIt also releases the `kill_process` function's reference to the process,\r\na step towards allowing the finished process to be garbage collected.",
          "timestamp": "2021-01-27T11:42:05Z",
          "url": "https://github.com/aiidateam/aiida-core/commit/950d1a424ac5be54c4771f8aeb7dd7189bf23ec9",
          "distinct": true,
          "tree_id": "8bd2bb11b95812035d980ab2e032f22d19c140e0"
        },
        "date": 1611748343183,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.210375102255976,
            "unit": "iter/sec",
            "range": "stddev: 0.0098260",
            "group": "engine",
            "extra": "mean: 311.49 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.7792775593673665,
            "unit": "iter/sec",
            "range": "stddev: 0.049565",
            "group": "engine",
            "extra": "mean: 1.2832 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.8605972055615372,
            "unit": "iter/sec",
            "range": "stddev: 0.089735",
            "group": "engine",
            "extra": "mean: 1.1620 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.1863045186519324,
            "unit": "iter/sec",
            "range": "stddev: 0.11950",
            "group": "engine",
            "extra": "mean: 5.3676 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.21366198818076268,
            "unit": "iter/sec",
            "range": "stddev: 0.092308",
            "group": "engine",
            "extra": "mean: 4.6803 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.492321961679064,
            "unit": "iter/sec",
            "range": "stddev: 0.010296",
            "group": "engine",
            "extra": "mean: 401.23 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.5690595399812308,
            "unit": "iter/sec",
            "range": "stddev: 0.086792",
            "group": "engine",
            "extra": "mean: 1.7573 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.6384311264594072,
            "unit": "iter/sec",
            "range": "stddev: 0.089051",
            "group": "engine",
            "extra": "mean: 1.5663 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.16146338216656175,
            "unit": "iter/sec",
            "range": "stddev: 0.12616",
            "group": "engine",
            "extra": "mean: 6.1934 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.19034401866776193,
            "unit": "iter/sec",
            "range": "stddev: 0.13247",
            "group": "engine",
            "extra": "mean: 5.2536 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.048549874750969,
            "unit": "iter/sec",
            "range": "stddev: 0.0073858",
            "group": "import-export",
            "extra": "mean: 488.15 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 1.8219445062576618,
            "unit": "iter/sec",
            "range": "stddev: 0.0054660",
            "group": "import-export",
            "extra": "mean: 548.86 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 1.3577787436656208,
            "unit": "iter/sec",
            "range": "stddev: 0.054831",
            "group": "import-export",
            "extra": "mean: 736.50 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 1.1927763766501813,
            "unit": "iter/sec",
            "range": "stddev: 0.072558",
            "group": "import-export",
            "extra": "mean: 838.38 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 886.1260136195086,
            "unit": "iter/sec",
            "range": "stddev: 0.00033115",
            "group": "node",
            "extra": "mean: 1.1285 msec\nrounds: 207"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 189.62078863001489,
            "unit": "iter/sec",
            "range": "stddev: 0.0013278",
            "group": "node",
            "extra": "mean: 5.2737 msec\nrounds: 129"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 187.1107707326664,
            "unit": "iter/sec",
            "range": "stddev: 0.0011581",
            "group": "node",
            "extra": "mean: 5.3444 msec\nrounds: 133"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 188.0731663747255,
            "unit": "iter/sec",
            "range": "stddev: 0.0015747",
            "group": "node",
            "extra": "mean: 5.3171 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 40.1236572437051,
            "unit": "iter/sec",
            "range": "stddev: 0.0068040",
            "group": "node",
            "extra": "mean: 24.923 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 40.981025424609086,
            "unit": "iter/sec",
            "range": "stddev: 0.0020914",
            "group": "node",
            "extra": "mean: 24.402 msec\nrounds: 100"
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
          "pythonVersion": "3.8.7",
          "metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "02ebeb88e231172cfebc5a510a72671da4ef061b",
          "message": "Fix: `PluginVersionProvider` should cache process class (#4683)\n\nCurrently, the `PluginVersionProvider` is caching process instance, rather than class.\r\nThis commit fixes the bug, meaning the cache will now work correctly.\r\nRemoving the reference to the process instance also is a step towards allowing it to be garbage collected.",
          "timestamp": "2021-01-27T12:01:39Z",
          "url": "https://github.com/aiidateam/aiida-core/commit/02ebeb88e231172cfebc5a510a72671da4ef061b",
          "distinct": true,
          "tree_id": "0a4289af19491bc9e27acfde002e51ad774d3d75"
        },
        "date": 1611749392719,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.8786948141837554,
            "unit": "iter/sec",
            "range": "stddev: 0.034609",
            "group": "engine",
            "extra": "mean: 257.82 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.9511080897687343,
            "unit": "iter/sec",
            "range": "stddev: 0.061385",
            "group": "engine",
            "extra": "mean: 1.0514 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 1.105511482579476,
            "unit": "iter/sec",
            "range": "stddev: 0.067373",
            "group": "engine",
            "extra": "mean: 904.56 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.22321127508245964,
            "unit": "iter/sec",
            "range": "stddev: 0.085153",
            "group": "engine",
            "extra": "mean: 4.4801 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.2584893441800172,
            "unit": "iter/sec",
            "range": "stddev: 0.090945",
            "group": "engine",
            "extra": "mean: 3.8686 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.920210317308353,
            "unit": "iter/sec",
            "range": "stddev: 0.058201",
            "group": "engine",
            "extra": "mean: 342.44 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.7385173411772376,
            "unit": "iter/sec",
            "range": "stddev: 0.061229",
            "group": "engine",
            "extra": "mean: 1.3541 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.8083374474799503,
            "unit": "iter/sec",
            "range": "stddev: 0.084158",
            "group": "engine",
            "extra": "mean: 1.2371 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.19560563681553583,
            "unit": "iter/sec",
            "range": "stddev: 0.086568",
            "group": "engine",
            "extra": "mean: 5.1123 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.234853808714425,
            "unit": "iter/sec",
            "range": "stddev: 0.077730",
            "group": "engine",
            "extra": "mean: 4.2580 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.5264798750334303,
            "unit": "iter/sec",
            "range": "stddev: 0.053784",
            "group": "import-export",
            "extra": "mean: 395.81 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.2585798957075016,
            "unit": "iter/sec",
            "range": "stddev: 0.049606",
            "group": "import-export",
            "extra": "mean: 442.76 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 1.7922800816253002,
            "unit": "iter/sec",
            "range": "stddev: 0.063515",
            "group": "import-export",
            "extra": "mean: 557.95 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 1.6731541436211501,
            "unit": "iter/sec",
            "range": "stddev: 0.053511",
            "group": "import-export",
            "extra": "mean: 597.67 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 1364.0577369683012,
            "unit": "iter/sec",
            "range": "stddev: 0.000038140",
            "group": "node",
            "extra": "mean: 733.11 usec\nrounds: 213"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 280.05245179680014,
            "unit": "iter/sec",
            "range": "stddev: 0.000058442",
            "group": "node",
            "extra": "mean: 3.5708 msec\nrounds: 163"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 259.48090884335437,
            "unit": "iter/sec",
            "range": "stddev: 0.00042571",
            "group": "node",
            "extra": "mean: 3.8538 msec\nrounds: 155"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 285.03829134553405,
            "unit": "iter/sec",
            "range": "stddev: 0.00023341",
            "group": "node",
            "extra": "mean: 3.5083 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 55.4183745736881,
            "unit": "iter/sec",
            "range": "stddev: 0.00099169",
            "group": "node",
            "extra": "mean: 18.045 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 49.08823430158693,
            "unit": "iter/sec",
            "range": "stddev: 0.016242",
            "group": "node",
            "extra": "mean: 20.371 msec\nrounds: 100"
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
          "pythonVersion": "3.8.7",
          "metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "cdb2e57906e10e31f04ccb58923643292f38b6c0",
          "message": "remove leftover use of Computer.name (#4681)\n\nRemove leftover use of deprecated Computer.name attribute in `verdi\r\ncomputer list`.\r\n\r\nAlso update minimum version of click dependency to 7.1, since click 7.1\r\nintroduces additional whitespace in the verdi autodocs (running with \r\nclick 7.0 locally resulted in pre-commit check failing on CI).\r\n\r\nCo-authored-by: Chris Sewell <chrisj_sewell@hotmail.com>",
          "timestamp": "2021-01-27T13:25:47+01:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/cdb2e57906e10e31f04ccb58923643292f38b6c0",
          "distinct": true,
          "tree_id": "10c3167904a028802c5cbc31aa834aef7786deab"
        },
        "date": 1611750880417,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.539126580147642,
            "unit": "iter/sec",
            "range": "stddev: 0.073891",
            "group": "engine",
            "extra": "mean: 282.56 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.9209005420795494,
            "unit": "iter/sec",
            "range": "stddev: 0.10270",
            "group": "engine",
            "extra": "mean: 1.0859 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 1.0382020739820739,
            "unit": "iter/sec",
            "range": "stddev: 0.10811",
            "group": "engine",
            "extra": "mean: 963.20 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.21094821959186155,
            "unit": "iter/sec",
            "range": "stddev: 0.11943",
            "group": "engine",
            "extra": "mean: 4.7405 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.2505915394654722,
            "unit": "iter/sec",
            "range": "stddev: 0.12654",
            "group": "engine",
            "extra": "mean: 3.9906 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.894241357810351,
            "unit": "iter/sec",
            "range": "stddev: 0.069359",
            "group": "engine",
            "extra": "mean: 345.51 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.705927159250845,
            "unit": "iter/sec",
            "range": "stddev: 0.094011",
            "group": "engine",
            "extra": "mean: 1.4166 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.7901338406393128,
            "unit": "iter/sec",
            "range": "stddev: 0.11462",
            "group": "engine",
            "extra": "mean: 1.2656 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.1879612826737655,
            "unit": "iter/sec",
            "range": "stddev: 0.16844",
            "group": "engine",
            "extra": "mean: 5.3202 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.2257391012896035,
            "unit": "iter/sec",
            "range": "stddev: 0.14969",
            "group": "engine",
            "extra": "mean: 4.4299 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.5830184375194523,
            "unit": "iter/sec",
            "range": "stddev: 0.065482",
            "group": "import-export",
            "extra": "mean: 387.14 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.382558022258502,
            "unit": "iter/sec",
            "range": "stddev: 0.0031488",
            "group": "import-export",
            "extra": "mean: 419.72 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 1.7677086526471029,
            "unit": "iter/sec",
            "range": "stddev: 0.064850",
            "group": "import-export",
            "extra": "mean: 565.70 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 1.6194861175481303,
            "unit": "iter/sec",
            "range": "stddev: 0.069847",
            "group": "import-export",
            "extra": "mean: 617.48 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 1350.7814998708,
            "unit": "iter/sec",
            "range": "stddev: 0.000033631",
            "group": "node",
            "extra": "mean: 740.31 usec\nrounds: 181"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 177.0025131962713,
            "unit": "iter/sec",
            "range": "stddev: 0.017625",
            "group": "node",
            "extra": "mean: 5.6496 msec\nrounds: 142"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 250.5193833217747,
            "unit": "iter/sec",
            "range": "stddev: 0.00015588",
            "group": "node",
            "extra": "mean: 3.9917 msec\nrounds: 115"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 291.25802861830016,
            "unit": "iter/sec",
            "range": "stddev: 0.00011421",
            "group": "node",
            "extra": "mean: 3.4334 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 54.85735464288299,
            "unit": "iter/sec",
            "range": "stddev: 0.0011457",
            "group": "node",
            "extra": "mean: 18.229 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 54.20142870556099,
            "unit": "iter/sec",
            "range": "stddev: 0.0012562",
            "group": "node",
            "extra": "mean: 18.450 msec\nrounds: 100"
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
          "pythonVersion": "3.8.7",
          "metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "3cf1d2ef9f0300a0ed9ef7cfade7c4f49ba09d91",
          "message": "Add `to_aiida_type` to the public API (#4672)\n\nSince `to_aiida_type` is intended for public use,\r\nthis commit makes it part of the public API,\r\nvia `from aiida.orm import to_aiida_type`.",
          "timestamp": "2021-01-27T13:01:48Z",
          "url": "https://github.com/aiidateam/aiida-core/commit/3cf1d2ef9f0300a0ed9ef7cfade7c4f49ba09d91",
          "distinct": true,
          "tree_id": "91af0213f8085466ab3c1718a24051b6fe1532a9"
        },
        "date": 1611753041571,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.108654829879591,
            "unit": "iter/sec",
            "range": "stddev: 0.049522",
            "group": "engine",
            "extra": "mean: 321.68 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.8194594802705405,
            "unit": "iter/sec",
            "range": "stddev: 0.056622",
            "group": "engine",
            "extra": "mean: 1.2203 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.9187729324058624,
            "unit": "iter/sec",
            "range": "stddev: 0.12650",
            "group": "engine",
            "extra": "mean: 1.0884 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.19859750164317114,
            "unit": "iter/sec",
            "range": "stddev: 0.51143",
            "group": "engine",
            "extra": "mean: 5.0353 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.2341621665712054,
            "unit": "iter/sec",
            "range": "stddev: 0.16863",
            "group": "engine",
            "extra": "mean: 4.2705 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 3.0830306650192143,
            "unit": "iter/sec",
            "range": "stddev: 0.020416",
            "group": "engine",
            "extra": "mean: 324.36 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.6817685117901809,
            "unit": "iter/sec",
            "range": "stddev: 0.058718",
            "group": "engine",
            "extra": "mean: 1.4668 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.7763984377422051,
            "unit": "iter/sec",
            "range": "stddev: 0.047834",
            "group": "engine",
            "extra": "mean: 1.2880 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.18821615250128018,
            "unit": "iter/sec",
            "range": "stddev: 0.16386",
            "group": "engine",
            "extra": "mean: 5.3130 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.22291836596222464,
            "unit": "iter/sec",
            "range": "stddev: 0.10470",
            "group": "engine",
            "extra": "mean: 4.4859 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.628192763063598,
            "unit": "iter/sec",
            "range": "stddev: 0.048774",
            "group": "import-export",
            "extra": "mean: 380.49 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.2687197936231245,
            "unit": "iter/sec",
            "range": "stddev: 0.062886",
            "group": "import-export",
            "extra": "mean: 440.78 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 1.7698383607642576,
            "unit": "iter/sec",
            "range": "stddev: 0.057768",
            "group": "import-export",
            "extra": "mean: 565.02 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 1.6378634270103571,
            "unit": "iter/sec",
            "range": "stddev: 0.053070",
            "group": "import-export",
            "extra": "mean: 610.55 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 1419.606239987138,
            "unit": "iter/sec",
            "range": "stddev: 0.000077168",
            "group": "node",
            "extra": "mean: 704.42 usec\nrounds: 200"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 291.5822737099153,
            "unit": "iter/sec",
            "range": "stddev: 0.00012098",
            "group": "node",
            "extra": "mean: 3.4296 msec\nrounds: 148"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 257.3270795060886,
            "unit": "iter/sec",
            "range": "stddev: 0.00013233",
            "group": "node",
            "extra": "mean: 3.8861 msec\nrounds: 133"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 285.0979072970022,
            "unit": "iter/sec",
            "range": "stddev: 0.00016738",
            "group": "node",
            "extra": "mean: 3.5076 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 45.59206371869799,
            "unit": "iter/sec",
            "range": "stddev: 0.016435",
            "group": "node",
            "extra": "mean: 21.934 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 53.00213067928467,
            "unit": "iter/sec",
            "range": "stddev: 0.0014966",
            "group": "node",
            "extra": "mean: 18.867 msec\nrounds: 100"
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
          "pythonVersion": "3.8.7",
          "metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "e9f234ec256dd2f2b94c70be9826917bd9861ec0",
          "message": "Add .dockerignore (#4564)\n\nThis commit adds a `.dockerignore` file to inhibit any unecessary/unwanted files being copied into the Docker container,\r\nduring the `COPY . aiida-core` command,\r\nand also reduces the build time.",
          "timestamp": "2021-01-27T14:23:11Z",
          "url": "https://github.com/aiidateam/aiida-core/commit/e9f234ec256dd2f2b94c70be9826917bd9861ec0",
          "distinct": true,
          "tree_id": "d8bafef396f9ee1057066c92f20aae0c34b9ef24"
        },
        "date": 1611757962845,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.153717116332391,
            "unit": "iter/sec",
            "range": "stddev: 0.0068017",
            "group": "engine",
            "extra": "mean: 317.09 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.7575854126000914,
            "unit": "iter/sec",
            "range": "stddev: 0.053933",
            "group": "engine",
            "extra": "mean: 1.3200 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.864009255311381,
            "unit": "iter/sec",
            "range": "stddev: 0.085566",
            "group": "engine",
            "extra": "mean: 1.1574 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.19256895019877324,
            "unit": "iter/sec",
            "range": "stddev: 0.20810",
            "group": "engine",
            "extra": "mean: 5.1929 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.21885279714695988,
            "unit": "iter/sec",
            "range": "stddev: 0.13877",
            "group": "engine",
            "extra": "mean: 4.5693 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.6969680709758106,
            "unit": "iter/sec",
            "range": "stddev: 0.049533",
            "group": "engine",
            "extra": "mean: 370.79 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.6320999137775369,
            "unit": "iter/sec",
            "range": "stddev: 0.052958",
            "group": "engine",
            "extra": "mean: 1.5820 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.7075242760778704,
            "unit": "iter/sec",
            "range": "stddev: 0.071530",
            "group": "engine",
            "extra": "mean: 1.4134 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.1658835754769376,
            "unit": "iter/sec",
            "range": "stddev: 0.14337",
            "group": "engine",
            "extra": "mean: 6.0283 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.20157674781883841,
            "unit": "iter/sec",
            "range": "stddev: 0.12260",
            "group": "engine",
            "extra": "mean: 4.9609 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.358041866541769,
            "unit": "iter/sec",
            "range": "stddev: 0.0076243",
            "group": "import-export",
            "extra": "mean: 424.08 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.0562459692984323,
            "unit": "iter/sec",
            "range": "stddev: 0.051123",
            "group": "import-export",
            "extra": "mean: 486.32 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 1.6175421612738432,
            "unit": "iter/sec",
            "range": "stddev: 0.044211",
            "group": "import-export",
            "extra": "mean: 618.22 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 1.4548392336706486,
            "unit": "iter/sec",
            "range": "stddev: 0.039111",
            "group": "import-export",
            "extra": "mean: 687.36 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 1022.1386652054708,
            "unit": "iter/sec",
            "range": "stddev: 0.00051040",
            "group": "node",
            "extra": "mean: 978.34 usec\nrounds: 131"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 242.69468864448177,
            "unit": "iter/sec",
            "range": "stddev: 0.00028475",
            "group": "node",
            "extra": "mean: 4.1204 msec\nrounds: 139"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 217.32313102664332,
            "unit": "iter/sec",
            "range": "stddev: 0.00058001",
            "group": "node",
            "extra": "mean: 4.6014 msec\nrounds: 138"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 238.28565045669308,
            "unit": "iter/sec",
            "range": "stddev: 0.00038758",
            "group": "node",
            "extra": "mean: 4.1966 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 44.62734740634028,
            "unit": "iter/sec",
            "range": "stddev: 0.014392",
            "group": "node",
            "extra": "mean: 22.408 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 45.55977142088931,
            "unit": "iter/sec",
            "range": "stddev: 0.014172",
            "group": "node",
            "extra": "mean: 21.949 msec\nrounds: 100"
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
          "pythonVersion": "3.8.7",
          "metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "d2b255b713a82230ad4f298b112d7095c31c1f24",
          "message": "CI: Remove `--use-feature=2020-resolver` pip feature flag tests. (#4689)\n\nThe feature is now on by default in the latest stable release.",
          "timestamp": "2021-01-27T14:51:33Z",
          "url": "https://github.com/aiidateam/aiida-core/commit/d2b255b713a82230ad4f298b112d7095c31c1f24",
          "distinct": true,
          "tree_id": "029884fba3c2bce87e30251f69307c449c98c7ad"
        },
        "date": 1611759716050,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.1349911000533868,
            "unit": "iter/sec",
            "range": "stddev: 0.012020",
            "group": "engine",
            "extra": "mean: 318.98 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.7239031946050295,
            "unit": "iter/sec",
            "range": "stddev: 0.047874",
            "group": "engine",
            "extra": "mean: 1.3814 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.8093787902391966,
            "unit": "iter/sec",
            "range": "stddev: 0.090511",
            "group": "engine",
            "extra": "mean: 1.2355 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.17060769427603292,
            "unit": "iter/sec",
            "range": "stddev: 0.099893",
            "group": "engine",
            "extra": "mean: 5.8614 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.20055355020842924,
            "unit": "iter/sec",
            "range": "stddev: 0.099931",
            "group": "engine",
            "extra": "mean: 4.9862 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.3215885820712314,
            "unit": "iter/sec",
            "range": "stddev: 0.060656",
            "group": "engine",
            "extra": "mean: 430.74 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.5689890735960133,
            "unit": "iter/sec",
            "range": "stddev: 0.056314",
            "group": "engine",
            "extra": "mean: 1.7575 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.6389295776636952,
            "unit": "iter/sec",
            "range": "stddev: 0.077592",
            "group": "engine",
            "extra": "mean: 1.5651 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.15279761204828624,
            "unit": "iter/sec",
            "range": "stddev: 0.11912",
            "group": "engine",
            "extra": "mean: 6.5446 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.1826705079140345,
            "unit": "iter/sec",
            "range": "stddev: 0.13731",
            "group": "engine",
            "extra": "mean: 5.4743 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.1771173121172858,
            "unit": "iter/sec",
            "range": "stddev: 0.012187",
            "group": "import-export",
            "extra": "mean: 459.32 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 1.8510946398790618,
            "unit": "iter/sec",
            "range": "stddev: 0.058071",
            "group": "import-export",
            "extra": "mean: 540.22 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 1.4088310148507592,
            "unit": "iter/sec",
            "range": "stddev: 0.060039",
            "group": "import-export",
            "extra": "mean: 709.81 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 1.3187914154465032,
            "unit": "iter/sec",
            "range": "stddev: 0.060821",
            "group": "import-export",
            "extra": "mean: 758.27 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 849.9673509681658,
            "unit": "iter/sec",
            "range": "stddev: 0.0017325",
            "group": "node",
            "extra": "mean: 1.1765 msec\nrounds: 190"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 196.785815972656,
            "unit": "iter/sec",
            "range": "stddev: 0.0016913",
            "group": "node",
            "extra": "mean: 5.0817 msec\nrounds: 122"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 198.12467915320633,
            "unit": "iter/sec",
            "range": "stddev: 0.00058403",
            "group": "node",
            "extra": "mean: 5.0473 msec\nrounds: 126"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 220.87431658096068,
            "unit": "iter/sec",
            "range": "stddev: 0.00032560",
            "group": "node",
            "extra": "mean: 4.5275 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 44.8527036203981,
            "unit": "iter/sec",
            "range": "stddev: 0.0026031",
            "group": "node",
            "extra": "mean: 22.295 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 45.393467182653694,
            "unit": "iter/sec",
            "range": "stddev: 0.0025275",
            "group": "node",
            "extra": "mean: 22.030 msec\nrounds: 100"
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
          "pythonVersion": "3.8.7",
          "metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "dcc80618368f405c02c9eaa6d122177e78d70a4b",
          "message": "CI: Notify slack on failure of the test-install workflow. (#4690)",
          "timestamp": "2021-01-27T16:02:48Z",
          "url": "https://github.com/aiidateam/aiida-core/commit/dcc80618368f405c02c9eaa6d122177e78d70a4b",
          "distinct": true,
          "tree_id": "c7d46b03e00e94b7fac292d93772a1c8d71cf772"
        },
        "date": 1611763946752,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.2054312581059516,
            "unit": "iter/sec",
            "range": "stddev: 0.059383",
            "group": "engine",
            "extra": "mean: 311.97 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.8058922757652505,
            "unit": "iter/sec",
            "range": "stddev: 0.058821",
            "group": "engine",
            "extra": "mean: 1.2409 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.8864412369445261,
            "unit": "iter/sec",
            "range": "stddev: 0.079649",
            "group": "engine",
            "extra": "mean: 1.1281 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.18971214221910326,
            "unit": "iter/sec",
            "range": "stddev: 0.12254",
            "group": "engine",
            "extra": "mean: 5.2711 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.21879167707138095,
            "unit": "iter/sec",
            "range": "stddev: 0.10186",
            "group": "engine",
            "extra": "mean: 4.5706 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.5795445119183573,
            "unit": "iter/sec",
            "range": "stddev: 0.054145",
            "group": "engine",
            "extra": "mean: 387.67 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.6225908480196428,
            "unit": "iter/sec",
            "range": "stddev: 0.055943",
            "group": "engine",
            "extra": "mean: 1.6062 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.6954099124500812,
            "unit": "iter/sec",
            "range": "stddev: 0.074796",
            "group": "engine",
            "extra": "mean: 1.4380 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.16764255021534813,
            "unit": "iter/sec",
            "range": "stddev: 0.12310",
            "group": "engine",
            "extra": "mean: 5.9651 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.19778403560805408,
            "unit": "iter/sec",
            "range": "stddev: 0.15924",
            "group": "engine",
            "extra": "mean: 5.0560 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.3567938217857987,
            "unit": "iter/sec",
            "range": "stddev: 0.0064328",
            "group": "import-export",
            "extra": "mean: 424.31 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 1.972505424414504,
            "unit": "iter/sec",
            "range": "stddev: 0.049413",
            "group": "import-export",
            "extra": "mean: 506.97 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 1.5611958002024513,
            "unit": "iter/sec",
            "range": "stddev: 0.057149",
            "group": "import-export",
            "extra": "mean: 640.53 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 1.410155124794884,
            "unit": "iter/sec",
            "range": "stddev: 0.060553",
            "group": "import-export",
            "extra": "mean: 709.14 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 1135.7304690982396,
            "unit": "iter/sec",
            "range": "stddev: 0.000044882",
            "group": "node",
            "extra": "mean: 880.49 usec\nrounds: 209"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 201.19848508384013,
            "unit": "iter/sec",
            "range": "stddev: 0.0023154",
            "group": "node",
            "extra": "mean: 4.9702 msec\nrounds: 126"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 215.93290150371453,
            "unit": "iter/sec",
            "range": "stddev: 0.00037028",
            "group": "node",
            "extra": "mean: 4.6311 msec\nrounds: 126"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 239.25524035436666,
            "unit": "iter/sec",
            "range": "stddev: 0.00030763",
            "group": "node",
            "extra": "mean: 4.1796 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 44.8305105753061,
            "unit": "iter/sec",
            "range": "stddev: 0.0016778",
            "group": "node",
            "extra": "mean: 22.306 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 44.55960756192712,
            "unit": "iter/sec",
            "range": "stddev: 0.0018431",
            "group": "node",
            "extra": "mean: 22.442 msec\nrounds: 100"
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
          "pythonVersion": "3.8.7",
          "metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "97cecd2ef57946dd53a0ecd2005f3d2d0a94a2aa",
          "message": "Improve namedtuples in aiida/engine (#4688)\n\nThis commit replaces old-style namedtuples with `typing.NamedTuple` sub-classes.\r\nThis allows for typing of fields and better default value assignment.\r\n\r\nNote this feature requires python>=3.6.1,\r\nbut it is anyhow intended that python 3.6 be dropped for the next release.",
          "timestamp": "2021-01-27T16:27:28Z",
          "url": "https://github.com/aiidateam/aiida-core/commit/97cecd2ef57946dd53a0ecd2005f3d2d0a94a2aa",
          "distinct": true,
          "tree_id": "be611dfc75a388167d29fbdf7fc4afa02083c7bb"
        },
        "date": 1611765423981,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.4209341742610637,
            "unit": "iter/sec",
            "range": "stddev: 0.0046123",
            "group": "engine",
            "extra": "mean: 292.32 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.8087063445622047,
            "unit": "iter/sec",
            "range": "stddev: 0.049351",
            "group": "engine",
            "extra": "mean: 1.2365 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.9152374693744867,
            "unit": "iter/sec",
            "range": "stddev: 0.077541",
            "group": "engine",
            "extra": "mean: 1.0926 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.18934058176208424,
            "unit": "iter/sec",
            "range": "stddev: 0.088937",
            "group": "engine",
            "extra": "mean: 5.2815 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.21819022150446968,
            "unit": "iter/sec",
            "range": "stddev: 0.088139",
            "group": "engine",
            "extra": "mean: 4.5832 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.6035985919647997,
            "unit": "iter/sec",
            "range": "stddev: 0.011353",
            "group": "engine",
            "extra": "mean: 384.08 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.6046050237896763,
            "unit": "iter/sec",
            "range": "stddev: 0.055058",
            "group": "engine",
            "extra": "mean: 1.6540 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.6911875755005648,
            "unit": "iter/sec",
            "range": "stddev: 0.060125",
            "group": "engine",
            "extra": "mean: 1.4468 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.16565503637344428,
            "unit": "iter/sec",
            "range": "stddev: 0.092619",
            "group": "engine",
            "extra": "mean: 6.0366 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.19594335730819915,
            "unit": "iter/sec",
            "range": "stddev: 0.11307",
            "group": "engine",
            "extra": "mean: 5.1035 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.247978385029812,
            "unit": "iter/sec",
            "range": "stddev: 0.051688",
            "group": "import-export",
            "extra": "mean: 444.84 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 1.9853187964735128,
            "unit": "iter/sec",
            "range": "stddev: 0.050404",
            "group": "import-export",
            "extra": "mean: 503.70 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 1.5631634651932305,
            "unit": "iter/sec",
            "range": "stddev: 0.041404",
            "group": "import-export",
            "extra": "mean: 639.73 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 1.4394841560735405,
            "unit": "iter/sec",
            "range": "stddev: 0.042863",
            "group": "import-export",
            "extra": "mean: 694.69 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 1147.1546047444717,
            "unit": "iter/sec",
            "range": "stddev: 0.000053448",
            "group": "node",
            "extra": "mean: 871.72 usec\nrounds: 196"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 231.9454927674105,
            "unit": "iter/sec",
            "range": "stddev: 0.00033361",
            "group": "node",
            "extra": "mean: 4.3114 msec\nrounds: 133"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 192.88563696788893,
            "unit": "iter/sec",
            "range": "stddev: 0.0034055",
            "group": "node",
            "extra": "mean: 5.1844 msec\nrounds: 129"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 245.00996413866037,
            "unit": "iter/sec",
            "range": "stddev: 0.00012037",
            "group": "node",
            "extra": "mean: 4.0815 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 45.7654182916141,
            "unit": "iter/sec",
            "range": "stddev: 0.0015465",
            "group": "node",
            "extra": "mean: 21.851 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 42.03009169296104,
            "unit": "iter/sec",
            "range": "stddev: 0.015895",
            "group": "node",
            "extra": "mean: 23.792 msec\nrounds: 100"
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
          "pythonVersion": "3.8.7",
          "metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "a490fe07ab5752f04efaac338c1f1a9ef648426a",
          "message": "test AiiDA ipython magics and remove copy-paste in docs (#4548)\n\nAdds tests for the AiiDA IPython extension.\r\n\r\nAlso:\r\n * move some additional lines from the registration snippet to\r\n  aiida-core (where we can adapt it if the IPython API ever changes)\r\n * rename and deprecate misnomer `load_ipython_extension` to\r\n   `register_ipython_extension` (to be removed in aiida 3)\r\n * include the snippet to register the AiiDA ipython magics from the\r\n   aiida-core codebase instead of the (already outdated) copy-pasted\r\n  version.\r\n * revisit the corresponding section of the documentation, starting\r\n  with the setup, and removing some generic information about jupyter.",
          "timestamp": "2021-01-28T11:35:19+01:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/a490fe07ab5752f04efaac338c1f1a9ef648426a",
          "distinct": true,
          "tree_id": "df1a18e7bcad8e261d21edd143dfbcca29a10db4"
        },
        "date": 1611830671624,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.4536011495067847,
            "unit": "iter/sec",
            "range": "stddev: 0.054734",
            "group": "engine",
            "extra": "mean: 289.55 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.8708576918989791,
            "unit": "iter/sec",
            "range": "stddev: 0.050944",
            "group": "engine",
            "extra": "mean: 1.1483 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.9858333582515034,
            "unit": "iter/sec",
            "range": "stddev: 0.069103",
            "group": "engine",
            "extra": "mean: 1.0144 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.19863680849221813,
            "unit": "iter/sec",
            "range": "stddev: 0.11723",
            "group": "engine",
            "extra": "mean: 5.0343 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.23237089325876464,
            "unit": "iter/sec",
            "range": "stddev: 0.079869",
            "group": "engine",
            "extra": "mean: 4.3035 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.7791725062720607,
            "unit": "iter/sec",
            "range": "stddev: 0.045284",
            "group": "engine",
            "extra": "mean: 359.82 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.6707545962041825,
            "unit": "iter/sec",
            "range": "stddev: 0.050660",
            "group": "engine",
            "extra": "mean: 1.4909 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.7481068429366599,
            "unit": "iter/sec",
            "range": "stddev: 0.082262",
            "group": "engine",
            "extra": "mean: 1.3367 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.17452339040335638,
            "unit": "iter/sec",
            "range": "stddev: 0.089748",
            "group": "engine",
            "extra": "mean: 5.7299 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.20825732638148636,
            "unit": "iter/sec",
            "range": "stddev: 0.086684",
            "group": "engine",
            "extra": "mean: 4.8018 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.4519716958674582,
            "unit": "iter/sec",
            "range": "stddev: 0.013378",
            "group": "import-export",
            "extra": "mean: 407.84 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.0843851249235263,
            "unit": "iter/sec",
            "range": "stddev: 0.046763",
            "group": "import-export",
            "extra": "mean: 479.76 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 1.5907886218425362,
            "unit": "iter/sec",
            "range": "stddev: 0.052764",
            "group": "import-export",
            "extra": "mean: 628.62 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 1.4092561189081427,
            "unit": "iter/sec",
            "range": "stddev: 0.077228",
            "group": "import-export",
            "extra": "mean: 709.59 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 1193.9776165003527,
            "unit": "iter/sec",
            "range": "stddev: 0.000081120",
            "group": "node",
            "extra": "mean: 837.54 usec\nrounds: 205"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 232.76180077175243,
            "unit": "iter/sec",
            "range": "stddev: 0.00099732",
            "group": "node",
            "extra": "mean: 4.2962 msec\nrounds: 147"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 206.5450248896095,
            "unit": "iter/sec",
            "range": "stddev: 0.0025622",
            "group": "node",
            "extra": "mean: 4.8416 msec\nrounds: 128"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 249.86778933016132,
            "unit": "iter/sec",
            "range": "stddev: 0.00059093",
            "group": "node",
            "extra": "mean: 4.0021 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 48.92080424540435,
            "unit": "iter/sec",
            "range": "stddev: 0.0015753",
            "group": "node",
            "extra": "mean: 20.441 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 47.82207235590449,
            "unit": "iter/sec",
            "range": "stddev: 0.0023684",
            "group": "node",
            "extra": "mean: 20.911 msec\nrounds: 100"
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
          "pythonVersion": "3.8.7",
          "metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "48fa47584c993cdac019c6199bc045a4c19da152",
          "message": "🐛 FIX: typing failure (#4700)\n\nAs of numpy v1.20, `numpy.inf` is no longer recognised as an integer type",
          "timestamp": "2021-02-01T16:58:01+01:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/48fa47584c993cdac019c6199bc045a4c19da152",
          "distinct": true,
          "tree_id": "b59c99e11366e8799e977e6ad12134514952c498"
        },
        "date": 1612195742497,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 2.907641586577871,
            "unit": "iter/sec",
            "range": "stddev: 0.016277",
            "group": "engine",
            "extra": "mean: 343.92 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.6639709497894977,
            "unit": "iter/sec",
            "range": "stddev: 0.14606",
            "group": "engine",
            "extra": "mean: 1.5061 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.769338043064394,
            "unit": "iter/sec",
            "range": "stddev: 0.12949",
            "group": "engine",
            "extra": "mean: 1.2998 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.16518074281984274,
            "unit": "iter/sec",
            "range": "stddev: 0.28154",
            "group": "engine",
            "extra": "mean: 6.0540 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.18687775244455807,
            "unit": "iter/sec",
            "range": "stddev: 0.28675",
            "group": "engine",
            "extra": "mean: 5.3511 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.1294578862484674,
            "unit": "iter/sec",
            "range": "stddev: 0.056223",
            "group": "engine",
            "extra": "mean: 469.60 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.514161649906011,
            "unit": "iter/sec",
            "range": "stddev: 0.22563",
            "group": "engine",
            "extra": "mean: 1.9449 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.6006292955299164,
            "unit": "iter/sec",
            "range": "stddev: 0.12744",
            "group": "engine",
            "extra": "mean: 1.6649 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.14016591944706483,
            "unit": "iter/sec",
            "range": "stddev: 0.34903",
            "group": "engine",
            "extra": "mean: 7.1344 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.16599362734213866,
            "unit": "iter/sec",
            "range": "stddev: 0.27841",
            "group": "engine",
            "extra": "mean: 6.0243 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 1.9143854807665845,
            "unit": "iter/sec",
            "range": "stddev: 0.061455",
            "group": "import-export",
            "extra": "mean: 522.36 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 1.7363224186856923,
            "unit": "iter/sec",
            "range": "stddev: 0.021723",
            "group": "import-export",
            "extra": "mean: 575.93 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 1.2285125462107462,
            "unit": "iter/sec",
            "range": "stddev: 0.072965",
            "group": "import-export",
            "extra": "mean: 813.99 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 1.1005604316018014,
            "unit": "iter/sec",
            "range": "stddev: 0.083238",
            "group": "import-export",
            "extra": "mean: 908.63 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 656.936219867946,
            "unit": "iter/sec",
            "range": "stddev: 0.00069633",
            "group": "node",
            "extra": "mean: 1.5222 msec\nrounds: 161"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 128.4339349393622,
            "unit": "iter/sec",
            "range": "stddev: 0.0030615",
            "group": "node",
            "extra": "mean: 7.7861 msec\nrounds: 101"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 152.6293063693742,
            "unit": "iter/sec",
            "range": "stddev: 0.0012075",
            "group": "node",
            "extra": "mean: 6.5518 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 160.65431598289828,
            "unit": "iter/sec",
            "range": "stddev: 0.0014656",
            "group": "node",
            "extra": "mean: 6.2245 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 41.333000081886,
            "unit": "iter/sec",
            "range": "stddev: 0.0014541",
            "group": "node",
            "extra": "mean: 24.194 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 37.66316378377917,
            "unit": "iter/sec",
            "range": "stddev: 0.0034551",
            "group": "node",
            "extra": "mean: 26.551 msec\nrounds: 100"
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
          "pythonVersion": "3.8.7",
          "metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "285ca45c41db75fbb0ed7eae5f6cdd3afd652da3",
          "message": "BUILD: drop support for python 3.6 (#4701)\n\nFollowing our support table, we drop python 3.6 support.",
          "timestamp": "2021-02-08T11:28:09+01:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/285ca45c41db75fbb0ed7eae5f6cdd3afd652da3",
          "distinct": true,
          "tree_id": "d2ac2f2e81d6c4a360b0643112b613ef08110a32"
        },
        "date": 1612780705311,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.1389251055452,
            "unit": "iter/sec",
            "range": "stddev: 0.010469",
            "group": "engine",
            "extra": "mean: 318.58 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.748396289058325,
            "unit": "iter/sec",
            "range": "stddev: 0.052936",
            "group": "engine",
            "extra": "mean: 1.3362 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.8352158328415044,
            "unit": "iter/sec",
            "range": "stddev: 0.076082",
            "group": "engine",
            "extra": "mean: 1.1973 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.18383401376294833,
            "unit": "iter/sec",
            "range": "stddev: 0.079618",
            "group": "engine",
            "extra": "mean: 5.4397 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.21307608470574443,
            "unit": "iter/sec",
            "range": "stddev: 0.096204",
            "group": "engine",
            "extra": "mean: 4.6932 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.3736859568582385,
            "unit": "iter/sec",
            "range": "stddev: 0.053008",
            "group": "engine",
            "extra": "mean: 421.29 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.571827222050785,
            "unit": "iter/sec",
            "range": "stddev: 0.066698",
            "group": "engine",
            "extra": "mean: 1.7488 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.6337411229439399,
            "unit": "iter/sec",
            "range": "stddev: 0.081563",
            "group": "engine",
            "extra": "mean: 1.5779 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.16050281542099815,
            "unit": "iter/sec",
            "range": "stddev: 0.094189",
            "group": "engine",
            "extra": "mean: 6.2304 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.1908510569996621,
            "unit": "iter/sec",
            "range": "stddev: 0.094543",
            "group": "engine",
            "extra": "mean: 5.2397 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.095466154032992,
            "unit": "iter/sec",
            "range": "stddev: 0.0056199",
            "group": "import-export",
            "extra": "mean: 477.22 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 1.7684418413541398,
            "unit": "iter/sec",
            "range": "stddev: 0.053965",
            "group": "import-export",
            "extra": "mean: 565.47 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 1.2854997940134278,
            "unit": "iter/sec",
            "range": "stddev: 0.058525",
            "group": "import-export",
            "extra": "mean: 777.91 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 1.1947161550254775,
            "unit": "iter/sec",
            "range": "stddev: 0.054380",
            "group": "import-export",
            "extra": "mean: 837.02 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 930.5294744491107,
            "unit": "iter/sec",
            "range": "stddev: 0.00012557",
            "group": "node",
            "extra": "mean: 1.0747 msec\nrounds: 208"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 208.04472136747847,
            "unit": "iter/sec",
            "range": "stddev: 0.00024444",
            "group": "node",
            "extra": "mean: 4.8067 msec\nrounds: 135"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 189.77358749375261,
            "unit": "iter/sec",
            "range": "stddev: 0.00074015",
            "group": "node",
            "extra": "mean: 5.2694 msec\nrounds: 125"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 193.59226859380695,
            "unit": "iter/sec",
            "range": "stddev: 0.00095199",
            "group": "node",
            "extra": "mean: 5.1655 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 40.08955202526467,
            "unit": "iter/sec",
            "range": "stddev: 0.0037949",
            "group": "node",
            "extra": "mean: 24.944 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 40.52657667588861,
            "unit": "iter/sec",
            "range": "stddev: 0.0019323",
            "group": "node",
            "extra": "mean: 24.675 msec\nrounds: 100"
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
          "pythonVersion": "3.8.7",
          "metadata": "postgres:12.3, rabbitmq:3.8.3"
        },
        "commit": {
          "id": "5d5fd4f4970743ddb2956a553db967e017fbbb0e",
          "message": "BUILD: bump jenkins dockerimage to 20.04 (#4714)\n\nDespite python3.7 being installed on the Jenkins dockerimage, pip\r\ninstall failed after dropping python 3.6 support (likely because pip\r\nfrom python 3.6 was being used).\r\n\r\nWe update ubuntu to 20.04, which comes with python 3.8.2 by default.",
          "timestamp": "2021-02-08T12:17:44+01:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/5d5fd4f4970743ddb2956a553db967e017fbbb0e",
          "distinct": true,
          "tree_id": "1efb6fa6841eb293d28aca1729fae41939ca1aab"
        },
        "date": 1612783631680,
        "benches": [
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.411897006724591,
            "unit": "iter/sec",
            "range": "stddev: 0.0083882",
            "group": "engine",
            "extra": "mean: 293.09 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.8117093585477106,
            "unit": "iter/sec",
            "range": "stddev: 0.044066",
            "group": "engine",
            "extra": "mean: 1.2320 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.8977875730519869,
            "unit": "iter/sec",
            "range": "stddev: 0.082455",
            "group": "engine",
            "extra": "mean: 1.1138 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.18748490262002662,
            "unit": "iter/sec",
            "range": "stddev: 0.083519",
            "group": "engine",
            "extra": "mean: 5.3338 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.21867301098393244,
            "unit": "iter/sec",
            "range": "stddev: 0.12007",
            "group": "engine",
            "extra": "mean: 4.5730 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.5286529856315942,
            "unit": "iter/sec",
            "range": "stddev: 0.052782",
            "group": "engine",
            "extra": "mean: 395.47 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.6141332550453958,
            "unit": "iter/sec",
            "range": "stddev: 0.050607",
            "group": "engine",
            "extra": "mean: 1.6283 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.6913659015033138,
            "unit": "iter/sec",
            "range": "stddev: 0.076944",
            "group": "engine",
            "extra": "mean: 1.4464 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.1657986079928882,
            "unit": "iter/sec",
            "range": "stddev: 0.11304",
            "group": "engine",
            "extra": "mean: 6.0314 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.1969532091806992,
            "unit": "iter/sec",
            "range": "stddev: 0.090226",
            "group": "engine",
            "extra": "mean: 5.0773 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[no-objects]",
            "value": 2.271966369675258,
            "unit": "iter/sec",
            "range": "stddev: 0.050781",
            "group": "import-export",
            "extra": "mean: 440.15 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_export[with-objects]",
            "value": 2.0002358461417544,
            "unit": "iter/sec",
            "range": "stddev: 0.053140",
            "group": "import-export",
            "extra": "mean: 499.94 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[no-objects]",
            "value": 1.5226903769329747,
            "unit": "iter/sec",
            "range": "stddev: 0.050647",
            "group": "import-export",
            "extra": "mean: 656.73 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_importexport.py::test_import[with-objects]",
            "value": 1.4141713985032727,
            "unit": "iter/sec",
            "range": "stddev: 0.053348",
            "group": "import-export",
            "extra": "mean: 707.13 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 1096.250114898771,
            "unit": "iter/sec",
            "range": "stddev: 0.00019318",
            "group": "node",
            "extra": "mean: 912.20 usec\nrounds: 192"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 235.12933710352866,
            "unit": "iter/sec",
            "range": "stddev: 0.00016280",
            "group": "node",
            "extra": "mean: 4.2530 msec\nrounds: 122"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 215.728152389119,
            "unit": "iter/sec",
            "range": "stddev: 0.00016021",
            "group": "node",
            "extra": "mean: 4.6355 msec\nrounds: 123"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 233.74257786348704,
            "unit": "iter/sec",
            "range": "stddev: 0.00098471",
            "group": "node",
            "extra": "mean: 4.2782 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 46.35167805377803,
            "unit": "iter/sec",
            "range": "stddev: 0.0013361",
            "group": "node",
            "extra": "mean: 21.574 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 42.82940269965724,
            "unit": "iter/sec",
            "range": "stddev: 0.011293",
            "group": "node",
            "extra": "mean: 23.348 msec\nrounds: 100"
          }
        ]
      }
    ]
  }
}