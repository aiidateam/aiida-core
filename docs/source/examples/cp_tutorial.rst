.. _my-ref-to-cp-tutorial:

Car-Parrinello
==============

.. toctree::
   :maxdepth: 2
   
This chapter will teach you how to set up a Car-Parrinello (CP)
calculation as implemented in the Quantum Espresso distribution.
Again, AiiDA is not meant to teach you how to use a Quantum-Espresso code,
it is assumed that you already know CP.

It is recommended that you first learn how to launch a PWscf calculation
before proceeding in this tutorial (see :ref:`my-ref-to-pw-tutorial`), since
here we will only emphasize the differences with respect to launching a PW 
calculation.

We want to setup a CP run of a 5 atom cell of BaTiO3.
The input file that we should create is more or less this one::

  &CONTROL
    calculation = 'cp'
    dt =   3.0000000000d+00
    iprint = 1
    isave = 100
    max_seconds = 1500
    ndr = 50
    ndw = 50
    nstep = 10
    outdir = './out/'
    prefix = 'aiida'
    pseudo_dir = './pseudo/'
    restart_mode = 'from_scratch'
    verbosity = 'high'
    wf_collect = .false.
  /
  &SYSTEM
    ecutrho =   2.4000000000d+02
    ecutwfc =   3.0000000000d+01
    ibrav = 0
    nat = 5
    nr1b = 24
    nr2b = 24
    nr3b = 24
    ntyp = 3
  /
  &ELECTRONS
    electron_damping =   1.0000000000d-01
    electron_dynamics = 'damp'
    emass =   4.0000000000d+02
    emass_cutoff =   3.0000000000d+00
  /
  &IONS
    ion_dynamics = 'none'
  /
  ATOMIC_SPECIES
  Ba     137.33 Ba.pbesol-spn-rrkjus_psl.0.2.3-tot-pslib030.UPF
  Ti     47.88 Ti.pbesol-spn-rrkjus_psl.0.2.3-tot-pslib030.UPF
  O      15.9994 O.pbesol-n-rrkjus_psl.0.1-tested-pslib030.UPF
  ATOMIC_POSITIONS angstrom
  Ba           0.0000000000       0.0000000000       0.0000000000 
  Ti           2.0000000000       2.0000000000       2.0000000000 
  O            2.0000000000       2.0000000000       0.0000000000 
  O            2.0000000000       0.0000000000       2.0000000000 
  O            0.0000000000       2.0000000000       2.0000000000 
  CELL_PARAMETERS angstrom
	  4.0000000000       0.0000000000       0.0000000000
	  0.0000000000       4.0000000000       0.0000000000
	  0.0000000000       0.0000000000       4.0000000000

You can immediately see that the structure of this input file closely
resembles that of the PWscf: only some variables are different.

Walkthrough
-----------

Everything works like the PW calculation: you need to get the code from
the database::

  codename = 'my_cp'
  code = Code.get_from_string(codename)

Then create the StructureData with the structure, and a ParameterData 
node for the inputs. This time, of course, you have to specify the correct
variables for a ``cp.x`` calculation::

  StructureData = DataFactory('structure')
  alat = 4. # angstrom
  cell = [[alat, 0., 0.,],
          [0., alat, 0.,],
          [0., 0., alat,],
         ]
  s = StructureData(cell=cell)
  s.append_atom(position=(0.,0.,0.),symbols=['Ba'])
  s.append_atom(position=(alat/2.,alat/2.,alat/2.),symbols=['Ti'])
  s.append_atom(position=(alat/2.,alat/2.,0.),symbols=['O'])
  s.append_atom(position=(alat/2.,0.,alat/2.),symbols=['O'])
  s.append_atom(position=(0.,alat/2.,alat/2.),symbols=['O'])

  ParameterData = DataFactory('parameter')
  parameters = ParameterData(dict={
            'CONTROL': {
                'calculation': 'cp',
                'restart_mode': 'from_scratch',
                'wf_collect': False,
                'iprint': 1,
                'isave': 100,
                'dt': 3.,
                'max_seconds': 25*60,
                'nstep': 10,
                },
            'SYSTEM': {
                'ecutwfc': 30.,
                'ecutrho': 240.,
                'nr1b': 24,
                'nr2b': 24,
                'nr3b': 24,
                },
            'ELECTRONS': {
                'electron_damping': 1.e-1,
                'electron_dynamics': 'damp', 
                'emass': 400.,
                'emass_cutoff': 3.,
                },
            'IONS': {
                'ion_dynamics': 'none',
            }}).store()

We then create a new calculation with the proper settings::
  
  calc = code.new_calc()
  calc.set_max_wallclock_seconds(30*60) # 30 min
  calc.set_resources({"num_machines": 1, "num_mpiprocs_per_machine": 16})

And we link the input data to the calculation
(and therefore set the links in the database). The main difference
here is that CP does not support k-points, so you should not (and cannot)
link any kpoint as input::

  calc.use_structure(s)
  calc.use_code(code)
  calc.use_parameters(parameters)
  
Finally, load the proper pseudopotentials using
e.g. a pseudopotential family (see :ref:`my-ref-to-pseudo-tutorial`)::
  
  pseudo_family = 'lda_pslib'
  calc.use_pseudos_from_family(pseudo_family)

and store everything and submit::

  calc.store_all()
  calc.submit()

And now, the calculation will be executed and saved in the database automatically.


Exception tolerant code
-----------------------
You can find a more sophisticated example, that checks the possible exceptions
and prints nice error messages inside your AiiDA folder, under
``examples/submission/quantumespresso/test_cp.py``.
