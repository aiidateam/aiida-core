window.BENCHMARK_DATA = {
  "lastUpdate": 1594913512546,
  "repoUrl": "https://github.com/aiidateam/aiida-core",
  "entries": {
    "Benchmark on ubuntu-latest": [
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
          "id": "9679afe7ce7b6fb5cc2f5ed53ebf4ba132a57bba",
          "message": "Update benchmark.yml",
          "timestamp": "2020-07-16T15:31:39+01:00",
          "tree_id": "795041457a0230860d8b1012909dee482b76a124",
          "url": "https://github.com/aiidateam/aiida-core/commit/9679afe7ce7b6fb5cc2f5ed53ebf4ba132a57bba"
        },
        "date": 1594910121512,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 203.6135164523408,
            "unit": "iter/sec",
            "range": "stddev: 0.00030139457489018116",
            "extra": "mean: 4.911265310002477 msec\nrounds: 100"
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
          "id": "9679afe7ce7b6fb5cc2f5ed53ebf4ba132a57bba",
          "message": "Update benchmark.yml",
          "timestamp": "2020-07-16T15:31:39+01:00",
          "tree_id": "795041457a0230860d8b1012909dee482b76a124",
          "url": "https://github.com/aiidateam/aiida-core/commit/9679afe7ce7b6fb5cc2f5ed53ebf4ba132a57bba"
        },
        "date": 1594910125393,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 104.9047126262413,
            "unit": "iter/sec",
            "range": "stddev: 0.0007878892639694616",
            "extra": "mean: 9.532460219998313 msec\nrounds: 100"
          }
        ]
      }
    ],
    "Benchmark on ubuntu-latest with sqlalchemy": [
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
          "id": "3764bbc348790a5e2a40b1506d7adb802aa5e1ed",
          "message": "turn-off ci test (temporarily)",
          "timestamp": "2020-07-16T16:28:33+01:00",
          "tree_id": "5a31a34d7701d4465f0c45c11f8a790fb9259d77",
          "url": "https://github.com/aiidateam/aiida-core/commit/3764bbc348790a5e2a40b1506d7adb802aa5e1ed"
        },
        "date": 1594913512054,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 130.58935412992292,
            "unit": "iter/sec",
            "range": "stddev: 0.0005085099741704551",
            "extra": "mean: 7.657592050000517 msec\nrounds: 100"
          }
        ]
      }
    ]
  }
}