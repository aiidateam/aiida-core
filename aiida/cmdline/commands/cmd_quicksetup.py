# -*- coding: utf-8 -*-
# pylint: disable=too-many-arguments,too-many-locals,too-many-statements,too-many-branches
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""`verdi quicksetup` command."""
from __future__ import absolute_import
import os
import sys
import hashlib

import click

from aiida.cmdline.commands.cmd_verdi import verdi
from aiida.cmdline.params import arguments, options
from aiida.cmdline.utils import echo
from aiida.control.profile import setup_profile
from aiida.control.postgres import Postgres, manual_setup_instructions, prompt_db_info


def _check_db_name(dbname, postgres):
    """Looks up if a database with the name exists, prompts for using or creating a differently named one."""
    create = True
    while create and postgres.db_exists(dbname):
        click.echo('database {} already exists!'.format(dbname))
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
    from aiida.common.setup import create_base_dirs, AIIDA_CONFIG_FOLDER
    create_base_dirs()

    aiida_dir = os.path.expanduser(AIIDA_CONFIG_FOLDER)

    # access postgres
    postgres = Postgres(host=db_host, port=db_port, interactive=bool(not non_interactive), quiet=False)
    postgres.set_setup_fail_callback(prompt_db_info)
    success = postgres.determine_setup()
    if not success:
        sys.exit(1)

    # default database name is <profile_name>_<login-name>
    # this ensures that for profiles named test_... the database will also
    # be named test_...
    import getpass
    osuser = getpass.getuser()
    aiida_base_dir_hash = hashlib.md5(AIIDA_CONFIG_FOLDER.encode('utf-8')).hexdigest()
    dbname = db_name or profile_name + '_' + osuser + '_' + aiida_base_dir_hash

    # default database user name is aiida_qs_<login-name>
    # default password is random
    dbuser = db_username or 'aiida_qs_' + osuser + '_' + aiida_base_dir_hash
    from aiida.common.setup import generate_random_secret_key
    dbpass = db_password or generate_random_secret_key()

    # check if there is a profile that contains the db user already
    # and if yes, take the db user password from there
    # This is ok because a user can only see his own config files
    from aiida.common.setup import get_or_create_config
    confs = get_or_create_config()
    profs = confs.get('profiles', {})
    for profile in profs.values():
        if profile.get('AIIDADB_USER', '') == dbuser and not db_password:
            dbpass = profile.get('AIIDADB_PASS')
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
        click.echo('\n'.join([
            'Oops! Something went wrong while creating the database for you.',
            'You may continue with the quicksetup, however:',
            'For aiida to work correctly you will have to do that yourself as follows.',
            manual_setup_instructions(dbuser=dbuser, dbname=dbname), '',
            'Or setup your (OS-level) user to have permissions to create databases and rerun quicksetup.', ''
        ]))
        raise exception

    # create a profile, by default 'quicksetup' and prompt the user if
    # already exists
    confs = get_or_create_config()
    profile_name = profile_name or 'quicksetup'
    write_profile = False
    while not write_profile:
        if profile_name in confs.get('profiles', {}):
            if click.confirm('overwrite existing profile {}?'.format(profile_name)):
                write_profile = True
            else:
                profile_name = click.prompt('new profile name', type=str)
        else:
            write_profile = True

    dbhost = postgres.dbinfo.get('host', 'localhost')
    dbport = postgres.dbinfo.get('port', '5432')

    from os.path import isabs
    repo = repository or 'repository-{}/'.format(profile_name)
    if not isabs(repo):
        repo = os.path.join(aiida_dir, repo)

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
