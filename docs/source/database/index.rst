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

    sudo apt-get install postgresql-9.1
    sudo apt-get install postgresql-client-9.1

  On Mac OS X, you can download binary packages to install PostgreSQL 
  from the official website. 
    
To properly configure a new database for AiiDA with PostgreSQL, you need to
create a new ``aiida`` user and a new ``aiidadb`` table.

To create the new ``aiida`` user and the ``aiidadb`` database, first 
become the UNIX ``postgres`` user, typing as root::

  su - postgres
  
(or equivalently type ``sudo su - postgres``, according on your distribution).

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

MySQL
-----
To use properly configure a new database for AiiDA with MySQL, you need to
create a new ``aiida`` user and a new ``aiidadb`` table.

We assume here that you already installed MySQL on your computer and that 
you know your MySQL root password (there are many tutorials online that explain
how to do it, depending on your operating system and distribution).

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

How to backup the databases
+++++++++++++++++++++++++++

It is strongly advised to backup the content of your database daily. Below are 
instructions to set this up for the SQLite, PostgreSQL and MySQL databases, under Ubuntu 
(tested with version 12.04).

.. _backup_sqlite:

SQLite backup
-------------

.. note:: perform the following operation after having set up AiiDA. Only then
  the ``~/.aiida`` folder (and the files within) will be created.

Simply make sure your database folder (typically /home/USERNAME/.aiida/ containing 
the file ``aiida.db`` and the ``repository`` directory) is properly backed up by 
your backup software (under Ubuntu, Backup -> check the "Folders" tab).

.. _backup_postgresql:

PostgreSQL backup
-----------------

.. note:: perform the following operation after having set up AiiDA. Only then
  the ``~/.aiida`` folder (and the files within) will be created.

The database files are not put in the ``.aiida`` folder but in the system directories
which typically are not backed up. Moreover, the database is spread over lots of files
that, if backed up as they are at a given time, cannot be re-used to restore the database.

So you need to periodically (typically once a day) dump the database contents in a file
that will be backed up. 
This can be done by the following bash script
:download:`backup_postgresql.sh<backup_postgresql.sh>`::

	#!/bin/bash
	AIIDAUSER=aiida
	AIIDADB=aiidadb
	AIIDAPORT=5432
	## STORE THE PASSWORD, IN THE PROPER FORMAT, IN THE ~/.pgpass file
	## see http://www.postgresql.org/docs/current/static/libpq-pgpass.html
	AIIDALOCALTMPDUMPFILE=~/.aiida/${AIIDADB}-backup.psql.gz
	
	
	if [ -e ${AIIDALOCALTMPDUMPFILE} ]
	then
	    mv ${AIIDALOCALTMPDUMPFILE} ${AIIDALOCALTMPDUMPFILE}~
	fi
	
	# NOTE: password stored in ~/.pgpass, where pg_dump will read it automatically
	pg_dump -h localhost -p $AIIDAPORT -U $AIIDAUSER $AIIDADB | gzip > $AIIDALOCALTMPDUMPFILE || rm $AIIDALOCALTMPDUMPFILE
    

Before launching the script you need to create the file ``~/.pgpass`` to avoid having to enter your database 
password each time you use the script. It should look like (:download:`.pgpass<pgpass>`)::

    localhost:5432:aiidadb:aiida:YOUR_DATABASE_PASSWORD

where ``YOUR_DATABASE_PASSWORD`` is the password you set up for the database.

.. note:: Do not forget to put this file in ~/ and to name it ``.pgpass``.
   Remember also to give it the right permissions (read and write): ``chmod u+rw .pgpass``.

To dump the database in a file automatically everyday, you can add the following script 
:download:`backup-aiidadb-USERNAME<backup-aiidadb-USERNAME>` in ``/etc/cron.daily/``, which will
launch the previous script once per day::

    #!/bin/bash
    su USERNAME -c "/home/USERNAME/.aiida/backup_postgresql.sh"

where all instances of ``USERNAME`` are replaced by your actual user name. The ``su USERNAME``
makes the dumped file be owned by you rather than by ``root``.
Remember to give the script the right permissions::

  sudo chmod +x /etc/cron.daily/backup-aiidadb-USERNAME

Finally make sure your database folder (``/home/USERNAME/.aiida/``) containing this dump file
and the ``repository`` directory, is properly backed up by 
your backup software (under Ubuntu, Backup -> check the "Folders" tab).

.. _backup_mysql:

MySQL backup
------------

.. todo:: Back-up instructions for the MySQL database.

We do not have explicit instructions on how to back-up MySQL yet, but you
can find plenty of information on Google.

How to retrieve the database from a backup
------------------------------------------

PostgreSQL backup
-----------------

In order to retrieve the database from a backup, you have first to
create a empty database following the instructions described above in
"Setup instructions: PostgreSQL" except the ``verdi install``
phase. Once that you have created your empty database with the same
names of the backuped one, type the following command:: 

    psql -h localhost -U aiida -d aiidadb -f aiidadb-backup.psql
