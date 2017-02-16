#-*- coding: utf8 -*-
"""
This module and the RegistryEntry class should be the sole
location for the (implicit) definition of the registry format.
"""

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
        if 'console_scripts' not in self.entry_points_raw:
            return []
        eps = self.entry_points_raw['console_scripts']
        return [i[:i.find('=')].strip() for i in eps]

    @property
    def gui_apps(self):
        """A list of GUI apps installed by this plugin"""
        if 'gui_scripts' not in self.entry_points_raw:
            return []
        eps = self.entry_points_raw['gui_scripts']
        return [i[:i.find('=')].strip() for i in eps]

    def install(self, **opts):
        """Call on pip to install the package if not yet installed"""
        if self.test_installed():
            return True
        if not self.pip_url:
            raise Exception('The plugin author did not provide an automatic install link')
        from pip.commands.install import InstallCommand
        ic = InstallCommand()
        opts, args = ic.parser.parse_args()
        args.append(self.pip_url)
        for k, v in opts.iteritems():
            setattr(opts, k, v)
        req_set = ci.run(opts, args)
        req_set.install()
        return self.test_installed()

    def test_installed(self):
        """return wether the plugin is installed"""
        from importlib import import_module
        # TODO: catch also old_school install case
        # TODO: Test with aiida-core aiida-qe
        try:
            import_module(self.package_name)
        except:
            from aiida.common.ep_pluginloader import all_plugins
            for cat, ep in self.entry_points.iteritems():
                if not set(ep).issubset(set(all_plugins(cat))):
                    return False
        return True
