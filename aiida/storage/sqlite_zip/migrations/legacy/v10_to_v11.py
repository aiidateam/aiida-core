# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Migration from v0.10 to v0.11, used by ``verdi archive migrate`` command.

This migration applies the name change of the ``Computer`` attribute ``name`` to ``label``.
"""
from ..utils import update_metadata, verify_metadata_version  # pylint: disable=no-name-in-module


def migrate_v10_to_v11(metadata: dict, data: dict) -> None:
    """Migration of export files from v0.10 to v0.11."""
    old_version = '0.10'
    new_version = '0.11'

    verify_metadata_version(metadata, old_version)
    update_metadata(metadata, new_version)

    # Apply migrations
    for attributes in data.get('export_data', {}).get('Computer', {}).values():
        attributes['label'] = attributes.pop('name')

    try:
        metadata['all_fields_info']['Computer']['label'] = metadata['all_fields_info']['Computer'].pop('name')
    except KeyError:
        pass
