###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Test for the `Parser` base class."""

import io

import pytest

from aiida import orm
from aiida.common import LinkType
from aiida.engine import CalcJob
from aiida.parsers import Parser
from aiida.parsers.plugins.arithmetic.add import SimpleArithmeticAddParser  # for demonstration purposes only
from aiida.plugins import CalculationFactory, ParserFactory

ArithmeticAddCalculation = CalculationFactory('core.arithmetic.add')
ArithmeticAddParser = ParserFactory('core.arithmetic.add')


class CustomCalcJob(CalcJob):
    """`CalcJob` implementation with output namespace and additional output node that should be passed to parser."""

    @classmethod
    def define(cls, spec):
        super().define(spec)
        spec.input('inp', valid_type=orm.Data)
        spec.output('output', pass_to_parser=True)
        spec.output_namespace('out.space', dynamic=True)

    def prepare_for_submission(self):
        pass


class BrokenArithmeticAddParser(Parser):
    """Parser for an ``ArithmeticAddCalculation`` job that is intentionally broken.

    It attaches an output that is not defined by the spec of the ``ArithmeticAddCalculation``.
    """

    def parse(self, **kwargs):
        """Intentionally attach an output that is not defined in the output spec of the calculation."""
        self.out('invalid_output', orm.Str('0'))


class ReportArithmeticAddParser(Parser):
    """Parser for an ``ArithmeticAddCalculation`` job that just logs a message at the ``REPORT`` level."""

    def parse(self, **kwargs):
        """Log a message at the ``REPORT`` level."""
        self.logger.report('test the report method.')
        self.out('sum', orm.Int(3))


class TestParser:
    """Test backend entities and their collections"""

    @pytest.fixture(autouse=True)
    def init_profile(self, aiida_localhost):
        """Initialize the profile."""
        self.computer = aiida_localhost

    def test_abstract_parse_method(self):
        """Verify that trying to instantiate base class will raise `TypeError` because of abstract `parse` method."""
        with pytest.raises(TypeError):
            Parser()

    def test_parser_retrieved(self):
        """Verify that the `retrieved` property returns the retrieved `FolderData` node."""
        node = orm.CalcJobNode(computer=self.computer, process_type=ArithmeticAddCalculation.build_process_type())
        node.set_option('resources', {'num_machines': 1, 'num_mpiprocs_per_machine': 1})
        node.set_option('max_wallclock_seconds', 1800)
        node.store()

        retrieved = orm.FolderData().store()
        retrieved.base.links.add_incoming(node, link_type=LinkType.CREATE, link_label='retrieved')

        parser = ArithmeticAddParser(node)
        assert parser.node.uuid == node.uuid
        assert parser.retrieved.uuid == retrieved.uuid

    def test_parser_exit_codes(self):
        """Ensure that exit codes from the `CalcJob` can be retrieved through the parser instance."""
        node = orm.CalcJobNode(computer=self.computer, process_type=ArithmeticAddCalculation.build_process_type())
        parser = ArithmeticAddParser(node)
        assert parser.exit_codes == ArithmeticAddCalculation.spec().exit_codes

    def test_parser_get_outputs_for_parsing(self):
        """Make sure that the `get_output_for_parsing` method returns the correct output nodes."""
        ArithmeticAddCalculation.define = CustomCalcJob.define
        node = orm.CalcJobNode(computer=self.computer, process_type=CustomCalcJob.build_process_type())
        node.set_option('resources', {'num_machines': 1, 'num_mpiprocs_per_machine': 1})
        node.set_option('max_wallclock_seconds', 1800)
        node.store()

        retrieved = orm.FolderData().store()
        retrieved.base.links.add_incoming(node, link_type=LinkType.CREATE, link_label='retrieved')

        output = orm.Data().store()
        output.base.links.add_incoming(node, link_type=LinkType.CREATE, link_label='output')

        parser = ArithmeticAddParser(node)
        outputs_for_parsing = parser.get_outputs_for_parsing()
        assert 'retrieved' in outputs_for_parsing
        assert outputs_for_parsing['retrieved'].uuid == retrieved.uuid
        assert 'output' in outputs_for_parsing
        assert outputs_for_parsing['output'].uuid == output.uuid

    @pytest.mark.requires_rmq
    def test_parse_from_node(self):
        """Test that the `parse_from_node` returns a tuple of the parsed output nodes and a calculation node.

        The calculation node represents the parsing process
        """
        summed = 3
        output_filename = 'aiida.out'

        # Mock the `CalcJobNode` which should have the `retrieved` folder containing the sum in the outputfile file
        # This is the value that should be parsed into the `sum` output node
        node = orm.CalcJobNode(computer=self.computer, process_type=ArithmeticAddCalculation.build_process_type())
        node.set_option('resources', {'num_machines': 1, 'num_mpiprocs_per_machine': 1})
        node.set_option('max_wallclock_seconds', 1800)
        node.set_option('output_filename', output_filename)
        node.store()

        retrieved = orm.FolderData()
        retrieved.base.repository.put_object_from_filelike(io.StringIO(f'{summed}'), output_filename)
        retrieved.store()
        retrieved.base.links.add_incoming(node, link_type=LinkType.CREATE, link_label='retrieved')

        for cls in [ArithmeticAddParser, SimpleArithmeticAddParser, ReportArithmeticAddParser]:
            result, calcfunction = cls.parse_from_node(node)

            assert isinstance(result['sum'], orm.Int)
            assert result['sum'].value == summed
            assert isinstance(calcfunction, orm.CalcFunctionNode)
            assert calcfunction.exit_status == 0

        # Verify that the `retrieved_temporary_folder` keyword can be passed, there is no validation though
        result, calcfunction = ArithmeticAddParser.parse_from_node(node, retrieved_temporary_folder='/some/path')

    @pytest.mark.requires_rmq
    def test_parse_from_node_output_validation(self):
        """Test that the ``parse_from_node`` properly validates attached outputs.

        The calculation node represents the parsing process.
        """
        output_filename = 'aiida.out'

        # Mock the `CalcJobNode` which should have the `retrieved` folder containing the sum in the outputfile file
        # This is the value that should be parsed into the `sum` output node
        node = orm.CalcJobNode(computer=self.computer, process_type=ArithmeticAddCalculation.build_process_type())
        node.set_option('resources', {'num_machines': 1, 'num_mpiprocs_per_machine': 1})
        node.set_option('max_wallclock_seconds', 1800)
        node.set_option('output_filename', output_filename)
        node.store()

        retrieved = orm.FolderData()
        retrieved.base.repository.put_object_from_filelike(io.StringIO('1'), output_filename)
        retrieved.store()
        retrieved.base.links.add_incoming(node, link_type=LinkType.CREATE, link_label='retrieved')

        with pytest.raises(ValueError, match=r'Error validating output .* for port .*: Unexpected ports .*'):
            BrokenArithmeticAddParser.parse_from_node(node)
