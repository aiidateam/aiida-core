.. role:: python(code)
   :language: python


How to extend the AiiDA REST API
++++++++++++++++++++++++++++++++

The AiIDA REST API is made of two main classes:

    - ``App``, inheriting ``flask.Flask``. The latter represents any Flask web app, including REST APIs.
    - ``Api``, inheriting ``flask_restful.Api``. This represents the API itself.

Once instanciated both ``Api`` and ``App`` classes into, say, ``app`` and ``api``, these two objects have to be coupled by adding ``app`` as one of the attributes of ``api``. As we will see in a moment, we provide a function that, besides other things, does exactly this.

In a Flask API the resources, e.g. *Nodes*, *Kpoints*, etc., are represented by ``flask_restful.Resource``-derived classes.

If you need to include additional endpoints besides those built in the AiiDA REST API you should:

    - create the resource classes that will be bound to the new endpoints;
    - extend the class ``Api`` into a user-defined class to register the new endpoints.
    - (Optional) Extend ``App`` into a user-defined class for finer customization.


Let's provide a minimal example through which we add the endpoint ``/new-endpoint`` supporting two HTTP methods:

    - *GET*: retrieves the latest created Dict object and returns its ``id``, ``ctime`` in ISO 8601 format, and ``attributes``.
    - *POST*: creates a Dict object with placeholder attributes, stores it, and returns its ``id``.

Let's assume you've put the code in the file ``example.py``, reading:

.. code-block:: python

    #!/usr/bin/env python
    from aiida.restapi.api import AiidaApi, App
    from aiida.restapi.run_api import run_api
    from flask_restful import Resource


    class NewResource(Resource):
        """
        resource containing GET and POST methods. Description of each method
        follows:

        GET: returns id, ctime, and attributes of the latest created Dict.

        POST: creates a Dict object, stores it in the database,
        and returns its newly assigned id.

        """

        def get(self):
            from aiida.orm import QueryBuilder, Dict

            qb = QueryBuilder()
            qb.append(Dict,
                      project=['id', 'ctime', 'attributes'],
                      tag='pdata')
            qb.order_by({'pdata': {'ctime': "desc"}})
            result = qb.first()

            # Results are returned as a dictionary, datetime objects is
            # serialized as ISO 8601
            return dict(id=result[0],
                        ctime=result[1].isoformat(),
                        attributes=result[2])

        def post(self):
            from aiida.orm import Dict

            params = dict(property1="spam", property2="egg")
            paramsData = Dict(dict=params).store()

            return {'id': paramsData.pk}


    class NewApi(AiidaApi):

        def __init__(self, app=None, **kwargs):
            """
            This init serves to add new endpoints to the basic AiiDA Api

            """
            super(NewApi, self).__init__(app=app, **kwargs)

            self.add_resource(NewResource, '/new-endpoint/', strict_slashes=False)


    # Standard boilerplate to run the api
    import sys
    import aiida.restapi.common as common
    config_dir = common.__path__[0]

    if __name__ == '__main__':
        """
        Run the app accepting arguments.

        Ex:
         python example.py --host=127.0.0.2 --port=6000 --config-dir

        Defaults:
         address: 127.0.01:5000,
         config directory: <aiida_path>/aiida/restapi/common
        """

        run_config = dict(
            hookup=True,
            default_config_dir=config_dir,
            default_host='127.0.0.1',
            default_port='5000',
            parse_aiida_profile=False,
        )

        run_api(App, NewApi, *sys.argv[1:], **run_config)


Let us dissect the previous code explaining each part. First things first: the imports.

.. code-block:: python

    from aiida.restapi.api import AiidaApi, App
    from aiida.restapi.run_api import run_api
    from flask_restful import Resource

To start with, we import the base classes to be extended/employed: ``AiidaApi`` and ``App``. For simplicity, it is advisable to import the method ``run_api``, as it provides an interface to configure the Api, parse command-line arguments, and couple the two classes representing the Api and the App. However, you can refer to the documentation of `flask_restful <https://flask-restful.readthedocs.io/>`_ to configure and hook-up an Api through its built-in methods.

Then we define a class representing the additional resource:

.. code-block:: python

    class NewResource(Resource):
        """
        resource containing GET and POST methods. Description of each method
        follows:

        GET: returns id, ctime, and attributes of the latest created Dict.

        POST: creates a Dict object, stores it in the database,
        and returns its newly assigned id.

        """

        def get(self):
            from aiida.orm import QueryBuilder, Dict

            qb = QueryBuilder()
            qb.append(Dict,
                      project=['id', 'ctime', 'attributes'],
                      tag='pdata')
            qb.order_by({'pdata': {'ctime': "desc"}})
            result = qb.first()

            # Results are returned as a dictionary, datetime objects is
            # serialized as ISO 8601
            return dict(id=result[0],
                        ctime=result[1].isoformat(),
                        attributes=result[2])

        def post(self):
            from aiida.orm import Dict

            params = dict(property1="spam", property2="egg")
            paramsData = Dict(dict=params).store()

            return {'id': paramsData.pk}

The class ``NewResource`` contains two methods: ``get`` and ``post``. The names chosen for these functions are not arbitrary but fixed by ``Flask`` to individuate the functions that respond to HTTP request of type GET and POST, respectively. In other words, when the API receives a GET (POST) request to the URL ``new-endpoint``, the function ``NewResource.get()`` (``NewResource.post()``) will be executed. The HTTP response is constructed around the data returned by these functions. The data, which are packed as dictionaries, are serialized by Flask as a JSON stream of data. All the Python built-in types can be serialized by Flask (e.g. ``int``, ``float``, ``str``, etc.), whereas for serialization of custom types we let you refer to the `Flask documentation <http://flask.pocoo.org/docs/>`_ . The documentation of Flask is the main source of information also for topics such as customization of HTTP responses, construction of custom URLs (e.g. accepting parameters), and more advanced serialization issues.

Whenever you face the need to handle errors, consider to use the AiiDA REST API-specific exceptions already defined in ``aiida.restapi.common.exceptions``. The reason will become clear slightly later in this section.

Once the new resource is defined, we have to register it to the API by assigning it one (or more) endpoint(s). This is done in the ``__init__()`` of ``NewApi`` by means of the method ``add_resource()``:

.. code-block:: python

    class NewApi(AiidaApi):

        def __init__(self, app=None, **kwargs):
            """
            This init serves to add new endpoints to the basic AiiDA Api

            """
            super(NewApi, self).__init__(app=app, **kwargs)

            self.add_resource(NewResource, '/new-endpoint/', strict_slashes=False)

In our original intentions, the main (if not the only) purpose of overriding the ``__init__()`` method is to register new resources to the API. In fact, the general form of ``__init__()`` is meant to be:

.. code-block:: python

    class NewApi(AiidaApi):

        def __init__(self, app=None, **kwargs):

            super(NewApi, self.__init__(app=app, *kwargs))

            self.add_resource( ... )
            self.add_resource( ... )
            self.add_resource( ... )

            ...

In the example, indeed, the only characteristic line is :python:`self.add_resource(NewResource, '/new-endpoint/', strict_slashes=False)`. Anyway, the method ``add_resource()`` is defined and documented in `Flask <http://flask.pocoo.org/docs/>`_.

Finally, the ``main`` code configures and runs the API, thanks to the method ``run_api()``:

.. code-block:: python

    # Standard boilerplate to run the api
    import sys
    import aiida.restapi.common as common
    config_dir = common.__path__[0]

    if __name__ == '__main__':
        """
        Run the app accepting arguments.

        Ex:
         python example.py --host=127.0.0.2 --port=6000 --config-dir '<path_to_config.py>'

        Defaults:
         address: 127.0.01:5000,
         config directory: <aiida_path>/aiida/restapi/common
        """

        run_config = dict(
            hookup=True,
            default_config_dir=config_dir,
            default_host='127.0.0.1',
            default_port='5000'
        )

        run_api(App, NewApi, *sys.argv[1:], **run_config)


The method ``run_api()`` accomplishes several functions: it couples the API to an instance of ``flask.Flask``, namely, the Flask fundamental class representing a web app. Consequently, the app is configured and, if required, hooked up.
The spirit of ``run_api`` is to take all the ingredients to setup an API and use them to build up a command-line utility that serves to hook it up.

It requires as inputs:

    - the classes representing the Api and the App. We strongly suggest to pass to ``run_api()`` the class ``aiida.restapi.api.App``, inheriting from ``flask.Flask``, as it handles correctly AiiDA RESTApi-specific exceptions.

    - a tuple of positional arguments representing the command-line arguments/options (notice the use of ``sys.argv``);

    - a dictionary of key-value arguments to set the default values of the command line options, e.g. ``--port``, ``--host``,  ``--config-dir`` and ``--aiida-profile``. If no default is set, the app will use ``5000``, ``127.0.0.1``, ``aiida.restapi.common`` and ``False``, respectively.

You should know few more things before using the script:

    - If you want to customize further the error handling, you can take inspiration by looking at the definition of ``App`` and create your derived class ``NewApp(App)``.

    - The option ``hookup`` of the configuration dictionary must be set to ``True`` to use the script to start the API from command line. Below, we will show when it is appropriate to set ``hookup=False``.

    - the supported command line options are identical to those of ``verdi restapi``. Use ``verdi restapi --help`` for their full documentation. If you want to add more options or modify the existing ones, create you custom runner taking inspiration from ``run_api``.

It is time to run ``example.py``. Type in a terminal

.. code-block:: bash

    chmod +x example.py
    ./example.py --host=127.0.0.2 --port=6000

You should read the message

.. code-block:: bash

   * Running on http://127.0.0.2:6000/ (Press CTRL+C to quit)

To route a request to the API from a terminal you can employ ``curl``. Alternatively, you can use any REST client providing a GUI. Let us first ask for the latest created node through the GET method:

.. code-block:: bash

    curl http://127.0.0.2:6000/api/v2/new-endpoint/ -X GET

The form of the output (and only the form) should resemble

.. code-block:: bash

    {"attributes": {"binding_energy_per_substructure_per_unit_area_units": "eV/ang^2", "binding_energy_per_substructure_per_unit_area": 0.0220032273047497}, "ctime": "2017-04-05T16:01:06.227942+00:00", "id": 403504}

, whereas the actual values of the response dictionary as well as the internal structure of the attributes field will be in general very different.

Now, let us create a node through the POST method, and check it again through GET:

.. code-block:: bash

    curl http://127.0.0.2:6000/api/v2/new-endpoint/ -X POST
    {"id": 410618}
    curl http://127.0.0.2:6000/api/v2/new-endpoint/ -X GET
    {"attributes": {"property1": "spam", "property2": "egg"}, "ctime": "2017-06-20T15:36:56.320180+00:00", "id": 410618}

The POST request triggers the creation of a new Dict node, as confirmed by the response to the GET request.

As a final remark, there might be circumstances in which you do not want to hook up the API from command line. For example, you might want to expose the API through Apache for production, rather than the built-in Flask server. In this case, you can invoke ``run_api`` to return two custom objects ``app`` and ``api``.

.. code-block:: python

    run_config = dict(
        hookup=False,
        catch_internal_server=False,
    )

    (app, api) = run_api(App, McloudApi, *sys.argv[1:], **run_config)

This snippet of code becomes the fundamental block of a *wsgi* file used by Apache as documented in  :ref:`restapi_apache`. Moreover, we recommend to consult the documentation of `mod_wsgi <https://modwsgi.readthedocs.io/mod_wsgi>`_.

Notice that we have set ``hookup=False`` and ``catch_internal_server=False``. It is clear why the app is no longer required to be hooked up, i.e. Apache will do the job for us. The second option, instead, is not mandatory but potentially useful. It lets the exceptions thrown during the execution of the apps propagate all the way through until they reach the logger of Apache. Especially when the app is not entirely stable yet, one would like to read the full python error traceback in the Apache error log.
