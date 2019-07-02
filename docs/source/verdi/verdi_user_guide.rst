.. _cli_concepts:

Concepts
========

This section explains basic concepts of the command line interface that apply to all ``verdi`` commands.

.. _cli_parameters:

Parameters
----------
Parameters to ``verdi`` commands come in two flavors:

  * Arguments: positional parameters, e.g. ``123`` in ``verdi process kill 123``
  * Options: announced by a flag (e.g. ``-f`` or ``--flag``), potentially followed by a value. E.g. ``verdi process list --limit 10`` or ``verdi process -h``.

.. _cli_multi_value_options:

Multi-value options
...................

Some ``verdi`` commands provide *options* that can take multiple values.
This allows to avoid repetition and e.g. write::

  verdi export create -N 10 11 12 -- archive.aiida

instead of the more lengthy::

  verdi export create -N 10 -N 11 -N 12 archive.aiida

Note the use of the so-called 'endopts' marker ``--`` that is necessary to mark the end of the ``-N`` option and distinguish it from the ``archive.aiida`` argument.

.. _cli_help_strings:

Help strings
------------
Append the ``--help`` option to any verdi (sub-)command to get help on how to use it.
For example, ``verdi process kill --help`` shows::

  Usage: verdi process kill [OPTIONS] [PROCESSES]...

    Kill running processes.

  Options:
    -t, --timeout FLOAT  Time in seconds to wait for a response before timing
                         out.  [default: 5.0]
    --wait / --no-wait   Wait for the action to be completed otherwise return as
                         soon as it's scheduled.
    -h, --help           Show this message and exit.

All help strings consist of three parts:

  * A ``Usage:`` line describing how to invoke the command
  * A description of the command's functionality
  * A list of the available options

The ``Usage:`` line encodes information on the command's parameters, e.g.:

 * ``[OPTIONS]``: this command takes one (or more) options
 * ``PROCESSES``: this command requires a process as a positional argument
 * ``[PROCESSES]``: this command takes a process as an optional positional argument
 * ``[PROCESSES]...``: this command takes one or more processes as (optional) positional arguments

Multi-value options are followed by ``...`` in the help string and the ``Usage:`` line
of the corresponding command will contains the 'endopts' marker. For example::

  Usage: verdi export create [OPTIONS] [--] OUTPUT_FILE

    Export various entities, such as Codes, Computers, Groups and Nodes, to an
    archive file for backup or sharing purposes.

  Options:
    -X, --codes CODE...             one or multiple codes identified by their
                                    ID, UUID or label
    -Y, --computers COMPUTER...     one or multiple computers identified by
                                    their ID, UUID or label
    -G, --groups GROUP...           one or multiple groups identified by their
                                    ID, UUID or name
    -N, --nodes NODE...             one or multiple nodes identified by their ID
                                    or UUID

.. _cli_profile:

Profile
-------
AiiDA supports multiple profiles per installation, one of which is marked as the default
and used unless another profile is requested.
Show the current default profile using::

  verdi profile list

In order to use a different profile, pass the ``-p/--profile`` option to any ``verdi`` command, for example::

  verdi -p <profile> process list

Note that the specified profile will be used for this and *only* this command.
Use ``verdi profile setdefault`` in order to permanently change the default profile.

.. _cli_identifiers:

Identifiers
-----------

When working with AiiDA entities, you need a way to *refer* to them on the command line.
Any entity in AiiDA can be addressed via three identifiers:

 * "Primary Key" (PK): An integer, e.g. ``723``, that identifies your entity within your database (automatically assigned)
 * `Universally Unique Identifier <https://en.wikipedia.org/wiki/Universally_unique_identifier#Version_4_(random)>`_ (UUID): A string, e.g. ``ce81c420-7751-48f6-af8e-eb7c6a30cec3`` that identifies your entity globally (automatically assigned)
 * Label: A human-readable string, e.g. ``test_calculation`` (manually assigned)

Any ``verdi`` command that expects and identifier as a paramter will accept PKs, UUIDs and labels.

In almost all cases, this will work out of the box.
Since command line parameters are passed as strings, AiiDA needs to deduce the type of identifier from its content, which can fail in edge cases (see :ref:`cli_identifier_resolution` for details).
You can take the following precautions in order to avoid such edge cases:

  * PK: no precautions needed
  * UUID: no precautions needed for full UUIDs. Partial UUIDs should include at least one non-numeric character or dash.
  * Label: add an exclamation mark ``!`` at the end of the identifier in order to force interpretation as a label


.. _cli_identifier_resolution:

Implementation of identifier resolution
.......................................

The logic for deducing the identifier type is as follows:

 1. Try interpreting the identifier as a PK (integer)
 2. If this fails, try interpreting the identifier as a UUID (full or partial).
 3. If this fails, interpret the identifier as a label

The following example illustrates edge cases that can arise in this logic:

===  =====================================  ========
PK   UUID                                   LABEL
===  =====================================  ========
10   12dfb104-7b2b-4bca-adc0-1e4fd4ffcc88   group
11   deadbeef-62ba-444f-976d-31d925dac557   10
12   3df34a1e-5215-4e1a-b626-7f75b9586ef5   deadbeef
===  =====================================  ========

 * trying to identify the first entity by its partial UUID ``12`` would match the third entity by its PK instead.
 * trying to identify the second entity by its label ``10`` would match the first entity by its PK instead
 * trying to identify the third entity by its label ``deadbeef`` would match the second entity on its partial UUID ``deadbeef`` instead.

The ambiguity between a partial UUID and a PK can always be resolved by including a longer substring of the UUID, eventually rendering the identifier no longer a valid PK.

The case of a label being also a valid PK or (partial) UUID requires a different solution.
For this case, ``verdi`` reserves a special character, the exclamation mark ``!``, that can be appended to the identifier.
Before any type guessing is done, AiiDA checks for the presence of this marker and, if found, will interpret the identifier as a label.
I.e. to solve ambiguity examples mentioned above, one would pass ``10!`` and ``deadbeef!``.


.. _verdi_commands:

Commands
========

.. _verdi_calcjob:

``verdi calcjob``
-----------------

::

    Usage:  [OPTIONS] COMMAND [ARGS]...

      Inspect and manage calcjobs.

    Options:
      --help  Show this message and exit.

    Commands:
      cleanworkdir  Clean all content of all output remote folders of calcjobs.
      gotocomputer  Open a shell and go to the calcjob folder on the computer...
      inputcat      Show the contents of a file with relative PATH in the raw...
      inputls       Show the list of files in the directory with relative PATH...
      outputcat     Show the contents of a file with relative PATH in the...
      outputls      Show the list of files in the directory with relative PATH...
      res           Print data from the result output node of a calcjob.


.. _verdi_code:

``verdi code``
--------------

::

    Usage:  [OPTIONS] COMMAND [ARGS]...

      Setup and manage codes.

    Options:
      --help  Show this message and exit.

    Commands:
      delete     Delete codes that have not yet been used for calculations, i.e.
      duplicate  Create duplicate of existing Code.
      hide       Hide one or more codes from the `verdi code list` command.
      list       List the codes in the database.
      relabel    Relabel a code.
      rename     Rename a code.
      reveal     Reveal one or more hidden codes to the `verdi code list`...
      setup      Setup a new Code.
      show       Display detailed information for the given CODE.
      update     Update an existing code.


.. _verdi_comment:

``verdi comment``
-----------------

::

    Usage:  [OPTIONS] COMMAND [ARGS]...

      Inspect, create and manage node comments.

    Options:
      --help  Show this message and exit.

    Commands:
      add     Add a comment to one or multiple nodes.
      remove  Remove a comment.
      show    Show the comments for one or multiple nodes.
      update  Update a comment.


.. _verdi_completioncommand:

``verdi completioncommand``
---------------------------

::

    Usage:  [OPTIONS]

      Return the bash code to activate completion.

      :note: this command is mainly for back-compatibility.     You should
      rather use:;

              eval "$(_VERDI_COMPLETE=source verdi)"

    Options:
      --help  Show this message and exit.


.. _verdi_computer:

``verdi computer``
------------------

::

    Usage:  [OPTIONS] COMMAND [ARGS]...

      Setup and manage computers.

    Options:
      --help  Show this message and exit.

    Commands:
      configure  Configure a computer with one of the available transport types.
      delete     Configure the authentication information for a given computer...
      disable    Disable the computer for the given user.
      duplicate  Duplicate a computer.
      enable     Enable the computer for the given user.
      list       List available computers.
      rename     Rename a computer.
      setup      Add a computer.
      show       Show information for a computer.
      test       Test the connection to a computer.


.. _verdi_config:

``verdi config``
----------------

::

    Usage:  [OPTIONS] OPTION_NAME OPTION_VALUE

      Set, unset and get profile specific or global configuration options.

    Options:
      --global  Apply the option configuration wide.
      --unset   Remove the line matching the option name from the config file.
      --help    Show this message and exit.


.. _verdi_daemon:

``verdi daemon``
----------------

::

    Usage:  [OPTIONS] COMMAND [ARGS]...

      Inspect and manage the daemon.

    Options:
      --help  Show this message and exit.

    Commands:
      decr     Remove NUMBER [default=1] workers from the running daemon.
      incr     Add NUMBER [default=1] workers to the running daemon.
      logshow  Show the log of the daemon, press CTRL+C to quit.
      restart  Restart the daemon.
      start    Start the daemon with NUMBER workers [default=1].
      status   Print the status of the current daemon or all daemons.
      stop     Stop the daemon.


.. _verdi_data:

``verdi data``
--------------

::

    Usage:  [OPTIONS] COMMAND [ARGS]...

      Inspect, create and manage data nodes.

    Options:
      --help  Show this message and exit.

    Commands:
      array       Manipulate ArrayData objects.
      bands       Manipulate BandsData objects.
      cif         Manipulation of CIF data objects.
      dict        View and manipulate Dict objects.
      plugins     Print a list of registered data plugins or details of a...
      remote      Managing RemoteData objects.
      structure   Manipulation of StructureData objects.
      trajectory  View and manipulate TrajectoryData instances.
      upf         Manipulation of the upf families.


.. _verdi_database:

``verdi database``
------------------

::

    Usage:  [OPTIONS] COMMAND [ARGS]...

      Inspect and manage the database.

    Options:
      --help  Show this message and exit.

    Commands:
      integrity  Various commands that will check the integrity of the database...
      migrate    Migrate the database to the latest schema version.


.. _verdi_devel:

``verdi devel``
---------------

::

    Usage:  [OPTIONS] COMMAND [ARGS]...

      Commands for developers.

    Options:
      --help  Show this message and exit.

    Commands:
      play        Open a browser and play the Aida triumphal march by Giuseppe...
      run_daemon  Run a daemon instance in the current interpreter.
      tests       Run the unittest suite or parts of it.


.. _verdi_export:

``verdi export``
----------------

::

    Usage:  [OPTIONS] COMMAND [ARGS]...

      Create and manage export archives.

    Options:
      --help  Show this message and exit.

    Commands:
      create   Export various entities, such as Codes, Computers, Groups and...
      inspect  Inspect the contents of an exported archive without importing
               the...
      migrate  Migrate an existing export archive file to the most recent...


.. _verdi_graph:

``verdi graph``
---------------

::

    Usage:  [OPTIONS] COMMAND [ARGS]...

      Create visual representations of part of the provenance graph. Requires
      that `graphviz<https://graphviz.org/download>` be installed.

    Options:
      --help  Show this message and exit.

    Commands:
      generate  Generate a graph for a given ROOT_NODE.


.. _verdi_group:

``verdi group``
---------------

::

    Usage:  [OPTIONS] COMMAND [ARGS]...

      Create, inspect and manage groups.

    Options:
      --help  Show this message and exit.

    Commands:
      add-nodes     Add NODES to the given GROUP.
      copy          Add all nodes that belong to source group to the
                    destination...
      create        Create a new empty group with the name GROUP_NAME.
      delete        Delete a GROUP.
      description   Change the description of the given GROUP to DESCRIPTION.
      list          Show a list of groups.
      relabel       Change the label of the given GROUP to LABEL.
      remove-nodes  Remove NODES from the given GROUP.
      show          Show information on a given group.


.. _verdi_import:

``verdi import``
----------------

::

    Usage:  [OPTIONS] [--] [ARCHIVES]...

      Import one or multiple exported AiiDA archives

      The ARCHIVES can be specified by their relative or absolute file path, or
      their HTTP URL.

    Options:
      -w, --webpages TEXT...          Discover all URL targets pointing to files
                                      with the .aiida extension for these HTTP
                                      addresses. Automatically discovered archive
                                      URLs will be downloadeded and added to
                                      ARCHIVES for importing
      -G, --group GROUP               Specify group to which all the import nodes
                                      will be added. If such a group does not
                                      exist, it will be created automatically.
      -e, --extras-mode-existing [keep_existing|update_existing|mirror|none|ask]
                                      Specify which extras from the export archive
                                      should be imported for nodes that are
                                      already contained in the database: ask:
                                      import all extras and prompt what to do for
                                      existing extras. keep_existing: import all
                                      extras and keep original value of existing
                                      extras. update_existing: import all extras
                                      and overwrite value of existing extras.
                                      mirror: import all extras and remove any
                                      existing extras that are not present in the
                                      archive. none: do not import any extras.
      -n, --extras-mode-new [import|none]
                                      Specify whether to import extras of new
                                      nodes: import: import extras. none: do not
                                      import extras.
      --comment-mode [newest|overwrite]
                                      Specify the way to import Comments with
                                      identical UUIDs: newest: Only the newest
                                      Comments (based on mtime)
                                      (default).overwrite: Replace existing
                                      Comments with those from the import file.
      --migration / --no-migration    Force migration of export file archives, if
                                      needed.  [default: True]
      -n, --non-interactive           Non-interactive mode: never prompt for
                                      input.
      --help                          Show this message and exit.


.. _verdi_node:

``verdi node``
--------------

::

    Usage:  [OPTIONS] COMMAND [ARGS]...

      Inspect, create and manage nodes.

    Options:
      --help  Show this message and exit.

    Commands:
      delete       Delete nodes and everything that originates from them.
      description  View or set the descriptions of one or more nodes.
      label        View or set the labels of one or more nodes.
      repo
      show         Show generic information on node(s).
      tree         Show trees of nodes.


.. _verdi_plugin:

``verdi plugin``
----------------

::

    Usage:  [OPTIONS] COMMAND [ARGS]...

      Inspect installed plugins for various entry point categories.

    Options:
      --help  Show this message and exit.

    Commands:
      list  Display a list of all available plugins.


.. _verdi_process:

``verdi process``
-----------------

::

    Usage:  [OPTIONS] COMMAND [ARGS]...

      Inspect and manage processes.

    Options:
      --help  Show this message and exit.

    Commands:
      call-root  Show the root process of the call stack for the given...
      kill       Kill running processes.
      list       Show a list of processes that are still running.
      pause      Pause running processes.
      play       Play paused processes.
      report     Show the log report for one or multiple processes.
      show       Show a summary for one or multiple processes.
      status     Print the status of the process.
      watch      Watch the state transitions for a process.


.. _verdi_profile:

``verdi profile``
-----------------

::

    Usage:  [OPTIONS] COMMAND [ARGS]...

      Inspect and manage the configured profiles.

    Options:
      --help  Show this message and exit.

    Commands:
      delete      Delete PROFILES (names, separated by spaces) from the aiida...
      list        Displays list of all available profiles.
      setdefault  Set PROFILE as the default profile.
      show        Show details for PROFILE or, when not specified, the default...


.. _verdi_quicksetup:

``verdi quicksetup``
--------------------

::

    Usage:  [OPTIONS]

      Setup a new profile where the database is automatically created and
      configured.

    Options:
      -n, --non-interactive           Non-interactive mode: never prompt for
                                      input.
      --profile PROFILE               The name of the new profile.  [required]
      --email TEXT                    Email address that serves as the user name
                                      and a way to identify data created by it.
                                      [required]
      --first-name TEXT               First name of the user.  [required]
      --last-name TEXT                Last name of the user.  [required]
      --institution TEXT              Institution of the user.  [required]
      --db-engine [postgresql_psycopg2]
                                      Engine to use to connect to the database.
      --db-backend [django|sqlalchemy]
                                      Backend type to use to map the database.
      --db-host TEXT                  Hostname to connect to the database.
      --db-port INTEGER               Port to connect to the database.
      --db-name TEXT                  Name of the database to create.
      --db-username TEXT              Name of the database user to create.
      --db-password TEXT              Password to connect to the database.
      --su-db-name TEXT               Name of the template database to connect to
                                      as the database superuser.
      --su-db-username TEXT           User name of the database super user.
      --su-db-password TEXT           Password to connect as the database
                                      superuser.
      --repository DIRECTORY          Absolute path for the file system
                                      repository.
      --config FILE                   Load option values from configuration file
                                      in yaml format.
      --help                          Show this message and exit.


.. _verdi_rehash:

``verdi rehash``
----------------

::

    Usage:  [OPTIONS] [NODES]...

      Recompute the hash for nodes in the database

      The set of nodes that will be rehashed can be filtered by their identifier
      and/or based on their class.

    Options:
      -e, --entry-point PLUGIN  Only include nodes that are class or sub class of
                                the class identified by this entry point.
      --help                    Show this message and exit.


.. _verdi_restapi:

``verdi restapi``
-----------------

::

    Usage:  [OPTIONS]

      Run the AiiDA REST API server

      Example Usage:

              verdi -p <profile_name> restapi --hostname 127.0.0.5 --port 6789 --config-dir <location of the config.py file>
              --debug --wsgi-profile --hookup

    Options:
      -H, --hostname TEXT     Hostname.
      -P, --port INTEGER      Port number.
      -c, --config-dir PATH   the path of the configuration directory
      --debug                 run app in debug mode
      --wsgi-profile          to use WSGI profiler middleware for finding
                              bottlenecks in web application
      --hookup / --no-hookup  to hookup app
      --help                  Show this message and exit.


.. _verdi_run:

``verdi run``
-------------

::

    Usage:  [OPTIONS] [--] SCRIPTNAME [VARARGS]...

      Execute an AiiDA script.

    Options:
      -g, --group                   Enables the autogrouping  [default: True]
      -n, --group-name TEXT         Specify the name of the auto group
      -e, --exclude TEXT            Exclude these classes from auto grouping
      -i, --include TEXT            Include these classes from auto grouping
      -E, --excludesubclasses TEXT  Exclude these classes and their sub classes
                                    from auto grouping
      -I, --includesubclasses TEXT  Include these classes and their sub classes
                                    from auto grouping
      --help                        Show this message and exit.


.. _verdi_setup:

``verdi setup``
---------------

::

    Usage:  [OPTIONS]

      Setup a new profile.

    Options:
      -n, --non-interactive           Non-interactive mode: never prompt for
                                      input.
      --profile PROFILE               The name of the new profile.  [required]
      --email TEXT                    Email address that serves as the user name
                                      and a way to identify data created by it.
                                      [required]
      --first-name TEXT               First name of the user.  [required]
      --last-name TEXT                Last name of the user.  [required]
      --institution TEXT              Institution of the user.  [required]
      --db-engine [postgresql_psycopg2]
                                      Engine to use to connect to the database.
      --db-backend [django|sqlalchemy]
                                      Backend type to use to map the database.
      --db-host TEXT                  Hostname to connect to the database.
      --db-port INTEGER               Port to connect to the database.
      --db-name TEXT                  Name of the database to create.  [required]
      --db-username TEXT              Name of the database user to create.
                                      [required]
      --db-password TEXT              Password to connect to the database.
                                      [required]
      --repository DIRECTORY          Absolute path for the file system
                                      repository.
      --config FILE                   Load option values from configuration file
                                      in yaml format.
      --help                          Show this message and exit.


.. _verdi_shell:

``verdi shell``
---------------

::

    Usage:  [OPTIONS]

      Start a python shell with preloaded AiiDA environment.

    Options:
      --plain                         Use a plain Python shell.)
      --no-startup                    When using plain Python, ignore the
                                      PYTHONSTARTUP environment variable and
                                      ~/.pythonrc.py script.
      -i, --interface [ipython|bpython]
                                      Specify an interactive interpreter
                                      interface.
      --help                          Show this message and exit.


.. _verdi_status:

``verdi status``
----------------

::

    Usage:  [OPTIONS]

      Print status of AiiDA services.

    Options:
      --help  Show this message and exit.


.. _verdi_user:

``verdi user``
--------------

::

    Usage:  [OPTIONS] COMMAND [ARGS]...

      Inspect and manage users.

    Options:
      --help  Show this message and exit.

    Commands:
      configure    Configure a new or existing user.
      list         Displays list of all users.
      set-default  Set the USER as the default user.



.. END_OF_VERDI_COMMANDS_MARKER
