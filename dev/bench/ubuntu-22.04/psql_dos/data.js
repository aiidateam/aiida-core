window.BENCHMARK_DATA = {
  "lastUpdate": 1683795787413,
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
      },
      {
        "cpu": {
          "speed": "2.60",
          "cores": 2,
          "physicalCores": 2,
          "processors": 1
        },
        "extra": {
          "pythonVersion": "3.10.11",
          "metadata": "postgres:12.14, rabbitmq:3.8.14-management"
        },
        "commit": {
          "id": "9a81d106b4eeefff52fb6986116bf9e95ea7b1c4",
          "message": "Dependencies: Bump `graphviz` version to `0.19` (#5965)\n\nIn the commit 80045ae7308de673a838c152998a6257c9a79134 a feature was\r\nadded that allows the user to specify the output name of the generated\r\ngraph with `verdi node graph generate`. This filename is passed to the\r\n`outfile` input argument of the `graphviz.render()` method, but this was\r\nonly added in v0.19 of `graphviz`, see:\r\n\r\nhttps://graphviz.readthedocs.io/en/latest/changelog.html#version-0-19\r\n\r\nHere we bump the `graphviz` version to `0.19`.",
          "timestamp": "2023-04-13T23:21:04+02:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/9a81d106b4eeefff52fb6986116bf9e95ea7b1c4",
          "distinct": true,
          "tree_id": "ad5e5ad3971c3ccfdb4a63c6c2fe01f1c1a0f759"
        },
        "date": 1681421392749,
        "benches": [
          {
            "name": "tests/benchmark/test_archive.py::test_export[no-objects]",
            "value": 3.579256242913035,
            "unit": "iter/sec",
            "range": "stddev: 0.056275",
            "group": "import-export",
            "extra": "mean: 279.39 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_export[with-objects]",
            "value": 3.4381985347671282,
            "unit": "iter/sec",
            "range": "stddev: 0.056565",
            "group": "import-export",
            "extra": "mean: 290.85 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[no-objects]",
            "value": 4.415329633288599,
            "unit": "iter/sec",
            "range": "stddev: 0.058318",
            "group": "import-export",
            "extra": "mean: 226.48 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[with-objects]",
            "value": 4.307725993226,
            "unit": "iter/sec",
            "range": "stddev: 0.058684",
            "group": "import-export",
            "extra": "mean: 232.14 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.584801581547913,
            "unit": "iter/sec",
            "range": "stddev: 0.0030522",
            "group": "engine",
            "extra": "mean: 278.96 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.7812161108451136,
            "unit": "iter/sec",
            "range": "stddev: 0.058429",
            "group": "engine",
            "extra": "mean: 1.2801 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.8844831108159091,
            "unit": "iter/sec",
            "range": "stddev: 0.063325",
            "group": "engine",
            "extra": "mean: 1.1306 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.19731504000509464,
            "unit": "iter/sec",
            "range": "stddev: 0.11893",
            "group": "engine",
            "extra": "mean: 5.0680 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.22677883083688166,
            "unit": "iter/sec",
            "range": "stddev: 0.075964",
            "group": "engine",
            "extra": "mean: 4.4096 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.679863724899032,
            "unit": "iter/sec",
            "range": "stddev: 0.072456",
            "group": "engine",
            "extra": "mean: 373.15 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.6570848087895941,
            "unit": "iter/sec",
            "range": "stddev: 0.065213",
            "group": "engine",
            "extra": "mean: 1.5219 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.7364412572480489,
            "unit": "iter/sec",
            "range": "stddev: 0.053216",
            "group": "engine",
            "extra": "mean: 1.3579 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.17612793436527882,
            "unit": "iter/sec",
            "range": "stddev: 0.12494",
            "group": "engine",
            "extra": "mean: 5.6777 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.20159523283462982,
            "unit": "iter/sec",
            "range": "stddev: 0.11803",
            "group": "engine",
            "extra": "mean: 4.9604 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 328.38988367022415,
            "unit": "iter/sec",
            "range": "stddev: 0.00035154",
            "group": "node",
            "extra": "mean: 3.0452 msec\nrounds: 227"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 133.67101365222155,
            "unit": "iter/sec",
            "range": "stddev: 0.00055502",
            "group": "node",
            "extra": "mean: 7.4811 msec\nrounds: 118"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 82.25881623567584,
            "unit": "iter/sec",
            "range": "stddev: 0.0010267",
            "group": "node",
            "extra": "mean: 12.157 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 226.45760752541494,
            "unit": "iter/sec",
            "range": "stddev: 0.00070305",
            "group": "node",
            "extra": "mean: 4.4158 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 52.97156323702895,
            "unit": "iter/sec",
            "range": "stddev: 0.020251",
            "group": "node",
            "extra": "mean: 18.878 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 59.02151155201195,
            "unit": "iter/sec",
            "range": "stddev: 0.0014845",
            "group": "node",
            "extra": "mean: 16.943 msec\nrounds: 100"
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
          "pythonVersion": "3.10.11",
          "metadata": "postgres:12.14, rabbitmq:3.8.14-management"
        },
        "commit": {
          "id": "b26c2d430329cd9da1d898f1d28dbac21e9f5eea",
          "message": "Docs: Fix the `intro/tutorial.md` notebook\n\nThe notebook creates and loads a temporary profile using the\n`SqliteTempBackend` backend. This works fine as long as the profile is\nonly used in the current interpreter and no code is hit that checks the\nprofile is present in the `Config`. The reason is that although the\nprofile is loaded, it is created on the fly and not actually added to\nthe `Config` that is loaded in memory, nor is it written to the\n`config.json` file on disk.\n\nAs soon as any code is called that will check the existence of the\ntemporary profile, through the config, it will fail. A good example is\nwhen `%verdi process list` is called. At the end of the command, the\nstatus of the daemon is checked, for which a `DaemonClient` instance is\nconstructed, which calls `config.get_option('daemon.timeout', profile)`.\nThis call will validate the provided profile to check that it actually\nexists, i.e., is known within the config, which is not the case, and so\na `ProfileConfigurationError` is raised.\n\nThe solution is to update the notebook to actually add the created\ntemporary profile to the config loaded in memory. Note that this could\nhave the undesirable consequence that if the config state is written to\ndisk, the temporary profile can be added to `config.json`. This will not\nbe automatically cleaned up. Since here it concerns a demo notebook that\nwill just be run on temporary resources anyway, it not being cleaned up\nis not a problem.\n\nIdeally there would be a utility for notebooks that creates a temporary\nprofile and actually adds it to the config, and cleans it up at the end\nof the notebook. But it will be difficult to guarantee the cleanup in\nall cases.",
          "timestamp": "2023-04-13T23:21:26+02:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/b26c2d430329cd9da1d898f1d28dbac21e9f5eea",
          "distinct": true,
          "tree_id": "7c654fc4642c3e112087101166519917c8ec148e"
        },
        "date": 1681421449143,
        "benches": [
          {
            "name": "tests/benchmark/test_archive.py::test_export[no-objects]",
            "value": 3.366683778594528,
            "unit": "iter/sec",
            "range": "stddev: 0.071637",
            "group": "import-export",
            "extra": "mean: 297.03 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_export[with-objects]",
            "value": 3.2730791724785053,
            "unit": "iter/sec",
            "range": "stddev: 0.070180",
            "group": "import-export",
            "extra": "mean: 305.52 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[no-objects]",
            "value": 4.260513191936243,
            "unit": "iter/sec",
            "range": "stddev: 0.075215",
            "group": "import-export",
            "extra": "mean: 234.71 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[with-objects]",
            "value": 4.186701523515348,
            "unit": "iter/sec",
            "range": "stddev: 0.071280",
            "group": "import-export",
            "extra": "mean: 238.85 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.3569359939469345,
            "unit": "iter/sec",
            "range": "stddev: 0.0089871",
            "group": "engine",
            "extra": "mean: 297.89 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.7452247443929034,
            "unit": "iter/sec",
            "range": "stddev: 0.074201",
            "group": "engine",
            "extra": "mean: 1.3419 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.8420792806687242,
            "unit": "iter/sec",
            "range": "stddev: 0.085195",
            "group": "engine",
            "extra": "mean: 1.1875 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.189527496897559,
            "unit": "iter/sec",
            "range": "stddev: 0.10850",
            "group": "engine",
            "extra": "mean: 5.2763 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.2145893336760352,
            "unit": "iter/sec",
            "range": "stddev: 0.18386",
            "group": "engine",
            "extra": "mean: 4.6601 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.728312142518595,
            "unit": "iter/sec",
            "range": "stddev: 0.021404",
            "group": "engine",
            "extra": "mean: 366.53 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.6092788481760509,
            "unit": "iter/sec",
            "range": "stddev: 0.047924",
            "group": "engine",
            "extra": "mean: 1.6413 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.6888449127893328,
            "unit": "iter/sec",
            "range": "stddev: 0.066127",
            "group": "engine",
            "extra": "mean: 1.4517 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.16967841193285807,
            "unit": "iter/sec",
            "range": "stddev: 0.14721",
            "group": "engine",
            "extra": "mean: 5.8935 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.19066865257990673,
            "unit": "iter/sec",
            "range": "stddev: 0.13644",
            "group": "engine",
            "extra": "mean: 5.2447 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 319.2263907930296,
            "unit": "iter/sec",
            "range": "stddev: 0.00016892",
            "group": "node",
            "extra": "mean: 3.1326 msec\nrounds: 187"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 126.35694113882045,
            "unit": "iter/sec",
            "range": "stddev: 0.00054349",
            "group": "node",
            "extra": "mean: 7.9141 msec\nrounds: 107"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 77.94862971562544,
            "unit": "iter/sec",
            "range": "stddev: 0.00069041",
            "group": "node",
            "extra": "mean: 12.829 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 246.72657734078322,
            "unit": "iter/sec",
            "range": "stddev: 0.00055650",
            "group": "node",
            "extra": "mean: 4.0531 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 58.98735443609299,
            "unit": "iter/sec",
            "range": "stddev: 0.0015361",
            "group": "node",
            "extra": "mean: 16.953 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 56.93346892258012,
            "unit": "iter/sec",
            "range": "stddev: 0.0017975",
            "group": "node",
            "extra": "mean: 17.564 msec\nrounds: 100"
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
          "pythonVersion": "3.10.11",
          "metadata": "postgres:12.14, rabbitmq:3.8.14-management"
        },
        "commit": {
          "id": "30c7f442951fdb22a8e63e4f761352a56d5f8713",
          "message": "`DaemonClient`: Fix and homogenize use of `timeout` in client calls (#5960)\n\nThe `DaemonClient` provides a number of methods that will attempt to\r\ncommunicate with the daemon process, e.g., `stop_daemon` and `get_status`.\r\nThis is done through the `CircusClient`, as the main daemon process is\r\nthe circus daemonizer, which takes a timeout as argument indicating the\r\nnumber of seconds after which the call should raise if the daemon did\r\nnot respond in time.\r\n\r\nThe default timeout is set in the constructor of the `DaemonClient`\r\nbased on the `daemon.timeout` config option. It was incorrectly getting\r\nthe global value instead of the profile specific one, which is corrected\r\nby using `config.get_option('daemon.timeout', scope=profile.name)` to\r\nfetch the conifg option.\r\n\r\nA `timeout` argument is added to all `DaemonClient` methods that call\r\nthrough to the `CircusClient` that can be used to override the default\r\nthat is based on the `daemon.timeout` config option.\r\n\r\nA default is added for `wait` in the `restart_daemon` method, to\r\nhomogenize its interface with `start_daemon` and `stop_daemon`. The\r\nmanual timeout cycle in `stop_daemon` by calling `_await_condition` has\r\nbeen removed as this functionality is already performed by the circus\r\nclient itself and so is superfluous. The only place it is still used is\r\nin `start_daemon` because there the circus client is not used, since the\r\ncircus process is not actually running yet, and a \"manual\" health check\r\nneeds to be performed after the daemon process is launched. The manual\r\ncheck is added to the `stop_daemon` fixture since the check in certain\r\nunit test scenarios could give a false positive without an additional\r\nmanual grace period for `is_daemon_running` to start returning `False`.\r\n\r\nThe default for the `daemon.timeout` configuration option is decreased\r\nto 2 seconds, as this should be sufficient for most conditions for the\r\ncircus daemon process to respond. Note that this daemon process is only\r\ncharged with monitoring the daemon workers and so won't be under heavy\r\nload that will prevent it from responding in time.",
          "timestamp": "2023-04-14T09:15:13+02:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/30c7f442951fdb22a8e63e4f761352a56d5f8713",
          "distinct": true,
          "tree_id": "fe77a0319479452c2795c546c47ec1a97d2eb7a4"
        },
        "date": 1681457046546,
        "benches": [
          {
            "name": "tests/benchmark/test_archive.py::test_export[no-objects]",
            "value": 3.2997224938332144,
            "unit": "iter/sec",
            "range": "stddev: 0.071597",
            "group": "import-export",
            "extra": "mean: 303.06 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_export[with-objects]",
            "value": 3.3570458903909723,
            "unit": "iter/sec",
            "range": "stddev: 0.055168",
            "group": "import-export",
            "extra": "mean: 297.88 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[no-objects]",
            "value": 4.3315996525647575,
            "unit": "iter/sec",
            "range": "stddev: 0.064538",
            "group": "import-export",
            "extra": "mean: 230.86 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[with-objects]",
            "value": 4.294291421202677,
            "unit": "iter/sec",
            "range": "stddev: 0.062341",
            "group": "import-export",
            "extra": "mean: 232.87 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.5444146757326354,
            "unit": "iter/sec",
            "range": "stddev: 0.0027946",
            "group": "engine",
            "extra": "mean: 282.13 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.769041177036133,
            "unit": "iter/sec",
            "range": "stddev: 0.065674",
            "group": "engine",
            "extra": "mean: 1.3003 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.8686261766001969,
            "unit": "iter/sec",
            "range": "stddev: 0.064401",
            "group": "engine",
            "extra": "mean: 1.1512 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.19571260925455708,
            "unit": "iter/sec",
            "range": "stddev: 0.10536",
            "group": "engine",
            "extra": "mean: 5.1095 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.22286670063899944,
            "unit": "iter/sec",
            "range": "stddev: 0.073531",
            "group": "engine",
            "extra": "mean: 4.4870 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.5352644182458897,
            "unit": "iter/sec",
            "range": "stddev: 0.087450",
            "group": "engine",
            "extra": "mean: 394.44 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.6046988609474692,
            "unit": "iter/sec",
            "range": "stddev: 0.15224",
            "group": "engine",
            "extra": "mean: 1.6537 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.692229784177772,
            "unit": "iter/sec",
            "range": "stddev: 0.10284",
            "group": "engine",
            "extra": "mean: 1.4446 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.17364218522123598,
            "unit": "iter/sec",
            "range": "stddev: 0.091529",
            "group": "engine",
            "extra": "mean: 5.7590 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.1976613372622021,
            "unit": "iter/sec",
            "range": "stddev: 0.055858",
            "group": "engine",
            "extra": "mean: 5.0592 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 331.59521465127705,
            "unit": "iter/sec",
            "range": "stddev: 0.00030117",
            "group": "node",
            "extra": "mean: 3.0157 msec\nrounds: 218"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 134.81457061789422,
            "unit": "iter/sec",
            "range": "stddev: 0.00057737",
            "group": "node",
            "extra": "mean: 7.4176 msec\nrounds: 116"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 82.39036564303916,
            "unit": "iter/sec",
            "range": "stddev: 0.00058462",
            "group": "node",
            "extra": "mean: 12.137 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 224.47989988244467,
            "unit": "iter/sec",
            "range": "stddev: 0.00022570",
            "group": "node",
            "extra": "mean: 4.4547 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 52.48126894702487,
            "unit": "iter/sec",
            "range": "stddev: 0.022283",
            "group": "node",
            "extra": "mean: 19.054 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 57.023670827983416,
            "unit": "iter/sec",
            "range": "stddev: 0.0018535",
            "group": "node",
            "extra": "mean: 17.537 msec\nrounds: 100"
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
          "pythonVersion": "3.10.11",
          "metadata": "postgres:12.14, rabbitmq:3.8.14-management"
        },
        "commit": {
          "id": "9de3f90a157ec7c9f99c1f17f3ca3548f6d96bba",
          "message": "CLI: Add `--timeout` option to all `verdi daemon` commands (#5966)\n\nThe timeout is passed on to the `DaemonClient` and can be used to\r\noverride the default that is defined through the `daemon.timeout`\r\nconfig option. This can be useful, for example, when the default timeout\r\nset in the configuration is low such that commands don't get stuck\r\nunnecessarily long. However, for certain commands, such as `verdi daemon\r\nstop`, it might make sense to give the client a bit more time to\r\nrespond.",
          "timestamp": "2023-04-14T13:50:02+02:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/9de3f90a157ec7c9f99c1f17f3ca3548f6d96bba",
          "distinct": true,
          "tree_id": "67555b82dbbdc4878a7369e18c2ea739c4fa85e4"
        },
        "date": 1681473696010,
        "benches": [
          {
            "name": "tests/benchmark/test_archive.py::test_export[no-objects]",
            "value": 2.6486979486368263,
            "unit": "iter/sec",
            "range": "stddev: 0.013417",
            "group": "import-export",
            "extra": "mean: 377.54 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_export[with-objects]",
            "value": 2.2832809753474756,
            "unit": "iter/sec",
            "range": "stddev: 0.089780",
            "group": "import-export",
            "extra": "mean: 437.97 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[no-objects]",
            "value": 3.3959163320518524,
            "unit": "iter/sec",
            "range": "stddev: 0.072292",
            "group": "import-export",
            "extra": "mean: 294.47 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[with-objects]",
            "value": 3.239176813938233,
            "unit": "iter/sec",
            "range": "stddev: 0.075657",
            "group": "import-export",
            "extra": "mean: 308.72 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 2.51111526464081,
            "unit": "iter/sec",
            "range": "stddev: 0.014008",
            "group": "engine",
            "extra": "mean: 398.23 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.5623298470647357,
            "unit": "iter/sec",
            "range": "stddev: 0.091379",
            "group": "engine",
            "extra": "mean: 1.7783 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.6415951928926649,
            "unit": "iter/sec",
            "range": "stddev: 0.068641",
            "group": "engine",
            "extra": "mean: 1.5586 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.1533425467283709,
            "unit": "iter/sec",
            "range": "stddev: 0.21606",
            "group": "engine",
            "extra": "mean: 6.5213 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.17159526759440402,
            "unit": "iter/sec",
            "range": "stddev: 0.17236",
            "group": "engine",
            "extra": "mean: 5.8277 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.283840961381097,
            "unit": "iter/sec",
            "range": "stddev: 0.023224",
            "group": "engine",
            "extra": "mean: 437.86 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.49625472726248704,
            "unit": "iter/sec",
            "range": "stddev: 0.10866",
            "group": "engine",
            "extra": "mean: 2.0151 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.5400831412963875,
            "unit": "iter/sec",
            "range": "stddev: 0.039649",
            "group": "engine",
            "extra": "mean: 1.8516 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.13429217440021216,
            "unit": "iter/sec",
            "range": "stddev: 0.27967",
            "group": "engine",
            "extra": "mean: 7.4465 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.1593060628107872,
            "unit": "iter/sec",
            "range": "stddev: 0.17781",
            "group": "engine",
            "extra": "mean: 6.2772 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 294.7381604365685,
            "unit": "iter/sec",
            "range": "stddev: 0.00047770",
            "group": "node",
            "extra": "mean: 3.3928 msec\nrounds: 212"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 110.2594397849576,
            "unit": "iter/sec",
            "range": "stddev: 0.0013037",
            "group": "node",
            "extra": "mean: 9.0695 msec\nrounds: 101"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 67.75633594122179,
            "unit": "iter/sec",
            "range": "stddev: 0.0016561",
            "group": "node",
            "extra": "mean: 14.759 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 184.45186094632908,
            "unit": "iter/sec",
            "range": "stddev: 0.0010203",
            "group": "node",
            "extra": "mean: 5.4215 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 45.69536342619225,
            "unit": "iter/sec",
            "range": "stddev: 0.0027498",
            "group": "node",
            "extra": "mean: 21.884 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 43.867223164448795,
            "unit": "iter/sec",
            "range": "stddev: 0.0032300",
            "group": "node",
            "extra": "mean: 22.796 msec\nrounds: 100"
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
          "pythonVersion": "3.10.11",
          "metadata": "postgres:12.14, rabbitmq:3.8.14-management"
        },
        "commit": {
          "id": "fce1cd6d7da2b0241830cab30a83eb5ab978a16d",
          "message": "Release `v2.3.0`",
          "timestamp": "2023-04-14T21:26:04+02:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/fce1cd6d7da2b0241830cab30a83eb5ab978a16d",
          "distinct": false,
          "tree_id": "2ec60e249640107139d458d82a7f16541edc02e3"
        },
        "date": 1681724452276,
        "benches": [
          {
            "name": "tests/benchmark/test_archive.py::test_export[no-objects]",
            "value": 2.3905642378428054,
            "unit": "iter/sec",
            "range": "stddev: 0.080584",
            "group": "import-export",
            "extra": "mean: 418.31 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_export[with-objects]",
            "value": 2.19012877398161,
            "unit": "iter/sec",
            "range": "stddev: 0.075098",
            "group": "import-export",
            "extra": "mean: 456.59 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[no-objects]",
            "value": 3.3901667411896677,
            "unit": "iter/sec",
            "range": "stddev: 0.077823",
            "group": "import-export",
            "extra": "mean: 294.97 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[with-objects]",
            "value": 3.4072996703586287,
            "unit": "iter/sec",
            "range": "stddev: 0.074327",
            "group": "import-export",
            "extra": "mean: 293.49 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 2.558937735405043,
            "unit": "iter/sec",
            "range": "stddev: 0.015662",
            "group": "engine",
            "extra": "mean: 390.79 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.5643728449438457,
            "unit": "iter/sec",
            "range": "stddev: 0.069485",
            "group": "engine",
            "extra": "mean: 1.7719 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.636079855563879,
            "unit": "iter/sec",
            "range": "stddev: 0.11565",
            "group": "engine",
            "extra": "mean: 1.5721 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.14730029025248195,
            "unit": "iter/sec",
            "range": "stddev: 0.14121",
            "group": "engine",
            "extra": "mean: 6.7889 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.16551162287473198,
            "unit": "iter/sec",
            "range": "stddev: 0.16661",
            "group": "engine",
            "extra": "mean: 6.0419 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.1188561787674405,
            "unit": "iter/sec",
            "range": "stddev: 0.018643",
            "group": "engine",
            "extra": "mean: 471.95 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.46261423364498183,
            "unit": "iter/sec",
            "range": "stddev: 0.074435",
            "group": "engine",
            "extra": "mean: 2.1616 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.5309852605242086,
            "unit": "iter/sec",
            "range": "stddev: 0.088795",
            "group": "engine",
            "extra": "mean: 1.8833 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.134378657275572,
            "unit": "iter/sec",
            "range": "stddev: 0.17113",
            "group": "engine",
            "extra": "mean: 7.4417 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.1515029528990958,
            "unit": "iter/sec",
            "range": "stddev: 0.21716",
            "group": "engine",
            "extra": "mean: 6.6005 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 179.39010762368935,
            "unit": "iter/sec",
            "range": "stddev: 0.020174",
            "group": "node",
            "extra": "mean: 5.5744 msec\nrounds: 171"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 109.12317975518364,
            "unit": "iter/sec",
            "range": "stddev: 0.0019444",
            "group": "node",
            "extra": "mean: 9.1640 msec\nrounds: 110"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 62.138201448300066,
            "unit": "iter/sec",
            "range": "stddev: 0.0018776",
            "group": "node",
            "extra": "mean: 16.093 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 175.93952688199795,
            "unit": "iter/sec",
            "range": "stddev: 0.0010699",
            "group": "node",
            "extra": "mean: 5.6838 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 44.64826843326646,
            "unit": "iter/sec",
            "range": "stddev: 0.0029080",
            "group": "node",
            "extra": "mean: 22.397 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 42.92160855015156,
            "unit": "iter/sec",
            "range": "stddev: 0.0035804",
            "group": "node",
            "extra": "mean: 23.298 msec\nrounds: 100"
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
          "pythonVersion": "3.10.11",
          "metadata": "postgres:12.14, rabbitmq:3.8.14-management"
        },
        "commit": {
          "id": "978217693af987f015b51dc1c422a2e71bd39f4f",
          "message": "Docs: Correct \"variable\" to \"variadic\" arguments (#5975)\n\nCo-authored-by: Sebastiaan Huber <mail@sphuber.net>",
          "timestamp": "2023-04-20T16:31:55+02:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/978217693af987f015b51dc1c422a2e71bd39f4f",
          "distinct": true,
          "tree_id": "cdd10fa8a59c959e4faf76638ef44e0c8a2f7cad"
        },
        "date": 1682666535692,
        "benches": [
          {
            "name": "tests/benchmark/test_archive.py::test_export[no-objects]",
            "value": 2.815267189464062,
            "unit": "iter/sec",
            "range": "stddev: 0.073796",
            "group": "import-export",
            "extra": "mean: 355.21 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_export[with-objects]",
            "value": 2.8256797001623957,
            "unit": "iter/sec",
            "range": "stddev: 0.011942",
            "group": "import-export",
            "extra": "mean: 353.90 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[no-objects]",
            "value": 3.79752311567503,
            "unit": "iter/sec",
            "range": "stddev: 0.014033",
            "group": "import-export",
            "extra": "mean: 263.33 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[with-objects]",
            "value": 3.3294165041759727,
            "unit": "iter/sec",
            "range": "stddev: 0.095114",
            "group": "import-export",
            "extra": "mean: 300.35 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 2.951696422552018,
            "unit": "iter/sec",
            "range": "stddev: 0.011323",
            "group": "engine",
            "extra": "mean: 338.79 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.6723265260141065,
            "unit": "iter/sec",
            "range": "stddev: 0.079943",
            "group": "engine",
            "extra": "mean: 1.4874 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.7992354904603924,
            "unit": "iter/sec",
            "range": "stddev: 0.067590",
            "group": "engine",
            "extra": "mean: 1.2512 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.1761043458307857,
            "unit": "iter/sec",
            "range": "stddev: 0.072111",
            "group": "engine",
            "extra": "mean: 5.6785 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.1968917815547754,
            "unit": "iter/sec",
            "range": "stddev: 0.27723",
            "group": "engine",
            "extra": "mean: 5.0789 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.290794231619234,
            "unit": "iter/sec",
            "range": "stddev: 0.035676",
            "group": "engine",
            "extra": "mean: 436.53 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.5747425093138478,
            "unit": "iter/sec",
            "range": "stddev: 0.093977",
            "group": "engine",
            "extra": "mean: 1.7399 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.6699131053232453,
            "unit": "iter/sec",
            "range": "stddev: 0.066255",
            "group": "engine",
            "extra": "mean: 1.4927 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.15460093973264777,
            "unit": "iter/sec",
            "range": "stddev: 0.19354",
            "group": "engine",
            "extra": "mean: 6.4683 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.17157352459335304,
            "unit": "iter/sec",
            "range": "stddev: 0.26680",
            "group": "engine",
            "extra": "mean: 5.8284 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 288.15155037134514,
            "unit": "iter/sec",
            "range": "stddev: 0.00027451",
            "group": "node",
            "extra": "mean: 3.4704 msec\nrounds: 189"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 111.43040753963692,
            "unit": "iter/sec",
            "range": "stddev: 0.00069396",
            "group": "node",
            "extra": "mean: 8.9742 msec\nrounds: 102"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 67.97829837149165,
            "unit": "iter/sec",
            "range": "stddev: 0.0013514",
            "group": "node",
            "extra": "mean: 14.711 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 190.16835102090664,
            "unit": "iter/sec",
            "range": "stddev: 0.00038718",
            "group": "node",
            "extra": "mean: 5.2585 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 46.77509250983242,
            "unit": "iter/sec",
            "range": "stddev: 0.022960",
            "group": "node",
            "extra": "mean: 21.379 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 52.21278432637472,
            "unit": "iter/sec",
            "range": "stddev: 0.0021984",
            "group": "node",
            "extra": "mean: 19.152 msec\nrounds: 100"
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
          "pythonVersion": "3.10.11",
          "metadata": "postgres:12.14, rabbitmq:3.8.14-management"
        },
        "commit": {
          "id": "5e92f5ef9ed7fdedeb890365809d1748052bff86",
          "message": "Dependencies: pre-commit autoupdate (#5993)\n\n- https://github.com/ikamensh/flynt/: 0.77 → 0.78\r\n- [github.com/google/yapf: v0.32.0 → v0.33.0](https://github.com/google/yapf/compare/v0.32.0...v0.33.0)",
          "timestamp": "2023-05-02T12:07:26+02:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/5e92f5ef9ed7fdedeb890365809d1748052bff86",
          "distinct": true,
          "tree_id": "839828c43c26d9796131871b3ff6872232a384d4"
        },
        "date": 1683022593496,
        "benches": [
          {
            "name": "tests/benchmark/test_archive.py::test_export[no-objects]",
            "value": 3.400353608722377,
            "unit": "iter/sec",
            "range": "stddev: 0.065232",
            "group": "import-export",
            "extra": "mean: 294.09 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_export[with-objects]",
            "value": 3.618143818609969,
            "unit": "iter/sec",
            "range": "stddev: 0.0048717",
            "group": "import-export",
            "extra": "mean: 276.38 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[no-objects]",
            "value": 4.802596840953564,
            "unit": "iter/sec",
            "range": "stddev: 0.0036293",
            "group": "import-export",
            "extra": "mean: 208.22 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[with-objects]",
            "value": 4.067465219300767,
            "unit": "iter/sec",
            "range": "stddev: 0.079895",
            "group": "import-export",
            "extra": "mean: 245.85 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.572385612258341,
            "unit": "iter/sec",
            "range": "stddev: 0.0087513",
            "group": "engine",
            "extra": "mean: 279.92 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.7903453284944342,
            "unit": "iter/sec",
            "range": "stddev: 0.073873",
            "group": "engine",
            "extra": "mean: 1.2653 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.8940206732464314,
            "unit": "iter/sec",
            "range": "stddev: 0.057107",
            "group": "engine",
            "extra": "mean: 1.1185 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.20036082836117583,
            "unit": "iter/sec",
            "range": "stddev: 0.10051",
            "group": "engine",
            "extra": "mean: 4.9910 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.22843767636954163,
            "unit": "iter/sec",
            "range": "stddev: 0.095657",
            "group": "engine",
            "extra": "mean: 4.3776 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.683814117591402,
            "unit": "iter/sec",
            "range": "stddev: 0.074177",
            "group": "engine",
            "extra": "mean: 372.60 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.6390367733482456,
            "unit": "iter/sec",
            "range": "stddev: 0.074140",
            "group": "engine",
            "extra": "mean: 1.5649 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.7312603564747916,
            "unit": "iter/sec",
            "range": "stddev: 0.055517",
            "group": "engine",
            "extra": "mean: 1.3675 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.17779826674429963,
            "unit": "iter/sec",
            "range": "stddev: 0.065231",
            "group": "engine",
            "extra": "mean: 5.6244 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.19714326020861841,
            "unit": "iter/sec",
            "range": "stddev: 0.13109",
            "group": "engine",
            "extra": "mean: 5.0725 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 341.6847220490638,
            "unit": "iter/sec",
            "range": "stddev: 0.00027218",
            "group": "node",
            "extra": "mean: 2.9267 msec\nrounds: 222"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 139.3310193329009,
            "unit": "iter/sec",
            "range": "stddev: 0.00015941",
            "group": "node",
            "extra": "mean: 7.1772 msec\nrounds: 122"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 85.70337209996418,
            "unit": "iter/sec",
            "range": "stddev: 0.00062835",
            "group": "node",
            "extra": "mean: 11.668 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 231.33110234243085,
            "unit": "iter/sec",
            "range": "stddev: 0.00053976",
            "group": "node",
            "extra": "mean: 4.3228 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 53.18233467343846,
            "unit": "iter/sec",
            "range": "stddev: 0.021198",
            "group": "node",
            "extra": "mean: 18.803 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 59.3795166268565,
            "unit": "iter/sec",
            "range": "stddev: 0.0014561",
            "group": "node",
            "extra": "mean: 16.841 msec\nrounds: 100"
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
          "pythonVersion": "3.10.11",
          "metadata": "postgres:12.14, rabbitmq:3.8.14-management"
        },
        "commit": {
          "id": "9e5f5eefd0cd6be44f0be76efae157dcf6e160ed",
          "message": "DevOps: Fix the `daemon_client` fixture (#5988)\n\nThe logic of the `DaemonClient` was changed in `aiida-core==2.3` such\r\nthat the timeout of the `stop_daemon` call is different from what is\r\nused by the `is_daemon_running` property. This can lead to the stop call\r\ngoing through just fine but `is_daemon_running` still returning `True`\r\nstraight after. This usually resolves after a while but this false\r\npositive can cause the tests to fail when the session is closing. The\r\n`stopped_daemon_client` was already fixed by adding a manual grace\r\nperiod for `is_daemon_running` to start returning `False`. Here the\r\nsame fix is added for `daemon_client`.",
          "timestamp": "2023-05-02T22:12:52+02:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/9e5f5eefd0cd6be44f0be76efae157dcf6e160ed",
          "distinct": true,
          "tree_id": "5de70fff8f25f151089ff93f34be4f3807a54b8e"
        },
        "date": 1683059105271,
        "benches": [
          {
            "name": "tests/benchmark/test_archive.py::test_export[no-objects]",
            "value": 2.4486717623133023,
            "unit": "iter/sec",
            "range": "stddev: 0.093571",
            "group": "import-export",
            "extra": "mean: 408.38 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_export[with-objects]",
            "value": 2.416701091398932,
            "unit": "iter/sec",
            "range": "stddev: 0.061976",
            "group": "import-export",
            "extra": "mean: 413.79 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[no-objects]",
            "value": 3.884621662027288,
            "unit": "iter/sec",
            "range": "stddev: 0.011448",
            "group": "import-export",
            "extra": "mean: 257.43 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[with-objects]",
            "value": 3.590406080579681,
            "unit": "iter/sec",
            "range": "stddev: 0.068185",
            "group": "import-export",
            "extra": "mean: 278.52 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 2.661135660123016,
            "unit": "iter/sec",
            "range": "stddev: 0.020691",
            "group": "engine",
            "extra": "mean: 375.78 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.560792641416826,
            "unit": "iter/sec",
            "range": "stddev: 0.12265",
            "group": "engine",
            "extra": "mean: 1.7832 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.5926771005150097,
            "unit": "iter/sec",
            "range": "stddev: 0.10296",
            "group": "engine",
            "extra": "mean: 1.6873 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.14421835404676905,
            "unit": "iter/sec",
            "range": "stddev: 0.36378",
            "group": "engine",
            "extra": "mean: 6.9339 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.16293702560443096,
            "unit": "iter/sec",
            "range": "stddev: 0.18923",
            "group": "engine",
            "extra": "mean: 6.1373 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.1461609006375943,
            "unit": "iter/sec",
            "range": "stddev: 0.020698",
            "group": "engine",
            "extra": "mean: 465.95 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.45508197927824595,
            "unit": "iter/sec",
            "range": "stddev: 0.091016",
            "group": "engine",
            "extra": "mean: 2.1974 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.5240168569729273,
            "unit": "iter/sec",
            "range": "stddev: 0.10291",
            "group": "engine",
            "extra": "mean: 1.9083 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.13488082248803238,
            "unit": "iter/sec",
            "range": "stddev: 0.21439",
            "group": "engine",
            "extra": "mean: 7.4140 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.15103569741943695,
            "unit": "iter/sec",
            "range": "stddev: 0.28078",
            "group": "engine",
            "extra": "mean: 6.6210 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 296.4106271322304,
            "unit": "iter/sec",
            "range": "stddev: 0.00056418",
            "group": "node",
            "extra": "mean: 3.3737 msec\nrounds: 227"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 105.97997891740908,
            "unit": "iter/sec",
            "range": "stddev: 0.0011853",
            "group": "node",
            "extra": "mean: 9.4357 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 61.038530506474906,
            "unit": "iter/sec",
            "range": "stddev: 0.0024433",
            "group": "node",
            "extra": "mean: 16.383 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 175.2421420563202,
            "unit": "iter/sec",
            "range": "stddev: 0.00077770",
            "group": "node",
            "extra": "mean: 5.7064 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 40.74145129278153,
            "unit": "iter/sec",
            "range": "stddev: 0.0030314",
            "group": "node",
            "extra": "mean: 24.545 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 40.735905954490015,
            "unit": "iter/sec",
            "range": "stddev: 0.0028190",
            "group": "node",
            "extra": "mean: 24.548 msec\nrounds: 100"
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
          "pythonVersion": "3.10.11",
          "metadata": "postgres:12.14, rabbitmq:3.8.14-management"
        },
        "commit": {
          "id": "777b976013d0041e059f86c1ac0d2f43b52884df",
          "message": "`CalcJob`: Assign outputs from node in case of cache hit (#5995)\n\nIf a `CalcJob` is launched and a cache hit occurs, the outputs of the\r\ncache source are attached automatically to the process node of the\r\n`CalcJob` instance in `Node.store`. The process execution itself,\r\nshortcuts in `CalcJob.run` to directly return the exit status instead of\r\ngoing to the upload stage.\r\n\r\nThis shortcut, however, also means that the `Parser` won't be called\r\nwhich normally is responsible for adding the outputs; to the process\r\n*node* but also to the *process* itself. By circumventing this, the\r\noutputs mapping on the process instance will be empty. This is a problem\r\nif the process was run as opposed to submitted. In this case, the\r\n`Runner.run` method will return the results by taking it from the\r\n`Process.outputs` method, but this will be empty.\r\n\r\nUltimately, this means that when a user *runs* a `CalcJob` that hits the\r\ncache, the returned `results` dictionary will always be empty. To fix\r\nit, the `CalcJob.run` method is updated to populate the `_outputs`\r\nattribute of the process instance with the outputs that are stored on\r\nthe associated process node. Now the run method will return the correct\r\nresults dictionary.",
          "timestamp": "2023-05-05T18:06:15+02:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/777b976013d0041e059f86c1ac0d2f43b52884df",
          "distinct": true,
          "tree_id": "553d99f40aa46982342d26aa2dbdc05ddcbf864d"
        },
        "date": 1683303445305,
        "benches": [
          {
            "name": "tests/benchmark/test_archive.py::test_export[no-objects]",
            "value": 2.649218166973279,
            "unit": "iter/sec",
            "range": "stddev: 0.075722",
            "group": "import-export",
            "extra": "mean: 377.47 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_export[with-objects]",
            "value": 2.573934357012596,
            "unit": "iter/sec",
            "range": "stddev: 0.070781",
            "group": "import-export",
            "extra": "mean: 388.51 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[no-objects]",
            "value": 3.5470520799105736,
            "unit": "iter/sec",
            "range": "stddev: 0.070243",
            "group": "import-export",
            "extra": "mean: 281.92 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[with-objects]",
            "value": 3.581525762351816,
            "unit": "iter/sec",
            "range": "stddev: 0.072920",
            "group": "import-export",
            "extra": "mean: 279.21 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 2.8119609941778383,
            "unit": "iter/sec",
            "range": "stddev: 0.016248",
            "group": "engine",
            "extra": "mean: 355.62 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.6351675661722034,
            "unit": "iter/sec",
            "range": "stddev: 0.095568",
            "group": "engine",
            "extra": "mean: 1.5744 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.7273892546081107,
            "unit": "iter/sec",
            "range": "stddev: 0.092599",
            "group": "engine",
            "extra": "mean: 1.3748 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.15831399572164004,
            "unit": "iter/sec",
            "range": "stddev: 0.14017",
            "group": "engine",
            "extra": "mean: 6.3166 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.1768655653699124,
            "unit": "iter/sec",
            "range": "stddev: 0.12606",
            "group": "engine",
            "extra": "mean: 5.6540 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.2177024721390746,
            "unit": "iter/sec",
            "range": "stddev: 0.078547",
            "group": "engine",
            "extra": "mean: 450.92 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.5300977499694376,
            "unit": "iter/sec",
            "range": "stddev: 0.076439",
            "group": "engine",
            "extra": "mean: 1.8864 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.58870108400768,
            "unit": "iter/sec",
            "range": "stddev: 0.057853",
            "group": "engine",
            "extra": "mean: 1.6987 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.14467274147209136,
            "unit": "iter/sec",
            "range": "stddev: 0.095642",
            "group": "engine",
            "extra": "mean: 6.9122 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.16619038591630209,
            "unit": "iter/sec",
            "range": "stddev: 0.15214",
            "group": "engine",
            "extra": "mean: 6.0172 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 296.0179978441812,
            "unit": "iter/sec",
            "range": "stddev: 0.00024394",
            "group": "node",
            "extra": "mean: 3.3782 msec\nrounds: 189"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 115.27994409279727,
            "unit": "iter/sec",
            "range": "stddev: 0.00029756",
            "group": "node",
            "extra": "mean: 8.6745 msec\nrounds: 101"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 60.866858457630734,
            "unit": "iter/sec",
            "range": "stddev: 0.0025153",
            "group": "node",
            "extra": "mean: 16.429 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 176.35717666934872,
            "unit": "iter/sec",
            "range": "stddev: 0.00044962",
            "group": "node",
            "extra": "mean: 5.6703 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 38.22313016970922,
            "unit": "iter/sec",
            "range": "stddev: 0.040540",
            "group": "node",
            "extra": "mean: 26.162 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 46.00882315802572,
            "unit": "iter/sec",
            "range": "stddev: 0.0026300",
            "group": "node",
            "extra": "mean: 21.735 msec\nrounds: 100"
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
          "pythonVersion": "3.10.11",
          "metadata": "postgres:12.14, rabbitmq:3.8.14-management"
        },
        "commit": {
          "id": "5df446cd3558b1b7ee11d9b60d75287d6395a693",
          "message": "Docs: Bump Python version for RTD build (#5999)\n\nThe readthedocs (RTD) build was failing with the following error:\r\n\r\n    read the docs ImportError: urllib3 v2.0 only supports OpenSSL 1.1.1\r\n\r\nThis was due to a change in the support for `urllib`, see:\r\n\r\nhttps://github.com/urllib3/urllib3/issues/2168\r\n\r\nWhich requires Python > 3.8. Hence here we update the Python version.",
          "timestamp": "2023-05-05T21:49:37+02:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/5df446cd3558b1b7ee11d9b60d75287d6395a693",
          "distinct": true,
          "tree_id": "9c3630284663317a4ea3f440f153d7244ffde7fc"
        },
        "date": 1683316746769,
        "benches": [
          {
            "name": "tests/benchmark/test_archive.py::test_export[no-objects]",
            "value": 3.255741968907189,
            "unit": "iter/sec",
            "range": "stddev: 0.071394",
            "group": "import-export",
            "extra": "mean: 307.15 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_export[with-objects]",
            "value": 3.265291967519348,
            "unit": "iter/sec",
            "range": "stddev: 0.060679",
            "group": "import-export",
            "extra": "mean: 306.25 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[no-objects]",
            "value": 4.265826087342503,
            "unit": "iter/sec",
            "range": "stddev: 0.065822",
            "group": "import-export",
            "extra": "mean: 234.42 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[with-objects]",
            "value": 4.2101693776297395,
            "unit": "iter/sec",
            "range": "stddev: 0.064220",
            "group": "import-export",
            "extra": "mean: 237.52 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.397460374112474,
            "unit": "iter/sec",
            "range": "stddev: 0.0053399",
            "group": "engine",
            "extra": "mean: 294.34 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.7394104060260408,
            "unit": "iter/sec",
            "range": "stddev: 0.061462",
            "group": "engine",
            "extra": "mean: 1.3524 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.8370232266975468,
            "unit": "iter/sec",
            "range": "stddev: 0.071180",
            "group": "engine",
            "extra": "mean: 1.1947 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.1889975963075155,
            "unit": "iter/sec",
            "range": "stddev: 0.10550",
            "group": "engine",
            "extra": "mean: 5.2911 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.21250800083458685,
            "unit": "iter/sec",
            "range": "stddev: 0.13402",
            "group": "engine",
            "extra": "mean: 4.7057 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.7126900407525305,
            "unit": "iter/sec",
            "range": "stddev: 0.018346",
            "group": "engine",
            "extra": "mean: 368.64 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.5896967127711102,
            "unit": "iter/sec",
            "range": "stddev: 0.058999",
            "group": "engine",
            "extra": "mean: 1.6958 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.6872759027727982,
            "unit": "iter/sec",
            "range": "stddev: 0.040478",
            "group": "engine",
            "extra": "mean: 1.4550 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.1647696877730375,
            "unit": "iter/sec",
            "range": "stddev: 0.13558",
            "group": "engine",
            "extra": "mean: 6.0691 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.18726863257383303,
            "unit": "iter/sec",
            "range": "stddev: 0.095230",
            "group": "engine",
            "extra": "mean: 5.3399 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 312.1476563321716,
            "unit": "iter/sec",
            "range": "stddev: 0.00018903",
            "group": "node",
            "extra": "mean: 3.2036 msec\nrounds: 209"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 115.86184208841989,
            "unit": "iter/sec",
            "range": "stddev: 0.00042916",
            "group": "node",
            "extra": "mean: 8.6310 msec\nrounds: 110"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 67.31108613264506,
            "unit": "iter/sec",
            "range": "stddev: 0.0013673",
            "group": "node",
            "extra": "mean: 14.856 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 200.75877098706488,
            "unit": "iter/sec",
            "range": "stddev: 0.00031780",
            "group": "node",
            "extra": "mean: 4.9811 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 48.650576573702715,
            "unit": "iter/sec",
            "range": "stddev: 0.023981",
            "group": "node",
            "extra": "mean: 20.555 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 54.22290382483606,
            "unit": "iter/sec",
            "range": "stddev: 0.0020384",
            "group": "node",
            "extra": "mean: 18.442 msec\nrounds: 100"
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
          "pythonVersion": "3.10.11",
          "metadata": "postgres:12.14, rabbitmq:3.8.14-management"
        },
        "commit": {
          "id": "ad8a539ee2b481d526607b5924789fbbd1e14102",
          "message": "`ProcessNode`: Add the `exit_code` property (#5973)\n\nThis is a convenience property that returns an `ExitCode` from a process\r\nnode as long as both the `exit_status` and `exit_message` attributes\r\nhave been defined.",
          "timestamp": "2023-05-06T15:05:00+02:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/ad8a539ee2b481d526607b5924789fbbd1e14102",
          "distinct": true,
          "tree_id": "41d79171673c01ae85585c73f9d96259079160a9"
        },
        "date": 1683378929778,
        "benches": [
          {
            "name": "tests/benchmark/test_archive.py::test_export[no-objects]",
            "value": 2.8515214851425155,
            "unit": "iter/sec",
            "range": "stddev: 0.069090",
            "group": "import-export",
            "extra": "mean: 350.69 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_export[with-objects]",
            "value": 2.746808688023202,
            "unit": "iter/sec",
            "range": "stddev: 0.052453",
            "group": "import-export",
            "extra": "mean: 364.06 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[no-objects]",
            "value": 3.963460300640501,
            "unit": "iter/sec",
            "range": "stddev: 0.068577",
            "group": "import-export",
            "extra": "mean: 252.30 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[with-objects]",
            "value": 3.8289836880065184,
            "unit": "iter/sec",
            "range": "stddev: 0.064902",
            "group": "import-export",
            "extra": "mean: 261.17 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.037848010050638,
            "unit": "iter/sec",
            "range": "stddev: 0.024102",
            "group": "engine",
            "extra": "mean: 329.18 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.6639149615184261,
            "unit": "iter/sec",
            "range": "stddev: 0.070322",
            "group": "engine",
            "extra": "mean: 1.5062 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.7141189892313463,
            "unit": "iter/sec",
            "range": "stddev: 0.12574",
            "group": "engine",
            "extra": "mean: 1.4003 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.1723580432168246,
            "unit": "iter/sec",
            "range": "stddev: 0.15117",
            "group": "engine",
            "extra": "mean: 5.8019 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.19374063799175328,
            "unit": "iter/sec",
            "range": "stddev: 0.13991",
            "group": "engine",
            "extra": "mean: 5.1615 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.3289303804459407,
            "unit": "iter/sec",
            "range": "stddev: 0.076569",
            "group": "engine",
            "extra": "mean: 429.38 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.553034347944058,
            "unit": "iter/sec",
            "range": "stddev: 0.083225",
            "group": "engine",
            "extra": "mean: 1.8082 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.6267672535530979,
            "unit": "iter/sec",
            "range": "stddev: 0.079650",
            "group": "engine",
            "extra": "mean: 1.5955 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.15607433647359958,
            "unit": "iter/sec",
            "range": "stddev: 0.18461",
            "group": "engine",
            "extra": "mean: 6.4072 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.17691408860370908,
            "unit": "iter/sec",
            "range": "stddev: 0.15530",
            "group": "engine",
            "extra": "mean: 5.6525 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 284.0770367006166,
            "unit": "iter/sec",
            "range": "stddev: 0.00074098",
            "group": "node",
            "extra": "mean: 3.5202 msec\nrounds: 168"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 106.71224708132333,
            "unit": "iter/sec",
            "range": "stddev: 0.0014147",
            "group": "node",
            "extra": "mean: 9.3710 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 72.76901663397297,
            "unit": "iter/sec",
            "range": "stddev: 0.0011448",
            "group": "node",
            "extra": "mean: 13.742 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 175.76070202885484,
            "unit": "iter/sec",
            "range": "stddev: 0.00060556",
            "group": "node",
            "extra": "mean: 5.6896 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 45.788926499793874,
            "unit": "iter/sec",
            "range": "stddev: 0.020565",
            "group": "node",
            "extra": "mean: 21.839 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 47.53045623541703,
            "unit": "iter/sec",
            "range": "stddev: 0.0028774",
            "group": "node",
            "extra": "mean: 21.039 msec\nrounds: 100"
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
          "id": "68be866e653c610e9b957a3fdedc1b77e6e41a05",
          "message": "`verdi process list`: Fix double percent sign in daemon usage (#6002)",
          "timestamp": "2023-05-08T09:41:00+02:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/68be866e653c610e9b957a3fdedc1b77e6e41a05",
          "distinct": true,
          "tree_id": "269653b9c327e2fad3027d3724432dcf2aa80795"
        },
        "date": 1683532187214,
        "benches": [
          {
            "name": "tests/benchmark/test_archive.py::test_export[no-objects]",
            "value": 3.6484644153703965,
            "unit": "iter/sec",
            "range": "stddev: 0.045611",
            "group": "import-export",
            "extra": "mean: 274.09 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_export[with-objects]",
            "value": 3.612423464585107,
            "unit": "iter/sec",
            "range": "stddev: 0.044147",
            "group": "import-export",
            "extra": "mean: 276.82 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[no-objects]",
            "value": 4.515223783052754,
            "unit": "iter/sec",
            "range": "stddev: 0.048043",
            "group": "import-export",
            "extra": "mean: 221.47 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[with-objects]",
            "value": 4.427814643518592,
            "unit": "iter/sec",
            "range": "stddev: 0.047668",
            "group": "import-export",
            "extra": "mean: 225.85 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.8764574228783673,
            "unit": "iter/sec",
            "range": "stddev: 0.0028961",
            "group": "engine",
            "extra": "mean: 257.97 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.8436069383514855,
            "unit": "iter/sec",
            "range": "stddev: 0.072484",
            "group": "engine",
            "extra": "mean: 1.1854 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.9522629682688569,
            "unit": "iter/sec",
            "range": "stddev: 0.062617",
            "group": "engine",
            "extra": "mean: 1.0501 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.2148770443775484,
            "unit": "iter/sec",
            "range": "stddev: 0.083649",
            "group": "engine",
            "extra": "mean: 4.6538 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.24060979835850713,
            "unit": "iter/sec",
            "range": "stddev: 0.13231",
            "group": "engine",
            "extra": "mean: 4.1561 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 3.0133399734972026,
            "unit": "iter/sec",
            "range": "stddev: 0.020752",
            "group": "engine",
            "extra": "mean: 331.86 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.6609181618907547,
            "unit": "iter/sec",
            "range": "stddev: 0.042147",
            "group": "engine",
            "extra": "mean: 1.5130 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.7536956802544916,
            "unit": "iter/sec",
            "range": "stddev: 0.079127",
            "group": "engine",
            "extra": "mean: 1.3268 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.17806309185961638,
            "unit": "iter/sec",
            "range": "stddev: 0.16955",
            "group": "engine",
            "extra": "mean: 5.6160 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.20356921083210094,
            "unit": "iter/sec",
            "range": "stddev: 0.10003",
            "group": "engine",
            "extra": "mean: 4.9123 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 307.065190634034,
            "unit": "iter/sec",
            "range": "stddev: 0.0013217",
            "group": "node",
            "extra": "mean: 3.2566 msec\nrounds: 104"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 140.745966231706,
            "unit": "iter/sec",
            "range": "stddev: 0.00019842",
            "group": "node",
            "extra": "mean: 7.1050 msec\nrounds: 125"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 84.89109360234698,
            "unit": "iter/sec",
            "range": "stddev: 0.00092357",
            "group": "node",
            "extra": "mean: 11.780 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 241.24130675831117,
            "unit": "iter/sec",
            "range": "stddev: 0.00015245",
            "group": "node",
            "extra": "mean: 4.1452 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 58.518510830474526,
            "unit": "iter/sec",
            "range": "stddev: 0.016413",
            "group": "node",
            "extra": "mean: 17.089 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 63.13826742881911,
            "unit": "iter/sec",
            "range": "stddev: 0.0013486",
            "group": "node",
            "extra": "mean: 15.838 msec\nrounds: 100"
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
          "id": "3df02550eff02cd625d0e14eb35e6d6b01b4b12d",
          "message": "Docs: Add `graphviz` to system requirements of RTD build runner (#6004)\n\nThe `graphviz` package provides the `dot` executable which is needed to\r\ngenerate provenance graph. Without this, the tutorials that produce\r\nprovenance graph representations will raise an exception.",
          "timestamp": "2023-05-09T15:19:10+02:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/3df02550eff02cd625d0e14eb35e6d6b01b4b12d",
          "distinct": true,
          "tree_id": "1cbee0948f722589e700a696ea212ea0cb9f6f0d"
        },
        "date": 1683638919064,
        "benches": [
          {
            "name": "tests/benchmark/test_archive.py::test_export[no-objects]",
            "value": 3.496613305647567,
            "unit": "iter/sec",
            "range": "stddev: 0.055324",
            "group": "import-export",
            "extra": "mean: 285.99 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_export[with-objects]",
            "value": 3.457835642894908,
            "unit": "iter/sec",
            "range": "stddev: 0.050356",
            "group": "import-export",
            "extra": "mean: 289.20 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[no-objects]",
            "value": 4.251221462899324,
            "unit": "iter/sec",
            "range": "stddev: 0.053411",
            "group": "import-export",
            "extra": "mean: 235.23 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[with-objects]",
            "value": 4.215623551955083,
            "unit": "iter/sec",
            "range": "stddev: 0.054144",
            "group": "import-export",
            "extra": "mean: 237.21 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.502495705766756,
            "unit": "iter/sec",
            "range": "stddev: 0.0032543",
            "group": "engine",
            "extra": "mean: 285.51 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.7782499220650001,
            "unit": "iter/sec",
            "range": "stddev: 0.052937",
            "group": "engine",
            "extra": "mean: 1.2849 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.8930112602553728,
            "unit": "iter/sec",
            "range": "stddev: 0.047665",
            "group": "engine",
            "extra": "mean: 1.1198 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.20035888908531288,
            "unit": "iter/sec",
            "range": "stddev: 0.071325",
            "group": "engine",
            "extra": "mean: 4.9910 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.22643571075567814,
            "unit": "iter/sec",
            "range": "stddev: 0.12099",
            "group": "engine",
            "extra": "mean: 4.4163 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.8537985810917865,
            "unit": "iter/sec",
            "range": "stddev: 0.017587",
            "group": "engine",
            "extra": "mean: 350.41 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.5926876928890398,
            "unit": "iter/sec",
            "range": "stddev: 0.095272",
            "group": "engine",
            "extra": "mean: 1.6872 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.6793462310540056,
            "unit": "iter/sec",
            "range": "stddev: 0.042802",
            "group": "engine",
            "extra": "mean: 1.4720 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.16774821391553651,
            "unit": "iter/sec",
            "range": "stddev: 0.19566",
            "group": "engine",
            "extra": "mean: 5.9613 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.19095695605001772,
            "unit": "iter/sec",
            "range": "stddev: 0.18328",
            "group": "engine",
            "extra": "mean: 5.2368 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 340.25249097440343,
            "unit": "iter/sec",
            "range": "stddev: 0.00049399",
            "group": "node",
            "extra": "mean: 2.9390 msec\nrounds: 231"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 128.99525597308147,
            "unit": "iter/sec",
            "range": "stddev: 0.00046455",
            "group": "node",
            "extra": "mean: 7.7522 msec\nrounds: 119"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 75.95919222742333,
            "unit": "iter/sec",
            "range": "stddev: 0.00084150",
            "group": "node",
            "extra": "mean: 13.165 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 218.654554895163,
            "unit": "iter/sec",
            "range": "stddev: 0.00025285",
            "group": "node",
            "extra": "mean: 4.5734 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 52.54153343329866,
            "unit": "iter/sec",
            "range": "stddev: 0.019099",
            "group": "node",
            "extra": "mean: 19.033 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 56.52242476218938,
            "unit": "iter/sec",
            "range": "stddev: 0.0017167",
            "group": "node",
            "extra": "mean: 17.692 msec\nrounds: 100"
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
          "pythonVersion": "3.10.11",
          "metadata": "postgres:12.14, rabbitmq:3.8.14-management"
        },
        "commit": {
          "id": "685e0f87d7c571df24aea8f0ce21c6c45dfbd8a0",
          "message": "`CalcJobNode`: Fix the computation of the hash (#5998)\n\nThe `CalcJobNode.get_hash()` was returning a different hash once the\r\ncalculation had been completed, compared to the one stored in the\r\n`_aiida_hash` extra, which was computed when the node initially got\r\nstored.\r\n\r\nThe reason is that upon storing, the repository of the `CalcJobNode` is\r\nempty, however, once the upload step has been completed, the input files\r\ngenerated by the `CalcJob` plugin will have been written to the\r\nrepository, and so now its hash, and with it the hash of the entire node\r\nwill be different.\r\n\r\nThe solution is to exclude the repository hash from the objects that\r\nare used to compute the node's hash. This is acceptable, since the\r\nrepository files are just a derivative of the input nodes, which are\r\nalready captured in the hash. This solution was actually already in\r\nplace and implemented by the `CalcJobNodeCaching`, however, it was never\r\nactually used. Since there was no test, this went by unnoticed since\r\nv2.0 at which point this code was introduced.\r\n\r\nThe solution is simply just to set `CalcJobNode._CLS_NODE_CACHING` to\r\nthe `CalcJobNodeCaching` subclass. A regression test is added to check\r\nthat the `get_hash` method matches the `_aiida_hash` extra.",
          "timestamp": "2023-05-09T15:52:32+02:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/685e0f87d7c571df24aea8f0ce21c6c45dfbd8a0",
          "distinct": true,
          "tree_id": "cb809e3b9321f20c8d18d22b4cf9f51ce750db76"
        },
        "date": 1683640913065,
        "benches": [
          {
            "name": "tests/benchmark/test_archive.py::test_export[no-objects]",
            "value": 3.179016864429121,
            "unit": "iter/sec",
            "range": "stddev: 0.077947",
            "group": "import-export",
            "extra": "mean: 314.56 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_export[with-objects]",
            "value": 3.231505917670395,
            "unit": "iter/sec",
            "range": "stddev: 0.062694",
            "group": "import-export",
            "extra": "mean: 309.45 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[no-objects]",
            "value": 4.297691565314619,
            "unit": "iter/sec",
            "range": "stddev: 0.062000",
            "group": "import-export",
            "extra": "mean: 232.68 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[with-objects]",
            "value": 4.21473632421463,
            "unit": "iter/sec",
            "range": "stddev: 0.063915",
            "group": "import-export",
            "extra": "mean: 237.26 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.404108967378436,
            "unit": "iter/sec",
            "range": "stddev: 0.0039662",
            "group": "engine",
            "extra": "mean: 293.76 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.7560661138365946,
            "unit": "iter/sec",
            "range": "stddev: 0.041127",
            "group": "engine",
            "extra": "mean: 1.3226 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.8613418104396229,
            "unit": "iter/sec",
            "range": "stddev: 0.078537",
            "group": "engine",
            "extra": "mean: 1.1610 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.19440893094743064,
            "unit": "iter/sec",
            "range": "stddev: 0.15059",
            "group": "engine",
            "extra": "mean: 5.1438 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.21880874275511247,
            "unit": "iter/sec",
            "range": "stddev: 0.15169",
            "group": "engine",
            "extra": "mean: 4.5702 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.7460180319294345,
            "unit": "iter/sec",
            "range": "stddev: 0.037230",
            "group": "engine",
            "extra": "mean: 364.16 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.6104565194399617,
            "unit": "iter/sec",
            "range": "stddev: 0.091634",
            "group": "engine",
            "extra": "mean: 1.6381 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.7071320209739833,
            "unit": "iter/sec",
            "range": "stddev: 0.033695",
            "group": "engine",
            "extra": "mean: 1.4142 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.16960180002829847,
            "unit": "iter/sec",
            "range": "stddev: 0.10679",
            "group": "engine",
            "extra": "mean: 5.8962 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.19121053711165314,
            "unit": "iter/sec",
            "range": "stddev: 0.19302",
            "group": "engine",
            "extra": "mean: 5.2298 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 382.04250658781325,
            "unit": "iter/sec",
            "range": "stddev: 0.00050033",
            "group": "node",
            "extra": "mean: 2.6175 msec\nrounds: 244"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 151.17171042769138,
            "unit": "iter/sec",
            "range": "stddev: 0.00022203",
            "group": "node",
            "extra": "mean: 6.6150 msec\nrounds: 135"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 85.95480880716117,
            "unit": "iter/sec",
            "range": "stddev: 0.00074901",
            "group": "node",
            "extra": "mean: 11.634 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 248.42610880875125,
            "unit": "iter/sec",
            "range": "stddev: 0.00017292",
            "group": "node",
            "extra": "mean: 4.0253 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 58.073696396503955,
            "unit": "iter/sec",
            "range": "stddev: 0.0014729",
            "group": "node",
            "extra": "mean: 17.219 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 55.6111010045381,
            "unit": "iter/sec",
            "range": "stddev: 0.0017985",
            "group": "node",
            "extra": "mean: 17.982 msec\nrounds: 100"
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
          "pythonVersion": "3.10.11",
          "metadata": "postgres:12.14, rabbitmq:3.8.14-management"
        },
        "commit": {
          "id": "f36bf583c2bb4ac532d97f843141c907ee350f69",
          "message": "`SinglefileData`: Fix bug when `filename` is `pathlib.Path` (#6006)\n\nIt would raise an exception when the node was stored since it would\r\ncompare the `filename` against the list of objects, but the latter would\r\nbe instances of a string instead of `pathlib.Path` and the validation\r\nwould fail. On top of that, the difference in type was not visible as\r\nthe cause in the error message, making for a cryptic error.",
          "timestamp": "2023-05-11T08:24:16+02:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/f36bf583c2bb4ac532d97f843141c907ee350f69",
          "distinct": true,
          "tree_id": "6c57e2fbfef7e2d47918b663c43a085b73d846fb"
        },
        "date": 1683786946899,
        "benches": [
          {
            "name": "tests/benchmark/test_archive.py::test_export[no-objects]",
            "value": 2.524264806250199,
            "unit": "iter/sec",
            "range": "stddev: 0.070844",
            "group": "import-export",
            "extra": "mean: 396.15 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_export[with-objects]",
            "value": 2.5049420267395806,
            "unit": "iter/sec",
            "range": "stddev: 0.079435",
            "group": "import-export",
            "extra": "mean: 399.21 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[no-objects]",
            "value": 3.6943273719881917,
            "unit": "iter/sec",
            "range": "stddev: 0.068254",
            "group": "import-export",
            "extra": "mean: 270.69 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[with-objects]",
            "value": 3.5537583699320114,
            "unit": "iter/sec",
            "range": "stddev: 0.070108",
            "group": "import-export",
            "extra": "mean: 281.39 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 2.932295779959863,
            "unit": "iter/sec",
            "range": "stddev: 0.0074312",
            "group": "engine",
            "extra": "mean: 341.03 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.6484849538561945,
            "unit": "iter/sec",
            "range": "stddev: 0.085767",
            "group": "engine",
            "extra": "mean: 1.5421 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.7232887791384776,
            "unit": "iter/sec",
            "range": "stddev: 0.068023",
            "group": "engine",
            "extra": "mean: 1.3826 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.16255498445289726,
            "unit": "iter/sec",
            "range": "stddev: 0.085132",
            "group": "engine",
            "extra": "mean: 6.1518 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.18476418000545225,
            "unit": "iter/sec",
            "range": "stddev: 0.078707",
            "group": "engine",
            "extra": "mean: 5.4123 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.22851255298887,
            "unit": "iter/sec",
            "range": "stddev: 0.087347",
            "group": "engine",
            "extra": "mean: 448.73 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.5400464082648739,
            "unit": "iter/sec",
            "range": "stddev: 0.066685",
            "group": "engine",
            "extra": "mean: 1.8517 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.5952473801051449,
            "unit": "iter/sec",
            "range": "stddev: 0.097473",
            "group": "engine",
            "extra": "mean: 1.6800 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.14806917227656285,
            "unit": "iter/sec",
            "range": "stddev: 0.13733",
            "group": "engine",
            "extra": "mean: 6.7536 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.16406418120962918,
            "unit": "iter/sec",
            "range": "stddev: 0.15866",
            "group": "engine",
            "extra": "mean: 6.0952 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 281.93589372457706,
            "unit": "iter/sec",
            "range": "stddev: 0.00020654",
            "group": "node",
            "extra": "mean: 3.5469 msec\nrounds: 192"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 111.4710486500709,
            "unit": "iter/sec",
            "range": "stddev: 0.00047195",
            "group": "node",
            "extra": "mean: 8.9709 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 63.12639831878735,
            "unit": "iter/sec",
            "range": "stddev: 0.0021598",
            "group": "node",
            "extra": "mean: 15.841 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 176.23760305733273,
            "unit": "iter/sec",
            "range": "stddev: 0.00069873",
            "group": "node",
            "extra": "mean: 5.6742 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 41.535512264045366,
            "unit": "iter/sec",
            "range": "stddev: 0.026244",
            "group": "node",
            "extra": "mean: 24.076 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 46.53533263745353,
            "unit": "iter/sec",
            "range": "stddev: 0.0023573",
            "group": "node",
            "extra": "mean: 21.489 msec\nrounds: 100"
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
          "pythonVersion": "3.10.11",
          "metadata": "postgres:12.14, rabbitmq:3.8.14-management"
        },
        "commit": {
          "id": "1a0c1ee932f24a6b191dc2e4d770973b8b32d66e",
          "message": "Expose `get_daemon_client` so it can be imported from `aiida.engine` (#6008)\n\nThis is public API that users should use to easily obtain a\r\n`DaemonClient` instance to control the daemon. Currently it has to be\r\nimported from `aiida.engine.daemon.client` which is unnecessarily buried\r\ndeep down.",
          "timestamp": "2023-05-11T10:52:56+02:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/1a0c1ee932f24a6b191dc2e4d770973b8b32d66e",
          "distinct": true,
          "tree_id": "125b38e583e81e1236f39532c22cbeadfa8fb3a2"
        },
        "date": 1683795780234,
        "benches": [
          {
            "name": "tests/benchmark/test_archive.py::test_export[no-objects]",
            "value": 3.3655058566543765,
            "unit": "iter/sec",
            "range": "stddev: 0.072321",
            "group": "import-export",
            "extra": "mean: 297.13 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_export[with-objects]",
            "value": 3.240276556372838,
            "unit": "iter/sec",
            "range": "stddev: 0.074687",
            "group": "import-export",
            "extra": "mean: 308.62 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[no-objects]",
            "value": 4.223699041642568,
            "unit": "iter/sec",
            "range": "stddev: 0.073891",
            "group": "import-export",
            "extra": "mean: 236.76 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[with-objects]",
            "value": 4.111525578091592,
            "unit": "iter/sec",
            "range": "stddev: 0.075665",
            "group": "import-export",
            "extra": "mean: 243.22 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.4412489527443753,
            "unit": "iter/sec",
            "range": "stddev: 0.0031561",
            "group": "engine",
            "extra": "mean: 290.59 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.7205071452664786,
            "unit": "iter/sec",
            "range": "stddev: 0.085358",
            "group": "engine",
            "extra": "mean: 1.3879 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.8129908620232003,
            "unit": "iter/sec",
            "range": "stddev: 0.086718",
            "group": "engine",
            "extra": "mean: 1.2300 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.18444601852762932,
            "unit": "iter/sec",
            "range": "stddev: 0.14797",
            "group": "engine",
            "extra": "mean: 5.4216 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.20925036802302865,
            "unit": "iter/sec",
            "range": "stddev: 0.12471",
            "group": "engine",
            "extra": "mean: 4.7790 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.6962210783189664,
            "unit": "iter/sec",
            "range": "stddev: 0.018237",
            "group": "engine",
            "extra": "mean: 370.89 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.5985439733831376,
            "unit": "iter/sec",
            "range": "stddev: 0.033613",
            "group": "engine",
            "extra": "mean: 1.6707 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.6744986800819307,
            "unit": "iter/sec",
            "range": "stddev: 0.085634",
            "group": "engine",
            "extra": "mean: 1.4826 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.16636498282741796,
            "unit": "iter/sec",
            "range": "stddev: 0.16025",
            "group": "engine",
            "extra": "mean: 6.0109 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.1880906511570997,
            "unit": "iter/sec",
            "range": "stddev: 0.13444",
            "group": "engine",
            "extra": "mean: 5.3166 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 312.94068739977695,
            "unit": "iter/sec",
            "range": "stddev: 0.00024195",
            "group": "node",
            "extra": "mean: 3.1955 msec\nrounds: 190"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 125.94624814127415,
            "unit": "iter/sec",
            "range": "stddev: 0.00037009",
            "group": "node",
            "extra": "mean: 7.9399 msec\nrounds: 116"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 73.35690523486288,
            "unit": "iter/sec",
            "range": "stddev: 0.00056696",
            "group": "node",
            "extra": "mean: 13.632 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 207.18821829515164,
            "unit": "iter/sec",
            "range": "stddev: 0.00024742",
            "group": "node",
            "extra": "mean: 4.8265 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 48.80151840264289,
            "unit": "iter/sec",
            "range": "stddev: 0.027096",
            "group": "node",
            "extra": "mean: 20.491 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 54.49322758222079,
            "unit": "iter/sec",
            "range": "stddev: 0.0023391",
            "group": "node",
            "extra": "mean: 18.351 msec\nrounds: 100"
          }
        ]
      }
    ]
  }
}