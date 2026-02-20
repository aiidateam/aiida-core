###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Utilities for testing memory leakage."""

import asyncio

from plumpy import get_or_create_event_loop
from pympler import muppy


def get_instances(classes, delay=0.0):
    """Return all instances of provided classes that are in memory.

    Useful for investigating memory leaks.

    :param classes: A class or tuple of classes to check (passed to `isinstance`).
    :param delay: How long to sleep (seconds) before collecting the memory dump.
        This is a convenience function for tests involving Processes. For example, :py:func:`~aiida.engine.run` returns
        before all futures are resolved/cleaned up. Dumping memory too early would catch those and the references they
        carry, although they may not actually be leaking memory.
    """
    if delay > 0:
        loop = get_or_create_event_loop()
        loop.run_until_complete(asyncio.sleep(delay))

    all_objects = muppy.get_objects()  # this also calls gc.collect()
    return [o for o in all_objects if hasattr(o, '__class__') and isinstance(o, classes)]
