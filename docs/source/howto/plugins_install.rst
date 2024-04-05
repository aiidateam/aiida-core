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

.. warning::

    If you installed or updated a plugin package while your daemon was running, be sure to restart it so that the changes take effect:

    .. code-block:: console

        $ verdi daemon restart

To verify which plugins are currently installed, use the command:

.. code-block:: console

    $ verdi plugin list

It will list the various categories of functionality that can be extended through plugins.
To see which plugins are installed for any of these categories, pass the category name as an argument, e.g.:

.. code-block:: console

    $ verdi plugin list aiida.data
