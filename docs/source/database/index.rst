===================
Databases for AiiDA
===================
AiiDA needs a database backend to store the nodes, node attributes and other
information, allowing the end user to perform very fast queries of the results.

Before installing AiiDA, you have to choose (and possibly configure) a suitable
supported backend.

Supported databases
+++++++++++++++++++
.. note:: For those who do not want to read all this section, the short answer
 if you want to choose a database is SQLite if you just want to try out AiiDA
 without spending too much time in configuration (but SQLite is not suitable
 for production runs), while PostgreSQL for regular production use of AiiDA.

For those who are interested in the details, there
are three supported database backends:

* `SQLite`_ The SQLite backend is the fastest to configure: in fact, it does
  not really use a "real" database, but stores everything in a file.
  This is great if you never configured a database before and you just want
  to give AiiDA a try. However, keep in mind that it has **many big
  shortcomings** for a real AiiDA usage!

  In fact, since everything is stored on a single file, each access (especially
  when writing or doing a transaction) to the database locks it: this means
  that a second thread wanting to access the database has to wait that the
  lock is released. We set up a timeout of about 60 seconds for each thread to
  retry to connect to the database, but after that time you will get an
  exception, with the risk of storing corrupted data in the AiiDA repository.

  Therefore, it is OK to use SQLite for testing, but as soon as you want to use
  AiiDA in production, with more than one calculation submitted at each given
  time, please switch to a real database backend, like PostgreSQL.

  .. note:: note, however, that typically SQLite is pretty fast for queries,
    once the database is loaded into memory, so it could be an interesting
    solution if you do not want to launch new calculations, but only to
    import the results and then query them (in a single-user approach).

* `PostgreSQL`_ This is the database backend that the we, the AiiDA developers,
  suggest to use, because it is the one with most features.

* `MySQL`_ This is another possible backend that you could use. However, we
  suggest that you use PostgreSQL instead of MySQL, due to some MySQL
  limitations (unless you have very strong reasons to prefer MySQL over
  PostgreSQL).
  In particular, some of the limitations of MySQL are:

  * Only a precision of 1 second is possible for time objects, while PostgreSQL
    supports microsecond precision. This can be relevant for a proper sorting
    of calculations launched almost simultaneously.

  * Indexed text columns can have an hardcoded maximum length. This can give
    issues with attributes, if you have very long key names or nested
    dictionaries/lists. These cannot be natively stored and therefore you
    either end up storing a JSON (therefore partially losing query capability)
    or you can even incur in problems.


.. _SQLite: http://www.sqlite.org/
.. _PostgreSQL: http://www.postgresql.org/
.. _MySQL: http://www.mysql.com/

Setup instructions
++++++++++++++++++
For any database, you may need to install a specific python package using
``pip``; this typically also requires to have the development libraries
installed (the ``.h`` C header files). Refer to the
:doc:`installation documentation <../installation>` for more details.

SQLite
------
To use SQLite as backend, please install::

  sudo apt-get install libsqlite3-dev

SQLite requires almost no configuration. In the ``verdi install`` phase,
just type ``sqlite`` when the ``Database engine`` is required,
and then provide an absolute path
for the ``AiiDA Database location`` field, that will be the file that
will store the full database (if
no file exists yet in that position, a fresh AiiDA database will be created).

.. note:: Do not forget to backup your database (instructions :ref:`here<backup_sqlite>`).

PostgreSQL
----------
.. note:: We assume here that you already installed PostgreSQL on your computer and that
  you know the password for the ``postgres`` user
  (there are many tutorials online that explain how to do it,
  depending on your operating system and distribution).
  To install PostgreSQL under Ubuntu, you can do::

    sudo apt-get install postgresql postgresql-server-dev-all postgresql-client

  On Mac OS X, you can download binary packages to install PostgreSQL
  from the official website.

To properly configure a new database for AiiDA with PostgreSQL, you need to
create a new ``aiida`` user and a new ``aiidadb`` table.

To create the new ``aiida`` user and the ``aiidadb`` database, first
become the UNIX ``postgres`` user, typing as root::

  su - postgres

(or equivalently type ``sudo su - postgres``, depending on your distribution).

Then type the following command to enter in the PostgreSQL shell in the
modality to create users::

  psql template1

To create a new user for postgres (you can call it simply ``aiida``, as in the
example below), type in the ``psql`` shell::

  CREATE USER aiida WITH PASSWORD 'the_aiida_password';

where of course you have to change ``the_aiida_password`` with a valid password.

.. note:: Remember, however, that since AiiDA needs to connect to this database,
  you will need to store this password in clear text in your home folder
  for each user that wants to have direct access to the database, therefore
  choose a strong password, but different from any that you already use!

.. note:: Did you just copy and paste the line above, therefore setting the
  password to ``the_aiida_password``? Then, let's change it! Choose a good
  password this time, and then type the following command (this time replacing
  the string ``new_aiida_password`` with the password you chose!)::

    ALTER USER aiida PASSWORD 'new_aiida_password';

Then create a new ``aiidadb`` database for AiiDA, and give ownership to user ``aiida`` created above::

  CREATE DATABASE aiidadb OWNER aiida;

and grant all privileges on this DB to the previously-created ``aiida`` user::

  GRANT ALL PRIVILEGES ON DATABASE aiidadb to aiida;

Finally, type ``\q`` to quit the ``template1`` shell, and ``exit`` to exit the PostgreSQL shell.

To test if this worked, type this on a bash terminal (as a normal user)::

  psql -h localhost -d aiidadb -U aiida -W

and type the password you inserted before, when prompted.
If everything worked, you should get no error and the ``psql`` shell.
Type ``\q`` to exit.

If you use the names suggested above, in the ``verdi install`` phase
you should use the following parameters::

  Database engine: postgresql
  PostgreSQL host: localhost
  PostgreSQL port: 5432
  AiiDA Database name: aiidadb
  AiiDA Database user: aiida
  AiiDA Database password: the_aiida_password

.. note:: Do not forget to backup your database (instructions :ref:`here<backup_postgresql>`).

.. note:: If you want to move the physical location of the data files
  on your hard drive AFTER it has been created and filled, look at the
  instructions :ref:`here<move_postgresql>`.

.. note:: Due to the presence of a bug, PostgreSQL could refuse to restart after a crash.
  If this happens you should follow the instructions written `here`_.

.. _here: https://wiki.postgresql.org/wiki/May_2015_Fsync_Permissions_Bug/

MySQL
-----
To use properly configure a new database for AiiDA with MySQL, you need to
create a new ``aiida`` user and a new ``aiidadb`` table.

We assume here that you already installed MySQL on your computer and that
you know your MySQL root password (there are many tutorials online that explain
how to do it, depending on your operating system and distribution). To install
mysql-client, you can do::

  sudo apt-get install libmysqlclient-dev

After MySQL is installed, connect to it as the MySQL root account to create
a new account. This can be done typing in the shell::

  mysql -h localhost mysql -u root -p

(we are assuming that you installed the database on ``localhost``, even if this
is not strictly required - if this is not the case, change ``localhost``
with the proper database host, but note that also some of the commands
reported below need to be adapted) and then type the MySQL root password when
prompted.

In the MySQL shell, type the following command to create a new user::

  CREATE USER 'aiida'@'localhost' IDENTIFIED BY 'the_aiida_password';

where of course you have to change ``the_aiida_password`` with a valid password.

.. note:: Remember, however, that since AiiDA needs to connect to this database,
  you will need to store this password in clear text in your home folder
  for each user that wants to have direct access to the database, therefore
  choose a strong password, but different from any that you already use!

Then, still in the MySQL shell, create a new database named ``aiida`` using the
command::

  CREATE DATABASE aiidadb;

and give all privileges to the ``aiida`` user on this database::

  GRANT ALL PRIVILEGES on aiidadb.* to aiida@localhost;

.. note:: ''(only for developers)'' If you are a developer and want to run
  the tests using the MySQL database (to do so, you also have to set the
  ``tests.use_sqlite`` AiiDA property to False using the
  ``verdi devel setproperty tests.use_sqlite False`` command), you also have
  to create a ``test_aiidadb`` database. In this case, run also the two
  following commands::

    CREATE DATABASE test_aiidadb;
    GRANT ALL PRIVILEGES on test_aiidadb.* to aiida@localhost;

If you use the names suggested above, in the ``verdi install`` phase
you should use the following parameters::

  Database engine: mysql
  mySQL host: localhost
  mySQL port: 3306
  AiiDA Database name: aiidadb
  AiiDA Database user: aiida
  AiiDA Database password: the_aiida_passwd

.. note:: Do not forget to backup your database (instructions :ref:`here<backup_mysql>`).

