# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=too-many-locals,too-many-branches,too-many-statements
""""Migrate the file repository to the new disk object store based implementation."""
import json
from tempfile import NamedTemporaryFile

from disk_objectstore import Container
from sqlalchemy import Integer, cast
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import column, func, select, table, text

from aiida.cmdline.utils import echo
from aiida.common import exceptions
from aiida.common.progress_reporter import get_progress_reporter, set_progress_bar_tqdm, set_progress_reporter
from aiida.storage.psql_dos.backend import CONTAINER_DEFAULTS, get_filepath_container
from aiida.storage.psql_dos.migrations.utils import utils


def migrate_repository(connection, profile):
    """Migrations for the upgrade."""
    DbNode = table(  # pylint: disable=invalid-name
        'db_dbnode',
        column('id', Integer),
        column('uuid', UUID),
        column('repository_metadata', JSONB),
    )

    node_count = connection.execute(select(func.count()).select_from(DbNode)).scalar()
    missing_repo_folder = []
    shard_count = 256

    filepath_container = get_filepath_container(profile)
    filepath_repository = filepath_container.parent / 'repository' / 'node'
    container = Container(filepath_container)

    if not profile.is_test_profile and (node_count > 0 and not filepath_repository.is_dir()):
        raise exceptions.StorageMigrationError(
            f'the file repository `{filepath_repository}` does not exist but the database is not empty, it contains '
            f'{node_count} nodes. Aborting the migration.'
        )

    if not profile.is_test_profile and container.is_initialised:
        raise exceptions.StorageMigrationError(
            f'the container {filepath_container} already exists. If you ran this migration before and it failed simply '
            'delete this directory and restart the migration.'
        )

    container.init_container(clear=True, **CONTAINER_DEFAULTS)

    # Only show the progress bar if there is at least a node in the database. Note that we cannot simply make the entire
    # next block under the context manager optional, since it performs checks on whether the repository contains files
    # that are not in the database that are still important to perform even if the database is empty.
    if node_count > 0:
        set_progress_bar_tqdm()
    else:
        set_progress_reporter(None)

    with get_progress_reporter()(total=shard_count, desc='Migrating file repository') as progress:
        for i in range(shard_count):

            shard = '%.2x' % i  # noqa flynt
            progress.set_description_str(f'Migrating file repository: shard {shard}')

            mapping_node_repository_metadata, missing_sub_repo_folder = utils.migrate_legacy_repository(profile, shard)

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
                # to-do in the django migration there was logic to log warnings for missing UUIDs, should we re-instate?
                connection.execute(DbNode.update().where(DbNode.c.uuid == node_uuid).values(repository_metadata=value))

            del mapping_node_repository_metadata
            progress.update()

    # Store the UUID of the repository container in the `DbSetting` table. Note that for new databases, the profile
    # setup will already have stored the UUID and so it should be skipped, or an exception for a duplicate key will be
    # raised. This migration step is only necessary for existing databases that are migrated.
    container_id = container.container_id
    statement = text(
        f"""
        INSERT INTO db_dbsetting (key, val, description, time)
        VALUES ('repository|uuid', to_json('{container_id}'::text), 'Repository UUID', NOW())
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
            echo.echo_warning(
                'Migrated file repository to the new disk object store. The old repository has not been deleted out'
                f' of safety and can be found at {filepath_repository.parent}.'
            )
