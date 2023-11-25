# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Test archive file migration from export version 0.7 to 0.8"""
from aiida.storage.sqlite_zip.migrations.legacy.v07_to_v08 import migrate_v7_to_v8, migration_default_link_label


def test_migrate_external(migrate_from_func):
    """Test the migration on the test archive provided by the external test package."""
    _, data = migrate_from_func('export_v0.7_manual.aiida', '0.7', '0.8', migrate_v7_to_v8)

    # Check that no links have the label '_return', since it should now be 'result'
    illegal_label = '_return'
    for link in data.get('links_uuid'):
        assert link['label'] != illegal_label, (
            f'The illegal link label {illegal_label} was not expected to be present - ' "it should now be 'result'"
        )


def test_migration_0043_default_link_label():
    """Check link labels are migrated properly."""
    # data has one "valid" link, in the form of <label="a_good_label">.
    # data also has one "invalid" link, in form of <label="_return">.
    # After the migration, the "invalid" link should have been updated to the "valid" link <label="result">
    data = {
        'links_uuid': [
            {'input': 'some-random-uuid', 'output': 'some-other-random-uuid', 'label': '_return', 'type': 'return'},
            {
                'input': 'some-random-uuid',
                'output': 'some-other-random-uuid',
                'label': 'a_good_label',
                'type': 'return',
            },
        ]
    }

    migration_default_link_label(data)

    assert data == {
        'links_uuid': [
            {'input': 'some-random-uuid', 'output': 'some-other-random-uuid', 'label': 'result', 'type': 'return'},
            {
                'input': 'some-random-uuid',
                'output': 'some-other-random-uuid',
                'label': 'a_good_label',
                'type': 'return',
            },
        ]
    }
