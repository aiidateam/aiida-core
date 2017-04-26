#-*- coding: utf8 -*-
"""
verdi plugin utilities
"""
import click
import click_plugins


def find_plugins(group):
    """get a name:entrypoint dict for an entrypoint group"""
    #from pkg_resources import iter_entry_points
    from reentry.manager import iter_entry_points
    return {i.name: i for i in iter_entry_points(group)}

def load_plugin(ep):
    """load an entrypoint"""
    #from pkg_resources import load_entry_point
    #return load_entry_point(ep)
    return ep.load()


class PluginGroup(click.MultiCommand):
    """
    Prevent plugin loading in subcommands from slowing down the base command
    """
    def __init__(self, *args, **kwargs):
        """
        store extra 'group' argument

        :param group: string, entry point group name to load plugins from
        """
        self.ep_group = kwargs.pop('group')
        super(PluginGroup, self).__init__(*args, **kwargs)

    def list_commands(self, ctx):
        """
        add plugin command names to directly loaded ones
        """
        from aiida.cmdline.aiida_verdi.utils.plugins import find_plugins
        cl = super(PluginGroup, self).list_commands(ctx)
        cl.extend(find_plugins(self.ep_group).keys())
        return cl

    def get_command(self, ctx, name):
        """
        if name not found in subcommands, try to load from entry points
        """
        if name in super(PluginGroup, self).list_commands(ctx):
            return super(PluginGroup, self).get_command(ctx, name)
        else:
            from aiida.cmdline.aiida_verdi.utils.plugins import find_plugins
            from click_plugins.core import BrokenCommand
            try:
                cmd = find_plugins(self.ep_group)[name].load()
                if not issubclass(cmd, click.Command):
                    cmd = BrokenCommand(name)
            except:
                cmd = BrokenCommand(name)

            return cmd
