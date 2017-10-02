#!/usr/bin/env python
# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
import sys

# Available alembic commands
REVISION_CMD = 'revision'
CURRENT_CMD = 'current'
HISTORY_CMD = 'history'
UPGRADE_CMD = 'upgrade'
DOWNGRADE_CMD = 'downgrade'

AVAIL_AL_COMMANDS = [REVISION_CMD, CURRENT_CMD, HISTORY_CMD,
                     UPGRADE_CMD, DOWNGRADE_CMD]

if __name__ == "__main__":
    import argparse
    from aiida.backends.sqlalchemy.utils import alembic_command
    from aiida.backends.profile import load_profile
    from aiida.backends.sqlalchemy.utils import _load_dbenv_noschemacheck
    from aiida.backends.profile import BACKEND_SQLA
    from aiida.common.exceptions import InvalidOperation

    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--aiida-profile', help='The AiiDA profile that you would like to use')
    parser.add_argument(
        '--aiida-process', help='The AiiDA process that you would like to use')

    subparsers = parser.add_subparsers(
        help='sub-command help', dest='command')

    parser_upg = subparsers.add_parser(
        'upgrade', help='Upgrade to a later version')
    parser_upg.add_argument(
        'arguments', choices=['head'], help='Upgrade to head')

    parser_dg = subparsers.add_parser(
        'downgrade', help='Revert to a previous version')
    parser_dg.add_argument(
        'arguments', choices=['base'], help='Revert to base')

    parser_hist = subparsers.add_parser(
        'history', help='List changeset scripts in chronological order')
    parser_hist.add_argument(
        'arguments', choices=['verbose'], nargs='?',
        help='Output in verbose mode')

    parser_cur = subparsers.add_parser(
        'current', help='Display the current version for a database')
    parser_cur.add_argument(
        'arguments', choices=['verbose'], nargs='?',
        help='Output in verbose mode')

    parser_rev = subparsers.add_parser(
        'revision', help='Create a new migration file')
    parser_rev.add_argument(
        'arguments', nargs=1, help='Migration message')

    args = parser.parse_args(sys.argv[1:])

    if args.command in AVAIL_AL_COMMANDS:
        # Use the default process if not specified
        process_name = args.aiida_process
        # Use the default profile if not specified
        profile_name = args.aiida_profile

        # Perform the same loading procedure as the normal load_dbenv does
        from aiida.backends import settings
        settings.LOAD_DBENV_CALLED = True
        # We load the needed profile.
        # This is going to set global variables in settings, including
        # settings.BACKEND
        load_profile(process=process_name, profile=profile_name)
        if settings.BACKEND != BACKEND_SQLA:
            raise InvalidOperation("A SQLAlchemy (alembic) revision "
                                   "generation procedure is initiated "
                                   "but a different backend is used!")
        _load_dbenv_noschemacheck(process=process_name, profile=profile_name)

        if 'arguments' in args:
            alembic_command(args.command, args.arguments)
        else:
            alembic_command(args.command)
    else:
        print("No valid command specified. The available commands are: " +
              str(AVAIL_AL_COMMANDS))
