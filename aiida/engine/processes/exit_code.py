# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""A namedtuple and namespace for ExitCodes that can be used to exit from Processes."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from collections import namedtuple

from aiida.common.extendeddicts import AttributeDict

__all__ = ('ExitCode', 'ExitCodesNamespace')

ExitCode = namedtuple('ExitCode', 'status message')
ExitCode.__new__.__defaults__ = (0, None)
"""
A namedtuple to define an exit code for a :class:`~aiida.engine.processes.process.Process`.

When this namedtuple is returned from a Process._run() call, it will be interpreted that the Process
should be terminated and that the exit status and message of the namedtuple should be set to the
corresponding attributes of the node.

:param status: positive integer exit status, where a non-zero value indicated the process failed, default is `0`
:param message: string, optional message with more details about the failure mode
"""


class ExitCodesNamespace(AttributeDict):
    """
    A namespace of ExitCode tuples that can be accessed through getattr as well as getitem.
    Additionally, the collection can be called with an identifier, that can either reference
    the integer `status` of the ExitCode that needs to be retrieved or the key in the collection
    """

    def __call__(self, identifier):
        """
        Return a specific exit code identified by either its exit status or label

        :param identifier: the identifier of the exit code. If the type is integer, it will be interpreted as
            the exit code status, otherwise it be interpreted as the exit code label
        :returns: an ExitCode named tuple
        :raises ValueError: if no exit code with the given label is defined for this process
        """
        if isinstance(identifier, int):
            for exit_code in self.values():
                if exit_code.status == identifier:
                    return exit_code

            raise ValueError('the exit code status {} does not correspond to a valid exit code')
        else:
            try:
                exit_code = self[identifier]
            except KeyError:
                raise ValueError('the exit code label {} does not correspond to a valid exit code')
            else:
                return exit_code
