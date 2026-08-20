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
"""Async/sync bridge for plumpy, built on greenback.

This module is the sole interface to greenback within the plumpy/aiida ecosystem.
All greenback usage should go through these wrappers so that the underlying
library remains an implementation detail of plumpy.
"""

import asyncio
from collections.abc import Awaitable, Callable
from typing import Any, TypeVar

import greenback

__all__: tuple[str, ...] = ()

_T = TypeVar('_T')


def has_portal() -> bool:
    """Return True if ``sync_await()`` can be called in the current context."""
    return greenback.has_portal()


def sync_await(awaitable: Awaitable[_T]) -> _T:
    """Await *awaitable* from synchronous code. Requires an active portal."""
    return greenback.await_(awaitable)


async def run_with_portal(fn: Callable[..., _T], *args: Any, **kwargs: Any) -> _T:
    """Run sync *fn* in a greenback portal so it can call ``sync_await()``."""
    return await greenback.with_portal_run_sync(fn, *args, **kwargs)


async def ensure_portal() -> None:
    """Ensure a greenback portal is active on the current asyncio task (no-op if one exists)."""
    await greenback.ensure_portal()


def run_until_complete(loop: asyncio.AbstractEventLoop, awaitable: Awaitable[_T]) -> _T:
    """Run *awaitable* to completion, even if the event loop is already running."""
    if loop.is_running():
        if greenback.has_portal():
            return greenback.await_(awaitable)
        raise RuntimeError(
            'Cannot run awaitable: event loop is running but no greenback portal '
            'is available. If running in a Jupyter notebook, call load_profile() '
            'in a prior cell.'
        )

    async def _with_portal() -> _T:
        await greenback.ensure_portal()
        return await awaitable

    return loop.run_until_complete(_with_portal())
