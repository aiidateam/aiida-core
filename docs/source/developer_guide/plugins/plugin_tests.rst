.. _plugin.testing:

Testing AiiDA plugins
=====================

We highly recommend writing tests for your AiiDA plugins and running continous integration tests using free platforms like `GitHub Actions <ghactions>`_.

We recommend the following folder structure for AiiDA plugin packages::

   aiida-mycode/           - distribution folder
      aiida_mycode/        - plugin package
      tests/               - tests directory (possibly with subdirectories)

.. note::
    Keeping the tests outside the plugin package keeps the distribution of your plugin package light.

.. _ghactions: https://github.com/features/actions

Using the pytest framework
--------------------------

We recommend the `pytest`_ framework for testing AiiDA plugins.

One concern when running tests for AiiDA plugins is to separate the test environment from your production environment.
Depending on the kind of test, each should even be run against a fresh AiiDA database.

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


.. _pytest: https://pytest.org
.. _unittest: https://docs.python.org/library/unittest.html
.. _fixture: https://docs.pytest.org/en/latest/fixture.html

AiiDA's fixtures
^^^^^^^^^^^^^^^^

Many tests require input data to be set up before the test starts, e.g. some AiiDA data nodes.
pytest has the concept of a `fixture`_, which can be a predefined object that the test acts on or just some code you want to run before the test starts.

AiiDA ships with a number of fixtures in :py:mod:`aiida.manage.tests.pytest_fixtures` for you to use.

For example:

  * The :py:func:`~aiida.manage.tests.pytest_fixtures.aiida_profile` fixture initializes the :py:class:`~aiida.manage.tests.TestManager` and yields it to the test function.
    Its parameters ``scope='session', autouse=True`` cause this fixture to automatically run once per test session, even if you don't explicitly require it.
  * The :py:func:`~aiida.manage.tests.pytest_fixtures.clear_database` fixture depends on the :py:func:`~aiida.manage.tests.pytest_fixtures.aiida_profile` fixture and tells the received :py:class:`~aiida.manage.tests.TestManager` instance to reset the database.
    This fixture lets each test start in a fresh AiiDA environment.
  * The :py:func:`~aiida.manage.tests.pytest_fixtures.temp_dir` fixture returns a temporary directory for file operations and deletes it after the test is finished.
  * ... you may want to add your own fixtures tailored for your plugins to set up specific ``Data`` nodes & more.

In order to make these fixtures available to your tests, add them to your ``conftest.py`` file at the root level of your plugin package as follows::

   import pytest
   pytest_plugins = ['aiida.manage.tests.pytest_fixtures']

   # Example of how to define your own fixture
   @pytest.fixture(scope='function', autouse=True)
   def clear_database_auto(clear_database):
       """Automatically clear database in between tests."""
       pass

Your custom fixtures would typically also go inside the ``conftest.py``.
For more information on the ``conftest.py``, see `here <conftest>`_.

You can now start writing tests e.g. in a ``test_calculations.py`` file::

      # No need to import fixtures - added by pytest "automagically"

      def test_qe_calculation(aiida_local_code_factory, clear_database):
          from aiida.engine import run
          from aiida.plugins import CalculationFactory

          code = aiida_local_code_factory(entry_point='quantumespresso.pw', executable='pw.x')
          # ...
          inputs = { 'code': code, ... }

          # submit a calculation using this code ...
          result = run(CalculationFactory('quantumespresso.pw'), **inputs)

          # check outputs of calculation
          assert result['...'] == ...

Feel free to check out the tests of the `aiida-diff`_ demo plugin package.

.. _conftest: https://docs.pytest.org/en/stable/fixture.html?highlight=conftest#conftest-py-sharing-fixture-functions
.. _aiida-diff: https://github.com/aiidateam/aiida-diff/


Running tests
^^^^^^^^^^^^^

Simply type::

  pytest

in the folder where your ``conftest.py`` resides.

pytest will automatically discover files, classes and function names starting with the word ``test``.


Using the unittest framework
----------------------------


The ``unittest`` package is included in the python standard library and is widely used despite its limitations.

In analogy to the fixtures of ``pytest``, for ``unittest`` we provide a :py:class:`aiida.manage.tests.unittest_classes.PluginTestCase` class that your test cases can inherit from.

Due to limitations of ``unittest``, tests written using the :py:class:`~aiida.manage.tests.unittest_classes.PluginTestCase` need to be run through a special :py:class:`~aiida.manage.tests.unittest_classes.TestRunner` (i.e. ``python -m unittest discover`` will *not* work).
To actually the tests, prepare a script ``run_tests.py``::

  import unittest
  from aiida.manage.tests.unittest_classes import TestRunner

  tests = unittest.defaultTestLoader.discover('.')
  TestRunner().run(tests)

and then run the tests using::

  python run_test.py



Migrating from ``AiidaTestCase`` to pytest
------------------------------------------

The slightly outdated testing framework of ``aiida-core`` defined an :py:class:`~aiida.backends.testbase.AiidaTestCase` class plus some functionality around it.

Below, we give an example of how to convert tests written for the :py:class:`~aiida.backends.testbase.AiidaTestCase` to work with ``pytest``.
In the process, we'll take advantage of the fact that the ``pytest`` framework can also run test cases using the ``unittest`` classes, in order to maintain the class-style layout.

Below is a typical test class based on the :py:class:`~aiida.backends.testbase.AiidaTestCase`::

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

If you enable the AiiDA fixtures in your ``conftest.py`` as explained above, they will also act on test functions defined in ``unittest`` test classes!
Thus, the conversion to ``pytest`` can look as follows:

.. code-block:: python

  import unittest
  import pytest
  from aiida.plugins import DataFactory

  # Assuming our new date type has entry point myplugin.complex
  ComplexData = DataFactory("myplugin.complex")

  class TestComplexData(unittest.TestCase):
      """Test ComplexData. Compatible with pytest."""

      @pytest.fixture(autouse=True)
      def setup_db(self, clear_database):
          """Clear database for each test."""

      def store_complex(self, comp_num):
          comdata = ComplexData()
          comdata.value = comp_num
          return comdata.pk

      def test_complex_store(self, clear_database):
          """Test if the complex numbers can be stored."""
          comdata = ComplexData()
          comdata.value = 1 + 2j
          comdata.store()

      def test_complex_retrieve(self, clear_database):
          """Test if the complex number stored can be retrieved."""
          comp_num = 1 + 2j
          pk = self.store_complex(cnum)
          comdata = load_node(pk)
          self.assertEqual(comdata.value == comp_num)

For more details on running ``unittest`` cases through pytest, see the `pytest documentation`_.

.. _pytest documentation: https://docs.pytest.org/en/latest/unittest.html
