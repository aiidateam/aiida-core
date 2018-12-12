.. _updating_installation:
.. _updating_aiida:

**************
Updating AiiDA
**************

Before you update your AiiDA installation, please:

* Enter the python environment where AiiDA is installed
* Stop your daemon by executing ``verdi daemon stop``
* Create a backup of your database(s) by following the guidelines in the :ref:`backup section<backup>`
* Create a backup of the ``~/.aiida`` folder (where configuration files are stored)

If you have installed AiiDA through ``pip`` run::

  pip install --upgrade aiida-core

If you have installed AiiDA from a local clone of the ``aiida_core``
repository, enter the directory of the local clone and run::

  find . -name "*.pyc" -type f -delete  # deletes pre-compiled python files
  git checkout <desired-branch>
  git pull
  pip install -e .
  
After upgrading AiiDA, you may need to migrate your AiiDA database to the latest 
version of the schema.
If migrations are required, running any ``verdi`` command will automatically raise an exception
and print the instructions for performing the :ref:`migrations <update_migrations>`.

.. code-block:: bash

    aiida.common.exceptions.ConfigurationError: Database schema version 1.0.19 is outdated compared to the code schema version 1.0.20
    To migrate the database to the current version, run the following commands:
      verdi -p quicksetup daemon stop
      verdi -p quicksetup database migrate

Once the migrations have been performed, start the daemon and you are done.

.. note::

    Each version increase may come with its own necessary migrations and you should
    only ever update the version by one at a time.  
    Therefore, first get the version number from ``verdi --version``

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

.. note::
  Since AiiDA ``0.9.0``, we use Alembic for the database migrations of the
  SQLAlchemy backend. In case you were using SQLAlchemy before the introduction
  of Alembic, you may experience problems during your first migration. If it is
  the case, please see :ref:`this section <first_alembic_migration>`.
