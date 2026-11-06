###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""A namedtuple and namespace for ExitCodes that can be used to exit from Processes."""

import enum
import typing as t

from aiida.common.extendeddicts import AttributeDict

__all__ = ('ExitCode', 'ExitCodeEnum', 'ExitCodesNamespace')


class ExitCode(t.NamedTuple):
    """A simple data class to define an exit code for a :class:`~aiida.engine.processes.process.Process`.

    When an instance of this class is returned from a `Process._run()` call, it will be interpreted that the `Process`
    should be terminated and that the exit status and message of the namedtuple should be set to the corresponding
    attributes of the node.

    :param status: positive integer exit status, where a non-zero value indicated the process failed, default is `0`
    :param message: optional message with more details about the failure mode
    :param invalidates_cache: optional flag, indicating that a process should not be used in caching
    """

    status: int = 0
    message: str | None = None
    invalidates_cache: bool = False

    def format(self, **kwargs: str) -> 'ExitCode':
        """Create a clone of this exit code where the template message is replaced by the keyword arguments.

        :param kwargs: replacement parameters for the template message

        """
        if self.message is None:
            raise ValueError('message is None')
        try:
            message = self.message.format(**kwargs)
        except KeyError:
            template = 'insufficient or incorrect format parameters `{}` for the message template `{}`.'
            raise ValueError(template.format(kwargs, self.message))

        return ExitCode(self.status, message, self.invalidates_cache)


class ExitCodeEnum(enum.Enum):
    """An enum whose members must be `ExitCode` values.

    Use this as the error type of a `Result` return annotation::

        class DivisionErrors(ExitCodeEnum):
            ZERO_DENOMINATOR = ExitCode(410, 'The denominator is zero.')

    Invalid values fail when the enum class is defined, not when a task using it is registered.
    """

    def __new__(cls, *args: object) -> 'ExitCodeEnum':
        """Validate one member value at class-creation time."""
        # `Enum` unpacks tuple values into `__new__`, so an `ExitCode` arrives as three arguments.
        code: object = ExitCode(*t.cast(t.Any, args)) if len(args) != 1 else args[0]
        if not isinstance(code, ExitCode):
            msg = f'`{cls.__name__}` members must be `ExitCode` values, got `{code!r}`.'
            raise TypeError(msg)
        status, message, invalidates_cache = t.cast('tuple[object, object, object]', tuple(code))
        if isinstance(status, bool) or not isinstance(status, int) or status <= 0:
            msg = f'`{cls.__name__}` members must declare a positive exit status, got `{status!r}`.'
            raise ValueError(msg)
        if not isinstance(message, str):
            msg = f'`{cls.__name__}` members must declare a string message, got `{message!r}`.'
            raise ValueError(msg)
        if not isinstance(invalidates_cache, bool):
            msg = f'`{cls.__name__}` members must declare a boolean cache flag, got `{invalidates_cache!r}`.'
            raise ValueError(msg)
        obj = object.__new__(cls)
        obj._value_ = code
        return obj

    @property
    def exit_code(self) -> 'ExitCode':
        """Return the `ExitCode` declared by this member."""
        return self.value

    @property
    def status(self) -> int:
        """Return the exit status declared by this member."""
        return self.value.status


class ExitCodesNamespace(AttributeDict):
    """A namespace of `ExitCode` instances that can be accessed through getattr as well as getitem.

    Additionally, the collection can be called with an identifier, that can either reference the integer `status` of the
    `ExitCode` that needs to be retrieved or the key in the collection.
    """

    def __call__(self, identifier: int | str) -> ExitCode:
        """Return a specific exit code identified by either its exit status or label.

        :param identifier: the identifier of the exit code. If the type is integer, it will be interpreted as the exit
            code status, otherwise it be interpreted as the exit code label

        :returns: an `ExitCode` instance

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
