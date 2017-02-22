=================================
Import and export data from AiiDA
=================================

AiiDA platform allows its users to exchange parts of their graphs containing
already executed calculations but also related nodes like their inputs &
outputs. Exchanging such information among AiiDA instances, or even users of
the same instance, is not a simple task.

Two tools are provided that facilitate the exchange of AiiDA information.

Export
++++++

The export tool can take as input various parameters allowing the user to
export specific nodes based on their identifier or nodes belonging to a
specific group. Given a set of nodes, the export function automatically
selects all the parents and the direct outputs of the selected calculations
(this can be overridden by the user).

The idea behind this automatic selection is that when a node is exported,
very likely, we would like to know how we arrived at the generation of this
node. The same stands for calculation nodes. When a calculation is exported,
it doesn't make a lot of sense to be exported without providing also the
results of that calculation. The exported data (database information but
also files) is stored to a single file which can also be compressed if the
user provides the corresponding option during the export.

Import
++++++
Import is less parameterizable than export. The user has just to provide
a path to the file to be imported (file-system path or URL) and AiiDA will
import the needed information by also checking, and avoiding, possible
identifier collisions and or node duplication.


File format
+++++++++++
The result of the export is a single file which contains all the needed
information for a successful import. Let's see more closely what is inside
this file. If you extract it, you will find the following files and
directories::

    -rw-rw-r--  1 aiida aiida 165336 Nov 29 16:39 data.json
    -rw-rw-r--  1 aiida aiida   1848 Nov 29 16:39 metadata.json
    drwxrwx--- 70 aiida aiida   4096 Nov 29 16:39 nodes/


* metadata.json - information about the schema of the database information
  that is exported.
* data.json - information about the exported database nodes that follows the
  format mentioned in the metadata.json. In this files the links between
  the nodes are stored too.
* nodes directory - the repository files that correspond to the exported nodes.

metadata.json
-------------
This file contains important information and it is necessary for the correct
interpretation of the *data.json*. Apart from the data schema, the AiiDA code
and the export file version are also mentioned. This is used to avoid any
incompatibilities among different versions of AiiDA. It should be noted that
the schema described in metadata.json is related to the data itself -
abstracted schema focused on the extracted information -  and not how the
data is stored in the database (database schema). This makes the import/export
mechanism to be transparent to the database system used, backend selected and
how the data is organised in the database (database schema).

Let's have a look at the contents of the metadata.json::

    {
        "export_version": "0.2",
        "aiida_version": "0.6.0",
        "unique_identifiers": {
            "aiida.backends.djsite.db.models.DbComputer": "uuid",
            "aiida.backends.djsite.db.models.DbGroup": "uuid",
            "aiida.backends.djsite.db.models.DbUser": "email",
            "aiida.backends.djsite.db.models.DbNode": "uuid",
            "aiida.backends.djsite.db.models.DbAttribute": null,
            "aiida.backends.djsite.db.models.DbLink": null
        },
        "all_fields_info": {
            "aiida.backends.djsite.db.models.DbComputer": {
                "description": {},
                "transport_params": {},
                "hostname": {},
                "enabled": {},
                "name": {},
                "transport_type": {},
                "metadata": {},
                "scheduler_type": {},
                "uuid": {}
            },
            "aiida.backends.djsite.db.models.DbLink": {
                "input": {
                    "related_name": "output_links",
                    "requires": "aiida.backends.djsite.db.models.DbNode"},
                "label": {},
                "output": {
                    "related_name": "input_links",
                    "requires": "aiida.backends.djsite.db.models.DbNode"}
            },
            "aiida.backends.djsite.db.models.DbUser": {
                "first_name": {},
                "last_name": {},
                "email": {},
                "institution": {}
            },
            "aiida.backends.djsite.db.models.DbNode": {
                "nodeversion": {},
                "description": {},
                "dbcomputer": {
                    "related_name": "dbnodes",
                    "requires": "aiida.backends.djsite.db.models.DbComputer"},
                "ctime": {
                    "convert_type": "date"},
                "user": {
                    "related_name": "dbnodes",
                    "requires": "aiida.backends.djsite.db.models.DbUser"},
                "mtime": {
                    "convert_type": "date"},
                "label": {},
                "type": {},
                "public": {},
                "uuid": {}
            },
            "aiida.backends.djsite.db.models.DbAttribute": {
                "dbnode": {
                    "related_name": "dbattributes",
                    "requires": "aiida.backends.djsite.db.models.DbNode"
                },
                "dval": {
                    "convert_type": "date"},
                "datatype": {},
                "fval": {},
                "tval": {},
                "key": {},
                "ival": {},
                "bval": {}
            },
            "aiida.backends.djsite.db.models.DbGroup": {
                "description": {},
                "name": {},
                "user": {
                    "related_name": "dbgroups",
                    "requires": "aiida.backends.djsite.db.models.DbUser"},
                "time": {
                    "convert_type": "date"},
                "type": {},
                "uuid": {}
            }
        }
    }


At the beginning of the file, we see that the version of the export file and
the versions of the AiiDA code.

The entities that are exported are mentioned in the sequel with their unique
identifiers. Knowing the unique IDs is useful for duplicate avoidance
(in order to avoid the insertion of the node multiple times).

Then in the *all_fields_info*, the properties of each entity are mentioned. It
is also mentioned the correlations with other entities. For example, the entity
*aiida.backends.djsite.db.models.DbNode* is related to a computer and a user.
The corresponding entity names appear nested next to the properties to show
this correlation.

data.json
---------
A sample of the *data.json* file follows::

    {
        "links_uuid": [
            {
                "output": "c208c9da-23b4-4c32-8f99-f9141ab28363",
                "label": "parent_calc_folder",
                "input": "eaaa114d-3d5b-42eb-a269-cf0e7a3a935d"
            },
            ...
        ],
        "export_data": {
            "aiida.backends.djsite.db.models.DbUser": {
                "2": {
                    "first_name": "AiiDA",
                    "last_name": "theossrv2",
                    "institution": "EPFL, Lausanne",
                    "email": "aiida@theossrv2.epfl.ch"
                },
                ...
            },
            "aiida.backends.djsite.db.models.DbComputer": {
                "1": {
                    "name": "theospc14-direct_",
                    "transport_params": "{}",
                    "description": "theospc14 (N. Mounet's PC) with direct scheduler",
                    "hostname": "theospc14.epfl.ch",
                    "enabled": true,
                    "transport_type": "ssh",
                    "metadata": "{\"default_mpiprocs_per_machine\": 8, \"workdir\": \"/scratch/{username}/aiida_run/\", \"append_text\": \"\", \"prepend_text\": \"\", \"mpirun_command\": [\"mpirun\", \"-np\", \"{tot_num_mpiprocs}\"]}",
                    "scheduler_type": "direct",
                    "uuid": "fb7729ff-8254-4bc0-bbec-acbdb573cfe2"
                },
                ...
            },
            "aiida.backends.djsite.db.models.DbNode": {
                "5921143": {
                    "uuid": "628ba258-ccc1-47bf-bab7-8aee64b563ea",
                    "description": "",
                    "dbcomputer": null,
                    "label": "",
                    "user": 2,
                    "mtime": "2016-08-21T11:55:53.132925",
                    "nodeversion": 1,
                    "type": "data.parameter.ParameterData.",
                    "public": false,
                    "ctime": "2016-08-21T11:55:53.118306"
                },
                "20063": {
                    "uuid": "1024e35e-166b-4104-95f6-c1706df4ce15",
                    "description": "",
                    "dbcomputer": 1,
                    "label": "",
                    "user": 2,
                    "mtime": "2016-02-16T10:33:54.095973",
                    "nodeversion": 16,
                    "type": "calculation.job.codtools.ciffilter.CiffilterCalculation.",
                    "public": false,
                    "ctime": "2015-10-02T20:08:06.628472"
                },
                ...
            }
        },
        "groups_uuid": {

        },
        "node_attributes_conversion": {
            "5921143": {
                "CONTROL": {
                    "calculation": null,
                    "restart_mode": null,
                    "max_seconds": null
                },
                "ELECTRONS": {
                    "electron_maxstep": null,
                    "conv_thr": null
                },
                "SYSTEM": {
                    "ecutwfc": null,
                    "input_dft": null,
                    "occupations": null,
                    "degauss": null,
                    "smearing": null,
                    "ecutrho": null
                }
            },
            "20063": {
                "retrieve_list": [
                    null,
                    null,
                    null,
                    null
                ],
                "last_jobinfo": null,
                "scheduler_state": null,
                "parser": null,
                "linkname_retrieved": null,
                "jobresource_params": {
                    "num_machines": null,
                    "num_mpiprocs_per_machine": null,
                    "default_mpiprocs_per_machine": null
                },
                "remote_workdir": null,
                "state": null,
                "max_wallclock_seconds": null,
                "retrieve_singlefile_list": [

                ],
                "scheduler_lastchecktime": "date",
                "job_id": null
            },
            ...
        },
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
                "last_jobinfo": "{\"job_state\": \"DONE\", \"detailedJobinfo\": \"AiiDA MESSAGE: This scheduler does not implement the routine get_detailed_jobinfo to retrieve the information on a job after it has finished.\", \"job_id\": \"13489\"}",
                "scheduler_state": "DONE",
                "parser": "codtools.ciffilter",
                "linkname_retrieved": "retrieved",
                "jobresource_params": {
                    "num_machines": 1,
                    "num_mpiprocs_per_machine": 1,
                    "default_mpiprocs_per_machine": 8
                },
                "remote_workdir": "/scratch/aiida/aiida_run/10/24/e35e-166b-4104-95f6-c1706df4ce15",
                "state": "FINISHED",
                "max_wallclock_seconds": 900,
                "retrieve_singlefile_list": [

                ],
                "scheduler_lastchecktime": "2015-10-02T20:30:36.481951",
                "job_id": "13489"
            "6480111": {
            },
            ...
        }
    }


At the start of the json file the links among the various AiiDA nodes are
stated (*links_uuid* field). For every link the UUID (Universal unique
identifiers) of the connected nodes but also the name of the link is mentioned.

Then the export data follows where for every entity the data appear. It is
worth observing the references between the instances of the various entities.
For example the DbNode with identifier *5921143* belongs to the user with
identifier 2 and was generated by the computer with identifier 1.

The name of the entities is, for the moment, a reference to the model
class of the Django backend. This stands for both backends (Django and
SQLAlchemy) ensuring that the export files are cross-backend compatible.
These names will change in the future to more abstract names.

If any groups are extracted, then they are mentioned in corresponding field
(*groups_uuid*).

Attributes of the extracted nodes, are described in the ending part of the json
file. The identifier of the corresponding node is used as a key for the
attribute. The field *node_attributes_conversion* contains information regarding
the type of the attribute. For example the dates are not inherently supported
by JSON, so it is specified explicitly in the schema if the value of an
attribute is of that specific type. After the *node_attributes_conversion*
the *node_attributes* section follows with the actual values.
