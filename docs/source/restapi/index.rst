.. _rest_api:

===================
REST API for AiiDA
===================

AiiDA provides a
`RESTful <https://en.wikipedia.org/wiki/Representational_state_transfer>`_
`API <https://en.wikipedia.org/wiki/Application_programming_interface>`_
that provides access to the AiiDA objects stored in the database.

The AiiDA REST API is implemented using the ``Flask RESTFul`` framework
and supports only GET methods (reading) for the time being.
The response contains the data in ``JSON`` format.

In this document, file paths are given relative to the AiiDA installation folder.
The source files of the API are contained in the folder ``aiida/restapi``.

Running the REST API
++++++++++++++++++++

To start the REST server open a terminal and type

.. code-block:: bash

    verdi restapi

This command will hook up a REST API with the default parameters, namely on port ``5000`` of ``localhost``, connecting
to the default AiiDA profile and assuming the default folder for the REST configuration files, namely ``common``.

For an overview of options accepted by ``verdi restapi`` you can type

.. code-block:: bash

    verdi restapi --help


Like all ``verdi`` commands, the AiiDA profile can be changed by putting ``-p PROFILE`` right after ``verdi``.

.. code-block:: bash

    verdi -p <another_profile> restapi

The base URL for your REST API is::

        http://localhost:5000/api/v3

where the last field identifies the version of the API (currently ``v3``).
Simply type this URL in your browser or use command-line tools such as ``curl`` or ``wget``.

.. note:: Note that the ``v2`` version of the API was used for versions of AiiDA previous to 1.0.0b3.

For the full list of configuration options, see the file ``aiida/restapi/common/config.py``.


General form of the URLs
++++++++++++++++++++++++

A generic URL to send requests to the REST API is formed by:

    1. The base URL. It specifies the host and the version of the API. Example::

        http://localhost:5000/api/v3

    2. The path. It defines the kind of resource requested by the client and the type of query. Example::

        ../nodes/..

    3. The query string (not mandatory). It can be used for any further specification of the request, e.g. to introduce
       query filters, to give instructions for ordering, to set how results have to be paginated, etc. Example::

        ?id=200

The query string is introduced by the question mark character ``?``. Here are some examples::

  http://localhost:5000/api/v3/users/
  http://localhost:5000/api/v3/computers?scheduler_type="slurm"
  http://localhost:5000/api/v3/nodes/?id>45&node_type=like="data%"

The trailing slash at the end of the path is not mandatory.

How to set the number of results
--------------------------------

Before exploring in details the functionalities of the API it is important to know that the AiiDA REST API provides two
different ways to limit the number of results returned by the server:
using pagination, or specifying explicitly *limit* and *offset*.

Pagination
**********

The complete set of results is divided in *pages* containing by default 20 results each.
Individual pages are accessed by appending ``/page/(PAGE)`` to the end of the path, where ``(PAGE)`` has to be replaced
by the number of the required page.
The number of results contained in each page can be altered by specifying the ``perpage=(PERPAGE)`` field in the
query string. Note that ``(PERPAGE)`` values larger than 400 are not allowed. Examples::

    http://localhost:5000/api/v3/computers/page/1?
    http://localhost:5000/api/v3/computers/page/1?perpage=5
    http://localhost:5000/api/v3/computers/page

If no page number is specified, as in the last example, the system redirects the request to page 1.
When pagination is used the **header** of the response contains two more non-empty fields:

    - ``X-Total-Counts`` (custom field): the total number of results returned by the query, i.e. the sum of the results
      of all pages
    - ``Links``: links to the first, previous, next, and last page. Suppose that you send a request whose results  fill
      8 pages. Then the value of the ``Links`` field would look like::

            <\http://localhost:5000/.../page/1?... >; rel=first,
            <\http://localhost:5000/.../page/3?... >; rel=prev,
            <\http://localhost:5000/.../page/5?... >; rel=next,
            <\http://localhost:5000/.../page/8?... >; rel=last

Setting *limit* and *offset*
****************************

You can specify two special fields in the query string:

    - ``limit=(LIMIT)``: field that specifies the largest number of results that will be returned, ex: "limit=20".
      The default and highest allowed ``LIMIT`` is 400.
    - ``offset=(OFFSET)``: field that specifies how many entries are skipped before returning results, ex:
      ``offset=20``. By default no offset applies.

Example::

    http://localhost:5000/api/v3/computers/?limit=3&offset=2


How to build the path
---------------------

The first element of the path is the *Resource* corresponding to the
AiiDA object(s) you want to request. The following resources are available:

+-------------------------------------------------------------------------+-------------------+
| Class                                                                   | Resource          |
+=========================================================================+===================+
| :py:class:`ProcessNode <aiida.orm.nodes.process.ProcessNode>`           | ``/calculations`` |
+-------------------------------------------------------------------------+-------------------+
| :py:class:`Computer <aiida.orm.Computer>`                               | ``/computers``    |
+-------------------------------------------------------------------------+-------------------+
| :py:class:`Data <aiida.orm.nodes.data.data.Data>`                       | ``/data``         |
+-------------------------------------------------------------------------+-------------------+
| :py:class:`Group <aiida.orm.groups.Group>`                              | ``/groups``       |
+-------------------------------------------------------------------------+-------------------+
| :py:class:`Node <aiida.orm.nodes.Node>`                                 | ``/nodes``        |
+-------------------------------------------------------------------------+-------------------+
| :py:class:`User <aiida.orm.User>`                                       | ``/users``        |
+-------------------------------------------------------------------------+-------------------+
| :py:class:`Code <aiida.orm.nodes.data.code.Code>`                       | ``/codes``        |
+-------------------------------------------------------------------------+-------------------+
| :py:class:`BandsData <aiida.orm.nodes.data.array.bands.BandsData>`      | ``/bands``        |
+-------------------------------------------------------------------------+-------------------+
| :py:class:`CifData <aiida.orm.nodes.data.cif.CifData>`                  | ``/cifs``         |
+-------------------------------------------------------------------------+-------------------+
| :py:class:`KpointsData <aiida.orm.nodes.data.array.kpoints.KpointsData>`| ``/kpoints``      |
+-------------------------------------------------------------------------+-------------------+
| :py:class:`StructureData <aiida.orm.nodes.data.structure.StructureData>`| ``/structures``   |
+-------------------------------------------------------------------------+-------------------+
| :py:class:`UpfData <aiida.orm.nodes.data.upf.UpfData>`                  | ``/upfs``         |
+-------------------------------------------------------------------------+-------------------+

For a **full list** of available endpoints for each resource, simply query the base URL of the REST API (e.g. ``http://localhost:5000``).

There are two types of paths: you may either request a list of objects
or one specific object of a resource.

If no specific endpoint is appended to the name of the resource, the API
returns the full list of objects of that resource (default limits apply).

Appending the endpoint ``schema`` to a
resource will give the list of fields that are normally returned by the API for
an object of a specific resource, whereas the endpoint ``statistics`` returns a
list of statistical facts concerning a resource.
Here are few examples of valid URIs::

    http://localhost:5000/api/v3/nodes/statistics
    http://localhost:5000/api/v3/users/
    http://localhost:5000/api/v3/groups/schema


If you request informations of a specific object, in general you have to append its entire *uuid* or the starting pattern of its *uuid* to the path.
 Here are two examples that should return the same object::

    http://localhost:5000/api/v3/nodes/338357f4-f236-4f9c-8fbe-cd550dc6b858
    http://localhost:5000/api/v3/nodes/338357f4-f2

In the first URL, we have specified the full *uuid*, whereas in the second only a chunk of its first characters that is
sufficiently long to match only one *uuid* in the database.

.. note:: Using *id* in place of *uuid* is not allowed anylonger, e.g.  ``http://localhost:5000/api/v3/nodes/201`` does not work.
    Use ``http://localhost:5000/api/v3/nodes?id=201`` instead.

Il the *uuid* pattern is not long enough to identify a unique object, the API will raise an exception.
The only exception to this rule is the resource *users* since the corresponding AiiDA``User`` class has no *uuid*
attribute. In this case, you have to specify the *id* (integer) of the object. Here is an example::

    http://localhost:5000/api/v3/users?id=2

When you ask for a single object (and only in that case) you can construct more complex requests, namely, you can ask
for its inputs/outputs or for its attributes/extras.
In the first case you have to append to the path the string ``/io/inputs`` or ``io/outputs`` depending on the desired
relation between the nodes, whereas in the second case you have to append ``content/attributes`` or ``content/extras``
depending on the kind of content you want to access. Here are some examples::

    http://localhost:5000/api/v3/calculations/338357f4-f2/io/inputs
    http://localhost:5000/api/v3/nodes/338357f4-f2/io/inputs
    http://localhost:5000/api/v3/data/338357f4-f2/content/attributes
    http://localhost:5000/api/v3/nodes/338357f4-f2/content/extras

.. note:: As you can see from the last examples, a *Node* object can be accessed requesting either a generic ``nodes``
    resource or requesting the resource corresponding to its specific node type (``data``, ``codes``, ``calculations``,
    ``kpoints``, ... ).
    This is because in AiiDA the classes *Data* and *Calculation* are derived from the class *Node*.
    In turn, *Data* is the baseclass of a number of built-in and custom classes, e.g. ``KpointsData``,
    ``StructureData``, ``BandsData``, ``Code``, ...

How to build the query string
-----------------------------

The query string is formed by one or more fields separated by the special character ``&``.
Each field has the form (``key``)(``operator``)(``value``).
The same constraints that apply to the names of python variables determine what are the valid keys, namely,
only alphanumeric characters plus ``_`` are allowed and the first character cannot be a number.

Special keys
************

There are several special keys that can be specified only once in a query string.
All of them must be followed by the operator ``=``. Here is the complete list:

    :limit: This key only supports integer values.

    :offset: Same format as ``limit``.

    :perpage: Same format as ``limit``.

    :orderby: This key is used to impose a specific ordering to the results. Two orderings are supported, ascending or
        descending.
        The value for the ``orderby`` key must be the name of the property with respect to which to order the results.
        Additionally, ``+`` or ``-`` can be pre-pended to the value in order to select, respectively, ascending or
        descending order.
        Specifying no leading character is equivalent to select ascending order.
        Ascending (descending) order for strings corresponds to alphabetical (reverse-alphabetical) order, whereas for
        datetime objects it corresponds to chronological (reverse-chronological order). Examples:

        ::

            http://localhost:5000/api/v3/computers?orderby=+id
            http://localhost:5000/api/v3/computers?orderby=+name
            http://localhost:5000/api/v3/computers?orderby=-uuid


    :alist: This key is used to specify which attributes of a specific object have to be returned.
        The desired attributes have to be provided as a comma-separated list of values.
        It requires that the path contains the endpoint ``/content/attributes``. Example:

        ::

            http://localhost:5000/api/v3/codes/4fb10ef1-1a/content/attributes?alist=append_text,prepend_text


    :nalist: (incompatible with ``alist``) This key is used to specify which attributes of a specific object should not
        be returned. The syntax is identical to ``alist``.
        The system returns all the attributes except those specified in the list of values.

    :elist: Similar to ``alist`` but for extras. It requires that the path contains the endpoint ``/content/extras``.

    :nelist: (incompatible with ``elist``) Similar to ``nalist`` but for extras.
        It requires that the path contains the endpoint ``/content/extras``.

Filters
*******

All the other fields composing a query string are filters, that is, conditions that have to be fulfilled by the
retrieved objects. When a query string contains multiple filters, those are applied as if they were related by the AND
logical clause, that is, the results have to fulfill all the conditions set by the filters (and not any of them).
Each filter key is associated to a unique value type. The possible types are:

    :string: Text enclosed in double quotes.
        If the string contains double quotes those have to be escaped as ``""`` (two double quotes).
        Note that in the unlikely occurrence of a sequence of double quotes you will have to escape it by writing twice
        as many double quotes.

    :integer: Positive integer numbers.

    :datetime: Datetime objects expressed in the format ``(DATE)T(TIME)(SHIFT)`` where ``(SHIFT)`` is the time
        difference with respect to the UTC time.
        This is required to avoid any problem arising from comparing datetime values expressed in different time zones.
        The formats of each field are:

        1. ``YYYY-MM-DD`` for ``(DATE)`` (mandatory).
        2. ``HH:MM:SS`` for ``(TIME)`` (optional). The formats ``HH`` and ``HH:MM`` are supported too.
        3. ``+/-HH:MM`` for ``(SHIFT)`` (optional, if present requires ``(TIME)`` to be specified). The format
           ``+/-HH`` is allowed too. If no shift is specified UTC time is assumed.
           The shift format follows the general convention that eastern (western) shifts are positive (negative).
           The API is unaware of daylight saving times so the user is required to adjust the shift to take them into
           account.

        This format is ``ISO-8601`` compliant. Note that date and time fields have to be separated by the character
        ``T``. Examples:

        ::

            http://localhost:5000/api/v3/nodes?ctime>2019-04-23T05:45+03:45
            http://localhost:5000/api/v3/nodes?ctime<2019-04-23T05:45
            http://localhost:5000/api/v3/nodes?mtime>=2019-04-23


    :bool: It can be either true or false (lower case).

The following table reports what is the value type and the supported resources associated to each key.

.. note:: In the following *id* is a synonym for *pk* (often used in other sections of the documentation).

.. note:: If a key is present in the resource *data*, it will be also in the derived resources: *structures*, *kpoints*,
    *bands*, ...

+--------------+----------+---------------------------------------------------+
|key           |value type|resources                                          |
+==============+==========+===================================================+
|id            |integer   |users, computers, groups, nodes, calculations, data|
+--------------+----------+---------------------------------------------------+
|user_id       |integer   |groups                                             |
+--------------+----------+---------------------------------------------------+
|uuid          |string    |computers, groups, nodes, calculations, data       |
+--------------+----------+---------------------------------------------------+
|name          |string    |computers                                          |
+--------------+----------+---------------------------------------------------+
|first_name    |string    |users                                              |
+--------------+----------+---------------------------------------------------+
|last_name     |string    |users                                              |
+--------------+----------+---------------------------------------------------+
|institution   |string    |users                                              |
+--------------+----------+---------------------------------------------------+
|email *       |string    |users                                              |
+--------------+----------+---------------------------------------------------+
|label         |string    |groups, nodes, calculations, data                  |
+--------------+----------+---------------------------------------------------+
|description   |string    |computers, groups                                  |
+--------------+----------+---------------------------------------------------+
|transport_type|string    |computers                                          |
+--------------+----------+---------------------------------------------------+
|scheduler_type|string    |computers                                          |
+--------------+----------+---------------------------------------------------+
|attributes    |string    |nodes, calculations, data                          |
+--------------+----------+---------------------------------------------------+
|ctime         |datetime  |nodes, calculations, data                          |
+--------------+----------+---------------------------------------------------+
|mtime         |datetime  |nodes, calculations, data                          |
+--------------+----------+---------------------------------------------------+
|user_email    |string    |groups, nodes, calculations, data                  |
+--------------+----------+---------------------------------------------------+
|node_type     |string    |nodes, calculations, data                          |
+--------------+----------+---------------------------------------------------+
|type_string   |string    |groups                                             |
+--------------+----------+---------------------------------------------------+
|hostname      |string    |computers                                          |
+--------------+----------+---------------------------------------------------+

\* Key not available via the ``/users/`` endpoint for reasons of privacy.

The operators supported by a specific key are uniquely determined by the value type associated to that key.
For example, a key that requires a boolean value admits only the identity operator ``=``, whereas an integer value
enables the usage of the relational operators ``=``, ``<``, ``<=``, ``>``, ``>=`` plus the membership operator ``=in=``.
Please refer to the following table for a comprehensive list.

+-----------+------------------------+---------------------------------+
|operator   |meaning                 |accepted value types             |
+===========+========================+=================================+
|``=``      |identity                |integers, strings, bool, datetime|
+-----------+------------------------+---------------------------------+
|``>``      |greater than            |integers, strings, datetime      |
+-----------+------------------------+---------------------------------+
|``<``      |lower than              |integers, strings, datetime      |
+-----------+------------------------+---------------------------------+
|``>=``     |greater than or equal to|integers, strings, datetime      |
+-----------+------------------------+---------------------------------+
|``<=``     |lower than or equal to  |integers, strings, datetime      |
+-----------+------------------------+---------------------------------+
|``=like=`` |pattern matching        |strings                          |
+-----------+------------------------+---------------------------------+
|``=ilike=``|case-insensitive        |strings                          |
|           |pattern matching        |                                 |
+-----------+------------------------+---------------------------------+
|``=in=``   |identity with one       |integers, strings, datetime      |
|           |element of a list       |                                 |
+-----------+------------------------+---------------------------------+

The pattern matching operators ``=like=`` and ``=ilike=`` must be followed by the pattern definition, namely, a string
where two characters assume special meaning:

    1. ``%`` is used to replace an arbitrary sequence of characters, including no characters.
    2. ``_`` is used to replace one or zero characters.

Differently from ``=like=``, ``=ilike=`` assumes that two characters that only differ in the case are equal.

To prevent interpreting special characters as wildcards, these have to be escaped by pre-pending the character ``\``.

Examples:

+-----------------------------------------------------+-------------------------------------+------------------+
| Filter                                              | Matched string                      |Non-matched string|
+=====================================================+=====================================+==================+
| ``name=like="a%d_"``                                |       "aiida"                       |     "AiiDA"      |
+-----------------------------------------------------+-------------------------------------+------------------+
| ``name=ilike="a%d_"``                               |   "aiida", "AiiDA"                  |                  |
+-----------------------------------------------------+-------------------------------------+------------------+
| ``name=like="a_d_"``                                |                                     |     "aiida"      |
+-----------------------------------------------------+-------------------------------------+------------------+
| ``name=like="aii%d_a"``                             |        "aiida"                      |                  |
+-----------------------------------------------------+-------------------------------------+------------------+
| ``uuid=like="cdfd48%"``                             |"cdfd48f9-7ed2-4969-ba06-09c752b83d2"|                  |
+-----------------------------------------------------+-------------------------------------+------------------+
|``description=like="This calculation is %\% useful"``|"This calculation is 100% useful"    |                  |
+-----------------------------------------------------+-------------------------------------+------------------+

The membership operator ``=in=`` has to be followed by a comma-separated list of values of the same type.
The condition is fulfilled if the column value of an object is an element of the list.

Examples::

    http://localhost:5000/api/v3/nodes?id=in=45,56,78
    http://localhost:5000/api/v3/computers/?scheduler_type=in="slurm","pbs"

The relational operators '<', '>', '<=', '>=' assume natural ordering for integers, (case-insensitive) alphabetical
ordering for strings, and chronological ordering for datetime values.

Examples:

    - ``http://localhost:5000/api/v3/nodes?id>578`` selects the nodes having an id larger than 578.
    - ``http://localhost:5000/api/v3/users/?last_name<="m"`` selects only the users whose last name begins with a
      character in the range [a-m].


.. note:: Node types have to be specified by a string that defines their position in the AiiDA source tree ending
    with a dot. Examples:

    - ``node_type="data.code.Code."`` selects only objects of *Code* type
    - ``node_type="data.remote.RemoteData."`` selects only objects of *RemoteData* type

.. note:: If you use in your request the endpoint *io/input* (*io/outputs*) together with one or more filters, the
    latter are applied to the input (output) nodes of the selected *id*. For example, the request:

        ::

            http://localhost:5000/api/v3/nodes/a67fba41-8a/io/outputs/?node_type="data.folder.FolderData."

    would first search for the outputs of the node with *uuid* starting with "a67fba41-8a" and then select only those
    nodes of type *FolderData*.



The HTTP response
+++++++++++++++++

The HTTP response of the REST API consists in a JSON object, a header, and a status code. Possible status are:

    1. 200 for successful requests.
    2. 400 for bad requests. In this case, the JSON object contains only an error message describing the problem.
    3. 500 for a generic internal server error. The JSON object contains only a generic error message.
    4. 404 for invalid URL.
       Differently from the 400 status, it is returned when the REST API does not succeed in directing the request
       to a specific resource.
       This typically happens when the path does not match any of the supported format. No JSON is returned.

The header is a standard HTTP response header with the additional custom field ``X-Total-Counts`` and, only if
paginated results are required, a non-empty ``Link`` field, as described in the Pagination section.

The JSON object mainly contains the list of the results returned by the API.
This list is assigned to the key ``data``.
Additionally, the JSON object contains several informations about the request (keys ``method``, ``url``, ``url_root``,
``path``, ``query_string``, and ``resource_type``).


.. _restapi_apache:

How to run the REST API through Apache
++++++++++++++++++++++++++++++++++++++
By default ``verdi restapi`` hooks up the REST API through the HTTP server (Werkzeug) that is  usually bundled with
Python distributions.
However, to deploy real web applications the server of choice is in most cases `Apache <https://httpd.apache.org/>`_.
In fact, you can instruct Apache to run Python applications by employing the `WSGI <modwsgi.readthedocs.io/>`_ module
and the AiiDA REST API is inherently structured so that you can easily realize the pipeline ``AiiDA-> WSGI-> Apache``.
Moreover, one single Apache service can support multiple apps so that you can, for instance, hook up multiple APIs
using as many different sets of configurations.
For example, one might have several apps connecting to different AiiDA profiles.
We'll go through an example to explain how to achieve this result.

We assume you have a working installation of Apache that includes ``mod_wsgi``.

The goal of the example is to hookup the APIs ``django`` and ``sqlalchemy`` pointing to two AiiDA profiles, called for
simplicity ``django`` and ``sqlalchemy``.

All the relevant files are enclosed under the path ``/docs/wsgi/`` starting from the AiiDA source code path.
In each of the folders ``app1/`` and ``app2/``, there is a file named ``rest.wsgi`` containing a python script that
instantiates and configures a python web app called ``application``, according to the rules of ``mod_wsgi``.
For how the script is written, the object ``application`` is configured through the file ``config.py`` contained in the
same folder. Indeed, in ``app1/config.py`` the variable ``aiida-profile`` is set to ``"django"``, whereas in
``app2/config.py`` its value is ``"sqlalchemy"``.

Anyway, the path where you put the ``.wsgi`` file as well as its name are irrelevant as long as they are correctly
referred to in the Apache configuration file, as shown later on.
Similarly, you can place ``config.py`` in a custom path, provided you change the variable ``config_file_path`` in
the ``wsgi file`` accordingly.

In ``rest.wsgi`` probably the only options you might want to change is ``catch_internal_server``.
When set to ``True``, it lets the exceptions thrown during the execution of the app propagate all the way through until
they reach the logger of Apache.
Especially when the app is not entirely stable yet, one would like to read the full python error traceback in the
Apache error log.

Finally, you need to setup the Apache site through a proper configuration file.
We provide two template files: ``one.conf`` or ``many.conf``.
The first file tells Apache to bundle both apps in a unique Apache daemon process.
Apache usually creates multiple process dynamically and with this configuration each process will handle both apps.

The script ``many.conf``, instead, defines two different process groups, one for each app.
So the processes created dynamically by Apache will always be handling one app each.
The minimal number of Apache daemon processes equals the number of apps, contrarily to the first architecture, where
one process is enough to handle two or even a larger number of apps.

Let us call the two apps for this example ``django`` and ``sqlalchemy``.
In both ``one.conf`` and ``many.conf``, the important directives that should be updated if one changes the paths or
names of the apps are:

    - ``WSGIProcessGroup`` to define the process groups for later reference.
      In ``one.conf`` this directive appears only once to define the generic group ``profiles``, as there is only one
      kind of process handling both apps.
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

The latest step is to move either ``one.conf`` or ``many.conf`` into the Apache configuration folder and restart
the Apache server. In Ubuntu, this is usually done with the commands:

.. code-block:: bash

    cp <conf_file>.conf /etc/apache2/sites-enabled/000-default.conf
    sudo service apache2 restart

We believe the two basic architectures we have just explained can be successfully applied in many different deployment
scenarios.
Nevertheless, we suggest users who need finer tuning of the deployment setup to look into to the official documentation
of `Apache <https://httpd.apache.org/>`_ and, more importantly, `WSGI <wsgi.readthedocs.io/>`__.

The URLs of the requests handled by Apache must start with one of the paths specified in the directives
``WSGIScriptAlias``.
These paths identify uniquely each app and allow Apache to route the requests to their correct apps.
Examples of well-formed URLs are:

.. code-block:: bash

    curl http://localhost/django/api/v3/computers -X GET
    curl http://localhost/sqlalchemy/api/v3/computers -X GET

The first (second) request will be handled by the app ``django`` (``sqlalchemy``), namely will serve results fetched
from the profile ``django`` (``sqlalchemy``).
Notice that we haven't specified any port in the URLs since Apache listens conventionally to port 80, where any request
lacking the port is automatically redirected.

Examples
++++++++


Computers
---------

1. Get a list of the *Computers* objects.

    REST URL::

        http://localhost:5000/api/v3/computers?limit=3&offset=2&orderby=id

    Description:

        returns the list of three *Computer* objects (``limit=3``) starting from the 3rd
        row (``offset=2``) of the database table and the list will be ordered
        by ascending values of ``id``.

    Response::

        {
          "data": {
            "computers": [
              {
                "description": "Alpha Computer",
                "hostname": "alpha.aiida.net",
                "id": 3,
                "name": "Alpha",
                "scheduler_type": "slurm",
                "transport_type": "ssh",
                "uuid": "9b5c84bb-4575-4fbe-b18c-b23fc30ec55e"
              },
              {
                "description": "Beta Computer",
                "hostname": "beta.aiida.net",
                "id": 4,
                "name": "Beta",
                "scheduler_type": "slurm",
                "transport_type": "ssh",
                "uuid": "5d490d77-638d-4d4b-8288-722f930783c8"
              },
              {
                "description": "Gamma Computer",
                "hostname": "gamma.aiida.net",
                "id": 5,
                "name": "Gamma",
                "scheduler_type": "slurm",
                "transport_type": "ssh",
                "uuid": "7a0c3ff9-1caf-405c-8e89-2369cf91b634"
              }
            ]
          },
          "method": "GET",
          "path": "/api/v3/computers",
          "query_string": "limit=3&offset=2&orderby=id",
          "resource_type": "computers",
          "url": "http://localhost:5000/api/v3/computers?limit=3&offset=2&orderby=id",
          "url_root": "http://localhost:5000/"
        }



2. Get details of a single *Computer* object:

    REST URL::

        http://localhost:5000/api/v3/computers/5d490d77-638d

    Description:

        returns the details of the *Computer* object ``uuid="5d490d77-638d..."``.

    Response::

        {
          "data": {
            "computers": [
              {
                "description": "Beta Computer",
                "hostname": "beta.aiida.net",
                "id": 4,
                "name": "Beta",
                "scheduler_type": "slurm",
                "transport_type": "ssh",
                "uuid": "5d490d77-638d-4d4b-8288-722f930783c8"
              }
            ]
          },
          "method": "GET",
          "path": "/api/v3/computers/5d490d77-638d",
          "query_string": "",
          "resource_type": "computers",
          "url": "http://localhost:5000/api/v3/computers/5d490d77-638d",
          "url_root": "http://localhost:5000/"
        }


Nodes
-----

1.  Get a list of *Node* objects

    REST URL::

        http://localhost:5000/api/v3/nodes?limit=2&offset=8&orderby=-id

    Description:

        returns the list of two *Node* objects (``limit=2``) starting from 9th
        row (``offset=8``) of the database table and the list will be ordered
        by ``id`` in descending order.

    Response::

        {
          "data": {
            "nodes  ": [
              {
                "attributes": {...},
                "ctime": "Fri, 29 Apr 2019 19:24:12 GMT",
                "extras": {},
                "id": 386913,
                "label": "",
                "mtime": "Fri, 29 Apr 2019 19:24:13 GMT",
                "node_type": "process.calculation.calcfunction.CalcFunctionNode.",
                "user_email": "aiida@theossrv5.epfl.ch",
                "user_id": 3,
                "uuid": "68d2ed6c-6f51-4546-8d10-7fe063525ab8"
              },
              {
                "attributes": {...},
                "ctime": "Fri, 29 Apr 2019 19:24:00 GMT",
                "extras": {},
                "id": 386912,
                "label": "",
                "mtime": "Fri, 29 Apr 2019 19:24:00 GMT",
                "node_type": "data.dict.Dict.",
                "user_email": "aiida@theossrv5.epfl.ch",
                "user_id": 3,
                "uuid": "a39dc158-fedd-4ea1-888d-d90ec6f86f35"
              }
            ]
          },
          "method": "GET",
          "path": "/api/v3/nodes",
          "query_string": "limit=2&offset=8&orderby=-id",
          "resource_type": "nodes",
          "url": "http://localhost:5000/api/v3/nodes?limit=2&offset=8&orderby=-id",
          "url_root": "http://localhost:5000/"
        }

2. Get the details of a single *Node* object:

    REST URL::

        http://localhost:5000/api/v3/nodes/e30da7cc

    Description:

        returns the details of the *Node* object with ``uuid="e30da7cc..."``.

    Response::

        {
          "data": {
            "nodes  ": [
              {
                "attributes": {...},
                "ctime": "Fri, 14 Aug 2018 13:18:04 GMT",
                "extras": {},
                "id": 1,
                "label": "",
                "mtime": "Mon, 25 Jan 2019 14:34:59 GMT",
                "node_type": "data.dict.Dict.",
                "user_email": "aiida@theossrv5.epfl.ch",
                "user_id": 3,
                "uuid": "e30da7cc-af50-40ca-a940-2ac8d89b2e0d"
              }
            ]
          },
          "method": "GET",
          "path": "/api/v3/nodes/e30da7cc",
          "query_string": "",
          "resource_type": "nodes",
          "url": "http://localhost:5000/api/v3/nodes/e30da7cc",
          "url_root": "http://localhost:5000/"
        }

3. Get the list of inputs of a specific node.

    REST URL::

        http://localhost:5000/api/v3/nodes/de83b1/io/inputs?limit=2

    Description:

        returns the list of the first two input nodes (``limit=2``) of the *Node* object with ``uuid="de83b1..."``.

    Response::

        {
          "data": {
            "inputs": [
              {
                "attributes": {...},
                "ctime": "Fri, 24 Jul 2018 18:49:23 GMT",
                "extras": {},
                "id": 10605,
                "label": "",
                "mtime": "Mon, 25 Jan 2019 14:35:00 GMT",
                "node_type": "data.remote.RemoteData.",
                "user_email": "aiida@theossrv5.epfl.ch",
                "user_id": 6,
                "uuid": "16b93b23-8629-4d83-9259-de2a947b43ed"
              },
              {
                "attributes": {...},
                "ctime": "Fri, 24 Jul 2018 14:33:04 GMT",
                "extras": {},
                "id": 9215,
                "label": "",
                "mtime": "Mon, 25 Jan 2019 14:35:00 GMT",
                "node_type": "data.array.kpoints.KpointsData.",
                "user_email": "aiida@theossrv5.epfl.ch",
                "user_id": 6,
                "uuid": "1b4d22ec-9f29-4e0d-9d68-84ddd18ad8e7"
              }
            ]
          },
          "method": "GET",
          "path": "/api/v3/nodes/de83b1/io/inputs",
          "query_string": "limit=2",
          "resource_type": "nodes",
          "url": "http://localhost:5000/api/v3/nodes/de83b1/io/inputs?limit=2",
          "url_root": "http://localhost:5000/"
        }


4. Filter the inputs/outputs of a node by their node type.

    REST URL::

        http://localhost:5000/api/v3/nodes/de83b1/io/inputs?node_type="data.array.kpoints.KpointsData."

    Description:

        returns the list of the `*KpointsData* input nodes of
        the *Node* object with ``uuid="de83b1..."``.

    Response::

        {
          "data": {
            "inputs": [
              {
                "attributes": {...},
                "ctime": "Fri, 24 Jul 2018 14:33:04 GMT",
                "extras": {},
                "id": 9215,
                "label": "",
                "mtime": "Mon, 25 Jan 2019 14:35:00 GMT",
                "node_type": "data.array.kpoints.KpointsData.",
                "user_email": "aiida@theossrv5.epfl.ch",
                "user_id": 6,
                "uuid": "1b4d22ec-9f29-4e0d-9d68-84ddd18ad8e7"
              }
            ]
          },
          "method": "GET",
          "path": "/api/v3/nodes/de83b1/io/inputs",
          "query_string": "node_type=\"data.array.kpoints.KpointsData.\"",
          "resource_type": "nodes",
          "url": "http://localhost:5000/api/v3/nodes/de83b1/io/inputs?node_type=\"data.array.kpoints.KpointsData.\"",
          "url_root": "http://localhost:5000/"
        }

    REST URL::

        http://localhost:5000/api/v3/nodes/de83b1/io/outputs?node_type="data.remote.RemoteData."

    Description:

        returns the list of the *RemoteData* output nodes of the *Node* object with ``uuid="de83b1..."``.

    Response::

        {
          "data": {
            "outputs": [
              {
                "attributes": {...},
                "ctime": "Fri, 24 Jul 2018 20:35:02 GMT",
                "extras": {},
                "id": 2811,
                "label": "",
                "mtime": "Mon, 25 Jan 2019 14:34:59 GMT",
                "node_type": "data.remote.RemoteData.",
                "user_email": "aiida@theossrv5.epfl.ch",
                "user_id": 6,
                "uuid": "bd48e333-da8a-4b6f-8e1e-6aaa316852eb"
              }
            ]
          },
          "method": "GET",
          "path": "/api/v3/nodes/de83b1/io/outputs",
          "query_string": "node_type=\"data.remote.RemoteData.\"",
          "resource_type": "nodes",
          "url": "http://localhost:5000/api/v3/nodes/de83b1/io/outputs?node_type=\"data.remote.RemoteData.\"",
          "url_root": "http://localhost:5000/"
        }



5. Getting the list of the attributes/extras of a specific node

    REST URL::

        http://localhost:5000/api/v3/nodes/ffe11/content/attributes

    Description:

        returns the list of all attributes of the *Node* object with ``uuid="ffe11..."``.

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
          "method": "GET",
          "path": "/api/v3/nodes/ffe11/content/attributes",
          "query_string": "",
          "resource_type": "nodes",
          "url": "http://localhost:5000/api/v3/nodes/ffe11/content/attributes",
          "url_root": "http://localhost:5000/"
        }



    REST URL::

        http://localhost:5000/api/v3/nodes/ffe11/content/extras

    Description:

        returns the list of all the extras of the *Node* object with ``uuid="ffe11..."``.

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
          "method": "GET",
          "path": "/api/v3/nodes/ffe11/content/extras",
          "query_string": "",
          "resource_type": "nodes",
          "url": "http://localhost:5000/api/v3/nodes/ffe11/content/extras",
          "url_root": "http://localhost:5000/"
        }


6. Getting a user-defined list of attributes/extras of a specific node

    REST URL::

         http://localhost:5000/api/v3/codes/ffe11/content/attributes?alist=append_text,is_local

    Description:

        returns a list of the attributes ``append_text`` and ``is_local`` of the *Node* object with ``uuid="ffe11..."``.

    Response::

        {
          "data": {
            "attributes": {
              "append_text": "",
              "is_local": false
            }
          },
          "method": "GET",
          "path": "/api/v3/codes/ffe11/content/attributes",
          "query_string": "alist=append_text,is_local",
          "resource_type": "codes",
          "url": "http://localhost:5000/api/v3/codes/ffe11/content/attributes?alist=append_text,is_local",
          "url_root": "http://localhost:5000/"
        }



    REST URL::

        http://localhost:5000/api/v3/codes/ffe11/content/extras?elist=trialBool,trialInt

    Description:

        returns a list of the extras ``trialBool`` and ``trialInt`` of the *Node* object with ``uuid="ffe11..."``.

    Response::

        {
          "data": {
            "extras": {
              "trialBool": true,
              "trialInt": 34
            }
          },
          "method": "GET",
          "path": "/api/v3/codes/ffe11/content/extras",
          "query_string": "elist=trialBool,trialInt",
          "resource_type": "codes",
          "url": "http://localhost:5000/api/v3/codes/ffe11/content/extras?elist=trialBool,trialInt",
          "url_root": "http://localhost:5000/"
        }

7. Getting all the attributes/extras of a specific node except a user-defined list


    REST URL::

        http://localhost:5000/api/v3/codes/ffe11/content/attributes?nalist=append_text,is_local

    Description:

        returns all the attributes of the *Node* object with ``uuid="ffe11..."`` except ``append_text`` and ``is_local``.

    Response::

        {
          "data": {
            "attributes": {
              "input_plugin": "quantumespresso.pw",
              "prepend_text": "",
              "remote_exec_path": "/project/espresso-5.1-intel/bin/pw.x"
            }
          },
          "method": "GET",
          "path": "/api/v3/codes/ffe11/content/attributes",
          "query_string": "nalist=append_text,is_local",
          "resource_type": "codes",
          "url": "http://localhost:5000/api/v3/codes/ffe11/content/attributes?nalist=append_text,is_local",
          "url_root": "http://localhost:5000/"
        }


    REST URL::

        http://localhost:5000/api/v3/codes/ffe11/content/extras?nelist=trialBool,trialInt

    Description:

        returns all the extras of the *Node* object with ``uuid="ffe11..."`` except ``trialBool`` and ``trialInt``.

    Response::

        {
          "data": {
            "extras": {
              "trialFloat": 3.0,
              "trialStr": "trial"
            }
          },
          "method": "GET",
          "path": "/api/v3/codes/ffe11/content/extras",
          "query_string": "nelist=trialBool,trialInt",
          "resource_type": "codes",
          "url": "http://localhost:5000/api/v3/codes/ffe11/content/extras?nelist=trialBool,trialInt",
          "url_root": "http://localhost:5000/"
        }


.. note:: The same REST URLs supported for the resource ``nodes`` are also available with the derived resources, namely,
    ``calculations`` and ``data``, just changing the resource field in the path.


Users
-----

1. Getting a list of the users

    REST URL::

        http://localhost:5000/api/v3/users/

    Description:

        returns a list of all the *User* objects.

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
          "method": "GET",
          "path": "/api/v3/users/",
          "query_string": "",
          "resource_type": "users",
          "url": "http://localhost:5000/api/v3/users/",
          "url_root": "http://localhost:5000/"
        }

2. Getting a list of users whose first name starts with a given string

    REST URL::

        http://localhost:5000/api/v3/users/?first_name=ilike="aii%"

    Description:

        returns a lists of the *User* objects whose first name starts with ``"aii"``, regardless the case of the characters.

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
          "method": "GET",
          "path": "/api/v3/users/",
          "query_string": "first_name=ilike=%22aii%%22",
          "resource_type": "users",
          "url": "http://localhost:5000/api/v3/users/?first_name=ilike=\"aii%\"",
          "url_root": "http://localhost:5000/"
        }

Groups
------


1. Getting a list of groups

    REST URL::

        http://localhost:5000/api/v3/groups/?limit=10&orderby=-user_id

    Description:

        returns the list of ten *Group* objects (``limit=10``) starting from the 1st
        row of the database table (``offset=0``) and the list will be ordered
        by ``user_id`` in descending order.

    Response::

        {
          "data": {
            "groups": [
              {
                "description": "",
                "id": 104,
                "label": "SSSP_new_phonons_0p002",
                "type_string": "",
                "user_email": "aiida@theossrv5.epfl.ch",
                "user_id": 2,
                "uuid": "7c0e0744-8549-4eea-b1b8-e7207c18de32"
              },
              {
                "description": "",
                "id": 102,
                "label": "SSSP_cubic_old_phonons_0p025",
                "type_string": "",
                "user_email": "aiida@localhost",
                "user_id": 1,
                "uuid": "c4e22134-495d-4779-9259-6192fcaec510"
              },
              ...

            ]
          },
          "method": "GET",
          "path": "/api/v3/groups/",
          "query_string": "limit=10&orderby=-user_id",
          "resource_type": "groups",
          "url": "http://localhost:5000/api/v3/groups/?limit=10&orderby=-user_id",
          "url_root": "http://localhost:5000/"
        }

2. Getting the details of a specific group

    REST URL::

        http://localhost:5000/api/v3/groups/a6e5b

    Description:

        returns the details of the *Group* object with ``uuid="a6e5b..."``.

    Response::

        {
          "data": {
            "groups": [
              {
                "description": "GBRV US pseudos, version 1.2",
                "id": 23,
                "label": "GBRV_1.2",
                "type_string": "data.upf.family",
                "user_email": "aiida@theossrv5.epfl.ch",
                "user_id": 2,
                "uuid": "a6e5b6c6-9d47-445b-bfea-024cf8333c55"
              }
            ]
          },
          "method": "GET",
          "path": "/api/v3/groups/a6e5b",
          "query_string": "",
          "resource_type": "groups",
          "url": "http://localhost:5000/api/v3/groups/a6e5b",
          "url_root": "http://localhost:5000/"
        }
