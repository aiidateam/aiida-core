# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=protected-access,fixme,too-many-arguments,too-many-locals,too-many-statements,too-many-branches,too-many-nested-blocks
"""Common import functions for both database backend"""
import copy
from typing import Dict
from uuid import UUID

from aiida.common import timezone
from aiida.common.progress_reporter import get_progress_reporter
from aiida.orm import Group, ImportGroup, Node, QueryBuilder
from aiida.tools.importexport.common import exceptions
from aiida.tools.importexport.common.config import NODE_ENTITY_NAME
from aiida.tools.importexport.dbimport.utils import IMPORT_LOGGER


def _make_import_group(
    *, group, existing_entries: Dict[str, Dict[str, dict]], new_entries: Dict[str, Dict[str, dict]],
    foreign_ids_reverse_mappings: Dict[str, Dict[str, int]]
):
    """Make an import group containing all imported nodes."""
    existing = existing_entries.get(NODE_ENTITY_NAME, {})
    existing_pk = [foreign_ids_reverse_mappings[NODE_ENTITY_NAME][v['uuid']] for v in existing.values()]
    new = new_entries.get(NODE_ENTITY_NAME, {})
    new_pk = [foreign_ids_reverse_mappings[NODE_ENTITY_NAME][v['uuid']] for v in new.values()]

    pks_for_group = existing_pk + new_pk

    # So that we do not create empty groups
    if not pks_for_group:
        IMPORT_LOGGER.debug('No Nodes to import, so no Group created, if it did not already exist')
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

            if counter == 100:
                raise exceptions.ImportUniquenessError(
                    "Overflow of import groups (more than 100 import groups exists with basename '{}')"
                    ''.format(basename)
                )
        group = ImportGroup(label=group_label).store()

    # Add all the nodes to the new group
    builder = QueryBuilder().append(Node, filters={'id': {'in': pks_for_group}})

    first = True
    nodes = []
    description = 'Creating import Group - Preprocessing'

    with get_progress_reporter()(total=len(pks_for_group), desc=description) as progress:
        for entry in builder.iterall():
            if first:
                progress.set_description_str('Creating import Group', refresh=False)
                first = False
            progress.update()
            nodes.append(entry[0])

        group.add_nodes(nodes)
        progress.set_description_str('Done (cleaning up)', refresh=True)

    return group


def _validate_uuid(given_uuid):
    """A simple check for the UUID validity."""
    try:
        parsed_uuid = UUID(given_uuid, version=4)
    except ValueError:
        # If not a valid UUID
        return False

    # Check if there was any kind of conversion of the hex during
    # the validation
    return str(parsed_uuid) == given_uuid


def _sanitize_extras(fields):
    """Remove unwanted extra keys."""
    fields = copy.copy(fields)
    fields['extras'] = {key: value for key, value in fields['extras'].items() if not key.startswith('_aiida_')}
    if fields.get('node_type', '').endswith('code.Code.'):
        fields['extras'] = {key: value for key, value in fields['extras'].items() if not key == 'hidden'}
    return fields
