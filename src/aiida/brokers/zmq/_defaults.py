###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Default constants for the ZMQ broker.

These are **developer-tunable** defaults, not exposed to end users via
``verdi config``.  User-facing options live in the config schema
(e.g. ``broker.task_timeout``).
"""

from __future__ import annotations

# -- Communicator (client-side) ------------------------------------------------

# Timeout (seconds) for scheduling work onto the background event loop.
# If the loop thread is blocked or dead for longer than this, the calling
# thread gets a ``TimeoutError``.
LOOP_TIMEOUT: float = 5.0

# Timeout (seconds) for joining the loop thread during shutdown.
LOOP_JOIN_TIMEOUT: float = 3.0

# -- Broker startup ------------------------------------------------------------

# How long (seconds) ``get_communicator()`` polls for the broker to write its
# socket files before raising ``ConnectionError``.  Relevant when the daemon
# and broker are started concurrently (e.g. by circus).
BROKER_READY_TIMEOUT: float = 10.0

# -- Server (broker-side) -----------------------------------------------------

# ZMQ socket polling interval in seconds.
POLL_TIMEOUT: float = 1.0

# ZMTP heartbeat interval (seconds) — how often the broker pings connected peers.
HEARTBEAT_IVL: float = 2.0

# ZMTP heartbeat timeout (seconds) — peer considered dead after this without a pong.
HEARTBEAT_TIMEOUT: float = 6.0

# -- Service -------------------------------------------------------------------

# How often (seconds) the broker service writes its status to disk.
STATUS_INTERVAL: float = 5.0
