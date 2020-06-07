# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=global-statement
"""Test engine utilities such as the exponential backoff mechanism."""
import asyncio

import pytest

from aiida import orm
from aiida.backends.testbase import AiidaTestCase
from aiida.engine import calcfunction, workfunction
from aiida.engine.utils import exponential_backoff_retry, is_process_function, \
        InterruptableFuture, interruptable_task

ITERATION = 0
MAX_ITERATIONS = 3


class TestExponentialBackoffRetry(AiidaTestCase):
    """Tests for the exponential backoff retry coroutine."""

    @classmethod
    def setUpClass(cls, *args, **kwargs):
        """Set up a simple authinfo and for later use."""
        super().setUpClass(*args, **kwargs)
        cls.authinfo = orm.AuthInfo(computer=cls.computer, user=orm.User.objects.get_default())
        cls.authinfo.store()

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
        with self.assertRaises(RuntimeError):
            loop.run_until_complete(exponential_backoff_retry(coro, initial_interval=0.1, max_attempts=max_attempts))


class TestUtils(AiidaTestCase):
    """ Tests for engine utils."""

    def test_is_process_function(self):
        """Test the `is_process_function` utility."""

        def normal_function():
            pass

        @calcfunction
        def calc_function():
            pass

        @workfunction
        def work_function():
            pass

        self.assertEqual(is_process_function(normal_function), False)
        self.assertEqual(is_process_function(calc_function), True)
        self.assertEqual(is_process_function(work_function), True)

    def test_is_process_scoped(self):
        pass

    def test_loop_scope(self):
        pass


class TestInterruptable(AiidaTestCase):
    """ Tests for InterruptableFuture and interruptable_task."""

    def test_normal_future(self):
        """Test interrupt future not being interrupted"""
        loop = asyncio.get_event_loop()

        interruptable = InterruptableFuture()
        fut = asyncio.Future()

        async def task():
            fut.set_result('I am done')

        loop.run_until_complete(interruptable.with_interrupt(task()))
        self.assertFalse(interruptable.done())
        self.assertEqual(fut.result(), 'I am done')

    def test_interrupt(self):
        """Test interrupt future being interrupted"""
        loop = asyncio.get_event_loop()

        interruptable = InterruptableFuture()
        loop.call_soon(interruptable.interrupt, RuntimeError('STOP'))
        try:
            loop.run_until_complete(interruptable.with_interrupt(asyncio.sleep(10.)))
        except RuntimeError as err:
            self.assertEqual(str(err), 'STOP')
        else:
            self.fail('ExpectedException not raised')

        self.assertTrue(interruptable.done())

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
            self.assertEqual(str(err), 'STOP')
        else:
            self.fail('ExpectedException not raised')

        self.assertTrue(interruptable.done())
        self.assertEqual(fut.result(), 'I got set.')

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
            self.assertEqual(str(err), "This interruptible future had it's result set unexpectedly to 'NOT ME!!!'")
        else:
            self.fail('ExpectedException not raised')

        self.assertTrue(interruptable.done())


class TestInterruptableTask(AiidaTestCase):
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
        self.assertTrue(isinstance(task_fut, InterruptableFuture))
        self.assertTrue(task_fut.done())
        self.assertEqual(result, 'I am done')

    @pytest.mark.asyncio
    async def test_interrupted(self):
        """Test interrupt future being interrupted"""

        async def task_fn(cancellable):
            cancellable.interrupt(RuntimeError('STOP'))

        task_fut = interruptable_task(task_fn)
        try:
            await task_fut
        except RuntimeError as err:
            self.assertEqual(str(err), 'STOP')
        else:
            self.fail('ExpectedException not raised')

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
        self.assertEqual(result, 'NOT ME!!!')
