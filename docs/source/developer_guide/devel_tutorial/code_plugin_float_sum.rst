.. _DevelopDataPluginTutorialFloat:

Data plugin - Float Summation
=============================

.. toctree::
   :maxdepth: 2

Now that you have written :doc:`your first AiiDA plugin <code_plugin_int_sum>`,
we can try to extend it to see how we can introduce different type of parameters
and how the plugins have to be modified to encompass these changes.

Introducing a new data type
---------------------------
We will start by describing what is a data plugin, and by creating a new one.

A data plugin is a subclass of :py:class:`Data<aiida.orm.nodes.data.data.Data>`.
In the class, you should provide methods that the end user should use to store
high-level objects (for instance, for a crystal structure, there can be a method
for setting the unit cell, one for adding an atom in a given position, ...).
Internally, you should choose where to store the content. There are two options:

* **In the AiiDA database**. This is useful for small amounts of data, that you plan 
  to query. In this case, use ``self._set_attr(attr_name, attr_value)`` to store
  the required value. 
* **In the AiiDA file repository (as a file on the disk)**. This is suitable 
  for big files and quantities that you do not 
  want to query. In this case, access the folder using ``self.folder`` and 
  use the methods of ``self.folder`` to create files, subfolders, ...
  
Of course, it is also good practice to provide "getter" methods to retrieve
the data in the database and return it back to the user. The idea is that the
user can operate directly only with the methods you provide, and should not
need to know how you decided to store the data inside the AiiDA database.

As a simple example that we will use for the exercise below, 
imagine that we want to introduce a new type of data node that simply 
stores a float number. We will call it ``FloatData``, and the class 
implementation can look like this::

   from aiida.orm import Data

   class FloatData(Data):

       @property
       def value(self):
           """
           The value of the Float
           """
           return self.get_attr('number')

       @value.setter
       def value(self,value):
           """
           Set the value of the Float

           :raise ValueError:
           """
           self._set_attr('number', float(value))

The definition of this new data type should reside below a ``data`` sub package in your
plugin package, with directory structure like::


   aiida-yourplugin/
      aiida_yourplugin/
         __init__.py
         calcs/
            __init__.py
            sum.py
         parsers/
            __init__.py
            sum_parser.py
         data/
            __init__.py
            float.py  <-- Put the code here
      setup.py
      setup.json


And following lines should be there in the ``setup.json`` file::

   {
      ...
      "entry_points": {
         "aiida.data": {
            "yourplugin.float = aiida_yourplugin.data.float:FloatData"
         },
         ...
      }
      ...
   }

.. seealso::
   Please see the documentation about the :ref:`entry points<plugins.entry_points>` to learn more about the plugin system.


Exercise: Modifying the calculation plugin
------------------------------------------
Your exercise consists in creating a new calculation plugin (let's call it for instance
``SumFloatCalculation``) that will also perform the sum, but accept as input two ``FloatData``
node and return also a ``FloatData`` node containing the sum.

Below, you will find some hints on the parts you need to modify with respect
to the :doc:`previous tutorial<code_plugin_int_sum>` using instead 
``Dict`` both as inputs and outputs.

.. note:: Remember to add an entry point for the ``SumFloatCalculation`` in the ``setup.json`` file and re-install the package and refresh entry points.
   It is up to you to either put the new class in the same ``sum.py`` or create a new ``floatsum.py``.
   The same also applies to the new parser class.

Changes to the parser
/////////////////////

The plugin should now return a ``FloatData`` instead of a ``Dict``,
therefore the parser code should contain something like the following::

    output_data = FloatData()
    output_data.value = out_dict["sum"]
    linkname = 'output_data'

Changes to the input plugin
///////////////////////////

To be able to run your new ``FloatsumParser``, you will need the corresponding
input plugin (``FloatsumCalculation``). The first modification is then to link
to the correct parser class::

    self._default_parser = 'sum.floatsum'  # Name of the entry point

For consistency, we also want that the input plugin accepts two
``FloatData`` instead of a single ``Dict``.
Therefore, you have to update the ``retdict`` object accordingly::

    retdict.update({
        "float_data_1": {
           'valid_types': FloatData,
           'additional_parameter': None,
           'linkname': 'float_data_1',
           'docstring': ("The first addend"),
           },
        "float_data_2": {
           'valid_types': FloatData,
           'additional_parameter': None,
           'linkname': 'float_data_2',
           'docstring': ("The second addend"),
           },
        })

You need then to change the main code to use the values obtained from the
two nodes, rather than from a single node as before. This should be easy, 
so we leave this task to you. Note that we plan to use the same python code
to actually perform the sum, so the JSON file to be generated should have
the same format.

We also suggest that you add utility methods (to the benefit of the end user)
to provide the addends to the code, something like::

   def set_addend1(self, value):
       fl = FloatData()
       fl.value = value
       self.use_float_data_1(fl)

and similarly for the second addend.

Code
////
The python code that actually performs the calculation does not need to be
modified. We can reuse the same file, but we suggest to setup a new code
in AiiDA, with a different name, using as default plugin the ``sum.floatsum``
plugin.

Submission script
/////////////////
Finally, adapt your submission script to create the correct input nodes, 
and try to perform a sum of two numbers to verify that you did all correctly!

.. note:: After (re)registering the entry points, do not forget to restart the daemon so that
   it will recognize the change! The same should be done if you do any change to
   the plugin, otherwise the daemon may have cached the old file and will keep
   using it.
   
