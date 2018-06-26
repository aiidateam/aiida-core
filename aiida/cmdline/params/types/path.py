# -*- coding: utf-8 -*-
"""Click parameter types for paths."""
import os
import click


class AbsolutePathParamType(click.Path):
    """
    The ParamType for identifying absolute Paths (derived from click.Path).
    """

    name = 'AbsolutePath'

    def convert(self, value, param, ctx):
        newval = super(AbsolutePathParamType, self).convert(value, param, ctx)
        if not os.path.isabs(newval):
            raise click.BadParameter('path must be absolute')
        return newval

    def __repr__(self):
        return 'ABSOLUTEPATH'
