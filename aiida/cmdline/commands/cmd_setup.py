# -*- coding: utf-8 -*-
# pylint: disable=too-many-arguments
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""`verdi setup` command."""
from __future__ import absolute_import
from aiida.cmdline.commands.cmd_verdi import verdi
from aiida.cmdline.params import arguments, options
from aiida.control.profile import setup_profile


@verdi.command('setup')
@arguments.PROFILE_NAME()
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
def setup(profile_name, only_config, set_default, non_interactive, backend, db_host, db_port, db_name, db_username,
          db_password, repository, email, first_name, last_name, institution):
    """Setup and configure a new profile."""
    kwargs = dict(
        profile=profile_name,
        only_config=only_config,
        set_default=set_default,
        non_interactive=non_interactive,
        backend=backend,
        db_host=db_host,
        db_port=db_port,
        db_name=db_name,
        db_user=db_username,
        db_pass=db_password,
        repo=repository,
        email=email,
        first_name=first_name,
        last_name=last_name,
        institution=institution)

    kwargs = {k: v for k, v in kwargs.items() if v is not None}

    setup_profile(**kwargs)
