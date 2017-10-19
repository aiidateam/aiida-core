==========
Quickstart
==========

You have a code and would like to use it from AiiDA?
You need a special data type, parser, scheduler, ... that is not available?
Then you'll need to write an **AiiDA plugin**.

Let's walk through the steps for creating a new plugin ``aiida-compute``.

 0. You know how to :ref:`install an aiida plugin <plugins>`

 1. Check on the `aiida plugin registry <https://aiidateam.github.io/aiida-registry/>`_
    that the plugin name is still available

 #. Download the AiiDA plugin template::

        wget https://github.com/aiidateam/aiida-plugin-template/archive/master.zip
        unzip master.zip
        cd aiida-plugin-template

 #. Replace the name ``aiida-plugin-template`` by ``aiida-compute``::

        mv aiida_plugin_template aiida_compute
        sed -i .bak 's/aiida_plugin_template/aiida_compute/g' README.md setup.json examples/*.py
        sed -i .bak 's/aiida-plugin-template/aiida-compute/g' README.md setup.json
        sed -i .bak 's/template\./compute./g' setup.json

        # Optional: put your plugin under version control
        git init && git add *
        git commit -m "start development"

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

 #. Now you might want to check that the plugin import is working correctly::

        workon <name_of_your_virtualenv>
        pip install -e .
        cd
        ipython

 #. and import your plugin::

        import aiida-compute

 #. When you update the plugin to a new version make sure to update the version number both in
    ``setup.json`` and in ``<your_plugin>/__init__.py``




OLD STUFF BELOW



If you are not familiar with ``setuptools`` and have never configured a python package for distribution you might want to read `packaging.python.org <packaging>`_ and possibly `setuptools.readthedocs.io <setuptools>`_ at this point.

Pay special attention to the entry points. A list of entry point groups and their intended use can be found in :ref:`plugins.entry_points`.

The simplest thing is to include just the following code in the
``setup.py`` file::

  from setuptools import setup, find_packages
  import json

  if __name__ == '__main__':
      with open('setup.json', 'r') as info:
          kwargs = json.load(info)
      setup(
          include_package_data=True,
          packages=find_packages(),
          **kwargs
      )

and then include all the information in a json file (in the same
directory tree) called ``setup.json``.

An example/template ``setup.json`` file (that of course needs to be properly adapted) follows::

   {
       "version": "1.0.0",
       "name": "aiida_myplugin",
       "url": "http://www.example.com",
       "license": "MIT License",
       "author": "Author names",
       "author_email": "the_email@example.com",
       "description": "A long description of what this plugin is and does",
       "classifiers": [
           "License :: OSI Approved :: MIT License",
           "Programming Language :: Python :: 2.7",
           "Development Status :: 4 - Beta"
       ],
       "install_requires": [
           "aiida[ssh]"
       ],
       "entry_points": {
           "aiida.calculations": [
               "myplugin.plug1 = aiida_myplugin.calculations.plug1:Plug1Calculation",
               "myplugin.plug2 = aiida_myplugin.calculations.plug2:Plug1Calculation"
            ],
           "aiida.parsers": [
               "myplugin.plug1 = aiida_myplugin.parsers.plug1:Plug1Parser",
               "myplugin.plug2 = aiida_myplugin.parsers.plug2:Plug1Parser"

           ]
       }
   }

If you are converting a plugin from the old system to new new system, the name of your entry points must correspond to where your plugin module was installed inside the AiiDA package. *Otherwise, your plugin will not be backwards compatible*. For example, if you were using a calculation as::

   from aiida.orm.calculation.job.myplugin.mycalc import MycalcCalculation
   # or
   CalculationFactory('myplugin.mycalc')

Then in ``setup.py``::

   setup(
      ...,
      entry_points: {
         'aiida.calculations': [
            'myplugin.mycalc = aiida_myplugin.calculations.mycalc:MycalcCalculation'
         ],
         ...
      },
      ...
   )
   
As you see, the name of the entry point matches the argument to the factory method.

3. Adjust import statements
---------------------------

If you haven't done so already, now would be a good time to search and replace any import statements that refer to the old locations of your modules inside AiiDA. We recommend to change them to absolute imports from your top-level package:

old::

   from aiida.tools.codespecific.myplugin.thistool import this_convenience_func

new::
   
   from aiida_myplugin.tools.thistool import this_convenience_func

4. Get Your Plugin Listed
-------------------------

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
