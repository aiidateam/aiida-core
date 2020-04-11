.. _plugins:

***************
Install Plugins
***************

While the ``aiida-core`` package provides the workflow engine and database model, it relies on *plugins* for connecting to specific simulation codes.

Search for AiiDA plugin packages on the `AiiDA plugin registry <https://aiidateam.github.io/aiida-registry>`_.
If a plugin package for your code does not yet exist, you may need to :ref:`write one <plugin_development>`.

Most plugin packages are hosted on the `Python Package Index <https://pypi.org/search/?q=aiida>`_ and can be installed as follows::

    pip install aiida-diff  # install 'aiida-diff' plugin from PyPI
    reentry scan -r aiida   # notify aiida of new entry points

If no PyPI package is available for a plugin, you can install the plugin package directly from a source code repository, e.g.::

    git clone https://github.com/aiidateam/aiida-diff
    pip install aiida-diff  # install 'aiida-diff' plugin from local folder
    reentry scan -r aiida   # notify aiida of new entry points

After installing new plugin packages, update the reentry cache using ``reentry scan`` and **restart the daemon**  using ``verdi daemon restart``.

.. note::
    The reentry cache can also be updated from python when access to the commandline is not available (e.g. in jupyter notebooks).

    .. code-block:: python

        from reentry import manager
        manager.scan(group_re='aiida')

.. note::
    What does ``pip install aiida-diff`` do?

    * resolves and installs the dependencies on other python packages
    * creates a folder ``aiida_diff.egg-info/`` with metadata about the package
    * if the ``-e`` option is given, creates a symbolic link from the python package
      search path to the ``aiida-diff`` directory and puts the ``.egg-info``
      folder there.
      Changes to the **source code** will be picked up by python without reinstalling (when restarting the interpreter),
      but changes to the **metadata** will not.

    For further details, see the Python `packaging user guide`_.

.. _packaging user guide: https://packaging.python.org/distributing/#configuring-your-project

