====================
Documenting a plugin
====================

The

 #. Modify ``docs/source/conf.py`` template configuration file inserting the information about your plugin:

        - Replace ``aiida_plugin_template`` by ``aiida-compute``::

                import aiida-compute

        - Modify ``intersphinx_mapping`` adding any other packages that are needed by your plugin

        - Update general information about the project::

                project = u'aiida-compute'
                copyright_first_year = 2017
                copyright_owners = "My Institution, Country"

        - Update ``release = aiida_plugin_template.__version__`` with the name of your plugin::

                release = aiida-compute.__version__

        - Do the same with::

                html_use_opensearch = 'http://aiida-compute.readthedocs.io'
                htmlhelp_basename = 'aiida-compute-doc'

 #. Modify ``docs/source/module_guide/calculations.rst``, ``docs/source/module_guide/data.rst``,
    ``docs/source/module_guide/parsers.rst`` substituting them with any other module you might have

 #. Update ``docs/source/module_guide/index.rst`` accordingly, listing the modules provided with the plugin

 #. Modify ``docs/source/user_guide/get_started.rst`` and ``docs/source/user_guide/tutorial.rst``
    to write the ReadTheDocs documentation about your plugin

 #. If you change the names of the ReadTheDocs sections or add a new one make sure to update
    ``docs/source/user_guide/index.rst`` accordingly

 #. Make sure that AiiDA docs dependencies ``Sphinx`` and ``sphinx_rtd_theme`` are installed

 #. Generate the ReadTheDocs page::

        cd docs
        make

 #. When you update the plugin to a new version make sure to update the version number both in
    ``setup.json`` and in ``<your_plugin>/__init__.py``

