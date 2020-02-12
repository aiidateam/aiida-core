# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Utilities dealing with plugins and entry points."""

from importlib import import_module

from aiida.common import AIIDA_LOGGER

__all__ = ('PluginVersionProvider',)

KEY_VERSION_ROOT = 'version'
KEY_VERSION_CORE = 'core'  # The version of `aiida-core`
KEY_VERSION_PLUGIN = 'plugin'  # The version of the plugin top level module, e.g. `aiida-quantumespresso`


class PluginVersionProvider:
    """Utility class that determines version information about a given plugin resource."""

    def __init__(self):
        self._cache = {}
        self._logger = AIIDA_LOGGER.getChild('plugin_version_provider')

    @property
    def logger(self):
        return self._logger

    def get_version_info(self, plugin):
        """Get the version information for a given plugin.

        .. note::

            This container will keep a cache, so if this function was already called for the given ``plugin`` before
            for this instance, the result computer at last invocation will be returned.

        :param plugin: a class or function
        :return: dictionary with the `version.core` and optionally `version.plugin` if it could be determined.
        """
        from aiida import __version__ as version_core

        # If the `plugin` already exists in the cache, simply return it. On purpose we do not verify whether the version
        # information is completed. If it failed the first time, we don't retry. If the failure was temporarily, whoever
        # holds a reference to this instance can simply reconstruct it to start with a clean slate.
        if plugin in self._cache:
            return self._cache[plugin]

        self._cache[plugin] = {
            KEY_VERSION_ROOT: {
                KEY_VERSION_CORE: version_core,
            }
        }

        try:
            parent_module_name = plugin.__module__.split('.')[0]
            parent_module = import_module(parent_module_name)
        except (AttributeError, IndexError, ImportError):
            self.logger.debug('could not determine the top level module for plugin: {}'.format(plugin))
            return self._cache[plugin]

        try:
            version_plugin = parent_module.__version__
        except AttributeError:
            self.logger.debug('parent module does not define `__version__` attribute for plugin: {}'.format(plugin))
            return self._cache[plugin]

        self._cache[plugin][KEY_VERSION_ROOT][KEY_VERSION_PLUGIN] = version_plugin

        return self._cache[plugin]
