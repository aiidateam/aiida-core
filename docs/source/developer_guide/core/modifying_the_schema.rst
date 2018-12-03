Mofidying the schema
++++++++++++++++++++

Django
------
The Django database schema can be found in :py:mod:`aiida.backends.djsite.db.models`.

If you need to change the database schema follow these steps:

1. Make all the necessary changes to :py:mod:`aiida.backends.djsite.db.models`
2. Create a new migration file.  From ``aiida/backends/djsite``, run::

     python manage.py makemigrations

   This will create the migration file in ``aiida/backends/djsite/db/migrations`` whose
   name begins with a number followed by some description.  If the description
   is not appropriate then change to it to something better but retain the
   number.

3. Open the generated file and make the following changes::

    from aiida.backends.djsite.db.migrations import upgrade_schema_version
    ...
    REVISION = # choose an appropriate version number (hint: higher than the last migration!)
    DOWN_REVISION = # the revision number of the previous migration
    ...
    class Migration(migrations.Migration):
      ...
      operations = [
        ..
        upgrade_schema_version(REVISION, DOWN_REVISION)
      ]

5. Change the ``LATEST_MIGRATION`` variable in
   ``aiida/backends/djsite/db/migrations/__init__.py`` to the name of your migration
   file::

     LATEST_MIGRATION = '0003_my_db_update'

   This let's AiiDA get the version number from your migration and make sure the
   database and the code are in sync.
6. Migrate your database to the new version, (again from ``aiida/backends/djsite``),
   run::

     python manage.py migrate


SQLAlchemy
----------
The SQLAlchemy database schema can be found in ``aiida/backends/sqlalchemy/models``

If you need to change the database schema follow these steps:

1. Make all the necessary changes to the model than you would like to modify
   located in the ``aiida/backends/sqlalchemy/models`` directory.
2. Create new migration file by going to ``aiida/backends/sqlalchemy`` and
   executing::

    ./alembic_manage.py revision "This is a new revision"

   This will create a new migration file in ``aiida/backends/sqlalchemy/migrations/versions``
   whose names begins with an automatically generated hash code and the
   provided message for this new migration. Of course you can change the
   migration message to a message of your preference. Please look at the
   generatedvfile and ensure that migration is correct. If you are in doubt
   about the operations mentioned in the file and its content, you can have a
   look at the Alembic documentation.
3. Your database will be automatically migrated to the latest revision as soon
   as you run your first verdi command. You can also migrate it manually with
   the help of the alembic_manage.py script as you can see below.

Overview of alembic_manage.py commands
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The alembic_manage.py provides several options to control your SQLAlchemy
migrations. By executing::

    ./alembic_manage.py --help

you will get a full list of the available arguments that you can pass and
commands. Briefly, the available commands are:

* **upgrade** This command allows you to upgrade to the later version. For the
  moment, you can only upgrade to the latest version.
* **downgrade** This command allows you to downgrade the version of your
  database. For the moment, you can only downgrade to the base version.
* **history** This command lists the available migrations in chronological
  order.
* **current** This command displays the current version of the database.
* **revision** This command creates a new migration file based on the model
  changes.

.. _first_alembic_migration:

Debugging Alembic
~~~~~~~~~~~~~~~~~
Alembic migrations should work automatically and migrate your database to the
latest version. However, if you were using SQLAlchemy before we introduced
Alembic, you may get a message like to following during the first migration::

    sqlalchemy.exc.ProgrammingError: (psycopg2.ProgrammingError) relation
    "db_dbuser" already exists [SQL: '\nCREATE TABLE db_dbuser (\n\tid SERIAL
    NOT NULL, \n\temail VARCHAR(254), \n\tpassword VARCHAR(128),
    \n\tis_superuser BOOLEAN NOT NULL, \n\tfirst_name VARCHAR(254),
    \n\tlast_name VARCHAR(254), \n\tinstitution VARCHAR(254), \n\tis_staff
    BOOLEAN, \n\tis_active BOOLEAN, \n\tlast_login TIMESTAMP WITH TIME ZONE,
    \n\tdate_joined TIMESTAMP WITH TIME ZONE, \n\tCONSTRAINT db_dbuser_pkey
    PRIMARY KEY (id)\n)\n\n']

In this case, you should create manually the Alembic table in your database and
add a line with the database version number. To do so, use psql to connect
to the desired database::

    psql aiidadb_sqla

(you should replace ``aiidadb_sqla`` with the name of the database that you
would like to modify). Then, execute the following commands::

    CREATE TABLE alembic_version (version_num character varying(32) not null, PRIMARY KEY(version_num));
    INSERT INTO alembic_version VALUES ('e15ef2630a1b');
    GRANT ALL ON alembic_version TO aiida;


