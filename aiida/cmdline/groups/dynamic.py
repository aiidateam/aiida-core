# -*- coding: utf-8 -*-
"""Subclass of :class:`click.Group` that loads subcommands dynamically from entry points."""
from __future__ import annotations

import copy
import functools
import re
import typing as t

import click

from aiida.common import exceptions
from aiida.plugins.entry_point import ENTRY_POINT_GROUP_FACTORY_MAPPING, get_entry_point_names
from aiida.plugins.factories import BaseFactory

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

    def __init__(
        self,
        command: t.Callable,
        entry_point_group: str,
        entry_point_name_filter: str = r'.*',
        shared_options: list[click.Option] | None = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self._command = command
        self.entry_point_group = entry_point_group
        self.entry_point_name_filter = entry_point_name_filter
        self.factory = ENTRY_POINT_GROUP_FACTORY_MAPPING.get(
            entry_point_group, functools.partial(BaseFactory, entry_point_group)
        )
        self.shared_options = shared_options

    def list_commands(self, ctx: click.Context) -> list[str]:
        """Return the sorted list of subcommands for this group.

        :param ctx: The :class:`click.Context`.
        """
        commands = super().list_commands(ctx)
        commands.extend([
            entry_point for entry_point in get_entry_point_names(self.entry_point_group)
            if re.match(self.entry_point_name_filter, entry_point) and
            getattr(self.factory(entry_point), 'cli_exposed', True)
        ])
        return sorted(commands)

    def get_command(self, ctx: click.Context, cmd_name: str) -> click.Command | None:
        """Return the command with the given name.

        :param ctx: The :class:`click.Context`.
        :param cmd_name: The name of the command.
        :returns: The :class:`click.Command`.
        """
        try:
            command: click.Command | None = self.create_command(ctx, cmd_name)
        except exceptions.EntryPointError:
            command = super().get_command(ctx, cmd_name)
        return command

    def create_command(self, ctx: click.Context, entry_point: str) -> click.Command:
        """Create a subcommand for the given ``entry_point``."""
        cls = self.factory(entry_point)
        command = functools.partial(self._command, ctx, cls)
        command.__doc__ = cls.__doc__
        return click.command(entry_point)(self.create_options(entry_point)(command))

    def create_options(self, entry_point: str) -> t.Callable:
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

            shared_options = self.shared_options or []
            shared_options.reverse()

            for option in shared_options:
                func = option(func)

            return func

        return apply_options

    def list_options(self, entry_point: str) -> list:
        """Return the list of options that should be applied to the command for the given entry point.

        :param entry_point: The entry point.
        """
        from pydantic_core import PydanticUndefined

        cls = self.factory(entry_point)

        if not hasattr(cls, 'Configuration'):
            # This should be enabled once the ``Code`` classes are migrated to using pydantic to define their model.
            # See https://github.com/aiidateam/aiida-core/pull/6190
            # from aiida.common.warnings import warn_deprecation
            # warn_deprecation(
            #     'Relying on `_get_cli_options` is deprecated. The options should be defined through a '
            #     '`pydantic.BaseModel` that should be assigned to the `Config` class attribute.',
            #     version=3
            # )
            options_spec = self.factory(entry_point).get_cli_options()  # type: ignore[union-attr]
        else:

            options_spec = {}

            for key, field_info in cls.Configuration.model_fields.items():
                default = field_info.default_factory if field_info.default is PydanticUndefined else field_info.default

                # The ``field_info.annotation`` property returns the annotation of the field. This can be a plain type
                # or a type from ``typing``, e.g., ``Union[int, float]`` or ``Optional[str]``. In these cases, the type
                # that needs to be passed to ``click`` is the arguments of the type, which can be obtained using the
                # ``typing.get_args()`` method. If it is not a compound type, this returns an empty tuplem so in that
                # case, the type is simply the ``field_info.annotation``.
                options_spec[key] = {
                    'required': field_info.is_required(),
                    'type': t.get_args(field_info.annotation) or field_info.annotation,
                    'prompt': field_info.title,
                    'default': default,
                    'help': field_info.description,
                }

        return [self.create_option(*item) for item in options_spec.items()]

    @staticmethod
    def create_option(name, spec: dict) -> t.Callable[[t.Any], t.Any]:
        """Create a click option from a name and a specification."""
        spec = copy.deepcopy(spec)

        is_flag = spec.pop('is_flag', False)
        default = spec.get('default')
        name_dashed = name.replace('_', '-')
        option_name = f'--{name_dashed}/--no-{name_dashed}' if is_flag else f'--{name_dashed}'
        option_short_name = spec.pop('short_name', None)
        option_names = (option_short_name, option_name) if option_short_name else (option_name,)

        kwargs = {'cls': spec.pop('cls', InteractiveOption), 'show_default': True, 'is_flag': is_flag, **spec}

        # If the option is a flag with no default, make sure it is not prompted for, as that will force the user to
        # specify it to be on or off, but cannot let it unspecified.
        if kwargs['cls'] is InteractiveOption and is_flag and default is None:
            kwargs['cls'] = functools.partial(InteractiveOption, prompt_fn=lambda ctx: False)

        return click.option(*(option_names), **kwargs)
