.. _how-to:plugins:

**********************
How to package plugins
**********************

This section focuses on how to *package* AiiDA extensions (plugins) so that they can be tested, published and eventually reused by others.
For guides on writing specific extensions, see :ref:`how-to:plugin-codes:interfacing` and :ref:`how-to:data:plugin`.

.. todo::

    For guides on writing specific extensions, see :ref:`how-to:plugin-codes:interfacing`, :ref:'how-to:plugin-codes:scheduler', :ref:'how-to:plugin-codes:transport' or :ref:`how-to:data:plugin`.


.. _how-to:plugins:bundle:

Creating a plugin package
=========================


AiiDA plugins can be bundled and distributed in a `Python package <packages>`_ that provides a set of extensions to AiiDA.

.. note::

  The Python community uses the term 'package' rather loosely.
  Depending on context, it may refer simply to a folder containing individual Python modules or it may include the files necessary for building and installing a package to be distributed via the `Python Package Index (PyPI) <pypi>`_.

.. _packages: https://docs.python.org/2/tutorial/modules.html?highlight=package#packages


Quickstart
----------

The fastest way to jumpstart an AiiDA plugin package is to use the `AiiDA plugin cutter <plugin-cutter>`_ in order to template the basic folder structure, already customized according to the desired name of your plugin, following AiiDA conventions.

Simply go to the `AiiDA plugin cutter <plugin-cutter>`_ and follow the usage instructions.
See also the `aiida-diff`_ demo plugin package for an in-depth explanation of the files & folders produced by the plugin cutter.

In the following, we explain some of the conventions implemented by the AiiDA plugin cutter.


Choosing a name
----------------

The naming convention for AiiDA plugin packages is ``aiida-mycode`` for the plugin distribution on `PyPI`_ and ``aiida_mycode`` for the corresponding python package, leading to the following folder structure::

   aiida-mycode/
      aiida_mycode/
         __init__.py

.. note::

   Python package names cannot contain dashes, thus the underscore.

If you intend to eventually publish your plugin package, please go to the `AiiDA plugin registry <registry>`_  and choose a name that is not already taken.
You are also encouraged to pre-register your package (instructions provided on the registry), both to reserve your plugin name and to inform others of your ongoing development.


.. _how-to:plugins:bundle:folderstructure:

Folder structure
----------------

The overall folder structure of your plugin is up to you, but it is useful to follow a set of basic conventions.
Here is an example of a folder structure for an AiiDA plugin, illustrating different levels of nesting (see also the `aiida-diff demo plugin`_)::

   aiida-mycode/           - distribution folder
      aiida_mycode/        - top-level package (from aiida_mycode import ..)
         __init__.py
         calculations/
            __init__.py
            mycode.py      - contains MycodeCalculation
         parsers/
            __init__.py
            basic.py       - contains BasicMycodeParser
            full.py        - contains FullMycodeParser
         data/
            __init__.py    - contains code-specific MyData data format
         commands.py       - contains verdi subcommand for visualizing MyData
         workflows/
            __init__.py
            basic.py       - contains a basic workflow using mycode
         ...
      LICENSE              - license of your plugin
      MANIFEST.in          - lists non-python files to be installed, such as LICENSE
      README.md            - project description for github and PyPI
      setup.json           - plugin metadata: installation requirements, author, entry points, etc.
      setup.py             - PyPI installation script, parses setup.json and README.md
      ...

A minimal plugin package instead might look like::

   aiida-minimal/
      aiida_minimal/
         __init__.py
      setup.py
      setup.json

.. _how-to:plugins:entrypoints:

Registering plugins through entry points
========================================

An AiiDA plugin is an extension of AiiDA that announces itself by means of a new *entry point* (for details, see :ref:`topics:plugins:entrypoints`).
Adding a new entry point consists of the following steps:

 #. Deciding a name.
    We *strongly* suggest to start the name of each entry point with the name of the plugin package (omitting the 'aiida-' prefix).
    For a package ``aiida-mycode``, this will usually mean ``"mycode.<something>"``

 #. Finding the right entry point group. You can list the entry point groups defined by AiiDA via ``verdi plugin list``.
    For a documentation of the groups, see :ref:`topics:plugins:entrypointgroups`.

 #. Adding the entry point to the ``entry_points`` field in the ``setup.json`` file::

     ...
     entry_points={
       "aiida.calculations": [
         "mycode.<something> = aiida_mycode.calcs.some:MysomethingCalculation"
       ]
     }
     ...

 #. Let setuptools and reentry know about your entry point by installing your plugin again::

     pip install -e .
     reentry scan

Your new entry point should now show up in ``verdi plugin list aiida.calculations``.


.. _how-to:plugins:test:

Testing a plugin package
=========================

Writing tests for your AiiDA plugins and running continuous integration tests using free platforms like `GitHub Actions <ghactions>`_ is the best way to ensure that your plugin works and keeps working as it is being developed.
We recommend using the `pytest`_ framework for testing AiiDA plugins.

For an example of how to write tests and how to set up continuous integration, see the `aiida-diff`_ demo plugin package.


Folder structure
----------------

We suggest the following folder structure for including tests in AiiDA plugin packages::

   aiida-mycode/           - distribution folder
      aiida_mycode/        - plugin package
      tests/               - tests directory (possibly with subdirectories)

.. note::
    Keeping the tests outside the plugin package keeps the distribution of your plugin package light.

AiiDA's fixtures
----------------

Many tests require a full AiiDA environment to be set up before the test starts, e.g. some AiiDA data nodes.
The pytest library has the concept of `fixtures`_ for encapsulating code you would like to run before a test starts.
AiiDA ships with a number of fixtures in :py:mod:`aiida.manage.tests.pytest_fixtures` that take care of setting up the test environment for you (for more details, see :ref:`topics:plugins:testfixtures`).

In order to make these fixtures available to your tests, create a ``conftest.py`` (see also `pytest docs <conftest>`_) at the root level of your plugin package as follows::

   import pytest
   pytest_plugins = ['aiida.manage.tests.pytest_fixtures']  # make AiiDA's fixtures available
   # tip: look inside aiida.manage.tests.pytest_fixtures to see which fixtures are provided

   @pytest.fixture(scope='function')  # a fixture that will run once per test function that requests it
   def integer_input():
       """Integer input for test run."""
       from aiida.orm import Int
       input_value = Int(5)
       return input_value

   @pytest.fixture(scope='function', autouse=True)  # a fixture that automatically runs once per test function
   def clear_database_auto(clear_database):  # request AiiDA's "clear_database" fixture
       """Automatically clear database in between tests."""
       pass

You can now start writing tests e.g. in a ``tests/test_calculations.py`` file::

      # No need to import fixtures here - they are added by pytest "automagically"

      def test_qe_calculation(aiida_local_code_factory, integer_input):  # requesting "aiida_local_code_factory" and "integer_input" fixtures
          """Test running a calculation using a CalcJob plugin."""
          from aiida.engine import run
          from aiida.plugins import CalculationFactory

          # search for 'pw.x' executable in PATH, set up an AiiDA code for it and return it
          code = aiida_local_code_factory(entry_point='quantumespresso.pw', executable='pw.x')
          # ...
          inputs = { 'code': code, 'int_input': integer_input, ... }  # use "integer_input" fixture

          # run a calculation using this code ...
          result = run(CalculationFactory('quantumespresso.pw'), **inputs)

          # check outputs of calculation
          assert result['...'] == ...

In order to run your tests, simply type ``pytest`` at the root level or your package.
pytest automatically discovers and executes files, classes and function names starting with the word ``test``.

.. _conftest: https://docs.pytest.org/en/stable/fixture.html?highlight=conftest#conftest-py-sharing-fixture-functions
.. _fixtures: https://docs.pytest.org/en/latest/fixture.html


.. _how-to:plugins:document:

Documenting a plugin package
============================

AiiDA plugin packages are python packages, and general `best practises for writing python documentation <https://docs.python-guide.org/writing/documentation/>`_ apply.

In the following, we mention a few hints that apply specifically to AiiDA plugins.

Repository-level documentation
------------------------------

Since the source code of most AiiDA plugins is hosted on GitHub, the first contact of a new user with your plugin package is likely the landing page of your GitHub repository.

 * Make sure to have a useful ``README.md``, describing what your plugin does and how to install it.
 * Leaving a contact email and adding a license is also a good idea.
 * Make sure the information in the ``setup.json`` file is correct and up to date (in particular the version number), since this information is used to advertise your package on the AiiDA plugin registry.

Source-code-level documentation
-------------------------------

Source-code level documentations matters both for users of your plugin's python API and, particularly, for attracting contributions from others.

When adding new types of calculations or workflows, make sure to use `docstrings <https://www.python.org/dev/peps/pep-0257/#what-is-a-docstring>`_, and use the ``help`` argument to document input ports and output ports.
Users of your plugin can then inspect which inputs the calculations/workflows expect and which outputs they produce directly through the ``verdi`` cli.
For example, try::

    verdi plugin list aiida.calculations arithmetic.add

Documentation website
---------------------

For simple plugins, a well-written ``README.md`` can be a good start.
Once the README grows out of proportion, you may want to consider creating a dedicated documentation website.

The `Sphinx <http://www.sphinx-doc.org/en/master/>`_ tool makes it very easy to create documentation websites for python packages, and the `ReadTheDocs <http://readthedocs.org/>`_ service will host your sphinx documentation online for free.
The `aiida-diff demo plugin <aiida-diff>`_ comes with a full template for a sphinx-based documentation, including a mix of manually written pages and an automatically generated documentation of your plugin's python API.
See the `developer guide of aiida-diff <https://aiida-diff.readthedocs.io/en/latest/developer_guide/index.html>`_ for instructions on how to build it.

AiiDA provides a sphinx extension for inserting automatically generated documentations of ``Process`` classes (calculations and workflows) into your sphinx documentation (analogous to the information displayed by ``verdi plugin list``).
Enable the extension by adding ``aiida.sphinxext`` to the list of ``extensions`` in your ``docs/conf.py`` file.
You can now use the ``aiida-process``, ``aiida-calcjob`` or ``aiida-workchain`` directives in your ReST files like so::

    .. aiida-workchain:: MyWorkChain
        :module: my_plugin
        :hide-nondb-inputs:

Here,

 * ``MyWorkChain`` is the name of the workchain to be documented.
 * ``:module:`` is the python module from which the workchain can be imported.
 * ``:hide-unstored-inputs:`` hides workchain inputs that are not stored in the database (shown by default).

.. note::

    The ``aiida-workchain`` directive is hooked into ``sphinx.ext.autodoc``, i.e. it is used automatically by the generic ``automodule``, ``autoclass`` directives when applied to workchain classes.



.. _how-to:plugins:publish:

Publishing a plugin package
===========================

AiiDA plugin packages are published on the `AiiDA plugin registry <registry>`_ and the `python package index (PyPI) <pypi>`_.

Before publishing your plugin, make sure your plugin comes with:

 * a ``setup.json`` file with the plugin metadata
 * a ``setup.py`` file for installing your plugin via ``pip``
 * a license

For examples of these files, see the `aiida-diff demo plugin <aiida-diff>`_.

.. _how-to:plugins:publish:plugin-registry:

Publishing on the plugin registry
---------------------------------

The `AiiDA plugin registry <registry>`_ aims to be the home for all publicly available AiiDA plugins.
It collects information on the type of plugins provided by your package, which AiiDA versions it is compatible with, etc.

In order to register your plugin package, simply go to the `plugin registry <registry>`_ and follow the instructions in the README.

.. note::

  The plugin registry reads the metadata of your plugin from the ``setup.json`` file in your plugin repository.


We encourage you to **get your plugin package listed as soon as possible**, both in order to reserve the plugin name and to inform others of the ongoing development.

Publishing on PyPI
------------------

For distributing AiiDA plugin packages, we recommend to follow the `guidelines for packaging python projects <packaging>`_, which include making the plugin available on the `python package index <PyPI>`_.
This makes it possible for users to simply ``pip install aiida-myplugin``.

.. note::
    When updating the version of your plugin, don't forget to update the version number both in the ``setup.json`` and in ``aiida_mycode/__init__.py``.


.. _plugin-cutter: https://github.com/aiidateam/aiida-plugin-cutter
.. _aiida-diff: https://github.com/aiidateam/aiida-diff
.. _pytest: https://pytest.org
.. _ghactions: https://github.com/features/actions
.. _registry: https://github.com/aiidateam/aiida-registry
.. _pypi: https://pypi.python.org
.. _packaging: https://packaging.python.org/distributing/#configuring-your-project
