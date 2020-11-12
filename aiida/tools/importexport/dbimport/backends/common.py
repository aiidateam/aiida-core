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
from typing import List, Optional

from aiida.common import timezone
from aiida.common.folders import RepositoryFolder
from aiida.common.progress_reporter import get_progress_reporter, create_callback
from aiida.orm import Group, ImportGroup, Node, QueryBuilder
from aiida.orm.utils._repository import Repository
from aiida.tools.importexport.archive.readers import ArchiveReaderAbstract
from aiida.tools.importexport.common import exceptions
from aiida.tools.importexport.dbimport.utils import IMPORT_LOGGER

MAX_COMPUTERS = 100
MAX_GROUPS = 100


def _copy_node_repositories(*, uuids_to_create: List[str], reader: ArchiveReaderAbstract):
    """Copy repositories of new nodes from the archive to the AiiDa profile.

    :param uuids_to_create: the node UUIDs to copy
    :param reader: the archive reader

    """
    if not uuids_to_create:
        return
    IMPORT_LOGGER.debug('CREATING NEW NODE REPOSITORIES...')
    with get_progress_reporter()(total=1, desc='Creating new node repos') as progress:

        _callback = create_callback(progress)

        for import_entry_uuid, subfolder in zip(
            uuids_to_create, reader.iter_node_repos(uuids_to_create, callback=_callback)
        ):
            destdir = RepositoryFolder(section=Repository._section_name, uuid=import_entry_uuid)  # pylint: disable=protected-access
            # Replace the folder, possibly destroying existing previous folders, and move the files
            # (faster if we are on the same filesystem, and in any case the source is a SandboxFolder)
            destdir.replace_with_folder(subfolder.abspath, move=True, overwrite=True)


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
