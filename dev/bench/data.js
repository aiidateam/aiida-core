window.BENCHMARK_DATA = {
  "lastUpdate": 1596625502925,
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
        "date": 1596625489856,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 274.7420561312717,
            "unit": "iter/sec",
            "range": "stddev: 0.0002045152706193347",
            "extra": "mean: 3.639777666664183 msec\nrounds: 135"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 109.02127941982381,
            "unit": "iter/sec",
            "range": "stddev: 0.0005073032450718767",
            "extra": "mean: 9.17252122999912 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 164.64756910417174,
            "unit": "iter/sec",
            "range": "stddev: 0.0002110341217648663",
            "extra": "mean: 6.073578889994451 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 38.98755793337806,
            "unit": "iter/sec",
            "range": "stddev: 0.013487641592083795",
            "extra": "mean: 25.649208440005395 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_calcfunction",
            "value": 6.166775142132536,
            "unit": "iter/sec",
            "range": "stddev: 0.01854520963248724",
            "extra": "mean: 162.15930968000066 msec\nrounds: 50"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_workchain",
            "value": 2.748578888390699,
            "unit": "iter/sec",
            "range": "stddev: 0.029474910664262503",
            "extra": "mean: 363.8243763800074 msec\nrounds: 50"
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
          "id": "e283e8267e994897129a1935fe7b714ac9480916",
          "message": "Update test_nodes.py",
          "timestamp": "2020-08-05T12:00:23+01:00",
          "tree_id": "302b17f31d6e2181b596c2116e1b7c606b06b92c",
          "url": "https://github.com/aiidateam/aiida-core/commit/e283e8267e994897129a1935fe7b714ac9480916"
        },
        "date": 1596625502224,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 248.6927738634807,
            "unit": "iter/sec",
            "range": "stddev: 0.0005368978776683586",
            "extra": "mean: 4.021025558824429 msec\nrounds: 136"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 97.22413987384623,
            "unit": "iter/sec",
            "range": "stddev: 0.0011828504161635796",
            "extra": "mean: 10.28551141000122 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 130.51556595592248,
            "unit": "iter/sec",
            "range": "stddev: 0.0008084414077911889",
            "extra": "mean: 7.661921340001072 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 31.245948855321213,
            "unit": "iter/sec",
            "range": "stddev: 0.002864108678353053",
            "extra": "mean: 32.00414891000179 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_calcfunction",
            "value": 4.879749116927658,
            "unit": "iter/sec",
            "range": "stddev: 0.02533864064619494",
            "extra": "mean: 204.9285682600032 msec\nrounds: 50"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_workchain",
            "value": 2.2616225211068115,
            "unit": "iter/sec",
            "range": "stddev: 0.0430366166056481",
            "extra": "mean: 442.16043599999693 msec\nrounds: 50"
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
          "id": "e283e8267e994897129a1935fe7b714ac9480916",
          "message": "Update test_nodes.py",
          "timestamp": "2020-08-05T12:00:23+01:00",
          "tree_id": "302b17f31d6e2181b596c2116e1b7c606b06b92c",
          "url": "https://github.com/aiidateam/aiida-core/commit/e283e8267e994897129a1935fe7b714ac9480916"
        },
        "date": 1596625478283,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmark/test_nodes.py::test_store_backend",
            "value": 797.4237580526371,
            "unit": "iter/sec",
            "range": "stddev: 0.0005099662909956973",
            "extra": "mean: 1.2540383828568988 msec\nrounds: 175"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_store",
            "value": 177.4589591646606,
            "unit": "iter/sec",
            "range": "stddev: 0.001074809265287746",
            "extra": "mean: 5.635105743363005 msec\nrounds: 113"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete_backend",
            "value": 179.3296905435707,
            "unit": "iter/sec",
            "range": "stddev: 0.0005030814947710931",
            "extra": "mean: 5.576321450000137 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_delete",
            "value": 37.50655793726516,
            "unit": "iter/sec",
            "range": "stddev: 0.001774577435559187",
            "extra": "mean: 26.6620040600003 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_calcfunction",
            "value": 6.737670325231581,
            "unit": "iter/sec",
            "range": "stddev: 0.02027261154863155",
            "extra": "mean: 148.41925350000395 msec\nrounds: 50"
          },
          {
            "name": "tests/benchmark/test_nodes.py::test_workchain",
            "value": 3.302415998073986,
            "unit": "iter/sec",
            "range": "stddev: 0.03368947933989457",
            "extra": "mean: 302.8086106000012 msec\nrounds: 50"
          }
        ]
      }
    ]
  }
}