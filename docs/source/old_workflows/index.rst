================
Legacy workflows
================

Workflows are one of the most important components for real high-throughput calculations, allowing the user
to scale well defined chains of calculations on any number of input structures, both generated or acquired from an external source.

Instead of offering a limited number of automatization schemes, crafted for some specific functions (equation of states,
phonons, etc...) in AiiDA a complete workflow engine is present, where the user can script in principle any possible
interaction with all the AiiDA components, from the submission engine to the materials databases connections. In AiiDA
a workflow is a python script executed by a daemon, containing several user defined functions called steps. In each step
all the AiiDA functions are available and calculations and launched and retrieved, as well as other sub-workflows.

In this document we'll introduce the main workflow infrastructure from the user perspective, discussing and presenting some examples
that will cover all the features implemented in the code. A more detailed description of each function can be found in the 
developer documentation.

How it works
++++++++++++

The rationale of the entire workflow infrastructure is to make efficient, reproducible and scriptable anything a user can do 
in the AiiDA shell. A workflow in this sense is nothing more than a list of AiiDA commands, split in different steps
that depend one on each other and that are executed in a specific order. A workflow step is written with the same
python language, using the same commands and libraries you use in the shell, stored in a file as a python class and 
managed by a daemon process. 

Before starting to analyze our first workflow we should summarize very shortly the main working logic of a typical workflow
execution, starting with the definition of the management daemon. The AiiDA daemon handles all the operations of a workflow, 
script loading, error handling and reporting, state monitoring and user interaction with the execution queue.

The daemon works essentially as an infinite loop, iterating several simple operations:

1. It checks the running step in all the active workflows, if there are new calculations attached to a step it submits them. 
2. It retrieves all the finished calculations. If one step of one workflow exists where all the calculations are correctly
   finished it reloads the workflow and executes the next step as indicated in the script.
3. If a workflow's next step is the exit one, the workflow is terminated and the report is closed.

This simplified process is the very heart of the workflow engine, and while the process loops a user can submit a new workflow 
to be managed from the Verdi shell (or through a script loading the necessary Verdi environment). In the next chapter we'll 
initialize the daemon and analyze a simple workflow, submitting it and retrieving the results.

.. note::
  The workflow engine of AiiDA is now fully operational but will undergo major
  improvements in a near future. Therefore, some of the methods or functionalities
  described in the following might change.

The AiiDA daemon
++++++++++++++++

As explained the daemon must be running to allow the execution of workflows, so the first thing needed to start it to launch the 
daemon. We can use the verdi script facility from your computer's shell::

  >> verdi daemon start

This command will launch a background job (a daemon in fact) that will continuously check for new or running workflow to manage. Thanks 
to the asynchronous structure of AiiDA if the daemon gets interrupted (or the computer running the daemon restarted for example), 
once it will be restarted all the workflow will proceed automatically without any problem. The only thing you need to do to restart the
workflow it's exactly the same command above. To stop the daemon instead we use the same command with the ``stop`` directive, and to
have a very fast check about the execution we can use the ``state`` directive to obtain more information.

A workflow demo
+++++++++++++++

Now that the daemon is running we can focus on how to write our first workflow. As explained a workflow is essentially a python 
class, stored in a file accessible by AiiDA (in the same AiiDA path). By convention workflows are stored in *.py* 
files inside the ``aiida/workflows`` directory; in the distribution you'll find some examples (some of them analyzed here) and 
a user directory where user defined workflows can be stored. Since the daemon is aware only of the classes present at the time of its
launch, remember to restart the daemon (``verdi daemon restart``) every time you add a new workflow to let AiiDA see it.

We can now study a very first example workflow, contained in the ``wf_demo.py`` file inside the distribution's ``workflows`` directory.
Even if this is just a toy model, it helps us to introduce all the features and details on how a workflow works, helping
us to understand the more sophisticated examples reported later. 

.. code-block:: python
  :linenos:

      import aiida.common
      from aiida.common import aiidalogger
      from aiida.orm.workflow import Workflow
      from aiida.orm import Code, Computer

      logger = aiidalogger.getChild('WorkflowDemo')

      class WorkflowDemo(Workflow):

        def __init__(self,**kwargs):

            super(WorkflowDemo, self).__init__(**kwargs)

        def generate_calc(self):

            from aiida.orm import Code, Computer, CalculationFactory
            from aiida.common.datastructures import calc_states

            CustomCalc = CalculationFactory('simpleplugins.templatereplacer')

            computer = Computer.get("localhost")

            calc = CustomCalc(computer=computer,withmpi=True)
            calc.set_option('resources', num_machines=1, num_mpiprocs_per_machine=1)
            calc._set_state(calc_states.FINISHED)
            calc.store()

            return calc

        @Workflow.step
        def start(self):

            from aiida.orm.node import Node

            # Testing parameters
            p = self.get_parameters()

            # Testing calculations
            self.attach_calculation(self.generate_calc())
            self.attach_calculation(self.generate_calc())

            # Testing report
            self.append_to_report("Starting workflow with params: {0}".format(p))

            # Testing attachments
            n = Node()
            attrs = {"a": [1,2,3], "n": n}
            self.add_attributes(attrs)

            # Test process
            self.next(self.second_step)

        @Workflow.step
        def second_step(self):

            # Test retrieval
            calcs = self.get_step_calculations(self.start)
            self.append_to_report("Retrieved calculation 0 (uuid): {0}".format(calcs[0].uuid))

            # Testing report
            a = self.get_attributes()
            self.append_to_report("Execution second_step with attachments: {0}".format(a))

            # Test results
            self.add_result("scf_converged", calcs[0])

            self.next(self.exit)

As discussed before this is native python code, meaning that a user can load any library or script accessible from their ``PYTHONPATH``
and interacting with any database or service of preference inside the workflow. We'll now go through all the details of the first workflow,
line by line, discussing the most important methods and discovering along the way all the features available. 

**lines 1-7** Module imports. Some are necessary for the Workflow objects but many more can be added for user defined functions and libraries.

**lines 8-12** Superclass definition, a workflow **MUST** extend the ``Workflow`` class from the ``aiida.orm.workflow``. This is a fundamental 
requirement, since the subclassing is the way AiiDA understand if a class inside the file is an AiiDA workflow or a simple utility class. Note that 
for back-compatibility with python 2.7 also the explicit initialization of line 12 is necessary to make things work correctly.

**lines 14-28** Once the class is defined a user can add as many methods as he wishes, to generate calculations or to download structures 
or to compute new ones starting form a query in previous AiiDA calculations present in the DB. In the script above the method ``generate_calc`` 
will simply prepare a dummy calculation, setting it's state to finished and returning the object after having it stored in the repository. 
This utility function will allow the dummy workflow run without the need of any code or machine except for localhost configured. In real 
cases, as we'll see, a calculation will be set up with parameters and structures defined in more sophisticated ways, but the logic underneath 
is identical as far as the workflow inner working is concerned.

**lines 30-51** This is the first *step*, one of the main components in the workflow logic. As you can see the ``start``
method is decorated as a ``Workflow.step`` making it a very unique kind of method, automatically stored in the database as a container of
calculations and sub-workflows. Several functions are available to the user when coding a workflow step, and in this method we can see most
of the basic ones:

* **line 36** ``self.get_parameters()``. With this method we can retrieve the parameters passed to the workflow
  when it was initialized. Parameters cannot be modified during an execution, while attributes can be added and removed.

* **lines 39-40** ``self.attach_calculation(JobCalculation)``. This is a key point in the workflow, and
  something possible only inside a step method. JobCalculations, generated in the methods or retrieved from other utility methods, are
  attached to the workflow's step, launched and executed completely by the daemon, without the need of user interaction. Failures,
  re-launching and queue management are all handled by the daemon, and thousands of calculations can be attached. The daemon will
  poll the servers until all the step calculations will be finished, and only after that it will pass to the next step. 

* **line 43** ``self.append_to_report(string)``. Once the workflow will be launched, the user interactions
  are limited to some events (stop, relaunch, list of the calculations) and most of the times is very useful to have custom messages
  during the execution. For this each workflow is equipped with a reporting facility, where the user can fill with any text and can
  retrieve both live and at the end of the execution.
  
* **lines 45-48** ``self.add_attributes(dict)``. Since the workflow is instantiated every step from scratch, if a
  user wants to pass arguments between steps he must use the attributes facility, where a dictionary of values (accepted values are
  basic types and AiiDA nodes) can be saved and retrieved from other steps during future executions.
  
* **line 52** ``self.next(Workflow.step)``. This is the final part of a step, where the user points the engine
  about what to do after all the calculations in the steps (on possible sub-workflows, as we'll see later) are terminated. The argument of
  this function has to be a ``Workflow.step`` decorated method of the same workflow class, or in case this is the last step to be executed you can
  use the common method ``self.exit``, always present in each Workflow subclass.

  .. note:: make sure to ``store()`` all input nodes for the attached calculations, as unstored nodes will be lost during the transition
     from one step to another.
  
**lines 53-67** When the workflow will be launched through the ``start`` method, the AiiDA daemon will load the workflow, execute the step, 
launch all the calculations and monitor their state. Once all the calculations in ``start`` will be finished the daemon will then load and 
execute the next step, in this case the one called ``second_step``. In this step new features are shown:

* **line 57** ``self.get_step_calculations(Workflow.step)``. Anywhere after the first step we may need to retrieve and analyze calculations 
  executed in a previous steps. With this method we can have access to the list of calculations of a specific workflows step, passed as 
  an argument.

* **line 61** ``self.get_attributes()``. With this call we can retrieve the attributes stored in previous steps. Remember that this is the only
  way to pass arguments between different steps, adding them as we did in line 48.
  
* **line 65** ``self.add_result()``. When all the calculations are done it's useful to tag some of them as results, using custom string to be
  later searched and retrieved. Similarly to the ``get_step_calculations``, this method works on the entire workflow and not on a single step.

* **line 67** ``self.next(self.exit)``. This is the final part of each workflow, setting the exit. Every workflow inheritate a fictitious step
  called exit that can be set as a next to any step. As the names suggest, this implies the workflow execution to finish correctly.


Running a workflow
++++++++++++++++++

After saving the workflow inside a python file located in the ``aiida/workflows`` directory, we can  launch the workflow simply invoking the
specific workflow class and executing the ``start()`` method inside the Verdi shell. It's important to remember that all the AiiDA framework 
needs to be accessible for the workflow to be launched, and this can be achieved either with the verdi shell or by any other python environment
that has previously loaded the AiiDA framework (see the developer manual for this).

To launch the verdi shell execute ``verdi shell`` from the command line; once inside the shell we have to import the workflow class we
want to launch (this command depends on the file location and the class name we decided). In this case we expect we'll launch the 
WorkflowDemo presented before, located in the ``wf_demo.py`` file in the clean AiiDA distribution. In the shell we execute::
 
  >> from aiida.workflows.wf_demo import WorkflowDemo
  >> params = {"a":[1,2,3]}
  >> wf = WorkflowDemo(params=params)
  >> wf.start()

.. note:: If you want to write the above script in a file, remember to run it
  with ``verdi run`` and not simply with python, or otherwise to use the other
  techniques described :doc:`here <../working_with_aiida/scripting>`.
  
In these four lines we loaded the class, we created some fictitious parameter and 
we initialized the workflow. Finally we launched it with the 
``start()`` method, a lazy command that in the backgroud adds the workflow to 
the execution queue monitored by the verdi daemon. In the backgroud
the daemon will handle all the workflow processes, stepping each method, launching
and retrieving calculations and monitoring possible errors and problems.

Since the workflow is now managed by the daemon, to interact with it we need 
special methods. There are basically two ways to see how the workflows
are running: by printing the workflow ``list`` or its ``report``.

* **Workflow list**

  From the command line we run::

  >> verdi workflow list

  This will list all the running workflows, showing the state of each step 
  and each calculation (and, when present, each sub-workflow - see below). It
  is the fastest way to have a snapshot of 
  what your AiiDA workflow daemon is working on. An example output
  right after the WorkflowDemo submission should be
  
  .. code-block:: python
  
    + Workflow WorkflowDemo (pk: 1) is RUNNING [0h:05m:04s]
    |-* Step: start [->second_step] is RUNNING
    | | Calculation (pk: 1) is FINISHED
    | | Calculation (pk: 2) is FINISHED
  
  For each workflow is reported the ``pk`` number, a unique 
  id identifying that specific execution of the workflow, something
  necessary to retrieve it at any other time in the future (as explained in the
  next point).
  
  .. note::
    You can also print the ``list`` of any individual workflow from the verdi
    shell (here in the shell where you defined your workflow as ``wf``, see above)::
  
    >> import aiida.orm.workflow as wfs
    >> print "\n".join(wfs.get_workflow_info(wf._dbworkflowinstance))
  
  
* **Workflow report** 

  As explained, each workflow is equipped with a reporting facility the user can
  use to log any important intermediate information, useful to debug the state 
  or show some details. Moreover the report is also used by AiiDA as an error 
  reporting tool: in case of errors encountered during the execution, the AiiDA 
  daemon will copy the entire stack trace in the workflow report before
  halting it's execution.
  To access the report we need the specific ``pk`` of the workflow. From the 
  command line we would run::
  
   >> verdi workflow report PK_NUMBER

  while from the verdi shell the same operation requires to use the ``get_report()`` method::
  
  >> load_workflow(PK_NUMBER).get_report()
   
  In both variants, PK_NUMBER is the ``pk`` number of the workflow we want
  the report of. The ``load_workflow`` function loads a Workflow instance from
  its ``pk`` number, or from its ``uuid`` (given as a string).
  
  .. note::
	It's always recommended to get the workflow instance
	from ``load_workflow`` (or from the ``Workflow.get_subclass_from_pk`` method) 
	without saving this object in a variable. 
	The information generated in the report may change and the user calling a 
	``get_report`` method of a class instantiated in the past will probably lose 
	the most recent additions to the report.
  
Once launched, the workflows will be handled by the daemon until the final step 
or until some error occurs. In the last case, the workflow gets halted and the report 
can be checked to understand what happened.

* **Killing a workflow** 

A user can also kill a workflow while it's running. This can be done with 
the following verdi command::

>> verdi workflow kill PK_NUMBER_1 PK_NUMBER_2 PK_NUMBER_N

where several ``pk`` numbers can be given. A prompt will ask for a confirmation;
this can be avoided by using the ``-f`` option.
  
An alternative way to kill an individual workflow is to use the ``kill`` method.
In the verdi shell type:: 

>> load_workflow(PK_NUMBER).kill()

or, equivalently::

>> Workflow.get_subclass_from_pk(PK_NUMBER).kill()

.. note::
  Sometimes the ``kill`` operation might fail because one calculation cannot be
  killed (e.g. if it's running but not in the ``WITHSCHEDULER``, ``TOSUBMIT`` or 
  ``NEW`` state), or because one workflow step is in the ``CREATED`` state. In that case the 
  workflow is put to the ``SLEEP`` state, such that no more workflow steps will be launched
  by the daemon. One can then simply wait until the calculation or step changes state,
  and try to kill it again.
    
A more sophisticated workflow
+++++++++++++++++++++++++++++

.. note:: This workflow uses the Quantum ESPRESSO plugins that are hosted
  `in the aiida-quantumespresso plugin repository <https://github.com/aiidateam/aiida-quantumespresso>`_.

In the previous chapter we've been able to see almost all the workflow features, and we're now ready to work on some more sophisticated examples, 
where real calculations are performed and common real-life issues are solved. As a real case example we'll compute the equation of state 
of a simple class of materials, XTiO3; the workflow will accept as an input the X material, it will build several structures with different 
crystal parameters, run and retrieve all the simulations, fit the curve and run an optimized final structure saving it as the workflow results, 
aside to the final optimal cell parameter value.

.. code-block:: python
  :linenos:

        ## ===============================================
        ##    WorkflowXTiO3_EOS
        ## ===============================================

        class WorkflowXTiO3_EOS(Workflow):

            def __init__(self,**kwargs):

                super(WorkflowXTiO3_EOS, self).__init__(**kwargs)

            ## ===============================================
            ##    Object generators
            ## ===============================================

            def get_structure(self, alat = 4, x_material = 'Ba'):

                cell = [[alat, 0., 0.,],
                        [0., alat, 0.,],
                        [0., 0., alat,],
                       ]

                # BaTiO3 cubic structure
                s = StructureData(cell=cell)
                s.append_atom(position=(0.,0.,0.),symbols=x_material)
                s.append_atom(position=(alat/2.,alat/2.,alat/2.),symbols=['Ti'])
                s.append_atom(position=(alat/2.,alat/2.,0.),symbols=['O'])
                s.append_atom(position=(alat/2.,0.,alat/2.),symbols=['O'])
                s.append_atom(position=(0.,alat/2.,alat/2.),symbols=['O'])
                s.store()

                return s

            def get_pw_parameters(self):

                parameters = ParameterData(dict={
                            'CONTROL': {
                                'calculation': 'scf',
                                'restart_mode': 'from_scratch',
                                'wf_collect': True,
                                },
                            'SYSTEM': {
                                'ecutwfc': 30.,
                                'ecutrho': 240.,
                                },
                            'ELECTRONS': {
                                'conv_thr': 1.e-6,
                                }}).store()

                return parameters

            def get_kpoints(self):

                kpoints = KpointsData()
                kpoints.set_kpoints_mesh([4,4,4])
                kpoints.store()

                return kpoints

            def get_pw_calculation(self, pw_structure, pw_parameters, pw_kpoint):

                params = self.get_parameters()

                pw_codename            = params['pw_codename']
                num_machines           = params['num_machines']
                num_mpiprocs_per_machine   = params['num_mpiprocs_per_machine']
                max_wallclock_seconds  = params['max_wallclock_seconds']
                pseudo_family          = params['pseudo_family']

                code = Code.get_from_string(pw_codename)
                computer = code.get_remote_computer()

                QECalc = CalculationFactory('quantumespresso.pw')

                calc = QECalc(computer=computer)
                calc.set_option('max_wallclock_seconds', max_wallclock_seconds)
                calc.set_option('resources', {"num_machines": num_machines, "num_mpiprocs_per_machine": num_mpiprocs_per_machine})
                calc.store()

                calc.use_code(code)

                calc.use_structure(pw_structure)
                calc.use_pseudos_from_family(pseudo_family)
                calc.use_parameters(pw_parameters)
                calc.use_kpoints(pw_kpoint)

                return calc


            ## ===============================================
            ##    Workflow steps
            ## ===============================================

            @Workflow.step
            def start(self):

                params = self.get_parameters()
                x_material             = params['x_material']

                self.append_to_report(x_material+"Ti03 EOS started")
                self.next(self.eos)

            @Workflow.step
            def eos(self):

                from aiida.orm import Code, Computer, CalculationFactory
                import numpy as np

                params = self.get_parameters()

                x_material             = params['x_material']
                starting_alat          = params['starting_alat']
                alat_steps             = params['alat_steps']


                a_sweep = np.linspace(starting_alat*0.85,starting_alat*1.15,alat_steps).tolist()
            
            aiidalogger.info("Storing a_sweep as "+str(a_sweep))
            self.add_attribute('a_sweep',a_sweep)
            
            for a in a_sweep:
                
                self.append_to_report("Preparing structure {0} with alat {1}".format(x_material+"TiO3",a))
                
                calc = self.get_pw_calculation(self.get_structure(alat=a, x_material=x_material),
                                          self.get_pw_parameters(),
                                          self.get_kpoints())
                
                self.attach_calculation(calc)
                
                
            self.next(self.optimize)
            
        @Workflow.step
        def optimize(self):
            
            from aiida.orm.data.parameter import ParameterData
            
            x_material   = self.get_parameter("x_material")
            a_sweep      = self.get_attribute("a_sweep")
            
            aiidalogger.info("Retrieving a_sweep as {0}".format(a_sweep))
            
            # Get calculations
            start_calcs = self.get_step_calculations(self.eos) #.get_calculations()
            
            #  Calculate results
            #-----------------------------------------
            
            e_calcs = [c.res.energy for c in start_calcs]
            v_calcs = [c.res.volume for c in start_calcs]
            
            e_calcs = zip(*sorted(zip(a_sweep, e_calcs)))[1]
            v_calcs = zip(*sorted(zip(a_sweep, v_calcs)))[1]
            
            #  Add to report
            #-----------------------------------------
            for i in range (len(a_sweep)):
                self.append_to_report(x_material+"Ti03 simulated with a="+str(a_sweep[i])+", e="+str(e_calcs[i]))
            
            #  Find optimal alat
            #-----------------------------------------
            
            murnpars, ier = Murnaghan_fit(e_calcs, v_calcs)
            
            # New optimal alat
            optimal_alat  = murnpars[3]** (1 / 3.0)
            self.add_attribute('optimal_alat',optimal_alat)
            
            #  Build last calculation
            #-----------------------------------------
            
            calc = self.get_pw_calculation(self.get_structure(alat=optimal_alat, x_material=x_material),
                                          self.get_pw_parameters(),
                                          self.get_kpoints())
            self.attach_calculation(calc)
            
            
            self.next(self.final_step)
         
        @Workflow.step
        def final_step(self):
            
            from aiida.orm.data.parameter import ParameterData
	        
            x_material   = self.get_parameter("x_material")
            optimal_alat = self.get_attribute("optimal_alat")
	        
            opt_calc = self.get_step_calculations(self.optimize)[0] #.get_calculations()[0]
            opt_e = opt_calc.get_outputs(node_type=ParameterData)[0].get_dict()['energy']
            
            self.append_to_report(x_material+"Ti03 optimal with a="+str(optimal_alat)+", e="+str(opt_e))
            
            self.add_result("scf_converged", opt_calc)
                
            self.next(self.exit)

Before getting into details, you'll notice that this workflow is devided into sections by comments in the script. This is not necessary, but helps
the user to differentiate the main parts of the code. In general it's useful to be able to recognize immediately which functions are steps and
which are instead utility or support functions that either generate structure, modify them, add special parameters for the calculations, etc. In
this case the support functions are reported first, under the ``Object generators`` part, while Workflow steps are reported later in the soundy
``Workflow steps`` section. Lets now get in deeper details for each function. 

* **__init__** Usual initialization function, notice again the necessary super class initialization for back compatibility.
  
* **start** The workflow tries to get the X material from the parameters, called in this case ``x_material``. If the entry is not present
  in the dictionary an error will be thrown and the workflow will hang, reporting the error in the report. After that a simple line
  in the report is added to notify the correct start and the eos step will be chained to the execution.

* **eos** This step is the heart of this workflow. At the beginning parameters needed to investigate the equation of states are retrieved. In this
  case we chose a very simple structure with only one interesting cell parameter, called ``starting_alat``. The code will take this alat as the
  central point of a linear mesh going from 0.85 alat to 1.15 alat where only a total of ``alat_steps`` will be generated. This decision
  is very much problem dependent, and your workflows will certanly need more parameters or more sophisticated meshes to run a satisfactory
  equation of state analysis, but again this is only a tutorial and the scope is to learn the basic concepts.
  
  After retrieving the parameters, a linear interpolation is generated between the values of interest and for each of these values a calculation
  is generated by the support function (see later). Each calculation is then attached to the step and finally the step chains ``optimize`` as the
  step. As told, the manager will handle all the job execution and retrieval for all the step's calculation before calling the next step, and this
  ensures that no optimization will be done before all the alat steps are computed with success.

* **optimize** In the first lines the step will retrieve the initial parameters, the ``a_sweep`` attribute computed in the previous step and all
  the calculations launched and succesfully retrieved. Energy and volume in each calculation is retrieved thanks to the output parser functions
  mentioned in the other chapters, and a simple message is added to the report for each calculation.
  
  Having the volume and the energy for each simulation we can run a Murnaghan fit to obtain the optimal cell parameter and expected energy, to
  do this we use a simple fitting function ``Murnaghan_fit`` defined at the bottom of the workflow file ``wf_XTiO3.py``. The optimal alat is then saved in
  the attributes and a new calculation is generated for it. The calculation is attached to the step and the ``final_step`` is attached to the 
  execution. 

* **final_step** In this step the main result is collected and stored. Parameters and attributes are retrieved, a new entry in the report is stored
  pointing to the optimal alat and to the final energy of the structure. Finally the calculation is added to the workflow results and the ``exit``
  step is chained for execution.

* **get_pw_calculation (get_kpoints, get_pw_parameters, get_structure)** As you noticed to let the code clean all the functions needed to generate
  AiiDA Calculation objects have been factored in the utility functions. These functions are highly specific for the task needed, and unrelated
  to the workflow functions. Nevertheless they're a good example of best practise on how to write clean and reusable workflows, and we'll comment
  the most important feature.
  
  ``get_pw_calculation`` is called in the workflow's steps, and it handles the entire Calculation object creation. First it extracts the
  parameters from the workflow initialization necessary for the execution (the machine, the code, and the number of core, pseudos, etc..) and
  then it generates and stores the JobCalculation objects, returning it for later use.
  
  ``get_kpoints`` genetates a k-point mesh suitable for the calculation, in this case a fixed MP mesh ``4x4x4``. In a real case scenario this
  needs much more sophisticated calculations to ensure a correct convergence, not necessary for the tutorial.
  
  ``get_pw_parameters`` builds the minimum set of parameters necessary to run the Quantum Espresso simulations. In this case as well parameters
  are not for production. 
  
  ``get_structure`` generates the real atomic arrangement for the specific calculation. In this case the configuration is extremely simple, but
  in principle this can be substituted with an external funtion, implementing even very sophisticated approaches such as genetic algorithm evolution
  or semi-randomic modifications, or any other structure evolution function the user wants to test.
  
As you noticed this workflow needs several parameters to be correctly executed, something natural for real case scenarios. Nevertheless the
launching procedure is identical as for the simple example before, with just a little longer dictionary of parameters::

  >> from aiida.workflows.wf_XTiO3 import WorkflowXTiO3_EOS
  >> params = {'pw_codename':'PWcode', 'num_machines':1, 'num_mpiprocs_per_machine':8, 'max_wallclock_seconds':30*60, 'pseudo_family':'PBE', 'alat_steps':5, 'x_material':'Ba','starting_alat':4.0}
  >> wf = WorkflowXTiO3_EOS(params=params)
  >> wf.start()

To run this workflow remember to update the ``params`` dictionary with the correct values for your AiiDA installation (namely ``pw_codename`` and
``pseudo_family``).


Chaining workflows
++++++++++++++++++

After the previous chapter we're now able to write a real case workflow that runs in a fully automatic way EOS analysis for simple 
structures. This covers almost all the workflow engine's features implemented in AiiDA, except for workflow chaining.

Thanks to their modular structure a user can write task-specific workflows very easly. An example is the EOS before, or an energy
convergence procedure to find optimal cutoffs, or any other necessity the user can code. These self contained workflows can easily become
a library of result-oriented scripts that a user would be happy to reuse in several ways. This is exactly where sub-workflows come in handy.

Workflows, in an abstract sense, are in fact calculations, that accept as input some parameters and that produce results as output. 
The way this calculations are handled is competely transparent for the user and the engine, and if a workflow could launch other 
workflows it would just be a natural extension of the step's calculation concept. This is in fact how workflow chaining has been 
implemented in AiiDA. Just as with calculations, in each step a workflow can attach another workflow for executions, and the AiiDA 
daemon will handle its execution waiting for its successful end (in case of errors in any subworkflow, such errors will be reported and the
entire workflow tree will be halted, exactly as when a calculation fails).

To introduce this function we analyze our last example, where the WorkflowXTiO3_EOS is used as a sub workflow. The general idea of this
new workflow is simple: if we're now able to compute the EOS of any XTiO3 structure we can build a workflow to loop among several X 
materials, obtain the relaxed structure for each material and run some more sophisticated calculation. In this case we'll compute
phonon vibrational frequncies for some XTiO3 materials, namely Ba, Sr and Pb.

.. code-block:: python
  :linenos:

        ## ===============================================
        ##    WorkflowXTiO3
        ## ===============================================

        class WorkflowXTiO3(Workflow):

            def __init__(self,**kwargs):

                super(WorkflowXTiO3, self).__init__(**kwargs)

            ## ===============================================
            ##    Calculations generators
            ## ===============================================

            def get_ph_parameters(self):

                parameters = ParameterData(dict={
                    'INPUTPH': {
                        'tr2_ph' : 1.0e-8,
                        'epsil' : True,
                        'ldisp' : True,
                        'nq1' : 1,
                        'nq2' : 1,
                        'nq3' : 1,
                        }}).store()

                return parameters

            def get_ph_calculation(self, pw_calc, ph_parameters):

                params = self.get_parameters()

                ph_codename            = params['ph_codename']
                num_machines           = params['num_machines']
                num_mpiprocs_per_machine   = params['num_mpiprocs_per_machine']
                max_wallclock_seconds  = params['max_wallclock_seconds']

                code = Code.get_from_string(ph_codename)
                computer = code.get_remote_computer()

                QEPhCalc = CalculationFactory('quantumespresso.ph')
                calc = QEPhCalc(computer=computer)

                calc.set_option('max_wallclock_seconds', max_wallclock_seconds) # 30 min
                calc.set_option('resources', {"num_machines": num_machines, "num_mpiprocs_per_machine": num_mpiprocs_per_machine})
                calc.store()

                calc.use_parameters(ph_parameters)
                calc.use_code(code)
                calc.use_parent_calculation(pw_calc)

                return calc

            ## ===============================================
            ##    Workflow steps
            ## ===============================================

            @Workflow.step
            def start(self):

                params = self.get_parameters()
                elements_alat = [('Ba',4.0),('Sr', 3.89), ('Pb', 3.9)]

                for x in elements_alat:

                    params.update({'x_material':x[0]})
                    params.update({'starting_alat':x[1]})

                    aiidalogger.info("Launching workflow WorkflowXTiO3_EOS for {0} with alat {1}".format(x[0],x[1]))

                    w = WorkflowXTiO3_EOS(params=params)
                    w.start()
                    self.attach_workflow(w)

                self.next(self.run_ph)

            @Workflow.step
            def run_ph(self):

                # Get calculations
                sub_wfs = self.get_step(self.start).get_sub_workflows()

                for sub_wf in sub_wfs:

                    # Retrieve the pw optimized calculation
                    pw_calc = sub_wf.get_step("optimize").get_calculations()[0]

                    aiidalogger.info("Launching PH for PW {0}".format(pw_calc.get_job_id()))
                    ph_calc = self.get_ph_calculation(pw_calc, self.get_ph_parameters())
                    self.attach_calculation(ph_calc)

                self.next(self.final_step)

            @Workflow.step
            def final_step(self):

                #self.append_to_report(x_material+"Ti03 EOS started")
                from aiida.orm.data.parameter import ParameterData
                import aiida.tools.physics as ps

                params = self.get_parameters()

                # Get calculations
                run_ph_calcs = self.get_step_calculations(self.run_ph) #.get_calculations()

                for c in run_ph_calcs:
                    dm = c.get_outputs(node_type=ParameterData)[0].get_dict()['dynamical_matrix_1']
                    self.append_to_report("Point q: {0} Frequencies: {1}".format(dm['q_point'],dm['frequencies']))

                self.next(self.exit)


    Most of the code is now simple adaptation of previous examples, so we're going to comment only the most relevant differences where
    workflow chaining plays an important role.

    * **start** This workflow accepts the same input as the WorkflowXTiO3_EOS, but right at the beginning the workflow a list of X materials
  is defined, with their respective initial alat. This list is iterated and for each material a new Workflow is both generated, started and
  attached to the step. At the end ``run_ph`` is chained as the following step.

* **run_ph** Only after all the subworkflows in ``start`` are succesfully completed this step will be executed, and it will immediately retrieve
  all the subworkflow, and from each of them it will get the result calculations. As you noticed the result can be stored with any user defined key,
  and this is necessary when someone wants to retrieve it from a completed workflow. For each result a phonon calculation is launched and then
  the ``final_step`` step is chained.
  
To launch this new workflow we have only to add a simple entry in the previous parameter dictionary, specifing the phonon code, as reported here::

  >> from aiida.workflows.wf_XTiO3 import WorkflowXTiO3
  >> params = {'pw_codename':'PWcode', 'ph_codename':'PHcode', 'num_machines':1, 'num_mpiprocs_per_machine':8, 'max_wallclock_seconds':30*60, 'pseudo_family':'PBE', 'alat_steps':5 }
  >> wf = WorkflowXTiO3(params=params)
  >> wf.start()
  
 

Compatibility with new workflows
++++++++++++++++++++++++++++++++

As part of the deprecation process of the old workflows to ease the transition we
support the ability to launch old workflows from :class:`~aiida.work.workchain.WorkChain` s.
The `ToContext` object can be used with the future returned by `self.submit`
that tells `ToContext` how to wait for it to be done and store it in the context on completion.
An example:

.. code-block:: python
    :linenos:
    
    from aiida.work.run import legacy_workflow
    from aiida.work.workchain import WorkChain, ToContext, Outputs

    class MyWf(WorkChain):
        @classmethod
        def define(cls, spec):
            super(MyWf, cls).define(spec)
            spec.outline(cls.step1, cls.step2)

        def step1(self):
            wf = OldEquationOfState()
            future = self.submit(wf)
            return ToContext(eos=wf)

        def step2(self):
            # Now self.ctx.eos contains the terminated workflow
            pass


similarly if you just want the outputs of an old workflow rather than the
workflow object itself replace line 12 with::

    return ToContext(eos=Outputs(wf)))
