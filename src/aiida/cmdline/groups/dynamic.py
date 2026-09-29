"""Subclass of :class:`click.Group` that loads subcommands dynamically from entry points."""

from __future__ import annotations

import functools
import re
import typing as t

import click

from aiida.cmdline.groups.verdi import VerdiCommandGroup
from aiida.cmdline.params import options
from aiida.cmdline.params.options.interactive import InteractiveOption
from aiida.common import exceptions
from aiida.plugins.entry_point import ENTRY_POINT_GROUP_FACTORY_MAPPING, get_entry_point_names
from aiida.plugins.factories import BaseFactory

if t.TYPE_CHECKING:
    from click.decorators import FC

    from aiida.cmdline.spec import CliCreateSpec

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
        command: click.Command,
        entry_point_group: str,
        entry_point_name_filter: str = r'.*',
        shared_options: list[FC] | None = None,
        **kwargs: t.Any,
    ) -> None:
        super().__init__(**kwargs)

        self._command = command
        self.entry_point_group = entry_point_group
        self.entry_point_name_filter = entry_point_name_filter
        self.factory = ENTRY_POINT_GROUP_FACTORY_MAPPING.get(
            entry_point_group,
            functools.partial(BaseFactory, entry_point_group),
        )
        self.shared_options = shared_options

    def _get_cli_create_spec(self, cls: type[t.Any]) -> CliCreateSpec | None:
        """Return the CLI creation specification exposed by a class."""
        from aiida.cmdline.spec import CliCreateSpec

        factory = getattr(cls, 'cli_spec', None)

        if factory is None:
            return None

        return t.cast(CliCreateSpec, factory)

    def _supports_cli_creation(self, entry_point: str) -> bool:
        """Return whether the plugin supports CLI-based creation."""
        cls = self.factory(entry_point)
        return self._get_cli_create_spec(cls) is not None  # type: ignore[arg-type]

    def list_commands(self, ctx: click.Context) -> list[str]:
        """Return the sorted list of subcommands for this group."""
        commands = super().list_commands(ctx)

        commands.extend(
            entry_point
            for entry_point in get_entry_point_names(self.entry_point_group)
            if re.match(self.entry_point_name_filter, entry_point)
            and getattr(self.factory(entry_point), 'cli_exposed', True)
            and self._supports_cli_creation(entry_point)
        )

        return sorted(commands)

    def get_command(self, ctx: click.Context, cmd_name: str) -> click.Command | None:
        """Return the command with the given name."""
        try:
            if not self._supports_cli_creation(cmd_name):
                return super().get_command(ctx, cmd_name)

            return self.create_command(ctx, cmd_name)
        except exceptions.EntryPointError:
            return super().get_command(ctx, cmd_name)

    def call_command(
        self,
        ctx: click.Context,
        cls: type[t.Any],
        non_interactive: bool,
        **kwargs: t.Any,
    ) -> t.Any:
        """Validate CLI inputs and call the configured creation command."""
        from pydantic import ValidationError

        cli_spec = self._get_cli_create_spec(cls)

        if cli_spec is None:
            msg = f'{cls.__name__} does not support CLI creation'
            raise TypeError(msg)

        try:
            model = cli_spec.validate(kwargs)
        except ValidationError as exception:
            error = exception.errors()[0]

            param_hint = [f'--{str(location).replace("_", "-")}' for location in error['loc']]
            message = '\n'.join(str(item['msg']) for item in exception.errors())

            raise click.BadParameter(
                message,
                param_hint=param_hint or 'one or more parameters',  # type: ignore[arg-type]
            ) from exception
        except ValueError as exception:
            raise click.BadParameter(str(exception)) from exception

        return self._command(ctx, cls, model=model)

    def create_command(self, ctx: click.Context, entry_point: str) -> click.Command:
        """Create a subcommand for the given entry point."""
        cls = self.factory(entry_point)

        command = functools.partial(self.call_command, ctx, cls)  # type: ignore[arg-type]
        command.__doc__ = cls.__doc__

        return click.command(entry_point)(self.create_options(entry_point)(command))

    def create_options(self, entry_point: str) -> t.Callable[[FC], FC]:
        """Create the option decorators for the given entry point."""

        def apply_options(func: FC) -> FC:
            func = options.NON_INTERACTIVE()(func)
            func = options.CONFIG_FILE()(func)

            dynamic_options = self.list_options(entry_point)
            dynamic_options.reverse()

            for option in dynamic_options:
                func = option(func)

            shared_options = list(self.shared_options or [])
            shared_options.reverse()

            for option in shared_options:
                func = option(func)

            return func

        return apply_options

    def list_options(self, entry_point: str) -> list[t.Callable[[FC], FC]]:
        """Return the options that should be applied to the command."""
        cls = self.factory(entry_point)
        cli_spec = self._get_cli_create_spec(cls)  # type: ignore[arg-type]

        if cli_spec is None:
            return []

        parameters = sorted(
            cli_spec.parameters(),
            key=lambda parameter: parameter.priority,
            reverse=True,
        )

        return [
            self.create_option(
                parameter.name,
                parameter.as_option_spec(),
            )
            for parameter in parameters
        ]

    @staticmethod
    def create_option(name: str, spec: dict[str, t.Any]) -> t.Callable[[FC], FC]:
        """Create a Click option from a name and specification."""
        is_flag = spec.pop('is_flag', False)
        spec.pop('priority', None)

        name_dashed = name.replace('_', '-')
        option_name = f'--{name_dashed}/--no-{name_dashed}' if is_flag else f'--{name_dashed}'

        short_name = spec.pop('short_name', '')
        option_names = (short_name, option_name) if short_name else (option_name,)

        kwargs = {
            'cls': spec.pop('option_cls', InteractiveOption),
            'show_default': True,
            'is_flag': is_flag,
            **spec,
        }

        # A nullable boolean should not be prompted for, since an interactive prompt
        # would force the value to either True or False instead of allowing None.
        if kwargs['cls'] is InteractiveOption and is_flag and spec.get('default') is None:
            kwargs['cls'] = functools.partial(
                InteractiveOption,
                prompt_fn=lambda ctx: False,
            )

        return click.option(*option_names, **kwargs)
