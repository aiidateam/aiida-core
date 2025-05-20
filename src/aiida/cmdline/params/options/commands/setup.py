###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Reusable command line interface options for the setup commands."""

from __future__ import annotations

import functools
import getpass
import typing as t

import click

from aiida.brokers.rabbitmq.defaults import BROKER_DEFAULTS
from aiida.cmdline.params import options, types
from aiida.manage.configuration import Profile, get_config, get_config_option
from aiida.manage.external.postgres import DEFAULT_DBINFO  # type: ignore[attr-defined]

PASSWORD_UNCHANGED = '***'


def validate_profile_parameter(ctx: click.Context) -> None:
    """Validate that the context contains the option `profile` and it contains a `Profile` instance.

    :param ctx: click context which should contain the selected profile
    :raises: BadParameter if the context does not contain a `Profile` instance for option `profile`
    """
    option = 'profile'
    if option not in ctx.params or ctx.params[option] is None or not isinstance(ctx.params[option], Profile):
        raise click.BadParameter('specifying the name of the profile is required', param_hint=f'"--{option}"')


def get_profile_attribute_default(attribute_tuple: tuple[str, t.Any], ctx: click.Context) -> t.Any:
    """Return the default value for the given attribute of the profile passed in the context.

    :param attribute_tuple: attribute for which to get the current value, and its default
    :param ctx: click context which should contain the selected profile
    :return: profile attribute default value if set, or None
    """
    attribute, default = attribute_tuple
    parts = attribute.split('.')

    try:
        validate_profile_parameter(ctx)
    except click.BadParameter:
        return default

    try:
        data = ctx.params['profile'].dictionary
        for part in parts:
            if data is None:
                return default
            data = data[part]
        return data
    except KeyError:
        return default


def get_repository_uri_default(ctx: click.Context) -> str:
    """Return the default value for the repository URI for the current profile in the click context.

    :param ctx: click context which should contain the selected profile
    :return: default repository URI
    """
    import os

    from aiida.manage.configuration.settings import AiiDAConfigDir

    validate_profile_parameter(ctx)
    configure_directory = AiiDAConfigDir.get()

    return os.path.join(configure_directory, 'repository', ctx.params['profile'].name)


def get_quicksetup_repository_uri(ctx: click.Context, _param: click.Parameter, _value: t.Any) -> str:
    """Return the repository URI to be used as default in `verdi quicksetup`

    :param ctx: click context which should contain the contextual parameters
    :return: the repository URI
    """
    return get_repository_uri_default(ctx)


def get_quicksetup_database_name(ctx: click.Context, _param: click.Parameter, value: str | None) -> str:
    """Determine the database name to be used as default for the Postgres connection in `verdi quicksetup`

    If a value is explicitly passed, that value is returned unchanged.

    If no value is passed, the name will be <profile_name>_<os_user>_<hash>, where <os_user> is the name of the current
    operating system user and <hash> is a hash of the path of the configuration directory.

    Note: This ensures that profiles named ``test_...`` will have databases named ``test_...`` .

    :param ctx: click context which should contain the contextual parameters
    :return: the database name
    """
    import hashlib

    if value is not None:
        return value

    config = get_config()
    profile = ctx.params['profile'].name
    config_hash = hashlib.md5(config.dirpath.encode('utf-8')).hexdigest()
    database_name = f'{profile}_{getpass.getuser()}_{config_hash}'

    return database_name


def get_quicksetup_username(ctx: click.Context, param: click.Parameter, value: str | None) -> str:
    """Determine the username to be used as default for the Postgres connection in `verdi quicksetup`

    If a value is explicitly passed, that value is returned. If there is no value, the name will be based on the
    name of the current operating system user and the hash of the path of the configuration directory.

    :param ctx: click context which should contain the contextual parameters
    :return: the username
    """
    import hashlib

    if value is not None:
        return value

    config = get_config()
    config_hash = hashlib.md5(config.dirpath.encode('utf-8')).hexdigest()
    username = f'aiida_qs_{getpass.getuser()}_{config_hash}'

    return username


def get_quicksetup_password(ctx: click.Context, param: click.Parameter, value: str | None) -> str:
    """Determine the password to be used as default for the Postgres connection in `verdi quicksetup`

    If a value is explicitly passed, that value is returned. If there is no value, the current username in the context
    will be scanned for in currently existing profiles. If it does, the corresponding password will be used. If no such
    user already exists, a random password will be generated.

    :param ctx: click context which should contain the contextual parameters
    :return: the password
    """
    from aiida.common.hashing import get_random_string

    if value is not None:
        return value

    username = ctx.params['db_username']
    config = get_config()

    for available_profile in config.profiles:
        if available_profile.storage_backend == 'core.psql_dos':
            storage_config = available_profile.storage_config
            if storage_config['database_username'] == username:
                value = storage_config['database_password']
                break
    else:
        value = get_random_string(16)

    return value


SETUP_PROFILE_UUID = options.OverridableOption(
    '--profile-uuid',
    prompt='Profile UUID',
    prompt_fn=lambda x: False,  # This option should not be prompted for.
    help='The UUID of the profile. This should only be defined if configuring a profile that should connect to the '
    'same services of a profile that is already configured in another AiiDA instance, in which case the profile UUIDs '
    'need to be identical.',
    required=False,
    hidden=True,
    type=str,
    cls=options.interactive.InteractiveOption,
)

SETUP_PROFILE = options.OverridableOption(
    '--profile',
    prompt='Profile name',
    help='The name of the new profile.',
    required=True,
    type=types.ProfileParamType(cannot_exist=True),
    cls=options.interactive.InteractiveOption,
)

SETUP_PROFILE_NAME = options.OverridableOption(
    '-p',
    '--profile-name',
    'profile',
    prompt='Profile name',
    help='The name of the new profile.',
    required=True,
    type=types.ProfileParamType(cannot_exist=True),
    cls=options.interactive.InteractiveOption,
)

SETUP_PROFILE_SET_AS_DEFAULT = options.OverridableOption(
    '--set-as-default/--no-set-as-default',
    prompt='Set as default?',
    help='Whether to set the profile as the default.',
    is_flag=True,
    default=True,
    cls=options.interactive.InteractiveOption,
)

SETUP_USER_EMAIL = options.USER_EMAIL.clone(
    prompt='Email Address (for sharing data)',
    default=functools.partial(get_config_option, 'autofill.user.email'),
    required=True,
    cls=options.interactive.InteractiveOption,
)

SETUP_USER_FIRST_NAME = options.USER_FIRST_NAME.clone(
    prompt='First name',
    default=lambda: get_config_option('autofill.user.first_name') or 'John',
    required=True,
    cls=options.interactive.InteractiveOption,
)

SETUP_USER_LAST_NAME = options.USER_LAST_NAME.clone(
    prompt='Last name',
    default=lambda: get_config_option('autofill.user.last_name') or 'Doe',
    required=True,
    cls=options.interactive.InteractiveOption,
)

SETUP_USER_INSTITUTION = options.USER_INSTITUTION.clone(
    prompt='Institution',
    default=lambda: get_config_option('autofill.user.institution') or 'Unknown',
    required=True,
    cls=options.interactive.InteractiveOption,
)

QUICKSETUP_DATABASE_ENGINE = options.DB_ENGINE

QUICKSETUP_DATABASE_BACKEND = options.DB_BACKEND

QUICKSETUP_DATABASE_HOSTNAME = options.DB_HOST

QUICKSETUP_DATABASE_PORT = options.DB_PORT

QUICKSETUP_DATABASE_NAME = options.OverridableOption(
    '--db-name',
    help='Name of the database to create.',
    type=types.NonEmptyStringParamType(),
    callback=get_quicksetup_database_name,
)

QUICKSETUP_DATABASE_USERNAME = options.DB_USERNAME.clone(
    help='Name of the database user to create.', callback=get_quicksetup_username
)

QUICKSETUP_DATABASE_PASSWORD = options.DB_PASSWORD.clone(callback=get_quicksetup_password)

QUICKSETUP_SUPERUSER_DATABASE_USERNAME = options.OverridableOption(
    '--su-db-username', help='User name of the database super user.', type=click.STRING, default=DEFAULT_DBINFO['user']
)

QUICKSETUP_SUPERUSER_DATABASE_NAME = options.OverridableOption(
    '--su-db-name',
    help='Name of the template database to connect to as the database superuser.',
    type=click.STRING,
    default=DEFAULT_DBINFO['dbname'],
)

QUICKSETUP_SUPERUSER_DATABASE_PASSWORD = options.OverridableOption(
    '--su-db-password',
    help='Password to connect as the database superuser.',
    type=click.STRING,
    hide_input=True,
    default=DEFAULT_DBINFO['password'],
)

QUICKSETUP_BROKER_PROTOCOL = options.BROKER_PROTOCOL

QUICKSETUP_BROKER_USERNAME = options.BROKER_USERNAME

QUICKSETUP_BROKER_PASSWORD = options.BROKER_PASSWORD

QUICKSETUP_BROKER_HOST = options.BROKER_HOST

QUICKSETUP_BROKER_PORT = options.BROKER_PORT

QUICKSETUP_BROKER_VIRTUAL_HOST = options.BROKER_VIRTUAL_HOST

QUICKSETUP_REPOSITORY_URI = options.REPOSITORY_PATH.clone(
    callback=get_quicksetup_repository_uri  # Cannot use `default` because `ctx` is needed to determine the default
)

SETUP_DATABASE_ENGINE = QUICKSETUP_DATABASE_ENGINE.clone(
    prompt='Database engine',
    contextual_default=functools.partial(
        get_profile_attribute_default, ('storage.config.database_engine', 'postgresql_psycopg')
    ),
    cls=options.interactive.InteractiveOption,
)

SETUP_DATABASE_BACKEND = QUICKSETUP_DATABASE_BACKEND.clone(
    prompt='Database backend',
    contextual_default=functools.partial(get_profile_attribute_default, ('storage_backend', 'core.psql_dos')),
    cls=options.interactive.InteractiveOption,
)

SETUP_DATABASE_HOSTNAME = QUICKSETUP_DATABASE_HOSTNAME.clone(
    prompt='Database host',
    contextual_default=functools.partial(
        get_profile_attribute_default, ('storage.config.database_hostname', 'localhost')
    ),
    cls=options.interactive.InteractiveOption,
)

SETUP_DATABASE_PORT = QUICKSETUP_DATABASE_PORT.clone(
    prompt='Database port',
    contextual_default=functools.partial(
        get_profile_attribute_default, ('storage.config.database_port', DEFAULT_DBINFO['port'])
    ),
    cls=options.interactive.InteractiveOption,
)

SETUP_DATABASE_NAME = QUICKSETUP_DATABASE_NAME.clone(
    prompt='Database name',
    required=True,
    contextual_default=functools.partial(get_profile_attribute_default, ('storage.config.database_name', None)),
    cls=options.interactive.InteractiveOption,
)

SETUP_DATABASE_USERNAME = QUICKSETUP_DATABASE_USERNAME.clone(
    prompt='Database username',
    required=True,
    contextual_default=functools.partial(get_profile_attribute_default, ('storage.config.database_username', None)),
    cls=options.interactive.InteractiveOption,
)

SETUP_DATABASE_PASSWORD = QUICKSETUP_DATABASE_PASSWORD.clone(
    prompt='Database password',
    required=True,
    contextual_default=functools.partial(get_profile_attribute_default, ('storage.config.database_password', None)),
    cls=options.interactive.InteractiveOption,
)

SETUP_USE_RABBITMQ = options.OverridableOption(
    '--use-rabbitmq/--no-use-rabbitmq',
    prompt='Use RabbitMQ?',
    is_flag=True,
    default=True,
    cls=options.interactive.InteractiveOption,
    help='Whether to configure the RabbitMQ broker. Required to enable the daemon and submitting processes.',
)

SETUP_BROKER_PROTOCOL = QUICKSETUP_BROKER_PROTOCOL.clone(
    prompt='Broker protocol',
    required=True,
    contextual_default=functools.partial(
        get_profile_attribute_default, ('process_control.config.broker_protocol', BROKER_DEFAULTS.protocol)
    ),
    cls=options.interactive.InteractiveOption,
)

SETUP_BROKER_USERNAME = QUICKSETUP_BROKER_USERNAME.clone(
    prompt='Broker username',
    required=True,
    contextual_default=functools.partial(
        get_profile_attribute_default, ('process_control.config.broker_username', BROKER_DEFAULTS.username)
    ),
    cls=options.interactive.InteractiveOption,
)

SETUP_BROKER_PASSWORD = QUICKSETUP_BROKER_PASSWORD.clone(
    prompt='Broker password',
    required=True,
    contextual_default=functools.partial(
        get_profile_attribute_default, ('process_control.config.broker_password', BROKER_DEFAULTS.password)
    ),
    cls=options.interactive.InteractiveOption,
)

SETUP_BROKER_HOST = QUICKSETUP_BROKER_HOST.clone(
    prompt='Broker host',
    required=True,
    contextual_default=functools.partial(
        get_profile_attribute_default, ('process_control.config.broker_host', BROKER_DEFAULTS.host)
    ),
    cls=options.interactive.InteractiveOption,
)

SETUP_BROKER_PORT = QUICKSETUP_BROKER_PORT.clone(
    prompt='Broker port',
    required=True,
    contextual_default=functools.partial(
        get_profile_attribute_default, ('process_control.config.broker_port', BROKER_DEFAULTS.port)
    ),
    cls=options.interactive.InteractiveOption,
)

SETUP_BROKER_VIRTUAL_HOST = QUICKSETUP_BROKER_VIRTUAL_HOST.clone(
    prompt='Broker virtual host name',
    required=True,
    contextual_default=functools.partial(
        get_profile_attribute_default, ('process_control.config.broker_virtual_host', BROKER_DEFAULTS.virtual_host)
    ),
    cls=options.interactive.InteractiveOption,
)

SETUP_REPOSITORY_URI = QUICKSETUP_REPOSITORY_URI.clone(
    prompt='Repository directory',
    required=True,
    callback=None,  # Unset the `callback` to define the default, which is instead done by the `contextual_default`
    contextual_default=get_repository_uri_default,
    cls=options.interactive.InteractiveOption,
)

SETUP_TEST_PROFILE = options.OverridableOption(
    '--test-profile', is_flag=True, help='Designate the profile to be used for running the test suite only.'
)

QUICKSETUP_TEST_PROFILE = SETUP_TEST_PROFILE.clone()
