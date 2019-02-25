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

This is the way AiiDA finds and loads classes provided by plugins.

.. _Entry points: https://setuptools.readthedocs.io/en/latest/setuptools.html#dynamic-discovery-of-services-and-plugins

AiiDA Entry Points
-------------------

.. _aiida plugin template: https://github.com/aiidateam/aiida-plugin-template 

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


For a plugin that uses this folder structure, see the  `aiida plugin template`_.

Note, however, that the folder structure inside ``aiida-mycode/`` is entirely up to you.
A very simple plugin might look like::

   aiida-mysimple/
      aiida_mysimple/
         __init__.py
         simpledata.py
      setup.py
      setup.json


The plugin has to tell AiiDA where to look for the classes to be used as
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

We *strongly* suggest to start the name of each entry point with the name of
the plugin, ommitting the leading 'aiida-'. 
In our example this leads to entry specifications like ``"mycode.<any.you.want> = <module.path:class>"``, just like the above example.
Exceptions to this rule are schedulers, transports and potentially data ones. Further exceptions can be tolerated in order to provide backwards compatibility if the plugin was in use before aiida-0.9 and its modules were installed in locations which does not make it possible to follow this rule.

Below, a list of valid entry points recognized by AiiDA follows.

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

For AiiDA workflows. Instead of putting a workflow somewhere under the ``aiida.workflows`` package, it can now be packaged as a plugin and exposed to aiida as follows:

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

For subcommands to verdi commands like ``verdi data mydata``. This was previously not possible to achieve without editing aiida source code directly. AiiDA expects each entry point to be either a ``click.Command`` or ``click.CommandGroup``.

Plugin support for commands is possible due to using `click`_.

.. note:: In aiida-0.9, the subcommand in question is not yet exposed to ``verdi``. There is a `aiida-verdi`_ package that is being developed to implement such functionality (experimental yet). The command will then be called ``verdi-exp data mydata`` instead.

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



``aiida.schedulers``
--------------------

For scheduler plugins. Note that the entry point name is not prefixed by the plugin name. This is because typically a scheduler should be distributed in a plugin on its own, and only one plugin per scheduler should be necessary.

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

Like schedulers, transports are supposed to be distributed in a separate plugin. Therefore we will again omit the plugin's name in the entry point name.

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

Jus like one would expect, when a computer is setup, ``mytransport`` can be given as the transport option.

.. _click: https://click.pocoo.org/6/
.. _aiida-verdi: https://github.com/DropD/aiida-verdi
