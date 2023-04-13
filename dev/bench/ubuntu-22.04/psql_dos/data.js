window.BENCHMARK_DATA = {
  "lastUpdate": 1681390481301,
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
      },
      {
        "cpu": {
          "speed": "2.80",
          "cores": 2,
          "physicalCores": 2,
          "processors": 1
        },
        "extra": {
          "pythonVersion": "3.10.11",
          "metadata": "postgres:12.14, rabbitmq:3.8.14-management"
        },
        "commit": {
          "id": "e1923a1faf0ce8222b83a364b1c0f13437f0b28f",
          "message": "Dependencies: Update requirement `importlib-metadata~=4.13` (#5963)\n\nThis allows us to revert 2a2bf21dc6b49d7783795f14d1de6d1fdcff007b\r\nalong with some other type ignore statements that are no longer\r\nnecessary.",
          "timestamp": "2023-04-13T14:45:45+02:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/e1923a1faf0ce8222b83a364b1c0f13437f0b28f",
          "distinct": true,
          "tree_id": "5436b7f15390228df838e62d07efca3c7cd7b31c"
        },
        "date": 1681390474387,
        "benches": [
          {
            "name": "tests/benchmark/test_archive.py::test_export[no-objects]",
            "value": 3.453061514596286,
            "unit": "iter/sec",
            "range": "stddev: 0.060640",
            "group": "import-export",
            "extra": "mean: 289.60 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_export[with-objects]",
            "value": 3.378898960927328,
            "unit": "iter/sec",
            "range": "stddev: 0.050798",
            "group": "import-export",
            "extra": "mean: 295.95 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[no-objects]",
            "value": 4.348488426340887,
            "unit": "iter/sec",
            "range": "stddev: 0.054279",
            "group": "import-export",
            "extra": "mean: 229.96 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[with-objects]",
            "value": 4.315716971304825,
            "unit": "iter/sec",
            "range": "stddev: 0.050243",
            "group": "import-export",
            "extra": "mean: 231.71 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.641542526912811,
            "unit": "iter/sec",
            "range": "stddev: 0.0079459",
            "group": "engine",
            "extra": "mean: 274.61 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.8088282341931257,
            "unit": "iter/sec",
            "range": "stddev: 0.062240",
            "group": "engine",
            "extra": "mean: 1.2364 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.9416360117384664,
            "unit": "iter/sec",
            "range": "stddev: 0.041733",
            "group": "engine",
            "extra": "mean: 1.0620 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.21084670562386007,
            "unit": "iter/sec",
            "range": "stddev: 0.10449",
            "group": "engine",
            "extra": "mean: 4.7428 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.23542665687781367,
            "unit": "iter/sec",
            "range": "stddev: 0.13683",
            "group": "engine",
            "extra": "mean: 4.2476 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.8453617530576993,
            "unit": "iter/sec",
            "range": "stddev: 0.030508",
            "group": "engine",
            "extra": "mean: 351.45 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.6484923103608282,
            "unit": "iter/sec",
            "range": "stddev: 0.051552",
            "group": "engine",
            "extra": "mean: 1.5420 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.7341357889685475,
            "unit": "iter/sec",
            "range": "stddev: 0.039502",
            "group": "engine",
            "extra": "mean: 1.3621 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.17341185448971924,
            "unit": "iter/sec",
            "range": "stddev: 0.17681",
            "group": "engine",
            "extra": "mean: 5.7666 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.20319902973435452,
            "unit": "iter/sec",
            "range": "stddev: 0.085038",
            "group": "engine",
            "extra": "mean: 4.9213 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 366.5382300100786,
            "unit": "iter/sec",
            "range": "stddev: 0.00011974",
            "group": "node",
            "extra": "mean: 2.7282 msec\nrounds: 250"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 143.66763117520412,
            "unit": "iter/sec",
            "range": "stddev: 0.00016370",
            "group": "node",
            "extra": "mean: 6.9605 msec\nrounds: 113"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 85.91739138354352,
            "unit": "iter/sec",
            "range": "stddev: 0.00065645",
            "group": "node",
            "extra": "mean: 11.639 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 242.00902651096746,
            "unit": "iter/sec",
            "range": "stddev: 0.00020077",
            "group": "node",
            "extra": "mean: 4.1321 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 54.43664639846015,
            "unit": "iter/sec",
            "range": "stddev: 0.018313",
            "group": "node",
            "extra": "mean: 18.370 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 60.31041554971896,
            "unit": "iter/sec",
            "range": "stddev: 0.0014946",
            "group": "node",
            "extra": "mean: 16.581 msec\nrounds: 100"
          }
        ]
      }
    ]
  }
}