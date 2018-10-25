# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Plugin aware click command Group."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
import click

from aiida.plugins.entry_point import load_entry_point, get_entry_point_names, MissingEntryPointError


class Pluginable(click.Group):
    """A click command group that finds and loads plugin commands lazily."""

    def __init__(self, *args, **kwargs):
        """Initialize with entry point group."""
        self._entry_point_group = kwargs.pop('entry_point_group')
        super(Pluginable, self).__init__(*args, **kwargs)

    def list_commands(self, ctx):
        """Add entry point names of available plugins to the command list."""
        subcommands = super(Pluginable, self).list_commands(ctx)
        subcommands.extend(get_entry_point_names(self._entry_point_group))
        return subcommands

    def get_command(self, ctx, name):  # pylint: disable=arguments-differ
        """Try to load a subcommand from entry points, else defer to super."""
        command = None
        try:
            command = load_entry_point(self._entry_point_group, name)
        except MissingEntryPointError:
            command = super(Pluginable, self).get_command(ctx, name)
        return command
