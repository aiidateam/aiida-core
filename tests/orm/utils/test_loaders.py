###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Module to test orm utilities to load nodes, codes etc."""

import pytest

from aiida.common.exceptions import NotExistent
from aiida.orm import Data, Group, Node
from aiida.orm.utils import load_code, load_computer, load_entity, load_group, load_node
from aiida.orm.utils.loaders import NodeEntityLoader


class TestOrmUtils:
    """Test orm utils."""

    @pytest.fixture(autouse=True)
    def init_profile(self, aiida_localhost):
        """Initialize the profile."""
        self.computer = aiida_localhost

    def test_load_entity(self):
        """Test the functionality of load_entity which is the base function for the other loader functions."""
        entity_loader = NodeEntityLoader

        with pytest.raises(TypeError):
            load_entity(entity_loader=None)

        # No identifier keyword arguments specified
        with pytest.raises(ValueError):
            load_entity(entity_loader)

        # More than one identifier keyword arguments specified
        with pytest.raises(ValueError):
            load_entity(entity_loader, identifier='a', pk=1)

        with pytest.raises(TypeError):
            load_entity(entity_loader, pk='1')

        with pytest.raises(TypeError):
            load_entity(entity_loader, uuid=1)

        with pytest.raises(TypeError):
            load_entity(entity_loader, label=1)

    def test_load_code(self):
        """Test the functionality of load_code."""
        from aiida.orm import InstalledCode

        label = 'compy'
        code = InstalledCode(label=label, computer=self.computer, filepath_executable='/x.x').store()

        # Load through full label
        loaded_code = load_code(code.full_label)
        assert loaded_code.uuid == code.uuid

        # Load through label
        loaded_code = load_code(code.label)
        assert loaded_code.uuid == code.uuid

        # Load through uuid
        loaded_code = load_code(code.uuid)
        assert loaded_code.uuid == code.uuid

        # Load through pk
        loaded_code = load_code(code.pk)
        assert loaded_code.uuid == code.uuid

        # Load through full label explicitly
        loaded_code = load_code(label=code.full_label)
        assert loaded_code.uuid == code.uuid

        # Load through label explicitly
        loaded_code = load_code(label=code.label)
        assert loaded_code.uuid == code.uuid

        # Load through uuid explicitly
        loaded_code = load_code(uuid=code.uuid)
        assert loaded_code.uuid == code.uuid

        # Load through pk explicitly
        loaded_code = load_code(pk=code.pk)
        assert loaded_code.uuid == code.uuid

        # Load through partial uuid without a dash
        loaded_code = load_code(uuid=code.uuid[:8])
        assert loaded_code.uuid == code.uuid

        # Load through partial uuid including a dash
        loaded_code = load_code(uuid=code.uuid[:10])
        assert loaded_code.uuid == code.uuid

        with pytest.raises(NotExistent):
            load_code('non-existent-uuid')

    def test_load_computer(self):
        """Test the functionality of load_group."""
        computer = self.computer

        # Load through label
        loaded_computer = load_computer(computer.label)
        assert loaded_computer.uuid == computer.uuid

        # Load through uuid
        loaded_computer = load_computer(computer.uuid)
        assert loaded_computer.uuid == computer.uuid

        # Load through pk
        loaded_computer = load_computer(computer.pk)
        assert loaded_computer.uuid == computer.uuid

        # Load through label explicitly
        loaded_computer = load_computer(label=computer.label)
        assert loaded_computer.uuid == computer.uuid

        # Load through uuid explicitly
        loaded_computer = load_computer(uuid=computer.uuid)
        assert loaded_computer.uuid == computer.uuid

        # Load through pk explicitly
        loaded_computer = load_computer(pk=computer.pk)
        assert loaded_computer.uuid == computer.uuid

        # Load through partial uuid without a dash
        loaded_computer = load_computer(uuid=computer.uuid[:8])
        assert loaded_computer.uuid == computer.uuid

        # Load through partial uuid including a dash
        loaded_computer = load_computer(uuid=computer.uuid[:10])
        assert loaded_computer.uuid == computer.uuid

        with pytest.raises(NotExistent):
            load_computer('non-existent-uuid')

    def test_load_group(self):
        """Test the functionality of load_group."""
        name = 'groupie'
        group = Group(label=name).store()

        # Load through label
        loaded_group = load_group(group.label)
        assert loaded_group.uuid == group.uuid

        # Load through uuid
        loaded_group = load_group(group.uuid)
        assert loaded_group.uuid == group.uuid

        # Load through pk
        loaded_group = load_group(group.pk)
        assert loaded_group.uuid == group.uuid

        # Load through label explicitly
        loaded_group = load_group(label=group.label)
        assert loaded_group.uuid == group.uuid

        # Load through uuid explicitly
        loaded_group = load_group(uuid=group.uuid)
        assert loaded_group.uuid == group.uuid

        # Load through pk explicitly
        loaded_group = load_group(pk=group.pk)
        assert loaded_group.uuid == group.uuid

        # Load through partial uuid without a dash
        loaded_group = load_group(uuid=group.uuid[:8])
        assert loaded_group.uuid == group.uuid

        # Load through partial uuid including a dash
        loaded_group = load_group(uuid=group.uuid[:10])
        assert loaded_group.uuid == group.uuid

        with pytest.raises(NotExistent):
            load_group('non-existent-uuid')

    def test_load_node(self):
        """Test the functionality of load_node."""
        node = Data().store()

        # Load through uuid
        loaded_node = load_node(node.uuid)
        assert isinstance(loaded_node, Node)
        assert loaded_node.uuid == node.uuid

        # Load through pk
        loaded_node = load_node(node.pk)
        assert isinstance(loaded_node, Node)
        assert loaded_node.uuid == node.uuid

        # Load through uuid explicitly
        loaded_node = load_node(uuid=node.uuid)
        assert isinstance(loaded_node, Node)
        assert loaded_node.uuid == node.uuid

        # Load through pk explicitly
        loaded_node = load_node(pk=node.pk)
        assert isinstance(loaded_node, Node)
        assert loaded_node.uuid == node.uuid

        # Load through partial uuid without a dash
        loaded_node = load_node(uuid=node.uuid[:8])
        assert isinstance(loaded_node, Node)
        assert loaded_node.uuid == node.uuid

        # Load through partial uuid including a dashs
        loaded_node = load_node(uuid=node.uuid[:10])
        assert isinstance(loaded_node, Node)
        assert loaded_node.uuid == node.uuid

        with pytest.raises(NotExistent):
            load_group('non-existent-uuid')
