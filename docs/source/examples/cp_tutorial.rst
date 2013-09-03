.. _my-ref-to-cp-tutorial:

Quantum Espresso Car-Parrinello user-tutorial
=============================================

.. toctree::
   :maxdepth: 2
   
This chapter will teach you how to set up a Car-Parrinello (CP) calculation as implemented in the Quantum Espresso distribution.
It is recommended that you first learn how to launch a PWscf calculation before proceeding in this tutorial (see :ref:`my-ref-to-cp-tutorial`).
Again, AiiDA is not meant to teach you how to use a Quantum-Espresso code, it is assumed that you already know CP.

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

You can immediately see that the structure of this input file closely resembles that of the PWscf: only some variables are different.



Walkthrough
-----------

From a more abstract point of view, we need to setup an input that is (structurally) the same of a PWscf run. We need:

1) an input structure,

2) pseudopotential files,

3) parameters.

Actually, it is a bit simpler, since there is no need for k-points.

Therefore, let's start writing the AiiDA submission script.

First we need to load the database and a couple of usual utilities::

  #!/usr/bin/env python
  from aiida.common.utils import load_django
  load_django()
  from aiida.orm import Code
  from aiida.orm import CalculationFactory, DataFactory

Then we start loading everything piece by piece.
We start by loading the code::

  codename = 'my_cp'
  code = Code.get(codename)

We setup the BaTiO3 structure. We first load the class, then create an instance ``s`` of it, to which we assign cell shape and atomic positions. Then we store it in the database.

::

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
  s.store()

We now set the parameters of the calculation: therefore we first load the class ParameterData, and then create an instance ``parameter``.
ParameterData will accept in input a nested dictionary: at the first level the name of the namelists, then the couples variables - values of it. Then we store the the object in the database.

::

  ParameterData = DataFactory('parameter')
  parameters = ParameterData({
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

Now we can load the computer form the code::

  computer = code.get_remote_computer()

we get the class describing a CP calculation::

  QECalc = CalculationFactory('quantumespresso.cp')

And create its instance::
  
  calc = QECalc(computer=computer)

We set the parameters for the scheduler (note that it will depend on the details of your scheduler, this configuration works for PBSpro and Slurm schedulers)::

  calc.set_max_wallclock_seconds(30*60) # 30 min
  calc.set_resources(num_machines=1, num_cpus_per_machine=16)

We save the object in the database::

  calc.store()

And we impose the input data to the calculation, (and therefore set the links in the database)::

  calc.use_structure(s)
  calc.use_code(code)
  calc.use_parameters(parameters)
  
If you have installed a pseudopotential family (see :ref:`my-ref-to-pseudo-tutorial`), then setting the pseudopotentials for this calculation is extremely easy, there's a function for that::
  
  pseudo_family = 'lda_pslib'
  calc.use_pseudo_from_family(pseudo_family)

Now, everything is ready to be submitted::

  calc.submit()

And now, the calculation will be executed and saved in the database automatically.












Script to execute
-----------------

This is the script described in the tutorial above. Remember to check the scheduler parameters, the pseudopotential family, and the codename before using it.

::

	#!/usr/bin/env python
	from aiida.common.utils import load_django
	load_django()

	from aiida.orm import Code
	from aiida.orm import CalculationFactory, DataFactory
	from aiida.djsite.db.models import Group
	UpfData = DataFactory('upf')
	ParameterData = DataFactory('parameter')
	StructureData = DataFactory('structure')

	codename = 'my_cp'
	code = Code.get(codename)

	# BaTiO3 cubic structure
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
	s.store()

	parameters = ParameterData({
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
				
	computer = code.get_remote_computer()
	QECalc = CalculationFactory('quantumespresso.cp')
	calc = QECalc(computer=computer)
	calc.set_max_wallclock_seconds(30*60) # 30 min
	calc.set_resources(num_machines=1, num_cpus_per_machine=16)
	calc.store()

	calc.use_structure(s)
	calc.use_code(code)
	calc.use_parameters(parameters)
	pseudo_family = 'lda_pslib'
	calc.use_pseudo_from_family(pseudo_family)

	calc.submit()




For a more fault tolerant script, that also allows to load the pseudopotentials from a subfolder 'data', you can use the one here below.
Again, remember to check and modify to your needs the au

::

	#!/usr/bin/env python
	import sys
	import os

	from aiida.common.utils import load_django
	load_django()

	from aiida.common.exceptions import NotExistent

	from aiida.orm import Code
	from aiida.orm import CalculationFactory, DataFactory
	from aiida.djsite.db.models import Group
	UpfData = DataFactory('upf')
	ParameterData = DataFactory('parameter')
	StructureData = DataFactory('structure')

	try:
		codename = sys.argv[1]
	except IndexError:
		codename = None

	expected_exec_name='cp.x'
	auto_pseudos = True

	num_cpus_per_machine = 16
	
	queue = None

	try:
		if codename is None:
			raise ValueError
		code = Code.get(codename)
		if not code.get_remote_exec_path().endswith(expected_exec_name):
			raise ValueError
	except (NotExistent, ValueError):
		valid_code_labels = [c.label for c in Code.query(
				attributes__key="_remote_exec_path",
				attributes__tval__endswith="/{}".format(expected_exec_name))]
		if valid_code_labels:
			print >> sys.stderr, "Pass as first parameter a valid code label."
			print >> sys.stderr, "Valid labels with a {} executable are:".format(expected_exec_name)
			for l in valid_code_labels:
				print >> sys.stderr, "*", l
		else:
			print >> sys.stderr, "Code not valid, and no valid codes for {}. Configure at least one first using".format(expected_exec_name)
			print >> sys.stderr, "    verdi code setup"
		sys.exit(1)

	if auto_pseudos:
		valid_pseudo_groups = Group.objects.filter(dbnodes__type__contains='.upf.').distinct().values_list('name',flat=True)

		try:
			pseudo_family = sys.argv[2]
		except IndexError:
			print >> sys.stderr, "Error, auto_pseudos set to True. You therefore need to pass as second parameter"
			print >> sys.stderr, "the pseudo family name."
			print >> sys.stderr, "Valid groups containing at least one UPFData object are:"
			print >> sys.stderr, "\n".join("* {}".format(i) for i in valid_pseudo_groups)
			sys.exit(1)
		

		if not Group.objects.filter(name=pseudo_family):
			print >> sys.stderr, "auto_pseudos is set to True and pseudo_family='{}',".format(pseudo_family)
			print >> sys.stderr, "but no group with such a name found in the DB."
			print >> sys.stderr, "Valid groups containing at least one UPFData object are:"
			print >> sys.stderr, ",".join(valid_pseudo_groups)
			sys.exit(1)


	alat = 4. # angstrom
	cell = [[alat, 0., 0.,],
			[0., alat, 0.,],
			[0., 0., alat,],
		   ]

	# BaTiO3 cubic structure
	s = StructureData(cell=cell)
	s.append_atom(position=(0.,0.,0.),symbols=['Ba'])
	s.append_atom(position=(alat/2.,alat/2.,alat/2.),symbols=['Ti'])
	s.append_atom(position=(alat/2.,alat/2.,0.),symbols=['O'])
	s.append_atom(position=(alat/2.,0.,alat/2.),symbols=['O'])
	s.append_atom(position=(0.,alat/2.,alat/2.),symbols=['O'])
	s.store()

	parameters = ParameterData({
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
				

	computer = code.get_remote_computer()

	QECalc = CalculationFactory('quantumespresso.cp')
	calc = QECalc(computer=computer)
	calc.set_max_wallclock_seconds(30*60) # 30 min
	calc.set_resources(num_machines=1, num_cpus_per_machine=num_cpus_per_machine)
	if queue is not None:
		calc.set_queue_name(queue)
	calc.store()
	print "created calculation; calc=Calculation(uuid='{}') # ID={}".format(
		calc.uuid,calc.dbnode.pk)

	calc.use_structure(s)
	calc.use_code(code)
	calc.use_parameters(parameters)

	if auto_pseudos:
		try:
			calc.use_pseudo_from_family(pseudo_family)
			print "Pseudos successfully loaded from family {}".format(pseudo_family)
		except NotExistent:
			print ("Pseudo or pseudo family not found. You may want to load the "
				   "pseudo family, or set auto_pseudos to False.")
			raise
	else:
		raw_pseudos = [
		   ("Ba.pbesol-spn-rrkjus_psl.0.2.3-tot-pslib030.UPF", 'Ba', 'pbesol'),
		   ("Ti.pbesol-spn-rrkjus_psl.0.2.3-tot-pslib030.UPF", 'Ti', 'pbesol'),
		   ("O.pbesol-n-rrkjus_psl.0.1-tested-pslib030.UPF", 'O', 'pbesol')]

		pseudos_to_use = {}
		for fname, elem, pot_type in raw_pseudos:
			absname = os.path.realpath(os.path.join(os.path.dirname(__file__),
													"data",fname))
			pseudo, created = UpfData.get_or_create(
				absname,use_first=True)
			if created:
				print "Created the pseudo for {}".format(elem)
			else:
				print "Using the pseudo for {} from DB: {}".format(elem,pseudo.pk)
			pseudos_to_use[elem] = pseudo

		for k, v in pseudos_to_use.iteritems():
			calc.use_pseudo(v, kind=k)


	calc.submit()
	print "submitted calculation; calc=Calculation(uuid='{}') # ID={}".format(
		calc.uuid,calc.dbnode.pk)

