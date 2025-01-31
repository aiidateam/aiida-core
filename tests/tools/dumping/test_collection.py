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
# TODO: Test incremental dumping

import pytest

from aiida import orm
from aiida.tools.dumping import BaseDumper, CollectionDumper, ProcessDumper

# Fixture that depends on generate_calculation_node_add_class
# @pytest.fixture(scope="class")
# def setup_calculation_node_add_class(generate_calculation_node_add_class):
#     # This will make sure the fixture runs and is available for setup_class
#     generate_calculation_node_add_class()  # You can also do any additional setup here


@pytest.fixture()
def setup_no_process_group():
    no_process_group, _ = orm.Group.collection.get_or_create(label='no-process')
    if no_process_group.is_empty:
        int_node = orm.Int(1).store()
        no_process_group.add_nodes([int_node])
    return no_process_group


@pytest.fixture()
def setup_add_group(generate_calculation_node_add):
    add_group, _ = orm.Group.collection.get_or_create(label='add')
    if add_group.is_empty:
        add_node = generate_calculation_node_add()
        add_group.add_nodes([add_node])
    return add_group


@pytest.fixture()
def setup_multiply_add_group(generate_workchain_multiply_add):
    multiply_add_group, _ = orm.Group.collection.get_or_create(label='multiply-add')
    if multiply_add_group.is_empty:
        multiply_add_node = generate_workchain_multiply_add()
        multiply_add_group.add_nodes([multiply_add_node])
    return multiply_add_group


@pytest.fixture()
def multiply_process_groups(): ...


@pytest.mark.usefixtures('aiida_profile_clean_class')
class TestCollectionDumper:
    def test_should_dump_processes(self, setup_no_process_group, setup_add_group):
        """"""
        no_process_group: orm.Group = setup_no_process_group
        add_group: orm.Group = setup_add_group

        base_dumper = BaseDumper()
        process_dumper = ProcessDumper()

        group_dumper = CollectionDumper(base_dumper=base_dumper, process_dumper=process_dumper, collection=no_process_group)

        assert group_dumper._should_dump_processes() is False

        group_dumper = CollectionDumper(base_dumper=base_dumper, process_dumper=process_dumper, collection=add_group)

        assert group_dumper._should_dump_processes() is True

    # def test_get_nodes(self):
    #     pass

    # def test_get_processes(self):
    #     pass

    # def test_dump_processes(self):
    #     pass

    # def test_dump_calculations(self):
    #     pass

    # def test_dump_workflows(self):
    #     pass

    # def test_dump(self):
    #     pass


#######3

# def test_setup_profile(
#     self,
#     generate_calculation_node_add,
#     generate_workchain_multiply_add,
#     generate_calculation_node_io,
#     generate_workchain_node_io,
# ):
#     # TODO: This is a hack... and not actually a real test
#     # TODO: I'm using the `aiida_profile_clean_class` fiture to make sure I have a clean profile for this class
#     # TODO: However, this method is not an actual test, but sets up the profile data how I want it for testing
#     # TODO: Ideally, I'd create a class-scoped fixture that does the setup
#     # TODO: Or define a `setup_class` method
#     # TODO: However, as most of AiiDA's fixtures are function-scoped, I didn't manage to get any of these approaches
#     # TODO: To work, due to pytest's ScopeMismatch exceptions

# # Create nodes for profile storage
# ## Not in any group
# int_node = orm.Int(1).store()
# _ = generate_calculation_node_add()
# _ = generate_workchain_multiply_add()
# ## For putting into groups
# add_node = generate_calculation_node_add()
# multiply_add_node = generate_workchain_multiply_add()

# # Create the various groups
# add_group, _ = orm.Group.collection.get_or_create(label='add')
# multiply_add_group, _ = orm.Group.collection.get_or_create(label='multiply-add')
# cj_dupl_group, _ = orm.Group.collection.get_or_create(label='cj-dupl')
# wc_dupl_group, _ = orm.Group.collection.get_or_create(label='wc-dupl')
# no_process_group, _ = orm.Group.collection.get_or_create(label='no-process')

# # Populate groups
# add_group.add_nodes([add_node])
# multiply_add_group.add_nodes([multiply_add_node])
# cj_dupl_group.add_nodes([add_node])
# wc_dupl_group.add_nodes([multiply_add_node])
# no_process_group.add_nodes([int_node])

# self.add_group = add_group
# self.multiply_add_group = multiply_add_group
# self.cj_dupl_group = cj_dupl_group
# self.wc_dupl_group = wc_dupl_group
# self.no_process_group = no_process_group
