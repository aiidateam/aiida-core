# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=invalid-name,too-few-public-methods,no-name-in-module,import-error
"""Migrate the file repository to the new disk object store based implementation."""
import pathlib

from django.core.exceptions import ObjectDoesNotExist
from django.db import migrations

from aiida.backends.djsite.db.migrations import upgrade_schema_version
from aiida.backends.general.migrations import utils
from aiida.cmdline.utils import echo

REVISION = '1.0.47'
DOWN_REVISION = '1.0.46'

REPOSITORY_UUID_KEY = 'repository|uuid'


def migrate_repository(apps, schema_editor):
    """Migrate the repository."""
    # pylint: disable=too-many-locals,too-many-branches,too-many-statements
    import json
    from tempfile import NamedTemporaryFile
    from disk_objectstore import Container

    from aiida.common import exceptions
    from aiida.common.progress_reporter import set_progress_bar_tqdm, get_progress_reporter, set_progress_reporter
    from aiida.manage.configuration import get_profile

    DbNode = apps.get_model('db', 'DbNode')

    profile = get_profile()
    node_count = DbNode.objects.count()
    missing_node_uuids = []
    missing_repo_folder = []
    shard_count = 256

    basepath = pathlib.Path(profile.repository_path) / 'repository' / 'node'
    filepath = pathlib.Path(profile.repository_path) / 'container'
    container = Container(filepath)

    if not profile.is_test_profile and (node_count > 0 and not basepath.is_dir()):
        raise exceptions.DatabaseMigrationError(
            f'the file repository `{basepath}` does not exist but the database is not empty, it contains {node_count} '
            'nodes. Aborting the migration.'
        )

    if not profile.is_test_profile and container.is_initialised:
        raise exceptions.DatabaseMigrationError(
            f'the container {filepath} already exists. If you ran this migration before and it failed simply '
            'delete this directory and restart the migration.'
        )

    container.init_container(clear=True, **profile.defaults['repository'])

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

            mapping_node_repository_metadata, missing_sub_repo_folder = utils.migrate_legacy_repository(shard)

            if missing_sub_repo_folder:
                missing_repo_folder.extend(missing_sub_repo_folder)
                del missing_sub_repo_folder

            if mapping_node_repository_metadata is None:
                continue

            for node_uuid, repository_metadata in mapping_node_repository_metadata.items():

                # If `repository_metadata` is `{}` or `None`, we skip it, as we can leave the column default `null`.
                if not repository_metadata:
                    continue

                try:
                    # This can happen if the node was deleted but the repo folder wasn't, or the repo folder just never
                    # corresponded to an actual node. In any case, we don't want to fail but just log the warning.
                    node = DbNode.objects.get(uuid=node_uuid)
                except ObjectDoesNotExist:
                    missing_node_uuids.append((node_uuid, repository_metadata))
                else:
                    node.repository_metadata = repository_metadata
                    node.save()

            del mapping_node_repository_metadata
            progress.update()

    # Store the UUID of the repository container in the `DbSetting` table. Note that for new databases, the profile
    # setup will already have stored the UUID and so it should be skipped, or an exception for a duplicate key will be
    # raised. This migration step is only necessary for existing databases that are migrated.
    container_id = profile.get_repository().uuid
    with schema_editor.connection.cursor() as cursor:
        cursor.execute(
            f"""
            INSERT INTO db_dbsetting (key, val, description, time)
            VALUES ('repository|uuid', to_json('{container_id}'::text), 'Repository UUID', current_timestamp)
            ON CONFLICT (key) DO NOTHING;
            """
        )

    if not profile.is_test_profile:

        if missing_node_uuids:
            prefix = 'migration-repository-missing-nodes-'
            with NamedTemporaryFile(prefix=prefix, suffix='.json', dir='.', mode='w+', delete=False) as handle:
                json.dump(missing_node_uuids, handle)
                echo.echo_warning(
                    '\nDetected node repository folders for nodes that do not exist in the database. The UUIDs of '
                    f'those nodes have been written to a log file: {handle.name}'
                )

        if missing_repo_folder:
            prefix = 'migration-repository-missing-subfolder-'
            with NamedTemporaryFile(prefix=prefix, suffix='.json', dir='.', mode='w+', delete=False) as handle:
                json.dump(missing_repo_folder, handle)
                echo.echo_warning(
                    '\nDetected repository folders that were missing the required subfolder `path` or `raw_input`.'
                    f' The paths of those nodes repository folders have been written to a log file: {handle.name}'
                )

        # If there were no nodes, most likely a new profile, there is not need to print the warning
        if node_count:
            echo.echo_warning(
                '\nMigrated file repository to the new disk object store. The old repository has not been deleted '
                f'out of safety and can be found at {pathlib.Path(profile.repository_path, "repository")}.'
            )


class Migration(migrations.Migration):
    """Migrate the file repository to the new disk object store based implementation."""

    dependencies = [
        ('db', '0046_add_node_repository_metadata'),
    ]

    operations = [
        migrations.RunPython(migrate_repository, reverse_code=migrations.RunPython.noop),
        upgrade_schema_version(REVISION, DOWN_REVISION),
    ]
