###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Plugin aware click command Group."""

from __future__ import annotations

import typing as t

import click

from aiida.cmdline.groups import VerdiCommandGroup
from aiida.common import exceptions
from aiida.plugins.entry_point import get_entry_point_names, load_entry_point


class Pluginable(VerdiCommandGroup):
    """A click command group that finds and loads plugin commands lazily."""

    def __init__(self, *args: t.Any, **kwargs: t.Any):
        """Initialize with entry point group."""
        self._exclude_external_plugins = False  # Default behavior is of course to include external plugins
        self._entry_point_group = kwargs.pop('entry_point_group', None)
        super().__init__(*args, **kwargs)

    def list_commands(self, ctx: click.Context) -> list[str]:
        """Add entry point names of available plugins to the command list."""
        subcommands = super().list_commands(ctx)

        if not self._exclude_external_plugins:
            subcommands.extend(get_entry_point_names(self._entry_point_group))

        return subcommands

    def get_command(self, ctx: click.Context, name: str) -> click.Command | None:
        """Try to load a subcommand from entry points, else defer to super."""
        if self._exclude_external_plugins:
            return super().get_command(ctx, name)
        else:
            try:
                return load_entry_point(self._entry_point_group, name)
            except exceptions.EntryPointError:
                return super().get_command(ctx, name)

    def set_exclude_external_plugins(self, exclude_external_plugins: bool) -> None:
        """Set whether external plugins should be excluded.

        If `exclude_external_plugins` is set to `True`, the plugins that belong to the `entry_point_group` defined
        for this `click.Group` will not be discoverable. This is useful to limit the available commands to only those
        provided by `aiida-core` (excluding those provided by plugins).

        :param exclude_external_plugins: bool, when True, external plugins will not be discoverable
        """
        self._exclude_external_plugins = exclude_external_plugins
