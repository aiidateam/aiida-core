#!/usr/bin/env python
# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Simple wrapper around Django's `manage.py` CLI script."""
import click

from aiida.cmdline.params import options, types


@click.command()
@options.PROFILE(required=True, type=types.ProfileParamType(load_profile=True))
@click.argument('command', nargs=-1)
def main(profile, command):  # pylint: disable=unused-argument
    """Simple wrapper around the Django command line tool that first loads an AiiDA profile."""
    from django.core.management import execute_from_command_line  # pylint: disable=import-error,no-name-in-module
    from aiida.manage.manager import get_manager

    manager = get_manager()
    manager._load_backend(schema_check=False)  # pylint: disable=protected-access

    # The `execute_from_command` expects a list of command line arguments where the first is the program name that one
    # would normally call directly. Since this is now replaced by our `click` command we just spoof a random name.
    argv = ['basename'] + list(command)
    execute_from_command_line(argv)


if __name__ == '__main__':
    main()  # pylint: disable=no-value-for-parameter
