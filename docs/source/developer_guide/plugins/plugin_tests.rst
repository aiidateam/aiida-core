.. _plugin.testing:

Writing tests for plugin
========================

When developing a plugin it is important to write tests. The main concern of running
tests is that the test environment has to be separated from the production environment
and care should be taken to avoid any unwanted change to the user's database.
You may have
noticed that AiiDA has a :ref:`testing framework <tools.testing>` for the development
of it new features. While it is possible to apply it to the plugins, it makes things
complicated as any tests for plugins has to be run using ``verdi devel tests`` command-line
interface with test-specific profile pre-defined.

AiiDA ships with tools to simply tests for plugins. The recommended way is to use the
`pytest`_ framework, while the `unittest`_ framework is also supported.
The test environments are created and managed by the :py:func:`aiida.utils.fixtures.fixture_manager` defined in :py:mod:`aiida.utils.fixtures`.

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
   :start-after: @pytest.fixture(scope='session')

  
The ``aiida_profile`` fixture initialize the ``fixture_manager`` yields a :py:class:`aiida.utils.fixtures.FixtureManager` object.
By using the *with* clause we can ensure that the resources used during the tests are released. Notice the line::

  @pytest.fixture(scope='session')

which signals that this fixture will be reused for the entire test session, as the test aiida
profile only needs to be initialized once.
The next fixture ``new_database`` request and ``aiida_profile`` and tells the received
``FixtureManager`` object to reset the database. By requesting the ``new_database`` fixture,
the test function will start with a fresh aiida environment.
The next fixture, ``new_workdir``, returns an temporary directory for file operations.
Using the yield statement allows the fixture to execute code after test function finishes.
Here, it automatically cleans up the returned directory.
You may want to define other fixtures such as those setup and return ``Data`` nodes or prepare calculations.

To make these two fixtures available to all tests, they can be put into the ``conftest.py``
in root level of the package or ``tests`` sub-packages. An example can be downloaded :download:`here <conftest.py>`.

.. seealso::
  More information of ``conftest.py`` can be found `here <conftest>`_.

.. _conftest: https://docs.pytest.org/en/stable/fixture.html?highlight=conftest#conftest-py-sharing-fixture-functions

Import statements in tests
^^^^^^^^^^^^^^^^^^^^^^^^^^

When running test, it is important that you DO NOT explicitly load the aiida database
via ``load_dbenv()``, which could result in corruption of your database with actual data.
However, many AiiDA modules, such as those in ``aiida.orm`` cannot be loaded without calling ``load_dbenv()`` first.
Modules in the plugin may also import such aiida modules at the top level,
which make themselves impossible to be imported directly in test moduels.
To solve this issue, import should be delay to after the test profile has been setup.
You can import these required modules at function level.
A better way is to define a fixture as a loader for module imports. Instead of having::

  import aiida.orm as orm

at the top of the file, you can define a special fixture::

  @pytest.fixture(scope='module')
  def orm(aiida_profile):
      import aiida.orm as orm
      return orm

and simply request this fixture for your test function::

  def test_load_dataclass(orm):
      """Test loading a data class defined by the plugin"""
      MyData = orm.DataFactory('my_plugin.maydata')

The ``'scope='module'`` avoids repetitively doing the import again for each test.
It is also possible to group many imports in a single fixture and return them::

  @pytest.fixture(scope='module')
  def imps(aiida_profile):
      """Return an class with all imports as its attributes"""
      class Imports(object):
          import aiida.orm as orm

      return Imports


  def test_load_dataclass(imps):
      """Test loading a data class defined by the plugin"""
      MyData = imps.orm.DataFactory('my_plugin.maydata')

Requesting the ``aiida_profile`` fixture in the ``imps`` fixture,
guarantees that the test environment will be loaded before the any import statement
are executed.

Running the tests
^^^^^^^^^^^^^^^^^

To run the tests, simply type::

  pytest

As ``pytest`` will handle the discovery of the test modules and test functions (their name should start with the work **test**)

.. note::
   You should see information about creating aiida profile and database in the beginning.
   Do not panic, as and the aiida profile and database are completely isolated and will not affect your ``.aiida`` folder.
   Internally, at temporary folder is used as the ``.aiida`` folder and the test database are created using the *pgtest* package.


.. seealso::
   Before jump in writing your own tests, please takes a look at the tests provided in the
   `aiida-cutter`_ plugin template.

.. _aiida-cutter: https://github.com/aiidateam/aiida-plugin-cutter/

Using unittest framework
------------------------

The ``uniitest`` package is included in the python standard library. It has some
limitations but is still widely used (also for ``aiida_core``).
The :py:class:`aiida.utils.fixtures.PluginTestCase` should be used for inheritance in the
TestCase classes. By default each test method will be run with a fresh aiida database.
Due to the limitation of ``uniitest``, sub-clasess of ``PluginTestCase`` has to be run
with the special runner in  :py:class:`aiida.utils.fixtures.TestRunner`.
To run the actually tests, you need to prepare a run script in python::

  import uniitest
  from aiida.utils.fixtures import TestRunner

  test = unittest.deaultTestLoader.discover('.')
  TestRunner().run(tests)

Save it as ``run_tests.py`` and tests can be discovered and run using::

  python run_test.py



Migrating existing AiiDATestCase tests
--------------------------------------

The ``pytest`` framework can also be used to run those tests defined using
``uniittest``. Furthermore, it is possible to blend in some ``pytest`` features.
Here, we will introduce how to adjust existing tests for the plugins, written by
inheriting ``AiiDATestCase`` to work with ``pytest``.
First, lets see a typical test class using the ``unittest``::

  from aiida.orm import DataFactory

  # Assuming our new date type has entry point myplugin.complex
  ComplexData = DataFactory("myplugin.complex")

  class TestComplexData(AiiDATestCase):

      def setUp(self):
          """Clean up database for each test"""
          self.clean_db()

      def store_complex(self, comp_num):

          comdata = ComplexData()
          comdata.value = comp_num
          return comdata.pk


      def test_complex_store(self):
          """Test if the complex numbers can be stored"""

          comdata = ComplexData()
          comdata.value = 1 + 2j
          comdata.store()

      def test_complex_retrived(self):
          """Test if the complex 

          comp_num = 1 + 2j
          pk = self.store_complx(cnum)
          comdata = load_node(pk)
          self.assertEqual(comdata.value == comp_num)

Previously, a test entry point has to be registered to AiiDA to point to this test.
Direct running with ``python unittest -m`` will not work and the same for ``pytest``.
We modify this test using some of the ``pytest`` features

.. code-block:: python
  :emphasize-lines: 6-9, 11, 15-19

  # Assuming our new date type has entry point myplugin.complex
  import unittest
  import pytest


  @pytest.fixture(scope='class')
  def cls_import(aiida_profile, request):
      from aiida.orm import DataFactory
      request.module.ComplexData = DataFactory('myplugin.complex')

  @pytest.mark.usefixtures('cls_import')
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

      def test_complex_retrived(self):
          """
          Test if the complex number stored can be retrieved
          """
          comp_num = 1 + 2j
          pk = self.store_complx(cnum)
          comdata = load_node(pk)
          self.assertEqual(comdata.value == comp_num)

 
To allow ``pytest`` to run the tests, we first swap the ``AiiDATestCase`` with the generic
``TestCase``. We define a class scope fixture ``cls_import`` to import the
required AiiDA modules and make them available in the module namespace.
Note this fixture relies on the ``aiida_profile`` fixture to ensure that the test environment is loaded first.
The `request`_ is a built-in fixture in pytest to introspect of the function from which
the fixture is requested.
Instead of the ``setUp`` and ``unittest.TestCase.tearDown`` methods,
we define a ``reset_db`` fixture to reset the database for every tests.
The ``autouse=True`` flag tells all test methods inside the class to use it automatically.

.. _request: https://docs.pytest.org/en/3.6.3/reference.html#request

.. seealso::
  More details can be found in the `pytest documentation`_ about running ``unittest`` tests.

.. note::
  The modification will break the compatibility of ``uniitest`` and you will not be able
  to run with ``verdi devel tests`` interface. Simply use ``pytest`` to run them and do
  not forget to remove entry points in your setup.json. 

.. _pytest documentation: https://docs.pytest.org/en/latest/unittest.html
