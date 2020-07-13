.. _tutorial:

.. _tutorial:basic:

.. For reference:

.. * The `tutorial guidelines <https://github.com/aiidateam/aiida-core/wiki/Writing-documentation#tutorial>`_.
.. * See `issue #3981 <https://github.com/aiidateam/aiida-core/issues/3981>`_.

**************
Basic tutorial
**************

Welcome to the AiiDA tutorial!
The goal of this tutorial is to give you a basic idea of how AiiDA helps you in executing data-driven workflows.
At the end of this tutorial you will know how to:

* Store data in the database and subsequently retrieve it.
* Decorate a Python function such that its inputs and outputs are automatically tracked.
* Run and monitor the status of processes.
* Explore and visualize the provenance graph.

.. important::

    If you are working on your own machine, note that the tutorial assumes that you have a working AiiDA installation, and have set up your AiiDA profile in the current Python environment.
    If this is not the case, consult the :ref:`getting started page<intro:get_started>`.

Provenance
==========

Before we dive in, we need to briefly introduce one of the most important concepts for AiiDA: *provenance*.
An AiiDA database does not only contain the results of your calculations, but also their inputs and each step that was executed to obtain them.
All of this information is stored in the form of a *directed acyclic graph* (DAG).
As an example, :numref:`fig_intro_workchain_graph` shows the provenance of the calculations of this tutorial.

.. _fig_intro_workchain_graph:
.. figure:: include/workchain_graph.png
    :scale: 30
    :align: center

    Provenance Graph of a basic AiiDA WorkChain.

In the provenance graph, you can see different types of *nodes* represented by different shapes.
The green ellipses are ``Data`` nodes, the blue ellipse is a ``Code`` node, and the rectangles represent *processes*, i.e. the calculations performed in your *workflow*.

The provenance graph allows us to not only see what data we have, but also how it was produced.
During this tutorial we will be using AiiDA to generate the provenance graph in :numref:`fig_intro_workchain_graph` step by step.

Data nodes
==========

Before running any calculations, let's create and store a *data node*.
AiiDA ships with an interactive IPython shell that has many basic AiiDA classes pre-loaded.
To start the IPython shell, simply type in the terminal:

.. code-block:: console

    $ verdi shell

AiiDA implements data node types for the most common types of data (int, float, str, etc.), which you can extend with your own (composite) data node types if needed.
For this tutorial, we'll keep it very simple, and start by initializing an ``Int`` node and assigning it to the `node` variable:

.. code-block:: ipython

    In [1]: node = Int(2)

We can check the contents of the ``node`` variable like this:

.. code-block:: ipython

    In [2]: node
    Out[2]: <Int: uuid: eac48d2b-ae20-438b-aeab-2d02b69eb6a8 (unstored) value: 2>

Quite a bit of information on our freshly created node is returned:

* The data node is of the type ``Int``
* The node has the *universally unique identifier* (**UUID**) ``eac48d2b-ae20-438b-aeab-2d02b69eb6a8``
* The node is currently not stored in the database ``(unstored)``
* The integer value of the node is ``2``

Let's store the node in the database:

.. code-block:: ipython

    In [3]: node.store()
    Out[3]: <Int: uuid: eac48d2b-ae20-438b-aeab-2d02b69eb6a8 (pk: 1) value: 2>

As you can see, the data node has now been assigned a *primary key* (**PK**), a number that identifies the node in your database ``(pk: 1)``.
The PK and UUID both reference the node with the only difference that the PK is unique *for your local database only*, whereas the UUID is a globally unique identifier and can therefore be used between *different* databases.
Use the PK only if you are working within a single database, i.e. in an interactive session and the UUID in all other cases.

.. important::

    The PK numbers shown throughout this tutorial assume that you start from a completely empty database.
    It is possible that the nodes' PKs will be different for your database!

    The UUIDs are generated randomly and are therefore **guaranteed** to be different.

Next, let's leave the IPython shell by typing ``exit()`` and then enter.
Back in the terminal, use the ``verdi`` command line interface (CLI) to check the data node we have just created:

.. code:: console

    $ verdi node show 1

This prints something like the following:

.. code-block:: bash

    Property     Value
    -----------  ------------------------------------
    type         Int
    pk           1
    uuid         eac48d2b-ae20-438b-aeab-2d02b69eb6a8
    label
    description
    ctime        2020-05-13 08:58:15.193421+00:00
    mtime        2020-05-13 08:58:40.976821+00:00

Once again, we can see that the node is of type ``Int``, has PK = 1, and UUID = ``eac48d2b-ae20-438b-aeab-2d02b69eb6a8``.
Besides this information, the ``verdi node show`` command also shows the (empty) ``label`` and ``description``, as well as the time the node was created (``ctime``) and last modified (``mtime``).

.. note:: AiiDA already provides many standard data types, but you can also :ref:`create your own<how-to:data:plugin>`.

Calculation functions
=====================

Once your data is stored in the database, it is ready to be used for some computational task.
For example, let's say you want to multiply two ``Int`` data nodes.
The following Python function:

.. code-block:: python

    def multiply(x, y):
        return x * y

will give the desired result when applied to two ``Int`` nodes, but the calculation will not be stored in the provenance graph.
However, we can use a `Python decorator <https://docs.python.org/3/glossary.html#term-decorator>`_ provided by AiiDA to automatically make it part of the provenance graph.
Start up the AiiDA IPython shell again using ``verdi shell`` and execute the following code snippet:

.. code-block:: ipython

    In [1]: from aiida.engine import calcfunction
       ...:
       ...: @calcfunction
       ...: def multiply(x, y):
       ...:     return x * y

This converts the ``multiply`` function into an AiIDA *calculation function*, the most basic execution unit in AiiDA.
Next, load the ``Int`` node you have created in the previous section using the ``load_node`` function and the PK of the data node:

.. code-block:: ipython

    In [2]: x = load_node(pk=1)

Of course, we need another integer to multiply with the first one.
Let's create a new ``Int`` data node and assign it to the variable ``y``:

.. code-block:: ipython

    In [3]: y = Int(3)

Now it's time to multiply the two numbers!

.. code-block:: ipython

    In [4]: multiply(x, y)
    Out[4]: <Int: uuid: 42541d38-1fb3-4f60-8122-ab8b3e723c2e (pk: 4) value: 6>

Success!
The ``calcfunction``-decorated ``multiply`` function has multiplied the two ``Int`` data nodes and returned a new ``Int`` data node whose value is the product of the two input nodes.
Note that by executing the ``multiply`` function, all input and output nodes are automatically stored in the database:

.. code-block:: ipython

    In [5]: y
    Out[5]: <Int: uuid: 7865c8ff-f243-4443-9233-dd303a9be3c5 (pk: 2) value: 3>

We had not yet stored the data node assigned to the ``y`` variable, but by providing it as an input argument to the ``multiply`` function, it was automatically stored with PK = 2.
Similarly, the returned ``Int`` node with value 6 has been stored with PK = 4.

Let's once again leave the IPython shell with ``exit()`` and look for the process we have just run using the ``verdi`` CLI:

.. code:: console

    $ verdi process list

The returned list will be empty, but don't worry!
By default, ``verdi process list`` only returns the *active* processes.
If you want to see *all* processes (i.e. also the processes that are *terminated*), simply add the ``-a`` option:

.. code:: console

    $ verdi process list -a

You should now see something like the following output:

.. code-block:: bash

      PK  Created    Process label    Process State    Process status
    ----  ---------  ---------------  ---------------  ----------------
       3  1m ago     multiply         ⏹ Finished [0]

    Total results: 1

    Info: last time an entry changed state: 1m ago (at 09:01:05 on 2020-05-13)

We can see that our ``multiply`` calcfunction was created 1 minute ago, assigned the PK 3, and has ``Finished``.

As a final step, let's have a look at the provenance of this simple calculation.
The provenance graph can be automatically generated using the verdi CLI.
Let's generate the provenance graph for the ``multiply`` calculation function we have just run with PK = 3:

.. code-block:: console

  $ verdi node graph generate 3

The command will write the provenance graph to a ``.pdf`` file.
Use your favorite PDF viewer to have a look.
It should look something like the graph shown in :numref:`fig_calcfun_graph`.

.. _fig_calcfun_graph:
.. figure:: include/calcfun_graph.png
    :scale: 50
    :align: center

    Provenance graph of the ``multiply`` calculation function.

.. note:: Remember that the PK of the ``CalcJob`` can be different for your database.

.. _tutorial:basic:calcjob:

CalcJobs
========

When running calculations that require an external code or run on a remote machine, a simple calculation function is no longer sufficient.
For this purpose, AiiDA provides the ``CalcJob`` process class.

To run a ``CalcJob``, you need to set up two things: a ``code`` that is going to implement the desired calculation and a ``computer`` for the calculation to run on.

If you're running this tutorial in the Quantum Mobile VM or on Binder, these have been pre-configured for you. If you're running on your own machine, you can follow the instructions in the panel below.

.. seealso::

   More details for how to :ref:`run external codes <how-to:run-codes>`.

.. dropdown:: Install localhost computer and code

    Let's begin by setting up the computer using the ``verdi computer`` subcommand:

    .. code-block:: console

        $ verdi computer setup -L tutor -H localhost -T local -S direct -w `echo $PWD/work` -n
        $ verdi computer configure local tutor --safe-interval 5 -n

    The first commands sets up the computer with the following options:

    * *label* (``-L``): tutor
    * *hostname* (``-H``): localhost
    * *transport* (``-T``): local
    * *scheduler* (``-S``): direct
    * *work-dir* (``-w``): The ``work`` subdirectory of the current directory

    The second command *configures* the computer with a minimum interval between connections (``--safe-interval``) of 5 seconds.
    For both commands, the *non-interactive* option (``-n``) is added to not prompt for extra input.

    Next, let's set up the code we're going to use for the tutorial:

    .. code-block:: console

        $ verdi code setup -L add --on-computer --computer=tutor -P arithmetic.add --remote-abs-path=/bin/bash -n

    This command sets up a code with *label* ``add`` on the *computer* ``tutor``, using the *plugin* ``arithmetic.add``.

A typical real-world example of a computer is a remote supercomputing facility.
Codes can be anything from a Python script to powerful *ab initio* codes such as Quantum Espresso or machine learning tools like Tensorflow.
Let's have a look at the codes that are available to us:

.. code:: console

    $ verdi code list
    # List of configured codes:
    # (use 'verdi code show CODEID' to see the details)
    * pk 5 - add@tutor

You can see a single code ``add@tutor``, with PK = 5, in the printed list.
This code allows us to add two integers together.
The ``add@tutor`` identifier indicates that the code with label ``add`` is run on the computer with label ``tutor``.
To see more details about the computer, you can use the following ``verdi`` command:

.. code:: console

    $ verdi computer show tutor
    Computer name:     tutor
     * PK:             1
     * UUID:           b9ecb07c-d084-41d7-b862-a2b1f02722c5
     * Description:
     * Hostname:       localhost
     * Transport type: local
     * Scheduler type: direct
     * Work directory: /Users/mbercx/epfl/tutorials/my_tutor/work
     * Shebang:        #!/bin/bash
     * mpirun command: mpirun -np {tot_num_mpiprocs}
     * prepend text:
     # No prepend text.
     * append text:
     # No append text.

We can see that the *Work directory* has been set up as the ``work`` subdirectory of the current directory.
This is the directory in which the calculations running on the ``tutor`` computer will be executed.

.. note::

    You may have noticed that the PK of the ``tutor`` computer is 1, same as the ``Int`` node we created at the start of this tutorial.
    This is because different entities, such as nodes, computers and groups, are stored in different tables of the database.
    So, the PKs for each entity type are unique for each database, but entities of different types can have the same PK within one database.

Let's now start up the ``verdi shell`` again and load the ``add@tutor`` code using its label:

.. code-block:: ipython

    In [1]: code = load_code(label='add')

Every code has a convenient tool for setting up the required input, called the *builder*.
It can be obtained by using the ``get_builder`` method:

.. code-block:: ipython

    In [2]: builder = code.get_builder()

Using the builder, you can easily set up the calculation by directly providing the input arguments.
Let's use the ``Int`` node that was created by our previous ``calcfunction`` as one of the inputs and a new node as the second input:

.. code-block:: ipython

    In [3]: builder.x = load_node(pk=4)
       ...: builder.y = Int(5)

In case that your nodes' PKs are different and you don't remember the PK of the output node from the previous calculation, check the provenance graph you generated earlier and use the UUID of the output node instead:

.. code-block:: ipython

    In [3]: builder.x = load_node(uuid='42541d38')
       ...: builder.y = Int(5)

Note that you don't have to provide the entire UUID to load the node.
As long as the first part of the UUID is unique within your database, AiiDA will find the node you are looking for.

.. note::

    One nifty feature of the builder is the ability to use tab completion for the inputs.
    Try it out by typing ``builder.`` + ``<TAB>`` in the verdi shell.

To execute the ``CalcJob``, we use the ``run`` function provided by the AiiDA engine:

.. code-block:: ipython

    In [4]: from aiida.engine import run
       ...: run(builder)

Wait for the process to complete.
Once it is done, it will return a dictionary with the output nodes:

.. code-block:: ipython

    Out[4]:
    {'sum': <Int: uuid: 7d5d781e-8f17-498a-b3d5-dbbd3488b935 (pk: 8) value: 11>,
    'remote_folder': <RemoteData: uuid: 888d654a-65fb-4da0-b3bc-d63f0374f274 (pk: 9)>,
    'retrieved': <FolderData: uuid: 4733aa78-2e2f-4aeb-8e09-c5cfb58553db (pk: 10s)>}

Besides the sum of the two ``Int`` nodes, the calculation function also returns two other outputs: one of type ``RemoteData`` and one of type ``FolderData``.
See the :ref:`topics section on calculation jobs <topics:calculations:usage:calcfunctions>` for more details.
Now, exit the IPython shell and once more check for *all* processes:

.. code-block:: console

    $ verdi process list -a

You should now see two processes in the list.
One is the ``multiply`` calcfunction you ran earlier, the second is the ``ArithmeticAddCalculation`` CalcJob that you have just run.
Grab the PK of the ``ArithmeticAddCalculation``, and generate the provenance graph.
The result should look like the graph shown in :numref:`fig_calcjob_graph`.

.. code-block:: console

    $ verdi node graph generate 7

.. _fig_calcjob_graph:
.. figure:: include/calcjob_graph.png
    :scale: 35
    :align: center

    Provenance graph of the ``ArithmeticAddCalculation`` CalcJob, with one input provided by the output of the ``multiply`` calculation function.

You can see more details on any process, including its inputs and outputs, using the verdi shell:

.. code:: console

    $ verdi process show 7

Submitting to the daemon
========================

When we used the ``run`` command in the previous section, the IPython shell was blocked while it was waiting for the ``CalcJob`` to finish.
This is not a problem when we're simply adding two number together, but if we want to run multiple calculations that take hours or days, this is no longer practical.
Instead, we are going to *submit* the ``CalcJob`` to the AiiDA *daemon*.
The daemon is a program that runs in the background and manages submitted calculations until they are *terminated*.
Let's first check the status of the daemon using the ``verdi`` CLI:

.. code-block:: console

    $ verdi daemon status

If the daemon is running, the output will be something like the following:

.. code-block:: bash

    Profile: tutorial
    Daemon is running as PID 96447 since 2020-05-22 18:04:39
    Active workers [1]:
      PID    MEM %    CPU %  started
    -----  -------  -------  -------------------
    96448    0.507        0  2020-05-22 18:04:39
    Use verdi daemon [incr | decr] [num] to increase / decrease the amount of workers

In this case, let's stop it for now:

.. code-block:: console

    $ verdi daemon stop

Next, let's *submit* the ``CalcJob`` we ran previously.
Start the ``verdi shell`` and execute the Python code snippet below.
This follows all the steps we did previously, but now uses the ``submit`` function instead of ``run``:

.. code-block:: ipython

    In [1]: from aiida.engine import submit
       ...:
       ...: code = load_code(label='add')
       ...: builder = code.get_builder()
       ...: builder.x = load_node(pk=4)
       ...: builder.y = Int(5)
       ...:
       ...: submit(builder)

When using ``submit`` the calculation job is not run in the local interpreter but is sent off to the daemon and you get back control instantly.
Instead of the *result* of the calculation, it returns the node of the ``CalcJob`` that was just submitted:

.. code-block:: ipython

    Out[1]: <CalcJobNode: uuid: e221cf69-5027-4bb4-a3c9-e649b435393b (pk: 12) (aiida.calculations:arithmetic.add)>

Let's exit the IPython shell and have a look at the process list:

.. code-block:: console

    $ verdi process list

You should see the ``CalcJob`` you have just submitted, with the state ``Created``:

.. code-block:: bash

      PK  Created    Process label             Process State    Process status
    ----  ---------  ------------------------  ---------------  ----------------
      12  13s ago    ArithmeticAddCalculation  ⏹ Created

    Total results: 1

    Info: last time an entry changed state: 13s ago (at 09:06:57 on 2020-05-13)

The ``CalcJob`` process is now waiting to be picked up by a daemon runner, but the daemon is currently disabled.
Let's start it up (again):

.. code-block:: console

    $ verdi daemon start

Now you can either use ``verdi process list`` to follow the execution of the ``CalcJob``, or ``watch`` its progress:

.. code-block:: console

    $ verdi process watch 12

Let's wait for the ``CalcJob`` to complete and then use ``verdi process list -a`` to see all processes we have run so far:

.. code-block:: bash

      PK  Created    Process label             Process State    Process status
    ----  ---------  ------------------------  ---------------  ----------------
       3  6m ago     multiply                  ⏹ Finished [0]
       7  2m ago     ArithmeticAddCalculation  ⏹ Finished [0]
      12  1m ago     ArithmeticAddCalculation  ⏹ Finished [0]

    Total results: 3

    Info: last time an entry changed state: 14s ago (at 09:07:45 on 2020-05-13)

Workflows
=========

So far we have executed each process manually.
AiiDA allows us to automate these steps by linking them together in a *workflow*, whose provenance is stored to ensure reproducibility.
For this tutorial we have prepared a basic ``WorkChain`` that is already implemented in ``aiida-core``.
You can see the code below:

.. dropdown:: MultiplyAddWorkChain code

    .. literalinclude:: ../../../aiida/workflows/arithmetic/multiply_add.py
        :language: python
        :start-after: start-marker

    First, we recognize the ``multiply`` function we have used earlier, decorated as a ``calcfunction``.
    The ``define`` class method specifies the ``input`` and ``output`` of the ``WorkChain``, as well as the ``outline``, which are the steps of the workflow.
    These steps are provided as methods of the ``MultiplyAddWorkChain`` class.

.. note::

    Besides WorkChain's, workflows can also be implemented as *work functions*.
    These are ideal for workflows that are not very computationally intensive and can be easily implemented in a Python function.

Let's run the ``WorkChain`` above!
Start up the ``verdi shell`` and load the ``MultiplyAddWorkChain`` using the ``WorkflowFactory``:

.. code-block:: ipython

    In [1]: MultiplyAddWorkChain = WorkflowFactory('arithmetic.multiply_add')

The ``WorkflowFactory`` is a useful and robust tool for loading workflows based on their *entry point*, e.g. ``'arithmetic.multiply_add'`` in this case.
Similar to a ``CalcJob``, the ``WorkChain`` input can be set up using a builder:

.. code-block:: ipython

    In [2]: builder = MultiplyAddWorkChain.get_builder()
       ...: builder.code = load_code(label='add')
       ...: builder.x = Int(2)
       ...: builder.y = Int(3)
       ...: builder.z = Int(5)

Once the ``WorkChain`` input has been set up, we submit it to the daemon using the ``submit`` function from the AiiDA engine:

.. code-block:: ipython

    In [3]: from aiida.engine import submit
       ...: submit(builder)

Now quickly leave the IPython shell and check the process list:

.. code-block:: console

    $ verdi process list -a

Depending on which step the workflow is running, you should get something like the following:

.. code-block:: bash

      PK  Created    Process label             Process State    Process status
    ----  ---------  ------------------------  ---------------  ------------------------------------
       3  7m ago     multiply                  ⏹ Finished [0]
       7  3m ago     ArithmeticAddCalculation  ⏹ Finished [0]
      12  2m ago     ArithmeticAddCalculation  ⏹ Finished [0]
      19  16s ago    MultiplyAddWorkChain      ⏵ Waiting        Waiting for child processes: 22
      20  16s ago    multiply                  ⏹ Finished [0]
      22  15s ago    ArithmeticAddCalculation  ⏵ Waiting        Waiting for transport task: retrieve

    Total results: 6

    Info: last time an entry changed state: 0s ago (at 09:08:59 on 2020-05-13)

We can see that the ``MultiplyAddWorkChain`` is currently waiting for its *child process*, the ``ArithmeticAddCalculation``, to finish.
Check the process list again for *all* processes (You should know how by now!).
After about half a minute, all the processes should be in the ``Finished`` state.

We can now generate the full provenance graph for the ``WorkChain`` with:

.. code-block:: console

    $ verdi node graph generate 19

Look familiar?
The provenance graph should be similar to the one we showed at the start of this tutorial (:numref:`fig_workchain_graph`).

.. _fig_workchain_graph:
.. figure:: include/workchain_graph.png
    :scale: 30
    :align: center

    Final provenance Graph of the basic AiiDA tutorial.

.. _tutorial:next-steps:

**********
Next Steps
**********

Congratulations! You have completed the first step to becoming an AiiDA expert.

We have also compiled useful how-to guides that are especially relevant for the following use cases:

.. div:: dropdown-group

    .. dropdown:: Run pure Python lightweight computations
        :container:

        Designing a workflow
            After reading the :ref:`Basic Tutorial <tutorial:basic>`, you may want to learn about how to encode the logic of a typical scientific workflow in the :ref:`multi-step workflows how-to <how-to:workflows>`.

        Reusable data types
            If you have a certain input or output data type, which you use often, then you may wish to turn it into its own :ref:`data plugin <how-to:data:plugin>`.

        Exploring your data
            Once you have run multiple computations, the :ref:`find and query data how-to <how-to:data:find>` can show you how to efficiently explore your data. The data lineage can also be visualised as a :ref:`provenance graph <how-to:data:visualise-provenance>`.

        Sharing your data
            You can export all or part of your data to file with the :ref:`export/import functionality<how-to:data:share>` or you can even serve your data over HTTP(S) using the :ref:`AiiDA REST API <how-to:data:serve>`.

        Sharing your workflows
            Once you have a working computation workflow, you may also wish to :ref:`package it into a python module <how-to:plugins>` for others to use.

    .. dropdown:: Run compute-intensive codes
        :container:

        Working with external codes
            Existing calculation plugins, for interfacing with external codes, are available on the `aiida plugin registry <https://aiidateam.github.io/aiida-registry/>`_.
            If none meet your needs, then the :ref:`external codes how-to <how-to:plugin-codes>` can show you how to create your own calculation plugin.

        Tuning performance
            To optimise the performance of AiiDA for running many concurrent computations see the :ref:`tuning performance how-to <how-to:installation:performance>`.

        Saving computational resources
            AiiDA can cache and reuse the outputs of identical computations, as described in the :ref:`caching how-to <how-to:run-codes:caching>`.

    .. dropdown:: Run computations on High Performance Computers

        Connecting to supercomputers
            To setup up a computer which can communicate with a high-performance computer over SSH, see the :ref:`how-to for running external codes <how-to:run-codes>`, or add a :ref:`custom transport <how-to:plugin-codes:transport>`.
            AiiDA has pre-written scheduler plugins to work with LSF, PBSPro, SGE, Slurm and Torque.

        Working with external codes
            Existing calculation plugins, for interfacing with external codes, are available on the `aiida plugin registry <https://aiidateam.github.io/aiida-registry/>`_.
            If none meet your needs, then the :ref:`external codes how-to <how-to:plugin-codes>` can show you how to create your own calculation plugin.

        Exploring your data
            Once you have run multiple computations, the :ref:`find and query data how-to <how-to:data:find>` can show you how to efficiently explore your data. The data lineage can also be visualised as a :ref:`provenance graph <how-to:data:visualise-provenance>`.

        Sharing your data
            You can export all or part of your data to file with the :ref:`export/import functionality<how-to:data:share>` or you can even serve your data over HTTP(S) using the :ref:`AiiDA REST API <how-to:data:serve>`.

        Sharing your calculation plugin
            Once you have a working plugin, you may also wish to :ref:`package it into a python module <how-to:plugins>` for others to use.

.. You can do more with AiiDA than basic arithmetic! Check out some cool real-world examples of AiiDA in action on the `demo page <LINK HERE>

.. todo::

    Add to "Connecting to supercomputers": , or you can add a :ref:`custom scheduler <how-to:plugin-codes:scheduler>`.
