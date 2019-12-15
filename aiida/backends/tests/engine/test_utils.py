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
from tornado.ioloop import IOLoop
from tornado.gen import coroutine

from aiida import orm
from aiida.backends.testbase import AiidaTestCase
from aiida.engine import calcfunction, workfunction
from aiida.engine.utils import exponential_backoff_retry, is_process_function

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
        loop = IOLoop()

        @coroutine
        def coro():
            """A function that will raise RuntimeError as long as ITERATION is smaller than MAX_ITERATIONS."""
            global ITERATION
            ITERATION += 1
            if ITERATION < MAX_ITERATIONS:
                raise RuntimeError

        max_attempts = MAX_ITERATIONS + 1
        loop.run_sync(lambda: exponential_backoff_retry(coro, initial_interval=0.1, max_attempts=max_attempts))

    def test_exp_backoff_max_attempts_exceeded(self):
        """Test that exponential backoff will finally raise if max_attempts is exceeded"""
        global ITERATION
        ITERATION = 0
        loop = IOLoop()

        @coroutine
        def coro():
            """A function that will raise RuntimeError as long as ITERATION is smaller than MAX_ITERATIONS."""
            global ITERATION
            ITERATION += 1
            if ITERATION < MAX_ITERATIONS:
                raise RuntimeError

        max_attempts = MAX_ITERATIONS - 1
        with self.assertRaises(RuntimeError):
            loop.run_sync(lambda: exponential_backoff_retry(coro, initial_interval=0.1, max_attempts=max_attempts))

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
