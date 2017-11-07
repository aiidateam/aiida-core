# -*- coding: utf-8 -*-
from aiida.orm import CalculationFactory
from aiida.parsers.parser import Parser

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

        return True, ()