# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""A namedtuple and namespace for ExitCodes that can be used to exit from Processes."""
from collections import namedtuple
from aiida.common.extendeddicts import AttributeDict

__all__ = ('ExitCode', 'ExitCodesNamespace')


class ExitCode(namedtuple('ExitCode', ['status', 'message', 'invalidates_cache'])):
    """A simple data class to define an exit code for a :class:`~aiida.engine.processes.process.Process`.

    When an instance of this clas is returned from a `Process._run()` call, it will be interpreted that the `Process`
    should be terminated and that the exit status and message of the namedtuple should be set to the corresponding
    attributes of the node.

    .. note:: this class explicitly sub-classes a namedtuple to not break backwards compatibility and to have it behave
        exactly as a tuple.

    :param status: positive integer exit status, where a non-zero value indicated the process failed, default is `0`
    :type status: int

    :param message: optional message with more details about the failure mode
    :type message: str

    :param invalidates_cache: optional flag, indicating that a process should not be used in caching
    :type invalidates_cache: bool
    """

    def format(self, **kwargs):
        """Create a clone of this exit code where the template message is replaced by the keyword arguments.

        :param kwargs: replacement parameters for the template message
        :return: `ExitCode`
        """
        try:
            message = self.message.format(**kwargs)
        except KeyError:
            template = 'insufficient or incorrect format parameters `{}` for the message template `{}`.'
            raise ValueError(template.format(kwargs, self.message))

        return ExitCode(self.status, message, self.invalidates_cache)


# Set the defaults for the `ExitCode` attributes
ExitCode.__new__.__defaults__ = (0, None, False)


class ExitCodesNamespace(AttributeDict):
    """A namespace of `ExitCode` instances that can be accessed through getattr as well as getitem.

    Additionally, the collection can be called with an identifier, that can either reference the integer `status` of the
    `ExitCode` that needs to be retrieved or the key in the collection.
    """

    def __call__(self, identifier):
        """Return a specific exit code identified by either its exit status or label.

        :param identifier: the identifier of the exit code. If the type is integer, it will be interpreted as the exit
            code status, otherwise it be interpreted as the exit code label
        :type identifier: str

        :returns: an `ExitCode` instance
        :rtype: :class:`aiida.engine.ExitCode`

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
