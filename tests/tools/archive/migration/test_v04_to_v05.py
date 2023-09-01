# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Test archive file migration from export version 0.4 to 0.5"""
from aiida.storage.sqlite_zip.migrations.legacy import migrate_v4_to_v5  # type: ignore[attr-defined]


def test_migrate_external(migrate_from_func):
    """Test the migration on the test archive provided by the external test package."""
    metadata, data = migrate_from_func('export_v0.4.aiida', '0.4', '0.5', migrate_v4_to_v5)

    # Check schema-changes
    removed_computer_attrs = {'transport_params'}
    removed_node_attrs = {'nodeversion', 'public'}
    for change in removed_computer_attrs:
        # data.json
        for computer in data['export_data']['Computer'].values():
            assert change not in computer, f"'{change}' unexpectedly found for {computer}"
        # metadata.json
        assert change not in metadata['all_fields_info']['Computer'], (
            f"'{change}' unexpectedly found in metadata.json for Computer"
        )
    for change in removed_node_attrs:
        # data.json
        for node in data['export_data']['Node'].values():
            assert change not in node, f"'{change}' unexpectedly found for {node}"
        # metadata.json
        assert change not in metadata['all_fields_info']['Node'], (
            f"'{change}' unexpectedly found in metadata.json for Node"
        )
