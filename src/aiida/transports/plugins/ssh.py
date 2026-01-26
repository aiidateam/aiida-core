###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Plugin for transport over SSH (and SFTP for file transfer)."""

import glob
import io
import os
import re
from stat import S_ISDIR, S_ISREG
from typing import Optional

import click

from aiida.cmdline.params import options
from aiida.cmdline.params.types.path import AbsolutePathOrEmptyParamType
from aiida.common.escaping import escape_for_bash
from aiida.common.warnings import warn_deprecation

from ..transport import BlockingTransport, TransportInternalError, TransportPath, has_magic

__all__ = ('SshTransport', 'convert_to_bool', 'parse_sshconfig')


def parse_sshconfig(computername):
    """Return the ssh configuration for a given computer name.

    This parses the ``.ssh/config`` file in the home directory and
    returns the part of configuration of the given computer name.

    :param computername: the computer name for which we want the configuration.
    """
    import paramiko

    config = paramiko.SSHConfig()
    try:
        with open(os.path.expanduser('~/.ssh/config'), encoding='utf8') as fhandle:
            config.parse(fhandle)
    except OSError:
        # No file found, so empty configuration
        pass

    return config.lookup(computername)


def convert_to_bool(string):
    """Convert a string passed in the CLI to a valid bool.

    :return: the parsed bool value.
    :raise ValueError: If the value is not parsable as a bool
    """
    upstring = str(string).upper()

    if upstring in ['Y', 'YES', 'T', 'TRUE']:
        return True
    if upstring in ['N', 'NO', 'F', 'FALSE']:
        return False
    raise ValueError('Invalid boolean value provided')


class SshTransport(BlockingTransport):
    """Support connection, command execution and data transfer to remote computers via SSH+SFTP."""

    # Valid keywords accepted by the connect method of paramiko.SSHClient
    # I disable 'password' and 'pkey' to avoid these data to get logged in the
    # aiida log file.
    _valid_connect_options = [
        (
            'username',
            {'prompt': 'User name', 'help': 'Login user name on the remote machine.', 'non_interactive_default': True},
        ),
        (
            'port',
            {
                'option': options.PORT,
                'prompt': 'Port number',
                'non_interactive_default': True,
            },
        ),
        (
            'look_for_keys',
            {
                'default': True,
                'switch': True,
                'prompt': 'Look for keys',
                'help': 'Automatically look for private keys in the ~/.ssh folder.',
                'non_interactive_default': True,
            },
        ),
        (
            'key_filename',
            {
                'type': AbsolutePathOrEmptyParamType(dir_okay=False, exists=True),
                'prompt': 'SSH key file',
                'help': 'Absolute path to your private SSH key. Leave empty to use the path set in the SSH config.',
                'non_interactive_default': True,
            },
        ),
        (
            'timeout',
            {
                'type': int,
                'prompt': 'Connection timeout in s',
                'help': 'Time in seconds to wait for connection before giving up. Leave empty to use default value.',
                'non_interactive_default': True,
            },
        ),
        (
            'allow_agent',
            {
                'default': False,
                'switch': True,
                'prompt': 'Allow ssh agent',
                'help': 'Switch to allow or disallow using an SSH agent.',
                'non_interactive_default': True,
            },
        ),
        (
            'proxy_jump',
            {
                'prompt': 'SSH proxy jump',
                'help': 'SSH proxy jump for tunneling through other SSH hosts.'
                ' Use a comma-separated list of hosts of the form [user@]host[:port].'
                ' If user or port are not specified for a host, the user & port values from the target host are used.'
                ' This option must be provided explicitly and is not parsed from the SSH config file when left empty.',
                'non_interactive_default': True,
            },
        ),  # Managed 'manually' in connect
        (
            'proxy_command',
            {
                'prompt': 'SSH proxy command',
                'help': 'SSH proxy command for tunneling through a proxy server.'
                ' For tunneling through another SSH host, consider using the "SSH proxy jump" option instead!'
                ' Leave empty to parse the proxy command from the SSH config file.',
                'non_interactive_default': True,
            },
        ),  # Managed 'manually' in connect
        (
            'compress',
            {
                'default': True,
                'switch': True,
                'prompt': 'Compress file transfers',
                'help': 'Turn file transfer compression on or off.',
                'non_interactive_default': True,
            },
        ),
        (
            'gss_auth',
            {
                'default': False,
                'type': bool,
                'prompt': 'GSS auth',
                'help': 'Enable when using GSS kerberos token to connect.',
                'non_interactive_default': True,
            },
        ),
        (
            'gss_kex',
            {
                'default': False,
                'type': bool,
                'prompt': 'GSS kex',
                'help': 'GSS kex for kerberos, if not configured in SSH config file.',
                'non_interactive_default': True,
            },
        ),
        (
            'gss_deleg_creds',
            {
                'default': False,
                'type': bool,
                'prompt': 'GSS deleg_creds',
                'help': 'GSS deleg_creds for kerberos, if not configured in SSH config file.',
                'non_interactive_default': True,
            },
        ),
        (
            'gss_host',
            {
                'prompt': 'GSS host',
                'help': 'GSS host for kerberos, if not configured in SSH config file.',
                'non_interactive_default': True,
            },
        ),
        # for Kerberos support through python-gssapi
    ]

    _valid_connect_params = [i[0] for i in _valid_connect_options]

    # Valid parameters for the ssh transport
    # For each param, a class method with name
    # _convert_PARAMNAME_fromstring
    # should be defined, that returns the value converted from a string to
    # a correct type, or raise a ValidationError
    #
    # moreover, if you want to help in the default configuration, you can
    # define a _get_PARAMNAME_suggestion_string
    # to return a suggestion; it must accept only one parameter, being a Computer
    # instance
    _valid_auth_options = _valid_connect_options + [
        (
            'load_system_host_keys',
            {
                'default': True,
                'switch': True,
                'prompt': 'Load system host keys',
                'help': 'Load system host keys from default SSH location.',
                'non_interactive_default': True,
            },
        ),
        (
            'key_policy',
            {
                'default': 'RejectPolicy',
                'type': click.Choice(['RejectPolicy', 'WarningPolicy', 'AutoAddPolicy']),
                'prompt': 'Key policy',
                'help': 'SSH key policy if host is not known.',
                'non_interactive_default': True,
            },
        ),
    ]

    # Max size of log message to print in _exec_command_internal.
    # Unlimited by default, but can be cropped by a subclass
    # if too large commands are sent, clogging the outputs or logs
    _MAX_EXEC_COMMAND_LOG_SIZE = None

    @classmethod
    def _get_username_suggestion_string(cls, computer):
        """Return a suggestion for the specific field."""
        import getpass

        config = parse_sshconfig(computer.hostname)
        # Either the configured user in the .ssh/config, or the current username
        return str(config.get('user', getpass.getuser()))

    @classmethod
    def _get_port_suggestion_string(cls, computer):
        """Return a suggestion for the specific field."""
        config = parse_sshconfig(computer.hostname)
        # Either the configured user in the .ssh/config, or the default SSH port
        return str(config.get('port', 22))

    @classmethod
    def _get_key_filename_suggestion_string(cls, computer):
        """Return a suggestion for the specific field."""
        config = parse_sshconfig(computer.hostname)

        try:
            identities = config['identityfile']
            # In paramiko > 0.10, identity file is a list of strings.
            if isinstance(identities, str):
                identity = identities
            elif isinstance(identities, (list, tuple)):
                if not identities:
                    # An empty list should not be provided; to be sure,
                    # anyway, behave as if no identityfile were defined
                    raise KeyError
                # By default we suggest only the first one
                identity = identities[0]
            else:
                # If the parser provides an unknown type, just skip to
                # the 'except KeyError' section, as if no identityfile
                # were provided (hopefully, this should never happen)
                raise KeyError
        except KeyError:
            # No IdentityFile defined: return an empty string
            return ''

        return os.path.expanduser(identity)

    @classmethod
    def _get_timeout_suggestion_string(cls, computer):
        """Return a suggestion for the specific field.

        Provide 60s as a default timeout for connections.
        """
        config = parse_sshconfig(computer.hostname)
        return str(config.get('connecttimeout', '60'))

    @classmethod
    def _get_allow_agent_suggestion_string(cls, computer):
        """Return a suggestion for the specific field."""
        config = parse_sshconfig(computer.hostname)
        return convert_to_bool(str(config.get('allow_agent', 'yes')))

    @classmethod
    def _get_look_for_keys_suggestion_string(cls, computer):
        """Return a suggestion for the specific field."""
        config = parse_sshconfig(computer.hostname)
        return convert_to_bool(str(config.get('look_for_keys', 'yes')))

    @classmethod
    def _get_proxy_command_suggestion_string(cls, computer):
        """Return a suggestion for the specific field."""
        config = parse_sshconfig(computer.hostname)
        # Either the configured user in the .ssh/config, or the default SSH port
        raw_string = str(config.get('proxycommand', ''))
        # Note: %h and %p get already automatically substituted with
        # hostname and port by the config parser!

        pieces = raw_string.split()
        new_pieces = []
        for piece in pieces:
            if '>' in piece:
                # If there is a piece with > to readdress stderr or stdout,
                # skip from here on (anything else can only be readdressing)
                break

            new_pieces.append(piece)

        return ' '.join(new_pieces)

    @classmethod
    def _get_proxy_jump_suggestion_string(cls, _):
        """Return an empty suggestion since Paramiko does not parse ProxyJump from the SSH config."""
        return ''

    @classmethod
    def _get_compress_suggestion_string(cls, computer):
        """Return a suggestion for the specific field."""
        return 'True'

    @classmethod
    def _get_load_system_host_keys_suggestion_string(cls, computer):
        """Return a suggestion for the specific field."""
        return 'True'

    @classmethod
    def _get_key_policy_suggestion_string(cls, computer):
        """Return a suggestion for the specific field."""
        return 'RejectPolicy'

    @classmethod
    def _get_gss_auth_suggestion_string(cls, computer):
        """Return a suggestion for the specific field."""
        config = parse_sshconfig(computer.hostname)
        return convert_to_bool(str(config.get('gssapiauthentication', 'no')))

    @classmethod
    def _get_gss_kex_suggestion_string(cls, computer):
        """Return a suggestion for the specific field."""
        config = parse_sshconfig(computer.hostname)
        return convert_to_bool(str(config.get('gssapikeyexchange', 'no')))

    @classmethod
    def _get_gss_deleg_creds_suggestion_string(cls, computer):
        """Return a suggestion for the specific field."""
        config = parse_sshconfig(computer.hostname)
        return convert_to_bool(str(config.get('gssapidelegatecredentials', 'no')))

    @classmethod
    def _get_gss_host_suggestion_string(cls, computer):
        """Return a suggestion for the specific field."""
        config = parse_sshconfig(computer.hostname)
        return str(config.get('gssapihostname', computer.hostname))

    def __init__(self, *args, **kwargs):
        """Initialize the SshTransport class.

        :param machine: the machine to connect to
        :param load_system_host_keys: (optional, default False)
           if False, do not load the system host keys
        :param key_policy: (optional, default = paramiko.RejectPolicy())
           the policy to use for unknown keys

        Other parameters valid for the ssh connect function (see the
        self._valid_connect_params list) are passed to the connect
        function (as port, username, password, ...); taken from the
        accepted paramiko.SSHClient.connect() params.
        """
        import paramiko

        super().__init__(*args, **kwargs)

        self._sftp = None
        self._proxy = None
        self._proxies = []

        self._machine = kwargs.pop('machine')

        self._client = paramiko.SSHClient()
        self._load_system_host_keys = kwargs.pop('load_system_host_keys', False)
        if self._load_system_host_keys:
            self._client.load_system_host_keys()

        self._missing_key_policy = kwargs.pop('key_policy', 'RejectPolicy')  # This is paramiko default
        if self._missing_key_policy == 'RejectPolicy':
            self._client.set_missing_host_key_policy(paramiko.RejectPolicy())
        elif self._missing_key_policy == 'WarningPolicy':
            self._client.set_missing_host_key_policy(paramiko.WarningPolicy())
        elif self._missing_key_policy == 'AutoAddPolicy':
            self._client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        else:
            raise ValueError(
                'Unknown value of the key policy, allowed values ' 'are: RejectPolicy, WarningPolicy, AutoAddPolicy'
            )

        self._connect_args = {}
        for k in self._valid_connect_params:
            try:
                self._connect_args[k] = kwargs.pop(k)
            except KeyError:
                pass

    def open(self):
        """Open a SSHClient to the machine possibly using the parameters given
        in the __init__.

        Also opens a sftp channel, ready to be used.
        The current working directory is set explicitly, so it is not None.

        :raise aiida.common.InvalidOperation: if the channel is already open
        """
        import paramiko
        from paramiko.ssh_exception import SSHException

        from aiida.common.exceptions import InvalidOperation
        from aiida.transports.util import _DetachedProxyCommand

        if self._is_open:
            raise InvalidOperation('Cannot open the transport twice')
        # Open a SSHClient
        connection_arguments = self._connect_args.copy()
        if 'key_filename' in connection_arguments and not connection_arguments['key_filename']:
            connection_arguments.pop('key_filename')

        proxyjumpstring = connection_arguments.pop('proxy_jump', None)
        proxycmdstring = connection_arguments.pop('proxy_command', None)

        if proxyjumpstring and proxycmdstring:
            raise ValueError('The SSH proxy jump and SSH proxy command options can not be used together')

        if proxyjumpstring:
            matcher = re.compile(r'^(?:(?P<username>[^@]+)@)?(?P<host>[^@:]+)(?::(?P<port>\d+))?\s*$')
            try:
                # don't use a generator here to have everything evaluated
                proxies = [matcher.match(s).groupdict() for s in proxyjumpstring.split(',')]
            except AttributeError:
                raise ValueError('The given configuration for the SSH proxy jump option could not be parsed')

            # proxy_jump supports a list of jump hosts, each jump host is another Paramiko SSH connection
            # but when opening a forward channel on a connection, we have to give the next hop.
            # So we go through adjacent pairs and by adding the final target to the list we make it universal.
            for proxy, target in zip(
                proxies,
                proxies[1:]
                + [
                    {
                        'host': self._machine,
                        'port': connection_arguments.get('port', 22),
                    }
                ],
            ):
                proxy_connargs = connection_arguments.copy()

                if proxy['username']:
                    proxy_connargs['username'] = proxy['username']
                if proxy['port']:
                    proxy_connargs['port'] = int(proxy['port'])
                if not target['port']:  # the target port for the channel can not be None
                    target['port'] = connection_arguments.get('port', 22)

                proxy_client = paramiko.SSHClient()
                if self._load_system_host_keys:
                    proxy_client.load_system_host_keys()
                if self._missing_key_policy == 'RejectPolicy':
                    proxy_client.set_missing_host_key_policy(paramiko.RejectPolicy())
                elif self._missing_key_policy == 'WarningPolicy':
                    proxy_client.set_missing_host_key_policy(paramiko.WarningPolicy())
                elif self._missing_key_policy == 'AutoAddPolicy':
                    proxy_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

                try:
                    proxy_client.connect(proxy['host'], **proxy_connargs)
                except Exception as exc:
                    self.logger.error(
                        f"Error connecting to proxy '{proxy['host']}' through SSH: [{self.__class__.__name__}] {exc}, "
                        f'connect_args were: {proxy_connargs}'
                    )
                    self._close_proxies()  # close all since we're going to start anew on the next open() (if any)
                    raise
                connection_arguments['sock'] = proxy_client.get_transport().open_channel(
                    'direct-tcpip', (target['host'], target['port']), ('', 0)
                )
                self._proxies.append(proxy_client)

        if proxycmdstring:
            self._proxy = _DetachedProxyCommand(proxycmdstring)
            connection_arguments['sock'] = self._proxy

        try:
            self._client.connect(self._machine, **connection_arguments)
        except Exception as exc:
            self.logger.error(
                f"Error connecting to '{self._machine}' through SSH: "
                + f'[{self.__class__.__name__}] {exc}, '
                + f'connect_args were: {self._connect_args}'
            )
            self._close_proxies()
            raise

        # Open the SFTP channel, and handle error by directing customer to try another transport
        try:
            self._sftp = self._client.open_sftp()
        except SSHException:
            self._close_proxies()
            raise InvalidOperation(
                'Error in ssh transport plugin. This may be due to the remote computer not supporting SFTP. '
                'Try setting it up with the core.ssh_async transport plugin with openssh backend, instead.'
            )

        self._is_open = True

        # Set the current directory to a explicit path, and not to None
        self._sftp.chdir(self._sftp.normalize('.'))

        return self

    def _close_proxies(self):
        """Close all proxy connections (proxy_jump and proxy_command)"""
        # Paramiko only closes the channel when closing the main connection, but not the connection itself.
        while self._proxies:
            self._proxies.pop().close()

        if self._proxy:
            # Paramiko should close this automatically when closing the channel,
            # but since the process is started in __init__this might not happen correctly.
            self._proxy.close()
            self._proxy = None

    def close(self):
        """Close the SFTP channel, and the SSHClient.

        :todo: correctly manage exceptions

        :raise aiida.common.InvalidOperation: if the channel is already open
        """
        from aiida.common.exceptions import InvalidOperation

        if not self._is_open:
            raise InvalidOperation('Cannot close the transport: it is already closed')

        self._sftp.close()
        self._client.close()
        self._close_proxies()

        self._is_open = False

    @property
    def sshclient(self):
        if not self._is_open:
            raise TransportInternalError('Error, ssh method called for SshTransport without opening the channel first')
        return self._client

    @property
    def sftp(self):
        if not self._is_open:
            raise TransportInternalError('Error, sftp method called for SshTransport without opening the channel first')
        return self._sftp

    def __str__(self):
        """Return a useful string."""
        conn_info = self._machine
        try:
            conn_info = f"{self._connect_args['username']}@{conn_info}"
        except KeyError:
            # No username explicitly defined: ignore
            pass
        try:
            conn_info += f":{self._connect_args['port']}"
        except KeyError:
            # No port explicitly defined: ignore
            pass

        return f"{'OPEN' if self._is_open else 'CLOSED'} [{conn_info}]"

    def chdir(self, path: TransportPath):
        """
        PLEASE DON'T USE `chdir()` IN NEW DEVELOPMENTS, INSTEAD DIRECTLY PASS ABSOLUTE PATHS TO INTERFACE.
        `chdir()` is DEPRECATED and will be removed in the next major version.

        Change directory of the SFTP session. Emulated internally by paramiko.

        Differently from paramiko, if you pass None to chdir, nothing
        happens and the cwd is unchanged.
        """
        warn_deprecation(
            '`chdir()` is deprecated and will be removed in the next major version. Use absolute paths instead.',
            version=3,
        )
        from paramiko.sftp import SFTPError

        path = str(path)
        old_path = self.sftp.getcwd()
        if path is not None:
            try:
                self.sftp.chdir(path)
            except SFTPError as exc:
                # e.args[0] is an error code. For instance,
                # 20 is 'the object is not a directory'
                # Here I just re-raise the message as OSError
                raise OSError(exc.args[1])

        # Paramiko already checked that path is a folder, otherwise I would
        # have gotten an exception. Now, I want to check that I have read
        # permissions in this folder (nothing is said on write permissions,
        # though).
        # Otherwise, if I do _exec_command_internal, that as a first operation
        # cd's in a folder, I get a wrong retval, that is an unwanted behavior.
        #
        # Note: I don't store the result of the function; if I have no
        # read permissions, this will raise an exception.
        try:
            self.stat('.')
        except OSError as exc:
            if 'Permission denied' in str(exc):
                self.chdir(old_path)
            raise OSError(str(exc))

    def normalize(self, path: TransportPath = '.'):
        """Returns the normalized path (removing double slashes, etc...)"""
        path = str(path)

        return self.sftp.normalize(path)

    def stat(self, path: TransportPath):
        """Retrieve information about a file on the remote system.  The return
        value is an object whose attributes correspond to the attributes of
        Python's ``stat`` structure as returned by ``os.stat``, except that it
        contains fewer fields.
        The fields supported are: ``st_mode``, ``st_size``, ``st_uid``,
        ``st_gid``, ``st_atime``, and ``st_mtime``.

        :param str path: the filename to stat

        :return: a `paramiko.sftp_attr.SFTPAttributes` object containing
            attributes about the given file.
        """
        path = str(path)

        return self.sftp.stat(path)

    def lstat(self, path: TransportPath):
        """Retrieve information about a file on the remote system, without
        following symbolic links (shortcuts). This otherwise behaves exactly
        the same as `stat`.

        :param str path: the filename to stat

        :return: a `paramiko.sftp_attr.SFTPAttributes` object containing
            attributes about the given file.
        """
        path = str(path)

        return self.sftp.lstat(path)

    def getcwd(self):
        """
        PLEASE DON'T USE `getcwd()` IN NEW DEVELOPMENTS, INSTEAD DIRECTLY PASS ABSOLUTE PATHS TO INTERFACE.
        `getcwd()` is DEPRECATED and will be removed in the next major version.

        Return the current working directory for this SFTP session, as
        emulated by paramiko. If no directory has been set with chdir,
        this method will return None. But in __enter__ this is set explicitly,
        so this should never happen within this class.
        """
        return self.sftp.getcwd()

    def makedirs(self, path: TransportPath, ignore_existing: bool = False):
        """Super-mkdir; create a leaf directory and all intermediate ones.
        Works like mkdir, except that any intermediate path segment (not
        just the rightmost) will be created if it does not exist.

        NOTE: since os.path.split uses the separators as the host system
        (that could be windows), I assume the remote computer is Linux-based
        and use '/' as separators!

        :param path: directory to create (string)
        :param ignore_existing: if set to true, it doesn't give any error
            if the leaf directory does already exist (bool)

        :raise OSError: If the directory already exists.
        """
        path = str(path)

        # check to avoid creation of empty dirs
        path = os.path.normpath(path)

        if path.startswith('/'):
            to_create = path.strip().split('/')[1:]
            this_dir = '/'
        else:
            to_create = path.strip().split('/')
            this_dir = ''

        for count, element in enumerate(to_create):
            if count > 0:
                this_dir += '/'
            this_dir += element
            if count + 1 == len(to_create) and self.isdir(this_dir) and ignore_existing:
                return
            if count + 1 == len(to_create) and self.isdir(this_dir) and not ignore_existing:
                self.mkdir(this_dir)
            if not self.isdir(this_dir):
                self.mkdir(this_dir)

    def mkdir(self, path: TransportPath, ignore_existing: bool = False):
        """Create a folder (directory) named path.

        :param path: name of the folder to create
        :param ignore_existing: if True, does not give any error if the directory
                  already exists

        :raise OSError: If the directory already exists.
        """
        path = str(path)

        if ignore_existing and self.isdir(path):
            return

        try:
            self.sftp.mkdir(path)
        except OSError as exc:
            if os.path.isabs(path):
                raise OSError(
                    "Error during mkdir of '{}', "
                    "maybe you don't have the permissions to do it, "
                    'or the directory already exists? ({})'.format(path, exc)
                )
            else:
                raise OSError(
                    "Error during mkdir of '{}' from folder '{}', "
                    "maybe you don't have the permissions to do it, "
                    'or the directory already exists? ({})'.format(path, self.getcwd(), exc)
                )

    def rmtree(self, path: TransportPath):
        """Remove a file or a directory at path, recursively
        Flags used: -r: recursive copy; -f: force, makes the command non interactive;

        :param path: remote path to delete

        :raise OSError: if the rm execution failed.
        """
        path = str(path)
        # Assuming linux rm command!

        rm_exe = 'rm'
        rm_flags = '-r -f'
        # if in input I give an invalid object raise ValueError
        if not path:
            raise ValueError('Input to rmtree() must be a non empty string. ' + f'Found instead {path} as path')

        command = f'{rm_exe} {rm_flags} {escape_for_bash(path)}'

        retval, stdout, stderr = self.exec_command_wait_bytes(command)

        if retval == 0:
            if stderr.strip():
                self.logger.warning(f'There was nonempty stderr in the rm command: {stderr}')
            return True
        self.logger.error(f"Problem executing rm. Exit code: {retval}, stdout: '{stdout}', stderr: '{stderr}'")
        raise OSError(f'Error while executing rm. Exit code: {retval}')

    def rmdir(self, path: TransportPath):
        """Remove the folder named 'path' if empty."""
        path = str(path)
        self.sftp.rmdir(path)

    def chown(self, path: TransportPath, uid, gid):
        """Change owner permissions of a file.

        For now, this is not implemented for the SSH transport.
        """
        raise NotImplementedError

    def isdir(self, path: TransportPath):
        """Return True if the given path is a directory, False otherwise.
        Return False also if the path does not exist.
        """
        # Return False on empty string (paramiko would map this to the local
        # folder instead)
        path = str(path)

        if not path:
            return False
        path = str(path)
        try:
            return S_ISDIR(self.stat(path).st_mode)
        except OSError as exc:
            if getattr(exc, 'errno', None) == 2:
                # errno=2 means path does not exist: I return False
                return False
            raise  # Typically if I don't have permissions (errno=13)

    def chmod(self, path: TransportPath, mode):
        """Change permissions of a path.

        :param path: Path to the file or directory.
        :param mode: New permissions as an integer, for example 0o700 (octal) or 448 (decimal) results in `-rwx------`
            for a file.
        """
        path = str(path)

        if not path:
            raise OSError('Input path is an empty argument.')
        return self.sftp.chmod(path, mode)

    @staticmethod
    def _os_path_split_asunder(path: TransportPath):
        """Used by makedirs. Takes path
        and returns a list deconcatenating the path
        """
        path = str(path)
        parts = []
        while True:
            newpath, tail = os.path.split(path)
            if newpath == path:
                assert not tail
                if path:
                    parts.append(path)
                break
            parts.append(tail)
            path = newpath
        parts.reverse()
        return parts

    def put(
        self,
        localpath: TransportPath,
        remotepath: TransportPath,
        callback=None,
        dereference: bool = True,
        overwrite: bool = True,
        ignore_nonexisting: bool = False,
    ):
        """Put a file or a folder from local to remote.
        Redirects to putfile or puttree.

        :param localpath: an (absolute) local path
        :param remotepath: a remote path
        :param dereference: follow symbolic links (boolean).
            Default = True (default behaviour in paramiko). False is not implemented.
        :param  overwrite: if True overwrites files and folders (boolean).
            Default = False.

        :raise ValueError: if local path is invalid
        :raise OSError: if the localpath does not exist
        """
        localpath = str(localpath)
        remotepath = str(remotepath)

        if not dereference:
            raise NotImplementedError

        if not os.path.isabs(localpath):
            raise ValueError('The localpath must be an absolute path')

        if has_magic(localpath):
            if has_magic(remotepath):
                raise ValueError('Pathname patterns are not allowed in the destination')

            # use the imported glob to analyze the path locally
            to_copy_list = glob.glob(localpath)

            rename_remote = False
            if len(to_copy_list) > 1:
                # I can't scp more than one file on a single file
                if self.isfile(remotepath):
                    raise OSError('Remote destination is not a directory')
                # I can't scp more than one file in a non existing directory
                elif not self.path_exists(remotepath):  # questo dovrebbe valere solo per file
                    raise OSError('Remote directory does not exist')
                else:  # the remote path is a directory
                    rename_remote = True

            for file in to_copy_list:
                if os.path.isfile(file):
                    if rename_remote:  # copying more than one file in one directory
                        # here is the case isfile and more than one file
                        remotefile = os.path.join(remotepath, os.path.split(file)[1])
                        self.putfile(file, remotefile, callback, dereference, overwrite)

                    elif self.isdir(remotepath):  # one file to copy in '.'
                        remotefile = os.path.join(remotepath, os.path.split(file)[1])
                        self.putfile(file, remotefile, callback, dereference, overwrite)
                    else:  # one file to copy on one file
                        self.putfile(file, remotepath, callback, dereference, overwrite)
                else:
                    self.puttree(file, remotepath, callback, dereference, overwrite)

        elif os.path.isdir(localpath):
            self.puttree(localpath, remotepath, callback, dereference, overwrite)
        elif os.path.isfile(localpath):
            if self.isdir(remotepath):
                remote = os.path.join(remotepath, os.path.split(localpath)[1])
                self.putfile(localpath, remote, callback, dereference, overwrite)
            else:
                self.putfile(localpath, remotepath, callback, dereference, overwrite)
        elif not ignore_nonexisting:
            raise OSError(f'The local path {localpath} does not exist')

    def putfile(
        self,
        localpath: TransportPath,
        remotepath: TransportPath,
        callback=None,
        dereference: bool = True,
        overwrite: bool = True,
    ):
        """Put a file from local to remote.

        :param localpath: an (absolute) local path
        :param remotepath: a remote path
        :param overwrite: if True overwrites files and folders (boolean).
            Default = True.

        :raise ValueError: if local path is invalid
        :raise OSError: if the localpath does not exist,
                    or unintentionally overwriting
        """
        localpath = str(localpath)
        remotepath = str(remotepath)

        if not dereference:
            raise NotImplementedError

        if not os.path.isabs(localpath):
            raise ValueError('The localpath must be an absolute path')

        if self.isfile(remotepath) and not overwrite:
            raise OSError('Destination already exists: not overwriting it')

        return self.sftp.put(localpath, remotepath, callback=callback)

    def puttree(
        self,
        localpath: TransportPath,
        remotepath: TransportPath,
        callback=None,
        dereference: bool = True,
        overwrite: bool = True,
    ):
        """Put a folder recursively from local to remote.

        By default, overwrite.

        :param localpath: an (absolute) local path
        :param remotepath: a remote path
        :param dereference: follow symbolic links (boolean)
            Default = True (default behaviour in paramiko). False is not implemented.
        :param overwrite: if True overwrites files and folders (boolean).
            Default = True

        :raise ValueError: if local path is invalid
        :raise OSError: if the localpath does not exist, or trying to overwrite
        :raise OSError: if remotepath is invalid

        .. note:: setting dereference equal to True could cause infinite loops.
              see os.walk() documentation
        """
        localpath = str(localpath)
        remotepath = str(remotepath)

        if not dereference:
            raise NotImplementedError

        if not os.path.isabs(localpath):
            raise ValueError('The localpath must be an absolute path')

        if not os.path.exists(localpath):
            raise OSError('The localpath does not exists')

        if not os.path.isdir(localpath):
            raise ValueError(f'Input localpath is not a folder: {localpath}')

        if not remotepath:
            raise OSError('remotepath must be a non empty string')

        if self.path_exists(remotepath) and not overwrite:
            raise OSError("Can't overwrite existing files")
        if self.isfile(remotepath):
            raise OSError('Cannot copy a directory into a file')

        if not self.isdir(remotepath):  # in this case copy things in the remotepath directly
            self.makedirs(remotepath)  # and make a directory at its place
        else:  # remotepath exists already: copy the folder inside of it!
            remotepath = os.path.join(remotepath, os.path.split(localpath)[1])
            self.makedirs(remotepath, ignore_existing=overwrite)  # create a nested folder

        for this_source in os.walk(localpath):
            # Get the relative path
            this_basename = os.path.relpath(path=this_source[0], start=localpath)

            try:
                self.stat(os.path.join(remotepath, this_basename))
            except OSError as exc:
                import errno

                if exc.errno == errno.ENOENT:  # Missing file
                    self.mkdir(os.path.join(remotepath, this_basename))
                else:
                    raise

            for this_file in this_source[2]:
                this_local_file = os.path.join(localpath, this_basename, this_file)
                this_remote_file = os.path.join(remotepath, this_basename, this_file)
                self.putfile(this_local_file, this_remote_file)

    def get(
        self,
        remotepath: TransportPath,
        localpath: TransportPath,
        callback=None,
        dereference: bool = True,
        overwrite: bool = True,
        ignore_nonexisting: bool = False,
    ):
        """Get a file or folder from remote to local.
        Redirects to getfile or gettree.

        :param remotepath: a remote path
        :param localpath: an (absolute) local path
        :param dereference: follow symbolic links.
            Default = True (default behaviour in paramiko).
            False is not implemented.
        :param overwrite: if True overwrites files and folders.
            Default = False

        :raise ValueError: if local path is invalid
        :raise OSError: if the remotepath is not found
        """
        remotepath = str(remotepath)
        localpath = str(localpath)

        if not dereference:
            raise NotImplementedError

        if not os.path.isabs(localpath):
            raise ValueError('The localpath must be an absolute path')

        if has_magic(remotepath):
            if has_magic(localpath):
                raise ValueError('Pathname patterns are not allowed in the destination')
            # use the self glob to analyze the path remotely
            to_copy_list = self.glob(remotepath)

            rename_local = False
            if len(to_copy_list) > 1:
                # I can't scp more than one file on a single file
                if os.path.isfile(localpath):
                    raise OSError('Remote destination is not a directory')
                # I can't scp more than one file in a non existing directory
                elif not os.path.exists(localpath):  # this should hold only for files
                    raise OSError('Remote directory does not exist')
                else:  # the remote path is a directory
                    rename_local = True

            for file in to_copy_list:
                if self.isfile(file):
                    if rename_local:  # copying more than one file in one directory
                        # here is the case isfile and more than one file
                        remote = os.path.join(localpath, os.path.split(file)[1])
                        self.getfile(file, remote, callback, dereference, overwrite)
                    else:  # one file to copy on one file
                        self.getfile(file, localpath, callback, dereference, overwrite)
                else:
                    self.gettree(file, localpath, callback, dereference, overwrite)

        elif self.isdir(remotepath):
            self.gettree(remotepath, localpath, callback, dereference, overwrite)
        elif self.isfile(remotepath):
            if os.path.isdir(localpath):
                remote = os.path.join(localpath, os.path.split(remotepath)[1])
                self.getfile(remotepath, remote, callback, dereference, overwrite)
            else:
                self.getfile(remotepath, localpath, callback, dereference, overwrite)
        elif ignore_nonexisting:
            pass
        else:
            raise OSError(f'The remote path {remotepath} does not exist')

    def getfile(
        self,
        remotepath: TransportPath,
        localpath: TransportPath,
        callback=None,
        dereference: bool = True,
        overwrite: bool = True,
    ):
        """Get a file from remote to local.

        :param remotepath: a remote path
        :param  localpath: an (absolute) local path
        :param  overwrite: if True overwrites files and folders.
                Default = False

        :raise ValueError: if local path is invalid
        :raise OSError: if unintentionally overwriting
        """
        remotepath = str(remotepath)
        localpath = str(localpath)

        if not os.path.isabs(localpath):
            raise ValueError('localpath must be an absolute path')

        if os.path.isfile(localpath) and not overwrite:
            raise OSError('Destination already exists: not overwriting it')

        if not dereference:
            raise NotImplementedError

        # Workaround for bug #724 in paramiko -- remove localpath on OSError
        try:
            return self.sftp.get(remotepath, localpath, callback)
        except OSError:
            try:
                os.remove(localpath)
            except OSError:
                pass
            raise

    def gettree(
        self,
        remotepath: TransportPath,
        localpath: TransportPath,
        callback=None,
        dereference: bool = True,
        overwrite: bool = True,
    ):
        """Get a folder recursively from remote to local.

        :param remotepath: a remote path
        :param localpath: an (absolute) local path
        :param dereference: follow symbolic links.
            Default = True (default behaviour in paramiko).
            False is not implemented.
        :param  overwrite: if True overwrites files and folders.
            Default = True

        :raise ValueError: if local path is invalid
        :raise OSError: if the remotepath is not found
        :raise OSError: if unintentionally overwriting
        """
        remotepath = str(remotepath)
        localpath = str(localpath)
        if not dereference:
            raise NotImplementedError

        if not remotepath:
            raise OSError('Remotepath must be a non empty string')
        if not localpath:
            raise ValueError('Localpaths must be a non empty string')

        if not os.path.isabs(localpath):
            raise ValueError('Localpaths must be an absolute path')

        if not self.isdir(remotepath):
            raise OSError(f'Input remotepath is not a folder: {localpath}')

        if os.path.exists(localpath) and not overwrite:
            raise OSError("Can't overwrite existing files")
        if os.path.isfile(localpath):
            raise OSError('Cannot copy a directory into a file')

        if not os.path.isdir(localpath):  # in this case copy things in the remotepath directly
            os.makedirs(localpath, exist_ok=True)  # and make a directory at its place
        else:  # localpath exists already: copy the folder inside of it!
            localpath = os.path.join(localpath, os.path.split(remotepath)[1])
            os.makedirs(localpath, exist_ok=overwrite)  # create a nested folder

        item_list = self.listdir(remotepath)
        dest = str(localpath)

        for item in item_list:
            item = str(item)  # noqa: PLW2901

            if self.isdir(os.path.join(remotepath, item)):
                self.gettree(os.path.join(remotepath, item), os.path.join(dest, item))
            else:
                self.getfile(os.path.join(remotepath, item), os.path.join(dest, item))

    def get_attribute(self, path: TransportPath):
        """Returns the object Fileattribute, specified in aiida.transports
        Receives in input the path of a given file.
        """
        path = str(path)
        from aiida.transports.util import FileAttribute

        paramiko_attr = self.lstat(path)
        aiida_attr = FileAttribute()
        # map the paramiko class into the aiida one
        # note that paramiko object contains more informations than the aiida
        for key in aiida_attr._valid_fields:
            aiida_attr[key] = getattr(paramiko_attr, key)
        return aiida_attr

    def copyfile(self, remotesource: TransportPath, remotedestination: TransportPath, dereference: bool = False):
        remotesource = str(remotesource)
        remotedestination = str(remotedestination)

        return self.copy(remotesource, remotedestination, dereference)

    def copytree(self, remotesource: TransportPath, remotedestination: TransportPath, dereference: bool = False):
        remotesource = str(remotesource)
        remotedestination = str(remotedestination)

        return self.copy(remotesource, remotedestination, dereference, recursive=True)

    def copy(
        self,
        remotesource: TransportPath,
        remotedestination: TransportPath,
        dereference: bool = False,
        recursive: bool = True,
    ):
        """Copy a file or a directory from remote source to remote destination.
        Flags used: ``-r``: recursive copy; ``-f``: force, makes the command non interactive;
        ``-L`` follows symbolic links

        :param remotesource: file to copy from
        :param remotedestination: file to copy to
        :param dereference: if True, copy content instead of copying the symlinks only
            Default = False.
        :param recursive: if True copy directories recursively.
            Note that if the `remotesource` is a directory, `recursive` should always be set to True.
            Default = True.
        :type recursive: bool
        :raise OSError: if the cp execution failed.

        .. note:: setting dereference equal to True could cause infinite loops.
        """
        remotesource = str(remotesource)
        remotedestination = str(remotedestination)

        # In the majority of cases, we should deal with linux cp commands
        cp_flags = '-f'
        if recursive:
            cp_flags += ' -r'

        # For the moment, this is hardcoded. May become a parameter
        cp_exe = 'cp'

        # To evaluate if we also want -p: preserves mode,ownership and timestamp
        if dereference:
            # use -L; --dereference is not supported on mac
            cp_flags += ' -L'

        # if in input I give an invalid object raise ValueError
        if not remotesource:
            raise ValueError(
                'Input to copy() must be a non empty string. ' + f'Found instead {remotesource} as remotesource'
            )

        if not remotedestination:
            raise ValueError(
                'Input to copy() must be a non empty string. '
                + f'Found instead {remotedestination} as remotedestination'
            )

        if has_magic(remotedestination):
            raise ValueError('Pathname patterns are not allowed in the destination')

        if has_magic(remotesource):
            to_copy_list = self.glob(remotesource)

            if len(to_copy_list) > 1:
                if not self.path_exists(remotedestination) or self.isfile(remotedestination):
                    raise OSError("Can't copy more than one file in the same destination file")

            for file in to_copy_list:
                self._exec_cp(cp_exe, cp_flags, file, remotedestination)

        else:
            self._exec_cp(cp_exe, cp_flags, remotesource, remotedestination)

    def _exec_cp(self, cp_exe: str, cp_flags: str, src: str, dst: str):
        """Execute the ``cp`` command on the remote machine."""
        # to simplify writing the above copy function
        command = f'{cp_exe} {cp_flags} {escape_for_bash(src)} {escape_for_bash(dst)}'

        retval, stdout, stderr = self.exec_command_wait_bytes(command)

        if retval == 0:
            if stderr.strip():
                self.logger.warning(f'There was nonempty stderr in the cp command: {stderr}')
        else:
            self.logger.error(
                "Problem executing cp. Exit code: {}, stdout: '{}', " "stderr: '{}', command: '{}'".format(
                    retval, stdout, stderr, command
                )
            )
            if 'No such file or directory' in str(stderr):
                raise FileNotFoundError(f'Error while executing cp: {stderr}')

            raise OSError(
                'Error while executing cp. Exit code: {}, ' "stdout: '{}', stderr: '{}', " "command: '{}'".format(
                    retval, stdout, stderr, command
                )
            )

    @staticmethod
    def _local_listdir(path: str, pattern=None):
        """Acts on the local folder, for the rest, same as listdir"""
        if not pattern:
            return os.listdir(path)
        if path.startswith('/'):  # always this is the case in the local case
            base_dir = path
        else:
            base_dir = os.path.join(os.getcwd(), path)

        filtered_list = glob.glob(os.path.join(base_dir, pattern))
        if not base_dir.endswith(os.sep):
            base_dir += os.sep
        return [re.sub(base_dir, '', i) for i in filtered_list]

    def listdir(self, path: TransportPath = '.', pattern=None):
        """Get the list of files at path.

        :param path: default = '.'
        :param pattern: returns the list of files matching pattern.
                             Unix only. (Use to emulate ``ls *`` for example)
        """
        path = str(path)

        if path.startswith('/'):
            abs_dir = path
        else:
            abs_dir = os.path.join(self.getcwd(), path)

        if not pattern:
            return self.sftp.listdir(abs_dir)

        filtered_list = self.glob(os.path.join(abs_dir, pattern))
        if not abs_dir.endswith('/'):
            abs_dir += '/'
        return [re.sub(abs_dir, '', i) for i in filtered_list]

    def remove(self, path: TransportPath):
        """Remove a single file at 'path'"""
        path = str(path)
        return self.sftp.remove(path)

    def rename(self, oldpath: TransportPath, newpath: TransportPath):
        """Rename a file or folder from oldpath to newpath.

        :param str oldpath: existing name of the file or folder
        :param str newpath: new name for the file or folder

        :raises OSError: if oldpath is not found or newpath already exists
        :raises ValueError: if oldpath/newpath is not a valid path
        """
        if not oldpath:
            raise ValueError(f'Source {oldpath} is not a valid path')
        if not newpath:
            raise ValueError(f'Destination {newpath} is not a valid path')

        oldpath = str(oldpath)
        newpath = str(newpath)

        if not self.isfile(oldpath):
            if not self.isdir(oldpath):
                raise OSError(f'Source {oldpath} does not exist')

        if self.path_exists(newpath):
            raise OSError(f'Destination {newpath} already exist')

        return self.sftp.rename(oldpath, newpath)

    def isfile(self, path: TransportPath):
        """Return True if the given path is a file, False otherwise.
        Return False also if the path does not exist.
        """
        # This should not be needed for files, since an empty string should
        # be mapped by paramiko to the local directory - which is not a file -
        # but this is just to be sure
        if not path:
            return False

        path = str(path)
        try:
            self.logger.debug(
                f"stat for path '{path}' ('{self.normalize(path)}'): {self.stat(path)} [{self.stat(path).st_mode}]"
            )
            return S_ISREG(self.stat(path).st_mode)
        except OSError as exc:
            if getattr(exc, 'errno', None) == 2:
                # errno=2 means path does not exist: I return False
                return False
            raise  # Typically if I don't have permissions (errno=13)

    def _exec_command_internal(self, command, combine_stderr=False, bufsize=-1, workdir=None):
        """Executes the specified command in bash login shell.


        For executing commands and waiting for them to finish, use
        exec_command_wait.

        :param  command: the command to execute. The command is assumed to be
            already escaped using :py:func:`aiida.common.escaping.escape_for_bash`.
        :param combine_stderr: (default False) if True, combine stdout and
                stderr on the same buffer (i.e., stdout).
                Note: If combine_stderr is True, stderr will always be empty.
        :param bufsize: same meaning of the one used by paramiko.
        :param workdir: (optional, default=None) if set, the command will be executed
                in the specified working directory.
                if None, the command will be executed in the current working directory,
                from DEPRECATED `self.getcwd()`, if that has a value.

        :return: a tuple with (stdin, stdout, stderr, channel),
            where stdin, stdout and stderr behave as file-like objects,
            plus the methods provided by paramiko, and channel is a
            paramiko.Channel object.
        """
        channel = self.sshclient.get_transport().open_session()
        channel.set_combine_stderr(combine_stderr)

        if workdir is not None:
            command_to_execute = f'cd {workdir} &&  ( {command} )'
        elif (cwd := self.getcwd()) is not None:
            escaped_folder = escape_for_bash(cwd)
            command_to_execute = f'cd {escaped_folder} && ( {command} )'
        else:
            command_to_execute = command

        self.logger.debug(f'Command to be executed: {command_to_execute[:self._MAX_EXEC_COMMAND_LOG_SIZE]}')

        # Note: The default shell will eat one level of escaping, while
        # 'bash -l -c ...' will eat another. Thus, we need to escape again.
        bash_commmand = self._bash_command_str + '-c '

        channel.exec_command(bash_commmand + escape_for_bash(command_to_execute))

        stdin = channel.makefile('wb', bufsize)
        stdout = channel.makefile('rb', bufsize)
        stderr = channel.makefile_stderr('rb', bufsize)

        return stdin, stdout, stderr, channel

    def exec_command_wait_bytes(
        self, command, stdin=None, combine_stderr=False, bufsize=-1, timeout=0.01, workdir: TransportPath = None
    ):
        """Executes the specified command and waits for it to finish.

        :param command: the command to execute
        :param stdin: (optional,default=None) can be a string or a
                   file-like object.
        :param combine_stderr: (optional, default=False) see docstring of
                   self._exec_command_internal()
        :param bufsize: same meaning of paramiko.
        :param timeout: ssh channel timeout for stdout, stderr.
        :param workdir: (optional, default=None) if set, the command will be executed
                in the specified working directory.

        :return: a tuple with (return_value, stdout, stderr) where stdout and stderr
            are both bytes and the return_value is an int.
        """
        import socket
        import time

        if workdir:
            workdir = str(workdir)

        ssh_stdin, stdout, stderr, channel = self._exec_command_internal(
            command, combine_stderr, bufsize=bufsize, workdir=workdir
        )

        if stdin is not None:
            if isinstance(stdin, str):
                filelike_stdin = io.StringIO(stdin)
            elif isinstance(stdin, bytes):
                filelike_stdin = io.BytesIO(stdin)
            elif isinstance(stdin, (io.BufferedIOBase, io.TextIOBase)):
                # It seems both StringIO and BytesIO work correctly when doing ssh_stdin.write(line)?
                # (The ChannelFile is opened with mode 'b', but until now it always has been a StringIO)
                filelike_stdin = stdin
            else:
                raise ValueError('You can only pass strings, bytes, BytesIO or StringIO objects')

            for line in filelike_stdin:
                ssh_stdin.write(line)

        # I flush and close them anyway; important to call shutdown_write
        # to avoid hangouts
        ssh_stdin.flush()
        ssh_stdin.channel.shutdown_write()

        # Now I get the output
        stdout_bytes = []
        stderr_bytes = []
        # 100kB buffer (note that this should be smaller than the window size of paramiko)
        # Also, apparently if the data is coming slowly, the read() command will not unlock even for
        # times much larger than the timeout. Therefore we don't want to have very large buffers otherwise
        # you risk that a lot of output is sent to both stdout and stderr, and stderr goes beyond the
        # window size and blocks.
        # Note that this is different than the bufsize of paramiko.
        internal_bufsize = 100 * 1024

        # Set a small timeout on the channels, so that if we get data from both
        # stderr and stdout, and the connection is slow, we interleave the receive and don't hang
        # NOTE: Timeouts and sleep time below, as well as the internal_bufsize above, have been benchmarked
        # to try to optimize the overall throughput. I could get ~100MB/s on a localhost via ssh (and 3x slower
        # if compression is enabled).
        # It's important to mention that, for speed benchmarks, it's important to disable compression
        # in the SSH transport settings, as it will cap the max speed.
        stdout.channel.settimeout(timeout)
        stderr.channel.settimeout(timeout)  # Maybe redundant, as this could be the same channel.

        while True:
            chunk_exists = False

            if stdout.channel.recv_ready():  # True means that the next .read call will at least receive 1 byte
                chunk_exists = True
                try:
                    piece = stdout.read(internal_bufsize)
                    stdout_bytes.append(piece)
                except socket.timeout:
                    # There was a timeout: I continue as there should still be data
                    pass

            if stderr.channel.recv_stderr_ready():  # True means that the next .read call will at least receive 1 byte
                chunk_exists = True
                try:
                    piece = stderr.read(internal_bufsize)
                    stderr_bytes.append(piece)
                except socket.timeout:
                    # There was a timeout: I continue as there should still be data
                    pass

            # If chunk_exists, there is data (either already read and put in the std*_bytes lists, or
            # still in the buffer because of a timeout). I need to loop.
            # Otherwise, there is no data in the buffers, and I enter this block.
            if not chunk_exists:
                # Both channels have no data in the buffer
                if channel.exit_status_ready():
                    # The remote execution is over

                    # I think that in some corner cases there might still be some data,
                    # in case the data arrived between the previous calls and this check.
                    # So we do a final read. Since the execution is over, I think all data is in the buffers,
                    # so we can just read the whole buffer without loops
                    stdout_bytes.append(stdout.read())
                    stderr_bytes.append(stderr.read())
                    # And we go out of the `while True` loop
                    break
                # The exit status is not ready:
                # I just put a small sleep to avoid infinite fast loops when data
                # is not available on a slow connection, and loop
                time.sleep(0.01)

        # I get the return code (blocking)
        # However, if I am here, the exit status is ready so this should be returning very quickly
        retval = channel.recv_exit_status()

        return (retval, b''.join(stdout_bytes), b''.join(stderr_bytes))

    def gotocomputer_command(self, remotedir: Optional[TransportPath] = None):
        """Specific gotocomputer string to connect to a given remote computer via
        ssh and directly go to the calculation folder.
        """
        further_params = []
        if 'username' in self._connect_args:
            further_params.append(f"-l {escape_for_bash(self._connect_args['username'])}")

        if self._connect_args.get('port'):
            further_params.append(f"-p {self._connect_args['port']}")

        if self._connect_args.get('key_filename'):
            further_params.append(f"-i {escape_for_bash(self._connect_args['key_filename'])}")

        if self._connect_args.get('proxy_jump'):
            further_params.append(f"-o ProxyJump={escape_for_bash(self._connect_args['proxy_jump'])}")

        if self._connect_args.get('proxy_command'):
            further_params.append(f"-o ProxyCommand={escape_for_bash(self._connect_args['proxy_command'])}")

        further_params_str = ' '.join(further_params)

        connect_string = self._gotocomputer_string(remotedir=remotedir)
        cmd = f'ssh -t {self._machine} {further_params_str} {connect_string}'
        return cmd

    def _symlink(self, source: TransportPath, dest: TransportPath):
        """Wrap SFTP symlink call without breaking API

        :param source: source of link
        :param dest: link to create
        """
        source = str(source)
        dest = str(dest)
        self.sftp.symlink(source, dest)

    def symlink(self, remotesource: TransportPath, remotedestination: TransportPath):
        """Create a symbolic link between the remote source and the remote
        destination.

        :param remotesource: remote source. Can contain a pattern.
        :param remotedestination: remote destination
        """
        remotesource = str(remotesource)
        remotedestination = str(remotedestination)
        # paramiko gives some errors if path is starting with '.'
        source = os.path.normpath(remotesource)
        dest = os.path.normpath(remotedestination)

        if has_magic(source):
            if has_magic(dest):
                # if there are patterns in dest, I don't know which name to assign
                raise ValueError('`remotedestination` cannot have patterns')

            # find all files matching pattern
            for this_source in self.glob(source):
                # create the name of the link: take the last part of the path
                this_dest = os.path.join(remotedestination, os.path.split(this_source)[-1])
                self._symlink(this_source, this_dest)
        else:
            self._symlink(source, dest)

    def path_exists(self, path: TransportPath):
        """Check if path exists"""
        import errno

        path = str(path)

        try:
            self.stat(path)
        except OSError as exc:
            if exc.errno == errno.ENOENT:
                return False
            raise
        else:
            return True
