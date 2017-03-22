===================
REST API for AiiDA
===================

AiiDA provides a REST API to access the information of the AiiDA objects stored
in the database. There are four types of AiiDA objects: *Computer*, *Node*, *User*,
and *Group*. The *Node* type has three subtypes: *Calculation*, *Data*,
and *Code*. Different REST urls are provided to get the list of objects, 
the details of a specific object as well as its inputs/outputs/attributes/extras.

The AiiDA REST API is implemented using ``Flask RESTFul`` framework.  For the time being, it only supports GET methods. The response data are always returned in ``JSON`` format.

In this document, the paths of the file systems are defined with respect to the AiiDA installation folder. The source files of the API are contained in the folder ``aiida/restapi``. To start the REST server open a terminal and type

.. code-block:: bash

    $ verdi restapi

This command will hook up a REST api with the default parameters, namely on port *5000*
of *localhost*, connecting to the AiiDA default profile and assuming the default folder for the REST configuration files, namely ``common``. For an overview of options accepted by ``verdi restapi`` you can type

.. code-block:: bash

    $ verdi restapi --help


As all the ``verdi`` commands the AiiDA profile can be changed by putting the option ``-p PROFILE`` right after ``verdi``. The base url for your REST API will then be:

    ::

        http://localhost:5000/api/v2

where the last field identifies the version of the API. This field enables running  multiple versions of the API simultaneously, so that the clients should not be obliged to update immediately the format of their requests when a new version of the API is deployed. The current latest version is ``v2``.


An alternative way to hook up the Api is to run the script ``run_api.py`` from folder ``aiida/restapi``. Move to the latter and type

.. code-block:: bash

    $ python run_api.py

This script has the same options as the ``verdi command`` (they actually invoke the same function) with the addition of ``--aiida-profile=AIIDA_PROFILE`` to set the AiiDA profile to which the Api should connect.

The default configuration file is  ``config.py`` `and by default is looked for in the folder `aiida/restapi``. The default folder can be overwritten by the the option ``--config-dir=CONFIG_DIR`` . All the available configuration options of the REST Api are documented therein.

In order to send requests to the REST API you can simply type the url of the request in the address bar of your browser or you can use command line tools such as ``curl`` or ``wget``.

Let us now introduce the urls supported by the API. 

General form of the urls
++++++++++++++++++++++++

A generic url to send requests to the REST API is formed by:
 
    1. the base url. It specifies the host and the version of the API. Example::
    
        http://localhost:5000/api/v2
        
    2. the path. It defines the kind of resource requested by the client and the type of query.
    3. the query string (not mandatory). It can be used for any further specification of the request, e.g. to introduce query filters, to give instructions for ordering, to set how results have to be paginated, etc.   

The query string is introduced by the question mark character ``?``. Here are some examples::
 
  http://localhost:5000/api/v2/users/
  http://localhost:5000/api/v2/computers?scheduler_type="slurm"
  http://localhost:5000/api/v2/nodes/?id>45&type=like="%data%"

The trailing slash at the end of the path is not mandatory.

How to set the number of results
--------------------------------

Before exploring in details the functionalities of the API it is important to know that the AiiDA RESTAPI provides two different ways to limit the number of results returned by the server: using pagination, or specifying explicitly *limit* and *offset*.

Pagination
**********

The complete set of results is divided in *pages* containing by default 20 results each. Individual pages are accessed by appending ``/page/(PAGE)`` to the end of the path, where ``(PAGE)`` has to be replaced by the number of the required page. The number of results contained in each page can be altered by specifying the ``perpage=(PERPAGE)`` field in the query string. However, ``(PERPAGE)`` values larger than 400 are not allowed. Examples::

    http://localhost:5000/api/v2/computers/page/1?
    http://localhost:5000/api/v2/computers/page/1?perpage=5
    http://localhost:5000/api/v2/computers/page

If no page number is specified, as in the last example, the system redirects the request to page 1. When pagination is used the header of the response contains two more non-empty fields:
    
    - ``X-Total-Counts`` (custom field): the total number of results returned by the query, i.e.the sum of the results of all pages)
    - ``Links``: links to the first, previous, next, and last page. Suppose you send a request whose results would fill 8 pages. Then the value of the ``Links`` field would look like::
        
            <\http://localhost:5000/.../page/1?... >; rel=first,
            <\http://localhost:5000/.../page/3?...     ;>; rel=prev,
            <\http://localhost:5000/.../page/5?... >; rel=next,
            <\http://localhost:5000/.../page/8?... >; rel=last

Setting *limit* and *offset*
****************************

You can specify two special fields in the query string:

    - ``limit=(LIMIT)``: field that specifies the largest number of results that will be returned, ex: "limit=20". The default and highest allowed ``LIMIT`` is 400.
    - ``offset=(OFFSET)``: field that specifies how many entries are skipped before returning results, ex: ``offset=20``. By default no offset applies.

Example::

    http://localhost:5000/api/v2/computers/?limit=3&offset=2


How to build the path
---------------------

There are two type of paths: those that request the list of objects of a specific resource, namely, the AiiDA object type you are requesting, and those that inquire a specific object of a certain resource. In both cases the path has to start with the name of the resource. The complete list of resources is: ``users``, ``computers``, ``groups``, ``nodes``, ``codes``, ``calculations``, and ``data``. If no specific endpoint is appended to the name of the resource, the Api will return the full list of objects of that resource (the Api default limit applies nevertheless to the number of results).
Appending the endpoint ``schema`` to a resource will give the list of fields that are normally returned by the Api for an object of a specific resource, whereas the endpoint ``statistics`` returns a list of statistical facts concerning a resource.
Here are few examples of valid URIs::

    http://localhost:5000/api/v2/users/
    http://localhost:5000/api/v2/groups/schema
    http://localhost:5000/api/v2/nodes/statistics


If you request informations of a specific object you have to append its pk to the path (note that the pk is also called id). Here is an example::

    http://localhost:5000/api/v2/nodes/345

When you ask for a single object (and only in that case) you can construct more complex requests, namely, you can ask for its inputs/outputs or for its attributes/extras. In the first case you have to append to the path the string ``/io/inputs`` or ``io/outputs`` depending on the desired relation between the nodes, whereas in the second case you have to append ``content/attributes`` or ``content/extras`` depending on the kind of content you want to access. Here are some examples::

    http://localhost:5000/api/v2/calculations/345/io/inputs
    http://localhost:5000/api/v2/nodes/345/io/inputs
    http://localhost:5000/api/v2/data/385/content/attributes
    http://localhost:5000/api/v2/nodes/385/content/extras

.. note:: As you can see from the last examples, a *Node* object can be accessed requesting either a generic ``nodes`` resource or requesting the resource corresponding to its specific type (``data``, ``codes``, ``calculations``). This is because in AiiDA  the classes *Data*, *Code*, and *Calculation* are derived from the class *Node*.

How to build the query string
-----------------------------

The query string is formed by one or more fields separated by the special character ``&``.
Each field has the form (``key``)(``operator``)(``value``). The same constraints that apply to the names of python variables determine what are the valid keys, namely, only alphanumeric characters plus ``_`` are allowed and the first character cannot be a number.

Special keys 
************

There are several special keys that can be specified only once in a query string. All of them must be followed by the operator ``=``. Here is the complete list:

    :limit: This key only supports integer values.

    :offset: Same format as ``limit``.

    :perpage: Same format as ``limit``.

    :orderby: This key is used to impose a specific ordering to the results. Two orderings are supported, ascending or descending. The value for the ``orderby`` key must be the name of the property with respect to which to order the results. Additionally, ``+`` or ``-`` can be pre-pended to the value in order to select, respectively, ascending or descending order. Specifying no leading character is equivalent to select ascending order. Ascending (descending) order for strings corresponds to alphabetical (reverse-alphabetical) order, whereas for datetime objects it corresponds to chronological (reverse-chronological order). Examples:

        ::
    
            http://localhost:5000/api/v2/c=+id
            http://localhost:5000/api/v2/computers=+name
            http://localhost:5000/api/v2/computers/orderby=-uuid
        
              
    :alist: This key is used to specify which attributes of a specific object have to be returned. The desired attributes have to be provided as a comma-separated list of values. It requires that the path contains the endpoint ``/content/attributes``. Example:                                  

        ::

            http://localhost:5000/api/v2/codes/1822/content/attributes?
                                        alist=append_text,prepend_text 


    :nalist: (incompatible with ``alist``) This key is used to specify which attributes of a specific object should not be returned. The syntax is identical to ``alist``. The system returns all the attributes except those specified in the list of values.  
    
    :elist: Similar to ``alist`` but for extras. It requires that the path contains the endpoint ``/content/extras``.
    
    :nelist: (incompatible with ``elist``) Similar to ``nalist`` but for extras. It requires that the path contains the endpoint ``/content/extras``.

Filters
*******

All the other fields composing a query string are filters, that is, conditions that have to be fulfilled by the retrieved objects. When a query string contains multiple filters, those are applied as if they were related by the AND logical clause, that is, the results have to fulfill all the conditions set by the filters (and not any of them). Each filter key is associated to a unique value type. The possible types are:

    :string: Text enclosed in double quotes. If the string contains double quotes those have to be escaped as ``""`` (two double quotes). Note that in the unlikely occurrence of a sequence of double quotes you will have to escape it by writing twice as many double quotes.  

    :integer: Positive integer numbers.
    
    :datetime: Datetime objects expressed in the format ``(DATE)T(TIME)(SHIFT)`` where ``(SHIFT)`` is the time difference with respect to the UTC time. This is required to avoid any problem arising from comparing datetime values expressed in different time zones. The formats of each field are:
    
        1. ``YYYY-MM-DD`` for ``(DATE)`` (mandatory).
        2. ``HH:MM:SS`` for ``(TIME)`` (optional). The formats ``HH`` and ``HH:MM`` are supported too.  
        3. ``+/-HH:MM`` for ``(SHIFT)`` (optional, if present requires ``(TIME)`` to be specified). The format ``+/-HH`` is allowed too. If no shift is specified UTC time is assumed. The shift format follows the general convention that eastern (western) shifts are positive (negative). The API is unaware of daylight saving times so the user is required to adjust the shift to take them into account. 
        
        This format is ``ISO-8601`` compliant. Note that date and time fields have to be separated by the character ``T``. Examples:

        ::
        
            ctime>2016-04-23T05:45+03:45
            ctime<2016-04-23T05:45 
            mtime>=2016-04-23    


    :bool: It can be either true or false (lower case).

The following table reports what is the value type and the supported resources associated to each key. 

+----------------+----------+----------------------------------------------------------+
|key             |value type|resources                                                 |
+================+==========+==========================================================+
|id              |integer   |users, computers, groups, nodes, calculations, codes, data|
+----------------+----------+----------------------------------------------------------+
|user_id         |integer   |groups                                                    |
+----------------+----------+----------------------------------------------------------+
|uuid            |string    |computers, groups, nodes, calculations, codes, data       |
+----------------+----------+----------------------------------------------------------+
|name            |string    |computers, groups                                         |
+----------------+----------+----------------------------------------------------------+
|first_name      |string    |users                                                     |
+----------------+----------+----------------------------------------------------------+
|last_name       |string    |users                                                     |
+----------------+----------+----------------------------------------------------------+
|institution     |string    |users                                                     |
+----------------+----------+----------------------------------------------------------+
|email           |string    |users                                                     |
+----------------+----------+----------------------------------------------------------+
|label           |string    |nodes, calculations, codes, data                          |
+----------------+----------+----------------------------------------------------------+
|description     |string    |computers, groups                                         |
+----------------+----------+----------------------------------------------------------+
|transport_type  |string    |computers                                                 |
+----------------+----------+----------------------------------------------------------+
|transport_params|string    |computers                                                 |
+----------------+----------+----------------------------------------------------------+
|scheduler_type  |string    |computers                                                 |
+----------------+----------+----------------------------------------------------------+
|enabled         |bool      |computers                                                 |
+----------------+----------+----------------------------------------------------------+
|is_active       |bool      |users                                                     |
+----------------+----------+----------------------------------------------------------+
|ctime           |datetime  |nodes, calculations, codes, data                          |
+----------------+----------+----------------------------------------------------------+
|mtime           |datetime  |nodes, calculations, codes, data                          |
+----------------+----------+----------------------------------------------------------+
|last_login      |datetime  |users                                                     |
+----------------+----------+----------------------------------------------------------+
|date_joined     |datetime  |users                                                     |
+----------------+----------+----------------------------------------------------------+
|type            |string    |groups, nodes, calculations, codes, data                  |
+----------------+----------+----------------------------------------------------------+
|state           |string    |nodes, calculations, codes, data                          |
+----------------+----------+----------------------------------------------------------+
|hostname        |string    |computers                                                 |
+----------------+----------+----------------------------------------------------------+

The operators supported by a specific key are uniquely determined by the value type associated to that key. For example, a key that requires a boolean value admits only the identity operator ``=``, whereas an integer value enables the usage of the relational operators ``=``, ``<``, ``<=``, ``>``, ``>=`` plus the membership operator ``=in=``.  
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
|           |    element of a list   |                                 |
+-----------+------------------------+---------------------------------+

The pattern matching operators ``=like=`` and ``=ilike=`` must be followed by the pattern definition, namely, a string where two characters assume special meaning:

    1. ``%`` is used to replace an arbitrary sequence of characters, including no characters.
    2. ``_`` is used to replace one or zero characters.
    
Differently from ``=like=``, ``=ilike=`` assumes that two characters that only differ in the case are equal. 

To prevent interpreting special characters as wildcards, these have to be escaped by pre-pending the character ``\``.

Examples:

+-------------------------------+----------------------+-------------------+
| Filter                        | Matched string       | Non-matched string|
+===============================+======================+===================+
| ``name=like="a%d_"``          |       "aiida"        |      "AiiDA"      |
+-------------------------------+----------------------+-------------------+
| ``name=ilike="a%d_"``         |   "aiida", "AiiDA"   |                   |
+-------------------------------+----------------------+-------------------+
| ``name=like="a_d_"``          |                      |      "aiida"      |
+-------------------------------+----------------------+-------------------+
| ``name=like="aii%d_a"``       |        "aiida"       |                   |
+-------------------------------+----------------------+-------------------+
| ``uuid=like="cdfd48%"``       | "cdfd48f9-7ed2-4969  |                   |
|                               |  -ba06-09c752b83d2"  |                   |
+-------------------------------+----------------------+-------------------+
| ``description=like="This``    | "This calculation is |                   | 
| ``calculation is %\% useful"``|  100% useful"        |                   |
+-------------------------------+----------------------+-------------------+

The membership operator ``=in=`` has to be followed by a comma-separated list of values of the same type. The condition is fulfilled if the column value of an object is an element of the list.

Examples:: 

    http://localhost:5000/api/v2/nodes?id=in=45,56,78
    http://localhost:5000/api/v2/computers/?
    scheduler_type=in="slurm","pbs"&state="FINISHED"

The relational operators '<', '>', '<=', '>=' assume natural ordering for integers, (case-insensitive) alphabetical ordering for strings, and chronological ordering for datetime values.

Examples:

    - ``http://localhost:5000/api/v2/nodes?id>578`` selects the nodes having an id larger than 578.  
    - ``http://localhost:5000/api/v2/users/?last_login>2014-04-07`` selects only the user that logged in for the last time after April 7th, 2014. 
    - ``http://localhost:5000/api/v2/users/?last_name<="m"`` selects only the users whose last name begins with a character in the range [a-m].


.. note:: Object types have to be specified by a string that defines their position in the AiiDA source tree ending with a dot. Examples:
 
    - ``type="data.Data."`` selects only objects of *Data* type
    - ``type="data.remote.RemoteData."`` selects only objects of *RemoteData* type

.. note:: If you use in your request the endpoint *io/input* (*io/outputs*) together with one or more filters, the latter are applied to the input (output) nodes of the selected *pk*. For example, the request:

        ::

            http://localhost:5000/api/v2/nodes/6/io/outputs/?
                              type="data.folder.FolderData."

    would first search for the outputs of the node with *pk* =6 and then select only those objects of type *FolderData*.

       

The HTTP response
+++++++++++++++++

The HTTP response of the REST API consists in a JSON object, a header, and a status code. Possible status are:

    1. 200 for successful requests.
    2. 400 for bad requests. In this case, the JSON object contains only an error message describing the problem.
    3. 500 for a generic internal server error. The JSON object contains only a generic error message.
    4. 404 for invalid url. Differently from the 400 status, it is returned when the REST API does not succeed in directing the request to a specific resource. This typically happens when the path does not match any of the supported format. No JSON is returned.

The header is a standard HTTP response header with the additional custom field ``X-Total-Counts`` and, only if paginated results are required, a non-empty ``Link`` field, as described in the Pagination section.

The JSON object mainly contains the list of the results returned by the API. This list is assigned to the key ``data``. Additionally, the JSON object contains several informations about the request (keys ``method``, ``url``, ``url_root``, ``path``, ``query_string``, ``resource_type``, and ``pk``).



Examples
++++++++

Computers
---------

1. Get a list of the *Computers* objects.

    REST url:: 

        http://localhost:5000/api/v2/computers?limit=3&offset=2&orderby=id

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
                "enabled": true, 
                "hostname": "alpha.aiida.net", 
                "id": 3, 
                "name": "Alpha", 
                "scheduler_type": "slurm", 
                "transport_params": "{}", 
                "transport_type": "ssh", 
                "uuid": "9b5c84bb-4575-4fbe-b18c-b23fc30ec55e"
              }, 
              {
                "description": "Beta Computer", 
                "enabled": true, 
                "hostname": "beta.aiida.net", 
                "id": 4, 
                "name": "Beta", 
                "scheduler_type": "slurm", 
                "transport_params": "{}", 
                "transport_type": "ssh", 
                "uuid": "5d490d77-638d-4d4b-8288-722f930783c8"
              }, 
              {
                "description": "Gamma Computer", 
                "enabled": true, 
                "hostname": "gamma.aiida.net", 
                "id": 5, 
                "name": "Gamma", 
                "scheduler_type": "slurm", 
                "transport_params": "{}", 
                "transport_type": "ssh", 
                "uuid": "7a0c3ff9-1caf-405c-8e89-2369cf91b634"
              }
            ]
          }, 
          "method": "GET", 
          "path": "/api/v2/computers", 
          "pk": null, 
          "query_string": "limit=3&offset=2&orderby=id", 
          "resource_type": "computers", 
          "url": "http://localhost:5000/api/v2/computers?limit=3&offset=2&orderby=id", 
          "url_root": "http://localhost:5000/"
        }
        
   

2. Get details of a single *Computer* object:

    REST url::

        http://localhost:5000/api/v2/computers/4

    Description:

        returns the details of the *Computer* object with ``pk=4``.

    Response::

        {
          "data": {
            "computers": [
              {
                "description": "Beta Computer", 
                "enabled": true, 
                "hostname": "beta.aiida.net", 
                "id": 4, 
                "name": "Beta", 
                "scheduler_type": "slurm", 
                "transport_params": "{}", 
                "transport_type": "ssh", 
                "uuid": "5d490d77-638d-4d4b-8288-722f930783c8"
              }
            ]
          }, 
          "method": "GET", 
          "path": "/api/v2/computers/4", 
          "pk": 4, 
          "query_string": "", 
          "resource_type": "computers", 
          "url": "http://localhost:5000/api/v2/computers/4", 
          "url_root": "http://localhost:5000/"
        }
        

Nodes
-----

1.  Get a list of *Node* objects
  
    REST url::

        http://localhost:5000/api/v2/nodes?limit=2&offset=8&orderby=-id

    Description:

        returns the list of two *Node* objects (``limit=2``) starting from 9th
        row (``offset=8``) of the database table and the list will be ordered
        by ``id`` in descending order.

    Response::

        {
          "data": {
            "nodes  ": [
              {
                "ctime": "Fri, 29 Apr 2016 19:24:12 GMT", 
                "id": 386913, 
                "label": "", 
                "mtime": "Fri, 29 Apr 2016 19:24:13 GMT", 
                "state": null, 
                "type": "calculation.inline.InlineCalculation.", 
                "uuid": "68d2ed6c-6f51-4546-8d10-7fe063525ab8"
              }, 
              {
                "ctime": "Fri, 29 Apr 2016 19:24:00 GMT", 
                "id": 386912, 
                "label": "", 
                "mtime": "Fri, 29 Apr 2016 19:24:00 GMT", 
                "state": null, 
                "type": "data.parameter.ParameterData.", 
                "uuid": "a39dc158-fedd-4ea1-888d-d90ec6f86f35"
              }
            ]
          }, 
          "method": "GET", 
          "path": "/api/v2/nodes", 
          "pk": null, 
          "query_string": "limit=2&offset=8&orderby=-id", 
          "resource_type": "nodes", 
          "url": "http://localhost:5000/api/v2/nodes?limit=2&offset=8&orderby=-id", 
          "url_root": "http://localhost:5000/"
        }
           
2. Get the details of a single *Node* object:

    REST url::

        http://localhost:5000/api/v2/nodes/1

    Description:

        returns the details of the *Node* object with ``pk=1``.

    Response::

        {
          "data": {
            "nodes  ": [
              {
                "ctime": "Fri, 14 Aug 2015 13:18:04 GMT", 
                "id": 1, 
                "label": "", 
                "mtime": "Mon, 25 Jan 2016 14:34:59 GMT", 
                "state": "IMPORTED", 
                "type": "data.parameter.ParameterData.", 
                "uuid": "e30da7cc-af50-40ca-a940-2ac8d89b2e0d"
              }
            ]
          }, 
          "method": "GET", 
          "path": "/api/v2/nodes/1", 
          "pk": 1, 
          "query_string": "", 
          "resource_type": "nodes", 
          "url": "http://localhost:5000/api/v2/nodes/1", 
          "url_root": "http://localhost:5000/"
        }
           
3. Get the list of inputs of a specific node.

    REST url:: 
    
        http://localhost:5000/api/v2/nodes/6/io/inputs?limit=2

    Description:
    
        returns the list of the first two input nodes (``limit=2``) of the *Node* object with ``pk=6``.

    Response::

        {
          "data": {
            "inputs": [
              {
                "ctime": "Fri, 24 Jul 2015 18:49:23 GMT", 
                "id": 10605, 
                "label": "", 
                "mtime": "Mon, 25 Jan 2016 14:35:00 GMT", 
                "state": "IMPORTED", 
                "type": "data.remote.RemoteData.", 
                "uuid": "16b93b23-8629-4d83-9259-de2a947b43ed"
              }, 
              {
                "ctime": "Fri, 24 Jul 2015 14:33:04 GMT", 
                "id": 9215, 
                "label": "", 
                "mtime": "Mon, 25 Jan 2016 14:35:00 GMT", 
                "state": "IMPORTED", 
                "type": "data.array.kpoints.KpointsData.", 
                "uuid": "1b4d22ec-9f29-4e0d-9d68-84ddd18ad8e7"
              }
            ]
          }, 
          "method": "GET", 
          "path": "/api/v2/nodes/6/io/inputs", 
          "pk": 6, 
          "query_string": "limit=2", 
          "resource_type": "nodes", 
          "url": "http://localhost:5000/api/v2/nodes/6/io/inputs?limit=2", 
          "url_root": "http://localhost:5000/"
        }
        

4. Filter the inputs/outputs of a node by their type. 

    REST url:: 
    
        http://localhost:5000/api/v2/nodes/6/io/inputs?type="data.array.kpoints.KpointsData."

    Description:
    
        returns the list of the `*KpointsData* input nodes of
        the *Node* object with ``pk=6``.

    Response::

        {
          "data": {
            "inputs": [
              {
                "ctime": "Fri, 24 Jul 2015 14:33:04 GMT", 
                "id": 9215, 
                "label": "", 
                "mtime": "Mon, 25 Jan 2016 14:35:00 GMT", 
                "state": "IMPORTED", 
                "type": "data.array.kpoints.KpointsData.", 
                "uuid": "1b4d22ec-9f29-4e0d-9d68-84ddd18ad8e7"
              }
            ]
          }, 
          "method": "GET", 
          "path": "/api/v2/nodes/6/io/inputs", 
          "pk": 6, 
          "query_string": "type=\"data.array.kpoints.KpointsData.\"", 
          "resource_type": "nodes", 
          "url": "http://localhost:5000/api/v2/nodes/6/io/inputs?type=\"data.array.kpoints.KpointsData.\"", 
          "url_root": "http://localhost:5000/"
        }
        
    REST url::
    
        http://localhost:5000/api/v2/nodes/6/io/outputs?type="data.remote.RemoteData."
    
    Description:
    
        returns the list of the *RemoteData* output nodes of the *Node* object with ``pk=6``.

    Response::

        {
          "data": {
            "outputs": [
              {
                "ctime": "Fri, 24 Jul 2015 20:35:02 GMT", 
                "id": 2811, 
                "label": "", 
                "mtime": "Mon, 25 Jan 2016 14:34:59 GMT", 
                "state": "IMPORTED", 
                "type": "data.remote.RemoteData.", 
                "uuid": "bd48e333-da8a-4b6f-8e1e-6aaa316852eb"
              }
            ]
          }, 
          "method": "GET", 
          "path": "/api/v2/nodes/6/io/outputs", 
          "pk": 6, 
          "query_string": "type=\"data.remote.RemoteData.\"", 
          "resource_type": "nodes", 
          "url": "http://localhost:5000/api/v2/nodes/6/io/outputs?type=\"data.remote.RemoteData.\"", 
          "url_root": "http://localhost:5000/"
        }
            


5. Getting the list of the attributes/extras of a specific node

    REST url::
    
        http://localhost:5000/api/v2/nodes/1822/content/attributes

    Description:
    
        returns the list of all attributes of the *Node* object with ``pk=1822``.

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
          "path": "/api/v2/nodes/1822/content/attributes", 
          "pk": 1822, 
          "query_string": "", 
          "resource_type": "nodes", 
          "url": "http://localhost:5000/api/v2/nodes/1822/content/attributes", 
          "url_root": "http://localhost:5000/"
        }
      


    REST url::

        http://localhost:5000/api/v2/nodes/1822/content/extras

    Description:
    
        returns the list of all the extras of the *Node* object with ``pk=1822``.

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
          "path": "/api/v2/codes/1822/content/extras", 
          "pk": 1822, 
          "query_string": "", 
          "resource_type": "codes", 
          "url": "http://localhost:5000/api/v2/codes/1822/content/extras", 
          "url_root": "http://localhost:5000/"
        }
     

6. Getting a user-defined list of attributes/extras of a specific node 

    REST url::
    
         http://localhost:5000/api/v2/codes/1822/content/attributes?alist=append_text,is_local

    Description:
    
        returns a list of the attributes ``append_text`` and ``is_local`` of the *Node* object with ``pk=1822``.

    Response::

        {
          "data": {
            "attributes": {
              "append_text": "", 
              "is_local": false
            }
          }, 
          "method": "GET", 
          "path": "/api/v2/codes/1822/content/attributes", 
          "pk": 1822, 
          "query_string": "alist=append_text,is_local", 
          "resource_type": "codes", 
          "url": "http://localhost:5000/api/v2/codes/1822/content/attributes?alist=append_text,is_local", 
          "url_root": "http://localhost:5000/"
        }
        


    REST url::
    
        http://localhost:5000/api/v2/codes/1822/content/extras?elist=trialBool,trialInt

    Description:
    
        returns a list of the extras ``trialBool`` and ``trialInt`` of the *Node* object with ``pk=1822``.

    Response::

        {
          "data": {
            "extras": {
              "trialBool": true, 
              "trialInt": 34
            }
          }, 
          "method": "GET", 
          "path": "/api/v2/codes/1822/content/extras", 
          "pk": 1822, 
          "query_string": "elist=trialBool,trialInt", 
          "resource_type": "codes", 
          "url": "http://localhost:5000/api/v2/codes/1822/content/extras?elist=trialBool,trialInt", 
          "url_root": "http://localhost:5000/"
        }

7. Getting all the attributes/extras of a specific node except a user-defined list


    REST url::

        http://localhost:5000/api/v2/codes/1822/content/attributes?nalist=append_text,is_local    

    Description:
    
        returns all the attributes of the *Node* object with ``pk=1822`` except ``append_text`` and ``is_local``.

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
          "path": "/api/v2/codes/1822/content/attributes", 
          "pk": 1822, 
          "query_string": "nalist=append_text,is_local", 
          "resource_type": "codes", 
          "url": "http://localhost:5000/api/v2/codes/1822/content/attributes?nalist=append_text,is_local", 
          "url_root": "http://localhost:5000/"
        }


    REST url::

        http://localhost:5000/api/v2/codes/1822/content/extras?nelist=trialBool,trialInt

    Description:
    
        returns all the extras of the *Node* object with ``pk=1822`` except ``trialBool`` and ``trialInt``.

    Response::

        {
          "data": {
            "extras": {
              "trialFloat": 3.0, 
              "trialStr": "trial"
            }
          }, 
          "method": "GET", 
          "path": "/api/v2/codes/1822/content/extras", 
          "pk": 1822, 
          "query_string": "nelist=trialBool,trialInt", 
          "resource_type": "codes", 
          "url": "http://localhost:5000/api/v2/codes/1822/content/extras?nelist=trialBool,trialInt", 
          "url_root": "http://localhost:5000/"
        }


.. note:: The same REST urls supported for the resource ``nodes`` are also available with the derived resources, namely,  ``calculations``, ``data``, and ``codes``, just changing the resource field in the path.


Users
-----

1. Getting a list of the users

    REST url:: 

        http://localhost:5000/api/v2/users/

    Description:
    
        returns a list of all the *User* objects. 

    Response::

        {
          "data": {
            "users": [
              {
                "date_joined": "Mon, 25 Jan 2016 14:31:17 GMT", 
                "email": "aiida@localhost", 
                "first_name": "AiiDA", 
                "id": 1, 
                "institution": "", 
                "is_active": true, 
                "last_login": "Mon, 25 Jan 2016 14:31:17 GMT", 
                "last_name": "Daemon"
              }, 
              {
                "date_joined": "Thu, 11 Aug 2016 12:35:32 GMT",
                "email": "gengis.khan@aiida.net",
                "first_name": "Gengis",
                "id": 2,
                "institution": "",
                "is_active": true,
                "last_login": "Thu, 11 Aug 2016 12:35:32 GMT", 
                "last_name": "Khan"
              }
            ]
          }, 
          "method": "GET", 
          "path": "/api/v2/users/", 
          "pk": null, 
          "query_string": "", 
          "resource_type": "users", 
          "url": "http://localhost:5000/api/v2/users/", 
          "url_root": "http://localhost:5000/"
        }
        
2. Getting a list of users whose first name starts with a given string

    REST url:: 

        http://localhost:5000/api/v2/users/?first_name=ilike="aii%"

    Description:
    
        returns a lists of the *User* objects whose first name starts with ``"aii"``, regardless the case of the characters.

    Response::

        {
          "data": {
            "users": [
              {
                "date_joined": "Mon, 25 Jan 2016 14:31:17 GMT", 
                "email": "aiida@localhost", 
                "first_name": "AiiDA", 
                "id": 1, 
                "institution": "", 
                "is_active": true, 
                "last_login": "Mon, 25 Jan 2016 14:31:17 GMT", 
                "last_name": "Daemon"
              }
            ]
          }, 
          "method": "GET", 
          "path": "/api/v2/users/", 
          "pk": null, 
          "query_string": "first_name=ilike=%22aii%%22", 
          "resource_type": "users", 
          "url": "http://localhost:5000/api/v2/users/?first_name=ilike=\"aii%\"", 
          "url_root": "http://localhost:5000/"
        }
        
Groups
------


1. Getting a list of groups

    REST url::

        http://localhost:5000/api/v2/groups/?limit=10&orderby=-user_id

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
                "name": "SSSP_new_phonons_0p002", 
                "type": "", 
                "user_id": 2, 
                "uuid": "7c0e0744-8549-4eea-b1b8-e7207c18de32"
              }, 
              {
                "description": "", 
                "id": 102, 
                "name": "SSSP_cubic_old_phonons_0p025", 
                "type": "", 
                "user_id": 1, 
                "uuid": "c4e22134-495d-4779-9259-6192fcaec510"
              }, 
              ...
     
            ]
          }, 
          "method": "GET", 
          "path": "/api/v2/groups/", 
          "pk": null, 
          "query_string": "limit=10&orderby=-user_id", 
          "resource_type": "groups", 
          "url": "http://localhost:5000/api/v2/groups/?limit=10&orderby=-user_id", 
          "url_root": "http://localhost:5000/"
        }

2. Getting the details of a specific group

    REST url::

        http://localhost:5000/api/v2/groups/23

    Description:
    
        returns the details of the *Group* object with ``pk=23``.

    Response::

        {
          "data": {
            "groups": [
              {
                "description": "GBRV US pseudos, version 1.2", 
                "id": 23,
                "name": "GBRV_1.2", 
                "type": "data.upf.family", 
                "user_id": 2, 
                "uuid": "a6e5b6c6-9d47-445b-bfea-024cf8333c55"
              }
            ]
          }, 
          "method": "GET", 
          "path": "/api/v2/groups/23", 
          "pk": 23, 
          "query_string": "", 
          "resource_type": "groups", 
          "url": "http://localhost:5000/api/v2/groups/23", 
          "url_root": "http://localhost:5000/"
        }
                
