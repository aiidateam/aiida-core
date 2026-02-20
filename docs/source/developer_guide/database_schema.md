# Modifying the database schema

AiiDA uses SQLAlchemy with [Alembic](https://alembic.sqlalchemy.org/en/latest/) for database schema migrations.

## Creating a migration

1. Make the necessary changes to the models in `src/aiida/storage/psql_dos/models/`.

2. Create a new migration file:

   ```console
   $ alembic revision -m "Description of the migration"
   ```

   This creates a migration file in the migrations directory with an auto-generated hash and your description.

3. Review the generated migration file.
   It should contain automatically generated hashes pointing to the previous and current revisions:

   ```python
   revision = 'e72ad251bcdb'
   down_revision = 'b8b23ddefad4'
   ```

   Ensure the `upgrade()` and `downgrade()` functions are correct.

4. For data migrations (changes to database content rather than schema), add manual SQL commands:

   ```python
   from sqlalchemy.sql import text

   forward_sql = [
       """UPDATE db_dbgroup SET type_string = 'auto.import' WHERE type_string = 'aiida.import';""",
   ]

   reverse_sql = [
       """UPDATE db_dbgroup SET type_string = 'aiida.import' WHERE type_string = 'auto.import';""",
   ]

   def upgrade():
       conn = op.get_bind()
       statement = text('\n'.join(forward_sql))
       conn.execute(statement)

   def downgrade():
       conn = op.get_bind()
       statement = text('\n'.join(reverse_sql))
       conn.execute(statement)
   ```

5. Test the migration:

   ```console
   $ verdi -p {profile} storage migrate
   ```

6. Add tests for the migration.

## Testing migrations

### Preparing a test environment

1. Create a clone of the PostgreSQL database you want to migrate:

   ```sql
   CREATE DATABASE aiida_clone WITH TEMPLATE aiida_original_db OWNER aiida;
   ```

2. Check database statistics before migration:

   ```sql
   SELECT count(*) FROM db_dbnode;
   SELECT pg_size_pretty(pg_database_size('aiida_clone'));
   ```

3. Create a profile with the correct database configured.
   The easiest approach is to open the AiiDA `config.json` and clone an existing entry, updating the database name and repository location.

### Running the migration

1. Ensure the daemon is not running.
2. Run the migration:

   ```console
   $ time verdi -p PROFILE storage migrate -f
   ```

### Checks after migration

* Rerun database statistics (node count, database size) and compare with pre-migration values.
* Run `verdi status` and check that the storage connection is green.
* Run `verdi storage info --statistics` and check the outcome.
* Open `verdi shell` and run some test queries, open repository files, etc.

:::{tip}
You can use `verdi devel run-sql "SQL_TEXT"` to run arbitrary SQL against the profile's database.
:::
