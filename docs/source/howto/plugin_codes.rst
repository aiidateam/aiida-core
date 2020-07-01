.. _how-to:plugin-codes:

******************************************
How to write a plugin for an external code
******************************************

.. tip::

    Before starting to write a new plugin, check the `aiida plugin registry <https://aiidateam.github.io/aiida-registry/>`_.
    If a plugin for your code is already available, you can skip straight to :ref:`how-to:run-codes`.

To run an external code with AiiDA, you need a corresponding *calculation* plugin, which tells AiiDA how to:

1. Prepare the required input files
2. Run the code with the correct command line parameters

Finally, you will probably want a *parser* plugin, which tells AiiDA how to:

3. Parse the output of the code.

This how-to takes you through the process of :ref:`creating a calculation plugin<how-to:plugin-codes:interfacing>` for a dummy executable that sums two numbers, using it to :ref:`run the code<how-to:plugin-codes:run>`, and :ref:`writing a parser <how-to:plugin-codes:parsing>` for its outputs.

In the following, as an example, our |Code| will be the `bash` executable, and our "input file" will be a `bash` script ``aiida.in`` that sums two numbers and prints the result:

.. code-block:: bash

   echo $(( numx + numy ))

We will run this as:

.. code-block:: bash

    /bin/bash < aiida.in > aiida.out

thus writing the sum of the two numbers ``numx`` and ``numy`` (provided by the user) to the output file ``aiida.out``.


.. todo::

    Add to preceding sentence: :ref:`the communication with external machines<how-to:plugin-codes:transport>` and the interaction with its :ref:`scheduling software<how-to:plugin-codes:scheduler>`.

.. _how-to:plugin-codes:interfacing:


Interfacing external codes
==========================

We start our ``calcjob.py`` script by subclassing the |CalcJob| class:

.. literalinclude:: ../../../aiida/calculations/arithmetic/add.py
    :language: python
    :lines: 10-18

In the following, we will tell AiiDA how to run our code by implementing two key methods:

 #. :py:meth:`~aiida.engine.processes.calcjobs.calcjob.CalcJob.define`
 #. :py:meth:`~aiida.engine.processes.calcjobs.calcjob.CalcJob.prepare_for_submission`

Defining the spec
-----------------

The |define| method tells AiiDA which inputs the |CalcJob| expects and which outputs it produces (exit codes will be :ref:`discussed later<how-to:plugin-codes:parsing:errors>`).
This is done through an instance of the :py:class:`~aiida.engine.processes.process_spec.CalcJobProcessSpec` class, which is passed as the |spec| argument to the |define| method.
For example:

.. literalinclude:: ../../../aiida/calculations/arithmetic/add.py
    :language: python
    :pyobject: ArithmeticAddCalculation.define

The first line of the method calls the |define| method of the |CalcJob| parent class.
This necessary step defines the `inputs` and `outputs` that are common to all |CalcJob|'s.

Next, we use the :py:meth:`~plumpy.process_spec.ProcessSpec.input` method in order to define our two input numbers ``x`` and ``y`` (we support integers and floating point numbers), and we use :py:meth:`~plumpy.process_spec.ProcessSpec.output` to define an output of the calculation with label ``'sum'``.
Once a calculation finishes, any output node specified here will be linked to the calculation node with the specified link label.

.. tip::

    In real-world plugins, popular types of input nodes are Python dictionaries (:py:class:`~aiida.orm.nodes.data.dict.Dict`) and files (:py:class:`~aiida.orm.nodes.data.singlefile.SinglefileData`).

Finally, we set a couple of default ``options``, such as the name of the parser (which we will implement later), the name of input and output files, and the computational resources to use for such a calculation.
These ``options`` have already been defined on the |spec| by the ``super().define(spec)`` call, and they can be accessed through the :py:attr:`~plumpy.process_spec.ProcessSpec.inputs` attribute, which behaves like a dictionary.

.. note::

    One more important input required by any |CalcJob| is which external executable to use.
    External executables are represented by |Code|  instances that contain information about the computer they reside on, their path in the file system and more.

    They are passed to a |CalcJob| via the ``code`` input (defined in the |CalcJob| base class, so you don't have to)::

        spec.input('code', valid_type=orm.Code, help='The `Code` to use for this job.')



Note that there is no ``return`` statement in ``define``: the ``define`` method directly modifies the |spec| object it receives.
For more details on setting up your `inputs` and `outputs` (covering validation, dynamic number of inputs, etc.) see the :ref:`Defining Processes <topics:processes:usage:defining>` topic.

Preparing for submission
------------------------

The :py:meth:`~aiida.engine.processes.calcjobs.calcjob.CalcJob.prepare_for_submission` method has two jobs:
Firstly, it creates the input files in the format the external code expects.
And secondly, it returns a :py:class:`~aiida.common.datastructures.CalcInfo` object that contains instructions for the AiiDA engine on how the code should be run.
For example:

.. literalinclude:: ../../../aiida/calculations/arithmetic/add.py
    :language: python
    :pyobject: ArithmeticAddCalculation.prepare_for_submission

.. note:: Unlike the |define| method, the ``prepare_for_submission`` method is implemented from scratch and so there is no super call.

We start by writing our simple bash script that sums the two numbers ``x`` and ``y``, using Python's string interpolation to replace the ``x`` and ``y`` placeholders with the actual values ``self.inputs.x`` and ``self.inputs.y`` that were passed by the user.

All inputs provided to the calculation are validated against the ``spec`` *before* |prepare_for_submission| is called.
When accessing the :py:attr:`~plumpy.processes.Process.inputs` attribute, you can therefore safely assume that all required inputs have been set and that all inputs have a valid type.

The ``folder`` argument (a |Folder| instance) allows us to write the input file to a sandbox folder, whose contents will be transferred to the compute resource where the actual calculation takes place.
In this example, we only create a single input file, but you can create as many as you need, including subfolders if required.

.. note::

    By default, the contents of the sandbox ``folder`` are also stored permanently in the file repository of the calculation node for additional provenance guarantees.
    There are cases (e.g. license issues, file size) where you may want to change this behavior and :ref:`exclude files from being stored<topics:calculations:usage:calcjobs:file_lists_provenance_exclude>`.

After having written the necessary input files, we let AiiDA know how to run the code via the |CodeInfo| object.

First, we forward the ``uuid`` of the |Code|  instance passed by the user via the generic ``code`` input mentioned previously (in this example, the ``code`` will represent a ``bash`` executable).

Second, let's recall how we want our executable to be run:

.. code-block:: bash

    #!/bin/bash

    '[executable path in code node]' < '[input_filename]' > '[output_filename]'

We want to pass our input file to the executable via standard input, and record standard output of the executable in the output file -- this is done using the ``stdin_name`` and ``stdout_name`` attributes of the |CodeInfo|.

.. tip::

     Many executables don't read from standard input but instead require the path to an input file to be passed via command line parameters (potentially including further configuration options).
     In that case, use the |CodeInfo| ``cmdline_params`` attribute:

     .. code-block:: python

         codeinfo.cmdline_params = ['--input', self.inputs.input_filename]

.. tip::

    ``self.inputs.input_filename`` is just a shorthand for ``self.inputs.metadata['options']['input_filename']``.

Finally, we pass the |CodeInfo| to a |CalcInfo| object (one calculation job can involve more than one executable, so ``codes_info`` is a list).
We define the ``retrieve_list`` of filenames that the engine should retrieve from the directory where the job ran after it has finished.
The engine will store these files in a |FolderData| node that will be attached as an output node to the calculation with the label ``retrieved``.
There are :ref:`other file lists available<topics:calculations:usage:calcjobs:file_lists>` that allow you to easily customize how to move files to and from the remote working directory in order to prevent the creation of unnecessary copies.

This was an example of how to implement the |CalcJob| class to interface AiiDA with an external code.
For more details on the |CalcJob| class, refer to the Topics section on :ref:`defining calculations <topics:calculations:usage>`.

.. _how-to:plugin-codes:parsing:

Parsing the outputs
===================

Parsing the output files produced by your code into AiiDA nodes is optional, but it can make your data queryable and therefore easier to access and analyze.

We start our ``parser.py`` plugin by subclassing the |Parser| class and implementing its :py:meth:`~aiida.parsers.parser.Parser.parse` method.

.. code-block:: python

    class ArithmeticAddParser(Parser):
        """Parser for an `ArithmeticAddCalculation` job."""

        def parse(self, **kwargs):
            """Parse the contents of the output files stored in the `retrieved` output node."""
            output_folder = self.retrieved

            with output_folder.open(self.node.get_option('output_filename'), 'r') as handle:
                result = int(handle.read())

            self.out('sum', Int(result))

Before the ``parse()`` method is called, two important attributes are set on the |Parser|  instance:

  1. ``self.retrieved``: An instance of |FolderData|, which points to the folder containing all output files produced by the code and provides the means to :py:meth:`~aiida.orm.nodes.node.Node.open` any file it contains.

  2. ``self.node``: The :py:class:`~aiida.orm.nodes.process.calculation.calcjob.CalcJobNode` representing the finished calculation, which e.g. provides access to all of its inputs (``self.node.inputs``).

We start by opening the output file, whose filename we get from the ``self.node`` attribute via the :py:meth:`~aiida.orm.nodes.process.calculation.calcjob.CalcJobNode.get_option` convenience method.

We read the content of the file and cast it to an integer, which should contain the sum that was produced by the ``bash`` code.

Finally, we use the :py:meth:`~aiida.parsers.parser.Parser.out` method to link the parsed sum as an output of the calculation.
The first argument is the name of the output, which will be used as the label for the link that connects the calculation and data node, and the second is the node that should be recorded as an output.
Note that the type of the output should match the type that is specified by the process specification of the corresponding |CalcJob|.
If any of the registered outputs do not match the specification, the calculation will be marked as failed.

In order to request automatic parsing of a |CalcJob| (once it has finished), users can set the ``metadata.options.parser_name`` input when launching the job.
If a particular parser should *always* be used by default, the |CalcJob| ``define`` method can set a default value for the parser name as we did in the :ref:`previous section <how-to:codes:interfacing>`:

.. code-block:: python

    @classmethod
    def define(cls, spec):
        ...
        spec.inputs['metadata']['options']['parser_name'].default = 'arithmetic.add'

Note, that we are not passing the |Parser| class itself, but an *entry point string* under which the parser class is registered.
How to register your parser class as an entry point is explained in the how-to section on :ref:`registering plugins <how-to:plugins>`.


.. _how-to:plugin-codes:parsing:errors:

Handling parsing errors
-----------------------

So far, we have not spent much attention on dealing with potential errors that can arise when running external codes.
However, there are lots of ways in which codes can fail to execute nominally.
A |Parser| can play an important role in detecting such errors and reporting them to AiiDA, where :ref:`workflows <how-to:workflows>` can then decide how to proceed, e.g. by modifying input parameters and resubmitting the calculation.

Parsers communicate errors through :ref:`exit codes<topics:processes:concepts:exit_codes>`, which are defined in the |spec| of the |CalcJob| they parse.
Our :py:class:`~aiida.calculations.arithmetic.add.ArithmeticAddCalculation` example, defines the following exit codes:

.. literalinclude:: ../../../aiida/calculations/arithmetic/add.py
    :language: python
    :start-after: start exit codes
    :end-before: end exit codes
    :dedent: 8

Each ``exit_code`` defines

 * an exit status (a positive integer),
 * a label that can be used to reference the code in the |parse| method (through the ``self.exit_codes`` property, as shown below), and
 * a message that provides a more detailed description of the problem.

In order to inform AiiDA about a failed calculation, simply return from the ``parse`` method the exit code that corresponds to the detected issue.
Here is a more complete version of our |Parser|:

.. literalinclude:: ../../../aiida/parsers/plugins/arithmetic/add.py
    :language: python
    :pyobject: ArithmeticAddParser

It checks:

 1. Whether a retrieved folder is present.
 2. Whether the output file can be read (whether ``open()`` or ``read()`` will throw an ``OSError``).
 3. Whether the output file contains an integer.
 4. Whether the sum is negative.

AiiDA stored the exit code returned by the |parse| method on the calculation node that is being parsed, from where it can then be inspected further down the line.
The Topics section on :ref:`defining processes <topics:processes:usage:defining>` provides more details on exit codes.


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


This marks the end of this how-to, and you should now be fully equipped to wrap your own code in an AiiDA calculation plugin.
For further reading, you may want to consult the :ref:`guidelines on plugin design <topics:plugins:guidelines>` or the how to on :ref:`packaging plugins <how-to:plugins>`.


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
.. |FolderData| replace:: :py:class:`~aiida.orm.nodes.data.folder.FolderData`
.. |spec| replace:: ``spec``
.. |define| replace:: :py:class:`~aiida.engine.processes.calcjobs.CalcJob.define`
.. |prepare_for_submission| replace:: :py:class:`~aiida.engine.processes.calcjobs.CalcJob.prepare_for_submission`

.. _#3988: https://github.com/aiidateam/aiida-core/issues/3988
.. _#3989: https://github.com/aiidateam/aiida-core/issues/3989
.. _#3990: https://github.com/aiidateam/aiida-core/issues/3990
.. _#4123: https://github.com/aiidateam/aiida-core/issues/4123
