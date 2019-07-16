The AiiDA Plugin System
=======================

Introduction
------------

The plugin system is the part of AiiDA that enables sharing workflows and distributing extensions to the core capabilities of AiiDA.

.. We want plugins to be installed as packages

Since both are written in python and shared as source code, we believe they should be distributed in the usual way for python code - python packages using `setuptools`_. This provides a well documented install process familiar to all python users. It simplifies the user experience for sharing workflows and extensions, especially since this allows AiiDA to be distributed and deployed in the same way. 

Goals
-----

The goals of the plugin system are the following

Sharing of workflows and extensions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A workflow or extension is written as a python package, distributed as a zip source archive, python ``egg`` or PyPI package. There is extensive documentation available for how to distribute python packages `here <https://packaging.python.org/>`_.

Ease of use
^^^^^^^^^^^

Plugins can be found in an online curated list of plugins and installed with one simple command. This process is familiar to every regular python user.

Decouple development and update cycles of AiiDA and plugins
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Since plugins are separate python packages, they can be developed in a separate code repository and updated when the developer sees fit without a need to update AiiDA. Similarly, if AiiDA is updated, plugins may not need to release a new version.

Promote modular design in AiiDA development
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Separating plugins into their own python packages ensures that plugins can not (easily) access parts of the AiiDA code which are not part of the public API, enabling AiiDA development to stay agile. The same applies to plugins relying on other plugins.

Low overhead for developers
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Plugin developers can write their extensions the same way they would write any python code meant for distribution.

Automatic AiiDA setup and testing of plugins
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Installation of complete python environments consisting of many packages can be automated, provided all packages use ``setuptools`` as a distribution tool. This enables use of AiiDA in a service-based way using, e.g., docker images. At the same it becomes possible to create automated tests for any combination of plugins, as long as the plugins provide test entry points.

Mechanism overview
------------------

.. We use Entry points

The new plugin system (introduced in AiiDA 0.9) takes advantage of the already well established entry points mechanism within `setuptools`_, documented in the section "`Extensible Applications and Frameworks`_" in the ``setuptools`` documentation. (Previously, plugins had to install python modules directly into specific source folders of AiiDA).

.. explain entry points: groups, names, object

Conceptually, an entry point consists of a group name, an entry point name and a path to the definition of a python object (any object, including modules, classes, functions, variables). A plugin host like AiiDA can iterate through entry points by group, find a specific one by name and load the associated python object. Iterating and finding entry points does not require any python code to be imported. A plugin is a separately-distributed, self-contained python package which implements any number of plugin classes and declares entry points accordingly.

Example
^^^^^^^

.. highlight:: python

In the following snippet only the most relevant code lines are picked to give an idea of the functioning. We will look only at one type of plugin, calculations, for simplicity.

First of all, AiiDA defines groups of of entry points in ``aiida-core/setup.py``::

    # in setuptools.setup() call
    entry_points = {
        'aiida.calculations' = [...],
        ...
    }

AiiDA then provides a callable ``CalculationFactory`` which does something equivalent to this::

   def CalculationFactory(plugin_name):
      from pkg_resources import iter_entry_points
      entry_points = iter_entry_points('aiida.calculations')
      plugin = [i for i in entry_points if i.name==plugin_name]
      if plugin and len(plugin) == 1:
         return plugin[0].load()
      elif len(plugin) > 1:
         # raise Error: Ambiguity
      else:
         # raise Error: Plugin not found

In ``aiida-myplugin/setup.py``::

    # in setuptools.setup() call
    entry_points = {
        'aiida.calculations' = [
            'myplugin.mycalc = aiida_myplugin.calculations.mycalc:MyPluginCalculation,
            ...
        ],
        ...
    }

In ``aiida-myplugin/aiida_myplugin/calculations/mycalc.py``::

    from aiida.orm import Calculation
    class MyPluginCalculation(Calculation):
        ...

In user code::

    from aiida.plugins import CalculationFactory
    Mycalc = CalculationFactory('myplugin.mycalc')
    ...


Note that the plugin developer can freely choose the code structure as well as the names of the modules and plugin classes. The developer is also free to refactor his code without fear of breaking compatibility, as long as no information stored in the database is changed (note that this unfortunately includes entry point name and class name).

Limitations
-----------

The chosen approach to plugins has some limitations:

* In the current version the interface for entry point objects is enforced implicitly by the way the object is used. It is the responsibility of the plugin developer to test for compliance, especially if the object is not derived from the recommended base classes provided by AiiDA. This is to be clearly communicated in the documentation for plugin developers;
* The freedom of the plugin developer to name and rename classes ends where the information in question is stored in the database as, e.g., node attributes.
* The system is designed with the possibility of plugin versioning in mind, however this is not implemented yet.
* In principle, two different plugins can give the same name to an entry point, creating ambiguity when trying to load the associated objects. Plugin development guidelines in the documentation will advise on how to avoid this problem, and this is addressed via the use of a centralized registry of known AiiDA plugins.
* Plugins can potentially contain malicious or otherwise dangerous code. In the registry of AiiDA plugins, we try to flag plugins that we know are safe to be used.

.. _setuptools: http://setuptools.readthedocs.io/en/latest/setuptools.html
.. _Extensible Applications and Frameworks: http://setuptools.readthedocs.io/en/latest/setuptools.html#extensible-applications-and-frameworks
.. _packaging-python: https://packaging.python.org/

