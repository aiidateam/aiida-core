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

AVAIL_AL_COMMANDS = ['revision', 'current', 'history', 'upgrade', 'sp']

if __name__ == "__main1__":
    import argparse

    actual_argv = sys.argv[:]
    print '====> ', actual_argv
    print '====> ', actual_argv[1:]

    parser = argparse.ArgumentParser()
    parser.add_argument('--aiida-profile',
                        help='The AiiDA profile that you would like to use.')
    parser.add_argument('--aiida-process',
                        help='The AiiDA process that you would like to use.')
    # parser.add_argument('revision',
    #                     help='Get current revision of the database')
    #
    subparsers = parser.add_subparsers(help='sub-command help', dest='command')

    parser_upg = subparsers.add_parser('upgrade', help='a help')
    parser_upg.add_argument('upgrade', choices=['head', 'base'],
                                       help='a help')
    parser_req = subparsers.add_parser('required', help='a help')
    parser_req = subparsers.add_parser('history', help='a help')
    parser_cur = subparsers.add_parser('current', help='a help')

    args = parser.parse_args(actual_argv[1:])

    print args
    # print args.upgrade

if __name__ == "__main__":
    # Copy sys.argv
    actual_argv = sys.argv[:]

    # Check if the first cmdline option is --aiida-process=PROCESSNAME
    try:
        first_cmdline_option = sys.argv[1]
    except IndexError:
        first_cmdline_option = None

    process_name = None  # Use the default process if not specified
    if first_cmdline_option is not None:
        cmdprefix = "--aiida-process="
        if first_cmdline_option.startswith(cmdprefix):
            process_name = first_cmdline_option[len(cmdprefix):]
            # I remove the argument I just read
            actual_argv = [sys.argv[0]] + sys.argv[2:]

    # Check if there is also a cmdline option is --aiida-profile=PROFILENAME
    try:
        first_cmdline_option = actual_argv[1]
    except IndexError:
        first_cmdline_option = None

    profile_name = None  # Use the default profile if not specified
    if first_cmdline_option is not None:
        cmdprefix = "--aiida-profile="
        if first_cmdline_option.startswith(cmdprefix):
            profile_name = first_cmdline_option[len(cmdprefix):]
            # I remove the argument I just read
            actual_argv = [actual_argv[0]] + actual_argv[2:]

    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--aiida-profile',
                        help='The AiiDA profile that you would like to use.')
    parser.add_argument('--aiida-process',
                        help='The AiiDA process that you would like to use.')

    subparsers = parser.add_subparsers(
        help='sub-command help', dest='command')

    parser_upg = subparsers.add_parser(
        'upgrade', help='Upgrade to a later version.')
    parser_upg.add_argument(
        'arguments', choices=['head'], help='Upgrade to head.')

    parser_dg = subparsers.add_parser(
        'downgrade', help='Revert to a previous version.')
    parser_dg.add_argument(
        'arguments', choices=['base'], help='Revert to base.')

    parser_hist = subparsers.add_parser(
        'history', help='List changeset scripts in chronological order.')
    parser_hist.add_argument(
        'arguments', choices=['verbose'], help='Output in verbose mode.')
    # parser_hist.add_argument('arguments', choices=['--verbose'], nargs='?', help='Output in verbose mode.')
    # parser_hist.add_argument(
    #     dest='arguments', choices=['--verbose'], required=False, help='Output in verbose mode.')
    # parser_hist.add_argument(
    #     "--verbose", action="store_true", help='Output in verbose mode.')

    parser_cur = subparsers.add_parser(
        'current', help='Display the current revision for a database.')

    parser_rev = subparsers.add_parser(
        'revision', help='Create a new revision file.')

    args = parser.parse_args(actual_argv[1:])
    # args = parser.parse_args(actual_argv)
    from aiida.backends.sqlalchemy.utils import alembic_command

    print args
    print args.command
    exit(0)

    if 'arguments' in args:
        print args.arguments

    if args.command in AVAIL_AL_COMMANDS:
        # Perform the same loading procedure as the normal load_dbenv does
        from aiida.backends import settings
        settings.LOAD_DBENV_CALLED = True
        # We load the needed profile.
        # This is going to set global variables in settings, including
        # settings.BACKEND
        from aiida.backends.profile import load_profile
        load_profile(process=process_name, profile=profile_name)
        from aiida.backends.profile import BACKEND_SQLA
        if settings.BACKEND != BACKEND_SQLA:
            from aiida.common.exceptions import InvalidOperation
            raise InvalidOperation("A SQLAlchemy (alembic) revision "
                                   "generation procedure is initiated "
                                   "but a different backend is used!")
        # We load the Django specific _load_dbenv_noschemacheck
        # When there will be a need for SQLAlchemy for a schema migration,
        # we may abstract thw _load_dbenv_noschemacheck and make a common
        # one for both backends
        from aiida.backends.sqlalchemy.utils import _load_dbenv_noschemacheck
        _load_dbenv_noschemacheck(process=process_name, profile=profile_name)

        if 'arguments' in args:
            alembic_command(args.command, args.arguments)
        else:
            alembic_command(args.command)

        # alembic_command(args.command)
        # if args.command == 'revision':
        #     alembic_command(actual_argv[1], autogenerate=True,
        #                     message="Added account table")
        # if actual_argv[1] == 'current':
        #     alembic_command(actual_argv[1])
        # if actual_argv[1] == 'history':
        #     alembic_command(actual_argv[1])
        # if actual_argv[1] == 'upgrade':
        #     alembic_command(actual_argv[1])
    else:
        print("No valid command specified. The available commands are: " +
              AVAIL_AL_COMMANDS)
