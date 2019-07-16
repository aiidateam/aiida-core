Developing The Plugin System
============================

.. note:: this page is intended for people wanting to contribute to 
   the plugin system in ``aiida-core`` and is not needed for people who just want to contribute a plugin.

Design Principles
+++++++++++++++++

1. Only restrict plugin developers when really necessary;

2. Avoid schema changes whenever reasonably possible;

3. Finding and loading plugins must be as fast as the plugin allows, especially for command-line ("cli") commands. In other words, directly importing a plugin class should not be noticeably faster than using the plugin loader/factory;

4. Implement as a drop-in replacement, provide backwards compatibility at first, think about changing interfaces if/when the old system is dropped;

5. plugin management should be as user friendly from ipython as from the cli.

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

   Each category maps to an entry point group called::
   
      aiida.<category>

Interfaces
----------

Pluginloader (aiida/plugins/entry_point.py)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The plugin loader relies on the `reentry PyPI package <https://github.com/dropd/reentry>`_ to find and load entry points. ``reentry`` has been added to setup_requires for AiiDA in order to enable scanning for existing plugins when AiiDA is installed. If for some reason ``reentry`` is uninstalled or is not found, the plugin system will fall back on ``pkg_resources`` from setuptools, which is slower.

The API docs are found at the following link: :py:mod:`aiida.plugins.entry_point`.

Registry Tools (aiida/plugins)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

See the API documentation in :py:mod:`aiida.plugins`.
