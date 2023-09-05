window.BENCHMARK_DATA = {
  "lastUpdate": 1693919665178,
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
          "id": "2bfc3c6a8ce4100a53fe9842835d5b7a03b1bd29",
          "message": "`DaemonClient`: Clean stale PID file in `stop_daemon` (#6007)\n\nThe daemon client was recently refactored to only clean the stale PID\r\nfile in the `start_daemon` command. Before it was done when asking the\r\nstatus which was considered an unexpected side-effect.\r\n\r\nSometimes, the user wants to make sure the daemon is no longer running.\r\nCurrently, the status would raise a warning if a stale PID file is found\r\nsuggesting the user to start the daemon to fix it. However, this is\r\ncounterintuitve and not desirable if the goal is for the daemon to be\r\nstopped.\r\n\r\nThe `stop_daemon` method is updated to also clean any potentially stale\r\nPID files. The error message is updated to suggest to either start or\r\nstop the daemon to return it to a nominal state.\r\n\r\nCo-authored-by: Sebastiaan Huber <mail@sphuber.net>",
          "timestamp": "2023-05-11T10:52:23+02:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/2bfc3c6a8ce4100a53fe9842835d5b7a03b1bd29",
          "distinct": true,
          "tree_id": "26255191abc46ac6b038ca95bcb01b18b5d6fd61"
        },
        "date": 1683795821034,
        "benches": [
          {
            "name": "tests/benchmark/test_archive.py::test_export[no-objects]",
            "value": 2.830518430636943,
            "unit": "iter/sec",
            "range": "stddev: 0.068828",
            "group": "import-export",
            "extra": "mean: 353.29 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_export[with-objects]",
            "value": 2.678653320623777,
            "unit": "iter/sec",
            "range": "stddev: 0.068078",
            "group": "import-export",
            "extra": "mean: 373.32 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[no-objects]",
            "value": 3.7556894293656096,
            "unit": "iter/sec",
            "range": "stddev: 0.066191",
            "group": "import-export",
            "extra": "mean: 266.26 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[with-objects]",
            "value": 3.57685280909954,
            "unit": "iter/sec",
            "range": "stddev: 0.069175",
            "group": "import-export",
            "extra": "mean: 279.58 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.032403915573102,
            "unit": "iter/sec",
            "range": "stddev: 0.0067854",
            "group": "engine",
            "extra": "mean: 329.77 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.637892250013662,
            "unit": "iter/sec",
            "range": "stddev: 0.13618",
            "group": "engine",
            "extra": "mean: 1.5677 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.7146178258762023,
            "unit": "iter/sec",
            "range": "stddev: 0.089402",
            "group": "engine",
            "extra": "mean: 1.3993 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.16466679605810222,
            "unit": "iter/sec",
            "range": "stddev: 0.19368",
            "group": "engine",
            "extra": "mean: 6.0729 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.1827608638792945,
            "unit": "iter/sec",
            "range": "stddev: 0.13890",
            "group": "engine",
            "extra": "mean: 5.4716 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.2584376225549203,
            "unit": "iter/sec",
            "range": "stddev: 0.075405",
            "group": "engine",
            "extra": "mean: 442.78 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.529061169132976,
            "unit": "iter/sec",
            "range": "stddev: 0.093035",
            "group": "engine",
            "extra": "mean: 1.8901 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.5923933134829,
            "unit": "iter/sec",
            "range": "stddev: 0.084651",
            "group": "engine",
            "extra": "mean: 1.6881 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.14483533397221612,
            "unit": "iter/sec",
            "range": "stddev: 0.23740",
            "group": "engine",
            "extra": "mean: 6.9044 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.16868712948185607,
            "unit": "iter/sec",
            "range": "stddev: 0.27870",
            "group": "engine",
            "extra": "mean: 5.9281 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 276.7426903030123,
            "unit": "iter/sec",
            "range": "stddev: 0.00031113",
            "group": "node",
            "extra": "mean: 3.6135 msec\nrounds: 196"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 110.40741924258246,
            "unit": "iter/sec",
            "range": "stddev: 0.00042356",
            "group": "node",
            "extra": "mean: 9.0574 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 63.24003968743083,
            "unit": "iter/sec",
            "range": "stddev: 0.0014855",
            "group": "node",
            "extra": "mean: 15.813 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 188.37804017034458,
            "unit": "iter/sec",
            "range": "stddev: 0.00019115",
            "group": "node",
            "extra": "mean: 5.3085 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 41.17236629909908,
            "unit": "iter/sec",
            "range": "stddev: 0.027226",
            "group": "node",
            "extra": "mean: 24.288 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 47.49660990809758,
            "unit": "iter/sec",
            "range": "stddev: 0.0020006",
            "group": "node",
            "extra": "mean: 21.054 msec\nrounds: 100"
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
          "id": "a2a05a69fb2fa6aae9a96d49d543e72008d2888f",
          "message": "Dependencies: Update requirement `flask~=2.2` (#6011)\n\nIn 508aeda0ad9c50b24d77f25234e63e67038eb8f2, an upper limit was placed\r\non the `flask` dependency because `flask==2.2` removed the class\r\n`flask.json.JSONEncoder`.\r\n\r\nHere the upper limit is removed and the minimum requirement is updated.\r\nThe `JSONEncoder` is replaced with `flask.json.provider.DefaultJSONProvider`.\r\n\r\nCo-authored-by: Marnik Bercx <mbercx@gmail.com>\r\nCo-authored-by: Kristjan Eimre <eimrek@users.noreply.github.com>",
          "timestamp": "2023-05-12T16:54:28+02:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/a2a05a69fb2fa6aae9a96d49d543e72008d2888f",
          "distinct": true,
          "tree_id": "352a9f224fddbfd9639374d253d8947fe7b814fb"
        },
        "date": 1683903841841,
        "benches": [
          {
            "name": "tests/benchmark/test_archive.py::test_export[no-objects]",
            "value": 3.370508469787377,
            "unit": "iter/sec",
            "range": "stddev: 0.067947",
            "group": "import-export",
            "extra": "mean: 296.69 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_export[with-objects]",
            "value": 3.291229873825162,
            "unit": "iter/sec",
            "range": "stddev: 0.070305",
            "group": "import-export",
            "extra": "mean: 303.84 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[no-objects]",
            "value": 4.255597575180283,
            "unit": "iter/sec",
            "range": "stddev: 0.074140",
            "group": "import-export",
            "extra": "mean: 234.98 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[with-objects]",
            "value": 4.236828188397565,
            "unit": "iter/sec",
            "range": "stddev: 0.069193",
            "group": "import-export",
            "extra": "mean: 236.03 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.5013550033782126,
            "unit": "iter/sec",
            "range": "stddev: 0.0042203",
            "group": "engine",
            "extra": "mean: 285.60 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.7586288883249894,
            "unit": "iter/sec",
            "range": "stddev: 0.087549",
            "group": "engine",
            "extra": "mean: 1.3182 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.8525272222217176,
            "unit": "iter/sec",
            "range": "stddev: 0.076225",
            "group": "engine",
            "extra": "mean: 1.1730 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.19022342386961044,
            "unit": "iter/sec",
            "range": "stddev: 0.17442",
            "group": "engine",
            "extra": "mean: 5.2570 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.21348106130323988,
            "unit": "iter/sec",
            "range": "stddev: 0.10863",
            "group": "engine",
            "extra": "mean: 4.6843 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.6338457292669872,
            "unit": "iter/sec",
            "range": "stddev: 0.032235",
            "group": "engine",
            "extra": "mean: 379.67 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.6068517029424951,
            "unit": "iter/sec",
            "range": "stddev: 0.038726",
            "group": "engine",
            "extra": "mean: 1.6478 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.69647044480499,
            "unit": "iter/sec",
            "range": "stddev: 0.047331",
            "group": "engine",
            "extra": "mean: 1.4358 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.1708059834938045,
            "unit": "iter/sec",
            "range": "stddev: 0.068470",
            "group": "engine",
            "extra": "mean: 5.8546 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.19327190140837308,
            "unit": "iter/sec",
            "range": "stddev: 0.082587",
            "group": "engine",
            "extra": "mean: 5.1741 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 320.59812368275254,
            "unit": "iter/sec",
            "range": "stddev: 0.00022215",
            "group": "node",
            "extra": "mean: 3.1192 msec\nrounds: 201"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 124.70585461769126,
            "unit": "iter/sec",
            "range": "stddev: 0.00099113",
            "group": "node",
            "extra": "mean: 8.0189 msec\nrounds: 113"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 78.64932079705838,
            "unit": "iter/sec",
            "range": "stddev: 0.0010065",
            "group": "node",
            "extra": "mean: 12.715 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 212.49299166226592,
            "unit": "iter/sec",
            "range": "stddev: 0.00058172",
            "group": "node",
            "extra": "mean: 4.7060 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 51.049044411243145,
            "unit": "iter/sec",
            "range": "stddev: 0.025269",
            "group": "node",
            "extra": "mean: 19.589 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 56.14427673718208,
            "unit": "iter/sec",
            "range": "stddev: 0.0020991",
            "group": "node",
            "extra": "mean: 17.811 msec\nrounds: 100"
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
          "id": "7ad91683643a5d9134c2a9532901e00b903996b4",
          "message": "`PsqlDos`: Add migration to remove hashes for all `CalcJobNodes`\n\nThe algorithm for computing the hashes of `CalcJobNodes` contained a bug\nwhich was fixed in 685e0f87d7c571df24aea8f0ce21c6c45dfbd8a0. This means\nhowever that all existing hashes for `CalcJobNodes` are inconsistent\nwith the new algorithm. This would mean that valid cache hits would be\nmissed, and worse, different calculatons could end up with the same hash\nand mistakingly be cached from one another.\n\nThe migration drops the `_aiida_hash` extra which is used to store the\nnode's hash. A warning is emitted to notify the user, suggesting to run\n`verdi node rehash` to recompute the hash of all `CalcJobNodes`.",
          "timestamp": "2023-05-15T17:37:30+02:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/7ad91683643a5d9134c2a9532901e00b903996b4",
          "distinct": true,
          "tree_id": "275a20d83f1b9201f575cede0a8dc98c337f3a73"
        },
        "date": 1684165710734,
        "benches": [
          {
            "name": "tests/benchmark/test_archive.py::test_export[no-objects]",
            "value": 2.662165789701788,
            "unit": "iter/sec",
            "range": "stddev: 0.071154",
            "group": "import-export",
            "extra": "mean: 375.63 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_export[with-objects]",
            "value": 2.778304983657816,
            "unit": "iter/sec",
            "range": "stddev: 0.074746",
            "group": "import-export",
            "extra": "mean: 359.93 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[no-objects]",
            "value": 3.66817201772232,
            "unit": "iter/sec",
            "range": "stddev: 0.067636",
            "group": "import-export",
            "extra": "mean: 272.62 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[with-objects]",
            "value": 3.5774267779599334,
            "unit": "iter/sec",
            "range": "stddev: 0.073361",
            "group": "import-export",
            "extra": "mean: 279.53 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 2.9158542064149886,
            "unit": "iter/sec",
            "range": "stddev: 0.012243",
            "group": "engine",
            "extra": "mean: 342.95 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.6425987806746214,
            "unit": "iter/sec",
            "range": "stddev: 0.044718",
            "group": "engine",
            "extra": "mean: 1.5562 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.7377947108300863,
            "unit": "iter/sec",
            "range": "stddev: 0.073053",
            "group": "engine",
            "extra": "mean: 1.3554 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.16410758017547386,
            "unit": "iter/sec",
            "range": "stddev: 0.14045",
            "group": "engine",
            "extra": "mean: 6.0936 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.18507855716131516,
            "unit": "iter/sec",
            "range": "stddev: 0.16270",
            "group": "engine",
            "extra": "mean: 5.4031 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.4025485997214346,
            "unit": "iter/sec",
            "range": "stddev: 0.026934",
            "group": "engine",
            "extra": "mean: 416.22 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.5351509303135739,
            "unit": "iter/sec",
            "range": "stddev: 0.066617",
            "group": "engine",
            "extra": "mean: 1.8686 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.5979336389147282,
            "unit": "iter/sec",
            "range": "stddev: 0.061301",
            "group": "engine",
            "extra": "mean: 1.6724 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.14539374716323453,
            "unit": "iter/sec",
            "range": "stddev: 0.13545",
            "group": "engine",
            "extra": "mean: 6.8779 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.16647676011438803,
            "unit": "iter/sec",
            "range": "stddev: 0.14563",
            "group": "engine",
            "extra": "mean: 6.0068 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 315.04409756529225,
            "unit": "iter/sec",
            "range": "stddev: 0.00082084",
            "group": "node",
            "extra": "mean: 3.1742 msec\nrounds: 213"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 119.1711744444555,
            "unit": "iter/sec",
            "range": "stddev: 0.0019638",
            "group": "node",
            "extra": "mean: 8.3913 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 71.32066463846846,
            "unit": "iter/sec",
            "range": "stddev: 0.0015735",
            "group": "node",
            "extra": "mean: 14.021 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 213.7016665627749,
            "unit": "iter/sec",
            "range": "stddev: 0.00017032",
            "group": "node",
            "extra": "mean: 4.6794 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 50.16092623338813,
            "unit": "iter/sec",
            "range": "stddev: 0.0016125",
            "group": "node",
            "extra": "mean: 19.936 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 47.851753819625486,
            "unit": "iter/sec",
            "range": "stddev: 0.0023762",
            "group": "node",
            "extra": "mean: 20.898 msec\nrounds: 100"
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
          "id": "60756fe30dfaff443ab434d92196249eea47f166",
          "message": "`Process`: Have `inputs` property always return `AttributesFrozenDict` (#6010)\n\nThe `Process.inputs` property as implemented in `plumpy` has as a return\r\ntype `AttributesFrozenDict | None`. This leads to a lot unnecessary\r\ncomplexities in the code having to deal with the potential `None`, where\r\nreally this should never really occur. A lot of user code will never\r\neven check for `Process.inputs` returning `None`, such as in `WorkChain`\r\nimplementations, and as a result type checkers will fail forcing a user\r\nto either unnecessarily complicate their code by explicitly checking for\r\n`None`, but will typically end up silencing the error.\r\n\r\nThe `inputs` property is overridden here to return an empty\r\n`AttributesFrozenDict` in case the inputs are `None`, which allows to\r\nsimplify the return type and get rid of any type errors in downstream\r\ncode.",
          "timestamp": "2023-05-15T22:26:30+02:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/60756fe30dfaff443ab434d92196249eea47f166",
          "distinct": true,
          "tree_id": "5f5dcf997a88724abfe2994d9a07b5f3639b2633"
        },
        "date": 1684183085383,
        "benches": [
          {
            "name": "tests/benchmark/test_archive.py::test_export[no-objects]",
            "value": 2.4433796693118515,
            "unit": "iter/sec",
            "range": "stddev: 0.072181",
            "group": "import-export",
            "extra": "mean: 409.27 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_export[with-objects]",
            "value": 2.400220231247226,
            "unit": "iter/sec",
            "range": "stddev: 0.072933",
            "group": "import-export",
            "extra": "mean: 416.63 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[no-objects]",
            "value": 3.5756353191516497,
            "unit": "iter/sec",
            "range": "stddev: 0.064861",
            "group": "import-export",
            "extra": "mean: 279.67 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[with-objects]",
            "value": 3.4922452071625614,
            "unit": "iter/sec",
            "range": "stddev: 0.087073",
            "group": "import-export",
            "extra": "mean: 286.35 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 2.6708759743245643,
            "unit": "iter/sec",
            "range": "stddev: 0.013850",
            "group": "engine",
            "extra": "mean: 374.41 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.6054905378568016,
            "unit": "iter/sec",
            "range": "stddev: 0.048788",
            "group": "engine",
            "extra": "mean: 1.6516 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.6931513845440108,
            "unit": "iter/sec",
            "range": "stddev: 0.070692",
            "group": "engine",
            "extra": "mean: 1.4427 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.15761979072271498,
            "unit": "iter/sec",
            "range": "stddev: 0.15975",
            "group": "engine",
            "extra": "mean: 6.3444 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.17463964285284012,
            "unit": "iter/sec",
            "range": "stddev: 0.15964",
            "group": "engine",
            "extra": "mean: 5.7261 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.2492512409625744,
            "unit": "iter/sec",
            "range": "stddev: 0.024020",
            "group": "engine",
            "extra": "mean: 444.59 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.49746719064550055,
            "unit": "iter/sec",
            "range": "stddev: 0.062987",
            "group": "engine",
            "extra": "mean: 2.0102 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.5639178448742471,
            "unit": "iter/sec",
            "range": "stddev: 0.087189",
            "group": "engine",
            "extra": "mean: 1.7733 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.14141680482310395,
            "unit": "iter/sec",
            "range": "stddev: 0.16041",
            "group": "engine",
            "extra": "mean: 7.0713 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.1543117969484742,
            "unit": "iter/sec",
            "range": "stddev: 0.16738",
            "group": "engine",
            "extra": "mean: 6.4804 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 290.48289342479165,
            "unit": "iter/sec",
            "range": "stddev: 0.00038291",
            "group": "node",
            "extra": "mean: 3.4425 msec\nrounds: 215"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 109.04667353453432,
            "unit": "iter/sec",
            "range": "stddev: 0.00069179",
            "group": "node",
            "extra": "mean: 9.1704 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 65.0663812719802,
            "unit": "iter/sec",
            "range": "stddev: 0.0011706",
            "group": "node",
            "extra": "mean: 15.369 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 178.15982116438323,
            "unit": "iter/sec",
            "range": "stddev: 0.00066573",
            "group": "node",
            "extra": "mean: 5.6129 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 43.95636227740958,
            "unit": "iter/sec",
            "range": "stddev: 0.0026969",
            "group": "node",
            "extra": "mean: 22.750 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 42.5217329342474,
            "unit": "iter/sec",
            "range": "stddev: 0.0024153",
            "group": "node",
            "extra": "mean: 23.517 msec\nrounds: 100"
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
          "id": "6a88cb3158c0b84b601a289f50f51cfe6ae42687",
          "message": "`CalcJob`: Remove default of `withmpi` input and make it optional (#6020)\n\nThe `metadata.options.withmpi` specified `False` as the default. This\r\ncan pose a problem for `CalcJob` implementations that can run with and\r\nwithout MPI.\r\n\r\nSince the recent changes in the handling of MPI for `CalcJob` runs, see\r\ncdb3eed92b052dea5ca697adffaf3025cbc0ab03, there are now three ways that\r\nit is controlled:\r\n\r\n * `metadata.options.withmpi` input\r\n * `CodeInfo.withmpi` returned by the `CalcJob` implementation\r\n * `AbstractCode.with_mpi` attribute\r\n\r\nThe engine will check each of these, and when any of them are explicitly\r\nset to conflicting values, an error is raised. The problem is that the\r\n`CalcJob` base class, set a default for the `metadata.options.withmpi`\r\ninput, and set it to `False`.\r\n\r\nThis forces all `CalcJob` plugins to manually unset it if they can in\r\nprinciple run with or without MPI, as it would except if a `Code` would\r\nbe passed in the inputs that set `with_mpi` to `True`. The code to do it\r\nis non-trivial though:\r\n\r\n    options['withmpi'].default = None\r\n    options['withmpi'].required = False\r\n    options['withmpi'].valid_type = (bool, type(None))\r\n\r\nThis is not user-friendly for users wanting to implement `CalcJob`\r\nplugins and it is better to remove the default on the base class.\r\n\r\nThis change should be fully-backwards compatible since the logic in\r\n`CalcJob.presubmit` will check the case where none of the three methods\r\nexplicitly set a value. In this case, the logic used to fall back on the\r\nvalue of the option set on the node. This branch would actually never be\r\nhit, because in this case, the default of `metadata.options.withmpi`\r\nwould always be set to `False`. This fallback keeps `False` as default,\r\nbut hardcodes it instead of taking it from the option input.",
          "timestamp": "2023-05-16T15:38:41+02:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/6a88cb3158c0b84b601a289f50f51cfe6ae42687",
          "distinct": true,
          "tree_id": "c5ba0efa67ec2dc27bfec28051483e9cacab526b"
        },
        "date": 1684244879097,
        "benches": [
          {
            "name": "tests/benchmark/test_archive.py::test_export[no-objects]",
            "value": 3.387988728893277,
            "unit": "iter/sec",
            "range": "stddev: 0.055355",
            "group": "import-export",
            "extra": "mean: 295.16 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_export[with-objects]",
            "value": 3.3539750410526556,
            "unit": "iter/sec",
            "range": "stddev: 0.060011",
            "group": "import-export",
            "extra": "mean: 298.15 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[no-objects]",
            "value": 4.412378170823918,
            "unit": "iter/sec",
            "range": "stddev: 0.062181",
            "group": "import-export",
            "extra": "mean: 226.64 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[with-objects]",
            "value": 4.314477632235739,
            "unit": "iter/sec",
            "range": "stddev: 0.060532",
            "group": "import-export",
            "extra": "mean: 231.78 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.5676103593760695,
            "unit": "iter/sec",
            "range": "stddev: 0.0061497",
            "group": "engine",
            "extra": "mean: 280.30 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.7856233806156364,
            "unit": "iter/sec",
            "range": "stddev: 0.033279",
            "group": "engine",
            "extra": "mean: 1.2729 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.8969586767701287,
            "unit": "iter/sec",
            "range": "stddev: 0.070926",
            "group": "engine",
            "extra": "mean: 1.1149 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.1994433236912906,
            "unit": "iter/sec",
            "range": "stddev: 0.12493",
            "group": "engine",
            "extra": "mean: 5.0140 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.22307454438054805,
            "unit": "iter/sec",
            "range": "stddev: 0.12116",
            "group": "engine",
            "extra": "mean: 4.4828 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.8929217060919634,
            "unit": "iter/sec",
            "range": "stddev: 0.019568",
            "group": "engine",
            "extra": "mean: 345.67 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.6286237638813598,
            "unit": "iter/sec",
            "range": "stddev: 0.040465",
            "group": "engine",
            "extra": "mean: 1.5908 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.7093214340921488,
            "unit": "iter/sec",
            "range": "stddev: 0.056505",
            "group": "engine",
            "extra": "mean: 1.4098 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.1741590688628506,
            "unit": "iter/sec",
            "range": "stddev: 0.11064",
            "group": "engine",
            "extra": "mean: 5.7419 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.19773671450349403,
            "unit": "iter/sec",
            "range": "stddev: 0.12621",
            "group": "engine",
            "extra": "mean: 5.0572 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 365.0036050760932,
            "unit": "iter/sec",
            "range": "stddev: 0.00036176",
            "group": "node",
            "extra": "mean: 2.7397 msec\nrounds: 247"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 146.70742568449134,
            "unit": "iter/sec",
            "range": "stddev: 0.00027050",
            "group": "node",
            "extra": "mean: 6.8163 msec\nrounds: 126"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 86.4353712430177,
            "unit": "iter/sec",
            "range": "stddev: 0.00058294",
            "group": "node",
            "extra": "mean: 11.569 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 247.71504668333412,
            "unit": "iter/sec",
            "range": "stddev: 0.00020065",
            "group": "node",
            "extra": "mean: 4.0369 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 60.06620932470433,
            "unit": "iter/sec",
            "range": "stddev: 0.0014262",
            "group": "node",
            "extra": "mean: 16.648 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 51.4958354772114,
            "unit": "iter/sec",
            "range": "stddev: 0.022201",
            "group": "node",
            "extra": "mean: 19.419 msec\nrounds: 100"
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
          "id": "c72a252ed563c7f0a7604d15632331c094973b5f",
          "message": "Improve clarity of various deprecation warnings (#5774)\n\nA number of deprecation warnings are updated to reference the actual\r\nmethod or property that is throwing the warning. In certain cases, the\r\n`stacklevel` is adjusted such that the relevant caller is displayed in\r\nthe warning making it easier to track down for the users.\r\n\r\nCo-authored-by: Sebastiaan Huber <mail@sphuber.net>",
          "timestamp": "2023-05-16T17:46:30+02:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/c72a252ed563c7f0a7604d15632331c094973b5f",
          "distinct": true,
          "tree_id": "278d96f7ac69d8aad37fdf091ca9eeb591a09232"
        },
        "date": 1684252562036,
        "benches": [
          {
            "name": "tests/benchmark/test_archive.py::test_export[no-objects]",
            "value": 3.4063232424254357,
            "unit": "iter/sec",
            "range": "stddev: 0.047252",
            "group": "import-export",
            "extra": "mean: 293.57 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_export[with-objects]",
            "value": 3.465532607162444,
            "unit": "iter/sec",
            "range": "stddev: 0.048241",
            "group": "import-export",
            "extra": "mean: 288.56 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[no-objects]",
            "value": 4.169918802267117,
            "unit": "iter/sec",
            "range": "stddev: 0.059365",
            "group": "import-export",
            "extra": "mean: 239.81 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[with-objects]",
            "value": 4.154708311110271,
            "unit": "iter/sec",
            "range": "stddev: 0.055566",
            "group": "import-export",
            "extra": "mean: 240.69 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.353531723089989,
            "unit": "iter/sec",
            "range": "stddev: 0.0075180",
            "group": "engine",
            "extra": "mean: 298.19 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.7646323062434666,
            "unit": "iter/sec",
            "range": "stddev: 0.046821",
            "group": "engine",
            "extra": "mean: 1.3078 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.85286557872908,
            "unit": "iter/sec",
            "range": "stddev: 0.067936",
            "group": "engine",
            "extra": "mean: 1.1725 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.2003915171309016,
            "unit": "iter/sec",
            "range": "stddev: 0.16909",
            "group": "engine",
            "extra": "mean: 4.9902 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.224895770396605,
            "unit": "iter/sec",
            "range": "stddev: 0.14444",
            "group": "engine",
            "extra": "mean: 4.4465 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.680085580010128,
            "unit": "iter/sec",
            "range": "stddev: 0.045187",
            "group": "engine",
            "extra": "mean: 373.12 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.6206674618932143,
            "unit": "iter/sec",
            "range": "stddev: 0.055231",
            "group": "engine",
            "extra": "mean: 1.6112 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.699505713174423,
            "unit": "iter/sec",
            "range": "stddev: 0.038325",
            "group": "engine",
            "extra": "mean: 1.4296 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.17052742059674625,
            "unit": "iter/sec",
            "range": "stddev: 0.19509",
            "group": "engine",
            "extra": "mean: 5.8642 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.19442031144110547,
            "unit": "iter/sec",
            "range": "stddev: 0.10345",
            "group": "engine",
            "extra": "mean: 5.1435 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 421.69884488985105,
            "unit": "iter/sec",
            "range": "stddev: 0.00021812",
            "group": "node",
            "extra": "mean: 2.3714 msec\nrounds: 284"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 155.5618752373146,
            "unit": "iter/sec",
            "range": "stddev: 0.00071300",
            "group": "node",
            "extra": "mean: 6.4283 msec\nrounds: 134"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 87.16680445411886,
            "unit": "iter/sec",
            "range": "stddev: 0.0014466",
            "group": "node",
            "extra": "mean: 11.472 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 260.72388903145924,
            "unit": "iter/sec",
            "range": "stddev: 0.00024853",
            "group": "node",
            "extra": "mean: 3.8355 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 57.04861299719197,
            "unit": "iter/sec",
            "range": "stddev: 0.0018791",
            "group": "node",
            "extra": "mean: 17.529 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 56.39794168832829,
            "unit": "iter/sec",
            "range": "stddev: 0.0017323",
            "group": "node",
            "extra": "mean: 17.731 msec\nrounds: 100"
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
          "id": "220a65c76d9fcf3144ef77925caff8f5c653b2c9",
          "message": "`DynamicEntryPointCommandGroup`: Add support for shared options\n\nThe idea for the `DynamicEntryPointCommandGroup` is to easily create a\ncommand that has subcommands that are created dynamically based on the\nentry points that are registered in a certain group. Each entry point\nwould provide the specific CLI options that it would require. However,\noften there will be shared options that are not specific to any entry\npoint but all of them would require.\n\nHere the `shared_options` argument is added to the constructor of the\n`DynamicEntryPointCommandGroup`. It takes a list of `click.Option`\ninstances and when defined, these options will be added in reverse order\nafter the options of the specific entry point have been added. This\nensures that the shared options will be available to all dynamically\ngenerated subcommands.",
          "timestamp": "2023-05-17T08:55:27+02:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/220a65c76d9fcf3144ef77925caff8f5c653b2c9",
          "distinct": true,
          "tree_id": "91d1168a2d19c309e23aeebf7bd28e5a2ed0821d"
        },
        "date": 1684307287235,
        "benches": [
          {
            "name": "tests/benchmark/test_archive.py::test_export[no-objects]",
            "value": 2.2721850957970506,
            "unit": "iter/sec",
            "range": "stddev: 0.069440",
            "group": "import-export",
            "extra": "mean: 440.10 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_export[with-objects]",
            "value": 2.184781311731154,
            "unit": "iter/sec",
            "range": "stddev: 0.070007",
            "group": "import-export",
            "extra": "mean: 457.71 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[no-objects]",
            "value": 3.247137678510736,
            "unit": "iter/sec",
            "range": "stddev: 0.070868",
            "group": "import-export",
            "extra": "mean: 307.96 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[with-objects]",
            "value": 3.102956115725034,
            "unit": "iter/sec",
            "range": "stddev: 0.090402",
            "group": "import-export",
            "extra": "mean: 322.27 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 2.400996087801433,
            "unit": "iter/sec",
            "range": "stddev: 0.010081",
            "group": "engine",
            "extra": "mean: 416.49 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.5229781313959712,
            "unit": "iter/sec",
            "range": "stddev: 0.061197",
            "group": "engine",
            "extra": "mean: 1.9121 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.5910016105134248,
            "unit": "iter/sec",
            "range": "stddev: 0.11091",
            "group": "engine",
            "extra": "mean: 1.6920 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.14065603381632438,
            "unit": "iter/sec",
            "range": "stddev: 0.22844",
            "group": "engine",
            "extra": "mean: 7.1095 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.15884473036569483,
            "unit": "iter/sec",
            "range": "stddev: 0.15651",
            "group": "engine",
            "extra": "mean: 6.2955 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 1.9711152238947496,
            "unit": "iter/sec",
            "range": "stddev: 0.054365",
            "group": "engine",
            "extra": "mean: 507.33 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.450475419450703,
            "unit": "iter/sec",
            "range": "stddev: 0.10058",
            "group": "engine",
            "extra": "mean: 2.2199 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.5128618885977454,
            "unit": "iter/sec",
            "range": "stddev: 0.10231",
            "group": "engine",
            "extra": "mean: 1.9498 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.1280890402080802,
            "unit": "iter/sec",
            "range": "stddev: 0.16549",
            "group": "engine",
            "extra": "mean: 7.8071 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.14322416712108368,
            "unit": "iter/sec",
            "range": "stddev: 0.20243",
            "group": "engine",
            "extra": "mean: 6.9821 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 261.85153808565593,
            "unit": "iter/sec",
            "range": "stddev: 0.0010253",
            "group": "node",
            "extra": "mean: 3.8190 msec\nrounds: 230"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 94.62961608198704,
            "unit": "iter/sec",
            "range": "stddev: 0.0023868",
            "group": "node",
            "extra": "mean: 10.568 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 53.67333331798308,
            "unit": "iter/sec",
            "range": "stddev: 0.0032230",
            "group": "node",
            "extra": "mean: 18.631 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 160.3189991533277,
            "unit": "iter/sec",
            "range": "stddev: 0.0010627",
            "group": "node",
            "extra": "mean: 6.2376 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 37.708052217292575,
            "unit": "iter/sec",
            "range": "stddev: 0.0042565",
            "group": "node",
            "extra": "mean: 26.520 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 36.813251286736296,
            "unit": "iter/sec",
            "range": "stddev: 0.0046088",
            "group": "node",
            "extra": "mean: 27.164 msec\nrounds: 100"
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
          "id": "c25de615e4680b809f5d65d42031afdf95bd6923",
          "message": "`SinglefileData`: Add the `from_string` classmethod (#6022)\n\nThis allows the construction of a `SinglefileData` from content that is\r\nalready in memory as a `str`. Although this was already possible through\r\n`SinglefileData(io.StringIO(content))`, the classmethod has advantages:\r\n\r\n* No need for separate import of `io`\r\n* Method can be found easily through introspection\r\n* Overall is more intuitive than turning string content into a stream",
          "timestamp": "2023-05-17T09:59:59+02:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/c25de615e4680b809f5d65d42031afdf95bd6923",
          "distinct": true,
          "tree_id": "d3be34b218b4690f1f42689a8ca7d6ca039bfcf1"
        },
        "date": 1684310969052,
        "benches": [
          {
            "name": "tests/benchmark/test_archive.py::test_export[no-objects]",
            "value": 3.335116316161432,
            "unit": "iter/sec",
            "range": "stddev: 0.067496",
            "group": "import-export",
            "extra": "mean: 299.84 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_export[with-objects]",
            "value": 3.245149976719581,
            "unit": "iter/sec",
            "range": "stddev: 0.061944",
            "group": "import-export",
            "extra": "mean: 308.15 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[no-objects]",
            "value": 4.265959149947397,
            "unit": "iter/sec",
            "range": "stddev: 0.061511",
            "group": "import-export",
            "extra": "mean: 234.41 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[with-objects]",
            "value": 4.174529832802034,
            "unit": "iter/sec",
            "range": "stddev: 0.066477",
            "group": "import-export",
            "extra": "mean: 239.55 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.411120042920329,
            "unit": "iter/sec",
            "range": "stddev: 0.0033887",
            "group": "engine",
            "extra": "mean: 293.16 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.7473560734118087,
            "unit": "iter/sec",
            "range": "stddev: 0.064057",
            "group": "engine",
            "extra": "mean: 1.3381 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.8597123606811938,
            "unit": "iter/sec",
            "range": "stddev: 0.081339",
            "group": "engine",
            "extra": "mean: 1.1632 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.19456380889478556,
            "unit": "iter/sec",
            "range": "stddev: 0.11524",
            "group": "engine",
            "extra": "mean: 5.1397 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.2123470992243502,
            "unit": "iter/sec",
            "range": "stddev: 0.10290",
            "group": "engine",
            "extra": "mean: 4.7093 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.713088497864192,
            "unit": "iter/sec",
            "range": "stddev: 0.026183",
            "group": "engine",
            "extra": "mean: 368.58 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.6046087684421828,
            "unit": "iter/sec",
            "range": "stddev: 0.077336",
            "group": "engine",
            "extra": "mean: 1.6540 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.7054480665959008,
            "unit": "iter/sec",
            "range": "stddev: 0.057063",
            "group": "engine",
            "extra": "mean: 1.4175 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.16589160223637828,
            "unit": "iter/sec",
            "range": "stddev: 0.17055",
            "group": "engine",
            "extra": "mean: 6.0280 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.1830926715757787,
            "unit": "iter/sec",
            "range": "stddev: 0.087555",
            "group": "engine",
            "extra": "mean: 5.4617 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 375.24192865330747,
            "unit": "iter/sec",
            "range": "stddev: 0.00054167",
            "group": "node",
            "extra": "mean: 2.6649 msec\nrounds: 246"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 143.5765739666392,
            "unit": "iter/sec",
            "range": "stddev: 0.00024547",
            "group": "node",
            "extra": "mean: 6.9649 msec\nrounds: 122"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 75.47829873314193,
            "unit": "iter/sec",
            "range": "stddev: 0.00090717",
            "group": "node",
            "extra": "mean: 13.249 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 233.89063186996856,
            "unit": "iter/sec",
            "range": "stddev: 0.00018906",
            "group": "node",
            "extra": "mean: 4.2755 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 52.84584864310111,
            "unit": "iter/sec",
            "range": "stddev: 0.0017765",
            "group": "node",
            "extra": "mean: 18.923 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 50.93757285857041,
            "unit": "iter/sec",
            "range": "stddev: 0.0022373",
            "group": "node",
            "extra": "mean: 19.632 msec\nrounds: 100"
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
          "id": "b2351a09720eb5f0eb8402558d1759c885ca6e66",
          "message": "Correct instructions to rehash nodes after migration (#6028)\n\nAfter a migration that can affect the hash of the migrated node, the\r\ninstructions to rehash the node are provided. However, these instructions are\r\ncurrently incorrect and likely to lead to confusion for the user.\r\n\r\nHere the instructions are corrected both when a specific entry point requires\r\nrehashing or not.",
          "timestamp": "2023-05-17T22:55:34+02:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/b2351a09720eb5f0eb8402558d1759c885ca6e66",
          "distinct": true,
          "tree_id": "1ff21433e4754bfbf215face05a557b48229d9e8"
        },
        "date": 1684357545298,
        "benches": [
          {
            "name": "tests/benchmark/test_archive.py::test_export[no-objects]",
            "value": 3.06023344568531,
            "unit": "iter/sec",
            "range": "stddev: 0.022340",
            "group": "import-export",
            "extra": "mean: 326.77 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_export[with-objects]",
            "value": 2.828374693797649,
            "unit": "iter/sec",
            "range": "stddev: 0.058646",
            "group": "import-export",
            "extra": "mean: 353.56 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[no-objects]",
            "value": 4.122368004968767,
            "unit": "iter/sec",
            "range": "stddev: 0.068314",
            "group": "import-export",
            "extra": "mean: 242.58 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[with-objects]",
            "value": 3.7575499700038066,
            "unit": "iter/sec",
            "range": "stddev: 0.066982",
            "group": "import-export",
            "extra": "mean: 266.13 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 2.9753844896942216,
            "unit": "iter/sec",
            "range": "stddev: 0.017766",
            "group": "engine",
            "extra": "mean: 336.09 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.6763715005345793,
            "unit": "iter/sec",
            "range": "stddev: 0.068035",
            "group": "engine",
            "extra": "mean: 1.4785 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.7634142696940471,
            "unit": "iter/sec",
            "range": "stddev: 0.072254",
            "group": "engine",
            "extra": "mean: 1.3099 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.1793135083840897,
            "unit": "iter/sec",
            "range": "stddev: 0.14491",
            "group": "engine",
            "extra": "mean: 5.5768 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.1985908857911219,
            "unit": "iter/sec",
            "range": "stddev: 0.11591",
            "group": "engine",
            "extra": "mean: 5.0355 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.4877001221252155,
            "unit": "iter/sec",
            "range": "stddev: 0.025517",
            "group": "engine",
            "extra": "mean: 401.98 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.5738346093826915,
            "unit": "iter/sec",
            "range": "stddev: 0.067096",
            "group": "engine",
            "extra": "mean: 1.7427 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.6525969451809674,
            "unit": "iter/sec",
            "range": "stddev: 0.090148",
            "group": "engine",
            "extra": "mean: 1.5323 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.16143635163956654,
            "unit": "iter/sec",
            "range": "stddev: 0.10918",
            "group": "engine",
            "extra": "mean: 6.1944 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.1841044071058166,
            "unit": "iter/sec",
            "range": "stddev: 0.11536",
            "group": "engine",
            "extra": "mean: 5.4317 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 332.47553117595464,
            "unit": "iter/sec",
            "range": "stddev: 0.00079903",
            "group": "node",
            "extra": "mean: 3.0077 msec\nrounds: 232"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 131.47742029448594,
            "unit": "iter/sec",
            "range": "stddev: 0.00077409",
            "group": "node",
            "extra": "mean: 7.6059 msec\nrounds: 112"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 78.01225729524153,
            "unit": "iter/sec",
            "range": "stddev: 0.00098769",
            "group": "node",
            "extra": "mean: 12.818 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 200.9633051436138,
            "unit": "iter/sec",
            "range": "stddev: 0.00041457",
            "group": "node",
            "extra": "mean: 4.9760 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 51.20598641731193,
            "unit": "iter/sec",
            "range": "stddev: 0.0022303",
            "group": "node",
            "extra": "mean: 19.529 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 47.3151883305127,
            "unit": "iter/sec",
            "range": "stddev: 0.0029229",
            "group": "node",
            "extra": "mean: 21.135 msec\nrounds: 100"
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
          "id": "13cadd05f2463b0fd240dde2f979801fbac122f9",
          "message": "CLI: Correct `verdi devel rabbitmq tasks revive` docstring (#6031)",
          "timestamp": "2023-05-21T16:52:07+02:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/13cadd05f2463b0fd240dde2f979801fbac122f9",
          "distinct": true,
          "tree_id": "69b9b2ee0b7d088f9dae44efe1074c2fae78ff87"
        },
        "date": 1684681269042,
        "benches": [
          {
            "name": "tests/benchmark/test_archive.py::test_export[no-objects]",
            "value": 3.7860993319486957,
            "unit": "iter/sec",
            "range": "stddev: 0.0095038",
            "group": "import-export",
            "extra": "mean: 264.12 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_export[with-objects]",
            "value": 3.423911661864771,
            "unit": "iter/sec",
            "range": "stddev: 0.044495",
            "group": "import-export",
            "extra": "mean: 292.06 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[no-objects]",
            "value": 4.392948340190162,
            "unit": "iter/sec",
            "range": "stddev: 0.053187",
            "group": "import-export",
            "extra": "mean: 227.64 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[with-objects]",
            "value": 4.288375987264455,
            "unit": "iter/sec",
            "range": "stddev: 0.054663",
            "group": "import-export",
            "extra": "mean: 233.19 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.6393144838607037,
            "unit": "iter/sec",
            "range": "stddev: 0.014753",
            "group": "engine",
            "extra": "mean: 274.78 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.8176940315640562,
            "unit": "iter/sec",
            "range": "stddev: 0.057189",
            "group": "engine",
            "extra": "mean: 1.2230 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.9242135323107725,
            "unit": "iter/sec",
            "range": "stddev: 0.066886",
            "group": "engine",
            "extra": "mean: 1.0820 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.21096401656729302,
            "unit": "iter/sec",
            "range": "stddev: 0.11169",
            "group": "engine",
            "extra": "mean: 4.7401 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.24146712424510608,
            "unit": "iter/sec",
            "range": "stddev: 0.058427",
            "group": "engine",
            "extra": "mean: 4.1414 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.9215606611856284,
            "unit": "iter/sec",
            "range": "stddev: 0.025393",
            "group": "engine",
            "extra": "mean: 342.28 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.6272958764830879,
            "unit": "iter/sec",
            "range": "stddev: 0.054141",
            "group": "engine",
            "extra": "mean: 1.5941 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.7101743938379566,
            "unit": "iter/sec",
            "range": "stddev: 0.065529",
            "group": "engine",
            "extra": "mean: 1.4081 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.17732485364672662,
            "unit": "iter/sec",
            "range": "stddev: 0.17242",
            "group": "engine",
            "extra": "mean: 5.6394 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.19996196151600765,
            "unit": "iter/sec",
            "range": "stddev: 0.11613",
            "group": "engine",
            "extra": "mean: 5.0010 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 417.30750734465636,
            "unit": "iter/sec",
            "range": "stddev: 0.00059853",
            "group": "node",
            "extra": "mean: 2.3963 msec\nrounds: 298"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 165.52181760218235,
            "unit": "iter/sec",
            "range": "stddev: 0.00025102",
            "group": "node",
            "extra": "mean: 6.0415 msec\nrounds: 141"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 97.50122571717426,
            "unit": "iter/sec",
            "range": "stddev: 0.00038521",
            "group": "node",
            "extra": "mean: 10.256 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 272.1708859093268,
            "unit": "iter/sec",
            "range": "stddev: 0.00026428",
            "group": "node",
            "extra": "mean: 3.6742 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 63.60676725140041,
            "unit": "iter/sec",
            "range": "stddev: 0.0013807",
            "group": "node",
            "extra": "mean: 15.722 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 62.23746177007858,
            "unit": "iter/sec",
            "range": "stddev: 0.0015391",
            "group": "node",
            "extra": "mean: 16.067 msec\nrounds: 100"
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
          "id": "99319b3c175b260ebc813cbec78208deefcdb562",
          "message": "Docs: Add missing `core.` prefix to all `verdi data` subcommands (#6032)\n\nAlso address remaining instances of `List` and `Dict` nodes being constructed\r\nexplicitly using the `list` and `dict` keyword, respectively.\r\n\r\nCo-authored-by: Marnik Bercx <mbercx@gmail.com>\r\nCo-authored-by: Sebastiaan Huber <mail@sphuber.net>",
          "timestamp": "2023-05-22T22:34:34+02:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/99319b3c175b260ebc813cbec78208deefcdb562",
          "distinct": true,
          "tree_id": "0d55168618bc3d651a3286b92ae5a44f35b86e9d"
        },
        "date": 1684788239946,
        "benches": [
          {
            "name": "tests/benchmark/test_archive.py::test_export[no-objects]",
            "value": 3.695937206130504,
            "unit": "iter/sec",
            "range": "stddev: 0.0062497",
            "group": "import-export",
            "extra": "mean: 270.57 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_export[with-objects]",
            "value": 3.3245503330964588,
            "unit": "iter/sec",
            "range": "stddev: 0.066189",
            "group": "import-export",
            "extra": "mean: 300.79 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[no-objects]",
            "value": 4.270958935599444,
            "unit": "iter/sec",
            "range": "stddev: 0.072604",
            "group": "import-export",
            "extra": "mean: 234.14 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[with-objects]",
            "value": 4.1068029311361585,
            "unit": "iter/sec",
            "range": "stddev: 0.077288",
            "group": "import-export",
            "extra": "mean: 243.50 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.499568563038729,
            "unit": "iter/sec",
            "range": "stddev: 0.0099296",
            "group": "engine",
            "extra": "mean: 285.75 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.7471415865028606,
            "unit": "iter/sec",
            "range": "stddev: 0.090478",
            "group": "engine",
            "extra": "mean: 1.3384 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.8440412582546277,
            "unit": "iter/sec",
            "range": "stddev: 0.087592",
            "group": "engine",
            "extra": "mean: 1.1848 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.19212749116379538,
            "unit": "iter/sec",
            "range": "stddev: 0.14467",
            "group": "engine",
            "extra": "mean: 5.2049 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.21996976303072416,
            "unit": "iter/sec",
            "range": "stddev: 0.13392",
            "group": "engine",
            "extra": "mean: 4.5461 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.7326479406692066,
            "unit": "iter/sec",
            "range": "stddev: 0.018407",
            "group": "engine",
            "extra": "mean: 365.95 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.6054775205665717,
            "unit": "iter/sec",
            "range": "stddev: 0.073508",
            "group": "engine",
            "extra": "mean: 1.6516 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.7031433543267561,
            "unit": "iter/sec",
            "range": "stddev: 0.056283",
            "group": "engine",
            "extra": "mean: 1.4222 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.17026970309991052,
            "unit": "iter/sec",
            "range": "stddev: 0.13327",
            "group": "engine",
            "extra": "mean: 5.8730 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.19368555014006925,
            "unit": "iter/sec",
            "range": "stddev: 0.17269",
            "group": "engine",
            "extra": "mean: 5.1630 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 385.9778183779243,
            "unit": "iter/sec",
            "range": "stddev: 0.00037166",
            "group": "node",
            "extra": "mean: 2.5908 msec\nrounds: 236"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 151.62531534740685,
            "unit": "iter/sec",
            "range": "stddev: 0.00032507",
            "group": "node",
            "extra": "mean: 6.5952 msec\nrounds: 128"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 90.33267262295814,
            "unit": "iter/sec",
            "range": "stddev: 0.00061640",
            "group": "node",
            "extra": "mean: 11.070 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 253.80149655554388,
            "unit": "iter/sec",
            "range": "stddev: 0.00029683",
            "group": "node",
            "extra": "mean: 3.9401 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 59.541823264483696,
            "unit": "iter/sec",
            "range": "stddev: 0.0015264",
            "group": "node",
            "extra": "mean: 16.795 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 56.62853436883058,
            "unit": "iter/sec",
            "range": "stddev: 0.0020591",
            "group": "node",
            "extra": "mean: 17.659 msec\nrounds: 100"
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
          "id": "a62c802ae6bb04e1458057dfab640f0fec6a4294",
          "message": "Post release: add the `.post0` qualifier to version attribute",
          "timestamp": "2023-05-22T10:41:47+02:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/a62c802ae6bb04e1458057dfab640f0fec6a4294",
          "distinct": true,
          "tree_id": "031a16bb882f2bf4b5dfbff81fc7ba175d2289c0"
        },
        "date": 1684792178723,
        "benches": [
          {
            "name": "tests/benchmark/test_archive.py::test_export[no-objects]",
            "value": 3.0791559363246623,
            "unit": "iter/sec",
            "range": "stddev: 0.0092387",
            "group": "import-export",
            "extra": "mean: 324.76 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_export[with-objects]",
            "value": 2.7294687374740567,
            "unit": "iter/sec",
            "range": "stddev: 0.070315",
            "group": "import-export",
            "extra": "mean: 366.37 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[no-objects]",
            "value": 3.6196069839183544,
            "unit": "iter/sec",
            "range": "stddev: 0.069331",
            "group": "import-export",
            "extra": "mean: 276.27 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[with-objects]",
            "value": 3.596281183087705,
            "unit": "iter/sec",
            "range": "stddev: 0.074009",
            "group": "import-export",
            "extra": "mean: 278.07 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 2.809770564551573,
            "unit": "iter/sec",
            "range": "stddev: 0.0077406",
            "group": "engine",
            "extra": "mean: 355.90 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.6228298024549552,
            "unit": "iter/sec",
            "range": "stddev: 0.070799",
            "group": "engine",
            "extra": "mean: 1.6056 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.7147163362897427,
            "unit": "iter/sec",
            "range": "stddev: 0.098257",
            "group": "engine",
            "extra": "mean: 1.3992 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.16414093765850993,
            "unit": "iter/sec",
            "range": "stddev: 0.14066",
            "group": "engine",
            "extra": "mean: 6.0923 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.18678104942386797,
            "unit": "iter/sec",
            "range": "stddev: 0.081176",
            "group": "engine",
            "extra": "mean: 5.3539 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.407845746540098,
            "unit": "iter/sec",
            "range": "stddev: 0.028318",
            "group": "engine",
            "extra": "mean: 415.31 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.5312921586172107,
            "unit": "iter/sec",
            "range": "stddev: 0.11432",
            "group": "engine",
            "extra": "mean: 1.8822 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.5928438781917462,
            "unit": "iter/sec",
            "range": "stddev: 0.042998",
            "group": "engine",
            "extra": "mean: 1.6868 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.14418097630148968,
            "unit": "iter/sec",
            "range": "stddev: 0.14189",
            "group": "engine",
            "extra": "mean: 6.9357 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.16502467647701918,
            "unit": "iter/sec",
            "range": "stddev: 0.10225",
            "group": "engine",
            "extra": "mean: 6.0597 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 215.59390779300543,
            "unit": "iter/sec",
            "range": "stddev: 0.018773",
            "group": "node",
            "extra": "mean: 4.6383 msec\nrounds: 195"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 133.8962996654237,
            "unit": "iter/sec",
            "range": "stddev: 0.00021284",
            "group": "node",
            "extra": "mean: 7.4685 msec\nrounds: 115"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 72.75472903913735,
            "unit": "iter/sec",
            "range": "stddev: 0.0011041",
            "group": "node",
            "extra": "mean: 13.745 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 214.31760780752236,
            "unit": "iter/sec",
            "range": "stddev: 0.0010847",
            "group": "node",
            "extra": "mean: 4.6660 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 49.582347434843236,
            "unit": "iter/sec",
            "range": "stddev: 0.0017860",
            "group": "node",
            "extra": "mean: 20.168 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 48.26309951473836,
            "unit": "iter/sec",
            "range": "stddev: 0.0022391",
            "group": "node",
            "extra": "mean: 20.720 msec\nrounds: 100"
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
          "id": "4cfd6d75cf47de92134db89e4ccfb7215cf31626",
          "message": "Post release: add the `.post0` qualifier to version attribute",
          "timestamp": "2023-05-23T07:16:00+02:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/4cfd6d75cf47de92134db89e4ccfb7215cf31626",
          "distinct": true,
          "tree_id": "82127e985a2f88c2387a3bfe436da8c611d4a789"
        },
        "date": 1684860397661,
        "benches": [
          {
            "name": "tests/benchmark/test_archive.py::test_export[no-objects]",
            "value": 3.2068902817007703,
            "unit": "iter/sec",
            "range": "stddev: 0.064406",
            "group": "import-export",
            "extra": "mean: 311.83 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_export[with-objects]",
            "value": 3.1250191041207436,
            "unit": "iter/sec",
            "range": "stddev: 0.066327",
            "group": "import-export",
            "extra": "mean: 320.00 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[no-objects]",
            "value": 4.251200627978051,
            "unit": "iter/sec",
            "range": "stddev: 0.069078",
            "group": "import-export",
            "extra": "mean: 235.23 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[with-objects]",
            "value": 4.153378882747533,
            "unit": "iter/sec",
            "range": "stddev: 0.070675",
            "group": "import-export",
            "extra": "mean: 240.77 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.4384062713784638,
            "unit": "iter/sec",
            "range": "stddev: 0.0089068",
            "group": "engine",
            "extra": "mean: 290.83 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.7556822189351183,
            "unit": "iter/sec",
            "range": "stddev: 0.094084",
            "group": "engine",
            "extra": "mean: 1.3233 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.8557606868833395,
            "unit": "iter/sec",
            "range": "stddev: 0.092778",
            "group": "engine",
            "extra": "mean: 1.1686 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.19235834500600454,
            "unit": "iter/sec",
            "range": "stddev: 0.16410",
            "group": "engine",
            "extra": "mean: 5.1986 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.22593619869058396,
            "unit": "iter/sec",
            "range": "stddev: 0.12464",
            "group": "engine",
            "extra": "mean: 4.4260 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.8707164114174497,
            "unit": "iter/sec",
            "range": "stddev: 0.020311",
            "group": "engine",
            "extra": "mean: 348.35 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.6379710115711614,
            "unit": "iter/sec",
            "range": "stddev: 0.055678",
            "group": "engine",
            "extra": "mean: 1.5675 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.7282293916851156,
            "unit": "iter/sec",
            "range": "stddev: 0.035303",
            "group": "engine",
            "extra": "mean: 1.3732 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.17327667273212327,
            "unit": "iter/sec",
            "range": "stddev: 0.13331",
            "group": "engine",
            "extra": "mean: 5.7711 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.19848194963919324,
            "unit": "iter/sec",
            "range": "stddev: 0.11190",
            "group": "engine",
            "extra": "mean: 5.0382 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 386.3062883357994,
            "unit": "iter/sec",
            "range": "stddev: 0.00026720",
            "group": "node",
            "extra": "mean: 2.5886 msec\nrounds: 235"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 152.61810812551224,
            "unit": "iter/sec",
            "range": "stddev: 0.00021258",
            "group": "node",
            "extra": "mean: 6.5523 msec\nrounds: 127"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 89.36448373220614,
            "unit": "iter/sec",
            "range": "stddev: 0.00065165",
            "group": "node",
            "extra": "mean: 11.190 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 251.91083817403327,
            "unit": "iter/sec",
            "range": "stddev: 0.00034760",
            "group": "node",
            "extra": "mean: 3.9697 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 59.607914872466075,
            "unit": "iter/sec",
            "range": "stddev: 0.0016235",
            "group": "node",
            "extra": "mean: 16.776 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 58.664052702851755,
            "unit": "iter/sec",
            "range": "stddev: 0.0015695",
            "group": "node",
            "extra": "mean: 17.046 msec\nrounds: 100"
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
          "id": "062a5826077907f43165084d4dc02db3f71bfb73",
          "message": "`verdi computer test`: Improve messaging of login shell check (#6026)\n\nThe recently added check for the effect of using a login shell for the\r\ntransport of the computer is improved:\r\n\r\n* The timings are now compared with a relative tolerance as well. Only\r\n  if the timings differ by a factor of two is a warning printed.\r\n* The transport type in the suggested command to change the setting was\r\n  hardcoded to `core.local`. It is now taken from the computer. This\r\n  also allows to actually put dynamically use the correct computer label.\r\n  Now the command can be literally copy-pasted. Note that this required\r\n  adding the `computer` argument to all test functions.\r\n* If the timings are not close, instead of failing the test, it simply\r\n  prints a warning. This is less alarming since really nothing is really\r\n  broken.",
          "timestamp": "2023-05-24T19:23:48+02:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/062a5826077907f43165084d4dc02db3f71bfb73",
          "distinct": true,
          "tree_id": "20a419e82677c0272b1630290b5d51fc478d5561"
        },
        "date": 1684949753758,
        "benches": [
          {
            "name": "tests/benchmark/test_archive.py::test_export[no-objects]",
            "value": 2.6665915701149103,
            "unit": "iter/sec",
            "range": "stddev: 0.014675",
            "group": "import-export",
            "extra": "mean: 375.01 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_export[with-objects]",
            "value": 2.6436812895542983,
            "unit": "iter/sec",
            "range": "stddev: 0.071888",
            "group": "import-export",
            "extra": "mean: 378.26 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[no-objects]",
            "value": 3.658398427287713,
            "unit": "iter/sec",
            "range": "stddev: 0.070326",
            "group": "import-export",
            "extra": "mean: 273.34 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[with-objects]",
            "value": 3.6010211999180757,
            "unit": "iter/sec",
            "range": "stddev: 0.076567",
            "group": "import-export",
            "extra": "mean: 277.70 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 2.6637411224118615,
            "unit": "iter/sec",
            "range": "stddev: 0.012037",
            "group": "engine",
            "extra": "mean: 375.41 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.6042378413513373,
            "unit": "iter/sec",
            "range": "stddev: 0.084196",
            "group": "engine",
            "extra": "mean: 1.6550 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.6982985036809825,
            "unit": "iter/sec",
            "range": "stddev: 0.058171",
            "group": "engine",
            "extra": "mean: 1.4321 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.15580004872895808,
            "unit": "iter/sec",
            "range": "stddev: 0.19012",
            "group": "engine",
            "extra": "mean: 6.4185 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.17159150944288046,
            "unit": "iter/sec",
            "range": "stddev: 0.21904",
            "group": "engine",
            "extra": "mean: 5.8278 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.0828576806711836,
            "unit": "iter/sec",
            "range": "stddev: 0.040983",
            "group": "engine",
            "extra": "mean: 480.11 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.5012961903051764,
            "unit": "iter/sec",
            "range": "stddev: 0.092584",
            "group": "engine",
            "extra": "mean: 1.9948 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.5657361358200464,
            "unit": "iter/sec",
            "range": "stddev: 0.071886",
            "group": "engine",
            "extra": "mean: 1.7676 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.13380781284036988,
            "unit": "iter/sec",
            "range": "stddev: 0.38697",
            "group": "engine",
            "extra": "mean: 7.4734 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.1439026362276159,
            "unit": "iter/sec",
            "range": "stddev: 0.13275",
            "group": "engine",
            "extra": "mean: 6.9491 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 164.06543310769416,
            "unit": "iter/sec",
            "range": "stddev: 0.023682",
            "group": "node",
            "extra": "mean: 6.0951 msec\nrounds: 158"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 100.25878898877298,
            "unit": "iter/sec",
            "range": "stddev: 0.0030411",
            "group": "node",
            "extra": "mean: 9.9742 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 56.71277005025641,
            "unit": "iter/sec",
            "range": "stddev: 0.0020480",
            "group": "node",
            "extra": "mean: 17.633 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 166.128966178951,
            "unit": "iter/sec",
            "range": "stddev: 0.0010825",
            "group": "node",
            "extra": "mean: 6.0194 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 39.64316145381422,
            "unit": "iter/sec",
            "range": "stddev: 0.0026771",
            "group": "node",
            "extra": "mean: 25.225 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 36.82674721288101,
            "unit": "iter/sec",
            "range": "stddev: 0.0035541",
            "group": "node",
            "extra": "mean: 27.154 msec\nrounds: 100"
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
          "id": "ffc869d8f91a860055b12f0d3803615895fa464f",
          "message": "`DirectScheduler`: Add `?` as `JobState.UNDETERMINED` (#6040)\n\nWhen running a process via `engine.run` on a MacOS `localhost` using the\r\n`core.direct` scheduler, warnings are often raised regarding an\r\n\"unrecognised job state `?`'. This is related to the fact that on MacOS the `ps`\r\ncommand is sometimes not able to determine the process state temporarily, and\r\nprints a `?` in the `STAT` column, see:\r\n\r\nhttps://apple.stackexchange.com/q/460394/497071\r\n\r\nHere we simply add the `?` as one of the possible outputs of the `ps` commmand\r\nin the `_MAP_STATUS_PS` dictionary, mapping it to `JobState.UNDETERMINED`.",
          "timestamp": "2023-05-29T16:34:35+02:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/ffc869d8f91a860055b12f0d3803615895fa464f",
          "distinct": true,
          "tree_id": "89d9eb7c41682ca56547187ce885a9543f8dd16f"
        },
        "date": 1685371450473,
        "benches": [
          {
            "name": "tests/benchmark/test_archive.py::test_export[no-objects]",
            "value": 3.3418328535427935,
            "unit": "iter/sec",
            "range": "stddev: 0.015768",
            "group": "import-export",
            "extra": "mean: 299.24 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_export[with-objects]",
            "value": 3.1207879440299533,
            "unit": "iter/sec",
            "range": "stddev: 0.058236",
            "group": "import-export",
            "extra": "mean: 320.43 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[no-objects]",
            "value": 4.242292598299843,
            "unit": "iter/sec",
            "range": "stddev: 0.065127",
            "group": "import-export",
            "extra": "mean: 235.72 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[with-objects]",
            "value": 4.185011428858357,
            "unit": "iter/sec",
            "range": "stddev: 0.066027",
            "group": "import-export",
            "extra": "mean: 238.95 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.2865095779789004,
            "unit": "iter/sec",
            "range": "stddev: 0.010232",
            "group": "engine",
            "extra": "mean: 304.27 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.7002707138037685,
            "unit": "iter/sec",
            "range": "stddev: 0.061307",
            "group": "engine",
            "extra": "mean: 1.4280 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.8273728608501791,
            "unit": "iter/sec",
            "range": "stddev: 0.086946",
            "group": "engine",
            "extra": "mean: 1.2086 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.18824515609091438,
            "unit": "iter/sec",
            "range": "stddev: 0.12682",
            "group": "engine",
            "extra": "mean: 5.3122 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.20963603830349645,
            "unit": "iter/sec",
            "range": "stddev: 0.077823",
            "group": "engine",
            "extra": "mean: 4.7702 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.726820992191374,
            "unit": "iter/sec",
            "range": "stddev: 0.023016",
            "group": "engine",
            "extra": "mean: 366.73 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.6254733693480762,
            "unit": "iter/sec",
            "range": "stddev: 0.045412",
            "group": "engine",
            "extra": "mean: 1.5988 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.698188439222122,
            "unit": "iter/sec",
            "range": "stddev: 0.057614",
            "group": "engine",
            "extra": "mean: 1.4323 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.1685747329415069,
            "unit": "iter/sec",
            "range": "stddev: 0.15527",
            "group": "engine",
            "extra": "mean: 5.9321 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.19153279653657726,
            "unit": "iter/sec",
            "range": "stddev: 0.22253",
            "group": "engine",
            "extra": "mean: 5.2210 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 369.81436453775456,
            "unit": "iter/sec",
            "range": "stddev: 0.00038924",
            "group": "node",
            "extra": "mean: 2.7041 msec\nrounds: 247"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 149.11994775150333,
            "unit": "iter/sec",
            "range": "stddev: 0.00038581",
            "group": "node",
            "extra": "mean: 6.7060 msec\nrounds: 135"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 82.62299316593224,
            "unit": "iter/sec",
            "range": "stddev: 0.00095776",
            "group": "node",
            "extra": "mean: 12.103 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 239.14107718412393,
            "unit": "iter/sec",
            "range": "stddev: 0.00084430",
            "group": "node",
            "extra": "mean: 4.1816 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 56.00172481280161,
            "unit": "iter/sec",
            "range": "stddev: 0.0017888",
            "group": "node",
            "extra": "mean: 17.857 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 53.81193122540941,
            "unit": "iter/sec",
            "range": "stddev: 0.0021560",
            "group": "node",
            "extra": "mean: 18.583 msec\nrounds: 100"
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
          "id": "ad4fbcccb14ac68653a941bf17be2e532ca162bc",
          "message": "Process control: Warn instead of except when daemon is not running (#6047)\n\nThe `play_processes`, `pause_processes` and `kill_processes` methods of\r\nthe `engine.processes.control` module would raise if the daemon is not\r\ncurrently running. This instinctively make sense, because in order to be\r\nable to interact with a process through an RPC call, which is what these\r\nmethods do, it has to be \"live\" with some runner. This normally means a\r\ndaemon worker, so if the daemon is not running, it is to be expected\r\nthat the process cannot be reached. However, runners can also be started\r\nmanually, for example through `verdi daemon worker` or within an\r\ninteractive shell when a process is \"run\" instead of submitted.\r\n\r\nThe `verdi process pause/play/kill` commands actually covered for this\r\ncase and would also check for the daemon to be running, but instead\r\nwould log a warning if not the case. Since they call through to the\r\ncontrol module, an exception would be logged nevertheless.\r\n\r\nThe control module now also logs a warning, instead of raise an\r\nexception. This allows the CLI command to remove the explicit check for\r\nthe daemon running with the `only_if_daemon_running` decorator as it can\r\nrely on the control module performing the check.",
          "timestamp": "2023-06-04T22:07:52+02:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/ad4fbcccb14ac68653a941bf17be2e532ca162bc",
          "distinct": true,
          "tree_id": "eb24dc1f441ba6a7b2aedd2acfa0fae1d0fdee5b"
        },
        "date": 1685909845599,
        "benches": [
          {
            "name": "tests/benchmark/test_archive.py::test_export[no-objects]",
            "value": 3.6220924636372676,
            "unit": "iter/sec",
            "range": "stddev: 0.0054003",
            "group": "import-export",
            "extra": "mean: 276.08 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_export[with-objects]",
            "value": 3.248687307386623,
            "unit": "iter/sec",
            "range": "stddev: 0.068662",
            "group": "import-export",
            "extra": "mean: 307.82 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[no-objects]",
            "value": 4.202953326830717,
            "unit": "iter/sec",
            "range": "stddev: 0.074119",
            "group": "import-export",
            "extra": "mean: 237.93 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[with-objects]",
            "value": 4.099072008526247,
            "unit": "iter/sec",
            "range": "stddev: 0.081022",
            "group": "import-export",
            "extra": "mean: 243.96 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.3341543521718773,
            "unit": "iter/sec",
            "range": "stddev: 0.0050409",
            "group": "engine",
            "extra": "mean: 299.93 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.7148467201708125,
            "unit": "iter/sec",
            "range": "stddev: 0.093088",
            "group": "engine",
            "extra": "mean: 1.3989 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.8284079291966926,
            "unit": "iter/sec",
            "range": "stddev: 0.070953",
            "group": "engine",
            "extra": "mean: 1.2071 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.19193279244979802,
            "unit": "iter/sec",
            "range": "stddev: 0.079108",
            "group": "engine",
            "extra": "mean: 5.2102 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.21657971637724993,
            "unit": "iter/sec",
            "range": "stddev: 0.13507",
            "group": "engine",
            "extra": "mean: 4.6172 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.4094063077692187,
            "unit": "iter/sec",
            "range": "stddev: 0.10173",
            "group": "engine",
            "extra": "mean: 415.04 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.6085612441839046,
            "unit": "iter/sec",
            "range": "stddev: 0.059208",
            "group": "engine",
            "extra": "mean: 1.6432 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.6838689755936681,
            "unit": "iter/sec",
            "range": "stddev: 0.036107",
            "group": "engine",
            "extra": "mean: 1.4623 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.16708849238188006,
            "unit": "iter/sec",
            "range": "stddev: 0.12028",
            "group": "engine",
            "extra": "mean: 5.9849 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.18957847392072216,
            "unit": "iter/sec",
            "range": "stddev: 0.069006",
            "group": "engine",
            "extra": "mean: 5.2749 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 336.2131860572023,
            "unit": "iter/sec",
            "range": "stddev: 0.00029860",
            "group": "node",
            "extra": "mean: 2.9743 msec\nrounds: 201"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 126.9437364037748,
            "unit": "iter/sec",
            "range": "stddev: 0.0013016",
            "group": "node",
            "extra": "mean: 7.8775 msec\nrounds: 118"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 73.16471139369392,
            "unit": "iter/sec",
            "range": "stddev: 0.0015268",
            "group": "node",
            "extra": "mean: 13.668 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 214.07085962088166,
            "unit": "iter/sec",
            "range": "stddev: 0.00014553",
            "group": "node",
            "extra": "mean: 4.6714 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 53.20892785193733,
            "unit": "iter/sec",
            "range": "stddev: 0.0016516",
            "group": "node",
            "extra": "mean: 18.794 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 46.63335895482409,
            "unit": "iter/sec",
            "range": "stddev: 0.027272",
            "group": "node",
            "extra": "mean: 21.444 msec\nrounds: 100"
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
          "id": "1de2ca576c7fbe5c6586f53160304b46c99a3a10",
          "message": "DevOps: Do not assume `pgtest` cluster started in `postgres_cluster` fixture (#6050)\n\nWhen a developer tries to run tests without Posgres installed, in addition\r\nto the original exception coming from the `pgtest` library, one would\r\nalso get a rather unhelpful exception coming from AiiDA fixture which\r\ntries to close the non-existent DB connection in the `finally` clause.",
          "timestamp": "2023-06-06T15:44:50+02:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/1de2ca576c7fbe5c6586f53160304b46c99a3a10",
          "distinct": true,
          "tree_id": "53828c7a9696d44803eb937a03deb3d79832b104"
        },
        "date": 1686059684225,
        "benches": [
          {
            "name": "tests/benchmark/test_archive.py::test_export[no-objects]",
            "value": 3.395510836491748,
            "unit": "iter/sec",
            "range": "stddev: 0.010468",
            "group": "import-export",
            "extra": "mean: 294.51 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_export[with-objects]",
            "value": 3.172647658662524,
            "unit": "iter/sec",
            "range": "stddev: 0.062018",
            "group": "import-export",
            "extra": "mean: 315.19 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[no-objects]",
            "value": 4.164295444543781,
            "unit": "iter/sec",
            "range": "stddev: 0.069062",
            "group": "import-export",
            "extra": "mean: 240.14 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[with-objects]",
            "value": 4.166625069859574,
            "unit": "iter/sec",
            "range": "stddev: 0.067693",
            "group": "import-export",
            "extra": "mean: 240.00 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.2638841155491614,
            "unit": "iter/sec",
            "range": "stddev: 0.0098554",
            "group": "engine",
            "extra": "mean: 306.38 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.6873296905281283,
            "unit": "iter/sec",
            "range": "stddev: 0.087200",
            "group": "engine",
            "extra": "mean: 1.4549 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.8070594681608465,
            "unit": "iter/sec",
            "range": "stddev: 0.068621",
            "group": "engine",
            "extra": "mean: 1.2391 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.185796833774163,
            "unit": "iter/sec",
            "range": "stddev: 0.14576",
            "group": "engine",
            "extra": "mean: 5.3822 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.2106780663313275,
            "unit": "iter/sec",
            "range": "stddev: 0.14001",
            "group": "engine",
            "extra": "mean: 4.7466 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.402111082449411,
            "unit": "iter/sec",
            "range": "stddev: 0.076419",
            "group": "engine",
            "extra": "mean: 416.30 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.5873948402510041,
            "unit": "iter/sec",
            "range": "stddev: 0.057196",
            "group": "engine",
            "extra": "mean: 1.7024 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.6622287417691272,
            "unit": "iter/sec",
            "range": "stddev: 0.065768",
            "group": "engine",
            "extra": "mean: 1.5101 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.15860260884553887,
            "unit": "iter/sec",
            "range": "stddev: 0.21794",
            "group": "engine",
            "extra": "mean: 6.3051 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.18477823438547855,
            "unit": "iter/sec",
            "range": "stddev: 0.21694",
            "group": "engine",
            "extra": "mean: 5.4119 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 339.69475128327474,
            "unit": "iter/sec",
            "range": "stddev: 0.00021959",
            "group": "node",
            "extra": "mean: 2.9438 msec\nrounds: 186"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 132.90831621576172,
            "unit": "iter/sec",
            "range": "stddev: 0.00027529",
            "group": "node",
            "extra": "mean: 7.5240 msec\nrounds: 119"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 72.63053123664064,
            "unit": "iter/sec",
            "range": "stddev: 0.00099263",
            "group": "node",
            "extra": "mean: 13.768 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 221.50790353494233,
            "unit": "iter/sec",
            "range": "stddev: 0.00027348",
            "group": "node",
            "extra": "mean: 4.5145 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 48.66476913225233,
            "unit": "iter/sec",
            "range": "stddev: 0.023402",
            "group": "node",
            "extra": "mean: 20.549 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 55.0313754067582,
            "unit": "iter/sec",
            "range": "stddev: 0.0018810",
            "group": "node",
            "extra": "mean: 18.171 msec\nrounds: 100"
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
          "id": "68cb4579d9e77b32dc6182dc704e6079b6f9c0c2",
          "message": "Process control: Change language when not waiting for response (#6048)\n\nWhen playing, pausing or killing a process with `wait=False`, the\r\nresponse would be like: `played/paused/killed Process<ID>`. This\r\nsuggests to the user that the action was completed, but actually,\r\nwithout waiting, the RPC was simply fire-and-forget and so it may take a\r\nwhile for the action to actually be completed, if at all.\r\n\r\nTherefore the language could be misleading, especially if the daemon is\r\nunder heavy load and cannot execute the RPC relatively quickly. The\r\nlanguage is changed to indicate that a request was sent, which should\r\nconvey that it is not necessarily completed already.",
          "timestamp": "2023-06-07T12:09:36+02:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/68cb4579d9e77b32dc6182dc704e6079b6f9c0c2",
          "distinct": true,
          "tree_id": "2f2f643b1f76459e226ccd6a758fdbb9fe549641"
        },
        "date": 1686133131184,
        "benches": [
          {
            "name": "tests/benchmark/test_archive.py::test_export[no-objects]",
            "value": 3.4579957316115153,
            "unit": "iter/sec",
            "range": "stddev: 0.068880",
            "group": "import-export",
            "extra": "mean: 289.18 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_export[with-objects]",
            "value": 3.3730922224675255,
            "unit": "iter/sec",
            "range": "stddev: 0.053877",
            "group": "import-export",
            "extra": "mean: 296.46 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[no-objects]",
            "value": 4.326915423171275,
            "unit": "iter/sec",
            "range": "stddev: 0.055277",
            "group": "import-export",
            "extra": "mean: 231.11 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[with-objects]",
            "value": 4.252458675305747,
            "unit": "iter/sec",
            "range": "stddev: 0.058117",
            "group": "import-export",
            "extra": "mean: 235.16 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.582990960034961,
            "unit": "iter/sec",
            "range": "stddev: 0.0040050",
            "group": "engine",
            "extra": "mean: 279.10 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.7909579858508428,
            "unit": "iter/sec",
            "range": "stddev: 0.055575",
            "group": "engine",
            "extra": "mean: 1.2643 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.895757737736413,
            "unit": "iter/sec",
            "range": "stddev: 0.048072",
            "group": "engine",
            "extra": "mean: 1.1164 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.20487316550066717,
            "unit": "iter/sec",
            "range": "stddev: 0.11860",
            "group": "engine",
            "extra": "mean: 4.8811 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.2305728034089182,
            "unit": "iter/sec",
            "range": "stddev: 0.091372",
            "group": "engine",
            "extra": "mean: 4.3370 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.721838683729565,
            "unit": "iter/sec",
            "range": "stddev: 0.059489",
            "group": "engine",
            "extra": "mean: 367.40 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.6291890940348492,
            "unit": "iter/sec",
            "range": "stddev: 0.075865",
            "group": "engine",
            "extra": "mean: 1.5893 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.7105900594353171,
            "unit": "iter/sec",
            "range": "stddev: 0.053281",
            "group": "engine",
            "extra": "mean: 1.4073 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.17052354412394752,
            "unit": "iter/sec",
            "range": "stddev: 0.17498",
            "group": "engine",
            "extra": "mean: 5.8643 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.19555106246900733,
            "unit": "iter/sec",
            "range": "stddev: 0.085971",
            "group": "engine",
            "extra": "mean: 5.1138 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 369.63389950664106,
            "unit": "iter/sec",
            "range": "stddev: 0.00021627",
            "group": "node",
            "extra": "mean: 2.7054 msec\nrounds: 251"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 137.53975204944123,
            "unit": "iter/sec",
            "range": "stddev: 0.00042751",
            "group": "node",
            "extra": "mean: 7.2706 msec\nrounds: 123"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 81.49156050258814,
            "unit": "iter/sec",
            "range": "stddev: 0.00070313",
            "group": "node",
            "extra": "mean: 12.271 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 232.7143168192678,
            "unit": "iter/sec",
            "range": "stddev: 0.00020839",
            "group": "node",
            "extra": "mean: 4.2971 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 51.95981988903939,
            "unit": "iter/sec",
            "range": "stddev: 0.019960",
            "group": "node",
            "extra": "mean: 19.246 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 58.12752553416724,
            "unit": "iter/sec",
            "range": "stddev: 0.0016168",
            "group": "node",
            "extra": "mean: 17.204 msec\nrounds: 100"
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
          "id": "bfd63c790a6bd5fdcb60a2d1b840c7b285c53334",
          "message": "Fix log messages being logged twice to the daemon log file (#6051)\n\nIn 276a93f3a60546674d0b18220f6415ed33716c89 the logging configuration\r\nlogic was modified to respect the log level being changed through the\r\n`--verbosity` option when invoking `verdi`. The changes added the `cli`\r\nhandler to all loggers.\r\n\r\nThis code was also being executed when a daemon worker started up and\r\ncalled `aiida.common.log.configure_logging` causing all logging to end\r\nup twice in the daemon log file.\r\n\r\nThe assertion of the `test_duplicate_subscriber_identifier` test is\r\nupdated since the expected error message contained the `Error:` literal\r\nwhich is the log level at which the message is logged and is therefore\r\nformatted based on the loggers formatter, which is configurable. In this\r\ncase, it is actually formatted as `[ERROR]` which was causing the test\r\nto fail.",
          "timestamp": "2023-06-08T15:37:51+02:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/bfd63c790a6bd5fdcb60a2d1b840c7b285c53334",
          "distinct": true,
          "tree_id": "32d5a060ccc3526127d4495dcb2ea036143b5276"
        },
        "date": 1686232059369,
        "benches": [
          {
            "name": "tests/benchmark/test_archive.py::test_export[no-objects]",
            "value": 3.1863327744628926,
            "unit": "iter/sec",
            "range": "stddev: 0.078745",
            "group": "import-export",
            "extra": "mean: 313.84 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_export[with-objects]",
            "value": 3.1655949424080765,
            "unit": "iter/sec",
            "range": "stddev: 0.060681",
            "group": "import-export",
            "extra": "mean: 315.90 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[no-objects]",
            "value": 4.339946293345387,
            "unit": "iter/sec",
            "range": "stddev: 0.071380",
            "group": "import-export",
            "extra": "mean: 230.42 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[with-objects]",
            "value": 4.184896135261599,
            "unit": "iter/sec",
            "range": "stddev: 0.066637",
            "group": "import-export",
            "extra": "mean: 238.95 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.221683785504538,
            "unit": "iter/sec",
            "range": "stddev: 0.075824",
            "group": "engine",
            "extra": "mean: 310.40 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.7602398303626552,
            "unit": "iter/sec",
            "range": "stddev: 0.043800",
            "group": "engine",
            "extra": "mean: 1.3154 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.8815618347162678,
            "unit": "iter/sec",
            "range": "stddev: 0.050820",
            "group": "engine",
            "extra": "mean: 1.1344 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.19268555586027156,
            "unit": "iter/sec",
            "range": "stddev: 0.11664",
            "group": "engine",
            "extra": "mean: 5.1898 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.2156347062524302,
            "unit": "iter/sec",
            "range": "stddev: 0.12317",
            "group": "engine",
            "extra": "mean: 4.6375 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.582009717777799,
            "unit": "iter/sec",
            "range": "stddev: 0.025144",
            "group": "engine",
            "extra": "mean: 387.30 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.616533945901468,
            "unit": "iter/sec",
            "range": "stddev: 0.064033",
            "group": "engine",
            "extra": "mean: 1.6220 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.6952735876019451,
            "unit": "iter/sec",
            "range": "stddev: 0.10010",
            "group": "engine",
            "extra": "mean: 1.4383 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.1694189235657209,
            "unit": "iter/sec",
            "range": "stddev: 0.17142",
            "group": "engine",
            "extra": "mean: 5.9025 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.18197603872295431,
            "unit": "iter/sec",
            "range": "stddev: 0.15982",
            "group": "engine",
            "extra": "mean: 5.4952 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 340.2279667215246,
            "unit": "iter/sec",
            "range": "stddev: 0.00040867",
            "group": "node",
            "extra": "mean: 2.9392 msec\nrounds: 218"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 136.83742649457346,
            "unit": "iter/sec",
            "range": "stddev: 0.00057803",
            "group": "node",
            "extra": "mean: 7.3079 msec\nrounds: 121"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 80.89847463904307,
            "unit": "iter/sec",
            "range": "stddev: 0.0011733",
            "group": "node",
            "extra": "mean: 12.361 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 220.52287734005736,
            "unit": "iter/sec",
            "range": "stddev: 0.00049461",
            "group": "node",
            "extra": "mean: 4.5347 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 56.41043094122203,
            "unit": "iter/sec",
            "range": "stddev: 0.0016410",
            "group": "node",
            "extra": "mean: 17.727 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 52.71270738293973,
            "unit": "iter/sec",
            "range": "stddev: 0.0021440",
            "group": "node",
            "extra": "mean: 18.971 msec\nrounds: 100"
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
          "id": "add474cbb0d67e278803e9340e521ea1046ef35c",
          "message": "CLI: Added `compress` option to `verdi storage maintain` (#5540)\n\nBy default, the disk-object store, which is used by the default storage\r\nbackend `PsqlDosStorage`, does _not_ compress files when joining them\r\ninto pack files during the maintenace operation. This behavior can be\r\ntoggled through a flag in the interface, but this is not exposed in the\r\n`verdi storage maintain` and so AiiDA users currently cannot benefit\r\nfrom file compression.\r\n\r\nMoreover, in the current implementation of the disk-object store, once\r\npacked with or without compression, it cannot be repacked with a\r\ndifferent setting.\r\n\r\nHere the `--compress` option is added to `verdi storage maintain` which\r\ncan change the default behavior of not compressing when packing loose\r\nfiles.\r\n\r\nNote that this is a storage backend dependent option that not all storage\r\nbackends may support, but currently the spread of alternative storage\r\nbackends in the AiiDA ecosystem is very limited and it is unlikely that\r\na fully dynamic interface for `verdi storage maintain` is necessary in\r\nthe near future. If this need arises in the future, the `--compress`\r\noption might have to be deprecated, but this is an acceptable cost to\r\nprevent from having to implement a fully dynamic CLI interface at this\r\npoint in time.",
          "timestamp": "2023-06-11T19:16:01+02:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/add474cbb0d67e278803e9340e521ea1046ef35c",
          "distinct": true,
          "tree_id": "f1e3c283009ad7b6190d5d2049fdc0d1e8638806"
        },
        "date": 1686504309749,
        "benches": [
          {
            "name": "tests/benchmark/test_archive.py::test_export[no-objects]",
            "value": 3.7634168763572786,
            "unit": "iter/sec",
            "range": "stddev: 0.057707",
            "group": "import-export",
            "extra": "mean: 265.72 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_export[with-objects]",
            "value": 3.663581567274809,
            "unit": "iter/sec",
            "range": "stddev: 0.045558",
            "group": "import-export",
            "extra": "mean: 272.96 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[no-objects]",
            "value": 4.3933815875251465,
            "unit": "iter/sec",
            "range": "stddev: 0.052197",
            "group": "import-export",
            "extra": "mean: 227.62 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[with-objects]",
            "value": 4.350201396216837,
            "unit": "iter/sec",
            "range": "stddev: 0.058709",
            "group": "import-export",
            "extra": "mean: 229.87 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.6615939734663567,
            "unit": "iter/sec",
            "range": "stddev: 0.0060833",
            "group": "engine",
            "extra": "mean: 273.11 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.8330502142759224,
            "unit": "iter/sec",
            "range": "stddev: 0.063166",
            "group": "engine",
            "extra": "mean: 1.2004 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.9403905747232355,
            "unit": "iter/sec",
            "range": "stddev: 0.077064",
            "group": "engine",
            "extra": "mean: 1.0634 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.20836971194150417,
            "unit": "iter/sec",
            "range": "stddev: 0.13991",
            "group": "engine",
            "extra": "mean: 4.7992 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.2348570356401549,
            "unit": "iter/sec",
            "range": "stddev: 0.10289",
            "group": "engine",
            "extra": "mean: 4.2579 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.7665424775985725,
            "unit": "iter/sec",
            "range": "stddev: 0.055993",
            "group": "engine",
            "extra": "mean: 361.46 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.6429733580136441,
            "unit": "iter/sec",
            "range": "stddev: 0.10192",
            "group": "engine",
            "extra": "mean: 1.5553 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.7333107395845644,
            "unit": "iter/sec",
            "range": "stddev: 0.055512",
            "group": "engine",
            "extra": "mean: 1.3637 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.17737693097673612,
            "unit": "iter/sec",
            "range": "stddev: 0.14026",
            "group": "engine",
            "extra": "mean: 5.6377 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.2063069244723492,
            "unit": "iter/sec",
            "range": "stddev: 0.081438",
            "group": "engine",
            "extra": "mean: 4.8471 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 364.399763874139,
            "unit": "iter/sec",
            "range": "stddev: 0.00079994",
            "group": "node",
            "extra": "mean: 2.7442 msec\nrounds: 259"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 140.19226715220225,
            "unit": "iter/sec",
            "range": "stddev: 0.00086806",
            "group": "node",
            "extra": "mean: 7.1331 msec\nrounds: 126"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 84.37678994546692,
            "unit": "iter/sec",
            "range": "stddev: 0.00061010",
            "group": "node",
            "extra": "mean: 11.852 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 236.25105839589366,
            "unit": "iter/sec",
            "range": "stddev: 0.00039705",
            "group": "node",
            "extra": "mean: 4.2328 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 54.968738195681865,
            "unit": "iter/sec",
            "range": "stddev: 0.018131",
            "group": "node",
            "extra": "mean: 18.192 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 62.40645973757796,
            "unit": "iter/sec",
            "range": "stddev: 0.0014743",
            "group": "node",
            "extra": "mean: 16.024 msec\nrounds: 100"
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
          "pythonVersion": "3.10.12",
          "metadata": "postgres:12.14, rabbitmq:3.8.14-management"
        },
        "commit": {
          "id": "39763444499eac6fbe76e337fe7e7ca21d675a07",
          "message": "DevOps: Update requirement `pylint~=2.17.4` (#6054)",
          "timestamp": "2023-06-15T09:17:10-07:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/39763444499eac6fbe76e337fe7e7ca21d675a07",
          "distinct": true,
          "tree_id": "f8a770ce048f96a772957d14c9c35bd104a52343"
        },
        "date": 1686846491041,
        "benches": [
          {
            "name": "tests/benchmark/test_archive.py::test_export[no-objects]",
            "value": 2.7906922552837274,
            "unit": "iter/sec",
            "range": "stddev: 0.11374",
            "group": "import-export",
            "extra": "mean: 358.33 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_export[with-objects]",
            "value": 2.753502105212484,
            "unit": "iter/sec",
            "range": "stddev: 0.097139",
            "group": "import-export",
            "extra": "mean: 363.17 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[no-objects]",
            "value": 3.6101991349470515,
            "unit": "iter/sec",
            "range": "stddev: 0.12988",
            "group": "import-export",
            "extra": "mean: 276.99 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[with-objects]",
            "value": 3.612181781440533,
            "unit": "iter/sec",
            "range": "stddev: 0.11240",
            "group": "import-export",
            "extra": "mean: 276.84 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 2.6703063683031254,
            "unit": "iter/sec",
            "range": "stddev: 0.12054",
            "group": "engine",
            "extra": "mean: 374.49 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.6280923940199308,
            "unit": "iter/sec",
            "range": "stddev: 0.084687",
            "group": "engine",
            "extra": "mean: 1.5921 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.7666013987883009,
            "unit": "iter/sec",
            "range": "stddev: 0.031142",
            "group": "engine",
            "extra": "mean: 1.3045 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.16817746462125133,
            "unit": "iter/sec",
            "range": "stddev: 0.20053",
            "group": "engine",
            "extra": "mean: 5.9461 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.18186300495153215,
            "unit": "iter/sec",
            "range": "stddev: 0.30096",
            "group": "engine",
            "extra": "mean: 5.4986 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.2866568880193485,
            "unit": "iter/sec",
            "range": "stddev: 0.046962",
            "group": "engine",
            "extra": "mean: 437.32 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.5229644935327492,
            "unit": "iter/sec",
            "range": "stddev: 0.088148",
            "group": "engine",
            "extra": "mean: 1.9122 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.5816623750185755,
            "unit": "iter/sec",
            "range": "stddev: 0.17815",
            "group": "engine",
            "extra": "mean: 1.7192 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.14641597761680425,
            "unit": "iter/sec",
            "range": "stddev: 0.22367",
            "group": "engine",
            "extra": "mean: 6.8299 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.16828583793538274,
            "unit": "iter/sec",
            "range": "stddev: 0.21791",
            "group": "engine",
            "extra": "mean: 5.9423 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 344.1505968317167,
            "unit": "iter/sec",
            "range": "stddev: 0.00035983",
            "group": "node",
            "extra": "mean: 2.9057 msec\nrounds: 169"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 133.39015391600185,
            "unit": "iter/sec",
            "range": "stddev: 0.00075662",
            "group": "node",
            "extra": "mean: 7.4968 msec\nrounds: 108"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 67.65800867922182,
            "unit": "iter/sec",
            "range": "stddev: 0.0026007",
            "group": "node",
            "extra": "mean: 14.780 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 219.9728357306749,
            "unit": "iter/sec",
            "range": "stddev: 0.00032246",
            "group": "node",
            "extra": "mean: 4.5460 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 47.17735511335307,
            "unit": "iter/sec",
            "range": "stddev: 0.0025578",
            "group": "node",
            "extra": "mean: 21.197 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 37.585236772461315,
            "unit": "iter/sec",
            "range": "stddev: 0.039946",
            "group": "node",
            "extra": "mean: 26.606 msec\nrounds: 100"
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
          "pythonVersion": "3.10.12",
          "metadata": "postgres:12.14, rabbitmq:3.8.14-management"
        },
        "commit": {
          "id": "afed5dc4630b25b72b2c5a27d542222c086067a7",
          "message": "🔧 Add types for `DefaultFieldsAttributeDict` subclasses (#6059)\n\nImproves type checking and LSP completion.",
          "timestamp": "2023-06-17T20:35:28+02:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/afed5dc4630b25b72b2c5a27d542222c086067a7",
          "distinct": true,
          "tree_id": "0f52f48b945add072e1588356bc7737c1bb571df"
        },
        "date": 1687027473508,
        "benches": [
          {
            "name": "tests/benchmark/test_archive.py::test_export[no-objects]",
            "value": 3.39452092612041,
            "unit": "iter/sec",
            "range": "stddev: 0.047557",
            "group": "import-export",
            "extra": "mean: 294.59 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_export[with-objects]",
            "value": 3.4132948180179765,
            "unit": "iter/sec",
            "range": "stddev: 0.050015",
            "group": "import-export",
            "extra": "mean: 292.97 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[no-objects]",
            "value": 4.378050742277342,
            "unit": "iter/sec",
            "range": "stddev: 0.054670",
            "group": "import-export",
            "extra": "mean: 228.41 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[with-objects]",
            "value": 4.32346415438234,
            "unit": "iter/sec",
            "range": "stddev: 0.052354",
            "group": "import-export",
            "extra": "mean: 231.30 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.360765515760825,
            "unit": "iter/sec",
            "range": "stddev: 0.059887",
            "group": "engine",
            "extra": "mean: 297.55 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.814120598211896,
            "unit": "iter/sec",
            "range": "stddev: 0.030532",
            "group": "engine",
            "extra": "mean: 1.2283 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.9571541586571722,
            "unit": "iter/sec",
            "range": "stddev: 0.026731",
            "group": "engine",
            "extra": "mean: 1.0448 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.20809819368547233,
            "unit": "iter/sec",
            "range": "stddev: 0.077365",
            "group": "engine",
            "extra": "mean: 4.8054 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.23519852332680616,
            "unit": "iter/sec",
            "range": "stddev: 0.067232",
            "group": "engine",
            "extra": "mean: 4.2517 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.9335226631988376,
            "unit": "iter/sec",
            "range": "stddev: 0.022891",
            "group": "engine",
            "extra": "mean: 340.89 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.6398804677076843,
            "unit": "iter/sec",
            "range": "stddev: 0.043117",
            "group": "engine",
            "extra": "mean: 1.5628 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.7150754969887912,
            "unit": "iter/sec",
            "range": "stddev: 0.10331",
            "group": "engine",
            "extra": "mean: 1.3985 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.17868951736416414,
            "unit": "iter/sec",
            "range": "stddev: 0.071569",
            "group": "engine",
            "extra": "mean: 5.5963 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.20298546663385422,
            "unit": "iter/sec",
            "range": "stddev: 0.089008",
            "group": "engine",
            "extra": "mean: 4.9265 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 404.18959647362686,
            "unit": "iter/sec",
            "range": "stddev: 0.00028042",
            "group": "node",
            "extra": "mean: 2.4741 msec\nrounds: 277"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 154.76827126243896,
            "unit": "iter/sec",
            "range": "stddev: 0.00018684",
            "group": "node",
            "extra": "mean: 6.4613 msec\nrounds: 133"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 90.207575379828,
            "unit": "iter/sec",
            "range": "stddev: 0.00064946",
            "group": "node",
            "extra": "mean: 11.086 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 259.2986545996028,
            "unit": "iter/sec",
            "range": "stddev: 0.00019076",
            "group": "node",
            "extra": "mean: 3.8566 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 62.792981021380925,
            "unit": "iter/sec",
            "range": "stddev: 0.0012666",
            "group": "node",
            "extra": "mean: 15.925 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 54.25183201086428,
            "unit": "iter/sec",
            "range": "stddev: 0.018335",
            "group": "node",
            "extra": "mean: 18.433 msec\nrounds: 100"
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
          "pythonVersion": "3.10.12",
          "metadata": "postgres:12.14, rabbitmq:3.8.14-management"
        },
        "commit": {
          "id": "603ff37a0b6ecd3f5309c8148054b2ac5d022833",
          "message": "`QueryBuilder`: Deprecate `debug` argument and use logger (#6055)\n\nThe `QueryBuilder` defined the `debug` flag, which when set to `True`\r\nwould cause certain methods to print additional debug information. This\r\nshould go through the logging functionality, however, so the print\r\nstatements are replaced by a `logger.debug` call.\r\n\r\nSince the debug messages can now be activated by configuring the logger\r\nlog level, the `debug` argument is no longer needed and is deprecated.",
          "timestamp": "2023-06-17T20:35:47+02:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/603ff37a0b6ecd3f5309c8148054b2ac5d022833",
          "distinct": true,
          "tree_id": "5b5d584ddf26bc200b4a30e0adb3002f3f36567a"
        },
        "date": 1687027501105,
        "benches": [
          {
            "name": "tests/benchmark/test_archive.py::test_export[no-objects]",
            "value": 3.5822884793913023,
            "unit": "iter/sec",
            "range": "stddev: 0.063827",
            "group": "import-export",
            "extra": "mean: 279.15 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_export[with-objects]",
            "value": 3.425897835387649,
            "unit": "iter/sec",
            "range": "stddev: 0.061286",
            "group": "import-export",
            "extra": "mean: 291.89 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[no-objects]",
            "value": 4.377668467323289,
            "unit": "iter/sec",
            "range": "stddev: 0.062158",
            "group": "import-export",
            "extra": "mean: 228.43 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[with-objects]",
            "value": 4.33466590933126,
            "unit": "iter/sec",
            "range": "stddev: 0.059138",
            "group": "import-export",
            "extra": "mean: 230.70 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.320085556719079,
            "unit": "iter/sec",
            "range": "stddev: 0.067373",
            "group": "engine",
            "extra": "mean: 301.20 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.782231136442038,
            "unit": "iter/sec",
            "range": "stddev: 0.030825",
            "group": "engine",
            "extra": "mean: 1.2784 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.910138115661579,
            "unit": "iter/sec",
            "range": "stddev: 0.032130",
            "group": "engine",
            "extra": "mean: 1.0987 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.20029063385935963,
            "unit": "iter/sec",
            "range": "stddev: 0.095820",
            "group": "engine",
            "extra": "mean: 4.9927 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.2256721119063918,
            "unit": "iter/sec",
            "range": "stddev: 0.10457",
            "group": "engine",
            "extra": "mean: 4.4312 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.7925806255489327,
            "unit": "iter/sec",
            "range": "stddev: 0.028481",
            "group": "engine",
            "extra": "mean: 358.09 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.633121383541011,
            "unit": "iter/sec",
            "range": "stddev: 0.064465",
            "group": "engine",
            "extra": "mean: 1.5795 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.7084534133589835,
            "unit": "iter/sec",
            "range": "stddev: 0.098914",
            "group": "engine",
            "extra": "mean: 1.4115 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.17455326588814293,
            "unit": "iter/sec",
            "range": "stddev: 0.10379",
            "group": "engine",
            "extra": "mean: 5.7289 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.19784367558920787,
            "unit": "iter/sec",
            "range": "stddev: 0.10200",
            "group": "engine",
            "extra": "mean: 5.0545 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 358.48366049399266,
            "unit": "iter/sec",
            "range": "stddev: 0.00018341",
            "group": "node",
            "extra": "mean: 2.7895 msec\nrounds: 239"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 143.31732434388135,
            "unit": "iter/sec",
            "range": "stddev: 0.00026784",
            "group": "node",
            "extra": "mean: 6.9775 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 86.59963665427865,
            "unit": "iter/sec",
            "range": "stddev: 0.00047238",
            "group": "node",
            "extra": "mean: 11.547 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 242.12807429801626,
            "unit": "iter/sec",
            "range": "stddev: 0.00011452",
            "group": "node",
            "extra": "mean: 4.1300 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 59.19354642503134,
            "unit": "iter/sec",
            "range": "stddev: 0.0013768",
            "group": "node",
            "extra": "mean: 16.894 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 51.03785477689631,
            "unit": "iter/sec",
            "range": "stddev: 0.021534",
            "group": "node",
            "extra": "mean: 19.593 msec\nrounds: 100"
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
          "pythonVersion": "3.10.12",
          "metadata": "postgres:12.14, rabbitmq:3.8.14-management"
        },
        "commit": {
          "id": "226159fd96c01782f4e1b4b52db945e3aef76285",
          "message": "Config: Add option to change recursion limit in daemon workers (#6044)\n\nAdd the `daemon.recursion_limit` config option which is used by a daemon\r\nworker to set the recursion limit using `sys.setrecursionlimit`. This is\r\nto help with the current problem where heavy workloads with many process\r\nfunctions can create deep stacks which would result in `RecursionError`\r\nexceptions being thrown. The default is set to 3000, increased from the\r\nbuilt-in default of 1000. This value has precedent as it is also used by\r\n`jedi` which is used for `ipython`.",
          "timestamp": "2023-06-17T23:40:58+02:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/226159fd96c01782f4e1b4b52db945e3aef76285",
          "distinct": true,
          "tree_id": "e38095ba04b0eae394d3a477aeb18d320e3d0e74"
        },
        "date": 1687038623211,
        "benches": [
          {
            "name": "tests/benchmark/test_archive.py::test_export[no-objects]",
            "value": 3.4370422184671003,
            "unit": "iter/sec",
            "range": "stddev: 0.055540",
            "group": "import-export",
            "extra": "mean: 290.95 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_export[with-objects]",
            "value": 3.292281176080931,
            "unit": "iter/sec",
            "range": "stddev: 0.060010",
            "group": "import-export",
            "extra": "mean: 303.74 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[no-objects]",
            "value": 4.247597055145963,
            "unit": "iter/sec",
            "range": "stddev: 0.063510",
            "group": "import-export",
            "extra": "mean: 235.43 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[with-objects]",
            "value": 4.23416319158781,
            "unit": "iter/sec",
            "range": "stddev: 0.056811",
            "group": "import-export",
            "extra": "mean: 236.17 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.2443172174633164,
            "unit": "iter/sec",
            "range": "stddev: 0.069397",
            "group": "engine",
            "extra": "mean: 308.23 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.7733547514983494,
            "unit": "iter/sec",
            "range": "stddev: 0.040969",
            "group": "engine",
            "extra": "mean: 1.2931 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.8834582826051682,
            "unit": "iter/sec",
            "range": "stddev: 0.032366",
            "group": "engine",
            "extra": "mean: 1.1319 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.19812969123935423,
            "unit": "iter/sec",
            "range": "stddev: 0.10043",
            "group": "engine",
            "extra": "mean: 5.0472 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.223780030588149,
            "unit": "iter/sec",
            "range": "stddev: 0.12482",
            "group": "engine",
            "extra": "mean: 4.4687 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.724305383386501,
            "unit": "iter/sec",
            "range": "stddev: 0.026229",
            "group": "engine",
            "extra": "mean: 367.07 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.6294355588573235,
            "unit": "iter/sec",
            "range": "stddev: 0.083556",
            "group": "engine",
            "extra": "mean: 1.5887 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.7267319410886467,
            "unit": "iter/sec",
            "range": "stddev: 0.043001",
            "group": "engine",
            "extra": "mean: 1.3760 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.17132270787322434,
            "unit": "iter/sec",
            "range": "stddev: 0.12334",
            "group": "engine",
            "extra": "mean: 5.8369 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.19538611767300376,
            "unit": "iter/sec",
            "range": "stddev: 0.11801",
            "group": "engine",
            "extra": "mean: 5.1181 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 366.8938551152288,
            "unit": "iter/sec",
            "range": "stddev: 0.00035106",
            "group": "node",
            "extra": "mean: 2.7256 msec\nrounds: 225"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 146.33480870852196,
            "unit": "iter/sec",
            "range": "stddev: 0.00029342",
            "group": "node",
            "extra": "mean: 6.8336 msec\nrounds: 129"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 84.51558108882398,
            "unit": "iter/sec",
            "range": "stddev: 0.00064576",
            "group": "node",
            "extra": "mean: 11.832 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 243.89337451911072,
            "unit": "iter/sec",
            "range": "stddev: 0.00033120",
            "group": "node",
            "extra": "mean: 4.1002 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 58.39611771491308,
            "unit": "iter/sec",
            "range": "stddev: 0.0014026",
            "group": "node",
            "extra": "mean: 17.124 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 55.36274903048766,
            "unit": "iter/sec",
            "range": "stddev: 0.0023324",
            "group": "node",
            "extra": "mean: 18.063 msec\nrounds: 100"
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
          "pythonVersion": "3.10.12",
          "metadata": "postgres:12.14, rabbitmq:3.8.14-management"
        },
        "commit": {
          "id": "bd9372a5f4ce6681b16ef806338512c0fb02e25e",
          "message": "`verdi process status`: Add `call_link_label` to stack entries (#6056)\n\nThe `metadata.call_link_label` input can be set to define a custom link\r\nlabel for call links when launching a subprocess, instead of the `CALL`\r\ndefault. The `aiida.cmdline.utils.ascii_vis.calc_info` function, which\r\nis called by `verdi process status` to produce a visual representation\r\nof the call stack of a process, is updated to include this call link\r\nlabel.",
          "timestamp": "2023-06-19T20:24:08+02:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/bd9372a5f4ce6681b16ef806338512c0fb02e25e",
          "distinct": true,
          "tree_id": "768f7f8402f6eca3bf76b75d0d84e5ac2ce2fc05"
        },
        "date": 1687199597193,
        "benches": [
          {
            "name": "tests/benchmark/test_archive.py::test_export[no-objects]",
            "value": 3.4600958786974516,
            "unit": "iter/sec",
            "range": "stddev: 0.011311",
            "group": "import-export",
            "extra": "mean: 289.01 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_export[with-objects]",
            "value": 3.360236176619039,
            "unit": "iter/sec",
            "range": "stddev: 0.045040",
            "group": "import-export",
            "extra": "mean: 297.60 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[no-objects]",
            "value": 4.33548626728873,
            "unit": "iter/sec",
            "range": "stddev: 0.052579",
            "group": "import-export",
            "extra": "mean: 230.65 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[with-objects]",
            "value": 4.266520200251593,
            "unit": "iter/sec",
            "range": "stddev: 0.057264",
            "group": "import-export",
            "extra": "mean: 234.38 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.5865143396844674,
            "unit": "iter/sec",
            "range": "stddev: 0.0090900",
            "group": "engine",
            "extra": "mean: 278.82 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.783977586399409,
            "unit": "iter/sec",
            "range": "stddev: 0.067423",
            "group": "engine",
            "extra": "mean: 1.2755 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.8853881656849615,
            "unit": "iter/sec",
            "range": "stddev: 0.074728",
            "group": "engine",
            "extra": "mean: 1.1294 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.2030897116441895,
            "unit": "iter/sec",
            "range": "stddev: 0.11558",
            "group": "engine",
            "extra": "mean: 4.9239 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.2328754976543188,
            "unit": "iter/sec",
            "range": "stddev: 0.081026",
            "group": "engine",
            "extra": "mean: 4.2941 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.7355778982511363,
            "unit": "iter/sec",
            "range": "stddev: 0.067748",
            "group": "engine",
            "extra": "mean: 365.55 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.6213060151846564,
            "unit": "iter/sec",
            "range": "stddev: 0.069989",
            "group": "engine",
            "extra": "mean: 1.6095 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.7205554696458443,
            "unit": "iter/sec",
            "range": "stddev: 0.035931",
            "group": "engine",
            "extra": "mean: 1.3878 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.17279768657528238,
            "unit": "iter/sec",
            "range": "stddev: 0.15286",
            "group": "engine",
            "extra": "mean: 5.7871 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.1965070119132822,
            "unit": "iter/sec",
            "range": "stddev: 0.083471",
            "group": "engine",
            "extra": "mean: 5.0889 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 347.19441245676006,
            "unit": "iter/sec",
            "range": "stddev: 0.00040190",
            "group": "node",
            "extra": "mean: 2.8802 msec\nrounds: 253"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 140.39157086202425,
            "unit": "iter/sec",
            "range": "stddev: 0.00039611",
            "group": "node",
            "extra": "mean: 7.1229 msec\nrounds: 108"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 81.87605486551038,
            "unit": "iter/sec",
            "range": "stddev: 0.00091462",
            "group": "node",
            "extra": "mean: 12.214 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 234.78939668147868,
            "unit": "iter/sec",
            "range": "stddev: 0.00033201",
            "group": "node",
            "extra": "mean: 4.2591 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 53.72411532769219,
            "unit": "iter/sec",
            "range": "stddev: 0.018900",
            "group": "node",
            "extra": "mean: 18.614 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 58.230552249942775,
            "unit": "iter/sec",
            "range": "stddev: 0.0016671",
            "group": "node",
            "extra": "mean: 17.173 msec\nrounds: 100"
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
          "pythonVersion": "3.10.12",
          "metadata": "postgres:12.14, rabbitmq:3.8.14-management"
        },
        "commit": {
          "id": "3defb8bb70fab87c5a4375e34dc07144077036fd",
          "message": "Dependencies: Drop support for Python 3.8\n\nAccording to AEP 003, the support for Python versions follows the\nsame timeline as that of numpy, defined in NEP 029. According to that\nschema, Python 3.8 is no longer support as of April 14 2023 and so\nofficial support is also dropped in `aiida-core`.",
          "timestamp": "2023-06-19T21:05:07+02:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/3defb8bb70fab87c5a4375e34dc07144077036fd",
          "distinct": true,
          "tree_id": "c94a1d855510b6fbb3546308f6712b56973f2423"
        },
        "date": 1687202189517,
        "benches": [
          {
            "name": "tests/benchmark/test_archive.py::test_export[no-objects]",
            "value": 2.681042311277006,
            "unit": "iter/sec",
            "range": "stddev: 0.065263",
            "group": "import-export",
            "extra": "mean: 372.99 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_export[with-objects]",
            "value": 2.6202397798497996,
            "unit": "iter/sec",
            "range": "stddev: 0.069775",
            "group": "import-export",
            "extra": "mean: 381.64 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[no-objects]",
            "value": 3.4942969151996803,
            "unit": "iter/sec",
            "range": "stddev: 0.084643",
            "group": "import-export",
            "extra": "mean: 286.18 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[with-objects]",
            "value": 3.4319980678193676,
            "unit": "iter/sec",
            "range": "stddev: 0.081249",
            "group": "import-export",
            "extra": "mean: 291.38 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 2.551647068598962,
            "unit": "iter/sec",
            "range": "stddev: 0.074026",
            "group": "engine",
            "extra": "mean: 391.90 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.6047132120814974,
            "unit": "iter/sec",
            "range": "stddev: 0.044687",
            "group": "engine",
            "extra": "mean: 1.6537 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.7111014444296835,
            "unit": "iter/sec",
            "range": "stddev: 0.075963",
            "group": "engine",
            "extra": "mean: 1.4063 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.15929796689411618,
            "unit": "iter/sec",
            "range": "stddev: 0.13248",
            "group": "engine",
            "extra": "mean: 6.2775 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.17774852897767698,
            "unit": "iter/sec",
            "range": "stddev: 0.19363",
            "group": "engine",
            "extra": "mean: 5.6259 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.274176569274747,
            "unit": "iter/sec",
            "range": "stddev: 0.029952",
            "group": "engine",
            "extra": "mean: 439.72 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.5158133152407627,
            "unit": "iter/sec",
            "range": "stddev: 0.072622",
            "group": "engine",
            "extra": "mean: 1.9387 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.5854103215407798,
            "unit": "iter/sec",
            "range": "stddev: 0.070861",
            "group": "engine",
            "extra": "mean: 1.7082 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.14045008649578014,
            "unit": "iter/sec",
            "range": "stddev: 0.14092",
            "group": "engine",
            "extra": "mean: 7.1200 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.15895888597313437,
            "unit": "iter/sec",
            "range": "stddev: 0.22766",
            "group": "engine",
            "extra": "mean: 6.2909 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 325.85512811096845,
            "unit": "iter/sec",
            "range": "stddev: 0.00018748",
            "group": "node",
            "extra": "mean: 3.0688 msec\nrounds: 216"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 121.77019939690614,
            "unit": "iter/sec",
            "range": "stddev: 0.00058382",
            "group": "node",
            "extra": "mean: 8.2122 msec\nrounds: 106"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 67.50705583916162,
            "unit": "iter/sec",
            "range": "stddev: 0.0010505",
            "group": "node",
            "extra": "mean: 14.813 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 202.61091680899747,
            "unit": "iter/sec",
            "range": "stddev: 0.00056020",
            "group": "node",
            "extra": "mean: 4.9356 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 47.74724766027283,
            "unit": "iter/sec",
            "range": "stddev: 0.0020963",
            "group": "node",
            "extra": "mean: 20.944 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 46.10976653648734,
            "unit": "iter/sec",
            "range": "stddev: 0.0025008",
            "group": "node",
            "extra": "mean: 21.687 msec\nrounds: 100"
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
          "pythonVersion": "3.10.12",
          "metadata": "postgres:12.14, rabbitmq:3.8.14-management"
        },
        "commit": {
          "id": "f797b476622d9b2724d1460bbe55ef989166f57d",
          "message": "Engine: Dynamically update maximum stack size close to overflow (#6052)\n\nThe Python interpreter maintains a stack of frames when executing code\r\nwhich has a limit. As soon as a frame is added to the stack that were to\r\nexceed this limit a `RecursionError` is raised. Note that, unlike the\r\nname suggests, the cause doesn't need to involve recursion necessarily\r\nalthough that is a common cause for the problem. Simply creating a deep\r\nbut non-recursive call stack will have the same effect.\r\n\r\nThis `RecursionError` was routinely hit when submitting large numbers of\r\nworkflows to the daemon that call one or more process functions. This is\r\ndue to the process function being called synchronously in an async\r\ncontext, namely the workchain, which is being executed as a task on the\r\nevent loop of the `Runner` in the daemon worker. To make this possible,\r\nthe event loop has to be made reentrant, but this is not supported by\r\nvanilla `asyncio`. This blockade is circumvented in `plumpy` through the\r\nuse of `nest-asyncio` which makes a running event loop reentrant.\r\n\r\nThe problem is that when the event loop is reentered, instead of\r\ncreating a separate stack for that task, it reuses the current one.\r\nConsequently, each process function adds frames to the current stack\r\nthat are not resolved and removed until after the execution finished. If\r\nmany process functions are started before they are finished, these\r\nframes accumulate and can ultimately hit the stack limit. Since the task\r\nqueue of the event loop uses a FIFO, it would very often lead to this\r\nsituation because all process function tasks would be created first,\r\nbefore being finalized.\r\n\r\nSince an actual solution for this problem is not trivial and this is\r\ncausing a lot problems, a temporary workaround is implemented. Each time\r\nwhen a process function is executed, the current stack size is compared\r\nto the current stack limit. If the stack is more than 80% filled, the\r\nlimit is increased by a 1000 and a warning message is logged. This\r\nshould give some more leeway for the created process function tasks to\r\nbe resolved.\r\n\r\nNote that the workaround will keep increasing the limit if necessary\r\nwhich can and will eventually lead to an actual stack overflow in the\r\ninterpreter. When this happens will be machine dependent so it is\r\ndifficult to put an absolute limit.\r\n\r\nThe function to get the stack size is using a custom implementation\r\ninstead of the naive `len(inspect.stack())`. This is because the\r\nperformance is three order of magnitudes better and it scales well for\r\ndeep stacks, which is typically the case for AiiDA daemon workers. See\r\nhttps://stackoverflow.com/questions/34115298 for a discussion on the\r\nimplementation and its performance.",
          "timestamp": "2023-06-20T10:45:16+02:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/f797b476622d9b2724d1460bbe55ef989166f57d",
          "distinct": true,
          "tree_id": "2ca938663890812e3b2a5b2cc94340ff3a8c4648"
        },
        "date": 1687251366120,
        "benches": [
          {
            "name": "tests/benchmark/test_archive.py::test_export[no-objects]",
            "value": 2.8529387808201925,
            "unit": "iter/sec",
            "range": "stddev: 0.063142",
            "group": "import-export",
            "extra": "mean: 350.52 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_export[with-objects]",
            "value": 2.7474118210133973,
            "unit": "iter/sec",
            "range": "stddev: 0.069376",
            "group": "import-export",
            "extra": "mean: 363.98 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[no-objects]",
            "value": 3.7212359531500288,
            "unit": "iter/sec",
            "range": "stddev: 0.078112",
            "group": "import-export",
            "extra": "mean: 268.73 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[with-objects]",
            "value": 3.5514307849415507,
            "unit": "iter/sec",
            "range": "stddev: 0.076864",
            "group": "import-export",
            "extra": "mean: 281.58 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 2.601738898730718,
            "unit": "iter/sec",
            "range": "stddev: 0.079571",
            "group": "engine",
            "extra": "mean: 384.36 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.6188001058739476,
            "unit": "iter/sec",
            "range": "stddev: 0.022531",
            "group": "engine",
            "extra": "mean: 1.6160 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.7931849163642617,
            "unit": "iter/sec",
            "range": "stddev: 0.026714",
            "group": "engine",
            "extra": "mean: 1.2607 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.1643901761829805,
            "unit": "iter/sec",
            "range": "stddev: 0.26144",
            "group": "engine",
            "extra": "mean: 6.0831 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.19683821416967062,
            "unit": "iter/sec",
            "range": "stddev: 0.13451",
            "group": "engine",
            "extra": "mean: 5.0803 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.402103950003525,
            "unit": "iter/sec",
            "range": "stddev: 0.030659",
            "group": "engine",
            "extra": "mean: 416.30 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.5497540014258012,
            "unit": "iter/sec",
            "range": "stddev: 0.074638",
            "group": "engine",
            "extra": "mean: 1.8190 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.6013921332773329,
            "unit": "iter/sec",
            "range": "stddev: 0.11433",
            "group": "engine",
            "extra": "mean: 1.6628 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.14781162933357925,
            "unit": "iter/sec",
            "range": "stddev: 0.18356",
            "group": "engine",
            "extra": "mean: 6.7654 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.16614528144045237,
            "unit": "iter/sec",
            "range": "stddev: 0.11189",
            "group": "engine",
            "extra": "mean: 6.0188 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 291.64704001349696,
            "unit": "iter/sec",
            "range": "stddev: 0.00087918",
            "group": "node",
            "extra": "mean: 3.4288 msec\nrounds: 216"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 113.2281886380171,
            "unit": "iter/sec",
            "range": "stddev: 0.00061704",
            "group": "node",
            "extra": "mean: 8.8317 msec\nrounds: 105"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 68.11961676640938,
            "unit": "iter/sec",
            "range": "stddev: 0.0010908",
            "group": "node",
            "extra": "mean: 14.680 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 192.23577912042495,
            "unit": "iter/sec",
            "range": "stddev: 0.00041408",
            "group": "node",
            "extra": "mean: 5.2019 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 48.74016352218945,
            "unit": "iter/sec",
            "range": "stddev: 0.0022487",
            "group": "node",
            "extra": "mean: 20.517 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 44.11193127478747,
            "unit": "iter/sec",
            "range": "stddev: 0.025537",
            "group": "node",
            "extra": "mean: 22.670 msec\nrounds: 100"
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
          "pythonVersion": "3.10.12",
          "metadata": "postgres:12.14, rabbitmq:3.8.14-management"
        },
        "commit": {
          "id": "8ef74a2510d863b7d7a2d235079a993ddaefb237",
          "message": "Devops: Update code to fix mypy error codes\n\nThe `requirements/requirements-3.9.txt` was recently updated which is\nalso used for the `pre-commit` CI job and so new `mypy` errors cropped\nup. The biggest change is changing the `verdi` root command from\n`click.command` to `click.group`. `mypy` was rightly claiming that the\ndecorated `verdi` function did not have attributes used to create\nsub-groups and sub-commands as a `Command` doesn't have those.",
          "timestamp": "2023-06-22T08:41:21+02:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/8ef74a2510d863b7d7a2d235079a993ddaefb237",
          "distinct": true,
          "tree_id": "1719e27b390366b9b2b063f980efbaae88b4376d"
        },
        "date": 1687416632931,
        "benches": [
          {
            "name": "tests/benchmark/test_archive.py::test_export[no-objects]",
            "value": 3.2613969118280286,
            "unit": "iter/sec",
            "range": "stddev: 0.074367",
            "group": "import-export",
            "extra": "mean: 306.62 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_export[with-objects]",
            "value": 3.297914445817271,
            "unit": "iter/sec",
            "range": "stddev: 0.0047305",
            "group": "import-export",
            "extra": "mean: 303.22 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[no-objects]",
            "value": 3.761894854073978,
            "unit": "iter/sec",
            "range": "stddev: 0.094799",
            "group": "import-export",
            "extra": "mean: 265.82 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[with-objects]",
            "value": 3.8345229330938744,
            "unit": "iter/sec",
            "range": "stddev: 0.079186",
            "group": "import-export",
            "extra": "mean: 260.79 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.132695845225145,
            "unit": "iter/sec",
            "range": "stddev: 0.0081395",
            "group": "engine",
            "extra": "mean: 319.21 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.6580458659068734,
            "unit": "iter/sec",
            "range": "stddev: 0.098436",
            "group": "engine",
            "extra": "mean: 1.5197 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.7761113859166384,
            "unit": "iter/sec",
            "range": "stddev: 0.12028",
            "group": "engine",
            "extra": "mean: 1.2885 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.17866740597404954,
            "unit": "iter/sec",
            "range": "stddev: 0.19331",
            "group": "engine",
            "extra": "mean: 5.5970 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.19957887422964632,
            "unit": "iter/sec",
            "range": "stddev: 0.19128",
            "group": "engine",
            "extra": "mean: 5.0106 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.418803789951254,
            "unit": "iter/sec",
            "range": "stddev: 0.036386",
            "group": "engine",
            "extra": "mean: 413.43 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.5566037741399329,
            "unit": "iter/sec",
            "range": "stddev: 0.059202",
            "group": "engine",
            "extra": "mean: 1.7966 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.6316400388882055,
            "unit": "iter/sec",
            "range": "stddev: 0.062018",
            "group": "engine",
            "extra": "mean: 1.5832 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.16075208840906074,
            "unit": "iter/sec",
            "range": "stddev: 0.11645",
            "group": "engine",
            "extra": "mean: 6.2208 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.18241052699825278,
            "unit": "iter/sec",
            "range": "stddev: 0.12309",
            "group": "engine",
            "extra": "mean: 5.4821 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 339.6274059966358,
            "unit": "iter/sec",
            "range": "stddev: 0.00048562",
            "group": "node",
            "extra": "mean: 2.9444 msec\nrounds: 210"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 128.71678697137773,
            "unit": "iter/sec",
            "range": "stddev: 0.00035133",
            "group": "node",
            "extra": "mean: 7.7690 msec\nrounds: 109"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 70.43908621387413,
            "unit": "iter/sec",
            "range": "stddev: 0.0010017",
            "group": "node",
            "extra": "mean: 14.197 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 213.41909343399257,
            "unit": "iter/sec",
            "range": "stddev: 0.00056124",
            "group": "node",
            "extra": "mean: 4.6856 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 52.32673383385866,
            "unit": "iter/sec",
            "range": "stddev: 0.0017552",
            "group": "node",
            "extra": "mean: 19.111 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 50.963429281203176,
            "unit": "iter/sec",
            "range": "stddev: 0.0020073",
            "group": "node",
            "extra": "mean: 19.622 msec\nrounds: 100"
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
          "pythonVersion": "3.10.12",
          "metadata": "postgres:12.14, rabbitmq:3.8.14-management"
        },
        "commit": {
          "id": "101a8d61ba1c9f50a0231cd249c5a7f7ff1d77a4",
          "message": "`CalcJob`: Ignore file in `remote_copy_list` not existing\n\nIf a statement in the `remote_copy_list` contained an explicit filename\nto copy, i.e., without wildcards, the transport would raise an `OSError`\nif the file didn't exist. This exception would be reraised and the\nexponential backoff mechanism would be triggered. However, in the case\nthat the file does not exist, it really is not a transient problem and\nthe operation would be guaranteed to fail in all retries as well.\n\nIn the previous commit, the transports were changed to raise the more\nspecific `FileNotFoundError` if the source in a `copy` operation does\nnot exist. This exception is now caught separately in the\n`upload_calculation` method and instead of reraising, a warning is\nlogged and the exception is swallowed.\n\nThis behavior falls more in line with other file handling operations of\nthe `CalcJob`, for example in the retrieval of files. There, also, a\nmissing file does not trigger an exception but is simply logged with a\nwarning.",
          "timestamp": "2023-06-22T15:35:04+02:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/101a8d61ba1c9f50a0231cd249c5a7f7ff1d77a4",
          "distinct": true,
          "tree_id": "1b615eb5c4675151b36cde5f63acc31a12128d26"
        },
        "date": 1687441415993,
        "benches": [
          {
            "name": "tests/benchmark/test_archive.py::test_export[no-objects]",
            "value": 3.480412042640507,
            "unit": "iter/sec",
            "range": "stddev: 0.054845",
            "group": "import-export",
            "extra": "mean: 287.32 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_export[with-objects]",
            "value": 3.6444016624084212,
            "unit": "iter/sec",
            "range": "stddev: 0.0049011",
            "group": "import-export",
            "extra": "mean: 274.39 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[no-objects]",
            "value": 4.283199259946169,
            "unit": "iter/sec",
            "range": "stddev: 0.056149",
            "group": "import-export",
            "extra": "mean: 233.47 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[with-objects]",
            "value": 3.971938676920852,
            "unit": "iter/sec",
            "range": "stddev: 0.072684",
            "group": "import-export",
            "extra": "mean: 251.77 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.6640241380165817,
            "unit": "iter/sec",
            "range": "stddev: 0.0029505",
            "group": "engine",
            "extra": "mean: 272.92 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.7795062081947108,
            "unit": "iter/sec",
            "range": "stddev: 0.048608",
            "group": "engine",
            "extra": "mean: 1.2829 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.9241304072019279,
            "unit": "iter/sec",
            "range": "stddev: 0.034923",
            "group": "engine",
            "extra": "mean: 1.0821 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.20621325996298526,
            "unit": "iter/sec",
            "range": "stddev: 0.089500",
            "group": "engine",
            "extra": "mean: 4.8493 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.23355944393755004,
            "unit": "iter/sec",
            "range": "stddev: 0.098386",
            "group": "engine",
            "extra": "mean: 4.2816 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.7544092594442975,
            "unit": "iter/sec",
            "range": "stddev: 0.054084",
            "group": "engine",
            "extra": "mean: 363.05 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.6296063948544334,
            "unit": "iter/sec",
            "range": "stddev: 0.038863",
            "group": "engine",
            "extra": "mean: 1.5883 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.6951794566218535,
            "unit": "iter/sec",
            "range": "stddev: 0.063380",
            "group": "engine",
            "extra": "mean: 1.4385 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.1679901142248678,
            "unit": "iter/sec",
            "range": "stddev: 0.16596",
            "group": "engine",
            "extra": "mean: 5.9527 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.19271803894139516,
            "unit": "iter/sec",
            "range": "stddev: 0.16474",
            "group": "engine",
            "extra": "mean: 5.1889 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 348.2507175207516,
            "unit": "iter/sec",
            "range": "stddev: 0.00040779",
            "group": "node",
            "extra": "mean: 2.8715 msec\nrounds: 244"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 138.52001294923195,
            "unit": "iter/sec",
            "range": "stddev: 0.00043327",
            "group": "node",
            "extra": "mean: 7.2192 msec\nrounds: 124"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 79.62378132779152,
            "unit": "iter/sec",
            "range": "stddev: 0.00056653",
            "group": "node",
            "extra": "mean: 12.559 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 226.02287164748452,
            "unit": "iter/sec",
            "range": "stddev: 0.00037685",
            "group": "node",
            "extra": "mean: 4.4243 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 51.782284240169766,
            "unit": "iter/sec",
            "range": "stddev: 0.020046",
            "group": "node",
            "extra": "mean: 19.312 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 58.61269795124882,
            "unit": "iter/sec",
            "range": "stddev: 0.0014768",
            "group": "node",
            "extra": "mean: 17.061 msec\nrounds: 100"
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
          "pythonVersion": "3.10.12",
          "metadata": "postgres:12.14, rabbitmq:3.8.14-management"
        },
        "commit": {
          "id": "cb8af9f3d52f887260c52f99aa429d18db2d8f75",
          "message": "Post release: add the `.post0` qualifier to version attribute",
          "timestamp": "2023-06-23T05:46:09+02:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/cb8af9f3d52f887260c52f99aa429d18db2d8f75",
          "distinct": true,
          "tree_id": "cde07c7cc7d29a3b2856bc65ffc584c9d84505a8"
        },
        "date": 1687498669960,
        "benches": [
          {
            "name": "tests/benchmark/test_archive.py::test_export[no-objects]",
            "value": 3.2795996780266403,
            "unit": "iter/sec",
            "range": "stddev: 0.059600",
            "group": "import-export",
            "extra": "mean: 304.92 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_export[with-objects]",
            "value": 3.308969530393067,
            "unit": "iter/sec",
            "range": "stddev: 0.012615",
            "group": "import-export",
            "extra": "mean: 302.21 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[no-objects]",
            "value": 4.156723989277209,
            "unit": "iter/sec",
            "range": "stddev: 0.062395",
            "group": "import-export",
            "extra": "mean: 240.57 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[with-objects]",
            "value": 3.740583266318516,
            "unit": "iter/sec",
            "range": "stddev: 0.091696",
            "group": "import-export",
            "extra": "mean: 267.34 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.3236933352838296,
            "unit": "iter/sec",
            "range": "stddev: 0.0065085",
            "group": "engine",
            "extra": "mean: 300.87 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.7172945999498023,
            "unit": "iter/sec",
            "range": "stddev: 0.081471",
            "group": "engine",
            "extra": "mean: 1.3941 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.8272578026417625,
            "unit": "iter/sec",
            "range": "stddev: 0.041725",
            "group": "engine",
            "extra": "mean: 1.2088 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.1909717375051192,
            "unit": "iter/sec",
            "range": "stddev: 0.13289",
            "group": "engine",
            "extra": "mean: 5.2364 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.2150157924749801,
            "unit": "iter/sec",
            "range": "stddev: 0.081168",
            "group": "engine",
            "extra": "mean: 4.6508 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.5295322971579717,
            "unit": "iter/sec",
            "range": "stddev: 0.068954",
            "group": "engine",
            "extra": "mean: 395.33 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.611772975449421,
            "unit": "iter/sec",
            "range": "stddev: 0.043334",
            "group": "engine",
            "extra": "mean: 1.6346 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.6735015565411858,
            "unit": "iter/sec",
            "range": "stddev: 0.045472",
            "group": "engine",
            "extra": "mean: 1.4848 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.16643917973454847,
            "unit": "iter/sec",
            "range": "stddev: 0.14333",
            "group": "engine",
            "extra": "mean: 6.0082 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.18957611211725156,
            "unit": "iter/sec",
            "range": "stddev: 0.11293",
            "group": "engine",
            "extra": "mean: 5.2749 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 323.5082129634552,
            "unit": "iter/sec",
            "range": "stddev: 0.00025460",
            "group": "node",
            "extra": "mean: 3.0911 msec\nrounds: 209"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 124.67940290701281,
            "unit": "iter/sec",
            "range": "stddev: 0.00077528",
            "group": "node",
            "extra": "mean: 8.0206 msec\nrounds: 115"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 69.5401204465487,
            "unit": "iter/sec",
            "range": "stddev: 0.0011342",
            "group": "node",
            "extra": "mean: 14.380 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 210.3815006800101,
            "unit": "iter/sec",
            "range": "stddev: 0.00088062",
            "group": "node",
            "extra": "mean: 4.7533 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 48.181624526720796,
            "unit": "iter/sec",
            "range": "stddev: 0.023167",
            "group": "node",
            "extra": "mean: 20.755 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 54.10317555542713,
            "unit": "iter/sec",
            "range": "stddev: 0.0017395",
            "group": "node",
            "extra": "mean: 18.483 msec\nrounds: 100"
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
          "pythonVersion": "3.10.12",
          "metadata": "postgres:12.14, rabbitmq:3.8.14-management"
        },
        "commit": {
          "id": "a8ae508537d2b6e9ffa1de9beb140065282a30f8",
          "message": "Dependencies: Bump `yapf` to `0.40.0` (#6068)",
          "timestamp": "2023-07-04T14:49:32+02:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/a8ae508537d2b6e9ffa1de9beb140065282a30f8",
          "distinct": true,
          "tree_id": "4205c0c49547be9dc13117bc1e7ad907b20924a9"
        },
        "date": 1688475457501,
        "benches": [
          {
            "name": "tests/benchmark/test_archive.py::test_export[no-objects]",
            "value": 3.662410168094287,
            "unit": "iter/sec",
            "range": "stddev: 0.046398",
            "group": "import-export",
            "extra": "mean: 273.04 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_export[with-objects]",
            "value": 3.6392182623271547,
            "unit": "iter/sec",
            "range": "stddev: 0.0066013",
            "group": "import-export",
            "extra": "mean: 274.78 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[no-objects]",
            "value": 4.40895235026472,
            "unit": "iter/sec",
            "range": "stddev: 0.056031",
            "group": "import-export",
            "extra": "mean: 226.81 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[with-objects]",
            "value": 4.350658326118567,
            "unit": "iter/sec",
            "range": "stddev: 0.053952",
            "group": "import-export",
            "extra": "mean: 229.85 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.5192566313071443,
            "unit": "iter/sec",
            "range": "stddev: 0.060764",
            "group": "engine",
            "extra": "mean: 284.15 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.8228711348187385,
            "unit": "iter/sec",
            "range": "stddev: 0.041592",
            "group": "engine",
            "extra": "mean: 1.2153 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.9600853043012673,
            "unit": "iter/sec",
            "range": "stddev: 0.044803",
            "group": "engine",
            "extra": "mean: 1.0416 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.2135410121926033,
            "unit": "iter/sec",
            "range": "stddev: 0.090452",
            "group": "engine",
            "extra": "mean: 4.6829 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.24246466447552678,
            "unit": "iter/sec",
            "range": "stddev: 0.061895",
            "group": "engine",
            "extra": "mean: 4.1243 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.879660078565959,
            "unit": "iter/sec",
            "range": "stddev: 0.019696",
            "group": "engine",
            "extra": "mean: 347.26 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.6439065439958277,
            "unit": "iter/sec",
            "range": "stddev: 0.084024",
            "group": "engine",
            "extra": "mean: 1.5530 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.7443421231592251,
            "unit": "iter/sec",
            "range": "stddev: 0.046273",
            "group": "engine",
            "extra": "mean: 1.3435 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.17954338589263139,
            "unit": "iter/sec",
            "range": "stddev: 0.10384",
            "group": "engine",
            "extra": "mean: 5.5697 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.20370542620849497,
            "unit": "iter/sec",
            "range": "stddev: 0.089323",
            "group": "engine",
            "extra": "mean: 4.9090 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 377.14663776862443,
            "unit": "iter/sec",
            "range": "stddev: 0.00015810",
            "group": "node",
            "extra": "mean: 2.6515 msec\nrounds: 264"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 145.79171395417413,
            "unit": "iter/sec",
            "range": "stddev: 0.00027749",
            "group": "node",
            "extra": "mean: 6.8591 msec\nrounds: 125"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 89.20245701316277,
            "unit": "iter/sec",
            "range": "stddev: 0.00054014",
            "group": "node",
            "extra": "mean: 11.210 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 242.25259427562938,
            "unit": "iter/sec",
            "range": "stddev: 0.00030782",
            "group": "node",
            "extra": "mean: 4.1279 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 61.58360960066959,
            "unit": "iter/sec",
            "range": "stddev: 0.0013443",
            "group": "node",
            "extra": "mean: 16.238 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 55.40666062082462,
            "unit": "iter/sec",
            "range": "stddev: 0.017191",
            "group": "node",
            "extra": "mean: 18.048 msec\nrounds: 100"
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
          "pythonVersion": "3.10.12",
          "metadata": "postgres:12.14, rabbitmq:3.8.14-management"
        },
        "commit": {
          "id": "4db54b7f833096e2d5f3d439683c28749467b20d",
          "message": "Devops: Using concurrency for CI actions (#6066)\n\nThis will cause running actions to be cancelled as soon as new commits\r\nare pushed to the same branch, saving computational resources.",
          "timestamp": "2023-07-04T14:57:28+02:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/4db54b7f833096e2d5f3d439683c28749467b20d",
          "distinct": true,
          "tree_id": "b0900711762aad10d4c8267844f893b8ec811fbb"
        },
        "date": 1688475948945,
        "benches": [
          {
            "name": "tests/benchmark/test_archive.py::test_export[no-objects]",
            "value": 2.9588546561028655,
            "unit": "iter/sec",
            "range": "stddev: 0.17861",
            "group": "import-export",
            "extra": "mean: 337.97 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_export[with-objects]",
            "value": 3.369923171882084,
            "unit": "iter/sec",
            "range": "stddev: 0.0045859",
            "group": "import-export",
            "extra": "mean: 296.74 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[no-objects]",
            "value": 4.172903694275478,
            "unit": "iter/sec",
            "range": "stddev: 0.066413",
            "group": "import-export",
            "extra": "mean: 239.64 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[with-objects]",
            "value": 4.289256422602469,
            "unit": "iter/sec",
            "range": "stddev: 0.053734",
            "group": "import-export",
            "extra": "mean: 233.14 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.4695016835536525,
            "unit": "iter/sec",
            "range": "stddev: 0.059977",
            "group": "engine",
            "extra": "mean: 288.23 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.8032920232867519,
            "unit": "iter/sec",
            "range": "stddev: 0.033285",
            "group": "engine",
            "extra": "mean: 1.2449 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.9608106983389586,
            "unit": "iter/sec",
            "range": "stddev: 0.028576",
            "group": "engine",
            "extra": "mean: 1.0408 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.21138775584249114,
            "unit": "iter/sec",
            "range": "stddev: 0.093427",
            "group": "engine",
            "extra": "mean: 4.7306 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.23724849831208905,
            "unit": "iter/sec",
            "range": "stddev: 0.097654",
            "group": "engine",
            "extra": "mean: 4.2150 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.9184036254773233,
            "unit": "iter/sec",
            "range": "stddev: 0.010003",
            "group": "engine",
            "extra": "mean: 342.65 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.6341590325509441,
            "unit": "iter/sec",
            "range": "stddev: 0.078256",
            "group": "engine",
            "extra": "mean: 1.5769 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.7225785705794868,
            "unit": "iter/sec",
            "range": "stddev: 0.059400",
            "group": "engine",
            "extra": "mean: 1.3839 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.173686543309548,
            "unit": "iter/sec",
            "range": "stddev: 0.089266",
            "group": "engine",
            "extra": "mean: 5.7575 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.20063744934535643,
            "unit": "iter/sec",
            "range": "stddev: 0.099695",
            "group": "engine",
            "extra": "mean: 4.9841 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 362.5308738950636,
            "unit": "iter/sec",
            "range": "stddev: 0.00074736",
            "group": "node",
            "extra": "mean: 2.7584 msec\nrounds: 258"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 147.92097638400497,
            "unit": "iter/sec",
            "range": "stddev: 0.00036154",
            "group": "node",
            "extra": "mean: 6.7604 msec\nrounds: 127"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 89.63315078496453,
            "unit": "iter/sec",
            "range": "stddev: 0.00038686",
            "group": "node",
            "extra": "mean: 11.157 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 243.7451235437641,
            "unit": "iter/sec",
            "range": "stddev: 0.00034891",
            "group": "node",
            "extra": "mean: 4.1026 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 62.320883587440356,
            "unit": "iter/sec",
            "range": "stddev: 0.0010683",
            "group": "node",
            "extra": "mean: 16.046 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 54.52105351907929,
            "unit": "iter/sec",
            "range": "stddev: 0.017787",
            "group": "node",
            "extra": "mean: 18.342 msec\nrounds: 100"
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
          "pythonVersion": "3.10.12",
          "metadata": "postgres:12.14, rabbitmq:3.8.14-management"
        },
        "commit": {
          "id": "923cc314c527a183e55819b96de8ae027c9f0612",
          "message": "Typing: Correct type annotation of `WorkChain.on_wait` (#5836)\n\nIt was incorrectly using the `Awaitable` defined by `aiida-core` instead\r\nof the `typing.Awaitable` class, which is what the actual notation is\r\nof the method defined by the `plumpy.processes.Process` base class.\r\n\r\nThe annotation of `Protect.final` is made more specific in passing.",
          "timestamp": "2023-07-05T17:02:02-07:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/923cc314c527a183e55819b96de8ae027c9f0612",
          "distinct": true,
          "tree_id": "232839113dde732c869758c7de183ceaf029f73e"
        },
        "date": 1688602287925,
        "benches": [
          {
            "name": "tests/benchmark/test_archive.py::test_export[no-objects]",
            "value": 3.038217908655863,
            "unit": "iter/sec",
            "range": "stddev: 0.064291",
            "group": "import-export",
            "extra": "mean: 329.14 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_export[with-objects]",
            "value": 3.1638002572620634,
            "unit": "iter/sec",
            "range": "stddev: 0.0060263",
            "group": "import-export",
            "extra": "mean: 316.08 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[no-objects]",
            "value": 3.8873003509791255,
            "unit": "iter/sec",
            "range": "stddev: 0.076880",
            "group": "import-export",
            "extra": "mean: 257.25 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[with-objects]",
            "value": 3.840853221268993,
            "unit": "iter/sec",
            "range": "stddev: 0.064913",
            "group": "import-export",
            "extra": "mean: 260.36 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 2.9766745791559184,
            "unit": "iter/sec",
            "range": "stddev: 0.069113",
            "group": "engine",
            "extra": "mean: 335.95 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.6958736655873241,
            "unit": "iter/sec",
            "range": "stddev: 0.032526",
            "group": "engine",
            "extra": "mean: 1.4370 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.7887697319257401,
            "unit": "iter/sec",
            "range": "stddev: 0.082514",
            "group": "engine",
            "extra": "mean: 1.2678 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.17807998116789917,
            "unit": "iter/sec",
            "range": "stddev: 0.068576",
            "group": "engine",
            "extra": "mean: 5.6155 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.19847769085801178,
            "unit": "iter/sec",
            "range": "stddev: 0.095440",
            "group": "engine",
            "extra": "mean: 5.0383 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.3312176567197835,
            "unit": "iter/sec",
            "range": "stddev: 0.078868",
            "group": "engine",
            "extra": "mean: 428.96 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.5419429444309606,
            "unit": "iter/sec",
            "range": "stddev: 0.055052",
            "group": "engine",
            "extra": "mean: 1.8452 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.6050987639857821,
            "unit": "iter/sec",
            "range": "stddev: 0.091220",
            "group": "engine",
            "extra": "mean: 1.6526 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.15520756143649628,
            "unit": "iter/sec",
            "range": "stddev: 0.20509",
            "group": "engine",
            "extra": "mean: 6.4430 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.17730860874649446,
            "unit": "iter/sec",
            "range": "stddev: 0.16652",
            "group": "engine",
            "extra": "mean: 5.6399 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 305.6681131807159,
            "unit": "iter/sec",
            "range": "stddev: 0.00034566",
            "group": "node",
            "extra": "mean: 3.2715 msec\nrounds: 206"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 119.72160894824091,
            "unit": "iter/sec",
            "range": "stddev: 0.00041064",
            "group": "node",
            "extra": "mean: 8.3527 msec\nrounds: 104"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 71.28606259521366,
            "unit": "iter/sec",
            "range": "stddev: 0.0018119",
            "group": "node",
            "extra": "mean: 14.028 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 196.68290117471787,
            "unit": "iter/sec",
            "range": "stddev: 0.00032047",
            "group": "node",
            "extra": "mean: 5.0843 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 53.629446448441826,
            "unit": "iter/sec",
            "range": "stddev: 0.0014370",
            "group": "node",
            "extra": "mean: 18.646 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 47.05982892665446,
            "unit": "iter/sec",
            "range": "stddev: 0.023459",
            "group": "node",
            "extra": "mean: 21.250 msec\nrounds: 100"
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
          "pythonVersion": "3.10.12",
          "metadata": "postgres:12.14, rabbitmq:3.8.14-management"
        },
        "commit": {
          "id": "227390a52a6dc77faa20cb1cc6372ec7f66e0409",
          "message": "Devops: Update tox to use Python 3.9 (#6076)\n\nThis was missed when Python 3.8 support was dropped.",
          "timestamp": "2023-07-07T08:39:55-07:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/227390a52a6dc77faa20cb1cc6372ec7f66e0409",
          "distinct": true,
          "tree_id": "1ed4b395c4878d4519d27024804fd62a4fec0591"
        },
        "date": 1688745026205,
        "benches": [
          {
            "name": "tests/benchmark/test_archive.py::test_export[no-objects]",
            "value": 2.95322715670716,
            "unit": "iter/sec",
            "range": "stddev: 0.0043299",
            "group": "import-export",
            "extra": "mean: 338.61 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_export[with-objects]",
            "value": 2.842393861504663,
            "unit": "iter/sec",
            "range": "stddev: 0.0082833",
            "group": "import-export",
            "extra": "mean: 351.82 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[no-objects]",
            "value": 3.601891538023577,
            "unit": "iter/sec",
            "range": "stddev: 0.066698",
            "group": "import-export",
            "extra": "mean: 277.63 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[with-objects]",
            "value": 3.568416540058998,
            "unit": "iter/sec",
            "range": "stddev: 0.071994",
            "group": "import-export",
            "extra": "mean: 280.24 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 2.9290458006985967,
            "unit": "iter/sec",
            "range": "stddev: 0.0039166",
            "group": "engine",
            "extra": "mean: 341.41 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.6447108910514755,
            "unit": "iter/sec",
            "range": "stddev: 0.096340",
            "group": "engine",
            "extra": "mean: 1.5511 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.7162562026831834,
            "unit": "iter/sec",
            "range": "stddev: 0.084567",
            "group": "engine",
            "extra": "mean: 1.3961 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.16474682648517266,
            "unit": "iter/sec",
            "range": "stddev: 0.088475",
            "group": "engine",
            "extra": "mean: 6.0699 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.18459675561064004,
            "unit": "iter/sec",
            "range": "stddev: 0.12631",
            "group": "engine",
            "extra": "mean: 5.4172 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.330486954948647,
            "unit": "iter/sec",
            "range": "stddev: 0.018501",
            "group": "engine",
            "extra": "mean: 429.09 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.5290702607389774,
            "unit": "iter/sec",
            "range": "stddev: 0.069940",
            "group": "engine",
            "extra": "mean: 1.8901 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.588673028784767,
            "unit": "iter/sec",
            "range": "stddev: 0.099111",
            "group": "engine",
            "extra": "mean: 1.6987 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.14561904028296677,
            "unit": "iter/sec",
            "range": "stddev: 0.079583",
            "group": "engine",
            "extra": "mean: 6.8672 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.16452810600832185,
            "unit": "iter/sec",
            "range": "stddev: 0.042676",
            "group": "engine",
            "extra": "mean: 6.0780 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 194.57401096854326,
            "unit": "iter/sec",
            "range": "stddev: 0.018907",
            "group": "node",
            "extra": "mean: 5.1394 msec\nrounds: 178"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 130.69940913417298,
            "unit": "iter/sec",
            "range": "stddev: 0.00020484",
            "group": "node",
            "extra": "mean: 7.6511 msec\nrounds: 112"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 72.90205373092708,
            "unit": "iter/sec",
            "range": "stddev: 0.00095219",
            "group": "node",
            "extra": "mean: 13.717 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 216.67999291981985,
            "unit": "iter/sec",
            "range": "stddev: 0.00022904",
            "group": "node",
            "extra": "mean: 4.6151 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 48.90692508904177,
            "unit": "iter/sec",
            "range": "stddev: 0.0021652",
            "group": "node",
            "extra": "mean: 20.447 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 46.978597724868465,
            "unit": "iter/sec",
            "range": "stddev: 0.0018373",
            "group": "node",
            "extra": "mean: 21.286 msec\nrounds: 100"
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
          "pythonVersion": "3.10.12",
          "metadata": "postgres:12.14, rabbitmq:3.8.14-management"
        },
        "commit": {
          "id": "03c86d5c988d9d2e1f656ba28bd2b8292fc7b02d",
          "message": "`CalcJobNode`: Fix validation for `depth=None` in `retrieve_list` (#6078)\n\nCommit a1b9f79a97c5e987aa900c1db3258339abaa6aa3 added support for using\r\n`None` as the third element in a directive of the `retrieve_list` of a\r\n`CalcJob`. However, the method `_validate_retrieval_directive` that\r\nvalidates the retrieve list directives when stored on the `CalcJobNode`\r\nwas not updated and would only still accept integers.",
          "timestamp": "2023-07-07T11:42:16-07:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/03c86d5c988d9d2e1f656ba28bd2b8292fc7b02d",
          "distinct": true,
          "tree_id": "e44cdb9aa1769215acc0a6aa73778acbe1bc714d"
        },
        "date": 1688755878303,
        "benches": [
          {
            "name": "tests/benchmark/test_archive.py::test_export[no-objects]",
            "value": 3.1292599397876004,
            "unit": "iter/sec",
            "range": "stddev: 0.072179",
            "group": "import-export",
            "extra": "mean: 319.56 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_export[with-objects]",
            "value": 3.3294587783383034,
            "unit": "iter/sec",
            "range": "stddev: 0.012818",
            "group": "import-export",
            "extra": "mean: 300.35 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[no-objects]",
            "value": 4.041704769866563,
            "unit": "iter/sec",
            "range": "stddev: 0.066120",
            "group": "import-export",
            "extra": "mean: 247.42 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[with-objects]",
            "value": 4.041358431010251,
            "unit": "iter/sec",
            "range": "stddev: 0.066781",
            "group": "import-export",
            "extra": "mean: 247.44 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.2766627230272696,
            "unit": "iter/sec",
            "range": "stddev: 0.0026425",
            "group": "engine",
            "extra": "mean: 305.19 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.7135192989470616,
            "unit": "iter/sec",
            "range": "stddev: 0.072056",
            "group": "engine",
            "extra": "mean: 1.4015 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.8090612160404583,
            "unit": "iter/sec",
            "range": "stddev: 0.076285",
            "group": "engine",
            "extra": "mean: 1.2360 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.18969500098519157,
            "unit": "iter/sec",
            "range": "stddev: 0.099621",
            "group": "engine",
            "extra": "mean: 5.2716 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.21514578763293402,
            "unit": "iter/sec",
            "range": "stddev: 0.11759",
            "group": "engine",
            "extra": "mean: 4.6480 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.550235974444038,
            "unit": "iter/sec",
            "range": "stddev: 0.023689",
            "group": "engine",
            "extra": "mean: 392.12 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.5736956107056602,
            "unit": "iter/sec",
            "range": "stddev: 0.056824",
            "group": "engine",
            "extra": "mean: 1.7431 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.6531030998611219,
            "unit": "iter/sec",
            "range": "stddev: 0.038739",
            "group": "engine",
            "extra": "mean: 1.5312 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.1583372798557267,
            "unit": "iter/sec",
            "range": "stddev: 0.10367",
            "group": "engine",
            "extra": "mean: 6.3156 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.18054888733246593,
            "unit": "iter/sec",
            "range": "stddev: 0.12135",
            "group": "engine",
            "extra": "mean: 5.5387 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 369.7055860293659,
            "unit": "iter/sec",
            "range": "stddev: 0.00027146",
            "group": "node",
            "extra": "mean: 2.7049 msec\nrounds: 255"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 131.41940331059666,
            "unit": "iter/sec",
            "range": "stddev: 0.00062516",
            "group": "node",
            "extra": "mean: 7.6092 msec\nrounds: 115"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 74.95725201030601,
            "unit": "iter/sec",
            "range": "stddev: 0.00086687",
            "group": "node",
            "extra": "mean: 13.341 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 218.06450693044064,
            "unit": "iter/sec",
            "range": "stddev: 0.00059549",
            "group": "node",
            "extra": "mean: 4.5858 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 52.07621123336409,
            "unit": "iter/sec",
            "range": "stddev: 0.0017360",
            "group": "node",
            "extra": "mean: 19.203 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 50.40203259423325,
            "unit": "iter/sec",
            "range": "stddev: 0.0018191",
            "group": "node",
            "extra": "mean: 19.840 msec\nrounds: 100"
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
          "pythonVersion": "3.10.12",
          "metadata": "postgres:12.14, rabbitmq:3.8.14-management"
        },
        "commit": {
          "id": "fd4c1269bf913602660b13bdb49c3bc15360448a",
          "message": "CLI: Fix bug in `verdi data core.trajectory show` for various formats (#5394)\n\nThese minor bugs went unnoticed because the methods are wholly untested.\r\nThis is partly because they rely on additional Python modules or external\r\nexecutables. For the formats that rely on external executables, i.e.,\r\n`jmol` and `xcrysden`, the `subprocess.check_output` function is\r\nmonkeypatched to prevent the actual executable from being called. This\r\ntests all code except for the actual external executable, which at least\r\ngives coverage of our code.\r\n\r\nThe test for `mpl_pos` needed to be monkeypatched as well. This is\r\nbecause the `_show_mpl_pos` method calls `plot_positions_xyz` which\r\nimports `matplotlib.pyplot` and for some completely unknown reason, this\r\ncauses `tests/storage/psql_dos/test_backend.py::test_unload_profile` to\r\nfail. For some reason, merely importing `matplotlib` (even here directly\r\nin the test) will cause that test to claim that there still is something\r\nholding on to a reference of an sqlalchemy session that it keeps track\r\nof in the `sqlalchemy.orm.session._sessions` weak ref dictionary. Since\r\nit is impossible to figure out why the hell importing matplotlib would\r\ninteract with sqlalchemy sessions, the function that does the import is\r\nsimply mocked out for now.\r\n\r\nCo-authored-by: Sebastiaan Huber <mail@sphuber.net>",
          "timestamp": "2023-07-10T22:21:33-05:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/fd4c1269bf913602660b13bdb49c3bc15360448a",
          "distinct": true,
          "tree_id": "20e803dbb5bf92f2d188d393732765010ee1b75d"
        },
        "date": 1689046217464,
        "benches": [
          {
            "name": "tests/benchmark/test_archive.py::test_export[no-objects]",
            "value": 3.6177434833917985,
            "unit": "iter/sec",
            "range": "stddev: 0.019894",
            "group": "import-export",
            "extra": "mean: 276.42 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_export[with-objects]",
            "value": 3.324211154048787,
            "unit": "iter/sec",
            "range": "stddev: 0.065918",
            "group": "import-export",
            "extra": "mean: 300.82 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[no-objects]",
            "value": 4.184558866890536,
            "unit": "iter/sec",
            "range": "stddev: 0.071905",
            "group": "import-export",
            "extra": "mean: 238.97 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[with-objects]",
            "value": 4.093328283275988,
            "unit": "iter/sec",
            "range": "stddev: 0.078367",
            "group": "import-export",
            "extra": "mean: 244.30 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.5188391421735044,
            "unit": "iter/sec",
            "range": "stddev: 0.0029767",
            "group": "engine",
            "extra": "mean: 284.18 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.7547582824736622,
            "unit": "iter/sec",
            "range": "stddev: 0.078831",
            "group": "engine",
            "extra": "mean: 1.3249 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.7711941043684014,
            "unit": "iter/sec",
            "range": "stddev: 0.14003",
            "group": "engine",
            "extra": "mean: 1.2967 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.19235252269315697,
            "unit": "iter/sec",
            "range": "stddev: 0.12416",
            "group": "engine",
            "extra": "mean: 5.1988 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.22096222213466513,
            "unit": "iter/sec",
            "range": "stddev: 0.13977",
            "group": "engine",
            "extra": "mean: 4.5257 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.8621191918896227,
            "unit": "iter/sec",
            "range": "stddev: 0.015961",
            "group": "engine",
            "extra": "mean: 349.39 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.6064080293487861,
            "unit": "iter/sec",
            "range": "stddev: 0.046707",
            "group": "engine",
            "extra": "mean: 1.6491 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.687012001244536,
            "unit": "iter/sec",
            "range": "stddev: 0.083176",
            "group": "engine",
            "extra": "mean: 1.4556 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.17073109607393125,
            "unit": "iter/sec",
            "range": "stddev: 0.13068",
            "group": "engine",
            "extra": "mean: 5.8572 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.19409551515306925,
            "unit": "iter/sec",
            "range": "stddev: 0.11989",
            "group": "engine",
            "extra": "mean: 5.1521 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 377.4969724324667,
            "unit": "iter/sec",
            "range": "stddev: 0.00015131",
            "group": "node",
            "extra": "mean: 2.6490 msec\nrounds: 227"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 151.37802070163178,
            "unit": "iter/sec",
            "range": "stddev: 0.00019447",
            "group": "node",
            "extra": "mean: 6.6060 msec\nrounds: 129"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 88.45950339283868,
            "unit": "iter/sec",
            "range": "stddev: 0.00060047",
            "group": "node",
            "extra": "mean: 11.305 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 250.0316027444419,
            "unit": "iter/sec",
            "range": "stddev: 0.00026786",
            "group": "node",
            "extra": "mean: 3.9995 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 58.8207967359475,
            "unit": "iter/sec",
            "range": "stddev: 0.0013167",
            "group": "node",
            "extra": "mean: 17.001 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 56.77485515202394,
            "unit": "iter/sec",
            "range": "stddev: 0.0018043",
            "group": "node",
            "extra": "mean: 17.613 msec\nrounds: 100"
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
          "pythonVersion": "3.10.12",
          "metadata": "postgres:12.14, rabbitmq:3.8.14-management"
        },
        "commit": {
          "id": "7bd546ebe67845b47c0dc14567c1ef7a557c23ef",
          "message": "ORM: Check nodes are from same backend in `validate_link` (#5462)",
          "timestamp": "2023-07-11T10:00:35-05:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/7bd546ebe67845b47c0dc14567c1ef7a557c23ef",
          "distinct": true,
          "tree_id": "902cb199b7d2685de8afd3d3ff80cde51c044780"
        },
        "date": 1689088205700,
        "benches": [
          {
            "name": "tests/benchmark/test_archive.py::test_export[no-objects]",
            "value": 3.277349558950622,
            "unit": "iter/sec",
            "range": "stddev: 0.0076802",
            "group": "import-export",
            "extra": "mean: 305.12 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_export[with-objects]",
            "value": 2.8951662927243076,
            "unit": "iter/sec",
            "range": "stddev: 0.085973",
            "group": "import-export",
            "extra": "mean: 345.40 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[no-objects]",
            "value": 3.8224326280546554,
            "unit": "iter/sec",
            "range": "stddev: 0.090058",
            "group": "import-export",
            "extra": "mean: 261.61 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[with-objects]",
            "value": 3.8569921944872703,
            "unit": "iter/sec",
            "range": "stddev: 0.090710",
            "group": "import-export",
            "extra": "mean: 259.27 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.134691525790226,
            "unit": "iter/sec",
            "range": "stddev: 0.011610",
            "group": "engine",
            "extra": "mean: 319.01 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.6693213535161424,
            "unit": "iter/sec",
            "range": "stddev: 0.075525",
            "group": "engine",
            "extra": "mean: 1.4941 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.7848002102759779,
            "unit": "iter/sec",
            "range": "stddev: 0.069462",
            "group": "engine",
            "extra": "mean: 1.2742 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.1694227501190969,
            "unit": "iter/sec",
            "range": "stddev: 0.21473",
            "group": "engine",
            "extra": "mean: 5.9024 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.19439595936415557,
            "unit": "iter/sec",
            "range": "stddev: 0.15121",
            "group": "engine",
            "extra": "mean: 5.1441 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.3868922475565406,
            "unit": "iter/sec",
            "range": "stddev: 0.037290",
            "group": "engine",
            "extra": "mean: 418.95 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.5429863330169469,
            "unit": "iter/sec",
            "range": "stddev: 0.086595",
            "group": "engine",
            "extra": "mean: 1.8417 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.6048194482265808,
            "unit": "iter/sec",
            "range": "stddev: 0.072492",
            "group": "engine",
            "extra": "mean: 1.6534 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.15386620536336681,
            "unit": "iter/sec",
            "range": "stddev: 0.12921",
            "group": "engine",
            "extra": "mean: 6.4992 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.17182879646735363,
            "unit": "iter/sec",
            "range": "stddev: 0.15449",
            "group": "engine",
            "extra": "mean: 5.8197 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 367.9859263103763,
            "unit": "iter/sec",
            "range": "stddev: 0.00055546",
            "group": "node",
            "extra": "mean: 2.7175 msec\nrounds: 216"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 136.66768804155865,
            "unit": "iter/sec",
            "range": "stddev: 0.00038719",
            "group": "node",
            "extra": "mean: 7.3170 msec\nrounds: 117"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 66.83226516816602,
            "unit": "iter/sec",
            "range": "stddev: 0.0031422",
            "group": "node",
            "extra": "mean: 14.963 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 220.09588662202987,
            "unit": "iter/sec",
            "range": "stddev: 0.00021722",
            "group": "node",
            "extra": "mean: 4.5435 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 48.523769370862055,
            "unit": "iter/sec",
            "range": "stddev: 0.0021584",
            "group": "node",
            "extra": "mean: 20.608 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 48.236708309554736,
            "unit": "iter/sec",
            "range": "stddev: 0.0019449",
            "group": "node",
            "extra": "mean: 20.731 msec\nrounds: 100"
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
          "pythonVersion": "3.10.12",
          "metadata": "postgres:12.14, rabbitmq:3.8.14-management"
        },
        "commit": {
          "id": "d1d64e8004c31209488f71a160a4f4824d02c081",
          "message": "Tests: Fix `StructureData` test breaking for recent `pymatgen` versions (#6088)\n\nThe roundtrip test for the `StructureData` class using `pymatgen`\r\nstructures as a go between started failing. The structure is constructed\r\nfrom a CIF file with partial occupancies. The `label` attribute of each\r\nsite in the pymatgen structure, as returned by `as_dict` would look like\r\nthe following, originally:\r\n\r\n    ['Bi', 'Bi', 'Te:0.667, Se:0.333', 'Te:0.667, Se:0.333', 'Te:0.667, Se:0.333']\r\n    ['Bi', 'Bi', 'Te:0.667, Se:0.333', 'Te:0.667, Se:0.333', 'Te:0.667, Se:0.333']\r\n\r\nIn commit 63bbd23b57ca2c68eaca07e4915a70ef66e13405, released with\r\nv2023.7.14, the CIF parsing logic in `pymatgen` was updated to include\r\nparsing of the atom site labels and store them on the site `label`\r\nattribute. This would result in the following site labels for the\r\nstructure parsed directly from the CIF and the one after roundtrip\r\nthrough `StructureData`:\r\n\r\n    ['Bi', 'Bi', 'Se1', 'Se1', 'Se1']\r\n    [None, None, None, None, None]\r\n\r\nThe roundtrip returned `None` values because in the previously mentioned\r\ncommit, the newly added `label` property would return `None` instead of\r\nthe species label that used to be returned before. This behavior was\r\ncorrected in commit 9a98f4ce722299d545f2af01a9eaf1c37ff7bd53 and released\r\nwith v2023.7.20, after which the new behavior is the following:\r\n\r\n    ['Bi', 'Bi', 'Se1', 'Se1', 'Se1']\r\n    ['Bi', 'Bi', 'Te:0.667, Se:0.333', 'Te:0.667, Se:0.333', 'Te:0.667, Se:0.333']\r\n\r\nThe site labels parsed from the CIF are not maintained in the roundtrip\r\nbecause the `StructureData` does not store them. Therefore when the final\r\npymatgen structure is created from it, the `label` is `None` and so\r\ndefaults to the species name.\r\n\r\nSince the label information is not persisted in the `StructureData` it\r\nis not guaranteed to be maintained in the roundtrip and so it is\r\nexcluded from the test.",
          "timestamp": "2023-07-27T17:59:31+02:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/d1d64e8004c31209488f71a160a4f4824d02c081",
          "distinct": true,
          "tree_id": "a24858230c0ae26926a964a60994842d2d69d058"
        },
        "date": 1690474322760,
        "benches": [
          {
            "name": "tests/benchmark/test_archive.py::test_export[no-objects]",
            "value": 2.1696932330512526,
            "unit": "iter/sec",
            "range": "stddev: 0.078477",
            "group": "import-export",
            "extra": "mean: 460.89 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_export[with-objects]",
            "value": 2.0772464980110064,
            "unit": "iter/sec",
            "range": "stddev: 0.081156",
            "group": "import-export",
            "extra": "mean: 481.41 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[no-objects]",
            "value": 3.1291393183865437,
            "unit": "iter/sec",
            "range": "stddev: 0.077662",
            "group": "import-export",
            "extra": "mean: 319.58 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[with-objects]",
            "value": 3.1570333726875455,
            "unit": "iter/sec",
            "range": "stddev: 0.092511",
            "group": "import-export",
            "extra": "mean: 316.75 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 2.4877445394918127,
            "unit": "iter/sec",
            "range": "stddev: 0.031227",
            "group": "engine",
            "extra": "mean: 401.97 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.5087695946765561,
            "unit": "iter/sec",
            "range": "stddev: 0.11117",
            "group": "engine",
            "extra": "mean: 1.9655 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.5690345238844364,
            "unit": "iter/sec",
            "range": "stddev: 0.15494",
            "group": "engine",
            "extra": "mean: 1.7574 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.1360183190813828,
            "unit": "iter/sec",
            "range": "stddev: 0.20494",
            "group": "engine",
            "extra": "mean: 7.3520 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.1588628696648254,
            "unit": "iter/sec",
            "range": "stddev: 0.23053",
            "group": "engine",
            "extra": "mean: 6.2947 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.0207115219969207,
            "unit": "iter/sec",
            "range": "stddev: 0.022240",
            "group": "engine",
            "extra": "mean: 494.88 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.4316338630480128,
            "unit": "iter/sec",
            "range": "stddev: 0.089851",
            "group": "engine",
            "extra": "mean: 2.3168 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.4944302288370177,
            "unit": "iter/sec",
            "range": "stddev: 0.098142",
            "group": "engine",
            "extra": "mean: 2.0225 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.12531971874148548,
            "unit": "iter/sec",
            "range": "stddev: 0.24722",
            "group": "engine",
            "extra": "mean: 7.9796 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.13895221180873593,
            "unit": "iter/sec",
            "range": "stddev: 0.34905",
            "group": "engine",
            "extra": "mean: 7.1967 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 276.54158877253946,
            "unit": "iter/sec",
            "range": "stddev: 0.00073503",
            "group": "node",
            "extra": "mean: 3.6161 msec\nrounds: 206"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 100.98000488863302,
            "unit": "iter/sec",
            "range": "stddev: 0.0013551",
            "group": "node",
            "extra": "mean: 9.9030 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 60.60679391153598,
            "unit": "iter/sec",
            "range": "stddev: 0.0023589",
            "group": "node",
            "extra": "mean: 16.500 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 166.70530034202574,
            "unit": "iter/sec",
            "range": "stddev: 0.00093267",
            "group": "node",
            "extra": "mean: 5.9986 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 40.555268575431384,
            "unit": "iter/sec",
            "range": "stddev: 0.0034393",
            "group": "node",
            "extra": "mean: 24.658 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 37.6228568276055,
            "unit": "iter/sec",
            "range": "stddev: 0.0037780",
            "group": "node",
            "extra": "mean: 26.580 msec\nrounds: 100"
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
          "pythonVersion": "3.10.12",
          "metadata": "postgres:12.14, rabbitmq:3.8.14-management"
        },
        "commit": {
          "id": "e01ea4b97d094f0543b0f0c631fa0463c8baf2f5",
          "message": "Devops: Update pre-commit requirement `flynt==1.0.1` (#6093)",
          "timestamp": "2023-08-07T12:37:46+02:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/e01ea4b97d094f0543b0f0c631fa0463c8baf2f5",
          "distinct": true,
          "tree_id": "d16380e8563bd1734db641bca2b2fdabf36f87ef"
        },
        "date": 1691405195289,
        "benches": [
          {
            "name": "tests/benchmark/test_archive.py::test_export[no-objects]",
            "value": 3.3701714965296077,
            "unit": "iter/sec",
            "range": "stddev: 0.0085125",
            "group": "import-export",
            "extra": "mean: 296.72 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_export[with-objects]",
            "value": 3.010544752867283,
            "unit": "iter/sec",
            "range": "stddev: 0.067399",
            "group": "import-export",
            "extra": "mean: 332.17 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[no-objects]",
            "value": 4.174313826971566,
            "unit": "iter/sec",
            "range": "stddev: 0.063214",
            "group": "import-export",
            "extra": "mean: 239.56 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[with-objects]",
            "value": 4.104482391696786,
            "unit": "iter/sec",
            "range": "stddev: 0.065033",
            "group": "import-export",
            "extra": "mean: 243.64 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.1066070591367305,
            "unit": "iter/sec",
            "range": "stddev: 0.074352",
            "group": "engine",
            "extra": "mean: 321.89 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.7240316271805286,
            "unit": "iter/sec",
            "range": "stddev: 0.040751",
            "group": "engine",
            "extra": "mean: 1.3812 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.8450979086424235,
            "unit": "iter/sec",
            "range": "stddev: 0.078731",
            "group": "engine",
            "extra": "mean: 1.1833 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.19070619026391616,
            "unit": "iter/sec",
            "range": "stddev: 0.13239",
            "group": "engine",
            "extra": "mean: 5.2437 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.21420305812832083,
            "unit": "iter/sec",
            "range": "stddev: 0.11219",
            "group": "engine",
            "extra": "mean: 4.6685 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.5405466313705865,
            "unit": "iter/sec",
            "range": "stddev: 0.075920",
            "group": "engine",
            "extra": "mean: 393.62 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.6035220850366304,
            "unit": "iter/sec",
            "range": "stddev: 0.062830",
            "group": "engine",
            "extra": "mean: 1.6569 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.6777735197243853,
            "unit": "iter/sec",
            "range": "stddev: 0.045141",
            "group": "engine",
            "extra": "mean: 1.4754 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.16768153860735757,
            "unit": "iter/sec",
            "range": "stddev: 0.10288",
            "group": "engine",
            "extra": "mean: 5.9637 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.19047968219008415,
            "unit": "iter/sec",
            "range": "stddev: 0.11563",
            "group": "engine",
            "extra": "mean: 5.2499 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 311.1178673478125,
            "unit": "iter/sec",
            "range": "stddev: 0.0012104",
            "group": "node",
            "extra": "mean: 3.2142 msec\nrounds: 218"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 133.34274391207356,
            "unit": "iter/sec",
            "range": "stddev: 0.00054308",
            "group": "node",
            "extra": "mean: 7.4995 msec\nrounds: 117"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 78.07365364177784,
            "unit": "iter/sec",
            "range": "stddev: 0.00085705",
            "group": "node",
            "extra": "mean: 12.808 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 216.89525829080517,
            "unit": "iter/sec",
            "range": "stddev: 0.00053293",
            "group": "node",
            "extra": "mean: 4.6105 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 55.244546528904614,
            "unit": "iter/sec",
            "range": "stddev: 0.0018543",
            "group": "node",
            "extra": "mean: 18.101 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 48.55859148067756,
            "unit": "iter/sec",
            "range": "stddev: 0.023715",
            "group": "node",
            "extra": "mean: 20.594 msec\nrounds: 100"
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
          "pythonVersion": "3.10.12",
          "metadata": "postgres:12.14, rabbitmq:3.8.14-management"
        },
        "commit": {
          "id": "d082df7f1b53057e15c8cbbc7e662ec808c27722",
          "message": "`SinglefileData`: Add `mode` keyword to `get_content`\n\nThis allows a user to retrieve the content in bytes. Currently, a user\nis forced to use the more elaborate form:\n\n    with singlefile.open(mode='rb') as handle:\n        content = handle.read()\n\nor go directly through the repository interface which is a bit hidden\nand requires to redundantly specify the filename:\n\n    content = singlefile.base.repository.get_object_content(\n\tsinglefile.filename,\n\tmode='rb'\n    )\n\nthese variants can now be simplified to:\n\n    content = singlefile.get_content('rb')",
          "timestamp": "2023-08-14T10:21:24+02:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/d082df7f1b53057e15c8cbbc7e662ec808c27722",
          "distinct": true,
          "tree_id": "206c8d54694865aff3d478c424fdba59f5bac6ea"
        },
        "date": 1692001817584,
        "benches": [
          {
            "name": "tests/benchmark/test_archive.py::test_export[no-objects]",
            "value": 3.4600346336723224,
            "unit": "iter/sec",
            "range": "stddev: 0.019768",
            "group": "import-export",
            "extra": "mean: 289.01 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_export[with-objects]",
            "value": 3.193943103394576,
            "unit": "iter/sec",
            "range": "stddev: 0.033824",
            "group": "import-export",
            "extra": "mean: 313.09 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[no-objects]",
            "value": 4.051131854945288,
            "unit": "iter/sec",
            "range": "stddev: 0.068556",
            "group": "import-export",
            "extra": "mean: 246.84 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[with-objects]",
            "value": 3.867577545724301,
            "unit": "iter/sec",
            "range": "stddev: 0.064300",
            "group": "import-export",
            "extra": "mean: 258.56 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.1761999572032193,
            "unit": "iter/sec",
            "range": "stddev: 0.0092017",
            "group": "engine",
            "extra": "mean: 314.84 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.6874448116727274,
            "unit": "iter/sec",
            "range": "stddev: 0.072031",
            "group": "engine",
            "extra": "mean: 1.4547 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.812691884975553,
            "unit": "iter/sec",
            "range": "stddev: 0.034409",
            "group": "engine",
            "extra": "mean: 1.2305 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.19108121546735884,
            "unit": "iter/sec",
            "range": "stddev: 0.13210",
            "group": "engine",
            "extra": "mean: 5.2334 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.22232743698714738,
            "unit": "iter/sec",
            "range": "stddev: 0.12879",
            "group": "engine",
            "extra": "mean: 4.4979 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.764781921125427,
            "unit": "iter/sec",
            "range": "stddev: 0.017742",
            "group": "engine",
            "extra": "mean: 361.69 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.5845165005327707,
            "unit": "iter/sec",
            "range": "stddev: 0.11134",
            "group": "engine",
            "extra": "mean: 1.7108 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.6695563726086817,
            "unit": "iter/sec",
            "range": "stddev: 0.077269",
            "group": "engine",
            "extra": "mean: 1.4935 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.16313158994406013,
            "unit": "iter/sec",
            "range": "stddev: 0.14901",
            "group": "engine",
            "extra": "mean: 6.1300 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.18495656122927961,
            "unit": "iter/sec",
            "range": "stddev: 0.095356",
            "group": "engine",
            "extra": "mean: 5.4067 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 312.624584273632,
            "unit": "iter/sec",
            "range": "stddev: 0.00067103",
            "group": "node",
            "extra": "mean: 3.1987 msec\nrounds: 162"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 129.86704615837107,
            "unit": "iter/sec",
            "range": "stddev: 0.00095196",
            "group": "node",
            "extra": "mean: 7.7002 msec\nrounds: 117"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 75.42882374362532,
            "unit": "iter/sec",
            "range": "stddev: 0.0014723",
            "group": "node",
            "extra": "mean: 13.258 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 210.5312754630435,
            "unit": "iter/sec",
            "range": "stddev: 0.00075257",
            "group": "node",
            "extra": "mean: 4.7499 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 48.816994296236224,
            "unit": "iter/sec",
            "range": "stddev: 0.027528",
            "group": "node",
            "extra": "mean: 20.485 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 57.8037957183735,
            "unit": "iter/sec",
            "range": "stddev: 0.0015341",
            "group": "node",
            "extra": "mean: 17.300 msec\nrounds: 100"
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
          "pythonVersion": "3.10.12",
          "metadata": "postgres:12.14, rabbitmq:3.8.14-management"
        },
        "commit": {
          "id": "2a2353d3dd2712afda8f1ebbcf749c7cc99f06fd",
          "message": "`RemoteData`: Add the `is_cleaned` property (#6101)\n\nThis is a convenience method that will return the `KEY_EXTRA_CLEANED`\r\nextra, which is set to `True` when the `clean` method is called. The\r\n`is_empty` method is also updated to use this new property and shortcut\r\nif set to `True`. This saves the method from having to open a transport\r\nconnection.",
          "timestamp": "2023-08-14T10:37:00+02:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/2a2353d3dd2712afda8f1ebbcf749c7cc99f06fd",
          "distinct": true,
          "tree_id": "fedb0e63d149170bf5f5195b389f697160f60600"
        },
        "date": 1692002917527,
        "benches": [
          {
            "name": "tests/benchmark/test_archive.py::test_export[no-objects]",
            "value": 2.3379815761421763,
            "unit": "iter/sec",
            "range": "stddev: 0.028788",
            "group": "import-export",
            "extra": "mean: 427.72 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_export[with-objects]",
            "value": 2.2274726384026713,
            "unit": "iter/sec",
            "range": "stddev: 0.016510",
            "group": "import-export",
            "extra": "mean: 448.94 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[no-objects]",
            "value": 3.219367384522085,
            "unit": "iter/sec",
            "range": "stddev: 0.089295",
            "group": "import-export",
            "extra": "mean: 310.62 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[with-objects]",
            "value": 3.1754014058325595,
            "unit": "iter/sec",
            "range": "stddev: 0.080821",
            "group": "import-export",
            "extra": "mean: 314.92 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 2.2997710546408,
            "unit": "iter/sec",
            "range": "stddev: 0.031467",
            "group": "engine",
            "extra": "mean: 434.83 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.5121798518386045,
            "unit": "iter/sec",
            "range": "stddev: 0.10660",
            "group": "engine",
            "extra": "mean: 1.9524 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.5957860808342471,
            "unit": "iter/sec",
            "range": "stddev: 0.072437",
            "group": "engine",
            "extra": "mean: 1.6785 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.1443080940352196,
            "unit": "iter/sec",
            "range": "stddev: 0.20389",
            "group": "engine",
            "extra": "mean: 6.9296 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.1592618382842413,
            "unit": "iter/sec",
            "range": "stddev: 0.23062",
            "group": "engine",
            "extra": "mean: 6.2790 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.0161040874411977,
            "unit": "iter/sec",
            "range": "stddev: 0.047967",
            "group": "engine",
            "extra": "mean: 496.01 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.4640456242856784,
            "unit": "iter/sec",
            "range": "stddev: 0.096876",
            "group": "engine",
            "extra": "mean: 2.1550 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.5102289280112668,
            "unit": "iter/sec",
            "range": "stddev: 0.070951",
            "group": "engine",
            "extra": "mean: 1.9599 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.1280112875265653,
            "unit": "iter/sec",
            "range": "stddev: 0.15460",
            "group": "engine",
            "extra": "mean: 7.8118 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.14460862382339162,
            "unit": "iter/sec",
            "range": "stddev: 0.16126",
            "group": "engine",
            "extra": "mean: 6.9152 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 213.37765326161522,
            "unit": "iter/sec",
            "range": "stddev: 0.0020953",
            "group": "node",
            "extra": "mean: 4.6865 msec\nrounds: 173"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 90.68189714352671,
            "unit": "iter/sec",
            "range": "stddev: 0.0017144",
            "group": "node",
            "extra": "mean: 11.028 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 55.27238789625359,
            "unit": "iter/sec",
            "range": "stddev: 0.0021017",
            "group": "node",
            "extra": "mean: 18.092 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 152.0768075718094,
            "unit": "iter/sec",
            "range": "stddev: 0.00095139",
            "group": "node",
            "extra": "mean: 6.5756 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 35.51608185198218,
            "unit": "iter/sec",
            "range": "stddev: 0.029909",
            "group": "node",
            "extra": "mean: 28.156 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 39.03439308702598,
            "unit": "iter/sec",
            "range": "stddev: 0.0034484",
            "group": "node",
            "extra": "mean: 25.618 msec\nrounds: 100"
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
          "pythonVersion": "3.10.12",
          "metadata": "postgres:12.14, rabbitmq:3.8.14-management"
        },
        "commit": {
          "id": "35c57b9eb63b42531111f27ac7cc76e129ccd14a",
          "message": "Remove `with_dbenv` use in `aiida.orm`\n\nThis forces the import of `aiida.cmdline` in `aiida.orm` which doesn't\njust slow down, but also is conceptually wrong. The problem of the\n`with_dbenv` decorator is also that it cannot be imported inside a\nmethod to avoid the import cost when importing `aiida.orm` but has to be\nimported at the top in order to be used.",
          "timestamp": "2023-08-31T19:50:20+02:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/35c57b9eb63b42531111f27ac7cc76e129ccd14a",
          "distinct": true,
          "tree_id": "ab5206d3ee5bf88f3d46ec2222c7ec9485767f80"
        },
        "date": 1693504726239,
        "benches": [
          {
            "name": "tests/benchmark/test_archive.py::test_export[no-objects]",
            "value": 3.5529381907347095,
            "unit": "iter/sec",
            "range": "stddev: 0.052114",
            "group": "import-export",
            "extra": "mean: 281.46 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_export[with-objects]",
            "value": 3.638081226325736,
            "unit": "iter/sec",
            "range": "stddev: 0.0027729",
            "group": "import-export",
            "extra": "mean: 274.87 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[no-objects]",
            "value": 4.2878374988029515,
            "unit": "iter/sec",
            "range": "stddev: 0.059283",
            "group": "import-export",
            "extra": "mean: 233.22 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[with-objects]",
            "value": 4.224217346593485,
            "unit": "iter/sec",
            "range": "stddev: 0.055411",
            "group": "import-export",
            "extra": "mean: 236.73 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.36315542008995,
            "unit": "iter/sec",
            "range": "stddev: 0.061749",
            "group": "engine",
            "extra": "mean: 297.34 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.7803063955930779,
            "unit": "iter/sec",
            "range": "stddev: 0.025548",
            "group": "engine",
            "extra": "mean: 1.2815 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.9084170711561202,
            "unit": "iter/sec",
            "range": "stddev: 0.040047",
            "group": "engine",
            "extra": "mean: 1.1008 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.2052794446221776,
            "unit": "iter/sec",
            "range": "stddev: 0.072836",
            "group": "engine",
            "extra": "mean: 4.8714 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.23019020115266214,
            "unit": "iter/sec",
            "range": "stddev: 0.079767",
            "group": "engine",
            "extra": "mean: 4.3442 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.734335588183994,
            "unit": "iter/sec",
            "range": "stddev: 0.018237",
            "group": "engine",
            "extra": "mean: 365.72 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.6134205432550838,
            "unit": "iter/sec",
            "range": "stddev: 0.092334",
            "group": "engine",
            "extra": "mean: 1.6302 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.6994245936124255,
            "unit": "iter/sec",
            "range": "stddev: 0.045603",
            "group": "engine",
            "extra": "mean: 1.4297 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.16854706490938354,
            "unit": "iter/sec",
            "range": "stddev: 0.15394",
            "group": "engine",
            "extra": "mean: 5.9331 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.19275322289292693,
            "unit": "iter/sec",
            "range": "stddev: 0.096546",
            "group": "engine",
            "extra": "mean: 5.1880 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 368.39025229753094,
            "unit": "iter/sec",
            "range": "stddev: 0.00012001",
            "group": "node",
            "extra": "mean: 2.7145 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 139.32973657134406,
            "unit": "iter/sec",
            "range": "stddev: 0.00066405",
            "group": "node",
            "extra": "mean: 7.1772 msec\nrounds: 124"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 84.18325179292003,
            "unit": "iter/sec",
            "range": "stddev: 0.00074670",
            "group": "node",
            "extra": "mean: 11.879 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 239.3065210991682,
            "unit": "iter/sec",
            "range": "stddev: 0.00016817",
            "group": "node",
            "extra": "mean: 4.1787 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 57.47344938285394,
            "unit": "iter/sec",
            "range": "stddev: 0.0014058",
            "group": "node",
            "extra": "mean: 17.399 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 51.28160463242852,
            "unit": "iter/sec",
            "range": "stddev: 0.020311",
            "group": "node",
            "extra": "mean: 19.500 msec\nrounds: 100"
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
          "pythonVersion": "3.10.12",
          "metadata": "postgres:12.14, rabbitmq:3.8.14-management"
        },
        "commit": {
          "id": "4ef293a297ed6c7d3709cf165095a24d335fb31d",
          "message": "Devops: Update `pyproject.toml` configuration (#6085)\n\nAdded stricter rules for `mypy` and `pytest`. Suggestions taken after\r\nautomated analysis by the following tool:\r\nhttps://learn.scientific-python.org/development/guides/repo-review/",
          "timestamp": "2023-09-01T11:54:45+02:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/4ef293a297ed6c7d3709cf165095a24d335fb31d",
          "distinct": true,
          "tree_id": "83368cb48c9bdda40556b2b2ff33a0d316cb047b"
        },
        "date": 1693562688206,
        "benches": [
          {
            "name": "tests/benchmark/test_archive.py::test_export[no-objects]",
            "value": 2.8569476364690263,
            "unit": "iter/sec",
            "range": "stddev: 0.063612",
            "group": "import-export",
            "extra": "mean: 350.02 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_export[with-objects]",
            "value": 2.9613368746052497,
            "unit": "iter/sec",
            "range": "stddev: 0.013839",
            "group": "import-export",
            "extra": "mean: 337.69 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[no-objects]",
            "value": 3.7168827696586755,
            "unit": "iter/sec",
            "range": "stddev: 0.076183",
            "group": "import-export",
            "extra": "mean: 269.04 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[with-objects]",
            "value": 3.7181685545057004,
            "unit": "iter/sec",
            "range": "stddev: 0.068756",
            "group": "import-export",
            "extra": "mean: 268.95 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 2.8352064508921093,
            "unit": "iter/sec",
            "range": "stddev: 0.078352",
            "group": "engine",
            "extra": "mean: 352.71 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.670237417814454,
            "unit": "iter/sec",
            "range": "stddev: 0.049145",
            "group": "engine",
            "extra": "mean: 1.4920 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.7794362276018838,
            "unit": "iter/sec",
            "range": "stddev: 0.040103",
            "group": "engine",
            "extra": "mean: 1.2830 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.1696323951022991,
            "unit": "iter/sec",
            "range": "stddev: 0.16798",
            "group": "engine",
            "extra": "mean: 5.8951 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.185516099696357,
            "unit": "iter/sec",
            "range": "stddev: 0.099307",
            "group": "engine",
            "extra": "mean: 5.3904 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.2753845158925814,
            "unit": "iter/sec",
            "range": "stddev: 0.024386",
            "group": "engine",
            "extra": "mean: 439.49 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.5119736602347066,
            "unit": "iter/sec",
            "range": "stddev: 0.14592",
            "group": "engine",
            "extra": "mean: 1.9532 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.5541596103182156,
            "unit": "iter/sec",
            "range": "stddev: 0.098377",
            "group": "engine",
            "extra": "mean: 1.8045 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.14315775588370433,
            "unit": "iter/sec",
            "range": "stddev: 0.21233",
            "group": "engine",
            "extra": "mean: 6.9853 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.16635424245876523,
            "unit": "iter/sec",
            "range": "stddev: 0.16521",
            "group": "engine",
            "extra": "mean: 6.0113 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 287.4296461327808,
            "unit": "iter/sec",
            "range": "stddev: 0.00041343",
            "group": "node",
            "extra": "mean: 3.4791 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 115.47759091295742,
            "unit": "iter/sec",
            "range": "stddev: 0.00084929",
            "group": "node",
            "extra": "mean: 8.6597 msec\nrounds: 102"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 69.83610442601714,
            "unit": "iter/sec",
            "range": "stddev: 0.00079580",
            "group": "node",
            "extra": "mean: 14.319 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 191.85338202328094,
            "unit": "iter/sec",
            "range": "stddev: 0.00035573",
            "group": "node",
            "extra": "mean: 5.2123 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 48.5202999449206,
            "unit": "iter/sec",
            "range": "stddev: 0.0017572",
            "group": "node",
            "extra": "mean: 20.610 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 43.33579157199962,
            "unit": "iter/sec",
            "range": "stddev: 0.023477",
            "group": "node",
            "extra": "mean: 23.076 msec\nrounds: 100"
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
          "pythonVersion": "3.10.12",
          "metadata": "postgres:12.14, rabbitmq:3.8.14-management"
        },
        "commit": {
          "id": "f272e197e2992f445b2b51608a6ffe17a2a8f4c1",
          "message": "Caching: Add the `strict` argument configuration validation\n\nSo far, the caching configuration validation only considered whether the\ndefined identifiers were valid syntactically. This made it possible for\na user to specify a valid identifier but that didn't actually match a\nclass that can be imported or an entry point that cannot be loaded. If\nthis is due to a typo, the user may be confused why the caching config\nseems to be ignored.\n\nThe caching control functionality adds the `strict` argument, which when\nset to `True`, besides checking the syntax validity of an identifier,\nwill also try to import/load it and raise a `ValueError` if it fails. By\ndefault it is set to `False` to maintain backwards compatibility.",
          "timestamp": "2023-09-04T11:51:58+02:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/f272e197e2992f445b2b51608a6ffe17a2a8f4c1",
          "distinct": true,
          "tree_id": "b8becb4006331e51f88727270587ae1d8509d169"
        },
        "date": 1693821629884,
        "benches": [
          {
            "name": "tests/benchmark/test_archive.py::test_export[no-objects]",
            "value": 3.8129043850215663,
            "unit": "iter/sec",
            "range": "stddev: 0.0034863",
            "group": "import-export",
            "extra": "mean: 262.27 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_export[with-objects]",
            "value": 3.3640005868342286,
            "unit": "iter/sec",
            "range": "stddev: 0.058032",
            "group": "import-export",
            "extra": "mean: 297.27 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[no-objects]",
            "value": 4.420566562598779,
            "unit": "iter/sec",
            "range": "stddev: 0.067978",
            "group": "import-export",
            "extra": "mean: 226.22 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[with-objects]",
            "value": 4.863794061823375,
            "unit": "iter/sec",
            "range": "stddev: 0.0048831",
            "group": "import-export",
            "extra": "mean: 205.60 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.780476870494136,
            "unit": "iter/sec",
            "range": "stddev: 0.0044111",
            "group": "engine",
            "extra": "mean: 264.52 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.8053610262550909,
            "unit": "iter/sec",
            "range": "stddev: 0.065463",
            "group": "engine",
            "extra": "mean: 1.2417 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.9635215859283389,
            "unit": "iter/sec",
            "range": "stddev: 0.031331",
            "group": "engine",
            "extra": "mean: 1.0379 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.20574794598231183,
            "unit": "iter/sec",
            "range": "stddev: 0.15906",
            "group": "engine",
            "extra": "mean: 4.8603 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.23337107966945947,
            "unit": "iter/sec",
            "range": "stddev: 0.11728",
            "group": "engine",
            "extra": "mean: 4.2850 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.8679582538459685,
            "unit": "iter/sec",
            "range": "stddev: 0.069558",
            "group": "engine",
            "extra": "mean: 348.68 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.6703549528691138,
            "unit": "iter/sec",
            "range": "stddev: 0.064315",
            "group": "engine",
            "extra": "mean: 1.4917 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.7522976577829555,
            "unit": "iter/sec",
            "range": "stddev: 0.058725",
            "group": "engine",
            "extra": "mean: 1.3293 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.17743894614520753,
            "unit": "iter/sec",
            "range": "stddev: 0.15951",
            "group": "engine",
            "extra": "mean: 5.6357 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.20765205818638485,
            "unit": "iter/sec",
            "range": "stddev: 0.11891",
            "group": "engine",
            "extra": "mean: 4.8157 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 318.6204306323132,
            "unit": "iter/sec",
            "range": "stddev: 0.00043214",
            "group": "node",
            "extra": "mean: 3.1385 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 125.65921412748085,
            "unit": "iter/sec",
            "range": "stddev: 0.00068552",
            "group": "node",
            "extra": "mean: 7.9580 msec\nrounds: 120"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 78.1653945935571,
            "unit": "iter/sec",
            "range": "stddev: 0.0010240",
            "group": "node",
            "extra": "mean: 12.793 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 215.36508269920034,
            "unit": "iter/sec",
            "range": "stddev: 0.00036302",
            "group": "node",
            "extra": "mean: 4.6433 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 58.02062020580344,
            "unit": "iter/sec",
            "range": "stddev: 0.0017924",
            "group": "node",
            "extra": "mean: 17.235 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 51.83925124284485,
            "unit": "iter/sec",
            "range": "stddev: 0.022371",
            "group": "node",
            "extra": "mean: 19.290 msec\nrounds: 100"
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
          "pythonVersion": "3.10.12",
          "metadata": "postgres:12.14, rabbitmq:3.8.14-management"
        },
        "commit": {
          "id": "ae637d8c474a0071031c6a9bf6f65d2a924f2e81",
          "message": "CLI: Add missing entry point groups for `verdi plugin list`\n\nThe following groups were not part of the entry point group mapping:\n\n * `aiida.calculations.monitors`\n * `aiida.calculations.importers`\n\nThis made that they were not available as subcommands to\n`verdi plugin list`.",
          "timestamp": "2023-09-04T12:27:09+02:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/ae637d8c474a0071031c6a9bf6f65d2a924f2e81",
          "distinct": true,
          "tree_id": "adaf1ee9c3deb5d9cb7c2f6b06db1dc6e08a1b0b"
        },
        "date": 1693823881076,
        "benches": [
          {
            "name": "tests/benchmark/test_archive.py::test_export[no-objects]",
            "value": 2.5671471078699795,
            "unit": "iter/sec",
            "range": "stddev: 0.029876",
            "group": "import-export",
            "extra": "mean: 389.54 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_export[with-objects]",
            "value": 2.2371645704341367,
            "unit": "iter/sec",
            "range": "stddev: 0.084617",
            "group": "import-export",
            "extra": "mean: 446.99 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[no-objects]",
            "value": 3.2748758398710787,
            "unit": "iter/sec",
            "range": "stddev: 0.086191",
            "group": "import-export",
            "extra": "mean: 305.36 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[with-objects]",
            "value": 3.58789541605628,
            "unit": "iter/sec",
            "range": "stddev: 0.012493",
            "group": "import-export",
            "extra": "mean: 278.71 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 2.463747057189118,
            "unit": "iter/sec",
            "range": "stddev: 0.012978",
            "group": "engine",
            "extra": "mean: 405.89 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.545789574177113,
            "unit": "iter/sec",
            "range": "stddev: 0.087039",
            "group": "engine",
            "extra": "mean: 1.8322 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.6543659353807028,
            "unit": "iter/sec",
            "range": "stddev: 0.020520",
            "group": "engine",
            "extra": "mean: 1.5282 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.15563864655693507,
            "unit": "iter/sec",
            "range": "stddev: 0.25655",
            "group": "engine",
            "extra": "mean: 6.4251 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.16766630968099452,
            "unit": "iter/sec",
            "range": "stddev: 0.25445",
            "group": "engine",
            "extra": "mean: 5.9642 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.1996170733268077,
            "unit": "iter/sec",
            "range": "stddev: 0.025405",
            "group": "engine",
            "extra": "mean: 454.62 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.4744055320629513,
            "unit": "iter/sec",
            "range": "stddev: 0.079172",
            "group": "engine",
            "extra": "mean: 2.1079 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.5399019763517229,
            "unit": "iter/sec",
            "range": "stddev: 0.078197",
            "group": "engine",
            "extra": "mean: 1.8522 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.13580019447231823,
            "unit": "iter/sec",
            "range": "stddev: 0.22721",
            "group": "engine",
            "extra": "mean: 7.3638 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.15771679301399213,
            "unit": "iter/sec",
            "range": "stddev: 0.29833",
            "group": "engine",
            "extra": "mean: 6.3405 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 234.07548706426954,
            "unit": "iter/sec",
            "range": "stddev: 0.0013668",
            "group": "node",
            "extra": "mean: 4.2721 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 98.10874227402248,
            "unit": "iter/sec",
            "range": "stddev: 0.0011722",
            "group": "node",
            "extra": "mean: 10.193 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 51.52865418206881,
            "unit": "iter/sec",
            "range": "stddev: 0.0025805",
            "group": "node",
            "extra": "mean: 19.407 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 142.4980351871367,
            "unit": "iter/sec",
            "range": "stddev: 0.0010517",
            "group": "node",
            "extra": "mean: 7.0176 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 35.4224390623145,
            "unit": "iter/sec",
            "range": "stddev: 0.030353",
            "group": "node",
            "extra": "mean: 28.231 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 42.644679406566695,
            "unit": "iter/sec",
            "range": "stddev: 0.0025189",
            "group": "node",
            "extra": "mean: 23.450 msec\nrounds: 100"
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
          "pythonVersion": "3.10.12",
          "metadata": "postgres:12.14, rabbitmq:3.8.14-management"
        },
        "commit": {
          "id": "8e6e08dc780152333e4a6b6966469a98e51fe061",
          "message": "Refactor: Delay import of heavy packages to speed up import time (#6106)\n\nThe importing of packages `disk_objectstore`, `jsonschema`, `requests`,\r\n`plumpy` and `paramiko` are moved from top-level to inside the scopes\r\nwhere they are needed. This significantly improves the load time of the\r\n`aiida` package and its subpackages.\r\n\r\nThe `ProcessLauncher` utility had to be removed from resources that are\r\nexposed at a higher package level because it required the import of\r\n`plumpy` which has a non-negligible import time. This is a breaking\r\nchange but it is not expected to be used outside of `aiida-core`.",
          "timestamp": "2023-09-05T09:06:12+02:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/8e6e08dc780152333e4a6b6966469a98e51fe061",
          "distinct": true,
          "tree_id": "85fbb9967394e6a7e450f5156ad7ea1114ef7dd5"
        },
        "date": 1693898106862,
        "benches": [
          {
            "name": "tests/benchmark/test_archive.py::test_export[no-objects]",
            "value": 3.2904570176268058,
            "unit": "iter/sec",
            "range": "stddev: 0.057970",
            "group": "import-export",
            "extra": "mean: 303.91 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_export[with-objects]",
            "value": 3.3299847469216357,
            "unit": "iter/sec",
            "range": "stddev: 0.0043626",
            "group": "import-export",
            "extra": "mean: 300.30 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[no-objects]",
            "value": 4.175850100511153,
            "unit": "iter/sec",
            "range": "stddev: 0.061028",
            "group": "import-export",
            "extra": "mean: 239.47 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[with-objects]",
            "value": 4.133850657321898,
            "unit": "iter/sec",
            "range": "stddev: 0.063348",
            "group": "import-export",
            "extra": "mean: 241.91 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.1197240494263787,
            "unit": "iter/sec",
            "range": "stddev: 0.068812",
            "group": "engine",
            "extra": "mean: 320.54 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.748556674490287,
            "unit": "iter/sec",
            "range": "stddev: 0.041663",
            "group": "engine",
            "extra": "mean: 1.3359 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.8454776499414309,
            "unit": "iter/sec",
            "range": "stddev: 0.059003",
            "group": "engine",
            "extra": "mean: 1.1828 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.18861170691475113,
            "unit": "iter/sec",
            "range": "stddev: 0.14800",
            "group": "engine",
            "extra": "mean: 5.3019 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.21577877680840699,
            "unit": "iter/sec",
            "range": "stddev: 0.10549",
            "group": "engine",
            "extra": "mean: 4.6344 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.6729415630647466,
            "unit": "iter/sec",
            "range": "stddev: 0.039658",
            "group": "engine",
            "extra": "mean: 374.12 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.6018121575227793,
            "unit": "iter/sec",
            "range": "stddev: 0.10307",
            "group": "engine",
            "extra": "mean: 1.6616 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.6994736276710419,
            "unit": "iter/sec",
            "range": "stddev: 0.047211",
            "group": "engine",
            "extra": "mean: 1.4296 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.1694817204006311,
            "unit": "iter/sec",
            "range": "stddev: 0.13779",
            "group": "engine",
            "extra": "mean: 5.9003 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.1923790632716477,
            "unit": "iter/sec",
            "range": "stddev: 0.10379",
            "group": "engine",
            "extra": "mean: 5.1981 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 331.6348796671037,
            "unit": "iter/sec",
            "range": "stddev: 0.00054838",
            "group": "node",
            "extra": "mean: 3.0154 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 134.5263944923123,
            "unit": "iter/sec",
            "range": "stddev: 0.00057375",
            "group": "node",
            "extra": "mean: 7.4335 msec\nrounds: 119"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 75.01223065046653,
            "unit": "iter/sec",
            "range": "stddev: 0.0019003",
            "group": "node",
            "extra": "mean: 13.331 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 211.1897200548981,
            "unit": "iter/sec",
            "range": "stddev: 0.00078634",
            "group": "node",
            "extra": "mean: 4.7351 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 53.65434116138192,
            "unit": "iter/sec",
            "range": "stddev: 0.0019994",
            "group": "node",
            "extra": "mean: 18.638 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 47.86892692802067,
            "unit": "iter/sec",
            "range": "stddev: 0.023631",
            "group": "node",
            "extra": "mean: 20.890 msec\nrounds: 100"
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
          "pythonVersion": "3.10.12",
          "metadata": "postgres:12.14, rabbitmq:3.8.14-management"
        },
        "commit": {
          "id": "2071517849820e218a28d3968e45d211e8cd6247",
          "message": "Tests: Fix flaky work chain tests using `recwarn` fixture (#6112)\n\nThe tests were often failing because the `recwarn` fixture contained\r\ntwo records instead of one. The reason is that elsewhere in the code a\r\n`ResourceWarning` is emitted because an event-loop is not closed when\r\nanother one is created. Until this is fixed, the assertion is updated to\r\nnot check for the number of warnings emitted, but specifically to check\r\nthe expected warning message is present.",
          "timestamp": "2023-09-05T12:10:11+02:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/2071517849820e218a28d3968e45d211e8cd6247",
          "distinct": true,
          "tree_id": "f1896d5615c2caa3c4be75774a95f4392c0c37c8"
        },
        "date": 1693909153856,
        "benches": [
          {
            "name": "tests/benchmark/test_archive.py::test_export[no-objects]",
            "value": 3.350961892145201,
            "unit": "iter/sec",
            "range": "stddev: 0.059542",
            "group": "import-export",
            "extra": "mean: 298.42 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_export[with-objects]",
            "value": 3.487968917276618,
            "unit": "iter/sec",
            "range": "stddev: 0.0040560",
            "group": "import-export",
            "extra": "mean: 286.70 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[no-objects]",
            "value": 4.230709477964253,
            "unit": "iter/sec",
            "range": "stddev: 0.064873",
            "group": "import-export",
            "extra": "mean: 236.37 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[with-objects]",
            "value": 4.215855369988729,
            "unit": "iter/sec",
            "range": "stddev: 0.058962",
            "group": "import-export",
            "extra": "mean: 237.20 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.1748788407657353,
            "unit": "iter/sec",
            "range": "stddev: 0.073291",
            "group": "engine",
            "extra": "mean: 314.97 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.749425518706907,
            "unit": "iter/sec",
            "range": "stddev: 0.042784",
            "group": "engine",
            "extra": "mean: 1.3344 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.8546621218517849,
            "unit": "iter/sec",
            "range": "stddev: 0.077019",
            "group": "engine",
            "extra": "mean: 1.1701 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.19314194104646037,
            "unit": "iter/sec",
            "range": "stddev: 0.15504",
            "group": "engine",
            "extra": "mean: 5.1775 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.21590872560085064,
            "unit": "iter/sec",
            "range": "stddev: 0.10340",
            "group": "engine",
            "extra": "mean: 4.6316 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.7060525492884406,
            "unit": "iter/sec",
            "range": "stddev: 0.020849",
            "group": "engine",
            "extra": "mean: 369.54 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.6149490852068613,
            "unit": "iter/sec",
            "range": "stddev: 0.12363",
            "group": "engine",
            "extra": "mean: 1.6262 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.7068064464407166,
            "unit": "iter/sec",
            "range": "stddev: 0.028249",
            "group": "engine",
            "extra": "mean: 1.4148 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.1673348999205025,
            "unit": "iter/sec",
            "range": "stddev: 0.14736",
            "group": "engine",
            "extra": "mean: 5.9760 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.19171715034579462,
            "unit": "iter/sec",
            "range": "stddev: 0.16829",
            "group": "engine",
            "extra": "mean: 5.2160 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 341.72992169738455,
            "unit": "iter/sec",
            "range": "stddev: 0.00047995",
            "group": "node",
            "extra": "mean: 2.9263 msec\nrounds: 194"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 137.99719295622396,
            "unit": "iter/sec",
            "range": "stddev: 0.00067944",
            "group": "node",
            "extra": "mean: 7.2465 msec\nrounds: 113"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 75.29734758791012,
            "unit": "iter/sec",
            "range": "stddev: 0.0017868",
            "group": "node",
            "extra": "mean: 13.281 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 231.40548567071076,
            "unit": "iter/sec",
            "range": "stddev: 0.00025262",
            "group": "node",
            "extra": "mean: 4.3214 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 55.53448768375261,
            "unit": "iter/sec",
            "range": "stddev: 0.0016043",
            "group": "node",
            "extra": "mean: 18.007 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 47.75324570023874,
            "unit": "iter/sec",
            "range": "stddev: 0.023802",
            "group": "node",
            "extra": "mean: 20.941 msec\nrounds: 100"
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
          "pythonVersion": "3.10.12",
          "metadata": "postgres:12.14, rabbitmq:3.8.14-management"
        },
        "commit": {
          "id": "96667c8c63b0053e79c8a1531707890027f10e6a",
          "message": "ORM: Explicitly pass backend when constructing new entity\n\nWhenever an ORM entity instance instantiates another entry, it should\nexplicitly pass its own backend as the storage backend to use. Similarly,\nfunctions that accept a storage backend as an argument, should\nconsistently pass whenever instantiating a new entity or its collection.\n\nCo-Authored-By: Riccardo Bertossa <33728857+rikigigi@users.noreply.github.com>",
          "timestamp": "2023-09-05T12:41:32+02:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/96667c8c63b0053e79c8a1531707890027f10e6a",
          "distinct": true,
          "tree_id": "fa9449c73721ea70b84db2b9010edf1904ee5cca"
        },
        "date": 1693911122697,
        "benches": [
          {
            "name": "tests/benchmark/test_archive.py::test_export[no-objects]",
            "value": 2.745494724892138,
            "unit": "iter/sec",
            "range": "stddev: 0.069119",
            "group": "import-export",
            "extra": "mean: 364.23 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_export[with-objects]",
            "value": 2.8065751429274863,
            "unit": "iter/sec",
            "range": "stddev: 0.0062299",
            "group": "import-export",
            "extra": "mean: 356.31 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[no-objects]",
            "value": 3.539451439534438,
            "unit": "iter/sec",
            "range": "stddev: 0.072823",
            "group": "import-export",
            "extra": "mean: 282.53 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[with-objects]",
            "value": 3.5083774209903607,
            "unit": "iter/sec",
            "range": "stddev: 0.073564",
            "group": "import-export",
            "extra": "mean: 285.03 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 2.6835539064364675,
            "unit": "iter/sec",
            "range": "stddev: 0.082561",
            "group": "engine",
            "extra": "mean: 372.64 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.6192273714120572,
            "unit": "iter/sec",
            "range": "stddev: 0.040385",
            "group": "engine",
            "extra": "mean: 1.6149 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.7029265000200309,
            "unit": "iter/sec",
            "range": "stddev: 0.067619",
            "group": "engine",
            "extra": "mean: 1.4226 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.1600408548069071,
            "unit": "iter/sec",
            "range": "stddev: 0.15746",
            "group": "engine",
            "extra": "mean: 6.2484 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.18061798433985882,
            "unit": "iter/sec",
            "range": "stddev: 0.12277",
            "group": "engine",
            "extra": "mean: 5.5365 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.2033731551563545,
            "unit": "iter/sec",
            "range": "stddev: 0.031406",
            "group": "engine",
            "extra": "mean: 453.85 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.5067931331265526,
            "unit": "iter/sec",
            "range": "stddev: 0.059840",
            "group": "engine",
            "extra": "mean: 1.9732 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.5737000359463934,
            "unit": "iter/sec",
            "range": "stddev: 0.086973",
            "group": "engine",
            "extra": "mean: 1.7431 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.14093858459471034,
            "unit": "iter/sec",
            "range": "stddev: 0.15974",
            "group": "engine",
            "extra": "mean: 7.0953 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.1618715480881346,
            "unit": "iter/sec",
            "range": "stddev: 0.096730",
            "group": "engine",
            "extra": "mean: 6.1777 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 305.8099458534324,
            "unit": "iter/sec",
            "range": "stddev: 0.00021090",
            "group": "node",
            "extra": "mean: 3.2700 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 115.64996458353808,
            "unit": "iter/sec",
            "range": "stddev: 0.0010503",
            "group": "node",
            "extra": "mean: 8.6468 msec\nrounds: 101"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 69.52993865017373,
            "unit": "iter/sec",
            "range": "stddev: 0.0010175",
            "group": "node",
            "extra": "mean: 14.382 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 190.1377973491165,
            "unit": "iter/sec",
            "range": "stddev: 0.00056293",
            "group": "node",
            "extra": "mean: 5.2593 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 47.08810597166344,
            "unit": "iter/sec",
            "range": "stddev: 0.0019186",
            "group": "node",
            "extra": "mean: 21.237 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 40.83756082878065,
            "unit": "iter/sec",
            "range": "stddev: 0.027525",
            "group": "node",
            "extra": "mean: 24.487 msec\nrounds: 100"
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
          "pythonVersion": "3.10.12",
          "metadata": "postgres:12.14, rabbitmq:3.8.14-management"
        },
        "commit": {
          "id": "e1a5bd14cd096fcdb79d5d8f719aef12b3e2ef2a",
          "message": "Docs: Add links to Discourse server (#6111)\n\nThe Discourse server replaces the mailing list and Slack channel.\r\nThe README and documentation is updated accordingly.",
          "timestamp": "2023-09-05T15:05:35+02:00",
          "url": "https://github.com/aiidateam/aiida-core/commit/e1a5bd14cd096fcdb79d5d8f719aef12b3e2ef2a",
          "distinct": true,
          "tree_id": "b8c3a62c21edab2ff2262bd682f00df1c5f95bb8"
        },
        "date": 1693919659353,
        "benches": [
          {
            "name": "tests/benchmark/test_archive.py::test_export[no-objects]",
            "value": 3.2211373221452595,
            "unit": "iter/sec",
            "range": "stddev: 0.058847",
            "group": "import-export",
            "extra": "mean: 310.45 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_export[with-objects]",
            "value": 3.416444150954396,
            "unit": "iter/sec",
            "range": "stddev: 0.012341",
            "group": "import-export",
            "extra": "mean: 292.70 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[no-objects]",
            "value": 4.203307768879764,
            "unit": "iter/sec",
            "range": "stddev: 0.064634",
            "group": "import-export",
            "extra": "mean: 237.91 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_archive.py::test_import[with-objects]",
            "value": 4.216919117824277,
            "unit": "iter/sec",
            "range": "stddev: 0.060412",
            "group": "import-export",
            "extra": "mean: 237.14 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[basic-loop]",
            "value": 3.2090388355071844,
            "unit": "iter/sec",
            "range": "stddev: 0.075900",
            "group": "engine",
            "extra": "mean: 311.62 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-wc-loop]",
            "value": 0.7638172794223513,
            "unit": "iter/sec",
            "range": "stddev: 0.031157",
            "group": "engine",
            "extra": "mean: 1.3092 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-wc-loop]",
            "value": 0.884039646882844,
            "unit": "iter/sec",
            "range": "stddev: 0.10223",
            "group": "engine",
            "extra": "mean: 1.1312 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[serial-calcjob-loop]",
            "value": 0.19226514361730015,
            "unit": "iter/sec",
            "range": "stddev: 0.15298",
            "group": "engine",
            "extra": "mean: 5.2012 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_local[threaded-calcjob-loop]",
            "value": 0.21690843200096754,
            "unit": "iter/sec",
            "range": "stddev: 0.12713",
            "group": "engine",
            "extra": "mean: 4.6102 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[basic-loop]",
            "value": 2.761287376468683,
            "unit": "iter/sec",
            "range": "stddev: 0.022443",
            "group": "engine",
            "extra": "mean: 362.15 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-wc-loop]",
            "value": 0.6108172372737709,
            "unit": "iter/sec",
            "range": "stddev: 0.10678",
            "group": "engine",
            "extra": "mean: 1.6372 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-wc-loop]",
            "value": 0.7039030939741479,
            "unit": "iter/sec",
            "range": "stddev: 0.046259",
            "group": "engine",
            "extra": "mean: 1.4207 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[serial-calcjob-loop]",
            "value": 0.16883528124310995,
            "unit": "iter/sec",
            "range": "stddev: 0.13458",
            "group": "engine",
            "extra": "mean: 5.9229 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_engine.py::test_workchain_daemon[threaded-calcjob-loop]",
            "value": 0.18933719390018683,
            "unit": "iter/sec",
            "range": "stddev: 0.090198",
            "group": "engine",
            "extra": "mean: 5.2816 sec\nrounds: 10"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 328.67438380432213,
            "unit": "iter/sec",
            "range": "stddev: 0.00051598",
            "group": "node",
            "extra": "mean: 3.0425 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 129.12124971595034,
            "unit": "iter/sec",
            "range": "stddev: 0.0017999",
            "group": "node",
            "extra": "mean: 7.7447 msec\nrounds: 114"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store_with_object",
            "value": 70.10832470906333,
            "unit": "iter/sec",
            "range": "stddev: 0.0044734",
            "group": "node",
            "extra": "mean: 14.264 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 228.14684286401334,
            "unit": "iter/sec",
            "range": "stddev: 0.00012748",
            "group": "node",
            "extra": "mean: 4.3831 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 55.046960630930386,
            "unit": "iter/sec",
            "range": "stddev: 0.0017858",
            "group": "node",
            "extra": "mean: 18.166 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_with_object",
            "value": 49.02496235434326,
            "unit": "iter/sec",
            "range": "stddev: 0.022500",
            "group": "node",
            "extra": "mean: 20.398 msec\nrounds: 100"
          }
        ]
      }
    ]
  }
}