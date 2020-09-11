window.BENCHMARK_DATA = {
  "lastUpdate": 1599832060242,
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
      }
    ]
  }
}