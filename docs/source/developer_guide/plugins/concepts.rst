Important Concepts
==================

.. _plugins.concepts.python_package:

Python Packages
---------------

According to `the python documentation <packages>`_:

   Packages are a way of structuring Python's module namespace by using "dotted module names". For example the module name A.B designates a submodule named B in a package named A. [...]

The way that this behaviour is achieved in practice is by creating a folder structure like the following::

   package/             Top-level package (import package)
      __init__.py       Marks the folder as a package and contains initialization
      moduleA.py        module (from package import moduleA)
      subpackage/       subpackage (from package import subpackage)
         __init__.py
         moduleB.py     module (from package.subpackage import moduleB)
         ...

The page linked on top of this section contains a more detailed examples as well as more information on how to write and use packages.

.. _plugins.concepts.python_distro:

Python Distributions
--------------------

The python community widely uses the term 'package' for both a package in the sense of a collection of subpackages and modules, as well as all the additional files necessary for building and installing a package. More about distributing packages `here <packagin>`_.

In this documentation we will refer to the latter as a distribution when we wish to distinguish between the two concepts.

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

.. _plugins.concepts.entry_point:

Installing a Package
--------------------

What happens when ``pip`` is used to install a package is explained in detail in `the python packaging user guide <packaging>`_. However it is worth summarizing some points here.

* the dependencies on other python packages as specified in ``setup.py`` are automatically resolved and installed
* a folder ``<distribution-name>.egg-info/`` is created, containing metadata about the distribution
* if the '-e' option is given, a symbolic link is put into the python package search path, pointing to the distribution top level directory. This is where the ``.egg-info`` folder gets created. Changes to the source code will be picked up by python without reinstalling, however changes to the distribution metadate will not.

Entry Points
------------

The ``setuptools`` package to which ``pip`` is a frontend has a feature called `entry points`_. When a distribution which registers entry points is installed, the entry point specifications are written to a file inside the distribution's ``.egg-info`` folder. ``setuptools`` provides a package ``pkg_resources`` which can find these entry points by distribution, group and / or name and load the data structure to which it points. This is the way aiida finds and loads classes provided by plugins.

.. _packages: https://docs.python.org/2/tutorial/modules.html?highlight=package#packages
.. _PyPI: https://pypi.python.org/pypi
.. _packaging: https://packaging.python.org
.. _Entry points: https://setuptools.readthedocs.io/en/latest/setuptools.html#dynamic-discovery-of-services-and-plugins
