# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=invalid-name
"""Utilities for the workflow engine."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import contextlib
import logging

from six.moves import range
import tornado.ioloop
from tornado import concurrent, gen

__all__ = ('RefObjectStore', 'interruptable_task', 'InterruptableFuture')

LOGGER = logging.getLogger(__name__)
PROCESS_STATE_CHANGE_KEY = 'process|state_change|{}'
PROCESS_STATE_CHANGE_DESCRIPTION = 'The last time a process of type {}, changed state'


def instantiate_process(runner, process, *args, **inputs):
    """
    Return an instance of the process with the given inputs. The function can deal with various types
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
        assert not args
        assert not inputs
        assert runner is process.runner
        return process

    if isinstance(process, ProcessBuilder):
        builder = process
        process_class = builder.process_class
        inputs.update(**builder)
    elif issubclass(process, Process):
        process_class = process
    else:
        raise ValueError('invalid process {}, needs to be Process or ProcessBuilder'.format(type(process)))

    process = process_class(runner=runner, inputs=inputs)

    return process


class InterruptableFuture(concurrent.Future):
    """A future that can be interrupted by calling `interrupt`."""

    def interrupt(self, reason):
        """This method should be called to interrupt the coroutine represented by this InterruptableFuture."""
        self.set_exception(reason)

    @gen.coroutine
    def with_interrupt(self, yieldable):
        """
        Yield a yieldable which will be interrupted if this future is interrupted ::

            from tornado import ioloop, gen
            loop = ioloop.IOLoop.current()

            interruptable = InterutableFuture()
            loop.add_callback(interruptable.interrupt, RuntimeError("STOP"))
            loop.run_sync(lambda: interruptable.with_interrupt(gen.sleep(2)))
            >>> RuntimeError: STOP


        :param yieldable: The yieldable
        :return: The result of the yieldable
        """
        # Wait for one of the two to finish, if it's us that finishes we expect that it was
        # because of an exception that will have been raised automatically
        wait_iterator = gen.WaitIterator(yieldable, self)
        result = yield wait_iterator.next()  # pylint: disable=stop-iteration-return
        if not wait_iterator.current_index == 0:
            raise RuntimeError("This interruptible future had it's result set unexpectedly to {}".format(result))

        result = yield [yieldable, self][0]
        raise gen.Return(result)


def interruptable_task(coro, loop=None):
    """
    Turn the given coroutine into an interruptable task by turning it into an InterruptableFuture and returning it.

    :param coro: the coroutine that should be made interruptable
    :param loop: the event loop in which to run the coroutine, by default uses tornado.ioloop.IOLoop.current()
    :return: an InterruptableFuture
    """

    loop = loop or tornado.ioloop.IOLoop.current()
    future = InterruptableFuture()

    @gen.coroutine
    def execute_coroutine():
        """Coroutine that wraps the original coroutine and sets it result on the future only if not already set."""
        try:
            result = yield coro(future)
        except Exception as exception:  # pylint: disable=broad-except
            if not future.done():
                future.set_exception(exception)
        else:
            # If the future has not been set elsewhere, i.e. by the interrupt call, by the time that the coroutine
            # is executed, set the future's result to the result of the coroutine
            if not future.done():
                future.set_result(result)

    loop.add_callback(execute_coroutine)

    return future


def ensure_coroutine(fct):
    """
    Ensure that the given function ``fct`` is a coroutine

    If the passed function is not already a coroutine, it will be made to be a coroutine

    :param fct: the function
    :returns: the coroutine
    """
    if tornado.gen.is_coroutine_function(fct):
        return fct

    @tornado.gen.coroutine
    def wrapper(*args, **kwargs):
        raise tornado.gen.Return(fct(*args, **kwargs))

    return wrapper


@gen.coroutine
def exponential_backoff_retry(fct, initial_interval=10.0, max_attempts=5, logger=None, ignore_exceptions=None):
    """
    Coroutine to call a function, recalling it with an exponential backoff in the case of an exception

    This coroutine will loop ``max_attempts`` times, calling the ``fct`` function, breaking immediately when the call
    finished without raising an exception, at which point the returned result will be raised, wrapped in a
    ``tornado.gen.Result`` instance. If an exception is caught, the function will yield a ``tornado.gen.sleep`` with a
    time interval equal to the ``initial_interval`` multiplied by ``2*N`` where ``N`` is the number of excepted calls.

    :param fct: the function to call, which will be turned into a coroutine first if it is not already
    :param initial_interval: the time to wait after the first caught exception before calling the coroutine again
    :param max_attempts: the maximum number of times to call the coroutine before re-raising the exception
    :raises: ``tornado.gen.Result`` if the ``coro`` call completes within ``max_attempts`` retries without raising
    """
    if logger is None:
        logger = LOGGER

    result = None
    coro = ensure_coroutine(fct)
    interval = initial_interval

    for iteration in range(max_attempts):
        try:
            result = yield coro()
            break  # Finished successfully
        except Exception as exception:  # pylint: disable=broad-except

            # Re-raise exceptions that should be ignored
            if ignore_exceptions is not None and isinstance(exception, ignore_exceptions):
                raise

            if iteration == max_attempts - 1:
                logger.warning('maximum attempts %d of calling %s, exceeded', max_attempts, coro.__name__)
                raise
            else:
                logger.exception('iteration %d of %s excepted, retrying after %d seconds', iteration + 1, coro.__name__,
                                 interval)

                yield gen.sleep(interval)
                interval *= 2

    raise gen.Return(result)


def is_process_function(function):
    """
    Return whether the given function is a process function

    :param function: a function
    :returns: True if the function is a wrapped process function, False otherwise
    """
    try:
        return function.is_process_function
    except AttributeError:
        return False


@contextlib.contextmanager
def loop_scope(loop):
    """
    Make an event loop current for the scope of the context

    :param loop: The event loop to make current for the duration of the scope
    :type loop: :class:`tornado.ioloop.IOLoop`
    """
    current = tornado.ioloop.IOLoop.current()

    try:
        loop.make_current()
        yield
    finally:
        current.make_current()


def set_process_state_change_timestamp(process):
    """
    Set the global setting that reflects the last time a process changed state, for the process type
    of the given process, to the current timestamp. The process type will be determined based on
    the class of the calculation node it has as its database container.

    :param process: the Process instance that changed its state
    """
    from aiida.backends.utils import set_global_setting
    from aiida.common.exceptions import UniquenessError
    from aiida.orm import ProcessNode, CalculationNode, WorkflowNode
    from aiida.common import timezone

    if isinstance(process.node, CalculationNode):
        process_type = 'calculation'
    elif isinstance(process.node, WorkflowNode):
        process_type = 'work'
    elif isinstance(process.node, ProcessNode):
        # This will only occur for testing, as in general users cannot launch plain Process classes
        return
    else:
        raise ValueError('unsupported calculation node type {}'.format(type(process.node)))

    key = PROCESS_STATE_CHANGE_KEY.format(process_type)
    description = PROCESS_STATE_CHANGE_DESCRIPTION.format(process_type)
    value = timezone.now()

    try:
        set_global_setting(key, value, description)
    except UniquenessError as exception:
        process.logger.debug('could not update the {} setting because of a UniquenessError: {}'.format(key, exception))


def get_process_state_change_timestamp(process_type=None):
    """
    Get the global setting that reflects the last time a process of the given process type changed its state.
    The returned value will be the corresponding timestamp or None if the setting does not exist.

    :param process_type: optional process type for which to get the latest state change timestamp.
        Valid process types are either 'calculation' or 'work'. If not specified, last timestamp for all
        known process types will be returned.
    :return: a timestamp or None
    """
    from aiida.backends.utils import get_global_setting

    valid_process_types = ['calculation', 'work']

    if process_type is not None and process_type not in valid_process_types:
        raise ValueError("invalid value for process_type, valid values are {}".format(', '.join(valid_process_types)))

    if process_type is None:
        process_types = valid_process_types
    else:
        process_types = [process_type]

    timestamps = []

    for process_type_key in process_types:
        key = PROCESS_STATE_CHANGE_KEY.format(process_type_key)
        try:
            timestamps.append(get_global_setting(key))
        except KeyError:
            pass

    if not timestamps:
        return None

    return max(timestamps)


class RefObjectStore(object):  # pylint: disable=useless-object-inheritance
    """
    An object store that has a reference count based on a context manager.
    Basic usage::

        store = RefObjectStore()
        with store.get('Martin', lambda: 'martin.uhrin@epfl.ch') as email:
            with store.get('Martin') as email2:
                email is email2  # True

    The use case for this store is when you have an object can be used by
    multiple parts of the code simultaneously (nested or async code) and
    where there should be one instance that exists for the lifetime of these
    contexts.  Once noone is using the object, it should be removed from the
    store (and therefore eventually garbage collected).
    """

    class Reference(object):  # pylint: disable=useless-object-inheritance
        """A reference to store the context reference count and the object itself."""

        def __init__(self, obj):
            self._count = 0
            self._obj = obj

        @property
        def count(self):
            """
            Get the reference count for the object

            :return: The reference count
            :rtype: int
            """
            return self._count

        @contextlib.contextmanager
        def get(self):
            """
            Get the object itself, which will up the reference count for the duration of the context.

            :return: The object
            """
            self._count += 1
            try:
                yield self._obj
            finally:
                self._count -= 1

    def __init__(self):
        self._objects = {}

    @contextlib.contextmanager
    def get(self, identifier, constructor=None):
        """
        Get or create an object.  The internal reference count will be upped for
        the duration of the context.  If the reference count drops to 0 the object
        will be automatically removed from the list.

        :param identifier: The key identifying the object
        :param constructor: An optional constructor that is called with no arguments
            if the object doesn't already exist in the store
        :return: The object corresponding to the identifier
        """
        try:
            ref = self._objects[identifier]
        except KeyError:
            if constructor is None:
                raise ValueError("Object not found and no constructor given")
            ref = self.Reference(constructor())
            self._objects[identifier] = ref

        try:
            with ref.get() as obj:
                yield obj
        finally:
            if ref.count == 0:
                self._objects.pop(identifier)
