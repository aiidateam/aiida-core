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
  that can be done with one click from the BitBucket web interface,
  and then you just do a local 'git pull')
* remember to fix generic bugs in the ``develop`` (or in a branch to be
  then merged in the develop), *not in your local branch*
  (except if the bug is present only in the branch); only then merge
  ``develop`` back into your branch. In particular, if it is a complex bugfix,
  better to have a branch because it allows to
  backport the fix also in old releases, if we want to support multiple versions
* only when a feature is ready, merge it back into ``develop``. If it is
  a big change, better to instead do a `pull request` on BitBucket instead
  of directly merging and wait for another (or a few other)
  developers to accept it beforehand, to be sure it does not break anything.

For a cheatsheet of git commands, see :doc:`here <git_cheatsheet>`.

.. note:: Before committing, **always** run::
  
    verdi devel tests
  
  to be sure that your modifications did not introduce any new bugs in existing
  code. Remember to do it even if you believe your modification to be small - 
  the tests run pretty fast! 

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
   ``aiida.djsite.db.substests``, and instead of inheriting each class directly
   from ``unittest``, inherit from ``aiida.djsite.db.testbase.AiidaTestCase``.
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
   
   Once you create a new file in ``aiida.djsite.db.substests``, you have to
   add a new entry to the ``db_test_list`` inside ``aiida.djsite.db.testbase``
   module in order for ``verdi devel tests`` to find it. In particular,
   the key should be the name that you want to use on the command line of
   ``verdi devel tests`` to run the test, and the value should be the full
   module name to load. Note that, in ``verdi devel tests``,
   the string ``db.`` is prepended to the name of each test involving the
   database.
   Therefore, if you add a line::
   
     db_test_list = {
       ...
       'newtests': 'aiida.djsite.db.subtests.mynewtestsmodule',
       ...
     }
   
   you will be able to run all all tests inside
   ``aiida.djsite.db.subtests.mynewtestsmodule`` with the command::
   
     verdi devel tests db.newtests
   
   .. note:: If in the list of parameters to ``verdi devel tests`` you add
     also a ``db`` parameter, then all database-related tests will be run, i.e.,
     all tests that start with ``db.`` (or, if you want, all tests in the
     ``db_test_list`` described above).
   
   .. note:: By default, the test database is created using an in-memory SQLite
     database, which is much faster than creating from scratch a new test
     database with PostgreSQL or SQLite. However, if you want to test
     database-specific settings and you want to use the same type of database
     you are using with AiiDA, set the ``tests.use_sqlite`` global property to
     ``False``::
     
       verdi devel setproperty tests.use_sqlite false
     
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

