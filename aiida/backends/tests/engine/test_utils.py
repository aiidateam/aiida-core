# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from __future__ import division
from __future__ import absolute_import
from __future__ import print_function

import unittest
from tornado.ioloop import IOLoop
from tornado.gen import coroutine

from aiida import orm
from aiida.backends.testbase import AiidaTestCase
from aiida.engine.utils import exponential_backoff_retry, RefObjectStore

ITERATION = 0
MAX_ITERATIONS = 3


class TestExponentialBackoffRetry(AiidaTestCase):
    """Tests for the exponential backoff retry coroutine."""

    @classmethod
    def setUpClass(cls, *args, **kwargs):
        """Set up a simple authinfo and for later use."""
        super(TestExponentialBackoffRetry, cls).setUpClass(*args, **kwargs)
        cls.authinfo = orm.AuthInfo(computer=cls.computer, user=orm.User.objects.get_default())
        cls.authinfo.store()

    def test_exponential_backoff_success(self):
        """Test that exponential backoff will successfully catch exceptions as long as max_attempts is not exceeded."""
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

    def test_exponential_backoff_max_attempts_exceeded(self):
        """Test that exponential backoff will finally raise if max_attempts is exceeded"""
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


class RefObjectsStore(unittest.TestCase):

    def test_simple(self):
        """ Test the reference counting works """
        IDENTIFIER = 'a'
        OBJECT = 'my string'
        obj_store = RefObjectStore()

        with obj_store.get(IDENTIFIER, lambda: OBJECT) as obj:
            # Make sure we got back the same object
            self.assertIs(OBJECT, obj)

            # Now check that the reference has the correct information
            ref = obj_store._objects['a']
            self.assertEqual(OBJECT, ref._obj)
            self.assertEqual(1, ref.count)

            # Now request the object again
            with obj_store.get(IDENTIFIER) as obj2:
                # ...and check the reference has had it's count upped
                self.assertEqual(OBJECT, obj2)
                self.assertEqual(2, ref.count)

            # Now it should have been reduced
            self.assertEqual(1, ref.count)

        # Finally the store should be empty  (there are no more references)
        self.assertEqual(0, len(obj_store._objects))

    def test_get_no_constructor(self):
        """
        Test that trying to get an object that does exists and providing
        no means to construct it fails
        """
        obj_store = RefObjectStore()
        with self.assertRaises(ValueError):
            with obj_store.get('a'):
                pass

    def test_construct(self):
        """ Test that construction only gets called when used """
        IDENTIFIER = 'a'
        OBJECT = 'my string'

        # Use a list for a  single number so we can get references to it
        times_constructed = [
            0,
        ]

        def construct():
            times_constructed[0] += 1
            return OBJECT

        obj_store = RefObjectStore()
        with obj_store.get(IDENTIFIER, construct):
            self.assertEqual(1, times_constructed[0])
            with obj_store.get(IDENTIFIER, construct):
                self.assertEqual(1, times_constructed[0])

        # Now the object should be removed and so another call to get
        # should create
        with obj_store.get(IDENTIFIER, construct):
            self.assertEqual(2, times_constructed[0])
