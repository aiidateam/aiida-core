Updating an Existing Plugin
============================

This document describes the process of updating an AiiDA plugin written using
the old plugin system (pre AiiDA version 0.8) to the current plugin system.

Once the update is complete, make sure to :ref:`get your plugin listed <plugins.get_listed>`.

Folder structure
-----------------

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

Entry points
-------------

If you are converting a plugin from the old system to new new system, the name
of your entry points must correspond to where your plugin module was installed
inside the AiiDA package. *Otherwise, your plugin will not be backwards
compatible*. For example, if you were using a calculation as::

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

import statements
------------------

If you haven't done so already, now would be a good time to search and replace
any import statements that refer to the old locations of your modules inside
AiiDA. We recommend to change them to absolute imports from your top-level
package:

old::

   from aiida.tools.codespecific.myplugin.thistool import this_convenience_func

new::

   from aiida_myplugin.tools.thistool import this_convenience_func


