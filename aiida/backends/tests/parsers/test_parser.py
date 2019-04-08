# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Test for the `Parser` base class."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from aiida import orm
from aiida.backends.testbase import AiidaTestCase
from aiida.common import LinkType
from aiida.engine import CalcJob
from aiida.parsers import Parser
from aiida.plugins import CalculationFactory, ParserFactory

ArithmeticAddCalculation = CalculationFactory('arithmetic.add')  # pylint: disable=invalid-name
ArithmeticAddParser = ParserFactory('arithmetic.add')  # pylint: disable=invalid-name


class CustomCalcJob(CalcJob):
    """`CalcJob` implementation with output namespace and additional output node that should be passed to parser."""

    @classmethod
    def define(cls, spec):
        super(CustomCalcJob, cls).define(spec)
        spec.input('inp', valid_type=orm.Data)
        spec.output('output', pass_to_parser=True)
        spec.output_namespace('out.space', dynamic=True)

    def prepare_for_submission(self):  # pylint: disable=arguments-differ
        pass


class TestParser(AiidaTestCase):
    """Test backend entities and their collections"""

    def test_abstract_parse_method(self):
        """Verify that trying to instantiate base class will raise `TypeError` because of abstract `parse` method."""
        with self.assertRaises(TypeError):
            Parser()  # pylint: disable=abstract-class-instantiated,no-value-for-parameter

    def test_parser_retrieved(self):
        """Verify that the `retrieved` property returns the retrieved `FolderData` node."""
        node = orm.CalcJobNode(computer=self.computer, process_type=ArithmeticAddCalculation.build_process_type())
        node.set_option('resources', {'num_machines': 1, 'num_mpiprocs_per_machine': 1})
        node.set_option('max_wallclock_seconds', 1800)
        node.store()

        retrieved = orm.FolderData().store()
        retrieved.add_incoming(node, link_type=LinkType.CREATE, link_label='retrieved')

        parser = ArithmeticAddParser(node)
        self.assertEqual(parser.node.uuid, node.uuid)
        self.assertEqual(parser.retrieved.uuid, retrieved.uuid)

    def test_parser_exit_codes(self):
        """Ensure that exit codes from the `CalcJob` can be retrieved through the parser instance."""
        node = orm.CalcJobNode(computer=self.computer, process_type=ArithmeticAddCalculation.build_process_type())
        parser = ArithmeticAddParser(node)
        self.assertEqual(parser.exit_codes, ArithmeticAddCalculation.spec().exit_codes)

    def test_parser_get_outputs_for_parsing(self):
        """Make sure that the `get_output_for_parsing` method returns the correct output nodes."""
        ArithmeticAddCalculation.define = CustomCalcJob.define
        node = orm.CalcJobNode(computer=self.computer, process_type=CustomCalcJob.build_process_type())
        node.set_option('resources', {'num_machines': 1, 'num_mpiprocs_per_machine': 1})
        node.set_option('max_wallclock_seconds', 1800)
        node.store()

        retrieved = orm.FolderData().store()
        retrieved.add_incoming(node, link_type=LinkType.CREATE, link_label='retrieved')

        output = orm.Data().store()
        output.add_incoming(node, link_type=LinkType.CREATE, link_label='output')

        parser = ArithmeticAddParser(node)
        outputs_for_parsing = parser.get_outputs_for_parsing()
        self.assertIn('retrieved', outputs_for_parsing)
        self.assertEqual(outputs_for_parsing['retrieved'].uuid, retrieved.uuid)
        self.assertIn('output', outputs_for_parsing)
        self.assertEqual(outputs_for_parsing['output'].uuid, output.uuid)
