.. _reference:command-line:

******************
AiiDA Command Line
******************

.. _reference:command-line:verdi:

Commands
========
Below is a list with all available subcommands.

.. _reference:command-line:verdi-archive:

``verdi archive``
-----------------

.. code:: console

    Usage:  [OPTIONS] COMMAND [ARGS]...

      Create, inspect and import AiiDA archives.

    Options:
      --help  Show this message and exit.

    Commands:
      create   Create an archive from all or part of a profiles's data.
      import   Import archived data to a profile.
      info     Summarise the contents of an archive.
      migrate  Migrate an archive to a more recent schema version.
      version  Print the current version of an archive's schema.


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
      remotecat     Show the contents of a file in the remote working directory.
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
      create     Create a new code.
      delete     Delete a code.
      duplicate  Duplicate a code allowing to change some parameters.
      export     Export code to a yaml file.
      hide       Hide one or more codes from `verdi code list`.
      list       List the available codes.
      relabel    Relabel a code.
      reveal     Reveal one or more hidden codes in `verdi code list`.
      setup      Setup a new code (use `verdi code create`). (DEPRECATED: Please use `verdi
                 code create` instead.)
      show       Display detailed information for a code.
      test       Run tests for the given code to check whether it is usable.


.. _reference:command-line:verdi-computer:

``verdi computer``
------------------

.. code:: console

    Usage:  [OPTIONS] COMMAND [ARGS]...

      Setup and manage computers.

    Options:
      --help  Show this message and exit.

    Commands:
      configure  Configure the transport for a computer and user.
      delete     Delete a computer.
      disable    Disable the computer for the given user.
      duplicate  Duplicate a computer allowing to change some parameters.
      enable     Enable the computer for the given user.
      export     Export the setup or configuration of a computer.
      list       List all available computers.
      relabel    Relabel a computer.
      setup      Create a new computer.
      show       Show detailed information for a computer.
      test       Test the connection to a computer.


.. _reference:command-line:verdi-config:

``verdi config``
----------------

.. code:: console

    Usage:  [OPTIONS] COMMAND [ARGS]...

      Manage the AiiDA configuration.

    Options:
      --help  Show this message and exit.

    Commands:
      caching    List caching-enabled process types for the current profile.
      downgrade  Print a configuration, downgraded to a specific version.
      get        Get the value of an AiiDA option for the current profile.
      list       List AiiDA options for the current profile.
      set        Set an AiiDA option.
      show       Show details of an AiiDA option for the current profile.
      unset      Unset an AiiDA option.


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
      worker   Run a single daemon worker in the current interpreter.


.. _reference:command-line:verdi-data:

``verdi data``
--------------

.. code:: console

    Usage:  [OPTIONS] COMMAND [ARGS]...

      Inspect, create and manage data nodes.

    Options:
      -v, --verbosity [notset|debug|info|report|warning|error|critical]
                                      Set the verbosity of the output.
      --help                          Show this message and exit.


.. _reference:command-line:verdi-devel:

``verdi devel``
---------------

.. code:: console

    Usage:  [OPTIONS] COMMAND [ARGS]...

      Commands for developers.

    Options:
      --help  Show this message and exit.

    Commands:
      check-load-time          Check for common indicators that slowdown `verdi`.
      check-undesired-imports  Check that verdi does not import python modules it shouldn't.
      launch-add               Launch an ``ArithmeticAddCalculation``.
      launch-multiply-add      Launch a ``MultipylAddWorkChain``.
      rabbitmq                 Commands to interact with RabbitMQ.
      run-sql                  Run a raw SQL command on the profile database (only...
      validate-plugins         Validate all plugins by checking they can be loaded.


.. _reference:command-line:verdi-group:

``verdi group``
---------------

.. code:: console

    Usage:  [OPTIONS] COMMAND [ARGS]...

      Create, inspect and manage groups of nodes.

    Options:
      --help  Show this message and exit.

    Commands:
      add-nodes     Add nodes to a group.
      copy          Duplicate a group.
      create        Create an empty group with a given label.
      delete        Delete groups and (optionally) the nodes they contain.
      description   Change the description of a group.
      dump          Dump data of an AiiDA group to disk.
      list          Show a list of existing groups.
      move-nodes    Move the specified NODES from one group to another.
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
      list         Query all nodes with optional filtering and ordering.
      rehash       Recompute the hash for nodes in the database.
      repo         Inspect the content of a node repository folder.
      show         Show generic information on one or more nodes.


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


.. _reference:command-line:verdi-presto:

``verdi presto``
----------------

.. code:: console

    Usage:  [OPTIONS]

      Set up a new profile in a jiffy.

      This command aims to make setting up a new profile as easy as possible. It does not
      require any services, such as PostgreSQL and RabbitMQ. It intentionally provides only a
      limited amount of options to customize the profile and by default does not require any
      options to be specified at all. To create a new profile with full control over its
      configuration, please use `verdi profile setup` instead.

      After running `verdi presto` you can immediately start using AiiDA without additional
      setup. The command performs the following actions:

      * Create a new profile that is set as the new default
      * Create a default user for the profile (email can be configured through the `--email` option)
      * Set up the localhost as a `Computer` and configure it
      * Set a number of configuration options with sensible defaults

      By default the command creates a profile that uses SQLite for the database. It
      automatically checks for RabbitMQ running on the localhost, and, if it can connect,
      configures that as the broker for the profile. Otherwise, the profile is created without
      a broker, in which case some functionality will be unavailable, most notably running the
      daemon and submitting processes to said daemon.

      When the `--use-postgres` flag is toggled, the command tries to connect to the
      PostgreSQL server with connection paramaters taken from the `--postgres-hostname`,
      `--postgres-port`, `--postgres-username` and `--postgres-password` options. It uses
      these credentials to try and automatically create a user and database. If successful,
      the newly created profile uses the new PostgreSQL database instead of SQLite.

    Options:
      -p, --profile-name TEXT         Name of the profile. By default, a unique name starting
                                      with `presto` is automatically generated.  [default:
                                      (dynamic)]
      --email TEXT                    Email of the default user.  [default: (dynamic)]
      --use-postgres                  When toggled on, the profile uses a PostgreSQL database
                                      instead of an SQLite one. The connection details to the
                                      PostgreSQL server can be configured with the relevant
                                      options. The command attempts to automatically create a
                                      user and database to use for the profile, but this can
                                      fail depending on the configuration of the server.
      --postgres-hostname TEXT        The hostname of the PostgreSQL server.
      --postgres-port INTEGER         The port of the PostgreSQL server.
      --postgres-username TEXT        The username of the PostgreSQL user that is authorized
                                      to create new databases.
      --postgres-password TEXT        The password of the PostgreSQL user that is authorized
                                      to create new databases.
      -n, --non-interactive / -I, --interactive
                                      Never prompt, such as for sudo password.  [default:
                                      (--interactive)]
      --help                          Show this message and exit.


.. _reference:command-line:verdi-process:

``verdi process``
-----------------

.. code:: console

    Usage:  [OPTIONS] COMMAND [ARGS]...

      Inspect and manage processes.

    Options:
      --help  Show this message and exit.

    Commands:
      call-root  Show root process of processes.
      dump       Dump process input and output files to disk.
      kill       Kill running processes.
      list       Show a list of processes.
      pause      Pause running processes.
      play       Play (unpause) paused processes.
      repair     Automatically repair all stuck processes.
      report     Show the log report of processes.
      show       Show details of processes.
      status     Show the status of processes.
      watch      Watch the state transitions of processes.


.. _reference:command-line:verdi-profile:

``verdi profile``
-----------------

.. code:: console

    Usage:  [OPTIONS] COMMAND [ARGS]...

      Inspect and manage the configured profiles.

    Options:
      --help  Show this message and exit.

    Commands:
      configure-rabbitmq  Configure RabbitMQ for a profile.
      delete              Delete one or more profiles.
      dump                Dump all data in an AiiDA profile's storage to disk.
      list                Display a list of all available profiles.
      rename              Rename a profile.
      set-default         Set a profile as the default profile.
      setdefault          Set a profile as the default profile. (DEPRECATED: Please use `verdi
                          profile set-default` instead.)
      setup               Set up a new profile.
      show                Show details for a profile.


.. _reference:command-line:verdi-quicksetup:

``verdi quicksetup``
--------------------

.. code:: console

    Usage:  [OPTIONS]

      Setup a new profile in a fully automated fashion. (DEPRECATED: This command is
      deprecated. For a fully automated alternative, use `verdi presto --use-postgres`
      instead. For full control, use `verdi profile setup core.psql_dos`.)

    Options:
      -n, --non-interactive / -I, --interactive
                                      In non-interactive mode, the CLI never prompts for
                                      options but simply uses default values for options that
                                      define one. In interactive mode, the CLI will prompt for
                                      each interactive option.   [default: (--interactive)]
      --profile PROFILE               The name of the new profile.  [required]
      --email EMAIL                   Email address associated with the data you generate. The
                                      email address is exported along with the data, when
                                      sharing it.  [required]
      --first-name NONEMPTYSTRING     First name of the user.  [required]
      --last-name NONEMPTYSTRING      Last name of the user.  [required]
      --institution NONEMPTYSTRING    Institution of the user.  [required]
      --db-engine [postgresql_psycopg|postgresql_psycopg2]
                                      Engine to use to connect to the database. (deprecated)
      --db-backend [core.psql_dos]    Database backend to use.  [required]
      --db-host HOSTNAME              Database server host. Leave empty for "peer"
                                      authentication.  [required]
      --db-port INTEGER               Database server port.  [required]
      --db-name NONEMPTYSTRING        Name of the database to create.
      --db-username NONEMPTYSTRING    Name of the database user to create.
      --db-password TEXT              Password of the database user.
      --su-db-name TEXT               Name of the template database to connect to as the
                                      database superuser.
      --su-db-username TEXT           User name of the database super user.
      --su-db-password TEXT           Password to connect as the database superuser.
      --broker-protocol [amqp|amqps]  Protocol to use for the message broker.  [default: amqp]
      --broker-username NONEMPTYSTRING
                                      Username to use for authentication with the message
                                      broker.  [default: guest]
      --broker-password NONEMPTYSTRING
                                      Password to use for authentication with the message
                                      broker.  [default: guest]
      --broker-host HOSTNAME          Hostname for the message broker.  [default: 127.0.0.1]
      --broker-port INTEGER           Port for the message broker.  [default: 5672]
      --broker-virtual-host TEXT      Name of the virtual host for the message broker without
                                      leading forward slash.  [default: ""]
      --repository DIRECTORY          Absolute path to the file repository.
      --test-profile                  Designate the profile to be used for running the test
                                      suite only.
      --config FILEORURL              Load option values from configuration file in yaml
                                      format (local path or URL).
      --help                          Show this message and exit.


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
      --help                   Show this message and exit.


.. _reference:command-line:verdi-run:

``verdi run``
-------------

.. code:: console

    Usage:  [OPTIONS] [--] FILEPATH [VARARGS]...

      Execute scripts with preloaded AiiDA environment.

    Options:
      --auto-group                    Enables the autogrouping
      -l, --auto-group-label-prefix TEXT
                                      Specify the prefix of the label of the auto group
                                      (numbers might be automatically appended to generate
                                      unique names per run).
      -e, --exclude STR...            Exclude these classes from auto grouping (use full
                                      entrypoint strings).
      -i, --include STR...            Include these classes from auto grouping (use full
                                      entrypoint strings or "all").
      --help                          Show this message and exit.


.. _reference:command-line:verdi-setup:

``verdi setup``
---------------

.. code:: console

    Usage:  [OPTIONS]

      Setup a new profile (use `verdi profile setup`).

      This method assumes that an empty PSQL database has been created and that the database
      user has been created. (DEPRECATED: Please use `verdi profile setup` instead.)

    Options:
      -n, --non-interactive / -I, --interactive
                                      In non-interactive mode, the CLI never prompts for
                                      options but simply uses default values for options that
                                      define one. In interactive mode, the CLI will prompt for
                                      each interactive option.   [default: (--interactive)]
      --profile PROFILE               The name of the new profile.  [required]
      --email EMAIL                   Email address associated with the data you generate. The
                                      email address is exported along with the data, when
                                      sharing it.  [required]
      --first-name NONEMPTYSTRING     First name of the user.  [required]
      --last-name NONEMPTYSTRING      Last name of the user.  [required]
      --institution NONEMPTYSTRING    Institution of the user.  [required]
      --db-engine [postgresql_psycopg|postgresql_psycopg2]
                                      Engine to use to connect to the database. (deprecated)
      --db-backend [core.psql_dos]    Database backend to use.  [required]
      --db-host HOSTNAME              Database server host. Leave empty for "peer"
                                      authentication.  [required]
      --db-port INTEGER               Database server port.  [required]
      --db-name NONEMPTYSTRING        Name of the database to create.  [required]
      --db-username NONEMPTYSTRING    Name of the database user to create.  [required]
      --db-password TEXT              Password of the database user.  [required]
      --broker-protocol [amqp|amqps]  Protocol to use for the message broker.  [required]
      --broker-username NONEMPTYSTRING
                                      Username to use for authentication with the message
                                      broker.  [required]
      --broker-password NONEMPTYSTRING
                                      Password to use for authentication with the message
                                      broker.  [required]
      --broker-host HOSTNAME          Hostname for the message broker.  [required]
      --broker-port INTEGER           Port for the message broker.  [required]
      --broker-virtual-host TEXT      Name of the virtual host for the message broker without
                                      leading forward slash.  [required]
      --repository DIRECTORY          Absolute path to the file repository.  [required]
      --test-profile                  Designate the profile to be used for running the test
                                      suite only.
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
      -t, --print-traceback  Print the full traceback in case an exception is raised.
      --no-rmq               Do not check RabbitMQ status
      --help                 Show this message and exit.


.. _reference:command-line:verdi-storage:

``verdi storage``
-----------------

.. code:: console

    Usage:  [OPTIONS] COMMAND [ARGS]...

      Inspect and manage stored data for a profile.

    Options:
      --help  Show this message and exit.

    Commands:
      backup     Backup the data storage of a profile.
      info       Summarise the contents of the storage.
      integrity  Checks for the integrity of the data storage.
      maintain   Performs maintenance tasks on the repository.
      migrate    Migrate the storage to the latest schema version.
      version    Print the current version of the storage schema.


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
