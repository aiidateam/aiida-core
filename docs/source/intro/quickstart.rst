.. _intro:quickstart:

**********
Quickstart
**********

To quickly install AiiDA and run a short demo, follow the three steps below.

.. grid:: 1
    :gutter: 3

    .. grid-item-card:: 1. Use Pip to install the AiiDA locally.

        Type the following in a terminal window:

        .. code-block:: bash

            pip install aiida-core

    .. grid-item-card:: 2. Create a new profile to store your data.

        Type the following in a terminal window:

        TBD: create a sqlite + null RMQ profile for the demo purposes only.

        .. code-block:: bash

            verdi profile setup core.sqlite_dos -n --profile quickstart --email quickstart@example.com
            # open the profile and change process runner to null
            # set runner interval to 1 second
            # consider to have a verdi quickstart for such purposes?

    .. grid-item-card:: 3. Run a workflow

        AiiDA has two types of workflows: :ref:`work function<topics:workflows:concepts:workfunctions>` and :ref:`work chain <topics:workflows:concepts:workchains>`.

        In quick-start, we show both examples of workflows.
        See `when to use which<topics:workflows:concepts:workfunctions_vs_workchains>` for more information.

        You can either open a Python interpreter or a Jupyter notebook and run the following code, or save it in a file and run it with ``verdi run``:

        .. tab-set::

            .. tab-item:: Work function

                The work functions are ideal for workflows that are not very computationally intensive and can be easily implemented in a Python function.

                .. code-block:: python

                    from aiida import engine

                    # Construct manageable tasks out of functions
                    # by adding the @engine.calcfunction decorator
                    @engine.calcfunction
                    def add(x, y):
                        return x + y

                    @engine.calcfunction
                    def multiply(x, y):
                        return x*y

                    # Construct the workflow by stitching together
                    # the calcfunction with the @engine.workfunction decorator
                    @engine.workfunction
                    def workflow(x, y, z):
                        r1 = add(x, y)
                        r2 = multiply(r1, z)

                        return r2

                    # Dispatch the workflow
                    result = engine.run(workflow, x=2, y=3, z=5)

                    # The result `25` is stored in the `value` attribute
                    print(result)
                    print(result.value)

            .. tab-item:: Work chain

                The work chain allows to save the progress between those steps as soon as they are successfully completed. The work chain is therefore the preferred solution for parts of the workflow that involve more expensive and complex calculations.

                XXX: it requires the code to be installed in the profile, and the computer to be configured.
                XXX: consider to have a ``verdi quickstart`` and add commands below for such purposes?

                .. code-block:: bash

                    verdi computer setup -L tutor -H localhost -T core.local -S core.direct -w `echo $PWD/work` -n
                    verdi computer configure core.local tutor --safe-interval 1 -n
                    verdi code create core.code.installed --label add --computer=tutor --default-calc-job-plugin core.arithmetic.add --filepath-executable=/bin/bash -n

                The work chain example uses the pre-defined ``MultiplyAddWorkChain`` from the AiiDA.

                :::{dropdown} MultiplyAddWorkChain code

                ```{literalinclude} ../../../src/aiida/workflows/arithmetic/multiply_add.py
                :language: python
                :start-after: start-marker
                ```

                .. code-block:: python

                    from aiida import plugins, engine, orm

                    MultiplyAddWorkChain = plugins.WorkflowFactory('core.arithmetic.multiply_add')

                    builder = MultiplyAddWorkChain.get_builder()
                    builder.code = orm.load_code(label='add')
                    builder.x = orm.Int(2)
                    builder.y = orm.Int(3)
                    builder.z = orm.Int(5)

                    output = engine.run(builder)
                    print(output['result'])

    .. grid-item-card:: 4. View the workflow and the provenance graph

        AiiDA command line interface ``verdi`` has commands that allows to view the progress of the workflow and the provenance graph of the workflow.

        To view the progress of the workflow, type the following in a terminal window:

        .. code-block:: bash

            verdi process list
            verdi process show <workflow_id>

        To view the provenance graph of the workflow, generate the graph and open it.
        (Make sure you have the ``graphviz`` package installed on your system, check the `graphviz installation instructions <https://graphviz.org/download/>`_ for more information.)

        .. code-block:: bash

            verdi node graph generate <workflow_id>

        You'll get a PDF file with the workflow graph, and you can use your favorite PDF viewer to open the graph.

        It looks like this:

        .. tab-set::

            .. tab-item:: Work function

                .. image:: ./include/quickstart_workfunction.png
                    :width: 100%

            .. tab-item:: Work chain

                .. image:: ./include/quickstart_workchain.png
                    :width: 100%

Querying the database
---------------------

AiiDA has a powerful query engine that allows to query the database in a very flexible way.

XXX: examples of querying the demo database.

.. warning:: The demo uses a sqlite database and without process controller that can not levegare the full power of AiiDA.
    Please, refer to the :ref:`installation guide <intro:get_started>` (XXX jy, the get start is actually installation guide, after the getstarted sadly user still can not really "start".) for the production installation.

Next?
-----
Again the links of index page are useful to guide the user to using AiiDA for their real research/work.

XXX: read xx for more examples.
XXX: read xx for the deep discussion.
