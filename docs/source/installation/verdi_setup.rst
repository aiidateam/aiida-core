.. _verdi_setup:

===========
Verdi setup
===========
The quick install section detailed how ``verdi quicksetup`` can be used to quickly setup AiiDA by creating a profile and a database for you.
If you want more control over this process, for example if you want to use a database that you created yourself, you can use ``verdi setup``::

    $ verdi setup <profile_name>

or equivalently::

    $ verdi -p <profile_name> setup

The same commands can also be used to edit already existing profiles.
The ``verdi setup`` command will guide you through the setup process through a series of prompts.

The first thing that will be asked to you is the timezone, extremely important to get correct dates and times for your calculations.

AiiDA will do its best to try and understand the local timezone (if properly configured on your machine), and will suggest a set of sensible values.
Choose the timezone that fits best to you (that is, the nearest city in your timezone - for Lausanne, for instance, we choose ``Europe/Zurich``) and type it at the prompt.

As a second parameter to input during the ``verdi setup`` phase, the "Default user email" is asked.
We suggest here to use your institution email, that will be used to associate the calculations to you.

.. note:: In AiiDA, the user email is used as username, and also as unique identifier when importing/exporting data from AiiDA.

.. note:: Even if you choose an email different from the default one
  (``aiida@localhost``), a user with email ``aiida@localhost`` will be
  set up,
  with its password set to ``None`` (disabling access via this user
  via API or Web interface).

  The existence of a default user is internally useful for multi-user
  setups, where only one user
  runs the daemon, even if many users can simultaneously access the DB.
  See the page on :ref:`setting up AiiDA in multi-user mode<aiida_multiuser>`
  for more details (only for advanced users).

.. note:: The password, in the current version of AiiDA, is not used (it will
    be used only in the REST API and in the web interface). If you leave the
    field empty, no password will be set and no access will be granted to the
    user via the REST API and the web interface.

Then, the following prompts will help you configure the database. Typical settings are::

    Insert your timezone: Europe/Zurich
    Default user email: richard.wagner@leipzig.de
    Database engine: postgresql_psycopg2
    PostgreSQL host: localhost
    PostgreSQL port: 5432
    AiiDA Database name: aiida_dev
    AiiDA Database user: aiida
    AiiDA Database password: <password>
    AiiDA repository directory: /home/wagner/.aiida/repository/
    [...]
    Configuring a new user with email 'richard.wagner@leipzig.de'
    First name: Richard
    Last name: Wagner
    Institution: BRUHL, LEIPZIG
    The user has no password, do you want to set one? [y/N] y
    Insert the new password:
    Insert the new password (again):


