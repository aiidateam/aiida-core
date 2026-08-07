###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Settings of a collab, stored as options of the profile that takes part in it."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from aiida.manage.configuration.config import Config

OPTION_ENABLED = 'collab.enabled'
OPTION_TOKEN = 'collab.token'
OPTION_BIND = 'collab.bind'
OPTION_PORT = 'collab.port'
OPTION_ACCEPT_PUSH = 'collab.accept_push'


def stored_config(config: Config) -> Config:
    """Return the configuration as it is on disk right now.

    The daemon's collab endpoint writes the configuration file too — it merges gossiped roster entries into it —
    and ``Config.store`` writes the whole dictionary its holder loaded. Whoever writes without re-reading first
    therefore silently reverts whatever the other one wrote while it was working, so every collab write goes
    through the file as it is now and mirrors the result into the configuration its own process holds.
    """
    from aiida.manage.configuration.config import Config

    return Config.from_file(config.filepath)


def is_ipv6(host: str) -> bool:
    """Return whether ``host`` is an IPv6 literal, which decides both the socket family and the URL spelling."""
    import ipaddress

    try:
        return ipaddress.ip_address(host).version == 6
    except ValueError:
        return False


def endpoint_url(host: str, port: int) -> str:
    """Return the URL at which the collab endpoint bound to ``host`` and ``port`` is reached.

    An IPv6 literal is bracketed, as the overlays this is deployed on commonly hand out IPv6 addresses.
    """
    return f'http://[{host}]:{port}' if is_ipv6(host) else f'http://{host}:{port}'
