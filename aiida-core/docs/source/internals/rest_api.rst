.. role:: python(code)
   :language: python

.. _internal_architecture:restapi:

********
REST API
********

The AiiDA REST API is made of two main classes:

* ``App``, inheriting from ``flask.Flask`` (generic class for Flask web applications).
* ``AiidaApi``, inheriting ``flask_restful.Api``. This class defines the resources served by the REST API.

The instances of both ``AiidaApi`` (let's call it ``api``) and ``App`` (let's call it ``app``) need to be coupled by setting ``api.app = app``.


Extending the REST API
======================

In the following, we will go through a minimal example of creating an API that extends the AiiDA REST API by adding an endpoint ``/new-endpoint``.
The endpoint implements a ``GET`` request that retrieves the latest created ``Dict`` node and returns its ``id``, ``ctime`` in ISO 8601 format, and ``attributes``.

.. warning::

    The REST API is currently read-only and does not support end-points that create new data or mutate existing data in the database.
    See `this AiiDA enhancement proposal draft <https://github.com/aiidateam/AEP/pull/24>`_ for efforts in this direction.

In order to achieve this, we will need to:

* Create the ``flask_restful.Resource`` class that will be bound to the new endpoint.
* Extend the :py:class:`~aiida.restapi.api.AiidaApi` class in order to register the new endpoint.
* (Optional) Extend the :py:class:`~aiida.restapi.api.App` class for additional customization.

Let's start by putting the following code into a  file ``api.py``:

.. literalinclude:: includes/snippets/api.py

We will now go through the previous code step by step.

First things first: the imports.

.. code-block:: python

    from aiida.restapi.api import AiidaApi, App
    from aiida.restapi.run_api import run_api
    from flask_restful import Resource

To start with, we import the base classes to be extended/employed: ``AiidaApi`` and ``App``.
For simplicity, it is advisable to import the method ``run_api``, as it provides an interface to configure the API, parse command-line arguments, and couple the two classes representing the API and the App.
However, you can refer to the documentation of `flask_restful <https://flask-restful.readthedocs.io/>`_ to configure and hook-up an API through its built-in methods.

Then we define a class representing the additional resource:

.. code-block:: python

    class NewResource(Resource):
        """Resource implementing a GET method returning id, ctime, and attributes of the latest created Dict."""

        def get(self):
            from aiida.orm import Dict, QueryBuilder

            query = QueryBuilder()
            query.append(Dict, project=['id', 'ctime', 'attributes'], tag='pdata')
            query.order_by({'pdata': {'ctime': 'desc'}})
            result = query.first()

            # Results are returned as a dictionary, datetime objects are serialized as ISO 8601
            return dict(
                id=result[0],
                ctime=result[1].isoformat(),
                attributes=result[2]
            )

The class ``NewResource`` contains a single method ``get``.
The name chosen for this method is not arbitrary but fixed by ``Flask`` which is called to respond to HTTP GET requests.
In other words, when the API receives a GET request to the URL ``new-endpoint``, the function ``NewResource.get()`` is called.
The HTTP response is constructed around the data returned by these functions.
The data, which are packed as dictionaries, are serialized by Flask as a JSON stream of data.
All the Python built-in types can be serialized by Flask (e.g. ``int``, ``float``, ``str``, etc.), whereas for serialization of custom types we let you refer to the `Flask documentation <http://flask.pocoo.org/docs/>`_ .
The documentation of Flask is the main source of information also for topics such as customization of HTTP responses, construction of custom URLs (e.g. accepting parameters), and more advanced serialization issues.

Whenever you face the need to handle errors, consider to use the AiiDA REST API-specific exceptions already defined in  :py:class:`aiida.restapi.common.exceptions`.
The reason will become clear slightly later in this section.

Once the new resource is defined, we have to register it to the API by assigning it one (or more) endpoint(s).
This is done in the ``__init__()`` of ``NewApi`` by means of the method ``add_resource()``:

.. code-block:: python

    class NewApi(AiidaApi):

        def __init__(self, app=None, **kwargs):
            """
            This init serves to add new endpoints to the basic AiiDA Api

            """
            super().__init__(app=app, **kwargs)

            self.add_resource(NewResource, '/new-endpoint/', strict_slashes=False)

In our original intentions, the main (if not the only) purpose of overriding the ``__init__()`` method is to register new resources to the API.
In fact, the general form of ``__init__()`` is meant to be:

.. code-block:: python

    class NewApi(AiidaApi):

        def __init__(self, app=None, **kwargs):

            super())

            self.add_resource( ... )
            self.add_resource( ... )
            self.add_resource( ... )

            ...

In the example, indeed, the only characteristic line is :python:`self.add_resource(NewResource, '/new-endpoint/', strict_slashes=False)`.
Anyway, the method ``add_resource()`` is defined and documented in `Flask <http://flask.pocoo.org/docs/>`_.

Finally, the ``main`` code configures and runs the API:

.. code-block:: python

    import aiida.restapi.common as common
    from aiida import load_profile

    CONFIG_DIR = common.__path__[0]

    import click
    @click.command()
    @click.option('-P', '--port', type=click.INT, default=5000,
        help='Port number')
    @click.option('-H', '--hostname', default='127.0.0.1',
        help='Hostname')
    @click.option('-c','--config-dir','config',type=click.Path(exists=True), default=CONFIG_DIR,
        help='the path of the configuration directory')
    @click.option('--debug', 'debug', is_flag=True, default=False,
        help='run app in debug mode')
    @click.option('--wsgi-profile', 'wsgi_profile', is_flag=True, default=False,
        help='to use WSGI profiler middleware for finding bottlenecks in web application')

    def newendpoint(**kwargs):
        """
        runs the REST api
        """
        # Invoke the runner
        run_api(App, NewApi, **kwargs)

    # main program
    if __name__ == '__main__':
        """
        Run the app with the provided options. For example:
        python api.py --host=127.0.0.2 --port=6000
        """

        load_profile()
        newendpoint()

The `click package <https://click.palletsprojects.com/en/7.x/>`_ is used to provide a a nice command line interface to process the options and handle the default values to pass to the ``newendpoint`` function.

The method ``run_api()`` accomplishes several functions: it couples the API to an instance of ``flask.Flask``, namely, the Flask fundamental class representing a web app.
Consequently, the app is configured and, if required, hooked up.

It takes as inputs:

* the classes representing the API and the application.
   We strongly suggest to pass to ``run_api()`` the :py:class:`aiida.restapi.api.App` class, inheriting from ``flask.Flask``, as it handles correctly AiiDA RESTApi-specific exceptions.

* positional arguments representing the command-line arguments/options, passed by the click function.
   Types, defaults and help strings can be set in the ``@click.option`` definitions, and will be handled by the command line call.


A few more things before using the script:

* if you want to customize further the error handling, you can take inspiration by looking at the definition of ``App`` and create your derived class ``NewApp(App)``.


* the supported command line options are identical to those of ``verdi restapi``.
   Use ``verdi restapi --help`` for their full documentation.
   If you want to add more options or modify the existing ones, create you custom runner taking inspiration from ``run_api``.

It is time to run ``api.py``. Type in a terminal

.. code-block:: console

   $ chmod +x api.py
   $ ./api.py --port=6000
      * REST API running on http://127.0.0.1:6000/api/v4
      * Serving Flask app "aiida.restapi.run_api" (lazy loading)
      * Environment: production
        WARNING: This is a development server. Do not use it in a production deployment.
        Use a production WSGI server instead.
      * Debug mode: off
      * Running on http://127.0.0.1:6000/ (Press CTRL+C to quit)

Let's use ``curl`` with the GET method to ask for the latest created node:

.. code-block:: bash

    curl http://127.0.0.2:6000/api/v4/new-endpoint/ -X GET

The form of the output (and only the form) should resemble

.. code-block:: python

    {
        "attributes": {
            "binding_energy_per_substructure_per_unit_area_units": "eV/ang^2",
            "binding_energy_per_substructure_per_unit_area": 0.0220032273047497
        },
        "ctime": "2017-04-05T16:01:06.227942+00:00",
        "id": 403504
    }

whereas the actual values of the response dictionary as well as the internal structure of the attributes field will be in general very different.

As a final remark, there might be circumstances in which you do not want to use the internal werkzeug-based server.
For example, you might want to run the app through Apache using a wsgi script.
In this case, simply use ``configure_api`` to return a custom object ``api``:

.. code-block:: python

    api = configure_api(App, MycloudApi, **kwargs)


The ``app`` can be retrieved by ``api.app``.
This snippet of code becomes the fundamental block of a *wsgi* file used by Apache as documented in  :ref:`how-to:share:serve:deploy`.
Moreover, we recommend to consult the documentation of `mod_wsgi <https://modwsgi.readthedocs.io/>`_.

.. note::
    Optionally, create a click option for the variable ``catch_internal_server`` to be ``False`` in order to let exceptions (including python tracebacks) bubble up to the apache error log.
    This can be particularly useful when the ``app`` is still under heavy development.


.. _internal_architecture:restapi:multiple_profiles:

Serving multiple profiles
=========================

A single REST API instance can serve data from all profiles of an AiiDA instance.
To maintain backwards compatibility, the new functionality needs to be explicitly enabled through the configuration:

.. code-block:: bash

    verdi config set rest_api.profile_switching true

After the REST API is restarted, it will now accept the profile query parameter, for example:

.. code-block:: console

    http://127.0.0.1:5000/api/v4/computers?profile=some-profile-name

If the specified profile is already loaded, the REST API functions exactly as without profile switching enabled.
If another profile is specified, the REST API will first switch profiles before executing the request.
If the profile parameter is specified in a request and the REST API does not have profile switching enabled, a 400 response is returned.
