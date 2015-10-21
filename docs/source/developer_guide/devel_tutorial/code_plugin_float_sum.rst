Developer code plugin tutorial  - Float summation
=================================================

.. toctree::
   :maxdepth: 2

Now that you have writen :doc:`your first AiiDA plugin <code_plugin_int_sum>`,
we can try to extend it to see how we can introduce different type of parameters
and how the plugins have to be modified to encompass these changes.

Introducing a new data type
---------------------------
Imagine that we would like to introduce the following kind of data that is
called ``FloatData``::

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

This file should be placed under ``aiida/orm/data/float.py`` and it should extend
the class ``Data``. It can also be downloaded from :download:`here <float.py>`.


Modifying the output plugin
---------------------------
As a first step, this class can be used to better represent our data when stored
in AiiDA. Therefore, one of the first steps that we can do is to modify the
`output plugin` \ `parser` to create a ``FloatData`` object when storing it
in AiiDA. This can be as simple as changing the following lines of the `output
plugin` of the :doc:`integer summation <code_plugin_int_sum>`::

    output_data = ParameterData(dict=out_dict)
    link_name = 'output_data'
    new_nodes_list = [(link_name, output_data)]

to the following ones::

    output_data = FloatData()
    output_data.value = out_dict["sum"]
    linkname = 'output_data'

A small test will convince you that the correct objects are stored in AiiDA.
For example, imagine that the output plugin of calculation `327` stores
``FloatData`` objects. We can load the node that corresponds to this calculation
and verify that it is the case::

    $ verdi shell
    Python 2.7.6 (default, Jun 22 2015, 17:58:13)
    Type "copyright", "credits" or "license" for more information.

    IPython 1.2.1 -- An enhanced Interactive Python.
    ?         -> Introduction and overview of IPython's features.
    %quickref -> Quick reference.
    help      -> Python's own help system.
    object?   -> Details about 'object', use 'object??' for extra details.

    In [1]: c = load_node(327)

    In [2]: c.get_outputs()
    Out[2]:
    [<FolderData: uuid: 019e09e8-0ed8-42a2-b298-7dc9ec5d3ee7 (pk: 329)>,
     <RemoteData: uuid: e8d40558-435c-444c-8eb3-b74637bf91a1 (pk: 328)>,
     <FloatData: uuid: 0a711199-3093-4ab3-9478-9edc2813c496 (pk: 330)>]


The complete ``FloatsumParser`` can be downloaded from :download:`here <floatsum_parser.py>`.
and it should be placed at ``aiida/parsers/plugins/floatsum.py``.


Modifying the input plugin
--------------------------
To be able to run your new ``FloatsumParser``, you will need the corresponding
input plugin (``FloatsumCalculation``). A basic ``FloatsumCalculation`` can be
a copy of the contents of the ``SumCalculation`` mentioned in the :doc:`plugin
introduction <code_plugin_int_sum>`, with a small change. It should point to
the correct `output plugin / parser`::

    self._default_parser = 'floatsum'

As you can see, we can still use the ParameterData at the `input plugin` without
any problem.

A version of this ``FloatsumCalculation`` calculation can be downloaded from
:download:`here <floatsum_calc_pd.py>` and should be placed at
``aiida/orm/calculation/job/floatsum.py``.

Code re-utilisation
-------------------
If we have a look at the integer summation code mentioned in the
:doc:`previous section<code_plugin_int_sum>`, we notice that it is not
integer specific. Therefore, we can re-use it for the float summation of this
section too. However, there is a small detail. The default `input plugin`
mentioned during the code setup, is the ``SumCalculation``::

    $ verdi code show 73
     * PK:             73
     * UUID:           34b44d33-86c1-478b-88ff-baadfb6f30bf
     * Label:          sum
     * Description:    sum
     * Default plugin: sum
     * Used by:        10 calculations
     * Type:           remote
     * Remote machine: user_pc
     * Remote absolute path:
       /home/aiida_user/Desktop/aiida/pluginTest/original/sum_executable.py
     * prepend text:
       # No prepend text.
     * append text:
       # No append text.

There is no need to change the setup of the code or re-register it for a second
time with a different `default plugin`. We just have to mention the desired
input plugin (if we don't want the default to be used) at the submission script.

More specifically, when we create the code object in the submission script, we
should also mention the desired `input plugin`::

    code = Code.get_from_string(codename)
    code.set_input_plugin_name('floatsum')

The full submission script can be downloaded from :download:`here <float_sum_submission_pd.py>`.

Using the ``FloatData`` in the input plugin
-------------------------------------------

It is not necessary but you can also use the ``FloatData`` in the input plugin.
To achieve it, you have to adapt it to accept two ``FloatData`` objects as input
parameters. Therefore, you have to update the ``retdict`` object accordingly at
the beginning of the plugin::

    retdict.update({
        "float_data_1": {
           'valid_types': FloatData,
           'additional_parameter': None,
           'linkname': 'float_data_1',
           'docstring': ("Use a node that specifies the input float"),
           },
        "float_data_2": {
           'valid_types': FloatData,
           'additional_parameter': None,
           'linkname': 'float_data_2',
           'docstring': ("Use a node that specifies the input float"),
           },
        })

After defining the parameters, you should also parse them using the appropriate
``linkname``:

Last but not least, since the code remained the same, the expected JSON input
file should be constructed and have the same style as in the summation input
plug-in.

The final input plugin can be downloaded from :download:`here <floatsum_calc_fd.py>`
and should be placed at ``aiida/orm/calculation/job/floatsum.py``.

Please note that since the input plugin, expects ``FloatData`` objects, then
the submission script should also be adapted. A version can be found
:download:`here <float_sum_submission_fd.py>`.
