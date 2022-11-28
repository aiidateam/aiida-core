# -*- coding: utf-8 -*-
"""Subclass of :class:`click.Group` that loads subcommands dynamically from entry points."""
from __future__ import annotations

import copy
import functools
import re

import click

from aiida.common import exceptions
from aiida.plugins.entry_point import ENTRY_POINT_GROUP_FACTORY_MAPPING, get_entry_point_names

from ..params import options
from ..params.options.interactive import InteractiveOption
from .verdi import VerdiCommandGroup

__all__ = ('DynamicEntryPointCommandGroup',)


class DynamicEntryPointCommandGroup(VerdiCommandGroup):
    """Subclass of :class:`click.Group` that loads subcommands dynamically from entry points.

    A command group using this class will automatically generate the sub commands from the entry points registered in
    the given ``entry_point_group``. The entry points can be additionally filtered using a regex defined for the
    ``entry_point_name_filter`` keyword. The actual command for each entry point is defined by ``command``, which should
    take as a first argument the class that corresponds to the entry point. In addition, it should accept ``kwargs``
    which will be the values for the options passed when the command is invoked. The help string of the command will be
    provided by the docstring of the class registered at the respective entry point. Example usage:

    .. code:: python

        def create_instance(cls, **kwargs):
            instance = cls(**kwargs)
            instance.store()
            echo.echo_success(f'Created {cls.__name__}<{instance.pk}>')

        @click.group('create', cls=DynamicEntryPointCommandGroup, command=create_instance,)
        def cmd_create():
            pass

    """

    def __init__(self, command, entry_point_group: str, entry_point_name_filter=r'.*', **kwargs):
        super().__init__(**kwargs)
        self.command = command
        self.entry_point_group = entry_point_group
        self.entry_point_name_filter = entry_point_name_filter
        self.factory = ENTRY_POINT_GROUP_FACTORY_MAPPING[entry_point_group]

    def list_commands(self, ctx) -> list[str]:
        """Return the sorted list of subcommands for this group.

        :param ctx: The :class:`click.Context`.
        """
        commands = super().list_commands(ctx)
        commands.extend([
            entry_point for entry_point in get_entry_point_names(self.entry_point_group)
            if re.match(self.entry_point_name_filter, entry_point)
        ])
        return sorted(commands)

    def get_command(self, ctx, cmd_name):
        """Return the command with the given name.

        :param ctx: The :class:`click.Context`.
        :param cmd_name: The name of the command.
        :returns: The :class:`click.Command`.
        """
        try:
            command = self.create_command(cmd_name)
        except exceptions.EntryPointError:
            command = super().get_command(ctx, cmd_name)
        return command

    def create_command(self, entry_point):
        """Create a subcommand for the given ``entry_point``."""
        cls = self.factory(entry_point)
        command = functools.partial(self.command, cls)
        command.__doc__ = cls.__doc__
        return click.command(entry_point)(self.create_options(entry_point)(command))

    def create_options(self, entry_point):
        """Create the option decorators for the command function for the given entry point.

        :param entry_point: The entry point.
        """

        def apply_options(func):
            """Decorate the command function with the appropriate options for the given entry point."""
            func = options.NON_INTERACTIVE()(func)
            func = options.CONFIG_FILE()(func)

            options_list = self.list_options(entry_point)
            options_list.reverse()

            for option in options_list:
                func = option(func)

            return func

        return apply_options

    def list_options(self, entry_point):
        """Return the list of options that should be applied to the command for the given entry point.

        :param entry_point: The entry point.
        """
        return [self.create_option(*item) for item in self.factory(entry_point).get_cli_options().items()]

    @staticmethod
    def create_option(name, spec):
        """Create a click option from a name and a specification."""
        spec = copy.deepcopy(spec)

        is_flag = spec.pop('is_flag', False)
        name_dashed = name.replace('_', '-')
        option_name = f'--{name_dashed}/--no-{name_dashed}' if is_flag else f'--{name_dashed}'

        option_short_name = spec.pop('short_name', None)

        kwargs = {'cls': spec.pop('cls', InteractiveOption), 'show_default': True, 'is_flag': is_flag, **spec}

        if option_short_name:
            option = click.option(option_short_name, option_name, **kwargs)
        else:
            option = click.option(option_name, **kwargs)

        return option
