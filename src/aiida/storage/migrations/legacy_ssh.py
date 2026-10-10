###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Conversion of the computers configured with the legacy ``core.ssh`` (paramiko) transport plugin.

That plugin kept every connection detail in the ``auth_params`` of each computer and never read
``~/.ssh/config``; the asynchronous plugin that took over its name connects to a host defined in a
client configuration. The ``main_0003`` revision of the ``psql_dos`` and ``sqlite_dos`` backends
therefore renders those parameters as an entry in :data:`CONFIG_NAME`, included from the top of
``~/.ssh/config``, and replaces them with the alias of that entry.
"""

import itertools
import json
import typing as t
from collections import Counter
from pathlib import Path

from sqlalchemy.engine import Connection
from sqlalchemy.sql import text

from aiida.storage.log import MIGRATE_LOGGER

#: The ``auth_params`` of a computer configured with the legacy ``core.ssh`` plugin.
LEGACY_PARAM_NAMES: t.Final = (
    'username',
    'port',
    'look_for_keys',
    'key_filename',
    'timeout',
    'allow_agent',
    'proxy_jump',
    'proxy_command',
    'compress',
    'gss_auth',
    'gss_kex',
    'gss_deleg_creds',
    'gss_host',
    'load_system_host_keys',
    'key_policy',
)

#: Holds the entries, next to ``~/.ssh/config`` and included from it.
CONFIG_NAME: t.Final = 'aiida-migrated-configs'

#: Names the host each entry defines.
HOST_PREFIX: t.Final = 'aiida-migrated-'


def ssh_dir() -> Path:
    """Return the directory the client configuration lives in."""
    return Path.home() / '.ssh'


def read_config() -> str:
    """Return the entries written by the migrations that ran on this machine before."""
    path = ssh_dir() / CONFIG_NAME
    return path.read_text(encoding='utf8') if path.is_file() else ''


def alias(uuid: str, user_id: int | None = None) -> str:
    """Return the ``Host`` name to define for a computer, per user where several configured it."""
    suffix = '' if user_id is None else f'-user{user_id}'
    return f'{HOST_PREFIX}{uuid}{suffix}'


def _checked(value: str) -> str:
    """Return a value that is safe to write as part of a directive.

    A line break would end the directive and turn the rest of the value into one of its own. Since
    the file is read before anything else the user has, a directive no client understands would
    break every connection they make, not only the ones AiiDA makes.
    """
    if '\n' in value or '\r' in value:
        msg = f'cannot write an `ssh_config` entry for `{value!r}`: the value contains a line break'
        raise ValueError(msg)

    return value


def _quote(value: str) -> str:
    """Quote a value that contains whitespace, which ``ssh_config`` would otherwise split."""
    checked = _checked(value)
    return f'"{checked}"' if any(character.isspace() for character in checked) else checked


def _yes_no(flag: t.Any) -> str:
    return 'yes' if flag else 'no'


def _render_host_key_policy(params: dict[str, t.Any]) -> list[str]:
    """Return the host key directives reproducing ``key_policy`` and ``load_system_host_keys``."""
    # `AutoAddPolicy` and `WarningPolicy` accepted an unknown host but still refused a *changed*
    # key, which `no` accepts too. Telling the two apart needs a validation hook of our own, and is
    # not worth it for a policy chosen to stop being asked. The migration reports this.
    permissive = params.get('key_policy', 'RejectPolicy') != 'RejectPolicy'
    directives = [f'StrictHostKeyChecking {_yes_no(not permissive)}']

    if params.get('load_system_host_keys') is False:
        # No host keys were loaded at all, so no host was ever known.
        directives.append('UserKnownHostsFile /dev/null')
        directives.append('GlobalKnownHostsFile /dev/null')

    return directives


def render_stanza(host: str, hostname: str, params: dict[str, t.Any]) -> str:
    """Render the connection parameters of a legacy computer as an ``ssh_config`` entry.

    Every parameter is pinned, including the ones that were switched off, so that a ``Host *`` entry
    of the user cannot change how a migrated computer connects.
    """
    directives = [f'Hostname {_quote(hostname)}']

    if username := params.get('username'):
        directives.append(f'User {_quote(str(username))}')
    if (port := params.get('port')) not in (None, ''):
        directives.append(f'Port {int(port)}')
    if (timeout := params.get('timeout')) not in (None, ''):
        directives.append(f'ConnectTimeout {int(timeout)}')

    if key_filename := params.get('key_filename'):
        directives.append(f'IdentityFile {_quote(str(key_filename))}')
        if params.get('look_for_keys') is False:
            directives.append('IdentitiesOnly yes')
    elif params.get('look_for_keys') is False:
        # `IdentitiesOnly` alone would not do it: with no `IdentityFile` to restrict them to, a
        # client still offers the default `~/.ssh/id_*`. `none` is what empties that list.
        directives.append('IdentityFile none')
    if params.get('allow_agent') is False:
        directives.append('IdentityAgent none')

    directives.append(f'Compression {_yes_no(params.get("compress"))}')

    if proxy_jump := params.get('proxy_jump'):
        directives.append(f'ProxyJump {_checked(str(proxy_jump))}')
    if proxy_command := params.get('proxy_command'):
        # Taken as the rest of the line by every client, which also expand its `%h`/`%p` tokens.
        directives.append(f'ProxyCommand {_checked(str(proxy_command))}')

    directives.append(f'GSSAPIAuthentication {_yes_no(params.get("gss_auth"))}')
    directives.append(f'GSSAPIDelegateCredentials {_yes_no(params.get("gss_deleg_creds"))}')
    # Both come from the GSSAPI key exchange patch Debian and Red Hat apply, and are unknown to the
    # stock client macOS and the BSDs ship, which aborts on a keyword it does not recognise.
    if params.get('gss_kex'):
        directives.append('GSSAPIKeyExchange yes')
    if gss_host := params.get('gss_host'):
        directives.append(f'GSSAPIServerIdentity {_quote(str(gss_host))}')

    directives.extend(_render_host_key_policy(params))

    body = '\n'.join(f'    {directive}' for directive in directives)
    return f'Host {host}\n{body}\n'


def connect_flags(params: dict[str, t.Any]) -> dict[str, t.Any]:
    """Return the ``auth_params`` for the directives ``asyncssh`` has no handler for.

    The ``ssh`` and ``scp`` clients honour all of them natively, so these are read by the
    ``asyncssh`` backend alone.
    """
    flags: dict[str, t.Any] = {}

    if params.get('key_policy', 'RejectPolicy') != 'RejectPolicy':
        flags['known_hosts'] = False
    if params.get('look_for_keys') is False and not params.get('key_filename'):
        flags['client_keys'] = False
    if gss_host := params.get('gss_host'):
        flags['gss_host'] = str(gss_host)

    return flags


def _tokens(line: str) -> list[str]:
    """Return the keyword and arguments of a line, which ``ssh_config`` may separate by ``=``."""
    tokens = line.split()

    if tokens and '=' in tokens[0]:
        keyword, _, argument = tokens[0].partition('=')
        tokens = [keyword, *([argument] if argument else []), *tokens[1:]]

    return tokens or ['']


def defines(content: str, host: str) -> bool:
    """Whether the configuration already has an entry for ``host``."""
    for line in content.splitlines():
        keyword, *patterns = _tokens(line)
        if keyword.lower() == 'host' and host in patterns:
            return True

    return False


def _write(path: Path, content: str, mode: int) -> None:
    """Replace a file through a temporary one, so that an interrupted write cannot lose it."""
    temporary = path.with_name(f'{path.name}.aiida-migration')

    try:
        temporary.write_text(content, encoding='utf8')
        temporary.chmod(mode)
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def write_config(entries: dict[str, str], comments: dict[str, str]) -> Path:
    """Append the entries to :data:`CONFIG_NAME`, and include it from the top of ``~/.ssh/config``.

    Nothing already in the file is rewritten: an entry a migration wrote before is recognised and
    left alone, so what the user has under their own hosts stays exactly as they left it.

    :param entries: the entry of each host, as rendered by :func:`render_stanza`.
    :param comments: the line recording which computer each host belongs to.
    :raises OSError: if the configuration cannot be written, which aborts the migration.
    """
    directory = ssh_dir()
    directory.mkdir(mode=0o700, exist_ok=True)
    path = directory / CONFIG_NAME

    existing = read_config()
    fresh = {host: stanza for host, stanza in entries.items() if stanza not in existing}

    if fresh:
        blocks = [existing.strip('\n')] if existing.strip() else []
        blocks += [f'# {comments[host]}\n{stanza}'.strip('\n') for host, stanza in fresh.items()]

        _write(path, '\n\n'.join(blocks) + '\n', 0o600)

    _include(path.name)

    return path


def _include(name: str) -> None:
    """Prepend the ``Include`` of ``name`` to ``~/.ssh/config``, unless it is already there.

    It goes first because a client takes the first value it obtains for a keyword, so an entry below
    a ``Host *`` of the user would lose every keyword that entry sets.
    """
    path = ssh_dir() / 'config'
    # What a dotfiles repository leaves here is a symlink, and what it points at is what to replace.
    target = path.resolve() if path.is_symlink() else path
    exists = target.is_file()
    content = target.read_text(encoding='utf8') if exists else ''

    for line in content.splitlines():
        keyword, *arguments = _tokens(line)
        if keyword.lower() == 'include' and any(Path(argument).name == name for argument in arguments):
            return

    _write(target, f'Include {name}\n\n{content}', target.stat().st_mode & 0o777 if exists else 0o600)


def _migrate_legacy_ssh_computers(connection: Connection) -> int:
    """Replace the stored connection parameters of every legacy computer with a configuration entry.

    Must run *before* the ``core.ssh_async`` computers are renamed, which is what still tells the two
    kinds of computer apart.

    :return: the number of authentication parameter sets that were converted.
    """
    rows = connection.execute(
        text(
            'SELECT a.id, a.auth_params, c.uuid, c.hostname, c.label, a.aiidauser_id, u.email '
            'FROM db_dbauthinfo AS a JOIN db_dbcomputer AS c ON c.id = a.dbcomputer_id '
            'JOIN db_dbuser AS u ON u.id = a.aiidauser_id '
            "WHERE c.transport_type = 'core.ssh'"
        )
    ).fetchall()

    if not rows:
        return 0

    # ``auth_params`` is a ``JSONB`` column on PostgreSQL, which will not take a string as it stands.
    params_value = 'CAST(:params AS JSONB)' if connection.dialect.name == 'postgresql' else ':params'
    statement = text(f'UPDATE db_dbauthinfo SET auth_params = {params_value} WHERE id = :id')
    entries: dict[str, str] = {}
    comments: dict[str, str] = {}
    permissive = []
    # The parameters are per user and computer both, so one computer can hold a connection of its
    # own for each user that configured it, and each of those needs an entry of its own.
    shared = {uuid for uuid, count in Counter(row[2] for row in rows).items() if count > 1}

    written = read_config()

    for authinfo_id, auth_params, uuid, hostname, label, user_id, email in rows:
        params = json.loads(auth_params) if isinstance(auth_params, str) else auth_params
        name = alias(uuid, user_id if uuid in shared else None)
        host, stanza = name, render_stanza(name, hostname, params)

        # A computer the same UUID names in another profile, or a host the user chose to define
        # themselves, keeps the entry it has; this one is written under a name of its own.
        for suffix in itertools.count(2):
            if stanza in written or not defines(written, host):
                break
            host = f'{name}-{suffix}'
            stanza = render_stanza(host, hostname, params)

        if params.get('key_policy') in ('AutoAddPolicy', 'WarningPolicy'):
            permissive.append(label)

        entries[host] = stanza
        comments[host] = f'computer `{label}` of `{email}`, migrated from the legacy `core.ssh` transport plugin'

        migrated = {key: value for key, value in params.items() if key not in LEGACY_PARAM_NAMES}
        migrated['host'] = host
        migrated['backend'] = 'asyncssh'
        migrated.update(connect_flags(params))

        connection.execute(statement, {'id': authinfo_id, 'params': json.dumps(migrated)})

    # Written before the database is committed, so that a configuration that cannot be written
    # aborts the migration rather than leaving a computer whose parameters have gone nowhere.
    path = write_config(entries, comments)

    MIGRATE_LOGGER.report(
        f'Moved the connection parameters of {len(rows)} computer configuration(s) from the legacy '
        f'`core.ssh` transport plugin into `{path}`, which is now included from `{ssh_dir() / "config"}`. '
        'Please verify each of them with `verdi computer test`.'
    )

    if permissive:
        MIGRATE_LOGGER.warning(
            f'{", ".join(sorted(set(permissive)))}: the `AutoAddPolicy`/`WarningPolicy` host key policy became '
            '`StrictHostKeyChecking no`, which is more permissive than it was. The old policies accepted a host '
            'missing from `known_hosts` but still refused a *changed* key for a known host; this also accepts the '
            f'changed key. Set `StrictHostKeyChecking yes` in `{path}` to tighten it again.'
        )

    return len(rows)


def _rename_ssh_async_transport(connection: Connection) -> None:
    """Rename ``core.ssh_async`` computers to ``core.ssh``."""
    result = connection.execute(
        text("UPDATE db_dbcomputer SET transport_type = 'core.ssh' WHERE transport_type = 'core.ssh_async'")
    )

    if result.rowcount > 0:
        MIGRATE_LOGGER.report(
            f'Renamed the transport of {result.rowcount} computer(s) from `core.ssh_async` to `core.ssh`.'
        )


def migrate_ssh_transports(connection: Connection) -> None:
    """Migrate legacy SSH computers before renaming asynchronous SSH computers."""
    _migrate_legacy_ssh_computers(connection)
    _rename_ssh_async_transport(connection)
