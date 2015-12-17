.. _ICSD_importer_guide:

######################
ICSD database importer
######################


In this section we explain how to import CIF files from the ICSD
database using the
:py:class:`IcsdDbImporter <aiida.tools.dbimporters.plugins.icsd.IcsdDbImporter>`
class.

Before being able to query ICSD, provided by FIZ Karlsruhe, you should have the intranet database installed on a server (http://www.fiz-karlsruhe.de/icsd_intranet.html). Follow the installation as decsribed in the manual.

It is necessary to know the webpage of the icsd web interface and have access to the full database from the local machine.

You can either query the mysql database or the web page, the latter is restricted to a maximum of 1000 search results, which makes it unsuitable for data mining. So better set up the mysql connection.

Setup
+++++

An instance of the :py:class:`IcsdDbImporter <aiida.tools.dbimporters.plugins.icsd.IcsdDbImporter>` can be created as follows::

    importer = aiida.tools.dbimporters.plugins.icsd.IcsdDbImporter(server="http://ICSDSERVER.com/", host= "127.0.0.1")

Here is a list of the most important input parameters with an
explanation.

For both connection types (web and SQL):

* **server**: address of web interface of the icsd database; it should
  contain both the protocol and the domain name and end with a slash;
  example::

    server = "http://ICSDSERVER.com/"

The following parameters are required only for the mysql query:

* **host**: database host name address.

    .. tip:: If the database is not hosted on your local machine, it can be useful to
      create an ssh tunnel to the 3306 port of the database host::

        ssh -L 3306:localhost:3306 username@icsddbhostname.com

      If you get an URLError with Errno 111 (Connection refused) when
      you query the database, try to use instead::
        
        ssh -L 3306:localhost:3306 -L 8010:localhost:80 username@icsddbhostname.com
        
      The database can then be accessed using "127.0.0.1" as host::

        host = "127.0.0.1"

* **user / pass_wd / db / port**: Login username, password, name of database and port of your mysql database.
    If the standard installation of ICSD intranet version has been followed, the default values should work.
    Otherwise contact your system administrator to get the required information::

        user = "dba", pass_wd = "sql", db = "icsd", port = 3306

Other settings:

* **querydb**: If True (default) the mysql database is queried, otherwise the web page is queried.

A more detailed documentation and additional settings are found under
:py:class:`IcsdDbImporter <aiida.tools.dbimporters.plugins.icsd.IcsdDbImporter>`.


How to do a query
+++++++++++++++++

If the setup worked, you can do your first query::

    cif_nr_list = ["50542","617290","35538"]

    queryresults = importer.query(id= cif_nr_list)

All supported keywords can be obtained using::

    importer.get_supported_keywords()

More information on the keywords are found under
http://www.fiz-karlsruhe.de/fileadmin/be_user/ICSD/PDF/sci_man_ICSD_v1.pdf

A query returns an instance of :py:class:`IcsdSearchResults <aiida.tools.dbimporters.plugins.icsd.IcsdSearchResults>`

The :py:class:`IcsdEntry <aiida.tools.dbimporters.plugins.icsd.IcsdEntry>` at position ``i`` can be accessed using::

    queryresults.at(i)

You can also iterate through all query results::

    for entry in query_results:
        do something

Instances of :py:class:`IcsdEntry <aiida.tools.dbimporters.plugins.icsd.IcsdEntry>` have following methods:

* **get_cif_node()**: Return an instance of :py:class:`CifData <aiida.orm.data.cif.CifData>`, which can be used in an AiiDA workflow.

* **get_aiida_structure()**: Return an AiiDA structure

* **get_ase_structure()**: Return an ASE structure

The most convenient format can be chosen for further processing.


Full example
++++++++++++

Here is a full example how the icsd importer can be used::

    import aiida.tools.dbimporters.plugins.icsd

    cif_nr_list = [
    "50542",
    "617290",
    "35538 ",
    "165226",
    "158366"
    ]

    importer = aiida.tools.dbimporters.plugins.icsd.IcsdDbImporter(server="http://ICSDSERVER.com/",
        host= "127.0.0.1")
    query_results = importer.query(id=cif_nr_list)
    for result in query_results:
        print result.source['db_id']
        aiida_structure = result.get_aiida_structure()
        #do something with the structure


Troubleshooting: Testing the mysql connection
+++++++++++++++++++++++++++++++++++++++++++++

To test your mysql connection, first make sure that you can connect
to the 3306 port of the machine hosting the database.
If the database is not hosted by your local machine,
use the local port tunneling provided by ssh, as follows::

    ssh -L 3306:localhost:3306 username@icsddbhostname.com

.. note:: If you get an URLError with Errno 111 (Connection refused) when
  you query the database, try to use instead::
        
    ssh -L 3306:localhost:3306 -L 8010:localhost:80 username@icsddbhostname.com


.. note:: You need an account on the host machine.
.. note:: There are plenty of explanations online explaining
  how to setup an tunnel over a SSH connection using the ``-L``
  option, just google for it in case you need more information.

Then open a new ``verdi shell`` and type::

    import MySQLdb

    db = MySQLdb.connect(host = "127.0.0.1", user ="dba", passwd = "sql", db = "icsd", port=3306)

If you do not get an error and it does not hang, you have successfully
established your connection to the mysql database.
