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
 * ``PROCESSES``: this command *requires* a process as a positional argument
 * ``[PROCESSES]``: this command takes a process as an *optional* positional argument
 * ``[PROCESSES]...``: this command takes one or more processes as *optional* positional arguments

Multi-value options are followed by ``...`` in the help string and the ``Usage:`` line of the corresponding command will contain the 'endopts' marker.
For example::

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
    ...

.. _cli_profile:

Profile
-------
AiiDA supports multiple profiles per installation, one of which is marked as the default and used unless another profile is requested.
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

 * "Primary Key" (PK): An integer, e.g. ``723``, identifying your entity within your database (automatically assigned)
 * `Universally Unique Identifier <https://en.wikipedia.org/wiki/Universally_unique_identifier#Version_4_(random)>`_ (UUID): A string, e.g. ``ce81c420-7751-48f6-af8e-eb7c6a30cec3`` identifying your entity globally (automatically assigned)
 * Label: A human-readable string, e.g. ``test_calculation`` (manually assigned)

.. note::

   PKs are easy to type and work as long as you stay within your database.
   **When sharing data with others, however, always use UUIDs.**

Any ``verdi`` command that expects an identifier as a paramter will accept PKs, UUIDs and labels.

In almost all cases, this will work out of the box.
Since command line parameters are passed as strings, AiiDA needs to deduce the type of identifier from its content, which can fail in edge cases (see :ref:`cli_identifier_resolution` for details).
You can take the following precautions in order to avoid such edge cases:

  * PK: no precautions needed
  * UUID: no precautions needed for full UUIDs. Partial UUIDs should include at least one non-numeric character or dash
  * Label: add an exclamation mark ``!`` at the end of the identifier in order to force interpretation as a label


.. _cli_identifier_resolution:

Implementation of identifier resolution
.......................................

The logic for deducing the identifier type is as follows:

 1. Try interpreting the identifier as a PK (integer)
 2. If this fails, try interpreting the identifier as a UUID (full or partial)
 3. If this fails, interpret the identifier as a label

The following example illustrates edge cases that can arise in this logic:

===  =====================================  ========
PK   UUID                                   LABEL
===  =====================================  ========
10   12dfb104-7b2b-4bca-adc0-1e4fd4ffcc88   group
11   deadbeef-62ba-444f-976d-31d925dac557   10
12   3df34a1e-5215-4e1a-b626-7f75b9586ef5   deadbeef
===  =====================================  ========

 * trying to identify the first entity by its partial UUID ``12`` would match the third entity by its PK instead
 * trying to identify the second entity by its label ``10`` would match the first entity by its PK instead
 * trying to identify the third entity by its label ``deadbeef`` would match the second entity on its partial UUID ``deadbeef`` instead

The ambiguity between a partial UUID and a PK can always be resolved by including a longer substring of the UUID, eventually rendering the identifier no longer a valid PK.

The case of a label being also a valid PK or (partial) UUID requires a different solution.
For this case, ``verdi`` reserves a special character, the exclamation mark ``!``, that can be appended to the identifier.
Before any type guessing is done, AiiDA checks for the presence of this marker and, if found, will interpret the identifier as a label.
I.e. to solve ambiguity examples mentioned above, one would pass ``10!`` and ``deadbeef!``.


.. _verdi_commands:

Commands
========
Below is a list with all available subcommands.

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
      gotocomputer  Open a shell in the remote folder on the calcjob.
      inputcat      Show the contents of one of the calcjob input files.
      inputls       Show the list of the generated calcjob input files.
      outputcat     Show the contents of one of the calcjob retrieved outputs.
      outputls      Show the list of the retrieved calcjob output files.
      res           Print data from the result output Dict node of a calcjob.


.. _verdi_code:

``verdi code``
--------------

::

    Usage:  [OPTIONS] COMMAND [ARGS]...

      Setup and manage codes.

    Options:
      --help  Show this message and exit.

    Commands:
      delete     Delete a code.
      duplicate  Duplicate a code allowing to change some parameters.
      hide       Hide one or more codes from `verdi code list`.
      list       List the available codes.
      relabel    Relabel a code.
      reveal     Reveal one or more hidden codes in `verdi code list`.
      setup      Setup a new code.
      show       Display detailed information for a code.


.. _verdi_comment:

``verdi comment``
-----------------

::

    Usage:  [OPTIONS] COMMAND [ARGS]...

      Inspect, create and manage node comments.

    Options:
      --help  Show this message and exit.

    Commands:
      add     Add a comment to one or more nodes.
      remove  Remove a comment of a node.
      show    Show the comments of one or multiple nodes.
      update  Update a comment of a node.


.. _verdi_completioncommand:

``verdi completioncommand``
---------------------------

::

    Usage:  [OPTIONS]

      Return the code to activate bash completion.

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
      configure  Configure the Authinfo details for a computer (and user).
      delete     Delete a computer.
      disable    Disable the computer for the given user.
      duplicate  Duplicate a computer allowing to change some parameters.
      enable     Enable the computer for the given user.
      list       List all available computers.
      rename     Rename a computer.
      setup      Create a new computer.
      show       Show detailed information for a computer.
      test       Test the connection to a computer.


.. _verdi_config:

``verdi config``
----------------

::

    Usage:  [OPTIONS] OPTION_NAME OPTION_VALUE

      Configure profile-specific or global AiiDA options.

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
      start    Start the daemon with NUMBER workers.
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


.. _verdi_database:

``verdi database``
------------------

::

    Usage:  [OPTIONS] COMMAND [ARGS]...

      Inspect and manage the database.

    Options:
      --help  Show this message and exit.

    Commands:
      integrity  Check the integrity of the database and fix potential issues.
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
      check-load-time   Check for common indicators that slowdown `verdi`.
      configure-backup  Configure backup of the repository folder.
      run_daemon        Run a daemon instance in the current interpreter.
      tests             Run the unittest suite or parts of it.
      validate-plugins  Validate all plugins by checking they can be loaded.


.. _verdi_export:

``verdi export``
----------------

::

    Usage:  [OPTIONS] COMMAND [ARGS]...

      Create and manage export archives.

    Options:
      --help  Show this message and exit.

    Commands:
      create   Export subsets of the provenance graph to file for sharing.
      inspect  Inspect contents of an exported archive without importing it.
      migrate  Migrate an export archive to a more recent format version.


.. _verdi_graph:

``verdi graph``
---------------

::

    Usage:  [OPTIONS] COMMAND [ARGS]...

      Create visual representations of the provenance graph.

    Options:
      --help  Show this message and exit.

    Commands:
      generate  Generate a graph from a ROOT_NODE (specified by pk or uuid).


.. _verdi_group:

``verdi group``
---------------

::

    Usage:  [OPTIONS] COMMAND [ARGS]...

      Create, inspect and manage groups of nodes.

    Options:
      --help  Show this message and exit.

    Commands:
      add-nodes     Add nodes to the a group.
      copy          Duplicate a group.
      create        Create an empty group with a given name.
      delete        Delete a group.
      description   Change the description of a group.
      list          Show a list of existing groups.
      path          Inspect groups of nodes, with delimited label paths.
      relabel       Change the label of a group.
      remove-nodes  Remove nodes from a group.
      show          Show information for a given group.


.. _verdi_help:

``verdi help``
--------------

::

    Usage:  [OPTIONS] [COMMAND]

      Show help for given command.

    Options:
      --help  Show this message and exit.


.. _verdi_import:

``verdi import``
----------------

::

    Usage:  [OPTIONS] [--] [ARCHIVES]...

      Import data from an AiiDA archive file.

      The archive can be specified by its relative or absolute file path, or its
      HTTP URL.

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
      attributes   Show the attributes of one or more nodes.
      comment      Inspect, create and manage node comments.
      delete       Delete nodes from the provenance graph.
      description  View or set the description of one or more nodes.
      extras       Show the extras of one or more nodes.
      graph        Create visual representations of the provenance graph.
      label        View or set the label of one or more nodes.
      rehash       Recompute the hash for nodes in the database.
      repo         Inspect the content of a node repository folder.
      show         Show generic information on one or more nodes.
      tree         Show a tree of nodes starting from a given node.


.. _verdi_plugin:

``verdi plugin``
----------------

::

    Usage:  [OPTIONS] COMMAND [ARGS]...

      Inspect AiiDA plugins.

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
      call-root  Show root process of the call stack for the given processes.
      kill       Kill running processes.
      list       Show a list of running or terminated processes.
      pause      Pause running processes.
      play       Play (unpause) paused processes.
      report     Show the log report for one or multiple processes.
      show       Show details for one or multiple processes.
      status     Print the status of one or multiple processes.
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
      delete      Delete one or more profiles.
      list        Display a list of all available profiles.
      setdefault  Set a profile as the default one.
      show        Show details for a profile.


.. _verdi_quicksetup:

``verdi quicksetup``
--------------------

::

    Usage:  [OPTIONS]

      Setup a new profile in a fully automated fashion.

    Options:
      -n, --non-interactive           Non-interactive mode: never prompt for
                                      input.

      --profile PROFILE               The name of the new profile.  [required]
      --email EMAIL                   Email address associated with the data you
                                      generate. The email address is exported
                                      along with the data, when sharing it.
                                      [required]

      --first-name NONEMPTYSTRING     First name of the user.  [required]
      --last-name NONEMPTYSTRING      Last name of the user.  [required]
      --institution NONEMPTYSTRING    Institution of the user.  [required]
      --db-engine [postgresql_psycopg2]
                                      Engine to use to connect to the database.
      --db-backend [django|sqlalchemy]
                                      Database backend to use.
      --db-host HOSTNAME              Database server host. Leave empty for "peer"
                                      authentication.

      --db-port INTEGER               Database server port.
      --db-name NONEMPTYSTRING        Name of the database to create.
      --db-username NONEMPTYSTRING    Name of the database user to create.
      --db-password TEXT              Password of the database user.
      --su-db-name TEXT               Name of the template database to connect to
                                      as the database superuser.

      --su-db-username TEXT           User name of the database super user.
      --su-db-password TEXT           Password to connect as the database
                                      superuser.

      --repository DIRECTORY          Absolute path to the file repository.
      --config FILE                   Load option values from configuration file
                                      in yaml format.

      --help                          Show this message and exit.


.. _verdi_rehash:

``verdi rehash``
----------------

::

    Usage:  [OPTIONS] [NODES]...

      Recompute the hash for nodes in the database.

      The set of nodes that will be rehashed can be filtered by their identifier
      and/or based on their class.

    Options:
      -e, --entry-point PLUGIN  Only include nodes that are class or sub class of
                                the class identified by this entry point.

      -f, --force               Do not ask for confirmation.
      --help                    Show this message and exit.


.. _verdi_restapi:

``verdi restapi``
-----------------

::

    Usage:  [OPTIONS]

      Run the AiiDA REST API server.

      Example Usage:

          verdi -p <profile_name> restapi --hostname 127.0.0.5 --port 6789

    Options:
      -H, --hostname HOSTNAME  Hostname.
      -P, --port INTEGER       Port number.
      -c, --config-dir PATH    Path to the configuration directory
      --debug                  Enable debugging
      --wsgi-profile           Whether to enable WSGI profiler middleware for
                               finding bottlenecks

      --hookup / --no-hookup   Hookup app to flask server
      --help                   Show this message and exit.


.. _verdi_run:

``verdi run``
-------------

::

    Usage:  [OPTIONS] [--] SCRIPTNAME [VARARGS]...

      Execute scripts with preloaded AiiDA environment.

    Options:
      --auto-group                    Enables the autogrouping
      -l, --auto-group-label-prefix TEXT
                                      Specify the prefix of the label of the auto
                                      group (numbers might be automatically
                                      appended to generate unique names per run).

      -n, --group-name TEXT           Specify the name of the auto group
                                      [DEPRECATED, USE --auto-group-label-prefix
                                      instead]. This also enables auto-grouping.

      -e, --exclude TEXT              Exclude these classes from auto grouping
                                      (use full entrypoint strings).

      -i, --include TEXT              Include these classes from auto grouping
                                      (use full entrypoint strings or "all").

      --help                          Show this message and exit.


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
      --email EMAIL                   Email address associated with the data you
                                      generate. The email address is exported
                                      along with the data, when sharing it.
                                      [required]

      --first-name NONEMPTYSTRING     First name of the user.  [required]
      --last-name NONEMPTYSTRING      Last name of the user.  [required]
      --institution NONEMPTYSTRING    Institution of the user.  [required]
      --db-engine [postgresql_psycopg2]
                                      Engine to use to connect to the database.
      --db-backend [django|sqlalchemy]
                                      Database backend to use.
      --db-host HOSTNAME              Database server host. Leave empty for "peer"
                                      authentication.

      --db-port INTEGER               Database server port.
      --db-name NONEMPTYSTRING        Name of the database to create.  [required]
      --db-username NONEMPTYSTRING    Name of the database user to create.
                                      [required]

      --db-password TEXT              Password of the database user.  [required]
      --repository DIRECTORY          Absolute path to the file repository.
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
      list         Show a list of all users.
      set-default  Set a user as the default user for the profile.



.. END_OF_VERDI_COMMANDS_MARKER
