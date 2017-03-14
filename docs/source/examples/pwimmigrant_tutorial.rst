.. _my-ref-to-pwimmigration-tutorial:

PWscf immigration
=================

.. toctree::
   :maxdepth: 2

If you are a new AiiDA user, it's likely you already have a large number of calculations that you ran before installing AiiDA. This tutorial will show you how to immigrate any of these PWscf (``pw.x``) calculations into your AiiDA database. They will then exist there as if you had actually run them using AiiDA (with the exception of the times and dates the calculations were run).

It is assumed that you have already performed the installation, that you already setup a computer (with ``verdi``), and that you have installed Quantum Espresso on the cluster and ``pw.x`` as a code in AiiDA. You should also be familiar with using AiiDA to run a PWscf calculation and the various input and output nodes of a PwCalculation. Please go through :ref:`my-ref-to-pw-tutorial` before proceeding.

.. admonition:: Example details
    :class: admonition note

    The rest of the tutorial will detail the steps of immigrating two example ``pw.x`` calculations that were run in ``/scratch/``, using the code named ``'pw_on_TheHive'``, on 1 node with 1 mpi process. The input/output file names of these calculations are

    * ``pw_job1.in``/``pw_job1.out``
    * ``pw_job2.in``/``pw_job2.out``




Imports and database environement
---------------------------------

As usual, we load the database environment and load the ``PwimmigrantCalculation`` class using the ``CalculationFactory``.

::

    # Load the database environment.
    from aiida import load_dbenv
    load_dbenv()

    from aiida.orm.code import Code
    from aiida.orm import CalculationFactory

    # Load the PwimmigrantCalculation class.
    PwimmigrantCalculation = CalculationFactory('quantumespresso.pwimmigrant')




Code, computer, and resources
-----------------------------

.. Important::
   It is up to the user to setup and link the following calculation inputs manually:

      * the code
      * the computer
      * the resources

   These input nodes should be created to be representative of those that were used for the calculation that is to be immigrated. (Eg. If the job was run using version 5.1 of Quantum-Espresso, the user should have already run ``verdi code setup`` to create the code's node and should load and pass this code when initializing the calculation node.) If any of these input nodes are not representative of the actual properties the calculation was run with, there may be errors when performing a calculation restart of an immigrated calculation, for example.

Next, we load the code and computer that have already been configured to be representative of those used to perform the calculation. We also define the resources representive of those that were used to run the calculation.

::

    # Load the Code node representative of the one used to perform the calculations.
    code = Code.get_from_string('pw_on_TheHive@machinename')

    # Get the Computer node representative of the one the calculations were run on.
    computer = code.get_remote_computer()

    # Define the computation resources used for the calculations.
    resources = {'num_machines': 1, 'num_mpiprocs_per_machine': 1}




Initialization of the calculation
---------------------------------

Now, we are ready to initialize the immigrated calculation objects from the ``PwimmigrantCalculation`` class. We will pass the necessary parameters as keywords during the initialization calls. Then, we link the code from above as an input node.

::

    # Initialize the pw_job1 calculation node.
    calc1 = PwimmigrantCalculation(computer=computer,
                                   resources=resources,
                                   remote_workdir='/scratch/',
                                   input_file_name='pw_job1.in',
                                   output_file_name='pw_job1.out')

    # Initialize the pw_job2 calculation node.
    calc2 = PwimmigrantCalculation(computer=computer,
                                   resources=resources,
                                   remote_workdir='/scratch/',
                                   input_file_name='pw_job2.in',
                                   output_file_name='pw_job2.out')

    # Link the code that was used to run the calculations.
    calc1.use_code(code)
    calc2.use_code(code)

The user may have noticed the additional initialization keywords/parameters--``remote_wordir``, ``input_file_name``, and ``output_file_name``--passed here. These are necessary in order to tell AiiDA which files to use to automatically generate the calculation`s input nodes in the next step.




The immigration
---------------

Now that AiiDA knows where to look for the input files of the calculations we are immigrating, all we need to do in order to generate all the input nodes is call the ``create_input_nodes`` method. This method is the most helpful method of the ``PwimmigrantCalculation`` class. It parses the job's input file and creates and links the follow types of input nodes:

* ParameterData -- based on the namelists and their variable-value pairs
* KpointsData -- based on the ``K_POINTS`` card
* SturctureData --  based on the ``ATOMIC_POSITIONS`` and ``CELL_PARAMETERS`` cards (and the ``a`` or ``celldm(1)`` of the ``&SYSTEM`` namelist, if ``alat`` is specified through these variables)
* UpfData -- one for each of the atomic species, based on the pseudopotential files specified in the ``ATOMIC_SPECIES`` card
* settings ParameterData --  if there are any fixed coordinates, or if the gamma kpoint is used

All units conversion and/or coordinate transformations are handled automatically, and the input nodes are generated in the correct units and coordinates required by AiiDA.

.. note:: Any existing UpfData nodes are simply linked without recreation; no duplicates are generated during this method call.

.. note:: After this method call, the calculation and the generated input nodes are still in the cached state and are not yet stored in the database. Therefore, the user may examine the input nodes that were generated (by examining the attributes of the ``NodeInputManager``, ``calc.inp``) and edit or replace any of them. The immigration can also be canceled at this point, in which case the calculation and the input nodes would not be stored in the database.

Finally, the last step of the immigration is to call the ``prepare_for_retrieval_and_parsing`` method. This method stores the calculation and it's input nodes in the database, copies the original input file to the calculation's repository folder, and then tells the daemon to retrieve and parse the calculation's output files.

 .. note:: If the daemon is not currently running, the retrieval and parsing process will not begin until it is started.

Because the input and pseudopotential files need to be retrieved from the computer, the computer's transport plugin needs to be open. Rather than opening and closing the transport for each calculation, we instead require the user to pass an open transport instance as a parameter to the ``create_input_nodes`` and ``prepare_for_retrieval_and_parsing`` methods. This minimizes the number of transport opening and closings, which is highly beneficial when immigrating a large number of calculations.

Calling these methods with an open transport is performed as follows:

::

    # Get the computer's transport and create an instance.
    from aiida.backends.utils import get_authinfo, get_automatic_user
    authinfo = get_authinfo(computer=computer, aiidauser=get_automatic_user())
    transport = a.get_transport()

    # Open the transport for the duration of the immigrations, so it's not
    # reopened for each one. This is best performed using the transport's
    # context guard through the ``with`` statement.
    with transport as open_transport:

        # Parse the calculations' input files to automatically generate and link the
        # calculations' input nodes.
        calc1.create_input_nodes(open_transport)
        calc2.create_input_nodes(open_transport)

        # Store the calculations and their input nodes and tell the daeomon the output
        # is ready to be retrieved and parsed.
        calc1.prepare_for_retrieval_and_parsing(open_transport)
        calc2.prepare_for_retrieval_and_parsing(open_transport)




The process above is easily expanded to large-scale immigrations of multiple jobs.




Compact script
--------------

Download: :download:`this example script <pwimmigrant_short_example.py>`

.. literalinclude:: pwimmigrant_short_example.py





