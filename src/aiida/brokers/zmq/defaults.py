"""Default configuration for ZMQ broker."""

from __future__ import annotations

from typing import Any

from aiida.common.extendeddicts import AttributeDict

__all__ = ('BROKER_DEFAULTS', 'RPC_TIMEOUT', 'get_zmq_config')

# Timeout (in seconds) for waiting on RPC Future results in the poll thread.
# None means no timeout, matching kiwipy RMQ behavior where _on_rpc awaits
# without a deadline. The runner event loop will eventually produce a result.
RPC_TIMEOUT: float | None = None

# ZMQ broker uses local IPC sockets, minimal configuration needed
# Paths are derived from profile UUID at runtime
BROKER_DEFAULTS = AttributeDict({})


def get_zmq_config() -> dict[str, Any]:
    """Return ZMQ broker configuration.

    ZMQ broker uses profile-derived paths, so minimal configuration is needed.
    The actual paths are computed from the profile UUID in ZmqBroker.__init__.

    :return: Empty configuration dictionary
    """
    return {}
