Developer code plugin tutorial  - Integer summation
===================================================

.. toctree::
   :maxdepth: 2

In this chapter we will give you some examples and a brief guide on how to write
a plugin to support a new code. We will focus on simple codes like summation to
understand what are the necessary components by AiiDA to perform the needed task.
This procedure will allow you to have an overview of how a plug-in is developed
and afterwards you will be able to proceed to more complex plug-in guides like
the guide for the Quantum Espresso plug-in or even to develop your own plug-in
directly!

Overview
--------
Before analysing the different components of the plug-in, it is important to
understand which are these and their interaction.

We should keep in mind that AiiDA is a tool allowing us to perform easily
calculations and to maintain data provenance. That said, it should be clear
that AiiDA doesn't perform the calculations but orchestrates the calculation
procedure following the user's orders. Therefore, AiiDA executes (external)
codes and it should be clear:

* Where the code is.

* How to prepare the input for the code. This is called an input plugin or a
  calculation.

* How to parse the output of the code. This is called an output plugin or a
  parser.

It is also useful, but not necessary, to have a script that launches the
calculation with the necessary parameters.

Code
----
The code is an external program that does a useful calculation for us. For
detailed information on how to setup the new codes, you can have a look at the
:doc:`respective documentation page <../../setup/computerandcodes>`.

Imagine that we have the following python code that we want to install. It
does the simple task of summation of two numbers that are found in a file which
name is given as a parameter::

   #!/usr/bin/env python
   # -*- coding: utf-8 -*-

   import json
   import sys

   __copyright__ = u"Copyright (c), 2015, ECOLE POLYTECHNIQUE FEDERALE DE LAUSANNE " \
                   u"(Theory and Simulation of Materials (THEOS) and National Centre " \
                   u"for Computational Design and Discovery of Novel Materials (NCCR MARVEL)), " \
                   u"Switzerland and ROBERT BOSCH LLC, USA. All rights reserved."
   __license__ = "MIT license, see LICENSE.txt file"
   __version__ = "0.4.1"

   in_file = sys.argv[1]
   out_file = sys.argv[2]

   with open(in_file) as f:
       in_dict = json.load(f)

   out_dict = { 'sum':in_dict['x1']+in_dict['x2'] }

   with open(out_file,'w') as f:
       json.dump(out_dict,f)

The result will be stored in JSON format in a file which name is also passed
as parameter. The resulting file from the script will be handled by AiiDA. The
code can be downloaded from :download:`here <sum_calc.py>`.

To install the above code, we should execute::

    verdi code setup

After defining the code, we should be able to see it in the list of our installed
codes by typing::

    verdi code list

A typical output of the above command is::

    $ verdi code list
    # List of configured codes:
    # (use 'verdi code show CODEID' to see the details)
    * Id 73: sum@user_pc

Where we can see the already installed summation code. We can further see the
specific parameters that we gave when we set-up the code by typing::

    verdi code show 73

Which will give us an output similar to the following::

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

What is important to keep from the above is that we have informed AiiDA for the
existence of a code that resides at a specific location and we have also
specified the `default plugin` that will be used. This will be covered in one
of the following sections, the `output plugin section`.

Input plugin
------------
In abstract term, this plugin must contain the following two pieces of
information:

* what are the input objects of the calculation;

* how to convert the input object in an input file

Let's have a look at the `input plugin` developed for the aforementioned
summation code::

    # -*- coding: utf-8 -*-

    from aiida.orm import JobCalculation
    from aiida.orm.data.parameter import ParameterData
    from aiida.common.utils import classproperty
    from aiida.common.exceptions import InputValidationError
    from aiida.common.exceptions import ValidationError
    from aiida.common.datastructures import CalcInfo, CodeInfo
    import json

    __copyright__ = u"Copyright (c), 2015, ECOLE POLYTECHNIQUE FEDERALE DE LAUSANNE " \
                    u"(Theory and Simulation of Materials (THEOS) and National Centre " \
                    u"for Computational Design and Discovery of Novel Materials (NCCR MARVEL)), " \
                    u"Switzerland and ROBERT BOSCH LLC, USA. All rights reserved."
    __license__ = "MIT license, see LICENSE.txt file"
    __version__ = "0.4.1"

    class SumCalculation(JobCalculation):
        """
        A generic plugin for calculations based on the ASE calculators.

        Requirement: the node should be able to import ase
        """

        def _init_internal_params(self):
            super(SumCalculation, self)._init_internal_params()

            self._INPUT_FILE_NAME = 'in.json'
            self._OUTPUT_FILE_NAME = 'out.json'
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
            input_filename = tempfolder.get_abs_path(self._INPUT_FILE_NAME)
            with open(input_filename, 'w') as infile:
                json.dump(input_json, infile)

            # ============================ calcinfo ================================

            calcinfo = CalcInfo()
            calcinfo.uuid = self.uuid
            calcinfo.local_copy_list = []
            calcinfo.remote_copy_list = []
            calcinfo.retrieve_list = [self._OUTPUT_FILE_NAME]

            codeinfo = CodeInfo()
            codeinfo.cmdline_params = [self._INPUT_FILE_NAME,self._OUTPUT_FILE_NAME]
            codeinfo.code_uuid = code.uuid
            calcinfo.codes_info = [codeinfo]

            return calcinfo


The above input plug-in can be downloaded from here
(:download:`here <sum_calc.py>`) and should be place at ``aiida/orm/calculation/job/sum.py``.

In order the plugin to be discoverable, it is important to:

* give the right name to the file. This should be the name of your input plugin;

* place the plugin ``aiida/orm/calculation/job``;

* name the class inside the plugin as plug_in_nameCalculation. For example, the
  class name of the summation input plugin is, as you see above, `SumCalculation`;

* inherit from ``JobCalculation``. Otherwise the plugin will not work.

By doing the above, your plugin will be able to be loaded with ``CalculationFactory``.

.. note:: The base ``Calculation`` class should only be used as the abstract
  base class. Any calculation that needs to run on a remote scheduler must
  inherit from  :class:`~aiida.orm.calculation.job.JobCalculation`, that
  contains all the methods to run on a remote scheduler, get the calculation
  state, copy files remotely and retrieve them, ...

The kind of parameters that the input plugin expect is defined by the following
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

This specific summation plugin, expects one input parameter which is of the
type ``ParameterData``. The parameters is retrieved using the link name
``parameters`` specified above with the following line::

    parameters = inputdict.pop(self.get_linkname('parameters'))

Since one of the main goals of the input plugin is to prepare the input that
will be passed to the code, the following lines write to a file what is stored
in the ``parameters`` variable::

    input_json = parameters.get_dict()

    # write all the input to a file
    input_filename = tempfolder.get_abs_path(self._INPUT_FILE_NAME)
    with open(input_filename, 'w') as infile:
        json.dump(input_json, infile)

Since the input file is ready, we can now create the calculation info and link the
current calculation object to it::

    calcinfo.uuid = self.uuid


define the output files that will be retrieved after the code execution::

   calcinfo.retrieve_list = [self._OUTPUT_FILE_NAME]

define the parameters that should be passed to the code::

    codeinfo.cmdline_params = [self._INPUT_FILE_NAME,self._OUTPUT_FILE_NAME]

and link the code to the ``codeinfo`` object. Also the code is linked to the
calculation::

    calcinfo.codes_info = [codeinfo]

By doing all the above, we clarify what parameters should be passed to which
code, we have prepared the input file that the code will access and we let also
AiiDA know the name of the output file!

Submission script
-----------------

To submit the code, we don't necessarily need a submission script but it
definitely facilitates the calculation submission especially now that we are
not yet experts. A sample script to submit the summation calculation is the
following::

    #!/usr/bin/env python
    # -*- coding: utf-8 -*-
    from aiida import load_dbenv

    __copyright__ = u"Copyright (c), 2015, ECOLE POLYTECHNIQUE FEDERALE DE LAUSANNE " \
                    u"(Theory and Simulation of Materials (THEOS) and National Centre " \
                    u"for Computational Design and Discovery of Novel Materials (NCCR MARVEL)), " \
                    u"Switzerland and ROBERT BOSCH LLC, USA. All rights reserved."
    __license__ = "MIT license, see LICENSE.txt file"
    __version__ = "0.4.1"

    load_dbenv()

    import sys
    import os

    from aiida.common.exceptions import NotExistent

    from aiida.orm import Code, DataFactory

    ################################################################

    if __name__ == "__main__":

        codename = 'sum@user_pc'

        ParameterData = DataFactory('parameter')

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

        #####

        code = Code.get_from_string(codename)

        parameters = ParameterData(dict={'x1':2,'x2':2,})

        calc = code.new_calc()
        calc.label = "Test sum"
        calc.description = "Test calculation with the sum code"
        calc.set_max_wallclock_seconds(30*60) # 30 min
        calc.set_withmpi(False)
        # Valid only for Slurm and PBS (using default values for the
        # number_cpus_per_machine), change for SGE-like schedulers
        calc.set_resources({"num_machines": 1, "num_mpiprocs_per_machine": 2})

        ## Otherwise, to specify a given # of cpus per machine, uncomment the following:
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

What is important to maintain from the above script is the definition of the code
to be used::

    codename = 'sum@user_pc'
    code = Code.get_from_string(codename)

and the definitation of the parameters::

    parameters = ParameterData(dict={'x1':2,'x2':2,})
    calc.use_parameters(parameters)

If everything is done correctly, the scipt will launch a calculation for the
code ``sum@user_pc``, it will provide parameters of the type ``ParameterData``
that the input plugin (calculation), will write them into a file and it will
pass the to the right code.

When the code finishes its execution, AiiDA should retrieve the results that
will also be in a file and store them back to the AiiDA ecosystem. This procedure
is done by the `output plugin` which is also named as `parser` and it will be
explained in the sequel. You can download the submission script from
:download:`here <sum_submission.py>`.

Output plugin
-------------

The following is a sample output plugin for the summation code::

    # -*- coding: utf-8 -*-

    from aiida.orm.calculation.job.sum import SumCalculation
    from aiida.parsers.parser import Parser
    from aiida.parsers.exceptions import OutputParsingError
    from aiida.orm.data.parameter import ParameterData

    import json

    __copyright__ = u"Copyright (c), 2015, ECOLE POLYTECHNIQUE FEDERALE DE LAUSANNE " \
                    u"(Theory and Simulation of Materials (THEOS) and National Centre " \
                    u"for Computational Design and Discovery of Novel Materials (NCCR MARVEL)), " \
                    u"Switzerland and ROBERT BOSCH LLC, USA. All rights reserved."
    __license__ = "MIT license, see LICENSE.txt file"
    __version__ = "0.4.1"

    class SumParser(Parser):
        """
        This class is the implementation of the Parser class for Sum.
        """
        _outarray_name = 'output_data'

        def __init__(self, calculation):
            """
            Initialize the instance of SumParser
            """
            # super(SumParser, self).__init__(calculation)
            super(SumParser, self).__init__(Parser)
            # check for valid input
            if not isinstance(calculation,SumCalculation):
                raise OutputParsingError("Input calc must be a SumCalculation")
            self._calc = calculation

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
            if self._calc._OUTPUT_FILE_NAME not in list_of_files:
                successful = False
                self.logger.error("Output json not found")
                return successful,()

            try:
                with open( out_folder.get_abs_path(self._calc._OUTPUT_FILE_NAME) ) as f:
                    out_dict = json.load(f)
            except ValueError:
                successful=False
                self.logger.error("Error parsing the output json")
                return successful,()

            # save the arrays
            output_data = ParameterData(dict=out_dict)
            link_name = 'output_data'
            new_nodes_list = [(link_name, output_data)]

            return successful,new_nodes_list

As mentioned above the `output plugin` will `parse` the output of the executed
code at the remote computer and it will store the results to the AiiDA database.

More specifically it gets the folder containing the calculation data::

    out_folder = retrieved[self._calc._get_linkname_retrieved()]

and it loads the specific file that will contain the code execution result::

    with open( out_folder.get_abs_path(self._calc._OUTPUT_FILE_NAME) ) as f:
        out_dict = json.load(f)

Remember that we have set the filename of the output file of the code at the
`input plugin` and now the `output plugin` can easily retrieve its name from
``elf._calc._OUTPUT_FILE_NAME``.

After loading the code result data to a dictionary::

    out_dict = json.load(f)

we construct a ``ParameterData`` object (``ParameterData(dict=out_dict)``)
that will be linked to the calculation in the AiiDA graph & will be stored
in the database::

    output_data = ParameterData(dict=out_dict)
    link_name = 'output_data'
    new_nodes_list = [(link_name, output_data)]

    return successful,new_nodes_list

The above `output plugin` can be downloaded from :download:`here <sum_parser.py>`
and should be placed at ``aiida/parsers/plugins/sum.py``.

Conclusion
----------
We have just managed to write our first AiiDA plugin! What is important to
maintain is that:

* AiiDA doesn't know how to execute your code. Therefore, you have to setup
  your code (with ``verdi code setup``) and let AiiDA know how to prepare the
  data that will be given to the code (`input plugin` \ `calculation`) and how
  to handle the result of the code (`output plugin` \ `parser`)

* you need to do some preliminary steps to submit your code (`submission
  script`)

It is also very useful to have a general understanding of what is executed &
where and which are the results of you computation.

Now that we have managed to execute the above, we can see the executed calculations
by doing a ``verdi calculation list``. More precisely, let's see the calculations
of the last day::

    $ verdi calculation list -a -p1
    # Last daemon state_updater check: 0h:00m:06s ago (at 20:10:31 on 2015-10-20)
    # Pk|State        |Creation|Sched. state|Computer |Type
    327 |FINISHED     |4h ago  |DONE        |user_pc  |sum

As we can see our calculation has finished successfully. We can also see the
various files that were created in the different stages. These are stored in
a specific directory just for this code and can be visited using the ``Pk`` of
that calculation::

    aiida_user@user_pc:/home/aiida_user$ verdi calculation gotocomputer 327
    Loading environment...
    Going the the remote folder...
    aiida_user@user_pc:/scratch/aiida_run/d7/4e/ac9b-6303-4ce7-a933-afdf31b874a2$ ls
    _aiidasubmit.sh  in.json  out.json  _scheduler-stderr.txt  _scheduler-stdout.txt

As you can see, in this folder, you can find the ``in.json`` which is the file
that was prepared by the `input plugin` and will be given as input to the code
that will be executed::

    aiida_user@user_pc:/scratch/aiida_run/d7/4e/ac9b-6303-4ce7-a933-afdf31b874a2$ cat in.json
    {"x2": 2, "x1": 2}

You can also find the ``out.json`` which is the output
of the executed code which will be parsed by the `output plugin` \ `parser`
that you have developed above::

    aiida_user@user_pc:/scratch/aiida_run/d7/4e/ac9b-6303-4ce7-a933-afdf31b874a2$ cat out.json
    {"sum": 4}

It is also interesting, for your general understanding to have a look at how
the code is launched. This is in the ``_aiidasubmit.sh`` and for a `PBS`
scheduler, it should look like the following::

    #!/bin/bash

    #PBS -r n
    #PBS -m n
    #PBS -N aiida-327
    #PBS -V
    #PBS -o _scheduler-stdout.txt
    #PBS -e _scheduler-stderr.txt
    #PBS -l walltime=00:30:00
    #PBS -l select=1:mpiprocs=2
    cd "$PBS_O_WORKDIR"

    '/home/aida_user/codes/sum_executable.py' 'in.json' 'out.json'

where it is clear the code that is executed, where it is placed and the
arguments that are passed to it.
