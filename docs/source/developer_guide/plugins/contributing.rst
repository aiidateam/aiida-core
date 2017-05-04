Developing The Plugin System
============================

Design Principles
+++++++++++++++++

1. Only restrict plugin developers when really necessary
1. Avoid schema changes whenever reasonably possible
1. Finding and loading plugins must be as fast as the plugin allows (especially for cli commands). In other words, directly importing a plugin class should not be noticeably faster than using the pluginloader / factory
1. Implement as a drop-in replacement, provide backwards compatibility at first, think about changing interfaces if / when the old system is dropped
1. plugin management should be as user friendly from ipython as from the cli.

Mini-Spec
+++++++++

Terms
-----
``plugin_name``
   A unique name identifying the plugin. Suggested naming scheme is

   * pypi distribution / repo name: aiida-<plugin_name>
   * import name: aiida_<plugin_name>
   * entry point names: <plugin_name>.name

``name`` (entry point)
   The entry point for a plugin class looks as follows::

      name = <module_path>:<classname>

   Therefore within a plugin category the name allows us to find a specific plugin (as well as a typestring) The name is recommended to contain the plugin name (as detailed under ``plugin_name``.

``category``
   A name given to each area extensible via plugins, one of

   * calculations
   * data
   * parsers
   * schedulers
   * transports
   * workflows
   * tools.dbexporters
   * tools.dbimporters
   * tools.dbexporters.tcod_plugins

   Each category maps to an entry point group called::
   
      aiida.<category>

Interfaces
----------

Pluginloader (aiida/common/pluginloader.py)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The pluginloader relies on reentry (PYPI package) to find and load entry points. reentry has been added to setup_requires for aiida in order to enable scanning for existing plugins when aiida is installed. If for some reason reentry should be uninstalled, the plugin system will fall back on pkg_resources from setuptools, which is slower.

The API docs are found at the following link: :ref:`aiida-autodocs-pluginloader`.

Registry Tools (aiida/plugins)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The registry tools API is located here: :ref:`aiida-autodocs-plugins`.
