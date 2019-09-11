Developing the plugin system
============================

.. note:: this page is intended for people wanting to contribute to the plugin system in ``aiida-core`` and is not needed for people who just want to contribute a plugin.

Design Principles
+++++++++++++++++

1. Only restrict plugin developers when really necessary;

2. Avoid schema changes whenever reasonably possible;

3. Finding and loading plugins must be as fast as the plugin allows, especially for command line interface (CLI) commands. In other words, directly importing a plugin class should not be noticeably faster than using the plugin loader/factory;

4. Implement as a drop-in replacement, provide backwards compatibility at first, think about changing interfaces if/when the old system is dropped;

5. Plugin management should be as user friendly from ipython as from the CLI.

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
   * cmdline.computer.configure
   * cmdline.data
   * data
   * parsers
   * schedulers
   * transports
   * tools.calculations
   * tools.data.orbitals
   * tools.dbexporters
   * tools.dbimporters
   * workflows

   Each category maps to an entry point group called::

      aiida.<category>

Interfaces
----------

Pluginloader
^^^^^^^^^^^^
The plugin loading functionality is defined in :py:mod:`aiida.plugins.entry_point` and relies on the `reentry PyPI package <https://github.com/dropd/reentry>`_ to find and load entry points.
The ``reentry`` package is part of the build requirements of ``aiida-core`` as defined in the ``pyproject.toml`` file.
This enables the scanning for existing plugins when AiiDA is installed.
If for some reason ``reentry`` is uninstalled or is not found, the plugin system will fall back on ``pkg_resources`` from setuptools, which is slower.

Registry Tools
^^^^^^^^^^^^^^
See the API documentation in :py:mod:`aiida.plugins`.
