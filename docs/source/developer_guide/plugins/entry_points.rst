.. note:: intended for aiida >= 0.9

   This information applies to `github.com/DropD/aiida_core/tree/ricoh-plugins`

.. _plugins.entry_points:

AiiDA Entry Points
==================

This document contains a list of entry point groups AiiDA uses, with an example usage for each. For the examples we assume the following plugin structure for a plugin that supports a code (example: 'mycode'):

.. code-block:: bash

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
      setup.py             - install configuration
      ...

Note that the structure inside ``aiida_mycode/`` is freely choosable. A very simple plugin might look like::

   aiida-mysimple/
      aiida_mysimple/
         __init__.py
         simpledata.py
      setup.py

The plugin has to tell AiiDA where to look for the classes to be used as calculations, parsers, transports, etc. This is done inside ``setup.py`` by way of the ``entry_points`` keyword argument to ``setup()``::

   setup(
      ...
      entry_points={
         <Entry Point Group>: [
            <Entry Point Specification>,
            ...
         ],
         ...
      },
      ...

It is given as a dictionary containing entry point group names as keywords. The list for each entry point group contains entry point specifications.

A specification in turn is given as a string and consists of two parts, a name and an import path describing where the class is to be imported from. The two parts are sparated by an `=` sign::
   
   "mycode.mydat = aiida_mycode.data.mydat:MyData"

We *strongly* suggest to start the name of each entry point with the name of the plugin, ommitting the leading 'aiida-'. In our example this leads to entry specifications like ``"mycode.<any.you.want> = <module.path:class>"``, just like the above example.
Exceptions to this rule are schedulers, transports and potentially data ones. Further exceptions can be tolerated in order to provide backwards compatibility if the plugin was in use before aiida-0.9 and it's modules were installed in locations which make adhering to this rule impossible.

``aiida.calculations``
----------------------

Entry points in this group are expected to be subclasses of :py:class:`aiida.orm.JobCalculation <aiida.orm.implementation.general.calculation.job.AbstractJobCalculation>`. This replaces the previous method of placing a python module with the class in question inside the ``aiida/orm/calculation/job`` subpackage.

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

   from aiida.orm import CalculationFactory
   calc = CalculationFactory('mycode.mycode')

``aiida.parsers``
-----------------

Aiida expects a subclass of ``Parser``. Replaces placing a parser module under ``aiida/parsers/plugins``

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
   
   from aiida.parsers import ParserFactory
   parser = ParserFactory('mycode.mycode')

``aiida.data``
--------------

Group for :py:class:`~aiida.orm.data.Data` subclasses. Previously located in a subpackage of ``aiida/orm/data``.

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

   from aiida.orm import DataFactory
   params = DataFactory('mycode.mydata')

``aiida.workflows``
-------------------

For AiiDA workflows. Instead of putting a workflow somewhere under the ``aiida.workflows`` package, it can now be packaged as a plugin and exposed to aiida as follows:

Spec::

   entry_points={
      "aiida.workflows": [
         "mycode.mywf = aiida_mycode.workflows.mywf:MyWorkflow"
      ]
   }

``aiida_mycode/workflows/mywf.py``::
   
   from aiida.work.workchain import WorkChain
   class MyWorkflow(WorkChain):
      ...
   
Usage::

   from aiida.orm import WorkflowFactory
   wf = WorkflowFactory('mycode.mywf')

``aiida.cmdline``
-----------------

For subcommands to verdi commands like ``verdi data mydata``. This was previously not possible to achieve without editing aiida source code directly. AiiDA expects each entry point to be either a ``click.Command`` or ``click.CommandGroup``.

Plugin support for commands is possible due to using `click`_.

.. note:: Prior to aiida-0.9, the subcommand in question will require `aiida-verdi`_ to be installed.The command will then be called ``verdi-plug data mydata`` instead.

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

   $ verdi data mydata animate --format=Format PK

``aiida.tools.dbexporters``
---------------------------

If your plugin adds support for exporting to an external database, use this entry point to have aiida find the module where you define the necessary functions.

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

If your plugin adds support for importing from an external database, use this entry point to have aiida find the module where you define the necessary functions.

.. .. Spec::
.. 
..    entry_points={
..        "aiida.tools.dbimporters": [
..          "mymatdb = aiida_mymatdb.mymatdb
..        ]
..    }

``aiida.tools.dbexporters.tcod_plugins``
----------------------------------------

If you want to support exporting your plugin classes to tcod, use this entry point for your :py:class:`~aiida.tools.dbexporters.tcod_plugins.BaseTcodtranslator` subclass.

Spec::

   entry_points={
       "aiida.tools.dbexporters.tcod_plugins": [
           "myplugin.mycalc = aiida_myplugin.tcod_plugins.mycalc:MycalcTcodtranslator"
       ]
   }

<{}>


``aiida.schedulers``
--------------------

For scheduler plugins. Note that the entry point name is not prefixed by the plugin name. This is because typically a scheduler should be distributed in a plugin of it's own, and only one plugin per scheduler should be necessary.

Spec::

   entry_points={
      "aiida.schedulers": [
         "myscheduler = aiida_myscheduler.myscheduler:MyScheduler"
      ]
   }

``aiida_myscheduler/myscheduler.py``::

   from aiida.scheduler import Scheduler
   class MyScheduler(Scheduler):
      ...

Usage: The scheduler is used in the familiar way by entering 'myscheduler' as the scheduler option when setting up a computer.

``aiida.transports``
--------------------

Much like for schedulers, transports are supposed to be distributed in their separate plugin. Therefore we will again omit the plugin's name in the entry point name.

Spec::

   entry_points={
      "aiida.transports": [
         "mytransport = aiida_mytransport.mytransport:MyTransport"
      ]
   }

``aiida_mytransport/mytransport.py``::

   from aiida.transport import Transport
   class MyTransport(Transport):
      ...

Usage::

   from aiida.transport import TransportFactory
   transport = TransportFactory('mytransport')

Jus like one would expect, when a computer is setup, 'mytransport' can be given as the transport option.

.. _click: https://click.pocoo.org/6/
.. _aiida-verdi: https://github.com/DropD/aiida-verdi
