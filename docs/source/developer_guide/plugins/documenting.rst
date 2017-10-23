====================
Documenting a plugin
====================

The `aiida plugin template`_ already comes with
a template for documentation that just needs to be adjusted to your needs.
In the following we, again, assume you wrote a plugin named ``aiida-compute``:


 #. Modify ``docs/source/conf.py`` template configuration file inserting the information about your plugin:

        - Replace ``aiida_plugin_template`` by ``aiida_compute``

        - Replace ``aiida-plugin-template`` by ``aiida-compute``

        - Modify ``intersphinx_mapping`` adding any other packages that are needed by your plugin

        - Update general information about the project::

                project = u'aiida-compute'
                copyright_first_year = 2017
                copyright_owners = "My Institution, Country"

 #. Populate or delete the individual documentation pages::

        docs/source/module_guide/calculations.rst
        docs/source/module_guide/data.rst
        docs/source/module_guide/parsers.rst
        docs/source/user_guide/get_started.rst
        docs/source/user_guide/tutorial.rst

 #. Update the indices accordingly::

        docs/source/module_guide/index.rst
        docs/source/user_guide/index.rst
    
 #. Make sure that AiiDA docs dependencies ``sphinx`` and ``sphinx_rtd_theme`` are installed

 #. Generate the ReadTheDocs page::

        cd docs
        make

 #. When you update the plugin to a new version make sure to update the version number both in
    ``setup.json`` and in ``aiida_compute/__init__.py``

.. _aiida plugin template: https://github.com/aiidateam/aiida-plugin-template
