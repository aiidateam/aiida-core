###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Support for computers migrated from the v2, paramiko-based ``core.ssh`` transport plugin.

That plugin kept every connection detail in the ``auth_params`` of each computer and never read
``~/.ssh/config``; the asynchronous plugin that took over its name connects to a host defined in a
client configuration. The storage migration therefore renders those parameters as a configuration
file of its own, one per computer, and records its path as ``ssh_config_file``.

``ssh_config_file`` is stored but never offered as an option: a computer configured today has none
and reads the default location. One that carries it has it passed to the client instead, as
``config`` for ``asyncssh`` and as ``-F`` for ``ssh`` and ``scp``.
"""

import typing as t
from pathlib import Path

__all__ = (
    'LEGACY_PARAM_NAMES',
    'client_options',
    'config_path',
    'connect_kwargs',
    'render_stanza',
    'resolve_config_file',
    'write_stanza',
)

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

_CONFIG_DIR_NAME: t.Final = '_migration_ssh_config'


def config_path(alias: str) -> Path:
    """Return where to write the client configuration of a computer being migrated."""
    from aiida.manage.configuration.settings import AiiDAConfigDir

    return AiiDAConfigDir.get() / _CONFIG_DIR_NAME / f'{alias}.conf'


def resolve_config_file(stored: str | None) -> Path | None:
    """Return the client configuration a computer connects through, or ``None`` for the default one.

    :param stored: the ``ssh_config_file`` of the computer, unset for one that was configured rather
        than migrated.
    :raises ConfigurationError: if the recorded configuration is gone. It cannot be written again,
        since the parameters it was rendered from were replaced by it.
    """
    if not stored:
        return None

    path = Path(stored)

    if not path.is_file():
        from aiida.common.exceptions import ConfigurationError

        msg = (
            f'The SSH client configuration `{path}` is missing. It was written when this profile was '
            'migrated to AiiDA v3 and holds the connection parameters this computer used to store '
            'itself, so it cannot be recreated. Restore it from a backup, or connect through your '
            'own `~/.ssh/config` instead with '
            '`verdi computer configure core.ssh <COMPUTER> --host <YOUR-ALIAS>`.'
        )
        raise ConfigurationError(msg)

    return path


def client_options(path: Path | None) -> list[str]:
    """Return the ``ssh``/``scp`` options selecting a client configuration, if there is one."""
    return ['-F', str(path)] if path is not None else []


def _quote(value: str) -> str:
    """Quote a value that contains whitespace, which ``ssh_config`` would otherwise split."""
    return f'"{value}"' if any(character.isspace() for character in value) else value


def _yes_no(flag: t.Any) -> str:
    return 'yes' if flag else 'no'


def _render_host_key_policy(params: dict[str, t.Any]) -> list[str]:
    """Return the host key directives reproducing ``key_policy`` and ``load_system_host_keys``."""
    directives = []

    if params.get('key_policy', 'RejectPolicy') != 'RejectPolicy':
        # `AutoAddPolicy` and `WarningPolicy` accepted an unknown host but still refused a *changed*
        # key, which `no` accepts too. Telling the two apart needs a validation hook of our own, and
        # is not worth it for a policy chosen to stop being asked. The migration reports this.
        directives.append('StrictHostKeyChecking no')

    if params.get('load_system_host_keys') is False:
        # No host keys were loaded at all, so no host was ever known.
        directives.append('UserKnownHostsFile /dev/null')
        directives.append('GlobalKnownHostsFile /dev/null')

    return directives


def render_stanza(alias: str, hostname: str, params: dict[str, t.Any]) -> str:
    """Render the connection parameters of a legacy computer as an ``ssh_config`` entry.

    Parameters that were switched off are pinned too, since ``ssh -F`` reads neither
    ``~/.ssh/config`` nor ``/etc/ssh/ssh_config`` and so inherits nothing.

    :param alias: the ``Host`` name to define, unique to the computer being migrated.
    :param hostname: the host the name resolves to.
    :param params: the ``auth_params`` of a computer configured with the legacy plugin.
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
        directives.append(f'ProxyJump {proxy_jump}')
    if proxy_command := params.get('proxy_command'):
        # Taken as the rest of the line by every client, which also expand its `%h`/`%p` tokens.
        directives.append(f'ProxyCommand {proxy_command}')

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
    return f'Host {alias}\n{body}\n'


def write_stanza(alias: str, stanza: str, comment: str) -> Path:
    """Write the client configuration of a migrated computer, and return where it went.

    :param alias: the host the entry defines, which names the file.
    :param stanza: the entry, as rendered by :func:`render_stanza`.
    :param comment: a line recording which computer the entry belongs to.
    """
    path = config_path(alias)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f'# {comment}\n{stanza}', encoding='utf8')
    path.chmod(0o600)

    return path


def connect_kwargs(path: Path) -> dict[str, t.Any]:
    """Return the ``asyncssh.connect()`` arguments for the directives it does not parse.

    ``asyncssh`` silently skips a directive it has no handler for, and two that a migrated computer
    may rely on are among them. The ``ssh`` and ``scp`` clients honour both natively.
    """
    directives = {}

    for raw_line in path.read_text(encoding='utf8').splitlines():
        line = raw_line.strip()
        if not line or line.startswith('#'):
            continue
        name, _, value = line.partition(' ')
        directives[name.lower()] = value.strip().strip('"')

    kwargs: dict[str, t.Any] = {}

    if directives.get('stricthostkeychecking') == 'no':
        kwargs['known_hosts'] = None

    if directives.get('identityfile') == 'none':
        # `asyncssh` would read `none` as a file name. `None` is how it is told to offer no key of
        # its own, leaving the agent as the only source, which is what `look_for_keys` did.
        kwargs['client_keys'] = None

    if gss_host := directives.get('gssapiserveridentity'):
        kwargs['gss_host'] = gss_host

    return kwargs
