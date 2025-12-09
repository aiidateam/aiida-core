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
import time

import pytest

from aiida import orm
from aiida.engine.transports import TransportQueue


class TestTransportQueue:
    """Tests for the transport queue."""

    @pytest.fixture(autouse=True)
    def init_profile(self, aiida_localhost):
        """Initialize the profile."""
        self.computer = aiida_localhost
        self.authinfo = self.computer.get_authinfo(orm.User.collection.get_default())

    def test_simple_request(self):
        """Test a simple transport request"""
        queue = TransportQueue()
        loop = queue.loop

        async def test():
            trans = None
            with queue.request_transport(self.authinfo) as request:
                trans = await request
                assert trans.is_open
            assert not trans.is_open

        loop.run_until_complete(test())

    def test_get_transport_nested(self):
        """Test nesting calls to get the same transport."""
        transport_queue = TransportQueue()
        loop = transport_queue.loop

        async def nested(queue, authinfo):
            with queue.request_transport(authinfo) as request1:
                trans1 = await request1
                assert trans1.is_open
                with queue.request_transport(authinfo) as request2:
                    trans2 = await request2
                    assert trans1 is trans2
                    assert trans2.is_open

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
        assert retval

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
            with pytest.raises(RuntimeError):
                loop.run_until_complete(test())
        finally:
            self.authinfo.get_transport().__class__.open = original

    def test_safe_interval(self):
        """Verify that the safe interval for a given in transport is respected by the transport queue."""
        # Temporarily set the safe open interval for the default transport to a finite value
        transport_class = self.authinfo.get_transport().__class__
        original_interval = transport_class._DEFAULT_SAFE_OPEN_INTERVAL

        try:
            transport_class._DEFAULT_SAFE_OPEN_INTERVAL = 0.25

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
                    assert time_elapsed > time_minimum, 'transport safe interval was violated'

            for iteration in range(5):
                loop.run_until_complete(test(iteration))

        finally:
            transport_class._DEFAULT_SAFE_OPEN_INTERVAL = original_interval

    def test_dynamic_safe_interval(self):
        """Verify that the transport queue opens immediately when enough time has passed since last close."""
        # Temporarily set the safe open interval for the default transport to a finite value
        transport_class = self.authinfo.get_transport().__class__
        original_interval = transport_class._DEFAULT_SAFE_OPEN_INTERVAL

        try:
            transport_class._DEFAULT_SAFE_OPEN_INTERVAL = 0.5

            queue = TransportQueue()
            loop = queue.loop

            # First transport request - should open immediately (no previous close time)
            async def test_first():
                time_start = time.time()
                with queue.request_transport(self.authinfo) as request:
                    trans = await request
                    time_elapsed = time.time() - time_start
                    # Should open immediately or very quickly
                    assert time_elapsed < 0.1, f'First transport took too long to open: {time_elapsed}s'
                    assert trans.is_open

            loop.run_until_complete(test_first())

            # Second transport request immediately after - should wait for remaining safe interval
            async def test_second_immediate():
                time_start = time.time()
                with queue.request_transport(self.authinfo) as request:
                    trans = await request
                    time_elapsed = time.time() - time_start
                    # Should wait approximately the safe interval since not enough time has passed
                    assert time_elapsed >= 0.4, f'Second transport opened too quickly: {time_elapsed}s'
                    assert trans.is_open

            loop.run_until_complete(test_second_immediate())

            # Wait for safe interval to pass
            time.sleep(0.6)

            # Third transport request after safe interval - should open immediately
            async def test_third_after_interval():
                time_start = time.time()
                with queue.request_transport(self.authinfo) as request:
                    trans = await request
                    time_elapsed = time.time() - time_start
                    # Should open immediately since safe interval has passed
                    assert time_elapsed < 0.1, f'Third transport took too long to open: {time_elapsed}s'
                    assert trans.is_open

            loop.run_until_complete(test_third_after_interval())

        finally:
            transport_class._DEFAULT_SAFE_OPEN_INTERVAL = original_interval
