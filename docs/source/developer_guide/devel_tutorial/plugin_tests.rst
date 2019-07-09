.. _plugin.testing:

Writing tests for plugin
========================

When developing a plugin it is important to write tests. The main concern of running
tests is that the test environment has to be separated from the production environment
and care should be taken to avoid any unwanted change to the user's database.
You may have noticed that ``aiida-core`` has its own test framework for developments.
While it is possible to use the same framework for the plugins,
it is not ideal as any tests of plugins has to be run with
the ``verdi devel tests`` command-line interface.
Special profiles also have to be set mannually by the user and in automated test environments.

AiiDA ships with tools to simplify tests for plugins.
The recommended way is to use the `pytest`_ framework, while the `unittest`_ package is also supported.
Internally, test environments are created and managed by the :py:func:`aiida.manage.fixtures.fixture_manager` defined in :py:mod:`aiida.manage.fixtures`.

.. _pytest: https://pytest.org
.. _unittest: https://docs.python.org/library/unittest.html
.. _fixture: https://docs.pytest.org/en/latest/fixture.html

Using the pytest framework
--------------------------

In this section we will introduce using the ``pytest`` framework to write tests for
plugins.

Preparing the fixtures
^^^^^^^^^^^^^^^^^^^^^^

One important concept of the pytest framework is the `fixture`_.
A fixture is something that a test requires. It could be a predefined object that the
test act on, resources for the tests, or just some code you want to run before the
test starts. Please see pytest's `documentation <https://docs.pytest.org/en/latest/>`_ for details, especially if you are new to writing testes.


To utilize the ``fixture_manager``, we first need to define the actual fixtures:

.. literalinclude:: conftest.py

  
The ``aiida_profile`` fixture initialize the ``fixture_manager`` yields it to the test function.
By using the *with* clause, we ensure that the test profile to run tests are destroyed in the end.
The scope of this fixture should be *session*, since there is no need to re-initialize the
test profile mid-way.
The next fixture ``new_database`` request the ``aiida_profile`` fixture and tells the received ``FixtureManager`` instance to reset the database.
By requesting the ``new_database`` fixture, the test function will start with a fresh aiida environment.
The next fixture, ``new_workdir``, returns an temporary directory for file operations and delete it when the test is finished.
You may also want to define other fixtures such as those setup and return ``Data`` nodes or prepare calculations.

To make these fixtures available to all tests, they can be put into the ``conftest.py``
in root level of the package or ``tests`` sub-packages. The code shown above can be downloaded :download:`here <conftest.py>`.

.. seealso::
  More information of ``conftest.py`` can be found `here <conftest>`_.

.. _conftest: https://docs.pytest.org/en/stable/fixture.html?highlight=conftest#conftest-py-sharing-fixture-functions

Import statements in tests
^^^^^^^^^^^^^^^^^^^^^^^^^^

When running test, it is important that you DO NOT explicitly load the aiida database
via ``load_dbenv()``, which could result in corruption of your database with actual data.
However, many AiiDA modules, such as those in ``aiida.orm`` cannot be loaded without calling ``load_dbenv()`` first.
Modules in your plugin may also import such aiida modules at the top level.
Hence, they can not be imported directly in test modules.
To solve this issue, import should be delayed until the test profile has been loaded.
You can always import these required modules inside the test function.
A better way is to define a fixture as a loader for module imports.
For example, instead of having::

  import aiida.orm as orm

at the module level, you can define a fixture::

  @pytest.fixture(scope='module')
  def orm(aiida_profile):
      import aiida.orm as orm
      return orm

and simply request this fixture for your test function::

  def test_load_dataclass(orm):
      """Test loading a data class defined by the plugin"""
      from aiida.plugins import DataFactory
      MyData = DataFactory('myplugin.maydata')

We set ``'scope='module'`` to declare that this is module scope fixture and
avoids repetitively doing the import for each test.
It is also possible to group many imports in a single fixture::

  @pytest.fixture(scope='module')
  def imps(aiida_profile):
      """Return an class with all imports as its attributes"""
      class Imports(object):
          import aiida.orm as orm

      return Imports


  def test_load_dataclass(imps):
      """Test loading a data class defined by the plugin"""
      MyData = imps.orm.DataFactory('my_plugin.maydata')

Requesting the ``aiida_profile`` fixture in the ``imps`` fixture guarantees
that the test environment will be loaded before the any import statement are executed.


Running the tests
^^^^^^^^^^^^^^^^^
Finally, to run the tests, simply type::

  pytest

in your terminal from the code directory.
The discovery of the tests will be handled by pytest (file, class and function name should start with the word **test**)

.. note::
   Your terminal will print something out during the creation of a test profile.
   Do not panic, as and the aiida profile and database are completely isolated and
   will not affect your ``.aiida`` folder and file repositories.
   Internally, at temporary folder is used as the ``.aiida`` folder and the test
   database are created using the `pgtest <https://github.com/jamesnunn/pgtest>`_ package.


.. seealso::
   Before jumping in and start writing your own tests, please takes a look at the tests provided in the
   `aiida-cutter`_ plugin template.

.. _aiida-cutter: https://github.com/aiidateam/aiida-plugin-cutter/

Using the unittest framework
----------------------------

The ``unittest`` package is included in the python standard library.
It is widely used despite some limitations (it is also used for testing ``aiida-core``).
We provide a :py:class:`aiida.manage.fixtures.PluginTestCase` to be used for inheritance.
By default, each test method in the test case class runs with a fresh aiida database.
Due to the limitation of ``unittest``, sub-clasess of ``PluginTestCase`` has to be run
with the special runner in  :py:class:`aiida.manage.fixtures.TestRunner`.
To run the actually tests, you need to prepare a run script in python::

  import unittest
  from aiida.manage.fixtures import TestRunner

  test = unittest.deaultTestLoader.discover('.')
  TestRunner().run(tests)

Save it as ``run_tests.py`` and tests can be discovered and run using::

  python run_test.py



Migrating existing AiidaTestCase tests
--------------------------------------

The ``pytest`` framework can also be used to run ``unittest`` tests.
Here, we will explain how to migrate existing tests for the plugins,
written as sub-classes of ``AiidaTestCase`` to work with ``pytest``.
First, let's see a typical test class using the ``unittest``::

  from aiida.plugins import DataFactory

  # Assuming our new date type has entry point myplugin.complex
  ComplexData = DataFactory("myplugin.complex")

  class TestComplexData(AiidaTestCase):

      def setUp(self):
          """Clean up database for each test"""
          self.clean_db()

      def store_complex(self, comp_num):
          """Store a complex number, returns pk"""
          comdata = ComplexData()
          comdata.value = comp_num
          return comdata.pk

      def test_complex_store(self):
          """Test if the complex numbers can be stored"""

          comdata = ComplexData()
          comdata.value = 1 + 2j
          comdata.store()

      def test_complex_retrieve(self):
          """Test if the complex 

          comp_num = 1 + 2j
          pk = self.store_complex(cnum)
          comdata = load_node(pk)
          self.assertEqual(comdata.value == comp_num)

We can modify this test class using some of the pytest features to allow it to be
run with ``pytest`` directly, as shown below:

.. code-block:: python
  :emphasize-lines: 6-11, 14, 18-22

  # Assuming our new date type has entry point myplugin.complex
  import unittest
  import pytest


  @pytest.fixture(scope='module')
  def module_import(aiida_profile, request):
      from aiida.plugins import DataFactory
      ComplexData = DataFactory("myplugin.complex")
      for name, value in locals():
          setattr(resquest.module, name, value)


  @pytest.mark.usefixtures('module_import')
  class TestComplexData(TestCase):
      """Test ComplexData. Compatible with pytest."""

      @pytest.fixture(autouse=True)
      def reset_db(aiida_profile):
          aiida_profile.reset_db()
          yield
          aiida_profile.reset_db()

      def store_complex(self, comp_num):
          comdata = ComplexData()
          comdata.value = comp_num
          return comdata.pk

      def test_complex_store(self):
          """Test if the complex numbers can be stored"""
          comdata = ComplexData()
          comdata.value = 1 + 2j
          comdata.store()

      def test_complex_retrieve(self):
          """
          Test if the complex number stored can be retrieved
          """
          comp_num = 1 + 2j
          pk = self.store_complex(cnum)
          comdata = load_node(pk)
          self.assertEqual(comdata.value == comp_num)

 
To allow pytest to run the tests, we first swap the ``AiidaTestCase`` with the generic
``TestCase``. We define a module scope fixture ``module_import`` to import the
required AiiDA modules and make them available in the module namespace.
All previous module levels imports should be encapsulated inside this fixture.
The `request`_ is a built-in fixture in pytest to allow introspect of the function
from which the fixture is requested.
Here, we simply add every things in the function scope back into the module of the
class which requested the fixture.

Instead of the ``setUp`` and ``tearDown`` methods,
we define a ``reset_db`` fixture to reset the database for every tests.
The ``autouse=True`` flag tells all test methods inside the class to use it automatically.

When migrating your code to use the pytest, you may define a base class with these
modifications and use it as the superclass for other test classes. 

.. _request: https://docs.pytest.org/en/3.6.3/reference.html#request

.. seealso::
  More details can be found in the `pytest documentation`_ about running ``unittest`` tests.

.. note::
  The modification will break the compatibility of ``unittest`` and you will not be able
  to run with ``verdi devel tests`` interface.
  Do not forget to remove redundant entry points in your setup.json. 

.. _pytest documentation: https://docs.pytest.org/en/latest/unittest.html
