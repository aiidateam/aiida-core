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
from collections import namedtuple
from functools import wraps

from ..exit_code import ExitCode

__all__ = ('ProcessHandler', 'ProcessHandlerReport', 'register_process_handler')

ProcessHandler = namedtuple('ProcessHandler', 'method priority exit_codes')
ProcessHandler.__new__.__defaults__ = (None, 0, None)
"""A namedtuple to define a process handler for a :class:`aiida.engine.BaseRestartWorkChain`.

The `method` element refers to a function decorated by the `register_process_handler` that has turned it into a bound
method of the target `WorkChain` class. The method takes an instance of a :class:`~aiida.orm.ProcessNode` as its sole
argument. The method can return an optional `ProcessHandlerReport` to signal whether other handlers still need to be
considered or whether the work chain should be terminated immediately. The priority determines in which order the
handler methods are executed, with the higher priority being executed first.

:param method: the decorated process handling function turned into a bound work chain class method
:param priority: integer denoting the process handler's priority
:param exit_codes: single or list of `ExitCode` instances. A handler that defines this should only be called for a given
    completed process if its exit status is a member of `exit_codes`.
"""

ProcessHandlerReport = namedtuple('ProcessHandlerReport', 'do_break exit_code')
ProcessHandlerReport.__new__.__defaults__ = (False, ExitCode())
"""A namedtuple to define a process handler report for a :class:`aiida.engine.BaseRestartWorkChain`.

This namedtuple should be returned by a process handler of a work chain instance if the condition of the handler was
met by the completed process. If no further handling should be performed after this method the `do_break` field should
be set to `True`. If the handler encountered a fatal error and the work chain needs to be terminated, an `ExitCode` with
non-zero exit status can be set. This exit code is what will be set on the work chain itself. This works because the
value of the `exit_code` field returned by the handler, will in turn be returned by the `inspect_process` step and
returning a non-zero exit code from any work chain step will instruct the engine to abort the work chain.

:param do_break: boolean, set to `True` if no further process handlers should be called, default is `False`
:param exit_code: an instance of the :class:`~aiida.engine.processes.exit_code.ExitCode` tuple. If not explicitly set,
    the default `ExitCode` will be instantiated which has status `0` meaning that the work chain step will be considered
    successful and the work chain will continue to the next step.
"""


def register_process_handler(cls, *, priority=None, exit_codes=None):
    """Decorator to register a function as a handler for a :class:`~aiida.engine.BaseRestartWorkChain`.

    The function expects two arguments, a work chain class and a priortity. The decorator will add the function as a
    class method to the work chain class and add an :class:`~aiida.engine.ProcessHandler` tuple to the `__handlers`
    private attribute of the work chain. During the `inspect_process` outline method, the work chain will retrieve all
    the registered handlers through the :meth:`~aiida.engine.BaseRestartWorkChain._handlers` property and loop over them
    sorted with respect to their priority in reverse. If the work chain class defines the
    :attr:`~aiida.engine.BaseRestartWorkChain._verbose` attribute and is set to `True`, a report message will be fired
    when the process handler is executed.

    Requirements on the function signature of process handling functions. The function to which the decorator is applied
    needs to take two arguments:

        * `self`: This is the instance of the work chain itself
        * `node`: This is the process node that finished and is to be investigated

    The function body typically consists of a conditional that will check for a particular problem that might have
    occurred for the sub process. If a particular problem is handled, the process handler should return an instance of
    the :class:`aiida.engine.ProcessHandlerReport` tuple. If no other process handlers should be considered, the set
    `do_break` attribute should be set to `True`. If the work chain is to be aborted entirely, the `exit_code` of the
    report can be set to an `ExitCode` instance with a non-zero status.

    :param cls: the work chain class to register the process handler with
    :param priority: optional integer that defines the order in which registered handlers will be called during the
        handling of a finished process. Higher priorities will be handled first.
    :param exit_codes: single or list of `ExitCode` instances. If defined, the handler will return `None` if the exit
        code set on the `node` does not appear in the `exit_codes`. This is useful to have a handler called only when
        the process failed with a specific exit code.
    """
    if priority is None:
        priority = 0

    if not isinstance(priority, int):
        raise TypeError('the `priority` should be an integer.')

    if exit_codes is not None and not isinstance(exit_codes, list):
        exit_codes = [exit_codes]

    if exit_codes and any([not isinstance(exit_code, ExitCode) for exit_code in exit_codes]):
        raise TypeError('`exit_codes` should be an instance of `ExitCode` or list thereof.')

    def process_handler_decorator(handler):
        """Decorate a function to dynamically register a handler to a `WorkChain` class."""

        @wraps(handler)
        def process_handler(self, node):
            """Wrap handler to add a log to the report if the handler is called and verbosity is turned on."""
            verbose = hasattr(cls, '_verbose') and cls._verbose  # pylint: disable=protected-access

            if exit_codes and node.exit_status not in [exit_code.status for exit_code in exit_codes]:
                if verbose:
                    self.report('skipped {} because of exit code filter'.format(handler.__name__))
                return None

            if verbose:
                self.report('({}){}'.format(priority, handler.__name__))

            result = handler(self, node)

            # If a handler report is returned, attach the handler's name to node's attributes
            if isinstance(result, ProcessHandlerReport):
                try:
                    called_process_handlers = self.node.get_extra('called_process_handlers', [])
                    current_process = called_process_handlers[-1]
                except IndexError:
                    # The extra was never initialized, so we skip this functionality
                    pass
                else:
                    # Append the name of the handler to the last list in `called_process_handlers` and save it
                    current_process.append(handler.__name__)
                    self.node.set_extra('called_process_handlers', called_process_handlers)

            return result

        cls.register_handler(handler.__name__, ProcessHandler(process_handler, priority, exit_codes))

        return process_handler

    return process_handler_decorator
