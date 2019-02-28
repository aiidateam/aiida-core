# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=invalid-name,protected-access
"""Tests for `verdi database`."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import enum

from click.testing import CliRunner

from aiida.backends.testbase import AiidaTestCase
from aiida.cmdline.commands import cmd_database
from aiida.common.links import LinkType
from aiida.orm import Data, Node, CalculationNode, WorkflowNode


class TestVerdiDatabasaIntegrity(AiidaTestCase):
    """Tests for `verdi database integrity`."""

    def setUp(self):
        self.cli_runner = CliRunner()

    def tearDown(self):
        self.reset_database()

    def test_detect_invalid_links_workflow_create(self):
        """Test `verdi database integrity detect-invalid-links` outgoing `create` from `workflow`."""
        result = self.cli_runner.invoke(cmd_database.detect_invalid_links, [])
        self.assertEqual(result.exit_code, 0)
        self.assertClickResultNoException(result)

        # Create an invalid link: outgoing `create` from a workflow
        data = Data().store().backend_entity
        workflow = WorkflowNode().store().backend_entity

        data.add_incoming(workflow, link_type=LinkType.CREATE, link_label='create')

        result = self.cli_runner.invoke(cmd_database.detect_invalid_links, [])
        self.assertNotEqual(result.exit_code, 0)
        self.assertIsNotNone(result.exception)

    def test_detect_invalid_links_calculation_return(self):
        """Test `verdi database integrity detect-invalid-links` outgoing `return` from `calculation`."""
        result = self.cli_runner.invoke(cmd_database.detect_invalid_links, [])
        self.assertEqual(result.exit_code, 0)
        self.assertClickResultNoException(result)

        # Create an invalid link: outgoing `return` from a calculation
        data = Data().store().backend_entity
        calculation = CalculationNode().store().backend_entity

        data.add_incoming(calculation, link_type=LinkType.RETURN, link_label='return')

        result = self.cli_runner.invoke(cmd_database.detect_invalid_links, [])
        self.assertNotEqual(result.exit_code, 0)
        self.assertIsNotNone(result.exception)

    def test_detect_invalid_links_calculation_call(self):
        """Test `verdi database integrity detect-invalid-links` outgoing `call` from `calculation`."""
        result = self.cli_runner.invoke(cmd_database.detect_invalid_links, [])
        self.assertEqual(result.exit_code, 0)
        self.assertClickResultNoException(result)

        # Create an invalid link: outgoing `call` from a calculation
        worklow = WorkflowNode().store().backend_entity
        calculation = CalculationNode().store().backend_entity

        worklow.add_incoming(calculation, link_type=LinkType.CALL_WORK, link_label='call')

        result = self.cli_runner.invoke(cmd_database.detect_invalid_links, [])
        self.assertNotEqual(result.exit_code, 0)
        self.assertIsNotNone(result.exception)

    def test_detect_invalid_links_create_links(self):
        """Test `verdi database integrity detect-invalid-links` when there are multiple incoming `create` links."""
        result = self.cli_runner.invoke(cmd_database.detect_invalid_links, [])
        self.assertEqual(result.exit_code, 0)
        self.assertClickResultNoException(result)

        # Create an invalid link: two `create` links
        data = Data().store().backend_entity
        calculation = CalculationNode().store().backend_entity

        data.add_incoming(calculation, link_type=LinkType.CREATE, link_label='create')
        data.add_incoming(calculation, link_type=LinkType.CREATE, link_label='create')

        result = self.cli_runner.invoke(cmd_database.detect_invalid_links, [])
        self.assertNotEqual(result.exit_code, 0)
        self.assertIsNotNone(result.exception)

    def test_detect_invalid_links_call_links(self):
        """Test `verdi database integrity detect-invalid-links` when there are multiple incoming `call` links."""
        result = self.cli_runner.invoke(cmd_database.detect_invalid_links, [])
        self.assertEqual(result.exit_code, 0)
        self.assertClickResultNoException(result)

        # Create an invalid link: two `call` links
        workflow = WorkflowNode().store().backend_entity
        calculation = CalculationNode().store().backend_entity

        calculation.add_incoming(workflow, link_type=LinkType.CALL_CALC, link_label='call')
        calculation.add_incoming(workflow, link_type=LinkType.CALL_CALC, link_label='call')

        result = self.cli_runner.invoke(cmd_database.detect_invalid_links, [])
        self.assertNotEqual(result.exit_code, 0)
        self.assertIsNotNone(result.exception)

    def test_detect_invalid_links_unknown_link_type(self):
        """Test `verdi database integrity detect-invalid-links` when link type is invalid."""
        result = self.cli_runner.invoke(cmd_database.detect_invalid_links, [])
        self.assertEqual(result.exit_code, 0)
        self.assertClickResultNoException(result)

        class WrongLinkType(enum.Enum):

            WRONG_CREATE = 'wrong_create'

        # Create an invalid link: invalid link type
        data = Data().store().backend_entity
        calculation = CalculationNode().store().backend_entity

        data.add_incoming(calculation, link_type=WrongLinkType.WRONG_CREATE, link_label='create')

        result = self.cli_runner.invoke(cmd_database.detect_invalid_links, [])
        self.assertNotEqual(result.exit_code, 0)
        self.assertIsNotNone(result.exception)

    def test_detect_invalid_nodes_unknown_node_type(self):
        """Test `verdi database integrity detect-invalid-nodes` when node type is invalid."""
        result = self.cli_runner.invoke(cmd_database.detect_invalid_nodes, [])
        self.assertEqual(result.exit_code, 0)
        self.assertClickResultNoException(result)

        # Create a node with invalid type: a base Node type string is considered invalid
        # Note that there is guard against storing base Nodes for this reason, which we temporarily disable
        Node._storable = True
        Node().store()
        Node._storable = False

        result = self.cli_runner.invoke(cmd_database.detect_invalid_nodes, [])
        self.assertNotEqual(result.exit_code, 0)
        self.assertIsNotNone(result.exception)
