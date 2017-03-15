.. _my-ref-to-ph-tutorial:

Phonon
======

.. toctree::
   :maxdepth: 2
   
In this chapter will get you through the launching of a phonon calculation with Quantum Espresso, with ``ph.x``, a density functional perturbation theory code.
For this tutorial, it is required that you managed to launch the ``pw.x`` calculation, which is at the base of the phonon code; and of course it is assumed that you already know how to use the QE code.

The input of a phonon calculation can be actually simple, the only care that has to be taken, is to point to the same scratch of the previous pw calculation.
Here we will try to compute the dynamical matrix on a mesh of points (actually consisting of a 1x1x1 mesh for brevity). 
The input file that we should create is more or less this one::

  AiiDA calculation
  &INPUTPH
     epsil = .true.
     fildyn = 'DYN_MAT/dynamical-matrix-'
     iverbosity = 1
     ldisp = .true.
     nq1 = 1
     nq2 = 1
     nq3 = 1
     outdir = './out/'
     prefix = 'aiida'
     tr2_ph =   1.0000000000d-08
  /



Walkthrough
-----------

This input is much simpler than the previous PWscf work, here the only novel thing you will have to learn is how to set a parent calculation.

As before, we write a script step-by-step.

We first load a couple of useful modules that you already met in the previous tutorial, and load the database settings::

    #!/usr/bin/env python
    from aiida import load_dbenv
    load_dbenv()

    from aiida.orm import Code
    from aiida.orm import CalculationFactory, DataFactory



So, you were able to launch previously a ``pw.x`` calculation. 

Code
----

Again, you need to have compiled the code on the cluster and configured a new code ``ph.x`` in AiiDA in the very same way you installed ``pw.x`` (see ....).
Then we load the ``Code`` class-instance from the database::

    codename = 'my-ph.x'
    code = Code.get_from_string(codename)

Parameter
---------

Just like the *PWscf* calculation, here we load the class ParameterData and we instanciate it in parameters.
Again, ``ParameterData`` will simply represent a nested dictionary in the database, namelists at the first level, and then variables and values.
But this time of course, we need to use the variables of *PHonon*!

::

    ParameterData = DataFactory('parameter')
    parameters = ParameterData(dict={
		'INPUTPH': {
		    'tr2_ph' : 1.0e-8,
		    'epsil' : True,
		    'ldisp' : True,
		    'nq1' : 1,
		    'nq2' : 1,
		    'nq3' : 1,
		    }})

Calculation
-----------

Now we create the object PH-calculation.
As for ``pw.x``, we simply do::

    calc = code.new_calc()
    
and we set the parameters of the scheduler
(and just like the PWscf, this is a configuration valid
for the PBSpro and slurm schedulers only, see :ref:`my-reference-to-scheduler`).
    
::
    
    calc.set_max_wallclock_seconds(30*60) # 30 min
    calc.set_resources({"num_machines": 1})

We then tell the calculation to use the code and the parameters that we prepared above::

    calc.use_parameters(parameters)

Parent calculation
------------------

The phonon calculation needs to know on which PWscf do the perturbation theory calculation.
From the database point of view, it means that the ``PHonon`` calculation
is always a child of a ``PWscf``.
In practice, this means that when you want to impose this relationship,
you decided to take the input parameters of the parent PWscf calculation,
take its charge density and use them in the phonon run.
That's way we need to set the parent calculation.

You first need to remember the ID of the parent calculation that you launched
before (let's say it's #6): so that you can load the class of *a*
QE-PWscf calculation (with the CalculationFactory),
and load the object that represent *the* QE-PWscf calculation with ID #6::

    from aiida.orm import CalculationFactory
    PwCalculation = CalculationFactory('quantumespresso.pw')
    parent_id = 6
    parentcalc = load_node(parent_id)

Now that we loaded the parent calculation, we can set the phonon calc to
inherit the right information from it::
    
    calc.use_parent_calculation( parentcalc )

Note that in our database schema relations between two calculation
objects are prohibited. The link between the two is indirect and is
mediated by a third Data object, which represent the scratch folder
on the remote cluster. Therefore the relation between the parent Pw
and the child Ph appears like: Pw -> remotescratch -> Ph.

Execution
---------

Now, everything is ready, and just like PWscf, you just need to store all the
nodes and submit this input to AiiDA, and the calculation will launch!

::

    calc.store_all()
    calc.submit()

Script to execute
-----------------

This is the script described in the tutorial above. You can use it, just
remember to customize it using the right parent_id,
the code, and the proper scheduler info.

::

    #!/usr/bin/env python
    from aiida import load_dbenv
    load_dbenv()

    from aiida.orm import Code
    from aiida.orm import CalculationFactory, DataFactory

    #####################
    # ADAPT TO YOUR NEEDS
    parent_id = 6
    codename = 'my-ph.x'
    #####################

    code = Code.get_from_string(codename)

    ParameterData = DataFactory('parameter')
    parameters = ParameterData(dict={
		'INPUTPH': {
		    'tr2_ph' : 1.0e-8,
		    'epsil' : True,
		    'ldisp' : True,
		    'nq1' : 1,
		    'nq2' : 1,
		    'nq3' : 1,
		    }})

    QEPwCalc = CalculationFactory('quantumespresso.pw')
    parentcalc = load_node(parent_id)

    calc = code.new_calc()
    calc.set_max_wallclock_seconds(30*60) # 30 min
    calc.set_resources({"num_machines": 1})

    calc.use_parameters(parameters)
    calc.use_code(code)
    calc.use_parent_calculation(parentcalc)

    calc.store_all()
    print "created calculation with PK={}".format(calc.pk)
    calc.submit()

Exception tolerant code
-----------------------
You can find a more sophisticated example, that checks the possible exceptions
and prints nice error messages inside your AiiDA folder, under
``examples/submission/quantumespresso/test_ph.py``.

 
