.. _DevelopDataPluginTutorialFloat:

Tutorial: Data plugin - Float summation
=======================================

.. toctree::
   :maxdepth: 2

Now that you have writen :doc:`your first AiiDA plugin <code_plugin_int_sum>`,
we can try to extend it to see how we can introduce different type of parameters
and how the plugins have to be modified to encompass these changes.

Introducing a new data type
---------------------------
We will start by describing what is a data plugin, and by creating a new one.

A data plugin is a subclass of :py:class:`Data<aiida.orm.data.Data>`. What
you have to do is just to define a subclass with a suitable name inside the
``aiida/orm/data`` folder (with the same name convention of Calculation plugins:
the class should be called ``NameData`` (with ``Name`` being a name of your
choice) and put in a ``aiida/orm/data/name.py`` file. 
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

   from aiida.orm.data import Data

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

Assuming you placed this file in ``<aiida_yourplugin>/data/float.py`` you should now expose the following entry point in your ``setup.py``: ``aiida.data: {'yourplugin.float = aiida_yourplugin.data.float:FloatData'``. 


Exercise: Modifying the calculation plugin
------------------------------------------
Your exercise consists in creating a new code plugin (let's call it for instance
``floatsum``) that will also perform the sum, but accept as input two ``FloatData``
node and return also a ``FloatData`` node containing the sum.

Below, you will find some hints on the parts you need to modify with respect
to the :doc:`previous tutorial<code_plugin_int_sum>` using instead 
``ParameterData`` both as inputs and outputs.

.. note:: remember to create copies of your files with a new name 
   ``floatsum.py`` instead of ``sum.py``, and to change the class
   name accordingly.

Changes to the parser
/////////////////////

The plugin should now return a ``FloatData`` instead of a ``ParameterData``,
therefore the parser code should contain something like the following::

    output_data = FloatData()
    output_data.value = out_dict["sum"]
    linkname = 'output_data'

Changes to the input plugin
///////////////////////////

To be able to run your new ``FloatsumParser``, you will need the corresponding
input plugin (``FloatsumCalculation``). The first modification is then to link
to the correct parser class::

    self._default_parser = 'floatsum'

For consistency, we also want that the input plugin accepts two
``FloatData`` instead of a single ``ParameterData``.
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

The final input plugin should be placed 
at ``aiida/orm/calculation/job/floatsum.py``.

Code
////
The python code that actually performs the calculation does not need to be
modified. We can reuse the same file, but we suggest to setup a new code
in AiiDA, with a different name, using as default plugin the ``floatsum``
plugin.

Submission script
/////////////////
Finally, adapt your submission script to create the correct input nodes, 
and try to perform a sum of two numbers to verify that you did all correctly!

.. note:: After placing your files, do not forget to restart the daemon so that
   it will recognize the files! The same should be done if you do any change to
   the plugin, otherwise the daemon may have cached the old file and will keep
   using it.
   
