# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
""" Convenience functions for printing output from verdi commands """
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from enum import IntEnum
import sys

import click

__all__ = ('echo', 'echo_info', 'echo_success', 'echo_warning', 'echo_error', 'echo_critical', 'echo_dictionary')


# pylint: disable=too-few-public-methods
class ExitCode(IntEnum):
    """Exit codes for the verdi command line."""
    CRITICAL = 1
    DEPRECATED = 80
    UNKNOWN = 99
    SUCCESS = 0


# pylint: disable=invalid-name
def echo(message, bold=False, nl=True, err=False):
    """
    Print a normal message through click's echo function to stdout

    :param message: the string representing the message to print
    :param bold: whether to print the message in bold
    :param nl: whether to print a newline at the end of the message
    :param err: whether to print to stderr
    """
    click.secho(message, bold=bold, nl=nl, err=err)


def echo_info(message, bold=False, nl=True, err=False):
    """
    Print an info message through click's echo function to stdout, prefixed with 'Info:'

    :param message: the string representing the message to print
    :param bold: whether to print the message in bold
    :param nl: whether to print a newline at the end of the message
    :param err: whether to print to stderr
    """
    click.secho('Info: ', fg='blue', bold=True, nl=False, err=err)
    click.secho(message, bold=bold, nl=nl, err=err)


def echo_success(message, bold=False, nl=True, err=False):
    """
    Print a success message through click's echo function to stdout, prefixed with 'Success:'

    :param message: the string representing the message to print
    :param bold: whether to print the message in bold
        include a newline character
    :param nl: whether to print a newline at the end of the message
    :param err: whether to print to stderr
    """
    click.secho('Success: ', fg='green', bold=True, nl=False, err=err)
    click.secho(message, bold=bold, nl=nl, err=err)


def echo_warning(message, bold=False, nl=True, err=False):
    """
    Print a warning message through click's echo function to stdout, prefixed with 'Warning:'

    :param message: the string representing the message to print
    :param bold: whether to print the message in bold
    :param nl: whether to print a newline at the end of the message
    :param err: whether to print to stderr
    """
    click.secho('Warning: ', fg='yellow', bold=True, nl=False, err=err)
    click.secho(message, bold=bold, nl=nl, err=err)


def echo_error(message, bold=False, nl=True, err=True):
    """
    Print an error message through click's echo function to stdout, prefixed with 'Error:'

    :param message: the string representing the message to print
    :param bold: whether to print the message in bold
    :param nl: whether to print a newline at the end of the message
    :param err: whether to print to stderr
    """
    click.secho('Error: ', fg='red', bold=True, nl=False, err=err)
    click.secho(message, bold=bold, nl=nl, err=err)


def echo_critical(message, bold=False, nl=True, err=True):
    """
    Print an error message through click's echo function to stdout, prefixed with 'Critical:'
    and then calls sys.exit with the given exit_status.

    This should be used to print messages for errors that cannot be recovered
    from and so the script should be directly terminated with a non-zero exit
    status to indicate that the command failed

    :param message: the string representing the message to print
    :param bold: whether to print the message in bold
    :param nl: whether to print a newline at the end of the message
    :param err: whether to print to stderr
    """
    click.secho('Critical: ', fg='red', bold=True, nl=False, err=err)
    click.secho(message, bold=bold, nl=nl, err=err)
    sys.exit(ExitCode.CRITICAL)


# pylint: disable=redefined-builtin
def echo_deprecated(message, bold=False, nl=True, err=True, exit=False):
    """
    Print an error message through click's echo function to stdout, prefixed with 'Deprecated:'
    and then calls sys.exit with the given exit_status.

    This should be used to indicate deprecated commands.

    :param message: the string representing the message to print
    :param bold: whether to print the message in bold
    :param nl: whether to print a newline at the end of the message
    :param err: whether to print to stderr
    :param exit: whether to exit after printing the message
    """
    click.secho('Deprecated: ', fg='red', bold=True, nl=False, err=err)
    click.secho(message, bold=bold, nl=nl, err=err)

    if exit:
        sys.exit(ExitCode.DEPRECATED)


def echo_dictionary(dictionary, fmt='json+date'):
    """
    Print the given dictionary to stdout in the given format

    :param dictionary: the dictionary
    :param fmt: the format to use for printing, valid options: ['json+data']
    """
    valid_formats_table = {'json+date': _format_dictionary_json_date}

    try:
        format_function = valid_formats_table[fmt]
    except KeyError:
        formats = ', '.join(valid_formats_table.keys())
        raise ValueError('Unrecognised printing format. Valid formats are: {}'.format(formats))

    echo(format_function(dictionary))


def _format_dictionary_json_date(dictionary):
    """Return a dictionary formatted as a string using the json format and converting dates to strings."""
    from aiida.common import json

    def default_jsondump(data):
        """Function needed to decode datetimes, that would otherwise not be JSON-decodable."""
        import datetime

        if isinstance(data, datetime.datetime):
            return data.strftime('%Y-%m-%dT%H:%M:%S.%f%z')

        raise TypeError(repr(data) + ' is not JSON serializable')

    return json.dumps(dictionary, indent=4, sort_keys=True, default=default_jsondump)


def is_stdout_redirected():
    """Determines if the standard output is redirected.

    For cases where the standard output is redirected and you want to
    inform the user without messing up the output. Example::

        echo.echo_info("Found {} results".format(qb.count()), err=echo.is_stdout_redirected)
        echo.echo(tabulate.tabulate(qb.all()))
    """
    # pylint: disable=no-member
    return not sys.stdout.isatty()
