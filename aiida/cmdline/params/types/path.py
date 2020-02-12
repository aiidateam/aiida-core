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
import urllib

import click

URL_TIMEOUT_SECONDS = 10


class AbsolutePathParamType(click.Path):
    """
    The ParamType for identifying absolute Paths (derived from click.Path).
    """

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
    """
    The ParamType for identifying absolute Paths, accepting also empty paths.
    """

    name = 'AbsolutePathEmpty'

    def convert(self, value, param, ctx):
        if not value:
            return value
        return super().convert(value, param, ctx)

    def __repr__(self):
        return 'ABSOLUTEPATHEMPTY'


class ImportPath(click.Path):
    """AiiDA extension of Click's Path-type to include URLs
    An ImportPath can either be a `click.Path`-type or a URL.
    :param timeout_seconds: Timeout time in seconds that a URL response is expected.
    :value timeout_seconds: Must be an int in the range [0;60], extrema included.
    If an int outside the range [0;60] is given, the value will be set to the respective extremum value.
    If any other type than int is given a TypeError will be raised.
    """

    # pylint: disable=protected-access

    def __init__(self, timeout_seconds=URL_TIMEOUT_SECONDS, **kwargs):
        super().__init__(**kwargs)

        self.timeout_seconds = timeout_seconds

    def convert(self, value, param, ctx):
        """Overwrite `convert`
        Check first if `click.Path`-type, then check if URL.
        """
        try:
            # Check if `click.Path`-type
            return super().convert(value, param, ctx)
        except click.exceptions.BadParameter:
            # Check if URL
            return self.checks_url(value, param, ctx)

    def checks_url(self, value, param, ctx):
        """Do checks for possible URL path"""
        from socket import timeout

        url = value

        try:
            urllib.request.urlopen(url, data=None, timeout=self.timeout_seconds)
        except (urllib.error.URLError, urllib.error.HTTPError, timeout):
            self.fail(
                '{0} "{1}" could not be reached within {2} s.\n'
                'It may be neither a valid {3} nor a valid URL.'.format(
                    self.path_type, click._compat.filename_to_ui(url), self.timeout_seconds, self.name
                ), param, ctx
            )

        return url

    @property
    def timeout_seconds(self):
        return self._timeout_seconds

    # pylint: disable=attribute-defined-outside-init
    @timeout_seconds.setter
    def timeout_seconds(self, value):
        try:
            self._timeout_seconds = int(value)
        except ValueError:
            raise TypeError('timeout_seconds should be an integer but got: {}'.format(type(value)))

        if self._timeout_seconds < 0:
            self._timeout_seconds = 0

        if self._timeout_seconds > 60:
            self._timeout_seconds = 60
