# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import io
import os

from aiida.common import exceptions
from aiida.orm import Dict
from aiida.parsers.parser import Parser
from aiida.plugins import CalculationFactory

TemplatereplacerCalculation = CalculationFactory('templatereplacer')


class TemplatereplacerDoublerParser(Parser):

    def parse(self, **kwargs):
        """Parse the contents of the output files retrieved in the `FolderData`."""
        template = self.node.inputs.template.get_dict()

        try:
            output_folder = self.retrieved
        except exceptions.NotExistent:
            return self.exit_codes.ERROR_NO_RETRIEVED_FOLDER

        try:
            output_file = template['output_file_name']
        except KeyError:
            return self.exit_codes.ERROR_NO_OUTPUT_FILE_NAME_DEFINED

        try:
            with output_folder.open(output_file, 'r') as handle:
                result = self.parse_stdout(handle)
        except (OSError, IOError):
            self.logger.exception('unable to parse the output for CalcJobNode<{}>'.format(self.node.pk))
            return self.exit_codes.ERROR_READING_OUTPUT_FILE

        output_dict = {'value': result, 'retrieved_temporary_files': []}
        retrieve_temporary_files = template.get('retrieve_temporary_files', None)

        # If the 'retrieve_temporary_files' key was set in the template input node, we expect a temporary directory
        # to have been passed in the keyword arguments under the name `retrieved_temporary_folder`.
        if retrieve_temporary_files is not None:
            try:
                retrieved_temporary_folder = kwargs['retrieved_temporary_folder']
            except KeyError:
                return self.exit_codes.ERROR_NO_TEMPORARY_RETRIEVED_FOLDER

            for retrieved_file in retrieve_temporary_files:

                file_path = os.path.join(retrieved_temporary_folder, retrieved_file)

                if not os.path.isfile(file_path):
                    self.logger.error('the file {} was not found in the temporary retrieved folder {}'.format(
                        retrieved_file, retrieved_temporary_folder))
                    return self.exit_codes.ERROR_READING_TEMPORARY_RETRIEVED_FILE

                with io.open(file_path, 'r', encoding='utf8') as handle:
                    parsed_value = handle.read().strip()

                # We always strip the content of the file from whitespace to simplify testing for expected output
                output_dict['retrieved_temporary_files'].append((retrieved_file, parsed_value))

        self.out(self.node.process_class.spec().default_output_node, Dict(dict=output_dict))

        return

    @staticmethod
    def parse_stdout(filelike):
        """
        Parse the sum from the output of the ArithmeticAddcalculation written to standard out

        :param filelike: filelike object containing the output
        :returns: the sum
        """
        try:
            result = int(filelike.read())
        except ValueError:
            result = None

        return result
