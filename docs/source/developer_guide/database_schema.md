# Modifying the database schema

AiiDA uses [SQLAlchemy](https://www.sqlalchemy.org/) as its ORM and [Alembic](https://alembic.sqlalchemy.org/en/latest/) for database schema migrations.

When a new AiiDA release changes the database structure, the change is shipped as a **migration** — a Python script committed to the codebase that describes how to move from the old schema to the new one (and back).
When users upgrade AiiDA, they run `verdi storage migrate` to apply any pending migrations to their profile's database.

Migrations come in two flavours:

- **Schema migrations**: change the database structure (e.g., adding a column, creating an index). These use Alembic's `op.add_column()`, `op.create_index()`, etc.
- **Data migrations**: transform existing data to match the new schema (e.g., renaming type strings, recomputing hashes). These execute SQL or use helper utilities.

The `sqlite_zip` backend has a separate migration chain for upgrading older archive files on import.

## Storage backends

Multiple storage backends have their own migration chains:

| Backend | Database | Migrations path |
|---------|----------|-----------------|
| `psql_dos` | PostgreSQL | `src/aiida/storage/psql_dos/migrations/versions/` |
| `sqlite_dos` | SQLite (disk) | `src/aiida/storage/sqlite_dos/migrations/versions/` |
| `sqlite_zip` | SQLite (archive) | `src/aiida/storage/sqlite_zip/migrations/versions/` |
| `sqlite_temp` | SQLite (in-memory) | No migrations — schema is created fresh each time |

All backends use Alembic with the same `main_NNNN` naming convention.
Schema changes typically need a corresponding migration in each persistent backend (`psql_dos` and `sqlite_dos`).

## Key locations (psql_dos)

| Path | Contents |
|------|----------|
| `src/aiida/storage/psql_dos/models/` | SQLAlchemy model definitions (the "current" schema) |
| `src/aiida/storage/psql_dos/migrations/versions/` | Alembic migration scripts |
| `src/aiida/storage/psql_dos/migrations/utils/` | Shared helper utilities for data migrations |

## Creating a migration

1. If it's a schema migration, make the necessary changes to the models in `src/aiida/storage/psql_dos/models/`.

1. Create a new migration file in `src/aiida/storage/psql_dos/migrations/versions/` by copying an existing one (e.g., `main_0002_recompute_hash_calc_job_node.py`) and updating it.
   Use the `main_NNNN_description.py` naming convention, incrementing the number from the latest migration:

   ```python
   revision = 'main_0003'
   down_revision = 'main_0002'
   branch_labels = None
   depends_on = None
   ```

1. Implement the `upgrade()` and `downgrade()` functions.
   For data migrations, reusable helpers are available in `src/aiida/storage/psql_dos/migrations/utils/`.

1. Test the migration:

   ```console
   $ verdi -p {profile} storage migrate
   ```

1. Add tests for the migration.

1. If the change affects the schema, also create the corresponding migration in `src/aiida/storage/sqlite_dos/migrations/versions/`.

:::{important}
The models in `src/aiida/storage/psql_dos/models/` must always reflect the **latest** schema.
Alembic migrations describe how to get from one version to the next, but the models define the target state.
:::

## Testing migrations manually

Beyond automated tests, it's good practice to verify migrations against a real database before release.

### PostgreSQL (`psql_dos`)

1. Create a clone of the database to test against:

   ```sql
   CREATE DATABASE aiida_clone WITH TEMPLATE aiida_original_db OWNER aiida;
   ```

1. Check database statistics before migration:

   ```sql
   SELECT count(*) FROM db_dbnode;
   SELECT pg_size_pretty(pg_database_size('aiida_clone'));
   ```

1. Create a profile pointing to the cloned database.
   The easiest approach is to open `~/.aiida/config.json` and clone an existing entry, updating the database name and repository location.

1. Ensure the daemon is not running, then run the migration:

   ```console
   $ time verdi -p PROFILE storage migrate -f
   ```

1. Verify after migration:
   - Rerun database statistics (node count, database size) and compare with pre-migration values.
   - Run `verdi status` and check that the storage connection is green.
   - Run `verdi storage info --statistics` and check the outcome.
   - Open `verdi shell` and run some test queries, open repository files, etc.

### SQLite (`sqlite_dos`)

For `sqlite_dos` profiles, simply copy the `.sqlite` database file before testing, and run `verdi -p PROFILE storage migrate` against the copy.

:::{tip}
You can use `verdi devel run-sql "SQL_TEXT"` to run arbitrary SQL against the profile's database.
:::

## Configuration migrations

Changes to the AiiDA configuration file (`config.json`) also require migrations, following a similar pattern to database schema migrations.

1. In `aiida/manage/configuration/migrations/migrations.py`, increment `CURRENT_CONFIG_VERSION`.
   If the change is **not** backwards-compatible, also set `OLDEST_COMPATIBLE_CONFIG_VERSION` to the new value.

1. Write a migration function that transforms the old config dict into the new version.

1. Add an entry to `MIGRATIONS` with the version **before** the migration and **hard-coded** version numbers (not references to the constants, as these will change with future migrations).

1. Add tests using `check_and_migrate_config` (with `store=False` to avoid overwriting your actual config).
