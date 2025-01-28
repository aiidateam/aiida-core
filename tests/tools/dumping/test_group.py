###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the dumping of group data to disk."""

# TODO: Test that de-duplication also works for calculations

import pytest

from aiida import orm


@pytest.mark.usefixtures('aiida_profile_clean')
@pytest.fixture(scope='session', autouse=True)
def setup_profile_groups(generate_calculation_node_add, generate_workchain_multiply_add):
    # Create nodes for profile storage
    int_node = orm.Int(1).store()
    _ = generate_calculation_node_add()
    _ = generate_workchain_multiply_add()
    cj_node = generate_calculation_node_add()
    wc_node = generate_workchain_multiply_add()

    # Create the various groups
    add_group = orm.Group.collection.get_or_create(label='add')[0]
    multiply_add_group = orm.Group.collection.get_or_create(label='multiply-add')[0]
    cj_dupl_group = orm.Group.collection.get_or_create(label='cj-dupl')[0]
    wc_dupl_group = orm.Group.collection.get_or_create(label='wc-dupl')[0]
    no_process_group = orm.Group.collection.get_or_create(label='add')[0]

    # Populate groups
    add_group.add_nodes([cj_node])
    multiply_add_group.add_nodes([wc_node])
    cj_dupl_group.add_nodes([cj_node])
    wc_dupl_group.add_nodes([wc_node])
    no_process_group.add_nodes([int_node])

    # Not sure if this is actually needed?
    return {
        'add_group': add_group,
        'multiply_add_group': multiply_add_group,
        'cj_dupl_group': cj_dupl_group,
        'wc_dupl_group': wc_dupl_group,
        'no_process_group': no_process_group,
    }


class TestGroupDumper:
    def test_should_dump_processes(self):
        print(orm.QueryBuilder().append(orm.Group).all(flat=True))
        assert False
        # pass

    def test_get_nodes(self):
        pass

    def test_get_processes(self):
        pass

    def test_dump_processes(self):
        pass

    def test_dump_calculations(self):
        pass

    def test_dump_workflows(self):
        pass

    def test_dump(self):
        pass
