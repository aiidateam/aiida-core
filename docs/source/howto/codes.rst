.. _how-to:codes:

*************************
How to run external codes
*************************

To run an external code with AiiDA, you will need to use an appropriate :ref:`calculation plugin <topics:plugins>`.
Its job is to orchestrate the whole process that starts with transforming the input nodes to the input files that the code expects, then copy everything to the machine where the code is located (using a :ref:`transport plugin <how-to:codes:transport>`), run the actual code (using a :ref:`scheduler plugin <how-to:codes:scheduler>`), and finally get back the outputs and, optionally, parse them into queryable AiiDA nodes (using a :ref:`parser plugin <how-to:codes:parser>`).

The following subsections will take you through the process of :ref:`creating the calculation plugin<how-to:codes:interfacing>` and its acompanying :ref:`parser<how-to:codes:parsing>`, and then using these to actually :ref:`run the code<how-to:codes:run>`.
Other supporting sections are also included.

As the underlying example for these we will use the process of using the `bash` interpreter (``/bin/bash``) to add up two numbers by running the command: ``echo $(( numx + numy ))``.
Here, the `bash` binary will be effectively acting as our |Code| executable, the input (``aiida.in``) will then be a file containing the command with the numbers provided by the user replaced, and the output (``aiida.out``) will be caught through the standard output.
The final recipe to run this code will then be:

.. code-block:: bash

    /bin/bash aiida.in > aiida.out

.. _how-to:codes:interfacing:

Interfacing external codes
==========================

The way you provide AiiDA with the set of instructions required to run a code is by extending the |CalcJob| class, which has the following two key methods:

.. code-block:: python

    from aiida.engine import CalcJob

    class ArithmeticAddCalculation(CalcJob):

        @classmethod
        def define(cls, spec):
            super().define(spec)
            # Specifications of the inputs and outputs (and exit codes).
            # no return statement

        def prepare_for_submission(self, folder):
            # No super call to parent class method
            # Preparation of input files and instructions for engine
            return calcinfo

We will now indicate how to deal with each of them separatedly.

Defining the specifications
---------------------------

As the comment in the code above indicates, the first method (|define|) is where one specifies the different inputs that the user of the |CalcJob| will have to provide in order to run the code, as well as the outputs that will be produced (exit codes are discussed in the respective section).
This is done through the |spec| object, which, as can be seen, is passed as an input to the method.
For the code that adds up two numbers, we will need to define those numbers as inputs (lets call them ``x`` and ``y`` to label them) and the result as an output (``sum``).

.. code-block:: python
   :linenos:

    @classmethod
    def define(cls, spec):
        from aiida import orm
        super().define(spec)

        spec.output('sum', valid_type=orm.Int, help='The sum of the left and right operand.')
        spec.input('x', valid_type=orm.Int, help='The left operand.')
        spec.input('y', valid_type=orm.Int, help='The right operand.')

        spec.inputs['metadata']['options']['input_filename'].default = 'aiida.in'
        spec.inputs['metadata']['options']['output_filename'].default = 'aiida.out'

The first line after the import just runs the |define| method of the parent base |CalcJob| class, which will do some set-ups and define some basic `inputs` and `outputs` (we will see some of them shortly).
The second "block of code" (lines 6-8), is where we are defining the specific inputs and outputs for the code, specifying their valid type (in this case AiiDA nodes of type |Int|) and a help message for the users of the class.

The last block (lines 10+11) seems similar to the previous one, but has a subtle difference: it is not defining new `inputs`, but modifying some properties of the base `inputs` that are already defined in the parent |CalcJob| class.
You can spot the difference in that the definition of new `inputs` uses the ``spec.input`` method, singular, whereas accessing is achieved via the ``spec.inputs`` method, plural.

You can check the Topics section about :ref:`defining processes <topics:processes:usage:defining>` if you want more information about setting up your `inputs` and `outputs` (covering validation, dynamic number of inputs, etc).

Preparing for submission
------------------------

There are two main tasks to take care of in this method: preparing the folder in which the code will be run (so that all required input files are correctly built or copied there) and setting up the configuration of the engine.
The first one is achieved by manipulating the |Folder| object that the method receives as an input, whereas the second one requires the construction of the |CalcInfo| object (which is then returned by the method) and the |CodeInfo| object (which will be included in the |CalcInfo| one, see line 18 in the following code snippet).

.. code-block:: python
   :linenos:

    def prepare_for_submission(self, folder):

        input_x = self.inputs['x']
        input_y = self.inputs['y']
        input_code = self.inputs['code']
        input_filename = self.inputs['metadata']['options']['input_filename']
        output_filename = self.inputs['metadata']['options']['output_filename']

        with folder.open(input_filename, 'w', encoding='utf8') as handle:
            handle.write('echo $(( {} + {} ))\n'.format(input_x.value, input_y.value))

        codeinfo = CodeInfo()
        codeinfo.code_uuid = input_code.uuid
        codeinfo.stdout_name = output_filename
        codeinfo.cmdline_params = [input_filename]

        calcinfo = CalcInfo()
        calcinfo.codes_info = [codeinfo]
        calcinfo.retrieve_list = [output_filename]

        return calcinfo

The first block of code (lines 3-7) is just the unloading of the information stored in the ``spec`` into local variables.
Note that this information is not accessed via the ``spec.inputs`` anymore, but by ``self.inputs``: by the time this method is executed the specs will have become properties of the |CalcJob| and now should contain the actual inputs provided by the user.

The input required by the addition "code" is just a `bashscript` line with the value of the input nodes replaced appropriately.
This is being created on line 9, using the |folder.open| method to get a handle to the file and simply wirting in it.
This directory represented by the |Folder| object (along with all the files created in it) will not only be copied to the remote machine for the code to be run there, but will also be stored in the local repository of the calculation node.

Next in lines 12-15 we are creating and setting up the ``codeinfo = CodeInfo()`` object.
The ``code_uuid`` being passed in line 13 is necessary for the engine to get the base information from the |Code| node (in which computer the code is placed, what is the location of the executable, etc).
Note that this was taken in the unloading block from ``input_code = self.inputs['code']``, which we never specified in the |define| method: this is one of the inputs defined in the base |CalcJob| class that we mentioned earlier when discussing the ``super().define(spec)``:

.. code-block:: python

    spec.input('code', valid_type=orm.Code, help='The `Code` to use for this job.')

Moreover, as this information is necessary for the engine, this input has a ``required=True`` setting (the default for all inputs, including the ones we manually defined earlier).
For the plugin user this means they will have to provide it when instantiating the calculation (as can be seen in the :ref:`respective section<how-to:codes:run>` below), whereas for the plugin developer this means they will have to make sure to manually pass its UUID from the ``self.inputs['code']`` node to the ``codeinfo.code_uuid`` property, as shown here.

The other two lines are configuring how to build the running script: line 14 indicates where to redirect the standard output, whereas line 15 lists the command line arguments to be passed to the code.
The specific combination presented here, together with the information inside of the |Code| node, results in the following script:

.. code-block:: bash

    #!/bin/bash

    '[executable path in code node]' '[input_filename]' > '[output_filename]'

Through the |CodeInfo| object you can also pass more flags (by adding them as string elements to the list in ``codeinfo.cmdline_params``), configure what to pass through the standard input (just as it is shown for the standard output), add commands to be run before and after the execution line, etc.

Finally, the last block remaining in lines 17-19 creates the |CalcInfo| object, passes to it the |CodeInfo| object, and adds the output to the ``retrieve_list``.
This is a list of all files that the engine needs to copy back from the computer where the code is located, either for immediate parsing or local storage in an output node labeled ``retrieved`` for future post-processing.
The ``retrieved`` node is a ``output`` defined in the base |CalcJob| class.
There are other lists available that allow you to easily customize how to move files to and from the remote working directory in order to prevent the creation of unnecessary copies.

In the Topics section on :ref:`defining calculations <topics:calculations:usage>` you will find more information on available settings of the |CalcInfo| and |CodeInfo|, such as available copy lists, running script options, etc.

Design guidelines
-----------------

 * | **Check existing resources.**
   | Before starting to write a plugin, check on the `aiida plugin registry <https://aiidateam.github.io/aiida-registry/>`_ whether a plugin for your code is already available.
 * | **Start simple.**
   | Make use of existing classes like :py:class:`~aiida.orm.nodes.data.dict.Dict`, :py:class:`~aiida.orm.nodes.data.singlefile.SinglefileData`, ...
   | Write only what is necessary to pass information from and to AiiDA.
 * | **Don't break data provenance.**
   | Store *at least* what is needed for full reproducibility.
 * | **Expose the full functionality.**
   | Standardization is good but don't artificially limit the power of a code you are wrapping - or your users will get frustrated.
   | If the code can do it, there should be *some* way to do it with your plugin.
 * | **Don't rely on AiiDA internals.**
   | AiiDA's :ref:`public python API<python_api_public_list>` includes anything that you can import via ``from aiida.module import thing``.
   | Functionality at deeper nesting levels is not considered part of the public API and may change between minor AiiDA releases, breaking your plugin.

.. _how-to:codes:parsing:

Parsing the outputs
===================

The parsing step occurs after the calculation has finished running and all the relevant outputs have been retrieved.
It is an optional step that allows you to extract relevant information from the output files and store it into AiiDA nodes in formats that are easier and quicker to query and analyze.
The way to implement this is by extending the base |Parser| class as you can see below:

.. code-block:: python
   :linenos:

    from aiida.parsers.parser import Parser
    from aiida import orm

    class ArithmeticAddParser(Parser):

        def parse(self, **kwargs):

            output_folder = self.retrieved
            output_filename = self.node.get_attribute('output_filename')

            with output_folder.open(output_filename, 'r') as handle:
                result = int(handle.read())

            self.out('sum', orm.Int(result))

The first command in the example (line 8) shows the way to get the ``retrieve`` folder that was generated by the associated |CalcJob| and that, by this point, should contain the files included in the ``retrieve_list`` (as specified in the |prepare_for_submission| method).
The second one (line 9) is also accessing a parameter of the |CalcJob|: in this case, the name of the output.
After unloading this information into local variables, these are then used to open said output file located in the obtained retrieved folder and read the single integer value that was written there by the addition |Code| (lines 11 and 12).

Finally, it uses the ``out`` method to provide the ``sum`` output of the calculation its final value (of type AiiDA integer, as was specified in the |define| section of the associated |CalcJob|).
It is important to note here that there is no return statement: the output is provided to the ``self.out`` method instead (any returned value is interpreted as an error signal) as an unstored node, and the engine will be in charge of performing the storing process.

In order to use this ``ArithmeticAddParser`` inside an appropriate |CalcJob| (such as the one described in the :ref:`previous section <how-to:codes:interfacing>`), one needs to add it as a `metadata.options.parser_name` input.
You can set a parser as the default option in the |define| method, but note that this choice can be overriden when instantiating the |CalcJob|.

.. code-block:: python

    @classmethod
    def define(cls, spec):
        (...)
        spec.inputs['metadata']['options']['parser_name'].default = 'arithmetic.add'

As can be seen in the previous line, the way to do this is not by passing the |Parser| class directly, but by providing the string label that identifies the |Parser| as a registered plugin in your working environment.
In other words, in order to use a |Parser| you will need to register it as explained in the following how-to section on :ref:`registering plugins <how-to:plugins>`.

Handling parsing errors
-----------------------

In order for you to be able to provide the user with information regarding the errors that can ocur after the calculation has finished (so, mostly during parsing), you have the option of defining ``exit_codes`` for cases when something goes wrong.
The typical way to implement these is to use ``try``/``except`` clauses to wrap the lines of code that might raise some typical errors, that can then be replaced by these ``exit_codes``:

.. code-block:: python
   :linenos:

    def parse(self, **kwargs):
        from aiida.common import exceptions

        try:
            output_folder = self.retrieved
        except exceptions.NotExistent:
            return self.exit_codes.ERROR_NO_RETRIEVED_FOLDER

        output_filename = self.node.get_attribute('output_filename')

        try:
            with output_folder.open(output_filename, 'r') as handle:
                try:
                    result = int(handle.read())
                except ValueError:
                    result = None
        except (OSError, IOError):
            return self.exit_codes.ERROR_READING_OUTPUT_FILE

        if result is None:
            return self.exit_codes.ERROR_INVALID_OUTPUT

        self.out('sum', orm.Int(result))

You can see there is one for the case where no ``retrieve`` output was found (lines 4-7), another for the case of not being able to read the output file (lines 11-18), and finally one for when the result printed in the file is not a valid integer (lines 20-21).
You then have to introduce all of these `exit_codes` inside of the |define| method of the |CalcJob| that will use this |Parser| (so, in that sense, when working like this the exit codes need to be "supported" by any calculation that wants to use the |Parser|).

.. code-block:: python

    @classmethod
    def define(cls, spec):
        (...)
        spec.exit_code(300, 'ERROR_NO_RETRIEVED_FOLDER', message='The retrieved folder data node could not be accessed.')
        spec.exit_code(310, 'ERROR_READING_OUTPUT_FILE', message='The output file could not be read from the retrieved folder.')
        spec.exit_code(320, 'ERROR_INVALID_OUTPUT', message='The output file contains invalid output.')

As you can see, for each ``exit_code`` you need to provide an ID number that will be used to identify it, a label you can then use to reference the code in the |parse| method (``self.exit_codes.LABEL``), and a message that will give the user more information on the problem.
The Topics section on :ref:`defining processes <topics:processes:usage:defining>` also contains more information on how to use exit codes.

Design guidelines
-----------------

 * | **Parse what you want to query for.**
   | Make a list of which information to:

     #. parse into the database for querying (:py:class:`~aiida.orm.nodes.data.dict.Dict`, ...)
     #. store in the file repository for safe-keeping (:py:class:`~aiida.orm.nodes.data.singlefile.SinglefileData`, ...)
     #. leave on the computer where the calculation ran (:py:class:`~aiida.orm.nodes.data.remote.RemoteData`, ...)

.. _how-to:codes:computers:

Configuring remote computers
============================

`#4123`_

.. _how-to:codes:run:

Running external codes
======================

To run an external code with AiiDA, you will need to use an appropriate :ref:`calculation plugin <topics:plugins>` that knows how to transform the input nodes into the input files that the code expects, copy everything in the code's machine, run the calculation and retrieve the results.
You can check the `plugin registry <https://aiidateam.github.io/aiida-registry/>`_ to see if a plugin already exists for the code that you would like to run.
If that is not the case, you can :ref:`develop your own <how-to:codes:plugin>`.
After you have installed the plugin, you can start running the code through AiiDA.
To check which calculation plugins you have currently installed, run:

.. code-block:: bash

    $ verdi plugin list aiida.calculations

As an example, we will show how to use the ``arithmetic.add`` plugin, which is a pre-installed plugin that uses the `bash shell<https://www.gnu.org/software/bash/>`_ to sum two integers.
You can access it with the ``CalculationFactory``:

.. code-block:: python

    from aiida.plugins import CalculationFactory
    calculation_class = CalculationFactory('arithmetic.add')

Next, we provide the inputs for the code when running the calculation.
Use ``verdi plugin`` to determine what inputs a specific plugin expects:

.. code-block:: bash

    $ verdi plugin list aiida.calculations arithmetic.add
    (...)
        Inputs:
               code:  required  Code        The `Code` to use for this job.
                  x:  required  Int, Float  The left operand.
                  y:  required  Int, Float  The right operand.
    (...)

You will see that 3 inputs nodes are required: two containing the values to add up (``x``, ``y``) and one containing information about the specific code to execute (``code``).
If you already have these nodes in your database, you can get them by :ref:`querying for them <how-to:data:finding-data>` or using ``orm.load_node(<PK>)``.
Otherwise, you will need to create them as shown below (note that you `will` need to already have the ``localhost`` computer configured, as explained in the :ref:`previous how-to<how-to:codes:computers>`):

.. code-block:: python

    from aiida import orm
    bash_binary = orm.Code(remote_computer_exec=[localhost, '/bin/bash'])
    number_x = orm.Int(17)
    number_y = orm.Int(11)

To provide these as inputs to the calculations, we will now use the ``builder`` object that we can get from the class:

.. code-block:: python

    calculation_builder = calculation_class.get_builder()
    calculation_builder.code = bash_binary
    calculation_builder.x = number_x
    calculation_builder.y = number_y

Now everything is in place and ready to perform the calculation, which can be done in two different ways.
The first one is blocking and will return a dictionary containing all the output nodes (keyed after their label, so in this case these should be: "remote_folder", "retrieved" and "sum") that you can safely inspect and work with:

.. code-block:: python

    from aiida.engine import run
    output_dict = run(calculation_builder)
    sum_result = output_dict['sum']

The second one is non blocking, as you will be submitting it to the daemon and control is immediately returned to the interpreter.
The return value in this case is the calculation node that is stored in the database.

.. code-block:: python

    from aiida.engine import submit
    calculation = submit(calculation_builder)

Note that, although you have access to the node, the underlying calculation `process` is not guaranteed to have finished when you get back control in the interpreter.
You can use the verdi command line interface to :ref:`monitor<topics:processes:usage:monitoring>` these processes:

.. code-block:: bash

    $ verdi process list

Performing a dry-run
--------------------

Additionally, you might want to check and verify your inputs before actually running or submitting a calculation.
You can do so by specifying to use a ``dry_run``, which will create all the input files in a local directory (``submit_test/[date]-0000[x]``) so you can inspect them before actually launching the calculation:

.. code-block:: python

    calculation_builder.metadata.dry_run = True
    calculation_builder.metadata.store_provenance = False
    run(calculation_builder)

.. _how-to:codes:caching:

Using caching to save computational resources
=============================================

`#3988`_


.. _how-to:codes:scheduler:

Adding support for a custom scheduler
=====================================

`#3989`_


.. _how-to:codes:transport:

Adding support for a custom transport
=====================================

`#3990`_


.. |Int| replace:: :py:class:`~aiida.orm.nodes.data.int.Int`
.. |Code| replace:: :py:class:`~aiida.orm.nodes.data.Code`
.. |Parser| replace:: :py:class:`~aiida.parsers.parser.Parser`
.. |parse| replace:: :py:class:`~aiida.parsers.parser.Parser.parse`
.. |folder| replace:: :py:class:`~aiida.common.folders.Folder`
.. |folder.open| replace:: :py:class:`~aiida.common.folders.Folder.open`
.. |CalcJob| replace:: :py:class:`~aiida.engine.processes.calcjobs.calcjob.CalcJob`
.. |CalcInfo| replace:: :py:class:`~aiida.common.CalcInfo`
.. |CodeInfo| replace:: :py:class:`~aiida.common.CodeInfo`
.. |spec| replace:: ``spec``
.. |define| replace:: :py:class:`~aiida.engine.processes.calcjobs.CalcJob.define`
.. |prepare_for_submission| :py:class:`~aiida.engine.processes.calcjobs.CalcJob.prepare_for_submission`

.. _#3986: https://github.com/aiidateam/aiida-core/issues/3986
.. _#3987: https://github.com/aiidateam/aiida-core/issues/3987
.. _#3988: https://github.com/aiidateam/aiida-core/issues/3988
.. _#3989: https://github.com/aiidateam/aiida-core/issues/3989
.. _#3990: https://github.com/aiidateam/aiida-core/issues/3990
.. _#4123: https://github.com/aiidateam/aiida-core/issues/4123
