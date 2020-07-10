.. _topics:plugins:

*******
Plugins
*******

.. _topics:plugins:may:

What a plugin can do
====================

* Add a new class to AiiDA's :ref:`entry point groups <topics:plugins:entrypointgroups>`, including:: calculations, parsers, workflows, data types, verdi commands, schedulers, transports and importers/exporters from external databases.
  This typically involves subclassing the respective base class AiiDA provides for that purpose.
* Install new commandline and/or GUI executables
* Depend on, and build on top of any number of other plugins (as long as their requirements do not clash)


.. _topics:plugins:maynot:

What a plugin should not do
===========================

An AiiDA plugin should not:

* Change the database schema AiiDA uses
* Use protected functions, methods or classes of AiiDA (those starting with an underscore ``_``)
* Monkey patch anything within the ``aiida`` namespace (or the namespace itself)

Failure to comply will likely prevent your plugin from being listed on the official `AiiDA plugin registry <registry>`_.

If you find yourself in a situation where you feel like you need to do any of the above, please open an issue on the `AiiDA repository <core>`_ and we can try to advise on how to proceed.


.. _core: https://github.com/aiidateam/aiida-core
.. _registry: https://github.com/aiidateam/aiida-registry

.. _topics:plugins:guidelines:

Guidelines for plugin design
============================

CalcJob & Parser plugins
------------------------

The following guidelines are useful to keep in mind when wrapping external codes:

 * | **Start simple.**
   | Make use of existing classes like :py:class:`~aiida.orm.nodes.data.dict.Dict`, :py:class:`~aiida.orm.nodes.data.singlefile.SinglefileData`, ...
     Write only what is necessary to pass information from and to AiiDA.
 * | **Don't break data provenance.**
   | Store *at least* what is needed for full reproducibility.
 * | **Expose the full functionality.**
   | Standardization is good but don't artificially limit the power of a code you are wrapping - or your users will get frustrated.
     If the code can do it, there should be *some* way to do it with your plugin.
 * | **Don't rely on AiiDA internals.**
     Functionality at deeper nesting levels is not considered part of the public API and may change between minor AiiDA releases, breaking your plugin.
 * | **Parse what you want to query for.**
   | Make a list of which information to:

     #. parse into the database for querying (:py:class:`~aiida.orm.nodes.data.dict.Dict`, ...)
     #. store in the file repository for safe-keeping (:py:class:`~aiida.orm.nodes.data.singlefile.SinglefileData`, ...)
     #. leave on the computer where the calculation ran (:py:class:`~aiida.orm.nodes.data.remote.RemoteData`, ...)


.. _topics:plugins:entrypoints:

What is an entry point?
=======================


The ``setuptools`` package (used by ``pip``) has a feature called `entry points`_, which allows to associate a string (the entry point *identifier*) with any python object defined inside a python package.
Entry points are defined in the ``setup.py`` file, for example::

      ...
      entry_points={
         "aiida.data": [
             # entry point = path.to.python.object
             "mycode.mydata = aiida_mycode.data.mydata:MyData",
         ]
      }
      ...

Here, we add a new entry point ``mycode.mydata`` to the entry point *group* ``aiida.data``.
The entry point identifier points to the ``MyData`` class inside the file ``mydata.py``, which is part of the ``aiida_mycode`` package.

When installing a python package that defines entry points, the entry point specifications are written to a file inside the distribution's ``.egg-info`` folder.
``setuptools`` provides a package ``pkg_resources`` for querying these entry point specifications by distribution, by entry point group and/or by name of the entry point and load the data structure to which it points.

Why entry points?
=================

AiiDA defines a set of entry point groups (see :ref:`topics:plugins:entrypointgroups` below).
By inspecting the entry points added to these groups by AiiDA plugins, AiiDA can offer uniform interfaces to interact with them.
For example:

 *  ``verdi plugin list aiida.workflows`` provides an overview of all workflows installed by AiiDA plugins.
    Users can inspect the inputs/outputs of each workflow using the same command without having to study the documentation of the plugin.
 *  The ``DataFactory``, ``CalculationFactory`` and ``WorkflowFactory`` methods allow instantiating new classes through a simple short string (e.g. ``quantumespresso.pw``).
    Users don't need to remember exactly where in the plugin package the class resides, and plugins can be refactored without users having to re-learn the plugin's API.


.. _topics:plugins:entrypointgroups:

AiiDA entry point groups
========================

Below, we list the entry point groups defined and searched by AiiDA.
You can get the same list as the output of ``verdi plugin list``.

``aiida.calculations``
----------------------

Entry points in this group are expected to be subclasses of :py:class:`aiida.orm.JobCalculation <aiida.orm.nodes.process.calculation.calcjob.CalcJobNode>`. This replaces the previous method of placing a python module with the class in question inside the ``aiida/orm/calculation/job`` subpackage.

Example entry point specification::

   entry_points={
      "aiida.calculations": [
         "mycode.mycode = aiida_mycode.calcs.mycode:MycodeCalculation"
      ]
   }

``aiida_mycode/calcs/mycode.py``::

   from aiida.orm import JobCalculation
   class MycodeCalculation(JobCalculation):
      ...

Will lead to usage::

   from aiida.plugins import CalculationFactory
   calc = CalculationFactory('mycode.mycode')

``aiida.parsers``
-----------------

AiiDA expects a subclass of ``Parser``. Replaces the previous approach consisting in placing a parser module under ``aiida/parsers/plugins``.

Example spec::

   entry_points={
      "aiida.calculations": [
         "mycode.mycode = aiida_mycode.parsers.mycode:MycodeParser"
      ]
   }

``aida_mycode/parsers/myparser.py``::

   from aiida.parsers import Parser
   class MycodeParser(Parser)
      ...

Usage::

   from aiida.plugins import ParserFactory
   parser = ParserFactory('mycode.mycode')

``aiida.data``
--------------

Group for :py:class:`~aiida.orm.nodes.data.data.Data` subclasses. Previously located in a subpackage of ``aiida/orm/data``.

Spec::

   entry_points={
      "aiida.data": [
         "mycode.mydata = aiida_mycode.data.mydat:MyData"
      ]
   }

``aiida_mycode/data/mydat.py``::

   from aiida.orm import Data
   class MyData(Data):
      ...

Usage::

   from aiida.plugins import DataFactory
   params = DataFactory('mycode.mydata')

``aiida.workflows``
-------------------

Package AiiDA workflows as follows:

Spec::

   entry_points={
      "aiida.workflows": [
         "mycode.mywf = aiida_mycode.workflows.mywf:MyWorkflow"
      ]
   }

``aiida_mycode/workflows/mywf.py``::

   from aiida.engine.workchain import WorkChain
   class MyWorkflow(WorkChain):
      ...

Usage::

   from aiida.plugins import WorkflowFactory
   wf = WorkflowFactory('mycode.mywf')

.. note:: For old-style workflows the entry point mechanism of the plugin system is not supported.
   Therefore one cannot load these workflows with the ``WorkflowFactory``.
   The only way to run these, is to store their source code in the ``aiida/workflows/user`` directory and use normal python imports to load the classes.


``aiida.cmdline``
-----------------

``verdi`` uses the `click_` framework, which makes it possible to add new subcommands to existing verdi commands, such as ``verdi data mydata``.
AiiDA expects each entry point to be either a ``click.Command`` or ``click.CommandGroup``.


Spec::

   entry_points={
      "aiida.cmdline.data": [
         "mydata = aiida_mycode.commands.mydata:mydata"
      ]
   }

``aiida_mycode/commands/mydata.py``::

   import click
   @click.group()
   mydata():
      """commandline help for mydata command"""

   @mydata.command('animate')
   @click.option('--format')
   @click.argument('pk')
   create_fancy_animation(format, pk):
      """help"""
      ...

Usage:

.. code-block:: bash

   verdi data mydata animate --format=Format PK

``aiida.tools.dbexporters``
---------------------------

If your plugin package adds support for exporting to an external database, use this entry point to have aiida find the module where you define the necessary functions.

.. Not sure how dbexporters work
.. .. Spec::
..
..    entry_points={
..       "aiida.tools.dbexporters": [
..          "mymatdb = aiida_mymatdb.mymatdb
..       ]
..    }

``aiida.tools.dbimporters``
---------------------------

If your plugin package adds support for importing from an external database, use this entry point to have aiida find the module where you define the necessary functions.

.. .. Spec::
..
..    entry_points={
..        "aiida.tools.dbimporters": [
..          "mymatdb = aiida_mymatdb.mymatdb
..        ]
..    }



``aiida.schedulers``
--------------------

We recommend naming the plugin package after the scheduler (e.g. ``aiida-myscheduler``), so that the entry point name can simply equal the name of the scheduler:

Spec::

   entry_points={
      "aiida.schedulers": [
         "myscheduler = aiida_myscheduler.myscheduler:MyScheduler"
      ]
   }

``aiida_myscheduler/myscheduler.py``::

   from aiida.schedulers import Scheduler
   class MyScheduler(Scheduler):
      ...

Usage: The scheduler is used in the familiar way by entering 'myscheduler' as the scheduler option when setting up a computer.

``aiida.transports``
--------------------

``aiida-core`` ships with two modes of transporting files and folders to remote computers: ``ssh`` and ``local`` (stub for when the remote computer is actually the same).
We recommend naming the plugin package after the mode of transport (e.g. ``aiida-mytransport``), so that the entry point name can simply equal the name of the transport:

Spec::

   entry_points={
      "aiida.transports": [
         "mytransport = aiida_mytransport.mytransport:MyTransport"
      ]
   }

``aiida_mytransport/mytransport.py``::

   from aiida.transports import Transport
   class MyTransport(Transport):
      ...

Usage::

   from aiida.plugins import TransportFactory
   transport = TransportFactory('mytransport')

When setting up a new computer, specify ``mytransport`` as the transport mode.



.. _topics:plugins:testfixtures:

Plugin test fixtures
====================

One concern when running tests for AiiDA plugins is to separate the test environment from your production environment.
Typically tests should be run against an empty AiiDA database.

AiiDA ships with tools that take care of this for you. They will:

 * start a temporary postgres server
 * create a new database
 * create a temporary ``.aiida`` folder
 * create a test profile
 * (optional) reset the AiiDA database before every individual test

thus letting you focus on testing the functionality of your plugin without having to worry about this separation.

.. note::
   The overhead for setting up the temporary environment is of the order of a few seconds and occurs only once per test session.
   You can control the database backend for the temporary profile by setting the ``AIIDA_TEST_BACKEND`` environment variable, e.g. ``export AIIDA_TEST_BACKEND=sqlalchemy``.


If you prefer to run tests on an existing profile, say ``test_profile``, simply set the following environment variable before running your tests::

  export AIIDA_TEST_PROFILE=test_profile


.. note::
   In order to prevent accidental data loss, AiiDA only allows to run tests on profiles whose name starts with ``test_``.

AiiDA ships with a number of fixtures in :py:mod:`aiida.manage.tests.pytest_fixtures` for you to use.

In particular:

  * The :py:func:`~aiida.manage.tests.pytest_fixtures.aiida_profile` fixture initializes the :py:class:`~aiida.manage.tests.TestManager` and yields it to the test function.
    Its parameters ``scope='session', autouse=True`` cause this fixture to automatically run once per test session, even if you don't explicitly require it.
  * The :py:func:`~aiida.manage.tests.pytest_fixtures.clear_database` fixture depends on the :py:func:`~aiida.manage.tests.pytest_fixtures.aiida_profile` fixture and tells the received :py:class:`~aiida.manage.tests.TestManager` instance to reset the database.
    This fixture lets each test start in a fresh AiiDA environment.
  * The :py:func:`~aiida.manage.tests.pytest_fixtures.temp_dir` fixture returns a temporary directory for file operations and deletes it after the test is finished.
  * ... you may want to add your own fixtures tailored for your plugins to set up specific ``Data`` nodes & more.

.. _pytest: https://pytest.org
.. _unittest: https://docs.python.org/library/unittest.html
.. _fixture: https://docs.pytest.org/en/latest/fixture.html
.. _click: https://click.palletsprojects.com/
.. _Entry points: https://setuptools.readthedocs.io/en/latest/setuptools.html#dynamic-discovery-of-services-and-plugins
