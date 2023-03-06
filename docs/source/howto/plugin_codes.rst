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

This how-to takes you through the process of :ref:`creating a calculation plugin<how-to:plugin-codes:interfacing>`, using it to :ref:`run the code<how-to:plugin-codes:run>`, and :ref:`writing a parser <how-to:plugin-codes:parsing>` for its outputs.

In this example, our |Code| will be the ``diff`` executable that "computes" the difference between two "input files" and prints the difference to standard output:

.. code-block:: console

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

We are using ``diff`` here since it is available on almost every UNIX system by default, and it takes both command line *arguments* (the two files) and command line *options* (e.g. ``-i`` for case-insensitive matching).
This is similar to how the executables of many scientific simulation codes work, making it easy to adapt this example to your use case.

We will run ``diff`` as:

.. code-block:: bash

   $ diff file1.txt file2.txt > diff.patch

thus writing difference between `file1.txt` and `file2.txt` to `diff.patch`.


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

.. literalinclude:: ../../../aiida/calculations/diff_tutorial/calculations.py
    :language: python
    :pyobject: DiffCalculation.define


The first line of the method calls the |define| method of the |CalcJob| parent class.
This necessary step defines the `inputs` and `outputs` that are common to all |CalcJob|'s.

Next, we use the :py:meth:`~plumpy.process_spec.ProcessSpec.input` method in order to define our two input files ``file1`` and ``file2`` of type |SinglefileData|.

.. admonition:: Further reading

    When using |SinglefileData|, AiiDA keeps track of the inputs as *files*.
    This is very flexible but has the downside of making it difficult to query for information contained in those files and ensuring that the inputs are valid.
    :ref:`how-to:plugin-codes:cli-options` shows how to use the |Dict| class to represent the ``diff`` command line options as a python dictionary.
    The `aiida-diff`_ demo plugin goes further and adds automatic validation.

We then use :py:meth:`~plumpy.process_spec.ProcessSpec.output` to define the only output of the calculation with the label ``diff``.
AiiDA will attach the outputs defined here to a (successfully) finished calculation using the link label provided.

..  I think the following is not really needed here at this point
    .. note::
        By default, AiiDA expects all outputs defined in the spec.
        Use ``required=False`` in order to mark an output as optional.


Finally, we set a few default ``options``, such as the name of the parser (which we will implement later), the name of input and output files, and the computational resources to use for such a calculation.
These ``options`` have already been defined on the |spec| by the ``super().define(spec)`` call, and they can be accessed through the :py:attr:`~plumpy.process_spec.ProcessSpec.inputs` attribute, which behaves like a dictionary.

There is no ``return`` statement in ``define``: the ``define`` method directly modifies the |spec| object it receives.

.. note::

        One more input required by any |CalcJob| is which external executable to use.

        External executables are represented by |Code|  instances that contain information about the computer they reside on, their path in the file system and more.
        They are passed to a |CalcJob| via the ``code`` input, which is defined in the |CalcJob| base class, so you don't have to:

        .. code-block:: python

            spec.input('code', valid_type=orm.AbstractCode, help='The `Code` to use for this job.')

.. admonition:: Further reading

    For more details on setting up your `inputs` and `outputs` (covering validation, dynamic number of inputs, etc.) see the :ref:`Defining Processes <topics:processes:usage:defining>` topic.

Preparing for submission
------------------------


The :py:meth:`~aiida.engine.processes.calcjobs.calcjob.CalcJob.prepare_for_submission` method has two jobs:
Creating the input files in the format the external code expects and returning a :py:class:`~aiida.common.datastructures.CalcInfo` object that contains instructions for the AiiDA engine on how the code should be run.
For example:

.. literalinclude:: ../../../aiida/calculations/diff_tutorial/calculations.py
    :language: python
    :pyobject: DiffCalculation.prepare_for_submission

All inputs provided to the calculation are validated against the ``spec`` *before* |prepare_for_submission| is called.
Therefore, when accessing the :py:attr:`~plumpy.processes.Process.inputs` attribute, you can safely assume that all required inputs have been set and that all inputs have a valid type.

We start by creating a |CodeInfo| object that lets AiiDA know how to run the code, i.e. here:

.. code-block:: bash

   $ diff file1.txt file2.txt > diff.patch

This includes the command line parameters (here: the names of the files that we would like to ``diff``) and the UUID of the |Code| to run.
Since ``diff`` writes directly to standard output, we redirect standard output to the specified output filename.

Next, we create a |CalcInfo| object that lets AiiDA know which files to copy back and forth.
In our example, the two input files are already stored in the AiiDA file repository and we can use the ``local_copy_list`` to pass them along.

.. note::

  In other use cases you may need to *create* new files on the fly.
  This is what the ``folder`` argument of :py:meth:`~aiida.engine.processes.calcjobs.calcjob.CalcJob.prepare_for_submission` is for:

  .. code:: python

    with folder.open("filename", 'w') as handle:
        handle.write("file content")


  Any files and directories created in this sandbox folder will automatically be transferred to the compute resource where the actual calculation takes place.


.. This is too detailed for a tutorial
    .. note::

        By default, the contents of the sandbox ``folder`` are also stored permanently in the file repository of the calculation node for additional provenance guarantees.
        There are cases (e.g. license issues, file size) where you may want to change this behavior and :ref:`exclude files from being stored<topics:calculations:usage:calcjobs:file_lists_provenance_exclude>`.


The ``retrieve_list`` on the other hand tells the engine which files to retrieve from the directory where the job ran after it has finished.
All files listed here will be store in a |FolderData| node that is attached as an output node to the calculation with the label ``retrieved``.

Finally, we pass the |CodeInfo| to a |CalcInfo| object.
One calculation job can involve more than one executable, so ``codes_info`` is a list.
If you have more than one executable in your ``codes_info``, you can set ``codes_run_mode`` to specify the mode with which these will be executed (`CodeRunMode.SERIAL` by default).
We define the ``retrieve_list`` of filenames that the engine should retrieve from the directory where the job ran after it has finished.
The engine will store these files in a |FolderData| node that will be attached as an output node to the calculation with the label ``retrieved``.

.. admonition:: Further reading

    There are :ref:`other file lists available<topics:calculations:usage:calcjobs:file_lists>` that allow you to easily customize how to move files to and from the remote working directory in order to prevent the creation of unnecessary copies.
    For more details on the |CalcJob| class, refer to the Topics section on :ref:`defining calculations <topics:calculations:usage>`.


.. _how-to:plugin-codes:parsing:

Parsing the outputs
===================

Parsing the output files produced by a code into AiiDA nodes is optional, but it can make your data queryable and therefore easier to access and analyze.

To create a parser plugin, subclass the |Parser| class in a file called ``parsers.py``.

.. literalinclude::  ../../../aiida/parsers/plugins/diff_tutorial/parsers.py
    :language: python
    :start-after: # START PARSER HEAD
    :end-before: # END PARSER HEAD

Before the ``parse()`` method is called, two important attributes are set on the |Parser|  instance:

  1. ``self.retrieved``: An instance of |FolderData|, which points to the folder containing all output files that the |CalcJob| instructed to retrieve, and provides the means to :py:meth:`~aiida.orm.nodes.repository.NodeRepository.open` any file it contains.

  2. ``self.node``: The :py:class:`~aiida.orm.nodes.process.calculation.calcjob.CalcJobNode` representing the finished calculation, which, among other things, provides access to all of its inputs (``self.node.inputs``).

Now implement its :py:meth:`~aiida.parsers.parser.Parser.parse` method as

.. literalinclude:: ../../../aiida/parsers/plugins/diff_tutorial/parsers.py
    :language: python
    :pyobject: DiffParserSimple.parse

The :py:meth:`~aiida.orm.nodes.process.calculation.calcjob.CalcJobNode.get_option` convenience method is used to get the filename of the output file.

Finally, the :py:meth:`~aiida.parsers.parser.Parser.out` method is used return the output file as the ``diff`` output of the calculation:
The first argument is the name to be used as the label for the link that connects the calculation and data node.
The second argument is the node that should be recorded as an output.

.. note::

    The outputs and their types need to match those from the process specification of the corresponding |CalcJob| (or an exception will be raised).

In this minimalist example, there isn't actually much parsing going on -- we are simply passing along the output file as a |SinglefileData| node.
If your code produces output in a structured format, instead of just returning the file you may want to parse it e.g. to a python dictionary (|Dict| node) to make the results easily searchable.

.. admonition:: Exercise

    Consider the different output files produced by your favorite simulation code.
    Which information would you want to:

     1. parse into the database for querying (e.g. as |Dict|, |StructureData|, ...)?
     2. store in the AiiDA file repository for safe-keeping (e.g. as |SinglefileData|, ...)?
     3. leave on the computer where the calculation ran (e.g. recording their remote location using |RemoteData| or simply ignoring them)?

    Once you know the answers to these questions, you are ready to start writing a parser for your code.

In order to request automatic parsing of a |CalcJob| (once it has finished), users can set the ``metadata.options.parser_name`` input when launching the job.
If a particular parser should be used by default, the |CalcJob| ``define`` method can set a default value for the parser name as was done in the :ref:`previous section <how-to:plugin-codes:interfacing>`:

.. code-block:: python

    @classmethod
    def define(cls, spec):
        ...
        spec.inputs['metadata']['options']['parser_name'].default = 'diff-tutorial'

Note that the default is not set to the |Parser| class itself, but to the *entry point string* under which the parser class is registered.
We will register the entry point for the parser in a bit.


.. _how-to:plugin-codes:parsing:errors:

Handling parsing errors
-----------------------

So far, we have not spent much attention on dealing with potential errors that can arise when running external codes.
However, there are lots of ways in which codes can fail to execute nominally.
A |Parser| can play an important role in detecting and communicating such errors, where :ref:`workflows <how-to:run-workflows>` can then decide how to proceed, e.g., by modifying input parameters and resubmitting the calculation.

Parsers communicate errors through :ref:`exit codes<topics:processes:concepts:exit_codes>`, which are defined in the |spec| of the |CalcJob| they parse.
The ``DiffCalculation`` example, defines the following exit code:

.. code-block:: python

    spec.exit_code(300, 'ERROR_MISSING_OUTPUT_FILES', message='Calculation did not produce all expected output files.')

An ``exit_code`` defines:

* an exit status (a positive integer, following the :ref:`topics:processes:usage:exit_code_conventions`),
* a label that can be used to reference the code in the |parse| method (through the ``self.exit_codes`` property, as shown below), and
* a message that provides a more detailed description of the problem.

In order to inform AiiDA about a failed calculation, simply return from the ``parse`` method the exit code that corresponds to the detected issue.
Here is a more complete version of the example |Parser| presented in the previous section:

.. literalinclude:: ../../../aiida/parsers/plugins/diff_tutorial/parsers.py
    :language: python
    :pyobject: DiffParser.parse

This simple check makes sure that the expected output file ``diff.patch`` is among the files retrieved from the computer where the calculation was run.
Production plugins will often scan further aspects of the output (e.g. the standard error, the output file, etc.) for any issues that may indicate a problem with the calculation and return a corresponding exit code.

AiiDA stores the exit code returned by the |parse| method on the calculation node that is being parsed, from where it can then be inspected further down the line (see the :ref:`defining processes <topics:processes:usage:defining>` topic for more details).
Note that some scheduler plugins can detect issues at the scheduler level (by parsing the job scheduler output) and set an exit code.
The Topics section on :ref:`scheduler exit codes <topics:calculations:usage:calcjobs:scheduler-errors>` explains how these can be inspected inside a parser and how they can optionally be overridden.


.. how-to:plugin-codes:customization:

Customizations
==============

.. how-to:plugin-codes:customization:process-label:

Process label
-------------

Each time a ``Process`` is run, a ``ProcessNode`` is stored in the database to record the execution.
A human-readable label is stored in the ``process_label`` attribute.
By default, the name of the process class is used as this label.
If this default is not informative enough, it can be customized by overriding the :meth:`~aiida.engine.processes.process.Process._build_process_label`: method:

.. code-block:: python

    class SomeProcess(Process):

        def _build_process_label(self):
            return 'custom_process_label'

Nodes created through executions of this process class will have ``node.process_label == 'custom_process_label'``.

.. _how-to:plugin-codes:entry-points:

Registering entry points
========================

:ref:`Entry points <how-to:plugins-develop:entrypoints>` are the preferred method of registering new calculation, parser and other plugins with AiiDA.

With your ``calculations.py`` and ``parsers.py`` files at hand, let's register entry points for the plugins they contain:

* Move your two scripts into a subfolder ``aiida_diff_tutorial``:

   .. code-block:: console

      $ mkdir aiida_diff_tutorial
      $ mv calculations.py parsers.py aiida_diff_tutorial/
      $ touch aiida_diff_tutorial/__init__.py

   You have just created an ``aiida_diff_tutorial`` Python *package*!

* Add a minimal set of metadata for your package by writing a ``pyproject.toml`` file:

    .. code-block:: toml

        [build-system]
        # build the package with [flit](https://flit.readthedocs.io)
        requires = ["flit_core >=3.4,<4"]
        build-backend = "flit_core.buildapi"

        [project]
        # See https://www.python.org/dev/peps/pep-0621/
        name = "aiida-diff-tutorial"
        version = "0.1.0"
        description = "AiiDA demo plugin"
        dependencies = [
            "aiida-core>=2.0,<3",
        ]

        [project.entry-points."aiida.calculations"]
        "diff-tutorial" = "aiida_diff_tutorial.calculations:DiffCalculation"

        [project.entry-points."aiida.parsers"]
        "diff-tutorial" = "aiida_diff_tutorial.parsers:DiffParser"

        [tool.flit.module]
        name = "aiida_diff_tutorial"


    .. note::
        This allows for the project metadata to be fully specified in the pyproject.toml file, using the PEP 621 format.


* Install your new ``aiida-diff-tutorial`` plugin package.

   .. code-block:: console

       $ pip install -e .  # install package in "editable mode"

   See the :ref:`how-to:plugins-install` section for details.

After this, you should see your plugins listed:

   .. code-block:: console

      $ verdi plugin list aiida.calculations
      $ verdi plugin list aiida.calculations diff-tutorial
      $ verdi plugin list aiida.parsers


.. _how-to:plugin-codes:run:

Running a calculation
=====================

With the entry points set up, you are ready to launch your first calculation with the new plugin:


* If you haven't already done so, :ref:`set up your computer<how-to:run-codes:computer>`.
   In the following we assume it to be the localhost:

    .. code-block:: console

        $ verdi computer setup -L localhost -H localhost -T core.local -S core.direct -w `echo $PWD/work` -n
        $ verdi computer configure core.local localhost --safe-interval 5 -n

*  Create the input files for our calculation

    .. code-block:: console

        $ echo -e "File with content\ncontent1" > file1.txt
        $ echo -e "File with content\ncontent2" > file2.txt
        $ mkdir input_files
        $ mv file1.txt file2.txt input_files

* Write a ``launch.py`` script:

    .. literalinclude:: ./include/snippets/plugins/launch.py
      :language: python

    .. note::

        The ``launch.py`` script sets up an AiiDA |Code| instance that associates the ``/usr/bin/diff`` executable with the ``DiffCalculation`` class (through its entry point ``diff``).

        This code is automatically set on the ``code`` input port of the builder and passed as an input to the calculation plugin.

* Launch the calculation:

    .. code-block:: console

        $ verdi run launch.py


    If everything goes well, this should print the results of your calculation, something like:

    .. code-block:: console

        $ verdi run launch.py
        Computed diff between files:
        2c2
        < content1
        ---
        > content2

.. tip::

    If you encountered a parsing error, it can be helpful to make a :ref:`topics:calculations:usage:calcjobs:dry_run`, which allows you to inspect the input folder generated by AiiDA before any calculation is launched.



Finally instead of running your calculation in the current shell, you can submit your calculation to the AiiDA daemon:

* (Re)start the daemon to update its Python environment:

    .. code-block:: console

        $ verdi daemon restart --reset

* Update your launch script to use:

    .. code-block:: python

        # Submit calculation to the aiida daemon
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

    $ verdi process list -a -p1

This should show the processes of both calculations you just ran.
Use ``verdi calcjob outputcat <pk>`` to check the output of the calculation you submitted to the daemon.

Congratulations - you can now write plugins for external simulation codes and use them to submit calculations!

If you still have time left, consider going through the optional exercise below.

.. _how-to:plugin-codes:importers:

Writing importers for existing computations
===========================================

.. versionadded:: 2.0

New users to your plugin may often have completed many previous computations without the use of AiiDA, which they wish to import into AiiDA.
In these cases, it is possible to write an importer for their inputs/outputs, which generates the provenance nodes for the corresponding |CalcJob|.

The importer must be written as a subclass of :class:`~aiida.engine.processes.calcjobs.importer.CalcJobImporter`,
for an example see :class:`aiida.calculations.importers.arithmetic.add.ArithmeticAddCalculationImporter`.

To associate the importer with the |CalcJob| class, the importer must be registered with an entry point in the group ``aiida.calculations.importers``.

.. code-block:: toml

    [project.entry-points."aiida.calculations.importers"]
    "core.arithmetic.add" = "aiida.calculations.importers.arithmetic.add:ArithmeticAddCalculationImporter"

.. note::

    Note that the entry point name can be any valid entry point name.
    If the importer plugin is provided by the same package as the corresponding |CalcJob| plugin, it is recommended that the entry point name of the importer and |CalcJob| plugin are the same.
    This will allow the :meth:`~aiida.engine.processes.calcjobs.calcjob.CalcJob.get_importer` method to automatically fetch the associated importer.
    If the entry point names differ, the entry point name of the desired importer implementation needs to be passed to :meth:`~aiida.engine.processes.calcjobs.calcjob.CalcJob.get_importer` as an argument.

Users can then import their calculations via the :py:meth:`~aiida.engine.processes.calcjobs.calcjob.CalcJob.get_importer` method:

.. code-block:: python

    from aiida.plugins import CalculationFactory

    ArithmeticAddCalculation = CalculationFactory('arithmetic.add')
    importer = ArithmeticAddCalculation.get_importer()
    remote_data = RemoteData('/some/absolute/path', computer=load_computer('computer'))
    inputs = importer.parse_remote_data(remote_data)
    results, node = run.get_node(ArithmeticAddCalculation, **inputs)
    assert node.is_imported

.. seealso:: :doc:`aep:004_calcjob_importer/readme`, for the design considerations around this feature.

.. _how-to:plugin-codes:cli-options:

Exercise - Support command-line options
=======================================

As discussed before, ``diff`` knows a couple of command-line options:

.. code-block:: bash

   $ diff --help
   Usage: diff [OPTION]... FILES
   Compare files line by line.
   ...
   -i, --ignore-case               ignore case differences in file contents
   -E, --ignore-tab-expansion      ignore changes due to tab expansion
   -b, --ignore-space-change       ignore changes in the amount of white space
   -w, --ignore-all-space          ignore all white space
   -B, --ignore-blank-lines        ignore changes where lines are all blank
   -I, --ignore-matching-lines=RE  ignore changes where all lines match RE
   ...

For simplicity let's focus on the excerpt of options shown above and allow the user of our plugin to pass these along.

Notice that one of the options (``--ignore-matching-lines``) requires the user to pass a regular expression string, while the other options don't require any value.

One way to represent a set of command line options like

.. code:: bash

   diff --ignore-case --ignore-matching-lines='.*ABC.*'

would be using a python dictionary:

.. code:: python

   parameters = {
     'ignore-case': True,
     'ignore-space-change': False,
     'ignore-matching-lines': '.*ABC.*'
    }

Here is a simple code snippet for translating the dictionary to a list of command line options:

.. code:: python

   def cli_options(parameters):
        """Return command line options for parameters dictionary.

        :param dict parameters: dictionary with command line parameters
        """
        options = []
        for key, value in parameters.items():
            # Could validate: is key a known command-line option?
            if isinstance(value, bool) and value:
                options.append(f'--{key}')
            elif isinstance(value, str):
                # Could validate: is value a valid regular expression?
                options.append(f'--{key}')
                options.append(value)

        return options

.. note::

   When passing parameters along to your simulation code, try *validating* them.
   This detects errors directly at *submission* of the calculation and thus prevents calculations with malformed inputs from ever entering the queue of your HPC system.

   For the sake of brevity we are *not* performing validation here but there are numerous python libraries, such as `voluptuous`_ (used by `aiida-diff`_, see `example <https://github.com/aiidateam/aiida-diff/blob/92c61bdcc2db201d69da4d8b83a2b3f5dd529bf1/aiida_diff/data/__init__.py#L14-L20>`_), `marshmallow`_ or `pydantic`_, that help you define a schema to validate input against.


Let's open our previous ``calculations.py`` file and start modifying the ``DiffCalculation`` class:

 1. In the ``define`` method, add a new ``input`` to the ``spec`` with label ``'parameters'`` and type |Dict|  (``from aiida.orm import Dict``)
 2. | In the ``prepare_for_submission`` method run the ``cli_options`` function from above on ``self.inputs.parameters.get_dict()`` to get the list of command-line options.
    | Add them to the ``codeinfo.cmdline_params``.

.. dropdown:: Solution

   For 1. add the following line to the ``define`` method:

   .. code-block:: python

        spec.input('parameters', valid_type=Dict, help='diff command-line parameters')

   For 2. copy the ``cli_options`` snippet at the end of ``calculations.py`` and set the ``cmdline_params`` to:

   .. code:: python

        codeinfo.cmdline_params = cli_options(self.inputs.parameters.get_dict()) + [ self.inputs.file1.filename, self.inputs.file2.filename]


That's it. Let's now open the ``launch.py`` script and pass along our command line parameters:

.. code:: python

   ...
   builder.parameters = orm.Dict(dict={'ignore-case': True})
   ...

Change the capitalization of one of the characters in the first line of ``file1.txt``.
Then, restart the daemon and submit the new calculation:

.. code:: bash

   $ verdi daemon restart
   $ verdi run launch.py

If everything worked as intended, the capitalization difference in the first line should be ignored (and thus not show up in the output).

This marks the end of this how-to.

The |CalcJob| and |Parser| plugins are still rather basic and the ``aiida-diff-tutorial`` plugin package is missing a number of useful features, such as package metadata, documentation, tests, CI, etc.
Continue with :ref:`how-to:plugins-develop` in order to learn how to quickly create a feature-rich new plugin package from scratch.

.. |Int| replace:: :py:class:`~aiida.orm.nodes.data.int.Int`
.. |SinglefileData| replace:: :py:class:`~aiida.orm.nodes.data.singlefile.SinglefileData`
.. |StructureData| replace:: :py:class:`~aiida.orm.nodes.data.structure.StructureData`
.. |RemoteData| replace:: :py:class:`~aiida.orm.RemoteData`
.. |Dict| replace:: :py:class:`~aiida.orm.nodes.data.dict.Dict`
.. |Code| replace:: :py:class:`~aiida.orm.nodes.data.code.abstract.AbstractCode`
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
.. |define| replace:: :py:class:`~aiida.engine.CalcJob.define`
.. |prepare_for_submission| replace:: :py:meth:`~aiida.engine.CalcJob.prepare_for_submission`
.. _aiida-diff: https://github.com/aiidateam/aiida-diff
.. _voluptuous: https://github.com/alecthomas/voluptuous
.. _pydantic: https://github.com/samuelcolvin/pydantic/
.. _marshmallow: https://github.com/marshmallow-code/marshmallow
.. _#3989: https://github.com/aiidateam/aiida-core/issues/3989
.. _#3990: https://github.com/aiidateam/aiida-core/issues/3990
