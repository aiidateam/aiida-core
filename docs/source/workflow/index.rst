===============
AiiDA workflows
===============

Workflows are one of the most important components for real high-throughput calculations, allowing the user
to scale well defined chains of calculations on any number of input structures, both generated or acquired from an external source.

Instead of offering a limited number of automatization schemes, crafted for some specific functions (equation of states,
phonons, etc...) in AiiDA a complete workflow engine is present, where the user can script in principle any possible
interaction with all the AiiDA components, from the submission engine to the materials databases connections. In this framework
a workflow is a python script that an AiiDA daemon can execute, containing several steps and eventually other sub-workflows. 

How it works
++++++++++++

The rationale of the entire workflow infrastructure is to make efficient, reproducible and scriptable what a user can do 
in the AiiDA shell. A workflow in this sense is nothing more than an ordered list of AiiDA commands, split in different steps
to give some ordering necessary on successive calculation depending one from another. A workflow step is written with the same
python language, using the same commands and libraries, stored in a file as a python class and managed by a daemon process. 

Before starting to analyze our first workflow we should summarize very shortly the main working logic of a typical workflow
execution, starting with te definition of the management daemon. The AiiDA daemon handles all the operations of a workflow, 
script loading, error handling and reporting, status monitoring and user interaction while in execution.  

The daemon iterates several simple operations:

1. Checks the running step in all the workflows, if there are new calculations attached to a step it submits them. 
2. Retrieves all the finished calculations. If it exists one step of one workflow where all the calculations are correctly
   finished it reload the workflow and executes the next step as indicated in the script.
3. If the next step is the exit one, the workflow is terminated and the report is closed.

This simplified process is the very heart of the workflow engine, and the user can submit a new workflow to be managed both from the
Verdi shell or a script loading the necessary Verdi environment. In the next chapter we'll initialize the Daemon and analyze a simple
workflow, submitting it and retrieving the results.  

The AiiDA daemon
++++++++++++++++

As explained the daemon must be running to allow the execution of workflows, but thanks to the asyncronous structure of AiiDA if the 
daemon gets interrupted (or the computer running the daemon restarted for example), once it will be restarted all the workflow
will proceed automatically without any problem.  

To launch the daemon we can use the verdi script facility from your computer's shell::

  >> verdi daemon start

To stop the daemon we use the same command with the ``stop`` directive (and ``status`` to obtain more information).

A workflow demo
+++++++++++++++

Once the daemon is running we can focus on a real workflow structure. As explained a workflow is essentially a python 
class, stored in a file accessible by AiiDA (in the same AiiDA path). By convention workflows are stored in *.py* 
files inside the ``aiida/workflows`` directory; in the distribution you'll find some examples (some of them analyzed here) and 
a user directory where user defined workflows can be stored. Remember to restart the daemon (``verdi daemon start``) every time 
you add a new workflow to let AiiDA access the new classes and files.

We can now study a very first example workflow, contained in the ``wf_demo.py`` file inside the distribution's ``workflows`` directory.
Even if this is just a toy model, it helps us to introduce all the features and details on how a workflow functions, helping
us to understand the more sophisticated examples reported later. 

.. code-block:: python
  :linenos:
   
  import aiida.common
  from aiida.common import aiidalogger
  from aiida.orm.workflow import Workflow
  from aiida.orm import Calculation, Code, Computer

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
        calc.set_resources(num_machines=1, num_mpiprocs_per_machine=1)
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
        self.add_result("scf.converged", calcs[0])
        
        self.next(self.exit)

As discussed before this is native python code, meaning that a user can load any library or script accessible from their ``PYTHONPATH``
and interacting with any database or service of preference inside the workflow, managed by AiiDA through the daemon in a fully automatized way.
We can now analyze all the details of the first workflow, discussing the most important methods. 

**lines 1-7** Module imports. Some are necessary for the Workflow objects but many more can be added for user defined functions and libraries.

**lines 8-12** Superclass definition, a workflow **MUST** extend the ``Workflow`` class from the ``aiida.orm.workflow``. This is a fundamental 
requirement, since the subclassing is the way AiiDA understand if a class inside the file is an AiiDA workflow or a simple utility class. Note that 
for back-compatibility with python 2.7 also the explicit initialization of line 12 is necessary to make things works correctly.

**lines 14-28** Once the class is defined a user can add as many methods as he wishes, to generate calculations or to download structures 
or to compute new ones starting form a query in previous AiiDA calculations present in the DB. In the script above the method ``generate_calc`` 
will simply prepare a dummy calculation, setting it's status to finished and returning the object after having it stored in the repository. 
This utility function will allow the dummy workflow run without the need of any code or machine except for localhost configured. In real 
case, as we'll see, a calculation will be set-up with parameters and structures defined in more sophisticated ways, but the logic underneath 
is identical as far as the workflow inner working is concerned.

**lines 30-51** This is the first *step*, one of the main components in the workflow logic. As you can see the ``start``
method is decorated as a ``Workflow.step`` making it a very unique kind of method, automatically stored in the database as a container of
calculations and sub-workflows. Several functions are available to the user when coding a workflow step, and in this methid we can see most
of the basic ones:

* **line 36** ``self.get_parameters()``. With this method we can retrieve the parameters passed to the workflow
  when it was initialized. Parameters cannot be modified during an execution, while attributes can be added and removed.

* **lines 39-40** ``self.attach_calculation(Calculation)``. This is a key point in the workflow, and
  something possible only inside a step method. Calculations, generated in the methos or retrived from other utility methods, are
  attached to the workflow's step, launched and executed completely by the daemon, without the need of user interaction. Failures,
  re-launching and queue management are all handled by the daemon, and thousands of calculations can be attached. The daemon will
  poll the servers until all the step calculations will be finished, and only after that it will pass to the next step. 

* **line 43** ``self.append_to_report(string)``. Once the workflow will be launched, the user interactions
  are limited to some events (stop, relaunch, list of the calculations) and most of the times is very usefull to have custom messages
  during the execution. For this each workflow is equipped with a reporting facility, where the user can fill with any text and can
  retrieve both live and at the end of the execution.  
  
* **lines 45-48** ``self.add_attributes(dict)``. Since the workflow is instantiated every step from scratch, if a
  user want to pass arguments between steps he must use the attributes facility, where a dictionary of values (accepted values are
  basic types and AiiDA nodes) can be saved and retrieved from other steps during future executions.
  
* **line 52** ``self.next(Workflow.step)``. This is the final part of a step, where the user points the engine
  about what to the after all the calculations in the steps (on possibile sub-workflows, as we'll see later) are terminated. The argument of
  this function has to be a ``Workflow.step`` decorated method of the same workflow class, or in case this is the last step to be executed you can
  use the common method ``self.exit``, always present in each Workflow subclass.
  
**lines 53-67** When the workflow will be launched through the ``start`` method, the AiiDA daemon will load the workflow, execute the step, 
launch all the calculations and monitor their status. Once all the calculations in ``start`` will be finished the daemon will then load and 
execute the next step, in this case the one called ``second``. In this step new features are shown:

* **line 57** ``self.get_step_calculations(Workflow.step)``. Anywhere after the first step we may need to retrieve and analyze calculations 
  executed in a previous steps. With this method we can have access to the list of calculations of a specific workflows step, passed as 
  an argument.

* **line 61** ``self.get_attributes()``. With this call we can retrive the attributes stored in previous steps. Remember that this is the only
  way to pass arguments between different steps, adding them as we did in line 48.
  
* **line 65** ``self.add_result()``. When all the calculations are done it's usefull to tag some of them as reults, using custom string to be
  later searched and retrived. Similary to the ``get_step_calculations``, this methos works on the entire workflow and not on a single step.

* **line 67** ``self.next(self.exit)``. This is the final part of each workflow, setting the exit. Every workflow inheritate a fictitious step
  called exit that can be set as a next to any step. As the names suggest, this implies the workflow execution to finish correctly.


Running a workflow
++++++++++++++++++

After saving the workflow inside a python file located in the ``aiida/workflows`` directory we can now launch the workflow simply invoking the
specific workflow class and executing the ``start()`` method. It's important to remember that all the AiiDA framework needs to be accessible
for the workflow to be launched, and this can be achieved with the verdi shell, an AiiDA-aware ipthon shell.

To launch the verdi shell simply execute ``verdi shell`` from the command line; once inside the shell we have to import the workflow class we
want to launch and this depends from the file location and name we decided. In this case we expect we'll launch the WorkflowDemo presented before,
located in the ``wf_demo.py`` file in the clean AiiDA distribution. In the shell we execute::
 
  >> from aiida.workflows.wf_demo import WorkflowDemo
  >> params = {"a":[1,2,3]}
  >> wf = WorkflowDemo(params=params)
  >> wf.start()
  
In this four lines we loaded the class, we created some fictitious parameter and we initialized the workflow. Finally we launched with the 
``start()`` method, a lazy command that in the backgroud adds the workflow to the execution queue monitored by the verdi daemon. In the backgroud
the daemon will handle all the workflow process, stepping each method, launching and retrieving calculations and monitoring possibile errors and
problems.

Since the workflow in now managed buy the daemon to interact with it we need special methods. There are basically two ways to see how the workflows
are running, calling the verbose ``list_workflows`` method present in the ``aiida.orm.workflow`` package or reading the workflow report of each
single workflow.   

* **list_workflows** From the verdi shell we run::
 
  >> import aiida.orm.workflow as wfs
  >> print wfs.list_workflows()
  
  This will list all the running workflow, showing the status of each step and calculation. And example output right after the
  WorkflowDemo submission should be
  
  .. code-block:: python
  
    + Workflow WorkflowDemo (pk=1) is RUNNING [0h:05m:04s]
    |-* Step: start [->second_step] is RUNNING
    | | Calculation (pk=1) is FINISHED
    | | Calculation (pk=2) is FINISHED
  
  As you can see for each workflow is reported the ``pk`` number, a unique number identifing that specific execution of the workflow, something
  necessary to retrive it in any other time in the future (as explained in the next point). The list methid con also be invoked from the verdi
  command line interface without accessing the shell and represents the fastest way to have a snapshot of what your AiiDA daemon is working on.
  
* **get_report** As explained before, each workflow is equipped with a reporting facility the user can use to log any important intemediary
  information, useful to debug the stauts or show some details. Moreover the report is also used by AiiDA as a error reporting tools, where in 
  case of errors encoutered during the execution the AiiDA daemon will copy the entire stakc trace of the error in the workflow report before
  halting it's execution. To access the report we have to retrive the specific workflow instance of interest and call the ``get_report()`` method.
  Using the verdi shell we can do this with a simple line of code::
  
  >> from aiida.orm.workflow import Workflow
  >> Workflow.get_subclass_from_pk(1).get_report()
   
  As you can see the specific ``pk`` is needed to retrive the report, and some caution is needed. In fact, it's always reccomended to get the report
  from ``Workflow.get_subclass_from_pk`` without saving this object in a new variable, since the information generated in the report may change
  and the user calling a ``get_report`` method of a class instantiated in the past will probably lose the most recent additions to the report.
  
As explained before, workflows will be hanlded by the daemon until the final step or until some error accours. In the last case, the workflow gets
halted and only the user can remove or kill the workflow through the interactive verdi shell. TODO
     
A more sophisticated workflow
+++++++++++++++++++++++++++++

In the simple example shown before we've been able to see almost all the workflow features, but nothing interesting happened. In this section we
show a more sophisticated example, where real calculations are performed and common real-life issues are solved. TODO

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
            
            kpoints = ParameterData(dict={
                            'type': 'automatic',
                            'points': [4, 4, 4, 0, 0, 0],
                            }).store()
            
            return kpoints
        
        def get_pw_calculation(self, pw_structure, pw_parameters, pw_kpoint):
            
            params = self.get_parameters()
            
            pw_codename            = params['pw_codename']
            num_machines           = params['num_machines']
            num_mpiprocs_per_machine   = params['num_mpiprocs_per_machine']
            max_wallclock_seconds  = params['max_wallclock_seconds']
            pseudo_family          = params['pseudo_family']
            
            code = Code.get(pw_codename)
            computer = code.get_remote_computer()
            
            QECalc = CalculationFactory('quantumespresso.pw')
            
            calc = QECalc(computer=computer)
            calc.set_max_wallclock_seconds(max_wallclock_seconds)
            calc.set_resources({"num_machines": num_machines, "num_mpiprocs_per_machine": num_mpiprocs_per_machine})
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
            import aiida.tools.physics as ps
            
            x_material   = self.get_parameter("x_material")
            a_sweep      = self.get_attribute("a_sweep")
            
            aiidalogger.info("Retrieving a_sweep as {0}".format(a_sweep))
            
            # Get calculations
            start_calcs = self.get_step_calculations(self.eos) #.get_calculations()
            
            #  Calculate results
            #-----------------------------------------
            
            e_calcs = [c.res.energy[-1] for c in start_calcs]
            v_calcs = [c.res.cell['volume'] for c in start_calcs]
            
            e_calcs = zip(*sorted(zip(a_sweep, e_calcs)))[1]
            v_calcs = zip(*sorted(zip(a_sweep, v_calcs)))[1]
            
            #  Add to report
            #-----------------------------------------
            for i in range (len(a_sweep)):
                self.append_to_report(x_material+"Ti03 simulated with a="+str(a_sweep[i])+", e="+str(e_calcs[i]))
            
            #  Find optimal alat
            #-----------------------------------------
            
            murnpars, ier = ps.Murnaghan_fit(e_calcs, v_calcs)
            
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
            
            x_material   = self.get_parameter("x_material")
            optimal_alat = self.get_attribute("optimal_alat")
            
            opt_calc = self.get_step_calculations(self.optimize) #.get_calculations()[0]
            opt_e = opt_calc.get_outputs(type=ParameterData)[0].get_dict()['energy'][-1]
            
            self.append_to_report(x_material+"Ti03 optimal with a="+str(optimal_alat)+", e="+str(opt_e))
            
            self.add_result("scf.converged", opt_calc)
                
            self.next(self.exit)



Chaining workflows
++++++++++++++++++

A final, an important feature of the workflow framework is the ability for a workflow to launch other workflows in every single step, allowing
the construction of complex experiments using modular and higly reusable atomic workflows. TODO

.. code-block:: python
  :linenos:

    ## ===============================================
    ##    WorkflowXTiO3
    ## ===============================================
    
    class WorkflowXTiO3(Workflow):
        
        def __init__(self,**kwargs):
            
            super(WorkflowXTiO3, self).__init__(**kwargs)
        
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
        
        ## ===============================================
        ##    Calculations generators
        ## ===============================================
        
        def get_ph_calculation(self, pw_calc, ph_parameters):
            
            params = self.get_parameters()
            
            ph_codename            = params['ph_codename']
            num_machines           = params['num_machines']
            num_mpiprocs_per_machine   = params['num_mpiprocs_per_machine']
            max_wallclock_seconds  = params['max_wallclock_seconds']
            
            code = Code.get(ph_codename)
            computer = code.get_remote_computer()
            
            QEPhCalc = CalculationFactory('quantumespresso.ph')
            calc = QEPhCalc(computer=computer)
            
            calc.set_max_wallclock_seconds(max_wallclock_seconds) # 30 min
            calc.set_resources({"num_machines": num_machines, "num_mpiprocs_per_machine": num_mpiprocs_per_machine})
            calc.store()
            
            calc.use_parameters(ph_parameters)
            calc.use_code(code)
            calc.set_parent_calc(pw_calc)
            
            return calc
        
        ## ===============================================
        ##    Wf steps
        ## ===============================================
        
        @Workflow.step
        def start(self):
            
            params = self.get_parameters()
            elements_alat = [('Ba',4.0),('Sr', 3.89), ('Pb', 3.9)]
            #elements_alat = [('Ba',4.0)]
            
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
                dm = c.get_outputs(type=ParameterData)[0].get_dict()['dynamical_matrix_1']
                self.append_to_report("Point q: {0} Frequencies: {1}".format(dm['q_point'],dm['frequencies']))
            
            self.next(self.exit)
        
