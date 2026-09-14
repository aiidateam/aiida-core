###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Run the snippets the documentation shows, so that what it shows is what happens."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest

SNIPPETS = Path(__file__).parents[4] / 'docs/source/topics/workflows/include/snippets/graphs'


@pytest.mark.parametrize('snippet', sorted(SNIPPETS.glob('*.py')), ids=lambda path: path.stem)
def test_a_snippet_runs(snippet, tmp_path, monkeypatch):
    """A snippet of the documentation runs, so that what it shows is what happens.

    Each is imported as a module of its own, since a task is reached by the name of the module it is declared in,
    which is as true of a snippet as of anything else a reader would write.
    """
    monkeypatch.chdir(tmp_path)
    monkeypatch.syspath_prepend(str(SNIPPETS))
    monkeypatch.delitem(sys.modules, snippet.stem, raising=False)

    importlib.import_module(snippet.stem)
