.. _rest_api:

==============
AiiDA REST API
==============

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

        http://localhost:5000/api/v4

where the last field identifies the version of the API (currently ``v4``).
Simply type this URL in your browser or use command-line tools such as ``curl`` or ``wget``.

.. note:: Note that the ``v3`` version of the API was used for versions of AiiDA previous to 1.0.0b6.

For the full list of configuration options, see the file ``aiida/restapi/common/config.py``.


General form of the URLs
++++++++++++++++++++++++

A generic URL to send requests to the REST API is formed by:

    1. The base URL. It specifies the host and the version of the API. Example::

        http://localhost:5000/api/v4

    2. The path. It defines the kind of resource requested by the client and the type of query. Example::

        ../nodes/..

    3. The query string (not mandatory). It can be used for any further specification of the request, e.g. to introduce
       query filters, to give instructions for ordering, to set how results have to be paginated, etc. Example::

        ?id=200

The query string is introduced by the question mark character ``?``. Here are some examples::

  http://localhost:5000/api/v4/users/
  http://localhost:5000/api/v4/computers?scheduler_type="slurm"
  http://localhost:5000/api/v4/nodes/?id>45&node_type=like="data%"

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

    http://localhost:5000/api/v4/computers/page/1?
    http://localhost:5000/api/v4/computers/page/1?perpage=5
    http://localhost:5000/api/v4/computers/page

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

    http://localhost:5000/api/v4/computers/?limit=3&offset=2


How to build the path
---------------------

The first element of the path is the *Resource* corresponding to the
AiiDA object(s) you want to request. The following resources are available:

+------------------------------------------------------------------------------------+----------------------+
| Class                                                                              | Resource             |
+====================================================================================+======================+
| :py:class:`Computer <aiida.orm.Computer>`                                          | ``/computers``       |
+------------------------------------------------------------------------------------+----------------------+
| :py:class:`Group <aiida.orm.groups.Group>`                                         | ``/groups``          |
+------------------------------------------------------------------------------------+----------------------+
| :py:class:`User <aiida.orm.User>`                                                  | ``/users``           |
+------------------------------------------------------------------------------------+----------------------+
| :py:class:`Node <aiida.orm.nodes.Node>`                                            | ``/nodes``           |
+------------------------------------------------------------------------------------+----------------------+
| :py:class:`ProcessNode <aiida.orm.nodes.process.ProcessNode>`                      | ``/processes``       |
+------------------------------------------------------------------------------------+----------------------+
| :py:class:`CalcJobNode <aiida.orm.nodes.process.calculation.calcjob.CalcJobNode>`  | ``/calcjobs``        |
+------------------------------------------------------------------------------------+----------------------+

For a **full list** of available endpoints for each resource, simply query the base URL of the REST API (e.g. ``http://localhost:5000``).

There are two types of paths: you may either request a list of objects
or one specific object of a resource.

If no specific endpoint is appended to the name of the resource, the API
returns the full list of objects of that resource (default limits apply).

Appending the endpoint ``projectable_properties`` to a
resources like nodes, processes, users, groups and computers will give the list of projectable fields
that are normally returned by the API for
an object of a specific resource, whereas the endpoint ``statistics`` returns a
list of statistical facts concerning a resource.
Here are few examples of valid URIs::

    http://localhost:5000/api/v4/nodes/statistics
    http://localhost:5000/api/v4/users/
    http://localhost:5000/api/v4/groups/projectable_properties


If you request informations of a specific object, in general you have to append its entire *uuid* or the starting pattern of its *uuid* to the path.
 Here are two examples that should return the same object::

    http://localhost:5000/api/v4/nodes/338357f4-f236-4f9c-8fbe-cd550dc6b858
    http://localhost:5000/api/v4/nodes/338357f4

In the first URL, we have specified the full *uuid*, whereas in the second only a chunk of its first characters that is
sufficiently long to match only one *uuid* in the database.

.. note:: Using *id* in place of *uuid* is not allowed anylonger, e.g.  ``http://localhost:5000/api/v4/nodes/201`` does not work.
    Use ``http://localhost:5000/api/v4/nodes?id=201`` instead.

If the *uuid* pattern is not long enough to identify a unique object, the API will raise an exception.
The only exception to this rule is the resource *users* since the corresponding AiiDA``User`` class has no *uuid*
attribute. In this case, you have to specify the *id* (integer) of the object. Here is an example::

    http://localhost:5000/api/v4/users?id=2

When you ask for a single object (and only in that case) you can construct more complex requests, namely, you can ask
for its incoming/outgoing or for its attributes/extras.
In the first case you have to append to the path the string ``/links/incoming`` or ``/links/outgoing`` depending on the desired
relation between the nodes, whereas in the second case you have to append ``contents/attributes`` or ``contents/extras``
depending on the kind of content you want to access. Here are some examples::

    http://localhost:5000/api/v4/nodes/338357f4/links/incoming
    http://localhost:5000/api/v4/nodes/338357f4/links/outgoing
    http://localhost:5000/api/v4/nodes/338357f4/contents/attributes
    http://localhost:5000/api/v4/nodes/338357f4/contents/extras

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

            http://localhost:5000/api/v4/computers?orderby=+id
            http://localhost:5000/api/v4/computers?orderby=+name
            http://localhost:5000/api/v4/computers?orderby=-uuid


    :attributes_filter: This key is used to specify which attributes of a specific object have to be returned.
        The desired attributes have to be provided as a comma-separated list of values.
        It is used in the endpoints ``/contents/attributes`` and ``/nodes``. Example:

        ::

            http://localhost:5000/api/v4/nodes/4fb10ef1/contents/attributes?attributes_filter=append_text,prepend_text


    :extras_filter: Similar to ``attributes_filter`` but for extras. It is used in the endpoints ``/contents/extras``
        and ``/nodes``.

    :attributes: by default ``attributes`` are not returned in ``/nodes`` endpoint. To get the
        list of all ``attributes`` specify ``attributes=true`` and to get selected ``attribute(s)`` list, use
        ``attributes=true&attributes_filters=<comma separated list of attributes you want to request>``.

    :extras: by default ``extras`` are not returned in ``/nodes`` endpoint. To get the list of all
        ``extras`` specify ``extras=true`` and to get selected ``extras`` list, use
        ``extras=true&extras_filters=<comma separated list of extras you want to request>``.

    :download_format: to specify download format in ``/download`` endpoint.

    :download: in ``/download`` endpoint, if ``download=false`` it displays the content in the browser instead of downloading a file.

    :filename: this filter is used to pass file name in ``/repo/list`` and ``/repo/contents`` endpoint.

    :tree_in_limit: specifies the limit on tree incoming nodes.

    :tree_out_limit: specifies the limit on tree outgoing nodes.

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

            http://localhost:5000/api/v4/nodes?ctime>2019-04-23T05:45+03:45
            http://localhost:5000/api/v4/nodes?ctime<2019-04-23T05:45
            http://localhost:5000/api/v4/nodes?mtime>=2019-04-23


    :bool: It can be either true or false (lower case).

The following table reports what is the value type and the supported resources associated to each key.

.. note:: In the following *id* is a synonym for *pk* (often used in other sections of the documentation).


+--------------+----------+---------------------------------------------------+
|key           |value type|resources                                          |
+==============+==========+===================================================+
|id            |integer   |users, computers, groups, nodes                    |
+--------------+----------+---------------------------------------------------+
|user_id       |integer   |groups                                             |
+--------------+----------+---------------------------------------------------+
|uuid          |string    |computers, groups, nodes                           |
+--------------+----------+---------------------------------------------------+
|name          |string    |computers                                          |
+--------------+----------+---------------------------------------------------+
|first_name    |string    |users                                              |
+--------------+----------+---------------------------------------------------+
|last_name     |string    |users                                              |
+--------------+----------+---------------------------------------------------+
|institution   |string    |users                                              |
+--------------+----------+---------------------------------------------------+
|label         |string    |groups, nodes,                                     |
+--------------+----------+---------------------------------------------------+
|description   |string    |computers, groups                                  |
+--------------+----------+---------------------------------------------------+
|transport_type|string    |computers                                          |
+--------------+----------+---------------------------------------------------+
|scheduler_type|string    |computers                                          |
+--------------+----------+---------------------------------------------------+
|attributes    |string    |nodes                                              |
+--------------+----------+---------------------------------------------------+
|ctime         |datetime  |nodes                                              |
+--------------+----------+---------------------------------------------------+
|mtime         |datetime  |nodes                                              |
+--------------+----------+---------------------------------------------------+
|node_type     |string    |nodes                                              |
+--------------+----------+---------------------------------------------------+
|full_type     |string    |nodes                                              |
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

    http://localhost:5000/api/v4/nodes?id=in=45,56,78
    http://localhost:5000/api/v4/computers/?scheduler_type=in="slurm","pbs"

The relational operators '<', '>', '<=', '>=' assume natural ordering for integers, (case-insensitive) alphabetical
ordering for strings, and chronological ordering for datetime values.

Examples:

    - ``http://localhost:5000/api/v4/nodes?id>578`` selects the nodes having an id larger than 578.
    - ``http://localhost:5000/api/v4/users/?last_name<="m"`` selects only the users whose last name begins with a
      character in the range [a-m].


.. note:: Node types have to be specified by a string that defines their position in the AiiDA source tree ending
    with a dot. Examples:

    - ``node_type="data.code.Code."`` selects only objects of *Code* type
    - ``node_type="data.remote.RemoteData."`` selects only objects of *RemoteData* type

.. note:: If you use in your request the endpoint *links/incoming* (*links/outgoing*) together with one or more filters, the
    latter are applied to the incoming (outgoing) nodes of the selected *id*. For example, the request:

        ::

            http://localhost:5000/api/v4/nodes/a67fba41/links/outgoing?full_type="data.dict.Dict.|"

    would first search for the outgoing of the node with *uuid* starting with "a67fba41" and then select only those
    nodes of full_type *data.dict.Dict.|*.



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

    curl http://localhost/django/api/v4/computers -X GET
    curl http://localhost/sqlalchemy/api/v4/computers -X GET

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

        http://localhost:5000/api/v4/computers?limit=3&offset=2&orderby=id

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
          "id": null,
          "method": "GET",
          "path": "/api/v4/computers",
          "query_string": "limit=3&offset=2&orderby=id",
          "resource_type": "computers",
          "url": "http://localhost:5000/api/v4/computers?limit=3&offset=2&orderby=id",
          "url_root": "http://localhost:5000/"
        }



2. Get details of a single *Computer* object:

    REST URL::

        http://localhost:5000/api/v4/computers/5d490d77

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
          "id": null,
          "method": "GET",
          "path": "/api/v4/computers/5d490d77",
          "query_string": "",
          "resource_type": "computers",
          "url": "http://localhost:5000/api/v4/computers/5d490d77",
          "url_root": "http://localhost:5000/"
        }


Nodes
-----

1.  Get a list of *Node* objects.

    REST URL::

        http://localhost:5000/api/v4/nodes?limit=2&offset=8&orderby=-id

    Description:

        returns the list of two *Node* objects (``limit=2``) starting from 9th
        row (``offset=8``) of the database table and the list will be ordered
        by ``id`` in descending order.

    Response::

        {
          "data": {
            "nodes  ": [
              {
                "ctime": "Sun, 21 Jul 2019 11:45:52 GMT",
                "full_type": "data.dict.Dict.|",
                "id": 102618,
                "label": "",
                "mtime": "Sun, 21 Jul 2019 11:45:52 GMT",
                "node_type": "data.dict.Dict.",
                "process_type": null,
                "user_id": 4,
                "uuid": "a43596fe-3d95-4d9b-b34a-acabc21d7a1e"
              },
              {
                "ctime": "Sun, 21 Jul 2019 18:18:26 GMT",
                "full_type": "data.remote.RemoteData.|",
                "id": 102617,
                "label": "",
                "mtime": "Sun, 21 Jul 2019 18:18:26 GMT",
                "node_type": "data.remote.RemoteData.",
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

    Get list of all nodes with attribute called ``pbc1``:

    REST URL::

        http://localhost:5000/api/v4/nodes?attributes=true&attributes_filter=pbc1

    Description:

        returns the list of *Node* objects. Every node object contains value of attribute called ``pbc1`` if present otherwise null.

    Response::

        {
          "data": {
            "nodes  ": [
              {
                "attributes.pbc1": true,
                "ctime": "Sun, 21 Jul 2019 15:36:30 GMT",
                "full_type": "data.structure.StructureData.|",
                "id": 51310,
                "label": "",
                "mtime": "Sun, 21 Jul 2019 15:36:30 GMT",
                "node_type": "data.structure.StructureData.",
                "process_type": null,
                "user_id": 4,
                "uuid": "98de8d6d-f533-4f97-a8ad-7720cc5ca8f6"
              },
              {
                "attributes.pbc1": null,
                "ctime": "Sun, 21 Jul 2019 15:44:14 GMT",
                "full_type": "data.dict.Dict.|",
                "id": 51311,
                "label": "",
                "mtime": "Sun, 21 Jul 2019 15:44:14 GMT",
                "node_type": "data.dict.Dict.",
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

2. Get a list of all available node types from database.

    REST URL::

        http://localhost:5000/api/v4/nodes/full_types

    Description:

        returns the list of full_types from database.

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

3. Get a list of all available download formats.

    REST URL::

        http://localhost:5000/api/v4/nodes/download_formats

    Description:

        returns the list of available download formats.

    Response::

        {
            "data": {
                "data.array.bands.BandsData.|": [
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
                "data.array.trajectory.TrajectoryData.|": [
                    "cif",
                    "xsf"
                ],
                "data.cif.CifData.|": [
                    "cif"
                ],
                "data.structure.StructureData.|": [
                    "chemdoodle",
                    "cif",
                    "xsf",
                    "xyz"
                ],
                "data.upf.UpfData.|": [
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

4. Get the details of a single *Node* object.

    REST URL::

        http://localhost:5000/api/v4/nodes/12f95e1c

    Description:

        returns the details of the *Node* object with ``uuid="12f95e1c..."``.

    Response::

        {
          "data": {
            "nodes  ": [
              {
                "ctime": "Sun, 21 Jul 2019 18:18:26 GMT",
                "full_type": "data.remote.RemoteData.|",
                "id": 102617,
                "label": "",
                "mtime": "Sun, 21 Jul 2019 18:18:26 GMT",
                "node_type": "data.remote.RemoteData.",
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

5. Get the list of incoming of a specific node.

    REST URL::

        http://localhost:5000/api/v4/nodes/de83b1/links/incoming?limit=2

    Description:

        returns the list of the first two input nodes (``limit=2``) of the *Node* object with ``uuid="de83b1..."``.

    Response::

        {
          "data": {
            "incoming": [
              {
                "ctime": "Sun, 21 Jul 2019 08:02:23 GMT",
                "full_type": "data.dict.Dict.|",
                "id": 53770,
                "label": "",
                "link_label": "settings",
                "link_type": "input_calc",
                "mtime": "Sun, 21 Jul 2019 08:02:23 GMT",
                "node_type": "data.dict.Dict.",
                "process_type": null,
                "user_id": 4,
                "uuid": "31993382-c1ab-4822-a116-bd88697f2796"
              },
              {
                "ctime": "Fri, 28 Jun 2019 10:54:25 GMT",
                "full_type": "data.upf.UpfData.|",
                "id": 54502,
                "label": "",
                "link_label": "pseudos__N",
                "link_type": "input_calc",
                "mtime": "Fri, 28 Jun 2019 10:54:28 GMT",
                "node_type": "data.upf.UpfData.",
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


6. Filter the incoming/outgoing of a node by their full type.

    REST URL::

        http://localhost:5000/api/v4/nodes/de83b1/links/incoming?full_type="data.dict.Dict.|"

    Description:

        returns the list of the `*dict* incoming nodes of
        the *Node* object with ``uuid="de83b1..."``.

    Response::

        {
          "data": {
            "incoming": [
              {
                "ctime": "Sun, 21 Jul 2019 08:02:23 GMT",
                "full_type": "data.dict.Dict.|",
                "id": 53770,
                "label": "",
                "link_label": "settings",
                "link_type": "input_calc",
                "mtime": "Sun, 21 Jul 2019 08:02:23 GMT",
                "node_type": "data.dict.Dict.",
                "process_type": null,
                "user_id": 4,
                "uuid": "31993382-c1ab-4822-a116-bd88697f2796"
              }
            ]
          },
          "id": "de83b1",
          "method": "GET",
          "path": "/api/v4/nodes/de83b1/links/incoming",
          "query_string": "full_type=%22data.dict.Dict.|%22",
          "resource_type": "nodes",
          "url": "http://localhost:5000/api/v4/nodes/de83b1/links/incoming?full_type=\"data.dict.Dict.|\"",
          "url_root": "http://localhost:5000/"
        }

    REST URL::

        http://localhost:5000/api/v4/nodes/de83b1/links/outgoing?full_type="data.dict.Dict.|"

    Description:

        returns the list of the *dict* outgoing nodes of the *Node* object with ``uuid="de83b1..."``.

    Response::

        {
          "data": {
            "outgoing": [
              {
                "ctime": "Sun, 21 Jul 2019 09:08:05 GMT",
                "full_type": "data.dict.Dict.|",
                "id": 67440,
                "label": "",
                "link_label": "output_parameters",
                "link_type": "create",
                "mtime": "Sun, 21 Jul 2019 09:08:05 GMT",
                "node_type": "data.dict.Dict.",
                "process_type": null,
                "user_id": 4,
                "uuid": "861e1108-33a1-4495-807b-8c5189ad74e3"
              }
            ]
          },
          "id": "de83b1",
          "method": "GET",
          "path": "/api/v4/nodes/de83b1/links/outgoing",
          "query_string": "full_type=%22data.dict.Dict.|%22",
          "resource_type": "nodes",
          "url": "http://localhost:5000/api/v4/nodes/de83b1/links/outgoing?full_type=\"data.dict.Dict.|\"",
          "url_root": "http://localhost:5000/"
        }



7. Getting the list of the attributes/extras of a specific node.

    REST URL::

        http://localhost:5000/api/v4/nodes/ffe11/contents/attributes

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
          "id": "ffe11",
          "method": "GET",
          "path": "/api/v4/nodes/ffe11/contents/extras",
          "query_string": "",
          "resource_type": "nodes",
          "url": "http://localhost:5000/api/v4/nodes/ffe11/contents/extras",
          "url_root": "http://localhost:5000/"
        }


8. Getting a user-defined list of attributes/extras of a specific node.

    REST URL::

         http://localhost:5000/api/v4/nodes/ffe11/contents/attributes?attributes_filter=append_text,is_local

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

        returns a list of the extras ``trialBool`` and ``trialInt`` of the *Node* object with ``uuid="ffe11..."``.

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

9. Get comments of specific node.

    REST URL::

        http://localhost:5000/api/v4/nodes/ffe11/contents/comments

    Description:

        returns comments of the given node

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

10. Get list of all the files/directories from node repository

    REST URL::

        http://localhost:5000/api/v4/nodes/ffe11/repo/list

    Description:

        returns list of all the files/directories from node repository

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

11. Download a file from node repository

    REST URL::

        http://localhost:5000/api/v4/nodes/ffe11/repo/contents?filename="aiida.in"

    Description:

        downloads the file ``aiida.in`` from node repository

    Response::

        It downloads the file.


12. There are specific download formats (check ``nodes/download_formats`` endpoint) available to download different
    types of nodes. This endpoint is used to download file in given format.

    REST URL::

        http://localhost:5000/api/v4/nodes/fafdsf/download?download_format=xsf

    Description:

        downloads structure node of uuid=fafdsf in ``xsf`` format

    Response::

        It downloads the file.

Processes
---------

1.  Get a process report.

    REST URL::

        http://localhost:5000/api/v4/processes/8b95cd85/report

    Description:

        returns report of process of ``uuid="8b95cd85-...."``

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

1.  Get a list of input or output files of given calcjob node.

    REST URL::

        http://localhost:5000/api/v4/calcjobs/sffs241j/input_files

    Description:

        returns list of all input files of given calcjob node of ``uuid="sffs241j-...."``

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


Users
-----

1. Getting a list of the users

    REST URL::

        http://localhost:5000/api/v4/users/

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
          "id": null,
          "method": "GET",
          "path": "/api/v4/users/",
          "query_string": "",
          "resource_type": "users",
          "url": "http://localhost:5000/api/v4/users/",
          "url_root": "http://localhost:5000/"
        }

2. Getting a list of users whose first name starts with a given string

    REST URL::

        http://localhost:5000/api/v4/users/?first_name=ilike="aii%"

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


1. Getting a list of groups

    REST URL::

        http://localhost:5000/api/v4/groups/?limit=10&orderby=-user_id

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
          "id": "a6e5b,
          "method": "GET",
          "path": "/api/v4/groups/a6e5b",
          "query_string": "",
          "resource_type": "groups",
          "url": "http://localhost:5000/api/v4/groups/a6e5b",
          "url_root": "http://localhost:5000/"
        }
