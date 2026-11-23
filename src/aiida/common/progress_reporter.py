###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Provide a singleton progress reporter implementation.

The interface is inspired by `tqdm <https://github.com/tqdm/tqdm>`,
and indeed a valid implementation is::

    from tqdm import tqdm
    set_progress_reporter(tqdm, bar_format='{l_bar}{bar}{r_bar}')

"""

from __future__ import annotations

import typing as t
from collections.abc import Callable
from functools import partial
from types import TracebackType
from typing_extensions import Self

from aiida.common.warnings import warn_deprecation

__all__ = (
    'TQDM_BAR_FORMAT',
    'ProgressReporter',
    'ProgressReporterAbstract',
    'ProgressReporterNull',
    'ProgressReporterType',
    'create_callback',
    'get_progress_reporter',
    'set_progress_bar_tqdm',
    'set_progress_reporter',
)

TQDM_BAR_FORMAT = '{desc:40.40}{percentage:6.1f}%|{bar}| {n_fmt}/{total_fmt}'


@t.runtime_checkable
class ProgressReporter(t.Protocol):
    """Protocol for progress reporters.

    This protocol specifies the structural interface for progress reporters (such as ``tqdm`` or
    custom progress bars) used throughout AiiDA.

    Example Usage::

        with get_progress_reporter()(total=10, desc="A process:") as progress:
            for i in range(10):
                progress.set_description_str(f"A process: {i}")
                progress.update()

    """

    @property
    def total(self) -> float | int | None: ...

    @property
    def desc(self) -> str | None: ...

    @property
    def n(self) -> float | int: ...

    def __enter__(self) -> Self: ...

    def __exit__(
        self,
        exctype: type[BaseException] | None,
        excinst: BaseException | None,
        exctb: TracebackType | None,
    ) -> bool | None: ...

    def set_description_str(self, text: str | None = None, /, refresh: bool = True) -> None: ...

    def update(self, n: float | int = 1) -> bool | None: ...

    def reset(self, total: float | int | None = None) -> None: ...


class ProgressReporterNull:
    """A null implementation of the progress reporter.

    This implementation does not output anything.
    """

    def __init__(self, *, total: float | int | None = None, desc: str | None = None, **kwargs: t.Any):
        """Initialise the progress reporting contextmanager.

        :param total: The number of expected iterations, or None if unknown in advance.
        :param desc: A description of the process
        """
        self._total = total
        self._desc = desc
        self._increment: float | int = 0

    @property
    def total(self) -> float | int | None:
        """Return the total iterations expected, or None if not known in advance."""
        return self._total

    @property
    def desc(self) -> str | None:
        """Return the description of the process."""
        return self._desc

    @property
    def n(self) -> float | int:
        """Return the current iteration."""
        # note using `n` as the attribute name is necessary for compatibility with tqdm
        return self._increment

    def __enter__(self) -> Self:
        """Enter the contextmanager."""
        return self

    def __exit__(
        self,
        exctype: type[BaseException] | None,
        excinst: BaseException | None,
        exctb: TracebackType | None,
    ) -> t.Literal[False]:
        """Exit the contextmanager."""
        return False

    def set_description_str(self, desc: str | None = None, refresh: bool = True, *, text: str | None = None) -> None:
        """Set the text shown by the progress reporter.

        :param desc: The text to show
        :param refresh: Force refresh of the progress reporter
        :param text: Optional backward-compatible alias for ``desc``
        """
        self._desc = desc if text is None else text

    def update(self, n: float | int = 1) -> bool | None:
        """Update the progress counter.

        :param n: Increment to add to the internal counter of iterations
        """
        self._increment += n
        return None

    def reset(self, total: float | int | None = None) -> None:
        """Resets current iterations to 0.

        :param total: If not None, update number of expected iterations.
        """
        self._increment = 0
        if total is not None:
            self._total = total


class ProgressReporterAbstract(ProgressReporterNull):
    """An abstract class for incrementing a progress reporter.

    .. deprecated:: 3.0.0
        Use :class:`~aiida.common.progress_reporter.ProgressReporter` protocol instead.
    """

    def __init_subclass__(cls, **kwargs: t.Any) -> None:
        """Warn when subclassed."""
        super().__init_subclass__(**kwargs)
        warn_deprecation(
            '`ProgressReporterAbstract` is deprecated and will be removed in v3. '
            'Use `aiida.common.ProgressReporter` protocol instead.',
            version=3,
            stacklevel=2,
        )

    def __init__(self, *, total: float | int | None = None, desc: str | None = None, **kwargs: t.Any):
        warn_deprecation(
            '`ProgressReporterAbstract` is deprecated and will be removed in v3. '
            'Use `aiida.common.ProgressReporter` protocol instead.',
            version=3,
            stacklevel=2,
        )
        super().__init__(total=total, desc=desc, **kwargs)


ProgressReporterType: t.TypeAlias = Callable[..., ProgressReporter]

PROGRESS_REPORTER: ProgressReporterType = ProgressReporterNull


def get_progress_reporter() -> ProgressReporterType:
    """Return the progress reporter

    Example Usage::

        with get_progress_reporter()(total=10, desc="A process:") as progress:
            for i in range(10):
                progress.set_description_str(f"A process: {i}")
                progress.update()

    """
    global PROGRESS_REPORTER  # noqa: PLW0602
    return PROGRESS_REPORTER


def set_progress_reporter(
    reporter: ProgressReporterType | None = None, **kwargs: t.Any
) -> None:
    """Set the progress reporter implementation

    :param reporter: A progress reporter for a process. If None, reset to ``ProgressReporterNull``.
    :param kwargs: If present, set a partial function with these kwargs

    The reporter should be a callable context manager that implements the
    :class:`~aiida.common.progress_reporter.ProgressReporter` interface.

    Example Usage::

        set_progress_reporter(ProgressReporterNull)
        with get_progress_reporter()(total=10, desc="A process:") as progress:
            for i in range(10):
                progress.set_description_str(f"A process: {i}")
                progress.update()

    """
    global PROGRESS_REPORTER  # noqa: PLW0603
    if reporter is None:
        PROGRESS_REPORTER = ProgressReporterNull
    elif kwargs:
        PROGRESS_REPORTER = partial(reporter, **kwargs)
    else:
        PROGRESS_REPORTER = reporter


def set_progress_bar_tqdm(
    bar_format: str | None = TQDM_BAR_FORMAT, leave: bool | None = False, **kwargs: t.Any
) -> None:
    """Set a `tqdm <https://github.com/tqdm/tqdm>`__ implementation of the progress reporter interface.

    See :func:`~aiida.common.progress_reporter.set_progress_reporter` for details.

    :param bar_format: Specify a custom bar string format. Pass ``bar_format=None`` when creating a
        bar with ``total=None``, since this format's percentage would sit frozen at 0%.
    :param leave: If True, keeps all traces of the progressbar upon termination of iteration.
            If `None`, will leave only if `position` is `0`.
    :param kwargs: pass to the tqdm init

    """
    from tqdm import tqdm

    set_progress_reporter(tqdm, bar_format=bar_format, leave=leave, **kwargs)


def create_callback(progress_reporter: ProgressReporter) -> Callable[[str, t.Any], None]:
    """Create a callback function to update the progress reporter.

    :returns: a callback to report on the process, ``callback(action, value)``,
        with the following callback signatures:

        - ``callback('init', {'total': <int>, 'description': <str>})``,
            to reset the progress with a new total iterations and description
        - ``callback('update', <int>)``,
            to update the progress by a certain number of iterations

    """

    def _callback(action: str, value: t.Any) -> None:
        if action == 'init':
            progress_reporter.reset(value['total'])
            progress_reporter.set_description_str(value['description'])
        elif action == 'update':
            progress_reporter.update(value)

    return _callback
