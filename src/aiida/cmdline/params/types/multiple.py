###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Module to define custom click param type for multiple values"""

from __future__ import annotations

import typing as t

import click

from .._shims import shim_add_ctx

__all__ = ('MultipleValueParamType',)


class MultipleValueParamType(click.ParamType):
    """An extension of click.ParamType that can parse multiple values for a given ParamType"""

    def __init__(self, param_type: click.ParamType):
        """Construct a new instance."""
        super().__init__()
        self._param_type = param_type

        if hasattr(param_type, 'name'):
            self.name = f'{param_type.name}...'
        elif hasattr(param_type, '__name__'):
            self.name = f'{param_type.__name__.upper()}...'
        else:
            self.name = ''

    @shim_add_ctx
    def get_metavar(self, param: click.Parameter, ctx: click.Context | None) -> str | None:
        try:
            if ctx is not None:
                return self._param_type.get_metavar(param, ctx=ctx)
            else:
                return self._param_type.get_metavar(param)  # type: ignore[call-arg]
        except AttributeError:
            return self.name

    def convert(self, value: t.Any, param: click.Parameter | None, ctx: click.Context | None) -> tuple[t.Any, ...]:
        try:
            return tuple(self._param_type(entry) for entry in value)
        except ValueError:
            self.fail(f'could not convert {value} into type {self._param_type}')
