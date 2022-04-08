# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Utilities for `WorkChain` implementations."""
from functools import partial
from inspect import getfullargspec
from types import FunctionType  # pylint: disable=no-name-in-module
from typing import List, NamedTuple, Optional, Union

from wrapt import decorator

from ..exit_code import ExitCode

__all__ = ('ProcessHandlerReport', 'process_handler')


class ProcessHandlerReport(NamedTuple):
    """A namedtuple to define a process handler report for a :class:`aiida.engine.BaseRestartWorkChain`.

    This namedtuple should be returned by a process handler of a work chain instance if the condition of the handler was
    met by the completed process. If no further handling should be performed after this method the `do_break` field
    should be set to `True`.
    If the handler encountered a fatal error and the work chain needs to be terminated, an `ExitCode` with
    non-zero exit status can be set. This exit code is what will be set on the work chain itself. This works because the
    value of the `exit_code` field returned by the handler, will in turn be returned by the `inspect_process` step and
    returning a non-zero exit code from any work chain step will instruct the engine to abort the work chain.

    :param do_break: boolean, set to `True` if no further process handlers should be called, default is `False`
    :param exit_code: an instance of the :class:`~aiida.engine.processes.exit_code.ExitCode` tuple.
        If not explicitly set, the default `ExitCode` will be instantiated,
        which has status `0` meaning that the work chain step will be considered
        successful and the work chain will continue to the next step.
    """
    do_break: bool = False
    exit_code: ExitCode = ExitCode()


def process_handler(
    wrapped: Optional[FunctionType] = None,
    *,
    priority: int = 0,
    exit_codes: Union[None, ExitCode, List[ExitCode]] = None,
    enabled: bool = True
) -> FunctionType:
    """Decorator to register a :class:`~aiida.engine.BaseRestartWorkChain` instance method as a process handler.

    The decorator will validate the `priority` and `exit_codes` optional keyword arguments and then add itself as an
    attribute to the `wrapped` instance method. This is used in the `inspect_process` to return all instance methods of
    the class that have been decorated by this function and therefore are considered to be process handlers.

    Requirements on the function signature of process handling functions. The function to which the decorator is applied
    needs to take two arguments:

        * `self`: This is the instance of the work chain itself
        * `node`: This is the process node that finished and is to be investigated

    The function body typically consists of a conditional that will check for a particular problem that might have
    occurred for the sub process. If a particular problem is handled, the process handler should return an instance of
    the :class:`aiida.engine.ProcessHandlerReport` tuple. If no other process handlers should be considered, the set
    `do_break` attribute should be set to `True`. If the work chain is to be aborted entirely, the `exit_code` of the
    report can be set to an `ExitCode` instance with a non-zero status.

    :param wrapped: the work chain method to register the process handler with
    :param priority: optional integer that defines the order in which registered handlers will be called during the
        handling of a finished process. Higher priorities will be handled first. Default value is `0`. Multiple handlers
        with the same priority is allowed, but the order of those is not well defined.
    :param exit_codes: single or list of `ExitCode` instances. If defined, the handler will return `None` if the exit
        code set on the `node` does not appear in the `exit_codes`. This is useful to have a handler called only when
        the process failed with a specific exit code.
    :param enabled: boolean, by default True, which will cause the handler to be called during `inspect_process`. When
        set to `False`, the handler will be skipped. This static value can be overridden on a per work chain instance
        basis through the input `handler_overrides`.
    """
    if wrapped is None:
        return partial(
            process_handler, priority=priority, exit_codes=exit_codes, enabled=enabled
        )  # type: ignore[return-value]

    if not isinstance(wrapped, FunctionType):
        raise TypeError('first argument can only be an instance method, use keywords for decorator arguments.')

    if not isinstance(priority, int):
        raise TypeError('the `priority` keyword should be an integer.')

    if exit_codes is not None and not isinstance(exit_codes, list):
        exit_codes = [exit_codes]

    if exit_codes and any(not isinstance(exit_code, ExitCode) for exit_code in exit_codes):
        raise TypeError('`exit_codes` keyword should be an instance of `ExitCode` or list thereof.')

    if not isinstance(enabled, bool):
        raise TypeError('the `enabled` keyword should be a boolean.')

    handler_args = getfullargspec(wrapped)[0]

    if len(handler_args) != 2:
        raise TypeError(f'process handler `{wrapped.__name__}` has invalid signature: should be (self, node)')

    wrapped.decorator = process_handler  # type: ignore[attr-defined]
    wrapped.priority = priority  # type: ignore[attr-defined]
    wrapped.enabled = enabled  # type: ignore[attr-defined]

    @decorator
    def wrapper(wrapped, instance, args, kwargs):

        # When the handler will be called by the `BaseRestartWorkChain` it will pass the node as the only argument
        node = args[0]

        if exit_codes is not None and node.exit_status not in [
            exit_code.status for exit_code in exit_codes  # type: ignore[union-attr]
        ]:
            result = None
        else:
            result = wrapped(*args, **kwargs)

        # Append the name and return value of the current process handler to the `considered_handlers` extra.
        try:
            considered_handlers = instance.node.base.extras.get(instance._considered_handlers_extra, [])  # pylint: disable=protected-access
            current_process = considered_handlers[-1]
        except IndexError:
            # The extra was never initialized, so we skip this functionality
            pass
        else:
            # Append the name of the handler to the last list in `considered_handlers` and save it
            serialized = result
            if isinstance(serialized, ProcessHandlerReport):
                serialized = {'do_break': serialized.do_break, 'exit_status': serialized.exit_code.status}
            current_process.append((wrapped.__name__, serialized))
            instance.node.base.extras.set(instance._considered_handlers_extra, considered_handlers)  # pylint: disable=protected-access

        return result

    return wrapper(wrapped)  # pylint: disable=no-value-for-parameter
