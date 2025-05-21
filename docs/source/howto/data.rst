.. _how-to:data:

*********************
How to work with data
*********************


.. _how-to:data:import:

Importing data
==============

AiiDA allows users to export data from their database into an export archive file, which can be imported into any other AiiDA database.
If you have an AiiDA export archive that you would like to import, you can use the ``verdi archive import`` command (see :ref:`the reference section<reference:command-line:verdi-archive>` for details).

.. note:: For information on exporting and importing data via AiiDA archives, see :ref:`"How to share data"<how-to:share:archives>`.

If, instead, you have existing data that are not yet part of an AiiDA export archive, such as files, folders, tabular data, arrays or any other kind of data, this how-to guide will show you how to import them into AiiDA.

To store any piece of data in AiiDA, it needs to be wrapped in a :py:class:`~aiida.orm.Data` node, such that it can be represented in the :ref:`provenance graph <topics:provenance>`.
There are different varieties, or subclasses, of this ``Data`` class that are suited for different types of data.
AiiDA ships with a number of built-in data types.
You can list these using the :ref:`verdi plugin<reference:command-line:verdi-plugin>` command.
Executing ``verdi plugin list aiida.data`` should display something like::

    Registered entry points for aiida.data:
    * core.array
    * core.bool
    * core.code
    * core.dict
    * core.float
    * core.folder
    * core.list
    * core.singlefile

    Info: Pass the entry point as an argument to display detailed information

As the output suggests, you can get more information about each type by appending the name to the command, for example, ``verdi plugin list aiida.data singlefile``::

    Description:

    The ``singlefile`` data type is designed to store a single file in its entirety.
    A ``singlefile`` node can be created from an existing file on the local filesystem in two ways.
    By passing the absolute path of the file:

        singlefile = SinglefileData(file='/absolute/path/to/file.txt')

    or by passing a filelike object:

        with open('/absolute/path/to/file.txt', 'rb') as handle:
            singlefile = SinglefileData(file=handle)

    The filename of the resulting file in the database will be based on the filename passed in the ``file`` argument.
    This default can be overridden by passing an explicit name for the ``filename`` argument to the constructor.

As you can see, the ``singlefile`` type corresponds to the :py:class:`~aiida.orm.nodes.data.singlefile.SinglefileData` class and is designed to wrap a single file that is stored on your local filesystem.
If you have such a file that you would like to store in AiiDA, you can use the ``verdi shell`` to create it:

.. code-block:: python

    SinglefileData = DataFactory('core.singlefile')
    singlefile = SinglefileData(file='/absolute/path/to/file.txt')
    singlefile.store()

The first step is to load the class that corresponds to the data type, which you do by passing the name (listed by ``verdi plugin list aiida.data``) to the :py:class:`~aiida.plugins.factories.DataFactory`.
Then we just construct an instance of that class, passing the file of interest as an argument.

.. note:: The exact manner of constructing an instance of any particular data type is type dependent.
    Use the ``verdi plugin list aiida.data <ENTRY_POINT>`` command to get more information for any specific type.

Note that after construction, you will get an *unstored* node.
This means that at this point your data is not yet stored in the database and you can first inspect it and optionally modify it.
If you are happy with the results, you can store the new data permanently by calling the :py:meth:`~aiida.orm.nodes.node.Node.store` method.
Every node is assigned a Universal Unique Identifier (UUID) upon creation and once stored it is also assigned a primary key (PK), which can be retrieved through the ``node.uuid`` and ``node.pk`` properties, respectively.
You can use these identifiers to reference and or retrieve a node.
Ways to find and retrieve data that have previously been imported are described in section :ref:`"How to find data"<how-to:query>`.

If none of the currently available data types, as listed by ``verdi plugin list``, seem to fit your needs, you can also create your own custom type.
For details refer to the next section :ref:`"How to add support for custom data types"<topics:data_types:plugin>`.

.. _how-to:data:dump:

Dumping data to disk
====================

Process dumping
---------------

.. versionadded:: 2.6

It is now possible to dump your executed workflows to disk in a hierarchical directory tree structure. This can be
particularly useful if one is not yet familiar with AiiDA's CLI endpoints and Python API to explore the data (such as
the ``QueryBuilder``) or one just wants to quickly explore input/output files
using existing shell scripts or common terminal utilities, such as ``grep``.
For one of our beloved ``MultiplyAddWorkChain``s, (PK=29) we run the ``verdi process dump`` command to obtain the following:

.. code-block:: shell

    $ verdi process dump 29

    Warning: This is a new feature which is still in its testing phase. If you encounter unexpected behavior or bugs, please report them via Discourse or GitHub.
    Report: No output path specified. Using default: `<my-pwd>/MultiplyAddWorkChain-29`
    Report: No config file found. Using command-line arguments.
    Report: Starting dump of process node (PK: 29) in `incremental` mode.
    Report: Saving final dump log and configuration.
    Success: Raw files for process `29` dumped into folder `MultiplyAddWorkChain-29`.
    Success: Raw files for WorkChainNode <pk> dumped into folder `dump-multiply_add`.

And the output directory tree:

.. code-block:: shell

    $ tree -a MultiplyAddWorkChain-29/
    MultiplyAddWorkChain-29
    ├── .aiida_dump_safeguard
    ├── .aiida_node_metadata.yaml
    ├── 01-multiply-30
    │  ├── .aiida_dump_safeguard
    │  ├── .aiida_node_metadata.yaml
    │  └── inputs
    │     └── source_file
    ├── 02-ArithmeticAddCalculation-32
    │  ├── .aiida_dump_safeguard
    │  ├── .aiida_node_metadata.yaml
    │  ├── inputs
    │  │  ├── .aiida
    │  │  │  ├── calcinfo.json
    │  │  │  └── job_tmpl.json
    │  │  ├── _aiidasubmit.sh
    │  │  └── aiida.in
    │  └── outputs
    │     ├── _scheduler-stderr.txt
    │     ├── _scheduler-stdout.txt
    │     └── aiida.out
    ├── aiida_dump_config.yaml
    ├── aiida_dump_log.json
    └── README.md

The ``README.md`` file provides a description of the directory structure, as well as useful information about the
top-level process.
The ``.aiida_dump_safeguard`` file is used to mark directories created by the dumping command to avoid accidental
cleaning of wrong directories, the ``aiida_dump_config.yaml`` file contains the
configuration for the command execution (provided via the CLI arguments), and the ``aiida_dump_log.json`` file logging
information about the dump (both files explained further below).

In the output directory, numbered subdirectories are created for each step of the workflow, resulting in the
``01-multiply-30`` and ``02-ArithmeticAddCalculation-32`` folders, where the prefixes denote the step in the workflow,
and the appendices are given by the ``ProcessNode`` PKs.
The raw calculation input and output files ``aiida.in`` and ``aiida.out`` of the ``ArithmeticAddCalculation`` are placed
in ``inputs`` and ``outputs``.
In addition, these also contain the submission script ``_aiidasubmit.sh``, as well as the scheduler stdout and stderr,
``_scheduler-stdout.txt`` and ``_scheduler-stderr.txt``, respectively.
Lastly, the source code of the ``multiply`` ``calcfunction`` presenting the first step of the workflow is contained in
the ``source_file``.
Since child processes are explored recursively, arbitrarily complex, nested workflows can be dumped.
Upon having a closer look at the directory, we also find the hidden ``.aiida_node_metadata.yaml`` files, which are
created for every ``ProcessNode`` and contain additional information about the ``Node``, the ``User``, and the
``Computer``, as well as the ``.aiida`` subdirectory with machine-readable
AiiDA-internal data in JSON format.

Further, the ``-p`` flag allows to specify a custom dumping path, and, as seen above, if none is provided, it is
automatically generated from either the node ``label``, the ``process_label``, or ``process_type`` (based
on availability, in that order) and the ``pk``.
By default, the command is run in ``incremental`` mode, meaning that files are gradually added to an existing directory.
The behavior can be changed either via the ``-n/--dry-run`` flag, or the ``-o/--overwrite`` option to fully overwrite
the existing dump target directory.
Further, only sealed processes nodes are dumped by default, however, the behavior can be changed with the
``--dump-unsealed`` flag.
This can be useful in conjunction with ``--incremental`` to gradually retrieve data while a process is still running.
Furthermore, the ``-f/--flat`` flag can be used to dump all files for each ``CalculationNode`` of the workflow in a flat
directory structure (the internal hierarchy of files stored in ``FolderData`` or ``RemoteData`` nodes is persisted,
though), and the ``--include-inputs/--exclude-inputs`` (``--include-outputs/--exclude-outputs``) flags can be
used to also dump additional node inputs (outputs) of each ``CalculationNode`` of the workflow into ``node_inputs``
(``node_outputs``) subdirectories.


Group Dumping
-------------

.. versionadded:: 2.7

The functionality has recently been expanded to also dump data contained in groups, which can be achieved via:

.. code-block:: shell

    verdi group dump <group-identifier>

This command will create a directory structure with all processes contained in the specified group. For example:

.. code-block:: shell

    $ verdi group dump my-calculations
    Warning: This is a new feature which is still in its testing phase. If you encounter unexpected behavior or bugs, please report them via Discourse or GitHub.
    Report: No output path specified. Using default: `<my-pwd>/my-calculations`
    Report: No config file found. Using command-line arguments.
    Report: Starting dump of group `my-calculations` (PK: 1) in `incremental` mode.
    Report: Dumping 1 nodes for group 'my-calculations'
    Report: Saving final dump log and configuration.
    Success: Raw files for group `my-calculations` dumped into folder `my-calculations`.

Will result in the following output directory:

.. code-block:: shell

    $ tree -a my-calculations/
    my-calculations
    ├── .aiida_dump_safeguard
    ├── aiida_dump_config.yaml
    ├── aiida_dump_log.json
    └── calculations
        └── ArithmeticAddCalculation-4
            ├── .aiida_dump_safeguard
            ├── .aiida_node_metadata.yaml
            ├── inputs
            │  ├── .aiida
            │  │  ├── calcinfo.json
            │  │  └── job_tmpl.json
            │  ├── _aiidasubmit.sh
            │  └── aiida.in
            └── outputs
                ├── _scheduler-stderr.txt
                ├── _scheduler-stdout.txt
                └── aiida.out

And similarly for a group ``my-workflows`` with a ``MultiplyAddWorkChain``:

.. code-block:: shell

    $ verdi group dump my-workflows
    Warning: This is a new feature which is still in its testing phase. If you encounter unexpected behavior or bugs, please report them via Discourse or GitHub.
    Report: No output path specified. Using default: `/home/geiger_j/aiida_projects/verdi-profile-dump/dev-dumps/docs/my-workflows`
    Report: No config file found. Using command-line arguments.
    Report: Starting dump of group `my-workflows` (PK: 2) in `incremental` mode.
    Report: Dumping 1 nodes for group 'my-workflows'
    Report: Saving final dump log and configuration.
    Success: Raw files for group `my-workflows` dumped into folder `my-workflows`.

And the following output directory:

.. code-block:: shell

    $ tree -a my-workflows/
    my-workflows
    ├── .aiida_dump_safeguard
    ├── aiida_dump_config.yaml
    ├── aiida_dump_log.json
    └── workflows
        └── MultiplyAddWorkChain-11
            ├── .aiida_dump_safeguard
            ├── .aiida_node_metadata.yaml
            ├── 01-multiply-12
            │  ├── .aiida_dump_safeguard
            │  ├── .aiida_node_metadata.yaml
            │  └── inputs
            │     └── source_file
            └── 02-ArithmeticAddCalculation-14
                ├── .aiida_dump_safeguard
                ├── .aiida_node_metadata.yaml
                ├── inputs
                │  ├── .aiida
                │  │  ├── calcinfo.json
                │  │  └── job_tmpl.json
                │  ├── _aiidasubmit.sh
                │  └── aiida.in
                └── outputs
                    ├── _scheduler-stderr.txt
                    ├── _scheduler-stdout.txt
                    └── aiida.out

The ``.aiida_dump_safeguard`` and ``aiida_dump_config.yaml`` files serve the same purposes as mentioned above.
Here, the latter file can be particularly helpful if a ``dump`` command is run multiply times to ensure the same
configuration options for the dumping operation are re-used, as the command automatically looks for the existence of
this file.
In effect, this successive usage of (any) ``verdi dump`` command allows one to incrementally populate the given ``dump``
output directory, while data is created by AiiDA.

To keep track of the dumping progress, the ``aiida_dump_log.json`` contains the dumped ``calculations``, ``workflows``,
``groups`` and ``data`` (to be implemented), including the dump path, possible symlinks, duplicate output directories,
and the directory ``mtime`` and size, the dumping time, as well as the groups-to-nodes and nodes-to-groups mapping after
every ``dump`` operation.
E.g., after dumping the ``my-calculations`` group, it contains the following content:

.. code-block:: json

    {
        "calculations": {
            "71d69fc2-a911-4715-9151-dcc422691fbd": {
                "path": "calculations/ArithmeticAddCalculation-4",
                "symlinks": [],
                "duplicates": [],
                "dir_mtime": "2025-05-21T09:23:59.008399+00:00",
                "dir_size": 2890
            }
        },
        "workflows": {},
        "groups": {
            "2c7e0144-c7fe-4b5c-9d64-4c4315332861": {
                "path": ".",
                "symlinks": [],
                "duplicates": [],
                "dir_mtime": "2025-05-21T09:23:59.008399+00:00",
                "dir_size": 2890
            }
        },
        "data": {},
        "last_dump_time": "2025-05-21T11:23:58.880261+02:00",
        "group_node_mapping": {
            "group_to_nodes": {
                "2c7e0144-c7fe-4b5c-9d64-4c4315332861": [
                    "71d69fc2-a911-4715-9151-dcc422691fbd"
                ],
                "20e93a51-f3ef-46d0-a69f-5626064ff69a": [
                    "407a6751-5f7c-48b8-b945-d48a5f48a883"
                ]
            },
            "node_to_groups": {
                "71d69fc2-a911-4715-9151-dcc422691fbd": [
                    "2c7e0144-c7fe-4b5c-9d64-4c4315332861"
                ],
                "407a6751-5f7c-48b8-b945-d48a5f48a883": [
                    "20e93a51-f3ef-46d0-a69f-5626064ff69a"
                ]
            }
        }
    }

If one then runs a new ``ArthmeticAddCalculation``, adds it to the ``my-calculations`` group, and executes ``verdi group
dump my-calculations`` command, one obtains:

.. code-block:: shell

    $ verdi group dump my-calculations
    Warning: This is a new feature which is still in its testing phase. If you encounter unexpected behavior or bugs, please report them via Discourse or GitHub.
    Report: No output path specified. Using default: `<my-pwd>/my-calculations`
    Report: Config file found at 'my-calculations/aiida_dump_config.yaml'.
    Report: Using config file settings ONLY (ignoring other CLI flags).
    Report: Starting dump of group `my-calculations` (PK: 1) in `incremental` mode.
    Report: Processing group changes...
    Report: Processing 1 modified groups (membership): ['my-calculations']
    Report: Dumping 1 nodes for group 'my-calculations'
    Report: Saving final dump log and configuration.
    Success: Raw files for group `my-calculations` dumped into folder `my-calculations`.

As evident from the report, the command automatically found and used the configuration file created at the end of the
previous dump operation, thus keeping the state of successive runs consistent.
It further picked up that only a single new node was added to the ``my-calculations`` group since the last execution and dumped it.

In addition to the options for dumping individual processes, the ``verdi group dump`` command provides further
configuration options, e.g., to apply various time filters via ``-p/--past-days``, ``--start-date``, ``--end-date``, and
``--filter-by-last-dump-time``, as well as changes to the output directory structure.
For the latter, the ``--only-top-level-calcs`` and ``--only-top-level-workflows`` flags dictate
if data of calculations/workflows called by other processes should be dumped again in their own dedicated directories
(in addition to being explicitly part of the output directory of the top-level workflow).
To avoid data duplication, both flags are true by default, however, if a sub-calculation/workflow has been explicitly
added to a group, this filtering is circumvented, and a dedicated directory is created for the given
sub-calculation/workflow.
In the case that the configuration would lead to sub-calculations/workflows being dumped more than once, the
``--symlink-calcs`` flag can be used to instead symlink from the dedicated dump-directories of the given sub-processes
to the top-level workflow dump directory, avoiding data duplication.
Finally, with the ``--delete-missing`` flag, dump output directories of nodes that were previously dumped but have since
been removed from AiiDA's database are cleaned, as well as their entries removed from the log JSON file.
As the ``dump`` commands intend to mirror AiiDA's internal data state, this flag is true by default.


Profile Dumping
---------------

.. versionadded:: 2.7

Going even further, you can now also dump the data from an entire AiiDA profile to disk.
To avoid initiating the ``dump`` operation for possibly very large databases, if no options are provided, no data is being dumped:

.. code-block:: shell

    $ verdi profile dump
    Warning: This is a new feature which is still in its testing phase. If you encounter unexpected behavior or bugs, please report them via Discourse or GitHub.
    Report: No output path specified. Using default: '<my-pwd>/my-profile'
    Report: No config file found. Using command-line arguments.
    Warning: No specific data selection determined from config file or CLI arguments.
    Warning: Please specify `--all` to dump all profile data or filters such as `groups`, `user`, etc.
    Warning: Use `--help` for all options and `--dry-run` to preview.
    Report: Starting dump of profile `docs` in `incremental` mode.
    Report: No changes detected since last dump and not dumping ungrouped. Nothing to do.
    Report: Saving final dump log and configuration.

Instead, if all data of the profile should be dumped, use the ``--all`` flag, or select a subset of your AiiDA data
using ``--groups``, ``--user``, filters, one of the various time-based filter options the command provides (see above).

If we run with ``--all`` on our current profile, we get the following result:

.. code-block:: shell

    $ verdi profile dump --all
    Warning: This is a new feature which is still in its testing phase. If you encounter unexpected behavior or bugs, please report them via Discourse or GitHub.
    Report: No output path specified. Using default: '<my-pwd>/my-profile'
    Report: No config file found. Using command-line arguments.
    Report: Starting dump of profile `my-profile` in `incremental` mode.
    Report: Processing group changes...
    Report: Processing 2 new or modified groups: ['my-calculations', 'my-workflows']
    Report: Dumping 1 nodes for group 'my-calculations'
    Report: Dumping 1 nodes for group 'my-workflows'
    Report: Saving final dump log and configuration.
    Success: Raw files for profile `my-profile` dumped into folder `my-profile`.

The resulting directory preserves the group organization:

.. code-block:: shell

    $ tree -a my-profile/
    my-profile
    ├── .aiida_dump_safeguard
    ├── aiida_dump_config.yaml
    ├── aiida_dump_log.json
    └── groups
        ├── my-calculations
        │  ├── .aiida_dump_safeguard
        │  └── calculations
        │     └── ArithmeticAddCalculation-4
        │        ├── .aiida_dump_safeguard
        │        ├── .aiida_node_metadata.yaml
        │        ├── inputs
        │        │  ├── .aiida
        │        │  │  ├── calcinfo.json
        │        │  │  └── job_tmpl.json
        │        │  ├── _aiidasubmit.sh
        │        │  └── aiida.in
        │        └── outputs
        │           ├── _scheduler-stderr.txt
        │           ├── _scheduler-stdout.txt
        │           └── aiida.out
        └── my-workflows
            ├── .aiida_dump_safeguard
            └── workflows
                └── MultiplyAddWorkChain-11
                    ├── .aiida_dump_safeguard
                    ├── .aiida_node_metadata.yaml
                    ├── 01-multiply-12
                    │  ├── .aiida_dump_safeguard
                    │  ├── .aiida_node_metadata.yaml
                    │  └── inputs
                    │     └── source_file
                    └── 02-ArithmeticAddCalculation-14
                    ├── .aiida_dump_safeguard
                    ├── .aiida_node_metadata.yaml
                    ├── inputs
                    │  ├── .aiida
                    │  │  ├── calcinfo.json
                    │  │  └── job_tmpl.json
                    │  ├── _aiidasubmit.sh
                    │  └── aiida.in
                    └── outputs
                        ├── _scheduler-stderr.txt
                        ├── _scheduler-stdout.txt
                        └── aiida.out

Finally, in addition to the configuration of process and group dumping, the ``verdi profile dump`` provides again a few
additional options, most importantly,
``--organize-by-groups`` to toggle if AiiDA's internal data organization by groups
should be preserved in the dump output directory (defaults to true),
``--also-ungrouped`` if also nodes that are not organized by groups should be included in the selected set for dumping
(defaults to false),
``--relabel-groups`` if relabelling of groups in AiiDA's DB has taken place since the last dumping operation, and the
changes should be reflected in the dumping output directory and the log JSON file (this is a separate option and not
done by default, as it requires verification of the group structure and dump organization, and can therefore be
computationally demanding).


Python API
----------

The dump functionality is also available through a Python API:

.. code-block:: python

    # Dump a single process
    from aiida import orm, load_profile
    from aiida.tools.dumping import ProcessDumper, GroupDumper, ProfileDumper

    load_profile()
    process_node = orm.load_node(4)  # ArithmeticAddCalculation node
    process_dumper = ProcessDumper(process_node=process_node)
    process_dumper.dump()

    # Dump a group
    group = orm.load_group('my-calculations')
    group_dumper = GroupDumper(group=group)
    group_dumper.dump()

    # Dump all data in the default profile
    profile_dumper = ProfileDumper()
    profile_dumper.config.all_entries = True
    profile_dumper.dump()


Usage Scenarios
---------------

The data dumping functionality was designed to bridge the gap between research conducted with AiiDA and scientists not familiar with AiiDA. Some common use cases include:

1. Sharing simulation results with collaborators who don't use AiiDA
2. Periodically running the ``dump`` command to mirror changes to a local directory while working on an AiiDA project
3. Analyzing data using traditional shell tools outside of AiiDA's programmatic approach (e.g., for beginners not yet
   familiar with AiiDA's API)

.. _how-to:data:import:provenance:

Provenance
----------

While AiiDA will automatically keep the provenance of data that is created by it through calculations and workflows, this is clearly not the case when creating data nodes manually, as described in the previous section.
Typically, the manual creation of data happens at the beginning of a project when data from external databases is imported as a starting point for further calculations.
To still keep some form of provenance, the :class:`~aiida.orm.Data` base class allows to record the _source_ of the data it contains.
When constructing a new data node, of any type, you can pass a dictionary with information of the source under the ``source`` keyword argument:

.. code-block:: python

    data = Data(source={'uri': 'http://some.domain.org/files?id=12345', 'id': '12345'})

Once stored, this data can always be retrieved through the ``source`` property:

.. code-block:: python

    data.source   # Will return the ``source`` dictionary that was passed in the constructor, if any

The following list shows all the keys that are allowed to be set in the ``source`` dictionary:

* ``db_name``: The name of the external database.
* ``db_uri``: The base URI of the external database.
* ``uri``: The exact URI of where the data can be retrieved. Ideally this is a persistent URI.
* ``id``: The external ID with which the data is identified in the external database.
* ``version``: The version of the data, if any.
* ``extras``: Optional dictionary with other fields for source description.
* ``source_md5``: MD5 checksum of the data.
* ``description``: Human-readable free form description of the data's source.
* ``license``: A string with the type of license that applies to the data, if any.

If any other keys are defined, an exception will be raised by the constructor.


.. _how-to:data:organize:

Organizing data
===============

.. _how-to:data:organize:group:

How to group nodes
------------------

AiiDA's database is great for automatically storing all your data, but sometimes it can be tricky to navigate this flat data store.
To create some order in this mass of data, you can *group* sets of nodes together, just as you would with files in folders on your filesystem.
A folder, in this analogy, is represented by the :py:class:`~aiida.orm.groups.Group` class.
Each group instance can hold any amount of nodes and any node can be contained in any number of groups.
A typical use case is to store all nodes that share a common property in a single group.

Below we show how to perform a typical set of operations one may want to perform with groups.

Create a new group
^^^^^^^^^^^^^^^^^^

From the command line interface:

.. code-block:: console

    $ verdi group create test_group

From the Python interface:

.. code-block:: ipython

    In [1]: group = Group(label='test_group')

    In [2]: group.store()
    Out[2]: <Group: "test_group" [type core], of user xxx@xx.com>


List available groups
^^^^^^^^^^^^^^^^^^^^^

Example:

.. code-block:: console

    $ verdi group list

Groups come in different types, indicated by their type string.
By default ``verdi group list`` only shows groups of the type *core*.
In case you want to show groups of another type use ``-T/--type-string`` option.
If you want to show groups of all types, use the ``-a/--all-types`` option.

For example, to list groups of type ``core.auto``, use:

.. code-block:: console

    $ verdi group list -T core.auto

Similarly, we can use the ``type_string`` key to filter groups with the ``QueryBuilder``:

.. code-block:: ipython

    In [1]: QueryBuilder().append(Group, filters={'type_string': 'core'}).all(flat=True)
    Out[1]:
    [<Group: "another_group" [type core], of user xxx@xx.com>,
    <Group: "old_group" [type core], of user xxx@xx.com>,
    <Group: "new_group" [type core], of user xxx@xx.com>]

Add nodes to a group
^^^^^^^^^^^^^^^^^^^^
Once the ``test_group`` has been created, we can add nodes to it.
For example, to add a node with ``pk=1`` to the group we could either use the command line interface:

.. code-block:: console

    $ verdi group add-nodes -G test_group 1
    Do you really want to add 1 nodes to Group<test_group>? [y/N]: y

Or the Python interface:

.. code-block:: ipython

    In [1]: group.add_nodes(load_node(pk=1))

Show information about a group
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
From the command line interface:

.. code-block:: console

    $ verdi group show test_group

    -----------------  ----------------
    Group label        test_group
    Group type_string  user
    Group description  <no description>
    -----------------  ----------------
    # Nodes:
    PK    Type    Created
    ----  ------  ---------------
     1    Code    26D:21h:45m ago

Remove nodes from a group
^^^^^^^^^^^^^^^^^^^^^^^^^
From the command line interface:

.. code-block:: console

    $ verdi group remove-nodes -G test_group 1
    Do you really want to remove 1 nodes from Group<test_group>? [y/N]: y

From the Python interface:

.. code-block:: ipython

    In [1]: group = load_group(label='test_group')

    In [2]: group.remove_nodes([load_node(1)])

Alternatively, you might want to remove *all* nodes from the group.
In the command line you just need to add ``-c/--clear`` option to ``verdi group remove-nodes ..``

.. code-block:: console

    $ verdi group remove-nodes -c -G test_group
    Do you really want to remove ALL the nodes from Group<test_group>? [y/N]:

In the Python interface you can use ``.clear()`` method to achieve the same goal:

.. code-block:: ipython

    In [1]: group = load_group(label='test_group')

    In [2]: group.clear()


Rename a group
^^^^^^^^^^^^^^
From the command line interface:

.. code-block:: console

      $ verdi group relabel test_group old_group
      Success: Label changed to old_group

From the Python interface:

.. code-block:: ipython

    In [1]: group = load_group(label='old_group')

    In [2]: group.label = 'another_group'


Delete a group
^^^^^^^^^^^^^^
From the command line interface:

.. code-block:: console

      $ verdi group delete another_group
      Are you sure to delete Group<another_group>? [y/N]: y
      Success: Group<another_group> deleted.

Any deletion operation related to groups, by default, will not affect the nodes themselves.
For example if you delete a group, the nodes that belonged to the group will remain in the database.
The same happens if you remove nodes from the group -- they will remain in the database but won't belong to the group anymore.

If you also wish to delete the nodes, when deleting the group, use the ``--delete-nodes`` option:

.. code-block:: console

      $ verdi group delete another_group --delete-nodes

Copy one group into another
^^^^^^^^^^^^^^^^^^^^^^^^^^^
This operation will copy the nodes of the source group into the destination group.
If the destination group does not yet exist, it will be created automatically.

From the command line interface:

.. code-block:: console

    $ verdi group copy source_group dest_group
    Success: Nodes copied from group<source_group> to group<dest_group>

From the Python interface:

.. code-block:: ipython

    In [1]: src_group = Group.collection.get(label='source_group')

    In [2]: dest_group = Group(label='destination_group').store()

    In [3]: dest_group.add_nodes(list(src_group.nodes))


Examples for using groups
-------------------------

In this section, we will provide some practical examples of how one can use Groups to structure and organize the nodes in the database.

.. _how-to:data:group-similar:

Group structures with a similar property
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Suppose, we wanted to group all structures for which the computed bandgap is higher than ``1.0 eV`` in a group named ``promising_structures``, one could use the following approach:

.. code-block:: python

    # Finding the structures with the bandgap > 1.0.
    qb = QueryBuilder()
    qb.append(StructureData,  tag='structure', project='*') # Here we are projecting the entire structure object
    qb.append(CalcJobNode, with_incoming='structure', tag='calculation')
    qb.append(Dict, with_incoming='calculation', filters={'attributes.bandgap': {'>': 1.0}})

    # Adding the structures in 'promising_structures' group.
    group = load_group(label='promising_structures')
    group.add_nodes(q.all(flat=True))

.. note::

    Any node can be included in a group only once and if it is added again, it is simply ignored.
    This means that add_nodes can be safely called multiple times, and only nodes that weren't already part of the group, will be added.


Use grouped data for further processing
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Here we demonstrate how to submit calculations for structures that all belong to a group named ``promising_structures``:

.. code-block:: python

    # Querying the structures that belong to the 'promising_structures' group.
    qb = QueryBuilder()
    qb.append(Group, filters={'label': 'promising_structures'}, tag='group')
    qb.append(StructureData, with_group='group')

    # Submitting the simulations.
    for structure in qb.all(flat=True):
        builder = SomeWorkChain.get_builder()
        builder.structure = structure
        ...
        submit(builder)

Note, however, that one can also use ``group.nodes`` to access the nodes of the group.
To achieve the same result as above one would need to do something as follows:

.. code-block:: python

    group = load_group(label='promising_structures')

    # Here make sure to include only structures, as group can contain any nodes.
    structures = [node for node in group.nodes if isinstance(node, StructureData)]
    for structure in structures:
        builder = SomeWorkChain.get_builder()
        builder.structure = structure
        ...
        submit(builder)


To find all structures that have a property ``property_a`` with a value lower than ``1`` and also belong to the ``promising_structures`` group, one could build a query as follows:

.. code-block:: python

    qb = QueryBuilder()
    qb.append(Group, filters={'label': 'promising_structures'}, tag='group')
    qb.append(StructureData, with_group='group', tag='structure', project='*')
    qb.append(SomeWorkChain, with_incoming='structure', tag='calculation')
    qb.append(Dict, with_incoming='calculation', filters={'attributes.property_a': {'<': 1}})

The return value of ``qb.all(flat=True)`` would contain all the structures matching the above mentioned criteria.

.. _how-to:data:organize:grouppath:

Organise groups in hierarchies
------------------------------

.. meta::
   :keywords: grouppath

Groups in AiiDA are inherently "flat", in that groups may only contain nodes and not other groups.
However it is possible to construct *virtual* group hierarchies based on delimited group labels, using the :py:class:`~aiida.tools.groups.paths.GroupPath` utility.

:py:class:`~aiida.tools.groups.paths.GroupPath` is designed to work in much the same way as Python's :py:class:`pathlib.Path`, whereby paths are denoted by forward slash characters '/' in group labels.

For example say we have the groups:

.. code-block:: console

    $ verdi group list

    PK    Label                    Type string    User
    ----  -----------------        -------------  --------------
    1     base1/sub_group1         core           user@email.com
    2     base1/sub_group2         core           user@email.com
    3     base2/other/sub_group3   core           user@email.com

We can also access them from the command-line as:

.. code-block:: console

    $ verdi group path ls -l
    Path         Sub-Groups
    ---------  ------------
    base1                 2
    base2                 1
    $ verdi group path ls base1
    base1/sub_group1
    base1/sub_group2

Or from the python interface:

.. code-block:: ipython

    In [1]: from aiida.tools.groups import GroupPath
    In [2]: path = GroupPath("base1")
    In [3]: print(list(path.children))
    Out[3]: [GroupPath('base1/sub_group2', cls='<class 'aiida.orm.groups.Group'>'),
             GroupPath('base1/sub_group1', cls='<class 'aiida.orm.groups.Group'>')]

The ``GroupPath`` can be constructed using indexing or "divisors":

.. code-block:: ipython

    In [4]: path = GroupPath()
    In [5]: path["base1"] == path / "base1"
    Out[5]: True

Using the :py:func:`~aiida.tools.groups.paths.GroupPath.browse` attribute, you can also construct the paths as preceding attributes.
This is useful in interactive environments, whereby available paths will be shown in the tab-completion:

.. code-block:: ipython

    In [6]: path.browse.base1.sub_group2()
    Out[6]: GroupPath('base1/sub_group2', cls='<class 'aiida.orm.groups.Group'>')

To check the existence of a path element:

.. code-block:: ipython

    In [7]: "base1" in path
    Out[7]: True

A group may be "virtual", in which case its label does not directly relate to a group, or the group can be retrieved with the :py:func:`~aiida.tools.groups.paths.GroupPath.get_group` method:

.. code-block:: ipython

    In [8]: path.is_virtual
    Out[8]: True
    In [9]: path.get_group() is None
    Out[9]: True
    In [10]: path["base1/sub_group1"].is_virtual
    Out[10]: False
    In [11]: path["base1/sub_group1"].get_group()
    Out[11]: <Group: "base1/sub_group1" [type core], of user user@email.com>

Groups can be created and destroyed:

.. code-block:: ipython

    In [12]: path["base1/sub_group1"].delete_group()
    In [13]: path["base1/sub_group1"].is_virtual
    Out[13]: True
    In [14]: path["base1/sub_group1"].get_or_create_group()
    Out[14]: (<Group: "base1/sub_group1" [type core], of user user@email.com>, True)
    In [15]: path["base1/sub_group1"].is_virtual
    Out[15]: False

To traverse paths, use the :py:func:`~aiida.tools.groups.paths.GroupPath.children` attribute - for recursive traversal, use :py:func:`~aiida.tools.groups.paths.GroupPath.walk`:

.. code-block:: ipython

    In [16]: for subpath in path.walk(return_virtual=False):
        ...:     print(subpath)
        ...:
    GroupPath('base1/sub_group1', cls='<class 'aiida.orm.groups.Group'>')
    GroupPath('base1/sub_group2', cls='<class 'aiida.orm.groups.Group'>')
    GroupPath('base2/other/sub_group3', cls='<class 'aiida.orm.groups.Group'>')

You can also traverse directly through the nodes of a path, optionally filtering by node class and any other filters allowed by the :ref:`QueryBuilder <how-to:query>`:

.. code-block:: ipython

    In [17]: from aiida.orm import Data
    In [18]: data = Data()
    In [19]: data.base.extras.set("key", "value")
    In [20]: data.store()
    Out[20]: <Data: uuid: 0adb5224-585d-4fd4-99ae-20a071972ddd (pk: 1)>
    In [21]: path["base1/sub_group1"].get_group().add_nodes(data)
    In [21]: next(path.walk_nodes(node_class=Data, filters={"extras.key": "value"}))
    Out[21]: WalkNodeResult(group_path=GroupPath('base1/sub_group1', cls='<class 'aiida.orm.groups.Group'>'),
    node=<Data: uuid: 0adb5224-585d-4fd4-99ae-20a071972ddd (pk: 1)>)

Finally, you can also specify the ``Group`` subclasses (as discussed above):

.. code-block:: ipython

    In [22]: from aiida.orm import UpfFamily
    In [23]: path2 = GroupPath(cls=UpfFamily)
    In [24]: path2["base1"].get_or_create_group()
    Out[24]: (<UpfFamily: "base1" [type core.upf], of user user@email.com>, True)

.. important::

    A :py:class:`~aiida.tools.groups.paths.GroupPath` instance will only recognise groups of the instantiated ``cls`` type.
    The default ``cls`` is ``aiida.orm.Group``:

    .. code-block:: ipython

        In [25]: orm.UpfFamily(label="a").store()
        Out[25]: <UpfFamily: "a" [type core.upf], of user user@email.com>
        In [26]: GroupPath("a").is_virtual
        Out[26]: True
        In [27]: GroupPath("a", cls=orm.UpfFamily).is_virtual
        Out[27]: False


.. _how-to:data:delete:

Deleting data
=============

By default, every time you run or submit a new calculation, AiiDA will create for you new nodes in the database, and will never replace or delete data.
There are cases, however, when it might be useful to delete nodes that are not useful anymore, for instance test runs or incorrect/wrong data and calculations.
For this case, AiiDA provides the ``verdi node delete`` command and the :py:func:`~aiida.tools.graph.deletions.delete_nodes` function, to remove the nodes from the provenance graph.

.. caution::
   Once the data is deleted, there is no way to recover it (unless you made a backup).

Critically, note that even if you ask to delete only one node, ``verdi node delete`` will typically delete a number of additional linked nodes, in order to preserve a consistent state of the provenance graph.
For instance, if you delete an input of a calculation, AiiDA will delete also the calculation itself (as otherwise you would be effectively changing the inputs to that calculation in the provenance graph).
The full set of consistency rules are explained in detail :ref:`here <topics:provenance:consistency>`.

Therefore: always check the output of ``verdi node delete`` to make sure that it is not deleting more than you expect.
You can also use the ``--dry-run`` flag of ``verdi node delete`` to see what the command would do without performing any actual operation.

In addition, there are a number of additional rules that are not mandatory to ensure consistency, but can be toggled by the user.
For instance, you can set ``--create-forward`` if, when deleting a calculation, you want to delete also the data it produced (using instead ``--no-create-forward`` will delete the calculation only, keeping the output data: note that this effectively strips out the provenance information of the output data).
The full list of these flags is available from the help command ``verdi node delete -h``.

.. code-block:: python

    from aiida.tools import delete_nodes
    pks_to_be_deleted = delete_nodes(
        [1, 2, 3], dry_run=True, create_forward=True, call_calc_forward=True, call_work_forward=True
    )

Deleting computers
------------------
To delete a computer, you can use ``verdi computer delete``.
This command is mostly useful if, right after creating a computer, you realise that there was an error and you want to remove it.
In particular, note that ``verdi computer delete`` will prevent execution if the computer has been already used by at least one node. In this case, you will need to use ``verdi node delete`` to delete first the corresponding nodes.

Deleting mutable data
---------------------
A subset of data in AiiDA is mutable also after storing a node, and is used as a convenience for the user to tag/group/comment on data.
This data can be safely deleted at any time.
This includes, notably:

* *Node extras*: These can be deleted using :py:attr:`Node.base.extras <aiida.orm.extras.EntityExtras>`.
* *Node comments*: These can be removed using :py:attr:`Node.base.comments <aiida.orm.nodes.comments.NodeComments>`.
* *Groups*: These can be deleted using :py:meth:`Group.objects.delete() <aiida.orm.groups.GroupCollection.delete>`.
  This command will only delete the group, not the nodes contained in the group.

Completely deleting an AiiDA profile
------------------------------------
If you don't want to selectively delete some nodes, but instead want to delete a whole AiiDA profile altogether, use the ``verdi profile delete`` command.
This command will delete both the file repository and the database.

.. danger::

  It is not possible to restore a deleted profile unless it was previously backed up!

.. _how-to:data:transfer:

Transferring data
=================

.. danger::

    This feature is still in beta version and its API might change in the near future.
    It is therefore not recommended that you rely on it for your public/production workflows.

    Moreover, feedback on its implementation is much appreciated (at https://github.com/aiidateam/aiida-core/issues/4811).

When a calculation job is launched, AiiDA will create a :py:class:`~aiida.orm.RemoteData` node that is attached as an output node to the calculation node with the label ``remote_folder``.
The input files generated by the ``CalcJob`` plugin are copied to this remote folder and, since the job is executed there as well, the code will produce its output files in that same remote folder also.
Since the :py:class:`~aiida.orm.RemoteData` node only explicitly stores the filepath on the remote computer, and not its actual contents, it functions more or less like a symbolic link.
That means that if the remote folder gets deleted, there will be no way to retrieve its contents.
The ``CalcJob`` plugin can for that reason specify some files that should be :ref:`retrieved<topics:calculations:usage:calcjobs:file_lists_retrieve>` and stored locally in a :py:class:`~aiida.orm.nodes.data.folder.FolderData` node for safekeeing, which is attached to the calculation node as an output with the label ``retrieved_folder``.

Although the :ref:`retrieve_list<topics:calculations:usage:calcjobs:file_lists_retrieve>` allows to specify what output files are to be retrieved locally, this has to be done *before* the calculation is submitted.
In order to provide more flexibility in deciding what files of completed calculation jobs are to be stored locally, even after it has terminated, AiiDA ships with a the :py:class:`~aiida.calculations.transfer.TransferCalculation` plugin.
This calculation plugin enables to retrieve files from a remote machine and save them in a local :py:class:`~aiida.orm.nodes.data.folder.FolderData`.
The specifications of what to copy are provided through an input of type

.. code-block:: ipython

    In [1]: instructions_cont = {}
        ... instructions_cont['retrieve_files'] = True
        ... instructions_cont['symlink_files'] = [
        ...     ('node_keyname', 'source/path/filename', 'target/path/filename'),
        ... ]
        ... instructions_node = orm.Dict(dict=instructions_cont)

The ``'source/path/filename'`` and ``'target/path/filename'`` are both relative paths (to their respective folders).
The ``node_keyname`` is a string that will be used when providing the source :py:class:`~aiida.orm.RemoteData` node to the calculation.
You also need to provide the computer between which the transfer will occur:

.. code-block:: ipython

    In [2]: transfer_builder = CalculationFactory('core.transfer').get_builder()
        ... transfer_builder.instructions = instructions_node
        ... transfer_builder.source_nodes = {'node_keyname': source_node}
        ... transfer_builder.metadata.computer = source_node.computer

The variable ``source_node`` here corresponds to the ``RemoteData`` node whose contents need to be retrieved.
Finally, you just run or submit the calculation as you would do with any other:

.. code-block:: ipython

    In [2]: from aiida.engine import submit
        ... submit(transfer_builder)

You can also use this to copy local files into a new :py:class:`~aiida.orm.RemoteData` folder.
For this you first have to adapt the instructions to set ``'retrieve_files'`` to ``False`` and use a ``'local_files'`` list instead of the ``'symlink_files'``:

.. code-block:: ipython

    In [1]: instructions_cont = {}
        ... instructions_cont['retrieve_files'] = False
        ... instructions_cont['local_files'] = [
        ...     ('node_keyname', 'source/path/filename', 'target/path/filename'),
        ... ]
        ... instructions_node = orm.Dict(dict=instructions_cont)

It is also relevant to note that, in this case, the ``source_node`` will be of type :py:class:`~aiida.orm.nodes.data.folder.FolderData` so you will have to manually select the computer to where you want to copy the files.
You can do this by looking at your available computers running ``verdi computer list`` and using the label shown to load it with :py:func:`~aiida.orm.load_computer`:

.. code-block:: ipython

    In [2]: transfer_builder.metadata.computer = load_computer('some-computer-label')

Both when uploading or retrieving, you can copy multiple files by appending them to the list of the ``local_files`` or ``symlink_files`` keys in the instructions input, respectively.
It is also possible to copy files from any number of nodes by providing several ``source_node`` s, each with a different ``'node_keyname'``.
The target node will always be one (so you can *"gather"* files in a single call, but not *"distribute"* them).
