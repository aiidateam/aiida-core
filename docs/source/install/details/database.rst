.. _database:

Database
========
AiiDA needs a database backend to store the nodes, node attributes and other
information, allowing the end user to perform very fast queries of the results.
Currently, only `PostgreSQL`_ is allowed as a database backend.


Setup instructions
------------------

In order for AiiDA to be able to use postgres it needs to be installed first.
On Ubuntu and other Debian derivative distributions this can be accomplished with::

    $ sudo apt-get install postgresql postgresql-server-dev-all postgresql-client

For Mac OS X, binary packages can be downloaded from the official website of `PostgreSQL`_ or you can use ``brew``::

    $ brew install postgresql
    $ pg_ctl -D /usr/local/var/postgres start

To manually create a database for AiiDA that will later be used in the configuration with ``verdi setup``, you should follow these instructions.
First you will need to run the program ``psql`` to interact with postgres and you have to do so as the ``postgres`` user that was created upon installing the software.
To assume the role of ``postgres`` run as root::

    $ su - postgres

and launch the postgres program::

    $ psql

Create a new database user account for AiiDA by running::

    CREATE USER aiida WITH PASSWORD '<password>';

replacing ``<password>`` with a password of your choice.
Make sure to remember it, as you will need it again when you configure AiiDA to use this database through ``verdi setup``.
If you want to change the password you just created use the command::

    ALTER USER aiida PASSWORD '<password>';

Next we create the database itself::

    CREATE DATABASE aiidadb OWNER aiida;

and grant all privileges on this DB to the previously-created ``aiida`` user::

    GRANT ALL PRIVILEGES ON DATABASE aiidadb to aiida;

You have now created a database for AiiDA and you can close the postgres shell by typing ``\q``.
To test if the database was created successfully, you can run the following command as a regular user in a bash terminal::

    $ psql -h localhost -d aiidadb -U aiida -W

and type the password you inserted before, when prompted.
If everything worked well, you should get no error and see the prompt of the ``psql`` shell.

If you uses the same names used in the example commands above, during the ``verdi setup`` phase you want to use the following parameters to use the database you just created::

    Database engine: postgresql_psycopg2
    PostgreSQL host: localhost
    PostgreSQL port: 5432
    AiiDA Database name: aiidadb
    AiiDA Database user: aiida
    AiiDA Database password: <password>

.. note:: Do not forget to backup your database (instructions :ref:`here<backup_postgresql>`).

.. note:: If you want to move the physical location of the data files
  on your hard drive AFTER it has been created and filled, look at the
  instructions :ref:`here<move_postgresql>`.

.. note:: Due to the presence of a bug, PostgreSQL could refuse to restart after a crash,
  or after a restore from binary backup. The workaround given below is adapted from `here`_.
  The error message would be something like::

    * Starting PostgreSQL 9.1 database server
    * The PostgreSQL server failed to start. Please check the log output:
    2015-05-26 03:27:20 UTC [331-1] LOG:  database system was interrupted; last known up at 2015-05-21 19:56:58 UTC
    2015-05-26 03:27:20 UTC [331-2] FATAL:  could not open file "/etc/ssl/certs/ssl-cert-snakeoil.pem": Permission denied
    2015-05-26 03:27:20 UTC [330-1] LOG:  startup process (PID 331) exited with exit code 1
    2015-05-26 03:27:20 UTC [330-2] LOG:  aborting startup due to startup process failure

  If this happens you should change the permissions on any symlinked files
  to being writable by the Postgres user. For example, on Ubuntu, with PostgreSQL 9.1,
  the following should work (**WARNING**: Make sure these configuration files are
  symbolic links before executing these commands! If someone has customized the server.crt
  or server.key file, you can erase them by following these steps.
  It's a good idea to make a backup of the server.crt and server.key files before removing them)::

    (as root)
    # go to PGDATA directory
    cd /var/lib/postgresql/9.1/main
    ls -l server.crt server.key
    # confirm both of those files are symbolic links
    # to files in /etc/ssl before going further
    # remove symlinks to SSL certs
    rm server.crt
    rm server.key
    # copy the SSL certs to the local directory
    cp /etc/ssl/certs/ssl-cert-snakeoil.pem server.crt
    cp /etc/ssl/private/ssl-cert-snakeoil.key server.key
    # set permissions on ssl certs
    # and postgres ownership on everything else
    # just in case
    chown postgres *
    chmod 640 server.crt server.key

    service postgresql start


.. _here: https://wiki.postgresql.org/wiki/May_2015_Fsync_Permissions_Bug


Alternative setup instructions
------------------------------

Instead of using passwords which could be used by users on the same machine to access the database,
PostgreSQL allows password-less logins via unix sockets. In this scenario PostgreSQL compares the
user connecting to the socket with its own database of users and will allow a connection if a matching
user exists.

First install the packages as described above and make sure that the PostgreSQL daemon is running, 
then assume the role of ``postgres`` by running the following as root::

    $ su - postgres

Create a database user with the **same name** as the user you are using to run AiiDA (usually your login name)::

    $ createuser <username>

replacing ``<username>`` with your username.

Next create the database itself making sure that your user is the owner::

    $ createdb -O <username> aiidadb

To test if the database was created successfully, you can run the following command as your user in a bash terminal::

    $ psql aiidadb


Make sure to leave the host, port and password empty when specifiying the parameters during the ``verdi setup`` phase
and specify your username as the *AiiDA Database user*::

    Database engine: postgresql_psycopg2
    PostgreSQL host: 
    PostgreSQL port: 
    AiiDA Database name: aiidadb
    AiiDA Database user: <username>
    AiiDA Database password:


.. _PostgreSQL: https://www.postgresql.org/downloads
