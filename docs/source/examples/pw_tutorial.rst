.. _my-ref-to-pw-tutorial:

PWscf
=====

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
In a more practical situation, you might load data from the database and perform a small modification to re-use it.

Let's say that through the ``verdi`` command you have already installed
a cluster, say ``TheHive``, and that you also compiled Quantum Espresso
on the cluster, and installed the code pw.x with ``verdi`` with label ``pw-5.1``
for instance, so that in the rest of this tutorial we will reference to the
code as ``pw-5.1@TheHive``.

Let's start writing the python script.
First of all, we need to load the configuration concerning your
particular installation, in particular, the details of your database installation::

  #!/usr/bin/env python
  from aiida import load_dbenv
  load_dbenv()

Code
----

Now we have to select the code. Note that in AiiDA the object 'code' in the
database is meant to represent a specific executable, i.e. a given
compiled version of a code.
This means that if you install Quantum Espresso (QE) on two computers A and B,
you will need to have two different 'codes' in the database
(although the source of the code is the same, the binary file is different).

If you setup the code ``pw-5.1`` on machine ``TheHive`` correctly, then it is
sufficient to write::

  codename = 'pw-5.1@TheHive'
  from aiida.orm import Code
  code = Code.get_from_string(codename)

Where in the last line we just load the database object representing the code.

.. note:: the ``.get_from_string()`` method is just a helper method for user
  convenience, but there are some weird cases that cannot be dealt in a
  simple way (duplicated labels, code names
  that are an integer number, code names containing the '@' symbol, ...: try
  to not do this! This is not an error, but does not allow to use the
  ``.get_from_string()`` method to get those calculations). 
  In this case, you can use directly the ``.get()`` method, for instance::
  
    code = Code.get(label='pw-5.1', machinename='TheHive')

  or even more generally get the code from its (integer) PK::
    
    code = load_node(PK)

Structure
---------

We now proceed in setting up the structure. 

.. note:: Here we discuss only the main features of structures in AiiDA, needed
    to run a Quantum ESPRESSO PW calculation.
     
    For more detailed information, give a look to the 
    :ref:`structure_tutorial`.

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

Now, we create the StructureData instance, assigning immediately the cell. 
Then, we append to the empty crystal cell the atoms, specifying their element name and their positions::

  # BaTiO3 cubic structure
  s = StructureData(cell=cell)
  s.append_atom(position=(0.,0.,0.),symbols='Ba')
  s.append_atom(position=(alat/2.,alat/2.,alat/2.),symbols='Ti')
  s.append_atom(position=(alat/2.,alat/2.,0.),symbols='O')
  s.append_atom(position=(alat/2.,0.,alat/2.),symbols='O')
  s.append_atom(position=(0.,alat/2.,alat/2.),symbols='O')

To see more methods associated to the class StructureData, look at the :ref:`my-ref-to-structure` documentation.

.. note:: When you create a node (in this case a ``StructureData`` node) as 
  described above, you are just creating it in the computer memory, and not 
  in the database. This is particularly useful to run tests without filling
  the AiiDA database with garbage.
  
  You will see how to store all the nodes in one shot toward the end of this
  tutorial; if, however, you want to directly store the structure in the
  database for later use, you can just call the ``store()`` method of the Node::
  
    s.store()
    
For an extended tutorial about the creation of Structure objects,
check :doc:`this tutorial <../examples/structure_tutorial>`.

.. note:: AiiDA supports also ASE structures. Once you created your structure
  with ASE, in an object instance called say ``ase_s``, you can
  straightforwardly use it to create the AiiDA StructureData, as::

    s = StructureData(ase=ase_s)

  and then save it ``s.store()``.

Parameters
----------

Now we need to provide also the parameters of a Quantum Espresso calculation,
like the cutoff for the wavefunctions, some convergence threshold, etc...
The Quantum ESPRESSO pw.x plugin requires to pass this information within a
ParameterData object, that is a specific AiiDA data node that can store a
dictionary (even nested) of basic data types: integers, floats, strings, lists,
dates, ...
We first load the class through the DataFactory, just like we did for the Structure.
Then we create the instance of the object ``parameter``.
To represent closely the structure of the QE input file,
ParameterData is a nested dictionary, at the first level the namelists
(capitalized), and then the variables with their values (in lower case).

Note also that numbers and booleans are written in Python, i.e. ``False`` and
not the Fortran string ``.false.``!
::

  ParameterData = DataFactory('parameter')

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
                }})

.. note:: also in this case, we chose not to store the ``parameters`` node.
  If we wanted, we could even have done it in a single line::
    
    parameters = ParameterData(dict={...}).store()

The experienced QE user will have noticed also that a couple of variables
are missing: the prefix, the pseudo directory and the scratch directory are
reserved to the plugin which will use default values, and there are specific
AiiDA methods to restart from a previous calculation.

Input parameters validation
///////////////////////////
The dictionary provided above is the standard format for storing the inputs
of Quantum ESPRESSO pw.x in the database. It is important to store the inputs
of different calculations in a consistent way because otherwise later querying
becomes impossible (e.g. if different units are used for the same flags,
if the same input is provided in different formats, ...).

In the PW input plugin, we provide a function that will help you in
both validating the input, and creating the input in the expected format 
without remembering in which namelists the keywords are located.

You can access this function as follows. First, you define the input dictionary::

  test_dict = {
            'CONTROL': {
                'calculation': 'scf',
                },
            'SYSTEM': {
                'ecutwfc': 30.,
                },
            'ELECTRONS': {
                'conv_thr': 1.e-6,
                }}

Then, you can verify if the input is correct by using the 
:py:func:`~aiida.orm.calculation.job.quantumespresso.helpers.pw_input_helper` function, 
conveniently exposes also as a ``input_helper`` class method of the ``PwCalculation`` class::

  resdict = CalculationFactory('quantumespresso.pw').input_helper(test_dict, structure=s)

If the input is invalid, the function will raise a ``InputValidationError``
exception, and the error message will have a verbose explanation of the possible
errors, and in many cases it will suggest how to fix them. Otherwise, in ``resdict``
you will find the same dictionary you passed in input, potentially slightly modified
to fix some small mistakes (e.g., if you pass an integer value where a float is expected,
the type will be converted). You can then use the output for the input ParameterData node::

  parameters = ParameterData(dict=resdict)

As an example, if you pass an incorrect input, e.g. the following where we have introduced 
a few errors::

  test_dict = {
            'CONTROL': {
                'calculation': 'scf',
                },
            'SYSTEM': {
                'ecutwfc': 30.,
		'cosab': 10.,
		'nosym': 1,
                },
            'ELECTRONS': {
                'convthr': 1.e-6,
                'ecutrho': 100.
                }}

After running the ``input_helper`` method, you will get an exception with a message
similar to the following::

  QEInputValidationError: Errors! 4 issues found:
  * You should not provide explicitly keyword 'cosab'.
  * Problem parsing keyword convthr. Maybe you wanted to specify one of these: conv_thr, nconstr, forc_conv_thr?
  * Expected a boolean for keyword nosym, found <type 'int'> instead
  * Error, keyword 'ecutrho' specified in namelist 'ELECTRONS', but it should be instead in 'SYSTEM'

As you see, a quite large number of checks are done, and if a name is not provided, a list of 
similar valid names is provided (e.g. for the wrong keyword "convthr" above).

There are a few additional options that are useful:
  
  - If you don't want to remember the namelists, you can pass a 'flat' dictionary, without
    namelists, and add the ``flat_mode=True`` option to ``input_helper``. Beside the usual
    validation, the function will reconstruct the correct dictionary to pass as input for
    the AiiDA QE calculation. Example::

      test_dict_flat = {
          'calculation': 'scf',
          'ecutwfc': 30.,
          'conv_thr': 1.e-6,
          }
      resdict = CalculationFactory('quantumespresso.pw').input_helper(
          test_dict_flat, structure=s, flat_mode = True)

    and after running, ``resdict`` will contain::
     
       test_dict = {
            'CONTROL': {
                'calculation': 'scf',
                },
            'SYSTEM': {
                'ecutwfc': 30.,
                },
            'ELECTRONS': {
                'conv_thr': 1.e-6,
                }}

    where the namelists have been automatically generated.


  - You can pass a string with a specific version number for a feature that was added
    only in a given version. For instance::

     resdict = CalculationFactory('quantumespresso.pw').input_helper(
         test_dict, structure=s,version='5.3.0')

    If the specific version is not among those for which we have a list of valid parameters,
    the error message will tell you which versions are available.


.. note:: We will try to maintain the input_helper every time a new version of Quantum ESPRESSO
   is released, but consider the ``input_helper`` function as a utility, rather than the 
   official way to provide the input -- the only officially supported way to provide
   an input to pw.x is through a direct dictionary, as described earlier in the section "Parameters".
   This applies in particular if you are using very old versions of QE, or customized versions
   that accept different parameters.



Other inputs
------------

The k-points have to be saved in another kind of data, namely KpointsData::
                
  KpointsData = DataFactory('array.kpoints')
  kpoints = KpointsData()
  kpoints.set_kpoints_mesh([4,4,4])
  
In this case it generates a 4*4*4 mesh without offset. To add an offset one 
can replace the last line by::

  kpoints.set_kpoints_mesh([4,4,4],offset=(0.5,0.5,0.5))

.. note:: Only offsets of 0 or 0.5 are possible (this is imposed by PWscf).

You can also specify kpoints manually, by inputing a list of points
in crystal coordinates (here they all have equal weights)::

    import numpy
    kpoints.set_kpoints([[i,i,0] for i in numpy.linspace(0,1,10)],
        weights = [1. for i in range(10)])

.. _gamma-only:
.. note:: It is also possible to generate a gamma-only computation. To do so 
  one has to specify additional settings, of type ParameterData, putting 
  gamma-only to True::
    
    settings = ParameterData(dict={'gamma_only':True})

  then set the kpoints mesh to a single point (gamma)::

    kpoints.set_kpoints_mesh([1,1,1])
    
  and in the end add (after ``calc = code.new_calc()``, see below) a line to use
  these settings::
  
    calc.use_settings(settings)
    
As a further comment, this is specific to the way the plugin
for Quantum Espresso works.
Other codes may need more than two ParameterData, or even none of them.
And also how this parameters have to be written depends on the plugin: 
what is discussed here is just the format that we decided for
the Quantum Espresso plugins.

Calculation
-----------

Now we proceed to set up the calculation.
Since during the setup of the code we already set the code to be a
``quantumespresso.pw`` code, there is a simple method to create a new
calculation::

  calc = code.new_calc()

We have to specify the details required by the scheduler.
For example, on a SLURM or PBS scheduler, we have to specify the number
of nodes (``num_machines``), possibly the number of MPI processes per node
(``num_mpiprocs_per_machine``) if we want to run with a different number
of MPI processes with respect to the default value configured when setting up
the computer in AiiDA, the job walltime, the queue name (if desired), ...::

  calc.set_max_wallclock_seconds(30*60) # 30 min
  calc.set_resources({"num_machines": 1})
  ## OPTIONAL, use only if you need to explicitly specify a queue name
  # calc.set_queue_name("the_queue_name")

(For the complete scheduler documentation, see :ref:`my-reference-to-scheduler`)

.. note:: an alternative way of calling a method starting with the string
  ``set_``, is to pass directly the value to the ``.new_calc()`` method. This
  is to say that the following lines::
  
    calc = code.new_calc()
    calc.set_max_wallclock_seconds(3600)
    calc.set_resources({"num_machines": 1})
    
  is equivalent to::
  
    calc = code.new_calc(max_wallclock_seconds=3600,
        resources={"num_machines": 1})

At this point, we just created a "lone" calculation, that still does not know 
anything about the inputs that we created before. We need therefore to  
tell the calculation to use the parameters that we prepared before, by 
properly linking them using the ``use_`` methods::

  calc.use_structure(s)
  calc.use_code(code)
  calc.use_parameters(parameters)
  calc.use_kpoints(kpoints)

In practice, when you say ``calc.use_structure(s)``, you are setting a link 
between the two nodes (``s`` and ``calc``), that means that 
``s`` is the input *structure* for *calculation* ``calc``. Also these links
are cached and do not require to store anything in the database yet.

In the case of the gamma-only computation (see :ref:`above <gamma-only>`), you 
also need to add::

  calc.use_settings(settings)
  
Pseudopotentials
----------------

There is still one missing piece of information, that is the
pseudopotential files, one for each element of the structure.

In AiiDA, it is possible to specify manually which pseudopotential files to use
for each atomic species. However, for any practical use, it is convenient
to use the pseudopotential families.
Its use is documented in :ref:`my-ref-to-pseudo-tutorial`.
If you got one installed, you can simply tell the calculation to use the
pseudopotential family with a given name, and AiiDA will take care of
linking the proper pseudopotentials to the calculation, one for each atomic
species present in the input structure. This can be done using::

  calc.use_pseudos_from_family('my_pseudo_family')

Labels and comments
-------------------

Sometimes it is useful to attach some notes to the calculation,
that may help you later understand why you did such a calculation,
or note down what you understood out of it.
Comments are a special set of properties of the calculation, in the sense
that it is one of the few properties that can be changed, even after
the calculation has run.

Comments come in various flavours. The most basic one is the label property,
a string of max 255 characters, which is meant to be the title of the calculation.
To create it, simply write::

  calc.label = "A generic title"

The label can be later accessed as a class property, i.e. the command::

  calc.label

will return the string you previously set (empty by default).
Another important property to set is the description, which instead does not have a
limitation on the maximum number of characters::

  calc.description = "A much longer description"

And finally, there is the possibility to add comments to any calculation
(actually, to any node).
The peculiarity of comments is that they are user dependent
(like the comments that you can post on facebook pages), so it is best
suited to calculation exposed on a website, where you want to remember
the comments of each user.
To set a comment, you need first to import the django user, and then
write it with a dedicated method::

  from aiida.backends.djsite.utils import get_automatic_user
  calc.add_comment("Some comment", user=get_automatic_user())

The comments can be accessed with this function::

  calc.get_comments_tuple()


Execute
-------
If we are satisfied with what you created, it is time to store everything
in the database. 
Note that after storing it, it will not be possible to modify it
(nor you should: you risk of compromising the integrity of the database)!

Unless you already stored all the inputs beforehand, you will need to store 
the inputs before being able to store the calculation itself.
Since this is a very common operation, there is an utility method that will
automatically store both all the input nodes of ``calc`` and then ``calc`` 
itself::

  calc.store_all()

Once we store the calculation, it is useful to print its PK (principal key, 
that is its identifier) that is useful in the following to interact with it::

  print "created calculation; with uuid='{}' and PK={}".format(calc.uuid,calc.pk)

.. note:: the PK will change if you give the calculation to someone else,
  while the UUID (the Universally Unique IDentifier) is a string that is
  assured to be always the same also if you share your data with collaborators.

Summarizing, we created all the inputs needed by a PW calculation,
that are: parameters, kpoints, pseudopotential files and the structure.
We then created the calculation, where we specified that it is a PW calculation
and we specified the details of the remote cluster.
We set the links between the inputs and the calculation (``calc.use_***``)
and finally we stored all this objects in the database (``.store_all()``).
 
That's all that the calculation needs.  Now we just need to submit it::

   calc.submit()

Everything else will be managed by AiiDA: the inputs will be checked to verify
that it is consistent with a PW input. If the input is complete, the pw input
file will be prepared in a folder together with all the other files required
for the execution (pseudopotentials, etc.). It will be then sent on cluster,
submitted, and after execution automatically retrieved and parsed.

To know how to monitor and check the state of submitted calculations, go to
:doc:`../state/calculation_state`.

To continue the tutorial with the ``ph.x`` phonon code of Quantum ESPRESSO,
continue here: :ref:`my-ref-to-ph-tutorial`.




Script: source code
-------------------

In this section you'll find two scripts that do what explained in the tutorial.
The compact is a script with a minimal configuration required.
You can copy and paste it (or download it), modify the two strings ``codename``
and ``pseudo_family`` with the correct values, and execute it with::

  python pw_short_example.py

(It requires to have one family of pseudopotentials configured).

You will also find a longer version, with more exception checks, error
management and user interaction.
Note that the configuration of the computer resources
(like number of nodes and machines) is hardware and scheduler dependent.
The configuration used below should work for a pbspro or slurm cluster,
asking to run on 1 node only.

Compact script
--------------
Download: :download:`this example script <pw_short_example.py>`

::

  #!/usr/bin/env python
  from aiida import load_dbenv
  load_dbenv()
  
  from aiida.orm import Code, DataFactory
  StructureData = DataFactory('structure')
  ParameterData = DataFactory('parameter')
  KpointsData = DataFactory('array.kpoints')
  
  ###############################
  # Set your values here
  codename = 'pw-5.1@TheHive'
  pseudo_family = 'lda_pslibrary'
  ###############################
  
  code = Code.get_from_string(codename)
  
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
                }})
  
  kpoints = KpointsData()
  kpoints.set_kpoints_mesh([4,4,4])
  
  calc = code.new_calc(max_wallclock_seconds=3600,
      resources={"num_machines": 1})
  calc.label = "A generic title"
  calc.description = "A much longer description"
  
  calc.use_structure(s)
  calc.use_code(code)
  calc.use_parameters(parameters)
  calc.use_kpoints(kpoints)
  calc.use_pseudos_from_family(pseudo_family)
  
  calc.store_all()
  print "created calculation with PK={}".format(calc.pk)
  calc.submit()
  



Exception tolerant code
-----------------------
You can find a more sophisticated example, that checks the possible exceptions
and prints nice error messages inside your AiiDA folder, under
``examples/submission/quantumespresso/test_pw.py``.

Advanced features
-----------------
For a list of advanced features that can be activated (change of the
command line parameters, blocking some coordinates, ...) you can refer
to :ref:`this section<pw-advanced-features>`
in the pw.x input plugin documentation.

Importing previously run Quantum ESPRESSO pw.x calculations: PwImmigrant
========================================================================

Once you start using AiiDA to run simulations, we believe that you will find it
so convenient that you will use it for all your calculations. 

At the beginning, however, you may have some calculations that you already have
run and are sitting in some folders, and that you want to import inside AiiDA.

This can be achieved with the PwImmigrant class described below.

.. toctree::
   :maxdepth: 2
   
   pwimmigrant_tutorial

