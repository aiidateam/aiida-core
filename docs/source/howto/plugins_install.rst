.. _how-to:plugins-install:

**********************
How to install plugins
**********************

The functionality of AiiDA can be extended through plugins.
There are various types of functionality that can be extended, such as new :ref:`data types<topics:data_types:plugin>`, :ref:`calculation plugins<how-to:plugin-codes>` and much more.
Multiple plugins can be bundled together and distributed in a :ref:`plugin package<how-to:plugins-develop>`.
The `AiiDA plugin registry <https://aiidateam.github.io/aiida-registry>`_ gives an overview of public plugin packages.

Installing an AiiDA plugin package is done with `pip <https://pypi.org/project/pip/>`_.
If the package is distributed via the `Python Package Index (PyPI) <https://pypi.org/search/?q=aiida>`_ you can install it as follows:

.. code-block:: console

    $ pip install aiida-plugin-name

A package can also be installed from the source code.
For example, if the code is available through a Git repository:

.. code-block:: console

    $ git clone https://github.com/aiidateam/aiida-diff
    $ cd aiida-diff
    $ pip install .

.. important::

    Each time when you install a new plugin package you should make sure to run the following command to let AiiDA know about the new plugins that come with it:

    .. code-block:: console

        $ reentry scan

    If you forget to run this command, AiiDA will not be able to find the plugins.
    The reentry cache can also be updated from python when access to the commandline is not available (e.g. in Jupyter notebooks).

    .. code-block:: python

        from reentry import manager
        manager.scan(group_re='aiida')

.. warning::

    If your daemon was running when installing or updating a plugin package, make sure to restart it with the ``--reset`` flag for changes to take effect:

    .. code-block:: console

        $ verdi daemon restart --reset

    This needs to be done *after* the command ``reentry scan`` is called.

To verify which plugins are currently installed, use the command:

.. code-block:: console

    $ verdi plugin list

It will list the various categories of functionality that can be extended through plugins.
To see which plugins are installed for any of these categories, pass the category name as an argument, e.g.:

.. code-block:: console

    $ verdi plugin list aiida.data
