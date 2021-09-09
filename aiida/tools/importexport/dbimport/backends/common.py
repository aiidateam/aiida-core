# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Common import functions for both database backend"""
import copy
from typing import Dict, List, Optional

from aiida.common import timezone
from aiida.common.progress_reporter import get_progress_reporter, create_callback
from aiida.orm import Group, ImportGroup, Node, QueryBuilder, ProcessNode
from aiida.tools.importexport.archive.readers import ArchiveReaderAbstract
from aiida.tools.importexport.common import exceptions
from aiida.tools.importexport.dbimport.utils import IMPORT_LOGGER

MAX_COMPUTERS = 100
MAX_GROUPS = 100


def _copy_node_repositories(*, repository_metadatas: List[Dict], reader: ArchiveReaderAbstract):
    """Copy repositories of new nodes from the archive to the AiiDa profile.

    :param repository_metadatas: list of repository metadatas
    :param reader: the archive reader
    """
    from aiida.manage.manager import get_manager

    if not repository_metadatas:
        return

    IMPORT_LOGGER.debug('CREATING NEW NODE REPOSITORIES...')

    # Copy the contents of the repository container. Note that this should really be done within the
    # database transaction and if that fails, the written files should be deleted, or at least
    # soft-deleted. This is to be done later. This is first working example
    container_export = reader.get_repository_container()

    if not container_export.is_initialised:
        container_export.init_container()

    profile = get_manager().get_profile()
    assert profile is not None, 'profile not loaded'
    container_profile = profile.get_repository().backend.container

    def collect_hashkeys(objects, hashkeys):
        for obj in objects.values():
            hashkey = obj.get('k', None)
            if hashkey is not None:
                hashkeys.append(hashkey)
            subobjects = obj.get('o', None)
            if subobjects:
                collect_hashkeys(subobjects, hashkeys)

    hashkeys: List[str] = []

    for repository_metadata in repository_metadatas:
        collect_hashkeys(repository_metadata.get('o', {}), hashkeys)

    with get_progress_reporter()(total=len(hashkeys), desc='Importing repository files') as progress:
        callback = create_callback(progress)
        container_export.export(
            set(hashkeys),  # type: ignore[arg-type]
            container_profile,
            compress=True,
            callback=callback
        )


def _make_import_group(*, group: Optional[ImportGroup], node_pks: List[int]) -> ImportGroup:
    """Make an import group containing all imported nodes.

    :param group: Use an existing group
    :param node_pks: node pks to add to group

    """
    # So that we do not create empty groups
    if not node_pks:
        IMPORT_LOGGER.debug('No nodes to import, so no import group created')
        return group

    # If user specified a group, import all things into it
    if not group:
        # Get an unique name for the import group, based on the current (local) time
        basename = timezone.localtime(timezone.now()).strftime('%Y%m%d-%H%M%S')
        counter = 0
        group_label = basename

        while Group.objects.find(filters={'label': group_label}):
            counter += 1
            group_label = f'{basename}_{counter}'

            if counter == MAX_GROUPS:
                raise exceptions.ImportUniquenessError(
                    f"Overflow of import groups (more than {MAX_GROUPS} groups exists with basename '{basename}')"
                )
        group = ImportGroup(label=group_label).store()

    # Add all the nodes to the new group
    builder = QueryBuilder().append(Node, filters={'id': {'in': node_pks}})

    first = True
    nodes = []
    description = 'Creating import Group - Preprocessing'

    with get_progress_reporter()(total=len(node_pks), desc=description) as progress:
        for entry in builder.iterall():
            if first:
                progress.set_description_str('Creating import Group', refresh=False)
                first = False
            progress.update()
            nodes.append(entry[0])

        group.add_nodes(nodes)
        progress.set_description_str('Done (cleaning up)', refresh=True)

    return group


def _sanitize_extras(fields: dict) -> dict:
    """Remove unwanted extra keys.

    :param fields: the database fields for the entity

    """
    fields = copy.copy(fields)
    fields['extras'] = {key: value for key, value in fields['extras'].items() if not key.startswith('_aiida_')}
    if fields.get('node_type', '').endswith('code.Code.'):
        fields['extras'] = {key: value for key, value in fields['extras'].items() if not key == 'hidden'}
    return fields


def _strip_checkpoints(fields: dict) -> dict:
    """Remove checkpoint from attributes of process nodes.

    :param fields: the database fields for the entity
    """
    if fields.get('node_type', '').startswith('process.'):
        fields = copy.copy(fields)
        fields['attributes'] = {
            key: value for key, value in fields['attributes'].items() if key != ProcessNode.CHECKPOINT_KEY
        }
    return fields
