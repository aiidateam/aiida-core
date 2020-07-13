.. _how-to:plugin-codes:

******************************************
How to write a plugin for an external code
******************************************

.. tip::

    Before starting to write a new plugin, check the `aiida plugin registry <https://aiidateam.github.io/aiida-registry/>`_.
    If a plugin for your code is already available, you can skip straight to :ref:`how-to:run-codes`.

To run an external code with AiiDA, you need a corresponding *calculation* plugin, which tells AiiDA how to:

1. Prepare the required input files.
2. Run the code with the correct command line parameters.

Finally, you will probably want a *parser* plugin, which tells AiiDA how to:

3. Parse the output of the code.

This how-to takes you through the process of :ref:`creating a calculation plugin<how-to:plugin-codes:interfacing>` for a simple executable that sums two numbers, using it to :ref:`run the code<how-to:plugin-codes:run>`, and :ref:`writing a parser <how-to:plugin-codes:parsing>` for its outputs.

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

Start by creating a file ``calculations.py`` and subclass the |CalcJob| class:

.. code-block:: python

    from aiida import orm
    from aiida.common.datastructures import CalcInfo, CodeInfo
    from aiida.common.folders import Folder
    from aiida.engine import CalcJob, CalcJobProcessSpec


    class ArithmeticAddCalculation(CalcJob):
        """`CalcJob` implementation to add two numbers using bash for testing and demonstration purposes."""


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

Next, we use the :py:meth:`~plumpy.process_spec.ProcessSpec.input` method in order to define our two input numbers ``x`` and ``y`` (we support integers and floating point numbers), and we use :py:meth:`~plumpy.process_spec.ProcessSpec.output` to define the only output of the calculation with the label ``sum``.
AiiDA will attach the outputs defined here to a (successfully) finished calculation using the link label provided.

.. note::
    This holds for *required* outputs (the default behaviour).
    Use ``required=False`` in order to mark an output as optional.

.. tip::

    For the input parameters and input files of more complex simulation codes, consider using :py:class:`~aiida.orm.nodes.data.dict.Dict` (python dictionary) and :py:class:`~aiida.orm.nodes.data.singlefile.SinglefileData` (file wrapper) input nodes.

Finally, we set a couple of default ``options``, such as the name of the parser (which we will implement later), the name of input and output files, and the computational resources to use for such a calculation.
These ``options`` have already been defined on the |spec| by the ``super().define(spec)`` call, and they can be accessed through the :py:attr:`~plumpy.process_spec.ProcessSpec.inputs` attribute, which behaves like a dictionary.

.. note::

    One more important input required by any |CalcJob| is which external executable to use.
    External executables are represented by |Code|  instances that contain information about the computer they reside on, their path in the file system and more.

    They are passed to a |CalcJob| via the ``code`` input, which is defined in the |CalcJob| base class, so you don't have to:

    .. code-block:: python

        spec.input('code', valid_type=orm.Code, help='The `Code` to use for this job.')



There is no ``return`` statement in ``define``: the ``define`` method directly modifies the |spec| object it receives.
For more details on setting up your `inputs` and `outputs` (covering validation, dynamic number of inputs, etc.) see the :ref:`Defining Processes <topics:processes:usage:defining>` topic.

Preparing for submission
------------------------

The :py:meth:`~aiida.engine.processes.calcjobs.calcjob.CalcJob.prepare_for_submission` method has two jobs:
Creating the input files in the format the external code expects and returning a :py:class:`~aiida.common.datastructures.CalcInfo` object that contains instructions for the AiiDA engine on how the code should be run.
For example:

.. literalinclude:: ../../../aiida/calculations/arithmetic/add.py
    :language: python
    :pyobject: ArithmeticAddCalculation.prepare_for_submission

.. note:: Unlike the |define| method, the ``prepare_for_submission`` method is implemented from scratch and so there is no super call.

The first step is writing the simple bash script mentioned in the beginning: summing the numbers ``x`` and ``y``, using Python's string interpolation to replace the ``x`` and ``y`` placeholders with the actual values ``self.inputs.x`` and ``self.inputs.y`` that were provided as inputs by the caller.

All inputs provided to the calculation are validated against the ``spec`` *before* |prepare_for_submission| is called.
Therefore, when accessing the :py:attr:`~plumpy.processes.Process.inputs` attribute, you can safely assume that all required inputs have been set and that all inputs have a valid type.

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

    ``self.options.input_filename`` is just a shorthand for ``self.inputs.metadata['options']['input_filename']``.

Finally, we pass the |CodeInfo| to a |CalcInfo| object (one calculation job can involve more than one executable, so ``codes_info`` is a list).
We define the ``retrieve_list`` of filenames that the engine should retrieve from the directory where the job ran after it has finished.
The engine will store these files in a |FolderData| node that will be attached as an output node to the calculation with the label ``retrieved``.
There are :ref:`other file lists available<topics:calculations:usage:calcjobs:file_lists>` that allow you to easily customize how to move files to and from the remote working directory in order to prevent the creation of unnecessary copies.

This was an example of how to implement the |CalcJob| class to interface AiiDA with an external code.
For more details on the |CalcJob| class, refer to the Topics section on :ref:`defining calculations <topics:calculations:usage>`.

.. _how-to:plugin-codes:parsing:

Parsing the outputs
===================

Parsing the output files produced by a code into AiiDA nodes is optional, but it can make your data queryable and therefore easier to access and analyze.

To create a parser plugin, subclass the |Parser| class (for example in a file called ``parsers.py``) and implement its :py:meth:`~aiida.parsers.parser.Parser.parse` method.
The following is an example of a simple implementation:

.. literalinclude:: ../../../aiida/parsers/plugins/arithmetic/add.py
    :language: python
    :pyobject: SimpleArithmeticAddParser

Before the ``parse()`` method is called, two important attributes are set on the |Parser|  instance:

  1. ``self.retrieved``: An instance of |FolderData|, which points to the folder containing all output files that the |CalcJob| instructed to retrieve, and provides the means to :py:meth:`~aiida.orm.nodes.node.Node.open` any file it contains.

  2. ``self.node``: The :py:class:`~aiida.orm.nodes.process.calculation.calcjob.CalcJobNode` representing the finished calculation, which, among other things, provides access to all of its inputs (``self.node.inputs``).

The :py:meth:`~aiida.orm.nodes.process.calculation.calcjob.CalcJobNode.get_option` convenience method is used to get the filename of the output file.
Its content is cast to an integer, since the output file should contain the sum produced by the ``aiida.in`` bash script.

Finally, the :py:meth:`~aiida.parsers.parser.Parser.out` method is used to link the parsed sum as an output of the calculation.
The first argument is the name of the output, which will be used as the label for the link that connects the calculation and data node, and the second is the node that should be recorded as an output.
Note that the type of the output should match the type that is specified by the process specification of the corresponding |CalcJob|.
If any of the registered outputs do not match the specification, the calculation will be marked as failed.

In order to request automatic parsing of a |CalcJob| (once it has finished), users can set the ``metadata.options.parser_name`` input when launching the job.
If a particular parser should be used by default, the |CalcJob| ``define`` method can set a default value for the parser name as was done in the :ref:`previous section <how-to:plugin-codes:interfacing>`:

.. code-block:: python

    @classmethod
    def define(cls, spec):
        ...
        spec.inputs['metadata']['options']['parser_name'].default = 'arithmetic.add'

Note, that the default is not set to the |Parser| class itself, but the *entry point string* under which the parser class is registered.
How to register a parser class through an entry point is explained in the how-to section on :ref:`registering plugins <how-to:plugins>`.


.. _how-to:plugin-codes:parsing:errors:

Handling parsing errors
-----------------------

So far, we have not spent much attention on dealing with potential errors that can arise when running external codes.
However, there are lots of ways in which codes can fail to execute nominally.
A |Parser| can play an important role in detecting and communicating such errors, where :ref:`workflows <how-to:workflows>` can then decide how to proceed, e.g., by modifying input parameters and resubmitting the calculation.

Parsers communicate errors through :ref:`exit codes<topics:processes:concepts:exit_codes>`, which are defined in the |spec| of the |CalcJob| they parse.
The :py:class:`~aiida.calculations.arithmetic.add.ArithmeticAddCalculation` example, defines the following exit codes:

.. literalinclude:: ../../../aiida/calculations/arithmetic/add.py
    :language: python
    :start-after: start exit codes
    :end-before: end exit codes
    :dedent: 8

Each ``exit_code`` defines:

 * an exit status (a positive integer),
 * a label that can be used to reference the code in the |parse| method (through the ``self.exit_codes`` property, as shown below), and
 * a message that provides a more detailed description of the problem.

In order to inform AiiDA about a failed calculation, simply return from the ``parse`` method the exit code that corresponds to the detected issue.
Here is a more complete version of the example |Parser| presented in the previous section:

.. literalinclude:: ../../../aiida/parsers/plugins/arithmetic/add.py
    :language: python
    :pyobject: ArithmeticAddParser

It checks:

 1. Whether a retrieved folder is present.
 2. Whether the output file can be read (whether ``open()`` or ``read()`` will throw an ``OSError``).
 3. Whether the output file contains an integer.
 4. Whether the sum is negative.

AiiDA stores the exit code returned by the |parse| method on the calculation node that is being parsed, from where it can then be inspected further down the line.
The Topics section on :ref:`defining processes <topics:processes:usage:defining>` provides more details on exit codes.


.. todo::

    .. _how-to:plugin-codes:computers:

    title: Configuring remote computers

    `#4123`_

.. _how-to:plugin-codes:entry-points:

Registering entry points
========================

:ref:`Entry points <how-to:plugins:entrypoints>` are the preferred method of registering new calculation, parser and other plugins with AiiDA.

With your ``calculations.py`` and ``parsers.py`` files at hand, let's register entry points for the plugins they contain:

 * Move your two scripts into a subfolder ``aiida_add``:

   .. code-block:: console

      mkdir aiida_add
      mv calculations.py parsers.py aiida_add/

   You have just created an ``aiida_add`` Python *package*!

 * Write a minimalistic ``setup.py`` script for your new package:

    .. code-block:: python

        from setuptools import setup

        setup(
            name='aiida-add',
            packages=['aiida_add'],
            entry_points={
                'aiida.calculations': ["add = aiida_add.calculations:ArithmeticAddCalculation"],
                'aiida.parsers': ["add = aiida_add.parsers:ArithmeticAddParser"],
            }
        )

    .. note::
        Strictly speaking, ``aiida-add`` is the name of the *distribution*, while ``aiida_add`` is the name of the *package*.
        The aiida-core documentation uses the term *package* a bit more loosely.


 * Install your new ``aiida-add`` plugin package:

   .. code-block:: console

      pip install -e .
      reentry scan


After this, you should see your plugins listed:

   .. code-block:: console

      $ verdi plugin list aiida.calculations
      $ verdi plugin list aiida.calculations add
      $ verdi plugin list aiida.parsers



.. _how-to:plugin-codes:run:

Running a calculation
=====================

With the entry points set up, you are ready to launch your first calculation with the new plugin:


 * If you haven't already done so, :ref:`set up your computer<how-to:run-codes:computer>`.
   In the following we assume it to be the localhost:

    .. code-block:: console

        $ verdi computer setup -L localhost -H localhost -T local -S direct -w `echo $PWD/work` -n
        $ verdi computer configure local localhost --safe-interval 5 -n

 * Write a ``launch.py`` script:

    .. code-block:: python

        from aiida import orm, engine
        from aiida.common.exceptions import NotExistent

        # Setting up inputs
        computer = orm.load_computer('localhost')
        try:
            code = load_code('add@localhost')
        except NotExistent:
            # Setting up code via python API (or use "verdi code setup")
            code = orm.Code(label='add', remote_computer_exec=[computer, '/bin/bash'], input_plugin_name='add')

        builder = code.get_builder()
        builder.x = Int(4)
        builder.y = Int(5)
        builder.metadata.options.withmpi = False
        builder.metadata.options.resources = {
            'num_machines': 1,
            'num_mpiprocs_per_machine': 1,
        }

        # Running the calculation & parsing results
        output_dict, node = engine.run_get_node(builder)
        print("Parsing completed. Result: {}".format(output_dict['sum'].value))

    .. note::

        ``output_dict`` is a dictionary containing all the output nodes keyed after their label.
        In this case: "remote_folder", "retrieved" and "sum".


 * Launch the calculation:

    .. code-block:: console

        $ verdi run launch.py


    If everything goes well, this should print the results of your calculation, something like:

    .. code-block:: console

        $ verdi run launch.py
        Parsing completed. Result: 9

.. tip::

    If you encountered a parsing error, it can be helpful to make a :ref:`topics:calculations:usage:calcjobs:dry_run`, which allows you to inspect the input folder generated by AiiDA before any calculation is launched.


Finally instead of running your calculation in the current shell, you can submit your calculation to the AiiDA daemon:

 * (Re)start the daemon to update its Python environment:

    .. code-block:: console

        $ verdi daemon restart --reset

 * Update your launch script to use:

    .. code-block:: python

        # Submitting the calculation
        node = engine.submit(builder)
        print("Submitted calculation {}".format(node))

    .. note::

        ``node`` is the |CalcJobNode| representing the state of the underlying calculation process (which may not be finished yet).


 * Launch the calculation:

    .. code-block:: console

        $ verdi run launch.py

    This should print the UUID and the PK of the submitted calculation.

You can use the verdi command line interface to :ref:`monitor<topics:processes:usage:monitoring>` this processes:

.. code-block:: bash

    $ verdi process list


This marks the end of this how-to.

The |CalcJob| and |Parser| plugins are still rather basic and the ``aiida-add`` plugin package is missing a number of useful features, such as package metadata, documentation, tests, CI, etc.
Continue with :ref:`how-to:plugins` in order to learn how to quickly create a feature-rich new plugin package from scratch.


.. todo::

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
.. |CalcJobNode| replace:: :py:class:`~aiida.orm.CalcJobNode`
.. |CalcInfo| replace:: :py:class:`~aiida.common.CalcInfo`
.. |CodeInfo| replace:: :py:class:`~aiida.common.CodeInfo`
.. |FolderData| replace:: :py:class:`~aiida.orm.nodes.data.folder.FolderData`
.. |spec| replace:: ``spec``
.. |define| replace:: :py:class:`~aiida.engine.processes.calcjobs.CalcJob.define`
.. |prepare_for_submission| replace:: :py:class:`~aiida.engine.processes.calcjobs.CalcJob.prepare_for_submission`

.. _#3989: https://github.com/aiidateam/aiida-core/issues/3989
.. _#3990: https://github.com/aiidateam/aiida-core/issues/3990
.. _#4123: https://github.com/aiidateam/aiida-core/issues/4123
