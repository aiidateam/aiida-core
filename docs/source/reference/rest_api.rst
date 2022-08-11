.. _reference:rest-api:

**************
AiiDA REST API
**************

AiiDA's `RESTful <https://en.wikipedia.org/wiki/Representational_state_transfer>`_ `API <https://en.wikipedia.org/wiki/Application_programming_interface>`_ is implemented using the `Flask RESTful framework <https://flask-restful.readthedocs.io/en/latest/>`_ and returns responses in `JSON <https://www.json.org/json-en.html>`_ format.

To use AiiDA's REST API, you must install this component during the AiiDA installation:

.. code-block:: console

  $ pip install aiida-core[rest]

Then, the REST service can be started with:

.. code-block:: console

  $ verdi restapi

See :ref:`here <reference:command-line:verdi-restapi>` for more details.

.. _reference:rest-api:endpoints-responses:

Available endpoints and responses
=================================

In order to obtain a list of all available endpoints, query the API base URL or the `/server/endpoints` endpoint::

           http://localhost:5000/api/v4
           http://localhost:5000/api/v4/server/endpoints

The HTTP response of the REST API consists of a status code, a header, and a JSON object.

Possible status codes are:

    #. 200 for successful requests.
    #. 400 for bad requests.
       The JSON object contains an error message describing the issue with the request.
    #. 500 for a generic internal server error.
       The JSON object contains a generic error message.
    #. 404 for invalid URL.
       The request does not match any resource, and no JSON is returned.

The header is a standard HTTP response header with the additional custom fields

 * ``X-Total-Counts`` and
 * ``Link`` (only if paginated results are required, see the Pagination section).

The ``data`` field of the JSON object contains the main payload returned by the API.
The JSON object further contains information on the request in the ``method``, ``url``, ``url_root``, ``path``, ``query_string``, and ``resource_type`` fields.

.. _restapi_apache:

Nodes
-----

#.  Get a list of |Node| objects.

    REST URL::

        http://localhost:5000/api/v4/nodes?limit=2&offset=8&orderby=-id

    Description:

        Returns the list of two |Node| objects (``limit=2``) starting from 9th row (``offset=8``) of the database table and the list will be ordered by ``id`` in descending order.

    Response::

        {
          "data": {
            "nodes  ": [
              {
                "ctime": "Sun, 21 Jul 2019 11:45:52 GMT",
                "full_type": "data.core.dict.Dict.|",
                "id": 102618,
                "label": "",
                "mtime": "Sun, 21 Jul 2019 11:45:52 GMT",
                "node_type": "data.core.dict.Dict.",
                "process_type": null,
                "user_id": 4,
                "uuid": "a43596fe-3d95-4d9b-b34a-acabc21d7a1e"
              },
              {
                "ctime": "Sun, 21 Jul 2019 18:18:26 GMT",
                "full_type": "data.core.remote.RemoteData.|",
                "id": 102617,
                "label": "",
                "mtime": "Sun, 21 Jul 2019 18:18:26 GMT",
                "node_type": "data.core.remote.RemoteData.",
                "process_type": null,
                "user_id": 4,
                "uuid": "12f95e1c-69df-4a4b-9b06-8e69072e6108"
              }
            ]
          },
          "id": null,
          "method": "GET",
          "path": "/api/v4/nodes",
          "query_string": "limit=2&offset=8&orderby=-id",
          "resource_type": "nodes",
          "url": "http://localhost:5000/api/v4/nodes?limit=2&offset=8&orderby=-id",
          "url_root": "http://localhost:5000/"
        }

#.  Get a list of all nodes with attribute called ``pbc1``:

    REST URL::

        http://localhost:5000/api/v4/nodes?attributes=true&attributes_filter=pbc1

    Description:

        Returns the list of |Node| objects.
        Every node object contains value of attribute called ``pbc1`` if present otherwise ``null``.

    Response::

        {
          "data": {
            "nodes  ": [
              {
                "attributes.pbc1": true,
                "ctime": "Sun, 21 Jul 2019 15:36:30 GMT",
                "full_type": "data.core.structure.StructureData.|",
                "id": 51310,
                "label": "",
                "mtime": "Sun, 21 Jul 2019 15:36:30 GMT",
                "node_type": "data.core.structure.StructureData.",
                "process_type": null,
                "user_id": 4,
                "uuid": "98de8d6d-f533-4f97-a8ad-7720cc5ca8f6"
              },
              {
                "attributes.pbc1": null,
                "ctime": "Sun, 21 Jul 2019 15:44:14 GMT",
                "full_type": "data.core.dict.Dict.|",
                "id": 51311,
                "label": "",
                "mtime": "Sun, 21 Jul 2019 15:44:14 GMT",
                "node_type": "data.core.dict.Dict.",
                "process_type": null,
                "user_id": 4,
                "uuid": "321795fa-338e-4852-ae72-2eb30e33386e"
              }
              ...
            ]
          },
          "id": null,
          "method": "GET",
          "path": "/api/v4/nodes",
          "query_string": "limit=2&offset=8&orderby=-id",
          "resource_type": "nodes",
          "url": "http://localhost:5000/api/v4/nodes?limit=2&offset=8&orderby=-id",
          "url_root": "http://localhost:5000/"
        }

#. Get a list of all available |Node| types from the database.

    REST URL::

        http://localhost:5000/api/v4/nodes/full_types

    Description:

        Returns the list of full_types from database.

    Response::

        {
            "data": {
                "full_type": "node.%|%",
                "label": node,
                "namespace": "node",
                "path": "node",
                "subspaces": [...]
            },
            "id": null,
            "method": "GET",
            "path": "/api/v4/nodes/full_types",
            "query_string": "",
            "resource_type": "nodes",
            "url": "http://localhost:5000/api/v4/nodes/full_types",
            "url_root": "http://localhost:5000/"
        }

#. Get a list of all available download formats.

    REST URL::

        http://localhost:5000/api/v4/nodes/download_formats

    Description:

        Returns the list of available download formats.

    Response::

        {
            "data": {
                "data.core.array.bands.BandsData.|": [
                    "agr",
                    "agr_batch",
                    "dat_blocks",
                    "dat_multicolumn",
                    "gnuplot",
                    "json",
                    "mpl_pdf",
                    "mpl_png",
                    "mpl_singlefile",
                    "mpl_withjson"
                ],
                "data.core.array.trajectory.TrajectoryData.|": [
                    "cif",
                    "xsf"
                ],
                "data.core.cif.CifData.|": [
                    "cif"
                ],
                "data.core.structure.StructureData.|": [
                    "chemdoodle",
                    "cif",
                    "xsf",
                    "xyz"
                ],
                "data.core.upf.UpfData.|": [
                    "upf"
                ]
            },
            "id": null,
            "method": "GET",
            "path": "/api/v4/nodes/download_formats",
            "query_string": "",
            "resource_type": "nodes",
            "url": "http://localhost:5000/api/v4/nodes/download_formats",
            "url_root": "http://localhost:5000/"
        }

#. Get the details of a single |Node| object.

    REST URL::

        http://localhost:5000/api/v4/nodes/12f95e1c

    Description:

        Returns the details of the |Node| object with ``uuid="12f95e1c..."``.

    Response::

        {
          "data": {
            "nodes  ": [
              {
                "ctime": "Sun, 21 Jul 2019 18:18:26 GMT",
                "full_type": "data.core.remote.RemoteData.|",
                "id": 102617,
                "label": "",
                "mtime": "Sun, 21 Jul 2019 18:18:26 GMT",
                "node_type": "data.core.remote.RemoteData.",
                "process_type": null,
                "user_id": 4,
                "uuid": "12f95e1c-69df-4a4b-9b06-8e69072e6108"
              }
            ]
          },
          "id": "12f95e1c",
          "method": "GET",
          "path": "/api/v4/nodes/12f95e1c",
          "query_string": "",
          "resource_type": "nodes",
          "url": "http://localhost:5000/api/v4/nodes/12f95e1c",
          "url_root": "http://localhost:5000/"
        }

#. Get the list of incoming of a specific |Node|.

    REST URL::

        http://localhost:5000/api/v4/nodes/de83b1/links/incoming?limit=2

    Description:

        Returns the list of the first two input nodes (``limit=2``) of the |Node| object with ``uuid="de83b#..."``.

    Response::

        {
          "data": {
            "incoming": [
              {
                "ctime": "Sun, 21 Jul 2019 08:02:23 GMT",
                "full_type": "data.core.dict.Dict.|",
                "id": 53770,
                "label": "",
                "link_label": "settings",
                "link_type": "input_calc",
                "mtime": "Sun, 21 Jul 2019 08:02:23 GMT",
                "node_type": "data.core.dict.Dict.",
                "process_type": null,
                "user_id": 4,
                "uuid": "31993382-c1ab-4822-a116-bd88697f2796"
              },
              {
                "ctime": "Fri, 28 Jun 2019 10:54:25 GMT",
                "full_type": "data.core.upf.UpfData.|",
                "id": 54502,
                "label": "",
                "link_label": "pseudos__N",
                "link_type": "input_calc",
                "mtime": "Fri, 28 Jun 2019 10:54:28 GMT",
                "node_type": "data.core.upf.UpfData.",
                "process_type": null,
                "user_id": 4,
                "uuid": "2e2df55d-27a5-4b34-bf7f-911b16da95f0"
              }
            ]
          },
          "id": "de83b1",
          "method": "GET",
          "path": "/api/v4/nodes/de83b1/links/incoming",
          "query_string": "limit=2",
          "resource_type": "nodes",
          "url": "http://localhost:5000/api/v4/nodes/de83b1/links/incoming?limit=2",
          "url_root": "http://localhost:5000/"
        }

#. Filter the incoming/outgoing of a |Node| by their full type.

    REST URL::

        http://localhost:5000/api/v4/nodes/de83b1/links/incoming?full_type="data.core.dict.Dict.|"

    Description:

        Returns the list of the *dict* incoming nodes of the |Node| object with ``uuid="de83b1..."``.

    Response::

        {
          "data": {
            "incoming": [
              {
                "ctime": "Sun, 21 Jul 2019 08:02:23 GMT",
                "full_type": "data.core.dict.Dict.|",
                "id": 53770,
                "label": "",
                "link_label": "settings",
                "link_type": "input_calc",
                "mtime": "Sun, 21 Jul 2019 08:02:23 GMT",
                "node_type": "data.core.dict.Dict.",
                "process_type": null,
                "user_id": 4,
                "uuid": "31993382-c1ab-4822-a116-bd88697f2796"
              }
            ]
          },
          "id": "de83b1",
          "method": "GET",
          "path": "/api/v4/nodes/de83b1/links/incoming",
          "query_string": "full_type=%22data.core.dict.Dict.|%22",
          "resource_type": "nodes",
          "url": "http://localhost:5000/api/v4/nodes/de83b1/links/incoming?full_type=\"data.core.dict.Dict.|\"",
          "url_root": "http://localhost:5000/"
        }

    REST URL::

        http://localhost:5000/api/v4/nodes/de83b1/links/outgoing?full_type="data.core.dict.Dict.|"

    Description:

        Returns the list of the *dict* outgoing nodes of the |Node| object with ``uuid="de83b1..."``.

    Response::

        {
          "data": {
            "outgoing": [
              {
                "ctime": "Sun, 21 Jul 2019 09:08:05 GMT",
                "full_type": "data.core.dict.Dict.|",
                "id": 67440,
                "label": "",
                "link_label": "output_parameters",
                "link_type": "create",
                "mtime": "Sun, 21 Jul 2019 09:08:05 GMT",
                "node_type": "data.core.dict.Dict.",
                "process_type": null,
                "user_id": 4,
                "uuid": "861e1108-33a1-4495-807b-8c5189ad74e3"
              }
            ]
          },
          "id": "de83b1",
          "method": "GET",
          "path": "/api/v4/nodes/de83b1/links/outgoing",
          "query_string": "full_type=%22data.core.dict.Dict.|%22",
          "resource_type": "nodes",
          "url": "http://localhost:5000/api/v4/nodes/de83b1/links/outgoing?full_type=\"data.core.dict.Dict.|\"",
          "url_root": "http://localhost:5000/"
        }

#. Getting the list of the attributes/extras of a specific |Node|.

    REST URL::

        http://localhost:5000/api/v4/nodes/ffe11/contents/attributes

    Description:

        Returns the list of all attributes of the |Node| object with ``uuid="ffe11..."``.

    Response::

        {
          "data": {
            "attributes": {
              "append_text": "",
              "input_plugin": "quantumespresso.pw",
              "is_local": false,
              "prepend_text": "",
              "remote_exec_path": "/project/espresso-5.1-intel/bin/pw.x"
            }
          },
          "id": "ffe11",
          "method": "GET",
          "path": "/api/v4/nodes/ffe11/contents/attributes",
          "query_string": "",
          "resource_type": "nodes",
          "url": "http://localhost:5000/api/v4/nodes/ffe11/contents/attributes",
          "url_root": "http://localhost:5000/"
        }

    REST URL::

        http://localhost:5000/api/v4/nodes/ffe11/contents/extras

    Description:

        Returns the list of all the extras of the |Node| object with ``uuid="ffe11..."``.

    Response::

        {
          "data": {
            "extras": {
              "trialBool": true,
              "trialFloat": 3.0,
              "trialInt": 34,
              "trialStr": "trial"
            }
          },
          "id": "ffe11",
          "method": "GET",
          "path": "/api/v4/nodes/ffe11/contents/extras",
          "query_string": "",
          "resource_type": "nodes",
          "url": "http://localhost:5000/api/v4/nodes/ffe11/contents/extras",
          "url_root": "http://localhost:5000/"
        }

#. Getting a user-defined list of attributes/extras of a specific |Node|.

    REST URL::

         http://localhost:5000/api/v4/nodes/ffe11/contents/attributes?attributes_filter=append_text,is_local

    Description:

        Returns a list of the attributes ``append_text`` and ``is_local`` of the |Node| object with ``uuid="ffe11..."``.

    Response::

        {
          "data": {
            "attributes": {
              "append_text": "",
              "is_local": false
            }
          },
          "id": "ffe11",
          "method": "GET",
          "path": "/api/v4/nodes/ffe11/contents/attributes",
          "query_string": "attributes_filter=append_text,is_local",
          "resource_type": "nodes",
          "url": "http://localhost:5000/api/v4/nodes/ffe11/contents/attributes?attributes_filter=append_text,is_local",
          "url_root": "http://localhost:5000/"
        }

    REST URL::

        http://localhost:5000/api/v4/nodes/ffe11/contents/extras?extras_filter=trialBool,trialInt

    Description:

        Returns a list of the extras ``trialBool`` and ``trialInt`` of the |Node| object with ``uuid="ffe11..."``.

    Response::

        {
          "data": {
            "extras": {
              "trialBool": true,
              "trialInt": 34
            }
          },
          "id": "ffe11",
          "method": "GET",
          "path": "/api/v4/nodes/ffe11/contents/extras",
          "query_string": "extras_filter=trialBool,trialInt",
          "resource_type": "nodes",
          "url": "http://localhost:5000/api/v4/nodes/ffe11/contents/extras?extras_filter=trialBool,trialInt",
          "url_root": "http://localhost:5000/"
        }

#. Get comments of specific |Node|.

    REST URL::

        http://localhost:5000/api/v4/nodes/ffe11/contents/comments

    Description:

        Returns comments of the given |Node|.

    Response::

        {
            "data": {
                "comments": ["This is test comment.", "Add another comment."]
            },
            "id": "ffe11",
            "method": "GET",
            "path": "/api/v4/nodes/ffe11/contents/comments/",
            "query_string": "",
            "resource_type": "nodes",
            "url": "http://localhost:5000/api/v4/nodes/ffe11/contents/comments/",
            "url_root": "http://localhost:5000/"
        }

#. Get list of all the files/directories from the repository of a specific |Node|.

    REST URL::

        http://localhost:5000/api/v4/nodes/ffe11/repo/list

    Description:

        Returns a list of all the files/directories from node repository

    Response::

        {
            "data": {
                "repo_list": [
                    {
                        "name": ".aiida",
                        "type": "DIRECTORY"
                    },
                    {
                        "name": "_aiidasubmit.sh",
                        "type": "FILE"
                    },
                    {
                        "name": "aiida.in",
                        "type": "FILE"
                    },
                    {
                        "name": "out",
                        "type": "DIRECTORY"
                    },
                    {
                        "name": "pseudo",
                        "type": "DIRECTORY"
                    }
                ]
            },
            "id": "ffe11",
            "method": "GET",
            "path": "/api/v4/nodes/ffe11/repo/list/",
            "query_string": "",
            "resource_type": "nodes",
            "url": "http://localhost:5000/api/v4/nodes/ffe11/repo/list/",
            "url_root": "http://localhost:5000/"
        }

#. Download a file from the repository of a |Node|.

    REST URL::

        http://localhost:5000/api/v4/nodes/ffe11/repo/contents?filename="aiida.in"

    Description:

        Downloads the file ``aiida.in`` from node repository

    Response::

        It downloads the file.

#. There are specific download formats (check ``nodes/download_formats`` endpoint) available to download different types of nodes.
    This endpoint is used to download file in given format.

    REST URL::

        http://localhost:5000/api/v4/nodes/fafdsf/download?download_format=xsf

    Description:

        Downloads structure node of uuid=fafdsf in ``xsf`` format

    Response::

        It downloads the file.

Processes
---------

1.  Get the report of a |ProcessNode|.

    REST URL::

        http://localhost:5000/api/v4/processes/8b95cd85/report

    Description:

        Returns report of process of ``uuid="8b95cd85-...."``

    Response::

        {
            "data": {
                "logs": []
            },
            "id": "8b95cd85",
            "method": "GET",
            "path": "/api/v4/processes/8b95cd85/report",
            "query_string": "",
            "resource_type": "processes",
            "url": "http://localhost:5000/api/v4/processes/8b95cd85/report",
            "url_root": "http://localhost:5000/"
        }

CalcJobs
--------

1.  Get a list of input or output files of given |CalcJobNode|.

    REST URL::

        http://localhost:5000/api/v4/calcjobs/sffs241j/input_files

    Description:

        Returns a list of all input files of given |CalcJobNode| of ``uuid="sffs241j-...."``

    Response::

        {
            "data": [
                {
                    "name": ".aiida",
                    "type": "DIRECTORY"
                },
                {
                    "name": "_aiidasubmit.sh",
                    "type": "FILE"
                },
                {
                    "name": "aiida.in",
                    "type": "FILE"
                },
                {
                    "name": "out",
                    "type": "DIRECTORY"
                },
                ...
            ],
            "id": "sffs241j",
            "method": "GET",
            "path": "/api/v4/calcjobs/sffs241j/input_files",
            "query_string": "",
            "resource_type": "calcjobs",
            "url": "http://localhost:5000/api/v4/calcjobs/sffs241j/input_files",
            "url_root": "http://localhost:5000/"
        }

Computers
---------

1. Get a list of |Computer| objects.

    REST URL::

        http://localhost:5000/api/v4/computers?limit=3&offset=2&orderby=id

    Description:

        Returns the list of three |Computer| objects (``limit=3``) starting from the 3rd row (``offset=2``) of the database table.
        The list will be ordered by ascending values of ``id``.

    Response::

        {
          "data": {
            "computers": [
              {
                "description": "Alpha Computer",
                "hostname": "alpha.aiida.net",
                "id": 3,
                "name": "Alpha",
                "scheduler_type": "core.slurm",
                "transport_type": "core.ssh",
                "uuid": "9b5c84bb-4575-4fbe-b18c-b23fc30ec55e"
              },
              {
                "description": "Beta Computer",
                "hostname": "beta.aiida.net",
                "id": 4,
                "name": "Beta",
                "scheduler_type": "core.slurm",
                "transport_type": "core.ssh",
                "uuid": "5d490d77-638d-4d4b-8288-722f930783c8"
              },
              {
                "description": "Gamma Computer",
                "hostname": "gamma.aiida.net",
                "id": 5,
                "name": "Gamma",
                "scheduler_type": "core.slurm",
                "transport_type": "core.ssh",
                "uuid": "7a0c3ff9-1caf-405c-8e89-2369cf91b634"
              }
            ]
          },
          "id": null,
          "method": "GET",
          "path": "/api/v4/computers",
          "query_string": "limit=3&offset=2&orderby=id",
          "resource_type": "computers",
          "url": "http://localhost:5000/api/v4/computers?limit=3&offset=2&orderby=id",
          "url_root": "http://localhost:5000/"
        }

2. Get details of a single |Computer| object:

    REST URL::

        http://localhost:5000/api/v4/computers/5d490d77

    Description:

        Returns the details of the |Computer| object ``uuid="5d490d77-638d..."``.

    Response::

        {
          "data": {
            "computers": [
              {
                "description": "Beta Computer",
                "hostname": "beta.aiida.net",
                "id": 4,
                "name": "Beta",
                "scheduler_type": "core.slurm",
                "transport_type": "core.ssh",
                "uuid": "5d490d77-638d-4d4b-8288-722f930783c8"
              }
            ]
          },
          "id": null,
          "method": "GET",
          "path": "/api/v4/computers/5d490d77",
          "query_string": "",
          "resource_type": "computers",
          "url": "http://localhost:5000/api/v4/computers/5d490d77",
          "url_root": "http://localhost:5000/"
        }


Users
-----

1. Getting a list of the |User| s

    REST URL::

        http://localhost:5000/api/v4/users/

    Description:

        Returns a list of all the |User| objects.

    Response::

        {
          "data": {
            "users": [
              {
                "first_name": "AiiDA",
                "id": 1,
                "institution": "",
                "last_name": "Daemon"
              },
              {
                "first_name": "Gengis",
                "id": 2,
                "institution": "",
                "last_name": "Khan"
              }
            ]
          },
          "id": null,
          "method": "GET",
          "path": "/api/v4/users/",
          "query_string": "",
          "resource_type": "users",
          "url": "http://localhost:5000/api/v4/users/",
          "url_root": "http://localhost:5000/"
        }

2. Getting a list of |User| s whose first name starts with a given string

    REST URL::

        http://localhost:5000/api/v4/users/?first_name=ilike="aii%"

    Description:

        Returns a lists of the |User| objects whose first name starts with ``"aii"``, regardless the case of the characters.

    Response::

        {
          "data": {
            "users": [
              {
                "first_name": "AiiDA",
                "id": 1,
                "institution": "",
                "last_name": "Daemon"
              }
            ]
          },
          "id": null,
          "method": "GET",
          "path": "/api/v4/users/",
          "query_string": "first_name=ilike=%22aii%%22",
          "resource_type": "users",
          "url": "http://localhost:5000/api/v4/users/?first_name=ilike=\"aii%\"",
          "url_root": "http://localhost:5000/"
        }

Groups
------

1. Getting a list of |Group| s

    REST URL::

        http://localhost:5000/api/v4/groups/?limit=10&orderby=-user_id

    Description:

        Returns the list of ten |Group| objects (``limit=10``) starting from the 1st row of the database table (``offset=0``) and the list will be ordered by ``user_id`` in descending order.

    Response::

        {
          "data": {
            "groups": [
              {
                "description": "",
                "id": 104,
                "label": "SSSP_new_phonons_0p002",
                "type_string": "",
                "user_id": 2,
                "uuid": "7c0e0744-8549-4eea-b1b8-e7207c18de32"
              },
              {
                "description": "",
                "id": 102,
                "label": "SSSP_cubic_old_phonons_0p025",
                "type_string": "",
                "user_id": 1,
                "uuid": "c4e22134-495d-4779-9259-6192fcaec510"
              },
              ...

            ]
          },
          "id": null,
          "method": "GET",
          "path": "/api/v4/groups/",
          "query_string": "limit=10&orderby=-user_id",
          "resource_type": "groups",
          "url": "http://localhost:5000/api/v4/groups/?limit=10&orderby=-user_id",
          "url_root": "http://localhost:5000/"
        }

2. Getting the details of a specific group

    REST URL::

        http://localhost:5000/api/v4/groups/a6e5b

    Description:

        Returns the details of the |Group| object with ``uuid="a6e5b..."``.

    Response::

        {
          "data": {
            "groups": [
              {
                "description": "GBRV US pseudos, version 1.2",
                "id": 23,
                "label": "GBRV_1.2",
                "type_string": "data.core.upf.family",
                "user_email": "aiida@theossrv5.epfl.ch",
                "user_id": 2,
                "uuid": "a6e5b6c6-9d47-445b-bfea-024cf8333c55"
              }
            ]
          },
          "id": "a6e5b,
          "method": "GET",
          "path": "/api/v4/groups/a6e5b",
          "query_string": "",
          "resource_type": "groups",
          "url": "http://localhost:5000/api/v4/groups/a6e5b",
          "url_root": "http://localhost:5000/"
        }

Querybuilder
------------

    REST URL::

        http://localhost:5000/api/v4/querybuilder

    Description:

        Posts a query to the database. The content of the query is passed in a attached JSON file.

To use this endpoint, you need a http operator that allows to pass attachments.
We will demonstrate two options, the `HTTPie <https://httpie.io/>`_ (to use in the terminal) and the python library `Requests <https://requests.readthedocs.io/en/latest/>`_ (to use in python).

Option 1: HTTPie

  Install `HTTPie <https://httpie.io/>`_ by typing in the terminal:

  .. code-block:: console

    $ pip install httpie

  Then execute the REST API call with

  .. code-block:: console

    $ http localhost:5000/api/v4/querybuilder < my_query.json

  where ``my_query.json`` is the file containing the query dictionary of in the json format.

  Response:

  .. dropdown::

    .. code-block:: python

      {
          "data": {
              "Code_1": [
                  {
                      "attributes": {
                          "append_text": " ",
                          "input_plugin": "quantumespresso.ph",
                          "is_local": false,
                          "prepend_text": "ulimit -s unlimited",
                          "remote_exec_path": "/home/ubuntu/codes/q-e/bin/ph.x"
                      },
                      "ctime": "Wed, 16 Dec 2020 11:50:03 GMT",
                      "dbcomputer_id": 1,
                      "description": "phonon quantum_espresso v6.6",
                      "extras": {
                          "_aiida_hash": "045368af9cfeafa6fe3b0c6707e71b85cbef4fec55514ad0068c3ff19193e11f",
                          "hidden": false
                      },
                      "full_type": "data.code.Code.|",
                      "id": 3428,
                      "label": "q-e_6.6_ph",
                      "mtime": "Wed, 16 Dec 2020 11:50:03 GMT",
                      "node_type": "data.code.Code.",
                      "process_type": null,
                      "user_id": 1,
                      "uuid": "7565cf2a-8219-4c2b-bbae-9c6cd3d95aa2"
                  },
                  {
                      "attributes": {
                          "append_text": " ",
                          "input_plugin": "quantumespresso.pp",
                          "is_local": false,
                          "prepend_text": "ulimit -s unlimited",
                          "remote_exec_path": "/home/ubuntu/codes/q-e/bin/pp.x"
                      },
                      "ctime": "Mon, 14 Dec 2020 16:44:20 GMT",
                      "dbcomputer_id": 1,
                      "description": "postproc quantum_espresso v6.6",
                      "extras": {
                          "_aiida_hash": "1dca299bb587e002ac7aa745b5fd0b8893105dc0a16acefdfbc6188637dad05f",
                          "hidden": false
                      },
                      "full_type": "data.code.Code.|",
                      "id": 1822,
                      "label": "q-e_6.6_pp",
                      "mtime": "Mon, 14 Dec 2020 16:44:20 GMT",
                      "node_type": "data.code.Code.",
                      "process_type": null,
                      "user_id": 1,
                      "uuid": "a1b0530d-1a8d-413c-a4bd-af79868926c8"
                  },
                  {
                      "attributes": {
                          "append_text": " ",
                          "input_plugin": "quantumespresso.pw",
                          "is_local": false,
                          "prepend_text": "ulimit -s unlimited",
                          "remote_exec_path": "/home/ubuntu/codes/q-e/bin/pw.x"
                      },
                      "ctime": "Thu, 19 Nov 2020 14:38:42 GMT",
                      "dbcomputer_id": 1,
                      "description": "quantum_espresso v6.6",
                      "extras": {
                          "_aiida_hash": "e714b9e79656a0cf1c24d19a92f3553c3052d103b4f5b25bd2ae89581cb4886e",
                          "hidden": false
                      },
                      "full_type": "data.code.Code.|",
                      "id": 1,
                      "label": "q-e_6.6_pw",
                      "mtime": "Thu, 19 Nov 2020 14:38:42 GMT",
                      "node_type": "data.code.Code.",
                      "process_type": null,
                      "user_id": 1,
                      "uuid": "e48ec85b-3034-435b-ac96-d5ba37df393e"
                  }
              ]
          },
          "method": "POST",
          "path": "/api/v4/querybuilder",
          "query_string": "",
          "resource_type": "QueryBuilder",
          "url": "http://localhost:5000/api/v4/querybuilder",
          "url_root": "http://localhost:5000/"
      }

  The easiest way to construct the query json file is by using the :ref:`QueryBuilder <topics:database:advancedquery>` from AiiDA as we will demonstrate next.
  Open a ``verdi shell`` section:

  .. code-block:: console

    $ verdi shell

  Build your query and save it in a file:

  .. code-block:: ipython

    In [1]: qb = QueryBuilder()

    In [2]: qb.append(Code)
    Out[2]: <aiida.orm.querybuilder.QueryBuilder at 0x7f2bbeedd700>

    In [3]: qb_dict = qb.queryhelp

    In [4]: import json

    In [5]: with open('my_query.json', 'w') as file:
      ...:     json.dump(qb_dict, file)

  Check the content of the ``my_query.json``:

  .. code-block:: python

    {
      "path": [
        {
          "entity_type": "data.code.Code.",
          "tag": "Code_1",
          "joining_keyword": null,
          "joining_value": null,
          "outerjoin": false,
          "edge_tag": null
        }
      ],
      "filters": {
        "Code_1": {
          "node_type": {
            "like": "data.code.%"
          }
        }
      },
      "project": {
        "Code_1": []
      },
      "order_by": {},
      "limit": null,
      "offset": null
    }

Option 2: Resquests library (all python approach)

  Here is a short example on how to do it in python:

  .. code-block:: python

    from aiida.orm import QueryBuilder, Code
    from aiida import load_profile
    import requests

    load_profile('my_profile')

    qb = QueryBuilder()
    qb.append(Code)

    qb_dict = qb.queryhelp

    response = requests.post('http://localhost:5000/api/v4/querybuilder/', json=qb_dict)

    response.json()

  One should then have the same response as before.


.. _reference:rest-api:pagination:

Pagination
==========

Pages of 20 results each are accessed by appending ``/page/2`` (2nd page) to the URL path.
The page limit can be controlled via the ``perpage=(PERPAGE)`` query string (maximum page limit is 400).
Examples::

    http://localhost:5000/api/v4/computers/page/1?
    http://localhost:5000/api/v4/computers/page/1?perpage=5
    http://localhost:5000/api/v4/computers/page

If no page number is specified, the system redirects the request to page 1.
When pagination is used, the **header** of the response contains two more non-empty fields:

    - ``X-Total-Counts`` (custom field): the total number of results returned by the query, i.e. the sum of the results of all pages.
    - ``Links``: links to the first, previous, next, and last page. Suppose that you send a request whose results fill 8 pages.
      Then the value of the ``Links`` field would look like::

            <\http://localhost:5000/.../page/1?... >; rel=first,
            <\http://localhost:5000/.../page/3?... >; rel=prev,
            <\http://localhost:5000/.../page/5?... >; rel=next,
            <\http://localhost:5000/.../page/8?... >; rel=last

Besides pagination, the number of results can also be controlled using the ``limit`` and ``offset`` filters, see :ref:`below <reference:rest-api:filtering:unique>`.


.. _reference:rest-api:filtering:

Filtering results
=================

The filter query string is formed by one or more **fields**, separated by the special character ``&``.

Each field has the form (``key``)(``operator``)(``value``).

.. note:: Fields can only contain alphanumeric characters plus ``_``, and the first character cannot be a number (similar to Python variable names).
.. note:: In the following *id* is a synonym for the *PK* used in other sections of the documentation.

.. _reference:rest-api:filtering:unique:

Filter keys
-----------

Unique filters can be specified only once in a query string.
All of them must be followed by the operator ``=``.

.. list-table:: Unique filters
    :header-rows: 1

    * - Filter key
      - Description

    * - ``limit``
      - Number of results (integer).

    * - ``offset``
      - Skips the first ``offset`` results (integer).

    * - ``perpage``
      - How many results to show per page (integer).

    * - ``orderby``
      - ``+<property>`` for ascending order and ``-<property>`` for descending order (``<property`` defaults to ascending).
        Ascending (descending) order for strings corresponds to alphabetical (reverse-alphabetical) order, whereas for datetime objects it corresponds to chronological (reverse-chronological) order.
        Examples::

            http://localhost:5000/api/v4/computers?orderby=+id
            http://localhost:5000/api/v4/computers?orderby=+name
            http://localhost:5000/api/v4/computers?orderby=-uuid

    * - ``attributes_filter``
      - A comma-separated list of attributes to return.
        Use together with ``attributes=true``.
        Available in the endpoints ``/contents/attributes`` and ``/nodes``.
        Example::

            http://localhost:5000/api/v4/nodes/4fb10ef1/contents/attributes?attributes_filter=append_text,prepend_text

    * - ``extras_filter``
      - Similar to ``attributes_filter`` but for extras. It is used in the endpoints ``/contents/extras`` and ``/nodes``.

    * - ``attributes``
      - Pass ``true`` in order to return attributes in the ``/nodes`` endpoint (excluded by default).

    * - ``extras``
      - Pass ``true`` in order to return extras in the ``/nodes`` endpoint (excluded by default).

    * - ``download_format``
      - to specify download format in ``/download`` endpoint.

    * - ``download``
      - in ``/download`` endpoint, if ``download=false`` it displays the content in the browser instead of downloading a file.

    * - ``filename``
      - this filter is used to pass file name in ``/repo/list`` and ``/repo/contents`` endpoint.

    * - ``tree_in_limit``
      - specifies the limit on tree incoming nodes.

    * - ``tree_out_limit``
      - specifies the limit on tree outgoing nodes.

Regular filters can be compounded, requiring all specified filters to apply.

.. list-table:: Regular filters
    :header-rows: 1

    * - Filter key
      - Value type
      - Supported resources

    * - ``attributes``
      - string
      - nodes
    * - ``ctime``
      - datetime
      - nodes
    * - ``description``
      - string
      - computers, groups, nodes
    * - ``email`` \*
      - string
      - users
    * - ``first_name``
      - string
      - users
    * - ``full_type``
      - string
      - nodes
    * - ``hostname``
      - string
      - computers
    * - ``id``
      - integer
      - users, computers, groups, nodes
    * - ``institution``
      - string
      - users
    * - ``label``
      - string
      - groups, nodes
    * - ``last_name``
      - string
      - users
    * - ``mtime``
      - datetime
      - nodes
    * - ``name``
      - string
      - computers
    * - ``node_type``
      - string
      - nodes
    * - ``scheduler_type``
      - string
      - computers
    * - ``transport_type``
      - string
      - computers
    * - ``type_string``
      - string
      - groups
    * - ``user_id``
      - integer
      - groups
    * - ``uuid``
      - string
      - computers, groups, nodes


\* Key filtered out in response of the ``/users/`` endpoint privacy reasons.

.. note:: Node types are specified by a string that defines their position in the AiiDA source tree, ending with a dot.
    Examples:

    - ``node_type="data.core.code.Code."`` selects only objects of type |Code|.
    - ``node_type="data.core.remote.RemoteData."`` selects only objects of type :py:class:`~aiida.orm.RemoteData`.

.. note:: When using the *links/incoming* (*links/outgoing*) endpoints in combination with one or more filters, the filters are applied to the incoming (outgoing) nodes of the selected *id*.
    For example, the request::

            http://localhost:5000/api/v4/nodes/a67fba41/links/outgoing?full_type="data.core.dict.Dict.|"

    would first search for the outgoing of the node with *uuid* starting with "a67fba41" and then select only those nodes of full_type *data.core.core.dict.Dict.|*.



Filter operators
----------------

The operators supported by a specific filter key are uniquely determined by the value type associated with that key.

For example, a key that requires a boolean value admits only the identity operator ``=``, whereas an integer value enables the usage of the comparison operators ``=``, ``<``, ``<=``, ``>``, ``>=`` plus the membership operator ``=in=``:

.. list-table:: Filter operators
    :header-rows: 1

    * - Operator
      - Meaning
      - Accepted value types
    * - ``=``
      - identity
      - integers, strings, bool, datetime
    * - ``>``
      - greater than
      - integers, strings, datetime
    * - ``<``
      - less than
      - integers, strings, datetime
    * - ``>=``
      - greater than or equal to
      - integers, strings, datetime
    * - ``<=``
      - less than or equal to
      - integers, strings, datetime
    * - ``=like=``
      - pattern matching
      - strings
    * - ``=ilike=``
      - case-insensitive pattern matching
      - strings
    * - ``=in=``
      - identity with one element of a list
      - integers, strings, datetime


Pattern matching
^^^^^^^^^^^^^^^^

The pattern matching operators ``=like=`` and ``=ilike=`` must be followed by the pattern definition, namely, a string where two characters assume special meaning:

    1. ``%`` is used to replace an arbitrary sequence of characters, including no characters.
    2. ``_`` is used to replace one or zero characters.

.. note:: When special characters are required verbatim, escape them by pre-pending a backslash ``\``.

.. list-table:: Pattern matching with ``=like=`` and ``=ilike=``
    :header-rows: 1

    * - Filter
      - Matches
      - Doesn't match
    * -  ``name=like="a%d_"``
      -  "aiida"
      -  "AiiDA"
    * -  ``name=ilike="a%d_"``
      -  "aiida", "AiiDA"
      -
    * -  ``name=like="a_d_"``
      -
      -  "aiida"
    * -  ``name=like="aii%d_a"``
      -  "aiida"
      -
    * -  ``uuid=like="cdfd48%"``
      - "cdfd48f9-7ed2-4969-ba06-09c752b83d2"
      -
    * - ``description=like="This calculation is %\% useful"``
      - "This calculation is 100% useful"
      -

Membership
^^^^^^^^^^

The membership operator ``=in=`` has to be followed by a comma-separated list of values of the same type.
The condition is fulfilled if the column value of an object is an element of the list.

Examples::

    http://localhost:5000/api/v4/nodes?id=in=45,56,78
    http://localhost:5000/api/v4/computers/?scheduler_type=in="core.slurm","core.pbs"

Comparison
^^^^^^^^^^^^^^^^^^^^

The comparison operators ``<``, ``>``, ``<=``, ``>=`` assume natural ordering for integers, (case-insensitive) alphabetical ordering for strings, and chronological ordering for datetime values.

Examples:

    - ``http://localhost:5000/api/v4/nodes?id>578`` selects the nodes having an id larger than 578.
    - ``http://localhost:5000/api/v4/users/?last_name<="m"`` selects only the users whose last name begins with a character in the range [a-m].


Filter value types
------------------

Filter values should be specified as follows:

.. list-table:: Filter value types
    :header-rows: 1

    * - Value type
      - Description

    * - ``bool``
      - Either ``true`` or ``false`` (lower case).

    * - ``datetime``
      -
        Datetime objects expressed in the format ``(DATE)T(TIME)(SHIFT)`` where ``(SHIFT)`` is the time difference with respect to the UTC time.
        This is required to avoid any problem arising from comparing datetime values expressed in different time zones.
        The formats of each field are:

        1. ``YYYY-MM-DD`` for ``(DATE)`` (mandatory).
        2. ``HH:MM:SS`` for ``(TIME)`` (optional). The formats ``HH`` and ``HH:MM`` are supported too.
        3. ``+/-HH:MM`` for ``(SHIFT)`` (optional, if present requires ``(TIME)`` to be specified).
           The format ``+/-HH`` is allowed too. If no shift is specified UTC time is assumed.
           The shift format follows the general convention that eastern (western) shifts are positive (negative).
           The API is unaware of daylight saving times so the user is required to adjust the shift to take them into account.

        This format is ``ISO-8601`` compliant.
        Note that date and time fields have to be separated by the character ``T``.
        Examples::

            http://localhost:5000/api/v4/nodes?ctime>2019-04-23T05:45+03:45
            http://localhost:5000/api/v4/nodes?ctime<2019-04-23T05:45
            http://localhost:5000/api/v4/nodes?mtime>=2019-04-23

    * - ``integer``
      - Positive integer numbers.

    * - ``string``
      - Text enclosed in double quotes.
        If the string contains double quotes those have to be escaped as ``""`` (two double quotes).
        Note that in the unlikely occurrence of a sequence of double quotes you will have to escape it by writing twice as many double quotes.


.. |Computer| replace:: :py:class:`~aiida.orm.computers.Computer`
.. |Code| replace:: :py:class:`~aiida.orm.Code`
.. |Node| replace:: :py:class:`~aiida.orm.Node`
.. |ProcessNode| replace:: :py:class:`~aiida.orm.ProcessNode`
.. |CalcJobNode| replace:: :py:class:`~aiida.orm.CalcJobNode`
.. |User| replace:: :py:class:`~aiida.orm.users.User`
.. |Group| replace:: :py:class:`~aiida.orm.groups.Group`
