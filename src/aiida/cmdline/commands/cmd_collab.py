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
        echo.echo_critical(
            f'profile `{profile.name}` is not part of a collab: create one with `verdi collab init`, or enter '
            'an existing one with `verdi collab join`.'
        )


def hold_the_sync_lock(ctx, profile):
    """Refuse to run while another sync command of this profile is running, and hold the lock until this one ends.

    The per-peer transfer stashes are stable paths with no guard of their own — a cron pull beside a manual push is
    enough — and two writers tear the file. A torn push uploads cleanly, since its checksum is taken from the torn
    bytes, fails the import as a corrupt archive and is then re-sent verbatim forever: that peer is wedged until a
    human finds and deletes a file no message names. A torn pull loops on 416 until the peer re-exports.
    """
    from aiida.tools.collab.state import CollabState, exclusive_lock

    # Registered on the command's context, which releases it however the command ends — including the abort below.
    if not ctx.with_resource(exclusive_lock(CollabState.get_workdir(profile) / 'sync.lock', blocking=False)):
        echo.echo_critical('another collab sync of this profile is running: wait for it to finish, then try again.')


def read_stash_meta(filepath, filepath_meta):
    """Return what a stashed push describes, or ``None`` when there is nothing usable to describe it.

    The description is written whole beside the archive it describes, so one that will not parse means the run
    that wrote it died mid-write or the disk filled. Unhandled, that ``JSONDecodeError`` escapes every handler
    this command has and kills every future push to every peer until somebody deletes the file by hand.
    Discarding the pair instead costs one renegotiation and re-transfer, which is what a push without a stash
    does anyway.
    """
    import json

    if not filepath_meta.exists():
        return None

    try:
        return json.loads(filepath_meta.read_text(encoding='utf-8'))
    except ValueError:
        echo.echo_warning(f'discarding the unreadable stash at {filepath_meta}: the push is negotiated afresh.')
        filepath_meta.unlink(missing_ok=True)
        filepath.unlink(missing_ok=True)

        return None


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
        echo.echo_critical('this collab has no peers yet: hand out a join code, or join with `verdi collab join`.')

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


def restart_endpoint(profile):
    """Restart the collab endpoint of a running daemon, and report whether it now runs what was just written.

    The endpoint reads the address it binds and whether it serves at all once, at start, so a change to either
    only reaches the process this way. Only that watcher is touched: the workers of the daemon keep running,
    which is the whole difference between this and `verdi daemon restart`.

    Every way of failing is a warning and ``False``, never an abort. What the caller has already written stands
    either way, and a caller that also announces has to go on and announce: a restart that failed is repaired by
    the next daemon start, while an announcement that was skipped is never made again — the address it would
    have carried is by then the address this profile is already configured for, so a re-run finds nothing to do.
    """
    from aiida.engine.daemon.client import DaemonClient, DaemonException

    client = DaemonClient(profile)

    # A PID file and nothing more, so a daemon that was killed passes this and fails in the call below.
    if not client.is_daemon_running:
        return False

    watcher = f'{client.daemon_name}-collab-endpoint'

    try:
        response = client.call_client({'command': 'restart', 'properties': {'name': watcher, 'waiting': True}})
    except DaemonException as exception:
        echo.echo_warning(f'could not restart the collab endpoint: {exception}')
        return False

    # circus answers a command naming a watcher it does not have rather than raising, and the daemon of a
    # profile whose `collab.enabled` was off when it started has no endpoint watcher at all.
    if response.get('status') != 'ok':
        echo.echo_warning(
            f'could not restart the collab endpoint: {response.get("reason", response)}. The watcher list is '
            'built when the daemon starts, so `verdi daemon restart` is what puts an endpoint in it.'
        )
        return False

    return True


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


ACCEPT_PUSH = options.OverridableOption(
    '--accept-push/--no-accept-push',
    default=None,
    help='Whether peers of the collab may push provenance into this profile. Asked for when neither is given, and '
    'refused under `--non-interactive`.',
)

BIND = options.OverridableOption(
    '--bind',
    metavar='ADDRESS',
    help="This machine's address on the private network of the collab, on which its endpoint listens. Prompted for "
    'when not given.',
)

PORT = options.OverridableOption(
    '--port',
    type=int,
    help='Port on which the endpoint of this profile listens. A free one is picked when not given.',
)


def choose_accept_push(accept_push, non_interactive):
    """Return whether peers of the collab may push into this profile, asked for unless an option settles it.

    Consent to being written to belongs beside the other consents of the setup. Until it was asked here it was
    reachable only through `verdi config set`, so a member that wanted to be pushed to learned of it from the
    documentation or from a peer's report that it had been refused.
    """
    if accept_push is None and not non_interactive:
        return click.confirm('accept pushes from peers into this profile?', default=False)

    accept_push = bool(accept_push)
    # Reported whenever it was not asked for, so that a flag -- or `--non-interactive` with neither flag -- does
    # not settle in silence who may write into this profile.
    echo.echo_report(f'pushes from peers into this profile are {"accepted" if accept_push else "refused"}.')

    return accept_push


def start_serving(config, profile, url):
    """Start the daemon that serves this profile's collab endpoint, and return whether it is being served.

    A daemon that is already running is stopped and started rather than left alone.

    The endpoint is a circus watcher, and the list of watchers is built once — by ``_create_watchers``, from
    ``collab.enabled``, when the arbiter starts. A daemon that was already up when the collab was created
    therefore supervises everything except the endpoint, and circus's own `restart` cannot add it: it restarts the
    watchers the arbiter already has. Stopping and starting is what rebuilds the list, which is why
    `verdi daemon restart` is a stop and a start too.
    """
    from aiida.common.exceptions import ConfigurationError
    from aiida.engine.daemon.client import DaemonException, DaemonNotRunningException, get_daemon_client

    client = get_daemon_client(profile.name)
    restarted = False

    try:
        if client.is_daemon_running:
            try:
                client.stop_daemon(wait=True)
                restarted = True
            except DaemonNotRunningException:
                # `is_daemon_running` reads the pid file, which outlives a daemon that a reboot or the OOM killer
                # took: stopping one that is already down is the work this asked for, done. Stopping it is also
                # what deleted the stale file, so the start below is now the start of a daemon, not a restart.
                pass

        client.start_daemon(number_workers=config.get_option('daemon.default_workers', scope=profile.name))
    except (DaemonException, ConfigurationError) as exception:
        # The profile is a member of the collab either way, and a daemon is one command away. Aborting here would
        # report a failure for a setup that succeeded, and invite a retry that the collab it just joined refuses.
        # The command named is the one that works from where this leaves the daemon -- `verdi daemon restart`
        # refuses to run on a daemon that is down, which is what a stop followed by a failed start leaves.
        command = 'restart' if client.is_daemon_running else 'start'
        echo.echo_warning(
            f'the collab is set up, but the daemon of profile `{profile.name}` could not be brought up: '
            f'{exception}\nNothing serves {url} until `verdi -p {profile.name} daemon {command}` succeeds.'
        )

        return False

    echo.echo_report(
        f'{"restarted" if restarted else "started"} the daemon of profile `{profile.name}`, which serves {url}.'
    )

    return True


def set_up_collab(ctx, *, profile, profile_name, policy, joining, bind, port, accept_push, non_interactive):
    """Take the consent to be pushed to, reserve an address, write the collab options and serve them.

    Everything `init` and `join` do alike, in the order they do it -- with the profile a join creates, and the
    announcement that enters it into the collab, threaded through in the two places they belong.

    :param profile: the profile the collab is founded on, or ``None`` for a join, which creates ``profile_name``
        here -- after the address, so that a refusal or a typo never leaves a half-made profile behind.
    :param joining: the decoded join code, or ``None`` when a collab is being founded rather than joined.
    """
    import secrets
    import uuid

    from aiida.tools.collab import config as collab_config

    config = ctx.obj.config
    accept_push = choose_accept_push(accept_push, non_interactive)

    # Everything that can still be refused happens before the profile exists: an address that is not this
    # machine's, or a mistyped one, would otherwise abort with a fresh profile left behind and the retry
    # refusing to reuse its name.
    scope = profile.name if profile else None
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
        collab_config.OPTION_POLICY: policy,
        collab_config.OPTION_ACCEPT_PUSH: accept_push,
    }

    # The configuration file is shared by every profile, so any collab endpoint running on this machine is a
    # second writer of it: what is written here goes onto the file as it is now, and into the copy this process
    # holds so that the rest of the command reads what it just wrote.
    with collab_config.mutate_config(config) as stored:
        for option_name, value in values.items():
            for target in (stored, config):
                target.set_option(option_name, value, scope=profile.name)

    # Before the daemon rather than after it: a join that cannot reach its issuer deletes the profile it made,
    # and deleting a profile stops a daemon this command would otherwise have started a moment earlier.
    if joining:
        join_collab(config, profile, joining)

    served = start_serving(config, profile, url)

    echo.echo_success(
        f'profile `{profile.name}` serves the collab at {url}.'
        if served
        else f'profile `{profile.name}` is part of the collab, to be served at {url}.'
    )
    echo.echo_report(
        f'Run `verdi collab link` for the code that lets others join, and `verdi -p {profile.name} config set '
        f'{collab_config.OPTION_ACCEPT_PUSH} <bool>` to change whether peers may push into this profile.'
    )


@verdi_collab.command('init')
@BIND()
@PORT()
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
@ACCEPT_PUSH()
@options.NON_INTERACTIVE()
@click.pass_context
def collab_init(ctx, bind, port, extras_mode, groups_mode, accept_push, non_interactive):
    """Create a collab on the loaded profile.

    Peers of a collab share one logical provenance graph: each of them can pull the sealed provenance of the others and
    push their own. Both are additive, deletions are never propagated.
    """
    from aiida.tools.collab import config as collab_config

    config = ctx.obj.config
    profile = ctx.obj.profile

    if profile is None:
        echo.echo_critical(
            'no profile loaded: create one with `verdi presto`, or join a collab with `verdi collab join`.'
        )

    # Guarded on the collab's identity rather than on `collab.enabled`, because leaving a collab is defined as
    # turning that option off: the member keeps its uuid, token, roster and cursors and comes back by turning
    # it on again. Founding over them would overwrite all four, and nothing prints the old token a second
    # time — the membership would be gone with no way back, since a join only ever creates a new profile.
    if config.get_option(collab_config.OPTION_UUID, scope=profile.name):
        echo.echo_critical(
            f'profile `{profile.name}` already belongs to a collab. Each profile can only take part in one: '
            f'rejoin this one with `verdi config set {collab_config.OPTION_ENABLED} True` and a daemon '
            'restart, or found a new collab on a fresh profile.'
        )

    set_up_collab(
        ctx,
        profile=profile,
        profile_name=None,
        policy=choose_policy(extras_mode, groups_mode, non_interactive),
        joining=None,
        bind=bind,
        port=port,
        accept_push=accept_push,
        non_interactive=non_interactive,
    )


@verdi_collab.command('join')
@click.argument('code', metavar='CODE')
@click.option(
    '-p',
    '--profile-name',
    help='Name of the profile to create for the collab. Prompted for when not given, and `collab` under '
    '`--non-interactive`.',
)
@BIND()
@PORT()
@ACCEPT_PUSH()
@options.NON_INTERACTIVE()
@click.pass_context
def collab_join(ctx, code, profile_name, bind, port, accept_push, non_interactive):
    """Join the collab a code was minted for, in a new profile.

    The code is what `verdi collab link` prints on any member, and it carries the terms the collab runs on: what
    it shares beyond provenance nodes was fixed when the collab was created and cannot be chosen here. Joining
    always creates a fresh profile: a collab shares one logical provenance graph, and folding the work you already
    have into someone else's is not what anyone asks for by pasting a join code.
    """
    from aiida.tools.collab.protocol import JoinCode

    config = ctx.obj.config

    try:
        joining = JoinCode.decode(code)
    except ValueError as exception:
        echo.echo_critical(str(exception))

    if not profile_name:
        profile_name = 'collab' if non_interactive else click.prompt('name of the profile to create', default='collab')

    if profile_name in config.profile_names:
        echo.echo_critical(f'profile `{profile_name}` already exists: joining a collab creates a new profile.')

    set_up_collab(
        ctx,
        profile=None,
        profile_name=profile_name,
        policy=accept_policy(joining.policy, non_interactive),
        joining=joining,
        bind=bind,
        port=port,
        accept_push=accept_push,
        non_interactive=non_interactive,
    )


def announce(config, profile, *, url, token, collab, timeout=None):
    """Announce this profile to the member serving ``url`` and merge the roster it answers with.

    The one contact a join code buys — it tells the issuer that this profile holds the token, which is what
    admits a newcomer and what recognizes a member returning after a rotation — and equally what a profile that
    just moved sends to every peer it holds, so that the new address does not wait for the next sync. Merged into
    the roster as it is on the file, so a returning member keeps its nicknames and the standing of everyone else.

    :param url: the endpoint to announce to, of a code's issuer or of a peer already in the roster.
    :param timeout: how long to wait for that peer, defaulting to the client's own. A loop over every peer passes
        the short one: nothing depends on the announcement arriving, since gossip carries it anyway.
    :raises CollabRequestError: when the peer cannot be reached or refuses the token.
    """
    from aiida.tools.collab.client import TIMEOUT, CollabClient
    from aiida.tools.collab.config import OPTION_PEERS, merge_roster, mutate_config, self_entry

    # Stamped like any outbound contact: a member that moved while it was dormant announces the address it is at
    # now, and only a raised stamp makes the issuer take it over the one it has held all along. In a transaction
    # of its own, since what follows it is a network round trip: no lock on the configuration file is worth
    # holding for the time a peer takes to answer.
    with mutate_config(config) as stored:
        announcement = self_entry(stored, profile, bump=True)

    with CollabClient(url, token, collab=collab, timeout=TIMEOUT if timeout is None else timeout) as client:
        response = client.join(announcement)

    with mutate_config(config) as stored:
        merged, reports = merge_roster(
            stored.get_option(OPTION_PEERS, scope=profile.name), response.roster, profile.uuid
        )

        # The peer just answered at that URL, so it is the one entry of the roster this profile has proof of.
        for entry in merged.values():
            if entry['url'] == url:
                entry['seen'] = True

        for target in (stored, config):
            target.set_option(OPTION_PEERS, merged, scope=profile.name)

    for report in reports:
        echo.echo_report(report)


def join_collab(config, profile, code):
    """Announce this profile to the member that issued the join code and adopt the roster it answers with.

    An announcement that never arrives takes the profile with it, storage and collab state included. The alternative
    is what this used to leave behind: a profile that is set up for a collab it is not in, which the retry then
    refuses to reuse the name of, so that recovering from an issuer being briefly offline is a manual deletion.
    """
    from aiida.tools.collab.config import mutate_config
    from aiida.tools.collab.protocol import CollabRequestError

    try:
        announce(config, profile, url=code.url, token=code.token, collab=code.collab)
    except CollabRequestError as exception:
        # Deleted against the file as it is now, not against the copy this process loaded before the announcement:
        # `Config.store` writes its holder's whole dictionary, so a delete off the stale copy silently reverts
        # whatever another collab writer on this machine put in the file while the issuer was answering.
        with mutate_config(config) as stored:
            stored.delete_profile(profile.name, delete_storage=True)
        echo.echo_critical(
            f'could not join through {code.url}: {exception}\nProfile `{profile.name}` was deleted again and '
            'nothing was left behind; run `verdi collab join` again with a code from a member that is online.'
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


@verdi_collab.command('link')
@requires_loaded_profile()
@click.pass_context
def collab_link(ctx):
    """Print the code that admits a newcomer to this collab.

    Any member can hand one out: once the collab exists its creator is nobody special, so a newcomer joins through
    whoever happens to be online, and a member that has to rekey after a rotation obtains a fresh code the same way.

    The code carries the token every request of the collab is authenticated with, which is why asking for it is a
    command of its own rather than a line of `verdi status`. Hand it over out of band, person to person.
    """
    from aiida.tools.collab.config import join_code

    profile = ctx.obj.profile
    require_collab(profile)

    echo.echo(join_code(ctx.obj.config, profile))


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

    CODE is a fresh join code of the same collab, as `verdi collab link` prints it on a member that already holds the
    new token. Peers, cursors and history are kept: this profile announces itself to the member whose code it is, and
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

        # Every member prints a code of its own, this profile included, and rekeying with that one is the one case
        # that cannot work: this profile is the only member its own endpoint can teach nothing, so it would rest
        # its whole roster dormant and reactivate none of it.
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
        announce(ctx.obj.config, profile, url=rekeyed.url, token=rekeyed.token, collab=rekeyed.collab)
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
    """Treat calculations that ran on a peer computer as if they ran on a local one, so they can be cache hits.

    Each mapping maps the label of a peer computer to the label of a local one, as PEER=LOCAL; pass several to map
    several computers. A computer that arrived through the collab is labelled `<label>@collab`, which is the name
    to map from, and `verdi computer list` shows them. Both halves have to be computers this profile holds, so a
    mapping is declared after the machine has arrived here, never before: the mapping is applied to the
    calculations already pulled as well, so waiting loses nothing.

    New mappings are merged into the existing ones. To remove mappings, run `verdi config unset
    collab.computer_map` and declare the remaining ones again. Restart the daemon for pushes received by the
    endpoint to pick up the change.
    """
    from aiida.common.exceptions import ConfigurationError
    from aiida.manage import get_manager
    from aiida.tools.collab.config import OPTION_COMPUTER_MAP, mutate_config
    from aiida.tools.collab.sync import apply_computer_map

    profile = ctx.obj.profile
    require_collab(profile)

    declared = parse_computer_map(mappings)
    mapping = dict(ctx.obj.config.get_option(OPTION_COMPUTER_MAP, scope=profile.name))
    mapping.update(declared)

    try:
        count = apply_computer_map(get_manager().get_profile_storage(), mapping)
    except ConfigurationError as exception:
        echo.echo_critical(str(exception))

    with mutate_config(ctx.obj.config) as stored:
        for target in (stored, ctx.obj.config):
            target.set_option(OPTION_COMPUTER_MAP, mapping, scope=profile.name)

    mapped = ', '.join(f'`{peer_label}` → `{local_label}`' for peer_label, local_label in sorted(declared.items()))

    if count:
        echo.echo_success(f'mapped {mapped}; {count} calculation(s) now carry the hash of their local twin.')
    else:
        echo.echo_success(
            f'mapped {mapped}; no calculation here ran on those computers, so nothing was rewritten — the mapping '
            'applies to whatever arrives from now on.'
        )


@verdi_collab.command('config')
@click.option(
    '--accept-push/--no-accept-push',
    default=None,
    help='Whether the peers of the collab may push their provenance into this profile. The endpoint reads this '
    'per request, so it holds from the next one on.',
)
@click.option(
    '--bind',
    metavar='ADDRESS',
    help="This machine's address on the private network of the collab, on which its endpoint listens.",
)
@click.option(
    '--port',
    type=click.IntRange(0, 65535),
    help='Port on which the endpoint of this profile listens.',
)
@options.NON_INTERACTIVE()
@requires_loaded_profile()
@click.pass_context
def collab_config(ctx, accept_push, bind, port, non_interactive):
    """Change what this profile serves to its peers: consent to pushes, and the address it is reached at.

    Called with no option it asks for all three, offering what is configured now; with options it sets those and
    asks nothing. A changed address is validated by binding it, so one that is not this machine's is refused
    before anything is written; the endpoint of a running daemon is then restarted onto it and every peer that
    answers is told at once, so that nobody has to wait for a sync to find this profile again.
    """
    from aiida.tools.collab.config import (
        OPTION_ACCEPT_PUSH,
        OPTION_BIND,
        OPTION_PEERS,
        OPTION_PORT,
        OPTION_TOKEN,
        OPTION_UUID,
        endpoint_url,
        mutate_config,
    )
    from aiida.tools.collab.protocol import CollabRequestError

    config = ctx.obj.config
    profile = ctx.obj.profile
    require_collab(profile)

    scope = profile.name
    served = config.get_option(OPTION_BIND, scope=scope), config.get_option(OPTION_PORT, scope=scope)
    accepts = config.get_option(OPTION_ACCEPT_PUSH, scope=scope)

    if accept_push is None and bind is None and port is None:
        if non_interactive:
            echo.echo(f'pushes from peers: {"accepted" if accepts else "refused"}')
            # The address is reported apart from the consent, each being a setting of its own.
            echo.echo(f'address: {endpoint_url(*served)}')
            return

        accept_push = click.confirm('accept pushes from the peers of this collab?', default=accepts)
        bind = click.prompt("this machine's address on the private network of the collab", default=served[0])
        port = click.prompt(
            'port on which the endpoint of this profile listens', default=served[1], type=click.IntRange(0, 65535)
        )

    address = (served[0] if bind is None else bind, served[1] if port is None else port)
    moved = address != served

    # Skipped when nothing moved, because the endpoint of this very profile is holding that socket: the test-bind
    # that validates a new address would refuse the one already in use by the thing being reconfigured.
    if moved:
        address = (address[0], reserve_port(address[0], address[1], address[1]))

    # Written only when it moved: these were read before the lock, so a consent-only run that wrote them back
    # would revert an address change another terminal made in between.
    values = {OPTION_BIND: address[0], OPTION_PORT: address[1]} if moved else {}

    if accept_push is not None:
        values[OPTION_ACCEPT_PUSH] = accept_push

    with mutate_config(config) as stored:
        for option_name, value in values.items():
            for target in (stored, config):
                target.set_option(option_name, value, scope=scope)

        active = [entry for entry in stored.get_option(OPTION_PEERS, scope=scope).values() if entry['active']]
        token = stored.get_option(OPTION_TOKEN, scope=scope)
        collab = stored.get_option(OPTION_UUID, scope=scope)

    if accept_push is not None:
        consent = 'accepted' if accept_push else 'refused'
        echo.echo_success(f'pushes from peers are {consent} from their next request on.')

    url = endpoint_url(*address)

    if not moved:
        echo.echo_report(f'the address is unchanged: this profile is configured for {url}.')
        return

    # The restart precedes the line that says what happened, so that a failure to restart reads as its reason.
    if restart_endpoint(profile):
        echo.echo_success(f'profile `{profile.name}` serves the collab at {url}.')
    else:
        echo.echo_success(f'profile `{profile.name}` serves the collab at {url} once its daemon starts it there.')

    # Announced now rather than at the next sync, because until a peer holds the new address it cannot reach this
    # profile at all, and a member that only ever pulls would never announce. Short-timeout like the advisory
    # signal of a rotation: whoever does not answer learns it from gossip, as every address change did before.
    reached = []

    for entry in active:
        try:
            announce(config, profile, url=entry['url'], token=token, collab=collab, timeout=SIGNAL_TIMEOUT)
        except CollabRequestError as exception:
            echo.echo_warning(f'could not tell {entry["nickname"]} about the new address: {exception}')
        else:
            reached.append(entry['nickname'])

    if reached:
        echo.echo_report(f'announced to {", ".join(reached)}.')

    if len(reached) != len(active):
        echo.echo_report('the peers that did not answer learn the new address from gossip at their next sync.')


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


def negotiate_pull(client, *, backend, state, cursor, claim, policy, include_deleted, roster):
    """Negotiate the delta of a peer and diff its manifest, returning everything that decision is made of.

    The manifest names what the delta holds; only the nodes this profile lacks are then requested, so already-held
    ancestors never travel. Returned together with the manifest because they are one reading of one computation:
    a peer that can no longer serve it invalidates the want, the refusal, the extras and the memberships at once.

    :param roster: what this profile gossips, which travels with the negotiation — how membership spreads and a
        corrected address heals.
    :return: the manifest, the nodes to ask for, the ones refused, the extras to take and the memberships to add.
    """
    from aiida.tools.collab.sync import members_wanted, missing_uuids, refresh_wanted

    manifest = client.negotiate_delta(cursor, claim, roster)
    missing = set(missing_uuids(backend, manifest.manifest))

    # A node this profile deleted is missing too, and is refused rather than asked for: that is where a deletion
    # is defended, bounded by the delta instead of by every deletion ever made. Only what is missing may be
    # refused — a node held *and* tombstoned, which a restoration leaves behind, is one the sender must keep
    # linking to. `--include-deleted` refuses nothing; that is what it means.
    refuse = set() if include_deleted else missing & state.tombstones

    return (
        manifest,
        missing - refuse,
        refuse,
        # Extras of shared nodes the peer edited more recently, and memberships of nodes this profile already
        # holds; both empty unless the collab shares them. Asked for under the local policy, not the peer's
        # offer, so that what is prompted for is what the import will write.
        refresh_wanted(backend, manifest.refresh) if policy['extras_mode'] == 'sync' else [],
        members_wanted(backend, manifest.members) if policy['groups_mode'] == 'grow' else [],
    )


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
    confirmed with the node count it asked for and its size before any payload travels.
    """
    from contextlib import nullcontext
    from functools import partial
    from http import HTTPStatus

    from aiida.common.exceptions import ConfigurationError, IntegrityError
    from aiida.engine.daemon.client import get_daemon_client
    from aiida.manage import get_manager
    from aiida.tools.collab.client import CollabClient
    from aiida.tools.collab.config import OPTION_COMPUTER_MAP, OPTION_PEERS, OPTION_POLICY, OPTION_TOKEN, OPTION_UUID
    from aiida.tools.collab.endpoint import local_identity, local_info, workers_stopped
    from aiida.tools.collab.protocol import CollabRequestError, VersionSkew, member_pairs
    from aiida.tools.collab.state import CollabState, import_lock
    from aiida.tools.collab.sync import import_delta, resolve_computer_map

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
    hold_the_sync_lock(ctx, profile)

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
            # otherwise never re-enter the delta. It then also has to drop the tombstoned nodes from the claim —
            # they sit in the import events, and a claimed node is never offered.
            cursor = None if include_deleted else state.cursors.get(peer_uuid)

            claim = state.imported_uuids_since(cursor)

            if include_deleted:
                claim = claim - state.tombstones

            # Bound once, because a renegotiation is the same negotiation over again: what it may not vary is the
            # cursor and the claim, which the export request presents beside the want they were diffed with.
            negotiate = partial(
                negotiate_pull,
                client,
                backend=backend,
                state=state,
                cursor=cursor,
                claim=claim,
                policy=policy,
                include_deleted=include_deleted,
                roster=gossip(ctx.obj.config, profile, bump=not dry_run),
            )

            try:
                manifest, want, refuse, refresh_want, members = negotiate()
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

                try:
                    offer = client.request_delta(cursor, claim, want, refresh_want, refuse, manifest.computed)
                except CollabRequestError as exception:
                    if exception.status != HTTPStatus.CONFLICT:
                        raise

                    # The peer cannot serve the computation this want was diffed against — it sealed something, or
                    # deleted a node of the manifest. One retry and no more: a peer sealing between every
                    # negotiation and request can refuse again, and that is a report, not something to spin on.
                    echo.echo_report(f'{nickname} asked to renegotiate: {exception}')
                    manifest, want, refuse, refresh_want, members = negotiate()
                    curated = len(member_pairs(members))
                    offer = client.request_delta(cursor, claim, want, refresh_want, refuse, manifest.computed)

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
                # Re-read under the lock, as the endpoint does. The copy above describes the moment the cursor and
                # the claim were computed at and has to; but a handshake, a negotiation and a download have run
                # since, and a `verdi node delete` in that window would be undone by an import honouring the
                # tombstones of before it.
                fresh = CollabState.read(state.filepath)

                with workers_stopped(profile) if pause else nullcontext():
                    report = import_delta(
                        filepath,
                        state=fresh,
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

    PEER is the nickname of a peer of the collab; without any, every peer that accepts pushes is pushed to. A
    transfer that carries anything is confirmed with its exact node count and size before any payload travels.
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
        required_refused,
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
    hold_the_sync_lock(ctx, profile)

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

                meta = read_stash_meta(filepath, filepath_meta)

                if filepath.exists() and meta is not None and meta['peer'] == peer_uuid:
                    # A previous push to this peer failed after the transfer. Retrying with the very same bytes
                    # is what lets the upload negotiate that everything is already staged and re-attempt only
                    # the import; the original instant travels with them, since it is what describes those bytes.
                    uuids, instant = meta['uuids'], datetime.fromisoformat(meta['instant'])
                    state = CollabState.load(profile)

                    # The extras and the memberships are negotiated again, though the bytes are not: the import
                    # advances the peer's cursor to the stashed instant — past every journal entry older than it,
                    # and past the mtime of every extras edit the failed push had already offered — so a retry
                    # that carried neither would lose what it had negotiated for good.
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
                    diff = client.diff_manifest([], offer, curations)
                    curated = len(member_pairs(diff.members))

                    if dry_run:
                        summary = f'{nickname}: {len(uuids)} node(s) to push (stashed retry)'

                        if diff.refresh:
                            summary += f', extras of {len(diff.refresh)} node(s) to be replaced by yours'

                        if curated:
                            summary += f', {curated} group membership(s) to add there'

                        echo.echo_report(summary)
                        # The handshake took a serving slot of the peer and is over: without this the peer would
                        # answer everybody else busy until the slot expired, for a command that sent nothing.
                        client.release()
                        continue

                    refresh = refresh_snapshots(backend, diff.refresh)
                    members = diff.members

                    echo.echo_report(f'retrying the delta of the previous failed push to {nickname}')
                else:
                    # The delta is offered to the peer as a manifest first — with the mtimes of the extras this
                    # profile edited, when the collab syncs them — so that only what the peer lacks travels.
                    delta = compute_delta(
                        state=CollabState.load(profile),
                        backend=backend,
                        cursor=handshake.cursor,
                        claim=frozenset(handshake.claim),
                    )

                    # Re-read now that the export instant the receiver's cursor will advance to has been taken:
                    # an offer computed from an older state omits whatever another process journalled in between,
                    # and what is omitted ends up behind that cursor for good. Over-stating is safe — the manifest
                    # diff and the mtime comparison drop what the receiver already holds.
                    state = CollabState.load(profile)
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
                    refuse = set(diff.refuse)

                    # A refused node the wanted provenance requires travels anyway: the receiver's own import
                    # closes over it regardless, so leaving it out would only make the archive link to a node
                    # that exists nowhere. One that is *not* required is cut out with its links instead, or the
                    # receiver would refuse the whole delta over a boundary endpoint it cannot resolve.
                    want = set(diff.missing)
                    want |= required_refused(delta=delta, backend=backend, want=want, refuse=refuse)
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
                        filepath,
                        delta=delta,
                        backend=backend,
                        want=want,
                        refuse=refuse,
                        groups_mode=policy['groups_mode'],
                    )
                    refresh = refresh_snapshots(backend, diff.refresh)
                    members = diff.members
                    uuids, instant = export.uuids, export.instant
                    filepath_meta.write_text(
                        json.dumps({'peer': peer_uuid, 'instant': instant.isoformat(), 'uuids': uuids}, indent=4),
                        encoding='utf-8',
                    )

                # Only an import writes the receiver's cursor — that is what the cursor means — so a peer that
                # holds none is pushed the empty delta anyway, once: without it the pusher presents a null cursor
                # forever and an extras-only change has no route to it at all.
                if handshake.cursor is not None and not uuids and not refresh and not members:
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

                # Nothing to ask about when nothing travels: the empty delta that sets a first cursor writes no
                # provenance, no extras and no membership. Mirrors the pull's own guard.
                if (uuids or refresh or members) and not force:
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
