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

Exporting individual nodes
^^^^^^^^^^^^^^^^^^^^^^^^^^
Let's say the key results of your study are contained in three AiiDA nodes with PKs ``12``, ``123``, ``1234``.
Exporting those results together with their provenance is as easy as:

.. code-block:: console

    $ verdi export create my-calculations.aiida --nodes 12 123 1234

As usual, you can use any identifier (label, PK or UUID) to specify the nodes to be exported.

The resulting archive file ``my-calculations.aiida`` contains all information pertaining to the exported nodes.
The default traversal rules make sure to include the complete provenance of any node specified and should be sufficient for most cases.
See ``verdi export create --help`` for ways to modify the traversal rules.

.. tip::

    If you want to make sure the archive includes everything you intended, you can create a new profile and import it:

    .. code-block:: console

        $ verdi quicksetup --profile test-export  # create new profile
        $ verdi --profile test-export import my-calculations.aiida

    Now use, e.g. the :py:class:`~aiida.orm.querybuilder.QueryBuilder` to query the database.

Please remember to use **UUIDs** when pointing your colleagues to data *inside* an AiiDA archive, since UUIDs are guaranteed to be universally unique (while PKs aren't).

Using groups for data exporting
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If the number of results to be exported is large, for example in a high-throughput study, use the ``QueryBuilder`` to add the corresponding nodes to a group ``my-results`` (see :ref:`how-to:data:organize:group`).
Then export the group:

.. code-block:: console

    $ verdi export create my-calculations.aiida --groups my-results

Publishing AiiDA archive files
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

AiiDA archive files can be published on any research data repository, for example the `Materials Cloud Archive`_, `Zenodo`_, or the `Open Science Framework`_.
When publishing AiiDA archives on the `Materials Cloud Archive`_, you also get an interactive *EXPLORE* section, which allows peers to browse the AiiDA provenance graph directly in the browser.

.. _Zenodo: https://zenodo.org
.. _Open Science Framework: https://osf.io
.. _Materials Cloud Archive: https://archive.materialscloud.org


Importing an archive
^^^^^^^^^^^^^^^^^^^^

Use ``verdi import`` to import AiiDA archives into your current AiiDA profile.
``verdi import`` accepts URLs, e.g.:

.. code-block:: console

    $ verdi import "https://archive.materialscloud.org/record/file?file_id=2a59c9e7-9752-47a8-8f0e-79bcdb06842c&filename=SSSP_1.1_PBE_efficiency.aiida&record_id=23"

During import, AiiDA will avoid identifier collisions and node duplication based on UUIDs (and email comparisons for :py:class:`~aiida.orm.users.User` entries).
By default, existing entities will be updated with the most recent changes.
Node extras and comments have special modes for determining how to import them - for more details, see ``verdi import --help``.

.. tip:: The AiiDA archive format has evolved over time, but you can still import archives created with previous AiiDA versions.
    If an outdated archive version is detected during import, you will be prompted to confirm automatic migration of the archive file.

    You can also use ``verdi export migrate`` to create updated archive files from existing archive files (or update them in place).

.. tip:: In order to get a quick overview of an archive file *without* importing it into your AiiDA profile, use ``verdi export inspect``:

    .. code-block:: console

        $ verdi export inspect sssp-efficiency.aiida
        --------------  -----
        Version aiida   1.2.1
        Version format  0.9
        Computers       0
        Groups          0
        Links           0
        Nodes           85
        Users           1
        --------------  -----

    Note: For archive versions 0.2 and below, the overview may be inaccurate.


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

     * ``aiida-core`` >= 1.0.0b6: ``v4``
     * ``aiida-core`` >= 1.0.0b3, <1.0.0b6: ``v3``
     * ``aiida-core`` <1.0.0b3: ``v2``


.. _how-to:share:serve:query:

Querying the REST API
^^^^^^^^^^^^^^^^^^^^^

A URL to query the REST API consists of:

1. The *base URL*, by default:

    http://127.0.0.1:5000/api/v4

   Querying the base URL returns a list of all available endpoints.

2. The *path* defining the requested *resource*, optionally followed by a more specific *endpoint*. For example::

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

3. (Optional) The *query string* for filtering, ordering and pagination of results. For example::

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


Deploying a REST API server
^^^^^^^^^^^^^^^^^^^^^^^^^^^

The ``verdi restapi`` command runs the REST API through the ``werkzeug`` python-based HTTP server.
In order to deploy production instances of the REST API for serving your data to others, we recommend using a fully fledged web server, such as `Apache <https://httpd.apache.org/>`_ or `NGINX <https://www.nginx.com/>`_.

.. note::
    One Apache/NGINX server can host multiple APIs, e.g. connecting to different AiiDA profiles.

In the following, we assume you have a working installation of Apache with the ``mod_wsgi`` `WSGI module <modwsgi.readthedocs.io/>`_ enabled.

The goal of the example is to hookup the APIs ``django`` and ``sqlalchemy`` pointing to two AiiDA profiles, called for simplicity ``django`` and ``sqlalchemy``.

All the relevant files are enclosed under the path ``/docs/wsgi/`` starting from the AiiDA source code path.
In each of the folders ``app1/`` and ``app2/``, there is a file named ``rest.wsgi`` containing a python script that instantiates and configures a python web app called ``application``, according to the rules of ``mod_wsgi``.
For how the script is written, the object ``application`` is configured through the file ``config.py`` contained in the same folder.
Indeed, in ``app1/config.py`` the variable ``aiida-profile`` is set to ``"django"``, whereas in ``app2/config.py`` its value is ``"sqlalchemy"``.

The path where you put the ``.wsgi`` file as well as its name are irrelevant as long as they are correctly referred to in the Apache configuration file, as shown later on.
Similarly, you can place ``config.py`` in a custom path, provided you change the variable ``config_file_path`` in the ``wsgi file`` accordingly.

In ``rest.wsgi`` the only options you might want to change is ``catch_internal_server``.
When set to ``True``, it lets the exceptions thrown during the execution of the app propagate all the way through until they reach the logger of Apache.
Especially when the app is not entirely stable yet, one would like to read the full python error traceback in the Apache error log.

Finally, you need to setup the Apache site through a proper configuration file.
We provide two template files: ``one.conf`` or ``many.conf``.
The first file tells Apache to bundle both apps in a unique Apache daemon process.
Apache usually creates multiple processes dynamically and with this configuration each process will handle both apps.

The script ``many.conf``, instead, defines two different process groups, one for each app.
So the processes created dynamically by Apache will always be handling one app each.
The minimal number of Apache daemon processes equals the number of apps, contrarily to the first architecture, where one process is enough to handle two or even a larger number of apps.

Let us call the two apps for this example ``django`` and ``sqlalchemy``, matching with the chosen AiiDA profiles.
In both ``one.conf`` and ``many.conf``, the important directives that should be updated if one changes the paths or names of the apps are:

    - ``WSGIProcessGroup`` to define the process groups for later reference.
      In ``one.conf`` this directive appears only once to define the generic group ``profiles``, as there is only one kind of process handling both apps.
      In ``many.conf`` this directive appears once per app and is embedded into a "Location" tag, e.g.::

        <Location /django>
            WSGIProcessGroup sqlalchemy
        <Location/>

    - ``WSGIDaemonProcess`` to define the path to the AiiDA virtual environment.
      This appears once per app in both configurations.

    - ``WSGIScriptAlias`` to define the absolute path of the ``.wsgi`` file of each app.

    - The ``<Directory>`` tag mainly used to grant Apache access to the files used by each app, e.g.::

        <Directory "<aiida.source.code.path>/aiida/restapi/wsgi/app1">
            Require all granted
        </Directory>

The latest step is to move either ``one.conf`` or ``many.conf`` into the Apache configuration folder and restart the Apache server.
In Ubuntu, this is usually done with the commands:

.. code-block:: bash

    cp <conf_file>.conf /etc/apache2/sites-enabled/000-default.conf
    sudo service apache2 restart

We believe the two basic architectures we have just explained can be successfully applied in many different deployment scenarios.
Nevertheless, we suggest users who need finer tuning of the deployment setup to look into to the official documentation of `Apache <https://httpd.apache.org/>`_ and, more importantly, `WSGI <wsgi.readthedocs.io/>`_.

The URLs of the requests handled by Apache must start with one of the paths specified in the directives ``WSGIScriptAlias``.
These paths identify uniquely each app and allow Apache to route the requests to their correct apps.
Examples of well-formed URLs are:

.. code-block:: bash

    curl http://localhost/django/api/v4/computers -X GET
    curl http://localhost/sqlalchemy/api/v4/computers -X GET

The first (second) request will be handled by the app ``django`` (``sqlalchemy``), and will serve results fetched from the AiiDA profile ``django`` (``sqlalchemy``).
Notice that we have not specified any port in the URLs since Apache listens conventionally to port 80, where any request lacking the port is automatically redirected (port 443 for HTTPS).
