###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""The `verdi setup` command."""

import pathlib

import click

from aiida.cmdline.commands.cmd_verdi import verdi
from aiida.cmdline.params import options
from aiida.cmdline.params.options.commands import setup as options_setup
from aiida.cmdline.utils import echo
from aiida.manage.configuration import Profile, load_profile


@verdi.command('setup', deprecated='Please use `verdi profile setup` instead.')
@options.NON_INTERACTIVE()
@options_setup.SETUP_PROFILE()
@options_setup.SETUP_USER_EMAIL()
@options_setup.SETUP_USER_FIRST_NAME()
@options_setup.SETUP_USER_LAST_NAME()
@options_setup.SETUP_USER_INSTITUTION()
@options_setup.SETUP_DATABASE_ENGINE()
@options_setup.SETUP_DATABASE_BACKEND()
@options_setup.SETUP_DATABASE_HOSTNAME()
@options_setup.SETUP_DATABASE_PORT()
@options_setup.SETUP_DATABASE_NAME()
@options_setup.SETUP_DATABASE_USERNAME()
@options_setup.SETUP_DATABASE_PASSWORD()
@options_setup.SETUP_BROKER_PROTOCOL()
@options_setup.SETUP_BROKER_USERNAME()
@options_setup.SETUP_BROKER_PASSWORD()
@options_setup.SETUP_BROKER_HOST()
@options_setup.SETUP_BROKER_PORT()
@options_setup.SETUP_BROKER_VIRTUAL_HOST()
@options_setup.SETUP_REPOSITORY_URI()
@options_setup.SETUP_TEST_PROFILE()
@options_setup.SETUP_PROFILE_UUID()
@options.CONFIG_FILE()
@click.pass_context
def setup(
    ctx,
    non_interactive,
    profile: Profile,
    email,
    first_name,
    last_name,
    institution,
    db_engine,
    db_backend,
    db_host,
    db_port,
    db_name,
    db_username,
    db_password,
    broker_protocol,
    broker_username,
    broker_password,
    broker_host,
    broker_port,
    broker_virtual_host,
    repository,
    test_profile,
    profile_uuid,
):
    """Setup a new profile (use `verdi profile setup`).

    This method assumes that an empty PSQL database has been created and that the database user has been created.
    """
    from aiida import orm
    from aiida.cmdline.utils.common import confirm_development_version

    confirm_development_version()

    # store default user settings so user does not have to re-enter them
    _store_default_user_settings(ctx.obj.config, email, first_name, last_name, institution)

    if profile_uuid is not None:
        profile.uuid = profile_uuid

    if non_interactive and db_engine != 'postgresql_psycopg':
        echo.echo_deprecated('The `--db-engine` option is deprecated and has no effect.')

    profile.set_storage(
        db_backend,
        {
            'database_engine': db_engine,
            'database_hostname': db_host,
            'database_port': db_port,
            'database_name': db_name,
            'database_username': db_username,
            'database_password': db_password,
            'repository_uri': pathlib.Path(f'{repository}').as_uri(),
        },
    )
    profile.set_process_controller(
        'rabbitmq',
        {
            'broker_protocol': broker_protocol,
            'broker_username': broker_username,
            'broker_password': broker_password,
            'broker_host': broker_host,
            'broker_port': broker_port,
            'broker_virtual_host': broker_virtual_host,
        },
    )
    profile.is_test_profile = test_profile

    config = ctx.obj.config

    # Create the profile, set it as the default and load it
    config.add_profile(profile)
    config.set_default_profile(profile.name)
    load_profile(profile.name)

    # Initialise the storage
    echo.echo_report('initialising the profile storage.')

    try:
        profile.storage_cls.initialise(profile)
    except Exception as exception:
        echo.echo_critical(
            f'storage initialisation failed, probably because connection details are incorrect:\n{exception}'
        )
    else:
        echo.echo_success('storage initialisation completed.')

    # Create the user if it does not yet exist
    created, user = orm.User.collection.get_or_create(
        email=email, first_name=first_name, last_name=last_name, institution=institution
    )
    if created:
        user.store()
    config.set_default_user_email(profile, user.email)

    # store the updated configuration
    config.store()
    echo.echo_success(f'created new profile `{profile.name}`.')


def _store_default_user_settings(config, email, first_name, last_name, institution):
    """Store the default user settings if not already present."""
    config.set_option('autofill.user.email', email, override=False)
    config.set_option('autofill.user.first_name', first_name, override=False)
    config.set_option('autofill.user.last_name', last_name, override=False)
    config.set_option('autofill.user.institution', institution, override=False)
    config.store()
