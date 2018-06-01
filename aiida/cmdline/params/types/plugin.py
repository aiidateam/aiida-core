#-*- coding: utf8 -*-
"""Click parameter type for AiiDA Plugins."""
import click


class PluginParamType(click.ParamType):
    """
    AiiDA Plugin name parameter type.

    :param category: Str, entry point group without leading "aiida.".
    :param available: [True] bool, If true, the plugin name has to be discoverable by the plugin loader.

    Usage::

        click.option(... type=PluginParamType(category='calculations')

    """
    name = 'aiida plugin'

    def __init__(self, category=None, available=True, *args, **kwargs):
        self.category = 'aiida.{}'.format(category)
        self.must_available = available
        super(PluginParamType, self).__init__(*args, **kwargs)

    def get_possibilities(self, incomplete=''):
        """return a list of plugins starting with incomplete"""
        return [p for p in self.get_all_plugins() if p.startswith(incomplete)]

    def get_all_plugins(self):
        """use entry points"""
        from aiida.plugins.entry_point import get_entry_point_names
        return get_entry_point_names(self.category)

    def complete(self, ctx, incomplete):  # pylint: disable=unused-argument
        """return possible completions"""
        return [(p, '') for p in self.get_possibilities(incomplete=incomplete)]

    def get_missing_message(self, param):
        return 'Possible arguments are:\n\n' + '\n'.join(self.get_all_plugins())

    def convert(self, value, param, ctx):
        """check value vs. possible plugins, raising BadParameter on fail """
        if not value:
            raise click.BadParameter('plugin name cannot be empty')
        if self.must_available:
            pluginlist = self.get_possibilities()
            if param.default:
                pluginlist.append(param.default)
            if value not in pluginlist:
                raise click.BadParameter('{} is not a plugin for category {}'.format(value, self.category))
        return value
