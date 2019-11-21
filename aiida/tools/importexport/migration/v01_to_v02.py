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
# pylint: disable=unused-argument

from aiida.tools.importexport.migration.utils import verify_metadata_version, update_metadata


def migrate_v1_to_v2(metadata, data, *args):
    """
    Migration of export files from v0.1 to v0.2, which means generalizing the
    field names with respect to the database backend

    :param metadata: the content of an export archive metadata.json file
    :param data: the content of an export archive data.json file
    """
    old_version = '0.1'
    new_version = '0.2'

    old_start = 'aiida.djsite'
    new_start = 'aiida.backends.djsite'

    verify_metadata_version(metadata, old_version)
    update_metadata(metadata, new_version)

    def get_new_string(old_string):
        """Replace the old module prefix with the new."""
        if old_string.startswith(old_start):
            return '{}{}'.format(new_start, old_string[len(old_start):])

        return old_string

    def replace_requires(data):
        """Replace the requires keys with new module path."""
        if isinstance(data, dict):
            new_data = {}
            for key, value in data.items():
                if key == 'requires' and value.startswith(old_start):
                    new_data[key] = get_new_string(value)
                else:
                    new_data[key] = replace_requires(value)
            return new_data

        return data

    for field in ['export_data']:
        for key in list(data[field]):
            if key.startswith(old_start):
                new_key = get_new_string(key)
                data[field][new_key] = data[field][key]
                del data[field][key]

    for field in ['unique_identifiers', 'all_fields_info']:
        for key in list(metadata[field].keys()):
            if key.startswith(old_start):
                new_key = get_new_string(key)
                metadata[field][new_key] = metadata[field][key]
                del metadata[field][key]

    metadata['all_fields_info'] = replace_requires(metadata['all_fields_info'])
