# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""
This module implements a generic output plugin, that is general enough
to allow the reading of the outputs of a calculation.
"""


class Parser(object):
    """
    Base class for a parser object.

    Receives a Calculation object. This should be in the PARSING state.
    Raises ValueError otherwise
    Looks for the attached parser_opts or input_settings nodes attached to the calculation.
    Get the child Folderdata, parse it and store the parsed data.
    """
    _linkname_outparams = 'output_parameters'
    _retrieved_temporary_folder_key = 'retrieved_temporary_folder'

    def __init__(self, calc):
        from aiida.common import aiidalogger

        self._logger = aiidalogger.getChild('parser').getChild( self.__class__.__name__)
        self._calc = calc

    @property
    def logger(self):
        """
        Return the logger, also with automatic extras of the associated
        extras of the calculation
        """
        import logging
        from aiida.common.log import get_dblogger_extra

        return logging.LoggerAdapter(logger=self._logger, extra=get_dblogger_extra(self._calc))

    @property
    def retrieved_temporary_folder_key(self):
        """
        Return the key under which the retrieved_temporary_folder will be passed in the
        dictionary of retrieved nodes in the parse_with_retrieved method
        """
        return self._retrieved_temporary_folder_key

    def parse_with_retrieved(self, retrieved):
        """
        Receives in input a dictionary of retrieved nodes.
        Implement all the logic in this function of the subclass.

        :param retrieved: dictionary of retrieved nodes
        """
        raise NotImplementedError

    def parse_from_calc(self, retrieved_temporary_folder=None):
        """
        Parses the datafolder, stores results.
        Main functionality of the class. If you only have one retrieved node,
        you do not need to reimplement this. Implement only the
        parse_with_retrieved
        """
        # select the folder object
        out_folder = self._calc.get_retrieved_node()
        if out_folder is None:
            self.logger.error("No retrieved folder found")
            return False, ()

        retrieved = {self._calc._get_linkname_retrieved(): out_folder}

        if retrieved_temporary_folder is not None:
            key = self.retrieved_temporary_folder_key
            retrieved[key] = retrieved_temporary_folder

        return self.parse_with_retrieved(retrieved)

    @classmethod
    def get_linkname_outparams(self):
        """
        The name of the link used for the output parameters
        """
        return self._linkname_outparams

    def get_result_dict(self):
        """
        Return a dictionary with all results (faster than doing multiple queries)

        :note: the function returns an empty dictionary if no output params node
          can be found (either because the parser did not create it, or because
          the calculation has not been parsed yet).
        """
        from aiida.common.exceptions import NotExistent

        try:
            resnode = self.get_result_parameterdata_node()
        except NotExistent:
            return {}

        return resnode.get_dict()

    def get_result_parameterdata_node(self):
        """
        Return the parameterdata node.

        :raise UniquenessError: if the node is not unique
        :raise NotExistent: if the node does not exist
        """
        from aiida.orm.data.parameter import ParameterData
        from aiida.common.exceptions import NotExistent

        out_parameters = self._calc.get_outputs(node_type=ParameterData, also_labels=True)
        out_parameter_data = [i[1] for i in out_parameters if i[0] == self.get_linkname_outparams()]

        if not out_parameter_data:
            raise NotExistent("No output .res ParameterData node found")
        elif len(out_parameter_data) > 1:
            from aiida.common.exceptions import UniquenessError

            raise UniquenessError("Output ParameterData should be found once, "
                                  "found it instead {} times"
                                  .format(len(out_parameter_data)))

        return out_parameter_data[0]

    def get_result_keys(self):
        """
        Return an iterator of list of strings of valid result keys,
        that can be then passed to the get_result() method.

        :note: the function returns an empty list if no output params node
          can be found (either because the parser did not create it, or because
          the calculation has not been parsed yet).

        :raise UniquenessError: if more than one output node with the name
          self._get_linkname_outparams() is found.
        """
        from aiida.common.exceptions import NotExistent

        try:
            resnode = self.get_result_parameterdata_node()
        except NotExistent:
            return iter([])

        return resnode.keys()

    def get_result(self, key_name):
        """
        Access the parameters of the output.
        The following method will should work for a generic parser,
        provided it has to query only one ParameterData object.
        """
        resnode = self.get_result_parameterdata_node()

        try:
            value = resnode.get_attr(key_name)
        except KeyError:
            from aiida.common.exceptions import ContentNotExistent

            raise ContentNotExistent("Key {} not found in results".format(key_name))

        # TODO: eventually, here insert further operations
        # (ex: key_name = energy_float_rydberg could return only the last element of a list,
        # and convert in the right units)

        return value
