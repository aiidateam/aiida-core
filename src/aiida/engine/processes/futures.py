###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Futures that can poll or receive broadcasted messages while waiting for a task to be completed."""

import asyncio
from typing import Optional, Union

import kiwipy
from plumpy import get_or_create_event_loop

from aiida.orm import Node, load_node

__all__ = ('ProcessFuture',)


class ProcessFuture(asyncio.Future):
    """Future that waits for a process to complete using both polling and listening for broadcast events if possible."""

    _filtered = None

    def __init__(
        self,
        pk: int,
        loop: Optional[asyncio.AbstractEventLoop] = None,
        poll_interval: Union[None, int, float] = None,
        communicator: Optional[kiwipy.Communicator] = None,
    ):
        """Construct a future for a process node being finished.

        If a None poll_interval is supplied polling will not be used.
        If a communicator is supplied it will be used to listen for broadcast messages.

        :param pk: process pk
        :param loop: An event loop
        :param poll_interval: optional polling interval, if None, polling is not activated.
        :param communicator: optional communicator, if None, will not subscribe to broadcasts.
        """
        from .process import ProcessState

        # create future in specified event loop
        loop = loop if loop is not None else get_or_create_event_loop()
        super().__init__(loop=loop)

        assert not (poll_interval is None and communicator is None), 'Must poll or have a communicator to use'

        node = load_node(pk=pk)

        if node.is_terminated:
            self.set_result(node)
        else:
            self._communicator = communicator
            self.add_done_callback(lambda _: self.cleanup())

            # Try setting up a filtered broadcast subscriber
            if self._communicator is not None:

                def _subscriber(*args, **kwargs):
                    if not self.done():
                        self.set_result(node)

                broadcast_filter = kiwipy.BroadcastFilter(_subscriber, sender=pk)
                for state in [ProcessState.FINISHED, ProcessState.KILLED, ProcessState.EXCEPTED]:
                    broadcast_filter.add_subject_filter(f'state_changed.*.{state.value}')
                self._broadcast_identifier = self._communicator.add_broadcast_subscriber(broadcast_filter)

            # Start polling
            if poll_interval is not None:
                loop.create_task(self._poll_process(node, poll_interval))

    def cleanup(self) -> None:
        """Clean up the future by removing broadcast subscribers from the communicator if it still exists."""
        if self._communicator is not None:
            self._communicator.remove_broadcast_subscriber(self._broadcast_identifier)
            self._communicator = None
            self._broadcast_identifier = None

    async def _poll_process(self, node: Node, poll_interval: Union[int, float]) -> None:
        """Poll whether the process node has reached a terminal state."""
        print('polling', node)
        while not self.done() and not node.is_terminated:
            await asyncio.sleep(poll_interval)

        if not self.done():
            self.set_result(node)
