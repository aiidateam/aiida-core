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
from __future__ import absolute_import
import logging
from aiida.common.exceptions import NotExistent
from aiida.common.log import aiidalogger, get_dblogger_extra


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
        self._logger = aiidalogger.getChild('parser').getChild( self.__class__.__name__)
        self._calc = calc

    @property
    def logger(self):
        """
        Return the logger, also with automatic extras of the associated
        extras of the calculation
        """
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
        This function should be implemented in the Parser subclass and should parse the desired
        output from the retrieved nodes in the 'retrieved' input dictionary. It should return a
        tuple of an integer and a list of tuples. The integer serves as an exit code to indicate
        the successfulness of the parsing, where 0 means success and any non-zero integer indicates
        a failure. These integer codes can be chosen by the plugin developer. The list of tuples
        are the parsed nodes that need to be stored as ouput nodes of the calculation. The first key
        should be the link name and the second key the output node itself.

        :param retrieved: dictionary of retrieved nodes
        :returns: exit code, list of tuples ('link_name', output_node)
        :rtype: int, [(basestring, aiida.orm.data.Data)]
        """
        raise NotImplementedError

    def parse_from_calc(self, retrieved_temporary_folder=None):
        """
        Parse the contents of the retrieved folder data node and return a tuple of to be stored
        output data nodes. If you only have one retrieved node, the default folder data node, this
        function does not have to be reimplemented in a plugin, only the parse_with_retrieved method.

        :param retrieved_temporary_folder: optional absolute path to directory with temporary retrieved files
        :returns: exit code, list of tuples ('link_name', output_node)
        :rtype: int, [(basestring, aiida.orm.data.Data)]
        """
        out_folder = self._calc.get_retrieved_node()
        if out_folder is None:
            self.logger.error('No retrieved folder found')
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

        out_parameters = self._calc.get_outputs(node_type=ParameterData, also_labels=True)
        out_parameter_data = [i[1] for i in out_parameters if i[0] == self.get_linkname_outparams()]

        if not out_parameter_data:
            raise NotExistent('No output .res ParameterData node found')

        elif len(out_parameter_data) > 1:
            from aiida.common.exceptions import UniquenessError

            raise UniquenessError(
                'Output ParameterData should be found once, found it instead {} times'
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
        try:
            node = self.get_result_parameterdata_node()
        except NotExistent:
            return iter([])

        return node.keys()

    def get_result(self, key_name):
        """
        Access the parameters of the output.
        The following method will should work for a generic parser,
        provided it has to query only one ParameterData object.
        """
        node = self.get_result_parameterdata_node()

        try:
            value = node.get_attr(key_name)
        except KeyError:
            from aiida.common.exceptions import ContentNotExistent

            raise ContentNotExistent("Key {} not found in results".format(key_name))

        return value
