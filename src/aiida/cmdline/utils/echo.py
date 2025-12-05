###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Convenience functions for logging output from ``verdi`` commands."""

from __future__ import annotations

import collections
import enum
import json
import logging
import sys
from collections.abc import Sequence
from typing import Any, Callable, NoReturn, Optional

import click

from aiida.common.log import AiidaLoggerType

CMDLINE_LOGGER: AiidaLoggerType = logging.getLogger('verdi')  # type: ignore[assignment]

__all__ = (
    'echo_critical',
    'echo_dictionary',
    'echo_error',
    'echo_info',
    'echo_report',
    'echo_success',
    'echo_tabulate',
    'echo_warning',
)


class ExitCode(enum.IntEnum):
    """Exit codes for the verdi command line."""

    CRITICAL = 1
    USAGE_ERROR = 2
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


def highlight_string(string: str, color: str = 'highlight') -> str:
    """Highlight a string with a certain color.

    Uses ``click.style`` to highlight the string.

    :param string: The string to highlight.
    :param color: The color to use.
    :returns: The highlighted string.
    """
    return click.style(string, fg=COLORS[color])


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
    CMDLINE_LOGGER.report(message, extra={'nl': nl, 'err': err, 'prefix': False})


def echo_debug(message: str, bold: bool = False, nl: bool = True, err: bool = False, prefix: bool = True) -> None:
    """Log a debug message to the cmdline logger.

    :param message: the message to log.
    :param bold: whether to format the message in bold.
    :param nl: whether to add a newline at the end of the message.
    :param err: whether to log to stderr.
    :param prefix: whether the message should be prefixed with a colored version of the log level.
    """
    message = click.style(message, bold=bold)
    CMDLINE_LOGGER.debug(message, extra={'nl': nl, 'err': err, 'prefix': prefix})


def echo_info(message: str, bold: bool = False, nl: bool = True, err: bool = False, prefix: bool = True) -> None:
    """Log an info message to the cmdline logger.

    :param message: the message to log.
    :param bold: whether to format the message in bold.
    :param nl: whether to add a newline at the end of the message.
    :param err: whether to log to stderr.
    :param prefix: whether the message should be prefixed with a colored version of the log level.
    """
    message = click.style(message, bold=bold)
    CMDLINE_LOGGER.info(message, extra={'nl': nl, 'err': err, 'prefix': prefix})


def echo_report(message: str, bold: bool = False, nl: bool = True, err: bool = False, prefix: bool = True) -> None:
    """Log an report message to the cmdline logger.

    :param message: the message to log.
    :param bold: whether to format the message in bold.
    :param nl: whether to add a newline at the end of the message.
    :param err: whether to log to stderr.
    :param prefix: whether the message should be prefixed with a colored version of the log level.
    """
    message = click.style(message, bold=bold)
    CMDLINE_LOGGER.report(message, extra={'nl': nl, 'err': err, 'prefix': prefix})


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

    CMDLINE_LOGGER.report(message, extra={'nl': nl, 'err': err, 'prefix': False})


def echo_warning(message: str, bold: bool = False, nl: bool = True, err: bool = False, prefix: bool = True) -> None:
    """Log a warning message to the cmdline logger.

    :param message: the message to log.
    :param bold: whether to format the message in bold.
    :param nl: whether to add a newline at the end of the message.
    :param err: whether to log to stderr.
    :param prefix: whether the message should be prefixed with a colored version of the log level.
    """
    message = click.style(message, bold=bold)
    CMDLINE_LOGGER.warning(message, extra={'nl': nl, 'err': err, 'prefix': prefix})


def echo_error(message: str, bold: bool = False, nl: bool = True, err: bool = True, prefix: bool = True) -> None:
    """Log an error message to the cmdline logger.

    :param message: the message to log.
    :param bold: whether to format the message in bold.
    :param nl: whether to add a newline at the end of the message.
    :param err: whether to log to stderr.
    :param prefix: whether the message should be prefixed with a colored version of the log level.
    """
    message = click.style(message, bold=bold)
    CMDLINE_LOGGER.error(message, extra={'nl': nl, 'err': err, 'prefix': prefix})


def echo_critical(message: str, bold: bool = False, nl: bool = True, err: bool = True, prefix: bool = True) -> NoReturn:
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
    CMDLINE_LOGGER.critical(message, extra={'nl': nl, 'err': err, 'prefix': prefix})
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
    prefix = click.style('Deprecated: ', fg=COLORS['deprecated'], bold=True)
    echo_warning(prefix + message, bold=bold, nl=nl, err=err, prefix=False)

    if exit:
        sys.exit(ExitCode.DEPRECATED)


def echo_formatted_list(
    collection: Sequence,
    attributes: list,
    sort: Callable | None = None,
    highlight: Callable | None = None,
    hide: Callable | None = None,
) -> None:
    """Log a collection of entries as a formatted list, one entry per line.

    :param collection: a list of objects
    :param attributes: a list of attributes to log for each entry in the collection
    :param sort: optional lambda to sort the collection
    :param highlight: optional lambda to highlight an entry in the collection if it returns True
    :param hide: optional lambda to skip an entry if it returns True
    """
    entries = collection
    if sort:
        entries = sorted(collection, key=sort)

    template = f"{{symbol}}{' {}' * len(attributes)}"

    for entry in entries:
        if hide and hide(entry):
            continue

        values = [getattr(entry, attribute) for attribute in attributes]
        if highlight and highlight(entry):
            echo(click.style(template.format(symbol='*', *values), fg=COLORS['highlight']))
        else:
            echo(click.style(template.format(symbol=' ', *values)))


def _format_dictionary_json_date(dictionary: dict | list, sort_keys: bool = True) -> str:
    """Return a dictionary formatted as a string using the json format and converting dates to strings."""

    def default_jsondump(data):
        """Function needed to decode datetimes, that would otherwise not be JSON-decodable."""
        import datetime

        from aiida.common import timezone

        if isinstance(data, datetime.datetime):
            return timezone.localtime(data).strftime('%Y-%m-%dT%H:%M:%S.%f%z')

        raise TypeError(f'{data!r} is not JSON serializable')

    return json.dumps(dictionary, indent=4, sort_keys=sort_keys, default=default_jsondump)


def _format_yaml(dictionary: dict | list, sort_keys: bool = True) -> str:
    """Return a dictionary formatted as a string using the YAML format."""
    import yaml

    return yaml.dump(dictionary, sort_keys=sort_keys)


def _format_yaml_expanded(dictionary: dict | list, sort_keys: bool = True) -> str:
    """Return a dictionary formatted as a string using the expanded YAML format."""
    import yaml

    return yaml.dump(dictionary, sort_keys=sort_keys, default_flow_style=False)


VALID_DICT_FORMATS_MAPPING = collections.OrderedDict(
    (('json+date', _format_dictionary_json_date), ('yaml', _format_yaml), ('yaml_expanded', _format_yaml_expanded))
)


def echo_tabulate(table: Any, **kwargs) -> None:
    """Echo the string generated by passing ``table`` to ``tabulate.tabulate``.

    This wrapper is added in order to lazily import the ``tabulate`` package only when invoked. This helps keeping the
    import time of the :mod:`aiida.cmdline` to a minimum, which is critical for keeping tab-completion snappy.

    :param table: The table of data to echo.
    :param kwargs: Additional arguments passed to :meth:`tabulate.tabulate`.
    """
    from tabulate import tabulate

    echo(tabulate(table, **kwargs))


def echo_dictionary(dictionary: dict | list, fmt: str = 'json+date', sort_keys: bool = True) -> None:
    """Log the given dictionary to stdout in the given format

    :param dictionary: dictionary or a list of dictionaries
    :param fmt: the format to use for printing
    :param sort_keys: Whether to automatically sort keys
    """
    try:
        format_function = VALID_DICT_FORMATS_MAPPING[fmt]
    except KeyError:
        formats = ', '.join(VALID_DICT_FORMATS_MAPPING.keys())
        raise ValueError(f'Unrecognised printing format. Valid formats are: {formats}')

    echo(format_function(dictionary, sort_keys=sort_keys))


def is_stdout_redirected() -> bool:
    """Determines if the standard output is redirected.

    For cases where the standard output is redirected and you want to
    inform the user without messing up the output. Example::

        echo.echo_info("Found {} results".format(qb.count()), err=echo.is_stdout_redirected)
        echo.echo(tabulate.tabulate(qb.all()))
    """
    return not sys.stdout.isatty()
