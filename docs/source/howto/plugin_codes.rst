.. _how-to:plugin-codes:

******************************************
How to write a plugin for an external code
******************************************

.. tip::

    Before starting to write a new plugin, check the `aiida plugin registry <https://aiidateam.github.io/aiida-registry/>`_.
    If a plugin for your code is already available, you can skip straight to :ref:`how-to:run-codes`.

.. tip::

    This how to walks you through all logical steps of how AiiDA interacts with an external code.
    If you already know the basics and would like to get started with a new plugin package quickly, check out :ref:`how-to:plugins-develop`.

To run an external code with AiiDA, you need a corresponding *calculation* plugin, which tells AiiDA how to:

1. Prepare the required input files.
2. Run the code with the correct command line parameters.

Finally, you will probably want a *parser* plugin, which tells AiiDA how to:

3. Parse the output of the code.

This how-to takes you through the process of :ref:`creating a calculation plugin<how-to:plugin-codes:interfacing>` for the `diff` executable that "computes" the difference between two files, using it to :ref:`run the code<how-to:plugin-codes:run>`, and :ref:`writing a parser <how-to:plugin-codes:parsing>` for its outputs. While this example is specifically meant for `diff` it can be easily expanded to most other codes with some changes.

In the following, our |Code| will be the `diff` executable, which takes two "input files" and prints the difference between the files to standard output.

.. code-block:: bash

   $ cat file1.txt
   file with content
   content1

   $ cat file2.txt
   file with content
   content2

   $ diff file1.txt file2.txt
   2c2
   < content1
   ---
   > content2

We will run it as:

.. code-block:: bash

   $ diff file1.txt file2.txt > diff.patch

thus writing difference between `file1.txt` and `file2.txt` to `diff.patch`.


.. admonition:: Why diff?

  * ``diff`` is available on almost every UNIX system
  * ``diff`` has both command line *arguments* (the two files) and command line *options* (e.g. `-i` for case-insensitive matching)
  * ``diff`` takes 2 input files & produces 1 output file

  This is similar to how many scientific codes work, making it easy to adapt this example to your use case.



.. _how-to:plugin-codes:interfacing:


Interfacing external codes
==========================

Start by creating a file ``calculations.py`` and subclass the |CalcJob| class:

.. code-block:: python

    from aiida.common import datastructures
    from aiida.engine import CalcJob
    from aiida.orm import SinglefileData

    class DiffCalculation(CalcJob):
        """AiiDA calculation plugin wrapping the diff executable."""


In the following, we will tell AiiDA how to run our code by implementing two key methods:

 #. :py:meth:`~aiida.engine.processes.calcjobs.calcjob.CalcJob.define`
 #. :py:meth:`~aiida.engine.processes.calcjobs.calcjob.CalcJob.prepare_for_submission`

Defining the spec
-----------------

The |define| method tells AiiDA which inputs the |CalcJob| expects and which outputs it produces (exit codes will be :ref:`discussed later<how-to:plugin-codes:parsing:errors>`).
This is done through an instance of the :py:class:`~aiida.engine.processes.process_spec.CalcJobProcessSpec` class, which is passed as the |spec| argument to the |define| method.
For example:

.. code-block:: python

    @classmethod
    def define(cls, spec):
        """Define inputs and outputs of the calculation."""
        super().define(spec)
        spec.input('file1', valid_type=SinglefileData, help='First file to be compared.')
        spec.input('file2', valid_type=SinglefileData, help='Second file to be compared.')
        spec.output('diff', valid_type=SinglefileData,
            help='diff between file1 and file2.')

        # set default values for AiiDA options (optional)
        spec.inputs['metadata']['options']['parser_name'].default = 'diff'
        spec.inputs['metadata']['options']['output_filename'].default = 'diff.patch'
        spec.inputs['metadata']['options']['resources'].default = {
            'num_machines': 1,
            'num_mpiprocs_per_machine': 1,
        }

        spec.exit_code(100, 'ERROR_MISSING_OUTPUT_FILES', message='Calculation did not produce all expected output files.')

The first line of the method calls the |define| method of the |CalcJob| parent class.
This necessary step defines the `inputs` and `outputs` that are common to all |CalcJob|'s.

Next, we use the :py:meth:`~plumpy.process_spec.ProcessSpec.input` method in order to define our two input files ``file1`` and ``file2`` of type |SinglefileData|.

.. note::
    When using |SinglefileData|, AiiDA keeps track of the inputs as *files*.
    This is very flexible but has the downside of making it difficult to query for information contained in those files and ensuring that the inputs are valid.
    The `aiida-diff`_ demo plugin builds on the example shown here and uses the |Dict| class to represent the `diff` command line options as a python dictionary, enabling querying and automatic validation.

We then use :py:meth:`~plumpy.process_spec.ProcessSpec.output` to define the only output of the calculation with the label ``diff``.
AiiDA will attach the outputs defined here to a (successfully) finished calculation using the link label provided.

.. note::
    This holds for *required* outputs (the default behaviour).
    Use ``required=False`` in order to mark an output as optional.


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

.. code-block:: python

    def prepare_for_submission(self, folder):
        """
        Create input files.
        :param folder: an `aiida.common.folders.Folder` where the plugin should temporarily place all files needed by
            the calculation.
        :return: `aiida.common.datastructures.CalcInfo` instance
        """
        codeinfo = datastructures.CodeInfo()
        codeinfo.cmdline_params = self.inputs.parameters.cmdline_params(
            file1_name=self.inputs.file1.filename,
            file2_name=self.inputs.file2.filename)
        codeinfo.code_uuid = self.inputs.code.uuid
        codeinfo.stdout_name = self.metadata.options.output_filename
        codeinfo.withmpi = self.inputs.metadata.options.withmpi

        # Prepare a `CalcInfo` to be returned to the engine
        calcinfo = datastructures.CalcInfo()
        calcinfo.codes_info = [codeinfo]
        calcinfo.local_copy_list = [
            (self.inputs.file1.uuid, self.inputs.file1.filename, self.inputs.file1.filename),
            (self.inputs.file2.uuid, self.inputs.file2.filename, self.inputs.file2.filename),
        ]
        calcinfo.retrieve_list = [self.metadata.options.output_filename]

        return calcinfo



.. note:: Unlike the |define| method, the ``prepare_for_submission`` method is implemented from scratch and so there is no super call.

There are two types of information that we have to specify, namely |CodeInfo|, which contains information necessary to execute the code and |CalcInfo|, which has to do with storage of data produced by the calculation.

We start by look at the inputs for |CodeInfo|. Here we supply the command line parameters as the names of the files that we would like to ``diff``. Use ``self.inputs``, which provides access to all inputs defined in ``spec``. All inputs provided to the calculation are validated against the ``spec`` *before* |prepare_for_submission| is called. Therefore, when accessing the :py:attr:`~plumpy.processes.Process.inputs` attribute, you can safely assume that all required inputs have been set and that all inputs have a valid type.

Recall that ``diff`` requires the two filenames as inputs. These are provided using ``self.inputs.file1.filename`` and ``self.inputs.file2.filename``. We would also need to supply the code, which is done through its uuid as ``self.inputs.code.uuid``. To capture the output of ``diff``, specify an output filename as ``self.metadata.options.output_filename``.

.. note::

    The ``folder`` argument (a |Folder| instance) allows us to write the input file to a sandbox folder, whose contents will be transferred to the compute resource where the actual calculation takes place.
    In this example, we only create a single input file, but you can create as many as you need, including subfolders if required.

.. note::

    By default, the contents of the sandbox ``folder`` are also stored permanently in the file repository of the calculation node for additional provenance guarantees.
    There are cases (e.g. license issues, file size) where you may want to change this behavior and :ref:`exclude files from being stored<topics:calculations:usage:calcjobs:file_lists_provenance_exclude>`.




We now pass the |CodeInfo| to a |CalcInfo| object (one calculation job can involve more than one executable, so ``codes_info`` is a list).
We define the ``retrieve_list`` of filenames that the engine should retrieve from the directory where the job ran after it has finished.
The engine will store these files in a |FolderData| node that will be attached as an output node to the calculation with the label ``retrieved``. Define a ``local_copy_list`` to provide the files that must be copied over to the remote computer.
There are :ref:`other file lists available<topics:calculations:usage:calcjobs:file_lists>` that allow you to easily customize how to move files to and from the remote working directory in order to prevent the creation of unnecessary copies.

This was an example of how to implement the |CalcJob| class to interface AiiDA with an external code.
For more details on the |CalcJob| class, refer to the Topics section on :ref:`defining calculations <topics:calculations:usage>`.

.. tip::

     Many executables don't read from standard input but instead require the path to an input file to be passed via command line parameters (potentially including further configuration options).
     In that case, use the |CodeInfo| ``cmdline_params`` attribute:

     .. code-block:: python

         codeinfo.cmdline_params = ['--input', self.inputs.input_filename]

.. tip::

    ``self.options.input_filename`` is just a shorthand for ``self.inputs.metadata['options']['input_filename']``.

.. _how-to:plugin-codes:parsing:

Parsing the outputs
===================

Parsing the output files produced by a code into AiiDA nodes is optional, but it can make your data queryable and therefore easier to access and analyze.

To create a parser plugin, subclass the |Parser| class (for example in a file called ``parsers.py``) and implement its :py:meth:`~aiida.parsers.parser.Parser.parse` method:

.. code-block:: python

    class DiffParser(Parser):
        """
        Parser class for parsing output of calculation.
        """

        def parse(self, **kwargs):
            """
            Parse results
            :returns: an exit code, if parsing fails (or nothing if parsing succeeds)
            """
            output_filename = self.node.get_option('output_filename')

            # add output file
            self.logger.info("Parsing '{}'".format(output_filename))
            with self.retrieved.open(output_filename, 'rb') as handle:
                output_node = SinglefileData(file=handle)
            self.out('diff', output_node)

        return ExitCode(0)

Before the ``parse()`` method is called, two important attributes are set on the |Parser|  instance:

  1. ``self.retrieved``: An instance of |FolderData|, which points to the folder containing all output files that the |CalcJob| instructed to retrieve, and provides the means to :py:meth:`~aiida.orm.nodes.repository.NodeRepositoryMixin.open` any file it contains.

  2. ``self.node``: The :py:class:`~aiida.orm.nodes.process.calculation.calcjob.CalcJobNode` representing the finished calculation, which, among other things, provides access to all of its inputs (``self.node.inputs``).

The :py:meth:`~aiida.orm.nodes.process.calculation.calcjob.CalcJobNode.get_option` convenience method is used to get the filename of the output file.

Finally, the :py:meth:`~aiida.parsers.parser.Parser.out` method is used return the output file as the ``diff`` output of the calculation:
The first argument is the name to be used as the label for the link that connects the calculation and data node.
The second argument is the node that should be recorded as an output.

.. note::

    The outputs and their types need to match those from the process specification of the corresponding |CalcJob| (or an exception will be raised).

In this minimalist example, there isn't actually much parsing going on -- we are simply passing along the output file as a |SinglefileData| node.
If your code produces output in a structured format, instead of just returning the file you will likely want to parse it and return information e.g. in the form of a python dictionary (i.e. a |Dict| node).

In order to request automatic parsing of a |CalcJob| (once it has finished), users can set the ``metadata.options.parser_name`` input when launching the job.
If a particular parser should be used by default, the |CalcJob| ``define`` method can set a default value for the parser name as was done in the :ref:`previous section <how-to:plugin-codes:interfacing>`:

.. code-block:: python

    @classmethod
    def define(cls, spec):
        ...
        spec.inputs['metadata']['options']['parser_name'].default = 'diff'

Note that the default is not set to the |Parser| class itself, but the *entry point string* under which the parser class is registered.
How to register a parser class through an entry point is explained in :ref:`registering plugins <how-to:plugins-develop>`.


.. _how-to:plugin-codes:parsing:errors:

Handling parsing errors
-----------------------

So far, we have not spent much attention on dealing with potential errors that can arise when running external codes.
However, there are lots of ways in which codes can fail to execute nominally.
A |Parser| can play an important role in detecting and communicating such errors, where :ref:`workflows <how-to:run-workflows>` can then decide how to proceed, e.g., by modifying input parameters and resubmitting the calculation.

Parsers communicate errors through :ref:`exit codes<topics:processes:concepts:exit_codes>`, which are defined in the |spec| of the |CalcJob| they parse.
The :py:class:`DiffCalculation` example, defines the following exit code:

.. code-block:: python

    spec.exit_code(100, 'ERROR_MISSING_OUTPUT_FILES', message='Calculation did not produce all expected output files.')

An ``exit_code`` defines:

 * an exit status (a positive integer),
 * a label that can be used to reference the code in the |parse| method (through the ``self.exit_codes`` property, as shown below), and
 * a message that provides a more detailed description of the problem.

In order to inform AiiDA about a failed calculation, simply return from the ``parse`` method the exit code that corresponds to the detected issue.
Here is a more complete version of the example |Parser| presented in the previous section:

.. code-block:: python

    def parse(self, **kwargs):
        """
        Parse outputs, store results in database.
        :returns: an exit code, if parsing fails (or nothing if parsing succeeds)
        """
        from aiida.orm import SinglefileData

        output_filename = self.node.get_option('output_filename')

        # Check that folder content is as expected
        files_retrieved = self.retrieved.list_object_names()
        files_expected = [output_filename]
        # Note: set(A) <= set(B) checks whether A is a subset of B
        if not set(files_expected) <= set(files_retrieved):
            self.logger.error("Found files '{}', expected to find '{}'".format(
                files_retrieved, files_expected))
            return self.exit_codes.ERROR_MISSING_OUTPUT_FILES

        # add output file
        self.logger.info("Parsing '{}'".format(output_filename))
        with self.retrieved.open(output_filename, 'rb') as handle:
            output_node = SinglefileData(file=handle)
        self.out('diff', output_node)

        return ExitCode(0)

This simple check makes sure that the expected output file ``diff.patch`` is among the files retrieved from the computer where the calculation was run.
Production plugins will often check further aspects of the output (e.g. the standard error, the output file, etc.) to detect whether the code failed and return a corresponding exit code.

AiiDA stores the exit code returned by the |parse| method on the calculation node that is being parsed, from where it can then be inspected further down the line (see the :ref:`defining processes <topics:processes:usage:defining>` topic for more details).
Note that some scheduler plugins can detect issues at the scheduler level (by parsing the job scheduler output) and set an exit code.
The Topics section on :ref:`scheduler exit codes <topics:calculations:usage:calcjobs:scheduler-errors>` explains how these can be inspected inside a parser and how they can optionally be overridden.


.. todo::

    .. _how-to:plugin-codes:computers:

    title: Configuring remote computers

    `#4123`_

.. _how-to:plugin-codes:entry-points:

Registering entry points
========================

:ref:`Entry points <how-to:plugins-develop:entrypoints>` are the preferred method of registering new calculation, parser and other plugins with AiiDA.

With your ``calculations.py`` and ``parsers.py`` files at hand, let's register entry points for the plugins they contain:

 * Move your two scripts into a subfolder ``aiida_diff``:

   .. code-block:: console

      $ mkdir aiida_diff
      $ mv calculations.py parsers.py aiida_diff/

   You have just created an ``aiida_diff`` Python *package*!

 * Write a minimalistic ``setup.py`` script for your new package:

    .. code-block:: python

        from setuptools import setup

        setup(
            name='aiida-diff',
            packages=['aiida_diff'],
            entry_points={
                'aiida.calculations': ["add = aiida_add.calculations:DiffCalculation"],
                'aiida.parsers': ["add = aiida_add.parsers:DiffParser"],
            }
        )

    .. note::
        Strictly speaking, ``aiida-diff`` is the name of the *distribution*, while ``aiida_diff`` is the name of the *package*.
        The aiida-core documentation uses the term *package* a bit more loosely.


 * Install your new ``aiida-diff`` plugin package.
   See the :ref:`how-to:plugins-install` section for details.

After this, you should see your plugins listed:

   .. code-block:: console

      $ verdi plugin list aiida.calculations
      $ verdi plugin list aiida.calculations diff
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

 *  Setup two simple files to run

    .. code-block:: console

        $ echo "This is the first file" > file1.txt
        $ echo "This is the second file" > file2.txt

 * Write a ``launch.py`` script:

    .. code-block:: python

        diff_code = load_code('diff@localhost')

        DiffParameters = DataFactory('diff')
        parameters = DiffParameters({'ignore-case': True})

        SinglefileData = DataFactory('singlefile')
        file1 = SinglefileData(file=path.join('file1.txt'))
        file2 = SinglefileData(file=path.join('file2.txt'))

        # set up calculation
        inputs = {
            'code': diff_code,
            'parameters': parameters,
            'file1': file1,
            'file2': file2,
            'metadata': {
                'description': "Test job submission with the aiida_diff plugin",
            },
        }

        # Note: in order to submit your calculation to the aiida daemon, do:
        result = engine.run(CalculationFactory('diff'), **inputs)

        computed_diff = result['diff'].get_content()
        print("Computed diff between files: \n{}".format(computed_diff))


 * Launch the calculation:

    .. code-block:: console

        $ verdi run launch.py


    If everything goes well, this should print the results of your calculation, something like:

    .. code-block:: console

        $ verdi run launch.py
        Computer diff between files:
        1c1
        < This is the first file
        ---
        > This is the second file

.. tip::

    If you encountered a parsing error, it can be helpful to make a :ref:`topics:calculations:usage:calcjobs:dry_run`, which allows you to inspect the input folder generated by AiiDA before any calculation is launched.


Finally instead of running your calculation in the current shell, you can submit your calculation to the AiiDA daemon:

 * (Re)start the daemon to update its Python environment:

    .. code-block:: console

        $ verdi daemon restart --reset

 * Update your launch script to use:

    .. code-block:: python

        # Submitting the calculation
        node = engine.submit(CalculationFactory('diff'), **inputs)
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

The |CalcJob| and |Parser| plugins are still rather basic and the ``aiida-diff`` plugin package is missing a number of useful features, such as package metadata, documentation, tests, CI, etc.
Continue with :ref:`how-to:plugins-develop` in order to learn how to quickly create a feature-rich new plugin package from scratch.


.. todo::

    .. _how-to:plugin-codes:scheduler:

    title: Adding support for a custom scheduler

    `#3989`_


    .. _how-to:plugin-codes:transport:

    title: Adding support for a custom transport

    `#3990`_


.. |Int| replace:: :py:class:`~aiida.orm.nodes.data.int.Int`
.. |SinglefileData| replace:: :py:class:`~aiida.orm.nodes.data.singlefile.SinglefileData`
.. |Dict| replace:: :py:class:`~aiida.orm.nodes.data.dict.Dict`
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
.. |PluginCutter| replace:: `AiiDA plugin cutter <https://github.com/aiidateam/aiida-plugin-cutter>`_

.. _aiida-diff: https://github.com/aiidateam/aiida-diff
