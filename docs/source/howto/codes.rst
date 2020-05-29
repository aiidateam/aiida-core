.. _how-to:codes:

*************************
How to run external codes
*************************

To run an external code with AiiDA, you will need to use an appropriate :ref:`calculation plugin <topics:plugins>`.
This plugin must contain the instructions necessary for the engine to be able to:

1. Prepare the required input files inside of the folder in which the code will be executed
2. Run the code with the correct set of command line parameters

The following subsections will not only take you through the process of :ref:`creating the calculation plugin<how-to:codes:interfacing>` and then using these to actually :ref:`run the code<how-to:codes:run>`.
It will also show examples on how to implement tools that are commonly coupled with the running of a calculation, such as :ref:`the parsing of outputs<how-to:codes:parsing>`, :ref:`the communication with external machines<how-to:codes:transport>` and the interaction with its :ref:`scheduling software<how-to:codes:scheduler>`.

Some general guidelines to keep in mind are:

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
   | Functionality at deeper nesting levels is not considered part of the public API and may change between minor AiiDA releases, breaking your plugin.
 * | **Parse what you want to query for.**
   | Make a list of which information to:

     #. parse into the database for querying (:py:class:`~aiida.orm.nodes.data.dict.Dict`, ...)
     #. store in the file repository for safe-keeping (:py:class:`~aiida.orm.nodes.data.singlefile.SinglefileData`, ...)
     #. leave on the computer where the calculation ran (:py:class:`~aiida.orm.nodes.data.remote.RemoteData`, ...)

To demonstrate how to create a plugin for an external code, we will use the trivial example of using the `bash` shell (``/bin/bash``) to sum two numbers by running the command: ``echo $(( numx + numy ))``.
Here, the `bash` binary will be effectively acting as our |Code| executable, the input (``aiida.in``) will then be a file containing the command with the numbers provided by the user replaced, and the output (``aiida.out``) will be caught through the standard output.
The final recipe to run this code will then be:

.. code-block:: bash

    /bin/bash < aiida.in > aiida.out

.. _how-to:codes:interfacing:

Interfacing external codes
==========================

To provide AiiDA with the set of instructions, required to run a code, one should implement the |CalcJob| class, which has the following two key methods:

.. code-block:: python

    from aiida.engine import CalcJob
    from aiida import orm

    class ArithmeticAddCalculation(CalcJob):

        @classmethod
        def define(cls, spec):
            """Set up the specifications for the inputs and outputs (and exit_codes)."""

        def prepare_for_submission(self, folder):
            """Prepare the input files and code configuration based on the provided inputs."""

We will now show how each of these can be implemented.

Defining the specifications
---------------------------

As the comment in the code above indicates, the first method (|define|) is where one specifies the different inputs that the user of the |CalcJob| will have to provide in order to run the code, as well as the outputs that will be produced (exit codes are discussed in the respective section).
This is done through the |spec| object, which, as can be seen, is passed as an argument to the method.
For the code that adds up two numbers, we will need to define those numbers as inputs (lets call them ``x`` and ``y`` to label them) and the result as an output (``sum``).

.. code-block:: python
   :linenos:

    @classmethod
    def define(cls, spec):
        """Set up the specifications for the inputs and outputs (and exit_codes)."""

        super().define(spec)
        spec.inputs['metadata']['options']['input_filename'].default = 'aiida.in'
        spec.inputs['metadata']['options']['output_filename'].default = 'aiida.out'

        spec.input('x', valid_type=orm.Int, help='The left operand.')
        spec.input('y', valid_type=orm.Int, help='The right operand.')
        spec.output('sum', valid_type=orm.Int, help='The sum of the left and right operand.')

The first line of the method (line 5) just runs the |define| method of the parent base |CalcJob| class, which will define `inputs` and `outputs` that are common to all |CalcJob|'s.
On the second part of that first "block of code" (lines 6+7), we are modifying some properties of a couple of these base `inputs`.

The second block (lines 9-11) seems similar to the previous one, but has a subtle difference: it is not modifying existing `inputs`/`outputs` but defining new ones that will be specific to this implementation.
You can spot the difference in that the definition of new `inputs` uses the ``spec.input`` method (note `input` is singular here), whereas existing inputs are accessed through the ``spec.inputs`` property (where `inputs` is now plural).
You can also see that the definitions do not involve the assignment of a value, but only the passing of parameters to the method: a label to identify it, their valid types (in this case AiiDA nodes of type |Int|) and a description.

Finally, note that there is no return statement: this method does not need to return anything, since all modifications are made directly into the received |spec| object.

You can check the Topics section about :ref:`defining processes <topics:processes:usage:defining>` if you want more information about setting up your `inputs` and `outputs` (covering validation, dynamic number of inputs, etc.).

Preparing for submission
------------------------

This is the method where one implements the main two functions of the |CalcJob|, as the required input files can be written by using the |Folder| object that the method receives as an argument, and the instructions on how the code should be run will be set during the construction of a |CalcInfo| object, which will be finally returned by the method.

.. code-block:: python
   :linenos:

    def prepare_for_submission(self, folder):
        """Prepare the input files and code configuration based on the provided inputs."""

        input_x = self.inputs['x']
        input_y = self.inputs['y']
        input_code = self.inputs['code']
        input_filename = self.inputs['metadata']['options']['input_filename']
        output_filename = self.inputs['metadata']['options']['output_filename']

        with folder.open(input_filename, 'w', encoding='utf8') as handle:
            handle.write('echo $(( {} + {} ))\n'.format(input_x.value, input_y.value))

        codeinfo = CodeInfo()
        codeinfo.code_uuid = input_code.uuid
        codeinfo.stdin_name = input_filename
        codeinfo.stdout_name = output_filename

        calcinfo = CalcInfo()
        calcinfo.codes_info = [codeinfo]
        calcinfo.retrieve_list = [output_filename]

        return calcinfo

The first block of code (lines 4-8) is just unpacking the inputs that have been passed, which can be accessed through ``self.inputs``, into local variables.
Note that, unlike in the |define| method, this one is implemented from scratch and so there is no call to a ``super().define(folder)`` method.

The input required by the addition "code" just contains a `bashscript` line with the value of the input nodes replaced appropriately.
This is being created on lines 10 and 11, using the |folder.open| method to get a handle to the file and simply writing in it.
This directory represented by the |Folder| object (along with all the files created in it) will not only be copied to the remote machine for the code to be run there, but will also be stored in the local repository of the calculation node.

Next in lines 13-16 we are creating and setting up the ``codeinfo = CodeInfo()`` object.
The ``code_uuid`` that is passed in line 14 is necessary for the engine to get the required information from the |Code| node (such as the full path of the executable, etc.).
Note that this was taken in the unloading block from ``input_code = self.inputs['code']``, which we never specified in the |define| method: this is one of the inputs defined in the base |CalcJob| class that we mentioned earlier when discussing the ``super().define(spec)``:

.. code-block:: python

    spec.input('code', valid_type=orm.Code, help='The `Code` to use for this job.')

Moreover, as this information is necessary for the engine, this input has a ``required=True`` setting (the default for all inputs, including the ones we manually defined earlier).
For the plugin user this means they will have to provide it when instantiating the calculation (as can be seen in the :ref:`respective section<how-to:codes:run>` below), whereas for the plugin developer this means they will have to make sure to manually pass its UUID from the ``self.inputs['code']`` node to the ``codeinfo.code_uuid`` property, as shown here.

The other two lines are configuring how to build the running script: line 15 indicates where to take the standard input from, whereas line 16 specifies where to redirect the standard output.
Together with the information taken from the provided |Code| node, the resulting script that will be created by the engine will be the following:

.. code-block:: bash

    #!/bin/bash

    '[executable path in code node]' < '[input_filename]' > '[output_filename]'

Through the |CodeInfo| object you can also pass command line arguments (such as flags or additional inputs), add commands to be run before and after the execution line, etc.

Finally, the last block remaining in lines 18-20 creates the |CalcInfo| object, passes to it the |CodeInfo| object, and adds the output to the ``retrieve_list``.
This is a list of all files that the code will produce that the engine should copy from the computer where the code ran into an output node labeled ``retrieved``.
The ``retrieved`` node is an ``output`` defined in the base |CalcJob| class.
There are other lists available that allow you to easily customize how to move files to and from the remote working directory in order to prevent the creation of unnecessary copies.

In the Topics section on :ref:`defining calculations <topics:calculations:usage>` you will find more information on available settings of the |CalcInfo| and |CodeInfo|, such as available copy lists, running script options, etc.

.. _how-to:codes:parsing:

Parsing the outputs
===================

The parsing step occurs after the calculation has finished running and all the relevant outputs have been retrieved.
It is an optional step that allows you to extract relevant information from the output files and store it into AiiDA nodes in formats that are easier and quicker to query and analyze.
To parse retrieved files into nodes that can be stored in the database, one should implement the |Parser| class:

.. code-block:: python
   :linenos:

    from aiida.parsers.parser import Parser
    from aiida.common import exceptions
    from aiida import orm

    class ArithmeticAddParser(Parser):

        def parse(self, **kwargs):
            """Parse the contents of the retrieved output files into nodes."""

            output_folder = self.retrieved
            output_filename = self.node.get_option('output_filename')

            with output_folder.open(output_filename, 'r') as handle:
                result = int(handle.read())

            self.out('sum', orm.Int(result))

The first command in the example (line 10) shows how to get the ``retrieved`` folder that was generated by the associated |CalcJob|, which contains the files included in the ``retrieve_list`` (as specified in the |prepare_for_submission| method).
The second one (line 11) retrieves the name of the output file that was defined in the inputs when the |CalcJob| was launched.
Lines 13 and 14 show how the content of the output file in the output folder is read, which should be the sum as written by the code, and cast to an integer.
Finally, the parsed sum is wrapped into an |Int| node, which allows it to be registered as the ``sum`` output through the ``out`` method.

To trigger the parsing using a |Parser| after a |CalcJob| has finished (such as the one described in the :ref:`previous section <how-to:codes:interfacing>`) its entry point name needs to be passed as the ``metadata.options.parser_name`` input.
If a particular parser should always be used by default for a given |CalcJob|, it can be defined as the default in the |define| method.

.. code-block:: python

    @classmethod
    def define(cls, spec):
        (...)
        spec.inputs['metadata']['options']['parser_name'].default = 'arithmetic.add'

Note that this default can be overridden through the inputs when launching the calculation job.
To define the parser that should be used, one should not pass the |Parser| class itself, but rather the corresponding entry point name under which it is registered as a plugin.
In other words, in order to use a |Parser| you will need to register it as explained in the following how-to section on :ref:`registering plugins <how-to:plugins>`.

Handling parsing errors
-----------------------

So far we have assumed in the implementation of the |Parser| that the code executed nominally and produced the correct output.
For this trivial example this is likely the case, but for many codes there can be a variety of errors that prevent it from producing the desired result.
These exit codes can be defined through the |spec| of the |CalcJob| that is used for that code, just as the inputs and output are defined
The parser can be used to detect these problems and communicate them to the caller by returning an `exit code`.
An `exit code` is a positive integer that corresponds to a particular known and well-defined error mode of a code.

.. code-block:: python

    @classmethod
    def define(cls, spec):
        (...)
        spec.exit_code(300, 'ERROR_NO_RETRIEVED_FOLDER', message='The retrieved folder data node could not be accessed.')
        spec.exit_code(310, 'ERROR_READING_OUTPUT_FILE', message='The output file could not be read from the retrieved folder.')
        spec.exit_code(320, 'ERROR_INVALID_OUTPUT', message='The output file contains invalid output.')

As you can see, for each ``exit_code`` we have provided an exit status (a positive integer), a label that can be used to reference the code in the |parse| method (through the ``self.exit_codes`` method, as seen below), and a message that provides a more detailed information on the problem.

To use these in the |parse| method, you just need to return the corresponding exit code and then the engine will know when to set it on the corresponding calculation job node.

.. code-block:: python
   :linenos:

    def parse(self, **kwargs):
        """Parse the contents of the retrieved output files into nodes."""

        try:
            output_folder = self.retrieved
        except exceptions.NotExistent:
            return self.exit_codes.ERROR_NO_RETRIEVED_FOLDER

        output_filename = self.node.get_option('output_filename')

        try:
            with output_folder.open(output_filename, 'r') as handle:
                try:
                    result = int(handle.read())
                except ValueError:
                    return self.exit_codes.ERROR_INVALID_OUTPUT
        except OSError:
            return self.exit_codes.ERROR_READING_OUTPUT_FILE


        self.out('sum', orm.Int(result))

You can see there is one for the case where no ``retrieve`` output was found (lines 4-7), another for the case of not being able to read the output file (outter ``try``/``except`` structure in lines 11-18), and finally one for when the result printed in the file is not a valid integer (inner ``try``/``except`` structure in lines 13-16).
The Topics section on :ref:`defining processes <topics:processes:usage:defining>` provides additional information on how to use exit codes.

.. todo::

    .. _how-to:codes:computers:

    title: Configuring remote computers

    `#4123`_

.. _how-to:codes:run:

Running external codes
======================

To run an external code with AiiDA, you will need to use an appropriate :ref:`calculation plugin <topics:plugins>` that knows how to transform the input nodes into the input files that the code expects, copy everything in the code's machine, run the calculation and retrieve the results.
You can check the `plugin registry <https://aiidateam.github.io/aiida-registry/>`_ to see if a plugin already exists for the code that you would like to run.
If that is not the case, you can :ref:`develop your own <how-to:codes:interfacing>`.
After you have installed the plugin, you can start running the code through AiiDA.
To check which calculation plugins you have currently installed, run:

.. code-block:: bash

    $ verdi plugin list aiida.calculations

As an example, we will show how to use the ``arithmetic.add`` plugin, which is a pre-installed plugin that uses the `bash shell <https://www.gnu.org/software/bash/>`_ to sum two integers.
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
If you already have these nodes in your database, you can get them by :ref:`querying for them <how-to:data:find>` or using ``orm.load_node(<PK>)``.
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

.. todo::

    .. _how-to:codes:caching:

    title: Using caching to save computational resources

    `#3988`_


    .. _how-to:codes:scheduler:

    title: Adding support for a custom scheduler

    `#3989`_


    .. _how-to:codes:transport:

    title: Adding support for a custom transport

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
.. |prepare_for_submission| replace:: :py:class:`~aiida.engine.processes.calcjobs.CalcJob.prepare_for_submission`

.. _#3988: https://github.com/aiidateam/aiida-core/issues/3988
.. _#3989: https://github.com/aiidateam/aiida-core/issues/3989
.. _#3990: https://github.com/aiidateam/aiida-core/issues/3990
.. _#4123: https://github.com/aiidateam/aiida-core/issues/4123
