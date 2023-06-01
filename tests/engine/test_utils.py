# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=global-statement,no-self-use
"""Test engine utilities such as the exponential backoff mechanism."""
import asyncio

import pytest

from aiida import orm
from aiida.engine import calcfunction, workfunction
from aiida.engine.utils import (
    InterruptableFuture,
    exponential_backoff_retry,
    instantiate_process,
    interruptable_task,
    is_process_function,
)

ITERATION = 0
MAX_ITERATIONS = 3


class TestExponentialBackoffRetry:
    """Tests for the exponential backoff retry coroutine."""

    @pytest.fixture(autouse=True)
    def init_profile(self, aiida_localhost):  # pylint: disable=unused-argument
        """Initialize the profile."""
        # pylint: disable=attribute-defined-outside-init
        self.computer = aiida_localhost
        self.authinfo = self.computer.get_authinfo(orm.User.collection.get_default())

    @staticmethod
    def test_exp_backoff_success():
        """Test that exponential backoff will successfully catch exceptions as long as max_attempts is not exceeded."""
        global ITERATION
        ITERATION = 0
        loop = asyncio.get_event_loop()

        async def coro():
            """A function that will raise RuntimeError as long as ITERATION is smaller than MAX_ITERATIONS."""
            global ITERATION
            ITERATION += 1
            if ITERATION < MAX_ITERATIONS:
                raise RuntimeError

        max_attempts = MAX_ITERATIONS + 1
        loop.run_until_complete(exponential_backoff_retry(coro, initial_interval=0.1, max_attempts=max_attempts))

    def test_exp_backoff_max_attempts_exceeded(self):
        """Test that exponential backoff will finally raise if max_attempts is exceeded"""
        global ITERATION
        ITERATION = 0
        loop = asyncio.get_event_loop()

        def coro():
            """A function that will raise RuntimeError as long as ITERATION is smaller than MAX_ITERATIONS."""
            global ITERATION
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
    """ Tests for InterruptableFuture and interruptable_task."""

    def test_normal_future(self):
        """Test interrupt future not being interrupted"""
        loop = asyncio.get_event_loop()

        interruptable = InterruptableFuture()
        fut = asyncio.Future()

        async def task():
            fut.set_result('I am done')

        loop.run_until_complete(interruptable.with_interrupt(task()))
        assert not interruptable.done()
        assert fut.result() == 'I am done'

    def test_interrupt(self):
        """Test interrupt future being interrupted"""
        loop = asyncio.get_event_loop()

        interruptable = InterruptableFuture()
        loop.call_soon(interruptable.interrupt, RuntimeError('STOP'))
        try:
            loop.run_until_complete(interruptable.with_interrupt(asyncio.sleep(10.)))
        except RuntimeError as err:
            assert str(err) == 'STOP'
        else:
            pytest.fail('ExpectedException not raised')

        assert interruptable.done()

    def test_inside_interrupted(self):
        """Test interrupt future being interrupted from inside of coroutine"""
        loop = asyncio.get_event_loop()

        interruptable = InterruptableFuture()
        fut = asyncio.Future()

        async def task():
            await asyncio.sleep(1.)
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
        loop = asyncio.get_event_loop()

        interruptable = InterruptableFuture()

        async def task():
            interruptable.set_result('NOT ME!!!')

        loop.create_task(task())
        try:
            loop.run_until_complete(interruptable.with_interrupt(asyncio.sleep(20.)))
        except RuntimeError as err:
            assert str(err) == "This interruptible future had it's result set unexpectedly to 'NOT ME!!!'"
        else:
            pytest.fail('ExpectedException not raised')

        assert interruptable.done()


@pytest.mark.requires_rmq
class TestInterruptableTask():
    """ Tests for InterruptableFuture and interruptable_task."""

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
