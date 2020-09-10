window.BENCHMARK_DATA = {
  "lastUpdate": 1599756062761,
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
            "name": "tests/benchmark/test_engine_run.py::test_workchain[basic-loop]",
            "value": 3.4230933763464417,
            "unit": "iter/sec",
            "range": "stddev: 0.013876",
            "group": "engine-run",
            "extra": "mean: 292.13 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine_run.py::test_workchain[serial-wc-loop]",
            "value": 0.8118020122037132,
            "unit": "iter/sec",
            "range": "stddev: 0.056500",
            "group": "engine-run",
            "extra": "mean: 1.2318 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine_run.py::test_workchain[threaded-wc-loop]",
            "value": 0.9223326829589825,
            "unit": "iter/sec",
            "range": "stddev: 0.048760",
            "group": "engine-run",
            "extra": "mean: 1.0842 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine_run.py::test_workchain[serial-calcjob-loop]",
            "value": 0.17412278513525872,
            "unit": "iter/sec",
            "range": "stddev: 0.18007",
            "group": "engine-run",
            "extra": "mean: 5.7431 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine_run.py::test_workchain[threaded-calcjob-loop]",
            "value": 0.20374746894490228,
            "unit": "iter/sec",
            "range": "stddev: 0.086164",
            "group": "engine-run",
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
      }
    ]
  }
}
