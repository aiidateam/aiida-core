###########################
Developer's Guide For AiiDA
###########################

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

For a cheatsheet of git commands, see :ref:`here <git_cheatsheet>`_.

.. note:: Before committing, **always** run::
  
    verdi devel tests
  
  to be sure that your modifications did not introduce any new bugs in existing
  code. Remember to do it even if you believe your modification to be small - 
  the tests run pretty fast! 

Tests
+++++

For any new feature that you add/modify, write a test for it! This is extremely
important to have the project last and be as bug-proof as possible.

Remember to make unit tests as atomic as possible, and to document them so that
other developers can understand why you wrote that test, in case it should fail
after some modification.

Remember in best codes actually the `tests are written even before writing the
actual code`_, because this helps in having a clear API. 

To run the tests, use the::

  verdi devel tests 
  
command. Moreover you can add a list of tests after the 
command to run only a selected portion of tests (e.g. while developing, if you
discover that only a few tests fail). You tab completion to get the full list
of tests. For instance, to run only the tests for transport and the generic
tests on the database, run::

  verdi devel tests aiida.transport db.generic

.. _tests are written even before writing the actual code: http://it.wikipedia.org/wiki/Test_Driven_Development

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

