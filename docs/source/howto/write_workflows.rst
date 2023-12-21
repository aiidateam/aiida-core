.. _how-to:write-workflows:

*********************************
How to write and extend workflows
*********************************

Writing workflows
=================

A workflow in AiiDA is a :ref:`process <topics:processes:concepts>` that calls other workflows and calculations and optionally *returns* data and as such can encode the logic of a typical scientific workflow.
Currently, there are two ways of implementing a workflow process:

* :ref:`work functions<topics:workflows:concepts:workfunctions>`
* :ref:`work chains<topics:workflows:concepts:workchains>`

Here we present a brief introduction on how to write both workflow types.

.. note::

    For more details on the concept of a workflow, and the difference between a work function and a work chain, please see the corresponding :ref:`topics section<topics:workflows:concepts>`.

.. note::

   Developing workflows may involve running several lengthy calculations. Consider :ref:`enabling caching <how-to:run-codes:caching>` to help avoid repeating long workflow steps.

Work function
-------------

A *work function* is a process function that calls one or more calculation functions and *returns* data that has been *created* by the calculation functions it has called.
Moreover, work functions can also call other work functions, allowing you to write nested workflows.
Writing a work function, whose provenance is automatically stored, is as simple as writing a Python function and decorating it with the :class:`~aiida.engine.processes.functions.workfunction` decorator:

.. literalinclude:: ../../../src/aiida/workflows/arithmetic/add_multiply.py
    :language: python
    :start-after: start-marker

It is important to reiterate here that the :class:`~aiida.engine.processes.functions.workfunction`-decorated ``add_multiply()`` function does not *create* any new data nodes.
The ``add()`` and ``multiply()`` calculation functions create the ``Int`` data nodes, all the work function does is *return* the results of the ``multiply()`` calculation function.
Moreover, both calculation and workflow functions can only accept and return data nodes, i.e. instances of classes that subclass the :class:`~aiida.orm.nodes.data.data.Data` class.

Work chain
----------

When the workflow you want to run is more complex and takes longer to finish, it is better to write a *work chain*.
Writing a work chain in AiiDA requires creating a class that inherits from the :class:`~aiida.engine.processes.workchains.workchain.WorkChain` class.
Below is an example of a work chain that takes three integers as inputs, multiplies the first two and then adds the third to obtain the final result:

.. literalinclude:: ../../../src/aiida/workflows/arithmetic/multiply_add.py
    :language: python
    :start-after: start-marker

You can give the work chain any valid Python class name, but the convention is to have it end in :class:`~aiida.engine.processes.workchains.workchain.WorkChain` so that it is always immediately clear what it references.
Let's go over the methods of the ``MultiplyAddWorkChain`` one by one:

.. literalinclude:: ../../../src/aiida/workflows/arithmetic/multiply_add.py
    :language: python
    :pyobject: MultiplyAddWorkChain.define
    :dedent: 4

The most important method to implement for every work chain is the ``define()`` method.
This class method must always start by calling the ``define()`` method of its parent class.
Next, the ``define()`` method should be used to define the specifications of the work chain, which are contained in the work chain ``spec``:

* the **inputs**, specified using the ``spec.input()`` method.
  The first argument of the ``input()`` method is a string that specifies the label of the input, e.g. ``'x'``.
  The ``valid_type`` keyword argument allows you to specify the required node type of the input.
  Other keyword arguments allow the developer to set a default for the input, or indicate that an input should not be stored in the database, see :ref:`the process topics section <topics:processes:usage:spec>` for more details.
* the **outline** or logic of the workflow, specified using the ``spec.outline()`` method.
  The outline of the workflow is constructed from the methods of the :class:`~aiida.engine.processes.workchains.workchain.WorkChain` class.
  For the ``MultiplyAddWorkChain``, the outline is a simple linear sequence of steps, but it's possible to include actual logic, directly in the outline, in order to define more complex workflows as well.
  See the :ref:`work chain outline section <topics:workflows:usage:workchains:define_outline>` for more details.
* the **outputs**, specified using the ``spec.output()`` method.
  This method is very similar in its usage to the ``input()`` method.
* the **exit codes** of the work chain, specified using the ``spec.exit_code()`` method.
  Exit codes are used to clearly communicate known failure modes of the work chain to the user.
  The first and second arguments define the ``exit_status`` of the work chain in case of failure (``400``) and the string that the developer can use to reference the exit code (``ERROR_NEGATIVE_NUMBER``).
  A descriptive exit message can be provided using the ``message`` keyword argument.
  For the ``MultiplyAddWorkChain``, we demand that the final result is not a negative number, which is checked in the ``validate_result`` step of the outline.

.. note::

    For more information on the ``define()`` method and the process spec, see the :ref:`corresponding section in the topics <topics:processes:usage:defining>`.

The ``multiply`` method is the first step in the outline of the ``MultiplyAddWorkChain`` work chain.


.. literalinclude:: ../../../src/aiida/workflows/arithmetic/multiply_add.py
    :language: python
    :pyobject: MultiplyAddWorkChain.multiply
    :dedent: 4

This step simply involves running the calculation function ``multiply()``, on the ``x`` and ``y`` **inputs** of the work chain.
To store the result of this function and use it in the next step of the outline, it is added to the *context* of the work chain using ``self.ctx``.


.. literalinclude:: ../../../src/aiida/workflows/arithmetic/multiply_add.py
    :language: python
    :pyobject: MultiplyAddWorkChain.add
    :dedent: 4

The ``add()`` method is the second step in the outline of the work chain.
As this step uses the ``ArithmeticAddCalculation`` calculation job, we start by setting up the inputs for this :class:`~aiida.engine.processes.calcjobs.calcjob.CalcJob` in a dictionary.
Next, when submitting this calculation job to the daemon, it is important to use the submit method from the work chain instance via ``self.submit()``.
Since the result of the addition is only available once the calculation job is finished, the ``submit()`` method returns the :class:`~aiida.orm.nodes.process.calculation.calcjob.CalcJobNode` of the *future* ``ArithmeticAddCalculation`` process.
To tell the work chain to wait for this process to finish before continuing the workflow, we return the ``ToContext`` class, where we have passed a dictionary to specify that the future calculation job node should be assigned to the ``'addition'`` context key.

.. warning::

    Never use the global ``submit()`` function to submit calculations to the daemon within a :class:`~aiida.engine.processes.workchains.workchain.WorkChain`.
    Doing so will raise an exception during runtime.
    See the :ref:`topics section on work chains<topics:workflows:usage:workchains:submitting_sub_processes>` for more details.

.. note::
    Instead of passing a dictionary, you can also initialize a ``ToContext`` instance by passing the future process as a keyword argument, e.g. ``ToContext(addition=calcjob_node)``.
    More information on the ``ToContext`` class can be found in :ref:`the topics section on submitting sub processes<topics:workflows:usage:workchains:submitting_sub_processes>`.


.. literalinclude:: ../../../src/aiida/workflows/arithmetic/multiply_add.py
    :language: python
    :pyobject: MultiplyAddWorkChain.validate_result
    :dedent: 4

Once the ``ArithmeticAddCalculation`` calculation job is finished, the next step in the work chain is to validate the result, i.e. verify that the result is not a negative number.
After the ``addition`` node has been extracted from the context, we take the ``sum`` node from the ``ArithmeticAddCalculation`` outputs and store it in the ``result`` variable.
In case the value of this ``Int`` node is negative, the ``ERROR_NEGATIVE_NUMBER`` exit code - defined in the ``define()`` method - is returned.
Note that once an exit code is returned during any step in the outline, the work chain will be terminated and no further steps will be executed.


.. literalinclude:: ../../../src/aiida/workflows/arithmetic/multiply_add.py
    :language: python
    :pyobject: MultiplyAddWorkChain.result
    :dedent: 4

The final step in the outline is to pass the result to the outputs of the work chain using the ``self.out()`` method.
The first argument (``'result'``) specifies the label of the output, which corresponds to the label provided to the spec in the ``define()`` method.
The second argument is the result of the work chain, extracted from the ``Int`` node stored in the context under the ``'addition'`` key.

For a more complete discussion on workflows and their usage, please read :ref:`the corresponding topics section<topics:workflows:usage>`.

.. _how-to:write-workflows:extend:

Extending workflows
===================

When designing workflows, there are many cases where you want to reuse an existing process.
This section explains how to extend workflows by wrapping them around other processes or linking them together.

As an example, let's say you want to extend the ``MultiplyAddWorkChain`` by adding another step of analysis that checks whether the result is an even number or not.
This final step can be written as a simple ``calcfunction``:

.. literalinclude:: include/snippets/extend_workflows.py
    :language: python
    :pyobject: is_even

We could simply write a new workflow based off ``MultiplyAddWorkChain`` that includes an extra step in the outline which runs the ``is_even`` calculation function.
However, this would lead to a lot of code duplication, and longer workflows consisting of multiple work chains would become very cumbersome to deal with (see the dropdown panel below).

.. dropdown:: ``BadMultiplyAddIsEvenWorkChain``

    .. literalinclude:: include/snippets/extend_workflows.py
        :language: python
        :pyobject: BadMultiplyAddIsEvenWorkChain

    .. note::

        We've removed the ``result`` step from the outline, as well as the ``result`` output.
        For this work chain, we're assuming that for now we are only interested in whether or not the result is even.

We can avoid some code duplication by simply submitting the ``MultiplyAddWorkChain`` within one of the steps of a new work chain which would then call ``is_even`` in a second step:

.. literalinclude:: include/snippets/extend_workflows.py
    :language: python
    :pyobject: BetterMultiplyAddIsEvenWorkChain

This already simplifies the extended work chain, and avoids duplicating the steps of the ``MultiplyAddWorkChain`` in the outline.
However, we still had to copy all of the input definitions of the ``MultiplyAddWorkChain``, and manually extract them from the inputs before passing them to the ``self.submit`` method.
Fortunately, there is a better way of *exposing* the inputs and outputs of subprocesses of the work chain.

Exposing inputs and outputs
---------------------------

In many cases it is convenient for work chains to expose the inputs of the subprocesses it wraps so users can specify these inputs directly, as well as exposing some of the outputs produced as one of the results of the parent work chain.
For the simple example presented in the previous section, simply copy-pasting the input and output port definitions of the subprocess ``MultiplyAddWorkChain`` was not too troublesome.
However, this quickly becomes tedious and error-prone once you start to wrap processes with quite a few more inputs.

To prevent the copy-pasting of input and output specifications, the :class:`~aiida.engine.processes.process_spec.ProcessSpec` class provides the :meth:`~plumpy.ProcessSpec.expose_inputs` and :meth:`~plumpy.ProcessSpec.expose_outputs` methods.
Calling :meth:`~plumpy.ProcessSpec.expose_inputs` for a particular ``Process`` class, will automatically copy the inputs of the class into the inputs namespace of the process specification:

.. code-block:: python

    @classmethod
    def define(cls, spec):
        """Specify inputs and outputs."""
        super().define(spec)
        spec.expose_inputs(MultiplyAddWorkChain)  # Expose the inputs instead of copying their definition
        spec.outline(
            cls.multiply_add,
            cls.is_even,
        )
        spec.output('is_even', valid_type=Bool)

.. note::

    The exposing functionality is not just limited to ``WorkChain`` implementations but works for all process classes, such as ``CalcJob`` plugins for example.
    It even works for process functions (i.e., ``calcfunctions`` and ``workfunctions``) since under the hood an actual ``Process`` class is generated for them on-the-fly.
    For process functions, the ``valid_type`` and ``help`` attributes of the exposed inputs are even preserved if they could be inferred from provided function type hints and docstrings (see :ref:`type validation<topics:processes:functions:type-validation>` and :ref:`docstring parsing<topics:processes:functions:docstring-parsing>` for details).

Be aware that any inputs that already exist in the namespace will be overridden.
To prevent this, the method accepts the ``namespace`` argument, which will cause the inputs to be copied into that namespace instead of the top-level namespace.
This is especially useful for exposing inputs since *all* processes have the ``metadata`` input.
If you expose the inputs without a namespace, the ``metadata`` input port of the exposed class will override the one of the host, which is often not desirable.
Let's copy the inputs of the ``MultiplyAddWorkChain`` into the ``multiply_add`` namespace:

.. literalinclude:: include/snippets/extend_workflows.py
    :language: python
    :pyobject: MultiplyAddIsEvenWorkChain.define
    :dedent: 4

That takes care of exposing the port specification of the wrapped process class in a very efficient way.
To easily retrieve the inputs that have been passed to the process, one can use the :meth:`~aiida.engine.processes.process.Process.exposed_inputs` method.
Note the past tense of the method name.
The method takes a process class and an optional namespace as arguments, and will return the inputs that have been passed into that namespace when it was launched.
This utility now allows us to simplify the ``multiply_add`` step in the outline:

.. literalinclude:: include/snippets/extend_workflows.py
    :language: python
    :pyobject: MultiplyAddIsEvenWorkChain.multiply_add
    :dedent: 4

This way we don't have to manually fish out all the individual inputs from the ``self.inputs`` but have to just call this single method, saving time and lines of code.
The final ``MultiplyAddIsEvenWorkChain`` can be found in the dropdown panel below.

.. dropdown:: ``MultiplyAddIsEvenWorkChain``

    .. literalinclude:: include/snippets/extend_workflows.py
        :language: python
        :pyobject: MultiplyAddIsEvenWorkChain

When submitting or running the work chain using namespaced inputs (``multiply_add`` in the example above), it is important to use the namespace when providing the inputs:

.. code-block:: python

    add_code = load_code(label='add')
    inputs = {
        'multiply_add': {'x': Int(1), 'y': Int(2), 'z': Int(3), 'code': add_code}
    }

    workchain_node = submit(MultiplyAddWorkChain, **inputs)

After running the ``MultiplyAddIsEvenWorkChain``, you can see a hierarchical overview of the processes called by the work chain using the ``verdi process status`` command:

.. code-block:: console

    $ verdi process status 164
    MultiplyAddIsEvenWorkChain<164> Finished [0] [1:is_even]
        ├── MultiplyAddWorkChain<165> Finished [0] [3:result]
        │   ├── multiply<166> Finished [0]
        │   └── ArithmeticAddCalculation<168> Finished [0]
        └── is_even<172> Finished [0]

Note that this command also recursively shows the processes called by the subprocesses of the ``MultiplyAddIsEvenWorkChain`` work chain.

As mentioned earlier, you can also expose the outputs of the ``MultiplyAddWorkChain`` using the :meth:`~plumpy.ProcessSpec.expose_outputs` method.
Say we want to add the ``result`` of the ``MultiplyAddWorkChain`` as one of the outputs of the extended work chain:

.. code-block:: python

    @classmethod
    def define(cls, spec):
        """Specify inputs and outputs."""
        super().define(spec)
        spec.expose_inputs(MultiplyAddWorkChain, namespace='multiply_add')
        spec.outline(
            cls.multiply_add,
            cls.is_even,
        )
        spec.expose_outputs(MultiplyAddWorkChain)
        spec.output('is_even', valid_type=Bool)

Since there is not one output port that is shared by all process classes, it is less critical to use the ``namespace`` argument when exposing outputs.
However, take care not to override the outputs of the parent work chain in case they do have outputs with the same port name.
We still need to pass the ``result`` of the ``MultiplyAddWorkChain`` to the outputs of the parent work chain.
For example, we could do this in the ``is_even`` step by using the :meth:`~aiida.engine.processes.process.Process.out` method:

.. code-block:: python

    def is_even(self):
        """Check if the result is even."""
        result = self.ctx.multi_addition.outputs.result
        result_is_even = is_even(result)

        self.out('result', result)
        self.out('is_even', result_is_even)

This works fine if we want to pass a single output to the parent work chain, but once again becomes tedious and error-prone when passing multiple outputs.
Instead we can use the :meth:`~aiida.engine.processes.process.Process.exposed_outputs` method in combination with the :meth:`~aiida.engine.processes.process.Process.out_many` method:

.. code-block:: python

    def is_even(self):
        """Check if the result is even."""
        result_is_even = is_even(self.ctx.multi_addition.outputs.result)

        self.out_many(self.exposed_outputs(self.ctx.multi_addition, MultiplyAddWorkChain))
        self.out('is_even', result_is_even)

The :meth:`~aiida.engine.processes.process.Process.exposed_outputs` method returns a dictionary of the exposed outputs of the ``MultiplyAddWorkChain``, extracted from the workchain node stored in the ``multi_addition`` key of the context.
The :meth:`~aiida.engine.processes.process.Process.out_many` method takes this dictionary and assigns its values to the output ports with names equal to the corresponding keys.

.. important::

    Besides avoiding code duplication and errors, using the methods for exposing inputs and outputs also has the advantage that our parent work chain doesn't have to be adjusted in case the inputs or outputs of the child work chain change.
    This makes the code much easier to maintain.
