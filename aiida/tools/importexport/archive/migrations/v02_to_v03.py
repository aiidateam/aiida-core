# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Migration from v0.2 to v0.3, used by `verdi export migrate` command."""
# pylint: disable=too-many-locals,too-many-statements,too-many-branches,unused-argument
import enum

from aiida.tools.importexport.archive.common import CacheFolder
from aiida.tools.importexport.common.exceptions import DanglingLinkError
from .utils import verify_metadata_version, update_metadata


def migrate_v2_to_v3(folder: CacheFolder):
    """
    Migration of archive files from v0.2 to v0.3, which means adding the link
    types to the link entries and making the entity key names backend agnostic
    by effectively removing the prefix 'aiida.backends.djsite.db.models'

    :param data: the content of an export archive data.json file
    :param metadata: the content of an export archive metadata.json file
    """

    old_version = '0.2'
    new_version = '0.3'

    class LinkType(enum.Enum):
        """This was the state of the `aiida.common.links.LinkType` enum before aiida-core v1.0.0a5"""

        UNSPECIFIED = 'unspecified'
        CREATE = 'createlink'
        RETURN = 'returnlink'
        INPUT = 'inputlink'
        CALL = 'calllink'

    class NodeType(enum.Enum):
        """A simple enum of relevant node types"""

        NONE = 'none'
        CALC = 'calculation'
        CODE = 'code'
        DATA = 'data'
        WORK = 'work'

    entity_map = {
        'aiida.backends.djsite.db.models.DbNode': 'Node',
        'aiida.backends.djsite.db.models.DbLink': 'Link',
        'aiida.backends.djsite.db.models.DbGroup': 'Group',
        'aiida.backends.djsite.db.models.DbComputer': 'Computer',
        'aiida.backends.djsite.db.models.DbUser': 'User',
        'aiida.backends.djsite.db.models.DbAttribute': 'Attribute'
    }

    _, metadata = folder.load_json('metadata.json')

    verify_metadata_version(metadata, old_version)
    update_metadata(metadata, new_version)

    _, data = folder.load_json('data.json')

    # Create a mapping from node uuid to node type
    mapping = {}
    for nodes in data['export_data'].values():
        for node in nodes.values():

            try:
                node_uuid = node['uuid']
                node_type_string = node['type']
            except KeyError:
                continue

            if node_type_string.startswith('calculation.job.'):
                node_type = NodeType.CALC
            elif node_type_string.startswith('calculation.inline.'):
                node_type = NodeType.CALC
            elif node_type_string.startswith('code.Code'):
                node_type = NodeType.CODE
            elif node_type_string.startswith('data.'):
                node_type = NodeType.DATA
            elif node_type_string.startswith('calculation.work.'):
                node_type = NodeType.WORK
            else:
                node_type = NodeType.NONE

            mapping[node_uuid] = node_type

    # For each link, deduce the link type and insert it in place
    for link in data['links_uuid']:

        try:
            input_type = NodeType(mapping[link['input']])
            output_type = NodeType(mapping[link['output']])
        except KeyError:
            raise DanglingLinkError(f"Unknown node UUID {link['input']} or {link['output']}")

        # The following table demonstrates the logic for inferring the link type
        # (CODE, DATA) -> (WORK, CALC) : INPUT
        # (CALC)       -> (DATA)       : CREATE
        # (WORK)       -> (DATA)       : RETURN
        # (WORK)       -> (CALC, WORK) : CALL
        if input_type in [NodeType.CODE, NodeType.DATA] and output_type in [NodeType.CALC, NodeType.WORK]:
            link['type'] = LinkType.INPUT.value
        elif input_type == NodeType.CALC and output_type == NodeType.DATA:
            link['type'] = LinkType.CREATE.value
        elif input_type == NodeType.WORK and output_type == NodeType.DATA:
            link['type'] = LinkType.RETURN.value
        elif input_type == NodeType.WORK and output_type in [NodeType.CALC, NodeType.WORK]:
            link['type'] = LinkType.CALL.value
        else:
            link['type'] = LinkType.UNSPECIFIED.value

    # Now we migrate the entity key names i.e. removing the 'aiida.backends.djsite.db.models' prefix
    for field in ['unique_identifiers', 'all_fields_info']:
        for old_key, new_key in entity_map.items():
            if old_key in metadata[field]:
                metadata[field][new_key] = metadata[field][old_key]
                del metadata[field][old_key]

    # Replace the 'requires' keys in the nested dictionaries in 'all_fields_info'
    for entity in metadata['all_fields_info'].values():
        for prop in entity.values():
            for key, value in prop.items():
                if key == 'requires' and value in entity_map:
                    prop[key] = entity_map[value]

    # Replace any present keys in the data.json
    for field in ['export_data']:
        for old_key, new_key in entity_map.items():
            if old_key in data[field]:
                data[field][new_key] = data[field][old_key]
                del data[field][old_key]

    folder.write_json('metadata.json', metadata)
    folder.write_json('data.json', data)
