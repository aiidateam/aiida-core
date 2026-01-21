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
from aiida.engine import calcfunction, workfunction
from aiida.engine.utils import (
    InterruptableFuture,
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

    #    @pytest.fixture(autouse=True)
    #    def init_profile(self, aiida_localhost):
    #        """Initialize the profile."""
    #        self.computer = aiida_localhost
    #        self.authinfo = self.computer.get_authinfo(orm.User.collection.get_default())

    # @staticmethod
    @pytest.mark.asyncio
    async def test_exp_backoff_success(self):
        """Test that exponential backoff will successfully catch exceptions as long as max_attempts is not exceeded."""
        global ITERATION  # noqa: PLW0603
        ITERATION = 0

        async def coro():
            """A function that will raise RuntimeError as long as ITERATION is smaller than MAX_ITERATIONS."""
            global ITERATION  # noqa: PLW0603
            ITERATION += 1
            if ITERATION < MAX_ITERATIONS:
                raise RuntimeError

        max_attempts = MAX_ITERATIONS + 1
        await exponential_backoff_retry(coro, initial_interval=0.1, max_attempts=max_attempts)

    @pytest.mark.asyncio
    async def test_exp_backoff_max_attempts_exceeded(self):
        """Test that exponential backoff will finally raise if max_attempts is exceeded"""
        global ITERATION  # noqa: PLW0603
        ITERATION = 0

        def coro():
            """A function that will raise RuntimeError as long as ITERATION is smaller than MAX_ITERATIONS."""
            global ITERATION  # noqa: PLW0603
            ITERATION += 1
            if ITERATION < MAX_ITERATIONS:
                raise RuntimeError

        max_attempts = MAX_ITERATIONS - 1
        with pytest.raises(RuntimeError):
            await exponential_backoff_retry(coro, initial_interval=0.1, max_attempts=max_attempts)


def test_instantiate_process_invalid(manager):
    """Test the :func:`aiida.engine.utils.instantiate_process` function for invalid ``process`` argument."""
    with pytest.raises(ValueError, match=r'invalid process <class \'bool\'>, needs to be Process or ProcessBuilder'):
        instantiate_process(manager.get_runner(), True)


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

    @pytest.mark.asyncio
    async def test_normal_future(self):
        """Test interrupt future not being interrupted"""
        interruptable = InterruptableFuture()
        fut = asyncio.Future()

        async def task():
            fut.set_result('I am done')

        await interruptable.with_interrupt(task())
        assert not interruptable.done()
        assert fut.result() == 'I am done'

    @pytest.mark.asyncio
    async def test_interrupt(self):
        """Test interrupt future being interrupted"""
        loop = asyncio.get_running_loop()

        interruptable = InterruptableFuture()
        loop.call_soon(interruptable.interrupt, RuntimeError('STOP'))
        try:
            await interruptable.with_interrupt(asyncio.sleep(10.0))
        except RuntimeError as err:
            assert str(err) == 'STOP'
        else:
            pytest.fail('ExpectedException not raised')

        assert interruptable.done()

    @pytest.mark.asyncio
    def test_inside_interrupted(self):
        """Test interrupt future being interrupted from inside of coroutine"""
        loop = asyncio.get_event_loop()

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

    @pytest.mark.asyncio
    def test_interruptable_future_set(self):
        """Test interrupt future being set before coroutine is done"""
        loop = asyncio.get_event_loop()

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


@pytest.mark.requires_rmq
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
