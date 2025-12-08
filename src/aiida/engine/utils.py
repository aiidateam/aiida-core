###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Utilities for the workflow engine."""

from __future__ import annotations

import asyncio
import contextlib
import inspect
import logging
from datetime import datetime
from typing import TYPE_CHECKING, Any, Awaitable, Callable, Iterator, List, Optional, Tuple, Type, Union

if TYPE_CHECKING:
    from aiida.orm import ProcessNode

    from .processes import Process, ProcessBuilder
    from .runners import Runner

__all__ = ('InterruptableFuture', 'interruptable_task', 'is_process_function')

LOGGER = logging.getLogger(__name__)
PROCESS_STATE_CHANGE_KEY = 'process|state_change|{}'
PROCESS_STATE_CHANGE_DESCRIPTION = 'The last time a process of type {}, changed state'


def prepare_inputs(inputs: dict[str, Any] | None = None, **kwargs: Any) -> dict[str, Any]:
    """Prepare inputs for launch of a process.

    This is a utility function to pre-process inputs for the process that can be specified both through keyword
    arguments as well as through the explicit ``inputs`` argument. When both are specified, a ``ValueError`` is raised.

    :param inputs: Inputs dictionary.
    :param kwargs: Inputs defined as keyword arguments.
    :raises ValueError: If both ``kwargs`` and ``inputs`` are defined.
    :returns: The dictionary of inputs for the process.
    """
    if inputs is not None and kwargs:
        raise ValueError('Cannot specify both `inputs` and `kwargs`.')

    if kwargs:
        inputs = kwargs

    return inputs or {}


def instantiate_process(
    runner: 'Runner', process: Union['Process', Type['Process'], 'ProcessBuilder'], **inputs
) -> 'Process':
    """Return an instance of the process with the given inputs. The function can deal with various types
    of the `process`:

        * Process instance: will simply return the instance
        * ProcessBuilder instance: will instantiate the Process from the class and inputs defined within it
        * Process class: will instantiate with the specified inputs

    If anything else is passed, a ValueError will be raised

    :param process: Process instance or class, CalcJobNode class or ProcessBuilder instance
    :param inputs: the inputs for the process to be instantiated with
    """
    from .processes import Process, ProcessBuilder

    if isinstance(process, Process):
        assert not inputs
        assert runner is process.runner
        return process

    if isinstance(process, ProcessBuilder):
        builder = process
        process_class = builder.process_class
        inputs.update(**builder._inputs(prune=True))
    elif is_process_function(process):
        process_class = process.process_class  # type: ignore[attr-defined]
    elif inspect.isclass(process) and issubclass(process, Process):
        process_class = process
    else:
        raise ValueError(f'invalid process {type(process)}, needs to be Process or ProcessBuilder')

    process = process_class(runner=runner, inputs=inputs)

    return process


class InterruptableFuture(asyncio.Future):
    """A future that can be interrupted by calling `interrupt`."""

    def interrupt(self, reason: Exception) -> None:
        """This method should be called to interrupt the coroutine represented by this InterruptableFuture."""
        self.set_exception(reason)

    async def with_interrupt(self, coro: Awaitable[Any]) -> Any:
        """Return result of a coroutine which will be interrupted if this future is interrupted ::

            import asyncio
            loop = asyncio.get_event_loop()

            interruptable = InterutableFuture()
            loop.call_soon(interruptable.interrupt, RuntimeError("STOP"))
            loop.run_until_complete(interruptable.with_interrupt(asyncio.sleep(2.)))
            >>> RuntimeError: STOP


        :param coro: The coroutine that can be interrupted
        :return: The result of the coroutine
        """
        task = asyncio.ensure_future(coro)
        wait_iter = asyncio.as_completed({self, task})
        result = await next(wait_iter)
        if self.done():
            raise RuntimeError(f"This interruptible future had it's result set unexpectedly to '{result}'")

        return result


def interruptable_task(
    coro: Callable[[InterruptableFuture], Awaitable[Any]], loop: Optional[asyncio.AbstractEventLoop] = None
) -> InterruptableFuture:
    """Turn the given coroutine into an interruptable task by turning it into an InterruptableFuture and returning it.

    :param coro: the coroutine that should be made interruptable with object of InterutableFuture as last paramenter
    :param loop: the event loop in which to run the coroutine, by default uses asyncio.get_event_loop()
    :return: an InterruptableFuture
    """
    loop = loop or asyncio.get_event_loop()
    future = InterruptableFuture()

    async def execute_coroutine():
        """Coroutine that wraps the original coroutine and sets it result on the future only if not already set."""
        try:
            result = await coro(future)
        except Exception as exception:
            if not future.done():
                future.set_exception(exception)
            else:
                LOGGER.warning(
                    'Interruptable future set to %s before its coro %s is done. %s',
                    future.result(),
                    coro.__name__,
                    str(exception),
                )
        else:
            # If the future has not been set elsewhere, i.e. by the interrupt call, by the time that the coroutine
            # is executed, set the future's result to the result of the coroutine
            if not future.done():
                future.set_result(result)

    loop.create_task(execute_coroutine())

    return future


def ensure_coroutine(fct: Callable[..., Any]) -> Callable[..., Awaitable[Any]]:
    """Ensure that the given function ``fct`` is a coroutine

    If the passed function is not already a coroutine, it will be made to be a coroutine

    :param fct: the function
    :returns: the coroutine
    """
    if asyncio.iscoroutinefunction(fct):
        return fct

    async def wrapper(*args, **kwargs):
        return fct(*args, **kwargs)

    return wrapper


async def exponential_backoff_retry(
    fct: Callable[..., Any],
    initial_interval: Union[int, float] = 10.0,
    max_attempts: int = 5,
    logger: Optional[logging.Logger] = None,
    ignore_exceptions: Union[None, Type[Exception], Tuple[Type[Exception], ...]] = None,
) -> Any:
    """Coroutine to call a function, recalling it with an exponential backoff in the case of an exception

    This coroutine will loop ``max_attempts`` times, calling the ``fct`` function, breaking immediately when the call
    finished without raising an exception, at which point the result will be returned. If an exception is caught, the
    function will await a ``asyncio.sleep`` with a time interval equal to the ``initial_interval`` multiplied by
    ``2 ** (N - 1)`` where ``N`` is the number of excepted calls.

    :param fct: the function to call, which will be turned into a coroutine first if it is not already
    :param initial_interval: the time to wait after the first caught exception before calling the coroutine again
    :param max_attempts: the maximum number of times to call the coroutine before re-raising the exception
    :param ignore_exceptions: exceptions to ignore, i.e. when caught do nothing and simply re-raise
    :return: result if the ``coro`` call completes within ``max_attempts`` retries without raising
    """
    if logger is None:
        logger = LOGGER

    result: Any = None
    coro = ensure_coroutine(fct)
    interval = initial_interval

    for iteration in range(max_attempts):
        try:
            result = await coro()
            break  # Finished successfully
        except Exception as exception:
            # Re-raise exceptions that should be ignored
            if ignore_exceptions is not None and isinstance(exception, ignore_exceptions):
                raise

            count = iteration + 1
            coro_name = coro.__name__

            if iteration == max_attempts - 1:
                logger.exception('iteration %d of %s excepted', count, coro_name)
                logger.warning('maximum attempts %d of calling %s, exceeded', max_attempts, coro_name)
                raise
            else:
                logger.exception('iteration %d of %s excepted, retrying after %d seconds', count, coro_name, interval)
                await asyncio.sleep(interval)
                interval *= 2

    return result


def is_process_function(function: Any) -> bool:
    """Return whether the given function is a process function

    :param function: a function
    :returns: True if the function is a wrapped process function, False otherwise
    """
    try:
        return function.is_process_function is True
    except AttributeError:
        return False


def is_process_scoped() -> bool:
    """Return whether the current scope is within a process.

    :returns: True if the current scope is within a nested process, False otherwise
    """
    from .processes.process import Process

    return Process.current() is not None


@contextlib.contextmanager
def loop_scope(loop) -> Iterator[None]:
    """Make an event loop current for the scope of the context

    :param loop: The event loop to make current for the duration of the scope
    """
    current = asyncio.get_event_loop()

    try:
        asyncio.set_event_loop(loop)
        yield
    finally:
        asyncio.set_event_loop(current)


def set_process_state_change_timestamp(node: 'ProcessNode') -> None:
    """Set the global setting that reflects the last time a process changed state, for the process type
    of the given process, to the current timestamp. The process type will be determined based on
    the class of the calculation node it has as its database container.

    :param process: the Process instance that changed its state
    """
    from sqlalchemy.exc import OperationalError

    from aiida.common import timezone
    from aiida.manage import get_manager
    from aiida.orm import CalculationNode, ProcessNode, WorkflowNode

    if isinstance(node, CalculationNode):
        process_type = 'calculation'
    elif isinstance(node, WorkflowNode):
        process_type = 'work'
    elif isinstance(node, ProcessNode):
        # This will only occur for testing, as in general users cannot launch plain Process classes
        return
    else:
        raise ValueError(f'unsupported calculation node type {type(node)}')

    key = PROCESS_STATE_CHANGE_KEY.format(process_type)
    description = PROCESS_STATE_CHANGE_DESCRIPTION.format(process_type)
    value = timezone.now().isoformat()

    backend = get_manager().get_profile_storage()

    try:
        backend.set_global_variable(key, value, description)
    except OperationalError:
        # This typically happens for SQLite-based storage plugins like ``core.sqlite_dos``. Since this is merely an
        # update of a timestamp that is likely to be updated soon again, just ignoring the failed update is not a
        # problem.
        LOGGER.info(
            f'Failed to write global variable `{key}` to `{value}` because the database was locked. If the storage '
            'plugin being used is `core.sqlite_dos` this is to be expected and can be safely ignored.'
        )

def get_process_state_change_timestamp(process_type: Optional[str] = None) -> Optional[datetime]:
    """Get the global setting that reflects the last time a process of the given process type changed its state.
    The returned value will be the corresponding timestamp or None if the setting does not exist.

    :param process_type: optional process type for which to get the latest state change timestamp.
        Valid process types are either 'calculation' or 'work'. If not specified, last timestamp for all
        known process types will be returned.
    :return: a timestamp or None
    """
    from aiida.manage import get_manager

    valid_process_types = ['calculation', 'work']

    if process_type is not None and process_type not in valid_process_types:
        raise ValueError(f"invalid value for process_type, valid values are {', '.join(valid_process_types)}")

    if process_type is None:
        process_types = valid_process_types
    else:
        process_types = [process_type]

    timestamps: List[datetime] = []

    backend = get_manager().get_profile_storage()

    for process_type_key in process_types:
        key = PROCESS_STATE_CHANGE_KEY.format(process_type_key)
        try:
            try:
                timestamp = backend.get_global_variable(key)
            except NotImplementedError:
                pass
            else:
                if timestamp is not None:
                    timestamps.append(datetime.fromisoformat(str(timestamp)))
        except KeyError:
            continue

    if not timestamps:
        return None

    return max(timestamps)
