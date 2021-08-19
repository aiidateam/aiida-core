# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""
Module to define custom click param type for multiple values
"""
import click

__all__ = ('MultipleValueParamType',)


class MultipleValueParamType(click.ParamType):
    """
    An extension of click.ParamType that can parse multiple values for a given ParamType
    """

    def __init__(self, param_type):
        super().__init__()
        self._param_type = param_type

        if hasattr(param_type, 'name'):
            self.name = f'{param_type.name}...'
        else:
            self.name = f'{param_type.__name__.upper()}...'

    def get_metavar(self, param):
        try:
            return self._param_type.get_metavar(param)
        except AttributeError:
            return self.name

    def convert(self, value, param, ctx):
        try:
            return tuple(self._param_type(entry) for entry in value)
        except ValueError:
            self.fail(f'could not convert {value} into type {self._param_type}')
