# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from aiida.orm import CalculationFactory
from aiida.parsers.parser import Parser
from aiida.orm.data.parameter import ParameterData

TemplatereplacerCalculation = CalculationFactory('simpleplugins.templatereplacer')

class TemplatereplacerDoublerParser(Parser):

    def __init__(self, calc):
        """
        Initialize the Parser for a TemplatereplacerCalculation

        :param calculation: instance of the TemplatereplacerCalculation
        """
        if not isinstance(calc, TemplatereplacerCalculation):
            raise ValueError('Input calculation must be of type {}'.format(type(TemplatereplacerCalculation)))

        super(TemplatereplacerDoublerParser, self).__init__(calc)

    def parse_with_retrieved(self, retrieved):
        """
        Parse the output nodes for a PwCalculations from a dictionary of retrieved nodes.
        Two nodes that are expected are the default 'retrieved' FolderData node which will
        store the retrieved files permanently in the repository. The second required node
        is the unstored FolderData node with the temporary retrieved files, which should
        be passed under the key 'retrieved_temporary_folder_key' of the Parser class.

        :param retrieved: a dictionary of retrieved nodes
        """
        output_nodes = []

        try:
            output_file = self._calc.inp.template.get_dict()['output_file_name']
        except KeyError:
            self.logger.error("the output file name 'output_file_name' was not specified in the 'template' input node")
            return False, ()

        retrieved_folder = retrieved[self._calc._get_linkname_retrieved()]
        try:
            parsed_value = int(retrieved_folder.get_file_content(output_file).strip())
        except (AttributeError, IOError, ValueError) as e:
            self.logger.error("* UNABLE TO RETRIEVE VALUE for calc pk={}: I got {}: {}".format(self._calc.pk, type(e), e))
            return False, ()

        output_dict = {
            'value': parsed_value,
            'retrieved_temporary_files': []
        }

        try:
            retrieve_temporary_files = self._calc.inp.template.get_dict()['retrieve_temporary_files']
        except KeyError:
            retrieve_temporary_files = None

        # If the 'retrieve_temporary_files' key was set in the template input node, we expect a temporary
        # FolderData node in the 'retrieved' arguments
        if retrieve_temporary_files is not None:
            try:
                temporary_folder = retrieved[self.retrieved_temporary_folder_key]
            except KeyError:
                self.logger.error('the {} was not passed as an argument'.format(self.retrieved_temporary_folder_key))
                return False, ()

            for retrieved_file in retrieve_temporary_files:
                if retrieved_file not in temporary_folder.get_folder_list():
                    self.logger.error('the file {} was not found in the temporary retrieved folder'.format(retrieved_file))
                    return False, ()

                # We always strip the content of the file from whitespace to simplify testing for expected output
                output_dict['retrieved_temporary_files'].append((retrieved_file, temporary_folder.get_file_content(retrieved_file).strip()))

        output_parameters = ParameterData(dict=output_dict)
        output_nodes.append((self.get_linkname_outparams(), output_parameters))

        return True, output_nodes