"""Plugin aware click command Group."""
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
        subcommands = super(Pluginable, self).list_commands()
        subcommands.extend(get_entry_point_names(self._entry_point_group))

    def get_command(self, ctx, name):
        """Try to load a subcommand from entry points, else defer to super."""
        command = None
        try:
            command = load_entry_point(self._entry_point_group, name)
        except MissingEntryPointError:
            command = super(Pluginable, self).get_command(ctx, name)
        return command
