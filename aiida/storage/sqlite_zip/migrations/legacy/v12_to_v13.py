# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Migration from v0.12 to v0.13, used by ``verdi archive migrate`` command.

This migration is necessary after the v0.11 to v0.12 migration did not add the core prefix
to transport entry points.
"""
from ..utils import update_metadata, verify_metadata_version  # pylint: disable=no-name-in-module

MAPPING_TRANSPORTS = {
    'local': 'core.local',
    'ssh': 'core.ssh',
}


def migrate_v12_to_v13(metadata: dict, data: dict) -> None:
    """Migration of export files from v0.12 to v0.13."""
    # pylint: disable=too-many-branches
    old_version = '0.12'
    new_version = '0.13'

    verify_metadata_version(metadata, old_version)
    update_metadata(metadata, new_version)

    # Migrate transport entry point names
    for values in data.get('export_data', {}).get('Computer', {}).values():

        if 'transport_type' in values:
            try:
                new_transport_type = MAPPING_TRANSPORTS[values['transport_type']]
            except KeyError:
                pass
            else:
                values['transport_type'] = new_transport_type
