.. _aiida-sphinxext:

AiiDA Sphinx extension
++++++++++++++++++++++

AiiDA defines a Sphinx extension to simplify documenting some of its features. To use this extension, you need to add  ``aiida.sphinxext`` to the ``extensions`` list in your Sphinx ``conf.py`` file.

WorkChain directive
-------------------

The following directive can be used to auto-document AiiDA workchains:

::

    .. aiida-workchain:: MyWorkChain
        :module: my_plugin
        :hide-nondb-inputs:

The argument ``MyWorkChain`` is the name of the workchain, and ``:module:`` is the module from which it can be imported. By default, the inputs which are not stored in the database are also shown. This can be disabled by passing the ``:hide-unstored-inputs:`` flag.

The ``aiida-workchain`` directive is also hooked into ``sphinx.ext.autodoc``, so if you use the corresponding directives (``automodule``, ``autoclass``), it will automatically use the ``aiida-workchain`` command for ``WorkChain`` classes.
