###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Module for various text-based string validation."""

from __future__ import annotations

import re
import typing as t

import click
from click.types import StringParamType

__all__ = ('EmailType', 'EntryPointType', 'HostnameType', 'LabelStringType', 'NonEmptyStringParamType')


class NonEmptyStringParamType(StringParamType):
    """Parameter whose values have to be string and non-empty."""

    name = 'nonemptystring'

    def convert(self, value: t.Any, param: click.Parameter | None, ctx: click.Context | None) -> str:
        # NOTE: The return value of click.StringParamType.convert is typed as t.Any,
        # but from its implementation its clear that it returns a string.
        newval = t.cast(str, super().convert(value, param, ctx))

        if not newval:  # empty string
            self.fail('Empty string is not valid!')

        return newval

    def __repr__(self) -> str:
        return 'NONEMPTYSTRING'


class LabelStringType(NonEmptyStringParamType):
    """Parameter accepting valid label strings.

    Non-empty string, made up of word characters (includes underscores [1]), dashes, and dots.

    [1] See https://docs.python.org/3/library/re.html
    """

    name = 'labelstring'

    ALPHABET = r'\w\.\-'

    def convert(self, value: t.Any, param: click.Parameter | None, ctx: click.Context | None) -> str:
        newval = super().convert(value, param, ctx)

        if not re.match(f'^[{self.ALPHABET}]*$', newval):
            self.fail('Please use only alphanumeric characters, dashes, underscores or dots')

        return newval

    def __repr__(self) -> str:
        return 'LABELSTRING'


HOSTNAME_REGEX = re.compile(
    r'^([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])'
    r'(\.([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]{0,61}[a-zA-Z0-9]))*$'
)


class HostnameType(StringParamType):
    """Parameter corresponding to a valid hostname (or empty) string.

    Regex according to https://stackoverflow.com/a/3824105/1069467
    """

    name = 'hostname'

    def convert(self, value: t.Any, param: click.Parameter | None, ctx: click.Context | None) -> str:
        newval = t.cast(str, super().convert(value, param, ctx))

        if newval and not HOSTNAME_REGEX.match(newval):
            self.fail('Please enter a valid hostname.')

        return newval

    def __repr__(self) -> str:
        return 'HOSTNAME'


class EmailType(StringParamType):
    """Parameter whose values have to correspond to a valid email address format.

    .. note:: For the moment, we do not require the domain suffix, i.e. 'aiida@localhost' is still valid.
    """

    name = 'email'

    def convert(self, value: t.Any, param: click.Parameter | None, ctx: click.Context | None) -> str:
        newval = t.cast(str, super().convert(value, param, ctx))

        if not re.match(r'[^@]+@[^@]+(\.[^@]+){0,1}', newval):
            self.fail('Please enter a valid email.')

        return newval

    def __repr__(self) -> str:
        return 'EMAIL'


class EntryPointType(NonEmptyStringParamType):
    """Parameter whose values have to be valid Python entry point strings.

    See https://packaging.python.org/en/latest/specifications/entry-points/
    """

    name = 'entrypoint'

    def convert(self, value: t.Any, param: click.Parameter | None, ctx: click.Context | None) -> str:
        newval = super().convert(value, param, ctx)

        if not re.match(r'[\w.-]', newval):
            self.fail(
                'Please enter a valid entry point string: Use only letters, numbers, undercores, dots and dashes.'
            )

        return newval

    def __repr__(self) -> str:
        return 'ENTRYPOINT'
