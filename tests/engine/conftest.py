###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Fixtures shared by the engine tests."""

import pytest

from aiida.common import callables


@pytest.fixture
def unresolvable_in_main(monkeypatch: pytest.MonkeyPatch):
    """Return a callable that reports a class as defined in ``__main__``, the way a notebook cell does.

    Under pytest ``__main__`` is the test runner, which holds no such class, so no interpreter reading the name back
    resolves it. That is the situation of a notebook, whose ``__main__`` is the kernel, seen from a daemon worker.

    Where a test needs the *submitting* interpreter's view instead, in which ``__main__`` does hold the class and its
    source is therefore readable, it has to build that itself: see ``main_holds_the_class`` in ``test_process.py``.
    """

    def _apply(cls: type) -> type:
        monkeypatch.setattr(cls, '__module__', '__main__')

        assert not callables.resolves_here(cls), 'premise: no name may reach the class once it reports `__main__`'

        return cls

    return _apply
