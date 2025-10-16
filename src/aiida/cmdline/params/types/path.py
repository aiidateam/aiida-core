###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Click parameter types for paths."""

from __future__ import annotations

import os
import pathlib
import typing as t

import click

if t.TYPE_CHECKING:
    try:
        from typing import TypeAlias
    except ImportError:
        from typing_extensions import TypeAlias

__all__ = ('AbsolutePathParamType', 'FileOrUrl', 'PathOrUrl')

URL_TIMEOUT_SECONDS = 10

PathType: TypeAlias = 'str | bytes | os.PathLike[str]'


def check_timeout_seconds(timeout_seconds: float) -> int:
    """Raise if timeout is not within range [0;60]"""
    try:
        timeout_seconds = int(timeout_seconds)
    except ValueError:
        raise TypeError(f'timeout_seconds should be an integer but got: {type(timeout_seconds)}')

    if timeout_seconds < 0 or timeout_seconds > 60:
        raise ValueError('timeout_seconds needs to be in the range [0;60].')

    return timeout_seconds


class AbsolutePathParamType(click.Path):
    """The ParamType for identifying absolute Paths (derived from click.Path)."""

    name = 'AbsolutePath'

    def convert(self, value: t.Any, param: click.Parameter | None, ctx: click.Context | None) -> PathType:
        value = os.path.expanduser(value)
        newval = super().convert(value, param, ctx)
        if not os.path.isabs(newval):
            raise click.BadParameter('path must be absolute')
        return newval

    def __repr__(self) -> str:
        return 'ABSOLUTEPATH'


class AbsolutePathOrEmptyParamType(AbsolutePathParamType):
    """The ParamType for identifying absolute Paths, accepting also empty paths."""

    name = 'AbsolutePathEmpty'

    def convert(self, value: t.Any, param: click.Parameter | None, ctx: click.Context | None) -> PathType:
        if not value:
            return value  # type: ignore[no-any-return]
        return super().convert(value, param, ctx)

    def __repr__(self) -> str:
        return 'ABSOLUTEPATHEMPTY'


def convert_possible_url(value: str, timeout: int) -> t.Any:
    """If ``value`` does not correspond to a path on disk, try to open it as a URL.

    :param value: Potential path to file on disk or URL.
    :param timeout: The timeout in seconds when opening the URL.
    :param return_handle: Return the ``value`` as is. When set to ``True`` return an open file handle instead.
    :returns: The URL if ``value`` could be opened as a URL
    """
    import socket
    import urllib.error
    import urllib.request

    filepath = pathlib.Path(value)

    # Check whether the path actually corresponds to a file on disk, in which case the exception is reraised.
    if filepath.exists():
        raise click.BadParameter(f'The path `{value}` exists but could not be read.')

    try:
        return urllib.request.urlopen(value, timeout=timeout)
    except urllib.error.URLError:
        raise click.BadParameter(f'The URL `{value}` could not be reached.')
    except socket.timeout:
        raise click.BadParameter(f'The URL `{value}` could not be reached within {timeout} seconds.')
    except ValueError as exception_url:
        raise click.BadParameter(
            f'The path `{value}` does not correspond to a file and also could not be reached as a URL.\n'
            'Please check the spelling for typos and if it is a URL, make sure to include the protocol, e.g., http://'
        ) from exception_url


class PathOrUrl(click.Path):
    """Parameter type that accepts a path on the local file system or a URL.

    :param timeout_seconds: Maximum timeout accepted for URL response. Must be an integer in the range [0;60].
    :returns: The path or URL.
    """

    name = 'PathOrUrl'

    def __init__(self, timeout_seconds: float = URL_TIMEOUT_SECONDS, **kwargs: t.Any):
        super().__init__(**kwargs)

        self.timeout_seconds = check_timeout_seconds(timeout_seconds)

    def convert(self, value: t.Any, param: click.Parameter | None, ctx: click.Context | None) -> t.Any:
        try:
            return super().convert(value, param, ctx)
        except click.exceptions.BadParameter:
            convert_possible_url(value, self.timeout_seconds)
            return value


class FileOrUrl(click.File):
    """Parameter type that accepts a path on the local file system or a URL.

    :param timeout_seconds: Maximum timeout accepted for URL response. Must be an integer in the range [0;60].
    :returns: The file or URL.
    """

    name = 'FileOrUrl'

    def __init__(self, timeout_seconds: float = URL_TIMEOUT_SECONDS, **kwargs: t.Any):
        super().__init__(**kwargs)

        self.timeout_seconds = check_timeout_seconds(timeout_seconds)

    def convert(self, value: t.Any, param: click.Parameter | None, ctx: click.Context | None) -> t.Any:
        try:
            return super().convert(value, param, ctx)
        except click.exceptions.BadParameter:
            return convert_possible_url(value, self.timeout_seconds)
