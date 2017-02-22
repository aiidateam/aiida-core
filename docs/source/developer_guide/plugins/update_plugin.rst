Updating an Existing Plugin
===========================

This section will take you through the steps needed to create a python package containing your plugin, which can then be easily developped, version controlled distributed and updated separately from aiida.

1. Create a Distribution
------------------------

First, choose a name under which your plugin will be distributed and potentially uploaded to `pypi.python.org <pypi>`_ (PyPI). The recommended naming convention is::
   
   aiida-<plugin name>/

where <plugin name> should be replaced by the name you have given to the folders containing your plugin modules. The reasons for this convention is to avoid name clashes with other python package distributions, as well as making it easy to find on the PyPI

Next, create inside this folder a python package, leading to this structure::

   aiida-<plugin name>/
      aiida_<plugin_name>/
         __init__.py

Note that python packages cannot contain dashes, and therefore we use an underscore.

Now we are ready to move the plugin modules into the package. You are free to use any valid python package structure you like, however we recommend to leave each plugin class in it's own module and to group plugin types in subpackages, see the following example.

Example
^^^^^^^

Current plugin::

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

If you are not familiar with ``setuptools`` and have never configured a python package for distribution you will want to read `packaging.python.org <packaging>`_ and possibly `setuptools.readthedocs.io <setuptools>`_

Pay special attention to the entry points. A list of entry point groups and their intended use can be found in :ref:`plugins.entry_points`.
The name of your entry points must correspond to where your plugin module was installed inside the aiida package. *Otherwise your plugin will not be backwards compatible*

Examples:
   
If you were using a calculation as::

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

If you haven't done so already, now would be a good time to search and replace any import statements that refer to the old locations of your modules inside aiida. We recommend to change them to absolute imports from your top-level package:

old::

   from aiida.tools.codespecific.myplugin.thistool import this_convenience_func

new::
   
   from aiida_myplugin.tools.thistool import this_convenience_func

4. Get Your Plugin Listed
-------------------------

If you wish to get your plugin listed on the official registry of endorsed plugins, you will provide the following keyword arguments as key-value pairs in a setup.json or setup.yaml file alongside. It is recommended to have setup.py read the keyword arguments from that file::

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
* ``scripts``

Now, fork `registry`_, fill in your plugin's information in the same fashion as the plugins already registered, and create a pull request. The registry will allow users to discover your plugin using ``verdi plugin search``.

.. _pypi: https://pypi.python.org
.. _packaging: https://packaging.python.org/distributing/#configuring-your-project
.. _setuptools: https://setuptools.readthedocs.io
.. _registry: https://github.com/DropD/aiida-registry
