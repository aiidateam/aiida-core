# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=global-statement,unused-argument
"""Provide a singleton progress reporter implementation.

The interface is inspired by `tqdm <https://github.com/tqdm/tqdm>`,
and indeed a valid implementation is::

    from tqdm import tqdm
    set_progress_reporter(tqdm, bar_format='{l_bar}{bar}{r_bar}')

"""
from contextlib import contextmanager
from functools import partial
from typing import Any, Callable, ContextManager, Iterator, Optional

__all__ = ('get_progress_reporter', 'set_progress_reporter', 'progress_reporter_base', 'ProgressIncrementerBase')


class ProgressIncrementerBase:
    """A base class for incrementing a progress reporter."""

    def set_description_str(self, text: Optional[str] = None, refresh: bool = True):
        """Set the text shown by the progress reporter.

        :param text: The text to show
        :param refresh: Force refresh of the progress reporter

        """

    def update(self, n: int = 1):  # pylint: disable=invalid-name
        """Update the progress counter.

        :param n: Increment to add to the internal counter of iterations

        """


@contextmanager
def progress_reporter_base(*,
                           total: int,
                           desc: Optional[str] = None,
                           **kwargs: Any) -> Iterator[ProgressIncrementerBase]:
    """A context manager for providing a progress reporter for a process.

    Example Usage::

        with progress_reporter(total=10, desc="A process:") as progress:
            for i in range(10):
                progress.set_description_str(f"A process: {i}")
                progress.update()

    :param total: The number of expected iterations.
    :param desc: A description of the process
    :yield: A class for incrementing the progress reporter

    """
    yield ProgressIncrementerBase()


PROGRESS_REPORTER = progress_reporter_base


def get_progress_reporter() -> Callable[..., ContextManager[Any]]:
    """Return the progress reporter

    Example Usage::

        with get_progress_reporter()(total=10, desc="A process:") as progress:
            for i in range(10):
                progress.set_description_str(f"A process: {i}")
                progress.update()

    """
    global PROGRESS_REPORTER
    return PROGRESS_REPORTER  # type: ignore


def set_progress_reporter(reporter: Optional[Callable[..., ContextManager[Any]]] = None, **kwargs: Any):
    """Set the progress reporter implementation

    :param reporter: A context manager for providing a progress reporter for a process.
        If None, reset to default null reporter

    :param kwargs: If present, set a partial function with these kwargs

    The reporter should be a context manager that implements the
    :func:`~aiida.common.progress_reporter.progress_reporter_base` interface.

    Example Usage::

        with get_progress_reporter()(total=10, desc="A process:") as progress:
            for i in range(10):
                progress.set_description_str(f"A process: {i}")
                progress.update()

    """
    global PROGRESS_REPORTER
    if reporter is None:
        PROGRESS_REPORTER = progress_reporter_base  # type: ignore
    elif kwargs:
        PROGRESS_REPORTER = partial(reporter, **kwargs)  # type: ignore
    else:
        PROGRESS_REPORTER = reporter  # type: ignore
