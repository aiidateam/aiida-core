###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the CalculationNode and CalcJobNode class."""

import pytest

from aiida.common.datastructures import CalcJobState
from aiida.common.exceptions import ModificationNotAllowed
from aiida.orm import CalcJobNode, CalculationNode


class TestProcessNode:
    """These tests check the features of process nodes that differ from the base Node type"""

    boolval = True
    intval = 123
    floatval = 4.56
    stringval = 'aaaa'
    listval = [1, 's', True, None]
    dictval = {
        'num': 3,
        'something': 'else',
        'emptydict': {},
        'recursive': {
            'integer': 1,
            'boolean': True,
            'float': 1.2,
            'list': [1, 2, None],
            'dictionary': {'string': 'z', 'none': None, 'empty_dictionary': {}, 'empty_list': []},
        },
    }
    stateval = 'RUNNING'
    emptydict = {}
    emptylist = []

    @pytest.fixture(autouse=True)
    def init_profile(self, aiida_localhost):
        """Initialize the profile."""
        self.calcjob = CalcJobNode()
        self.calcjob.computer = aiida_localhost
        self.calcjob.set_options({'resources': {'num_machines': 1, 'num_mpiprocs_per_machine': 1}})
        self.calcjob.store()

    @staticmethod
    def test_process_state():
        """Check the properties of a newly created bare CalculationNode"""
        process_node = CalculationNode()

        assert process_node.is_terminated is False
        assert process_node.is_excepted is False
        assert process_node.is_killed is False
        assert process_node.is_finished is False
        assert process_node.is_finished_ok is False
        assert process_node.is_failed is False

    def test_process_node_updatable_attribute(self):
        """Check that updatable attributes and only those can be mutated for a stored but unsealed CalculationNode."""
        node = CalculationNode()
        attrs_to_set = {
            'bool': self.boolval,
            'integer': self.intval,
            'float': self.floatval,
            'string': self.stringval,
            'dict': self.dictval,
            'list': self.listval,
            'state': self.stateval,
        }

        for key, value in attrs_to_set.items():
            node.base.attributes.set(key, value)

        # Check before storing
        node.base.attributes.set(CalculationNode.PROCESS_STATE_KEY, self.stateval)
        assert node.base.attributes.get(CalculationNode.PROCESS_STATE_KEY) == self.stateval

        node.store()

        # Check after storing
        assert node.base.attributes.get(CalculationNode.PROCESS_STATE_KEY) == self.stateval

        # I should be able to mutate the updatable attribute but not the others
        node.base.attributes.set(CalculationNode.PROCESS_STATE_KEY, 'FINISHED')
        node.base.attributes.delete(CalculationNode.PROCESS_STATE_KEY)

        # Deleting non-existing attribute should raise attribute error
        with pytest.raises(AttributeError):
            node.base.attributes.delete(CalculationNode.PROCESS_STATE_KEY)

        with pytest.raises(ModificationNotAllowed):
            node.base.attributes.set('bool', False)

        with pytest.raises(ModificationNotAllowed):
            node.base.attributes.delete('bool')

        node.seal()

        # After sealing, even updatable attributes should be immutable
        with pytest.raises(ModificationNotAllowed):
            node.base.attributes.set(CalculationNode.PROCESS_STATE_KEY, 'FINISHED')

        with pytest.raises(ModificationNotAllowed):
            node.base.attributes.delete(CalculationNode.PROCESS_STATE_KEY)

    def test_get_description(self):
        assert self.calcjob.get_description() == ''
        self.calcjob.set_state(CalcJobState.PARSING)
        assert self.calcjob.get_description() == CalcJobState.PARSING.value

    def test_get_authinfo(self):
        """Test that we can get the AuthInfo object from the calculation instance."""
        from aiida.orm import AuthInfo

        authinfo = self.calcjob.get_authinfo()
        assert isinstance(authinfo, AuthInfo)

    def test_get_transport(self):
        """Test that we can get the Transport object from the calculation instance."""
        from aiida.transports import Transport

        transport = self.calcjob.get_transport()
        assert isinstance(transport, Transport)
