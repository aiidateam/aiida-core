.. _intro:install:
.. _intro:advanced-config:

**********************
Advanced configuration
**********************

This chapter covers topics that go beyond the :ref:`standard setup of AiiDA <intro:get_started:setup>`.
If you are new to AiiDA, we recommed you first go through the :ref:`Basic Tutorial <tutorial:basic>`,
or see our :ref:`Next steps guide <tutorial:next-steps>`.

.. _intro:install:database:

Creating the database
---------------------

AiiDA uses a database to store the nodes, node attributes and other information, allowing the end user to perform fast queries of the results.
Currently, the highly performant `PostgreSQL`_ database is supported as a database backend.

.. _PostgreSQL: https://www.postgresql.org/downloads

.. admonition:: Find out more about the database
   :class: seealso title-icon-read-more

   - `Creating a Database Cluster <https://www.postgresql.org/docs/12/creating-cluster.html>`__.
   - `Starting the Database Server <https://www.postgresql.org/docs/12/server-start.html>`__.
   - :ref:`The database topic <topics:database>`.

To manually create the database for AiiDA, you need to run the program ``psql`` to interact with postgres.
On most operating systems, you need to do so as the ``postgres`` user that was created upon installing the software.
To assume the role of ``postgres`` run as root:

.. code-block:: console

   $ su - postgres

(or, equivalently, type ``sudo su - postgres``, depending on your distribution) and launch the postgres program:

.. code-block:: console

   $ psql

Create a new database user account for AiiDA by running:

.. code-block:: sql

   CREATE USER aiida WITH PASSWORD '<password>';

replacing ``<password>`` with a password of your choice.

You will need to provide the password again when you configure AiiDA to use this database through ``verdi setup``.
If you want to change the password you just created use the command:

.. code-block:: sql

   ALTER USER aiida PASSWORD '<password>';

Next, we create the database itself. We enforce the UTF-8 encoding and specific locales:

.. code-block:: sql

   CREATE DATABASE aiidadb OWNER aiida ENCODING 'UTF8' LC_COLLATE='en_US.UTF-8' LC_CTYPE='en_US.UTF-8' TEMPLATE=template0;

and grant all privileges on this DB to the previously-created ``aiida`` user:

.. code-block:: sql

   GRANT ALL PRIVILEGES ON DATABASE aiidadb to aiida;

You have now created a database for AiiDA and you can close the postgres shell by typing ``\q``.
To test if the database was created successfully, you can run the following command as a regular user in a bash terminal:

.. code-block:: console

   $ psql -h localhost -d aiidadb -U aiida -W

and type the password you inserted before, when prompted.
If everything worked well, you should get no error and see the prompt of the ``psql`` shell.

If you use the same names as in the example commands above, then during the ``verdi setup`` phase the following parameters will apply to the newly created database:

.. code-block:: console

   $ Database engine: postgresql_psycopg2
   $ Database host: localhost
   $ Database port: 5432
   $ AiiDA Database name: aiidadb
   $ AiiDA Database user: aiida
   $ AiiDA Database password: <password>

.. admonition:: Don't forget to backup your database!
   :class: tip title-icon-tip

   See the :ref:`Database backup how-to <how-to:installation:backup:postgresql>`), and :ref:`how to move your database <how-to:installation:performance>`.

Database setup using 'peer' authentication
------------------------------------------

On Ubuntu Linux, the default PostgreSQL setup is configured to use ``peer`` authentication, which allows password-less login via local Unix sockets.
In this mode, PostgreSQL compares the Unix user connecting to the socket with its own database of users and allows a connection if a matching user exists.

.. note::

    This is an alternative route to set up your database - the standard approach will work on Ubuntu just as well.

Below we are going to take advantage of the command-line utilities shipped on Ubuntu to simplify creating users and databases compared to issuing the SQL commands directly.

Assume the role of ``postgres``:

.. code-block:: console

   $ sudo su postgres

Create a database user with the **same name** as the UNIX user who will be running AiiDA (usually your login name):

.. code-block:: console

   $ createuser <username>

replacing ``<username>`` with your username.

Next, create the database itself with your user as the owner:

.. code-block:: console

   $ createdb -O <username> aiidadb

Exit the shell to go back to your login user.
To test if the database was created successfully, try:

.. code-block:: console

   $ psql aiidadb

During the ``verdi setup`` phase, use ``!`` to leave host empty and specify your Unix user name as the *AiiDA Database user*.:

.. code-block:: console

   $ Database engine: postgresql_psycopg2
   $ Database host: !
   $ Database port: 5432
   $ AiiDA Database name: aiidadb
   $ AiiDA Database user: <username>
   $ AiiDA Database password: ""


RabbitMQ configuration
----------------------

In most normal setups, RabbitMQ will be installed and run as a service on the same machine that hosts AiiDA itself.
In that case, using the default configuration proposed during a profile setup will work just fine.
However, when the installation of RabbitMQ is not standard, for example it runs on a different port, or even runs on a completely different machine, all relevant connection details can be configured with ``verdi setup``.

The following parameters can be configured:

+--------------+---------------------------+---------------+-------------------------------------------------------------------------------------------------------------------------+
| Parameter    | Option                    | Default       | Explanation                                                                                                             |
+==============+===========================+===============+=========================================================================================================================+
| Protocol     | ``--broker-protocol``     | ``amqp``      | The protocol to use, can be either ``amqp`` or ``amqps`` for SSL enabled connections.                                   |
+--------------+---------------------------+---------------+-------------------------------------------------------------------------------------------------------------------------+
| Username     | ``--broker-username``     | ``guest``     | The username with which to connect. The ``guest`` account is available and usable with a default RabbitMQ installation. |
+--------------+---------------------------+---------------+-------------------------------------------------------------------------------------------------------------------------+
| Password     | ``--broker-password``     | ``guest``     | The password with which to connect. The ``guest`` account is available and usable with a default RabbitMQ installation. |
+--------------+---------------------------+---------------+-------------------------------------------------------------------------------------------------------------------------+
| Host         | ``--broker-host``         | ``127.0.0.1`` | The hostname of the RabbitMQ server.                                                                                    |
+--------------+---------------------------+---------------+-------------------------------------------------------------------------------------------------------------------------+
| Port         | ``--broker-port``         | ``5672``      | The port to which the server listens.                                                                                   |
+--------------+---------------------------+---------------+-------------------------------------------------------------------------------------------------------------------------+
| Virtual host | ``--broker-virtual-host`` | ``''``        | Optional virtual host. Should not contain the leading forward slash, this will be added automatically by AiiDA.         |
+--------------+---------------------------+---------------+-------------------------------------------------------------------------------------------------------------------------+


verdi setup
-----------

After the database has been created, do:

.. code-block:: console

    $ verdi setup --profile <profile_name>

where `<profile_name>` is a profile name of your choosing.
The ``verdi setup`` command will guide you through the setup process through a series of prompts.

The first information asked is your email, which will be used to associate the calculations to you.
In AiiDA, the email is your username, and acts as a unique identifier when importing/exporting data from AiiDA.

.. note::

   The password, in the current version of AiiDA, is not used (it will be used only in the REST API and in the web interface).
   If you leave the field empty, no password will be set and no access will be granted to the user via the REST API and the web interface.

Then, the following prompts will help you configure the database. Typical settings are:

.. code-block:: console

   $ Default user email: richard.wagner@leipzig.de
   $ Database engine: postgresql_psycopg2
   $ PostgreSQL host: localhost
   $ PostgreSQL port: 5432
   $ AiiDA Database name: aiida_dev
   $ AiiDA Database user: aiida
   $ AiiDA Database password: <password>
   $ AiiDA repository directory: /home/wagner/.aiida/repository/
   [...]
   Configuring a new user with email 'richard.wagner@leipzig.de'
   $ First name: Richard
   $ Last name: Wagner
   $ Institution: BRUHL, LEIPZIG
   $ The user has no password, do you want to set one? [y/N] y
   $ Insert the new password:
   $ Insert the new password (again):

.. admonition:: Don't forget to backup your data!
   :class: tip title-icon-tip

   See the :ref:`installation backup how-to <how-to:installation:backup>`.

.. _intro:install:start_daemon:

Managing the daemon
-------------------

The AiiDA daemon process runs in the background and takes care of processing your submitted calculations and workflows, checking their status, retrieving their results once they are finished and storing them in the AiiDA database.

The AiiDA daemon is controlled using three simple commands:

 * ``verdi daemon start``: start the daemon
 * ``verdi daemon status``: check the status of the daemon
 * ``verdi daemon stop``: stop the daemon

.. note::

    While operational, the daemon logs its activity to a file in ``~/.aiida/daemon/log/`` (or, more generally, ``$AIIDA_PATH/.aiida/daemon/log``).
    Get the latest log messages via ``verdi daemon logshow``.

.. _intro:install:jupyter:

Using AiiDA in Jupyter
----------------------

`Jupyter <http://jupyter.org>`_ is an open-source web application that allows you to create in-browser notebooks containing live code, visualizations and formatted text.

Originally born out of the iPython project, it now supports code written in many languages and customized iPython kernels.

If you didn't already install AiiDA with the ``[notebook]`` option (during ``pip install``), run ``pip install jupyter`` **inside** the virtualenv, and then run **from within the virtualenv**:

.. code-block:: console

    $ jupyter notebook

This will open a tab in your browser. Click on ``New -> Python`` and type:

.. code-block:: python

   import aiida

followed by ``Shift-Enter``. If no exception is thrown, you can use AiiDA in Jupyter.

If you want to set the same environment as in a ``verdi shell``,
add the following code to a ``.py`` file (create one if there isn't any) in ``<home_folder>/.ipython/profile_default/startup/``:

.. code-block:: python

    try:
        import aiida
    except ImportError:
        pass
    else:
        import IPython
        from aiida.tools.ipython.ipython_magics import load_ipython_extension

        # Get the current Ipython session
        ipython = IPython.get_ipython()

        # Register the line magic
        load_ipython_extension(ipython)

This file will be executed when the ipython kernel starts up and enable the line magic ``%aiida``.
Alternatively, if you have a ``aiida-core`` repository checked out locally,
you can just copy the file ``<aiida-core>/aiida/tools/ipython/aiida_magic_register.py`` to the same folder.
The current ipython profile folder can be located using:

.. code-block:: console

   $ ipython locate profile

After this, if you open a Jupyter notebook as explained above and type in a cell:

.. code-block:: ipython

   %aiida

followed by ``Shift-Enter``. You should receive the message "Loaded AiiDA DB environment."
This line magic should also be enabled in standard ipython shells.
