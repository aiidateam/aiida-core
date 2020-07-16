window.BENCHMARK_DATA = {
  "lastUpdate": 1594910122022,
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
      }
    ]
  }
}