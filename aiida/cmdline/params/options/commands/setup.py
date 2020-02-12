# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Reusable command line interface options for the setup commands."""

import functools
import getpass
import hashlib

import click

from aiida.backends import BACKEND_DJANGO, BACKEND_SQLA
from aiida.cmdline.params import options, types
from aiida.manage.configuration import get_config, get_config_option, Profile
from aiida.manage.external.postgres import DEFAULT_DBINFO

PASSWORD_UNCHANGED = '***'  # noqa


def validate_profile_parameter(ctx):
    """Validate that the context contains the option `profile` and it contains a `Profile` instance.

    :param ctx: click context which should contain the selected profile
    :raises: BadParameter if the context does not contain a `Profile` instance for option `profile`
    """
    option = 'profile'
    if option not in ctx.params or ctx.params[option] is None or not isinstance(ctx.params[option], Profile):
        raise click.BadParameter('specifying the name of the profile is required', param_hint='"--{}"'.format(option))


def get_profile_attribute_default(attribute_tuple, ctx):
    """Return the default value for the given attribute of the profile passed in the context.

    :param attribute: attribute for which to get the current value
    :param ctx: click context which should contain the selected profile
    :return: profile attribute default value if set, or None
    """
    attribute, default = attribute_tuple

    try:
        validate_profile_parameter(ctx)
    except click.BadParameter:
        return default
    else:
        try:
            return getattr(ctx.params['profile'], attribute)
        except KeyError:
            return default


def get_repository_uri_default(ctx):
    """Return the default value for the repository URI for the current profile in the click context.

    :param ctx: click context which should contain the selected profile
    :return: default repository URI
    """
    import os
    from aiida.manage.configuration.settings import AIIDA_CONFIG_FOLDER

    validate_profile_parameter(ctx)

    return os.path.join(AIIDA_CONFIG_FOLDER, 'repository', ctx.params['profile'].name)


def get_quicksetup_repository_uri(ctx, param, value):  # pylint: disable=unused-argument
    """Return the repository URI to be used as default in `verdi quicksetup`

    :param ctx: click context which should contain the contextual parameters
    :return: the repository URI
    """
    return get_repository_uri_default(ctx)


def get_quicksetup_database_name(ctx, param, value):  # pylint: disable=unused-argument
    """Determine the database name to be used as default for the Postgres connection in `verdi quicksetup`

    If a value is explicitly passed, that value is returned unchanged.

    If no value is passed, the name will be <profile_name>_<os_user>_<hash>, where <os_user> is the name of the current
    operating system user and <hash> is a hash of the path of the configuration directory.

    Note: This ensures that profiles named ``test_...`` will have databases named ``test_...`` .

    :param ctx: click context which should contain the contextual parameters
    :return: the database name
    """
    if value is not None:
        return value

    config = get_config()
    profile = ctx.params['profile'].name
    config_hash = hashlib.md5(config.dirpath.encode('utf-8')).hexdigest()
    database_name = '{profile}_{user}_{hash}'.format(profile=profile, user=getpass.getuser(), hash=config_hash)

    return database_name


def get_quicksetup_username(ctx, param, value):  # pylint: disable=unused-argument
    """Determine the username to be used as default for the Postgres connection in `verdi quicksetup`

    If a value is explicitly passed, that value is returned. If there is no value, the name will be based on the
    name of the current operating system user and the hash of the path of the configuration directory.

    :param ctx: click context which should contain the contextual parameters
    :return: the username
    """
    if value is not None:
        return value

    config = get_config()
    config_hash = hashlib.md5(config.dirpath.encode('utf-8')).hexdigest()
    username = 'aiida_qs_{user}_{hash}'.format(user=getpass.getuser(), hash=config_hash)

    return username


def get_quicksetup_password(ctx, param, value):  # pylint: disable=unused-argument
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
        if available_profile.database_username == username:
            value = available_profile.database_password
            break
    else:
        value = get_random_string(16)

    return value


SETUP_PROFILE = options.OverridableOption(
    '--profile',
    prompt='Profile name',
    help='The name of the new profile.',
    required=True,
    type=types.ProfileParamType(cannot_exist=True),
    cls=options.interactive.InteractiveOption
)

SETUP_USER_EMAIL = options.OverridableOption(
    '--email',
    'email',
    prompt='User email',
    help='Email address that serves as the user name and a way to identify data created by it.',
    default=get_config_option('user.email'),
    required_fn=lambda x: get_config_option('user.email') is None,
    required=True,
    cls=options.interactive.InteractiveOption
)

SETUP_USER_FIRST_NAME = options.OverridableOption(
    '--first-name',
    'first_name',
    prompt='First name',
    help='First name of the user.',
    type=click.STRING,
    default=get_config_option('user.first_name'),
    required_fn=lambda x: get_config_option('user.first_name') is None,
    required=True,
    cls=options.interactive.InteractiveOption
)

SETUP_USER_LAST_NAME = options.OverridableOption(
    '--last-name',
    'last_name',
    prompt='Last name',
    help='Last name of the user.',
    type=click.STRING,
    default=get_config_option('user.last_name'),
    required_fn=lambda x: get_config_option('user.last_name') is None,
    required=True,
    cls=options.interactive.InteractiveOption
)

SETUP_USER_INSTITUTION = options.OverridableOption(
    '--institution',
    'institution',
    prompt='Institution',
    help='Institution of the user.',
    type=click.STRING,
    default=get_config_option('user.institution'),
    required_fn=lambda x: get_config_option('user.institution') is None,
    required=True,
    cls=options.interactive.InteractiveOption
)

SETUP_USER_PASSWORD = options.OverridableOption(
    '--password',
    'password',
    prompt='Password',
    help='Optional password to connect to REST API.',
    hide_input=True,
    type=click.STRING,
    default=PASSWORD_UNCHANGED,
    confirmation_prompt=True,
    cls=options.interactive.InteractiveOption
)

QUICKSETUP_DATABASE_ENGINE = options.OverridableOption(
    '--db-engine',
    help='Engine to use to connect to the database.',
    default='postgresql_psycopg2',
    type=click.Choice(['postgresql_psycopg2'])
)

QUICKSETUP_DATABASE_BACKEND = options.OverridableOption(
    '--db-backend',
    help='Backend type to use to map the database.',
    default=BACKEND_DJANGO,
    type=click.Choice([BACKEND_DJANGO, BACKEND_SQLA])
)

QUICKSETUP_DATABASE_HOSTNAME = options.OverridableOption(
    '--db-host', help='Hostname to connect to the database.', default=DEFAULT_DBINFO['host'], type=click.STRING
)

QUICKSETUP_DATABASE_PORT = options.OverridableOption(
    '--db-port', help='Port to connect to the database.', default=DEFAULT_DBINFO['port'], type=click.INT
)

QUICKSETUP_DATABASE_NAME = options.OverridableOption(
    '--db-name', help='Name of the database to create.', type=click.STRING, callback=get_quicksetup_database_name
)

QUICKSETUP_DATABASE_USERNAME = options.OverridableOption(
    '--db-username', help='Name of the database user to create.', type=click.STRING, callback=get_quicksetup_username
)

QUICKSETUP_DATABASE_PASSWORD = options.OverridableOption(
    '--db-password',
    help='Password to connect to the database.',
    type=click.STRING,
    hide_input=True,
    callback=get_quicksetup_password
)

QUICKSETUP_SUPERUSER_DATABASE_USERNAME = options.OverridableOption(
    '--su-db-username', help='User name of the database super user.', type=click.STRING, default=DEFAULT_DBINFO['user']
)

QUICKSETUP_SUPERUSER_DATABASE_NAME = options.OverridableOption(
    '--su-db-name',
    help='Name of the template database to connect to as the database superuser.',
    type=click.STRING,
    default=DEFAULT_DBINFO['database']
)

QUICKSETUP_SUPERUSER_DATABASE_PASSWORD = options.OverridableOption(
    '--su-db-password',
    help='Password to connect as the database superuser.',
    type=click.STRING,
    hide_input=True,
    default=DEFAULT_DBINFO['password']
)

QUICKSETUP_REPOSITORY_URI = options.OverridableOption(
    '--repository',
    help='Absolute path for the file system repository.',
    type=click.Path(file_okay=False),
    callback=get_quicksetup_repository_uri  # Cannot use `default` because `ctx` is needed to determine the default
)

SETUP_DATABASE_ENGINE = QUICKSETUP_DATABASE_ENGINE.clone(
    prompt='Database engine',
    contextual_default=functools.partial(get_profile_attribute_default, ('database_engine', 'postgresql_psycopg2')),
    cls=options.interactive.InteractiveOption
)

SETUP_DATABASE_BACKEND = QUICKSETUP_DATABASE_BACKEND.clone(
    prompt='Database backend',
    contextual_default=functools.partial(get_profile_attribute_default, ('database_backend', BACKEND_DJANGO)),
    cls=options.interactive.InteractiveOption
)

SETUP_DATABASE_HOSTNAME = QUICKSETUP_DATABASE_HOSTNAME.clone(
    prompt='Database hostname',
    contextual_default=functools.partial(get_profile_attribute_default, ('database_hostname', 'localhost')),
    cls=options.interactive.InteractiveOption
)

SETUP_DATABASE_PORT = QUICKSETUP_DATABASE_PORT.clone(
    prompt='Database port',
    contextual_default=functools.partial(get_profile_attribute_default, ('database_port', 5432)),
    cls=options.interactive.InteractiveOption
)

SETUP_DATABASE_NAME = QUICKSETUP_DATABASE_NAME.clone(
    prompt='Database name',
    required=True,
    contextual_default=functools.partial(get_profile_attribute_default, ('database_name', None)),
    cls=options.interactive.InteractiveOption
)

SETUP_DATABASE_USERNAME = QUICKSETUP_DATABASE_USERNAME.clone(
    prompt='Database username',
    required=True,
    contextual_default=functools.partial(get_profile_attribute_default, ('database_username', None)),
    cls=options.interactive.InteractiveOption
)

SETUP_DATABASE_PASSWORD = QUICKSETUP_DATABASE_PASSWORD.clone(
    prompt='Database password',
    required=True,
    contextual_default=functools.partial(get_profile_attribute_default, ('database_password', None)),
    cls=options.interactive.InteractiveOption
)

SETUP_REPOSITORY_URI = QUICKSETUP_REPOSITORY_URI.clone(
    prompt='Repository directory',
    callback=None,  # Unset the `callback` to define the default, which is instead done by the `contextual_default`
    contextual_default=get_repository_uri_default,
    cls=options.interactive.InteractiveOption
)
