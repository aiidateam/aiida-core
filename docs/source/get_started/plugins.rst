.. _plugins:

*******
Plugins
*******

AiiDA plug-ins are input generators and output parsers, enabling the
integration of codes into AiiDA calculations and workflows.

The plug-ins are not meant to completely automatize the calculation of physical properties. An underlying knowledge of how each code works, which flags it requires, etc. is still required. A total automatization, if desired, has to be implemented at the level of a workflow.

Plugins live in different repositories than AiiDA.
You can find a list of existing plugins on the `AiiDA website <http://www.aiida.net/plugins/>`_ or on the
``aiida-registry`` (check the `JSON version <https://github.com/aiidateam/aiida-registry/blob/master/plugins.json>`_
or the `human-readable version <https://aiidateam.github.io/aiida-registry/>`_), the official location to register
and list plugins.


Installing plugins
==================

The plugins available for AiiDA are listed on the
`AiiDA homepage <http://www.aiida.net/plugins/>`_

For a plugin ``aiida-diff`` hosted on `PyPI <https://pypi.python.org/>`_,
simply do::

    pip install aiida-diff
    reentry scan -r aiida   # notify aiida of new entry points

In case there is no PyPI package available, you can install 
the plugin directly from a source code repository, e.g.::

    git clone https://github.com/aiidateam/aiida-diff
    pip install aiida-diff
    reentry scan -r aiida

**Note:** Instead of updating the reentry cache via ``reentry scan -r aiida``,
the same can be achieved from  python:

.. code-block:: python

    from reentry import manager
    manager.scan(group_re='aiida')

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
