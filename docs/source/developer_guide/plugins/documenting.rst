====================
Documenting a plugin
====================

If you used the `AiiDA plugin cutter`_,  your plugin already comes with a basic
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

Note: When updating the plugin to a new version, remember to update the
version number both in ``setup.json`` and ``aiida_mycode/__init__.py``.

.. _aiida plugin cutter: https://github.com/aiidateam/aiida-plugin-cutter
.. _ReadTheDocs: http://readthedocs.org/
.. _sphinx: http://www.sphinx-doc.org/en/master/
