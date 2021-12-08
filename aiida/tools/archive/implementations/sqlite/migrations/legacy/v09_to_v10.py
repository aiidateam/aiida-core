# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Migration from v0.9 to v0.10, used by `verdi export migrate` command."""
# pylint: disable=invalid-name,unused-argument
from ..utils import update_metadata, verify_metadata_version  # pylint: disable=no-name-in-module


def migrate_v9_to_v10(metadata: dict, data: dict) -> None:
    """Migration of archive files from v0.9 to v0.10."""
    old_version = '0.9'
    new_version = '0.10'

    verify_metadata_version(metadata, old_version)
    update_metadata(metadata, new_version)

    metadata['all_fields_info']['Node']['attributes'] = {'convert_type': 'jsonb'}
    metadata['all_fields_info']['Node']['extras'] = {'convert_type': 'jsonb'}
    metadata['all_fields_info']['Group']['extras'] = {'convert_type': 'jsonb'}
