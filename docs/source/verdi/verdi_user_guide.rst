.. _cli_concepts:

Concepts
========

In this section, a few basic concepts of the command line interface will be explained that will apply to all the ``verdi`` commands.

.. _cli_help_strings:

Help strings
------------
Each ``verdi`` command and any optional sub commands have automatically generated help strings that explain the command's functionality and usage.
To show the help string for any command, simply append the ``--help`` option.
For example ``verdi process kill --help`` will display:

::

  Usage: verdi process kill [OPTIONS] [PROCESSES]...

    Kill running processes.

  Options:
    -t, --timeout FLOAT  Time in seconds to wait for a response before timing
                         out.  [default: 5.0]
    --wait / --no-wait   Wait for the action to be completed otherwise return as
                         soon as it's scheduled.
    -h, --help           Show this message and exit.

All help strings have the same format and consist of three parts:

  * A usage line describing how to invoke and the accepted parameters
  * A description of the commands functionality
  * A list of the available options

The ``[OPTIONS]`` and ``[PROCESSES]...`` tags in the usage description, denote the 'parameters' that the command takes.
A more detailed description of the available options will be listed after the description of the commands functionality
The positional arguments will only be described in the command description itself.
For a more detailed explanation of the difference between options and arguments, see the section about command line :ref:`parameters<cli_parameters>`.


.. _cli_parameters:

Parameters
----------
Most of the ``verdi`` commands and their subcommands can take one or multiple parameters.
In the language of command line interfaces, these parameters come in two flavors:

  * Options
  * Arguments

Arguments are positional parameters, whereas options are indicated by a flag that precedes the value, typically of the form ``-f``, or ``--flag``.
The command line :ref:`help string<cli_help_strings>` section explained that each command will have a help string with a usage line, for example::

  Usage: verdi process kill [OPTIONS] [PROCESSES]...

The ``[OPTIONS]`` tag indicates that the command takes one or multiple options and one or multiple ``[PROCESSES]`` as arguments.
The square brackets in the usage line, indicate that the parameter is optional and not required.
Three dots ``...`` following a parameter indicate that it can not take just one, but also more than one values.


.. _cli_profile:

Profile
-------
AiiDA supports multiple profiles per installation, that can each be configured to use different databases.
One of these profiles will always be marked as the default profile.
To show the current default profile, execute the command::

  verdi profile list

The default profile will be highlighted.
By default, all ``verdi`` commands will always use the default profile.
Having to change the default profile, anytime one wants to apply the ``verdi`` command to another profile is cumbersome.
Therefore, each ``verdi`` command supports the ``-p/--profile`` option, that will force ``verdi`` to use the given profile.
For example, if you wanted to display the list of processes for a profile that is not the current default, you can execute::

  verdi -p <profile> process list

Note that the specified profile will be used for this and only this command.
All subsequent commands, when no specific profile is given, will return to using the default profile.


.. _cli_identifiers:

Identifiers
-----------
Many commands will support arguments or options that serve to identify specific entities in the database, such as nodes, users, groups etc.
Any entity in AiiDA typically will have three different types of identifier:

  * ``ID``: the integer primary key in the database
  * ``UUID``: the universally unique identifier, a dash-separated hexadecimal string
  * ``LABEL``: a custom string-based label

The ``ID`` and ``UUID`` identifiers follow the exact same rules for all the entities in AiiDA's data model.
However, the ``LABEL`` will vary from entity to entity.
For a ``Code`` instance it will be the ``label`` attribute, whereas for a ``Group`` instance, it will be its name.

All ``verdi`` command arguments and options that serve to pass an entity identifier, will automatically deduce the intended identifier type.
However, since the type of the value is lost over the command line (as each value will be passed as a string type), the command line will have to guess the type.
Each value will first be interpreted as an ``ID``.
If the value cannot be mapped to the ``ID`` of an entity, it will instead be considered a partial or full ``UUID``.
In the case where the identifier can be resolved to neither a valid ``ID`` nor a ``UUID``, the code will finally assume that the value should be interpreted as a ``LABEL``.
In almost all cases, this approach will be able to successfully and unambiguously determine the identifier type, however, there are exceptions.

Consider for example a database with the following three groups:

===  =====================================  ========
ID   UUID                                   LABEL
===  =====================================  ========
10   12dfb104-7b2b-4bca-adc0-1e4fd4ffcc88   group
11   deadbeef-62ba-444f-976d-31d925dac557   10
12   3df34a1e-5215-4e1a-b626-7f75b9586ef5   deadbeef
===  =====================================  ========

We would run into trouble if we wanted to identify the second group by its label ``10``, since it would first be interpreted as an ``ID``, which would return the first group instead.
Likewise, if we wanted to retrieve the third group by its label, we would get the second group instead, since the label ``deadbeef`` is also a valid partial UUID of the second group.
Finally, say we wanted to select the first group using its partial ``UUID`` ``12``, it would unfortunately match the third group on its ``ID`` instead.

Luckily, ``verdi`` provides the tools to break all of these ambiguities with guaranteed success.
The latter ambiguity, between an ``ID`` and ``UUID`` can always be resolved by passing a larger partial ``UUID``.
Inevitably, eventually a non-numeric character or a dash will be included in the partial ``UUID``, rendering it an invalid ``ID`` and the identifier will be cast to the right type.
The case of an identifier, that is intended to refer to a ``LABEL``, that just happens to also be a valid ``ID`` or ``UUID`` cannot be solved in this way.
For this case ``verdi`` reserves a special character, the exclamation mark ``!`` that can be appended to the identifier.
Before any type guessing is done, the command line will check for the presence of this marker, and if found will directly interpret the identifier as a ``LABEL``.
For example, to solve ambiguity problems of the first two examples given in this section, one would have had to pass ``10!`` and ``deadbeef!``.
The exclamation point would have forced them to be interpreted as a ``LABEL`` and ensured that the right group would be retrieved.

In summary, to guarantee correct identification of a specific type:

  * ``UUID``: include at least one non-numeric character or dash in the partial identifier
  * ``LABEL``: append an exclamation mark ``!`` at the end of the identifier


.. _cli_multi_value_options:

Multi value options
-------------------
The section on command line :ref:`parameters<cli_parameters>` explained that some commands support options and arguments that take one or multiple values.
This is fairly typical for command line arguments, but slightly more unorthodox for options, that typically only ever take one value, or none at all if it is a flag.
However, ``verdi`` has multiple commands where an option needs to be able to support options that take more than one value.
Take for example the ``verdi export create`` command, with part of its help string::

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

The file to which the export archive should be written is given by the argument ``OUTPUT_FILE`` and the command supports various identifier options, e.g. ``CODE...`` and ``NODE...``, that allow the user to specify which entities should be exported.
Note the terminal dots ``...`` that indicate that the options take one or more values.
In traditional command line interfaces, one would have to repeat the option flag if multiple values needed to be specified, e.g.::

  verdi export create -N 10 -N 11 -N 12 archive.aiida

However, for large numbers of values, this gets cumbersome, which is why ``verdi`` supports so-called multiple value options, that allow this to be rewritten as::

  verdi export create -N 10 11 12 archive.aiida

Unfortunately, this leads to an ambiguity, as the 'greedy' multi value option ``-N`` will interpret the argument ``archive.aiida`` as an option value.
This will cause the command to abort if the validation fails, but even worse it might be silently accepted.
The root of the problem is that the multi value option needs to necessarily be greedy and cannot distinguish which value belongs to it and which value is just another argument.
The typical solution for this problem is to use the so called 'endopts' marker, which is defined as two dashes ``--``, which can be used to mark the end of the options and clearly distinguish them from the arguments.
Note that this is also indicated by the usage string of the command where it shows ``[--]`` between the ``[OPTIONS]`` and ``OUTPUT_FILE`` parameters, meaning that the ``--`` endopts marker can optionally be used.
The previous command can therefore be made unambiguous as follows::

  verdi export create -N 10 11 12 -- archive.aiida

This time the parser will notice the ``--`` end options marker and correctly identify ``archive.aiida`` as the positional argument.


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
      reveal     Reveal one or more hidden codes to the `verdi code list`...
      setup      Setup a new Code.
      show       Display detailed information for the given CODE.


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

      Create visual representations of part of the provenance graph.

    Options:
      --help  Show this message and exit.

    Commands:
      generate  Generate a graph from a ROOT_NODE (specified by pk or uuid).


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
      tree         Show tree of nodes.


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
