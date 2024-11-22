###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Utilities dealing with plugins and entry points."""

from __future__ import annotations

import typing as t
from importlib import import_module
from logging import Logger
from types import FunctionType

from aiida.common import AIIDA_LOGGER
from aiida.common.exceptions import EntryPointError

from .entry_point import load_entry_point_from_string

__all__ = ('PluginVersionProvider',)

KEY_VERSION_ROOT: str = 'version'
KEY_VERSION_CORE: str = 'core'  # The version of `aiida-core`
KEY_VERSION_PLUGIN: str = 'plugin'  # The version of the plugin top level module, e.g. `aiida-quantumespresso`


class PluginVersionProvider:
    """Utility class that determines version information about a given plugin resource."""

    def __init__(self):
        self._cache: dict[type | FunctionType, dict[t.Any, dict[t.Any, t.Any]]] = {}
        self._logger: Logger = AIIDA_LOGGER.getChild('plugin_version_provider')

    @property
    def logger(self) -> Logger:
        return self._logger

    def get_version_info(self, plugin: str | t.Any) -> dict[t.Any, dict[t.Any, t.Any]]:
        """Get the version information for a given plugin.

        .. note::

            This container will keep a cache, so if this method was already called for the given ``plugin`` before for
            this instance, the result computed at the last invocation will be returned.

        :param plugin: A class, function, or an entry point string. If the type is string, it will be assumed to be an
            entry point string and the class will attempt to load it first. It should be a full entry point string,
            including the entry point group.
        :return: Dictionary with the `version.core` and optionally `version.plugin` if it could be determined.
        :raises EntryPointError: If ``plugin`` is a string but could not be loaded as a valid entry point.
        :raises TypeError: If ``plugin`` (or the resource pointed to it in the case of an entry point) is not a class
            or a function.
        """
        from inspect import isclass, isfunction

        from aiida import __version__ as version_core

        if isinstance(plugin, str):
            try:
                plugin = load_entry_point_from_string(plugin)
            except EntryPointError as exc:
                raise EntryPointError(f'got string `{plugin}` but could not load corresponding entry point') from exc

        if not isclass(plugin) and not isfunction(plugin):
            raise TypeError(f'`{plugin}` is not a class nor a function.')

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
            self.logger.debug(f'could not determine the top level module for plugin: {plugin}')
            return self._cache[plugin]

        try:
            version_plugin = parent_module.__version__
        except AttributeError:
            self.logger.debug(f'parent module does not define `__version__` attribute for plugin: {plugin}')
            return self._cache[plugin]

        self._cache[plugin][KEY_VERSION_ROOT][KEY_VERSION_PLUGIN] = version_plugin

        return self._cache[plugin]
