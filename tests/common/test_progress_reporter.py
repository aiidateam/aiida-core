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

import pytest

from aiida.common.progress_reporter import get_progress_reporter, set_progress_bar_tqdm, set_progress_reporter


@pytest.fixture
def tqdm_reporter():
    """Install the tqdm reporter and restore the default afterwards."""

    def _install(**kwargs):
        set_progress_bar_tqdm(**kwargs)
        return get_progress_reporter()

    try:
        yield _install
    finally:
        set_progress_reporter(None)


def _run_bar(reporter, stream):
    with reporter(total=10, desc='Doing something', file=stream) as progress:
        progress.update(5)


def test_disabled_when_stream_is_not_a_terminal(tqdm_reporter):
    """A redirected stream must get no output at all, so log files do not fill with redraw frames."""
    stream = io.StringIO()
    _run_bar(tqdm_reporter(), stream)
    assert stream.getvalue() == ''


def test_enabled_when_disable_is_explicitly_false(tqdm_reporter):
    """Passing ``disable=False`` must still write, so the default is what silences a redirected stream."""
    stream = io.StringIO()
    _run_bar(tqdm_reporter(disable=False), stream)
    assert 'Doing something' in stream.getvalue()
