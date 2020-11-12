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
# pylint: disable=invalid-name
from aiida.tools.importexport.archive.common import CacheFolder

from .utils import verify_metadata_version, update_metadata


def migrate_v9_to_v10(folder: CacheFolder):
    """Migration of archive files from v0.9 to v0.10."""
    old_version = '0.9'
    new_version = '0.10'

    _, metadata = folder.load_json('metadata.json')

    verify_metadata_version(metadata, old_version)
    update_metadata(metadata, new_version)

    metadata['all_fields_info']['Node']['attributes'] = {'convert_type': 'jsonb'}
    metadata['all_fields_info']['Node']['extras'] = {'convert_type': 'jsonb'}
    metadata['all_fields_info']['Group']['extras'] = {'convert_type': 'jsonb'}

    folder.write_json('metadata.json', metadata)
