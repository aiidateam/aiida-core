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
After you have performed all the steps in the checklist described in the previous section, go to your local clone of the ``aiida_core`` repository and checkout the desired branch or tag.
If you installed ``aiida_core`` in a virtual environment make sure that you have loaded it.

Each version increase may come with its own necessary migrations and you should only ever update the version by one at a time.
Therefore, first make sure you know the version number of the current installed version by using ``verdi shell`` and typing::

  import aiida
  aiida.__version__

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

Updating from 0.9.* to 0.10.0
-----------------------------
Multiple things have changed in AiiDA ``v0.10.0`` that require some manual attention when upgrading the ``aiida_core`` code base.
There have been changes to the:

1. Database schema
2. Export archive format
3. Plugins for Quantum ESPRESSO, ASE, COD tools and NWChem

For each of these three points, you will find instructions on how to perform the necessary migration below.

Database migration
^^^^^^^^^^^^^^^^^^

The exact migration procedure will differ slightly depending on which backend the profile uses, but for both Django and SqlAlchemy the procedure starts as follows.

* Backup your database
* Upgrade AiiDA within the virtual environment

After having performed these steps, the remainder of the migration can be triggered by executing any ``verdi`` command.
For example you can execute ``verdi calculation list`` and you should be prompted with an exception for Django or a message for SqlAlchemy.
Depending on your backend, follow the instructions below.

Django
""""""

When the profile that you want to migrate uses Django for the backend you will get an exception and instructions to run a command that looks like the following::

    python aiida_core/aiida/backends/djsite/manage.py --aiida-profile=PROFILENAME migrate

After you execute the migration command, a warning will appear since we are deleting a table::

    The following content types are stale and need to be deleted:

        db | dbpath

    Any objects related to these content types by a foreign key will also
    be deleted. Are you sure you want to delete these content types?
    If you're unsure, answer 'no'.

        Type 'yes' to continue, or 'no' to cancel:

Have faith in your AiiDA team and type ``yes``!

  .. note::
    For everyone who `tuned` his AiiDA-database by dropping the path-table and the corresponding triggers,
    the migration will fail because the table db_dbpath does not exist.
    In such a case, you have to insert the table manually into the database of your profile
    (which we call AIIDADB in the demonstration):

    .. code-block:: psql

        > psql AIIDADB
        AIIDADB=# CREATE TABLE db_dbpath (
        id integer NOT NULL,
        depth integer NOT NULL,
        entry_edge_id integer,
        direct_edge_id integer,
        exit_edge_id integer,
        child_id integer NOT NULL,
        parent_id integer NOT NULL
        );

SqlAlchemy
""""""""""

When the profile that you want to migrate uses SqlAlchemy for the backend you will get a message that looks like the following::

  It is time to perform your first SQLAlchemy migration.
  Would you like to migrate to the latest version? [Y/n]

Simply enter ``Y`` and hit enter and the database migration should be automatically applied.


Export archive file migration
-----------------------------

The format of the export archives, created with ``verdi export``, has changed in ``aiida_core v0.10.0`` and in order
to be able to import them, they have to be migrated. To do this you can use the ``verdi export migrate`` command.
The archive format version up to ``0.10.0`` was ``0.2`` and starting from ``0.10.0`` it is now ``0.3``.

Plugin migration
----------------

In ``v0.10.0`` the plugins for Quantum ESPRESSO, ASE, COD tools and NWChem that used to be included in ``aiida_core`` have
been moved to separate plugin repositories which can be found here:

* `Quantum ESPRESSO`_ (aiida-quantumespresso)
* `ASE`_ (aiida-ase)
* `COD tools`_ (aiida-codtools)
* `NWChem`_ (aiida-nwchem)

.. _Quantum ESPRESSO: https://github.com/aiidateam/aiida-quantumespresso
.. _ASE: https://github.com/aiidateam/aiida-ase
.. _COD tools: https://github.com/aiidateam/aiida-codtools
.. _NWChem: https://github.com/aiidateam/aiida-nwchem

With the new plugin system introduced in ``aiida_core v0.9.0``, all you have to do to install a plugin for AiiDA is to install it with ``pip``.
For example, to install all four original plugins you can execute::

  pip install aiida-quantumespresso aiida-ase aiida-codtools aiida-nwchem

Note, however, that if you are upgrading an existing manual installation of ``aiida_core``, you first need to make sure that your code base is cleaned.
After you have upgraded your local repository to ``v0.10.0`` by checking out the relevant branch or tag, before you run ``pip install``, make sure
that all old ``*pyc`` files are removed, by running the following command from your local checked out repository::

  find . -name "*pyc" -type f -delete

Now you can install the new version of ``aiida_core`` with any of the optional extra dependencies that you might need::

  pip install -e .[<EXTRAS>]

and make sure to refresh the plugin cache by executing::

  reentry scan

Now you can reinstall any of the Quantum ESPRESSO, ASE, COD tools or NWChem plugins, either through ``pip`` for example::

  pip install aiida-quantumespresso

or you can install them for development just like ``aiida_core`` by checking out the repository and using ``pip install -e``, like so::

  git clone https://github.com/aiidateam/aiida-quantumespresso
  pip install -e aiida-quantumespresso

You can verify that the plugins were properly installed by running the following ``verdi`` command::

  verdi calculation plugins

Now everything should be working properly and you can use the plugin as you were used to.
You can use the class factories, such as ``CalculationFactory``, exactly in the same way to load the plugin classes.
For example you can still call ``CalculationFactory('quantumespresso.pw')`` to load the ``PwCalculation`` class.
The only thing that will have changed is that you can no longer use any of the old direct import paths, as those files no longer exist.


Updating from older versions
============================
To find the update instructions for older versions of AiiDA follow the following links to the documentation of the corresponding version:

* `0.8.* Django`_
* `0.7.* Django`_
* `0.6.* Django`_
* `0.6.* SqlAlchemy`_
* `0.5.* Django`_
* `0.4.* Django`_

.. _0.8.* Django: http://aiida-core.readthedocs.io/en/v0.9.1/installation/index.html#updating-from-0-8-django-to-0-9-0-django
.. _0.7.* Django: http://aiida-core.readthedocs.io/en/v0.8.1/installation/index.html#updating-from-0-7-0-django-to-0-8-0-django
.. _0.6.* Django: http://aiida-core.readthedocs.io/en/v0.7.0/installation.html#updating-from-0-6-0-django-to-0-7-0-django
.. _0.6.* SqlAlchemy:   http://aiida-core.readthedocs.io/en/v0.7.0/installation.html#updating-from-0-6-0-django-to-0-7-0-sqlalchemy
.. _0.5.* Django: http://aiida-core.readthedocs.io/en/v0.7.0/installation.html#updating-from-0-5-0-to-0-6-0
.. _0.4.* Django: http://aiida-core.readthedocs.io/en/v0.5.0/installation.html#updating-from-0-4-1-to-0-5-0