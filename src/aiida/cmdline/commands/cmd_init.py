###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""``verdi init`` command."""

import pathlib

import click

from aiida.cmdline.commands.cmd_verdi import verdi
from aiida.cmdline.utils import echo
from aiida.manage.configuration import get_config_option


@verdi.command('init')
@click.argument(
    'directory', type=click.Path(exists=False, path_type=pathlib.Path, resolve_path=True), default=pathlib.Path.cwd()
)
@click.option(
    '--from-archive',
    type=click.Path(dir_okay=False, exists=True, resolve_path=True, path_type=pathlib.Path),
    help='Mount the archive as a read-only profile instead of creating an empty profile.',
)
@click.option(
    '--email',
    default=get_config_option('autofill.user.email') or 'aiida@localhost',
    show_default=True,
    help='The email of the user.',
)
@click.option(
    '--first-name',
    default=get_config_option('autofill.user.first_name') or 'John',
    show_default=True,
    help='The first name of the user.',
)
@click.option(
    '--last-name',
    default=get_config_option('autofill.user.last_name') or 'Doe',
    show_default=True,
    help='The last name of the user.',
)
@click.option(
    '--institution',
    default=get_config_option('autofill.user.institution') or 'Unknown',
    show_default=True,
    help='The institution of the user.',
)
def verdi_init(directory, from_archive, email, first_name, last_name, institution):
    """Initialize a new AiiDA instance.

    The instance is initialized in DIRECTORY, which defaults to the current working directory. A profile is
    automatically created using the `core.sqlite_dos` storage backend and the localhost is configured as a computer.

    By default, a user is created in the database that is automatically attached to all the nodes that will be created
    in the future. The user details are specified by default but can be customized using a number of options that this
    command exposes.
    """
    import tempfile
    import warnings

    from aiida.common import exceptions
    from aiida.manage import get_manager
    from aiida.manage.configuration import create_profile, get_config, load_profile, reset_config, settings
    from aiida.orm import Computer

    # Unload the profile that was loaded by default and reset the configuration.
    get_manager().unload_profile()
    reset_config()

    dirpath_config = directory / settings.DEFAULT_CONFIG_DIR_NAME

    if dirpath_config.is_dir():
        echo.echo_critical(f'A configuration directory already exists in `{directory}`.')

    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        settings.set_configuration_directory(dirpath_config)

    echo.echo_success(f'Initialized new AiiDA instance in `{dirpath_config}`.')

    # Now load the config causing the configuration file to be created.
    config = get_config(create=True)
    dirpath_loaded = pathlib.Path(config.filepath).parent
    assert dirpath_loaded == dirpath_config, f'Filepath of loaded config `{dirpath_loaded}` != `{dirpath_config}`.'

    if from_archive:
        storage_backend = 'core.sqlite_zip'
        storage_config = {
            'filepath': str(from_archive),
        }
    else:
        storage_backend = 'core.sqlite_dos'
        storage_config = {}

    try:
        profile = create_profile(
            config,
            name='init',
            email=email,
            first_name=first_name,
            last_name=last_name,
            institution=institution,
            storage_backend=storage_backend,
            storage_config=storage_config,
        )
    except (ValueError, TypeError, exceptions.EntryPointError, exceptions.StorageMigrationError) as exception:
        echo.echo_critical(str(exception))

    echo.echo_success(f'Created new profile `{profile.name}`.')

    config.set_option('runner.poll.interval', 1, scope=profile.name)
    config.set_default_profile(profile.name, overwrite=True)
    config.store()

    if not from_archive:
        echo.echo_info(f'Loaded newly created profile `{profile.name}`.')
        load_profile(profile.name, allow_switch=True)

        computer = Computer(
            label='localhost',
            hostname='localhost',
            description='Localhost automatically created by `verdi blitz`',
            transport_type='core.local',
            scheduler_type='core.direct',
            workdir=str(pathlib.Path(tempfile.gettempdir()) / 'aiida_scratch'),
        ).store()
        computer.configure(safe_interval=0)
        computer.set_minimum_job_poll_interval(1)
        computer.set_default_mpiprocs_per_machine(1)

        echo.echo_success('Configured the localhost as a computer.')
