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

    sudo apt-get install postgresql-9.1
    sudo apt-get install postgresql-server-dev-9.1
    sudo apt-get install postgresql-client-9.1

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
   Remember also to give it the right permissions (read and write): ``chmod u=rw .pgpass``.

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

How to move the physical location of a database
+++++++++++++++++++++++++++++++++++++++++++++++

It might happen that you need to move the physical location of the database
files on your hard-drive (for instance, due to the lack of space in the
partition where it is located). Below we explain how to do it.

.. _move_postgresql:

PostgreSQL move
---------------

First, make sure you have a backup of the full database (see instructions
:ref:`here<backup_postgresql>`), and that the AiiDA daemon is not running.
Then, become the UNIX ``postgres`` user, typing as root::

  su - postgres
  
(or, equivalently, type ``sudo su - postgres``, depending on your distribution).

Stop the postgres database daemon::

  service postgresql stop
  
Then enter the postgres shell::

  psql

and look for the current location of the data directory::

  SHOW data_directory;

Typically you should get something like ``/var/lib/postgresql/9.1/main``.

.. note :: If you are experiencing memory problems and cannot enter the postgres
	shell, you can look directly into the file ``/etc/postgresql/9.1/main/postgresql.conf``
	and check out the line defining the variable ``data_directory``.

Then exit the shell with ``\q``, go to this directory and copy all the
files to the new directory::

  cp -a SOURCE_DIRECTORY DESTINATION_DIRECTORY

where ``SOURCE_DIRECTORY`` is the directory you got from the
``SHOW data_directory;`` command, and ``DESTINATION_DIRECTORY`` is the new
directory for the database files.

Make sure the permissions, owner and group are the same in the old and new directory
(including all levels above the ``DESTINATION_DIRECTORY``). The owner and group
should be both ``postgres``, at the notable exception of some symbolic links in
``server.crt`` and ``server.key``.

.. note :: If the permissions of these links need to be changed, use the ``-h``
  option of ``chown`` to avoid changing the permissions of the destination of the
  links. In case you have changed the permission of the links destination by
  mistake, they should typically be (beware that this might depend on your 
  actual distribution!)::

    -rw-r--r-- 1 root root 989 Mar  1  2012 /etc/ssl/certs/ssl-cert-snakeoil.pem
    -rw-r----- 1 root ssl-cert 1704 Mar  1  2012 /etc/ssl/private/ssl-cert-snakeoil.key
    
Then you can change the postgres configuration file, that should typically
be located here::

   /etc/postgresql/9.1/main/postgresql.conf

Make a backup version of this file, then look for the line defining 
``data_directory`` and replace it with the new data directory path::

   data_directory = 'NEW_DATA_DIRECTORY'

Then start again the database daemon::

  service postgresql start

You can check that the data directory has indeed changed::

  psql
  SHOW data_directory;
  \q

Before removing definitely the previous location of the database files, 
first rename it and test AiiDA with the new database location (e.g. do simple
queries like ``verdi code list`` or create a node and store it). If 
everything went fine, you can delete the old database location.

How to backup the repository
++++++++++++++++++++++++++++
Apart from the database backup, you should also backup the AiiDA repository.
For small repositories, this can be easily done by a simple directory copy or,
even better, with the use of the rsync which can copy only the differences.
However, both of the aforementioned approaches are not efficient in big
repositories where even a partial recursive directory listing may take
significant time, especially for filesystems where accessing a directory has
a constant (and significant) latency time. Therefore, we provide scripts for 
making efficient backups of the AiiDA repository.

Before running the backup script, you will have to configure it. Therefore you
should execute the ``backup_setup.py`` which is located under
``MY_AIIDA_FOLDER/aiida/common/additions/backup_script``. For example::

	python MY_AIIDA_FOLDER/aiida/common/additions/backup_script/backup_setup.py

This will ask a set of questions. More precisely, it will initially ask for:

 * The backup folder. This is the destination of the backup *configuration file*.
   By default a folder named ``backup`` in your ``.aiida`` directory is
   proposed to be created.

 * The destination folder of the backup. This is the destination folder of the
   files to be backed up. By default it is a folder inside the aforementioned
   ``backup`` folder (e.g. ``~/.aiida/backup/backup_dest``).

.. note:: You should backup the repository on a different disk than the one in
  which you have the AiiDA repository! If you just use the same disk, you don't
  have any security against the most common data loss cause: disk failure.
  The best option is to use a destination folder mounted over ssh (google for instance
  for "sshfs" for more info).

A template backup configuration file (``backup_info.json.tmpl``) will be copied
in the backup folder. You can set the backup variables by yourself after renaming
the template file to ``backup_info.json``, or you can answer the questions asked
by the script, and then ``backup_info.json`` will be created based on you answers.

The main script backs up the AiiDA repository that is referenced by the current
AiiDA database. The script will start from the ``oldest_object_backedup`` date
or the date of the oldest node/workflow object found and it will periodically
backup (in periods of ``periodicity`` days) until the ending date of the backup
specified by ``end_date_of_backup`` or ``days_to_backup``

The backup parameters to be set in the ``backup_info.json`` are:

 * ``periodicity`` (in days): The backup runs periodically for a number of days
   defined in the periodicity variable. The purpose of this variable is to limit
   the backup to run only on a few number of days and therefore to limit the
   number of files that are backed up at every round. e.g. ``"periodicity": 2``
   Example: if you have files in the AiiDA repositories created in the past 30
   days, and periodicity is 15, the first run will backup the files of the first
   15 days; a second run of the script will backup the next 15 days, completing
   the backup (if it is run within the same day). Further runs will only backup
   newer files, if they are created.

 * ``oldest_object_backedup`` (timestamp or null): This is the timestamp of the
   oldest object that was backed up. If you are not aware of this value or if it
   is the first time that you start a backup up for this repository, then set
   this value to ``null``. Then the script will search the creation date of the
   oldest workflow or node object in the database and it will start
   the backup from that date. E.g. ``"oldest_object_backedup": "2015-07-20 11:13:08.145804+02:00"``

 * ``end_date_of_backup``: If set, the backup script will backup files that
   have a modification date until the value specified by this variable. If not set,
   the ending of the backup will be set by the following variable
   (``days_to_backup``) which specifies how many days to backup from the start
   of the backup. If none of these variables are set (``end_date_of_backup``
   and ``days_to_backup``), then the end date of backup is set to the current date.
   E.g. ``"end_date_of_backup": null`` or ``"end_date_of_backup": "2015-07-20 11:13:08.145804+02:00"``


 * ``days_to_backup``: If set, you specify how many days you will backup from the starting date
   of your backup. If it set to ``null`` and also
   ``end_date_of_backup`` is set to ``null``, then the end date of the backup is set
   to the current date. You can not set ``days_to_backup`` & ``end_date_of_backup``
   at the same time (it will lead to an error). E.g. ``"days_to_backup": null``
   or ``"days_to_backup": 5``

 * ``backup_length_threshold`` (in hours): The backup script runs in rounds and
   on every round it backs-up a number of days that are controlled primarily by
   ``periodicity`` and also by ``end_date_of_backup`` / ``days_to_backup``,
   for the last backup round. The ``backup_length_threshold`` specifies the
   lowest acceptable round length. This is important for the end of the backup.

 * ``backup_dir``: The destination directory of the backup. e.g.
   ``"backup_dir": "/scratch/aiida_user/backup_script_dest"``

To start the backup, run the ``start_backup.py`` script. Run as often as needed to complete a
full backup, and then run it periodically (e.g. calling it from a cron script, for instance every
day) to backup new changes.
