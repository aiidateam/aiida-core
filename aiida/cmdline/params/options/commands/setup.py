# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Reusable command line interface options for the setup commands."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import functools
import click

from aiida.backends import BACKEND_DJANGO, BACKEND_SQLA
from aiida.cmdline.params import options, types
from aiida.cmdline.params.options.interactive import InteractiveOption
from aiida.cmdline.params.options.overridable import OverridableOption
from aiida.manage.configuration import get_config_option, Profile

PASSWORD_UNCHANGED = '***'  # noqa


def get_profile_attribute_default(attribute_tuple, ctx=None):
    """Return the default value for the given attribute of the profile passed in the context.

    :param attribute: attribute for which to get the current value
    :param ctx: click context which should contain the selected profile
    :return: profile attribute default value if set, or None
    """
    if ctx.params['profile'] is None or not isinstance(ctx.params['profile'], Profile):
        raise click.BadParameter('specifying the name of the profile is required', param_hint='"--profile"')

    attribute, default = attribute_tuple
    profile = ctx.params['profile']

    if not profile:
        return default

    try:
        return getattr(profile, attribute)
    except KeyError:
        return default


def get_repository_path_default(ctx):
    """Return the default value for the repository URI for the current profile in the context.

    :param ctx: click context which should contain the selected profile
    :return: default absolute path for the repository
    """
    import os
    from aiida.manage.configuration.settings import AIIDA_CONFIG_FOLDER

    if ctx.params['profile'] is None or not isinstance(ctx.params['profile'], Profile):
        raise click.BadParameter('specifying the name of the profile is required', param_hint='"--profile"')

    return os.path.join(AIIDA_CONFIG_FOLDER, 'repository', ctx.params['profile'].name)


SETUP_PROFILE = OverridableOption(
    '--profile',
    prompt='Profile name',
    help='The name of the new profile.',
    type=types.ProfileParamType(must_exist=False),
    cls=InteractiveOption)

SETUP_USER_EMAIL = OverridableOption(
    '--email',
    'email',
    prompt='User email',
    help='Email address that serves as the user name and a way to identify data created by it.',
    default=get_config_option('user.email'),
    cls=InteractiveOption)

SETUP_USER_FIRST_NAME = OverridableOption(
    '--first-name',
    'first_name',
    prompt='First name',
    help='First name of the user.',
    type=click.STRING,
    default=get_config_option('user.first_name'),
    cls=InteractiveOption)

SETUP_USER_LAST_NAME = OverridableOption(
    '--last-name',
    'last_name',
    prompt='Last name',
    help='Last name of the user.',
    type=click.STRING,
    default=get_config_option('user.last_name'),
    cls=InteractiveOption)

SETUP_USER_INSTITUTION = OverridableOption(
    '--institution',
    'institution',
    prompt='Institution',
    help='Institution of the user.',
    type=click.STRING,
    default=get_config_option('user.institution'),
    cls=InteractiveOption)

SETUP_USER_PASSWORD = OverridableOption(
    '--password',
    'password',
    prompt='Password',
    help='Optional password to connect to REST API.',
    hide_input=True,
    required=False,
    type=click.STRING,
    default=PASSWORD_UNCHANGED,
    confirmation_prompt=True,
    cls=InteractiveOption)

SETUP_DATABASE_ENGINE = OverridableOption(
    '--db-engine',
    prompt='Database engine',
    help='Engine to use to connect to the database.',
    default='postgresql_psycopg2',
    type=click.Choice(['postgresql_psycopg2']),
    contextual_default=functools.partial(get_profile_attribute_default, ('database_engine', 'postgresql_psycopg2')),
    cls=options.interactive.InteractiveOption)

SETUP_DATABASE_BACKEND = OverridableOption(
    '--db-backend',
    prompt='Database backend',
    help='Backend type to use to map the database.',
    type=click.Choice([BACKEND_DJANGO, BACKEND_SQLA]),
    contextual_default=functools.partial(get_profile_attribute_default, ('database_backend', BACKEND_DJANGO)),
    cls=options.interactive.InteractiveOption)

SETUP_DATABASE_HOSTNAME = OverridableOption(
    '--db-host',
    prompt='Database hostname',
    help='Hostname to connect to the database.',
    type=click.STRING,
    contextual_default=functools.partial(get_profile_attribute_default, ('database_hostname', 'localhost')),
    cls=options.interactive.InteractiveOption)

SETUP_DATABASE_PORT = OverridableOption(
    '--db-port',
    prompt='Database port',
    help='Port to connect to the database.',
    type=click.INT,
    contextual_default=functools.partial(get_profile_attribute_default, ('database_port', 5432)),
    cls=options.interactive.InteractiveOption)

SETUP_DATABASE_NAME = OverridableOption(
    '--db-name',
    prompt='Database name',
    help='Name of the database to connect to.',
    type=click.STRING,
    contextual_default=functools.partial(get_profile_attribute_default, ('database_name', None)),
    cls=options.interactive.InteractiveOption)

SETUP_DATABASE_USERNAME = OverridableOption(
    '--db-username',
    prompt='Database username',
    help='User name to connect to the database.',
    type=click.STRING,
    contextual_default=functools.partial(get_profile_attribute_default, ('database_username', None)),
    cls=options.interactive.InteractiveOption)

SETUP_DATABASE_PASSWORD = OverridableOption(
    '--db-password',
    prompt='Database password',
    help='Password to connect to the database.',
    type=click.STRING,
    hide_input=True,
    contextual_default=functools.partial(get_profile_attribute_default, ('database_password', None)),
    cls=options.interactive.InteractiveOption)

SETUP_REPOSITORY_URI = OverridableOption(
    '--repository',
    prompt='Repository directory',
    help='Absolute path for the file system repository.',
    type=click.Path(file_okay=False),
    contextual_default=get_repository_path_default,
    cls=options.interactive.InteractiveOption)
