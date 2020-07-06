.. _how-to:plugin-codes:

******************************************
How to write a plugin for an external code
******************************************

To run an external code with AiiDA, you will need to use an appropriate :ref:`calculation plugin <topics:plugins>`.
This plugin must contain the instructions necessary for the engine to be able to:

1. Prepare the required input files inside of the folder in which the code will be executed
2. Run the code with the correct set of command line parameters

The following subsections will not only take you through the process of :ref:`creating the calculation plugin<how-to:plugin-codes:interfacing>` and then using these to actually :ref:`run the code<how-to:plugin-codes:run>`.
It will also show examples on how to implement tools that are commonly coupled with the running of a calculation, such as :ref:`the parsing of outputs<how-to:plugin-codes:parsing>`.

.. todo::

    Add to preceding sentence: :ref:`the communication with external machines<how-to:plugin-codes:transport>` and the interaction with its :ref:`scheduling software<how-to:plugin-codes:scheduler>`.

Some general guidelines to keep in mind are:

 * | **Check existing resources.**
   | Before starting to write a plugin, check on the `aiida plugin registry <https://aiidateam.github.io/aiida-registry/>`_ whether a plugin for your code is already available.
     If it is, there is maybe no need to write your own, and you can skip straight ahead to :ref:`running the code<how-to:plugin-codes:run>`.
 * | **Start simple.**
   | Make use of existing classes like :py:class:`~aiida.orm.nodes.data.dict.Dict`, :py:class:`~aiida.orm.nodes.data.singlefile.SinglefileData`, ...
     Write only what is necessary to pass information from and to AiiDA.
 * | **Don't break data provenance.**
   | Store *at least* what is needed for full reproducibility.
 * | **Expose the full functionality.**
   | Standardization is good but don't artificially limit the power of a code you are wrapping - or your users will get frustrated.
     If the code can do it, there should be *some* way to do it with your plugin.
 * | **Don't rely on AiiDA internals.**
     Functionality at deeper nesting levels is not considered part of the public API and may change between minor AiiDA releases, breaking your plugin.
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

.. _how-to:plugin-codes:interfacing:

Interfacing external codes
==========================

To provide AiiDA with the set of instructions, required to run a code, one should subclass the |CalcJob| class and implement the following two key methods:

 #. :py:meth:`~aiida.engine.processes.calcjobs.calcjob.CalcJob.define`
 #. :py:meth:`~aiida.engine.processes.calcjobs.calcjob.CalcJob.prepare_for_submission`

We will now show how each of these can be implemented.

Defining the specifications
---------------------------

The |define| method is where one specifies the different inputs that the caller of the |CalcJob| will have to provide in order to run the code, as well as the outputs that will be produced (exit codes will be :ref:`discussed later<how-to:plugin-codes:parsing:errors>`).
This is done through an instance of :py:class:`~aiida.engine.processes.process_spec.CalcJobProcessSpec`, which, as can be seen in the snippet below, is passed as the |spec| argument to the |define| method.
For the code that adds up two numbers, we will need to define those numbers as inputs (let's call them ``x`` and ``y`` to label them) and the result as an output (``sum``).
The snippet below shows one potential implementation, as it is included in ``aiida-core``:

.. literalinclude:: ../../../aiida/calculations/arithmetic/add.py
    :language: python
    :pyobject: ArithmeticAddCalculation.define
    :dedent: 4

The first line of the |define| implementation calls the method of the parent class |CalcJob|.
This step is crucial as it will define `inputs` and `outputs` that are common to all |CalcJob|'s and failing to do so will leave the implementation broken.
After the super call, we modify the default values for some of these inputs that are defined by the base class.
Inputs that have already been defined can be accessed from the |spec| through the :py:attr:`~plumpy.process_spec.ProcessSpec.inputs` attribute, which behaves like a normal dictionary.

After modifying the existing inputs, we define the inputs that are specific to this code.
For this purpose we use the :py:meth:`~plumpy.process_spec.ProcessSpec.input` method, which does not modify the existing `inputs`, accessed through :py:attr:`~plumpy.process_spec.ProcessSpec.inputs`, but defines new ones that will be specific to this implementation.
You can also see that the definitions do not involve the assignment of a value, but only the passing of parameters to the method: a label to identify it, their valid types (in this case nodes of type |Int|) and a description.
Finally, note that there is no return statement: this method does not need to return anything, since all modifications are made directly into the received |spec| object.
You can check the Topics section about :ref:`defining processes <topics:processes:usage:defining>` if you want more information about setting up your `inputs` and `outputs` (covering validation, dynamic number of inputs, etc.).

Preparing for submission
------------------------

The :py:meth:`~aiida.engine.processes.calcjobs.calcjob.CalcJob.prepare_for_submission` method is used for two purposes.
Firstly, it should create the input files, based on the input nodes passed to the calculation, in the format that the external code will expect.
Secondly, the method should create and return a :py:class:`~aiida.common.datastructures.CalcInfo` instance that contains various instructions for the engine on how the code should be run.
An example implementation, as shipped with ``aiida-core`` can be seen in the following snippet:

.. literalinclude:: ../../../aiida/calculations/arithmetic/add.py
    :language: python
    :pyobject: ArithmeticAddCalculation.prepare_for_submission
    :dedent: 4

Note that, unlike the |define| method, this one is implemented from scratch and so there is no super call.
The external code that we are running with this |CalcJob| is ``bash`` and so to sum the input numbers ``x`` and ``y``, we should write a bash input file that performs the summation, for example ``echo $((x + y))``, where one of course has to replace ``x`` and ``y`` with the actual numbers.
You can see how the snippet uses the ``folder`` argument, which is a |Folder| instance that represents a temporary folder on disk, to write the input file with the bash summation.
It uses Python's string interpolation to replace the ``x`` and ``y`` placeholders with the actual values that were passed as input, ``self.inputs.x`` and ``self.inputs.y``, respectively.

.. note::

    When the |prepare_for_submission| is called, the inputs that have been passed will have been validated against the specification defined in the |define| method and they can be accessed through the :py:attr:`~plumpy.processes.Process.inputs` attribute.
    This means that if a particular input is required according to the spec, you can safely assume that it will have been set and you do not need to check explicitly for its existence.

All the files that are copied into the sandbox ``folder`` will be automatically copied by the engine to the scratch directory where the code will be run.
In this case we only create one input file, but you can create as many as you need, including subfolders if required.

.. note::

    The input files written to the ``folder`` sandbox, will also be permanently stored in the file repository of the calculation node for the purpose of additional provenance guarantees.
    See the section on :ref:`excluding files from provenance<topics:calculations:usage:calcjobs:file_lists_provenance_exclude>` to learn how to prevent certain input files from being stored explicitly.

After having written the necessary input files, one should create the |CodeInfo| object, which can be used to instruct the engine on how to run the code.
We assign the ``code_uuid`` attribute to the ``uuid`` of the ``Code`` node that was passed as an input, which can be retrieved through ``self.inputs.code``.
This is necessary such that the engine can retrieve the required information from the |Code| node, such as the full path of the executable.
Note that we didn't explicitly define this |Code| input in the |define| method, but this is one of the inputs defined in the base |CalcJob| class:

.. code-block:: python

    spec.input('code', valid_type=orm.Code, help='The `Code` to use for this job.')

After defining the UUID of the code node that the engine should use, we define the filenames where the stdin and stdout file descriptors should be redirected to.
These values are taken from the inputs, which are part of the ``metadata.options`` namespace, for some of whose inputs we overrode the default values in the specification definition in the previous section.
Note that instead of retrieving them through ``self.inputs.metadata['options']['input_filename']``, one can use the shortcut ``self.options.input_filename`` as we do here.
Based on this definition of the |CodeInfo|, the engine will create a run script that looks like the following:

.. code-block:: bash

    #!/bin/bash

    '[executable path in code node]' < '[input_filename]' > '[output_filename]'

The |CodeInfo| should be attached to the ``codes_info`` attribute of a |CalcInfo| object.
A calculation can potentially run more than one code, so the |CodeInfo| object should be assigned as a list.
Finally, we define the ``retrieve_list`` attribute, which is a list of filenames that the engine should retrieve from the running directory once the calculation job has finished.
The engine will store these files in a :py:class:`~aiida.orm.nodes.data.folder.FolderData` node that will be attached as an output node to the calculation with the label ``retrieved``.
There are :ref:`other file lists available<topics:calculations:usage:calcjobs:file_lists>` that allow you to easily customize how to move files to and from the remote working directory in order to prevent the creation of unnecessary copies.

This was a minimal example of how to implement the |CalcJob| class to interface AiiDA with an external code.
For more detailed information and advanced functionality on the |CalcJob| class, refer to the Topics section on :ref:`defining calculations <topics:calculations:usage>`.

.. _how-to:plugin-codes:parsing:

Parsing the outputs
===================

The parsing of the output files generated by a |CalcJob| is optional and can be used to store (part of) their information as AiiDA nodes, which makes the data queryable and therefore easier to access and analyze.
To enable |CalcJob| output file parsing, one should subclass the |Parser| class and implement the :py:meth:`~aiida.parsers.parser.Parser.parse` method.
The following is an example implementation, as shipped with ``aiida-core``, to parse the outputs of the :py:class:`~aiida.calculations.arithmetic.add.ArithmeticAddCalculation` discussed in the previous section:

.. literalinclude:: ../../../aiida/parsers/plugins/arithmetic/add.py
    :language: python
    :pyobject: ArithmeticAddParser

The output files generated by the completed calculation can be accessed from the ``retrieved`` output folder, which can be accessed through the :py:attr:`~aiida.parsers.parser.Parser.retrieved` property.
It is an instance of :py:class:`~aiida.orm.nodes.data.folder.FolderData` and so provides, among other things, the :py:meth:`~aiida.orm.nodes.node.Node.open` method to open any file it contains.
In this example implementation, we use it to open the output file, whose filename we get through the :py:meth:`~aiida.orm.nodes.process.calculation.calcjob.CalcJobNode.get_option` method of the corresponding calculation node, which we obtain through the :py:attr:`~aiida.parsers.parser.Parser.node` property of the ``Parser``.
We read the content of the file and cast it to an integer, which should contain the sum that was produced by the ``bash`` code.
We catch any exceptions that might be thrown, for example when the file cannot be read, or if its content cannot be interpreted as an integer, and return an exit code.
This method of dealing with potential errors of external codes is discussed in the section on :ref:`handling parsing errors<how-to:plugin-codes:parsing:errors>`.

To attach the parsed sum as an output, use the :py:meth:`~aiida.parsers.parser.Parser.out` method.
The first argument is the name of the output, which will be used as the label for the link that connects the calculation and data node, and the second is the node that should be recorded as an output.
Note that the type of the output should match the type that is specified by the process specification of the corresponding |CalcJob|.
If any of the registered outputs do not match the specification, the calculation will be marked as failed.

To trigger the parsing using a |Parser| after a |CalcJob| has finished (such as the one described in the :ref:`previous section <how-to:plugin-codes:interfacing>`) it should be defined in the ``metadata.options.parser_name`` input.
If a particular parser should always be used by default for a given |CalcJob|, it can be defined as the default in the |define| method, for example:

.. code-block:: python

    @classmethod
    def define(cls, spec):
        ...
        spec.inputs['metadata']['options']['parser_name'].default = 'arithmetic.add'

The default can be overridden through the inputs when launching the calculation job.
Note, that one should not pass the |Parser| class itself, but rather the corresponding entry point name under which it is registered as a plugin.
In other words, in order to use a |Parser| you will need to register it as explained in the how-to section on :ref:`registering plugins <how-to:plugins>`.


.. _how-to:plugin-codes:parsing:errors:

Handling parsing errors
-----------------------

So far we have not spent too much attention on dealing with potential errors that might arise when running external codes.
However, for many codes, there are lots of ways in which it can fail to execute nominally and produced the correct output.
A |Parser| is the solution to detect these errors and report them to the caller through :ref:`exit codes<topics:processes:concepts:exit_codes>`.
These exit codes can be defined through the |spec| of the |CalcJob| that is used for that code, just as the inputs and output are defined.
For example, the :py:class:`~aiida.calculations.arithmetic.add.ArithmeticAddCalculation` introduced in :ref:`"Interfacing external codes"<how-to:plugin-codes:interfacing>`, defines the following exit codes:

.. literalinclude:: ../../../aiida/calculations/arithmetic/add.py
    :language: python
    :start-after: start exit codes
    :end-before: end exit codes
    :dedent: 8

Each ``exit_code`` defines an exit status (a positive integer), a label that can be used to reference the code in the |parse| method (through the ``self.exit_codes`` property, as seen below), and a message that provides a more detailed description of the problem.
To use these in the |parse| method, you just need to return the corresponding exit code which instructs the engine to store it on the node of the calculation that is being parsed.
The snippet of the previous section on :ref:`parsing the outputs<how-to:plugin-codes:parsing>` already showed two problems that are detected and are communicated by returning the corresponding the exit code:

.. literalinclude:: ../../../aiida/parsers/plugins/arithmetic/add.py
    :language: python
    :lines: 27-33
    :dedent: 8

If the ``read()`` call fails to read the output file, for example because the calculation failed to run entirely and did not write anything, it will raise an ``OSError``, which the parser catches and returns the ``ERROR_READING_OUTPUT_FILE`` exit code.
Alternatively, if the file *could* be read, but it's content cannot be interpreted as an integer, the parser returns ``ERROR_INVALID_OUTPUT``.
The Topics section on :ref:`defining processes <topics:processes:usage:defining>` provides additional information on how to use exit codes.

.. todo::

    .. _how-to:plugin-codes:computers:

    title: Configuring remote computers

    `#4123`_

.. _how-to:plugin-codes:run:

Running external codes
======================

To run an external code with AiiDA, you will need to use an appropriate :ref:`calculation plugin <topics:plugins>` that knows how to transform the input nodes into the input files that the code expects, copy everything in the code's machine, run the calculation and retrieve the results.
You can check the `plugin registry <https://aiidateam.github.io/aiida-registry/>`_ to see if a plugin already exists for the code that you would like to run.
If that is not the case, you can :ref:`develop your own <how-to:plugin-codes:interfacing>`.
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
    ...
        Inputs:
               code:  required  Code        The `Code` to use for this job.
                  x:  required  Int, Float  The left operand.
                  y:  required  Int, Float  The right operand.
    ...

You will see that 3 inputs nodes are required: two containing the values to add up (``x``, ``y``) and one containing information about the specific code to execute (``code``).
If you already have these nodes in your database, you can get them by :ref:`querying for them <how-to:data:find>` or using ``orm.load_node(<PK>)``.
Otherwise, you will need to create them as shown below (note that you `will` need to already have the ``localhost`` computer configured, as explained in the :ref:`previous how-to<how-to:plugin-codes:computers>`):

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

    .. _how-to:plugin-codes:caching:

    title: Using caching to save computational resources

    `#3988`_


    .. _how-to:plugin-codes:scheduler:

    title: Adding support for a custom scheduler

    `#3989`_


    .. _how-to:plugin-codes:transport:

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
