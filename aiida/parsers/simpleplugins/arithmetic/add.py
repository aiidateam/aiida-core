# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from __future__ import absolute_import
from aiida.orm import CalculationFactory
from aiida.parsers.parser import Parser
from aiida.orm.data.int import Int
from aiida.orm.data.parameter import ParameterData


ArithmeticAddCalculation = CalculationFactory('simpleplugins.arithmetic.add')


class ArithmeticAddParser(Parser):

    _linkname_output = 'sum'

    def __init__(self, calculation):
        """
        Initialize the Parser for an ArithmeticAddCalculation

        :param calculation: instance of the ArithmeticAddCalculation
        """
        if not isinstance(calculation, ArithmeticAddCalculation):
            raise ValueError('Input calculation must be of type {}'.format(type(ArithmeticAddCalculation)))

        self.calculation = calculation

        super(ArithmeticAddParser, self).__init__(calculation)

    @classmethod
    def get_linkname_output(self):
        """
        The name of the link used for the output node
        """
        return self._linkname_output

    def parse_with_retrieved(self, retrieved):
        """
        Parse the contents of the output file

        :param retrieved: a dictionary of retrieved nodes
        """
        is_success = True
        output_nodes = []

        try:
            output_folder = retrieved[self.calculation._get_linkname_retrieved()]
        except KeyError:
            self.logger.error("no retrieved folder found")
            return False, ()

        # Verify the standard output file is present, parse the value and attach as output node
        try:
            filepath_stdout = output_folder.get_abs_path(self.calculation._OUTPUT_FILE_NAME)
        except OSError as exception:
            self.logger.error("expected output file '{}' was not found".format(filepath_stdout))
            return False, ()

        is_success, output_node = self.parse_stdout(filepath_stdout)

        if not is_success:
            self.logger.error('failed to parse the result from the output file {}'.format(filepath_stdout))
            return False, ()

        output_nodes.append((self.get_linkname_output(), output_node))

        return 0, output_nodes

    def parse_stdout(self, filepath):
        """
        Parse the sum from the output of the ArithmeticAddcalculation written to standard out

        :param filepath: path to file containing output written to stdout
        :returns: boolean representing success status of parsing, True equals parsing was successful
        :returns: the sum as a node
        """
        is_successful = True

        try:
            with open(filepath, 'r') as handle:
                output = handle.read()
        except IOError:
            return False, None

        try:
            result = int(output)
        except ValueError:
            return False, None

        output_node = Int(result)

        return is_successful, output_node
