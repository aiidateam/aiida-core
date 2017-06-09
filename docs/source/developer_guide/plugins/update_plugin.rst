Updating an Existing Plugin (or creating a new one)
===================================================

This section will walk you through the steps needed to create a python package containing your plugin, which can then be easily developed, distributed via a version control system (e.g., GIT) and updated separately from AiiDA.

1. Create a Distribution
------------------------

First, choose a name under which your plugin will be distributed and potentially uploaded to `pypi.python.org <pypi>`_ (PyPI). The recommended naming convention is::
   
   aiida-<plugin name>/

where <plugin name> should be replaced by the name you have given to the folders containing your plugin modules. The reasons for this convention is to avoid name clashes with other python package distributions, marking it clearly as a AiiDA plugin for ``<plugin name>`` rather than a python package for ``<plugin name>`` itself (e.g. in the case ``<plugin name>`` is a simulation package), as well as making it easy to find on PyPI.

It is important to ensure that the name is not taken by another plugin yet. To do so, visit the `registry`_. If you wish to secure the name you can register your plugin already at this point, just follow the instructions in section :ref:`step_4` and leave all information that you do not have yet empty.

Next, create inside this folder a python package, leading to this structure::

   aiida-<plugin name>/
      aiida_<plugin_name>/
         __init__.py

Note that python packages cannot contain dashes, and therefore we use an underscore.

Now we are ready to move the plugin modules into the package. You are free to use any valid python package structure you like, however we recommend to leave each plugin class in it's own module and to group plugin types in subpackages, see the following example.

Example
^^^^^^^

Old plugin system::

   aiida/
      orm/
         calculation/
            job/
               myplugin/
                  __init__.py
                  mycalc.py
                  myothercalc.py
      parsers/
         plugins/
            myplugin/
               __init__.py
               myparser.py
               myotherparser.py
      data/
         myplugin/
            __init__.py
            mydata.py
      tools/
         codespecific/
            myplugin/
               __init__.py
               ...

Turns into::
   
   aiida-myplugin/
      aiida_myplugin/
         __init__.py
         calculations/
            __init__.py
            mycalc.py
            myothercalc.py
         parsers/
            __init__.py
            myparser.py
            myotherparser.py
         data/
            __init__.py
            mydata.py
         tools/
            __init__.py
            ...

2. Create ``setup.py``
----------------------

::
   
   aiida-myplugin/
      aiida_myplugin/
         ...
      setup.py

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

.. _step_4:

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
