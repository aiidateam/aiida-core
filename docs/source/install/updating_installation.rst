.. _updating_installation:

*********************
Updating installation
*********************

Before you update your AiiDA installation, first make sure that you do the following:

* Stop your daemon by executing ``verdi daemon stop``
* Create a backup of your database(s) by following the guidelines in the :ref:`backup section<backup>`
* Create a backup of the ``~/.aiida`` folder (where configuration files are stored)

If you have installed AiiDA manually from a local clone of the ``aiida_core`` repository, skip to the instructions for :ref:`developers <update_developers>`.
Otherwise, if you have installed AiiDA through ``pip``, you can also update your installation through ``pip``.
If you installed ``aiida_core`` in a virtual environment make sure to load it first.
Now you are ready to update your AiiDA installation through ``pip``::

  pip install --upgrade aiida_core

After upgrading your AiiDA installation you may have to perform :ref:`version specific migrations <update_migrations>`.
When all necessary migrations are completed, finalize the update by executing::

  verdi setup

This updates your daemon profile and related files.
It should not be done when another version of aiida is wished to be used productively on the same machine/user.


.. _update_developers:

Updating AiiDA for developers
=============================
Each version increase may come with its own necessary migrations and you should only ever update the version by one at a time.
Therefore, first make sure you know the version number of the current installed version by using ``verdi shell`` and typing::

  import aiida
  aiida.__version__

After you have performed all the steps in the checklist described in the previous section and determined the current installed version, go to your local clone of the ``aiida_core`` repository and checkout the desired branch or tag.
If you installed ``aiida_core`` in a virtual environment make sure that you have loaded it.

Now you can install the updated version of ``aiida_core`` by simply executing::

  pip install -e .

After upgrading your AiiDA installation you may have to perform :ref:`version specific migrations <update_migrations>` based on the version of your previous installation.
When all necessary migrations are completed, finalize the update by executing::

  verdi setup

This updates your daemon profile and related files.

.. note::
  A few general remarks:

  * If you want to update the code in the same folder, but modified some files locally,
    you can stash them (``git stash``) before cloning or pulling the new code.
    Then put them back with ``git stash pop`` (note that conflicts might appear).
  * If you encounter any problems and/or inconsistencies, delete any ``.pyc``
    files that may have remained from the previous version. E.g. If you are
    in your AiiDA folder you can type ``find . -name "*.pyc" -type f -delete``.

.. note::
  Since AiiDA ``0.9.0``, we use Alembic for the database migrations of the
  SQLAlchemy backend. In case you were using SQLAlchemy before the introduction
  of Alembic, you may experience problems during your first migration. If it is
  the case, please have a look at the following section :ref:`first_alembic_migration`


.. _update_migrations:

Version migration instructions
==============================

Updating from 0.12.* to 1.0
---------------------------

Configuration file
^^^^^^^^^^^^^^^^^^
* The tab-completion activation for ``verdi`` has changed, simply replace the ``eval "$(verdi completioncommand)"`` line in your activation script with ``eval "$(_VERDI_COMPLETE=source verdi)"``



Updating from older versions
----------------------------
To find the update instructions for older versions of AiiDA follow the following links to the documentation of the corresponding version:

* `0.11.*`_
* `0.10.*`_
* `0.9.*`_
* `0.8.* Django`_
* `0.7.* Django`_
* `0.6.* Django`_
* `0.6.* SqlAlchemy`_
* `0.5.* Django`_
* `0.4.* Django`_

.. _0.11.*: https://aiida-core.readthedocs.io/en/v0.12.2/installation/updating.html#updating-from-0-11-to-0-12-0
.. _0.10.*: http://aiida-core.readthedocs.io/en/v0.10.0/installation/updating.html#updating-from-0-9-to-0-10-0
.. _0.9.*: http://aiida-core.readthedocs.io/en/v0.10.0/installation/updating.html#updating-from-0-9-to-0-10-0
.. _0.8.* Django: http://aiida-core.readthedocs.io/en/v0.9.1/installation/index.html#updating-from-0-8-django-to-0-9-0-django
.. _0.7.* Django: http://aiida-core.readthedocs.io/en/v0.8.1/installation/index.html#updating-from-0-7-0-django-to-0-8-0-django
.. _0.6.* Django: http://aiida-core.readthedocs.io/en/v0.7.0/installation.html#updating-from-0-6-0-django-to-0-7-0-django
.. _0.6.* SqlAlchemy:   http://aiida-core.readthedocs.io/en/v0.7.0/installation.html#updating-from-0-6-0-django-to-0-7-0-sqlalchemy
.. _0.5.* Django: http://aiida-core.readthedocs.io/en/v0.7.0/installation.html#updating-from-0-5-0-to-0-6-0
.. _0.4.* Django: http://aiida-core.readthedocs.io/en/v0.5.0/installation.html#updating-from-0-4-1-to-0-5-0