# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Convenience functions for logging output from ``verdi`` commands."""
import collections
import enum
import json
import sys
from typing import Any, Optional

import click
import yaml

from aiida.common.log import AIIDA_LOGGER

CMDLINE_LOGGER = AIIDA_LOGGER.getChild('cmdline')

__all__ = ('echo_report', 'echo_info', 'echo_success', 'echo_warning', 'echo_error', 'echo_critical', 'echo_dictionary')


class ExitCode(enum.IntEnum):
    """Exit codes for the verdi command line."""
    CRITICAL = 1
    DEPRECATED = 80
    UNKNOWN = 99
    SUCCESS = 0


COLORS = {
    'success': 'green',
    'highlight': 'green',
    'debug': 'white',
    'info': 'blue',
    'report': 'blue',
    'warning': 'bright_yellow',
    'error': 'red',
    'critical': 'red',
    'deprecated': 'red',
}


def echo(message: Any, fg: Optional[str] = None, bold: bool = False, nl: bool = True, err: bool = False) -> None:
    """Log a message to the cmdline logger.

    .. note:: The message will be logged at the ``REPORT`` level but always without the log level prefix.

    :param message: the message to log.
    :param fg: if provided this will become the foreground color.
    :param bold: whether to print the messaformat bold.
    :param nl: whether to print a newlineaddhe end of the message.
    :param err: whether to log to stderr.
    """
    message = click.style(message, fg=fg, bold=bold)
    CMDLINE_LOGGER.report(message, extra=dict(nl=nl, err=err, prefix=False))


def echo_debug(message: str, bold: bool = False, nl: bool = True, err: bool = False, prefix: bool = True) -> None:
    """Log a debug message to the cmdline logger.

    :param message: the message to log.
    :param bold: whether to format the message in bold.
    :param nl: whether to add a newline at the end of the message.
    :param err: whether to log to stderr.
    :param prefix: whether the message should be prefixed with a colored version of the log level.
    """
    message = click.style(message, bold=bold)
    CMDLINE_LOGGER.debug(message, extra=dict(nl=nl, err=err, prefix=prefix))


def echo_info(message: str, bold: bool = False, nl: bool = True, err: bool = False, prefix: bool = True) -> None:
    """Log an info message to the cmdline logger.

    :param message: the message to log.
    :param bold: whether to format the message in bold.
    :param nl: whether to add a newline at the end of the message.
    :param err: whether to log to stderr.
    :param prefix: whether the message should be prefixed with a colored version of the log level.
    """
    message = click.style(message, bold=bold)
    CMDLINE_LOGGER.info(message, extra=dict(nl=nl, err=err, prefix=prefix))


def echo_report(message: str, bold: bool = False, nl: bool = True, err: bool = False, prefix: bool = True) -> None:
    """Log an report message to the cmdline logger.

    :param message: the message to log.
    :param bold: whether to format the message in bold.
    :param nl: whether to add a newline at the end of the message.
    :param err: whether to log to stderr.
    :param prefix: whether the message should be prefixed with a colored version of the log level.
    """
    message = click.style(message, bold=bold)
    CMDLINE_LOGGER.report(message, extra=dict(nl=nl, err=err, prefix=prefix))


def echo_success(message: str, bold: bool = False, nl: bool = True, err: bool = False, prefix: bool = True) -> None:
    """Log a success message to the cmdline logger.

    .. note:: The message will be logged at the ``REPORT`` level and always with the ``Success:`` prefix.

    :param message: the message to log.
    :param bold: whether to format the message in bold.
    :param nl: whether to add a newline at the end of the message.
    :param err: whether to log to stderr.
    :param prefix: whether the message should be prefixed with a colored version of the log level.
    """
    message = click.style(message, bold=bold)

    if prefix:
        message = click.style('Success: ', bold=True, fg=COLORS['success']) + message

    CMDLINE_LOGGER.report(message, extra=dict(nl=nl, err=err, prefix=False))


def echo_warning(message: str, bold: bool = False, nl: bool = True, err: bool = False, prefix: bool = True) -> None:
    """Log a warning message to the cmdline logger.

    :param message: the message to log.
    :param bold: whether to format the message in bold.
    :param nl: whether to add a newline at the end of the message.
    :param err: whether to log to stderr.
    :param prefix: whether the message should be prefixed with a colored version of the log level.
    """
    message = click.style(message, bold=bold)
    CMDLINE_LOGGER.warning(message, extra=dict(nl=nl, err=err, prefix=prefix))


def echo_error(message: str, bold: bool = False, nl: bool = True, err: bool = True, prefix: bool = True) -> None:
    """Log an error message to the cmdline logger.

    :param message: the message to log.
    :param bold: whether to format the message in bold.
    :param nl: whether to add a newline at the end of the message.
    :param err: whether to log to stderr.
    :param prefix: whether the message should be prefixed with a colored version of the log level.
    """
    message = click.style(message, bold=bold)
    CMDLINE_LOGGER.error(message, extra=dict(nl=nl, err=err, prefix=prefix))


def echo_critical(message: str, bold: bool = False, nl: bool = True, err: bool = True, prefix: bool = True) -> None:
    """Log a critical error message to the cmdline logger and exit with ``exit_status``.

    This should be used to print messages for errors that cannot be recovered from and so the script should be directly
    terminated with a non-zero exit status to indicate that the command failed.

    :param message: the message to log.
    :param bold: whether to format the message in bold.
    :param nl: whether to add a newline at the end of the message.
    :param err: whether to log to stderr.
    :param prefix: whether the message should be prefixed with a colored version of the log level.
    """
    message = click.style(message, bold=bold)
    CMDLINE_LOGGER.critical(message, extra=dict(nl=nl, err=err, prefix=prefix))
    sys.exit(ExitCode.CRITICAL)


def echo_deprecated(message: str, bold: bool = False, nl: bool = True, err: bool = True, exit: bool = False) -> None:
    """Log an error message to the cmdline logger, prefixed with 'Deprecated:' exiting with the given ``exit_status``.

    This should be used to indicate deprecated commands.

    :param message: the message to log.
    :param bold: whether to format the message in bold.
    :param nl: whether to add a newline at the end of the message.
    :param err: whether to log to stderr.
    :param exit: whether to exit after printing the message
    """
    # pylint: disable=redefined-builtin
    prefix = click.style('Deprecated: ', fg=COLORS['deprecated'], bold=True)
    echo_warning(prefix + message, bold=bold, nl=nl, err=err, prefix=False)

    if exit:
        sys.exit(ExitCode.DEPRECATED)


def echo_formatted_list(collection, attributes, sort=None, highlight=None, hide=None):
    """Log a collection of entries as a formatted list, one entry per line.

    :param collection: a list of objects
    :param attributes: a list of attributes to log for each entry in the collection
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
            echo(click.style(template.format(symbol='*', *values), fg=COLORS['highlight']))
        else:
            echo(click.style(template.format(symbol=' ', *values)))


def _format_dictionary_json_date(dictionary, sort_keys=True):
    """Return a dictionary formatted as a string using the json format and converting dates to strings."""

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


VALID_DICT_FORMATS_MAPPING = collections.OrderedDict(
    (('json+date', _format_dictionary_json_date), ('yaml', _format_yaml), ('yaml_expanded', _format_yaml_expanded))
)


def echo_dictionary(dictionary, fmt='json+date', sort_keys=True):
    """Log the given dictionary to stdout in the given format

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
