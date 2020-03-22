===========================
Publishing a plugin package
===========================

.. _plugins.get_listed:

1. Choose a name
----------------

The naming convention for AiiDA plugin packages is ``aiida-mycode`` for the plugin distribution on `PyPI`_ and ``aiida_mycode`` for the corresponding python package, leading to the following folder structure::

   aiida-mycode/
      aiida_mycode/
         __init__.py

**Note:** Python packages cannot contain dashes, thus the underscore.


2. Add to plugin registry
-------------------------

AiiDA plugin packages should be listed on the AiiDA plugin `registry`_ to avoid name-clashes with other plugins.

If you wish to get your plugin package listed on the official plugin registry, please provide the following keyword arguments as key-value pairs in a ``setup.json`` or ``setup.yaml`` file.

* ``name``
* ``author``
* ``author_email``
* ``description``
* ``url``
* ``license``
* ``classifiers`` (optional)
* ``version``
* ``install_requires``
* ``entry_points``
* ``scripts`` (optional)

It is recommended to have your ``setup.py`` file simply read the keyword arguments from the ``setup.json``::

   aiida-myplugin/
      aiida_myplugin/
         ...
      setup.py
      setup.json       # or setup.yaml

Now, fork the plugin `registry`_ repository, fill in the information for your plugin package, and create a pull request.

3. Upload to PyPI
-----------------

For packaging and distributing AiiDA plugins, we recommend to follow existing `guidelines for packaging python <packaging>`_, which include making the plugin available on the `python package index <PyPI>`_.
This makes it possible for users to simply ``pip install aiida-myplugin``.

Our suggested layout::

   aiida-compute/       top-folder containing you package and additional files
      aiida_compute/    The package that is to be installed
         __init__.py
         ...
      MANIFEST.in       (optional) lists non-python files to be installed
      README.rst        (optional) description to be used by github etc and PyPI
      setup.py          installation script
      setup.json        contains requirements, metainformation, etc

Note: In principle, the ``aiida-compute`` folder could contain and install multiple python packages.
We recommend against this practice, unless there are good reasons to keep multiple packages in the same repository.

.. _pypi: https://pypi.python.org
.. _packaging: https://packaging.python.org/distributing/#configuring-your-project
.. _setuptools: https://setuptools.readthedocs.io
.. _registry: https://github.com/aiidateam/aiida-registry
