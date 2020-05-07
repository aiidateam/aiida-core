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
.. py:module::contextualdefault
    :synopsis: Tools for options which allow for a default callable that needs
    also the context ctx
"""

import click


class ContextualDefaultOption(click.Option):
    """A class that extends click.Option allowing to define a default callable
    that also get the context ctx as a parameter.
    """

    def __init__(self, *args, contextual_default=None, **kwargs):
        self._contextual_default = contextual_default
        super().__init__(*args, **kwargs)

    def get_default(self, ctx):
        """If a contextual default is defined, use it, otherwise behave normally."""
        if self._contextual_default is None:
            return super().get_default(ctx)
        return self._contextual_default(ctx)
