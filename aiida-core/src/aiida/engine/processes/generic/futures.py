###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
#                                                                         #
# Portions of this file are derived from Plumpy.                         #
# Copyright (c), 2022, ECOLE POLYTECHNIQUE FEDERALE DE LAUSANNE          #
# (Theory and Simulation of Materials (THEOS) and National Centre for    #
# Computational Design and Discovery of Novel Materials (NCCR MARVEL)), #
# Switzerland and ROBERT BOSCH LLC, USA. All rights reserved.            #
#                                                                         #
# The Plumpy license is reproduced in open_source_licenses.txt.         #
###########################################################################
"""Generic process-engine future helpers."""

import asyncio
from collections.abc import Awaitable, Callable
from typing import Any

import kiwipy

from aiida.engine.processes.events import get_or_create_event_loop
from aiida.engine.processes.exceptions import InvalidStateError

__all__: tuple[str, ...] = ()

CancelledError = kiwipy.CancelledError


copy_future = kiwipy.copy_future
chain = kiwipy.chain
gather = asyncio.gather

Future = asyncio.Future


class CancellableAction(Future):
    """
    An action that can be launched and potentially cancelled
    """

    def __init__(
        self,
        action: Callable[..., Any],
        cookie: Any = None,
        loop: asyncio.AbstractEventLoop | None = None,
    ):
        super().__init__(loop=loop)
        self._action = action
        self._cookie = cookie

    @property
    def cookie(self) -> Any:
        """A cookie that can be used to correlate the actions with something"""
        return self._cookie

    def run(self, *args: Any, **kwargs: Any) -> None:
        """Run the action

        :param args: the positional arguments to the action
        :param kwargs: the keyword arguments to the action
        """
        if self.done():
            raise InvalidStateError('Action has already been ran')

        try:
            with kiwipy.capture_exceptions(self):
                self.set_result(self._action(*args, **kwargs))
        finally:
            self._action = None  # type: ignore[assignment]


def create_task(coro: Callable[[], Awaitable[Any]], loop: asyncio.AbstractEventLoop | None = None) -> Future:
    """
    Schedule a call to a coro in the event loop and wrap the outcome
    in a future.

    :param coro: a function which creates the coroutine to schedule
    :param loop: the event loop to schedule it in
    :return: the future representing the outcome of the coroutine

    """
    loop = loop or get_or_create_event_loop()

    future = loop.create_future()

    async def run_task() -> None:
        with kiwipy.capture_exceptions(future):
            res = await coro()
            future.set_result(res)

    asyncio.run_coroutine_threadsafe(run_task(), loop)
    return future


def unwrap_kiwi_future(future: kiwipy.Future) -> kiwipy.Future:
    """
    Create a kiwi future that represents the final results of a nested series of futures,
    meaning that if the futures provided itself resolves to a future the returned
    future will not resolve to a value until the final chain of futures is not a future
    but a concrete value.  If at any point in the chain a future resolves to an exception
    then the returned future will also resolve to that exception.

    :param future: the future to unwrap
    :return: the unwrapping future

    """
    unwrapping = kiwipy.Future()

    def unwrap(fut: kiwipy.Future) -> None:
        if fut.cancelled():
            unwrapping.cancel()
        else:
            with kiwipy.capture_exceptions(unwrapping):
                result = fut.result()
                if isinstance(result, kiwipy.Future):
                    result.add_done_callback(unwrap)
                else:
                    unwrapping.set_result(result)

    future.add_done_callback(unwrap)
    return unwrapping
