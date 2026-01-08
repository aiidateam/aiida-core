.. _topics:calculations:usage:

=====
Usage
=====

.. note:: This chapter assumes knowledge of the :ref:`basic concept<topics:calculations:concepts>` and difference between calculation functions and calculation jobs is known and when one should use on or the other.

A calculation is a process (see the :ref:`process section<topics:processes:concepts>` for details) that *creates* new data.
Currently, there are two ways of implementing a calculation process:

* :ref:`calculation function<topics:calculations:usage:calcfunctions>`
* :ref:`calculation job<topics:calculations:usage:calcjobs>`

This section will provide detailed information and best practices on how to implement these two calculation types.

.. _topics:calculations:usage:calcfunctions:

Calculation functions
=====================

The section on the :ref:`concept of calculation functions<topics:calculations:concepts:calcfunctions>` already addressed their aim: automatic recording of their execution with their inputs and outputs in the provenance graph.
The :ref:`section on process functions<topics:processes:functions>` subsequently detailed the rules that apply when implementing them, all of which to calculation functions, which are a sub type, just like work functions.
However, there are some differences given that calculation functions are 'calculation'-like processes and work function behave like 'workflow'-like processes.
What this entails in terms of intended usage and limitations for calculation functions is the scope of this section.

Creating data
-------------
It has been said many times before: calculation functions, like all 'calculation'-like processes, `create` data, but what does `create` mean exactly?
In this context, the term 'create' is not intended to refer to the simple creation of a new data node in the graph, in an interactive shell or a script for example.
But rather it indicates the creation of a new piece of data from some other data through a computation implemented by a process.
This is then exactly what the calculation function does.
It takes one or more data nodes as inputs and returns one or more data nodes as outputs, whose content is based on those inputs.
As explained in the :ref:`technical section<topics:processes:functions>`, outputs are created simply by returning the nodes from the function.
The engine will inspect the return value from the function and attach the output nodes to the calculation node that represents the calculation function.
To verify that the output nodes are in fact 'created', the engine will check that the nodes are not stored.
Therefore, it is very important that you **do not store the nodes you create yourself**, or the engine will raise an exception, as shown in the following example:

.. include:: include/snippets/calcfunctions/add_calcfunction_store.py
    :code: python

Because the returned node is already stored, the engine will raise the following exception:

.. code:: bash

    ValueError: trying to return an already stored Data node from a @calcfunction, however, @calcfunctions cannot return data.
    If you stored the node yourself, simply do not call `store()` yourself.
    If you want to return an input node, use a @workfunction instead.

The reason for this strictness is that a node that was stored after being created in the function body, is indistinguishable from a node that was already stored and had simply been loaded in the function body and returned, e.g.:

.. include:: include/snippets/calcfunctions/add_calcfunction_load_node.py
    :code: python

The loaded node would also have gotten a `create` link from the calculation function, even though it was not really created by it at all.
It is exactly to prevent this ambiguity that calculation functions require all returned output nodes to be *unstored*.

Note that work functions have exactly the opposite required and all the outputs that it returns **have to be stored**, because as a 'workflow'-like process, it *cannot* create new data.
For more details refer to the :ref:`work function section<topics:workflows:usage:workfunctions>`.

.. _topics:calculations:usage:calcjobs:

Calculation jobs
================

To explain how a calculation job can be implemented, we will continue with the example presented in the section on the :ref:`concept of the calculation job<topics:calculations:concepts:calcjobs>`.
There we described a code that adds two integers, implemented as a simple bash script, and how the :py:class:`~aiida.engine.processes.calcjobs.calcjob.CalcJob` class can be used to run this code through AiiDA.
Since it is a sub class of the :py:class:`~aiida.engine.processes.process.Process` class, it shares all its properties.
It will be very valuable to have read the section on working with :ref:`generic processes<topics:processes:usage>` before continuing, because all the concepts explained there will apply also to calculation jobs.


.. _topics:calculations:usage:calcjobs:define:

Define
------
To implement a calculation job, one simply sub classes the :py:class:`~aiida.engine.processes.calcjobs.calcjob.CalcJob` process class and implements the :py:meth:`~aiida.engine.processes.calcjobs.calcjob.CalcJob.define` method.
You can pick any name that is a valid python class name.
The most important method of the ``CalcJob`` class, is the ``define`` class method.
Here you define, what inputs it takes and what outputs it will generate.

.. include:: include/snippets/calcjobs/arithmetic_add_spec_inputs.py
    :code: python

As the snippet above demonstrates, the class method takes two arguments:

* ``cls`` this is the reference of the class itself and is mandatory for any class method
* ``spec`` which is the 'specification'

.. warning::
    Do not forget to add the line ``super().define(spec)`` as the first line of the ``define`` method, where you replace the class name with the name of your calculation job.
    This will call the ``define`` method of the parent class, which is necessary for the calculation job to work properly

As the name suggests, the ``spec`` can be used to specify the properties of the calculation job.
For example, it can be used to define inputs that the calculation job takes.
In our example, we need to be able to pass two integers as input, so we define those in the spec by calling ``spec.input()``.
The first argument is the name of the input.
This name should be used later to specify the inputs when launching the calculation job and it will also be used as the label for link to connect the data node and the calculation node in the provenance graph.
Additionally, as we have done here, you can specify which types are valid for that particular input.
Since we expect integers, we specify that the valid type is the database storable :py:class:`~aiida.orm.nodes.data.int.Int` class.

.. note::

    Since we sub class from ``CalcJob`` and call its ``define`` method, it will inherit the ports that it declares as well.
    If you look at the implementation, you will find that the base class ``CalcJob`` already defines an input ``code`` that takes a ``Code`` instance.
    This will reference the code that the user wants to run when he launches the ``CalcJob``.
    For this reason, you **do not** again have to declare this input.

Next we should define what outputs we expect the calculation to produce:

.. include:: include/snippets/calcjobs/arithmetic_add_spec_outputs.py
    :code: python

Just as for the inputs, one can specify what node type each output should have.
By default a defined output will be 'required', which means that if the calculation job terminates and the output has not been attached, the process will be marked as failed.
To indicate that an output is optional, one can use ``required=False`` in the ``spec.output`` call.
Note that the process spec, and its :py:meth:`~plumpy.ProcessSpec.input` and :py:meth:`~plumpy.ProcessSpec.output` methods provide a lot more functionality.
Fore more details, please refer to the section on :ref:`process specifications<topics:processes:usage:spec>`.


.. _topics:calculations:usage:calcjobs:prepare:

Prepare
-------
We have now defined through the process specification, what inputs the calculation job expects and what outputs it will create.
The final remaining task is to instruct the engine how the calculation job should actually be run.
To understand what the engine would have to do to accomplish this, let's consider what one typically does when manually preparing to run a computing job through a scheduler:

* Prepare a working directory in some scratch space on the machine where the job will run
* Create the raw input files required by the executable
* Create a launch script containing scheduler directives, loading of environment variables and finally calling the executable with certain command line parameters.

So all we need to do now is instruct the engine how to accomplish these things for a specific calculation job.
Since these instructions will be calculation dependent, we will implement this with the :py:meth:`~aiida.engine.processes.calcjobs.calcjob.CalcJob.prepare_for_submission` method.
The implementation of the ``ArithmeticAddCalculation`` that we are considering in the example looks like the following:

.. include:: include/snippets/calcjobs/arithmetic_add_spec_prepare_for_submission.py
    :code: python

Before we go into the code line-by-line, let's describe the big picture of what is happening here.
The goal of this method is to help the engine accomplish the three steps required for preparing the submission a calculation job, as described above.
The raw input files that are required can be written to a sandbox folder that is passed in as the ``folder`` argument.

.. note::

    The ``folder`` argument points to a temporary sandbox folder on the local file system that can be used to write the input files to.
    After the ``prepare_for_submission`` method returns, the engine will take those contents and copy them to the working directory where the calculation will be run.
    On top of that, these files will also be written to the file repository of the node that represents the calculation as an additional measure of provenance.
    Even though the information written there should be a derivation of the contents of the nodes that were passed as input nodes, since it is a derived form we store this explicitly nonetheless.
    Sometimes, this behavior is undesirable, for example for efficiency or data privacy reasons, so it can be controlled with various lists such as :ref:`local_copy_list <topics:calculations:usage:calcjobs:file_lists_local_copy>` and :ref:`provenance_exclude_list <topics:calculations:usage:calcjobs:file_lists_provenance_exclude>`.

All the other required information, such as the directives of which files to copy and what command line options to use are defined through the :py:class:`~aiida.common.datastructures.CalcInfo` datastructure, which should be returned from the method as the only value.
In principle, this is what one **should do** in the ``prepare_for_submission`` method:

* Writing raw inputs files required for the calculation to run to the ``folder`` sandbox folder.
* Use a ``CalcInfo`` to instruct the engine which files to copy to the working directory
* Use a ``CalcInfo`` to tell which codes should run, using which command line parameters, such as standard input and output redirection.

.. note::

    The ``prepare_for_submission`` does not have to write the submission script itself.
    The engine will know how to do this, because the codes that are to be used have been configured on a specific computer, which defines what scheduler is to be used.
    This gives the engine all the necessary information on how to write the launch script such as what scheduler directives to write.

Now that we know what the ``prepare_for_submission`` is expected to do, let's see how the implementation of the ``ArithmeticAddCalculation`` accomplishes it line-by-line.
The input file required for this example calculation will consist of the two integers that are passed as inputs.
The ``self.inputs`` attribute returns an attribute dictionary with the parsed and validated inputs, according to the process specification defined in the ``define`` method.
This means that you do not have to validate the inputs yourself.
That is to say, if an input is marked as required and of a certain type, by the time we get to the ``prepare_for_submission`` it is guaranteed that the dictionary returned by ``self.inputs`` will contain that input and of the correct type.

From the two inputs ``x`` and ``y`` that will have been passed when the calculation job was launched, we should now generate the input file, that is simply a text file with these two numbers on a single line, separated by a space.
We accomplish this by opening a filehandle to the input file in the sandbox folder and write the values of the two ``Int`` nodes to the file.

.. note::

    The format of this input file just so happens to be the format that the :ref:`bash script<topics:calculations:concepts:calcjobs>` expects that we are using in this example.
    The exact number of input files and their content will of course depend on the code for which the calculation job is being written.

With the input file written, we now have to create an instance of :py:class:`~aiida.common.datastructures.CalcInfo` that should be returned from the method.
This data structure will instruct the engine exactly what needs to be done to execute the code, such as what files should be copied to the remote computer where the code will be executed.
In this simple example, we define four simple attributes:

* ``codes_info``: a list of :py:class:`~aiida.common.datastructures.CodeInfo` datastructures, that tell which codes to run consecutively during the job
* ``local_copy_list``: a list of tuples that instruct what files to copy to the working directory from the local machine
* ``remote_copy_list``: a list of tuples that instruct what files to copy to the working directory from the machine on which the job will run
* ``retrieve_list``: a list of tuples instructing which files should be retrieved from the working directory and stored in the local repository after the job has finished

See :ref:`topics:calculations:usage:calcjobs:file-copy-order` for details on the order in which input files are copied to the working directory.
In this example we only need to run a single code, so the ``codes_info`` list has a single ``CodeInfo`` datastructure.
This datastructure needs to define which code it needs to run, which is one of the inputs passed to the ``CalcJob``, and does so by means of its UUID.
Through the ``stdout_name`` attribute, we tell the engine where the output of the executable should be redirected to.
In this example this is set to the value of the  ``output_filename`` option.
What options are available in calculation jobs, what they do and how they can be set will be explained in the :ref:`section on options<topics:calculations:usage:calcjobs:options>`.
Finally, the ``cmdline_params`` attribute takes a list with command line parameters that will be placed *after* the executable in the launch script.
Here we use it to explicitly instruct the executable to read its input from the filename stored in the option ``input_filename``.

.. note::

    Since we instruct the executable should read the input from ``self.options.input_filename``, this is also the filename we used when writing that very input file in the sandbox folder.

Finally, we have to define the various "file lists" that tell what files to copy from where to where and what files to retrieve.
Here we will briefly describe their intended goals.
The implementation details will be described in full in the :ref:`file lists section<topics:calculations:usage:calcjobs:file_lists>`.

The local copy list is useful to instruct the engine to copy over files that you might already have stored in your database, such as instances of :py:class:`~aiida.orm.nodes.data.singlefile.SinglefileData` nodes, that you can define and pass as inputs of the ``CalcJob``.
You could have of course many copied their content to the ``folder`` sandbox folder, which will also have caused them to be written to the working directory.
The disadvantage of that method, however, is that all the contents written to the sandbox folder will also be stored in the repository of the ``CalcJobNode`` that will represent the execution of the ``CalcJob`` in the provenance graph.
This will cause duplication of the data contained within these data nodes.
By not writing them explicitly to the sandbox folder, you avoid this duplication, without losing provenance, because the data node itself will of course be recorded in the provenance graph.

The remote copy list is useful to avoid unnecessary file transfers between the machine where the engine runs and where the calculation jobs are executed.
For example, imagine you have already completed a calculation job on a remote cluster and now want to launch a second one, that requires some of the output files of the first run as its inputs.
The remote copy list allows you to specify exactly what output files to copy to the remote working directory, without them having to be retrieved to the engine's machine in between.

The retrieve list, finally, allows you to instruct the engine what files should be retrieved from the working directory after the job has terminated.
These files will be downloaded to the local machine, stored in a :py:class:`~aiida.orm.nodes.data.folder.FolderData` data node and attached as an output to the ``CalcJobNode`` with the link label ``retrieved``.

.. note::

    We didn't explicitly define the ``retrieved`` folder data node as an output in the example ``ArithmeticAddCalculation`` implementation shown above.
    This is because this is already defined by the ``CalcJob`` base class.
    Just as the ``code`` input, the ``retrieved`` output is common for all calculation job implementations.


.. _topics:calculations:usage:calcjobs:file_lists:

File lists
----------

.. _topics:calculations:usage:calcjobs:file_lists_local_copy:

Local copy list
~~~~~~~~~~~~~~~
The local copy list consists of three-element tuples, each defining a file or directory to be copied.
The tuple contains the following items:

* Node UUID: The UUID of the node (e.g. a ``SinglefileData`` or ``FolderData``) containing the file/directory.
* Source Relative Path: The path of the file/directory within the node's repository, relative to its base directory.
* Target Relative Path: The destination path relative to the working directory of the target node, where the file/directory contents will be copied.

As an example, consider a ``CalcJob`` implementation that receives a ``SinglefileData`` node as input with the name ``pseudopotential``, to copy its contents one can specify:

.. code:: python

    calc_info.local_copy_list = [(self.inputs.pseudopotential.uuid, self.inputs.pseudopotential.filename, 'pseudopotential.dat')]

The ``SinglefileData`` node only contains a single file by definition, the relative path of which is returned by the ``filename`` attribute.
If instead, you need to transfer a specific file from a ``FolderData``, you can specify the explicit key of the file, like so:

.. code:: python

    calc_info.local_copy_list = [(self.inputs.folder.uuid, 'internal/relative/path/file.txt', 'relative/target/file.txt')]

Note that the filenames in the relative source and target path need not be the same.
This depends fully on how the files are stored in the node's repository and what files need to be written to the working directory.

To copy the contents of a directory of the source node, simply define it as the `source relative path`.
For example, imagine we have a `FolderData` node that is passed as the `folder` input, which has the following repository virtual hierarchy:

.. code:: bash

    ├─ sub
    │  └─ file_b.txt
    └─ file_a.txt

If the entire content needs to be copied over, specify the ``local_copy_list`` as follows:

.. code:: python

    calc_info.local_copy_list = [(self.inputs.folder.uuid, '.', None)]

The ``'.'`` here indicates that the entire contents need to be copied over.
Alternatively, one can specify a sub directory, e.g.:

.. code:: python

    calc_info.local_copy_list = [(self.inputs.folder.uuid, 'sub', None)]

Finally, the `target relative path` can be used to write the contents of the source repository to a particular sub directory in the working directory.
For example, the following statement:

.. code:: python

    calc_info.local_copy_list = [(self.inputs.folder.uuid, 'sub', 'relative/target')]

will result in the following file hierarchy in the working directory of the calculation:

.. code:: bash

    └─ relative
       └─ target
           └─ file_b.txt

One might think what the purpose of the list is, when one could just as easily use normal the normal API to write the file to the ``folder`` sandbox folder.
It is true, that in this way the file will be copied to the working directory, however, then it will *also* be copied into the repository of the calculation node.
Since in this case it is merely a direct one-to-one copy of the file that is already part of one of the input nodes (in an unaltered form), this duplication is unnecessary and adds useless weight to the file repository.
Using the ``local_copy_list`` prevents this unnecessary duplication of file content.
It can also be used if the content of a particular input node is privacy sensitive and cannot be duplicated in the repository.

.. _topics:calculations:usage:calcjobs:file_lists_provenance_exclude:

Provenance exclude list
~~~~~~~~~~~~~~~~~~~~~~~
The :ref:`local_copy_list <topics:calculations:usage:calcjobs:file_lists_local_copy>`  allows one to instruct the engine to write files from the input files to the working directory, without them *also* being copied to the file repository of the calculation node.
As discussed in the corresponding section, this is useful in order to avoid duplication or in case where the data of the nodes is proprietary or privacy sensitive and cannot be duplicated arbitrarily everywhere in the file repository.
However, the limitation of the ``local_copy_list`` is that the it can only target single files in its entirety and cannot be used for arbitrary files that are written to the ``folder`` sandbox folder.
To provide full control over what files from the ``folder`` are stored permanently in the calculation node file repository, the ``provenance_exclude_list`` is introduced.
This :py:class:`~aiida.common.datastructures.CalcInfo` attribute is a list of filepaths, relative to the base path of the ``folder`` sandbox folder, which *are not stored* in the file repository.

Consider the following file structure as written by an implementation of ``prepare_for_submission`` to the ``folder`` sandbox:

.. code:: bash

    ├─ sub
    │  ├─ file_b.txt
    │  └─ personal.dat
    ├─ file_a.txt
    └─ secret.key

Clearly, we do not want the ``personal.dat`` and ``secret.key`` files to end up permanently in the file repository.
This can be achieved by defining:

.. code:: python

    calc_info.provenance_exclude_list = ['sub/personal.dat', 'secret.key']

With this specification, the final contents of the repository of the calculation node will contain:

.. code:: bash

    ├─ sub
    │  └─ file_b.txt
    └─ file_a.txt

.. _topics:calculations:usage:calcjobs:file_lists_remote_copy:

Remote copy list
~~~~~~~~~~~~~~~~
The remote copy list takes tuples of length three, each of which represents a file to be copied on the remote machine where the calculation will run, defined through the following items:

* `computer uuid`: this is the UUID of the ``Computer`` on which the source file resides. For now the remote copy list can only copy files on the same machine where the job will run.
* `source absolute path`: the absolute path of the source file on the remote machine
* `target relative path`: the relative path within the working directory to which to copy the file

.. code:: python

    calc_info.remote_copy_list[(self.inputs.parent_folder.computer.uuid, 'output_folder', 'restart_folder')]

Note that the source path can point to a directory, in which case its contents will be recursively copied in its entirety.

.. _topics:calculations:usage:calcjobs:file_lists_retrieve:

Retrieve list
~~~~~~~~~~~~~
The retrieve list is a list of instructions of what files and folders should be retrieved by the engine once a calculation job has terminated.
Each instruction should have one of two formats:

* a string representing a relative filepath in the remote working directory
* a tuple of length three that allows to control the name of the retrieved file or folder in the retrieved folder

The retrieve list can contain any number of instructions and can use both formats at the same time.
The first format is obviously the simplest, however, this requires one knows the exact name of the file or folder to be retrieved and in addition any subdirectories will be ignored when it is retrieved.
If the exact filename is not known and `glob patterns <https://en.wikipedia.org/wiki/Glob_%28programming%29>`_ should be used, or if the original folder structure should be (partially) kept, one should use the tuple format, which has the following format:

* `source relative path`: the relative path, with respect to the working directory on the remote, of the file or directory to retrieve.
* `target relative path`: the relative path of the directory in the retrieved folder in to which the content of the source will be copied. The string ``'.'`` indicates the top level in the retrieved folder.
* `depth`: the number of levels of nesting in the source path to maintain when copying, starting from the deepest file.

To illustrate the various possibilities, consider the following example file hierarchy in the remote working directory:

.. code:: bash

    ├─ path
    |  ├── sub
    │  │   ├─ file_c.txt
    │  │   └─ file_d.txt
    |  └─ file_b.txt
    └─ file_a.txt

Below, you will find examples for various use cases of files and folders to be retrieved.
Each example starts with the format of the ``retrieve_list``, followed by a schematic depiction of the final file hierarchy that would be created in the retrieved folder.

Explicit file or folder
.......................

Retrieving a single toplevel file or folder (with all its contents) where the final folder structure is not important.

.. code:: bash

    retrieve_list = ['file_a.txt']

    └─ file_a.txt

.. code:: bash

    retrieve_list = ['path']

    ├── sub
    │   ├─ file_c.txt
    │   └─ file_d.txt
    └─ file_b.txt


Explicit nested file or folder
..............................

Retrieving a single file or folder (with all its contents) that is located in a subdirectory in the remote working directory, where the final folder structure is not important.

.. code:: bash

    retrieve_list = ['path/file_b.txt']

    └─ file_b.txt

.. code:: bash

    retrieve_list = ['path/sub']

    ├─ file_c.txt
    └─ file_d.txt


Explicit nested file or folder keeping (partial) hierarchy
..........................................................

The following examples show how the file hierarchy of the retrieved files can be controlled.
By changing the ``depth`` parameter of the tuple, one can control what part of the remote folder hierarchy is kept.
In the given example, the maximum depth of the remote folder hierarchy is ``3``.
The following example shows that by specifying ``3``, the exact folder structure is kept:

.. code:: bash

    retrieve_list = [('path/sub/file_c.txt', '.', 3)]

    └─ path
        └─ sub
           └─ file_c.txt

For ``depth=2``, only two levels of nesting are kept (including the file itself) and so the ``path`` folder is discarded.

.. code:: bash

    retrieve_list = [('path/sub/file_c.txt', '.', 2)]

    └─ sub
       └─ file_c.txt

The same applies for directories.
By specifying a directory for the first element, all its contents will be retrieved.
With ``depth=1``, only the first level ``sub`` is kept of the folder hierarchy.

.. code:: bash

    retrieve_list = [('path/sub', '.', 1)]

    └── sub
        ├─ file_c.txt
        └─ file_d.txt


Pattern matching
................

If the exact file or folder name is not known beforehand, glob patterns can be used.
In the following examples, all files that match ``*c.txt`` in the directory ``path/sub`` will be retrieved.

To maintain the folder structure set ``depth`` to ``None``:

.. code:: bash

    retrieve_list = [('path/sub/*c.txt', '.', None)]

    └─ path
        └─ sub
           └─ file_c.txt

Alternatively, the ``depth`` can be used to specify the number of levels of nesting that should be kept.
For example, ``depth=0`` instructs to copy the matched files without any subfolders:

.. code:: bash

    retrieve_list = [('path/sub/*c.txt', '.', 0)]

    └─ file_c.txt

and ``depth=2`` will keep two levels in the final filepath:

.. code:: bash

    retrieve_list = [('path/sub/*c.txt', '.', 2)]

    └── sub
        └─ file_c.txt


Specific target directory
.........................

The final folder hierarchy of the retrieved files in the retrieved folder is not only determined by the hierarchy of the remote working directory, but can also be controlled through the second and third elements of the instructions tuples.
The final ``depth`` element controls what level of hierarchy of the source is maintained, where the second element specifies the base path in the retrieved folder into which the remote files should be retrieved.
For example, to retrieve a nested file, maintaining the remote hierarchy and storing it locally in the ``target`` directory, one can do the following:

.. code:: bash

    retrieve_list = [('path/sub/file_c.txt', 'target', 3)]

    └─ target
        └─ path
            └─ sub
               └─ file_c.txt

The same applies for folders that are to be retrieved:

.. code:: bash

    retrieve_list = [('path/sub', 'target', 1)]

    └─ target
        └── sub
            ├─ file_c.txt
            └─ file_d.txt

Note that `target` here is not used to rename the retrieved file or folder, but indicates the path of the directory into which the source is copied.
The target relative path is also compatible with glob patterns in the source relative paths:

.. code:: bash

    retrieve_list = [('path/sub/*c.txt', 'target', 0)]

    └─ target
        └─ file_c.txt


Retrieve temporary list
~~~~~~~~~~~~~~~~~~~~~~~

Recall that, as explained in the :ref:`'prepare' section<topics:calculations:usage:calcjobs:prepare>`, all the files that are retrieved by the engine following the 'retrieve list', are stored in the ``retrieved`` folder data node.
This means that any file you retrieve for a completed calculation job will be stored in your repository.
If you are retrieving big files, this can cause your repository to grow significantly.
Often, however, you might only need a part of the information contained in these retrieved files.
To solve this common issue, there is the concept of the 'retrieve temporary list'.
The specification of the retrieve temporary list is identical to that of the normal :ref:`retrieve list<topics:calculations:usage:calcjobs:file_lists_retrieve>`, but it is added to the ``calc_info`` under the ``retrieve_temporary_list`` attribute:

.. code-block:: python

    calcinfo = CalcInfo()
    calcinfo.retrieve_temporary_list = ['relative/path/to/file.txt']

The only difference is that, unlike the files of the retrieve list which will be permanently stored in the retrieved :py:class:`~aiida.orm.nodes.data.folder.FolderData` node, the files of the retrieve temporary list will be stored in a temporary sandbox folder.
This folder is then passed under the ``retrieved_temporary_folder`` keyword argument to the ``parse`` method of the :ref:`parser<topics:calculations:usage:calcjobs:parsers>`, if one was specified for the calculation job:

.. code-block:: python

    def parse(self, **kwargs):
        """Parse the retrieved files of the calculation job."""

        retrieved_temporary_folder = kwargs['retrieved_temporary_folder']

The parser implementation can then parse these files and store the relevant information as output nodes.

.. important::

    The type of ``kwargs['retrieved_temporary_folder']`` is a simple ``str`` that represents the `absolute` filepath to the temporary folder.
    You can access its contents with the ``os`` standard library module or convert it into a ``pathlib.Path``.

After the parser terminates, the engine will automatically clean up the sandbox folder with the temporarily retrieved files.
The concept of the ``retrieve_temporary_list`` is essentially that the files will be available during parsing and will be destroyed immediately afterwards.


.. _topics:calculations:usage:calcjobs:file-copy-order:

Controlling order of file copying
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. versionadded:: 2.6

Input files can come from three sources in a calculations job:

#. Sandbox: files that are written by the ``CalcJob`` plugin in the :meth:`~aiida.engine.processes.calcjobs.calcjob.CalcJob.prepare_for_submission` to the sandbox folder
#. Local: files of input nodes that are defined through the ``local_copy_list``
#. Remote: files of ``RemoteData`` input nodes that are defined through the ``remote_copy_list``

By default, these files are copied in the order of sandbox, local, and finally remote.
The order can be controlled through the ``file_copy_operation_order`` attribute of the :class:`~aiida.common.datastructures.CalcInfo` which takes a list of :class:`~aiida.common.datastructures.FileCopyOperation` instances, for example:

.. code-block:: python

    class CustomFileCopyOrder(CalcJob)

        def prepare_for_submission(self, _):
            from aiida.common.datastructures import CalcInfo, CodeInfo, FileCopyOperation

            code_info = CodeInfo()
            code_info.code_uuid = self.inputs.code.uuid
            calc_info = CalcInfo()
            calc_info.codes_info = [code_info]
            calc_info.file_copy_operation_order = [
                FileCopyOperation.LOCAL,
                FileCopyOperation.REMOTE,
                FileCopyOperation.SANDBOX,
            ]
            return calc_info


.. _topics:calculations:usage:calcjobs:stashing:


Stashing Files on the Remote
----------------------------


In many scientific workflows, calculations produce files that are either too large to retrieve to your local AiiDA repository or simply not needed locally. However, you may still want to keep these files available on the remote machine—for example, to facilitate restarts, enable debugging, or for archiving purposes—but outside the compute or scratch directory that might be cleaned up regularly.

AiiDA offers a stashing mechanism to help with this: it can automatically copy or archive specified files to a persistent location on the remote computer, either immediately after the calculation completes or as a separate follow-up calcjob.

Below, we briefly describe the two supported methods for remote stashing and provide guidance on how to choose the best approach for your use case.

Which method should I use?
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1

   * - Scenario
     - Recommended method
   * - Stash files regardless of calculation outcome (even if failed)
     - Method 1: Stashing **Immediately After Job Completion on HPC**
   * - Stash files from an already completed calculation
     - Method 2: Stashing via a **Dedicated Calculation Job**
   * - I want to submit my own custom script for stashing
     - Method 2: Stashing via a **Dedicated Calculation Job**

Quick comparison between these methods:

::

   (Method 1) Immediate stashing:
   +---------------------+      +--------------------------------+
   |  Calculation job    | ---> | Stash files with no submission |
   +---------------------+      |         (before retrieve)      |
                                +--------------------------------+
                                             |
                                             v
                                +------------------------+
                                | Retrieve & parse files |
                                +------------------------+

   (Method 2) Stashing via Dedicated Calculation:
   +---------------------+      +------------------------+
   |  Calculation job    | ---> | Retrieve & parse files |  ->
   +---------------------+      +------------------------+

   +---------------------+      +---------------------------------+
   |  StashCalculation   | ---> |  Stash files with no submission |
   +---------------------+      |         or                      |
                                | Submit as a custom script       |
                                +---------------------------------+


Method 1: Stashing Immediately After Job Completion on HPC
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This approach performs stashing as soon as the calculation finishes, but **before** any files are retrieved or parsed. It is available for stash modes: ``COPY``, ``COMPRESS_TAR``, ``COMPRESS_TARBZ2``, ``COMPRESS_TARGZ``, and ``COMPRESS_TARXZ``.

**Typical use case:** You need to preserve output files from all runs, even failed ones, for debugging or restarting purposes.

Specify which files or folders to stash (by relative paths) using the ``stash.source_list`` option, and the destination on the remote using ``stash.target_base``. Example:

.. code-block:: python

   from aiida.common.datastructures import StashMode

   inputs = {
       'code': ....,
       ...
       'metadata': {
           'options': {
               'stash': {
                   'stash_mode': StashMode.COPY.value,
                   'target_base': '/storage/project/stash_folder',
                   'source_list': ['aiida.out', 'output.txt'],
               }
           }
       }
   }

The stashed files are represented by an output node with the label ``remote_stash`` (an instance of ``RemoteStashFolderData``), attached to the calculation node. This node acts like a "symbolic link" pointing to the location on the remote system.

.. important::

   The stashing operation occurs *before* any file retrieval or parsing. As a result, files may be stashed even for calculations that later turn out to have failed.

Method 2: Stashing via a Dedicated Calculation Job
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This approach lets you stash files **only after a successful calculation**. This is done by running a follow-up `core.stash` calculation that copies or archives files from the remote folder of a finished calculation job.

**Typical use case:** You want to avoid keeping files from failed calculations, or need to run custom post-processing scripts.

This method requires specifying the ``remote_folder`` of the original calculation as ``source_node``. Example:

.. code-block:: python

    from aiida.common.datastructures import StashMode
    from aiida.orm import load_node, load_computer

    StashCalculation = CalculationFactory('core.stash')

    calcjob_node = load_node(<CALCJOB_PK>)
    remote_folder = calcjob_node.outputs.remote_folder

    inputs = {
        'metadata': {
            'computer': load_computer(label=<COMPUTER_LABEL>),
            'options': {
                'stash': {
                    'stash_mode': StashMode.COPY.value,
                    'target_base': '/scratch/',
                    'source_list': ['aiida.out', 'output.txt'],
                },
            },
        },
        'source_node': remote_folder,
    }

    result = run(StashCalculation, **inputs)

Custom script stashing (advanced)
.................................

You can run your own script as part of the stashing step, using the ``SUBMIT_CUSTOM_CODE`` stash mode.
First, place your script on the remote machine and define it as an AiiDA code:

.. code-block:: python

   code = InstalledCode(
       label='<MY_STASH_CODE>',
       default_calc_job_plugin='core.stash',
       computer=load_computer(<COMPUTER_LABEL>),
       filepath_executable=str(<Path_to_script.sh>),
   )
   code.store()

Run the custom stashing job with:

.. code-block:: python

   StashCalculation = CalculationFactory('core.stash')
   inputs = {
       'metadata': {
           'computer': load_computer(<COMPUTER_LABEL>),
           'options': {
               'resources': {'num_machines': 1},
               'stash': {
                   'stash_mode': StashMode.SUBMIT_CUSTOM_CODE.value,
                   'target_base': str(target_base),
                   'source_list': ['aiida.out', 'output.txt'],
               },
           },
       },
       'source_node': <orm.RemoteData>,
       'code': load_code(label='<MY_STASH_CODE>'),
   }
   submit(StashCalculation, **inputs)



This calculation produces an ``aiida.in`` file in JSON format with the stashing parameters, for example:

.. code-block:: none

   {"source_path": <orm.RemoteData>.get_remote_path(),
    "source_list": ["aiida.out", "output.txt"],
    "target_base": "/path/to/stash"}

Which is used as an input to your script:

::

    ./script.sh < aiida.in > aiida.out

Therefore, your script should parse the JSON, and implement the stashing by any means. For example:

.. code-block:: bash

   json=$(cat)
   source_path=$(echo "$json" | jq -r '.source_path')
   source_list=$(echo "$json" | jq -r '.source_list[]')
   target_base=$(echo "$json" | jq -r '.target_base')

   mkdir -p "$target_base"
   for item in $source_list; do
       cp "$source_path/$item" "$target_base/"
       echo "$item copied successfully."
   done

This way you can implement any custom logic in your script, such as tape commands, handling errors, or filtering files dynamically.

Caveats and best practices
""""""""""""""""""""""""""

.. important::

   - **AiiDA does not manage the files in the remote stash after creation.** Files may be deleted or lost at any time, depending on the cluster's configuration or cleanup policies.
   - **Check quotas and permissions**: Make sure you have write access and sufficient quota in the target stash directory.
   - **Handle errors**: If the stashing operation fails (e.g., due to missing files or lack of permissions), AiiDA will log the issue, but will not raise. It is your responsibility to check and recover as needed.
   - **Source files are not deleted after stashing**: This is to prevent unwanted data-loss.


.. _topics:calculations:usage:calcjobs:unstashing:


Unstashing Files from the Remote
--------------------------------

AiiDA provides an unstashing mechanism through the `core.unstash` calculation to retrieve previously stashed files. The process supports all stash modes and offers two restoration targets:

1. **OriginalPlace**: Restores files back to the original remote folder location. E.g., for restarting a calculation.
2. **NewRemoteData**: Restores files to the new remote folder of `UnstashCalculation`. E.g., for further processing.

::

   +------------------------+      +---------------------+
   | Stashed files          | ---> | UnstashCalculation  |
   | (RemoteStashData node) |      +---------------------+
   +------------------------+                |
                                             v
                              +---------------------------+
                              | Files restored to:        |
                              | - Original location OR    |
                              | - New RemoteData folder   |
                              +---------------------------+


Example of unstashing files:

.. code-block:: python

    from aiida.common.datastructures import UnstashTargetMode
    from aiida.orm import load_node, load_computer

    UnstashCalculation = CalculationFactory('core.unstash')

    # Get the stashed data node from a previous stash operation
    stash_node = load_node(<STASH_NODE_PK>)  # RemoteStashFolderData or RemoteStashCompressedData

    inputs = {
        'metadata': {
            'computer': load_computer(label=<COMPUTER_LABEL>),
            'options': {
                'resources': {'num_machines': 1},
                'unstash': {
                    'unstash_target_mode': UnstashTargetMode.NewRemoteData.value,
                    'source_list': ['*'],  # Optional for StashMode.COPY
                },
            },
        },
        'source_node': stash_node,
    }

    result = run(UnstashCalculation, **inputs)


Unstashing from Different Stash Modes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The unstashing process automatically handles different stash modes with varying capabilities:

**COPY mode:**
Files are directly copied from the stashed location to the target. You can selectively restore specific files using the ``source_list`` parameter. For example, ``source_list = ['restart.chk']`` will only restore the restart file if it exists in the stash.

**COMPRESS modes (TAR, TARBZ2, TARGZ, TARXZ):**
Archives are automatically extracted and files restored to the target location. Currently, ``source_list`` must be set to ``['*']`` to extract all contents. Future versions may support selective file extraction.

**SUBMIT_CUSTOM_CODE mode:**
For custom stashing scripts, you must provide a corresponding custom unstashing script with full control over the restoration process.

Custom Script Unstashing (Advanced)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For stashed files created with custom scripts, you can provide a custom unstashing script.
The custom unstashing script receives a JSON input file (``aiida.in``) with the following structure:

.. code-block:: none

   {"source_path": "/path/to/stashed/files",
    "source_list": ["aiida.out", "output.txt"],
    "target_base": "/path/to/restore/location"}

Example custom unstashing script:

.. code-block:: bash

   #!/bin/bash
   json=$(cat)
   source_path=$(echo "$json" | jq -r '.source_path')
   source_list=$(echo "$json" | jq -r '.source_list[]')
   target_base=$(echo "$json" | jq -r '.target_base')

   mkdir -p "$target_base"
   for item in $source_list; do
       cp "$source_path/$item" "$target_base/"
       echo "$item copied successfully."
   done

Now, you can install that script as a `code`.

.. code-block:: python

   # Define your custom unstashing script as an AiiDA code
   unstash_code = InstalledCode(
       label='<MY_UNSTASH_CODE>',
       default_calc_job_plugin='core.unstash',
       computer=load_computer(<COMPUTER_LABEL>),
       filepath_executable=str(<Path_to_unstash_script.sh>),
   )
   unstash_code.store()

.. note::

   In this example, our unstashing script is identical to the stashing script that we used earlier!
   That means we could just as well skip the installation step and use the `MY_STASH_CODE` code again!

.. code-block:: python

   # Run unstashing with custom code
   inputs = {
       'metadata': {
           'computer': load_computer(<COMPUTER_LABEL>),
           'options': {
               'resources': {'num_machines': 1},
               'unstash': {
                   'unstash_target_mode': UnstashTargetMode.NewRemoteData.value,
                   'source_list': ['aiida.out', 'output.txt'],
               },
           },
       },
       'source_node': stash_node,  # RemoteStashCustomData node
       'code': unstash_code,
   }

   submit(UnstashCalculation, **inputs)


Finding Stashed Data Nodes
~~~~~~~~~~~~~~~~~~~~~~~~~~~

To locate stashed data nodes from previous calculations:

.. code-block:: python

    from aiida.orm import QueryBuilder, RemoteStashData

    # Find all stashed data from a specific calculation
    calcjob_node = load_node(<CALCJOB_PK>)

    # For immediate stashing (Method 1)
    if 'remote_stash' in calcjob_node.outputs:
        stash_node = calcjob_node.outputs.remote_stash

    # For separate stash calculation (Method 2)
    qb = QueryBuilder()
    qb.append(CalculationFactory('core.stash'),
              filters={'id': <STASH_CALC_PK>},
              tag='calc')
    qb.append((RemoteStashData),
              with_incoming='calc',
              project='*')
    stash_node = qb.one()[0]


Best Practices and Considerations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. important::

   - **Usability**: Unlike stashing, untashing can only be performed as a dedicated calcjob via `core.unstash`.

   - **Check stash node availability**: Before unstashing, verify that the stashed files still exist on the remote system. Files in the stash location are not managed by AiiDA and may be deleted by system administrators.

   - **Error handling**: In case of custom stashing, it's your sole responsibility to manage the failures and log errors.

.. _topics:calculations:usage:calcjobs:options:

Options
-------
In addition to the common metadata inputs, such as ``label`` and ``description``, that all processes have, the :py:class:`~aiida.engine.processes.calcjobs.calcjob.CalcJob` has an additonal input called ``options``.
These options allow to subtly change the behavior of the calculation job, for example which parser should be used once it is finished and special scheduler directives.
The full list of available options are documented below as part of the ``CalcJob`` interface:

.. aiida-calcjob:: CalcJob
    :module: aiida.engine.processes.calcjobs
    :expand-namespaces:


The ``rerunnable`` option enables the scheduler to re-launch the calculation if it has failed, for example due to node failure or a failure to launch the job. It corresponds to the ``--requeue`` option in SLURM, and the ``-r`` option in SGE, LSF, and PBS. The following two conditions must be met in order for this to work well with AiiDA:

- the scheduler assigns the same job-id to the restarted job
- the code produces the same results if it has already partially run before (not every scheduler may produce this situation)

Because this depends on the scheduler, its configuration, and the code used, we cannot say conclusively when it will work -- do your own testing! It has been tested on a cluster using SLURM, but that does not guarantee other SLURM clusters behave in the same way.


.. _topics:calculations:usage:calcjobs:mpi:

Controlling MPI
---------------

The `Message Passing Interface <https://en.wikipedia.org/wiki/Message_Passing_Interface>`_ (MPI) is a standardized and portable message-passing standard designed to function on parallel computing architectures.
AiiDA implements support for running calculation jobs with or without MPI enabled.
There are a number of settings that can be used to control when and how MPI is used.

.. _topics:calculations:usage:calcjobs:mpi:computer:

The ``Computer``
~~~~~~~~~~~~~~~~

Each calculation job is executed on a compute resource, which is modeled by an instance of the :class:`~aiida.orm.computers.Computer` class.
If the computer supports running with MPI, the command to use is stored in the ``mpirun_command`` attribute, which is retrieved and set using the :meth:`~aiida.orm.computers.Computer.get_mpirun_command` and :meth:`~aiida.orm.computers.Computer.get_mpirun_command`, respectively.
For example, if the computer has `OpenMPI <https://docs.open-mpi.org/en/v5.0.x/index.html>`_ installed, it can be set to ``mpirun``.
If the ``Computer`` does not specify an MPI command, then enabling MPI for a calculation job is ineffective.

.. _topics:calculations:usage:calcjobs:mpi:code:

The ``Code``
~~~~~~~~~~~~

.. versionadded:: 2.3

When creating a code, you can tell AiiDA that it should be run as an MPI program, by setting the ``with_mpi`` attribute to ``True`` or ``False``.
From AiiDA 2.3 onward, this is the **recommended** way of controlling MPI behavior.
The attribute can be set from the Python API as ``AbstractCode(with_mpi=with_mpi)`` or through the ``--with-mpi`` / ``--no-with-mpi`` option of the ``verdi code create`` CLI command.
If the code can be run with or without MPI, setting the ``with_mpi`` attribute can be skipped.
It will default to ``None``, leaving the question of whether to run with or without MPI up to the ``CalcJob`` plugin or user input.

.. _topics:calculations:usage:calcjobs:mpi:calcjob-implementation:

The ``CalcJob`` implementation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``CalcJob`` implementation instructs AiiDA how the codes should be run through the :class:`~aiida.common.datastructures.CalcInfo` object, which it returns from the :meth:`~aiida.engine.processes.calcjobs.calcjob.CalcJob.prepare_for_submission` method.
For each code that the job should run (usually only a single one), a :class:`~aiida.common.datastructures.CodeInfo` object should be added to the list of the ``CalcInfo.codes_info`` attribute.
If the plugin developer knows that the executable being wrapped is *always* MPI program (no serial version available) or *never* an MPI program, they can set the ``withmpi`` attribute of the ``CodeInfo`` to ``True`` or ``False``, respectively.
Note that this setting is fully optional; if the code could be run either way, it is best not to set it and leave it up to the ``Code`` or the ``metadata.options.withmpi`` input.

.. note::

    When implementing a ``CalcJob`` that runs a single code, consider using specifying whether MPI should be enabled or disabled through the :ref:`metadata option<topics:calculations:usage:calcjobs:mpi:calcjob-inputs>`.
    This can be accomplished by changing the default in the process specification:

    .. code:: python

        class SomeCalcJob(CalcJob):

            @classmethod
            def define(cls, spec):
                super().define(spec)
                spec.inputs['metadata']['options']['withmpi'].default = True

    The advantage over using the ``CodeInfo.withmpi`` attribute is that the default of the metadata option can be introspected programmatically from the process spec, and so is more visible to the user.

    Naturally, this approach is not viable for calculation jobs that run multiple codes that are different in whether they require MPI or not.
    In this case, one should resort to using the ``CodeInfo.withmpi`` attribute.

.. _topics:calculations:usage:calcjobs:mpi:calcjob-inputs:

The ``CalcJob`` inputs
~~~~~~~~~~~~~~~~~~~~~~

Finally, the MPI setting can be controlled on a per-instance basis, using the ``withmpi`` :ref:`metadata option<topics:calculations:usage:calcjobs:options>`.
If MPI should be enabled or disabled, explicitly set this option to ``True`` or ``False``, respectively.
For example, the following instructs to run all codes in the calculation job with MPI enabled:

.. code:: python

    inputs = {
        ...,
        'metadata': {
            'options': {
                'withmpi': True
            }
        }
    }
    submit(CalcJob, **inputs)

The default for this option is set to ``False`` on the base ``CalcJob`` implementation, but it will be overruled if explicitly defined.

.. note::

    The value set for the ``withmpi`` option will be applied to all codes.
    If a calculation job runs more than one code, and each requires a different MPI setting, this option should not be used, and instead MPI should be controlled :ref:`through the code input <topics:calculations:usage:calcjobs:mpi:code>`.

.. _topics:calculations:usage:calcjobs:mpi:conflict-resolution:

Conflict resolution
~~~~~~~~~~~~~~~~~~~

As described above, MPI can be enabled or disabled for a calculation job on a number of levels:

* The ``Code`` input
* The ``CalcJob`` implementation
* The ``metadata.options.withmpi`` input

MPI is enabled or disabled if any of these values is explicitly set to ``True`` or ``False``, respectively.
If multiple values are specified and they are not equivalent, a ``RuntimeError`` is raised.
Depending on the conflict, one has to change the ``Code`` or ``metadata.options.withmpi`` input.
If none of the values are explicitly defined, the value specified by the default of ``metadata.options.withmpi`` is taken.


.. _topics:calculations:usage:calcjobs:launch:

Launch
------

Launching a calculation job is no different from launching any other process class, so please refer to the section on :ref:`launching processes<topics:processes:usage:launch>`.
The only caveat that we should place is that calculation jobs typically tend to take quite a bit of time.
The trivial example we used above of course will run very fast, but a typical calculation job that will be submitted to a scheduler will most likely take longer than just a few seconds.
For that reason it is highly advisable to **submit** calculation jobs instead of running them.
By submitting them to the daemon, you free up your interpreter straight away and the process will be checkpointed between the various :ref:`transport tasks<topics:calculations:concepts:calcjobs_transport_tasks>` that will have to be performed.
The exception is of course when you want to run a calculation job locally for testing or demonstration purposes.


.. _topics:calculations:usage:calcjobs:dry_run:

Dry run
-------
The calculation job has one additional feature over all other processes when it comes to launching them.
Since an incorrectly configured calculation job can potentially waste computational resources, one might want to inspect the input files that will be written by the plugin, before actually submitting the job.
A so-called dry-run is possible by simply specifying it in the metadata of the inputs.
If you are using the process builder, it is as simple as:

.. code:: python

    builder.metadata.dry_run = True

When you now launch the process builder, the engine will perform the entire process of a normal calculation job run, except that it will not actually upload and submit the job to the remote computer.
However, the ``prepare_for_submission`` method will be called.
The inputs that it writes to the input folder will be stored in temporary folder called ``submit_test`` that will be created in the current working directory.
Each time you perform a dry-run, a new sub folder will be created in the ``submit_test`` folder, which you allows you to perform multiple dry-runs without overwriting the previous results.

Moreover, the following applies:

- when calling :py:func:`~aiida.engine.launch.run` for a calculation with the
  ``dry_run`` flag set, you will get back its results, being always an empty dictionary ``{}``;

- if you call :py:func:`~aiida.engine.launch.run_get_node`, you will get back as a node
  an unstored ``CalcJobNode``. In this case, the unstored ``CalcJobNode`` (let's call it
  ``node``) will have an additional property ``node.dry_run_info``. This is a dictionary
  that contains additional information on the dry-run output. In particular, it will have
  the following keys:

  - ``folder``: the absolute path to the folder within the ``submit_test`` folder
    where the files have been created, e.g.: ``/home/user/submit_test/20190726-00019``

  - ``script_filename``: the filename of the submission script that AiiDA generated
    in the folder, e.g.: ``_aiidasubmit.sh``

- if you send a dry-run to the :py:func:`~aiida.engine.launch.submit` function,
  this will be just forwarded to run and you will get back the unstored node
  (with the same properties as above).


.. warning::

    By default the storing of provenance is enabled and this goes also for a dry run.
    If you do not want any nodes to be created during a dry run, simply set the metadata input ``store_provenance`` to ``False``.


.. _topics:calculations:usage:calcjobs:parsers:

Parsing
-------
The previous sections explained in detail how the execution of an external executable is wrapped by the ``CalcJob`` class to make it runnable by AiiDA's engine.
From the first steps of preparing the input files on the remote machine, to retrieving the relevant files and storing them in a :py:class:`~aiida.orm.nodes.data.folder.FolderData` node, that is attached as the ``retrieved`` output.
This is the last *required* step for a ``CalcJob`` to terminate, but often we would *like* to parse the raw output and attach them as queryable output nodes to the calculation job node.
To automatically trigger the parsing of a calculation job after its output has been retrieved, is to specify the :ref:`parser name option<topics:calculations:usage:calcjobs:options>`.
If the engine find this option specified, it will load the corresponding parser class, which should be a sub class of :py:class:`~aiida.parsers.parser.Parser` and calls its :py:meth:`~aiida.parsers.parser.Parser.parse` method.

To explain the interface of the ``Parser`` class and the ``parse`` method, let's take the :py:class:`~aiida.parsers.plugins.arithmetic.add.ArithmeticAddParser` as an example.
This parser is designed to parse the output produced by the simple bash script that is wrapped by the ``ArithmeticAddCalculation`` discussed in the previous sections.

.. literalinclude:: include/snippets/calcjobs/arithmetic_add_parser.py
    :language: python
    :linenos:

To create a new parser implementation, simply create a new class that sub classes the :py:class:`~aiida.parsers.parser.Parser` class.
As usual, any valid python class name will work, but the convention is to always use the ``Parser`` suffix and to use the same name as the calculation job for which the parser is designed.
For example, here we are implementing a parser for the ``ArithmeticAddCalculation``, so therefore we name it ``ArithmeticAddParser``, just replacing the ``Calculation`` suffix for ``Parser``.
The only method that needs to be implemented is the :py:meth:`~aiida.parsers.parser.Parser.parse` method.
Its signature should include ``**kwargs``, the reason for which will become clear later.
The goal of the ``parse`` method is very simple:

* Open and load the content of the output files generated by the calculation job and have been retrieved by the engine
* Create data nodes out of this raw data that are attached as output nodes
* Log human-readable warning messages in the case of worrying output
* Optionally return an :ref:`exit code<topics:processes:concepts:exit_codes>` to indicate that the results of the calculation was not successful

The advantage of adding the raw output data in different form as output nodes, is that in that form the content becomes queryable.
This allows one to query for calculations that produced specific outputs with a certain value, which becomes a very powerful approach for post-processing and analyses of big databases.

The ``retrieved`` attribute of the parser will return the ``FolderData`` node that should have been attached by the engine containing all the retrieved files, as specified using the :ref:`retrieve list<topics:calculations:usage:calcjobs:file_lists_retrieve>` in the :ref:`preparation step of the calculation job<topics:calculations:usage:calcjobs:prepare>`.
This retrieved folder can be used to open and read the contents of the files it contains.
In this example, there should be a single output file that was written by redirecting the standard output of the bash script that added the two integers.
The parser opens this file, reads its content and tries to parse the sum from it:

.. literalinclude:: include/snippets/calcjobs/arithmetic_add_parser.py
    :language: python
    :lines: 12-16
    :linenos:
    :lineno-start: 12

Note that this parsing action is wrapped in a try-except block to catch the exceptions that would be thrown if the output file could not be read.
If the exception would not be caught, the engine will catch the exception instead and set the process state of the corresponding calculation to ``Excepted``.
Note that this will happen for any uncaught exception that is thrown during parsing.
Instead, we catch these exceptions and return an exit code that is retrieved by referencing it by its label, such as ``ERROR_READING_OUTPUT_FILE`` in this example, through the ``self.exit_codes`` property.
This call will retrieve the corresponding exit code defined on the ``CalcJob`` that we are currently parsing.
Returning this exit code from the parser will stop the parsing immediately and will instruct the engine to set its exit status and exit message on the node of this calculation job.

The ``parse_stdout`` method is just a small utility function to separate the actual parsing of the data from the main parser code.
In this case, the parsing is so simple that we might have as well kept it in the main method, but this is just to illustrate that you are completely free to organize the code within the ``parse`` method for clarity.
If we manage to parse the sum, produced by the calculation, we wrap it in the appropriate :py:class:`~aiida.orm.nodes.data.int.Int` data node class, and register it as an output through the ``out`` method:

.. literalinclude:: include/snippets/calcjobs/arithmetic_add_parser.py
    :language: python
    :lines: 21-21
    :linenos:
    :lineno-start: 21

Note that if we encountered no problems, we do not have to return anything.
The engine will interpret this as the calculation having finished successfully.
You might now pose the question: "what part of the raw data should I parse and in what types of data nodes should I store it?".
This not an easy question to answer in the general, because it will heavily depend on the type of raw output that is produced by the calculation and what parts you would like to be queryable.
However, we can give you some guidelines:

*   Store data that you might want to query for, in the lightweight data nodes, such as :py:class:`~aiida.orm.nodes.data.dict.Dict`, :py:class:`~aiida.orm.nodes.data.list.List` and :py:class:`~aiida.orm.nodes.data.structure.StructureData`.
    The contents of these nodes are stored as attributes in the database, which makes sure that they can be queried for.
*   Bigger data sets, such as large (multi-dimnensional) arrays, are better stored in an :py:class:`~aiida.orm.nodes.data.array.array.ArrayData` or one of its sub classes.
    If you were to store all this data in the database, it would become unnecessarily bloated, because the chances you would have to query for this data are unlikely.
    Instead these array type data nodes store the bulk of their content in the repository.
    This way you still keep the data and therewith the provenance of your calculations, while keeping your database lean and fast!


.. _topics:calculations:usage:calcjobs:scheduler-errors:

Scheduler errors
----------------

Besides the output parsers, the scheduler plugins can also provide parsing of the output generated by the job scheduler, by implementing the :meth:`~aiida.schedulers.scheduler.Scheduler.parse_output` method.
If the scheduler plugin has implemented this method, the output generated by the scheduler, written to the stdout and stderr file descriptors as well as the output of the detailed job info command, is parsed.
If the parser detects a known problem, such as an out-of-memory (OOM) or out-of-walltime (OOW) error, the corresponding exit code will already be set on the calculation job node.
The output parser, if defined in the inputs, can inspect the exit status on the node and decide to keep it or override it with a different, potentially more useful, exit code.

.. code:: python

    class SomeParser(Parser):

        def parse(self, **kwargs):
            """Parse the contents of the output files retrieved in the `FolderData`."""

            # It is probably best to check for explicit exit codes.
            if self.node.exit_status == self.exit_codes.ERROR_SCHEDULER_OUT_OF_WALLTIME.status:
                # The scheduler parser detected an OOW error.
                # By returning `None`, the same exit code will be kept.
                return None

            # It is also possible to just check for any exit status to be set as a fallback.
            if self.node.exit_status is not None:
                # You can still try to parse files before exiting the parsing.
                return None

Note that in the example given above, the parser returns immediately if it detects that the scheduler detected a problem.
Since it returns `None`, the exit code of the scheduler will be kept and will be the final exit code of the calculation job.
However, the parser does not have to immediately return.
It can still try to parse some of the retrieved output, if there is any.
If it finds a more specific problem than the generic scheduler error, it can always return an exit code of itself to override it.
The parser can even return ``ExitCode(0)`` to have the calculation marked as successfully finished, despite the scheduler having determined that there was a problem.
The following table summarizes the possible scenarios of the scheduler parser and output parser returning an exit code and what the final resulting exit code will be that is set on the node:

+------------------------------------------------------------------------------------+-----------------------+-----------------------+-----------------------+
| **Scenario**                                                                       | **Scheduler result**  | **Retrieved result**  | **Final result**      |
+====================================================================================+=======================+=======================+=======================+
| Neither parser found any problem.                                                  | ``None``              | ``None``              | ``ExitCode(0)``       |
+------------------------------------------------------------------------------------+-----------------------+-----------------------+-----------------------+
| Scheduler parser found an issue,                                                   | ``ExitCode(100)``     | ``None``              | ``ExitCode(100)``     |
| but output parser does not override.                                               |                       |                       |                       |
+------------------------------------------------------------------------------------+-----------------------+-----------------------+-----------------------+
| Only output parser found a problem.                                                | ``None``              | ``ExitCode(400)``     | ``ExitCode(400)``     |
+------------------------------------------------------------------------------------+-----------------------+-----------------------+-----------------------+
| Scheduler parser found an issue, but the output parser overrides with a more       | ``ExitCode(100)``     | ``ExitCode(400)``     | ``ExitCode(400)``     |
| specific error code.                                                               |                       |                       |                       |
+------------------------------------------------------------------------------------+-----------------------+-----------------------+-----------------------+
| Scheduler found issue but output parser overrides saying that despite that the     | ``ExitCode(100)``     | ``ExitCode(0)``       | ``ExitCode(0)``       |
| calculation should be considered finished successfully.                            |                       |                       |                       |
+------------------------------------------------------------------------------------+-----------------------+-----------------------+-----------------------+
