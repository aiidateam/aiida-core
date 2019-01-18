# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""
Cached information for each plugin.

This module and the RegistryEntry class should be the sole
location for the (implicit) definition of the registry format.
"""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import


class InvalidPluginEntryError(Exception):
    def __init__(self, msg=''):
        msg = 'Error: Invalid Plugin Registry Entry: {}'.format(msg)
        super(InvalidPluginEntryError, self).__init__(msg)


class RegistryEntry(object):
    """
    Can be created from an entry in the online aiida plugin registry.
    An instance will be created and cached for each entry on update.
    """
    def __init__(self, **kwargs):
        """
        stores registry entry keys and loads the setup_info from the url given in plugin_info
        """
        self.entry_point = kwargs['entry_point']
        self.name = kwargs['name']
        self.pip_url = kwargs.get('pip_url', None)
        self.info_url = kwargs['plugin_info']
        self.load_setup_info(self.info_url)

        '''placeholders'''
        self._entry_points = {}

    def load_setup_info(self, info_url):
        """Load setup kwargs from the link in the registry"""
        from aiida.plugins.utils import load_json_from_url
        self.setup_info = load_json_from_url(info_url)
        required = ['name', 'version', 'author', 'author_email', 'description',
                    'url', 'license']
        for kw in required:
            if kw not in self.setup_info:
                msg = '"{}" is missing the key "{}" in the file in info_url'.format(self.name, kw)
                raise InvalidPluginEntryError(msg)

    @property
    def package_name(self):
        """The name used to import the package"""
        return self.setup_info['name']

    @property
    def version(self):
        """The version of the plugin package"""
        return self.setup_info['version']

    @property
    def entry_points_raw(self):
        """The full entry point spec in setuptools.setup() format"""
        return self.setup_info['entry_points']

    @property
    def entry_point_categories(self):
        """A list of categories for which this plugin exposes entry points"""
        eps = self.entry_points_raw
        return [i.replace('aiida.', '') for i in eps if i.startswith('aiida')]

    @property
    def entry_points(self):
        """A dict of entry point names by category"""
        if not self._entry_points:
            for category in self.entry_point_categories:
                key = 'aiida.' + category
                ep_list = [i[:i.find('=')].strip() for i in self.entry_points_raw[key]]
                self._entry_points[category] = ep_list
        return self._entry_points

    @property
    def cli_apps(self):
        """A list of cli apps installed by this plugin"""
        eps = self.entry_points_raw.get('console_scripts', [])
        return [i[:i.find('=')].strip() for i in eps]

    @property
    def gui_apps(self):
        """A list of GUI apps installed by this plugin"""
        eps = self.entry_points_raw.get('gui_scripts', [])
        return [i[:i.find('=')].strip() for i in eps]

    def install(self, **opts):
        """Call on pip to install the package if not yet installed"""
        installed, new_style, ivers = self.test_installed()
        if installed:
            return True
        if not self.pip_url:
            raise Exception('The plugin author did not provide an automatic install link')
        from pip.commands.install import InstallCommand
        ic = InstallCommand()
        opts, args = ic.parser.parse_args()
        args.append(self.pip_url)
        for k, v in opts.__dict__.items():
            setattr(opts, k, v)
        req_set = ic.run(opts, args)
        req_set.install(opts)
        return self.test_installed()

    def test_installed(self):
        """
        Return wether the plugin is installed

        First, this checks wether the package_name can be imported.
        If not, we know that at least no new style plugin with
        that name is installed.

        Secondly, tests wether all the entry points are currently
        found by the plugin loader. If not, it is considered not
        installed.

        potential failures:
            * loading of the entry points is not tested
            * not properly uninstalled plugins might show up as
                installed if the entry points are still around.
            * it does not distinguish between not installed and
                an old version is installed
        """
        from importlib import import_module
        from pkg_resources import get_distribution
        new_style = False
        installed = True
        iversion = None
        try:
            import_module(self.package_name)
            new_style = True
            iversion = get_distribution(self.package_name).version
        except ImportError:
            new_style = False

        from aiida.plugins.entry_point import get_entry_point_names

        if iversion == self.version or not new_style:
            for cat, ep in self.entry_points.items():
                if not set(ep).issubset(set(get_entry_point_names('aiida.' + cat))):
                    installed = False
        return installed, new_style, iversion

    @property
    def install_requirements(self):
        return self.setup_info.get('install_requires', [])

    @property
    def extras_requirements(self):
        return self.setup_info.get('extras_require', [])

    @property
    def author(self):
        return self.setup_info.get('author')

    @property
    def author_email(self):
        return self.setup_info.get('author_email')

    @property
    def description(self):
        return self.setup_info.get('description')

    @property
    def tags(self):
        return self.setup_info.get('keywords', [])

    @property
    def home_url(self):
        return self.setup_info['url']

    @property
    def installed(self):
        installed, new_style, version = self.test_installed()
        if new_style:
            installed = version or '?'
        return installed

    def format_info(self, **kwargs):
        """
        format and return a datastructure containing all known information about the plugin

        :param format: str, one of [tabulate | dict]
            tabulate: use tabulate to create and return a table of properties as a string
            dict: create a dict of properties
        :param as_str: bool
            format='dict' and as_str=True: return a pretty printed string version of the dict
            format='dict' and as_str=False: return a dictionary
            format='tabulate': as_str is ignored
        """
        fmt = kwargs.pop('format', None)
        as_str = kwargs.pop('as_str', False)
        res = ''
        if fmt == 'tabulate':
            table = []
            table.append(['Name:', self.name])
            table.append(['Version:', self.version])
            table.append(['Installed:', self.installed])
            table.append(['Pip url:', self.pip_url])
            table.append(['Project home:', self.home_url])
            table.append(['Author:', self.author])
            table.append(['Author Email:', self.author_email])
            table.append(['Package:', self.package_name])
            table.append(['Description:', self.description])
            table.append(['Plugins:', ''])
            for category, eps in self.entry_points.items():
                table.append(['', category.capitalize() + ':'])
                table.extend([['', ep] for ep in eps])
                table.append(['', ''])
            if self.cli_apps:
                table.append(['CLI apps:', ''])
                table.extend([['', app] for app in self.cli_apps])
            if self.gui_apps:
                table.append(['GUI apps:', ''])
                table.extend([['', app] for app in self.gui_apps])
            if as_str:
                from tabulate import tabulate
                res = tabulate(table, **kwargs)
            else:
                res = table
        elif fmt == 'dict':
            res = {
                'name': self.name,
                'version': self.version,
                'installed': self.installed,
                'pip url': self.pip_url,
                'project home': self.home_url,
                'author': self.author,
                'author email': self.author_email,
                'package:': self.package_name,
                'description': self.description,
                'plugins': self.entry_points,
                'cli apps': self.cli_apps,
                'gui apps': self.gui_apps
            }
            if as_str:
                import pprint
                res = pprint.pformat(res)
        return res
