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
                    assert time_elapsed > time_minimum, 'transport safe interval was violated'

            for iteration in range(5):
                loop.run_until_complete(test(iteration))

        finally:
            transport_class._DEFAULT_SAFE_OPEN_INTERVAL = original_interval

    def test_request_removed_before_close(self):
        """Test that transport_request is removed from dict before close() is called.

        This is a regression test for a race condition with async transports where:
        1. close() is called, which for AsyncTransport uses run_until_complete()
        2. With nest_asyncio (used by plumpy), this can yield to the event loop
        3. Another task might enter and get the same transport_request
        4. That task tries to use the transport that's being closed -> error

        The fix ensures transport_request is removed BEFORE close(), so new tasks
        create fresh transport requests.
        """
        queue = TransportQueue()
        loop = queue.loop

        events = []  # Track order of operations

        async def test():
            with queue.request_transport(self.authinfo) as request:
                trans = await request
                # Patch close to track when it's called
                original_close = trans.close

                def mock_close():
                    # Check if request was already removed from dict
                    if self.authinfo.pk not in queue._transport_requests:
                        events.append('pop_before_close')
                    events.append('close')
                    return original_close()

                trans.close = mock_close

        loop.run_until_complete(test())

        assert 'close' in events, 'Transport close() should have been called'
        assert 'pop_before_close' in events, 'Transport request should be removed before close() is called'
        assert events.index('pop_before_close') < events.index('close'), 'pop should happen before close'

    def test_new_request_during_close_gets_fresh_transport(self):
        """Test that a new request made while transport is closing gets a fresh transport.

        This verifies that after the race condition fix, new tasks don't get
        a reference to a transport that's in the process of being closed.
        We verify this by checking that each sequential request creates a new
        transport request (i.e., no request is reused from the queue).
        """
        queue = TransportQueue()
        loop = queue.loop
        transport_class = self.authinfo.get_transport().__class__

        # Use very short safe interval for this test
        original_interval = transport_class._DEFAULT_SAFE_OPEN_INTERVAL
        transport_class._DEFAULT_SAFE_OPEN_INTERVAL = 0.01

        try:
            transport_states = []

            async def use_transport(task_id):
                # Before requesting, check if there's an existing request in the queue
                had_existing_request = self.authinfo.pk in queue._transport_requests
                with queue.request_transport(self.authinfo) as request:
                    trans = await request
                    transport_states.append(
                        {
                            'task_id': task_id,
                            'had_existing_request': had_existing_request,
                            'is_open': trans.is_open,
                        }
                    )
                    # Small delay to allow interleaving
                    await asyncio.sleep(0.05)
                # After context exit, transport should be closed and removed from queue
                assert self.authinfo.pk not in queue._transport_requests

            # Run multiple tasks sequentially - each should get a fresh transport
            # because the previous one should be closed after each context exit
            for i in range(3):
                loop.run_until_complete(use_transport(i))

            # Verify each task got a fresh transport (no existing request in queue)
            for state in transport_states:
                assert not state[
                    'had_existing_request'
                ], f"Task {state['task_id']} should not have found an existing request"
                assert state['is_open'], f"Task {state['task_id']} transport should be open"

        finally:
            transport_class._DEFAULT_SAFE_OPEN_INTERVAL = original_interval
