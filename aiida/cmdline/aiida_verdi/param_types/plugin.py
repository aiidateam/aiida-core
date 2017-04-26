#-*- coding: utf8 -*-
"""
click parameter type for Plugins
"""
import click
from click_completion import startswith

from aiida.cmdline.aiida_verdi.verdic_utils import aiida_dbenv


class PluginParam(click.ParamType):
    """
    handle verification, completion for plugin arguments
    """
    name = 'aiida plugin'

    def __init__(self, category=None, available=True, *args, **kwargs):
        self.category = category
        self.must_available = available
        super(PluginParam, self).__init__(*args, **kwargs)
        try:
            '''if aiida has new plugin system'''
            from aiida.common import ep_pluginloader
            self.get_all_plugins = self.new_get_plugins(category)
        except ImportError:
            '''old plugin system'''
            if self.category == 'calculations':
                self.get_all_plugins = self.old_get_calculations
            elif self.category == 'parsers':
                self.get_all_plugins = self.old_get_parsers
            elif self.category == 'transports':
                self.get_all_plugins = self.old_get_transports
            elif self.category == 'schedulers':
                self.get_all_plugins = self.old_get_schedulers
            else:
                raise ValueError('unsupported plugin category for cmdline args')

    def get_possibilities(self, incomplete=''):
        """return a list of plugins starting with incomplete"""
        return [p for p in self.get_all_plugins() if startswith(p, incomplete)]

    @aiida_dbenv
    def old_get_calculations(self):
        """return all available input plugins"""
        from aiida.common.pluginloader import existing_plugins
        from aiida.orm.calculation.job import JobCalculation
        return existing_plugins(
            JobCalculation, 'aiida.orm.calculation.job', suffix='Calculation')

    @aiida_dbenv
    def old_get_parsers(self):
        """return all available parser plugins"""
        from aiida.common.pluginloader import existing_plugins
        from aiida.parsers import Parser
        return existing_plugins(Parser, 'aiida.parsers.plugins')

    @aiida_dbenv
    def old_get_transports(self):
        """return all available transport plugins"""
        from aiida.common.pluginloader import existing_plugins
        from aiida.transport import Transport
        return existing_plugins(Transport, 'aiida.transport.plugins')

    @aiida_dbenv
    def old_get_schedulers(self):
        """return all available scheduler plugins"""
        from aiida.common.pluginloader import existing_plugins
        from aiida.scheduler import Scheduler
        return existing_plugins(Scheduler, 'aiida.scheduler.plugins')

    def new_get_plugins(self, category):
        """use entry points"""
        @aiida_dbenv
        def get_plugins():
            from aiida.common.ep_pluginloader import all_plugins
            return all_plugins(category)
        return get_plugins

    def complete(self, ctx, incomplete):
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
