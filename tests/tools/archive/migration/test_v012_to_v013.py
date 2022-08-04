# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Test archive file migration from export version 0.12 to 0.13"""
from aiida.storage.sqlite_zip.migrations.legacy.v12_to_v13 import migrate_v12_to_v13


def test_migrate_v12_to_v13(core_archive, migrate_from_func):
    """Test the data migration of transport entry point strings
    e.g. from local to core.local.
    """

    # Migrate v0.12 to v0.13
    _, data = migrate_from_func('export_0.12_simple.aiida', '0.12', '0.13', migrate_v12_to_v13, core_archive)

    for values in data.get('export_data', {}).get('Computer', {}).values():
        if 'transport_type' in values:
            assert values['transport_type'] in [
                'core.local',
                'core.ssh',
            ], (f"encountered illegal transport entry point string `{values['transport_type']}`")
