# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Click parameter types for paths."""
import os
from socket import timeout
import urllib.error
import urllib.request

import click

__all__ = ('AbsolutePathParamType', 'FileOrUrl', 'PathOrUrl')

URL_TIMEOUT_SECONDS = 10


def check_timeout_seconds(timeout_seconds):
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

    def convert(self, value, param, ctx):
        value = os.path.expanduser(value)
        newval = super().convert(value, param, ctx)
        if not os.path.isabs(newval):
            raise click.BadParameter('path must be absolute')
        return newval

    def __repr__(self):
        return 'ABSOLUTEPATH'


class AbsolutePathOrEmptyParamType(AbsolutePathParamType):
    """The ParamType for identifying absolute Paths, accepting also empty paths."""

    name = 'AbsolutePathEmpty'

    def convert(self, value, param, ctx):
        if not value:
            return value
        return super().convert(value, param, ctx)

    def __repr__(self):
        return 'ABSOLUTEPATHEMPTY'


class PathOrUrl(click.Path):
    """Extension of click's Path-type to include URLs.

    A PathOrUrl can either be a `click.Path`-type or a URL.

    :param int timeout_seconds: Maximum timeout accepted for URL response.
        Must be an integer in the range [0;60].
    """

    name = 'PathOrUrl'

    def __init__(self, timeout_seconds=URL_TIMEOUT_SECONDS, **kwargs):
        super().__init__(**kwargs)

        self.timeout_seconds = check_timeout_seconds(timeout_seconds)

    def convert(self, value, param, ctx):
        """Overwrite `convert` Check first if `click.Path`-type, then check if URL."""
        try:
            return super().convert(value, param, ctx)
        except click.exceptions.BadParameter:
            return self.checks_url(value, param, ctx)

    def checks_url(self, url, param, ctx):
        """Check whether URL is reachable within timeout."""
        try:
            with urllib.request.urlopen(url, timeout=self.timeout_seconds):
                pass
        except (urllib.error.URLError, urllib.error.HTTPError, timeout):
            self.fail(f'{self.name} "{url}" could not be reached within {self.timeout_seconds} s.\n', param, ctx)

        return url


class FileOrUrl(click.File):
    """Extension of click's File-type to include URLs.

    Returns handle either to local file or to remote file fetched from URL.

    :param int timeout_seconds: Maximum timeout accepted for URL response.
        Must be an integer in the range [0;60].
    """

    name = 'FileOrUrl'

    def __init__(self, timeout_seconds=URL_TIMEOUT_SECONDS, **kwargs):
        super().__init__(**kwargs)

        self.timeout_seconds = check_timeout_seconds(timeout_seconds)

    def convert(self, value, param, ctx):
        """Return file handle."""
        try:
            return super().convert(value, param, ctx)
        except click.exceptions.BadParameter:
            handle = self.get_url(value, param, ctx)
        return handle

    def get_url(self, url, param, ctx):
        """Retrieve file from URL."""
        try:
            return urllib.request.urlopen(url, timeout=self.timeout_seconds)  # pylint: disable=consider-using-with
        except (urllib.error.URLError, urllib.error.HTTPError, timeout):
            self.fail(f'{self.name} "{url}" could not be reached within {self.timeout_seconds} s.\n', param, ctx)
