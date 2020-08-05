window.BENCHMARK_DATA = {
  "lastUpdate": 1596614848421,
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
      }
    ]
  }
}