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
from __future__ import absolute_import

import six
import plumpy

from aiida.work.exit_code import ExitCode, ExitCodesNamespace
from aiida.work.ports import InputPort, PortNamespace


class ProcessSpec(plumpy.ProcessSpec):
    """
    Sub classes plumpy.ProcessSpec to define the INPUT_PORT_TYPE and PORT_NAMESPACE_TYPE
    with the variants implemented in AiiDA
    """

    INPUT_PORT_TYPE = InputPort
    PORT_NAMESPACE_TYPE = PortNamespace

    def __init__(self):
        super(ProcessSpec, self).__init__()
        self._exit_codes = ExitCodesNamespace()

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
