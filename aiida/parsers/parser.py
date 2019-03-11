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
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from aiida.common import exceptions
from aiida.common import extendeddicts
from aiida.engine import calcfunction

__all__ = ('Parser',)


class Parser(object):  # pylint: disable=useless-object-inheritance
    """Base class for a Parser that can parse the outputs produced by a CalcJob process."""

    def __init__(self, node):
        """Construct the Parser instance.

        :param node: the `CalcJobNode` that contains the results of the executed `CalcJob` process.
        """
        from aiida.common.log import AIIDA_LOGGER
        from aiida.orm.utils.log import create_logger_adapter

        self._logger = create_logger_adapter(AIIDA_LOGGER.getChild('parser').getChild(self.__class__.__name__), node)
        self._node = node
        self._outputs = extendeddicts.AttributeDict()

    @property
    def logger(self):
        """Return the logger preconfigured for the calculation node associated with this parser instance.

        :return: `logging.Logger`
        """
        return self._logger

    @property
    def node(self):
        """Return the node instance

        :return: the `CalcJobNode` instance
        """
        return self._node

    @property
    def exit_codes(self):
        """Return the exit codes defined for the process class of the node being parsed.

        :returns: ExitCodesNamespace of ExitCode named tuples
        """
        return self.node.process_class.exit_codes

    @property
    def retrieved(self):
        return self.node.get_outgoing().get_node_by_label(self.node.process_class.link_label_retrieved)

    @property
    def outputs(self):
        """Return the dictionary of outputs that have been registered.

        :return: an AttributeDict instance with the registered output nodes
        """
        return self._outputs

    def out(self, link_label, node):
        """Register a node as an output with the given link label.

        :param link_label: the name of the link label
        :param node: the node to register as an output
        :raises aiida.common.ModificationNotAllowed: if an output node was already registered with the same link label
        """
        if link_label in self._outputs:
            raise exceptions.ModificationNotAllowed('the output {} already exists'.format(link_label))
        self._outputs[link_label] = node

    def get_outputs_for_parsing(self):
        """Return the dictionary of nodes that should be passed to the `Parser.parse` call.

        Output nodes can be marked as being required by the `parse` method, by setting the `pass_to_parser` attribute,
        in the `spec.output` call in the process spec of the `CalcJob`, to True.

        :return: dictionary of nodes that are required by the `parse` method
        """
        link_triples = self.node.get_outgoing()
        result = {}

        for label, port in self.node.process_class.spec().outputs.items():
            if port.pass_to_parser:
                try:
                    result[label] = link_triples.get_node_by_label(label)
                except exceptions.NotExistent:
                    if port.required:
                        raise

        return result

    @classmethod
    def parse_from_node(cls, node, store_provenance=True):
        """Parse the outputs directly from the `CalcJobNode`.

        If `store_provenance` is set to False, a `CalcFunctionNode` will still be generated, but it will not be stored.
        It's storing method will also be disabled, making it impossible to store, because storing it afterwards would
        not have the expected effect, as the outputs it produced will not be stored with it.

        :param node: a `CalcJobNode` instance
        :param store_provenance: bool, if True will store the parsing as a `CalcFunctionNode` in the provenance
        :return: a tuple of the parsed results and the `CalcFunctionNode`
        """
        parser = cls(node=node)

        @calcfunction
        def parse_calcfunction(**kwargs):
            """A wrapper function that will turn calling the `Parser.parse` method into a `CalcFunctionNode`.

            :param kwargs: keyword arguments that are passed to `Parser.parse` after it has been constructed
            """
            exit_code = parser.parse(**kwargs)
            outputs = parser.outputs

            if exit_code and exit_code.status:
                return exit_code

            return dict(outputs)

        inputs = {'metadata': {'store_provenance': store_provenance}}
        inputs.update(parser.get_outputs_for_parsing())

        return parse_calcfunction.run_get_node(**inputs)

    def parse(self, **kwargs):
        """Parse the contents of the output files retrieved in the `FolderData`.

        This method should be implemented in the sub class. Outputs can be registered through the `out` method.
        After the `parse` call finishes, the runner will automatically link them up to the underlying `CalcJobNode`.

        :param kwargs: output nodes attached to the `CalcJobNode` of the parser instance.
        :return: an instance of ExitCode or None
        """
        raise NotImplementedError
