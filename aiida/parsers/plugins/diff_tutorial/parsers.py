# -*- coding: utf-8 -*-
"""
Parsers for DiffCalculation of plugin tutorial.

Register parsers via the "aiida.parsers" entry point in the pyproject.toml file.
"""
# START PARSER HEAD
from aiida.engine import ExitCode
from aiida.orm import SinglefileData
from aiida.parsers.parser import Parser
from aiida.plugins import CalculationFactory

DiffCalculation = CalculationFactory('diff-tutorial')


class DiffParser(Parser):
    # END PARSER HEAD
    """
    Parser class for DiffCalculation.
    """

    def parse(self, **kwargs):
        """
        Parse outputs, store results in database.

        :returns: non-zero exit code, if parsing fails
        """

        output_filename = self.node.get_option('output_filename')

        # Check that folder content is as expected
        files_retrieved = self.retrieved.list_object_names()
        files_expected = [output_filename]
        # Note: set(A) <= set(B) checks whether A is a subset of B
        if not set(files_expected) <= set(files_retrieved):
            self.logger.error(f"Found files '{files_retrieved}', expected to find '{files_expected}'")
            return self.exit_codes.ERROR_MISSING_OUTPUT_FILES

        # add output file
        self.logger.info(f"Parsing '{output_filename}'")
        with self.retrieved.open(output_filename, 'rb') as handle:
            output_node = SinglefileData(file=handle)
        self.out('diff', output_node)

        return ExitCode(0)


class DiffParserSimple(Parser):
    """
    Simple Parser class for DiffCalculation.
    """

    def parse(self, **kwargs):
        """
        Parse outputs, store results in database.
        """

        output_filename = self.node.get_option('output_filename')

        # add output file
        self.logger.info(f"Parsing '{output_filename}'")
        with self.retrieved.open(output_filename, 'rb') as handle:
            output_node = SinglefileData(file=handle)
        self.out('diff', output_node)

        return ExitCode(0)
