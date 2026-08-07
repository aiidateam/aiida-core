###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Settings of a collab, stored as options of the profile that takes part in it.

Three identities live here, with three lifetimes. The **token** is the current key to the collab and authenticates
every request. The **profile UUID** is the permanent identity of a member: the roster is keyed by it, and so are the
cursors, so a member survives any change of its address. The **collab UUID** is the permanent identity of the collab
itself; it travels in every join code and handshake, so two different collabs can never be spliced into one.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from aiida.manage.configuration import Profile
    from aiida.manage.configuration.config import Config

OPTION_ENABLED = 'collab.enabled'
OPTION_UUID = 'collab.uuid'
OPTION_TOKEN = 'collab.token'
OPTION_PEERS = 'collab.peers'
OPTION_BIND = 'collab.bind'
OPTION_PORT = 'collab.port'
OPTION_ACCEPT_PUSH = 'collab.accept_push'


def is_enabled() -> bool:
    """Return whether the loaded profile takes part in a collab."""
    from aiida.manage.configuration import get_config_option, get_profile

    return get_profile() is not None and get_config_option(OPTION_ENABLED)


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


def join_code(config: Config, profile: Profile) -> str:
    """Return the code that admits a newcomer to this collab, or rekeys a member onto its current token.

    Built from where the endpoint listens now rather than from what was last announced: a moved address only
    catches up with its announcement at the next outbound sync, and a code handed out meanwhile has to work.
    """
    from aiida.tools.collab.protocol import JoinCode

    scope = profile.name
    url = endpoint_url(config.get_option(OPTION_BIND, scope=scope), config.get_option(OPTION_PORT, scope=scope))

    return JoinCode(
        collab=config.get_option(OPTION_UUID, scope=scope),
        url=url,
        token=config.get_option(OPTION_TOKEN, scope=scope),
    ).encode()


def self_entry(config: Config, profile: Profile) -> dict[str, Any]:
    """Return the roster entry with which this profile announces itself to the collab."""
    url = endpoint_url(
        config.get_option(OPTION_BIND, scope=profile.name), config.get_option(OPTION_PORT, scope=profile.name)
    )

    return {'uuid': profile.uuid, 'url': url, 'name': profile.name}


def roster_entries(peers: dict[str, dict[str, Any]], mine: dict[str, Any]) -> list[dict[str, Any]]:
    """Return the membership of the collab: this profile's own entry first, then every peer it holds.

    Only the owner's self-announced name travels; the local nickname is a display alias of this machine alone.
    """
    return [
        mine,
        *(
            {'uuid': uuid, 'url': entry['url'], 'name': entry.get('name') or entry['nickname']}
            for uuid, entry in peers.items()
        ),
    ]


def unique_nickname(peers: dict[str, dict[str, Any]], name: str) -> str:
    """Return ``name`` deduplicated against the nicknames already in use, since they address peers on the CLI."""
    taken = {entry['nickname'] for entry in peers.values()}

    if name not in taken:
        return name

    index = 2

    while f'{name}-{index}' in taken:
        index += 1

    return f'{name}-{index}'


def merge_roster(
    peers: dict[str, dict[str, Any]], entries: list[dict[str, Any]], own_uuid: str
) -> tuple[dict[str, dict[str, Any]], list[str]]:
    """Merge gossiped roster entries into the peers of this profile.

    Entries are auto-trusted — only a token holder can hand one out — but never silent: the second return value
    reports every peer that was added, for the command output.

    :param peers: the roster of this profile, keyed by profile UUID.
    :param entries: the membership a peer handed over: its own entry first, as ``roster_entries`` builds it, and
        the ones it knows after it.
    :param own_uuid: the profile UUID of this profile, whose entry the peers hand back.
    :return: the merged roster and one report line per added peer.
    """
    merged = {uuid: dict(entry) for uuid, entry in peers.items()}
    reports = []

    for gossiped in entries:
        uuid, url, name = gossiped.get('uuid'), gossiped.get('url'), gossiped.get('name')

        # Typed as strictly as the entry is used, since a peer running anything is what hands these over: an
        # entry that is not what it claims is skipped like an incomplete one, rather than raising in the merge or
        # at the schema on its way into the configuration — where it would abort a pull that already imported.
        if not isinstance(uuid, str) or not isinstance(url, str):
            continue

        if not uuid or not url or uuid == own_uuid:
            continue

        name = name if isinstance(name, str) and name else uuid[:8]
        known = merged.get(uuid)

        if known is None:
            nickname = unique_nickname(merged, name)
            merged[uuid] = {
                'url': url,
                'nickname': nickname,
                'name': name,
                'seen': False,
            }
            reports.append(f'learned about peer `{nickname}` at {url}')

    return merged, reports
