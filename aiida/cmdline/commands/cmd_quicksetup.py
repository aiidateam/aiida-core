# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=too-many-arguments,too-many-locals,too-many-statements,too-many-branches
"""`verdi quicksetup` command."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import os
import sys
import hashlib

import click

from aiida.cmdline.commands.cmd_verdi import verdi
from aiida.cmdline.params import arguments, options
from aiida.cmdline.utils import echo
from aiida.manage.external.postgres import Postgres, manual_setup_instructions, prompt_db_info
from aiida.manage.configuration.setup import setup_profile


def _check_db_name(dbname, postgres):
    """Looks up if a database with the name exists, prompts for using or creating a differently named one."""
    create = True
    while create and postgres.db_exists(dbname):
        echo.echo_info('database {} already exists!'.format(dbname))
        if not click.confirm('Use it (make sure it is not used by another profile)?'):
            dbname = click.prompt('new name', type=str, default=dbname)
        else:
            create = False
    return dbname, create


@verdi.command('quicksetup')
@arguments.PROFILE_NAME(default='quicksetup')
@options.PROFILE_ONLY_CONFIG()
@options.PROFILE_SET_DEFAULT()
@options.NON_INTERACTIVE()
@options.BACKEND()
@options.DB_HOST()
@options.DB_PORT()
@options.DB_NAME()
@options.DB_USERNAME()
@options.DB_PASSWORD()
@options.REPOSITORY_PATH()
@options.USER_EMAIL()
@options.USER_FIRST_NAME()
@options.USER_LAST_NAME()
@options.USER_INSTITUTION()
def quicksetup(profile_name, only_config, set_default, non_interactive, backend, db_host, db_port, db_name, db_username,
               db_password, repository, email, first_name, last_name, institution):
    """Set up a sane configuration with as little interaction as possible."""
    import getpass
    from aiida.common.hashing import get_random_string
    from aiida.manage.configuration.utils import load_config
    from aiida.manage.configuration.setup import create_instance_directories

    create_instance_directories()
    config = load_config(create=True)

    # create a profile, by default 'quicksetup' and prompt the user if already exists
    profile_name = profile_name or 'quicksetup'
    write_profile = False
    while not write_profile:
        if profile_name in config.profile_names:
            echo.echo_warning("Profile '{}' already exists.".format(profile_name))
            if click.confirm("Overwrite existing profile '{}'?".format(profile_name)):
                write_profile = True
            else:
                profile_name = click.prompt('New profile name', type=str)
        else:
            write_profile = True

    # access postgres
    dbinfo = {'host': db_host, 'port': db_port}
    postgres = Postgres(interactive=bool(not non_interactive), quiet=False, dbinfo=dbinfo)
    postgres.set_setup_fail_callback(prompt_db_info)
    success = postgres.determine_setup()
    if not success:
        sys.exit(1)

    osuser = getpass.getuser()
    config_dir_hash = hashlib.md5(config.dirpath.encode('utf-8')).hexdigest()

    # default database user name is aiida_qs_<login-name>
    # default password is random
    # default database name is <profile_name>_<login-name>
    # this ensures that for profiles named test_... the database will also be named test_...
    dbuser = db_username or 'aiida_qs_' + osuser + '_' + config_dir_hash
    dbpass = db_password or get_random_string(length=50)

    # check if there is a profile that contains the db user already
    # and if yes, take the db user password from there
    # This is ok because a user can only see his own config files
    dbname = db_name or profile_name + '_' + osuser + '_' + config_dir_hash
    for profile in config.profiles:
        if profile.dictionary.get('AIIDADB_USER', '') == dbuser and not db_password:
            dbpass = profile.dictionary.get('AIIDADB_PASS')
            echo.echo('using found password for {}'.format(dbuser))
            break

    try:
        create = True
        if not postgres.dbuser_exists(dbuser):
            postgres.create_dbuser(dbuser, dbpass)
        else:
            dbname, create = _check_db_name(dbname, postgres)
        if create:
            postgres.create_db(dbuser, dbname)
    except Exception as exception:
        echo.echo_error('\n'.join([
            'Oops! Something went wrong while creating the database for you.',
            'You may continue with the quicksetup, however:',
            'For aiida to work correctly you will have to do that yourself as follows.',
            manual_setup_instructions(dbuser=dbuser, dbname=dbname), '',
            'Or setup your (OS-level) user to have permissions to create databases and rerun quicksetup.', ''
        ]))
        raise exception

    dbhost = postgres.get_dbinfo().get('host', 'localhost')
    dbport = postgres.get_dbinfo().get('port', '5432')

    repo = repository or 'repository/{}/'.format(profile_name)
    if not os.path.isabs(repo):
        repo = os.path.join(config.dirpath, repo)

    setup_args = {
        'backend': backend,
        'email': email,
        'db_host': dbhost,
        'db_port': dbport,
        'db_name': dbname,
        'db_user': dbuser,
        'db_pass': dbpass,
        'repo': repo,
        'first_name': first_name,
        'last_name': last_name,
        'institution': institution,
        'force_overwrite': write_profile,
    }

    setup_profile(profile_name, only_config=only_config, set_default=set_default, non_interactive=True, **setup_args)
    echo.echo_success("Set up profile '{}'.".format(profile_name))
