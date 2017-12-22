############################
Tutorial: Developer Workflow
############################



Creating new workflows
++++++++++++++++++++++

In this section we are going to write a very simple AiiDA workflow. 
Before starting this tutorial, we assume that you have successfully 
completed the :doc:`Developer calculation 
plugin tutorial<devel_tutorial/code_plugin_int_sum>` and have your input and 
output plugins ready to use with this tutorial.

This tutorial creates a workflow for the addition of three numbers. 
Number could be an integer or a float value. All three numbers will be passed 
as parameters to the workflow in dictionary format 
(e.g. ``{"a": 1, "b": 2.2, "c":3}``).

To demonstrate how a workflow works, we will perform the sum of three 
numbers in two steps:

1. Step 1: temp_value = a + b
2. Step 2: sum = temp_value + c

A workflow in AiiDA is a python script with several user defined functions called ``steps``. All AiiDA functions are available inside “steps” and calculations or sub-workflows can be launched and retrieved. The AiiDA daemon executes a workflow and handles all the operations starting from script loading, error handling and reporting, state monitoring and user interaction with the execution queue. The daemon works essentially as an infinite loop, iterating several simple operations:

1. It checks the running step in all the active workflows, if there are new calculations attached to a step it submits them.
2. It retrieves all the finished calculations. If one step of one workflow exists where all the calculations are correctly finished it reloads the workflow and executes the next step as indicated in the script.
3. If a workflow's next step is the exit one, the workflow is terminated and the report is closed.

.. note:: Since the daemon is aware only of the classes present at the time 
   of its launch, make sure you restart the daemon every time you add a 
   new workflow, or modify an existing one. 
   To restart a daemon, use following command::

     verdi daemon restart

Let's start to write a workflow step by step. First we have to import some 
packages:

.. code-block:: python

    from aiida.common import aiidalogger
    from aiida.orm.workflow import Workflow
    from aiida.orm import Code, Computer
    from aiida.orm.data.parameter import ParameterData
    from aiida.common.exceptions import InputValidationError

In order to write a workflow, we must create a class by extending the 
``Workflow`` class from ``aiida.orm.workflow``. This is a fundamental 
requirement, since the subclassing is the way AiiDA understand if a class 
inside the file is an AiiDA workflow or a simple utility class. In the class, 
you need to re-define an __init__ method as shown below (in the current
code version, this is a requirement).
Create a new file, which has the same name as the class you are creating 
(in this way, it will be possible to load it with ``WorkflowFactory``),
in this case ``addnumbers.py``, with the following content:

.. code-block:: python

    class AddnumbersWorkflow(Workflow):
        """
        This workflow takes 3 numbers as an input and gives
        its addition as an output.
        Workflow steps:
        passed parameters: a,b,c
        1st step: a + b = step1_result
        2nd step: step1_result + c = final_result
        """

        def __init__(self, **kwargs):
            super(AddnumbersWorkflow, self).__init__(**kwargs)

Once the class is defined a user can add methods to generate calculations, download structures or compute new structures starting form a query in previous AiiDA calculations present in the DB. Here we will add simple helper function to validate the input parameters which will be the dictionary with keys ``a``, ``b`` and ``c``. All dictionary values should be of type integer or float.

.. code-block:: python

    def validate_input(self):
        """
        Check if the passed parameters are of type int or float
        else raise exception
        """
        # get parameters passed to workflow when it was
        # initialised. These parameters can not be modified
        # during an execution
        params = self.get_parameters()

        for k in ['a','b','c']:
            try:
                # check if value is int or float
                if not (isinstance(params[k], int) or isinstance(params[k], float)):
                    raise InputValidationError("Value of {} is not of type int or float".format(k))
            except KeyError:
                raise InputValidationError("Missing input key {}".format(k))

        # add in report
        self.append_to_report("Starting workflow with params: {0}".format(params))

In the above method we have used append_to_report workflow method. Once the workflow is launched, the user interactions are limited to some events (stop, relaunch, list of the calculations). So most of the times it is very useful to have custom messages during the execution. Hence, workflow is equipped with a reporting facility ``self.append_to_report(string)``, where the user can fill with any text and can retrieve both live and at the end of the execution.

Now we will add the method to launch the actual calculations. We have already done this as part of plugin exercise and hence we do not discuss it in detail here.

.. code-block:: python

    def get_calculation_sum(self, a, b):
            """
            launch new calculation
            :param a: number
            :param b: number
            :return: calculation object, already stored
            """
            # get code/executable file
            codename = 'sum'
            code = Code.get_from_string(codename)

            computer_name = 'localhost'
            computer = Computer.get(computer_name)             

            # create new calculation
            calc = code.new_calc()
            calc.set_computer(computer)
            calc.label = "Add two numbers"
            calc.description = "Calculation step in a workflow to add more than two numbers"
            calc.set_max_wallclock_seconds(30*60) # 30 min
            calc.set_withmpi(False)
            calc.set_resources({"num_machines": 1})

            # pass input to the calculation
            parameters = ParameterData(dict={'x1': a,'x2':b,})
            calc.use_parameters(parameters)

            # store calculation in database
            calc.store_all()
            return calc

Now we will write the first ``step`` which is one of the main components 
in the workflow. In the example below, the start method is decorated with 
``Workflow.step`` making it a very unique kind of method, automatically stored
in the database as a container of calculations and sub-workflows.

.. code-block:: python

    @Workflow.step
        def start(self):
            """
            Addition for first two parameters passed to workflow
            when it was initialised
            """

            try:
                self.validate_input()
            except InputValidationError:
                self.next(self.exit)
                return

            # get first parameter passed to workflow when it was initialised.
            a = self.get_parameter("a")
            # get second parameter passed to workflow when it was initialised.
            b = self.get_parameter("b")

            # start first calculation
            calc = self.get_calculation_sum(a, b)

            # add in report
            self.append_to_report("First step calculation is running...")

            # attach calculation in workflow to access in next steps
            self.attach_calculation(calc)

            # go to next step
            self.next(self.stage2)

Several functions are available to the user when coding a workflow step, and 
in the above method we have used basic ones discussed below:



* ``self.get_parameters()``: with this method we can retrieve the parameters 
  passed to the workflow when it was initialized. Parameters cannot be modified 
  during an execution, while attributes can be added and removed.

* ``self.attach_calculation(calc)``: this is a key point in the workflow, and
  something possible only inside a step method. Every ``JobCalculation``, generated in 
  the method itself or retrieved from other utility methods, is attached to the 
  workflow’s step. They are then launched and executed completely by 
  the daemon, without the need of user interaction. 
  Any number of calculations can be attached. The 
  daemon will poll the servers until all the step calculations will be finished,
  and only after that it will call the next step.

* ``self.next(Workflow.step)``: this is the final part of a step,
  where the user points the engine about what to do after all the calculations 
  in the steps (on possible sub-workflows, as we will see later) are terminated. 
  The argument of this function has to be a Workflow.step decorated method 
  of the same workflow class, or in case this is the last step to be executed,
  you can use the common method ``self.exit`` which is always present in 
  each ``Workflow`` subclass.
  Note that while this call typically occurs at the end of the function, this
  is not required and you can call the ``next()`` method as soon as you can
  decide which method should follow the current one. As it can be seen above,
  we can use some python logic (``if``, ...) to decide what the ``next`` method
  is going to be (above, we directly point to ``self.exit`` if the input is 
  invalid).
 
 .. note:: remember to call ``self.next(self.stage2)`` and NOT 
    ``self.next(self.stage2())``!! In the first case, we are correctly passing
    the `method` ``stage2`` to ``next``. In the second case we are instead
    immediately running the ``stage2`` method, something we do not want to do
    (we need to wait for the current step to finish), and passing its `return
    value` to  ``self.next`` (which is wrong).

The above start step calls method ``validate_input()`` to validate the input 
parameters. When the workflow will be launched through the ``start`` method, 
the AiiDA daemon will load the workflow, execute the step, launch all the
calculations and monitor their state.

Now we will create a second step to retrieve the addition of first two numbers 
from the first step and then we will add the third input number. 
Once all the calculations in the start step will be finished, 
the daemon will load and execute the next step i.e. ``stage2``, shown below:

.. code-block:: python

    @Workflow.step
        def stage2(self):
            """
            Get result from first calculation and add third value passed
            to workflow when it was initialised
            """
            # get third parameter passed to workflow when it was initialised.
            c = self.get_parameter("c")
            # get result from first calculation
            start_calc = self.get_step_calculations(self.start)[0]

            # add in report
            self.append_to_report("Result of first step calculation is {}".format(
                start_calc.res.sum))

            # start second calculation
            result_calc = self.get_calculation_sum(start_calc.res.sum, c)

            # add in report
            self.append_to_report("Second step calculation is done..")

            # attach calculation in workflow to access in next steps
            self.attach_calculation(result_calc)

            # go to next step
            self.next(self.stage3)

The new feature used in the above step is:

* ``self.get_step_calculations(Workflow.step)``: anywhere after the first step
  we may need to retrieve and analyze calculations executed in a previous steps.
  With this method we can have access to the list of calculations of a specific 
  workflows step, passed as an argument.

Now in the last step of the workflow we will retrieve the results from 
``stage2`` and exit the workflow by calling ``self.next(self.exit)`` method:

.. code-block:: python

    @Workflow.step
        def stage3(self):
            """
            Get the result from second calculation and add it as final
            result of this workflow
            """
            # get result from second calculation
            second_calc = self.get_step_calculations(self.stage2)[0]

            # add in report
            self.append_to_report("Result of second step calculation is {}".format(
                second_calc.res.sum))

            # add workflow result
            self.add_result('value',second_calc.res.sum)

            # add in report
            self.append_to_report("Added value to workflow results")

            # Exit workflow
            self.next(self.exit)

The new features used in the above step are:

* ``self.add_result()``: When all calculations are done it is useful to tag 
  some of them as results, using custom string to be later searched and 
  retrieved. Similarly to the ``get_step_calculations``, this method works 
  on the entire workflow and not on a single step.

* ``self.next(self.exit)``: This is the final part of each workflow. Every 
  workflow inheritate a fictitious step called ``exit`` that can be set as 
  a next to any step. As the names suggest, this implies the workflow 
  execution finished correctly.


Running a workflow
+++++++++++++++++++

After saving the workflow inside a python file (i.e. ``addnumbers.py`) 
located in the ``aiida/workflows`` directory, we can launch the workflow 
simply invoking the specific workflow class and executing the ``start()`` 
method inside the ``verdi shell`` or in a python script (with the AiiDA framework
loaded).

.. note:: Don't forget to (re)start your daemon at this point!

In this case, let's use the ``verdi shell``. In the shell we execute:

.. code-block:: python

    AddnumbersWorkflow = WorkflowFactory("addnumbers")
    params = {"a":2, "b": 1.4, "c": 1}
    wobject = AddnumbersWorkflow(params=params)
    wobject.store()
    wobject.start()

In the above example we initialized the workflow with input parameters as 
a dictionary. The ``WorkflowFactory`` will work only if you gave the correct
name both the python file and to the class. Otherwise, you can just substitute
that line with a suitable import like::

  from aiida.orm.workflows.addnumbers import AddnumbersWorkflow

We launched the workflow using ``start()`` method after storing it.
Since ``start`` is a decorated workflow step, the workflow is added to the
workflow to the execution queue monitored by the AiiDA daemon. 

 We now need to know what is going on.
 There are basically two main ways to see the workflows that are running: 
 by printing the workflow ``list`` or a single workflow ``report``.

* **Workflow list**

  From the command line we run::

  >> verdi workflow list

  This will list all the running workflows, showing the state of each step 
  and each calculation (and, when present, each sub-workflow). It
  is the fastest way to have a snapshot of 
  what your AiiDA workflow daemon is working on. An example output
  right after the AddnumbersWorkflow submission should be:

  .. code-block:: python
  
    + Workflow AddnumbersWorkflow (pk: 76) is RUNNING [0h:00m:14s ago]
    |-* Step: start [->stage2] is RUNNING
    | | Calculation ('Number sum', pk: 739) is TOSUBMIT
    |

  The ``pk`` number of each workflow is reported, a unique 
  ID identifying that specific execution of the workflow, something
  necessary to retrieve it at any other time in the future (as explained in the
  next point).

* **Workflow report** 

  As explained, each workflow is equipped with a reporting facility the user can
  use to log any intermediate information, useful to debug the state 
  or show some details. Moreover the report is also used by AiiDA as an error 
  reporting tool: in case of errors encountered during the execution, the AiiDA 
  daemon will copy the entire stack trace in the workflow report before
  halting its execution.
  To access the report we need the specific ``pk`` of the workflow. From the 
  command line you would run::
  
   verdi workflow report PK_NUMBER

  while from the verdi shell the same operation requires to use the 
  ``get_report()`` method::
  
   >> load_workflow(PK_NUMBER).get_report()
   
  In both variants, PK_NUMBER is the ``pk`` number of the workflow we want
  the report of. The ``load_workflow`` function loads a Workflow instance from
  its ``pk`` number, or from its ``uuid`` (given as a string).

  Once launched, the workflows will be handled by the daemon until the final step 
  or until some error occurs. In the last case, the workflow gets halted and the report 
  can be checked to understand what happened.

* **Workflow result**

  As explained, when all the calculations are done it is useful to tag some 
  nodes or quantities as results, using a custom string to be later searched 
  and retrieved. This method works on the entire workflow and not on a 
  single step.

  To access the results we need the specific ``pk`` of the workflow. From the 
  verdi shell, you can use the ``get_report()`` method::
  
   >> load_workflow(PK_NUMBER).get_results()
   
  In both variants, PK_NUMBER is the ``pk`` number of the workflow we want
  the report of. 

* **Killing a workflow** 

  A user can also kill a workflow while it is running. This can be done with 
  the following verdi command::

     >> verdi workflow kill PK_NUMBER_1 PK_NUMBER_2 PK_NUMBER_N
  
  where several ``pk`` numbers can be given. A prompt will ask for a confirmation;
  this can be avoided by using the ``-f`` option.
  
  An alternative way to kill an individual workflow is to use the ``kill`` method.
  In the verdi shell type:: 

     >> load_workflow(PK_NUMBER).kill()

Exercise
+++++++++

In the exercise you have to write a workflow for the addition of 
six numbers, using the workflow we just wrote as subworkflows.

For this workflow use:

* Input parameters: 
    params = {“w1”: {“a”: 2, “b”: 2.1, “c”: 1}, “w2”: {“a”: 2, “b”: 2.1, “c”: 4}}

* start step: 
        Use two sub workflows (the ones developed above)
        for the addition of three numbers:
        
        - Sub workflow with input w1 and calculate its sum (temp_result1)
        - Sub workflow with input w2 and calculate its sum (temp_result2)

* stage2 step:
    ``final_result = temp_result1 + temp_result2``
    Add ``final_result`` to the workflow results and exit the workflow.

Some notes and tips:

* You can attach a subworkflow similarly to how you attach a calculation: in the
  step, create the new subworkflow, set its parameters using ``set_parameters``,
  store it, call the start() method, and then call 
  ``self.attach_workflow(wobject)`` to attach it to the current step.

* If you want to pass intermediate data from one step to another, you can set
  the data as a workflow attibute: in a step, call 
  ``self.add_attribute(attr_name, attr_value)``, and retrieve it
  in another step using ``attr_value = self.get_attribute(attr_name)``.
  Values can be any JSON-serializable value, or an AiiDA node.



