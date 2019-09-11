===================
Publishing a plugin
===================

.. _plugins.get_listed:

1. Choose a name
----------------

The naming convention for AiiDA plugins is ``aiida-mycode`` for the plugin
and ``aiida_mycode`` for the corresponding python package, leading to the
following folder structure::

   aiida-mycode/
      aiida_mycode/
         __init__.py

This marks your plugin as an AiiDA package and makes it easy to find on package indices like `PyPI`_.

**Note:** Python packages cannot contain dashes, thus the underscore.


2. Get Your Plugin Listed
-------------------------

AiiDA plugins should be listed on the AiiDA plugin `registry`_ to
avoid name-clashes with other plugins.

If you wish to get your plugin listed on the official registry for AiiDA
plugins, you will provide the following keyword arguments as key-value pairs in
a ``setup.json`` or ``setup.yaml``. It is recommended to have setup.py
read the keyword arguments from that file::

   aiida-myplugin/
      aiida_myplugin/
         ...
      setup.py
      setup.json       # or setup.yaml

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

Now, fork the plugin `registry`_ repository, fill in your plugin's information
in the same fashion as the plugins already registered, and create a pull
request. The registry will allow users to discover your plugin using ``verdi
plugin search`` (note: the latter verdi command is not yet implemented in
AiiDA).

3. Get Your Plugin On PyPI
--------------------------

For packaging and distributing AiiDA plugins, we recommend to follow existing
`guidelines for packaging python <packaging>`_,
which include making the plugin available on the `python package index <PyPI>`_.
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

Note: In principle, ``aiida-compute`` could contain and install multiple packages.

Incidentally a distribution can contain and install more than one package at a time.

The most user-friendly way to distribute a package is to create such a
distribution and uploading it to `PyPI`_. Users then can simply install the
package(s) by running ``pip <distribution-name>``.


.. _pypi: https://pypi.python.org
.. _packaging: https://packaging.python.org/distributing/#configuring-your-project
.. _setuptools: https://setuptools.readthedocs.io
.. _registry: https://github.com/aiidateam/aiida-registry
