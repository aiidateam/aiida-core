===========================
Documenting plugin packages
===========================

If you used the `AiiDA plugin cutter`_,  your plugin package already comes with a basic
documentation that just needs to be adjusted to your needs.

 #. Install the ``docs`` extra::

        pip install -e .[docs]

 #. Populate, delete, or add to the individual documentation pages::

        docs/source/index.rst
        docs/source/module_guide/index.rst
        docs/source/user_guide/index.rst
        docs/source/user_guide/get_started.rst
        docs/source/user_guide/tutorial.rst

 #. Use `Sphinx`_ to generate the html documentation::

        cd docs
        make

    Check the result by opening ``build/html/index.html`` in your browser.

 #. Host your documentation online on ReadTheDocs_.
    Simply sign up and import your project.  Make sure to add the path to the
    requirements file ``docs/requirements_for_rtd.txt`` and the Python
    configuration file ``docs/source/conf.py`` in Admin => Advanced settings.

Note: When updating the plugin package to a new version, remember to update the
version number both in ``setup.json`` and ``aiida_mycode/__init__.py``.

.. _aiida plugin cutter: https://github.com/aiidateam/aiida-plugin-cutter
.. _ReadTheDocs: http://readthedocs.org/
.. _sphinx: http://www.sphinx-doc.org/en/master/


.. _aiida-sphinxext:

Sphinx extension
++++++++++++++++

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
