===================
REST API for AiiDA
===================

AiiDA provides a REST API to access the information of the AiiDA objects stored
in the database. There are four types of AiiDA objects: *Computer*, *Node*, *User*,
and *Group*. The *Node* type has three subtypes: *Calculation*, *Data*,
and *Code*. Different REST urls are provided to get the list of objects, 
the details of a specific object as well as its inputs/outputs/attributes/extras.

The AiiDA REST API is implemented using *Flask RESTFul* framework. The response
data are always returned in *JSON* format.

To start the REST server 
python api.py --host=HOST --port=PORT

If you do not define the host and the port, the REST API will run on the port *5000* 
of *localhost*. So the **base url** for your REST API will be:

    \http://localhost:5000/api/v2

where the last field identifies the version of the API. This field enables running  multiple versions of the API simultaneously, so that the clients should not be obliged to update immediately the format of their requests when a new version of the API is deployed. The current latest version is **v2**. 
    
Let us now introduce the urls supported by the API.

General form of the urls
++++++++++++++++++++++++

A generic url to send requests to the REST API is formed by:
 
    1. the base url. It specifies the host and the version of the API. Ex. \http://localhost:5000/api/v2.
    2. the path. It defines the kind of resource requested by the client and the type of query.
    3. the query string (not mandatory). It can be used for any further specification of the request, e.g. to introduce query filters, to give instructions for ordering, to set how results have to be paginated, etc.   

The query string is introduced by the question mark character "?". Here are some examples:
 
  \http://localhost:5000/api/v2/users/
  
  \http://localhost:5000/api/v2/computers?scheduler_type="slurm"
  
  \http://localhost:5000/api/v2/nodes/?id>45&type=like="%data%"

The trailing slash at the end of the path is not mandatory.

How to set the number of results
--------------------------------

Before exploring in details the functionalities of the API it is important to know that the AiiDA RESTAPI provides two different ways to limit the number of results returned by the server: using pagination, or specifying explicitly *limit* and *offset*.

Pagination
**********

The complete set of results is divided in *pages* containing by default 20 results each. Individual pages are accessed by appending "/page/(PAGE)" to the end of the path, where (PAGE) is the number of the page required. The number of results contained in each page can be altered by specifying the *perpage* field in the query string. However, *perpage* values larger than 400 are not allowed. Examples:

    \http://localhost:5000/api/v2/computers/page/1?

    \http://localhost:5000/api/v2/computers/page/1?perpage=5

    \http://localhost:5000/api/v2/computers/page

If no page number is specified, as in the last example, the system redirects the request to page 1. When pagination is used the header of the response contains two more non-empty fields:
    
    - *X-Total-Counts* (custom field): the total number of results returned by the query, i.e.the sum of the results of all pages)
    - *Links*: links to the first, previous, next, and last page. Suppose you send a request whose results would fill 8 pages. Then the value of the *Links* field would look like:     <\http://localhost:5000/.../page/1?... ;>; rel=first, <\http://localhost:5000/.../page/3?...     ;>; rel=prev, <\http://localhost:5000/.../page/5?... ;>; rel=next, <\http://localhost:5000/.../page/8?... ;>; rel=last,

Setting *limit* and *offset*
****************************

You can specify two special fields in the query string:

    - *limit*: field that specifies the largest number of results that will be returned. The syntax is the following: "limit=(LIMIT)", ex: "limit=20". The default and highest allowed limit is 400
    - *offset*: field that specifies how many entries are skipped before returning results. The syntax is the following: "offset=(OFFSET)", ex: "offset=20". By default no offset applies.



How to build the path
---------------------

There are two type of paths: those that request a list of objects of a specific resource, namely, the AiiDA object type you are requesting, and those that inquire a specific object of a certain resource. In both cases the path has to start with the name of the resource. The complete list of resources is: **users**, **computers**, **groups**, **nodes**, **codes**, **calculations**, and **datafdatra**.
If you request data for a specific object you have to append its pk to the path (note that the pk is also called id). Here are few examples:

    \http://localhost:5000/api/v2/users/
    
    \http://localhost:5000/api/v2/users/2
    
    \http://localhost:5000/api/v2/nodes/345
    
    
When you ask for a single object (and only in that case) you can construct more complex requests, namely, you can ask for the inputs/outputs or for the attributes/extras of an object. In the first case you have to append to the path the fields **"/io/inputs"** or **"io/outputs"** depending on the desired relation between the nodes, whereas in the second case you have to append **"content/attributes"** or **"content/extras"** depending on the kind of content you want to access. Here are some examples: 

    \http://localhost:5000/api/v2/calculations/345/io/inputs
    
    \http://localhost:5000/api/v2/nodes/345/io/inputs
    
    \http://localhost:5000/api/v2/data/385/content/attributes
    
    \http://localhost:5000/api/v2/nodes/385/content/extras

.. note:: As you can see from the last examples, a *Node*-type object can be accessed requesting either a generic **/nodes** resource or requesting the resource corresponding to its specific type (**/data**, **/codes**, **/calculations** ). This is because in AiiDA  the classes *Data*, *Code*, and *Calculation* are derived from the class *Node*.

How to build the query string
-----------------------------

The query string is formed by one or more fields separated by the special character "&".
Each field has the form (*key*)(*operator*)(*value*). The same constraints that apply to the names of python variables determine what are the valid keys, namely, only alphanumeric characters plus '_' are allowed and the first character cannot be a number.

Special keys 
************

There are several special keys that can be specified only once in a query string. All of them must be followed by the operator '='. Here is the complete list:

    :limit: This key only supports integer values.

    :offset: Same format as *limit*.

    :perpage: Same format as *limit*.

    :orderby: This key is used to impose a specific ordering to the results. Two orderings are supported, ascending or descending. The value for the *orderby* key must be the name of the property with respect to which to order the results. Additionall'+' or '-' can be pre-pended to the value in order to select, respectively, ascending or descending order. Specifying no leading character is equivalent to select ascending order. Ascending (descending) order for strings corresponds to alphabetical (reverse-alphabetical) order, whereas for datetime objects it corresponds to chronological (reverse-chronological order). Examples:
    
        \http://localhost:5000/api/v2/c=+id

        \http://localhost:5000/api/v2/computers=+name

        \http://localhost:5000/api/v2/computers/orderby=-uuid
          
    :alist: This key is be used to specify which attributes of a specific object have to be returned. The desired attributes have to be provided as a comma-separated list of values. It requires that the path contains the endpoint "/content/attributes". Example:         

        \http://localhost:5000/api/v2/codes/1822/content/attributes?alist=append_text,prepend_text 

    :nalist: (incompatible with *alist*) This key is be used to specify which attributes of a specific object *should not* be returned. The syntax is identical to *alist*. The system returns all the attributes except those specified in the list of values.  
    
    :elist: Similar to *alist* but for extras. It requires that the path contains the endpoint "/content/extras".
    
    :nelist: (incompatible with *elist*) Similar to *nalist* but for extras. It requires that the path contains the endpoint "/content/extras".

Filters
*******

All the other fields composing a query string are filters, that is, conditions that have to be fulfilled by the retrieved objects. When a query string contains multiple filters, those are applied as they were related by the AND logical clause, that is, the results have to fulfill all the conditions set by the filters (and not any of them). Each filter key is associated to a unique value type. The possible types are:

    :string: Text enclosed in double quotes. If the string contains double quotes those have to be escaped as '""' (two double quotes). Note that in the unlikely occurrence of a sequence of double quotes you will have escape it by writing twice as many double quotes.  

    :integer: Positive integer numbers.
    
    :datetime: Datetime objects expressed in the format (DATE)T(TIME)(SHIFT) where SHIFT is the time difference with respect to the UTC time. This is required to avoid any problem arising from comparing datetime values expressed in different time zones. The formats of each field are:
    
        1. YYYY-MM-DD for DATE (mandatory).
        2. HH:MM:SS for TIME (optional). The formats HH and HH:MM are supported too.  
        3. SHIFT(optional) has +/-HH:MM. The format +/-HH is allowed too. If no sign is specified, a positive shift is assumed.
        
        This format is ISO-8601 compliant. Note that date and time fields have to be separated by the character 'T'. Examples:
    
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

The operators supported by a specific key are uniquely determined by the value type associated to that key. For example, a key that requires a boolean value admits only the identity operator '=', whereas an integer value enables the usage of the relational operators '=', '<', '<=', '>', '>=' plus the membership operator '=in='.  
Please refer to the following table for a comprehensive list. 

+---------+------------------------+---------------------------------+
|operator |meaning                 |accepted value types             |
+=========+========================+=================================+
|'='      |identity                |integers, strings, bool, datetime|
+---------+------------------------+---------------------------------+
|'>'      |greater than            |integers, strings, datetime      |
+---------+------------------------+---------------------------------+
|'<'      |lower than              |integers, strings, datetime      |
+---------+------------------------+---------------------------------+
|'>='     |greater than or equal to|integers, strings, datetime      |
+---------+------------------------+---------------------------------+
|'<='     |lower than or equal to  |integers, strings, datetime      |
+---------+------------------------+---------------------------------+
|'=like=' |pattern matching        |strings                          |
+---------+------------------------+---------------------------------+
|'=ilike='|case-insensitive        |strings                          |
|         |pattern matching        |                                 |
+---------+------------------------+---------------------------------+
|'=in='   |identity with one       |integers, strings, datetime      |
|         |    element of a list   |                                 |
+---------+------------------------+---------------------------------+

The pattern matching operators '=like=' and '=ilike=' must be followed by the pattern definition, namely, a string where two characters assume special meaning:

    1. '%' is used to replace an arbitrary sequence of characters, including no characters.
    2. '_' is used to replace one or zero characters.
    
Differently from '=like=', '=ilike=' assumes that two characters that only differ in the case are equal. 

To prevent interpreting special characters as wildcards, these have to be escaped by pre-pending the character '\'.

Examples:

    **name=like="a%d_"** matches **"aiida"** but does not match **"AiiDA"**
    
    **name=ilike="a%d_"** matches both **"aiida"** and **"AiiDA"**
    
    **name=like="a_d_"** does not match **"aiida"** 
    
    **name=like="aii%d_a"** matches **"aiida"**
    
    **uuid=like="cdfd48%"** matches **"cdfd48f9-7ed2-4969-ba06-09c752b83d26"**
    
    **description=like="This calculation is %\\% useful"** matches **"This calculation is 100% useful"**

The membership operator '=in=' has to be followed by a comma-separated list of values of the same type. The condition is fulfilled if the column value of an object is an element of the list.

Examples: 

    \http://localhost:5000/api/v2/nodes?id=in=45,56,78
    
    \http://localhost:5000/api/v2/computers/?scheduler_type=in="slurm","pbs"&state="FINISHED"

The relational operators '<', '>', '<=', '>=' assume natural ordering for integers, (case-insensitive) alphabetical ordering for strings, and chronological ordering for datetime values.

Examples:

    1. \http://localhost:5000/api/v2/nodes?id>578
    2. *\http://localhost:5000/api/v2/users/?last_login>2014-04-07* selects only the user that logged in for the last time after April 7th, 2014.
    3. *\http://localhost:5000/api/v2/users/?last_name<="m"* selects only the users whose last name begins with a character in the range [a-m].


.. note:: Object types have to be specified by a string that defines their position in the AiiDA source tree. Examples: 
    - type="data.Data" selects only objects of *Data* type
    - type="data.remote.RemoteData" selects only objects of *RemoteData* type
    - type="data.parameter.ParameterData"

The HTTP response
+++++++++++++++++

The HTTP response of the REST API consists in a JSON object, a header, and a status code. Possible status are:
1. 200 for successful requests.
2. 400 for bad requests. In this case, the JSON object contains only an error message describing the problem.
3. 500 for a generic internal server error. No JSON is returned.
4. 404 for invalid url. Differently from the 400 status, it is returned when the REST API does not succeed in directing the request to a specific resource. This typically happens when the path does not match any of the supported format. No JSON is returned.

The header is a standard HTTP response header with the additional custom field *X-Total-Counts* and, only if paginated results are required, a non-empty *Link* field, as described in the Pagination section.

The JSON object mainly contains the list of the results returned by the API. This list is assigned to the key *data*. Additionally, the JSON object contains several informations about the request (keys *method*, *url*, *url_root*, *path*, *query_string*, *resource_type*, and *pk*).



Examples
++++++++

AiiDA REST API provides the urls to get the list of *Computer* nodes stored in the database
or to get the details of a single *Computer* node. The REST urls for *Computer* are explained
below.

1. Get list of *Computer* nodes:
--------------------------------

This url returns the list of *Computer* nodes stored in AiiDA database. There are two ways to limit the number of results returned by the REST API, either using pagination, or providing values LIMIT and OFFSET
The URL format is:

    \http://localhost:5000/api/computers/page/(PAGE)?(COLUMN_FILTERS)&(ORDERBY)&(PERPAGE)
    \http://localhost:5000/api/computers?(COLUMN_FILTERS)&(LIMIT)&(OFFSET)&(ORDERBY)

In the first case, the results of a request are organized in pages containing by default 20 results each.

The order of the fields composing the querystring is not significant and none of the field is mandatory.
Here, we give a detailed explanation of the fields that form a query string.

    - COLUMN_FILTERS: Each filter is composed by a key, an operator, and a value. A key represents a column name, namely, a specific property of a node. The supported operators depend on the key, see the following table. A value can be either an integer number or a double quoted string. The operator '=in=' can be followed by a comma-separated list of values.

        +---------------+-----------+-----------------------+------------------------+
        | Key           | Operator  | Query string          |             Details    |
        +===============+===========+=======================+========================+
        | id            | "=",      | | id=1                | | Primary key of the   |
        +               +-----------+-----------------------+ | Computer             +
        |               | "<" ,"<=" | | id<5, id<=5         |                        |
        +               +-----------+-----------------------+                        +
        |               | ">", ">=" | | id>5, id>=5         |                        |
        +               +-----------+-----------------------+                        +
        |               | "in"      | | id=in=2,3,6,7       |                        |
        +---------------+-----------+-----------------------+------------------------+
        | name          | "="       | | name="abc"          | | Name of the          |
        +               +-----------+-----------------------+ | Computer             +
        |               | "like"    | | name=like="ab_c%"   |                        |
        +               +-----------+-----------------------+                        +
        |               | "ilike"   | | name=ilike="aB_c%"  |                        |
        +---------------+-----------+-----------------------+------------------------+
        | hostname      | "="       | | hostname="abc"      | | Hostname of the      |
        +               +-----------+-----------------------+ | Computer             +
        |               | "like"    | | hostname=like=      |                        |
        |               |           | | "ab_c%"             |                        |
        +               +-----------+-----------------------+                        +
        |               | "ilike"   | | hostname=ilike=     |                        |
        |               |           | | "aB_c%"             |                        |
        +---------------+-----------+-----------------------+------------------------+
        | description   | "="       | | description="lmn"   | | Description of the   |
        +               +-----------+-----------------------+ | Computer             +
        |               | "like"    | | description=like=   |                        |
        |               |           | | "lm_n%"             |                        |
        +               +-----------+-----------------------+                        +
        |               | "ilike"   | | description=ilike=  |                        |
        |               |           | | "Km_N%"             |                        |
        +---------------+-----------+-----------------------+------------------------+
        | enabled       | "="       | | enabled=true        | | If *true*, Computer  |
        |               |           |                       | | is enabled to run    |
        |               |           |                       | | calculations else    |
        |               |           |                       | | *false*              |
        +---------------+-----------+-----------------------+------------------------+
        | scheduler_type| "="       | | scheduler_type=     | | Scheduler type       |
        |               |           | | "slurm"             |                        |
        +               +-----------+-----------------------+                        +
        |               | "in"      | | scheduler_type=in=  |                        |
        |               |           | | "slurm","pbspro"    |                        |
        +---------------+-----------+-----------------------+------------------------+
        | transport_type| "="       | | transport_type="ssh"| | Transport type       |
        +               +-----------+-----------------------+                        +
        |               | "in"      | | transport_type=in=  |                        |
        |               |           | | "ssh", ...          |                        |
        +---------------+-----------+-----------------------+------------------------+
        | uuid          | "="       | | uuid="aabh-6754-.." | | Uuid of the Computer |
        +               +-----------+-----------------------+                        +
        |               | "in"      | | uuid=in=            |                        |
        |               |           | | "aa..", "bb..", ... |                        |
        +---------------+-----------+-----------------------+------------------------+

.. note:: Multiple filters can be specified separating them by the special character "&". In this case, the boolean operator AND is applied between the conditions set by the filters. You can specify multiple filters on the same column, ex: "id>10&id<=30". Clearly, the query string "id=20&d=30" would yield no results.
.. note:: If a string value contains '"' characters (double quotes), the latter must be escaped as '""' (two double quotes). If you use "=like=" or "=ilike=" operators and you want to match a string that contains "%" or "_" characters, you have to escape those using a backslash, e.g. "\\%" and "\\_".
.. note:: Filter keys can only contain alphanumeric characters, dashes, and underscores. In any case, if a query string contains well-formed column names that, however, do not correspond to any column of the database table, an error is returned.


    - ORDERBY: field that specifies how to order the elements returned by the API. For each of the projected columns you can choose between ascending or descending order. If for a certain column the order is not specified, then the ascending order will be used.

        +-------------+-----------+--------------------+-----------------------------+
        | Column name | Order type| Query string       |             Details         |
        +=============+===========+====================+=============================+
        | id          | ascending | | orderby=id       | | Final results will be     |
        |             |           | |     OR           | | ordered by *id* in        |
        |             |           | | orderby=+id      | | ascending order           |
        +             +-----------+--------------------+-----------------------------+
        |             | descending| | orderby=-id      | | Final results will be     |
        |             |           | |                  | | ordered by *id* in        |
        |             |           |                    | | descending order          |
        +-------------+-----------+--------------------+-----------------------------+
        | ...                                                                        |
        +-------------+-----------+--------------------+-----------------------------+


.. note:: You can replace the column name e.g. *id* by *name/hostname/enabled/scheduler_type/transport_type/uuid*
.. note:: You can require ordering on multiple columns, e.g. "orderby=+scheduler_type,-id". This way, computers will be ordered by their scheduler type in ascending alphabetical order, and computers with the same scheduler type will be ordered from the highest to the lowest id.

**Example**

    REST url:: \http://localhost:5000/computers?limit=3&offset=2&orderby=id

    Description::
        returns the list of 3 *Computer* nodes (limit=3) starting from the 2nd
        row (offset=2) of the database table and the list will be ordered
        by ascending values of *id* (default ordering if ORDERBY is not provided).

    Response::

        {
          "data": [
            {
              "description": "",
              "enabled": true,
              "hostname": "test.abc.ch",
              "id": 3,
              "name": "test3",
              "scheduler_type": "pbspro",
              "transport_params": "{}",
              "transport_type": "local",
              "uuid": "56d7f972-1232-4adc-aa5b-c425619fdd58"
            },
            {...},
            {...},
            {...},
          ],
          "method": "GET",
          "node_type": "computers",
          "path": "/computers",
          "pk": null,
          "query_string": {},
          "url": "\http://localhost:5000/computers",
          "url_root": "\http://localhost:5000/"
        }


2. Get details of single *Computer* node:
------------------------------------------

This url returns the details of *Computer* node from AiiDA database.
The URL format is:

    \http://localhost:5000/computers/(PK)

Where,
    - PK: Primary key of the *Computer*
    - PK: Primary key of the *Computer*

**Example**

    REST url:: \http://localhost:5000/computers/1

    Description::
        returns the details of *Computer* node (pk=1) from database.

    Response::

        {
          "data": [
            {
              "description": "",
              "enabled": true,
              "hostname": "test.abb.ch",
              "id": 1,
              "name": "test1",
              "scheduler_type": "pbspro",
              "transport_params": "{}",
              "transport_type": "local",
              "uuid": "56d7f972-56bb-4adc-aa5b-c425619fdd58"
            }
          ],
          "method": "GET",
          "node_type": "computers",
          "path": "/computers/1",
          "pk": "1",
          "query_string": {},
          "url": "\http://localhost:5000/computers/1",
          "url_root": "\http://localhost:5000/"
        }


Nodes
++++++

AiiDA *Node* type is subdivided into *Calculation, Data and Code*. All the REST urls
provided for *Node* can be applied to *Calculation, Data and Code* as well.The AiiDA
REST API provides the urls to get the list of *Node* nodes stored in database or to get
the details of single *Node* node, its inputs, outputs, attributes and extras. Different
type of filters can be applied on list of nodes. The REST urls are explained below.

1. Get list of *Node* nodes:
-----------------------------

This url returns the list of *Node* nodes stored in AiiDA database.
The URL format is:

    \http://localhost:5000/nodes?(COLUMN_FILTERS)&(LIMIT)&(OFFSET)&(ORDERBY)

Where,

    - COLUMN_FILTERS:

        +---------------+-----------+-----------------------+------------------------+
        | Column name   | Operation | Query string          |             Details    |
        +===============+===========+=======================+========================+
        | id            | "="       | | id=1                | | Primary key of the   |
        +               +-----------+-----------------------+ | Node                 +
        |               | "<" ,"<=" | | id<5, id<=5         |                        |
        +               +-----------+-----------------------+                        +
        |               | ">", ">=" | | id>5, id>=5         |                        |
        +               +-----------+-----------------------+                        +
        |               | "in"      | | id={in:[2,3,6,7]}   |                        |
        +---------------+-----------+-----------------------+------------------------+
        | label         | "="       | | label=abc           | | Label of the Node    |
        +               +-----------+-----------------------+                        +
        |               | "like"    | | label={like:abc%}   |                        |
        +               +-----------+-----------------------+                        +
        |               | "ilike"   | | label={like:aBc%}   |                        |
        +---------------+-----------+-----------------------+------------------------+
        | type          | "="       | | type=abc            | | Type of the Node.    |
        |               |           |                       | | Please note that     |
        |               |           |                       | | here we need to      |
        |               |           |                       | | give complete Node   |
        |               |           |                       | | type e.g.            |
        |               |           |                       | | type=data.Data.      |
        |               |           |                       | | to get all Data Node |
        +---------------+-----------+-----------------------+------------------------+
        | state         | "="       | | state=FINISHED      | | State of the Node    |
        +---------------+-----------+-----------------------+------------------------+
        | ctime         | "="       | | ctime=??            | | Creation time of     |
        +               +-----------+-----------------------+ | the Node             +
        |               | "<" ,"<=" | | ctime<??, ctime<=?? |                        |
        +               +-----------+-----------------------+                        +
        |               | ">", ">=" | | ctime>??, ctime>=?? |                        |
        +---------------+-----------+-----------------------+------------------------+
        | mtime         | "="       | | mtime=??            | | Last modification    |
        +               +-----------+-----------------------+ | time of the Node     +
        |               | "<" ,"<=" | | mtime<??, mtime<=?? |                        |
        +               +-----------+-----------------------+                        +
        |               | ">", ">=" | | mtime>??, mtime>=?? |                        |
        +---------------+-----------+-----------------------+------------------------+
        | uuid          | "="       | | uuid=aabh-6754-..   | | Uuid of the Node     |
        +               +-----------+-----------------------+                        +
        |               | "in"      | | uuid=               |                        |
        |               |           | | {in:[aa..,bb..]}    |                        |
        +---------------+-----------+-----------------------+------------------------+

    - LIMIT: number that says no more than that many rows will be returned

    - OFFSET: number that says to skip that many rows before beginning to return rows.

    - ORDERBY: requested node list would be ordered by the provided column. If the order
        type is not provided, then *asc* will be used as default order type.

        +-------------+-----------+--------------------+-----------------------------+
        | Column name | Order type| Query string       |             Details         |
        +=============+===========+====================+=============================+
        | id          | "asc",    | | orderby=id OR    | | Final results will be     |
        |             |           | | orderby={id:asc} | | ordered by *id* in        |
        |             |           |                    | | ascending order           |
        +             +-----------+--------------------+-----------------------------+
        |             | "desc",   | | orderby=id OR    | | Final results will be     |
        |             |           | | orderby={id:desc}| | ordered by *id* in        |
        |             |           |                    | | descending order          |
        +-------------+-----------+--------------------+-----------------------------+
        | ...                                                                        |
        +-------------+-----------+--------------------+-----------------------------+


        .. note:: You could replace column name e.g. *id* with *label/type/state/*
*ctime/mtime/uuid*

**Example**

    REST url:: \http://localhost:5000/nodes?limit=2&offset=8&orderby=id

    Description::
        returns the list of 2 *Node* nodes (limit=2) starting from 8th
        row (offset=8) of the database table and the list will be ordered
        by *id* in descending order (default order if order is not provided).

    Response::

        {
          "data": {
            "node": [
              {
                "id": 9,
                "label": "",
                "state": null,
                "type": "data.array.kpoints.KpointsData.",
                "uuid": "4e872a4c-dc21-4910-ba60-c627cf33eeb0"
              },
              {
                "id": 43,
                "label": "",
                "state": "FAILED",
                "type": "calculation.job.simpleplugins.templatereplacer.TemplatereplacerCalculation.",
                "uuid": "9b1f2e61-5236-422e-809e-2b72ed7d9ce9"
              }
            ]
          },
          "method": "GET",
          "node_type": "nodes",
          "path": "/nodes",
          "pk": null,
          "query_string": {
            "limit": "2",
            "offset": "8",
            "orderby": "id"
          },
          "url": "\http://localhost:5000/nodes?limit=2&offset=8&orderby=id",
          "url_root": "\http://localhost:5000/"
        }


2. Get details of single *Node* node:
--------------------------------------

This url returns the details of *Node* type node from AiiDA database.
The URL format is:

    \http://localhost:5000/nodes/(PK)

Where,
    - PK: Primary key of the *Node*

**Example**

    REST url:: \http://localhost:5000/nodes/1

    Description::
        returns the details of *Node* node (pk=1) from database.

    Response::

        {
          "data": {
            "node": [
              {
                "id": 1,
                "label": "pw",
                "state": null,
                "type": "code.Code.",
                "uuid": "3e5d980c-5fc7-44a9-9189-343063a1366b"
              }
            ]
          },
          "method": "GET",
          "node_type": "nodes",
          "path": "/nodes/1",
          "pk": "1",
          "query_string": {},
          "url": "\http://localhost:5000/nodes/1",
          "url_root": "\http://localhost:5000/"
        }


3. Get list of *Node* inputs:
------------------------------

This url returns the inputs of the *Node* from AiiDA database.
The URL format is:

    \http://localhost:5000/nodes/(PK)/io/inputs?(COLUMN_FILTERS)&(LIMIT)&(OFFSET)&(ORDERBY)

.. note:: Please note that in this url the COLUMN_FILTERS, LIMIT, OFFSET
and ORDERBY will be applyed to the input list of the selected node
          with its PK.

Where,
    - PK: Primary key of the *Node* whose inputs are requested
    - COLUMN_FILTERS:

        +---------------+-----------+-----------------------+------------------------+
        | Column name   | Operation | Query string          |             Details    |
        +===============+===========+=======================+========================+
        | id            | "=",      | | id=1                | | Primary key of the   |
        +               +-----------+-----------------------+ | input Node           +
        |               | "<" ,"<=" | | id<5, id<=5         |                        |
        +               +-----------+-----------------------+                        +
        |               | ">", ">=" | | id>5, id>=5         |                        |
        +               +-----------+-----------------------+                        +
        |               | "in"      | | id={in:[2,3,6,7]}   |                        |
        +---------------+-----------+-----------------------+------------------------+
        | label         | "="       | | label=abc           | | Label of the input   |
        +               +-----------+-----------------------+ | node                 +
        |               | "like"    | | label={like:abc%}   |                        |
        +               +-----------+-----------------------+                        +
        |               | "ilike"   | | label={like:aBc%}   |                        |
        +---------------+-----------+-----------------------+------------------------+
        | type          | "="       | | type=abc            | | Type of the input    |
        |               |           |                       | | Node.                |
        |               |           |                       | | Please note that     |
        |               |           |                       | | here we need to      |
        |               |           |                       | | give complete Node   |
        |               |           |                       | | type e.g.            |
        |               |           |                       | | type=data.Data.      |
        |               |           |                       | | to get all Data Node |
        +---------------+-----------+-----------------------+------------------------+
        | state         | "="       | | state=FINISHED      | | State of the input   |
        |               |           |                       | | Node                 |
        +---------------+-----------+-----------------------+------------------------+
        | ctime         | "="       | | ctime=??            | | Creation time of     |
        +               +-----------+-----------------------+ | the input Node       +
        |               | "<" ,"<=" | | ctime<??, ctime<=?? |                        |
        +               +-----------+-----------------------+                        +
        |               | ">", ">=" | | ctime>??, ctime>=?? |                        |
        +---------------+-----------+-----------------------+------------------------+
        | mtime         | "="       | | mtime=??            | | Last modification    |
        +               +-----------+-----------------------+ | time of the input    +
        |               | "<" ,"<=" | | mtime<??, mtime<=?? | | Node                 |
        +               +-----------+-----------------------+                        +
        |               | ">", ">=" | | mtime>??, mtime>=?? |                        |
        +---------------+-----------+-----------------------+------------------------+
        | uuid          | "="       | | uuid=aabh-6754-..   | | Uuid of the input    |
        +               +-----------+-----------------------+ | Node                 +
        |               | "in"      | | uuid=               |                        |
        |               |           | | {in:[aa..,bb..]}    |                        |
        +---------------+-----------+-----------------------+------------------------+

    - LIMIT: number that says no more than that many rows will be returned

    - OFFSET: number that says to skip that many rows before beginning to return rows.

    - ORDERBY: requested node list would be ordered by the provided column. If the order
        type is not provided, then *asc* will be used as default order type.

        +-------------+-----------+--------------------+-----------------------------+
        | Column name | Order type| Query string       |             Details         |
        +=============+===========+====================+=============================+
        | id          | "asc",    | | orderby=id OR    | | Inputs will be            |
        |             |           | | orderby={id:asc} | | ordered by *id* in        |
        |             |           |                    | | ascending order           |
        +             +-----------+--------------------+-----------------------------+
        |             | "desc",   | | orderby=id OR    | | Inputs will be            |
        |             |           | | orderby={id:desc}| | ordered by *id* in        |
        |             |           |                    | | descending order          |
        +-------------+-----------+--------------------+-----------------------------+
        | ...                                                                        |
        +-------------+-----------+--------------------+-----------------------------+


        .. note:: You could replace column name e.g. *id* with *label/type/state/*
*ctime/mtime/uuid*


**Example 1**

    REST url:: \http://localhost:5000/nodes/10/io/inputs

    Description::
        returns the inputs list of *Node* node (pk=10) from database.

    Response::

        {
          "data": {
            "inputs": [
              {
                "id": 9,
                "label": "",
                "state": null,
                "type": "data.array.kpoints.KpointsData.",
                "uuid": "4e872a4c-dc21-4910-ba60-c627cf33eeb0"
              },
              {...},
              ...
            ]
          },
          "method": "GET",
          "node_type": "nodes",
          "path": "/nodes/10/io/inputs",
          "pk": "10",
          "query_string": {},
          "url": "\http://localhost:5000/nodes/10/io/inputs",
          "url_root": "\http://localhost:5000/"
        }


**Example 2**

    REST url:: \http://localhost:5000/nodes/10/io/inputs?type=data.array.kpoints.KpointsData.

    Description::
        returns the inputs (having *type=data.array.kpoints.KpointsData.*) list of
        the *Node* node (pk=10) from database.

    Response::

        {
          "data": {
            "inputs": [
              {
                "id": 9,
                "label": "",
                "state": null,
                "type": "data.array.kpoints.KpointsData.",
                "uuid": "4e872a4c-dc21-4910-ba60-c627cf33eeb0"
              }
            ]
          },
          "method": "GET",
          "node_type": "nodes",
          "path": "/nodes/10/io/inputs",
          "pk": "10",
          "query_string": {
            "type": "data.array.kpoints.KpointsData."
          },
          "url": "\http://localhost:5000/nodes/10/io/inputs?type=data.array.kpoints.KpointsData.",
          "url_root": "\http://localhost:5000/"
        }


4. Get list of *Node* outputs:
-------------------------------

This url returns the outputs of the *Node* from AiiDA database.
The URL format is:

    \http://localhost:5000/nodes/(PK)/io/outputs?(COLUMN_FILTERS)&(LIMIT)&(OFFSET)&(ORDERBY)

.. note:: Please note that in this url the COLUMN_FILTERS, LIMIT, OFFSET
and ORDERBY will be applyed to the output list of the selected node
          with its PK.

Where,
    - PK: Primary key of the *Node* whose outputs are requested
    - COLUMN_FILTERS:

        +---------------+-----------+-----------------------+------------------------+
        | Column name   | Operation | Query string          |             Details    |
        +===============+===========+=======================+========================+
        | id            | "=",      | | id=1                | | Primary key of the   |
        +               +-----------+-----------------------+ | output Node          +
        |               | "<" ,"<=" | | id<5, id<=5         |                        |
        +               +-----------+-----------------------+                        +
        |               | ">", ">=" | | id>5, id>=5         |                        |
        +               +-----------+-----------------------+                        +
        |               | "in"      | | id={in:[2,3,6,7]}   |                        |
        +---------------+-----------+-----------------------+------------------------+
        | label         | "="       | | label=abc           | | Label of the output  |
        +               +-----------+-----------------------+ | node                 +
        |               | "like"    | | label={like:abc%}   |                        |
        +               +-----------+-----------------------+                        +
        |               | "ilike"   | | label={like:aBc%}   |                        |
        +---------------+-----------+-----------------------+------------------------+
        | type          | "="       | | type=abc            | | Type of the output   |
        |               |           |                       | | Node.                |
        |               |           |                       | | Please note that     |
        |               |           |                       | | here we need to      |
        |               |           |                       | | give complete Node   |
        |               |           |                       | | type e.g.            |
        |               |           |                       | | type=data.Data.      |
        |               |           |                       | | to get all Data Node |
        +---------------+-----------+-----------------------+------------------------+
        | state         | "="       | | state=FINISHED      | | State of the output  |
        |               |           |                       | | Node                 |
        +---------------+-----------+-----------------------+------------------------+
        | ctime         | "="       | | ctime=??            | | Creation time of     |
        +               +-----------+-----------------------+ | the output Node      +
        |               | "<" ,"<=" | | ctime<??, ctime<=?? |                        |
        +               +-----------+-----------------------+                        +
        |               | ">", ">=" | | ctime>??, ctime>=?? |                        |
        +---------------+-----------+-----------------------+------------------------+
        | mtime         | "="       | | mtime=??            | | Last modification    |
        +               +-----------+-----------------------+ | time of the output   +
        |               | "<" ,"<=" | | mtime<??, mtime<=?? | | Node                 |
        +               +-----------+-----------------------+                        +
        |               | ">", ">=" | | mtime>??, mtime>=?? |                        |
        +---------------+-----------+-----------------------+------------------------+
        | uuid          | "="       | | uuid=aabh-6754-..   | | Uuid of the output   |
        +               +-----------+-----------------------+ | Node                 +
        |               | "in"      | | uuid=               |                        |
        |               |           | | {in:[aa..,bb..]}    |                        |
        +---------------+-----------+-----------------------+------------------------+

    - LIMIT: number that says no more than that many rows will be returned

    - OFFSET: number that says to skip that many rows before beginning to return rows.

    - ORDERBY: requested node list would be ordered by the provided column. If the order
        type is not provided, then *asc* will be used as default order type.

        +-------------+-----------+--------------------+-----------------------------+
        | Column name | Order type| Query string       |             Details         |
        +=============+===========+====================+=============================+
        | id          | "asc",    | | orderby=id OR    | | Inputs will be            |
        |             |           | | orderby={id:asc} | | ordered by *id* in        |
        |             |           |                    | | ascending order           |
        +             +-----------+--------------------+-----------------------------+
        |             | "desc",   | | orderby=id OR    | | Inputs will be            |
        |             |           | | orderby={id:desc}| | ordered by *id* in        |
        |             |           |                    | | descending order          |
        +-------------+-----------+--------------------+-----------------------------+
        | ...                                                                        |
        +-------------+-----------+--------------------+-----------------------------+


        .. note:: You could replace column name e.g. *id* with *label/type/state/*
*ctime/mtime/uuid*


**Example 1**

    REST url:: \http://localhost:5000/nodes/150/io/outputs

    Description::
        returns the outputs list of *Node* node (pk=150) from database.

    Response::

        {
          "data": {
            "outputs": [
              {
                "id": 163,
                "label": "",
                "state": null,
                "type": "data.remote.RemoteData.",
                "uuid": "fd89962e-6197-43a8-a07c-5a737d900cff"
              },
              {
                "id": 165,
                "label": "",
                "state": null,
                "type": "data.folder.FolderData.",
                "uuid": "4835dd56-8423-452a-b299-88057796efb9"
              },
              {...},
              ...
            ]
          },
          "method": "GET",
          "node_type": "nodes",
          "path": "/nodes/150/io/outputs",
          "pk": "150",
          "query_string": {},
          "url": "\http://localhost:5000/nodes/150/io/outputs",
          "url_root": "\http://localhost:5000/"
        }


**Example 2**

    REST url:: \http://localhost:5000/nodes/150/io/outputs?type=data.remote.RemoteData.

    Description::
        returns the outputs (having *type=data.remote.RemoteData.*) list of
        the *Node* node (pk=150) from database.

    Response::

        {
          "data": {
            "outputs": [
              {
                "id": 163,
                "label": "",
                "state": null,
                "type": "data.remote.RemoteData.",
                "uuid": "fd89962e-6197-43a8-a07c-5a737d900cff"
              }
            ]
          },
          "method": "GET",
          "node_type": "nodes",
          "path": "/nodes/150/io/outputs",
          "pk": "150",
          "query_string": {
            "type": "data.remote.RemoteData."
          },
          "url": "\http://localhost:5000/nodes/150/io/outputs?type=data.remote.RemoteData.",
          "url_root": "\http://localhost:5000/"
        }

5. Get list of *Node* attributes:
----------------------------------

This url returns the list of *Node* attributes. The *Node* attributes can be stored
in AiiDA database or calculated on fly. User can filter the list of attributes or can
request a specific attribute of the node.
The URL format is:

    \http://localhost:5000/nodes/(PK)/content/attributes?(alist)

Where,
    - PK: Primary key of the *Node*
    - alist: It is a list of attributes. There are two ways to specify
             the list of attributes. Consider, a1, a2, a3 are the attributes.
             1. alist=[a1,a2,a3] : response will contain the list of atrributes
                                   a1, a2 and a3
             2. alist=[-a1,-a2,-a3] : response will contain the list of all
                                      atrributes EXCEPT a1, a2 and a3

**Example 1**

    REST url:: \http://localhost:5000/nodes/10/content/attributes

    Description::
        returns the list of all attributes of *Node* node (pk=10).

    Response::

        {
          "data": {
            "attributes": {
              "append_text": "",
              "input_plugin": "quantumespresso.pw",
              "is_local": false,
              "prepend_text": "",
              "remote_exec_path": "/home/waychal/software/espresso-5.2.0/bin/pw.x"
            }
          },
          "method": "GET",
          "node_type": "nodes",
          "path": "/nodes/10/content/attributes",
          "pk": "10",
          "query_string": {},
          "url": "\http://localhost:5000/nodes/10/content/attributes",
          "url_root": "\http://localhost:5000/"
        }

**Example 2**

    REST url:: \http://localhost:5000/nodes/10/content/attributes?alist=[a1,a2,a3]

    Description::
        returns the list of attributes a1,a2,a3 of *Node* node (pk=10).

    Response::

        {
          "data": {
            "attributes": {
              "a1": ??,
              "a2": ??,
              "a3": ??,
            }
          },
          "method": "GET",
          "node_type": "nodes",
          "path": "/nodes/10/content/attributes",
          "pk": "10",
          "query_string": {
            "alist": [a1,a2,a3]
          },
          "url": "\http://localhost:5000/nodes/10/content/attributes?alist=[a1,a2,a3]",
          "url_root": "\http://localhost:5000/"
        }


**Example 3**

    REST url:: \http://localhost:5000/nodes/10/content/attributes?alist=[-a1,-a2,-a3]

    Description::
        returns the list of attributes a1,a2,a3 of *Node* node (pk=10).

    Response::

        {
          "data": {
            "attributes": {
              "a4": ??,
              "a5": ??,
            }
          },
          "method": "GET",
          "node_type": "nodes",
          "path": "/nodes/10/content/attributes",
          "pk": "10",
          "query_string": {
            "alist": [-a1,-a2,-a3]
          },
          "url": "\http://localhost:5000/nodes/10/content/attributes?alist=[-a1,-a2,-a3]",
          "url_root": "\http://localhost:5000/"
        }


6. Get list of *Node* extras:
------------------------------

This url returns the list of *Node* extras. *Extras* are the additional attributes added
by user. User can filter the list of extras or can request a specific extra of the node.
The URL format is:

    \http://localhost:5000/nodes/(PK)/content/extras?(elist)

Where,
    - PK: Primary key of the *Node*
    - elist: It is a list of extras. There are two ways to specify
             the list of extras. Consider, e1, e2, e3 are the extras.
             1. elist=[e1,e2,e3] : response will contain the list of extras
                                   e1, e2 and e3
             2. elist=[-e1,-e2,-e3] : response will contain the list of all
                                      extras EXCEPT e1, e2 and e3

**Example 1**

    REST url:: \http://localhost:5000/nodes/10/content/extras

    Description::
        returns the list of all extras of *Node* node (pk=10).

    Response::

        {
          "data": {
            "extras": {
              "e1": ??,
              "e2": ??,
              "e3": ??,
              "e4": ??,
              "e5": ??,
              }
          },
          "method": "GET",
          "node_type": "nodes",
          "path": "/nodes/10/content/extras",
          "pk": "10",
          "query_string": {},
          "url": "\http://localhost:5000/nodes/10/content/extras",
          "url_root": "\http://localhost:5000/"
        }

**Example 2**

    REST url:: \http://localhost:5000/nodes/10/content/extras?elist=[e1,e2,e3]

    Description::
        returns the list of extras a1,a2,a3 of *Node* node (pk=10).

    Response::

        {
          "data": {
            "extras": {
              "e1": ??,
              "e2": ??,
              "e3": ??,
            }
          },
          "method": "GET",
          "node_type": "nodes",
          "path": "/nodes/10/content/extras",
          "pk": "10",
          "query_string": {
            "elist": [e1,e2,e3]
          },
          "url": "\http://localhost:5000/nodes/10/content/extras?elist=[e1,e2,e3]",
          "url_root": "\http://localhost:5000/"
        }


**Example 3**

    REST url:: \http://localhost:5000/nodes/10/content/extras?elist=[-e1,-e2,-e3]

    Description::
        returns the list of extras e1,e2,e3 of *Node* node (pk=10).

    Response::

        {
          "data": {
            "extras": {
              "a4": ??,
              "a5": ??,
            }
          },
          "method": "GET",
          "node_type": "nodes",
          "path": "/nodes/10/content/extras",
          "pk": "10",
          "query_string": {
            "elist": [-e1,-e2,-e3]
          },
          "url": "\http://localhost:5000/nodes/10/content/extras?elist=[-e1,-e2,-e3]",
          "url_root": "\http://localhost:5000/"
        }


Calculations
+++++++++++++

*Calculation* is a subtype of the *Node*. So all the *Node* REST urls can also be applied
to the *Calculation* by replacing *nodes* from url with *calculations*. Below are some
examples of *Calculation* REST urls:

1. \http://localhost:5000/calculations?(COLUMN_FILTERS)&(LIMIT)&(OFFSET)&(ORDERBY)

2. \http://localhost:5000/calculations/(PK)

3. \http://localhost:5000/calculations/(PK)/io/inputs?(COLUMN_FILTERS)&(LIMIT)&(OFFSET)&(ORDERBY)

4. \http://localhost:5000/calculations/(PK)/io/outputs?(COLUMN_FILTERS)&(LIMIT)&(OFFSET)&(ORDERBY)

5. \http://localhost:5000/calculations/(PK)/content/attributes?(alist)

6. \http://localhost:5000/calculations/(PK)/content/extras?(elist)

The COLUMN_FILTERS, LIMIT, OFFSET and ORDERBY works same as in *Node*.
If the provided pk is not of type *Calculation*, it gives an error saying
that "given node is not of type Calculation".


Data
++++++

*Data* is a subtype of the *Node*. So all the *Node* REST urls can also be applied
to the *Data* by replacing *nodes* from url with *data*. Below are some
examples of *Data* REST urls:

1. \http://localhost:5000/data?(COLUMN_FILTERS)&(LIMIT)&(OFFSET)&(ORDERBY)

2. \http://localhost:5000/data/(PK)

3. \http://localhost:5000/data/(PK)/io/inputs?(COLUMN_FILTERS)&(LIMIT)&(OFFSET)&(ORDERBY)

4. \http://localhost:5000/data/(PK)/io/outputs?(COLUMN_FILTERS)&(LIMIT)&(OFFSET)&(ORDERBY)

5. \http://localhost:5000/data/(PK)/content/attributes?(alist)

6. \http://localhost:5000/data/(PK)/content/extras?(elist)

The COLUMN_FILTERS, LIMIT, OFFSET and ORDERBY works same as in *Node*.
If the provided pk is not of type *Data*, it gives an error saying
that "given node is not of type Data".


Codes
++++++

*Code* is a subtype of the *Node*. So all the *Node* REST urls can also be applied
to the *Code* by replacing *nodes* from url with *codes*. Below are some
examples of *Code* REST urls:

1. \http://localhost:5000/codes?(COLUMN_FILTERS)&(LIMIT)&(OFFSET)&(ORDERBY)

2. \http://localhost:5000/codes/(PK)

3. \http://localhost:5000/codes/(PK)/io/inputs?(COLUMN_FILTERS)&(LIMIT)&(OFFSET)&(ORDERBY)

4. \http://localhost:5000/codes/(PK)/io/outputs?(COLUMN_FILTERS)&(LIMIT)&(OFFSET)&(ORDERBY)

5. \http://localhost:5000/codes/(PK)/content/attributes?(alist)

6. \http://localhost:5000/codes/(PK)/content/extras?(elist)

The COLUMN_FILTERS, LIMIT, OFFSET and ORDERBY works same as in *Node*.
If the provided pk is not of type *Code*, it gives an error saying
that "given node is not of type Code".

