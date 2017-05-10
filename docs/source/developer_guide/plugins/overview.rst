.. note:: intended for aiida >= 0.9

   Most of this information applies to `github.com/DropD/aiida_core/tree/ricoh-plugins` already

Overview
========

In this document the terms 'python package' and 'python distribution' are used to mean the following:

:ref:`python package <plugins.concepts.python_package>`
   a folder containing a file named ``__init__.py``.

:ref:`python distribution <plugins.concepts.python_distro>`
   a folder containing one or more python packages and a file named ``setup.py`` which tells `setuptools`_ what should be installed and how.

In the python community the term 'package' is often used to refer to distributions as well.

What a Plugin Is
----------------

In principle a plugin is a self contained collection of one or more python modules (".py files"), which provides a set of logically grouped extensions to AiiDA.

In technical terms, a plugin for AiiDA is a :ref:`python distribution <plugins.concepts.python_distro>` containing
one or more :ref:`python packages <plugins.concepts.python_package>`. It typically should have the aiida-core distribution as a requirement. It may import from the aiida package and provide :ref:`entry points <plugins.concepts.entry_point>` with extensions or workflows that integrate into aiida. 

It may also provide commandline or GUI applications based on AiiDA functionality.

All publicly available plugins should be registered at the `registry`_ to avoid name-clashes with other plugins. Visiting the registry to see if the desired functionality is already being provided is a good idea as well.

What a Plugin Can Do
--------------------

A plugin can do any of the following:

* depend on the aiida distribution (it normally would)
* depend on any amount of other plugins
* depend on any number of other python distributions, however the required versions must not clash with aiida's requirements
* Provide classes that can be used together with aiida's through a unified interface, types include

  - calculations 
  - parsers
  - data types
  - schedulers
  - transports
  - db importers
  - db exporters
  - subcommands to some ``verdi`` commands.
  - tests to be run using ``verdi devel tests``

  This is typically achieved by subclassing the according base class aiida provides for that purpose.
* install separate commandline and / or GUI executables

.. _plugins.maynot:

What a Plugin Cannot Do
-----------------------

It is important to keep in mind that, even though there is very little that is impossible to achieve, in the interest of a consistent and clear user experience there are things that should not be done.

Failure to comply with the points below will probably mean that your plugin will not be able to be listed as an officially endorsed plugin.

A plugin may / should not

* change the database schema AiiDA uses
* monkey patch anything within the ``aiida`` namespace nor the namespace itself
* use functionality of aiida or it's classes, which is marked as implementation detail, examples include functions, methods and classes starting with an underscore, '`_`'.
* circumvent data proveniency in any way

Should you find yourself tempted to do any of the above, you should post your usecase and reasoning as an issue on the `aiida repository <aiida_core>`_, simultaneously you may fork the repository, implement your changes directly and then create a pull request. You may also choose to ask on the aiida users mailing list for advice on how to proceed.

When to Contribute instead
--------------------------

In case it is unclear wether a certain functionality should be part of a plugin or of aiida itself, first ask yourself the following questions:

* is it impossible or very hard to implement as a separate package?
* would implementing it as a plugin involve any of the points listed in :ref:`plugins.maynot`?

If you answered any of those questions with yes, we strongly encourage you to contribute to `aiida_core`_ instead.

* would most users potentially profit from this functionality?
* would many plugins profit from this functionality?

   If yes, consider developing as a plugin and then open an issue on `aiida_core`_, describing the functionality, why you think it should be in the main distribution, and linking to the repository for your plugin. We will then advise you on how to proceed.

If any of the above applies to only part of a planned plugin, please consider splitting them into a separate plugin (or contribution).

.. _setuptools: https://setuptools.readthedocs.io/en/latest/
.. _aiida_core: https://github.com/aiidateam/aiida_core
.. _registry: https://github.com/aiidateam/aiida-registry
