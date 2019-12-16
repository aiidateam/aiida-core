.. _plugin_development:

Basics
======


What a plugin Is
----------------

An AiiDA plugin is a `python package <packages>`_ that provides a set of extensions to AiiDA.

AiiDA plugins can use :ref:`entry points <plugins.entry_points>` in order to make the ``aiida-core`` package aware of the extensions.

.. note::

  In the python community, the term 'package' is used rather loosely.
  Depending on context, it can refer to a collection of python modules or it may, in addition, include the files necessary for building and installing the package.

.. _packages: https://docs.python.org/2/tutorial/modules.html?highlight=package#packages


Goals
-----

The plugin system was designed with the following goals in mind.

* **Sharing of workflows and extensions**: a workflow or extension is written as a python package, distributed as a zip source archive, python ``egg`` or PyPI package. There is extensive documentation available for how to distribute python packages `here <https://packaging.python.org/>`_.

* **Ease of use**: plugins can be found in an online curated list of plugins and installed with one simple command. This process is familiar to every regular python user.

* **Decouple development and update cycles of AiiDA and plugins**: since plugins are separate python packages, they can be developed in a separate code repository and updated when the developer sees fit without a need to update AiiDA. Similarly, if AiiDA is updated, plugins may not need to release a new version.

* **Promote modular design in AiiDA development**: separating plugins into their own python packages ensures that plugins can not (easily) access parts of the AiiDA code which are not part of the public API, enabling AiiDA development to stay agile. The same applies to plugins relying on other plugins.

* **Low overhead for developers**: plugin developers can write their extensions the same way they would write any python code meant for distribution.

* **Automatic AiiDA setup and testing of plugins**: installation of complete python environments consisting of many packages can be automated, provided all packages use ``setuptools`` as a distribution tool. This enables use of AiiDA in a service-based way using, e.g., docker images. At the same it becomes possible to create automated tests for any combination of plugins, as long as the plugins provide test entry points.


Design guidelines
------------------

* **Start simple.**: make use of existing classes like :py:class:`~aiida.orm.nodes.process.calculation.calcjob.CalcJobNode`, :py:class:`~aiida.orm.nodes.data.dict.Dict`, :py:class:`~aiida.orm.nodes.data.singlefile.SinglefileData`, ... Write only what is necessary to pass information from and to AiiDA.

* **Don't break data provenance.**: store *at least* what is needed for full reproducibility.

* **Parse what you want to query for.**: make a list of which information to:

  #. parse into the database for querying (:py:class:`~aiida.orm.nodes.data.dict.Dict`, ...)
  #. store in files for safe-keeping (:py:class:`~aiida.orm.nodes.data.singlefile.SinglefileData`, ...)
  #. leave on the remote computer (:py:class:`~aiida.orm.nodes.data.remote.RemoteData`, ...)

* **Expose the full functionality.**: standardization is good but don't artificially limit the power of a code you are wrapping - or your users will get frustrated. If the code can do it, there should be *some* way to do it with your plugin.


What a plugin can do
--------------------

* Add new classes to AiiDA's unified interface, including:

  - calculations
  - parsers
  - data types
  - schedulers
  - transports
  - db importers
  - db exporters
  - subcommands to some ``verdi`` commands

  This typically involves subclassing the respective base class AiiDA provides for that purpose.
* Install separate commandline and/or GUI executables
* Depend on any number of other plugins (the required versions must not clash with AiiDA's requirements)


.. _plugins.maynot:

What a plugin should not do
---------------------------

An AiiDA plugin should not:

* Change the database schema AiiDA uses
* Use protected functions, methods or classes of AiiDA (those starting with an underscore ``_``)
* Monkey patch anything within the ``aiida`` namespace (or the namespace itself)

Failure to comply will likely prevent your plugin from being listed on the official `AiiDA plugin registry <registry>`_.

If you find yourself tempted to do any of the above, please open an issue on the `AiiDA repository <core>`_ and explain why.
We will advise on how to proceed.


.. _core: https://github.com/aiidateam/aiida-core
.. _registry: https://github.com/aiidateam/aiida-registry


Limitations
-----------

The chosen approach to plugins has some limitations:

* In the current version the interface for entry point objects is enforced implicitly by the way the object is used. It is the responsibility of the plugin developer to test for compliance, especially if the object is not derived from the recommended base classes provided by AiiDA. This is to be clearly communicated in the documentation for plugin developers;
* The freedom of the plugin developer to name and rename classes ends where the information in question is stored in the database as, e.g., node attributes.
* The system is designed with the possibility of plugin versioning in mind, however this is not implemented yet.
* In principle, two different plugins can give the same name to an entry point, creating ambiguity when trying to load the associated objects. Plugin development guidelines in the documentation will advise on how to avoid this problem, and this is addressed via the use of a centralized registry of known AiiDA plugins.
* Plugins can potentially contain malicious or otherwise dangerous code. In the registry of AiiDA plugins, we try to flag plugins that we know are safe to be used.
