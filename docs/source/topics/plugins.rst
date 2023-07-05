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

Failure to comply will likely prevent your plugin from being listed on the official `AiiDA plugin registry <registry_>`_.

If you find yourself in a situation where you feel like you need to do any of the above, please open an issue on the `AiiDA repository <core_>`_ and we can try to advise on how to proceed.


.. _core: https://github.com/aiidateam/aiida-core
.. _registry: https://github.com/aiidateam/aiida-registry

.. _topics:plugins:guidelines:

Guidelines for plugin design
============================

CalcJob & Parser plugins
------------------------

The following guidelines are useful to keep in mind when wrapping external codes:

* **Start simple.**
  Make use of existing classes like :py:class:`~aiida.orm.nodes.data.dict.Dict`, :py:class:`~aiida.orm.nodes.data.singlefile.SinglefileData`, ...
  Write only what is necessary to pass information from and to AiiDA.
* **Don't break data provenance.**
  Store *at least* what is needed for full reproducibility.
* **Expose the full functionality.**
  Standardization is good but don't artificially limit the power of a code you are wrapping - or your users will get frustrated.
  If the code can do it, there should be *some* way to do it with your plugin.
* **Don't rely on AiiDA internals.**
  Functionality at deeper nesting levels is not considered part of the public API and may change between minor AiiDA releases, breaking your plugin.
* **Parse what you want to query for.**
  Make a list of which information to:

  #. parse into the database for querying (:py:class:`~aiida.orm.nodes.data.dict.Dict`, ...)
  #. store in the file repository for safe-keeping (:py:class:`~aiida.orm.nodes.data.singlefile.SinglefileData`, ...)
  #. leave on the computer where the calculation ran (:py:class:`~aiida.orm.RemoteData`, ...)


.. _topics:plugins:entrypoints:

What is an entry point?
=======================


The ``setuptools`` package (used by ``pip``) has a feature called `entry points`_, which allows to associate a string (the entry point *identifier*) with any python object defined inside a python package.
Entry points are defined in the ``pyproject.toml`` file, for example::

      ...
      [project.entry-points."aiida.data"]
      # entry point = path.to.python.object
      "mycode.mydata = aiida_mycode.data.mydata:MyData",
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

*   ``verdi plugin list aiida.workflows`` provides an overview of all workflows installed by AiiDA plugins.
    Users can inspect the inputs/outputs of each workflow using the same command without having to study the documentation of the plugin.
*   The ``DataFactory``, ``CalculationFactory`` and ``WorkflowFactory`` methods allow instantiating new classes through a simple short string (e.g. ``quantumespresso.pw``).
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

   [project.entry-points."aiida.calculations"]
   "mycode.mycode" = "aiida_mycode.calcs.mycode:MycodeCalculation"

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

   [project.entry-points."aiida.parsers"]
   "mycode.myparser" = "aiida_mycode.parsers.mycode:MycodeParser"

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

   [project.entry-points."aiida.data"]
   "mycode.mydata" = "aiida_mycode.data.mydata:MyData"

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

   [project.entry-points."aiida.workflows"]
   "mycode.mywf" = "aiida_mycode.workflows.mywf:MyWorkflow"

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
AiiDA expects each entry point to be either a ``click.Command`` or ``click.Group``. At present extra commands can be injected at the following levels:

* As a :ref:`direct subcommand of verdi data<spec-verdi-data>`
* As a :ref:`subcommand of verdi data core.structure import<spec-verdi-data-structure-import>`


.. _spec-verdi-data:

Spec for ``verdi data``::

   [project.entry-points."aiida.cmdline.data"]
   "mydata" = "aiida_mycode.commands.mydata:mydata"

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

.. _spec-verdi-data-structure-import:

Spec for ``verdi data core.structure import``::

   entry_points={
      "aiida.cmdline.data.structure.import": [
         "myformat = aiida_mycode.commands.myformat:myformat"
      ]
   }
   [project.entry-points."aiida.cmdline.data.structure.import"]
   "myformat" = "aiida_mycode.commands.myformat:myformat"

``aiida_mycode/commands/myformat.py``::

   import click
   @click.group()
   @click.argument('filename', type=click.File('r'))
   myformat(filename):
      """commandline help for myformat import command"""
      ...

Usage:

.. code-block:: bash

   verdi data core.structure import myformat a_file.myfmt


``aiida.tools.dbexporters``
---------------------------

If your plugin package adds support for exporting to an external database, use this entry point to have aiida find the module where you define the necessary functions.

.. Not sure how dbexporters work
.. .. Spec::

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

   [project.entry-points."aiida.schedulers"]
   "myscheduler" = "aiida_myscheduler.myscheduler:MyScheduler"

``aiida_myscheduler/myscheduler.py``::

   from aiida.schedulers import Scheduler
   class MyScheduler(Scheduler):
      ...

Usage: The scheduler is used in the familiar way by entering 'myscheduler' as the scheduler option when setting up a computer.

``aiida.transports``
--------------------

``aiida-core`` ships with two modes of transporting files and folders to remote computers: ``core.ssh`` and ``core.local`` (stub for when the remote computer is actually the same).
We recommend naming the plugin package after the mode of transport (e.g. ``aiida-mytransport``), so that the entry point name can simply equal the name of the transport:

Spec::

   [project.entry-points."aiida.transports"]
   "mytransport" = "aiida_mytransport.mytransport:MyTransport"

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

When developing AiiDA plugin packages, it is recommended to use `pytest <https://docs.pytest.org/>`__ as the unit test library, which is the de-facto standard in the Python ecosystem.
It provides a number of `fixtures <https://docs.pytest.org/en/7.1.x/how-to/fixtures.html>`__ that make it easy to setup and write tests.
``aiida-core`` also provides a number fixtures that are specific to AiiDA and make it easy to test various sorts of plugins.

To make use of these fixtures, create a ``conftest.py`` file in your ``tests`` folder and add the following code:

.. code-block:: python

   pytest_plugins = ['aiida.manage.tests.pytest_fixtures']

Just by adding this line, the fixtures that are provided by the :mod:`~aiida.manage.tests.pytest_fixtures` module are automatically imported.
The module provides the following fixtures:

* :ref:`aiida_manager <topics:plugins:testfixtures:aiida-manager>`: Return the global instance of the :class:`~aiida.manage.manager.Manager`
* :ref:`aiida_profile <topics:plugins:testfixtures:aiida-profile>`: Provide a loaded AiiDA test profile with loaded storage backend
* :ref:`aiida_profile_clean <topics:plugins:testfixtures:aiida-profile-clean>`: Same as ``aiida_profile`` but the storage backend is cleaned
* :ref:`aiida_profile_clean_class <topics:plugins:testfixtures:aiida-profile-clean-class>`: Same as ``aiida_profile_clean`` but should be used at the class scope
* :ref:`aiida_profile_factory <topics:plugins:testfixtures:aiida-profile-factory>`: Create a temporary profile ready to be used for testing
* :ref:`aiida_instance <topics:plugins:testfixtures:aiida-instance>`: Return the :class:`~aiida.manage.configuration.config.Config` instance that is used for the test session
* :ref:`config_psql_dos <topics:plugins:testfixtures:config-psql-dos>`: Return a profile configuration for the :class:`~aiida.storage.psql_dos.backend.PsqlDosBackend`
* :ref:`postgres_cluster <topics:plugins:testfixtures:postgres-cluster>`: Create a temporary and isolated PostgreSQL cluster using ``pgtest`` and cleanup after the yield
* :ref:`aiida_local_code_factory <topics:plugins:testfixtures:aiida-local-code-factory>`: Setup a :class:`~aiida.orm.nodes.data.code.installed.InstalledCode` instance on the ``localhost`` computer
* :ref:`aiida_computer <topics:plugins:testfixtures:aiida-computer>`: Setup a :class:`~aiida.orm.computers.Computer` instance
* :ref:`aiida_computer_local <topics:plugins:testfixtures:aiida-computer-local>`: Setup the localhost as a :class:`~aiida.orm.computers.Computer` using local transport
* :ref:`aiida_computer_ssh <topics:plugins:testfixtures:aiida-computer-ssh>`: Setup the localhost as a :class:`~aiida.orm.computers.Computer` using SSH transport
* :ref:`aiida_localhost <topics:plugins:testfixtures:aiida-localhost>`: Shortcut for <topics:plugins:testfixtures:aiida-computer-local> that immediately returns a :class:`~aiida.orm.computers.Computer` instance for the ``localhost`` computer instead of a factory
* :ref:`submit_and_await <topics:plugins:testfixtures:submit-and-await>`: Submit a process or process builder to the daemon and wait for it to reach a certain process state
* :ref:`started_daemon_client <topics:plugins:testfixtures:started-daemon-client>`: Same as ``daemon_client`` but the daemon is guaranteed to be running
* :ref:`stopped_daemon_client <topics:plugins:testfixtures:stopped-daemon-client>`: Same as ``daemon_client`` but the daemon is guaranteed to *not* be running
* :ref:`daemon_client <topics:plugins:testfixtures:daemon-client>`: Return a :class:`~aiida.engine.daemon.client.DaemonClient` instance to control the daemon
* :ref:`entry_points <topics:plugins:testfixtures:entry-points>`: Return a :class:`~aiida.manage.tests.pytest_fixtures.EntryPointManager` instance to add and remove entry points


.. _topics:plugins:testfixtures:aiida-manager:

``aiida_manager``
-----------------

Return the global instance of the :class:`~aiida.manage.manager.Manager`.
Can be used, for example, to retrieve the current :class:`~aiida.manage.configuration.config.Config` instance:

.. code-block:: python

   def test(aiida_manager):
      aiida_manager.get_config().get_option('logging.aiida_loglevel')


.. _topics:plugins:testfixtures:aiida-profile:

``aiida_profile``
-----------------

This fixture ensures that an AiiDA profile is loaded with an initialized storage backend, such that data can be stored.
The fixture is session-scoped and it has set ``autouse=True``, so it is automatically enabled for the test session.

By default, the fixture will generate a completely temporary independent AiiDA instance and test profile.
This includes:

* A temporary ``.aiida`` configuration folder with configuration files
* A temporary PostgreSQL cluster
* A temporary test profile complete with storage backend (creates a database in the temporary PostgreSQL cluster)

The temporary test instance and profile are automatically destroyed at the end of the test session.
The fixture guarantees that no changes are made to the actual instance of AiiDA with its configuration and profiles.

The creation of the temporary instance and profile takes a few seconds at the beginning of the test suite to setup.
It is possible to avoid this by creating a dedicated test profile once and telling the fixture to use that instead of generating one each time:

* Create a profile, by using `verdi setup` or `verdi quicksetup` and specify the ``--test-profile`` flag
* Set the ``AIIDA_TEST_PROFILE`` environment variable to the name of the test profile: ``export AIIDA_TEST_PROFILE=<test-profile-name>``

Although the fixture is automatically used, and so there is no need to explicitly pass it into a test function, it may
still be useful, as it can be used to clean the storage backend from all data:

.. code-block:: python

   def test(aiida_profile):
      from aiida.orm import Data, QueryBuilder

      Data().store()
      assert QueryBuilder().append(Data).count() != 0

      # The following call clears the storage backend, deleting all data, except for the default user.
      aiida_profile.clear_profile()

      assert QueryBuilder().append(Data).count() == 0


.. _topics:plugins:testfixtures:aiida-profile-clean:

``aiida_profile_clean``
-----------------------

Provides a loaded test profile through ``aiida_profile`` but empties the storage before calling the test function.
Note that a default user will be inserted into the database after cleaning it.

.. code-block:: python

   def test(aiida_profile_clean):
      """The profile storage is guaranteed to be emptied at the start of this test."""

This functionality can be useful if it is easier to setup and write the test if there is no pre-existing data.
However, cleaning the storage may take a non-negligible amount of time, so only use it when really needed in order to keep tests running as fast as possible.


.. _topics:plugins:testfixtures:aiida-profile-clean-class:

``aiida_profile_clean_class``
-----------------------------

Provides the same as ``aiida_profile_clean`` but with ``scope=class``.
Should be used for a test class:

.. code-block:: python

    @pytest.mark.usefixtures('aiida_profile_clean_class')
    class TestClass:

        def test():
            ...

The storage is cleaned once when the class is initialized.


.. _topics:plugins:testfixtures:aiida-profile-factory:

``aiida_profile_factory``
-------------------------

Create a temporary profile, add it to the config of the loaded AiiDA instance and load the profile.
Can be useful to create a test profile for a custom storage backend:

.. code-block:: python

    @pytest.fixture(scope='session')
    def custom_storage_profile(aiida_profile_factory) -> Profile:
        """Return a test profile for a custom :class:`~aiida.orm.implementation.storage_backend.StorageBackend`"""
        from some_module import CustomStorage
        configuration = {
            'storage': {
                'backend': 'plugin_package.custom_storage',
                'config': {
                    'username': 'joe'
                    'api_key': 'super-secret-key'
                }
            }
        }
        yield aiida_profile_factory(configuration)

Note that the configuration above is not actually functional and the actual configuration depends on the storage implementation that is used.


.. _topics:plugins:testfixtures:aiida-instance:

``aiida_instance``
------------------

Return the :class:`~aiida.manage.configuration.config.Config` instance that is used for the test session.

.. code-block:: python

    def test(aiida_instance):
        aiida_instance.get_option('logging.aiida_loglevel')


.. _topics:plugins:testfixtures:config-psql-dos:

``config_psql_dos``
-------------------

Return a profile configuration for the :class:`~aiida.storage.psql_dos.backend.PsqlDosBackend`.
This can be used in combination with the ``aiida_profile_factory`` fixture to create a test profile with customised database parameters:

.. code-block:: python

   @pytest.fixture(scope='session')
   def psql_dos_profile(aiida_profile_factory, config_psql_dos) -> Profile:
       """Return a test profile configured for the :class:`~aiida.storage.psql_dos.PsqlDosStorage`."""
       configuration = config_psql_dos()
       configuration['storage']['config']['repository_uri'] = '/some/custom/path'
       yield aiida_profile_factory(configuration)


Note that this is only useful if the storage configuration needs to be customized.
If any configuration works, simply use the ``aiida_profile`` fixture straight away, which uses the ``PsqlDosStorage`` storage backend by default.


.. _topics:plugins:testfixtures:postgres-cluster:

``postgres_cluster``
--------------------

Create a temporary and isolated PostgreSQL cluster using ``pgtest`` and cleanup after the yield.

.. code-block:: python

    @pytest.fixture()
    def custom_postgres_cluster(postgres_cluster):
        yield postgres_cluster(
            database_name='some-database-name',
            database_username='guest',
            database_password='guest',
        )


.. _topics:plugins:testfixtures:aiida-localhost:

``aiida_localhost``
-------------------

This test is useful if a test requires a :class:`~aiida.orm.computers.Computer` instance.
This fixture returns a :class:`~aiida.orm.computers.Computer` that represents the ``localhost``.

.. code-block:: python

    def test(aiida_localhost):
        aiida_localhost.get_minimum_job_poll_interval()


.. _topics:plugins:testfixtures:aiida-local-code-factory:

``aiida_local_code_factory``
----------------------------

This test is useful if a test requires an :class:`~aiida.orm.nodes.data.code.installed.InstalledCode` instance.
For example:

.. code-block:: python

    def test(aiida_local_code_factory):
        code = aiida_local_code_factory(
            entry_point='core.arithmetic.add',
            executable='/usr/bin/bash'
        )

By default, it will use the ``localhost`` computer returned by the ``aiida_localhost`` fixture.


.. _topics:plugins:testfixtures:aiida-computer:

``aiida_computer``
------------------

This fixture should be used to create and configure a :class:`~aiida.orm.computers.Computer` instance.
The fixture provides a factory that can be called without any arguments:

.. code-block:: python

    def test(aiida_computer):
        from aiida.orm import Computer
        computer = aiida_computer()
        assert isinstance(computer, Computer)

By default, the localhost is used for the hostname and a random label is generated.

.. code-block:: python

    def test(aiida_computer):
        custom_label = 'custom-label'
        computer = aiida_computer(label=custom_label)
        assert computer.label == custom_label

First the database is queried to see if a computer with the given label already exist.
If found, the existing computer is returned, otherwise a new instance is created.

The returned computer is also configured for the current default user.
The configuration can be customized through the ``configuration_kwargs`` dictionary:

.. code-block:: python

    def test(aiida_computer):
        configuration_kwargs = {'safe_interval': 0}
        computer = aiida_computer(configuration_kwargs=configuration_kwargs)
        assert computer.get_minimum_job_poll_interval() == 0


.. _topics:plugins:testfixtures:aiida-computer-local:

``aiida_computer_local``
----------------------------

This fixture is a shortcut for ``aiida_computer`` to setup the localhost with local transport:

.. code-block:: python

    def test(aiida_computer_local):
        localhost = aiida_computer_local()
        assert localhost.hostname == 'localhost'
        assert localhost.transport_type == 'core.local'

To leave a newly created computer unconfigured, pass ``configure=False``:

.. code-block:: python

    def test(aiida_computer_local):
        localhost = aiida_computer_local(configure=False)
        assert not localhost.is_configured

Note that if the computer already exists and was configured before, it won't be unconfigured.
If you need a guarantee that the computer is not configured, make sure to clean the database before the test or use a unique label:

.. code-block:: python

    def test(aiida_computer_local):
        import uuid
        localhost = aiida_computer_local(label=str(uuid.uuid4()), configure=False)
        assert not localhost.is_configured


.. _topics:plugins:testfixtures:aiida-computer-ssh:

``aiida_computer_ssh``
----------------------

This fixture is a shortcut for ``aiida_computer`` to setup the localhost with SSH transport:

.. code-block:: python

    def test(aiida_computer_ssh):
        localhost = aiida_computer_ssh()
        assert localhost.hostname == 'localhost'
        assert localhost.transport_type == 'core.ssh'

This can be useful if the functionality that needs to be tested involves testing the SSH transport, but these use-cases should be rare outside of `aiida-core`.
To leave a newly created computer unconfigured, pass ``configure=False``:

.. code-block:: python

    def test(aiida_computer_ssh):
        localhost = aiida_computer_ssh(configure=False)
        assert not localhost.is_configured

Note that if the computer already exists and was configured before, it won't be unconfigured.
If you need a guarantee that the computer is not configured, make sure to clean the database before the test or use a unique label:

.. code-block:: python

    def test(aiida_computer_ssh):
        import uuid
        localhost = aiida_computer_ssh(label=str(uuid.uuid4()), configure=False)
        assert not localhost.is_configured


.. _topics:plugins:testfixtures:submit-and-await:

``submit_and_await``
--------------------

This fixture is useful when testing submitting a process to the daemon.
It submits the process to the daemon and will wait until it has reached a certain state.
By default it will wait for the process to reach ``ProcessState.FINISHED``:

.. code-block:: python

    def test(aiida_local_code_factory, submit_and_await):
        code = aiida_local_code_factory('core.arithmetic.add', '/usr/bin/bash')
        builder = code.get_builder()
        builder.x = orm.Int(1)
        builder.y = orm.Int(1)
        node = submit_and_await(builder)
        assert node.is_finished_ok

Note that the fixture automatically depends on the ``started_daemon_client`` fixture to guarantee the daemon is running.


.. _topics:plugins:testfixtures:started-daemon-client:

``started_daemon_client``
-------------------------

This fixture ensures that the daemon for the test profile is running and returns an instance of the :class:`~aiida.engine.daemon.client.DaemonClient` which can be used to control the daemon.

.. code-block:: python

    def test(started_daemon_client):
        assert started_daemon_client.is_daemon_running


.. _topics:plugins:testfixtures:stopped-daemon-client:

``stopped_daemon_client``
-------------------------

This fixture ensures that the daemon for the test profile is stopped and returns an instance of the :class:`~aiida.engine.daemon.client.DaemonClient` which can be used to control the daemon.

.. code-block:: python

    def test(stopped_daemon_client):
        assert not stopped_daemon_client.is_daemon_running


.. _topics:plugins:testfixtures:daemon-client:

``daemon_client``
-----------------

Return a :class:`~aiida.engine.daemon.client.DaemonClient` instance that can be used to control the daemon:

.. code-block:: python

    def test(daemon_client):
        daemon_client.start_daemon()
        assert daemon_client.is_daemon_running
        daemon_client.stop_daemon(wait=True)

The fixture is session scoped.
At the end of the test session, this fixture automatically shuts down the daemon if it is still running.


.. _topics:plugins:testfixtures:entry-points:

``entry_points``
----------------

Return a :class:`~aiida.manage.tests.pytest_fixtures.EntryPointManager` instance to add and remove entry points.

.. code-block:: python

    def test_parser(entry_points):
        """Test a custom ``Parser`` implementation."""
        from aiida.parsers import Parser
        from aiida.plugins import ParserFactory

        class CustomParser(Parser):
            """Parser implementation."""

        entry_points.add(CustomParser, 'custom.parser')

        assert ParserFactory('custom.parser', CustomParser)

Any entry points additions and removals are automatically undone at the end of the test.


.. _click: https://click.palletsprojects.com/
.. _Entry points: https://packaging.python.org/en/latest/guides/creating-and-discovering-plugins/
