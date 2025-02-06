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

from datetime import datetime

import pytest

from aiida import orm
from aiida.tools.dumping import CollectionDumper

# Fixture that depends on generate_calculation_node_add_class
# @pytest.fixture(scope="class")
# def setup_calculation_node_add_class(generate_calculation_node_add_class):
#     # This will make sure the fixture runs and is available for setup_class
#     generate_calculation_node_add_class()  # You can also do any additional setup here


@pytest.fixture()
def setup_no_process_group() -> orm.Group:
    no_process_group, _ = orm.Group.collection.get_or_create(label='no-process')
    if no_process_group.is_empty:
        int_node = orm.Int(1).store()
        no_process_group.add_nodes([int_node])
    return no_process_group


@pytest.fixture()
def setup_add_group(generate_calculation_node_add) -> orm.Group:
    add_group, _ = orm.Group.collection.get_or_create(label='add')
    if add_group.is_empty:
        add_node = generate_calculation_node_add()
        add_group.add_nodes([add_node])
    return add_group


@pytest.fixture()
def setup_multiply_add_group(generate_workchain_multiply_add) -> orm.Group:
    multiply_add_group, _ = orm.Group.collection.get_or_create(label='multiply-add')
    if multiply_add_group.is_empty:
        multiply_add_node = generate_workchain_multiply_add()
        multiply_add_group.add_nodes([multiply_add_node])
    return multiply_add_group


@pytest.fixture()
def duplicate_group():
    def _duplicate_group(source_group: orm.Group, dest_group_label: str):
        dupl_group, created = orm.Group.collection.get_or_create(label=dest_group_label)
        dupl_group.add_nodes(list(source_group.nodes))
        return dupl_group

    return _duplicate_group


@pytest.mark.usefixtures('aiida_profile_clean_class')
class TestCollectionDumper:
    def test_should_dump_processes(self, setup_no_process_group, setup_add_group):
        """"""
        no_process_group: orm.Group = setup_no_process_group
        add_group: orm.Group = setup_add_group

        collection_dumper = CollectionDumper(collection=no_process_group)

        assert collection_dumper.should_dump_processes() is False

        collection_dumper = CollectionDumper(collection=add_group)

        assert collection_dumper.should_dump_processes() is True

    @pytest.mark.usefixtures('aiida_profile_clean')
    def test_get_nodes(
        self, setup_no_process_group, setup_add_group, setup_multiply_add_group, generate_calculation_node_add
    ):
        add_group: orm.Group = setup_add_group

        collection_dumper = CollectionDumper(collection=add_group)
        nodes = collection_dumper._get_nodes()
        group_node = orm.load_node(nodes[0])
        group_node_uuid = nodes[0]

        assert len(nodes) == 1
        assert isinstance(nodes[0], str)
        assert isinstance(group_node, orm.CalcJobNode)
        assert nodes[0] == group_node_uuid

        # Now, add another CalcJobNode to the profile
        # As not part of the group, should not be returned
        cj_node1 = generate_calculation_node_add()
        nodes = collection_dumper._get_nodes()
        assert len(nodes) == 1

        # Now, add the node to the group, should be captured by get_nodes
        add_group.add_nodes([cj_node1])
        nodes = collection_dumper._get_nodes()
        assert len(nodes) == 2

        # Filtering by time should work
        collection_dumper.base_dumper.last_dump_time = datetime.now().astimezone()

        cj_node2 = generate_calculation_node_add()
        add_group.add_nodes([cj_node2])

        nodes = collection_dumper._get_nodes()
        assert len(nodes) == 1
        assert nodes[0] == cj_node2.uuid

        with pytest.raises(TypeError):
            collection_dumper = CollectionDumper(collection=[1])
            collection_dumper._get_nodes()

    def test_get_processes_to_dump(self, setup_add_group, setup_multiply_add_group, duplicate_group):
        add_group: orm.Group = setup_add_group
        multiply_add_group: orm.Group = setup_multiply_add_group

        add_nodes = list(add_group.nodes)
        multiply_add_nodes = list(multiply_add_group.nodes)

        add_dumper = CollectionDumper(collection=add_group)
        multiply_add_dumper = CollectionDumper(collection=multiply_add_group)

        add_process_to_dump = add_dumper._get_processes_to_dump()
        assert len(add_process_to_dump.calculations) == 1
        assert add_process_to_dump.calculations[0].uuid == add_nodes[0].uuid
        assert len(add_process_to_dump.workflows) == 0

        multiply_add_processes_to_dump = multiply_add_dumper._get_processes_to_dump()

        assert len(multiply_add_processes_to_dump.calculations) == 2
        assert set(multiply_add_processes_to_dump.calculations) == set(multiply_add_nodes[0].called_descendants)
        assert len(multiply_add_processes_to_dump.workflows) == 1
        assert multiply_add_processes_to_dump.calculations[0].uuid == multiply_add_nodes[0].uuid

        # TODO: Test here also de-duplication with a Workflow with a sub-workflow

    def test_dump_calculations(self, setup_add_group, setup_multiply_add_group, tmp_path):
        add_group: orm.Group = setup_add_group
        multiply_add_group: orm.Group = setup_multiply_add_group

        add_group_path = tmp_path / 'add_group'
        multiply_add_group_path = tmp_path / 'multiply_add_group'

        add_dumper = CollectionDumper(collection=add_group, output_path=add_group_path)
        multiply_add_dumper = CollectionDumper(collection=multiply_add_group, output_path=multiply_add_group_path)

        add_processes_to_dump = add_dumper._get_processes_to_dump()

        add_dumper._dump_calculations(add_processes_to_dump.calculations)

        assert (add_group_path / 'calculations' / 'ArithmeticAddCalculation-4' / 'inputs' / 'aiida.in').exists()

        multiply_add_processes_to_dump = multiply_add_dumper._get_processes_to_dump()

        multiply_add_dumper._dump_calculations(multiply_add_processes_to_dump.calculations)

        pytest.set_trace()

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
