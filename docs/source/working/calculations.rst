.. _working_calculations:

************
Calculations
************

A calculation is a process (see the :ref:`process section<concepts_processes>` for details) that *creates* new data.
Currently, there are two ways of implementing a calculation process:

 * :ref:`calculation function<working_calcfunctions>`
 * :ref:`calculation job<working_calcjobs>`

This section will provide detailed information and best practices on how to implement these two calculation types.

.. warning::
    This chapter assumes that the basic concept and difference between calculation functions and calculation jobs is known and when one should use on or the other.
    It is therefore crucial that, before you continue, you have read and understood the basic concept of :ref:`calculation processes<concepts_calculations>`.

.. _working_calcfunctions:

Calculation functions
=====================

The section on the :ref:`concept of calculation functions<concepts_calcfunctions>` already addressed their aim: automatic recording of their execution with their inputs and outputs in the provenance graph.
The :ref:`section on process functions<working_process_functions>` subsequently detailed the rules that apply when implementing them, all of which to calculation functions, which are a sub type, just like work functions.
However, there are some differences given that calculation functions are 'calculation'-like processes and work function behave like 'workflow'-like processes.
What this entails in terms of intended usage and limitations for calculation functions is the scope of this section.

Creating data
-------------
It has been said many times before: calculation functions, like all 'calculation'-like processes, `create` data, but what does `create` mean exactly?
In this context, the term 'create' is not intended to refer to the simple creation of a new data node in the graph, in an interactive shell or a script for example.
But rather it indicates the creation of a new piece of data from some other data through a computation implemented by a process.
This is then exactly what the calculation function does.
It takes one or more data nodes as inputs and returns one or more data nodes as outputs, whose content is based on those inputs.
As explained in the :ref:`technical section<working_process_functions>`, outputs are created simply by returning the nodes from the function.
The engine will inspect the return value from the function and attach the output nodes to the calculation node that represents the calculation function.
To verify that the output nodes are in fact 'created', the engine will check that the nodes are not stored.
Therefore, it is very important that you **do not store the nodes you create yourself**, or the engine will raise an exception, as shown in the following example:

.. include:: include/snippets/calculations/calcfunctions/add_calcfunction_store.py
    :code: python

Because the returned node is already stored, the engine will raise the following exception:

.. code:: bash

    ValueError: trying to return an already stored Data node from a @calcfunction, however, @calcfunctions cannot return data.
    If you stored the node yourself, simply do not call `store()` yourself.
    If you want to return an input node, use a @workfunction instead.

The reason for this strictness is that a node that was stored after being created in the function body, is indistinguishable from a node that was already stored and had simply been loaded in the function body and returned, e.g.:

.. include:: include/snippets/calculations/calcfunctions/add_calcfunction_load_node.py
    :code: python

The loaded node would also have gotten a `create` link from the calculation function, even though it was not really created by it at all.
It is exactly to prevent this ambiguity that calculation functions require all returned output nodes to be *unstored*.

Note that work functions have exactly the opposite required and all the outputs that it returns **have to be stored**, because as a 'workflow'-like process, it *cannot* create new data.
For more details refer to the :ref:`work function section<working_workfunctions>`.

.. _working_calcjobs:

Calculation jobs
================

`Issue [#2628] <https://github.com/aiidateam/aiida_core/issues/2628>`_

.. Defining a CalcJob
.. ------------------
.. To implement a calc job, one simply sub classes the :py:class:`~aiida.engine.processes.calcjobs.calcjob.CalcJob` process class and implements the :py:meth:`~aiida.engine.processes.calcjobs.calcjob.CalcJob.define` method.
.. You can pick any name that is a valid python class name.
.. The most important method of the ``CalcJob`` class, is the ``define`` class method.
.. Here you define, what inputs it takes and what outputs it will generate.

.. .. include:: include/snippets/calculations/calcjobs/arithmetic_add_spec_inputs.py
..     :code: python

.. As the snippet above demonstrates, the class method takes two arguments:

..  * ``cls`` this is the reference of the class itself and is mandatory for any class method
..  * ``spec`` which is the 'specification'

.. .. warning::
..     Do not forget to add the line ``super(AddAndMultiplyWorkChain, self).define(spec)`` as the first line of the ``define`` method, where you replace the class name with the name of your calculation job.
..     This will call the ``define`` method of the parent class, which is necessary for the work chain to work properly

.. As the name suggests, the ``spec`` can be used to specify the properties of the calculation job.
.. For example, it can be used to define inputs that the calculation job takes.
.. In our example, we need to be able to pass two integers as input, so we define those in the spec by calling ``spec.input()``.
.. The first argument is the name of the input.
.. This name should be used later to specify the inputs when launching the calculation job and it will also be used as the label for link to connect the data node and the calculation node in the provenance graph.
.. Additionally, as we have done here, you can specify which types are valid for that particular input.
.. Since we expect integers, we specify that the valid type is the database storable :py:class:`~aiida.orm.nodes.data.int.Int` class.
.. Next we should define what outputs we expect the calculation to produce:

.. .. include:: include/snippets/calculations/calcjobs/arithmetic_add_spec_outputs.py
..     :code: python

.. Just as for the inputs, one can specify what node type each output should have.
.. By default a defined output will be 'required', which means that if the calculation job terminates and the output has not been attached, the process will be marked as failed.
.. To indicate that an output is optional, one can use ``required=False`` in the ``spec.output`` call.
.. The only thing that remains to be done is to implement the :py:meth:`~aiida.engine.processes.calcjobs.calcjob.CalcJob.prepare_for_submission` method.
.. When a calculation job is launched, the engine will call this method to prepare the input files that will be read by the code when it will eventually be called.

.. .. include:: include/snippets/calculations/calcjobs/arithmetic_add_spec_prepare_for_submission.py
..     :code: python

.. The snippet above shows a minimal implementation of the :py:meth:`~aiida.engine.processes.calcjobs.calcjob.CalcJob.prepare_for_submission` method.
.. As an argument it receives a ``folder`` which is an instance of the :py:class:`~aiida.common.folders.Folder` class.
.. This is a sandbox folder on the local filesystem to which you can write the input files, based on the inputs that have been passed to the calculation job.
.. Those inputs can be accessed through the ``self.inputs`` attribute, which return an attribute dictionary with the validated inputs.
.. This means that you do not have to validate the inputs yourself.
.. If an input is marked as required by the specification, which is the default, then at the point that the ``prepare_for_submission`` method is called by the engine, you are guaranteed that it exists and has the correct type.

.. From the two inputs ``x`` and ``y`` we should now generate the input file, that is simply a text file with these two numbers on a single line, separated by a space.
.. We accomplish this by opening a filehandle to the input file in the sandbox folder and write the values of the two ``Int`` nodes to the file.
.. With the input file written, we now have to create an instance of :py:class:`~aiida.common.datastructures.CalcInfo` that should be returned from the method.
.. This data structure will instruct the engine exactly what needs to be done to execute the code, such as what files should be copied to the remote computer where the code will be executed.


.. Running a CalcJob
.. -----------------

.. Launching a calculation job is no different from launching any other process class, so please refer to the section on :ref:`launching processes<concepts_process_launch>`.
.. The only caveat that we should place is that calculation jobs tend to take quite a bit of time.
.. The trivial example we used above of course will run very fast, but a typical calculation job that will be submitted to a scheduler will most likely take longer than just a few seconds.
.. For that reason it is highly advisable to **submit** calculation jobs instead of running them.
.. By submitting them to the daemon, you free up your interpreter straight away and the process will be checkpointed between the various :ref:`transport tasks<concepts_calcjobs_transport_tasks>` that will have to be performed.
.. The exception is of course when you want to run a calculation job locally for testing or demonstration purposes.

.. Process builder submit test
.. ---------------------------
.. The ``ProcessBuilder`` of a ``CalcJob`` works exactly as any other :ref:`process builder<concepts_process_builder>`, except that it has one additional feature.
.. It has the method :py:meth:`~aiida.engine.processes.builder.CalcJobBuilder.submit_test()`.
.. When this method is called, provided that the inputs are valid, a directory will be created locally with all the inputs files and scripts that would be created if the builder were to be submitted for real.
.. This gives you a chance to inspect the generated files before actually sending them to the remote computer.
.. This action also will not create an actual calculation node in the database, nor do the input nodes have to be stored, allowing you to check that everything is correct without polluting the database.

.. By default the method will create a folder ``submit_test`` in the current working directory and within it a directory with an automatically generated unique name, each time the method is called.
.. The method takes two optional arguments ``folder`` and ``subfolder_name``, to change the base folder and the name of the test directory, respectively.

.. _working_calcjobs_parsers:
