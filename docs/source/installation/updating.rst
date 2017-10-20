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

Updating from 0.9.* to 0.10.0
++++++++++++++++++++++++++++++++++++++++++

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


Updating from 0.8.* Django to 0.9.0 Django
++++++++++++++++++++++++++++++++++++++++++

* Enable your virtual environment::

    virtualenv ~/aiidapy
    source ~/aiidapy/bin/activate

* Go to the directory where you want to place your code and clone the latest
  version from Github::

    cd <where_you_want_the_aiida_sourcecode>
    git clone git@github.com:aiidateam/aiida_core.git

.. note::
    * If you have cloned in the past the code, you can just checkout the latest version

    * In case you have an older version of pip or setuptools, try to upgrade them::

        pip install -U setuptools pip

* Install the new version of AiiDA by typing::

    pip install -e aiida_core[<EXTRAS>]

  where <EXTRAS> is a comma separated list of the optional features
  you wish to install (see the :ref:`optional dependencies<install_optional_dependencies>`).
  The two first steps above can be removed if you do not want to install AiiDA
  into a virtual environment (reminder: this is *not* recommended).


Updating from 0.7.0 Django to 0.8.0 Django
++++++++++++++++++++++++++++++++++++++++++

* In a virtual environment, clone and install the code from github with::

    virtualenv ~/aiidapy
    source ~/aiidapy/bin/activate
    cd <where_you_want_the_aiida_sourcecode>
    git clone git@github.com:aiidateam/aiida_core.git
    pip install -e aiida_core[<EXTRAS>]

  where <EXTRAS> is a comma separated list of the optional features
  you wish to install (see the :ref:`optional dependencies<install_optional_dependencies>`).
  The two first steps above can be removed if you do not want to install AiiDA
  into a virtual environment (reminder: this is *not* recommended).

* Undo all PATH and PYTHONPATH changes you did in your ``.bashrc`` and similar
  files to add ``verdi`` and ``runaiida`` of the previous version.
  When using the virtual environment, you do not need anymore to update
  the PYTHONPATH nor the PATH.
* Run a ``verdi`` command, e.g., ``verdi calculation list``. This should
  raise an exception, and in the exception message you will see the
  command to run to update the schema version of the DB (version 0.8
  is using a newer version of the schema). The command will look like
  ``python manage.py --aiida-profile=default migrate`` (to be run from
  <AiiDA_folder>/aiida/backends/djsite) but please read the message for the correct command to run.
* If you run ``verdi calculation list`` again now, it should work without
  error messages.
* Rerun ``verdi setup`` (formerly ``verdi install``), no manual changes
  to your profile should be necessary. This step is necessary as it
  updates some internal configuration files.
* You might want to create an alias to easily go into the correct virtual
  environment and have all AiiDA commands available: in your `~/.bashrc`
  file you can add an alias like::

    alias aiida_env='source ~/aiidapy/bin/activate'

* Activate the tab-completion of `verdi` commands (see :ref:`here<tab-completion>`).

**Updating the backup script**

In case you used the AiiDA repository backup mechanism in 0.7.0 and you would
like to continue using it in 0.8.0, you should update the backup scripts.

To do so:

* Re-run the backup_setup.py (``verdi -p PROFILENAME run MY_AIIDA_FOLDER/aiida/common/additions/backup_script/backup_setup.py``).
  Keep in mind that you should have activated your virtual environment in case
  you use one.

* Provide the backup folder by providing the full path. This is the folder
  where the backup configuration files and scripts reside.

* Provide the destination folder of the backup (normally in the previously
  provided backup folder)

* Reply *No* when the scripts asks you to print the configuration parameters
  explanation.

* Reply *No* when the scripts asks you to configure backup configuration file.

* The script should have exited now. Ignore its proposals to update the
  ``backup_info.json.tmpl`` and the startup script.

* Your backup mechanism is ready to be used again. You can continue using it
  by executing ``start_backup.py``.

Updating from an older version
++++++++++++++++++++++++++++++

Because the database schema changes typically at every version, and since
the migration script assumes that you are using the previous AiiDA version,
one has to migrate in steps, from the version of AiiDA you were using,
until the current one. For instance, if you are currently using AiiDA 0.5,
you should first update to 0.6, then to 0.7, and finally to 0.8. Do not forget to
**deactivate** the current virtual environment before installing any new version.

For *each intermediate update* (e.g. when you update from 0.5 to 0.6 in the above example),
do the following::

  virtualenv ~/aiidapy_<VERSION>
  source ~/aiidapy_<VERSION>/bin/activate
  cd <where_you_want_the_aiida_sourcecode>

(<VERSION> being the intermediate version you are updating to, in our example 0.6).

Then get the code with the appropriate version and install its dependencies:
AiiDA versions prior or equal to 0.7 can be cloned from bitbucket::

  git clone git@bitbucket.org:aiida_team/aiida_core.git aiida_core_<VERSION>
  cd aiida_core_<VERSION>
  git checkout v<VERSION>
  pip install -U -r requirements.txt

and update the ``PATH`` and ``PYTHONPATH`` environment variables
in your ``~/.bashrc`` file before sourcing it (replace <AiiDA_folder> with the folder in
which you just installed AiiDA)::

    export PATH="${PATH}:<AiiDA_folder>/bin"
    export PYTHONPATH="${PYTHONPATH}:<AiiDA_folder>"

Then follow the specific instructions below for each intermediate update.

.. note::
  * If you have an issue with ``ultrajson`` during the ``pip install`` step,
    replace ``ultrajson`` with ``ujson`` in the ``requirements.txt`` file
    (the name of this module changed over time).
  * In the ``pip install`` step, you might need to install some dependencies
    located in ``optional_requirements.txt`` (e.g. ``psycopg2`` for postgresql
    database users), as well as ``ipython`` to get a proper shell, e.g.::

      pip install -U -r requirements.txt psycopg2==2.6 ipython

Updating from 0.6.0 Django to 0.7.0 Django
------------------------------------------
In version 0.7 we have changed the Django database schema and we also have
updated the AiiDA configuration files.

* Run a ``verdi`` command, e.g., ``verdi calculation list``. This should
  raise an exception, and in the exception message you will see the
  command to run to update the schema version of the DB (version 0.7
  is using a newer version of the schema).
  The command will look like
  ``python manage.py --aiida-profile=default migrate`` (to be run from
  <AiiDA_folder>/aiida/backends/djsite) but please read the
  message for the correct command to run.
* If you run ``verdi calculation list`` again now, it should work without
  error messages.
* To update the AiiDA configuration files, you should execute the migration
  script::

    python <AiiDA_folder>/aiida/common/additions/migration_06dj_to_07dj.py

Updating from 0.6.0 Django to 0.7.0 SQLAlchemy
----------------------------------------------
The SQLAlchemy backend was in beta mode for version 0.7.0. Therefore some of
the verdi commands may not work as expected or at all (these are very few).
If you would like to test the SQLAlchemy backend with your existing AiiDA database,
you should convert it to the JSON format. We provide a transition script
that will update your config files and change your database to the proper schema.

* Go to you AiiDA folder and run ``ipython``. Then execute::

    from aiida.backends.sqlalchemy.transition_06dj_to_07sqla import transition
    transition(profile="<your_profile>",group_size=10000)

  by replacing ``<your_profile>`` with the name of the appropriate profile
  (typically, ``default`` if you have only one profile).

Updating from 0.5.0 to 0.6.0
----------------------------

* Execute the migration script::

    python <AiiDA_folder>/aiida/common/additions/migration.py

.. note::
  * In this version a lot of changes were introduced in order to allow
    a second object-relational mapper later (we will refer to it as
    backend) for the management of the used DBMSs and more specifically
    of PostgreSQL.
    Even if most of the needed restructuring & code addition was finished,
    a bit of more work was needed to get the new backend available.
  * You can not directly import data (``verdi import``) that you have exported
    (``verdi export``) with a previous version of AiiDA. Please use
    :download:`this script <../examples/convert_exportfile_version.py>`
    to convert it to the new schema. (Usage: ``python
    convert_exportfile_version.py input_file output_file``).


Updating from 0.4.1 to 0.5.0
----------------------------
* Run a ``verdi`` command, e.g., ``verdi calculation list``. This should
  raise an exception, and in the exception message you will see the
  command to run to update the schema version of the DB (version 0.5
  is using a newer version of the schema).
  The command will look like
  ``python manage.py --aiida-profile=default migrate``
  (to be run from `<AiiDA_folder>/ai    aiida/djsite`) but please read the
  message for the correct command to run.
* If you run ``verdi calculation list`` again now, it should work without
  error messages.

.. note:: If you were working on a plugin, the plugin interface changed:
  you need to change the CalcInfo returning also a CodeInfo, as specified
  :ref:`here<qeplugin-prepare-input>` and also accept a ``Code`` object
  among the inputs (also described in the same page).

