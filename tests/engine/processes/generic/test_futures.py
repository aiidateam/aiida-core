###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for :mod:`aiida.engine.processes.generic.futures`."""

import kiwipy

from aiida.engine.processes.generic.futures import unwrap_kiwi_future


def test_unwrap_kiwi_future_cancelled():
    """A cancelled future should cancel the unwrapping future."""
    future: kiwipy.Future = kiwipy.Future()
    unwrapped = unwrap_kiwi_future(future)

    future.cancel()

    assert unwrapped.cancelled()
