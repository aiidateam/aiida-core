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

Pre-commit hooks can help you write clean code by running

 * code formatting
 * syntax checking
 * static analysis
 * checks for missing docstrings
 * ...

locally at every commit you make. We currently use `yapf`_ and `prospector`_, but more tools may follow.

Set up the hooks as follows::

   cd aiida_core
   pip install [-e] .[dev_precommit]
   pre-commit install
   # from now on on every git commit the checks will be run on changed files

.. note:: If you work in a ``conda`` environment, make sure to ``conda install
   virtualenv`` to avoid problems with virtualenv inside conda.

Then, you'll need to explicitly enable pre-commit checks for the python files
you're working on by editing ``.pre-commit-config.yaml``.
Now, every time you ``git commit``, your code will be checked.

 * If you ever need to commit a 'work in progress' you may skip the checks via ``git commit --no-verify``. Yet, keep in mind that the pre-commit hooks will also run (and fail) at the continuous integration stage when you push them upstream.
 * Use ``pre-commit run`` to run the checks without committing


.. _yapf: https://github.com/google/yapf
.. _prospector: https://prospector.landscape.io/en/master/



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

