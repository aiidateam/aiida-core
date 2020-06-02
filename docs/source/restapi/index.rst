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
