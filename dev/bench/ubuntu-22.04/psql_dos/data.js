window.BENCHMARK_DATA = {
  "lastUpdate": 1681421455580,
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
      }
    ]
  }
}