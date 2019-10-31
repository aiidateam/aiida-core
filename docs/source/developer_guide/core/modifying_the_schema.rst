Modifying the schema
++++++++++++++++++++

Django
------

The Django database schema can be found in :py:mod:`aiida.backends.djsite.db.models`.
If you need to change the database schema follow these steps:

 1. Make all the necessary changes to :py:mod:`aiida.backends.djsite.db.models`
 2. Create a new migration file by running::

        python aiida/backends/djsite/manage.py makemigrations

    This will create the migration file in ``aiida/backends/djsite/db/migrations`` whose name begins with a number followed by some description.
    If the description is not appropriate then change it to something better but retain the number.

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

 4. The migration file now contains some migrations steps that were generated automatically.
    Please make sure that they are correct.
    Also, if you want to add some changes that affect the content of the database -- you should do it "manually" by adding some sql commands that will run directly on your database::

        forward_sql = [
            """UPDATE db_dbgroup SET type_string = 'auto.import' WHERE type_string = 'aiida.import';""",
            """UPDATE db_dbgroup SET type_string = 'auto.run' WHERE type_string = 'autogroup.run';""",
        ]

        reverse_sql = [
            """UPDATE db_dbgroup SET type_string = 'aiida.import' WHERE type_string = 'auto.import';""",
            """UPDATE db_dbgroup SET type_string = 'autogroup.run' WHERE type_string = 'auto.run';""",
            ]
        ...

        operations = [
            ...
            migrations.RunSQL(
                sql='\n'.join(forward_sql),
                reverse_sql='\n'.join(reverse_sql)),
            upgrade_schema_version(REVISION, DOWN_REVISION),
            ...
        ]

    As you can see here, you should not only provide the sql commands to upgrade your database, but also the commands to revert these changes in case you want to perform a downgrade (see: ``sql=forward_sql``, ``reverse_sql=reverse_sql``)

 5. Change the ``LATEST_MIGRATION`` variable in ``aiida/backends/djsite/db/migrations/__init__.py`` to the name of your migration file::

        LATEST_MIGRATION = '0003_my_db_update'

    This allows AiiDA to get the version number from your migration and make sure the database and the code are in sync.

 6. Migrate your database to the new version using ``verdi`` and specifying the correct profile::

        verdi -p {profile} database migrate

    In case you want to (and, most probably, you should) test the downgrade operation, please
    check the list of available versions of the database::

        python aiida/backends/djsite/manage.py showmigrations db

    The output will look something like the following::

        db
        [X] 0001_initial
        [X] 0002_db_state_change
        [X] 0003_add_link_type
        [X] 0004_add_daemon_and_uuid_indices
        [X] 0005_add_cmtime_indices
        [X] 0006_delete_dbpath
        [X] 0007_update_linktypes
        [X] 0008_code_hidden_to_extra
        [X] 0009_base_data_plugin_type_string
        [X] 0010_process_type
        [X] 0011_delete_kombu_tables
        [X] 0012_drop_dblock
        [X] 0013_django_1_8
        [X] 0014_add_node_uuid_unique_constraint
        [X] 0015_invalidating_node_hash
        [X] 0016_code_sub_class_of_data
        [X] 0017_drop_dbcalcstate
        [X] 0018_django_1_11

    Choose the previous migration step and migrate to it::

        python aiida/backends/djsite/manage.py migrate db 0017_drop_dbcalcstate

    Check that both: upgrade and downgrade changes are succesfull and if yes, go to the next step.

 7. Add tests for your migrations to the ``aiida-core/aiida/backends/djsite/db/subtests/migrations`` module.

.. note::

    Such a test can only be applied to the migration of the database content.
    For example, you can **not** test modifications of the database column names.



SQLAlchemy
----------

The SQLAlchemy database schema can be found in :py:mod:`aiida.backends.sqlalchemy.models`.
If you need to change the database schema follow these steps:

 1. Make all the necessary changes to the model than you would like to modify located in the ``aiida/backends/sqlalchemy/models`` directory.

 2. Create new migration file by going to ``aiida/backends/sqlalchemy`` and executing::

        python aiida/backends/sqlalchemy/manage.py revision "This is the description for the next revision"

    This will create a new migration file in ``aiida/backends/sqlalchemy/migrations/versions`` whose names begins with an automatically generated hash and the provided message for this new migration.
    Modify the migration message to accurately describe the purpose of the migration.

 3. Have a look at the generated migration file and ensure that migration is correct.
    The file should contain automatically generated hashes that point to the previous and to the current revision::

        revision = 'e72ad251bcdb'
        down_revision = 'b8b23ddefad4'

    Also ``upgrade()`` and ``downgrade()`` function definitions should be present in the file::

        def upgrade():
            # some upgrage operations
        def downgrade():
            # some downgrade operations

    If you want to add some changes that affect the content of the database -- you should do it "manually" by adding some sql commands that will run directly on your database.
    Learn the following example and adapt it for your needs::

        from sqlalchemy.sql import text

        forward_sql = [
            """UPDATE db_dbgroup SET type_string = 'auto.import' WHERE type_string = 'aiida.import';""",
            """UPDATE db_dbgroup SET type_string = 'auto.run' WHERE type_string = 'autogroup.run';""",
        ]

        reverse_sql = [
            """UPDATE db_dbgroup SET type_string = 'aiida.import' WHERE type_string = 'auto.import';""",
            """UPDATE db_dbgroup SET type_string = 'autogroup.run' WHERE type_string = 'auto.run';""",
            ]

        def upgrade():
            conn = op.get_bind()
            statement = text('\n'.join(forward_sql))
            conn.execute(statement)
        def downgrade():
            conn = op.get_bind()
            statement = text('\n'.join(reverse_sql))
            conn.execute(statement)

    If you want to learn more about the migration operations, you can have a look at the Alembic documentation.

 4. Migrate your database to the new version using ``verdi`` and specifying the correct profile::

        verdi -p {profile} database migrate

 5. Add tests for your migrations to ``aiida-core/aiida/backends/sqlalchemy/tests/test_migrations.py``


Overview of ``manage.py`` commands
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The alembic_manage.py provides several options to control your SQLAlchemy migrations.
By executing::

    python aiida/backends/sqlalchemy/manage.py --help

you will get a full list of the available arguments that you can pass and commands.
Briefly, the available commands are:

* **upgrade** This command allows you to upgrade to the later version.
* **downgrade** This command allows you to downgrade the version of your database.
* **history** This command lists the available migrations in chronological order.
* **current** This command displays the current version of the database.
* **revision** This command creates a new migration file based on the model changes.

.. _first_alembic_migration:

Debugging Alembic
~~~~~~~~~~~~~~~~~
Alembic migrations should work automatically and migrate your database to the latest version.
However, if you were using SQLAlchemy before we introduced Alembic, you may get a message like to following during the first migration::

    sqlalchemy.exc.ProgrammingError: (psycopg2.ProgrammingError) relation
    "db_dbuser" already exists [SQL: '\nCREATE TABLE db_dbuser (\n\tid SERIAL
    NOT NULL, \n\temail VARCHAR(254), \n\tpassword VARCHAR(128),
    \n\tis_superuser BOOLEAN NOT NULL, \n\tfirst_name VARCHAR(254),
    \n\tlast_name VARCHAR(254), \n\tinstitution VARCHAR(254), \n\tis_staff
    BOOLEAN, \n\tis_active BOOLEAN, \n\tlast_login TIMESTAMP WITH TIME ZONE,
    \n\tdate_joined TIMESTAMP WITH TIME ZONE, \n\tCONSTRAINT db_dbuser_pkey
    PRIMARY KEY (id)\n)\n\n']

In this case, you should create manually the Alembic table in your database and add a line with the database version number.
To do so, use psql to connect to the desired database::

    psql aiidadb_sqla

where you should replace ``aiidadb_sqla`` with the name of the database that you would like to modify.
Then, execute the following commands::

    CREATE TABLE alembic_version (version_num character varying(32) not null, PRIMARY KEY(version_num));
    INSERT INTO alembic_version VALUES ('e15ef2630a1b');
    GRANT ALL ON alembic_version TO aiida;
