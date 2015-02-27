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

      Therefore the database can then be accessed using "127.0.0.1" as host::

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
        print result.source['extras']["cif_nr"]

        aiida_structure = result.get_aiida_structure()

        #do something with the structure


Troubleshooting: Testing the mysql connection
+++++++++++++++++++++++++++++++++++++++++++++

To test your mysql connection, first make sure that you can connect
to the 3306 port of the machine hosting the database.
If the database is not hosted by your local machine,
use the local port tunneling provided by ssh, as follows::

    ssh -L 3306:localhost:3306 username@icsddbhostname.com

.. note:: You need an account on the host machine.
.. note:: There are plenty of explanations online explaining
  how to setup an tunnel over a SSH connection using the ``-L``
  option, just google for it in case you need more information.

Then open a new ``verdi shell`` and type::

    import MySQLdb

    db = MySQLdb.connect(host = "127.0.0.1", user ="dba", passwd = "sql", db = "icsd", port=3306)

If you do not get an error and it does not hang, you have successfully
established your connection to the mysql database.




Low Dimensionality Structure Finder
+++++++++++++++++++++++++++++++++++

In this section we are going to explain you how to extract
low dimensionality structures out of a 3D structure.

The low dimensionality structure finder takes an AiiDA structure
as input and searches for groups of atoms which are only weakly
bonded by van der Waals forces. It can either return the found
structures or a dictionary containing information on dimensionality,
chemical formula, chemical symbols, positions and cell parameters
of the different groups.

.. note:: Structures with different dimensionalities can be found
    in a 3D crystal.

.. note:: The lower dimensionality structure search is stopped when
    all atoms of the original structure have been attributed to a group of atoms.

Setup
+++++

The most important parameters to set up the LowDimFinder

* **cov_bond_margin**: The criterium which defines if atoms are bonded or not.
    The margin is percentage which is added to the covalent
    bond length. (default: 0.16)

* **vacuum_space**: The amount of empty space which is added around the lower
    dimensionality structures.

* **rotation**: If True, 2D structures are rotated into xy-plane and 1D structures
    oriented along z-axis. (default: False)


More infomation and settings is found under :py:class:`LowDimFinder <aiida.tools.lowdimfinder.LowDimFinder>`

Example
+++++++

In this example first a layered graphite AiiDA structure is manually defined, which is then analysed with the low dimensionality structure finder::

    import aiida.tools.lowdimfinder

    #define the positions, the chemical symbols, and the cell of graphite
    positions =   ((1.06085029e-16,   1.83744660e-16,   1.73250000e+00),
                    (3.18255087e-16,   5.51233980e-16,   5.19750000e+00),
                    (3.28129634e-16,   1.42591256e+00,   1.73250000e+00),
                    (1.23500000e+00,   7.13170188e-01,   5.19750000e+00))

    chemical_symbols = ['C', 'C', 'C', 'C']

    cell = [[  2.47000000e+00,   0.00000000e+00,   0.00000000e+00],
       [ -1.23500000e+00,   2.13908275e+00,   0.00000000e+00],
       [  4.24340116e-16,   7.34978640e-16,   6.93000000e+00]]

    #build a graphite AiiDA structure
    StructureData = DataFactory("structure")
    aiida_graphite = StructureData(cell=cell)

    for idx, symbol in enumerate(chemical_symbols):
        aiida_graphite.append_atom(position=positions[idx],symbols=symbol)

    #pass the structure to the LowDimFinder
    low_dim_finder = aiida.tools.lowdimfinder.LowDimFinder(aiida_structure = aiida_graphite)

    #analyse the structure and store the layers
    graphene_layers = low_dim_finder.get_reduced_aiida_structures()

    #print the dimensionality of the two layers, which should be as expected [2,2]
    print low_dim_finder.get_group_data()["dimensionality"]



Example 2 with ICSD importer
++++++++++++++++++++++++++++

The low dimensionality structure finder can be combined with the
:py:class:`IcsdDbImporter <aiida.tools.dbimporters.plugins.icsd.IcsdDbImporter>`::

    import aiida.tools.lowdimfinder
    import aiida.tools.dbimporters.plugins.icsd

    # A selection of layered structures
    cif_list = ["617290","35538", "152836", "626809", "647260","280850"]

    # ICSDSERVER.com should be replaced by the server domain name
    # and a mysql connection to the database should be set up.

    importer = aiida.tools.dbimporters.plugins.icsd.IcsdDbImporter(server="http://ICSDSERVER.com", host= "127.0.0.1")

    query_results = importer.query(id=cif_list)

    for i in query_results:

        aiida_structure = i.get_aiida_structure()

        low_dim_finder = aiida.tools.lowdimfinder.LowDimFinder(aiida_structure = aiida_structure)

        groupdata = low_dim_finder.get_group_data()

        print i.source['extras']["cif_nr"], groupdata["dimensionality"]












