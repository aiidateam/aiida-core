###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Module to define the custom click type for code."""

from __future__ import annotations

import typing as t

import click
from click.shell_completion import CompletionItem

if t.TYPE_CHECKING:
    from aiida.manage.configuration.options import Option

__all__ = ('ConfigOptionParamType',)


class ConfigOptionParamType(click.types.StringParamType):
    """ParamType for configuration options."""

    name = 'config option'

    def convert(self, value: t.Any, param: click.Parameter | None, ctx: click.Context | None) -> Option:
        from aiida.manage.configuration.options import get_option, get_option_names

        if value not in get_option_names():
            raise click.BadParameter(f'{value} is not a valid configuration option')

        return get_option(value)

    def shell_complete(self, ctx: click.Context, param: click.Parameter, incomplete: str) -> list[CompletionItem]:
        """Return possible completions based on an incomplete value

        :returns: list of tuples of valid entry points (matching incomplete) and a description
        """
        from aiida.manage.configuration.options import get_option_names

        return [CompletionItem(option_name) for option_name in get_option_names() if option_name.startswith(incomplete)]
