Testing
+++++++

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

