window.BENCHMARK_DATA = {
  "lastUpdate": 1681378855277,
  "repoUrl": "https://github.com/aiidateam/aiida-core",
  "xAxis": "id",
  "oneChartGroups": [],
  "entries": {
    "pytest-benchmarks:ubuntu-22.04,psql_dos": [
      {
        "cpu": {
          "speed": "2.60",
          "cores": 2,
          "physicalCores": 2,
          "processors": 1
        },
        "extra": {
          "pythonVersion": "3.10.10",
          "metadata": "postgres:12.14, rabbitmq:3.8.14-management"
        },
        "commit": {
          "id": "888e90b0879ff1d1329224f49431b22ce51fbdf0",
          "message": "Docs: Update AiiDA logo in `README.md`\n\nIt was still pointing to the logo on the old website which is now a 404.\nIt is replaced with an SVG that is included in the `docs/source/images`\ndirectory.",
          "timestamp": "2023-04-13T11:30:18+02:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/888e90b0879ff1d1329224f49431b22ce51fbdf0",
          "distinct": true,
          "tree_id": "115ee823b8334f6ff8e0dc00085bfc10be93dc02"
        },
        "date": 1681378848555,
        "benches": [
          {
            "name": "tests/benchmark/test_archive.py::test_export[no-objects]",
            "value": 2.8876392836835816,
            "unit": "iter/sec",
            "range": "stddev: 0.022420",
            "group": "import-export",
            "extra": "mean: 346.30 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_export[with-objects]",
            "value": 2.6769811935876464,
            "unit": "iter/sec",
            "range": "stddev: 0.056983",
            "group": "import-export",
            "extra": "mean: 373.56 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[no-objects]",
            "value": 3.7607903173737296,
            "unit": "iter/sec",
            "range": "stddev: 0.062393",
            "group": "import-export",
            "extra": "mean: 265.90 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[with-objects]",
            "value": 3.6652388702176535,
            "unit": "iter/sec",
            "range": "stddev: 0.070781",
            "group": "import-export",
            "extra": "mean: 272.83 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 2.8756702260971028,
            "unit": "iter/sec",
            "range": "stddev: 0.010986",
            "group": "engine",
            "extra": "mean: 347.75 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.6492074721229942,
            "unit": "iter/sec",
            "range": "stddev: 0.071163",
            "group": "engine",
            "extra": "mean: 1.5403 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.7016592365409008,
            "unit": "iter/sec",
            "range": "stddev: 0.083850",
            "group": "engine",
            "extra": "mean: 1.4252 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.163695739341247,
            "unit": "iter/sec",
            "range": "stddev: 0.27571",
            "group": "engine",
            "extra": "mean: 6.1089 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.18997491021935023,
            "unit": "iter/sec",
            "range": "stddev: 0.20074",
            "group": "engine",
            "extra": "mean: 5.2639 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.572326572472463,
            "unit": "iter/sec",
            "range": "stddev: 0.021279",
            "group": "engine",
            "extra": "mean: 388.75 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.5488749547201898,
            "unit": "iter/sec",
            "range": "stddev: 0.083758",
            "group": "engine",
            "extra": "mean: 1.8219 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.6277458708044702,
            "unit": "iter/sec",
            "range": "stddev: 0.072544",
            "group": "engine",
            "extra": "mean: 1.5930 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.1514930467423563,
            "unit": "iter/sec",
            "range": "stddev: 0.099107",
            "group": "engine",
            "extra": "mean: 6.6010 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.1690153761653955,
            "unit": "iter/sec",
            "range": "stddev: 0.11221",
            "group": "engine",
            "extra": "mean: 5.9166 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 335.7967069945107,
            "unit": "iter/sec",
            "range": "stddev: 0.00025407",
            "group": "node",
            "extra": "mean: 2.9780 msec\nrounds: 224"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 120.73994451204337,
            "unit": "iter/sec",
            "range": "stddev: 0.0014195",
            "group": "node",
            "extra": "mean: 8.2823 msec\nrounds: 121"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 71.3890311858818,
            "unit": "iter/sec",
            "range": "stddev: 0.0017212",
            "group": "node",
            "extra": "mean: 14.008 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 201.25897471140746,
            "unit": "iter/sec",
            "range": "stddev: 0.00045655",
            "group": "node",
            "extra": "mean: 4.9687 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 49.31935234779601,
            "unit": "iter/sec",
            "range": "stddev: 0.0021739",
            "group": "node",
            "extra": "mean: 20.276 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 46.88613692271245,
            "unit": "iter/sec",
            "range": "stddev: 0.0022107",
            "group": "node",
            "extra": "mean: 21.328 msec\nrounds: 100"
          }
        ]
      }
    ]
  }
}