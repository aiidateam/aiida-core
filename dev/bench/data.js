window.BENCHMARK_DATA = {
  "lastUpdate": 1596625443777,
  "repoUrl": "https://github.com/aiidateam/aiida-core",
  "entries": {
    "ubuntu-latest with sqlalchemy [ci skip]": [
      {
        "commit": {
          "author": {
            "email": "chrisj_sewell@hotmail.com",
            "name": "Chris Sewell",
            "username": "chrisjsewell"
          },
          "committer": {
            "email": "chrisj_sewell@hotmail.com",
            "name": "Chris Sewell",
            "username": "chrisjsewell"
          },
          "distinct": true,
          "id": "e227fdeb4ab178a976c3049281812ff6b5999602",
          "message": "Update ci.yml",
          "timestamp": "2020-08-05T09:03:23+01:00",
          "tree_id": "6d500bf7a3e74835201f660311552e13466a3e2d",
          "url": "https://github.com/aiidateam/aiida-core/commit/e227fdeb4ab178a976c3049281812ff6b5999602"
        },
        "date": 1596614827064,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 253.59158531822152,
            "unit": "iter/sec",
            "range": "stddev: 0.001225484276932371",
            "extra": "mean: 3.943348509553823 msec\nrounds: 157"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 113.00704027080876,
            "unit": "iter/sec",
            "range": "stddev: 0.001006747755738709",
            "extra": "mean: 8.849006199999678 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 172.46096266351353,
            "unit": "iter/sec",
            "range": "stddev: 0.000820131795128979",
            "extra": "mean: 5.798413649998508 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 45.51548160200394,
            "unit": "iter/sec",
            "range": "stddev: 0.0019417712257783848",
            "extra": "mean: 21.970546389999583 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_calcfunction",
            "value": 6.736920710349332,
            "unit": "iter/sec",
            "range": "stddev: 0.01840880991984833",
            "extra": "mean: 148.43576805999646 msec\nrounds: 50"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_workchain",
            "value": 3.0597400340640095,
            "unit": "iter/sec",
            "range": "stddev: 0.026097483229442345",
            "extra": "mean: 326.8251514399998 msec\nrounds: 50"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "chrisj_sewell@hotmail.com",
            "name": "Chris Sewell",
            "username": "chrisjsewell"
          },
          "committer": {
            "email": "chrisj_sewell@hotmail.com",
            "name": "Chris Sewell",
            "username": "chrisjsewell"
          },
          "distinct": true,
          "id": "c70b9c977b5a7bffa2840dadd7a899b941ce312a",
          "message": "add tests",
          "timestamp": "2020-08-05T08:52:59+01:00",
          "tree_id": "094bb7aade583d53297f2848965bd93f477d92ad",
          "url": "https://github.com/aiidateam/aiida-core/commit/c70b9c977b5a7bffa2840dadd7a899b941ce312a"
        },
        "date": 1596618275052,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 259.92930459285884,
            "unit": "iter/sec",
            "range": "stddev: 0.000258777495114052",
            "extra": "mean: 3.847199920633625 msec\nrounds: 126"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 101.92309442442853,
            "unit": "iter/sec",
            "range": "stddev: 0.0009875844779563706",
            "extra": "mean: 9.8113190700019 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 150.4962327331674,
            "unit": "iter/sec",
            "range": "stddev: 0.0008412244319780143",
            "extra": "mean: 6.64468459999938 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 39.976294632942356,
            "unit": "iter/sec",
            "range": "stddev: 0.0018511809152728176",
            "extra": "mean: 25.014824639999347 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_calcfunction",
            "value": 6.007422872385487,
            "unit": "iter/sec",
            "range": "stddev: 0.021623121275687694",
            "extra": "mean: 166.46073054000112 msec\nrounds: 50"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_workchain",
            "value": 2.5952117563079256,
            "unit": "iter/sec",
            "range": "stddev: 0.033840187708945035",
            "extra": "mean: 385.32501156000023 msec\nrounds: 50"
          }
        ]
      }
    ],
    "ubuntu-latest with django [ci skip]": [
      {
        "commit": {
          "author": {
            "email": "chrisj_sewell@hotmail.com",
            "name": "Chris Sewell",
            "username": "chrisjsewell"
          },
          "committer": {
            "email": "chrisj_sewell@hotmail.com",
            "name": "Chris Sewell",
            "username": "chrisjsewell"
          },
          "distinct": true,
          "id": "e227fdeb4ab178a976c3049281812ff6b5999602",
          "message": "Update ci.yml",
          "timestamp": "2020-08-05T09:03:23+01:00",
          "tree_id": "6d500bf7a3e74835201f660311552e13466a3e2d",
          "url": "https://github.com/aiidateam/aiida-core/commit/e227fdeb4ab178a976c3049281812ff6b5999602"
        },
        "date": 1596614847880,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 975.4904815666273,
            "unit": "iter/sec",
            "range": "stddev: 0.00026224908753781645",
            "extra": "mean: 1.025125328126227 msec\nrounds: 192"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 206.9704873537671,
            "unit": "iter/sec",
            "range": "stddev: 0.0006569644791628286",
            "extra": "mean: 4.831606731885095 msec\nrounds: 138"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 214.6422591487697,
            "unit": "iter/sec",
            "range": "stddev: 0.00032159830158901996",
            "extra": "mean: 4.658914809999715 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 42.10094843997962,
            "unit": "iter/sec",
            "range": "stddev: 0.002213753476042013",
            "extra": "mean: 23.7524340199991 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_calcfunction",
            "value": 7.784309980113376,
            "unit": "iter/sec",
            "range": "stddev: 0.022271581503572738",
            "extra": "mean: 128.46353788000556 msec\nrounds: 50"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_workchain",
            "value": 3.8718428647525993,
            "unit": "iter/sec",
            "range": "stddev: 0.03141803113426121",
            "extra": "mean: 258.27494423999497 msec\nrounds: 50"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "chrisj_sewell@hotmail.com",
            "name": "Chris Sewell",
            "username": "chrisjsewell"
          },
          "committer": {
            "email": "chrisj_sewell@hotmail.com",
            "name": "Chris Sewell",
            "username": "chrisjsewell"
          },
          "distinct": true,
          "id": "c70b9c977b5a7bffa2840dadd7a899b941ce312a",
          "message": "add tests",
          "timestamp": "2020-08-05T08:52:59+01:00",
          "tree_id": "094bb7aade583d53297f2848965bd93f477d92ad",
          "url": "https://github.com/aiidateam/aiida-core/commit/c70b9c977b5a7bffa2840dadd7a899b941ce312a"
        },
        "date": 1596618297805,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 789.7207021411292,
            "unit": "iter/sec",
            "range": "stddev: 0.00019945197325431594",
            "extra": "mean: 1.2662704640878115 msec\nrounds: 181"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 160.53490770640826,
            "unit": "iter/sec",
            "range": "stddev: 0.0009021792151035201",
            "extra": "mean: 6.22917479000165 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 153.9367015454929,
            "unit": "iter/sec",
            "range": "stddev: 0.001033495645587714",
            "extra": "mean: 6.496176609997519 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 34.67008671817223,
            "unit": "iter/sec",
            "range": "stddev: 0.004205909146886394",
            "extra": "mean: 28.843308300000672 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_calcfunction",
            "value": 6.02453170441198,
            "unit": "iter/sec",
            "range": "stddev: 0.02307988579711844",
            "extra": "mean: 165.98800522000147 msec\nrounds: 50"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_workchain",
            "value": 2.9721102003721183,
            "unit": "iter/sec",
            "range": "stddev: 0.03247905677013635",
            "extra": "mean: 336.4612792199955 msec\nrounds: 50"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "chrisj_sewell@hotmail.com",
            "name": "Chris Sewell",
            "username": "chrisjsewell"
          },
          "committer": {
            "email": "chrisj_sewell@hotmail.com",
            "name": "Chris Sewell",
            "username": "chrisjsewell"
          },
          "distinct": true,
          "id": "576cbf505afbc5a3268b0576c28b73beff026ce3",
          "message": "Update test_nodes.py",
          "timestamp": "2020-08-05T12:00:36+01:00",
          "tree_id": "e4b037bd66901f779641d247a812e6446e5f1528",
          "url": "https://github.com/aiidateam/aiida-core/commit/576cbf505afbc5a3268b0576c28b73beff026ce3"
        },
        "date": 1596625443252,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 1182.498515965622,
            "unit": "iter/sec",
            "range": "stddev: 0.00017326251659363173",
            "extra": "mean: 845.6670232549134 usec\nrounds: 215"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 247.79202511470402,
            "unit": "iter/sec",
            "range": "stddev: 0.0008033667771898908",
            "extra": "mean: 4.03564238815634 msec\nrounds: 152"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 261.6035880335696,
            "unit": "iter/sec",
            "range": "stddev: 0.0005100162134566177",
            "extra": "mean: 3.822577539997951 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 55.809076439615204,
            "unit": "iter/sec",
            "range": "stddev: 0.0014574656515329632",
            "extra": "mean: 17.918232369997895 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_calcfunction",
            "value": 10.25491412649457,
            "unit": "iter/sec",
            "range": "stddev: 0.020565350904558872",
            "extra": "mean: 97.51422466000008 msec\nrounds: 50"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_workchain",
            "value": 4.867534198096861,
            "unit": "iter/sec",
            "range": "stddev: 0.0309682788645429",
            "extra": "mean: 205.4428298400012 msec\nrounds: 50"
          }
        ]
      }
    ]
  }
}