.. _how-to:share:

*****************
How to share data
*****************

AiiDA offers two avenues for sharing data with others: archive files and the REST API.


.. _how-to:share:archives:

Sharing AiiDA archives
======================

You have performed your calculations with AiiDA and you would like to share your AiiDA provenance graph, for example to make your scientific study reproducible.

Since AiiDA keeps track of the provenance of every computed result, this step is easy:
Tell AiiDA the **final results** you would like to be reproducible, and AiiDA will automatically include their entire provenance using the :ref:`topics:provenance:consistency:traversal-rules`.

.. seealso:: :ref:`internal_architecture:storage:sqlite_zip` and :ref:`how-to:data:share:archive:profile`.

Exporting individual nodes
^^^^^^^^^^^^^^^^^^^^^^^^^^

Let's say the key results of your study are contained in three AiiDA nodes with PKs ``12``, ``123``, ``1234``.
Exporting those results together with their provenance is as easy as:

.. code-block:: console

    $ verdi archive create my-calculations.aiida --nodes 12 123 1234

As usual, you can use any identifier (label, PK or UUID) to specify the nodes to be exported.

The resulting archive file ``my-calculations.aiida`` contains all information pertaining to the exported nodes.
The default traversal rules make sure to include the complete provenance of any node specified and should be sufficient for most cases.
See ``verdi archive create --help`` for ways to modify the traversal rules.

.. tip::

    To see what would be exported, before exporting, you can use the ``--test-run`` option:

    .. code-block:: console

        $ verdi archive create --test-run my-calculations.aiida

Please remember to use **UUIDs** when pointing your colleagues to data *inside* an AiiDA archive, since UUIDs are guaranteed to be universally unique (while PKs aren't).

Exporting large numbers of nodes
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If the number of results to be exported is large, for example in a high-throughput study, use the ``QueryBuilder`` to add the corresponding nodes to a group ``my-results`` (see :ref:`how-to:data:organize:group`).
Then export the group:

.. code-block:: console

    $ verdi archive create my-calculations.aiida --groups my-results

Alternatively, export your entire profile with:

.. code-block:: console

    $ verdi archive create my-calculations.aiida --all

Publishing AiiDA archive files
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

AiiDA archive files can be published on any research data repository, for example the `Materials Cloud Archive`_, `Zenodo`_, or the `Open Science Framework`_.
When publishing AiiDA archives on the `Materials Cloud Archive`_, you also get an interactive *EXPLORE* section, which allows peers to browse the AiiDA provenance graph directly in the browser.

.. _Zenodo: https://zenodo.org
.. _Open Science Framework: https://osf.io
.. _Materials Cloud Archive: https://archive.materialscloud.org

Inspecting an archive
^^^^^^^^^^^^^^^^^^^^^

In order to get a quick overview of an archive file *without* importing it into your AiiDA profile, use ``verdi archive info``:

.. code-block:: console

    $ verdi archive info --detailed test.aiida
    metadata:
        export_version: main_0001
        aiida_version: 2.0.0
        key_format: sha256
        compression: 6
        ctime: '2022-03-06T23:50:57.964429'
        creation_parameters:
            entities_starting_set:
            node:
            - 6af3f8a0-cf0d-4427-8472-f8907acfc87a
            include_authinfos: false
            include_comments: true
            include_logs: true
            graph_traversal_rules:
            input_calc_forward: false
            input_calc_backward: true
            create_forward: true
            create_backward: true
            return_forward: true
            return_backward: false
            input_work_forward: false
            input_work_backward: true
            call_calc_forward: true
            call_calc_backward: true
            call_work_forward: true
            call_work_backward: true
    entities:
        Users:
            count: 1
            emails:
            - aiida@epfl.ch
        Computers:
            count: 2
            labels:
            - computer1
            - computer2
        Nodes:
            count: 53
            node_types:
            - data.core.array.trajectory.TrajectoryData.
            - data.core.cif.CifData.
            - data.core.code.Code.
            - data.core.dict.Dict.
            - data.core.folder.FolderData.
            - data.core.remote.RemoteData.
            - data.core.singlefile.SinglefileData.
            - data.core.structure.StructureData.
            - process.calculation.calcfunction.CalcFunctionNode.
            - process.calculation.calcjob.CalcJobNode.
            process_types:
            - aiida.calculations:codtools.ciffilter
            - aiida.calculations:quantumespresso.pw
        Groups:
            count: 0
            type_strings: []
        Comments:
            count: 0
        Logs:
            count: 0
        Links:
            count: 59
    repository:
        objects:
            count: 71

You can also use the Python API to inspect the archive file as a profile, see :ref:`how-to:data:share:archive:profile`.

Importing an archive
^^^^^^^^^^^^^^^^^^^^

Use ``verdi archive import`` to import AiiDA archives into your current AiiDA profile.
``verdi archive import`` accepts URLs, e.g.:

.. code-block:: console

    $ verdi archive import "https://archive.materialscloud.org/record/file?file_id=2a59c9e7-9752-47a8-8f0e-79bcdb06842c&filename=SSSP_1.1_PBE_efficiency.aiida&record_id=23"

During import, AiiDA will avoid identifier collisions and node duplication based on UUIDs (and email comparisons for :py:class:`~aiida.orm.users.User` entries).
By default, existing entities will be updated with the most recent changes.
Node extras and comments have special modes for determining how to import them - for more details, see ``verdi archive import --help``.

To see what would be imported, before importing, you can use the ``--test-run`` option:

.. code-block:: console

    $ verdi archive import --test-run my-calculations.aiida

.. tip:: The AiiDA archive format has evolved over time, but you can still import archives created with previous AiiDA versions.
    If an outdated archive version is detected during import, the archive file will be automatically migrated to the newest version (within a temporary folder) and the import retried.

    You can also use ``verdi archive migrate`` to create updated archive files from existing archive files (or update them in place).

.. _how-to:share:serve:

Serving data through the REST API
=================================

The AiiDA REST API allows to query your AiiDA database over HTTP(S) and returns results in :ref:`JSON format <reference:rest-api:endpoints-responses>`.

.. note::

    As of October 2020, the AiiDA REST API only supports ``GET`` methods (reading); in particular, it does *not* yet support workflow management.
    This feature is, however, part of the `AiiDA roadmap <https://github.com/aiidateam/aiida-core/wiki/AiiDA-release-roadmap>`_.

.. _how-to:share:serve:launch:

Launching the REST API
^^^^^^^^^^^^^^^^^^^^^^

Start serving data from your default AiiDA profile via the REST API:

.. code-block:: console

    $ verdi restapi
     * REST API running on http://127.0.0.1:5000/api/v4
     * Serving Flask app "aiida.restapi.run_api" (lazy loading)
     * Environment: production
       WARNING: This is a development server. Do not use it in a production deployment.
       Use a production WSGI server instead.
     * Debug mode: off
     * Running on http://127.0.0.1:5000/ (Press CTRL+C to quit)

The REST API is now running on port ``5000`` of your local computer.

Like all ``verdi`` commands, you can select a different AiiDA profile via the ``-p PROFILE`` option:

.. code-block:: bash

    verdi -p <another_profile> restapi

.. note::

    REST API version history:


Version history
---------------

     * ``aiida-core`` >= 1.0.0b6: ``v4``. Simplified endpoints; only ``/nodes``, ``/processes``, ``/calcjobs``, ``/groups``, ``/computers`` and ``/servers`` remain.
     * ``aiida-core`` >= 1.0.0b3, <1.0.0b6: ``v3``. Development version, never shipped with a stable release.
     * ``aiida-core`` <1.0.0b3: ``v2``. First API version, with new endpoints added step by step.


.. _how-to:share:serve:query:

Querying the REST API
^^^^^^^^^^^^^^^^^^^^^

A URL to query the REST API consists of:

1. The *base URL*, by default:

    http://127.0.0.1:5000/api/v4

   Querying the base URL returns a list of all available endpoints.

2. The *path* defining the requested *resource*, optionally followed by a more specific *endpoint*.
   For example::

        /nodes
        /nodes/page/2
        /nodes/projectable_properties
        /nodes/<uuid>
        /nodes/<uuid>/links/outgoing

   If no endpoint is appended, the API returns a list of objects of that resource.
   In order to request a specific object of a resource, append its *UUID*.

   .. note::

       As usual, you can use partial UUIDs as long as they are unique.

       In order to query by *PK* you need to use the ``id`` filter (see below).
       This also applies to :py:class:`~aiida.orm.users.User` s, which don't have UUIDs (but instead uses email).

3. (Optional) The *query string* for filtering, ordering and pagination of results.
   For example::

    ?limit=20&offset=35
    ?id=200
    ?node_type=like="data%"

Here are some examples to try::

  http://127.0.0.1:5000/api/v4/users/
  http://127.0.0.1:5000/api/v4/computers?scheduler_type="slurm"
  http://127.0.0.1:5000/api/v4/nodes/?id>45&node_type=like="data%"

.. tip::

    The interactive `EXPLORE sections on Materials Cloud <https://www.materialscloud.org/explore/menu>`_ are all powered by the AiiDA REST API and you can query the underlying API, either using your web browser or using a tool like ``curl``:

    .. code-block:: console

       $ curl https://aiida-dev.materialscloud.org/2dstructures/api/v4/users

For an extensive user documentation of the endpoints, the query string as well as the format of the responses, see the :ref:`AiiDA REST API reference <reference:rest-api>`.

.. versionadded:: 2.1.0

It is possible to allow a request to declare a specific profile for which to run the profile.
This makes it possible to use a single REST API to serve the content of all configured profiles.
The profile switching functionality is disabled by default but can be enabled through the config:

.. code-block:: console

    verdi config set rest_api.profile_switching True

After the REST API is restarted, it will now accept the `profile` query parameter, for example:

.. code-block:: console

    http://127.0.0.1:5000/api/v4/computers?profile=some-profile-name

If the specified is already loaded, the REST API functions exactly as without profile switching enabled.
If another profile is specified, the REST API will first switch profiles before executing the request.

.. note::

    If the profile parameter is specified in a request and the REST API does not have profile switching enabled, a 400 response is returned.

.. _how-to:share:serve:deploy:

Deploying a REST API server
^^^^^^^^^^^^^^^^^^^^^^^^^^^

The ``verdi restapi`` command runs the REST API through the ``werkzeug`` python-based HTTP server.
In order to deploy production instances of the REST API for serving your data to others, we recommend using a fully fledged web server, such as `Apache <https://httpd.apache.org/>`_ or `NGINX <https://www.nginx.com/>`_, which then runs the REST API python application through the `web server gateway interface (WSGI) <https://wsgi.readthedocs.io/>`_.

.. note::
    One Apache/NGINX server can host multiple instances of the REST APIs, e.g. serving data from different AiiDA profiles.

A ``myprofile-rest.wsgi`` script for an AiiDA profile ``myprofile`` would look like this:

.. literalinclude:: include/snippets/myprofile-rest.wsgi

.. note:: See the documentation of :py:func:`~aiida.restapi.run_api.configure_api` for all available configuration options.

In the following, we explain how to run this wsgi application using Apache on Ubuntu.

    #. Install and enable the ``mod_wsgi`` `WSGI module <https://modwsgi.readthedocs.io/>`_ module:

    .. code-block:: console

           $ sudo apt install libapache2-mod-wsgi-py3
           $ sudo a2enmod wsgi

    #. Place the WSGI script in a folder on your server, for example ``/home/ubuntu/wsgi/myprofile-rest.wsgi``.

    #. Configure apache to run the WSGI application using a virtual host configuration similar to:

       .. literalinclude:: include/snippets/aiida-rest.conf

       Place this ``aiida-rest.conf`` file in ``/etc/apache2/sites-enabled``

    #. Restart apache: ``sudo service apache2 restart``.

You should now be able to reach your REST API at ``localhost/myprofile/api/v4`` (Port 80).
