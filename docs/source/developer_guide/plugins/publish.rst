===================
Publishing a plugin
===================

AiiDA plugins should be `registered <registry>`_ to avoid name-clashes with other plugins. Visiting the registry to see if the desired functionality is already being provided is a good idea as well.

For packaging and distributing AiiDA plugins, we recommend to follow existing
`guidelines for packaging python <packaging>`_,
which include making the plugin available on the `python package index <PyPI>`_.
This makes it possible for users to simply ``pip install aiida-myplugin``.

Example::

   distribution/        Distribution enclosing package and additional files
      package/          The package that the distribution installs
         __init__.py
         ...
      MANIFEST.in       (optional) lists non-python files to be installed
      README.rst        (optional) description to be used by github etc and PyPI
      setup.py          (required) contains requirements, metainformation, etc

Incidentally a distribution can contain and install more than one package at a time.

The most user-friendly way to distribute a package is to create such a distribution and uploading it to `PyPI`_. Users then can simply install the package(s) by running ``pip <distribution-name>``.

Installing a Package
--------------------

What happens when ``pip`` is used to install a package is explained in detail in `the python packaging user guide <packaging>`_. However it is worth summarizing some points here.

* the dependencies on other python packages as specified in ``setup.py`` are automatically resolved and installed;
* a folder ``<distribution-name>.egg-info/`` is created, containing metadata about the distribution;
* if the ``-e`` option is given, a symbolic link is put into the python package search path, pointing to the distribution top level directory. This is where the ``.egg-info`` folder gets created. Changes to the source code will be picked up by python without reinstalling, however changes to the distribution metadata will not.


.. _plugins.get_listed:

Get Your Plugin Listed
------------------------

This step is important to ensure that the name by which your plugin classes are loaded stays unique and unambiguous!

If you wish to get your plugin listed on the official registry for AiiDA plugins, you will provide the following keyword arguments as key-value pairs in a setup.json or setup.yaml file alongside. It is recommended to have setup.py read the keyword arguments from that file::

   aiida-myplugin/
      aiida_myplugin/
         ...
      setup.py
      setup.json | setup.yaml

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

Now, fork the plugin `registry`_ repository, fill in your plugin's information in the same fashion as the plugins already registered, and create a pull request. The registry will allow users to discover your plugin using ``verdi plugin search`` (note: the latter verdi command is not yet implemented in AiiDA).

.. _pypi: https://pypi.python.org
.. _packaging: https://packaging.python.org/distributing/#configuring-your-project
.. _setuptools: https://setuptools.readthedocs.io
.. _registry: https://github.com/aiidateam/aiida-registry
