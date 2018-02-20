.. _processes:

*********
Processes
*********

Anything that runs in AiiDA is an instance of :py:class:`~aiida.work.processes.Process`.

ISSUE#1131



.. _process_builder:

The Process Builder
===================
The process builder is essentially a tool that helps you build the object that you want to run.
To get a *builder* for a ``Calculation`` or a ``Workflow`` all you need is the ``Calculation`` or ``Workflow`` class itself, which can be loaded through the ``CalculationFactory`` and ``WorkflowFactory``, respectively.
Let's take the :py:class:`~aiida.orm.calculation.job.simpleplugins.templatereplacer.TemplatereplacerCalculation` as an example::

    TemplatereplacerCalculation = CalculationFactory('simpleplugins.templatereplacer')
    builder = TemplatereplacerCalculation.get_builder()

The string ``simpleplugins.templatereplacer`` is the entry point of the ``TemplatereplacerCalculation`` and passing it to the ``CalculationFactory`` will return the corresponding class.
Calling the ``get_builder`` method on that class will return an instance of the ``ProcessBuilder`` that is tailored for the ``TemplatereplacerCalculation``.
The builder will help you in defining the inputs that the ``TemplatereplacerCalculation`` requires and has a few handy tools to simplify this process.

Defining inputs
---------------
For starters, if you are in an interactive shell and you simply evaluate the ``builder`` it will show you the inputs that it can take::

    builder
    {
        'code': None,
        'description': None,
        'parameters': None,
        'label': None,
        'options': None,
        'template': None,
        'store_provenance': True [default]
    }

Each key in the dictionary is an input of the ``TemplatereplacerCalculation`` class and the value is the current value that is set.
If the calculation class defined a default value for an input (e.g. the ``store_provenance`` input in this example), it will be filled in and marked with ``[default]``.
Another way to reveal the available inputs is through tab completion.
In an interactive python shell, simply typing ``builder.`` and hitting the tab key, will show an autocomplete list of all available inputs.

There is one specific key that will always be there and is in fact not an input: ``launch``.
This is the method that will be used to actually launch the ``Process`` through the ``ProcessBuilder`` and will be discussed in more detail in :ref:`another section<launching_process_builder>`).

Each input of the builder can also show additional information about what sort of input it expects.
In an interactive shell, you can get this information to display as follows::

    builder.parameters?
    Type:        ProcessBuilderInput
    String form: None
    File:        ~/code/aiida/env/workflows/aiida-core/aiida/work/process_builder.py
    Docstring:
        "help": "Parameters used to replace placeholders in the template",
        "name": "parameters",
        "valid_type": "<class 'aiida.orm.data.parameter.ParameterData'>"

In the ``Docstring`` you will see a ``help`` string that contains more detailed information about the input port.
Additionally, it will display a ``valid_type``, which when defined shows which data types are expected.
If a default value has been defined, that will also be displayed.

Setting an input to the builder is as simply as simply assigning it to the attribute.
The following example shows how to set the ``description`` and ``label`` inputs::

    builder.label = 'This is my calculation label'
    builder.description = 'An example calculation to demonstrate the process builder'

If you evaluate the ``builder`` instance once more, it will now display the updated status of the builder::

    builder
    {
        'code': None,
        'description': 'An example calculation to demonstrate the process builder',
        'parameters': None,
        'label': 'This is my calculation label',
        'options': None,
        'template': None,
        'store_provenance': True [default]
    }

All that remains is to fill in all the required inputs and we are ready to launch the ``Calculation`` or ``Workflow``.

.. _launching_process_builder:

Launching the process
---------------------
When all the inputs have been defined for the builder, it can be used to actually launch the ``Process``.
As discussed before, the builder instance has the ``launch`` method, which can be used for this very purpose::

    builder.launch()

This will create the ``Calculation`` or ``Workflow`` instance for which the builder was created, with the inputs that were defined in the builder, and subsequently submitted to the daemon which will take care of running it to completion.
The ``launch`` method takes an optional argument ``daemon``, which is set to ``True`` by default.
If instead of having the process being submitted to the daemon, you want to run the process in the current interpreter, simply set this optional argument to ``False``::

    builder.launch(daemon=False)

Note that this will run the process in a blocking way and therefore the interpreter will be blocked until the entire process is finished.
For processes that take a long time, such as complex workflows, this might not be the best choice.


Test submission
---------------
For ``Calculation`` classes, the ``get_builder`` class method actually returns a slightly modified process builder, namely the ``JobProcessBuilder``.
This is a subclass of the ``ProcessBuilder`` and provides the ``launch`` method with an additional feature.
If you have built your process builder with all the necessary inputs and want to *test* what the result would be before actually storing the calculation in the database and submitting it to the scheduler, you can pass the optional argument ``test=True`` to the ``launch`` method::

    builder.launch(test=True)

This will create a temporary folder in the current folder with the calculation folder as it would be created on the computer when it were to be actually launched by the builder.
This gives you the opportunity to verify that the generated input files based on the current state of the builder would be correct.
If you made a mistake, you can simply update the inputs of the builder and try again, without creating incorrect calculation nodes in the database and repository.