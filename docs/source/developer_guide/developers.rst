###########################
Developer's Guide For AiiDA
###########################

Python style
++++++++++++
When writing python code, a more than reasonable guideline is given by
the Google python styleguide
http://google-styleguide.googlecode.com/svn/trunk/pyguide.html.
The documentation should be written consistently in the style of
sphinx.

And more generally, write verbose! Will you remember
after a month why you had to write that check on that line? (Hint: no)
Write comments!

Pylint
------
You can check your code style and other important code errors by using Pylint.
Once installed you can run Pylint from the root source directory on the code
using the command::

  pylint aiida

The most important part is the summary under the ``Messages`` table near the
end.

Version number
++++++++++++++

The AiiDA version number is stored in ``aiida/__init__.py``.  Make sure to
update this when changing version number.

Inline calculations
+++++++++++++++++++
If an operation is extremely fast to be run, this can be done directly in
Python, without being submitted to a cluster.
However, this operation takes one (or more) input data nodes, and creates new
data nodes, the operation itself is not recorded in the database, and provenance
is lost. In order to put a Calculation object inbetween, we define the
:py:class:`InlineCalculation <aiida.orm.implementation.general.calculation.inline.InlineCalculation>`
class, that is used as the class for these calculations that are run "in-line".

We also provide a wrapper (that also works as a decorator of a function),
:py:func:`~aiida.orm.implementation.general.calculation.inline.make_inline`. This can be used
to wrap suitably defined function, so that after their execution,
a node representing their execution is stored in the DB, and suitable input
and output nodes are also stored.

.. note:: See the documentation of this function for further documentation of
  how it should be used, and of the requirements for the wrapped function.


Database schema
+++++++++++++++

Django
------
The Django database schema can be found in :py:mod:`aiida.backends.djsite.db.models`.

If you need to change the database schema follow these steps:

1. Make all the necessary changes to :py:mod:`aiida.backends.djsite.db.models`
2. Create a new migration file.  From ``aiida/backends/djsite``, run::

     python manage.py makemigrations

   This will create the migration file in ``aiida/backends/djsite/db/migrations`` whose
   name begins with a number followed by some description.  If the description
   is not appropriate then change to it to something better but retain the
   number.

3. Open the generated file and make the following changes::

    from aiida.backends.djsite.db.migrations import update_schema_version
    ...
    SCHEMA_VERSION = # choose an appropriate version number
                     # (hint: higher than the last migration!)
    ...
    class Migration(migrations.Migration):
      ...
      operations = [
        ..
        update_schema_version(SCHEMA_VERSION)
      ]

5. Change the ``LATEST_MIGRATION`` variable in
   ``aiida/backends/djsite/db/migrations/__init__.py`` to the name of your migration
   file::

     LATEST_MIGRATION = '0003_my_db_update'

   This let's AiiDA get the version number from your migration and make sure the
   database and the code are in sync.
6. Migrate your database to the new version, (again from ``aiida/backends/djsite``),
   run::

     python manage.py migrate


SQLAlchemy
----------
The SQLAlchemy database schema can be found in ``aiida/backends/sqlalchemy/models``

If you need to change the database schema follow these steps:

1. Make all the necessary changes to the model than you would like to modify
   located in the ``aiida/backends/sqlalchemy/models`` directory.
2. Create new migration file by going to ``aiida/backends/sqlalchemy`` and
   executing::

    ./alembic_manage.py revision "This is a new revision"

   This will create a new migration file in ``aiida/backends/sqlalchemy/migrations/versions``
   whose names begins with an automatically generated hash code and the
   provided message for this new migration. Of course you can change the
   migration message to a message of your preference. Please look at the
   generatedvfile and ensure that migration is correct. If you are in doubt
   about the operations mentioned in the file and its content, you can have a
   look at the Alembic documentation.
3. Your database will be automatically migrated to the latest revision as soon
   as you run your first verdi command. You can also migrate it manually with
   the help of the alembic_manage.py script as you can see below.

Overview of alembic_manage.py commands
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The alembic_manage.py provides several options to control your SQLAlchemy
migrations. By executing::

    ./alembic_manage.py --help

you will get a full list of the available arguments that you can pass and
commands. Briefly, the available commands are:

* **upgrade** This command allows you to upgrade to the later version. For the
  moment, you can only upgrade to the latest version.
* **downgrade** This command allows you to downgrade the version of your
  database. For the moment, you can only downgrade to the base version.
* **history** This command lists the available migrations in chronological
  order.
* **current** This command displays the current version of the database.
* **revision** This command creates a new migration file based on the model
  changes.

.. _first_alembic_migration:

Debugging Alembic
~~~~~~~~~~~~~~~~~
Alembic migrations should work automatically and migrate your database to the
latest version. However, if you were using SQLAlchemy before we introduced
Alembic, you may get a message like to following during the first migration::

    sqlalchemy.exc.ProgrammingError: (psycopg2.ProgrammingError) relation
    "db_dbuser" already exists [SQL: '\nCREATE TABLE db_dbuser (\n\tid SERIAL
    NOT NULL, \n\temail VARCHAR(254), \n\tpassword VARCHAR(128),
    \n\tis_superuser BOOLEAN NOT NULL, \n\tfirst_name VARCHAR(254),
    \n\tlast_name VARCHAR(254), \n\tinstitution VARCHAR(254), \n\tis_staff
    BOOLEAN, \n\tis_active BOOLEAN, \n\tlast_login TIMESTAMP WITH TIME ZONE,
    \n\tdate_joined TIMESTAMP WITH TIME ZONE, \n\tCONSTRAINT db_dbuser_pkey
    PRIMARY KEY (id)\n)\n\n']

In this case, you should create manually the Alembic table in your database and
add a line with the database version number. To do so, use psql to connect
to the desired database::

    psql aiidadb_sqla

(you should replace ``aiidadb_sqla`` with the name of the database that you
would like to modify). Then, execute the following commands::

    CREATE TABLE alembic_version (version_num character varying(32) not null, PRIMARY KEY(version_num));
    INSERT INTO alembic_version VALUES ('e15ef2630a1b');
    GRANT ALL ON alembic_version TO aiida;

Commits and GIT usage
+++++++++++++++++++++

In order to have an efficient management of the project development, we chose
to adopt the guidelines for the branching model described
`here <http://nvie.com/posts/a-successful-git-branching-model/>`_.
In particular:

* The main branch in which one should work is called ``develop``
* The ``master`` branch is reserved for releases: every commit there implies
  a new release. Therefore, one should never commit directly there (except once
  per every release).
* New releases should also be tagged.
* Any new modification requiring just one commit can be done in develop
* mid-to-long development efforts should be done in a branch, branching off
  from develop (e.g. a long bugfix, or a new feature)
* while working on the branch, often merge the develop branch back
  into it (if you also have a remote branch and there are no conflicts,
  that can be done with one click from the GitHub web interface,
  and then you just do a local 'git pull')
* remember to fix generic bugs in the ``develop`` (or in a branch to be
  then merged in the develop), *not in your local branch*
  (except if the bug is present only in the branch); only then merge
  ``develop`` back into your branch. In particular, if it is a complex bugfix,
  better to have a branch because it allows to
  backport the fix also in old releases, if we want to support multiple versions
* only when a feature is ready, merge it back into ``develop``. If it is
  a big change, better to instead do a `pull request` on GitHub instead
  of directly merging and wait for another (or a few other)
  developers to accept it beforehand, to be sure it does not break anything.

For a cheatsheet of git commands, see :doc:`here <git_cheatsheet>`.

.. note:: Before committing, **always** run::

    verdi devel tests

  to be sure that your modifications did not introduce any new bugs in existing
  code. Remember to do it even if you believe your modification to be small -
  the tests run pretty fast!

Pre-commit hooks
----------------

Git has a *hooks* mechanism to run tasks automatically when an event is triggered.We use this mechanism to trigger code checks on every commit. Currently only the :`aiida.control` module is affected, but more parts of the code will be added progressively.

These checks are to prevent syntax or other coding errors from being committed and to enforce style consistency.

Two tools are run on all changed files before allowing a commit:

 * `yapf`_ will automatically format your files for you. If it makes any changes, the commit will fail and you will get the opportunity to review them. Once you are done, ``git add`` the changed file and commit again.
 * `prospector`_ will run multiple linters (mainly pylint) that will do:

   - Syntax checking
   - Static analysis
   - Check for missing docstrings
   - Check for *secrets* (prevent you from committing passwords, tokens, etc)

   It will output file, line number and helpful messages and suggestions for each problem it finds.
   
  
.. _yapf: https://github.com/google/yapf
.. _prospector: https://prospector.landscape.io/en/master/

Setting up the hooks is simple::

   cd aiida_core
   pip install [-e] .[dev_precommit]
   pre-commit install
   # from now on on every git commit the checks will be run on changed files
   
When working on parts of the code that are not included in pre-commit tests yet, it is ok to not install the hooks. 

When code that fails the pre-commit checks is commited, the checks will run in a continuous integration stage and the commit will fail tests. Still sometimes it is necessary to push a work-in-progress state to continue working somewhere else, this can be accomplished by ``git commit --no-verify``.

If you want to run the checks without having to call ``git commit``, you can do so using ``pre-commit run``.

Tests
+++++

Running the tests
-----------------

To run the tests, use the::

  verdi devel tests

command. You can add a list of tests after the
command to run only a selected portion of tests (e.g. while developing, if you
discover that only a few tests fail). Use TAB completion to get the full list
of tests. For instance, to run only the tests for transport and the generic
tests on the database, run::

  verdi devel tests aiida.transport db.generic

Furthermore, you need to set up a few things on your local machine to successfully run the tests:

Test profile
~~~~~~~~~~~~

To run the tests involving the database, you need to have a special testing profile. A profile is considered a testing profile if the **profile name** and the **database name** both start with ``test_``, and the repository path contains ``test_``.

SSH to localhost
~~~~~~~~~~~~~~~~

For the transport tests, you need to be able to ssh into your local machine (``localhost``). Here is how this is done for different operating systems:

Linux (Ubuntu)
==============

    * Install ``openssh-server``
    * Create an ssh key (if you don't have one already), and add it to ``~/.ssh/authorized_keys``
    * For **security** reasons, you might want to disallow ssh connections from outside your local machine. To do this, change ``#ListenAddress 0.0.0.0`` to ``ListenAddress 127.0.0.1`` (note the missing ``#``) in ``/etc/ssh/sshd_config``.
    * Now you should be able to type ``ssh localhost`` and get a successful connection.

If your OS was not listed above but you managed to get the ssh connection running, please add the description above.

Install extras
~~~~~~~~~~~~~~

In case you did not install all extras, it is possible that some tests fail due to missing packages. If you installed AiiDA with ``pip``, you can use the following command to get the necessary extras:

.. code :: bash

    pip install -e .[testing]

Where the ``-e`` flag means that the code is just linked to the appropriate folder, and the package will update when you change the code.


The test-first approach
-----------------------

Remember in best codes actually the `tests are written even before writing the
actual code`_, because this helps in having a clear API.

For any new feature that you add/modify, write a test for it! This is extremely
important to have the project last and be as bug-proof as possible. Even more
importantly, add a test that fails when you find a new bug, and then solve the
bug to make the test work again, so that in the future the bug is not introduced
anymore.

Remember to make unit tests as atomic as possible, and to document them so that
other developers can understand why you wrote that test, in case it should fail
after some modification.

.. _tests are written even before writing the actual code: http://it.wikipedia.org/wiki/Test_Driven_Development

Creating a new test
-------------------

There are three types of tests:

1. Tests that do not require the usage of the database (testing the creation of
   paths in k-space, the functionality of a transport plugin, ...)
2. Tests that require the database, but do not require submission (e.g.
   verifying that node attributes can be correctly queried, that the transitive
   closure table is correctly generated, ...)
3. Tests that require the submission of jobs

For each of the above types of tests, a different testing approach is followed
(you can also see existing tests as guidelines of how tests are written):

1. Tests are written inside the package that one wants to test, creating
   a ``test_MODULENAME.py`` file. For each group of tests, create a new subclass
   of ``unittest.TestCase``, and then create the tests as methods using
   the `unittests module <https://docs.python.org/2/library/unittest.html>`_.
   Tests inside a selected number of AiiDA packages are automatically discovered
   when running ``verdi devel tests``. To make sure that your test is discovered,
   verify that its parent module is listed in the
   ``base_allowed_test_folders`` property of the ``Devel`` class, inside
   ``aiida.cmdline.commands.devel``.

   For an example of this type of tests, see, e.g.,
   the ``aiida.common.test_utils`` module.
2. In this case, we use the `testing functionality of
   Django <https://docs.djangoproject.com/en/dev/topics/testing/>`_,
   adapted to run smoothly with AiiDA.

   To create a new group of tests, create a new python file under
   ``aiida.backends.djsite.db.substests``, and instead of inheriting each class directly
   from ``unittest``, inherit from ``aiida.backends.djsite.db.testbase.AiidaTestCase``.
   In this way:

   a. The Django testing functionality is used, and a temporary database is used
   b. every time the class is created to run its tests, default data are
      added to the database, that would otherwise be empty (in particular, a
      computer and a user; for more details, see the code of
      the ``AiidaTestCase.setUpClass()`` method).
   c. at the end of all tests of the class, the database is cleaned
      (nodes, links, ... are deleted) so that the temporary database
      is ready to run the tests of the following test classes.

   .. note:: it is *extremely important* that these tests are run from the
     ``verdi devel tests`` command line interface. Not only this will ensure
     that a temporary database is used (via Django), but also that a temporary
     repository folder is used. Otherwise, you risk to corrupt your database
     data. (In the codes there are some checks to avoid that these classes
     are run without the correct environment being prepared by ``verdi
     devel tests``.)

   Once you create a new file in ``aiida.backends.djsite.db.substests``, you have to
   add a new entry to the ``db_test_list`` inside ``aiida.backends.djsite.db.testbase``
   module in order for ``verdi devel tests`` to find it. In particular,
   the key should be the name that you want to use on the command line of
   ``verdi devel tests`` to run the test, and the value should be the full
   module name to load. Note that, in ``verdi devel tests``,
   the string ``db.`` is prepended to the name of each test involving the
   database.
   Therefore, if you add a line::

     db_test_list = {
       ...
       'newtests': 'aiida.backends.djsite.db.subtests.mynewtestsmodule',
       ...
     }

   you will be able to run all all tests inside
   ``aiida.backends.djsite.db.subtests.mynewtestsmodule`` with the command::

     verdi devel tests db.newtests

   .. note:: If in the list of parameters to ``verdi devel tests`` you add
     also a ``db`` parameter, then all database-related tests will be run, i.e.,
     all tests that start with ``db.`` (or, if you want, all tests in the
     ``db_test_list`` described above).


3. These tests require an external engine to submit the calculations and then
   check the results at job completion. We use for this a continuous integration
   server, and the best approach is to write suitable workflows to run
   simulations and then verify the results at the end.

Special tests
~~~~~~~~~~~~~

Some tests have special routines to ease and simplify the creation of new tests.
One case is represented by the tests for transport. In this case, you can define
tests for a specific plugin as described above (e.g., see the
``aiida.transport.plugins.test_ssh`` and ``aiida.transport.plugins.test_local``
tests). Moreover, there is a ``test_all_plugins`` module in the same folder.
Inside this module, the discovery code is adapted so that each test method
defined in that file **and decorated with** ``@run_for_all_plugins`` is
run for *all* available plugins, to avoid to rewrite the same
test code more than once and ensure that all plugins behave in the
same way (e.g., to copy files, remove folders, etc.).

Virtual environment
+++++++++++++++++++

Sometimes it's useful to have a virtual environment that separates out the
AiiDA dependencies from the rest of the system.  This is especially the case
when testing AiiDA against library versions that are different from those
installed on the system.

First, install virtualenv using pip::

  pip install virtualenv

Basic usage
-----------

#. To create a virtual environment in folder ``venv``, while in the AiiDA
   directory type::

     virtualenv venv

   This puts a copy of the Python executables and the pip library within the
   ``venv`` folder hierarchy.

#. Activate the environment with::

     source venv/bin/activate

   Your shell should now be prompt should now start with ``(venv)``.

#. (optional) Install AiiDA::

     pip install .

#. Deactivate the virtual environment::

     deactivate

Deprecated features, renaming, and adding new methods
+++++++++++++++++++++++++++++++++++++++++++++++++++++
In case a method is renamed or removed, this is the procedure to follow:

1. (If you want to rename) move the code to the new function name.
   Then, in the docstring, add something like::

     .. versionadded:: 0.7
        Renamed from OLDMETHODNAME

2. Don't remove directly the old function, but just change the code to use
   the new function, and add in the docstring::

     .. deprecated:: 0.7
        Use :meth:`NEWMETHODNAME` instead.

   Moreover, at the beginning of the function, add something like::

     import warnings

     warnings.warn(
         "OLDMETHODNAME is deprecated, use NEWMETHODNAME instead",
         DeprecationWarning)

   (of course, replace ``OLDMETHODNAME`` and ``NEWMETHODNAME`` with the
   correct string, and adapt the strings to the correct content if you are
   only removing a function, or just adding a new one).
