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


@pytest.fixture
def unresolvable_in_main(monkeypatch: pytest.MonkeyPatch):
    """Return a helper that sets a class's `__module__` to `__main__`."""

    def _apply(cls: type) -> type:
        monkeypatch.setattr(cls, '__module__', '__main__')

        return cls

    return _apply
