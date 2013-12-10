.. _my-ref-to-pw-tutorial:

Quantum Espresso PWscf user-tutorial
====================================

.. toctree::
   :maxdepth: 2
   
This chapter will show how to launch a single PWscf (``pw.x``) calculation. It is assumed that you have already performed the installation, and that you already setup a computer (with ``verdi``), installed Quantum Espresso on the cluster and in AiiDA. Although the code could be quite readable, a basic knowledge of Python and object programming is useful.

Your classic pw.x input file
----------------------------

This is the input file of Quantum Espresso that we will try to execute. It consists in the total energy calculation of a 5 atom cubic cell of BaTiO3. Note also that AiiDA is a tool to use other codes: if the following input is not clear to you, please refer to the Quantum Espresso Documentation.

::

    &CONTROL
      calculation = 'scf'
      outdir = './out/'
      prefix = 'aiida'
      pseudo_dir = './pseudo/'
      restart_mode = 'from_scratch'
      verbosity = 'high'
      wf_collect = .true.
    /
    &SYSTEM
      ecutrho =   2.4000000000d+02
      ecutwfc =   3.0000000000d+01
      ibrav = 0
      nat = 5
      ntyp = 3
    /
    &ELECTRONS
      conv_thr =   1.0000000000d-06
    /
    ATOMIC_SPECIES
    Ba     137.33    Ba.pbesol-spn-rrkjus_psl.0.2.3-tot-pslib030.UPF
    Ti     47.88     Ti.pbesol-spn-rrkjus_psl.0.2.3-tot-pslib030.UPF
    O      15.9994   O.pbesol-n-rrkjus_psl.0.1-tested-pslib030.UPF
    ATOMIC_POSITIONS angstrom
    Ba           0.0000000000       0.0000000000       0.0000000000 
    Ti           2.0000000000       2.0000000000       2.0000000000 
    O            2.0000000000       2.0000000000       0.0000000000 
    O            2.0000000000       0.0000000000       2.0000000000 
    O            0.0000000000       2.0000000000       2.0000000000 
    K_POINTS automatic
    4 4 4 0 0 0
    CELL_PARAMETERS angstrom
          4.0000000000       0.0000000000       0.0000000000
          0.0000000000       4.0000000000       0.0000000000
          0.0000000000       0.0000000000       4.0000000000

In the old way, not only you had to prepare 'manually' this file, but also prepare the scheduler submission script, send everything on the cluster, etc.
We are going instead to prepare everything in a more programmatic way.

Quantum Espresso Pw Walkthrough
-------------------------------

We've got to prepare a script to submit a job to your local installation of AiiDA.
This example will be a rather long script: in fact there is still nothing in your database, so that we will have to load everything, like the pseudopotential files and the structure.
In a more practical situation, you might load data from the database and perform small modification to re-use it.

Let's say that through the ``verdi`` command you have already installed a cluster, say ``TheHive``, and that you also compiled Quantum Espresso on the cluster, and installed the code pw.x with ``verdi``, that we will call ``pw_on_TheHive``.

Let's start writing the python script.
First of all, we need to load the configuration concerning your particular installation, in particular, the details of your database installation::

  #!/usr/bin/env python
  import sys
  import os

  from aiida.common.utils import load_django
  load_django()

Code
----

Now we have to select the code. Note that in AiiDA the object 'code' in the database is meant to represent a specific compilation of a code. This means that if you install Quantum Espresso (QE) on two computers A and B, you will need to have two different 'codes' in the database (although the source of the code is the same, the binary file is different).

If you setup the code ``pw_on_TheHive`` correctly, then it is sufficient to write::

  codename = 'pw_on_TheHive'
  from aiida.orm import Code
  code = Code.get(codename)

Where in the last line we just load the database object representing the code.

This is not a exception tolerant code: there are so many errors that could happen when trying to load this code... 
It is not strictly necessary, but we can rewrite this part, so that we 

1) load the codename from the command line, 

2) check if the codename is a valid string, 

3) if we find a code, check that it is a pw.x file, as you should have from a standard QE distribution, 

4) if exceptions are raised, try to interpret them and then stop smoothly.

::

  expected_exec_name='pw.x'
  try:
      codename = sys.argv[1]
  except IndexError:
      codename = None

  from aiida.orm import Code
  from aiida.common.exceptions import NotExistent
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

It's a bit longer, but it will respond more gently to errors!

Structure
---------

We now proceed in setting up the structure. 
There are two ways to do that in AiiDA, a first one is to use the AiiDA Structure, which we will explain in the following; the second choice is the `Atomic Simulation Environment (ASE) <http://wiki.fysik.dtu.dk/ase/>`_ which provides excellent tools to manipulate structures (the ASE Atoms object needs to be converted into an AiiDA Structure, see the note at the end of the section).

We first have to load the abstract object class that describes a structure. 
We do it in the following way: we load the DataFactory, which is a tool to load the classes by their name, and then call StructureData the abstract class that we loaded. 
(NB: it's not yet a class instance!) 
(If you are not familiar with the terminology of object programming, we could take `Wikipedia <http://en.wikipedia.org/wiki/Object_(computer_science)>`_ and see their short explanation: in common speech that one refers to *a* file as a class, while *the* file is the object or the class instance. In other words, the class is our definition of the object Structure, while its instance is what will be saved as an object in the database)::

  from aiida.orm import DataFactory
  StructureData = DataFactory('structure')

We define the cell with a 3x3 matrix (we choose the convention where each ROW represents a lattice vector), which in this case is just a cube of size 4 Angstroms::

  alat = 4. # angstrom
  cell = [[alat, 0., 0.,],
          [0., alat, 0.,],
          [0., 0., alat,],
         ]

Now, we create the StructureData instance, assigning immediatly the cell. 
Then, we append to the empty crystal cell the atoms, specifying their element name and their positions::

  # BaTiO3 cubic structure
  s = StructureData(cell=cell)
  s.append_atom(position=(0.,0.,0.),symbols='Ba')
  s.append_atom(position=(alat/2.,alat/2.,alat/2.),symbols='Ti')
  s.append_atom(position=(alat/2.,alat/2.,0.),symbols='O')
  s.append_atom(position=(alat/2.,0.,alat/2.),symbols='O')
  s.append_atom(position=(0.,alat/2.,alat/2.),symbols='O')
  s.store()

To see more methods associated to the class StructureData, look at the :ref:`my-ref-to-structure` documentation.
Note also last line: with the method store(), we saved the instance of the structure in the database.
It is also fundamental for later use: the calculation that will use this structure, will need to find it in the database.

For an extended tutorial about the creation of Structure objects, check :doc:`this tutorial <../examples/structure_tutorial>`.

.. note:: AiiDA supports also ASE structures. Once you created your structure with ASE, in an object instance called say ``ase_s``, you can straightforwardly use it to create the AiiDA StructureData, as ``s = StructureData(ase=ase_s)`` and then save it ``s.store()``.

Parameters
----------

Now we need to provide also the parameters of a Quantum Espresso calculation, like saying that we need a certain cutoff for the wfc, some convergence threshold, etc...
The Quantum Espresso Pw plugin requires to pass this information with the object ParameterData.
This object is more or less the representation of a Python dictionary in the database.
We first load the class through the DataFactory, just like we did for the Structure.
Then we create the instance of the object ``parameter`` and we store it in the DB.
To represent closely the structure of the QE input file, ParameterData is a nested dictionary, at the first level the namelists, and then the variables with their values.
Note also that numbers and booleans are written in Python, i.e. not ``.false.`` but ``False``!.
::

  ParameterData = DataFactory('parameter')

  parameters = ParameterData({
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

( The experienced QE user will have noticed also that a couple of variables are missing: the prefix, the pseudo directory and the scratch directory are reserved to the plugin which will use default values: in case you want to use the scratch of a previous calculation, it must be specified)
The k-points have to be saved in a different ParameterData, analogously as before::
                
  kpoints = ParameterData({
                'type': 'automatic',
                'points': [4, 4, 4, 0, 0, 0],
                }).store()

As a further generic comments, this is specific to the way the plugin for Quantum Espresso works.
Other codes may need more than 2 ParameterData, or even none of them.
And also how this parameters have to be written depends on the plugin.
This is just the scheme that we decided for the Quantum Espresso codes.




Calculation
-----------

Now we proceed to set up the calculation.
We first get the object representing the computer: since it is uniquely identified by the code, there is a practical method to load the computer from the code directly.

::

  computer = code.get_remote_computer()

Then, we load the abstract class QECalc with the CalculationFactory function (that loads the class defined inside the module quantumespresso.pw), and we create an instance ``calc`` of it, assigning immediately the computer on which it will be executed.

::

  from aiida.orm import CalculationFactory
  QECalc = CalculationFactory('quantumespresso.pw')
  calc = QECalc(computer=computer)

We have to specify the details required by the scheduler.
For example, on a slurm or pbs scheduler, we have to specify the number of nodes (``num_machines``), the number of cpus per node (``num_cpus_per_machine``), the job walltime, the queue name (if desired).
For the complete scheduler documentation, see :ref:`my-reference-to-scheduler`

::

  queue = None
  calc.set_max_wallclock_seconds(30*60) # 30 min
  num_cpus_per_machine = 48
  calc.set_resources(num_machines=1, num_cpus_per_machine=num_cpus_per_machine)
  queue = None
  if queue is not None:
      calc.set_queue_name(queue)

If we are satisfied with the configuration on the cluster, we can store the calculation in the database. 
Note that after storing it, it will not be possible to modify it (Nor you should: you risk of compromizing the integrity of the database)!

::

  calc.store()

And we can also print on the screen some useful information, like the calculation uuid (a unique identifier consisting in a random string) or id (a sequential integer).

::

  print "created calculation; with uuid='{}' and ID={}".format( calc.uuid,calc.dbnode.pk )

After the object calculation is stored in the database, we can tell the calculation to use the parameters that we prepared before::

  calc.use_structure(s)
  calc.use_code(code)
  calc.use_parameters(parameters)
  calc.use_kpoints(kpoints)

This operation must be done only after the calculation is stored in the database.
In fact, when you say ``calc.use_structure(s)``, you are trying to put an arrow inside the database, representing the input *structure* given to the *calculation*: you cannot put an arrow from A to B if they are not there!




Pseudopotentials
----------------

There is only one missing piece of information, that is the pseudopotential files, one for each element of the structure.
We create a list of tuples, with element name and the pseudopotential file name::

    raw_pseudos = [
       ("Ba.pbesol-spn-rrkjus_psl.0.2.3-tot-pslib030.UPF", 'Ba'),
       ("Ti.pbesol-spn-rrkjus_psl.0.2.3-tot-pslib030.UPF", 'Ti'),
       ("O.pbesol-n-rrkjus_psl.0.1-tested-pslib030.UPF", 'O')]

Then, we loop over the filenames and
1) define the path to the pseudopotential file with ``absname``. Here we assume that in the folder where you executed the script, there is a subfolder called ``data``, with the files inside. (Note also that the working directory ``'.'`` is called with ``__file__`` and not with ``os.getcwd()``, since the software AiiDA runs in another folder)
2) tries to get an element from the database or create it if it doesn't exist yet
3) creates a dictionary, useful for later, with keys of atomic species, and for values the pseudopotential-objects (and not the file names).

::

    UpfData = DataFactory('upf')
    pseudos_to_use = {}

    for fname, elem in raw_pseudos:
        absname = os.path.realpath(os.path.join(os.path.dirname(__file__), "data",fname))
        pseudo, created = UpfData.get_or_create(absname,use_first=True)
        pseudos_to_use[elem] = pseudo

As the last step, we make a loop over the atomic species, and attach its pseudopotential object to the calculation::

    for k, v in pseudos_to_use.iteritems():
        calc.use_pseudo(v, kind=k)

In this example, we loaded the files directly from the hard disk. 
For a more practical use, it is convenient to use the pseudopotential families. Its use is documented in :ref:`my-ref-to-pseudo-tutorial`.
If you got one installed, you can simply tell the calculation to use the pseudopotential family, then AiiDA will take care of attaching the proper pseudopotential to the element::

  calc.use_pseudo_from_family('my_pseudo_family')






Execute
-------

Summarizing, we created all the inputs needed by a PW calculation, that are: parameters, kpoints, pseudopotential files and the structure. We then created the calculation, where we specified that it is a PW calculation and we specified the details of the remote cluster.
We stored all this objects in the database (``.store()``), and set the links between the inputs and the calculation (``calc.use_***``).
That's all that the calculation needs. 
Now we just need to submit it::

   calc.submit()

Everything else will be managed by AiiDA: the inputs will be checked to verify that it is consistent with a PW input. If the input is complete, the pw input file will be prepared and the folder where it will be executed. It will be sent on cluster, executed, retrieved and parsed.





If for example you want to check for the state of the calculation, you can execute a script like this one, where you just need to specify the id of the calculation under investigation (or use the uuid with ``.get_subclass_from_uuid()``, note that the id may change after a sync of two databases, while the uuid is a unique identifier)

::

  import paramiko

  from aiida.common.utils import load_django
  load_django()

  from aiida.orm import CalculationFactory

  QECalc = CalculationFactory('quantumespresso.pw')
  calc = QECalc.get_subclass_from_pk('...............')
  print calc.get_state()

The calculation could be in several states.
The most common you should see:

1. 'WITHSCHEDULER': the job is in queue on the cluster

2. 'RUNNING': in execution on the cluster

2. 'FINISHED': the job on the cluster was finished, AiiDA already retrieved it, and store the results in the database. Moreover, the Pw code seems to have ended without crashing

3. 'FAILED': something went wrong, and AiiDA rose an exception. This could be of several nature: the inputs weren't enough, the execution on the cluster failed, or the code ended without reaching te end successfully. In practice, anything bad that could happen.


Eventually, if the calculation is finished, you will find the computed quantities in the database.
You will be able to query the database for the energies that you computed!


Jump to :ref:`my-ref-to-ph-tutorial`.




Script: source code
-------------------

In this section you'll find two scripts that do what explained in the tutorial.
The compact is a script with a minimal configuration required
You can copy and paste it to start using it, executing as::

  python your_pw_codename pseudo_family_name

It requires to have one family of pseudopotentials configured.

You will also find a longer version, with more exception checks and with the possibility to load the pseudopotentials from hard disk.
Note that the configuration of the computer resources (like number of nodes and machines) is hardware and scheduler dependent. The configuration used below should work for a pbspro or slurm cluster, asking 1 node of 16 cpus.

Compact script
--------------

::

    #!/usr/bin/env python
    from aiida.common.utils import load_django
    load_django()
    from aiida.orm import Code
    from aiida.orm import CalculationFactory, DataFactory
    
    ParameterData = DataFactory('parameter')
    StructureData = DataFactory('structure')
    
    codename = 'your_pw.x'
    
    pseudo_family = 'lda_pslib'

    code = Code.get(codename)
    computer = code.get_remote_computer()

    # BaTiO3 cubic structure
    alat = 4. # angstrom
    cell = [[alat, 0., 0.,],
	    [0., alat, 0.,],
	    [0., 0., alat,],
	   ]
    s = StructureData(cell=cell)
    s.append_atom(position=(0.,0.,0.),symbols='Ba')
    s.append_atom(position=(alat/2.,alat/2.,alat/2.),symbols='Ti')
    s.append_atom(position=(alat/2.,alat/2.,0.),symbols='O')
    s.append_atom(position=(alat/2.,0.,alat/2.),symbols='O')
    s.append_atom(position=(0.,alat/2.,alat/2.),symbols='O')
    s.store()

    parameters = ParameterData({
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

    kpoints = ParameterData({
		    'type': 'automatic',
		    'points': [4, 4, 4, 0, 0, 0],
		    }).store()

    QECalc = CalculationFactory('quantumespresso.pw')
    calc = QECalc(computer=computer)
    calc.set_max_wallclock_seconds(30*60) # 30 min
    calc.set_resources(num_machines=1, num_cpus_per_machine=16)
    calc.store()

    calc.use_structure(s)
    calc.use_code(code)
    calc.use_parameters(parameters)
    calc.use_pseudo_from_family(pseudo_family)
    calc.use_kpoints(kpoints)

    calc.submit()






Exception tolerant code
-----------------------
::

    #!/usr/bin/env python
    import sys
    import os

    from aiida.common.utils import load_django
    load_django()

    from aiida.common import aiidalogger
    import logging
    from aiida.common.exceptions import NotExistent
    aiidalogger.setLevel(logging.INFO)

    from aiida.orm import Code
    from aiida.orm import CalculationFactory, DataFactory
    from aiida.djsite.db.models import Group
    UpfData = DataFactory('upf')
    ParameterData = DataFactory('parameter')
    StructureData = DataFactory('structure')

    ################################################################

    try:
	codename = sys.argv[1]
    except IndexError:
	codename = None

    # If True, load the pseudos from the family specified below
    # Otherwise, use static files provided
    expected_exec_name='pw.x'
    auto_pseudos = False

    queue = None
    #queue = "P_share_queue"

    #####

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


    computer = code.get_remote_computer()

    num_cpus_per_machine = 16


    alat = 4. # angstrom
    cell = [[alat, 0., 0.,],
	    [0., alat, 0.,],
	    [0., 0., alat,],
	   ]

    # BaTiO3 cubic structure
    s = StructureData(cell=cell)
    s.append_atom(position=(0.,0.,0.),symbols='Ba')
    s.append_atom(position=(alat/2.,alat/2.,alat/2.),symbols='Ti')
    s.append_atom(position=(alat/2.,alat/2.,0.),symbols='O')
    s.append_atom(position=(alat/2.,0.,alat/2.),symbols='O')
    s.append_atom(position=(0.,alat/2.,alat/2.),symbols='O')
    s.store()

    parameters = ParameterData({
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

    kpoints = ParameterData({
		    'type': 'automatic',
		    'points': [4, 4, 4, 0, 0, 0],
		    }).store()

    QECalc = CalculationFactory('quantumespresso.pw')
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

    calc.use_kpoints(kpoints)
    #calc.use_settings(settings)
    #from aiida.orm.data.remote import RemoteData
    #calc.set_outdir(remotedata)

    calc.submit()
    print "submitted calculation; calc=Calculation(uuid='{}') # ID={}".format(
	calc.uuid,calc.dbnode.pk)

