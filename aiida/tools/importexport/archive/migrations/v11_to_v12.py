# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Migration from v0.11 to v0.12, used by ``verdi archive migrate`` command.

This migration applies the name change of the ``Computer`` attribute ``name`` to ``label``.
"""
from aiida.tools.importexport.archive.common import CacheFolder
from .utils import verify_metadata_version, update_metadata


def migrate_v11_to_v12(folder: CacheFolder):
    """Migration of export files from v0.11 to v0.12."""
    old_version = '0.11'
    new_version = '0.12'

    _, metadata = folder.load_json('metadata.json')

    verify_metadata_version(metadata, old_version)
    update_metadata(metadata, new_version)

    _, data = folder.load_json('data.json')

    # Apply migrations
    for attributes in data.get('export_data', {}).get('Computer', {}).values():
        attributes['label'] = attributes.pop('name')

    try:
        metadata['all_fields_info']['Computer']['label'] = metadata['all_fields_info']['Computer'].pop('name')
    except KeyError:
        pass

    folder.write_json('metadata.json', metadata)
    folder.write_json('data.json', data)
