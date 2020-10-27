.. _internal_architecture:plugin_system:

*************
Plugin system
*************

.. note:: This page explains how to contribute to the plugin system in ``aiida-core``.
   For instrucions on how to develop plugins, see :ref:`how-to:plugins-develop`.

Design Principles
=================

1. Only restrict plugin developers when really necessary;

2. Avoid database schema changes whenever reasonably possible;

3. Finding and loading plugins must be as fast as the plugin allows, especially for command line interface (CLI) commands.
   In other words, directly importing a plugin class should not be noticeably faster than using the plugin loader/factory;

4. Implement as a drop-in replacement, provide backwards compatibility to pre-0.9 plugin system;

5. Plugin management should be as user friendly from the verdi shell as from the CLI.

Mini-Spec
=========

Nomenclature
------------
``plugin_name``
   A unique name identifying the plugin. Suggested naming scheme is

   * ``aiida-<plugin-name>`` for pypi distribution / source code repository
   * ``aiida_<plugin_name>`` for python package (``import aiida_<plugin_name>``; dashes replaced by underscores)
   * ``<plugin_name>.ep_name`` for entry points


``category``
   A name given to each aspect of AiiDA that can be extended via plugins, such as ``calculations``, ``schedulers``, ...
   (see output of ``verdi plugin list`` for a complete list).

   Each category maps to an *entry point group* ``aiida.<category>``.

Interfaces
----------

Pluginloader
^^^^^^^^^^^^
The plugin loading functionality is defined in :py:mod:`aiida.plugins.entry_point` and relies on the `reentry package <https://pypi.org/project/reentry/>`_ to find and load entry points.
``reentry`` is about 10x faster than the equivalent functionality in ``pkg_resources`` from ``setuptools``, leading to significant speedup of tab-autocompletion in the ``verdi`` cli.
If, for some reason, ``reentry`` is not found, the plugin system falls back on ``pkg_resources``.

Registry Tools
^^^^^^^^^^^^^^
See the API documentation in :py:mod:`aiida.plugins`.
