.. _how-to:data:

*********************
How to work with data
*********************


.. _how-to:data:import:

Importing data
==============

`#3994`_


.. _how-to:data:plugin:

Adding support for custom data types
====================================

`#3995`_


.. _how-to:data:find:

Finding data
============

`#3996`_


.. _how-to:data:organize:

Organizing data
===============

`#3997`_


.. _how-to:data:share:

Sharing data
============

`#3998`_


.. _how-to:data:delete:

Deleting data
=============

`#3999`_

Serving your data to others
===========================

The AiiDA REST API allows to query your AiiDA database over HTTP(S), e.g. by writing requests directly or via a JavaScript application as on `Materials Cloud <http://materialscloud.org/explore>`_.

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

Anyway, the path where you put the ``.wsgi`` file as well as its name are irrelevant as long as they are correctly referred to in the Apache configuration file, as shown later on.
Similarly, you can place ``config.py`` in a custom path, provided you change the variable ``config_file_path`` in the ``wsgi file`` accordingly.

In ``rest.wsgi`` probably the only options you might want to change is ``catch_internal_server``.
When set to ``True``, it lets the exceptions thrown during the execution of the app propagate all the way through until they reach the logger of Apache.
Especially when the app is not entirely stable yet, one would like to read the full python error traceback in the Apache error log.

Finally, you need to setup the Apache site through a proper configuration file.
We provide two template files: ``one.conf`` or ``many.conf``.
The first file tells Apache to bundle both apps in a unique Apache daemon process.
Apache usually creates multiple process dynamically and with this configuration each process will handle both apps.

The script ``many.conf``, instead, defines two different process groups, one for each app.
So the processes created dynamically by Apache will always be handling one app each.
The minimal number of Apache daemon processes equals the number of apps, contrarily to the first architecture, where one process is enough to handle two or even a larger number of apps.

Let us call the two apps for this example ``django`` and ``sqlalchemy``.
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
Nevertheless, we suggest users who need finer tuning of the deployment setup to look into to the official documentation of `Apache <https://httpd.apache.org/>`_ and, more importantly, `WSGI <wsgi.readthedocs.io/>`__.

The URLs of the requests handled by Apache must start with one of the paths specified in the directives ``WSGIScriptAlias``.
These paths identify uniquely each app and allow Apache to route the requests to their correct apps.
Examples of well-formed URLs are:

.. code-block:: bash

    curl http://localhost/django/api/v4/computers -X GET
    curl http://localhost/sqlalchemy/api/v4/computers -X GET

The first (second) request will be handled by the app ``django`` (``sqlalchemy``), namely will serve results fetched from the profile ``django`` (``sqlalchemy``).
Notice that we haven't specified any port in the URLs since Apache listens conventionally to port 80, where any request lacking the port is automatically redirected.



.. _#3994: https://github.com/aiidateam/aiida-core/issues/3994
.. _#3995: https://github.com/aiidateam/aiida-core/issues/3995
.. _#3996: https://github.com/aiidateam/aiida-core/issues/3996
.. _#3997: https://github.com/aiidateam/aiida-core/issues/3997
.. _#3998: https://github.com/aiidateam/aiida-core/issues/3998
.. _#3999: https://github.com/aiidateam/aiida-core/issues/3999
