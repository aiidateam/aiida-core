# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=cyclic-import
"""Futures that can poll or receive broadcasted messages while waiting for a task to be completed."""
import tornado.gen

import plumpy
import kiwipy

__all__ = ('ProcessFuture',)


class ProcessFuture(plumpy.Future):
    """Future that waits for a process to complete using both polling and listening for broadcast events if possible."""

    _filtered = None

    def __init__(self, pk, loop=None, poll_interval=None, communicator=None):
        """Construct a future for a process node being finished.

        If a None poll_interval is supplied polling will not be used. If a communicator is supplied it will be used
        to listen for broadcast messages.

        :param pk: process pk
        :param loop: An event loop
        :param poll_interval: optional polling interval, if None, polling is not activated.
        :param communicator: optional communicator, if None, will not subscribe to broadcasts.
        """
        from aiida.orm import load_node
        from .process import ProcessState

        super().__init__()
        assert not (poll_interval is None and communicator is None), 'Must poll or have a communicator to use'

        node = load_node(pk=pk)

        if node.is_terminated:
            self.set_result(node)
        else:
            self._communicator = communicator
            self.add_done_callback(lambda _: self.cleanup())

            # Try setting up a filtered broadcast subscriber
            if self._communicator is not None:
                broadcast_filter = kiwipy.BroadcastFilter(lambda *args, **kwargs: self.set_result(node), sender=pk)
                for state in [ProcessState.FINISHED, ProcessState.KILLED, ProcessState.EXCEPTED]:
                    broadcast_filter.add_subject_filter(f'state_changed.*.{state.value}')
                self._broadcast_identifier = self._communicator.add_broadcast_subscriber(broadcast_filter)

            # Start polling
            if poll_interval is not None:
                loop.add_callback(self._poll_process, node, poll_interval)

    def cleanup(self):
        """Clean up the future by removing broadcast subscribers from the communicator if it still exists."""
        if self._communicator is not None:
            self._communicator.remove_broadcast_subscriber(self._broadcast_identifier)
            self._communicator = None
            self._broadcast_identifier = None

    @tornado.gen.coroutine
    def _poll_process(self, node, poll_interval):
        """Poll whether the process node has reached a terminal state."""
        while not self.done() and not node.is_terminated:
            yield tornado.gen.sleep(poll_interval)

        if not self.done():
            self.set_result(node)
