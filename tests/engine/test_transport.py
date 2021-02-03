# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Module to test transport."""
import asyncio

from aiida.backends.testbase import AiidaTestCase
from aiida.engine.transports import TransportQueue
from aiida import orm


class TestTransportQueue(AiidaTestCase):
    """Tests for the transport queue."""

    def setUp(self, *args, **kwargs):  # pylint: disable=arguments-differ
        """ Set up a simple authinfo and for later use """
        super().setUp(*args, **kwargs)
        self.authinfo = orm.AuthInfo(computer=self.computer, user=orm.User.objects.get_default()).store()

    def tearDown(self, *args, **kwargs):  # pylint: disable=arguments-differ
        orm.AuthInfo.objects.delete(self.authinfo.id)
        super().tearDown(*args, **kwargs)

    def test_simple_request(self):
        """ Test a simple transport request """
        queue = TransportQueue()
        loop = queue.loop

        async def test():
            trans = None
            with queue.request_transport(self.authinfo) as request:
                trans = await request
                self.assertTrue(trans.is_open)
            self.assertFalse(trans.is_open)

        loop.run_until_complete(test())

    def test_get_transport_nested(self):
        """Test nesting calls to get the same transport."""
        transport_queue = TransportQueue()
        loop = transport_queue.loop

        async def nested(queue, authinfo):
            with queue.request_transport(authinfo) as request1:
                trans1 = await request1
                self.assertTrue(trans1.is_open)
                with queue.request_transport(authinfo) as request2:
                    trans2 = await request2
                    self.assertIs(trans1, trans2)
                    self.assertTrue(trans2.is_open)

        loop.run_until_complete(nested(transport_queue, self.authinfo))

    def test_get_transport_interleaved(self):
        """Test interleaved calls to get the same transport."""
        transport_queue = TransportQueue()
        loop = transport_queue.loop

        async def interleaved(authinfo):
            with transport_queue.request_transport(authinfo) as trans_future:
                await trans_future

        loop.run_until_complete(asyncio.gather(interleaved(self.authinfo), interleaved(self.authinfo)))

    def test_return_from_context(self):
        """Test raising a Return from coroutine context."""
        queue = TransportQueue()
        loop = queue.loop

        async def test():
            with queue.request_transport(self.authinfo) as request:
                trans = await request
                return trans.is_open

        retval = loop.run_until_complete(test())
        self.assertTrue(retval)

    def test_open_fail(self):
        """Test that if opening fails."""
        queue = TransportQueue()
        loop = queue.loop

        async def test():
            with queue.request_transport(self.authinfo) as request:
                await request

        def broken_open(trans):
            raise RuntimeError('Could not open transport')

        original = None
        try:
            # Let's put in a broken open method
            original = self.authinfo.get_transport().__class__.open
            self.authinfo.get_transport().__class__.open = broken_open
            with self.assertRaises(RuntimeError):
                loop.run_until_complete(test())
        finally:
            self.authinfo.get_transport().__class__.open = original

    def test_safe_interval(self):
        """Verify that the safe interval for a given in transport is respected by the transport queue."""

        # Temporarily set the safe open interval for the default transport to a finite value
        transport_class = self.authinfo.get_transport().__class__
        original_interval = transport_class._DEFAULT_SAFE_OPEN_INTERVAL  # pylint: disable=protected-access

        try:
            transport_class._DEFAULT_SAFE_OPEN_INTERVAL = 0.25  # pylint: disable=protected-access

            import time
            queue = TransportQueue()
            loop = queue.loop

            time_start = time.time()

            async def test(iteration):
                trans = None
                with queue.request_transport(self.authinfo) as request:
                    trans = await request
                    time_current = time.time()
                    time_elapsed = time_current - time_start
                    time_minimum = trans.get_safe_open_interval() * (iteration + 1)
                    self.assertTrue(time_elapsed > time_minimum, 'transport safe interval was violated')

            for iteration in range(5):
                loop.run_until_complete(test(iteration))

        finally:
            transport_class._DEFAULT_SAFE_OPEN_INTERVAL = original_interval  # pylint: disable=protected-access
