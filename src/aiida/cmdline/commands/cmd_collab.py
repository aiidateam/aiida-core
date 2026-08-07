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


@verdi.group('collab')
def verdi_collab():
    """Share provenance with the peers of a collab."""


def require_collab(profile):
    """Abort unless the loaded profile takes part in a collab."""
    from aiida.tools.collab.config import is_enabled

    if not is_enabled():
        echo.echo_critical(f'profile `{profile.name}` is not part of a collab: run `verdi collab init` first.')


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
def collab_init(ctx, code, profile_name, bind, port, extras_mode, groups_mode, non_interactive):
    """Set up a profile as part of a collab.

    Peers of a collab share one logical provenance graph: each of them can pull the sealed provenance of the others and
    push their own. Both are additive, deletions are never propagated.
    """
    import secrets
    import uuid

    from aiida.tools.collab import config as collab_config
    from aiida.tools.collab.protocol import JoinCode

    config = ctx.obj.config
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
        collab_config.OPTION_POLICY: policy,
    }

    # The configuration file is shared by every profile, so any collab endpoint running on this machine is a
    # second writer of it: what is written here goes onto the file as it is now, and into the copy this process
    # holds so that the rest of the command reads what it just wrote.
    stored = collab_config.stored_config(config)

    for option_name, value in values.items():
        for target in (stored, config):
            target.set_option(option_name, value, scope=profile.name)

    stored.store()

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
    from aiida.tools.collab.config import OPTION_PEERS, merge_roster, self_entry, stored_config

    with CollabClient(code.url, code.token, collab=code.collab) as client:
        # Stamped like any outbound contact: a member that moved announces the address it is at now, and only a
        # raised stamp makes the issuer take it over the one it has held all along.
        response = client.join(self_entry(config, profile))

    stored = stored_config(config)
    merged, reports = merge_roster(stored.get_option(OPTION_PEERS, scope=profile.name), response.roster, profile.uuid)

    # The issuer just answered at that URL, so it is the one entry of the roster this profile has proof of.
    for entry in merged.values():
        if entry['url'] == code.url:
            entry['seen'] = True

    for target in (stored, config):
        target.set_option(OPTION_PEERS, merged, scope=profile.name)

    stored.store()

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
