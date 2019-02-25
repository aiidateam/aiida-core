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
from __future__ import print_function
from __future__ import absolute_import

from six.moves import range
from tornado.gen import coroutine, Return

from aiida.backends.testbase import AiidaTestCase
from aiida.engine.transports import TransportQueue
from aiida import orm


class TestTransportQueue(AiidaTestCase):
    """ Tests for the transport queue """

    def setUp(self, *args, **kwargs):
        """ Set up a simple authinfo and for later use """
        super(TestTransportQueue, self).setUp(*args, **kwargs)
        self.authinfo = orm.AuthInfo(computer=self.computer, user=orm.User.objects.get_default()).store()

    def tearDown(self, *args, **kwargs):
        orm.AuthInfo.objects.delete(self.authinfo.id)
        super(TestTransportQueue, self).tearDown(*args, **kwargs)

    def test_simple_request(self):
        """ Test a simple transport request """
        queue = TransportQueue()
        loop = queue.loop()

        @coroutine
        def test():
            trans = None
            with queue.request_transport(self.authinfo) as request:
                trans = yield request
                self.assertTrue(trans.is_open)
            self.assertFalse(trans.is_open)

        loop.run_sync(lambda: test())

    def test_get_transport_nested(self):
        """ Test nesting calls to get the same transport """
        transport_queue = TransportQueue()
        loop = transport_queue.loop()

        @coroutine
        def nested(queue, authinfo):
            with queue.request_transport(authinfo) as request1:
                trans1 = yield request1
                self.assertTrue(trans1.is_open)
                with queue.request_transport(authinfo) as request2:
                    trans2 = yield request2
                    self.assertIs(trans1, trans2)
                    self.assertTrue(trans2.is_open)

        loop.run_sync(lambda: nested(transport_queue, self.authinfo))

    def test_get_transport_interleaved(self):
        """ Test interleaved calls to get the same transport """
        transport_queue = TransportQueue()
        loop = transport_queue.loop()

        @coroutine
        def interleaved(authinfo):
            with transport_queue.request_transport(authinfo) as trans_future:
                yield trans_future

        loop.run_sync(lambda: [interleaved(self.authinfo), interleaved(self.authinfo)])

    def test_return_from_context(self):
        """ Test raising a Return from coroutine context """
        queue = TransportQueue()
        loop = queue.loop()

        @coroutine
        def test():
            with queue.request_transport(self.authinfo) as request:
                trans = yield request
                raise Return(trans.is_open)

        retval = loop.run_sync(lambda: test())
        self.assertTrue(retval)

    def test_open_fail(self):
        """ Test that if opening fails  """
        queue = TransportQueue()
        loop = queue.loop()

        @coroutine
        def test():
            with queue.request_transport(self.authinfo) as request:
                yield request

        def broken_open(trans):
            raise RuntimeError("Could not open transport")

        original = None
        try:
            # Let's put in a broken open method
            original = self.authinfo.get_transport().__class__.open
            self.authinfo.get_transport().__class__.open = broken_open
            with self.assertRaises(RuntimeError):
                loop.run_sync(lambda: test())
        finally:
            self.authinfo.get_transport().__class__.open = original

    def test_safe_interval(self):
        """Verify that the safe interval for a given in transport is respected by the transport queue."""

        # Temporarily set the safe open interval for the default transport to a finite value
        transport_class = self.authinfo.get_transport().__class__
        original_interval = transport_class._DEFAULT_SAFE_OPEN_INTERVAL

        try:
            transport_class._DEFAULT_SAFE_OPEN_INTERVAL = 0.25

            import time
            queue = TransportQueue()
            loop = queue.loop()

            time_start = time.time()

            @coroutine
            def test(iteration):
                trans = None
                with queue.request_transport(self.authinfo) as request:
                    trans = yield request
                    time_current = time.time()
                    time_elapsed = time_current - time_start
                    time_minimum = trans.get_safe_open_interval() * (iteration + 1)
                    self.assertTrue(time_elapsed > time_minimum, 'transport safe interval was violated')

            for i in range(5):
                loop.run_sync(lambda: test(i))

        finally:
            transport_class._DEFAULT_SAFE_OPEN_INTERVAL = original_interval
