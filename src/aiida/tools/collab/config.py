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

OPTION_ENABLED = 'collab.enabled'
OPTION_TOKEN = 'collab.token'
OPTION_BIND = 'collab.bind'
OPTION_PORT = 'collab.port'


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
