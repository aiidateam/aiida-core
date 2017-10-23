======================================
Updating AiiDA from a previous version
======================================

AiiDA can be updated from a previously installed version. Before beginning
the procedure, make sure of the following:

  * your daemon is stopped (use ``verdi daemon stop``),
  * you know your current AiiDA version. In case, you can get it from the ``verdi shell``::

      import aiida
      aiida.__version__

    (only the two first digits matter),
  * you have a backup of your database(s) (follow the guidelines in the
    :ref:`backup section<backup>`),
  * you have a backup of the full ``~/.aiida`` folder (where configuration
    files are stored),
  * (optional) ``virtualenv`` is installed, i.e. you once ran the command::

      pip install --user -U setuptools pip wheel virtualenv

.. note::
  A few general remarks:

  * If you want to update the code in the same folder, but modified some files locally,
    you can stash them (``git stash``) before cloning or pulling the new code.
    Then put them back with ``git stash pop`` (note that conflicts might appear).
  * If you encounter any problems and/or inconsistencies, delete any .pyc
    files that may have remained from the previous version. E.g. If you are
    in your AiiDA folder you can type ``find . -name "*.pyc" -type f -delete``.
  * From 0.8.0 onwards there is no ``requirements.txt`` file anymore. It has been replaced by ``setup_requirements.py`` and ``pip`` will install all the requirements automatically. If for some reason you would still like to get such a file, you can create it using the script ``aiida_core/utils/create_requirements.py``

.. note::
  Since AiiDA 0.9.0, we use Alembic for the database migrations of the
  SQLAlchemy backend. In case you were using SQLAlchemy before the introduction
  of Alembic, you may experience problems during your first migration. If it is
  the case, please have a look at the following section :ref:`first_alembic_migration`

Updating between development versions (for Developers)
++++++++++++++++++++++++++++++++++++++++++++++++++++++

After you checkout a development branch or pull a new state from the repository

* run ``pip install -e`` again (or in a different virtualenv)
  This applies changes to the distribution system (setup.py and related)

To use the new version in production:

* run ``verdi setup``
  This updates your daemon profile and related files. It should not be done when another version of aiida is wished to be used productively on the same machine/user.

Updating from 0.9.* Django to 0.10.0 Django
+++++++++++++++++++++++++++++++++++++++++++

* Backup your database

* Upgrade AiiDA within the virtual environment

* Run the migration::

    python backends/djsite/manage.py --aiida-profile=PROFILENAME migrate

  An warning will appear since we are deleting a table::

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


Updating from 0.9.* to 0.10.0
++++++++++++++++++++++++++++++++++++++++++

Export archive files
------------------------------------------
The format of the export archives, created with ``verdi export``, has changed and in order
to import them, they have to be migrated. To do this you can use the ``verdi export migrate`` command.
The archive format version up to ``0.10.0`` was ``0.2`` and starting from ``0.10.0`` it is now ``0.3``.

Quantum ESPRESSO plugins
------------------------------------------
In version ``0.10.0`` the Quantum ESPRESSO plugin was removed from the ``aiida_core`` repository and moved to a
`separate plugin repository <https://github.com/aiidateam/aiida-quantumespresso>`_.
With the new plugin system introduced in version ``0.9.0``, installing the Quantum ESPRESSO plugin through the repository is very easy.
However, if your current AiiDA installation still has the plugin files in the ``aiida_core`` tree, they have to be removed manually and the old entry points have to be removed from the cache.
The instructions to accomplish this will be detailed below.

* First, make sure that you are in the correct virtual environment, for example (replace the path with the path to your actual virtual environment::

    source ~/aiidapy/bin/activate

* Go to the directory of the ``aiida_core`` source code tree, for example::

    cd ~/code/aiida/core

* Check out the new version, either through the develop branch or a specific tag::

    git checkout -b develop
    git pull origin develop

  or::

    git checkout -b v0.10.0 v0.10.0

* Remove the obsolete Quantum ESPRESSO plugin directory::

    rm -rf aiida/orm/calculation/job/quantumespresso

* Install the new version of AiiDA by typing::

    pip install -e .[<EXTRAS>]

  where <EXTRAS> is a comma separated list of the optional features you wish to install (see the :ref:`optional dependencies<install_optional_dependencies>`).

This should have successfully removed the old plugin entry points from your virtual environment installation.
To verify this, execute the following command and make sure that the ``quantumespresso.*`` plugins are **not** listed::

  verdi calculation plugins

If this is not the case, run the following command and check the ``verdi`` command again::

  reentry scan
  verdi calculation plugins

If the plugin is no longer listed, we can safely reinstall them from the new plugin repository and the plugin loading system.
First, clone the plugin repository from github in a separate directory::

  mkdir -p ~/code/aiida/plugins
  cd ~/code/aiida/plugins
  git clone https://github.com/aiidateam/aiida-quantumespresso

Now all we have to do to install the plugin and have it registered with AiiDA is execute the following ``pip`` command::

  pip install -e aiida-quantumespresso

To verify that the plugin was installed correctly, list the plugin entry points through ``verdi``::

  verdi calculation plugins

If the Quantum ESPRESSO plugin entry points are not listed, you can try the following::

  reentry scan
  verdi calculation plugins

If the entry points are still not listed, please contact the developers for support.
Finally, make sure to restart the daemon::

  verdi daemon restart

Now everything should be working properly and you can use the plugin as you were used to.
You can use the ``CalculationFactory`` exactly in the same way to load calculation classes.
For example you can still call ``CalculationFactory('quantumespresso.pw')`` to load the ``PwCalculation`` class.
The only thing that will have changed is that you can no longer directly import from the old plugin location.
That means that ``from aiida.orm.calculation.job.quantumespresso.pw import PwCalculation`` will no longer work as those files no longer exist.
Instead you can use the factories or the new import location ``from aiida_quantumespresso.calculation.pw import PwCalculation``.


Updating from older versions
++++++++++++++++++++++++++++++++++++++++++
To find the update instructions for older versions of AiiDA follow the following links
to the documentation of the corresponding version:

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