# -*- coding: utf-8 -*-
# pylint: disable=invalid-name,no-member
"""Migrate the file repository to the new disk object store based implementation.

Revision ID: 1feaea71bd5a
Revises: 7536a82b2cc4
Create Date: 2020-10-01 15:05:49.271958

"""
from alembic import op
from sqlalchemy import Integer, cast
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import table, column, select, func, text

from aiida.backends.general.migrations import utils
from aiida.cmdline.utils import echo

# revision identifiers, used by Alembic.
revision = '1feaea71bd5a'
down_revision = '7536a82b2cc4'
branch_labels = None
depends_on = None


def upgrade():
    """Migrations for the upgrade."""
    # pylint: disable=too-many-locals
    import json
    from tempfile import NamedTemporaryFile
    from aiida.common.progress_reporter import set_progress_bar_tqdm, get_progress_reporter
    from aiida.manage.configuration import get_profile

    connection = op.get_bind()

    DbNode = table(
        'db_dbnode',
        column('id', Integer),
        column('uuid', UUID),
        column('repository_metadata', JSONB),
    )

    profile = get_profile()
    node_count = connection.execute(select([func.count()]).select_from(DbNode)).scalar()
    missing_repo_folder = []
    shard_count = 256

    set_progress_bar_tqdm()

    with get_progress_reporter()(total=shard_count, desc='Migrating file repository') as progress:
        for i in range(shard_count):

            shard = '%.2x' % i  # noqa flynt
            progress.set_description_str(f'Migrating file repository: shard {shard}')

            mapping_node_repository_metadata, missing_sub_repo_folder = utils.migrate_legacy_repository(
                node_count, shard
            )

            if missing_sub_repo_folder:
                missing_repo_folder.extend(missing_sub_repo_folder)
                del missing_sub_repo_folder

            if mapping_node_repository_metadata is None:
                continue

            for node_uuid, repository_metadata in mapping_node_repository_metadata.items():

                # If `repository_metadata` is `{}` or `None`, we skip it, as we can leave the column default `null`.
                if not repository_metadata:
                    continue

                value = cast(repository_metadata, JSONB)
                connection.execute(DbNode.update().where(DbNode.c.uuid == node_uuid).values(repository_metadata=value))

            del mapping_node_repository_metadata
            progress.update()

    # Store the UUID of the repository container in the `DbSetting` table. Note that for new databases, the profile
    # setup will already have stored the UUID and so it should be skipped, or an exception for a duplicate key will be
    # raised. This migration step is only necessary for existing databases that are migrated.
    container_id = profile.get_repository_container().container_id
    statement = text(
        f"""
        INSERT INTO db_dbsetting (key, val, description)
        VALUES ('repository|uuid', to_json('{container_id}'::text), 'Repository UUID')
        ON CONFLICT (key) DO NOTHING;
        """
    )
    connection.execute(statement)

    if not profile.is_test_profile:

        if missing_repo_folder:
            prefix = 'migration-repository-missing-subfolder-'
            with NamedTemporaryFile(prefix=prefix, suffix='.json', dir='.', mode='w+', delete=False) as handle:
                json.dump(missing_repo_folder, handle)
                echo.echo_warning(
                    'Detected repository folders that were missing the required subfolder `path` or `raw_input`. '
                    f'The paths of those nodes repository folders have been written to a log file: {handle.name}'
                )

        # If there were no nodes, most likely a new profile, there is not need to print the warning
        if node_count:
            import pathlib
            echo.echo_warning(
                'Migrated file repository to the new disk object store. The old repository has not been deleted out'
                f' of safety and can be found at {pathlib.Path(get_profile().repository_path, "repository")}.'
            )


def downgrade():
    """Migrations for the downgrade."""
