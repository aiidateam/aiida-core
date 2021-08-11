# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
""" Convenience functions for printing output from verdi commands """

from enum import IntEnum
from collections import OrderedDict
import sys
import yaml

import click

__all__ = (
    'echo', 'echo_info', 'echo_success', 'echo_warning', 'echo_error', 'echo_critical', 'echo_highlight',
    'echo_dictionary'
)


class ExitCode(IntEnum):
    """Exit codes for the verdi command line."""
    CRITICAL = 1
    DEPRECATED = 80
    UNKNOWN = 99
    SUCCESS = 0


COLORS = {
    'success': 'green',
    'highlight': 'green',
    'info': 'blue',
    'warning': 'bright_yellow',
    'error': 'red',
    'critical': 'red',
    'deprecated': 'red',
}
BOLD = True  # whether colors are used together with 'bold'


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
    click.secho('Info: ', fg=COLORS['info'], bold=True, nl=False, err=err)
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
    click.secho('Success: ', fg=COLORS['success'], bold=True, nl=False, err=err)
    click.secho(message, bold=bold, nl=nl, err=err)


def echo_warning(message, bold=False, nl=True, err=False):
    """
    Print a warning message through click's echo function to stdout, prefixed with 'Warning:'

    :param message: the string representing the message to print
    :param bold: whether to print the message in bold
    :param nl: whether to print a newline at the end of the message
    :param err: whether to print to stderr
    """
    click.secho('Warning: ', fg=COLORS['warning'], bold=True, nl=False, err=err)
    click.secho(message, bold=bold, nl=nl, err=err)


def echo_error(message, bold=False, nl=True, err=True):
    """
    Print an error message through click's echo function to stdout, prefixed with 'Error:'

    :param message: the string representing the message to print
    :param bold: whether to print the message in bold
    :param nl: whether to print a newline at the end of the message
    :param err: whether to print to stderr
    """
    click.secho('Error: ', fg=COLORS['error'], bold=True, nl=False, err=err)
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
    click.secho('Critical: ', fg=COLORS['critical'], bold=True, nl=False, err=err)
    click.secho(message, bold=bold, nl=nl, err=err)
    sys.exit(ExitCode.CRITICAL)


def echo_highlight(message, nl=True, bold=True, color='highlight'):
    """
    Print a highlighted message to stdout

    :param message: the string representing the message to print
    :param bold: whether to print the message in bold
    :param nl: whether to print a newline at the end of the message
    :param color: a color from COLORS
    """
    click.secho(message, bold=bold, nl=nl, fg=COLORS[color])


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
    click.secho('Deprecated: ', fg=COLORS['deprecated'], bold=True, nl=False, err=err)
    click.secho(message, bold=bold, nl=nl, err=err)

    if exit:
        sys.exit(ExitCode.DEPRECATED)


def echo_formatted_list(collection, attributes, sort=None, highlight=None, hide=None):
    """Print a collection of entries as a formatted list, one entry per line.

    :param collection: a list of objects
    :param attributes: a list of attributes to print for each entry in the collection
    :param sort: optional lambda to sort the collection
    :param highlight: optional lambda to highlight an entry in the collection if it returns True
    :param hide: optional lambda to skip an entry if it returns True
    """
    if sort:
        entries = sorted(collection, key=sort)
    else:
        entries = collection

    template = f"{{symbol}}{' {}' * len(attributes)}"

    for entry in entries:
        if hide and hide(entry):
            continue

        values = [getattr(entry, attribute) for attribute in attributes]
        if highlight and highlight(entry):
            click.secho(template.format(symbol='*', *values), fg=COLORS['highlight'])
        else:
            click.secho(template.format(symbol=' ', *values))


def _format_dictionary_json_date(dictionary, sort_keys=True):
    """Return a dictionary formatted as a string using the json format and converting dates to strings."""
    from aiida.common import json

    def default_jsondump(data):
        """Function needed to decode datetimes, that would otherwise not be JSON-decodable."""
        import datetime
        from aiida.common import timezone

        if isinstance(data, datetime.datetime):
            return timezone.localtime(data).strftime('%Y-%m-%dT%H:%M:%S.%f%z')

        raise TypeError(f'{repr(data)} is not JSON serializable')

    return json.dumps(dictionary, indent=4, sort_keys=sort_keys, default=default_jsondump)


def _format_yaml(dictionary, sort_keys=True):
    """Return a dictionary formatted as a string using the YAML format."""
    return yaml.dump(dictionary, sort_keys=sort_keys)


def _format_yaml_expanded(dictionary, sort_keys=True):
    """Return a dictionary formatted as a string using the expanded YAML format."""
    return yaml.dump(dictionary, sort_keys=sort_keys, default_flow_style=False)


VALID_DICT_FORMATS_MAPPING = OrderedDict(
    (('json+date', _format_dictionary_json_date), ('yaml', _format_yaml), ('yaml_expanded', _format_yaml_expanded))
)


def echo_dictionary(dictionary, fmt='json+date', sort_keys=True):
    """
    Print the given dictionary to stdout in the given format

    :param dictionary: the dictionary
    :param fmt: the format to use for printing
    :param sort_keys: Whether to automatically sort keys
    """
    try:
        format_function = VALID_DICT_FORMATS_MAPPING[fmt]
    except KeyError:
        formats = ', '.join(VALID_DICT_FORMATS_MAPPING.keys())
        raise ValueError(f'Unrecognised printing format. Valid formats are: {formats}')

    echo(format_function(dictionary, sort_keys=sort_keys))


def is_stdout_redirected():
    """Determines if the standard output is redirected.

    For cases where the standard output is redirected and you want to
    inform the user without messing up the output. Example::

        echo.echo_info("Found {} results".format(qb.count()), err=echo.is_stdout_redirected)
        echo.echo(tabulate.tabulate(qb.all()))
    """
    # pylint: disable=no-member
    return not sys.stdout.isatty()
