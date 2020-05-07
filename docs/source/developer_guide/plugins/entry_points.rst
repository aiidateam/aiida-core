.. _plugins.entry_points:

Entry Points
=============


What is an Entry Point?
-----------------------

The ``setuptools`` package to which ``pip`` is a frontend has a feature called
`entry points`_.
When a distribution which registers entry points is installed,
the entry point specifications are written to a file inside the distribution's
``.egg-info`` folder. ``setuptools`` provides a package ``pkg_resources`` which
can find these entry points by distribution, group and/or name and load the
data structure to which it points.

This is the way AiiDA finds plugins and and loads the functionality they provide.

.. _Entry points: https://setuptools.readthedocs.io/en/latest/setuptools.html#dynamic-discovery-of-services-and-plugins

.. _plugins.aiida_entry_points:

AiiDA Entry Points
-------------------

AiiDA defines a set of entry point groups that it will search for new functionality provided by plugins.
You can list those groups and their contents via::

    verdi plugin list  # list all groups
    verdi plugin list aiida.calculations  # show contents of one group

Plugin packages can add new entry points through the ``entry_points`` field in the ``setup.json`` file::

      ...
      entry_points={
         <Entry Point Group>: [
            <Entry Point Specification>,
            ...
         ],
      ...

Here, ``<Entry Point Group>`` can be any of the groups shown in the output of ``verdi plugin list``, and the ``<Entry Point Specification>`` contains the entry point name and the path to the Python object it points to::

   "mycode.mydat = aiida_mycode.data.mydat:MyData"

We *strongly* suggest to start the name of each entry point with the name of the plugin package (omitting the 'aiida-' prefix).
For a package ``aiida-mycode``, this leads to specifications like ``"mycode.<something> = <module.path:class>"``.
Exceptions to this rule can be tolerated if required for backwards compatibility.

Below, we list the entry point groups defined and searched by AiiDA.


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

Aiida expects a subclass of ``Parser``. Replaces the previous approach consisting in placing a parser module under ``aiida/parsers/plugins``.

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

.. _click: https://click.pocoo.org/6/
.. _aiida-verdi: https://github.com/DropD/aiida-verdi
