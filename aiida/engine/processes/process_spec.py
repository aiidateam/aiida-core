# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""AiiDA specific implementation of plumpy's ProcessSpec."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import six
import plumpy

from .exit_code import ExitCode, ExitCodesNamespace
from .ports import InputPort, PortNamespace, CalcJobOutputPort


class ProcessSpec(plumpy.ProcessSpec):
    """Default process spec for process classes defined in `aiida-core`.

    This sub class defines custom classes for input ports and port namespaces. It also adds support for the definition
    of exit codes and retrieving them subsequently.
    """

    METADATA_KEY = 'metadata'
    METADATA_OPTIONS_KEY = 'options'
    INPUT_PORT_TYPE = InputPort
    PORT_NAMESPACE_TYPE = PortNamespace

    def __init__(self):
        super(ProcessSpec, self).__init__()
        self._exit_codes = ExitCodesNamespace()

    @property
    def metadata_key(self):
        return self.METADATA_KEY

    @property
    def options_key(self):
        return self.METADATA_OPTIONS_KEY

    @property
    def exit_codes(self):
        """
        Return the namespace of exit codes defined for this ProcessSpec

        :returns: ExitCodesNamespace of ExitCode named tuples
        """
        return self._exit_codes

    def exit_code(self, status, label, message):
        """
        Add an exit code to the ProcessSpec

        :param status: the exit status integer
        :param label: a label by which the exit code can be addressed
        :param message: a more detailed description of the exit code
        """
        if not isinstance(status, int):
            raise TypeError('status should be of integer type and not of {}'.format(type(status)))

        if status < 0:
            raise ValueError('status should be a positive integer, received {}'.format(type(status)))

        if not isinstance(label, six.string_types):
            raise TypeError('label should be of basestring type and not of {}'.format(type(label)))

        if not isinstance(message, six.string_types):
            raise TypeError('message should be of basestring type and not of {}'.format(type(message)))

        self._exit_codes[label] = ExitCode(status, message)


class CalcJobProcessSpec(ProcessSpec):
    """Process spec intended for the `CalcJob` process class."""

    OUTPUT_PORT_TYPE = CalcJobOutputPort

    def __init__(self):
        super(CalcJobProcessSpec, self).__init__()
        self._default_output_node = None

    @property
    def default_output_node(self):
        return self._default_output_node

    @default_output_node.setter
    def default_output_node(self, port_name):
        from aiida.orm import Dict

        if port_name not in self.outputs:
            raise ValueError('{} is not a registered output port'.format(port_name))

        valid_type_port = self.outputs[port_name].valid_type
        valid_type_required = Dict

        if valid_type_port is not valid_type_required:
            raise ValueError('the valid type of a default output has to be a {} but it is {}'.format(
                valid_type_port, valid_type_required))

        self._default_output_node = port_name
