###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Daemon exception classes.

The DaemonClient and Circus code have been removed. Use
:class:`~aiida.engine.daemon.daemon.AiidaDaemonController` instead.
"""

from __future__ import annotations

from aiida.common.exceptions import AiidaException

__all__ = (
    'DaemonException',
    'DaemonNotRunningException',
    'DaemonStalePidException',
    'DaemonTimeoutException',
)


class DaemonException(AiidaException):
    """Base class for exceptions related to the daemon."""


class DaemonNotRunningException(DaemonException):
    """Raised when a connection to the daemon is attempted but it is not running."""


class DaemonTimeoutException(DaemonException):
    """Raised when a connection to the daemon is attempted but it times out."""


class DaemonStalePidException(DaemonException):
    """Raised when a connection to the daemon is attempted but it fails and the PID file appears to be stale."""
