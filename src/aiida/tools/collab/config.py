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

from contextlib import contextmanager
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Iterator

    from aiida.manage.configuration import Profile
    from aiida.manage.configuration.config import Config
    from aiida.orm.implementation import StorageBackend

OPTION_ENABLED = 'collab.enabled'
OPTION_UUID = 'collab.uuid'
OPTION_TOKEN = 'collab.token'
OPTION_PEERS = 'collab.peers'
OPTION_BIND = 'collab.bind'
OPTION_PORT = 'collab.port'
OPTION_STAMP = 'collab.stamp'
OPTION_ANNOUNCED = 'collab.announced'
OPTION_ACCEPT_PUSH = 'collab.accept_push'
OPTION_POLICY = 'collab.policy'
OPTION_COMPUTER_MAP = 'collab.computer_map'
OPTION_MAX_CONCURRENCY = 'collab.max_concurrency'

# Groups AiiDA generates to record how provenance arrived in a profile rather than what a person curated. They
# describe the history of the profile that made them and would mean nothing in another one, so they stay home.
GENERATED_GROUP_TYPES = ('core.import', 'core.auto')


def is_enabled() -> bool:
    """Return whether the loaded profile takes part in a collab."""
    from aiida.manage.configuration import get_config_option, get_profile

    return get_profile() is not None and get_config_option(OPTION_ENABLED)


def get_collab_profile(backend: StorageBackend) -> Profile | None:
    """Return the loaded profile if it takes part in a collab and ``backend`` is its storage, or ``None``.

    Operations on any other backend, such as that of an archive, must not affect the collab state of the profile.
    """
    from aiida.manage import get_manager

    if not is_enabled():
        return None

    manager = get_manager()

    return manager.get_profile() if backend is manager.get_profile_storage() else None


def shares_group_membership(backend: StorageBackend, type_string: str) -> Profile | None:
    """Return the profile whose collab replicates the membership of a group of this type, or ``None``.

    A ``GROUP_NODE`` row carries no timestamp, so a collab that grows groups has no way to answer "which
    memberships were made since T" other than to journal each addition as it happens — which is what this gates.
    """
    from aiida.manage.configuration import get_config_option

    profile = get_collab_profile(backend)

    if profile is None or type_string in GENERATED_GROUP_TYPES:
        return None

    return profile if get_config_option(OPTION_POLICY)['groups_mode'] == 'grow' else None


@contextmanager
def mutate_config(config: Config) -> Iterator[Config]:
    """Hold the collab lock on the configuration file, yield it as it is on disk, and store it on exit.

    Every collab write goes through this. The daemon's collab endpoint writes the configuration file too — it
    merges gossiped roster entries into it — and ``Config.store`` writes the whole dictionary its holder loaded,
    so a writer that merely re-read the file before storing still reverts whatever the other one wrote in
    between. Read, modify and write happen inside one held lock instead, and two collab writers serialize.

    Nothing is written back when the document was left as it was found, so a caller that reads the file and
    decides against writing — a dry run announcing itself without raising its stamp — leaves it untouched.

    Never nest: the lock is taken on a new file handle every time, which ``flock`` does not grant twice to one
    process. A site that writes from inside another one's transaction takes the yielded configuration instead.
    """
    import copy
    from pathlib import Path

    from aiida.manage.configuration.config import Config
    from aiida.tools.collab.state import exclusive_lock

    with exclusive_lock(Path(f'{config.filepath}.collab.lock')):
        stored = Config.from_file(config.filepath)
        before = copy.deepcopy(stored.dictionary)

        yield stored

        if stored.dictionary != before:
            stored.store()


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

    The policy travels in the code because that is the one moment at which a newcomer can still decline it: the
    consent has to precede the profile it would govern. Any member mints a code from its own stored policy — the
    policy is fixed at the collab's creation, so every member's copy is equally authoritative.
    """
    from aiida.tools.collab.protocol import JoinCode

    scope = profile.name
    url = endpoint_url(config.get_option(OPTION_BIND, scope=scope), config.get_option(OPTION_PORT, scope=scope))

    return JoinCode(
        collab=config.get_option(OPTION_UUID, scope=scope),
        url=url,
        token=config.get_option(OPTION_TOKEN, scope=scope),
        policy=config.get_option(OPTION_POLICY, scope=scope),
    ).encode()


def self_entry(config: Config, profile: Profile, *, bump: bool = False) -> dict[str, Any]:
    """Return the roster entry with which this profile announces itself to its peers.

    :param config: the configuration to stamp, which a bump requires to be one ``mutate_config`` yielded: this is
        the one write site that happens inside another one's transaction, and it is that transaction which stores.
    :param bump: raise the version stamp when the endpoint URL changed since the last announcement, and record the
        new one. Only the owner of an entry ever stamps it, which is what makes "whose information is newer" a
        local fact: a stale URL cannot gossip its way back over a fresher one.
    """
    url = endpoint_url(
        config.get_option(OPTION_BIND, scope=profile.name), config.get_option(OPTION_PORT, scope=profile.name)
    )
    stamp = config.get_option(OPTION_STAMP, scope=profile.name)

    if bump and config.get_option(OPTION_ANNOUNCED, scope=profile.name) != url:
        stamp += 1
        config.set_option(OPTION_STAMP, stamp, scope=profile.name)
        config.set_option(OPTION_ANNOUNCED, url, scope=profile.name)

    return {'uuid': profile.uuid, 'url': url, 'name': profile.name, 'stamp': stamp}


def roster_entries(peers: dict[str, dict[str, Any]], mine: dict[str, Any]) -> list[dict[str, Any]]:
    """Return what this profile gossips: its own entry first, then every peer it holds as active.

    The order is part of the protocol, not presentation: the receiving ``merge_roster`` reads the first entry as
    the self-announcement of whoever is making contact, which is the one entry that contact is evidence about.

    Only the owner's self-announced name travels; the local nickname is a display alias of this machine alone.

    Dormant peers stay home. A gossiped entry is a vouching — the receiver takes it as confirmed under the current
    token — so vouching for a member one has not seen under that token would undo every rotation: the branch that
    rotated away, or the member that was excluded, would be handed back to everyone at the next sync.
    """
    return [
        mine,
        *(
            {'uuid': uuid, 'url': entry['url'], 'name': entry.get('name') or entry['nickname'], 'stamp': entry['stamp']}
            for uuid, entry in peers.items()
            if entry['active']
        ),
    ]


def dormant_roster(peers: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Return the roster with every entry set dormant, as ``rotate`` and ``rekey`` leave it.

    Dormancy deletes nothing: URL, nickname and stamp are kept as the history that lets a member returning under
    the new token be recognized rather than re-added, and resume at its existing cursor.
    """
    return {uuid: {**entry, 'active': False, 'signalled': False} for uuid, entry in peers.items()}


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
    peers: dict[str, dict[str, Any]], entries: list[Any], own_uuid: str
) -> tuple[dict[str, dict[str, Any]], list[str]]:
    """Merge gossiped roster entries into the peers of this profile.

    Entries are auto-trusted — only a token holder can hand one out — but never silent: the second return value
    reports every peer that was added, moved or reactivated, for the command output.

    Everything merged here is marked active: a merge only ever follows a contact authenticated by the current
    token, and a peer gossips its active entries alone. That is the whole of recognition — a member returning
    after a rotation is found by its profile UUID and resumes at the cursor its dormant entry kept.

    :param peers: the roster of this profile, keyed by profile UUID.
    :param entries: what a peer gossiped, of whatever shape it sent — this is wire data, hence the loose type:
        its own entry **first**, as ``roster_entries`` builds it, and the ones
        it knows after it. That first entry is the only one this contact is direct evidence about; the rest are
        hearsay, which is enough to vouch for a member but not to speak for one.
    :param own_uuid: the profile UUID of this profile, whose entry the peers gossip back and which only this
        profile itself may stamp.
    :return: the merged roster and one report line per added, moved or reactivated peer.
    """
    merged = {uuid: dict(entry) for uuid, entry in peers.items()}
    reports = []
    contact = entries[0].get('uuid') if entries and isinstance(entries[0], dict) else None

    for gossiped in entries:
        # An entry that is not even a mapping is skipped like an incomplete one. It arrives from whatever a peer
        # is running, and raising here would abort a pull that has already imported — the one place the design's
        # own rule for wire data, "malformed, so skip silently", must not be broken.
        if not isinstance(gossiped, dict):
            continue

        uuid, url, stamp, name = gossiped.get('uuid'), gossiped.get('url'), gossiped.get('stamp'), gossiped.get('name')

        # Typed as strictly as the entry is used, since a peer running anything is what hands these over: an
        # entry that is not what it claims is skipped like an incomplete one, rather than raising in the merge or
        # at the schema on its way into the configuration — where it would abort a pull that already imported.
        if not isinstance(uuid, str) or not isinstance(url, str) or not isinstance(stamp, int):
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
                'stamp': stamp,
                'seen': False,
                'active': True,
                'signalled': False,
            }
            reports.append(f'learned about peer `{nickname}` at {url}')
            continue

        entry = dict(known)

        if stamp > known['stamp']:
            # Only the owner raises its own stamp, so a higher one is the owner's own correction and supersedes
            # whatever is held here — a manual `peer set --url` included.
            entry.update(url=url, name=name, stamp=stamp)

            if known['url'] != url:
                # The flag is about the address that is announced now, so a move puts the peer back to unproven.
                entry['seen'] = False
                reports.append(f'peer `{known["nickname"]}` moved to {url}')

        if not known['active']:
            # Recognition: the member is met again under the current token, so it takes up its entry — and with
            # it the cursor kept under its UUID — where the rotation left it.
            entry['active'] = True
            reports.append(f'peer `{known["nickname"]}` is back under the current token')

        if uuid == contact:
            # The signal says "the key we share is retired", and this profile hearing from its sender under the
            # current key is what falsifies it — a rotator that rekeyed onto somebody else's code instead would
            # otherwise leave its peers told forever to rekey onto a code that no longer exists. Restricted to
            # the entry the contact speaks for, so that a *relayed* entry cannot clear the flag: third-party
            # gossip would otherwise erase a warning it knows nothing about, and nothing would restore it. Which
            # entry that is comes from the contact's own first entry and is not verified, so this orders honest
            # gossip rather than preventing a member from retracting another's signal.
            entry['signalled'] = False

        merged[uuid] = entry

    return merged, reports


def find_peer(peers: dict[str, dict[str, Any]], selector: str) -> str | None:
    """Return the profile UUID of the peer a nickname or UUID selects, or ``None`` when it selects none."""
    if selector in peers:
        return selector

    return next((uuid for uuid, entry in peers.items() if entry['nickname'] == selector), None)
