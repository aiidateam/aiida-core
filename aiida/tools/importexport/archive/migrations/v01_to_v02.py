# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Migration from v0.1 to v0.2, used by `verdi export migrate` command."""
from aiida.tools.importexport.archive.common import CacheFolder

from .utils import verify_metadata_version, update_metadata


def migrate_v1_to_v2(folder: CacheFolder):
    """
    Migration of archive files from v0.1 to v0.2, which means generalizing the
    field names with respect to the database backend

    :param metadata: the content of an export archive metadata.json file
    :param data: the content of an export archive data.json file
    """
    old_version = '0.1'
    new_version = '0.2'

    old_start = 'aiida.djsite'
    new_start = 'aiida.backends.djsite'

    _, metadata = folder.load_json('metadata.json')

    verify_metadata_version(metadata, old_version)
    update_metadata(metadata, new_version)

    _, data = folder.load_json('data.json')

    for field in ['export_data']:
        for key in list(data[field]):
            if key.startswith(old_start):
                new_key = get_new_string(key, old_start, new_start)
                data[field][new_key] = data[field][key]
                del data[field][key]

    for field in ['unique_identifiers', 'all_fields_info']:
        for key in list(metadata[field].keys()):
            if key.startswith(old_start):
                new_key = get_new_string(key, old_start, new_start)
                metadata[field][new_key] = metadata[field][key]
                del metadata[field][key]

    metadata['all_fields_info'] = replace_requires(metadata['all_fields_info'], old_start, new_start)

    folder.write_json('metadata.json', metadata)
    folder.write_json('data.json', data)


def get_new_string(old_string, old_start, new_start):
    """Replace the old module prefix with the new."""
    if old_string.startswith(old_start):
        return f'{new_start}{old_string[len(old_start):]}'

    return old_string


def replace_requires(data, old_start, new_start):
    """Replace the requires keys with new module path."""
    if isinstance(data, dict):
        new_data = {}
        for key, value in data.items():
            if key == 'requires' and value.startswith(old_start):
                new_data[key] = get_new_string(value, old_start, new_start)
            else:
                new_data[key] = replace_requires(value, old_start, new_start)
        return new_data

    return data
