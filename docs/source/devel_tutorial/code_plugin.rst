Developer code plugin tutorial
==============================

.. toctree::
   :maxdepth: 2

In this chapter we will give you a brief guide that will teach you how to write a plugin to support a new code.

Generally speaking, we expect that each code will have its own
peculiarity, so that sometimes a new strategy for code plugin might be
needed to be carefully thought.
Anyway, we will show you how we implemented the plugin for Quantum
Espresso, in order for you to be able to replicate the task for other
codes.
Therefore, it will be assumed that you have already tried to run an
example of QE, and you know more or less how the AiiDA interface
works.

In fact, when writing your own plugin, keep in mind that you need to
satisfy multiple users, and the interface needs to be simple (not the
code below). But always try to follow the Zen of Python:

Simple is better than complex.

Complex is better than complicated.

Readability counts.

There will be two kinds of plugins, the input and the output. The former will
run your calculations on the cluster, the latter will make your results
readable in the database.
 
InputPlugin
-----------

Step 1: know your code inputs
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A fundamental task is to understand which elements a calculations
receives as an input.
It is not at all a trivial task: you need to decide how to represent
the inputs inside the database!
And those differ in a substantial way between different codes.


For example, many codes do a calculation on top of a structure, let's
say it is trying to compute the energy of a structure.
In the case of Quantum Espresso for example, there is a single file
that contains all the information, and it was the developer's task to
decide to split it into more atomic pieces of information.
Therefore we identified different input objects:

- A structure
- A set of pseudopotential files (one object per pseudo)
- A set of input parameters (where we actually decided to take out the k-points into a different object)
- possibly a previous scratch

Let's see how all those objects are managed by the QuantumEspresso plugin, so let's have a look at the class ``BasePwCpInputGenerator``.

    Note: since Pw and Cp have a very similar plugin structure, with the only difference being the k-points, which require a different input node.

Every plugin has to define a class that inherits the calculation
object (that shares a lot of database-specific methods), so it would
look like the following::

    from aiida.orm import Calculation
    class MyNewPlugin(calculation):

Note: the PwCalculation inherits both the calculation and the ``BasicPwCpInputGenerator`` classes.

Every plugin class is required to have the following hidden method::

  def _prepare_for_submission(self,tempfolder):

This function is called by the executionmanager when it's needed to create a new calculation.
No other specific functions have to be created for the plugin to work.
This function is expected to receive in input a tempfolder. 
This is a folder object in which the plugin will prepare and write the files needed for the code execution on the cluster (this is actually the folder that will be copied on the cluster and executed).

Therefore, you don't have to prepare a multitude of inputs to the function::

  the actual code inputs have to be taken out of the database.

How? The plugin follows the links inside the database, that have to be set by the user.
Therefore the Pw plugin contains functions such as::

    def use_structure(self, data):
    def use_parent_folder(self, data):
    def use_parameters(self, data):
    def use_pseudo(self, data, kind):

The user prepares the object structure, the object calculation, and uses this function to set the link between the two elements in the database.
More into details, a function use_parameters will check if the input
node is of the desired kind, and then it will set the link from the
input to the calculation.
::

    def use_parameters(self, data):
        """
        Set the parameters for this calculation
        """
        if not isinstance(data, ParameterData):
            raise ValueError("The data must be an instance of the ParameterData class")

        self.replace_link_from(data, self.get_linkname_parameters())

We didn't implement any further input data analysis or verification
here, what we worked was at the level of the input writing.
Note also that a link can also have a label, therefore the calculation
plugin has to implement a simple method that returns the name of the
link (avoid hard-coding!)::

    def get_linkname_parameters(self):
        """
        The name of the link used for the parameters
        """
        return "parameters"


Step 2: write your input
^^^^^^^^^^^^^^^^^^^^^^^^

How does the method ``_prepare_for_submission`` work in practice?
At first, one needs to find all the input nodes of the calculation. 
The method ``self.get_inputdata_dict()`` does a query to the database,
and asks for all the nodes that are input to the calculation object (``self``), as a result, it returns a dictionary that has the linkname for the key, and the node object as for the value.
After this first query, you should check if the input nodes are logically sufficient to run an actual calculation. 
For example, a Pw calculation with QE strictly requires parameters, k_points, pseudopotentials and a structure.
There are some nodes that are optional or that may be used in future for further functionalities.
Note however that is good to check that there are no unused nodes, if this happens, an ``InputValidationError`` exception must be raised. 
In the long term, the absence of such validation can lead to databases more complicated than necessary, and where you don't understand which is the actual input.

Now it is time to build the input.
You can load the object from the database as in the following way::

    input_dict = self.get_inputdata_dict()
    kpoints = inputdict.pop(self.get_linkname_kpoints())

And then you have to use the information that you stored in this object to build the actual lines of the code input.
Now the problem is simply that of reading the database and convert that information into code/text input, which essentially requires a bit of time and code-specific knowledge.

Note that some code-variables are now prohibited to the user. 
For example, Quantum Espresso requires you to write in the input the number of atoms; using a Structure data object this information should'nt be provided manually: it is blocked to the user and set automatically by counting how many species there are in the Structure. 
(the same holds for other pseudo-related properties)

Note also that in this part you will decide how inputs have to be written, and in particular the ParameterData one.
For example, for the case of Quantum Espresso we opted for a nested
dictionary structure, where the first level identifies the Cardlists,
and the following the variables.
We could have implemented the plugin in a way such that you only
provide the variable and the cardlist is selected automatically. We
decided to avoid that, since if a private (or future) version of the
code there is imlpemented a new variable, than how would the plugin be
able to recognize where to put this variable without changing the
plugin?
Easyness of maintainance here win over user comfort!



When everything is ready, you can just write everything inside a file
in tempfolder, or in multiple if necessary::

    input_filename = tempfolder.get_abs_path(self.INPUT_FILE_NAME)

    with open(input_filename,'w') as infile:
        infile.write("All the input I need!")





If you need to copy remotely the scratch of a previous calculation, than it works as follows: a user set a link between the FolderData that is created by the parent calculation and the new one.
Then you will save in a list ``remote_calc_folder`` a tuple of length 3, which contains the remote computer source, the source folder path and the destination folder paths that have to be copied.
This list will be appended to a CalcInfo object that we will discuss later.
Note that this method has to be used for copying data in the same remote machine, i.e. not between two clusters.

::

        if parent_calc_folder is not None:   # if needed
            remote_copy_list.append(
                (parent_calc_folder.get_remote_machine(),
                 os.path.join(parent_calc_folder.get_remote_path(),parent_calc_out_subfolder),
                 self.OUTPUT_SUBFOLDER)
		 )



The whole function ``_prepare_for_submission`` needs to return an object of type CalcInfo.
Only few things are needed to be tweaked by your code, so you can use the following as a template::

        calcinfo = CalcInfo()

        calcinfo.uuid = self.uuid
        calcinfo.cmdline_params = settings_dict.pop('CMDLINE', [])
        calcinfo.local_copy_list = local_copy_list
        calcinfo.remote_copy_list = remote_copy_list
	### Modify here and put a name for standard input/output files
        calcinfo.stdin_name = self.INPUT_FILE_NAME
        calcinfo.stdout_name = self.OUTPUT_FILE_NAME
	###        
	
	calcinfo.retrieve_list = []
	### Modify here !
        calcinfo.retrieve_list.append('Every file/folder you want to store back locally')
	###
        settings_retrieve_list = settings_dict.pop('additional_retrieve_list', [])
        calcinfo.retrieve_list += settings_retrieve_list
        calcinfo.retrieve_list += self._internal_retrieve_list
        
        return calcinfo

Note that all the file names you need to modify are not absolute path names (you don't know the name of the folder where it will be created) but rather the path relative to the scratch folder.


That's what is needed to write an input plugin.
Reassuming, what you need to do is:

* check if you have all needed input nodes

* write the input files in the temporary folder

* Instance and return the calcinfo object





OutputPlugin
------------

Well done! You were able to have a successful input plugin.
Now we are going to see what you need to do for an output plugin.
First of all let's create a new folder:
``$path_to_aiida/aiida/parsers/plugins/the_name_of_new_code``, and put there an empty ``__init__.py`` file.

Here you will write in a new python file the output parser class.
It is actually a rather simple class, performing only a few (but tedious) tasks.
It has to read the raw outputs of a calculation, which at their basic state consists only in an object of type FolderData, which represents the files retrieved from the remote cluster to your local computer.

Therefore, you only need to define a class, with a couple of methods:

* parse_from_data(data). Currently not implemented. It will reparse the output of a calculation.

* parse_from_calc(calc). It parses (for the first time) the output of a calculation, and store the results in the database.

* get_energy_ev(calc). If possible, the parser returns the energy of the calculation

To write the plugin, it is sufficient to implement the parse_from_calc method. 
Logically, this function has to analyze the inputs/outputs of the
calculation and see if everything is present as expected, analyze it,
and store in the database objects containing the results.

To show its functioning, it is reported below part of the code of the
PwCalculation parser, with a variety of comments and leaving only a
minimal set of lines.
You could also use it as a template, just remember to change the
names referring to the code PW, and remembering however that what a
calculation gives you in output, depends really much on the code.

The difficult and long part is hidden in writing the raw_parser
function, that will convert the text of the outputs into a useful
dictionary.
The more you will write, the better it will be.
*Note also that not only you should parse physical values, a very
important thing that could be used by workflows are exceptions or
others errors occurring in the calculation. 
You could save them in a dedicated key of the dictionary (say
'warnings'), later a  workflow can easily read the exceptions from the
results and perform a dedicated correction!*

::

    from aiida.orm.calculation.quantumespresso.pw import PwCalculation
    from aiida.orm.data.parameter import ParameterData
    from aiida.orm.data.folder import FolderData
    from aiida.parsers.parser import Parser
    from aiida.common.datastructures import calc_states

    class PwParser(Parser):
        """
        This class is the implementation of the Parser class for your new code.
        """

        def __init__(self):
            """
            Initialize the instance of PwParser
            """
        
        def parse_from_data(self,data):
            """
            Parse, taking as input a datanode. Creates a dummy parser
            calculation, connected with the old datanode in input, and a
            new datanode with the parsed values.
            (to be used by the user for eventual re-parsing of out-data,
            for example with another or updated version of the parser)
            """
	    # we still have to think about it...
            raise NotImplementedError
            
        def parse_from_calc(self,calc):
            """
            Parses the calculation-output datafolder, and stores
            results.

	    Steps:
	    1. check input of the function
	    2. check status of the calculation (must be PARSING)
	    3. check whether calculation+node local structure is as expected
	    4. check if standard output and the files that have to be parsed exist
	    5. call a low level parsing function, which converts the text into a dictionary
	    6. save parsed values
	    7. return a boolean, if the calculation was successfull or not.
            """
            from aiida.common.exceptions import UniquenessError,InvalidOperation
            import os
	            
            # 1. check for valid input
            if not isinstance(calc,PwCalculation):
                raise QEOutputParsingError("Input must calc must be a PwCalculation")
            
            # 2. check the calc status, not to overwrite anything
            state = calc.get_state()
            if state != calc_states.PARSING:
                raise InvalidOperation("Calculation not in {} state"
                                       .format(calc_states.PARSING) )
        
            # 3. load the input dictionary its information can be used for the parsing
            input_dict = calc_input.get_dict()
            
            # 3. load all output FolderData nodes of the calculation
            calc_outputs = calc.get_outputs(type=FolderData,also_labels=True)
            # 3. look for retrieved files only
            retrieved_files = [i[1] for i in calc_outputs if i[0]==calc.get_linkname_retrieved()]
	    # 3. check uniqueness of retrieved data
            if len(retrieved_files)!=1:
                raise QEOutputParsingError("Output folder should be found once, "
                                           "found it instead {} times"
                                           .format(len(retrieved_files)) )
            # 3. get the retrieved DataFolder object
            out_folder = calc_outputs[0][1]
	
            # 4. check what is inside the folder
            list_of_files = out_folder.get_path_list()
            # 4. at least the stdout should exist
            if not calc.OUTPUT_FILE_NAME in list_of_files:
                raise QEOutputParsingError("Standard output not found")
            # 4. get the path to the standard output
            out_file = os.path.join( out_folder.get_abs_path('.'), 
                                     calc.OUTPUT_FILE_NAME )

            # 5. call the raw parsing function. Here it was thought to return a
            # dictionary with all keys and values parsed from the out_file (i.e. enery, forces, etc...)
            # and a flag indicating whether the calculation is successfull or not
	    # In practice, this is the function deciding the final status of the calculation
            out_dict,successful = parse_raw_output(out_file)
            
            # 6. convert the dictionary into an AiiDA object
            output_params = ParameterData(out_dict)
            # 6. save it into db and set link from calc to output
	    # note that the name of the output parameters is set in the baseclass
            output_params.store()
            calc.add_link_to(output_params, label=self.get_linkname_outparams() )
	    # 6. Note: here only a dictionary is stored in the DB, but
	    # you could also decide to store other output objects, for
	    # example an output structure (as it is actually done for Pw.

	    # 7. if false, the calculation status will be flagged as failed, to finished if true
            return successful

        def get_energy_ev(self,calc,all_values=False):
            """
            Returns the float value of energy.
            To be implemented for practicality, if the calculation returns the total energy.
	    It requires that the output parameters object contains a key called 'energy' which is a list of floats
	    If this is the case, the function could probably be used without modifications.
		    
            :param calc: calculation object
            :param bool all_values: if true returns a list of energies, else only a float (default=False)

            :raise FailedError: calculation is failed
            :raise InvalidOperation: calculation has not been parsed yet
            :raise NotExistent: no output found
            :raise UniquenessError: more than one output found
            :raise ContentNotExistent: no key energy found in the results
            """
            from aiida.common.exceptions import InvalidOperation, FailedError
            from aiida.common.exceptions import NotExistent,UniquenessError,ContentNotExistent
        
            calc_state = calc.get_state()
        
            if 'FAILED' in calc_state:  # one of SUBMISSIONFAILED','RETRIEVALFAILED','PARSINGFAILED','FAILED',
                raise FailedError('Calculation is in state {}'
                                  .format(calc_state))
        
            if calc_state != calc_states.FINISHED:
                raise InvalidOperation("Calculation is in state {}: "
                                   "doesn't have results yet".format(calc_state))
        
            out_parameters = calc.get_outputs(type=ParameterData,also_labels=True)
            out_parameterdata = [ i[1] for i in out_parameters if i[0]==self.get_linkname_outparams() ]
        
            if not out_parameterdata:
                raise NotExistent("No output ParameterData found")
        
            if len(out_parameterdata) > 1:
                raise UniquenessError("Output ParameterData should be found once, "
                                  "found it instead {} times"
                                  .format(len(out_parameterdata)) )
            
            out_parameterdata = out_parameterdata[0]

            try:
                if not all_values:
                    energy = out_parameterdata.get_attr('energy')[-1]# a float
                else:
                    energy = out_parameterdata.get_attr('energy') # a list
            except AttributeError:
                raise ContentNotExistent("Key energy not found in results")
        
            return energy

    def parse_raw_output(out_file):
        """
	A parsing function. Takes in input something (here the path to
        a file), analyze it and returns 
	* a boolean, stating if the calculation reached the end without occurring in problems.
	* a dictionary with what will be stored in the ParameterData node.
	"""
	...
	return successfull_or_not, one_big_dictionary


