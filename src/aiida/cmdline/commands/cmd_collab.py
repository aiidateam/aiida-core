###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""`verdi collab` commands."""

import click

from aiida.cmdline.commands.cmd_verdi import verdi
from aiida.cmdline.params import options
from aiida.cmdline.utils import echo
from aiida.cmdline.utils.decorators import requires_loaded_profile


@verdi.group('collab')
def verdi_collab():
    """Share provenance with the peers of a collab."""


# How long the advisory signal of a rotation waits for one peer. Short, like the `verdi status` probe: nothing
# depends on it arriving, and what the user is waiting for is the new join code printed after it.
SIGNAL_TIMEOUT = 2.0


def require_collab(profile):
    """Abort unless the loaded profile takes part in a collab."""
    from aiida.tools.collab.config import is_enabled

    if not is_enabled():
        echo.echo_critical(f'profile `{profile.name}` is not part of a collab: run `verdi collab init` first.')


def parse_computer_map(entries):
    """Parse ``PEER=LOCAL`` computer mapping entries, aborting on a malformed one."""
    mapping = {}

    for entry in entries:
        peer_label, separator, local_label = entry.partition('=')

        if not separator or not peer_label or not local_label:
            echo.echo_critical(f'`{entry}` is not a valid computer mapping: pass it as PEER=LOCAL.')

        mapping[peer_label] = local_label

    return mapping


def complete_peer(ctx, param, incomplete):
    """Complete a PEER argument with the nicknames of the peers that can be synced with.

    Dormant peers are left out, as they are from `verdi status` and from every sync: a member that has not been
    seen under the current token is not somebody one can act on from here, and its address is corrected by its
    own announcement when it returns. Only the configuration file is read — no storage, daemon or network — so
    completion stays instant.
    """
    from click.shell_completion import CompletionItem

    try:
        from aiida.manage.configuration import get_config
        from aiida.tools.collab.config import OPTION_PEERS

        config = get_config()
        profile = ctx.find_root().params.get('profile')
        name = getattr(profile, 'name', None) or profile or config.default_profile_name
        peers = config.get_option(OPTION_PEERS, scope=name)
    except Exception:
        return []

    nicknames = sorted(entry['nickname'] for entry in peers.values() if entry['active'])

    return [CompletionItem(nickname) for nickname in nicknames if nickname.startswith(incomplete)]


def select_peers(configured, names):
    """Return the peers to sync with, keyed by profile UUID: the named ones, or every active one when none was named.

    A name is a local nickname or, for a peer whose nickname one does not remember, its profile UUID.

    Dormant peers are never contacted, named or not: they have not been seen under the current token, so the
    collab either rotated away from them or they have not rekeyed yet. They come back on their own — by their
    next contact here, or vouched by a peer that has seen them.
    """
    from aiida.tools.collab.config import find_peer

    if not configured:
        echo.echo_critical('this collab has no peers yet: hand out a join code, or join with `verdi collab init`.')

    active = {uuid: entry for uuid, entry in configured.items() if entry['active']}

    if not active:
        echo.echo_critical(
            'every peer of this collab is dormant: none has been seen under the current token. They reactivate '
            'when they contact this profile after rekeying, or when a peer that has seen them gossips them here.'
        )

    if not names:
        return active

    selected = {name: find_peer(configured, name) for name in names}
    unknown = [name for name, uuid in selected.items() if uuid is None]
    dormant = [name for name, uuid in selected.items() if uuid is not None and uuid not in active]

    if unknown:
        known = ', '.join(sorted(entry['nickname'] for entry in active.values()))
        echo.echo_critical(f'unknown peer(s) {", ".join(unknown)}: the peers of this collab are {known}.')

    if dormant:
        echo.echo_critical(
            f'dormant peer(s) {", ".join(dormant)}: they have not been seen under the current token, and are '
            'contacted again once they rekey and make contact.'
        )

    return {uuid: configured[uuid] for uuid in selected.values()}


def gossip(config, profile, bump=True):
    """Return what this profile announces to a peer it contacts: its own entry and everyone it knows.

    Read from the file for every peer, so that what one peer just taught this profile reaches the next one in the
    same run, and so that the daemon's own merges are not written back over.

    :param bump: raise the version stamp when this machine's address changed, which is what spreads the
        correction. A dry run announces without stamping: it is to leave nothing behind.
    """
    from aiida.tools.collab.config import OPTION_PEERS, mutate_config, roster_entries, self_entry

    with mutate_config(config) as stored:
        return roster_entries(
            stored.get_option(OPTION_PEERS, scope=profile.name), self_entry(stored, profile, bump=bump)
        )


def skipped_peer(entry, exception):
    """Return how to name a peer being skipped, calling out an address nothing has ever answered at.

    An address announced at join is only ever proven by a contact, since a peer's endpoint starts with its daemon,
    long after the join finished — so a wrong one shows up here and nowhere else. A peer that answered at all —
    with a 401 while it has not rekeyed, say, which is the routine outcome after a rotation — says why itself and
    is not called offline on top of it.
    """
    if exception.status is not None:
        return f'peer {entry["nickname"]}'

    return f'{"never-answering" if not entry.get("seen") else "offline"} peer {entry["nickname"]}'


def pin_peer(config, profile, *, peer_uuid, url, roster, token):
    """Record a completed contact: mark the peer answered and merge what it gossiped.

    :param url: the address the peer was reached at, which is what the contact proves. Its own announcement may
        have moved it in the very roster being merged here, and that address nothing has answered at yet.
    :param token: the key this contact was made under. A pin belongs to it: a `verdi collab rotate` run in
        another terminal while a long transfer was in flight has already set the roster dormant, and merging
        this contact into it would mark the peer — and everyone it vouched for, the excluded member included —
        active again under a key none of them holds.
    """
    from aiida.tools.collab.config import OPTION_PEERS, OPTION_TOKEN, merge_roster, mutate_config

    with mutate_config(config) as stored:
        if stored.get_option(OPTION_TOKEN, scope=profile.name) != token:
            echo.echo_warning(f'the collab was rekeyed while syncing with {url}: its standing is left to the rekey.')
            return

        peers, reports = merge_roster(stored.get_option(OPTION_PEERS, scope=profile.name), roster, profile.uuid)
        peers[peer_uuid] = {**peers[peer_uuid], 'seen': peers[peer_uuid]['url'] == url}

        # Written to the file as it is now and mirrored into the configuration this command holds, so that the
        # rest of the process reads what was written and not what it loaded at startup.
        for target in (stored, config):
            target.set_option(OPTION_PEERS, peers, scope=profile.name)

    # Membership is auto-trusted — only a token holder hands an entry out — but never silent.
    for report in reports:
        echo.echo_report(report)


def peer_agrees(config, profile, peer_uuid, entry, info):
    """Check the identity, the collab and the policy a peer presents, and report whether it may be synced with.

    Nothing is written here, so a refusal leaves both the configuration and the state file untouched.
    """
    from aiida.tools.collab.config import OPTION_POLICY, OPTION_UUID

    nickname = entry['nickname']

    # A URL answering with another profile UUID is a different profile — a reprovisioned machine, or a stranger —
    # and must not inherit the sync history of its predecessor.
    if info.uuid is not None and info.uuid != peer_uuid:
        echo.echo_warning(
            f'refusing to sync with {nickname}: the profile at {entry["url"]} is not the one this collab knows '
            f'(expected {peer_uuid}, found {info.uuid}). Correct the address with `verdi collab peer set`.'
        )
        return False

    # The collab UUID is what keeps a token that was shared too widely from splicing two collabs into one.
    collab = config.get_option(OPTION_UUID, scope=profile.name)

    if info.collab != collab:
        echo.echo_warning(
            f'refusing to sync with {nickname}: it takes part in collab `{info.collab}`, this profile in `{collab}`.'
        )
        return False

    # The policy is fixed when a collab is created and travels in the join code, so there is no legitimate way for
    # two members to declare different ones: a mismatch means a configuration file was edited by hand.
    policy = config.get_option(OPTION_POLICY, scope=profile.name)

    if (info.extras_mode, info.groups_mode) != (policy['extras_mode'], policy['groups_mode']):
        echo.echo_warning(
            f'refusing to sync with {nickname}: it declares extras `{info.extras_mode}` and groups '
            f'`{info.groups_mode}`, this profile extras `{policy["extras_mode"]}` and groups '
            f'`{policy["groups_mode"]}`. The policy of a collab is fixed when it is created and cannot be '
            f'changed, so one of the two `{OPTION_POLICY}` options was edited by hand; restore it to the policy '
            'the collab was founded with.'
        )
        return False

    return True


def candidate_addresses():
    """Return the addresses of this machine a collab endpoint could sensibly bind, as ``(interface, address)``.

    Only shown as candidates: which network the collaborators share is not observable from here — a default-route
    guess picks the institution LAN exactly when a private overlay is in use — so the user has to say.
    """
    import ipaddress
    import socket

    import psutil

    candidates = []

    for interface, addresses in psutil.net_if_addrs().items():
        for address in addresses:
            if address.family not in (socket.AF_INET, socket.AF_INET6):
                continue

            try:
                parsed = ipaddress.ip_address(address.address.partition('%')[0])
            except ValueError:
                continue

            if not (parsed.is_loopback or parsed.is_link_local or parsed.is_multicast):
                candidates.append((interface, str(parsed)))

    return candidates


def resolve_bind(bind, non_interactive):
    """Return the address the endpoint is to bind, prompting for it when it was not given.

    Refusing to complete without one is what makes the enabled-but-unbound profile — whose endpoint dies at every
    daemon start and is restarted forever — impossible to create.
    """
    if not bind:
        if non_interactive:
            echo.echo_critical(
                'the address of this machine on the private network of the collab is required: pass `--bind`.'
            )

        for interface, address in candidate_addresses():
            echo.echo(f'  {address} ({interface})')

        bind = click.prompt("this machine's address on the private network of the collab")

    return bind


def reserve_port(bind, port, default):
    """Return the port the endpoint is to listen on, validating the bind address by test-binding it.

    Binding is the whole validation: an address that is not this machine's fails here immediately, with no
    interface enumeration to get wrong, and the socket is also what tells us whether the address was in truth the
    wildcard — which `0`, `::0` and `0.0.0.0` all spell. The port is persisted, so the URL peers were given keeps
    working across restarts.
    """
    import errno
    import ipaddress
    import socket

    from aiida.tools.collab.config import is_ipv6

    family = socket.AF_INET6 if is_ipv6(bind) else socket.AF_INET
    # Without an explicit port the default is preferred and an ephemeral one is the fallback, so that a profile
    # set up while another one is already serving that port gets a working endpoint rather than a collision.
    candidates = [port] if port is not None else [default, 0]

    for candidate in candidates:
        with socket.socket(family, socket.SOCK_STREAM) as sock:
            try:
                sock.bind((bind, candidate))
            except OSError as exception:
                if exception.errno == errno.EADDRINUSE and candidate != candidates[-1]:
                    continue

                hint = f' `{bind}` is not an address of this machine.' if exception.errno == errno.EADDRNOTAVAIL else ''
                echo.echo_critical(f'cannot serve the collab endpoint on {bind}:{candidate}: {exception}.{hint}')

            bound, port = sock.getsockname()[:2]

            if ipaddress.ip_address(bound).is_unspecified:
                echo.echo_critical(
                    f'refusing to bind `{bind}`: the endpoint speaks plain HTTP with the token in cleartext, so '
                    'it has to listen on the private network of the collab alone.'
                )

            return port


EXTRAS_SYNC_TERMS = (
    "On nodes you share, the extras of whoever edited them last replace everyone else's: your values are "
    'overwritten, your deletions propagate, and "last" is decided by the clocks of the machines. Extras whose key '
    'starts with `_` stay private and never travel.'
)


def choose_policy(extras_mode, groups_mode, non_interactive):
    """Return the policy the creator of a collab fixes for it, asking for what was not passed.

    The choice is permanent for everyone who will ever join, so it is explained — and said to be permanent —
    before it is asked for, rather than in the help of an option nobody reads twice.
    """
    if (extras_mode and groups_mode) or non_interactive:
        policy = {'extras_mode': extras_mode or 'local', 'groups_mode': groups_mode or 'local'}
        # Reported even when it was chosen by the options, since this is the moment it becomes permanent and
        # `--non-interactive` with neither option would otherwise fix the terms of the collab in silence.
        echo.echo_report(f'this collab shares extras `{policy["extras_mode"]}` and groups `{policy["groups_mode"]}`.')

        return policy

    echo.echo_report(
        'A collab agrees on what it shares beyond provenance nodes. The choice is made once, now, and holds for '
        'every member that ever joins: it travels in the join code, and there is no way to change it afterwards. '
        'Changing your mind later means founding a new collab and joining it.'
    )

    if not extras_mode:
        echo.echo('  extras `local`: extras stop travelling once the node has, and stay yours to edit')
        echo.echo(f'  extras `sync`:  {EXTRAS_SYNC_TERMS}')
        extras_mode = click.prompt('extras mode', type=click.Choice(['local', 'sync']), default='local')

    if not groups_mode:
        echo.echo('  groups `local`: your groups stay yours, and no sync creates one')
        echo.echo('  groups `grow`:  a node curated into a group joins it on every peer, additions only')
        groups_mode = click.prompt('groups mode', type=click.Choice(['local', 'grow']), default='local')

    return {'extras_mode': extras_mode, 'groups_mode': groups_mode}


def accept_policy(policy, non_interactive):
    """Return the policy carried by a join code once its consequences have been consented to.

    A joiner chooses nothing: the policy is the collab's, fixed at its creation. What it does decide is whether to
    join at all, which is why the one policy that lets other people's edits overwrite this profile's data is shown
    and confirmed here — before a profile exists to be governed by it.
    """
    echo.echo_report(f'this collab shares extras `{policy["extras_mode"]}` and groups `{policy["groups_mode"]}`.')

    if policy['extras_mode'] == 'sync' and not non_interactive:
        echo.echo_warning(f'This collab syncs extras. {EXTRAS_SYNC_TERMS}')

        if not click.confirm('join this collab?', default=False):
            echo.echo_critical('the join was declined: no profile was created and nothing was written.')

    return policy


def create_profile(ctx, profile_name, non_interactive):
    """Create the profile that joins the collab, quickly or with the full set of questions.

    Joining always creates a fresh profile: a collab shares one logical provenance graph, and folding an existing
    profile's history into someone else's is not what anyone asks for by pasting a join code.
    """
    from aiida.cmdline.commands.cmd_presto import verdi_presto
    from aiida.cmdline.commands.cmd_profile import profile_setup
    from aiida.manage.configuration import get_profile, load_profile

    quick = non_interactive or click.confirm(
        f'set up profile `{profile_name}` quickly, with SQLite storage and no external services?', default=True
    )

    if quick:
        ctx.invoke(verdi_presto, profile_name=profile_name)
    else:
        storage = click.prompt('storage backend', default='core.psql_dos')
        command = profile_setup.get_command(ctx, storage)

        if command is None:
            echo.echo_critical(f'`{storage}` is not a storage backend of this installation.')

        # Invoked through a context of its own rather than ``ctx.invoke``, so that its options prompt for what
        # they need instead of silently taking defaults.
        with command.make_context(command.name, ['--profile-name', profile_name], parent=ctx) as sub_context:
            command.invoke(sub_context)

    load_profile(profile_name, allow_switch=True)

    return get_profile()


@verdi_collab.command('init')
@click.option(
    '--join',
    'code',
    metavar='CODE',
    help='The code of a collab to join, as shown by `verdi status` on any of its members. A new profile is created '
    'for the collab. Without it, a new collab is set up on the current profile.',
)
@click.option(
    '-p',
    '--profile-name',
    default='collab',
    show_default=True,
    help='Name of the profile to create when joining a collab.',
)
@click.option(
    '--bind',
    metavar='ADDRESS',
    help="This machine's address on the private network of the collab, on which its endpoint listens. Prompted for "
    'when not given.',
)
@click.option(
    '--port',
    type=int,
    help='Port on which the endpoint of this profile listens. A free one is picked when not given.',
)
@click.option(
    '--map-computer',
    'computer_map',
    metavar='PEER=LOCAL',
    multiple=True,
    help='Treat calculations that ran on peer computer PEER as if they ran on local computer LOCAL, so pulled '
    'calculations can be cache hits. Pass multiple times for multiple computers.',
)
@click.option(
    '--extras-mode',
    type=click.Choice(['local', 'sync']),
    help='Whether the extras of shared nodes keep being replicated (`sync`) or stop travelling once the node has '
    '(`local`, the default). Chosen once when the collab is created and permanent; prompted for when not given.',
)
@click.option(
    '--groups-mode',
    type=click.Choice(['local', 'grow']),
    help='Whether curated group membership travels (`grow`) or groups stay home (`local`, the default). Chosen '
    'once when the collab is created and permanent; prompted for when not given.',
)
@options.NON_INTERACTIVE()
@click.pass_context
def collab_init(ctx, code, profile_name, bind, port, computer_map, extras_mode, groups_mode, non_interactive):
    """Set up a profile as part of a collab.

    Peers of a collab share one logical provenance graph: each of them can pull the sealed provenance of the others and
    push their own. Both are additive, deletions are never propagated.
    """
    import secrets
    import uuid

    from aiida.tools.collab import config as collab_config
    from aiida.tools.collab.protocol import JoinCode

    config = ctx.obj.config
    mapping = parse_computer_map(computer_map)
    joining = None

    if code:
        try:
            joining = JoinCode.decode(code)
        except ValueError as exception:
            echo.echo_critical(str(exception))

        if extras_mode or groups_mode:
            echo.echo_critical(
                'a collab is joined on its own terms: its policy is fixed when it is created and travels in the '
                'join code, so `--extras-mode` and `--groups-mode` are for creating one.'
            )

        if profile_name in config.profile_names:
            echo.echo_critical(f'profile `{profile_name}` already exists: joining a collab creates a new profile.')
    else:
        profile = ctx.obj.profile

        if profile is None:
            echo.echo_critical('no profile loaded: create one with `verdi presto`, or join a collab with `--join`.')

        if collab_config.is_enabled():
            echo.echo_critical(
                f'profile `{profile.name}` is already part of a collab. Each profile can only take part in one.'
            )

    # Everything that can still be refused happens before the profile exists: an address that is not this
    # machine's, or a mistyped one, would otherwise abort with a fresh profile left behind and the retry
    # refusing to reuse its name. The policy belongs to that list — the joiner's consent to it, and the
    # creator's choice of it, both precede the profile they would govern.
    policy = (
        accept_policy(joining.policy, non_interactive)
        if joining
        else choose_policy(extras_mode, groups_mode, non_interactive)
    )
    scope = None if joining else profile.name
    bind = resolve_bind(bind, non_interactive)
    port = reserve_port(bind, port, config.get_option(collab_config.OPTION_PORT, scope=scope))
    url = collab_config.endpoint_url(bind, port)

    if joining:
        profile = create_profile(ctx, profile_name, non_interactive)

    values = {
        collab_config.OPTION_ENABLED: True,
        collab_config.OPTION_UUID: joining.collab if joining else uuid.uuid4().hex,
        collab_config.OPTION_TOKEN: joining.token if joining else secrets.token_urlsafe(32),
        collab_config.OPTION_PEERS: {},
        collab_config.OPTION_BIND: bind,
        collab_config.OPTION_PORT: port,
        collab_config.OPTION_STAMP: 1,
        collab_config.OPTION_ANNOUNCED: url,
        collab_config.OPTION_COMPUTER_MAP: mapping,
        collab_config.OPTION_POLICY: policy,
    }

    # The configuration file is shared by every profile, so any collab endpoint running on this machine is a
    # second writer of it: what is written here goes onto the file as it is now, and into the copy this process
    # holds so that the rest of the command reads what it just wrote.
    with collab_config.mutate_config(config) as stored:
        for option_name, value in values.items():
            for target in (stored, config):
                target.set_option(option_name, value, scope=profile.name)

    if joining:
        join_collab(config, profile, joining)

    echo.echo_success(f'profile `{profile.name}` serves the collab at {url}.')
    echo.echo_report('Run `verdi daemon start` to serve it, and `verdi status` for the code that lets others join.')


def announce(config, profile, code):
    """Announce this profile to the member that issued a code and merge the roster it answers with.

    The one contact a code buys: it tells the issuer that this profile holds the token — which is what admits a
    newcomer and what recognizes a member returning after a rotation — and brings back the membership the issuer
    vouches for. Merged into the roster as it is on the file, so a returning member keeps its nicknames and the
    standing of everyone else.

    :raises CollabRequestError: when the issuer cannot be reached or refuses the token.
    """
    from aiida.tools.collab.client import CollabClient
    from aiida.tools.collab.config import OPTION_PEERS, merge_roster, mutate_config, self_entry

    # Stamped like any outbound contact: a member that moved while it was dormant announces the address it is at
    # now, and only a raised stamp makes the issuer take it over the one it has held all along. In a transaction
    # of its own, since what follows it is a network round trip: no lock on the configuration file is worth
    # holding for the time a peer takes to answer.
    with mutate_config(config) as stored:
        announcement = self_entry(stored, profile, bump=True)

    with CollabClient(code.url, code.token, collab=code.collab) as client:
        response = client.join(announcement)

    with mutate_config(config) as stored:
        merged, reports = merge_roster(
            stored.get_option(OPTION_PEERS, scope=profile.name), response.roster, profile.uuid
        )

        # The issuer just answered at that URL, so it is the one entry of the roster this profile has proof of.
        for entry in merged.values():
            if entry['url'] == code.url:
                entry['seen'] = True

        for target in (stored, config):
            target.set_option(OPTION_PEERS, merged, scope=profile.name)

    for report in reports:
        echo.echo_report(report)


def join_collab(config, profile, code):
    """Announce this profile to the member that issued the join code and adopt the roster it answers with."""
    from aiida.tools.collab.protocol import CollabRequestError

    try:
        announce(config, profile, code)
    except CollabRequestError as exception:
        echo.echo_critical(
            f'could not join through {code.url}: {exception}\nProfile `{profile.name}` was created and is set '
            f'up; delete it with `verdi profile delete {profile.name}`, then run `verdi collab init --join` '
            'again with a code from a member that is online.'
        )


def set_key(stored, config, profile, token):
    """Write a new token and set the whole roster dormant, on the locked file and in this process.

    Both are one act: a token nobody has presented yet is a roster nobody has been confirmed under. The roster
    is read from the very snapshot it is written back into, so that an entry the daemon's endpoint merged
    meanwhile goes dormant with the rest instead of being dropped — dormancy deletes nothing.

    :param stored: the configuration file as ``mutate_config`` yielded it, which stores it when its caller is done.
    :param config: the configuration this process holds, mirrored into so the rest of the command sees the key.
    """
    from aiida.tools.collab.config import OPTION_PEERS, OPTION_TOKEN, dormant_roster

    values = {OPTION_TOKEN: token, OPTION_PEERS: dormant_roster(stored.get_option(OPTION_PEERS, scope=profile.name))}

    for target in (stored, config):
        for option, value in values.items():
            target.set_option(option, value, scope=profile.name)


@verdi_collab.command('rotate')
@requires_loaded_profile()
@click.pass_context
def collab_rotate(ctx):
    """Retire the token of the collab and mint a new one.

    Every member has to rekey with the code this prints, handed to them out of band. Whoever is not given it stays
    out: rotating is how a collab excludes a member, and how it splits into two groups going separate ways. The
    exclusion completes when the last member has rekeyed — until then the old token still opens the laggards.
    """
    import secrets

    from aiida.tools.collab.client import CollabClient
    from aiida.tools.collab.config import OPTION_PEERS, OPTION_TOKEN, OPTION_UUID, join_code, mutate_config
    from aiida.tools.collab.protocol import CollabRequestError

    profile = ctx.obj.profile
    require_collab(profile)

    scope = profile.name

    # The key that is retired and the key that replaces it are read and written under one lock: a second rotation
    # that read the same file first would otherwise mint its key over this one and hand out a code nobody holds.
    with mutate_config(ctx.obj.config) as stored:
        retired = stored.get_option(OPTION_TOKEN, scope=scope)
        collab = stored.get_option(OPTION_UUID, scope=scope)
        active = [entry for entry in stored.get_option(OPTION_PEERS, scope=scope).values() if entry['active']]

        set_key(stored, ctx.obj.config, profile, secrets.token_urlsafe(32))

    # Sent with the token that was just retired, the only one the peers still know, and purely advisory: it makes
    # their `verdi status` ask for a rekey and nothing else. Acting on it would hand an excluded member — who
    # holds that same token — the power to make the whole collab demand a rekey it cannot serve. A courtesy to
    # whoever answers quickly, so an unreachable peer costs the probe timeout and not the transfer one: the code
    # below is what the user is waiting for.
    for entry in active:
        with CollabClient(entry['url'], retired, collab=collab, timeout=SIGNAL_TIMEOUT) as client:
            try:
                client.signal_retired(profile.uuid)
            except CollabRequestError as exception:
                echo.echo_warning(f'could not tell {entry["nickname"]} about the rotation: {exception}')

    echo.echo_success('the collab is keyed by a new token; peers rest dormant until they rekey and make contact.')
    echo.echo_report(
        'Hand the code below to the members that stay, out of band — person to person. Sending it through the '
        'collab itself would hand it to whoever was just excluded, since that channel is keyed by the old token.'
    )
    echo.echo(join_code(ctx.obj.config, profile))


@verdi_collab.command('rekey')
@click.argument('code', metavar='CODE')
@requires_loaded_profile()
@click.pass_context
def collab_rekey(ctx, code):
    """Adopt the new token of a collab whose token was rotated.

    CODE is a fresh join code of the same collab, as `verdi status` shows it on a member that already holds the new
    token. Peers, cursors and history are kept: this profile announces itself to the member whose code it is, and
    syncing resumes where it left off.
    """
    from http import HTTPStatus

    from aiida.tools.collab.config import OPTION_BIND, OPTION_PORT, OPTION_UUID, endpoint_url, mutate_config
    from aiida.tools.collab.protocol import CollabRequestError, JoinCode

    profile = ctx.obj.profile
    require_collab(profile)

    try:
        rekeyed = JoinCode.decode(code)
    except ValueError as exception:
        echo.echo_critical(str(exception))

    scope = profile.name

    # Both refusals are inside the transaction, so a refused code leaves the file exactly as it found it.
    with mutate_config(ctx.obj.config) as stored:
        collab = stored.get_option(OPTION_UUID, scope=scope)

        # A rotation replaces the key of a collab, never its identity, so a code naming another collab is somebody
        # else's — and adopting its token would leave this profile unable to talk to either.
        if rekeyed.collab != collab:
            echo.echo_critical(
                f'this code belongs to collab `{rekeyed.collab}`, this profile takes part in `{collab}`. Rotation '
                'keeps the identity of a collab, so a code of another one is never the one to rekey with.'
            )

        # Every member's `verdi status` prints a code, this profile's own included, and rekeying with that one is
        # the one case that cannot work: this profile is the only member its own endpoint can teach nothing, so it
        # would rest its whole roster dormant and reactivate none of it.
        if rekeyed.url == endpoint_url(
            stored.get_option(OPTION_BIND, scope=scope), stored.get_option(OPTION_PORT, scope=scope)
        ):
            echo.echo_critical(
                'this is the join code of this very profile: rekeying needs the code of another member, who already '
                'holds the new key.'
            )

        set_key(stored, ctx.obj.config, profile, rekeyed.token)

    echo.echo_success('the new token is in place; cursors and history are untouched.')

    # The contact the code buys: the issuer learns this profile is back under the current token — nothing else
    # would tell it, since nobody polls a dormant peer — and vouches for the members it has seen in return.
    try:
        announce(ctx.obj.config, profile, rekeyed)
    except CollabRequestError as exception:
        if exception.status == HTTPStatus.UNAUTHORIZED:
            # The code was minted before its issuer rotated again, so this profile now holds a key nobody has:
            # no peer can reach it and it can reach none, which no amount of waiting repairs.
            echo.echo_critical(
                f'{rekeyed.url} refused this code: {exception}\nIt was superseded by a later rotation, and this '
                'profile now holds a key no member accepts. Obtain the current code and run this again.'
            )

        echo.echo_warning(
            f'could not reach {rekeyed.url} to announce the rekey: {exception}\nThe key is in place, but the peers '
            'stay dormant until one of them contacts this profile; run this again with the code of a member that '
            'is online to announce yourself now.'
        )


@verdi_collab.command('map-computer')
@click.argument('mappings', metavar='PEER=LOCAL...', nargs=-1, required=True)
@requires_loaded_profile()
@click.pass_context
def collab_map_computer(ctx, mappings):
    """Declare peer computers equivalent to local ones, so pulled calculations can be cache hits.

    Each mapping maps the label of a peer computer to the label of a local one, as PEER=LOCAL. New mappings are
    merged into the existing ones and applied to already-pulled calculations, so declaring a mapping after the
    first pull loses nothing. To remove mappings, run `verdi config unset collab.computer_map` and declare the
    remaining ones again. Restart the daemon for pushes received by the endpoint to pick up the change.
    """
    from aiida.common.exceptions import ConfigurationError
    from aiida.manage import get_manager
    from aiida.tools.collab.config import OPTION_COMPUTER_MAP, mutate_config
    from aiida.tools.collab.sync import apply_computer_map

    profile = ctx.obj.profile
    require_collab(profile)

    mapping = dict(ctx.obj.config.get_option(OPTION_COMPUTER_MAP, scope=profile.name))
    mapping.update(parse_computer_map(mappings))

    try:
        count = apply_computer_map(get_manager().get_profile_storage(), mapping)
    except ConfigurationError as exception:
        echo.echo_critical(str(exception))

    with mutate_config(ctx.obj.config) as stored:
        for target in (stored, ctx.obj.config):
            target.set_option(OPTION_COMPUTER_MAP, mapping, scope=profile.name)

    echo.echo_success(
        f'{len(mapping)} computer mapping(s) configured, the mapped hash was written onto {count} calculation(s).'
    )


@verdi_collab.group('peer')
def verdi_collab_peer():
    """Correct the entries of the peers of the collab."""


@verdi_collab_peer.command('set')
@click.argument('peer', metavar='PEER', shell_complete=complete_peer)
@click.option('--url', help='Correct the address at which the peer is reached.')
@click.option('--nickname', help='Rename the peer on this machine. The new name never travels to other machines.')
@requires_loaded_profile()
@click.pass_context
def collab_peer_set(ctx, peer, url, nickname):
    """Correct the entry of a peer of the collab.

    PEER is the nickname or the profile UUID of the peer. A corrected address is provisional: only the owner of an
    entry stamps it, so the first contact that carries the owner's own announcement reconciles it.
    """
    from aiida.tools.collab.config import OPTION_PEERS, find_peer, mutate_config

    profile = ctx.obj.profile
    require_collab(profile)

    if url is None and nickname is None:
        echo.echo_critical('nothing to set: pass `--url`, `--nickname` or both.')

    # A manual correction is the one write nothing ever re-applies, since it deliberately never travels: it has to
    # be merged into the roster as the daemon's endpoint left it, not into the copy this command started with.
    with mutate_config(ctx.obj.config) as stored:
        peers = dict(stored.get_option(OPTION_PEERS, scope=profile.name))
        uuid = find_peer(peers, peer)

        if uuid is None:
            known = ', '.join(sorted(entry['nickname'] for entry in peers.values()))
            echo.echo_critical(f'unknown peer {peer}: the peers of this collab are {known}.')

        if nickname is not None and any(
            other != uuid and entry['nickname'] == nickname for other, entry in peers.items()
        ):
            echo.echo_critical(f'nickname `{nickname}` is already in use: nicknames address peers on this machine.')

        entry = dict(peers[uuid])

        if url is not None:
            # A manual correction is a local guess about someone else's address, so it does not raise their stamp
            # and is superseded by their own announcement — and it is unproven until they answer at it.
            entry.update(url=url, seen=False)

        if nickname is not None:
            entry['nickname'] = nickname

        peers[uuid] = entry

        for target in (stored, ctx.obj.config):
            target.set_option(OPTION_PEERS, peers, scope=profile.name)

    changed = [text for text in (url and f'is at {url}', nickname and f'is now called `{nickname}`') if text]
    echo.echo_success(f'peer `{peer}` {" and ".join(changed)}.')


@verdi_collab.command('log')
@requires_loaded_profile()
@click.pass_context
def collab_log(ctx):
    """Show the history of the pulls, pushes and extras refreshes of the collab."""
    from aiida.tools.collab.config import OPTION_PEERS
    from aiida.tools.collab.state import CollabState

    profile = ctx.obj.profile
    require_collab(profile)

    state = CollabState.load(profile)

    if not state.events:
        echo.echo_report('no sync events recorded yet.')
        return

    # Events key peers by profile UUID; shown under the nickname of this machine where one matches.
    alias = {
        uuid: entry['nickname'] for uuid, entry in ctx.obj.config.get_option(OPTION_PEERS, scope=profile.name).items()
    }

    rows = [
        [
            event.time.isoformat(timespec='seconds'),
            event.direction,
            alias.get(event.peer, event.peer),
            len(event.uuids),
            event.size,
        ]
        for event in state.events
    ]
    echo.echo_tabulate(rows, headers=['Time', 'Direction', 'Peer', 'Nodes', 'Bytes'])


@verdi_collab.command('pull')
@click.argument('peers', metavar='[PEER]...', nargs=-1, shell_complete=complete_peer)
@options.FORCE(help='Do not prompt for confirmation before transferring.')
@options.DRY_RUN(help='Report what a pull would transfer from every peer, without transferring anything.')
@click.option(
    '--include-deleted',
    is_flag=True,
    help='Import nodes that were deleted from this profile before, and drop their tombstones.',
)
@click.option(
    '--pause-my-daemon',
    is_flag=True,
    help='Stop the daemon workers while the delta is imported. Required on SQLite storage while workers run.',
)
@requires_loaded_profile()
@click.pass_context
def collab_pull(ctx, peers, force, dry_run, include_deleted, pause_my_daemon):
    """Fetch the new sealed provenance of peers and import it.

    PEER is the nickname of a peer of the collab; without any, every peer is pulled from. Each transfer is
    confirmed with its exact node count and size before any payload travels.
    """
    from contextlib import nullcontext

    from aiida.common.exceptions import ConfigurationError, IntegrityError
    from aiida.engine.daemon.client import get_daemon_client
    from aiida.manage import get_manager
    from aiida.tools.collab.client import CollabClient
    from aiida.tools.collab.config import OPTION_COMPUTER_MAP, OPTION_PEERS, OPTION_POLICY, OPTION_TOKEN, OPTION_UUID
    from aiida.tools.collab.endpoint import local_identity, local_info, workers_stopped
    from aiida.tools.collab.protocol import CollabRequestError, VersionSkew, member_pairs
    from aiida.tools.collab.state import CollabState, import_lock
    from aiida.tools.collab.sync import (
        import_delta,
        members_wanted,
        missing_uuids,
        refresh_wanted,
        resolve_computer_map,
    )

    profile = ctx.obj.profile
    require_collab(profile)

    # Checked before anything is transferred: SQLite is single-writer, so the import and running workers would
    # starve each other over the database lock.
    pause = False

    if not dry_run and 'sqlite' in profile.storage_backend and get_daemon_client().is_daemon_running:
        if not pause_my_daemon:
            echo.echo_critical('cannot proceed: please pause your daemon, or pass `--pause-my-daemon`.')

        pause = True

    selected = select_peers(ctx.obj.config.get_option(OPTION_PEERS, scope=profile.name), peers)
    token = ctx.obj.config.get_option(OPTION_TOKEN, scope=profile.name)
    collab = ctx.obj.config.get_option(OPTION_UUID, scope=profile.name)
    computer_map = ctx.obj.config.get_option(OPTION_COMPUTER_MAP, scope=profile.name)
    # This profile's own policy decides what a delta may bring into it, whatever a peer declares or serves.
    policy = ctx.obj.config.get_option(OPTION_POLICY, scope=profile.name)
    backend = get_manager().get_profile_storage()
    local = local_info(profile, backend)
    workdir = CollabState.get_workdir(profile)
    pulled = 0
    failed = []

    # A mapping naming a computer this profile does not have is about this profile, not about any peer: it would
    # refuse every delta identically. Resolved here so that it aborts with nobody contacted and nothing
    # transferred, rather than once per peer after each download.
    if computer_map:
        try:
            resolve_computer_map(backend, computer_map)
        except ConfigurationError as exception:
            echo.echo_critical(str(exception))

    workdir.mkdir(parents=True, exist_ok=True)

    for peer_uuid, entry in selected.items():
        url, nickname = entry['url'], entry['nickname']

        # Reloaded per peer, so the claim presented to the second peer names what the first one just delivered.
        state = CollabState.load(profile)

        with CollabClient(url, token, collab=collab, peer=local_identity(profile)) as client:
            try:
                info = client.check_version_skew(local, direction='pull')
            except CollabRequestError as exception:
                echo.echo_warning(f'skipping {skipped_peer(entry, exception)}: {exception}')
                continue
            except VersionSkew as exception:
                # Skipped like an offline or a refusing peer: one collaborator on an aiida-core this one cannot
                # read must not stop the sync with everybody else.
                echo.echo_warning(f'skipping peer {nickname}: {exception}')
                continue

            if not peer_agrees(ctx.obj.config, profile, peer_uuid, entry, info):
                continue

            # `--include-deleted` rewinds the cursor for this pull: a tombstoned node older than the cursor would
            # otherwise never re-enter the delta. The claim keeps the transfer bounded, and drops the tombstones
            # so they are delivered again.
            cursor = None if include_deleted else state.cursors.get(peer_uuid)

            claim = state.imported_uuids_since(cursor)
            claim = claim - state.tombstones if include_deleted else claim | state.tombstones

            try:
                # The manifest names what the delta holds; only the nodes this profile lacks are then requested,
                # so already-held ancestors never travel. The roster travels with it, which is how membership
                # spreads and a corrected address heals.
                manifest = client.negotiate_delta(cursor, claim, gossip(ctx.obj.config, profile, bump=not dry_run))
                want = set(missing_uuids(backend, manifest.manifest))

                # Extras of shared nodes the peer edited more recently; empty unless this profile syncs extras.
                # Asked for under the local policy, not the peer's offer, so that what is prompted for is what
                # the import will write: the import gates on the same value and would drop the rest anyway.
                refresh_want = (
                    refresh_wanted(backend, manifest.refresh, state.tombstones)
                    if policy['extras_mode'] == 'sync'
                    else []
                )

                # Memberships of nodes this profile already holds; empty unless the collab grows groups. Filtered
                # here rather than at the import, so that what is prompted for is what will be written.
                members = (
                    members_wanted(backend, manifest.members, state.tombstones)
                    if policy['groups_mode'] == 'grow'
                    else []
                )
                curated = len(member_pairs(members))

                if dry_run:
                    summary = f'{nickname}: {len(want)} node(s) to pull'

                    if refresh_want:
                        summary += f', extras of {len(refresh_want)} node(s) to be replaced by theirs'

                    if curated:
                        summary += f', {curated} group membership(s) to add'

                    echo.echo_report(summary)
                    # The negotiation took a serving slot of the peer and is over: without this the peer would
                    # answer everybody else busy until the slot expired, for a command that transferred nothing.
                    client.release()
                    continue

                offer = client.request_delta(cursor, claim, want, refresh_want)

                if (want or refresh_want or curated) and not force:
                    prompt = f'pull {len(want)} node(s) ({offer.size} bytes) from {nickname}'

                    if refresh_want:
                        prompt += f', letting their extras replace yours on {len(refresh_want)} node(s)'

                    if curated:
                        prompt += f', adding {curated} group membership(s)'

                    if not click.confirm(f'{prompt}?', default=False):
                        echo.echo_report(f'skipped {nickname}.')
                        client.release()
                        continue

                # A stable per-peer path, so an interrupted download resumes on the next pull.
                filepath = workdir / f'pull-{peer_uuid}.aiida'
                client.download_delta(filepath, offer.delta)
            except CollabRequestError as exception:
                echo.echo_warning(f'skipping peer {nickname}: {exception}')
                # A transfer that failed abandons its slot as surely as one that was declined: the peer answered
                # a moment ago, so it is there to be told, and it is the other members that pay if it is not.
                client.release()
                continue

        try:
            with import_lock(state.filepath):
                with workers_stopped(profile) if pause else nullcontext():
                    report = import_delta(
                        filepath,
                        state=state,
                        backend=backend,
                        extras_mode=policy['extras_mode'],
                        peer=peer_uuid,
                        # The peer may have recomputed its delta between the negotiation and the request; the
                        # cursor must not advance past either the manifest the want was diffed against or the
                        # computation the bytes were cut from, or in-window nodes would never be delivered.
                        instant=min(manifest.instant, offer.instant),
                        include_deleted=include_deleted,
                        computer_map=computer_map,
                        refresh=offer.refresh,
                        groups_mode=policy['groups_mode'],
                        members=members,
                    )
        # What one peer served: a link this profile cannot resolve, or bytes the archive reader cannot read
        # (``CorruptStorage`` and its siblings are ``ConfigurationError``s, and the mapping that is genuinely this
        # profile's own was refused before the loop). Nothing landed, and the next peer's delta is unaffected, so
        # it is skipped like an offline one — but named, and with the exit code of a transfer that failed. The
        # downloaded delta is left in place for the next pull to reuse.
        except (ConfigurationError, IntegrityError) as exception:
            echo.echo_warning(f'skipping peer {nickname}: {exception}')
            failed.append(nickname)
            continue

        pin_peer(ctx.obj.config, profile, peer_uuid=peer_uuid, url=url, roster=manifest.roster, token=token)

        filepath.unlink()
        filepath.with_name(f'{filepath.name}.etag').unlink(missing_ok=True)
        pulled += len(report.uuids)

        message = f'pulled {len(report.uuids)} node(s) ({report.size} bytes) from {nickname}'

        if report.refreshed:
            message += f', refreshed the extras of {len(report.refreshed)} node(s)'

        if report.members:
            message += f', added {len(report.members)} group membership(s)'

        if report.skipped:
            message += f', skipped {len(report.skipped)} deleted node(s)'

        echo.echo_success(message)

    if pulled:
        _dump_hint(profile)

    if failed:
        echo.echo_critical(f'the delta of {", ".join(failed)} did not land: see the warnings above.')


def _dump_hint(profile):
    """Point at the full dump, since an incremental one selects by mtime and pulled nodes keep old timestamps."""
    from aiida.tools._dumping.utils import DumpPaths

    filepath = DumpPaths.get_default_dump_path(entity=profile) / DumpPaths.TRACKING_LOG_FILE_NAME

    if filepath.exists():
        echo.echo_report(
            'this profile has an incremental dump: pulled nodes keep their original timestamps, so run '
            '`verdi profile dump --no-filter-by-last-dump-time` once to include them.'
        )


@verdi_collab.command('push')
@click.argument('peers', metavar='[PEER]...', nargs=-1, shell_complete=complete_peer)
@options.FORCE(help='Do not prompt for confirmation before transferring.')
@options.DRY_RUN(help='Report what a push would transfer to every peer, without transferring anything.')
@requires_loaded_profile()
@click.pass_context
def collab_push(ctx, peers, force, dry_run):
    """Send the new sealed provenance of this profile to peers.

    PEER is the nickname of a peer of the collab; without any, every peer that accepts pushes is pushed to. Each
    transfer is confirmed with its exact node count and size before any payload travels.
    """
    import json
    from datetime import datetime
    from http import HTTPStatus

    from aiida.common import timezone
    from aiida.manage import get_manager
    from aiida.tools.collab.client import CollabClient
    from aiida.tools.collab.config import OPTION_PEERS, OPTION_POLICY, OPTION_TOKEN, OPTION_UUID
    from aiida.tools.collab.endpoint import local_identity, local_info
    from aiida.tools.collab.protocol import CollabRequestError, VersionSkew, member_pairs
    from aiida.tools.collab.state import CollabEvent, CollabState
    from aiida.tools.collab.sync import (
        compute_delta,
        export_delta,
        membership_offer,
        refresh_offer,
        refresh_snapshots,
    )

    profile = ctx.obj.profile
    require_collab(profile)

    selected = select_peers(ctx.obj.config.get_option(OPTION_PEERS, scope=profile.name), peers)
    token = ctx.obj.config.get_option(OPTION_TOKEN, scope=profile.name)
    collab = ctx.obj.config.get_option(OPTION_UUID, scope=profile.name)
    policy = ctx.obj.config.get_option(OPTION_POLICY, scope=profile.name)
    backend = get_manager().get_profile_storage()
    identity = local_identity(profile)
    local = local_info(profile, backend)
    workdir = CollabState.get_workdir(profile)
    failed = []

    workdir.mkdir(parents=True, exist_ok=True)

    for peer_uuid, entry in selected.items():
        url, nickname = entry['url'], entry['nickname']
        filepath = workdir / f'push-{peer_uuid}.aiida'
        filepath_meta = workdir / f'push-{peer_uuid}.json'

        with CollabClient(url, token, collab=collab, peer=identity) as client:
            try:
                info = client.check_version_skew(local, direction='push')
            except CollabRequestError as exception:
                echo.echo_warning(f'skipping {skipped_peer(entry, exception)}: {exception}')
                continue
            except VersionSkew as exception:
                # Skipped like an offline or a refusing peer: one collaborator that cannot read what this profile
                # writes must not stop the sync with everybody else.
                echo.echo_warning(f'skipping peer {nickname}: {exception}')
                continue

            if not info.accept_push:
                echo.echo_warning(f'skipping peer {nickname}: it does not accept pushes.')
                continue

            if not peer_agrees(ctx.obj.config, profile, peer_uuid, entry, info):
                continue

            # A peer that dies anywhere between the handshake and the upload is skipped like an offline one:
            # nothing durable was written, the stash (if any) is preserved, and the remaining peers still sync.
            try:
                handshake = client.push_handshake(identity, gossip(ctx.obj.config, profile, bump=not dry_run))

                if handshake.busy:
                    echo.echo_warning(f'skipping peer {nickname}: it is busy right now, try again shortly.')
                    continue

                meta = json.loads(filepath_meta.read_text(encoding='utf-8')) if filepath_meta.exists() else None

                state = CollabState.load(profile)
                refresh = []
                members = []
                curated = 0

                if filepath.exists() and meta is not None and meta['peer'] == peer_uuid:
                    # A previous push to this peer failed after the transfer. Retrying with the very same bytes
                    # is what lets the upload negotiate that everything is already staged and re-attempt only
                    # the import; the original instant travels with them, since it is what describes those bytes.
                    uuids, instant = meta['uuids'], datetime.fromisoformat(meta['instant'])

                    # The memberships are negotiated again, though the bytes are not: the import advances the
                    # peer's cursor to the stashed instant, past every journal entry older than it, so a retry
                    # that carried none would lose the curation the failed push had negotiated for good.
                    curations = (
                        membership_offer(state=state, backend=backend, cursor=handshake.cursor)
                        if policy['groups_mode'] == 'grow'
                        else []
                    )
                    members = client.diff_manifest([], {}, curations).members if curations else []
                    curated = len(member_pairs(members))

                    if dry_run:
                        summary = f'{nickname}: {len(uuids)} node(s) to push (stashed retry)'

                        if curated:
                            summary += f', {curated} group membership(s) to add there'

                        echo.echo_report(summary)
                        # The handshake took a serving slot of the peer and is over: without this the peer would
                        # answer everybody else busy until the slot expired, for a command that sent nothing.
                        client.release()
                        continue

                    echo.echo_report(f'retrying the delta of the previous failed push to {nickname}')
                else:
                    # The delta is offered to the peer as a manifest first — with the mtimes of the extras this
                    # profile edited, when the collab syncs them — so that only what the peer lacks travels.
                    delta = compute_delta(
                        state=state,
                        backend=backend,
                        cursor=handshake.cursor,
                        claim=frozenset(handshake.claim),
                    )
                    offer = (
                        refresh_offer(state=state, backend=backend, cursor=handshake.cursor)
                        if policy['extras_mode'] == 'sync'
                        else {}
                    )
                    curations = (
                        membership_offer(state=state, backend=backend, cursor=handshake.cursor)
                        if policy['groups_mode'] == 'grow'
                        else []
                    )
                    diff = client.diff_manifest(delta.uuids, offer, curations)
                    want = set(diff.missing)
                    curated = len(member_pairs(diff.members))

                    if dry_run:
                        summary = f'{nickname}: {len(want)} node(s) to push'

                        if diff.refresh:
                            summary += f', extras of {len(diff.refresh)} node(s) to be replaced by yours'

                        if curated:
                            summary += f', {curated} group membership(s) to add there'

                        echo.echo_report(summary)
                        client.release()
                        continue

                    export = export_delta(
                        filepath, delta=delta, backend=backend, want=want, groups_mode=policy['groups_mode']
                    )
                    refresh = refresh_snapshots(backend, diff.refresh)
                    members = diff.members
                    uuids, instant = export.uuids, export.instant
                    filepath_meta.write_text(
                        json.dumps({'peer': peer_uuid, 'instant': instant.isoformat(), 'uuids': uuids}, indent=4),
                        encoding='utf-8',
                    )

                if not uuids and not refresh and not members:
                    filepath.unlink()
                    filepath_meta.unlink()

                    # Logged even though nothing travelled, so that the log answers "when did this last run"
                    # and not only "when did this last transfer". A sync that had nothing to carry is still a
                    # completed contact, so the identity and policy it revealed are pinned as after any other.
                    with CollabState.mutate(CollabState.get_filepath(profile)) as fresh:
                        fresh.events.append(
                            CollabEvent(time=timezone.now(), direction='push', peer=peer_uuid, uuids=[], size=0)
                        )

                    pin_peer(
                        ctx.obj.config,
                        profile,
                        peer_uuid=peer_uuid,
                        url=url,
                        roster=handshake.roster,
                        token=token,
                    )
                    echo.echo_report(f'nothing to push: {nickname} is up to date.')
                    client.release()
                    continue

                if not force:
                    prompt = f'push {len(uuids)} node(s) ({filepath.stat().st_size} bytes) to {nickname}'

                    if refresh:
                        prompt += f', replacing their extras with yours on {len(refresh)} node(s)'

                    if curated:
                        prompt += f', adding {curated} group membership(s) there'

                    if not click.confirm(f'{prompt}?', default=False):
                        # The cut is dropped rather than stashed: a stash is re-sent without renegotiation, which
                        # is right after a failed import but wrong after a decline, when the peer moves on.
                        filepath.unlink()
                        filepath_meta.unlink()
                        echo.echo_report(f'skipped {nickname}.')
                        client.release()
                        continue

                upload = client.upload_delta(filepath)
                echo.echo_report(f'transferred {upload.sent} bytes, {upload.staged} staged on the peer')
            except CollabRequestError as exception:
                echo.echo_warning(f'skipping peer {nickname}: {exception}')
                client.release()
                continue

            # An import that did not land says nothing about the next peer's, so it is skipped like an offline one
            # — but named, and with the exit code of a transfer that failed.
            try:
                client.trigger_import(upload.sha256, peer=identity, instant=instant, refresh=refresh, members=members)
            except CollabRequestError as exception:
                # A refusal that never reached the import — corrupt bytes, a staging file that is gone, a token
                # rotated in between — leaves the slot the handshake took with nothing to release it: the import
                # whose `finally` would have is the one that did not run.
                client.release()
                failed.append(nickname)

                if exception.status == HTTPStatus.UNPROCESSABLE_ENTITY:
                    # The delta can never land — it links to a node the peer no longer holds — so retrying the
                    # same bytes would abort forever. The next push negotiates afresh, its diff includes the hole.
                    filepath.unlink()
                    filepath_meta.unlink()
                    echo.echo_warning(
                        f'skipping peer {nickname}: it refused the delta: {exception}\nThe next push negotiates afresh.'
                    )
                    continue

                echo.echo_warning(
                    f'skipping peer {nickname}: files transferred, provenance not landed: {exception}\n'
                    'The next push resumes from whatever the peer still has staged.'
                )
                continue

        size = filepath.stat().st_size

        # Only the event is recorded: what the peer now holds is its cursor for this profile, kept on its side.
        # The peer is keyed as pull events key it — by its profile UUID — so `collab log` maps it through the
        # alias and a renamed nickname does not orphan old rows.
        with CollabState.mutate(CollabState.get_filepath(profile)) as fresh:
            fresh.events.append(
                CollabEvent(time=timezone.now(), direction='push', peer=peer_uuid, uuids=uuids, size=size)
            )

        pin_peer(ctx.obj.config, profile, peer_uuid=peer_uuid, url=url, roster=handshake.roster, token=token)

        filepath.unlink()
        filepath_meta.unlink()

        message = f'pushed {len(uuids)} node(s) ({size} bytes) to {nickname}'

        if refresh:
            message += f', refreshed the extras of {len(refresh)} node(s)'

        if members:
            message += f', added {len(member_pairs(members))} group membership(s)'

        echo.echo_success(message)

    if failed:
        echo.echo_critical(f'the delta sent to {", ".join(failed)} did not land: see the warnings above.')
