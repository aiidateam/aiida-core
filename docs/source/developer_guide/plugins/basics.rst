.. _plugin_development:

Basics
======


Nomenclature
------------

An AiiDA plugin is an extension of AiiDA, announcing itself to ``aiida-core`` by means of a new :ref:`entry point <plugins.entry_points>`.

AiiDA plugins can be bundled and distributed in a `python package <packages>`_ that provides a set of extensions to AiiDA.

.. note::

  The python community uses the term 'package' rather loosely.
  Depending on context, it can refer to a collection of python modules or it may, in addition, include the files necessary for building and installing the package.

.. _packages: https://docs.python.org/2/tutorial/modules.html?highlight=package#packages


What a plugin can do
--------------------

* Add a new class to AiiDA's :ref:`entry point groups <plugins.aiida_entry_points>`, including:: calculations, parsers, workflows, data types, verdi commands, schedulers, transports and importers/exporters from external databases.
  This typically involves subclassing the respective base class AiiDA provides for that purpose.
* Install new commandline and/or GUI executables
* Depend on, and build on top of any number of other plugins (as long as their requirements do not clash)


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


Design guidelines
------------------

Wrapping an external code
.........................

In order to wrap an external simulation code for use in AiiDA, you will need to write a calculation input plugin (subclassing the :py:class:`~aiida.engine.CalcJob` class) and an output parser plugin (subclassing the :py:class:`~aiida.parsers.Parser` class):

 * | **Start simple.**
   | Make use of existing classes like :py:class:`~aiida.orm.nodes.data.dict.Dict`, :py:class:`~aiida.orm.nodes.data.singlefile.SinglefileData`, ...
   | Write only what is necessary to pass information from and to AiiDA.
 * | **Don't break data provenance.**
   | Store *at least* what is needed for full reproducibility.
 * | **Parse what you want to query for.**
   | Make a list of which information to:

     #. parse into the database for querying (:py:class:`~aiida.orm.nodes.data.dict.Dict`, ...)
     #. store in files for safe-keeping (:py:class:`~aiida.orm.nodes.data.singlefile.SinglefileData`, ...)
     #. leave on the remote computer (:py:class:`~aiida.orm.nodes.data.remote.RemoteData`, ...)

 * | **Expose the full functionality.**
   | Standardization is good but don't artificially limit the power of a code you are wrapping - or your users will get frustrated.
   | If the code can do it, there should be *some* way to do it with your plugin.

 * | **Don't rely on AiiDA internals.**
   | AiiDA's :ref:`public python API<python_api_public_list>` includes anything that you can import via  ``from aiida.module import thing``.
   | Functionality at deeper nesting levels is not considered part of the public API and may change between minor AiiDA releases, forcing you to update your plugin.

Folder structure
................

While it is up to you to decide the folder structure for your plugin, here is how a typical AiiDA plugin package may look like (see also the `aiida-diff`_ demo plugin)::

   aiida-mycode/           - distribution folder
      aiida_mycode/        - toplevel package (from aiida_mycode import ..)
         __init__.py
         calculations/
            __init__.py
            mycode.py      - contains MycodeCalculation
         parsers/
            __init__.py
            mycode.py      - contains MycodeParser
         data/
            __init__.py
            mydat.py       - contains MyData (supports code specific format)
         commands/
            __init__.py
            mydat.py       - contains visualization subcommand for MyData
         workflows/
            __init__.py
            mywf.py        - contains a basic workflow using mycode
         ...
      setup.py             - install script
      setup.json           - install configuration
      ...

A minimal plugin package instead might look like::

   aiida-minimal/
      aiida_minimal/
         __init__.py
         simpledata.py
      setup.py
      setup.json


.. _aiida-diff: https://github.com/aiidateam/aiida-diff
