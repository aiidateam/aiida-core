.. _plugins:

==================
Installing plugins
==================

The plugins available for AiiDA are listed on the
`AiiDA homepage <http://www.aiida.net/plugins/>`_

For a plugin ``aiida-diff`` hosted on `PyPI <https://pypi.python.org/>`_,
simply do::

    pip install aiida-diff
    reentry scan -r aiida   # notify aiida of new entry points

In case there is no PyPI package available, you can install 
the plugin from the python source, e.g.::

    git clone https://github.com/aiidateam/aiida-diff
    pip install aiida-diff
    reentry scan -r aiida

Background
-----------

What does ``pip install aiida-diff`` do?

* resolves and installs the dependencies on other python packages as specified in ``setup.py``
* creates a folder ``aiida_diff.egg-info/`` with metadata about the package
* if the ``-e`` option is given, creates a symbolic link from the python package
  search path to the ``aiida-diff`` directory
  and puts the ``.egg-info`` folder there.
  Changes to the **source code** will be picked up by python without reinstalling, 
  but changes to the **metadata** in ``setup.json`` will not.

For further details, see the Python `packaging user guide`_.

.. _packaging user guide: https://packaging.python.org/distributing/#configuring-your-project
