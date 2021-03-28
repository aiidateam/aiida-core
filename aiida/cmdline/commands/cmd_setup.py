# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""The `verdi setup` and `verdi quicksetup` commands."""

import click

from aiida.cmdline.commands.cmd_verdi import verdi
from aiida.cmdline.params import options
from aiida.cmdline.params.options.commands import setup as options_setup
from aiida.cmdline.utils import echo
from aiida.manage.configuration import load_profile
from aiida.manage.manager import get_manager


@verdi.command('setup')
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
@options.CONFIG_FILE()
def setup(
    non_interactive, profile, email, first_name, last_name, institution, db_engine, db_backend, db_host, db_port,
    db_name, db_username, db_password, broker_protocol, broker_username, broker_password, broker_host, broker_port,
    broker_virtual_host, repository
):
    """Setup a new profile."""
    # pylint: disable=too-many-arguments,too-many-locals,unused-argument
    from aiida import orm
    from aiida.manage.configuration import get_config

    profile.database_engine = db_engine
    profile.database_backend = db_backend
    profile.database_name = db_name
    profile.database_port = db_port
    profile.database_hostname = db_host
    profile.database_username = db_username
    profile.database_password = db_password
    profile.broker_protocol = broker_protocol
    profile.broker_username = broker_username
    profile.broker_password = broker_password
    profile.broker_host = broker_host
    profile.broker_port = broker_port
    profile.broker_virtual_host = broker_virtual_host
    profile.repository_uri = f'file://{repository}'

    config = get_config()

    # Creating the profile
    config.add_profile(profile)
    config.set_default_profile(profile.name)

    # Load the profile
    load_profile(profile.name)
    echo.echo_success(f'created new profile `{profile.name}`.')

    # Migrate the database
    echo.echo_info('migrating the database.')
    manager = get_manager()
    backend = manager._load_backend(schema_check=False)  # pylint: disable=protected-access

    try:
        backend.migrate()
    except Exception as exception:  # pylint: disable=broad-except
        echo.echo_critical(
            f'database migration failed, probably because connection details are incorrect:\n{exception}'
        )
    else:
        echo.echo_success('database migration completed.')

    # Retrieve the repository UUID from the database. If set, this means this database is associated with the repository
    # with that UUID and we have to make sure that the provided repository corresponds to it.
    backend_manager = manager.get_backend_manager()
    repository_uuid_database = backend_manager.get_repository_uuid()
    repository_uuid_profile = profile.get_repository_container().container_id

    # If database contains no repository UUID, it should be a clean database so associate it with the repository
    if repository_uuid_database is None:
        backend_manager.set_repository_uuid(repository_uuid_profile)

    # Otherwise, if the database UUID does not match that of the repository, it means they do not belong together. Note
    # that if a new repository path was specified, which does not yet contain a container, the call to retrieve the
    # repo by `get_repository_container` will initialize the container and generate a UUID. This guarantees that if a
    # non-empty database is configured with an empty repository path, this check will hit.
    elif repository_uuid_database != repository_uuid_profile:
        echo.echo_critical(
            f'incompatible database and repository configured:\n'
            f'Database `{db_name}` is associated with the repository with UUID `{repository_uuid_database}`\n'
            f'However, the configured repository `{repository}` has UUID `{repository_uuid_profile}`.'
        )

    # Optionally setting configuration default user settings
    config.set_option('autofill.user.email', email, override=False)
    config.set_option('autofill.user.first_name', first_name, override=False)
    config.set_option('autofill.user.last_name', last_name, override=False)
    config.set_option('autofill.user.institution', institution, override=False)

    # Create the user if it does not yet exist
    created, user = orm.User.objects.get_or_create(
        email=email, first_name=first_name, last_name=last_name, institution=institution
    )
    if created:
        user.store()
    profile.default_user = user.email
    config.update_profile(profile)
    config.store()


@verdi.command('quicksetup')
@options.NON_INTERACTIVE()
# Cannot use `default` because that will fail validation of the `ProfileParamType` if the profile already exists and it
# will be validated before the prompt to choose another. The `contextual_default` however, will not trigger the
# validation but will populate the default in the prompt.
@options_setup.SETUP_PROFILE(contextual_default=lambda x: 'quicksetup')
@options_setup.SETUP_USER_EMAIL()
@options_setup.SETUP_USER_FIRST_NAME()
@options_setup.SETUP_USER_LAST_NAME()
@options_setup.SETUP_USER_INSTITUTION()
@options_setup.QUICKSETUP_DATABASE_ENGINE()
@options_setup.QUICKSETUP_DATABASE_BACKEND()
@options_setup.QUICKSETUP_DATABASE_HOSTNAME()
@options_setup.QUICKSETUP_DATABASE_PORT()
@options_setup.QUICKSETUP_DATABASE_NAME()
@options_setup.QUICKSETUP_DATABASE_USERNAME()
@options_setup.QUICKSETUP_DATABASE_PASSWORD()
@options_setup.QUICKSETUP_SUPERUSER_DATABASE_NAME()
@options_setup.QUICKSETUP_SUPERUSER_DATABASE_USERNAME()
@options_setup.QUICKSETUP_SUPERUSER_DATABASE_PASSWORD()
@options_setup.QUICKSETUP_BROKER_PROTOCOL()
@options_setup.QUICKSETUP_BROKER_USERNAME()
@options_setup.QUICKSETUP_BROKER_PASSWORD()
@options_setup.QUICKSETUP_BROKER_HOST()
@options_setup.QUICKSETUP_BROKER_PORT()
@options_setup.QUICKSETUP_BROKER_VIRTUAL_HOST()
@options_setup.QUICKSETUP_REPOSITORY_URI()
@options.CONFIG_FILE()
@click.pass_context
def quicksetup(
    ctx, non_interactive, profile, email, first_name, last_name, institution, db_engine, db_backend, db_host, db_port,
    db_name, db_username, db_password, su_db_name, su_db_username, su_db_password, broker_protocol, broker_username,
    broker_password, broker_host, broker_port, broker_virtual_host, repository
):
    """Setup a new profile in a fully automated fashion."""
    # pylint: disable=too-many-arguments,too-many-locals
    from aiida.manage.external.postgres import Postgres, manual_setup_instructions

    dbinfo_su = {
        'host': db_host,
        'port': db_port,
        'user': su_db_username,
        'password': su_db_password,
    }
    postgres = Postgres(interactive=not non_interactive, quiet=False, dbinfo=dbinfo_su)

    if not postgres.is_connected:
        echo.echo_critical('failed to determine the PostgreSQL setup')

    try:
        db_username, db_name = postgres.create_dbuser_db_safe(dbname=db_name, dbuser=db_username, dbpass=db_password)
    except Exception as exception:
        echo.echo_error(
            '\n'.join([
                'Oops! quicksetup was unable to create the AiiDA database for you.',
                'See `verdi quicksetup -h` for how to specify non-standard parameters for the postgresql connection.\n'
                'Alternatively, create the AiiDA database yourself: ',
                manual_setup_instructions(dbuser=su_db_username,
                                          dbname=su_db_name), '', 'and then use `verdi setup` instead', ''
            ])
        )
        raise exception

    # The contextual defaults or `verdi setup` are not being called when `invoking`, so we have to explicitly define
    # them here, even though the `verdi setup` command would populate those when called from the command line.
    setup_parameters = {
        'non_interactive': non_interactive,
        'profile': profile,
        'email': email,
        'first_name': first_name,
        'last_name': last_name,
        'institution': institution,
        'db_engine': db_engine,
        'db_backend': db_backend,
        'db_name': db_name,
        # from now on we connect as the AiiDA DB user, which may be forbidden when going via sockets
        'db_host': postgres.host_for_psycopg2,
        'db_port': postgres.port_for_psycopg2,
        'db_username': db_username,
        'db_password': db_password,
        'broker_protocol': broker_protocol,
        'broker_username': broker_username,
        'broker_password': broker_password,
        'broker_host': broker_host,
        'broker_port': broker_port,
        'broker_virtual_host': broker_virtual_host,
        'repository': repository,
    }
    ctx.invoke(setup, **setup_parameters)
