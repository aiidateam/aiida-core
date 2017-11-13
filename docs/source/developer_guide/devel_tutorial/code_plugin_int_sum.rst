Developer calculation plugin tutorial  - Integer summation
==========================================================

.. toctree::
   :maxdepth: 2

In this chapter we will give you some examples and a brief guide on how to write
a plugin to support a new code. We will focus here on a very simple code (that
simply adds two numbers), so that we can focus only on how AiiDA manages 
the calculation. At the end, you will have an overview of how a plugin is 
developed. You will be able then to proceed to more complex plugin guides like
the guide for the Quantum Espresso plugin, or you can directly jump in
and develop your own plugin!

Overview
--------
Before analysing the different components of the plugin, it is important to
understand which are these and their interaction.

We should keep in mind that AiiDA is a tool allowing us to perform easily
calculations and to maintain data provenance. That said, it should be clear
that AiiDA doesn't perform the calculations but orchestrates the calculation
procedure following the user's directives. Therefore, AiiDA executes (external)
codes and it needs to know:

* where the code is;

* how to prepare the input for the code. This is called an `input plugin` or a
  `Calculation` subclass;

* how to parse the output of the code. This is called an `output plugin` or a
  `Parser` subclass.

It is also useful, but not necessary, to have a script that prepares the
calculation for AiiDA with the necessary parameters and submits it. 
Let's start to see how to prepare these components.

Code
----
The code is an external program that does a useful calculation for us. For
detailed information on how to setup the new codes, you can have a look at the
:ref:`respective documentation page <setup_computers_codes>`.

Imagine that we have the following python code that we want to install. It
does the simple task of adding two numbers that are found in a JSON file, whose
name is given as a command-line parameter::

   #!/usr/bin/env python
   # -*- coding: utf-8 -*-

   import json
   import sys

   in_file = sys.argv[1]
   out_file = sys.argv[2]

   with open(in_file) as f:
       in_dict = json.load(f)

   out_dict = { 'sum':in_dict['x1']+in_dict['x2'] }

   with open(out_file,'w') as f:
       json.dump(out_dict,f)

The result will be stored in JSON format in a file which name is also passed
as parameter. The resulting file from the script will be handled by AiiDA. The
code can be downloaded from :download:`here <sum_executable.py>`. We will now 
proceed to prepare an AiiDA input plugin for this code.

Input plugin
------------
In abstract term, this plugin must contain the following two pieces of
information:

* what are the input data objects of the calculation;

* how to convert the input data object in the actual input file required by
  the external code.

Let's have a look at the `input plugin` developed for the aforementioned
summation code (a detailed description of the different sections follows)::

    # -*- coding: utf-8 -*-

    from aiida.orm import JobCalculation
    from aiida.orm.data.parameter import ParameterData
    from aiida.common.utils import classproperty
    from aiida.common.exceptions import InputValidationError
    from aiida.common.exceptions import ValidationError
    from aiida.common.datastructures import CalcInfo, CodeInfo
    import json

    class SumCalculation(JobCalculation):
        """
        A generic plugin for adding two numbers.
        """

        def _init_internal_params(self):
            super(SumCalculation, self)._init_internal_params()

            self._DEFAULT_INPUT_FILE = 'in.json'
            self._DEFAULT_OUTPUT_FILE = 'out.json'
            self._default_parser = 'sum'

        @classproperty
        def _use_methods(cls):
            """
            Additional use_* methods for the namelists class.
            """
            retdict = JobCalculation._use_methods
            retdict.update({
                "parameters": {
                   'valid_types': ParameterData,
                   'additional_parameter': None,
                   'linkname': 'parameters',
                   'docstring': ("Use a node that specifies the input parameters "
                                 "for the namelists"),
                   },
                })
            return retdict

        def _prepare_for_submission(self,tempfolder, inputdict):
            """
            This is the routine to be called when you want to create
            the input files and related stuff with a plugin.

            :param tempfolder: a aiida.common.folders.Folder subclass where
                               the plugin should put all its files.
            :param inputdict: a dictionary with the input nodes, as they would
                    be returned by get_inputs_dict (with the Code!)
            """
            try:
                parameters = inputdict.pop(self.get_linkname('parameters'))
            except KeyError:
                raise InputValidationError("No parameters specified for this "
                                           "calculation")
            if not isinstance(parameters, ParameterData):
                raise InputValidationError("parameters is not of type "
                                           "ParameterData")
            try:
                code = inputdict.pop(self.get_linkname('code'))
            except KeyError:
                raise InputValidationError("No code specified for this "
                                           "calculation")
            if inputdict:
                raise ValidationError("Cannot add other nodes beside parameters")

            ##############################
            # END OF INITIAL INPUT CHECK #
            ##############################

            input_json = parameters.get_dict()

            # write all the input to a file
            input_filename = tempfolder.get_abs_path(self._DEFAULT_INPUT_FILE)
            with open(input_filename, 'w') as infile:
                json.dump(input_json, infile)

            # ============================ calcinfo ================================

            calcinfo = CalcInfo()
            calcinfo.uuid = self.uuid
            calcinfo.local_copy_list = []
            calcinfo.remote_copy_list = []
            calcinfo.retrieve_list = [self._DEFAULT_OUTPUT_FILE]
            calcinfo.retrieve_temporary_list = [['path/hugefiles*[0-9].xml', '.', '1']]

            codeinfo = CodeInfo()
            codeinfo.cmdline_params = [self._DEFAULT_INPUT_FILE,self._DEFAULT_OUTPUT_FILE]
            codeinfo.code_uuid = code.uuid
            calcinfo.codes_info = [codeinfo]

            return calcinfo


The above input plugin can be downloaded from
(:download:`here <sum_calc.py>`) and should be placed at 
``aiida/orm/calculation/job/sum.py``.

In order the plugin to be automatically discoverable by AiiDA, it is important 
to:

* give the right name to the file. This should be the name of your input plugin
  (all lowercase);

* place the plugin under ``aiida/orm/calculation/job``;

* name the class inside the plugin as PluginnameCalculation. For example, the
  class name of the summation input plugin is, as you see above, 
  ``SumCalculation``. The first letter must be capitalized, the other letters
  must be lowercase;

* inherit the class from ``JobCalculation``.

By doing the above, your plugin will be discoverable and loadable
using ``CalculationFactory``.

.. note:: The base ``Calculation`` class should only be used as the abstract
  base class. Any calculation that needs to run on a remote scheduler must
  inherit from  :class:`~aiida.orm.implementation.general.calculation.job.AbstractJobCalculation`, that
  contains all the methods to run on a remote scheduler, get the calculation
  state, copy files remotely and retrieve them, ...

Defining the accepted input Data nodes
//////////////////////////////////////

The input data nodes that the input plugin expects are those returned by the
``_use_methods`` class property.
It is important to always extend the dictionary returned by the parent class,
starting this method with::
   
    retdict = JobCalculation._use_methods
    
(or the correct parent class, instead of ``JobCalculation``, if you are 
inheriting from a subclass).
    
The specific parameters needed by the plugin are defined by the following 
code snippet::

    retdict.update({
        "parameters": {
           'valid_types': ParameterData,
           'additional_parameter': None,
           'linkname': 'parameters',
           'docstring': ("Use a node that specifies the input parameters "
                         "for the namelists"),
           },
        })

This means that this specific summation plugin expects only one input data 
node, which is of the type ``ParameterData`` and with link name ``parameters``.


The main plugin logic
/////////////////////

The main logic of the plugin (called by AiiDA just before submission, in order
to read the AiiDA input data nodes and create the actual input files for the 
extenal code) must be defined inside a method ``_prepare_for_submission``, that
will receive (beside ``self``) two parameters, a temporary folder ``tempfolder``
in which content can be written, and a dictionary containing all the input 
nodes that AiiDA will retrieve from the database (in this way, the plugin does
not need to browse the database).

The input data node with the parameter is retrieved using its link name 
``parameters`` specified above::

    parameters = inputdict.pop(self.get_linkname('parameters'))

A few additional checks are performed to retrieve also the input code (the AiiDA
node representing the code executable, that we are going to setup in the next
section) and verify that there are no unexpected additional input nodes.

The following lines do the actual job, and prepare the input file for the 
external code, creating a suitable JSON file::

    input_json = parameters.get_dict()

    # write all the input to a file
    input_filename = tempfolder.get_abs_path(self._DEFAULT_INPUT_FILE)
    with open(input_filename, 'w') as infile:
        json.dump(input_json, infile)

The last step: the calcinfo
///////////////////////////

We can now create the calculation info: an object containing some additional
information that AiiDA needs (beside the files you generated in the folder)
in order to submit the claculation. 
In the calcinfo object, you need to store the calculation UUID::

    calcinfo.uuid = self.uuid

You should also define a list of output files that will be retrieved
automatically after the code execution, and that will be stored permanently
into the AiiDA database::

   calcinfo.retrieve_list = [self._DEFAULT_OUTPUT_FILE]

The entries of the list should either be a string, which corresponds to the full
filepath of the file on the remote, or if you want to specify a group of files with
wildcards, it should be another list containing the following three items

* Remote path with wildcards e.g. ``some/path/bigfiles*[0-9].xml``
* Local path, which should always be ``'.'`` in this case of using wildcards
* Depth, which is an integer that indicates to what level the nested subtree structure should be kept.
  For example in this example, with a depth of ``1``, the matched files will be copied to the
  root directory as ``bigfiles*[0-9].xml``. For ``depth=1``, the sub path ``path`` will be included
  and the files will be copied as ``path/bigfiles*[0-9].xml``

There is another field that follows exactly the same syntax as the ``retrieve_list`` but behaves a little differently.

   calcinfo.retrieve_temporary_list = [['some/path/bigfiles*[0-9].xml', '.', 0]]

The difference is that these files will be retrieved and stored in a temporary folder, that will only
be available during the parsing of the calculation. After the parsing is completed, successfully or not, the
files will be deleted. This is useful if during parsing, one wants to analyze the contents of big files and
parse a small subset of the data to keep permanently, but does not want to have the store the raw files themselves
which would unnecessarily increase the size of the repository. The files that are retrieved will be stored in
a temporary ``FolderData`` and be passed as an argument to the ``parse_with_retrieved`` method of the ``Parser``
class, which is implemented by the specific plugin. It will be passed under the key ``retrieved_temporary_folder``.

For the time being, just define also the following variables as empty lists
(we will describe them in the next sections)::

    calcinfo.local_copy_list = []
    calcinfo.remote_copy_list = []


Finally, you need to specify which code executable(s) need to be called
link the code to the ``codeinfo`` object. 
For each code, you need to create a ``CodeInfo`` object, specify the code UUID,
and define the command line parameters that should be passed to the code as a
list of strings (only paramters after the executable name must be specified. 
Moreover, AiiDA takes care of escaping spaces and other symbols). 
In our case, our code requires the name of the input file, followed by the
name of the output file, so we write::

    codeinfo.cmdline_params = [self._DEFAULT_INPUT_FILE,self._DEFAULT_OUTPUT_FILE]

Finally, we link the just created ``codeinfo`` to the ``calcinfo``, and return
it::

    calcinfo.codes_info = [codeinfo]
    
    return calcinfo

.. note:: ``calcinfo.codes_info`` is a list of ``CodeInfo`` objects. This
  allows to support the execution of more than one code, and will be described
  later.

.. note:: All content stored in the tempfolder will be then stored into the 
  AiiDA database, potentially `forever`. Therefore, before generating 
  huge files, you should carefully   think at how to design your plugin 
  interface. In particular, give a look to the ``local_copy_list`` and 
  ``remote_copy_list`` attributes of ``calcinfo``, 
  described in more detail in the :doc:`Quantum ESPRESSO developer 
  plugin tutorial<code_plugin_qe>`.

By doing all the above, we have clarified what parameters should be passed
to which code, we have prepared the input file that the code will access
and we let also AiiDA know the name of the output file: our first input plugin
is ready!

.. note:: A few class internal parameters can (or should) be defined inside the 
  ``_init_internal_params`` method::

        def _init_internal_params(self):
            super(SumCalculation, self)._init_internal_params()

            self._DEFAULT_INPUT_FILE = 'in.json'
            self._DEFAULT_OUTPUT_FILE = 'out.json'
            self._default_parser = 'sum'

  In particular, it is good practice to define
  a ``_DEFAULT_INPUT_FILE`` and ``_DEFAULT_OUTPUT_FILE`` attributes (pointing to the
  default input and output file name -- these variables are then used by some
  ``verdi`` commands, such as ``verdi calculation outputcat``). Also, you need
  to define the name of the default parser that will be invoked when the
  calculation completes in ``_default_parser``. 
  In the example above, we choose the 'sum' plugin (that
  we are going to define later on). If you don't want to call any parser,
  set this variable to ``None``.

As a final step, after copying the file in the location specified above, we
can check if AiiDA recognised the plugin, by running the command
``verdi calculation plugins`` and veryfing that our new ``sum`` plugin is
now listed.

Setup of the code
-----------------
Now that we know the executable that we want to run, and we have setup the
input plugin, we can proceed to configure AiiDA by setting up a new code to
execute::

    verdi code setup

During the setup phase, you can either configure a `remote` code (meaning that
you are going to place the python executable in the right folder of the remote
computer, and then just instruct AiiDA on the location), or as a `local` folder,
meaning that you are going to store (during the setup phase) the python
executable into the AiiDA DB, and AiiDA will copy it to the remote computer 
when needed. In this second case, put the ``sum_executable.py`` in an empty
folder and pass this folder in the setup phase.

.. note:: In both cases, remember to set the executable flag to the code by
  running ``chmod +x sum_executable.py``.

After defining the code, we should be able to see it in the list of our installed
codes by typing::

    verdi code list

A typical output of the above command is::

    $ verdi code list
    # List of configured codes:
    # (use 'verdi code show CODEID' to see the details)
    * Id 73: sum

Where we can see the already installed summation code. We can further see the
specific parameters that we gave when we set-up the code by typing::

    verdi code show 73

Which will give us an output similar to the following::

    $ verdi code show 73
     * PK:             73
    * UUID:           34b44d33-86c1-478b-88ff-baadfb6f30bf
     * Label:          sum
     * Description:    A simple sum executable
     * Default plugin: sum
     * Used by:        0 calculations
     * Type:           local
     * Exec name:      ./sum_executable.py
     * List of files/folders:
       * [file] sum_executable.py
     * prepend text:
       # No prepend text.
     * append text:
       # No append text.

What is important to keep from the above is that we have informed AiiDA for the
existence of a code that resides at a specific location and we have also
specified the `default (input) plugin` that will be used. 

Output plugin: the parser
-------------------------

In general, it is useful to parse files generated by the code to import
relevant data into the database. This has two advantages:

* we can store information in specific data classes to facilitate their use
  (e.g. crystal structures, parameters, ...)
  
* we can then make use of efficient database queries if, e.g., output quantities
  are stored as integers or floats rather than as strings in a long text file.

The following is a sample output plugin for the summation code, described in 
detail later::

    # -*- coding: utf-8 -*-

    from aiida.orm.calculation.job.sum import SumCalculation
    from aiida.parsers.parser import Parser
    from aiida.parsers.exceptions import OutputParsingError
    from aiida.orm.data.parameter import ParameterData

    import json

    class SumParser(Parser):
        """
        This class is the implementation of the Parser class for Sum.
        """
        def parse_with_retrieved(self, retrieved):
            """
            Parses the datafolder, stores results.
            This parser for this simple code does simply store in the DB a node
            representing the file of forces in real space
            """

            successful = True
            # select the folder object
            # Check that the retrieved folder is there
            try:
                out_folder = retrieved[self._calc._get_linkname_retrieved()]
            except KeyError:
                self.logger.error("No retrieved folder found")
                return False, ()

            # check what is inside the folder
            list_of_files = out_folder.get_folder_list()
            # at least the stdout should exist
            if self._calc._DEFAULT_OUTPUT_FILE not in list_of_files:
                successful = False
                self.logger.error("Output json not found")
                return successful,()

            try:
                with open( out_folder.get_abs_path(self._calc._DEFAULT_OUTPUT_FILE) ) as f:
                    out_dict = json.load(f)
            except ValueError:
                successful=False
                self.logger.error("Error parsing the output json")
                return successful,()

            # save the arrays
            output_data = ParameterData(dict=out_dict)
            link_name = self.get_linkname_outparams()
            new_nodes_list = [(link_name, output_data)]

            return successful,new_nodes_list

As mentioned above the `output plugin` will `parse` the output of the executed
code at the remote computer and it will store the results to the AiiDA database.

All the parsing code is enclosed in a single method ``parse_with_retrieved``,
that will receive as a single parameter ``retrieved``, a dictionary of retrieved
nodes. The default behavior is to create a single FolderData node, that can
be retrieved using::

    out_folder = retrieved[self._calc._get_linkname_retrieved()]

We then read and parse the output file that will contain the result::

    with open( out_folder.get_abs_path(self._calc._DEFAULT_OUTPUT_FILE) ) as f:
        out_dict = json.load(f)

.. note:: all parsers have a ``self._calc`` attribute that points to the 
  calculation being parsed. This is automatically set in the parent ``Parser`` 
  class.

After loading the code result data to the dictionary ``out_dict``,
we construct a ``ParameterData`` object (``ParameterData(dict=out_dict)``)
that will be linked to the calculation in the AiiDA graph to be later
in the database::

    output_data = ParameterData(dict=out_dict)
    link_name = self.get_linkname_outparams()
    new_nodes_list = [(link_name, output_data)]

    return successful,new_nodes_list

.. note:: Parsers should not store nodes manually. Instead, they should return
  a list of output unstored nodes (together with a link name string, as shown 
  above). AiiDA will then take care of storing the node, and creating the
  appropriate links in the DB.

.. note:: the ``self.get_linkname_outparams()`` is a string automatically
  defined in all ``Parser`` classes and subclasses. In general, you can have
  multiple output nodes with any name, but it is good pratice so have also
  one of the output nodes with link name ``self.get_linkname_outparams()``
  and of type ``ParameterData``. The reason is that this node is the one exposed
  with the ``calc.res`` interface (for instance, later we will be able to get
  the results using ``print calc.res.sum``.

The above `output plugin` can be downloaded from :download:`here <sum_parser.py>`
and should be placed at ``aiida/parsers/plugins/sum.py``.

.. note:: Before continuing, it is important to restart the daemon, so that 
  it can recognize the new files added into the aiida code and use the new 
  plugins. To do so, run now::
  
    verdi daemon restart

Submission script
-----------------

It's time to calculate how much 2+3 is! We need to submit a new calculation.
To this aim, we don't necessarily need a submission script, but it
definitely facilitates the calculation submission. A very minimal
sample script follows (other examples can be found in the 
``aiida/examples/submission`` folder)::

    #!/usr/bin/env runaiida
    # -*- coding: utf-8 -*-
    import sys
    import os

    from aiida.common.exceptions import NotExistent
    ParameterData = DataFactory('parameter')

    # The name of the code setup in AiiDA
    codename = 'sum'
    computer_name = 'localhost'

    ################################################################
    try:
        dontsend = sys.argv[1]
        if dontsend == "--dont-send":
            submit_test = True
        elif dontsend == "--send":
            submit_test = False
        else:
            raise IndexError
    except IndexError:
        print >> sys.stderr, ("The first parameter can only be either "
                              "--send or --dont-send")
        sys.exit(1)

    code = Code.get_from_string(codename)
    # The following line is only needed for local codes, otherwise the
    # computer is automatically set from the code
    computer = Computer.get(computer_name) 

    # These are the two numbers to sum
    parameters = ParameterData(dict={'x1':2,'x2':3})

    calc = code.new_calc()
    calc.label = "Test sum"
    calc.description = "Test calculation with the sum code"
    calc.set_max_wallclock_seconds(30*60) # 30 min
    calc.set_computer(computer)
    calc.set_withmpi(False)
    calc.set_resources({"num_machines": 1})

    calc.use_parameters(parameters)

    if submit_test:
        subfolder, script_filename = calc.submit_test()
        print "Test submit file in {}".format(os.path.join(
            os.path.relpath(subfolder.abspath),
            script_filename
            ))
    else:
        calc.store_all()
        calc.submit()
        print "submitted calculation; calc=Calculation(uuid='{}') # ID={}".format(
            calc.uuid,calc.dbnode.pk)

What is important to note in the script above is the definition of the code
to be used::

    codename = 'sum'
    code = Code.get_from_string(codename)

and the definition of the parameters::

    parameters = ParameterData(dict={'x1':2,'x2':3})
    calc.use_parameters(parameters)

If everything is done correctly, by running the script a new calculation  will
be generated and submitted to AiiDA (to run the script, remember to change its
permissions with ``chmod +x filename`` first,
and then run it with ``./scriptname.py``).
When the code finishes its
execution, AiiDA will retrieve the results, parse and store them back to 
the AiiDA database using the output plugin. 
You can download the submission script from :download:`here <sum_submission.py>`.

Conclusion
----------
We have just managed to write our first AiiDA plugin! What is important to
remember is that:

* AiiDA doesn't know how to execute your code. Therefore, you have to setup
  your code (with ``verdi code setup``) and let AiiDA know how to prepare the
  data that will be given to the code (`input plugin` or `calculation`) and how
  to handle the result of the code (`output plugin` or `parser`).

* you need to do pass the actual data for the calculation you want to
  submit, either in the interactive shell, or via a submission script.

As usual, we can see the executed calculations by doing a
``verdi calculation list``. To see the calculations of the last day::

    $ verdi calculation list -a -p1
    # Last daemon state_updater check: 0h:00m:06s ago (at 20:10:31 on 2015-10-20)
    # Pk|State        |Creation|Sched. state|Computer   |Type
    327 |FINISHED     |4h ago  |DONE        |localhost  |sum

and we can see the result of the sum by running in the verdi shell the following
commands (change 327 with the correct calculation PK)::

  >>> calc = load_node(327)
  >>> print calc.res.sum
  <<< 5
  
So we verified that, indeed, 2+3=5.
