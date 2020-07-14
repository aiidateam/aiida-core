.. _reference:command-line:

******************
AiiDA Command Line
******************

.. _reference:command-line:verdi:

Commands
========
Below is a list with all available subcommands.

.. _reference:command-line:verdi-calcjob:

``verdi calcjob``
-----------------

.. code:: console

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


.. _reference:command-line:verdi-code:

``verdi code``
--------------

.. code:: console

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


.. _reference:command-line:verdi-comment:

``verdi comment``
-----------------

.. code:: console

    Usage:  [OPTIONS] COMMAND [ARGS]...

      Inspect, create and manage node comments.

    Options:
      --help  Show this message and exit.

    Commands:
      add     Add a comment to one or more nodes.
      remove  Remove a comment of a node.
      show    Show the comments of one or multiple nodes.
      update  Update a comment of a node.


.. _reference:command-line:verdi-completioncommand:

``verdi completioncommand``
---------------------------

.. code:: console

    Usage:  [OPTIONS]

      Return the code to activate bash completion.

      This command is mainly for back-compatibility.
      You should rather use: eval "$(_VERDI_COMPLETE=source verdi)"

    Options:
      --help  Show this message and exit.


.. _reference:command-line:verdi-computer:

``verdi computer``
------------------

.. code:: console

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


.. _reference:command-line:verdi-config:

``verdi config``
----------------

.. code:: console

    Usage:  [OPTIONS] OPTION_NAME OPTION_VALUE

      Configure profile-specific or global AiiDA options.

    Options:
      --global  Apply the option configuration wide.
      --unset   Remove the line matching the option name from the config file.
      --help    Show this message and exit.


.. _reference:command-line:verdi-daemon:

``verdi daemon``
----------------

.. code:: console

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


.. _reference:command-line:verdi-data:

``verdi data``
--------------

.. code:: console

    Usage:  [OPTIONS] COMMAND [ARGS]...

      Inspect, create and manage data nodes.

    Options:
      --help  Show this message and exit.


.. _reference:command-line:verdi-database:

``verdi database``
------------------

.. code:: console

    Usage:  [OPTIONS] COMMAND [ARGS]...

      Inspect and manage the database.

    Options:
      --help  Show this message and exit.

    Commands:
      integrity  Check the integrity of the database and fix potential issues.
      migrate    Migrate the database to the latest schema version.


.. _reference:command-line:verdi-devel:

``verdi devel``
---------------

.. code:: console

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


.. _reference:command-line:verdi-export:

``verdi export``
----------------

.. code:: console

    Usage:  [OPTIONS] COMMAND [ARGS]...

      Create and manage export archives.

    Options:
      --help  Show this message and exit.

    Commands:
      create   Export subsets of the provenance graph to file for sharing.
      inspect  Inspect contents of an exported archive without importing it.
      migrate  Migrate an export archive to a more recent format version.


.. _reference:command-line:verdi-graph:

``verdi graph``
---------------

.. code:: console

    Usage:  [OPTIONS] COMMAND [ARGS]...

      Create visual representations of the provenance graph.

    Options:
      --help  Show this message and exit.

    Commands:
      generate  Generate a graph from a ROOT_NODE (specified by pk or uuid).


.. _reference:command-line:verdi-group:

``verdi group``
---------------

.. code:: console

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


.. _reference:command-line:verdi-help:

``verdi help``
--------------

.. code:: console

    Usage:  [OPTIONS] [COMMAND]

      Show help for given command.

    Options:
      --help  Show this message and exit.


.. _reference:command-line:verdi-import:

``verdi import``
----------------

.. code:: console

    Usage:  [OPTIONS] [--] [ARCHIVES]...

      Import data from an AiiDA archive file.

      The archive can be specified by its relative or absolute file path, or its HTTP URL.

    Options:
      -w, --webpages TEXT...          Discover all URL targets pointing to files with the
                                      .aiida extension for these HTTP addresses. Automatically
                                      discovered archive URLs will be downloadeded and added
                                      to ARCHIVES for importing

      -G, --group GROUP               Specify group to which all the import nodes will be
                                      added. If such a group does not exist, it will be
                                      created automatically.

      -e, --extras-mode-existing [keep_existing|update_existing|mirror|none|ask]
                                      Specify which extras from the export archive should be
                                      imported for nodes that are already contained in the
                                      database: ask: import all extras and prompt what to do
                                      for existing extras. keep_existing: import all extras
                                      and keep original value of existing extras.
                                      update_existing: import all extras and overwrite value
                                      of existing extras. mirror: import all extras and remove
                                      any existing extras that are not present in the archive.
                                      none: do not import any extras.

      -n, --extras-mode-new [import|none]
                                      Specify whether to import extras of new nodes: import:
                                      import extras. none: do not import extras.

      --comment-mode [newest|overwrite]
                                      Specify the way to import Comments with identical UUIDs:
                                      newest: Only the newest Comments (based on mtime)
                                      (default).overwrite: Replace existing Comments with
                                      those from the import file.

      --migration / --no-migration    Force migration of export file archives, if needed.
                                      [default: True]

      -n, --non-interactive           Non-interactive mode: never prompt for input.
      --help                          Show this message and exit.


.. _reference:command-line:verdi-node:

``verdi node``
--------------

.. code:: console

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


.. _reference:command-line:verdi-plugin:

``verdi plugin``
----------------

.. code:: console

    Usage:  [OPTIONS] COMMAND [ARGS]...

      Inspect AiiDA plugins.

    Options:
      --help  Show this message and exit.

    Commands:
      list  Display a list of all available plugins.


.. _reference:command-line:verdi-process:

``verdi process``
-----------------

.. code:: console

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


.. _reference:command-line:verdi-profile:

``verdi profile``
-----------------

.. code:: console

    Usage:  [OPTIONS] COMMAND [ARGS]...

      Inspect and manage the configured profiles.

    Options:
      --help  Show this message and exit.

    Commands:
      delete      Delete one or more profiles.
      list        Display a list of all available profiles.
      setdefault  Set a profile as the default one.
      show        Show details for a profile.


.. _reference:command-line:verdi-quicksetup:

``verdi quicksetup``
--------------------

.. code:: console

    Usage:  [OPTIONS]

      Setup a new profile in a fully automated fashion.

    Options:
      -n, --non-interactive           Non-interactive mode: never prompt for input.
      --profile PROFILE               The name of the new profile.  [required]
      --email EMAIL                   Email address associated with the data you generate. The
                                      email address is exported along with the data, when
                                      sharing it.  [required]

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
      --su-db-name TEXT               Name of the template database to connect to as the
                                      database superuser.

      --su-db-username TEXT           User name of the database super user.
      --su-db-password TEXT           Password to connect as the database superuser.
      --repository DIRECTORY          Absolute path to the file repository.
      --config FILEORURL              Load option values from configuration file in yaml
                                      format (local path or URL).

      --help                          Show this message and exit.


.. _reference:command-line:verdi-rehash:

``verdi rehash``
----------------

.. code:: console

    Usage:  [OPTIONS] [NODES]...

      Recompute the hash for nodes in the database.

      The set of nodes that will be rehashed can be filtered by their identifier and/or
      based on their class.

    Options:
      -e, --entry-point PLUGIN  Only include nodes that are class or sub class of the class
                                identified by this entry point.

      -f, --force               Do not ask for confirmation.
      --help                    Show this message and exit.


.. _reference:command-line:verdi-restapi:

``verdi restapi``
-----------------

.. code:: console

    Usage:  [OPTIONS]

      Run the AiiDA REST API server.

      Example Usage:

          verdi -p <profile_name> restapi --hostname 127.0.0.5 --port 6789

    Options:
      -H, --hostname HOSTNAME  Hostname.
      -P, --port INTEGER       Port number.
      -c, --config-dir PATH    Path to the configuration directory
      --wsgi-profile           Whether to enable WSGI profiler middleware for finding
                               bottlenecks

      --hookup / --no-hookup   Hookup app to flask server
      --help                   Show this message and exit.


.. _reference:command-line:verdi-run:

``verdi run``
-------------

.. code:: console

    Usage:  [OPTIONS] [--] SCRIPTNAME [VARARGS]...

      Execute scripts with preloaded AiiDA environment.

    Options:
      --auto-group                    Enables the autogrouping
      -l, --auto-group-label-prefix TEXT
                                      Specify the prefix of the label of the auto group
                                      (numbers might be automatically appended to generate
                                      unique names per run).

      -n, --group-name TEXT           Specify the name of the auto group [DEPRECATED, USE
                                      --auto-group-label-prefix instead]. This also enables
                                      auto-grouping.

      -e, --exclude TEXT              Exclude these classes from auto grouping (use full
                                      entrypoint strings).

      -i, --include TEXT              Include these classes from auto grouping  (use full
                                      entrypoint strings or "all").

      --help                          Show this message and exit.


.. _reference:command-line:verdi-setup:

``verdi setup``
---------------

.. code:: console

    Usage:  [OPTIONS]

      Setup a new profile.

    Options:
      -n, --non-interactive           Non-interactive mode: never prompt for input.
      --profile PROFILE               The name of the new profile.  [required]
      --email EMAIL                   Email address associated with the data you generate. The
                                      email address is exported along with the data, when
                                      sharing it.  [required]

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
      --db-username NONEMPTYSTRING    Name of the database user to create.  [required]
      --db-password TEXT              Password of the database user.  [required]
      --repository DIRECTORY          Absolute path to the file repository.
      --config FILEORURL              Load option values from configuration file in yaml
                                      format (local path or URL).

      --help                          Show this message and exit.


.. _reference:command-line:verdi-shell:

``verdi shell``
---------------

.. code:: console

    Usage:  [OPTIONS]

      Start a python shell with preloaded AiiDA environment.

    Options:
      --plain                         Use a plain Python shell.
      --no-startup                    When using plain Python, ignore the PYTHONSTARTUP
                                      environment variable and ~/.pythonrc.py script.

      -i, --interface [ipython|bpython]
                                      Specify an interactive interpreter interface.
      --help                          Show this message and exit.


.. _reference:command-line:verdi-status:

``verdi status``
----------------

.. code:: console

    Usage:  [OPTIONS]

      Print status of AiiDA services.

    Options:
      --no-rmq  Do not check RabbitMQ status
      --help    Show this message and exit.


.. _reference:command-line:verdi-user:

``verdi user``
--------------

.. code:: console

    Usage:  [OPTIONS] COMMAND [ARGS]...

      Inspect and manage users.

    Options:
      --help  Show this message and exit.

    Commands:
      configure    Configure a new or existing user.
      list         Show a list of all users.
      set-default  Set a user as the default user for the profile.



.. END_OF_VERDI_COMMANDS_MARKER
