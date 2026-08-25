###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the progress reporter."""

import io
import sys
from types import SimpleNamespace

import pytest

from aiida.common.progress_reporter import get_progress_reporter, set_progress_bar_tqdm, set_progress_reporter


class Stream(io.StringIO):
    """A stream whose terminal-ness is settable, since ``io.StringIO`` is never a terminal."""

    def __init__(self, *, isatty: bool):
        super().__init__()
        self._isatty = isatty

    def isatty(self) -> bool:
        return self._isatty


@pytest.fixture
def tqdm_reporter():
    """Install the tqdm reporter and restore the default afterwards."""

    def _install(**kwargs):
        """Install the tqdm reporter with ``kwargs`` and return the installed reporter."""
        set_progress_bar_tqdm(**kwargs)
        return get_progress_reporter()

    try:
        yield _install
    finally:
        set_progress_reporter(None)


def _run_bar(reporter, stream):
    """Run a short progress bar to completion on ``stream``."""
    with reporter(total=10, desc='Doing something', file=stream) as progress:
        progress.update(5)


@pytest.mark.parametrize(
    'kwargs, isatty, expect_bar',
    (
        pytest.param({}, False, False, id='default-hidden-on-redirected-stream'),
        pytest.param({}, True, True, id='default-shown-on-terminal'),
        pytest.param({'disable': False}, False, True, id='explicit-false-shows-on-redirected-stream'),
        pytest.param({'disable': True}, True, False, id='explicit-true-hides-on-terminal'),
    ),
)
def test_bar_visibility(tqdm_reporter, kwargs, isatty, expect_bar):
    """The stream's terminal-ness decides by default, and an explicit ``disable`` overrides it."""
    stream = Stream(isatty=isatty)

    _run_bar(tqdm_reporter(**kwargs), stream)

    written = stream.getvalue()
    # A hidden bar has to leave the stream untouched, so a log file does not fill with redraw frames.
    assert (written != '') is expect_bar
    assert ('Doing something' in written) is expect_bar


def test_shown_in_jupyter_kernel(tqdm_reporter, monkeypatch):
    """A Jupyter kernel's stderr is not a terminal, but it renders the redraws as an animation."""
    shell = SimpleNamespace(kernel=object())
    monkeypatch.setitem(sys.modules, 'IPython', SimpleNamespace(get_ipython=lambda: shell))

    stream = Stream(isatty=False)

    _run_bar(tqdm_reporter(), stream)

    assert 'Doing something' in stream.getvalue()
