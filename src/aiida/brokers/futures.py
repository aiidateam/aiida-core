###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
#                                                                         #
# Portions of this file are derived from kiwipy.                          #
# Copyright (c), 2022, ECOLE POLYTECHNIQUE FEDERALE DE LAUSANNE          #
# (Theory and Simulation of Materials (THEOS) and National Centre for    #
# Computational Design and Discovery of Novel Materials (NCCR MARVEL)), #
# Switzerland and ROBERT BOSCH LLC, USA. All rights reserved.            #
#                                                                         #
# The kiwipy license is reproduced in open_source_licenses.txt.          #
###########################################################################
"""Thread-based future helpers for the broker communication layer."""

from __future__ import annotations

import asyncio
import concurrent.futures
import contextlib
import logging
from collections.abc import Iterator
from typing import Any

__all__ = (
    'CancelledError',
    'Future',
    'as_completed',
    'capture_exceptions',
    'chain',
    'copy_future',
    'wait',
)

_LOGGER = logging.getLogger(__name__)

CancelledError = concurrent.futures.CancelledError
wait = concurrent.futures.wait
as_completed = concurrent.futures.as_completed
Future = concurrent.futures.Future


def copy_future(source: Future[Any], target: Future[Any]) -> None:
    """Copy the status of future ``source`` to ``target`` unless ``target`` is already done.

    :param source: The source future.
    :param target: The target future.
    """
    if target.done():
        return

    if source.cancelled():
        target.cancel()
    else:
        with capture_exceptions(target):
            target.set_result(source.result())


def chain(source: Future[Any], target: Future[Any]) -> None:
    """Chain two futures together so that when one completes, so does the other.

    The result (success or failure) of ``source`` will be copied to ``target``, unless
    ``target`` has already been completed or cancelled by the time ``source`` finishes.
    """
    source.add_done_callback(lambda first: copy_future(first, target))


@contextlib.contextmanager
def capture_exceptions(
    future: Future[Any] | asyncio.Future[Any], ignore: tuple[type[Exception], ...] = ()
) -> Iterator[None]:
    """Capture any exceptions in the context and set them as the result of the given future.

    :param future: The future to set the exception on.
    :param ignore: An optional list of exception types to ignore, these will be raised and not set on the future.
    """
    try:
        yield
    except Exception as exception:
        if isinstance(exception, ignore):
            raise

        future.set_exception(exception)
