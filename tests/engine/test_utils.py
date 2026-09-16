###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Test engine utilities such as the exponential backoff mechanism."""

import asyncio
import contextlib

import pytest

from aiida import orm
from aiida.engine import calcfunction, graph, run_get_node, workfunction
from aiida.engine.processes.events import get_or_create_event_loop
from aiida.engine.utils import (
    InterruptableFuture,
    Launchable,
    ensure_coroutine,
    exponential_backoff_retry,
    get_process_state_change_timestamp,
    instantiate_process,
    interruptable_task,
    is_process_function,
    set_process_state_change_timestamp,
)

ITERATION = 0
MAX_ITERATIONS = 3


class TestExponentialBackoffRetry:
    """Tests for the exponential backoff retry coroutine."""

    @pytest.fixture(autouse=True)
    def init_profile(self, aiida_localhost):
        """Initialize the profile."""
        self.computer = aiida_localhost
        self.authinfo = self.computer.get_authinfo(orm.User.collection.get_default())

    @staticmethod
    def test_exp_backoff_success():
        """Test that exponential backoff will successfully catch exceptions as long as max_attempts is not exceeded."""
        global ITERATION  # noqa: PLW0603
        ITERATION = 0
        loop = get_or_create_event_loop()

        async def coro():
            """A function that will raise RuntimeError as long as ITERATION is smaller than MAX_ITERATIONS."""
            global ITERATION  # noqa: PLW0603
            ITERATION += 1
            if ITERATION < MAX_ITERATIONS:
                raise RuntimeError

        max_attempts = MAX_ITERATIONS + 1
        loop.run_until_complete(exponential_backoff_retry(coro, initial_interval=0.1, max_attempts=max_attempts))

    def test_exp_backoff_max_attempts_exceeded(self):
        """Test that exponential backoff will finally raise if max_attempts is exceeded"""
        global ITERATION  # noqa: PLW0603
        ITERATION = 0
        loop = get_or_create_event_loop()

        def coro():
            """A function that will raise RuntimeError as long as ITERATION is smaller than MAX_ITERATIONS."""
            global ITERATION  # noqa: PLW0603
            ITERATION += 1
            if ITERATION < MAX_ITERATIONS:
                raise RuntimeError

        max_attempts = MAX_ITERATIONS - 1
        with pytest.raises(RuntimeError):
            loop.run_until_complete(exponential_backoff_retry(coro, initial_interval=0.1, max_attempts=max_attempts))


def test_instantiate_process_invalid(manager):
    """Test the :func:`aiida.engine.utils.instantiate_process` function for invalid ``process`` argument."""
    with pytest.raises(ValueError, match=r'invalid process <class \'bool\'>, needs to be Process or ProcessBuilder'):
        instantiate_process(manager.get_runner(), True)


@calcfunction
def multiply(x, y):
    return x * y


@graph
def empty_graph(x):
    """Declare a graph, which is never built here since only its type is under test."""


@pytest.mark.parametrize(
    'subject',
    [
        pytest.param(multiply, id='process_function'),
        pytest.param(multiply.process_class.get_builder(), id='process_builder'),
        pytest.param(empty_graph, id='graph'),
    ],
)
def test_launchable_covers_the_core_launch_types(subject):
    """Each type the engine can launch reaches it through the protocol, so none needs a check of its own."""
    assert isinstance(subject, Launchable)


def test_launchable_custom_type_is_launched(manager):
    """An object the engine has never heard of is launched by implementing the protocol."""

    class Doubler:
        """A launchable that supplies one of the inputs itself."""

        @property
        def process_class(self):
            return multiply.process_class

        def get_launch_inputs(self, **inputs):
            return {**inputs, 'y': orm.Int(2)}

    assert isinstance(Doubler(), Launchable)

    results, node = run_get_node(Doubler(), x=orm.Int(21))

    assert node.is_finished_ok, node.exit_message
    assert results['result'] == 42


def test_is_process_function():
    """Test the `is_process_function` utility."""

    def normal_function():
        pass

    @calcfunction
    def calc_function():
        pass

    @workfunction
    def work_function():
        pass

    assert is_process_function(normal_function) is False
    assert is_process_function(calc_function) is True
    assert is_process_function(work_function) is True


class TestInterruptable:
    """Tests for InterruptableFuture and interruptable_task."""

    def test_normal_future(self):
        """Test interrupt future not being interrupted"""
        loop = get_or_create_event_loop()

        interruptable = InterruptableFuture()
        fut = asyncio.Future()

        async def task():
            fut.set_result('I am done')

        loop.run_until_complete(interruptable.with_interrupt(task()))
        assert not interruptable.done()
        assert fut.result() == 'I am done'

    def test_interrupt(self):
        """Test interrupt future being interrupted"""
        loop = get_or_create_event_loop()

        interruptable = InterruptableFuture()
        loop.call_soon(interruptable.interrupt, RuntimeError('STOP'))
        try:
            loop.run_until_complete(interruptable.with_interrupt(asyncio.sleep(10.0)))
        except RuntimeError as err:
            assert str(err) == 'STOP'
        else:
            pytest.fail('ExpectedException not raised')

        assert interruptable.done()

    def test_inside_interrupted(self):
        """Test interrupt future being interrupted from inside of coroutine"""
        loop = get_or_create_event_loop()

        interruptable = InterruptableFuture()
        fut = asyncio.Future()

        async def task():
            await asyncio.sleep(1.0)
            interruptable.interrupt(RuntimeError('STOP'))
            fut.set_result('I got set.')

        try:
            loop.run_until_complete(interruptable.with_interrupt(task()))
        except RuntimeError as err:
            assert str(err) == 'STOP'
        else:
            pytest.fail('ExpectedException not raised')

        assert interruptable.done()
        assert fut.result() == 'I got set.'

    def test_interruptable_future_set(self):
        """Test interrupt future being set before coroutine is done"""
        loop = get_or_create_event_loop()

        interruptable = InterruptableFuture()

        async def task():
            interruptable.set_result('NOT ME!!!')

        future = loop.create_task(task())
        try:
            loop.run_until_complete(interruptable.with_interrupt(asyncio.sleep(20.0)))
        except RuntimeError as err:
            assert str(err) == "This interruptible future had it's result set unexpectedly to 'NOT ME!!!'"
        else:
            pytest.fail('ExpectedException not raised')

        assert interruptable.done()
        assert future.done()


@pytest.mark.requires_broker
class TestInterruptableTask:
    """Tests for InterruptableFuture and interruptable_task."""

    @pytest.mark.asyncio
    async def test_task(self):
        """Test coroutine run and succed"""

        async def task_fn(cancellable):
            fut = asyncio.Future()

            async def coro():
                fut.set_result('I am done')

            await cancellable.with_interrupt(coro())
            return fut.result()

        task_fut = interruptable_task(task_fn)
        result = await task_fut
        assert isinstance(task_fut, InterruptableFuture)
        assert task_fut.done()
        assert result == 'I am done'

    @pytest.mark.asyncio
    async def test_interrupted(self):
        """Test interrupt future being interrupted"""

        async def task_fn(cancellable):
            cancellable.interrupt(RuntimeError('STOP'))

        task_fut = interruptable_task(task_fn)
        try:
            await task_fut
        except RuntimeError as err:
            assert str(err) == 'STOP'
        else:
            raise AssertionError('ExpectedException not raised')

    @pytest.mark.asyncio
    async def test_future_already_set(self):
        """Test interrupt future being set before coroutine is done"""

        async def task_fn(cancellable):
            fut = asyncio.Future()

            async def coro():
                fut.set_result('I am done')

            await cancellable.with_interrupt(coro())
            cancellable.set_result('NOT ME!!!')
            return fut.result()

        task_fut = interruptable_task(task_fn)

        result = await task_fut
        assert result == 'NOT ME!!!'


class _AsyncCallable:
    """Callable class for testing :func:`aiida.engine.utils.ensure_coroutine`."""

    async def __call__(self, value: str) -> str:
        return value


class TestEnsureCoroutine:
    """Tests for :func:`aiida.engine.utils.ensure_coroutine`."""

    @pytest.mark.asyncio
    async def test_coroutine_function_returned(self):
        """A coroutine function is returned unchanged."""

        async def callback(value: str) -> str:
            return value

        coro = ensure_coroutine(callback)

        assert coro is callback
        assert await coro('result') == 'result'

    @pytest.mark.asyncio
    async def test_sync_function_wrapped(self):
        """A plain function is wrapped into a coroutine function."""

        def callback(value: str) -> str:
            return value

        coro = ensure_coroutine(callback)

        assert coro is not callback
        assert await coro('result') == 'result'

    @pytest.mark.asyncio
    async def test_instance_with_async_call_returned(self):
        """An instance with an ``async def __call__`` is returned unchanged."""
        instance = _AsyncCallable()

        coro = ensure_coroutine(instance)

        assert coro is instance
        assert await coro('result') == 'result'

    @pytest.mark.asyncio
    async def test_class_with_async_call_normalized(self):
        """A class with an ``async def __call__`` is normalized to its ``__call__`` method."""
        coro = ensure_coroutine(_AsyncCallable)

        assert coro is not _AsyncCallable
        assert await coro(_AsyncCallable(), 'result') == 'result'

    def test_non_callable_raises(self):
        """A non-callable raises a ``TypeError``."""
        with pytest.raises(TypeError, match='fct must be callable'):
            ensure_coroutine(object())


@pytest.mark.parametrize('with_transaction', (True, False))
@pytest.mark.parametrize('monkeypatch_process_state_change', (True, False))
def test_set_process_state_change_timestamp(manager, with_transaction, monkeypatch_process_state_change, monkeypatch):
    """Test :func:`aiida.engine.utils.set_process_state_change_timestamp`.

    This function is known to except when the ``core.sqlite_dos`` storage plugin is used and multiple processes are run.
    The function is called each time a process changes state and since it is updating the same row in the settings table
    the limitation of SQLite to not allow concurrent writes to the same page causes an exception to be thrown because
    the database is locked. This exception is caught in ``set_process_state_change_timestamp`` and simply is ignored.
    This test makes sure that if this happens, any other state changes, e.g. an extra being set on a node, are not
    accidentally reverted, when the changes are performed in an explicit transaction or not.
    """
    storage = manager.get_profile_storage()

    node = orm.CalculationNode().store()
    extra_key = 'some_key'
    extra_value = 'some value'

    # Initialize the process state change timestamp so it is possible to check whether it was changed or not at the
    # end of the test.
    set_process_state_change_timestamp(node)
    current_timestamp = get_process_state_change_timestamp()
    assert current_timestamp is not None

    if monkeypatch_process_state_change:

        def set_global_variable(*_, **__):
            from sqlalchemy.exc import OperationalError

            raise OperationalError('monkey failure', None, '', '')

        monkeypatch.setattr(storage, 'set_global_variable', set_global_variable)

    transaction_context = storage.transaction if with_transaction else contextlib.nullcontext

    with transaction_context():
        node.base.extras.set(extra_key, extra_value)
        set_process_state_change_timestamp(node)

    # The node extra should always have been set, regardless if the process state change excepted
    assert node.base.extras.get(extra_key) == extra_value

    # The process state change should have changed if the storage plugin was not monkeypatched to fail
    if monkeypatch_process_state_change:
        assert get_process_state_change_timestamp() == current_timestamp
    else:
        assert get_process_state_change_timestamp() != current_timestamp
