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

AiiDA Entry Points
-------------------

.. _aiida-diff: https://github.com/aiidateam/aiida-diff

This document contains a list of entry point groups AiiDA uses, with an example
usage for each.
In the following, we assume the following folder structure::

   aiida-mycode/           - distribution folder
      aiida_mycode/        - toplevel package (from aiida_myplug import ..)
         __init__.py
         calcs/
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


For a plugin package that uses this folder structure, see the  `aiida-diff`_ demo plugin.

Note, however, that the folder structure inside ``aiida-mycode/`` is entirely up to you.
A very simple plugin package might look like::

   aiida-mysimple/
      aiida_mysimple/
         __init__.py
         simpledata.py
      setup.py
      setup.json


The plugin package has to tell AiiDA where to look for the classes to be used as
calculations, parsers, transports, etc. This is done inside ``setup.json`` by way
of the ``entry_points`` keyword::

      ...
      entry_points={
         <Entry Point Group>: [
            <Entry Point Specification>,
            ...
         ],
      ...

It is given as a dictionary containing entry point group names as keywords. The list for each entry point group contains entry point specifications.

A specification in turn is given as a string and consists of two parts, a name and an import path describing where the class is to be imported from. The two parts are sparated by an `=` sign::

   "mycode.mydat = aiida_mycode.data.mydat:MyData"

We *strongly* suggest to start the name of each entry point with the name of the plugin package, ommitting the leading 'aiida-'.
In our example this leads to entry specifications like ``"mycode.<any.you.want> = <module.path:class>"``, just like the above example.
Exceptions to this rule can be tolerated if required for backwards compatibility.

Below, we list the entry point groups defined and searched by AiiDA.

.. _plugins.entry_point_list:

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

For scheduler plugins.
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
