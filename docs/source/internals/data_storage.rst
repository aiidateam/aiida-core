.. _internal_architecture:data-storage:

************
Data storage
************

.. todo::

    .. _internal_architecture:orm:database:

    title: Database schema & migrations

    `#4035`_

    .. _internal_architecture:orm:repository:

    title: File repository

    `#4036`_

.. _internal_architecture:orm:export:

Export archive
==============

An AiiDA export file is an archive of ``.zip`` or ``.tar.gz`` format with the following content:

* ``metadata.json`` file containing information on the version of AiiDA as well as the database schema.
* ``data.json`` file containing the exported nodes and their links.
* ``nodes/`` directory containing the repository files corresponding to the exported nodes.

.. _metadata-json:

``metadata.json``
-----------------

This file contains important information, and it is necessary for the correct interpretation of ``data.json``.
Apart from the data schema, the AiiDA and export versions are also mentioned.
This is used to avoid any incompatibilities among different versions of AiiDA.
It should be noted that the schema described in ``metadata.json`` is related to the data itself - abstracted schema focused on the extracted information - and not how the data is stored in the database (database schema).
This makes the import/export mechanism transparent to the database system used, backend selected and how the data is organised in the database (database schema).

Let's have a look at the contents of ``metadata.json``:

.. code-block:: json

    {
      "export_version": "0.7",
      "aiida_version": "1.0.0",
      "export_parameters": {
        "graph_traversal_rules": {
          "input_calc_forward": false,
          "input_calc_backward": true,
          "create_forward": true,
          "create_backward": true,
          "return_forward": true,
          "return_backward": false,
          "input_work_forward": false,
          "input_work_backward": true,
          "call_calc_forward": true,
          "call_calc_backward": false,
          "call_work_forward": true,
          "call_work_backward": false
        },
        "entities_starting_set": {
          "Node": ["1024e35e-166b-4104-95f6-c1706df4ce15"]
        },
        "include_comments": true,
        "include_logs": false
      },
      "unique_identifiers": {
        "Computer": "uuid",
        "Group": "uuid",
        "User": "email",
        "Node": "uuid",
        "Log": "uuid",
        "Comment": "uuid"
      },
      "all_fields_info": {
        "Computer": {
          "transport_type": {},
          "hostname": {},
          "description": {},
          "scheduler_type": {},
          "metadata": {},
          "uuid": {},
          "name": {}
        },
        "User": {
          "last_name": {},
          "first_name": {},
          "institution": {},
          "email": {}
        },
        "Node": {
          "ctime": {
            "convert_type": "date"
          },
          "uuid": {},
          "mtime": {
            "convert_type": "date"
          },
          "node_type": {},
          "label": {},
          "user": {
            "related_name": "dbnodes",
            "requires": "User"
          },
          "dbcomputer": {
            "related_name": "dbnodes",
            "requires": "Computer"
          },
          "description": {},
          "process_type": {}
        },
        "Group": {
          "description": {},
          "user": {
            "related_name": "dbgroups",
            "requires": "User"
          },
          "time": {
            "convert_type": "date"
          },
          "type_string": {},
          "uuid": {},
          "label": {}
        },
        "Log": {
          "uuid": {},
          "time": {
            "convert_type": "date"
          },
          "loggername": {},
          "levelname": {},
          "message": {},
          "metadata": {},
          "dbnode": {
            "requires": "Node",
            "related_name": "dblogs"
          }
        },
        "Comment": {
          "uuid": {},
          "ctime": {
            "convert_type": "date"
          },
          "mtime": {
            "convert_type": "date"
          },
          "content": {},
          "dbnode": {
            "related_name": "dbcomments",
            "requires": "Node"
          },
          "user": {
            "related_name": "dbcomments",
            "requires": "User"
          }
        }
      }
    }

At the beginning of the file, we see the version of the export file and the version of the AiiDA code.

The entities that are exported are mentioned in *unique_identifiers* with their respective unique identifiers.
Knowing the unique IDs is useful for duplicate avoidance (in order to avoid the insertion of the node multiple times).

Then in *all_fields_info*, the properties of each entity are mentioned.
The correlations with other entities are also mentioned.
For example, the entity *Node* is related to a *Computer* and a *User*.
The corresponding entity names appear nested next to the properties to show this correlation.

.. note::

    If you have migrated an export archive to the newest export version, there may be an extra entry in ``metadata.json``.
    This simply states from which export version the archive was migrated.

.. note::

    If you supply an old export archive that the current AiiDA code does not support, ``verdi import`` will automatically try to migrate the archive by calling ``verdi export migrate``.

.. _data-json:

``data.json``
-------------

A sample of the ``data.json`` file follows:

.. code-block:: json

    {
      "links_uuid": [
        {
          "output": "1024e35e-166b-4104-95f6-c1706df4ce15",
          "label": "parameters",
          "input": "628ba258-ccc1-47bf-bab7-8aee64b563ea",
          "type": "input_calc"
        }
      ],
      "export_data": {
        "User": {
          "2": {
            "first_name": "AiiDA",
            "last_name": "theossrv2",
            "institution": "EPFL, Lausanne",
            "email": "aiida@theossrv2.epfl.ch"
          }
        },
        "Computer": {
          "1": {
            "name": "theospc14-direct",
            "description": "theospc14 (N. Mounet's PC) with direct scheduler",
            "hostname": "theospc14.epfl.ch",
            "transport_type": "ssh",
            "metadata": {
              "default_mpiprocs_per_machine": 8,
              "workdir": "/scratch/{username}/aiida_run/",
              "append_text": "",
              "prepend_text": "",
              "mpirun_command": ["mpirun", "-np", "{tot_num_mpiprocs}"]
            },
            "scheduler_type": "direct",
            "uuid": "fb7729ff-8254-4bc0-bbec-acbdb573cfe2"
          }
        },
        "Node": {
          "5921143": {
            "uuid": "628ba258-ccc1-47bf-bab7-8aee64b563ea",
            "description": "",
            "dbcomputer": 1,
            "label": "",
            "user": 2,
            "mtime": "2016-08-21T11:55:53.132925",
            "node_type": "data.dict.Dict.",
            "ctime": "2016-08-21T11:55:53.118306",
            "process_type": ""
          },
          "20063": {
            "uuid": "1024e35e-166b-4104-95f6-c1706df4ce15",
            "description": "",
            "dbcomputer": 1,
            "label": "",
            "user": 2,
            "mtime": "2016-02-16T10:33:54.095973",
            "process_type": "aiida.calculations:codtools.ciffilter",
            "node_type": "process.calculation.calcjob.CalcJobNode.",
            "ctime": "2015-10-02T20:08:06.628472"
          }
        },
        "Comment": {
          "1": {
            "uuid": "8c165836-6ae1-4ae8-8cf1-fb111abc483e",
            "ctime": "2016-08-21T11:56:05.501162",
            "mtime": "2016-08-21T11:56:05.501697",
            "content": "vc-relax calculation with cold smearing",
            "dbnode": 20063,
            "user": 2
          }
        }
      },
      "groups_uuid": {},
      "node_attributes": {
        "5921143": {
          "CONTROL": {
            "calculation": "vc-relax",
            "restart_mode": "from_scratch",
            "max_seconds": 83808
          },
          "ELECTRONS": {
            "electron_maxstep": 100,
            "conv_thr": 3.6e-10
          },
          "SYSTEM": {
            "ecutwfc": 90.0,
            "input_dft": "vdw-df2-c09",
            "occupations": "smearing",
            "degauss": 0.02,
            "smearing": "cold",
            "ecutrho": 1080.0
          }
        },
        "20063": {
          "retrieve_list": [
            "aiida.out",
            "aiida.err",
            "_scheduler-stdout.txt",
            "_scheduler-stderr.txt"
          ],
          "last_job_info": {
            "job_state": "DONE",
            "job_id": "13489"
          },
          "scheduler_state": "DONE",
          "parser": "codtools.ciffilter",
          "linkname_retrieved": "retrieved",
          "jobresource_params": {
            "num_machines": 1,
            "num_mpiprocs_per_machine": 1,
            "default_mpiprocs_per_machine": 8
          },
          "remote_workdir": "/scratch/aiida/aiida_run/10/24/e35e-166b-4104-95f6-c1706df4ce15",
          "process_state": "finished",
          "max_wallclock_seconds": 900,
          "retrieve_singlefile_list": [],
          "scheduler_lastchecktime": "2015-10-02T20:30:36.481951+00:00",
          "job_id": "13489",
          "exit_status": 0,
          "process_status": null,
          "process_label": "vc-relax",
          "sealed": true
        }
      },
      "node_extras": {
        "5921143": {},
        "20063": {}
      }
    }

At the start of the JSON file shown above, the links among the various AiiDA nodes are stated (*links_uuid* field).
For every link the UUIDs (universal unique identifiers) of the connected nodes, as well as the name of the link, are mentioned.

Then the export data follows, where the data appears "grouped" into entity types.
It is worth noticing the references between the instances of the various entities.
For example the DbNode with identifier *5921143* belongs to the user with identifier 2 and was generated by the computer with identifier 1.

The name of the entities is a reference to the base ORM entities.
This ensuries that the export files are cross-backend compatible.

If any groups are extracted, then they are mentioned in the corresponding field (*groups_uuid*).

Attributes and extras of the extracted nodes, are described in the final part of the JSON file.
The identifier of the corresponding node is used as a key for the attribute or extra.


.. _#4035: https://github.com/aiidateam/aiida-core/issues/4035
.. _#4036: https://github.com/aiidateam/aiida-core/issues/4036
