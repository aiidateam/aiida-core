window.BENCHMARK_DATA = {
  "lastUpdate": 1596614194425,
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
    ],
    "Benchmark on ubuntu-latest with django": [
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
        "date": 1594913541768,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 180.24419902251145,
            "unit": "iter/sec",
            "range": "stddev: 0.0007032042410700108",
            "extra": "mean: 5.548028759999681 msec\nrounds: 100"
          }
        ]
      }
    ],
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
          "id": "6e45865a238c4885471eeeebba6258e9ebb8e45b",
          "message": "Update benchmark.yml",
          "timestamp": "2020-07-16T16:44:57+01:00",
          "tree_id": "5fceeb2f9acd95a456eaf1ce9873a5ec78fcafda",
          "url": "https://github.com/aiidateam/aiida-core/commit/6e45865a238c4885471eeeebba6258e9ebb8e45b"
        },
        "date": 1594914502627,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 115.2278490482805,
            "unit": "iter/sec",
            "range": "stddev: 0.00022098278209678026",
            "extra": "mean: 8.678457579998735 msec\nrounds: 100"
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
          "id": "a256b6e52d3325532255dbf3c8f7dc4093a3d8e2",
          "message": "Merge branch 'develop' into benchmark-test-cjs",
          "timestamp": "2020-08-05T07:42:18+01:00",
          "tree_id": "992558b9e06efcce6b98682f74f9256aba4c715b",
          "url": "https://github.com/aiidateam/aiida-core/commit/a256b6e52d3325532255dbf3c8f7dc4093a3d8e2"
        },
        "date": 1596609974704,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 122.27299641003899,
            "unit": "iter/sec",
            "range": "stddev: 0.0007167117963143431",
            "extra": "mean: 8.178420660000256 msec\nrounds: 100"
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
          "id": "6e45865a238c4885471eeeebba6258e9ebb8e45b",
          "message": "Update benchmark.yml",
          "timestamp": "2020-07-16T16:44:57+01:00",
          "tree_id": "5fceeb2f9acd95a456eaf1ce9873a5ec78fcafda",
          "url": "https://github.com/aiidateam/aiida-core/commit/6e45865a238c4885471eeeebba6258e9ebb8e45b"
        },
        "date": 1594914530236,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 192.49545231383794,
            "unit": "iter/sec",
            "range": "stddev: 0.0008580438898631543",
            "extra": "mean: 5.194927921567905 msec\nrounds: 102"
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
          "id": "a256b6e52d3325532255dbf3c8f7dc4093a3d8e2",
          "message": "Merge branch 'develop' into benchmark-test-cjs",
          "timestamp": "2020-08-05T07:42:18+01:00",
          "tree_id": "992558b9e06efcce6b98682f74f9256aba4c715b",
          "url": "https://github.com/aiidateam/aiida-core/commit/a256b6e52d3325532255dbf3c8f7dc4093a3d8e2"
        },
        "date": 1596609973918,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 186.99695574940264,
            "unit": "iter/sec",
            "range": "stddev: 0.0003543803807064963",
            "extra": "mean: 5.347680639999908 msec\nrounds: 100"
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
        "date": 1596614193988,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 1069.8260731703901,
            "unit": "iter/sec",
            "range": "stddev: 0.0002130300512098516",
            "extra": "mean: 934.7313783786713 usec\nrounds: 222"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 237.6806252163459,
            "unit": "iter/sec",
            "range": "stddev: 0.0005556159526390421",
            "extra": "mean: 4.207326529412156 msec\nrounds: 136"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 238.64205055780678,
            "unit": "iter/sec",
            "range": "stddev: 0.0006709560241102778",
            "extra": "mean: 4.190376329999594 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 48.84833301631936,
            "unit": "iter/sec",
            "range": "stddev: 0.0015444266585462735",
            "extra": "mean: 20.471527650000212 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_calcfunction",
            "value": 8.983072854463394,
            "unit": "iter/sec",
            "range": "stddev: 0.017483383153065354",
            "extra": "mean: 111.32048200000213 msec\nrounds: 50"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_workchain",
            "value": 4.333458509789095,
            "unit": "iter/sec",
            "range": "stddev: 0.028723228034663838",
            "extra": "mean: 230.7625647600048 msec\nrounds: 50"
          }
        ]
      }
    ]
  }
}