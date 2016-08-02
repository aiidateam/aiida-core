.. _my-ref-to-wannier90-tutorial:

Wannier90 user-tutorial
=========

.. note:: The Wannier90 plugin referenced below is available in the EPFL version.

Here we will review an example application of the wannier90 input plugin. In this example we will attempt to
make MLWF for the oxygen 2p states in BaTiO3. This tutorial assumes that you are already familiar with the
`wannier90 code`_). You should also finish the :ref:`my-ref-to-pw-tutorial`. This tutorial will make use of parent_calculations
and therefore it would be helpful, though not necessary, to do :ref:`my-ref-to-ph-tutorial`.
For more details on the wannier90 plugin consult :ref:`my-ref-to-wannier90-doc`.



.. _wannier90 code: http://www.wannier.org/index.html


Calculation Setup
-----------------

Prior to running this tutorial first you must prepare the SCF and NSCF calculations. First run an SCF calculation for BaTiO3,
you can use the settings in ``examples/submission/test_pw.py`` which should properly setup the SCF calculation. After the SCF
calculation you will need to compute an NSCF calculation, with the kpoint grid explicitly written. You may use
``examples/submission/wannier/test_nscf4wann.py`` to help here. Before continuing, note inside the nscf script. You should see the following lines::

    settings_dict.update({ 'FORCE_KPOINTS_LIST':True})
    kpoints = KpointsData()
    kpoints_mesh = 4
    kpoints.set_kpoints_mesh([kpoints_mesh, kpoints_mesh, kpoints_mesh])

This is very similar to using a kpoint mesh for a PW calculation, but note that we must use the ``FORCE_KPOINTS_LIST`` in the settings dict. The
following settings should be used as cards in the PW calculation setup::

    new_input_dict['CONTROL'].update({'calculation': 'nscf'})
    new_input_dict['SYSTEM'].update({'nosym': True})
    # new_input_dict['SYSTEM'].update({'nbnd':20}) # Tune if you need more bands

 where the nosym is a requirement of wannier90.x but not of this plugin specifically. It is often useful to change the number of bands in the calculation
 as shown in the ``{'nbnd':20}`` dictionary.

Input Script
------------

Here we will go through a sample input script. First import the wannier90 code name and setup a new calculation::

    # Basic Code setup
    from aiida.orm import Code
    codename = "MY_Wannier90_CODENAME"
    code = Code.get_from_string(codename)
    calc = code.new_calc()

Then set up the precode, e.g. ``pw2wannier90.x``::

    # Basic Precode setup
    pre_codename = "MY_PRECODE_NAME"
    pre_code = Code.get_from_string(pre_codename)
    calc.use_preprocessing_code(pre_code)

.. note:: Whether a pre_code is supplied or not will change the way the calculation is run. After finishing
          this tutorial try running the same calculation again without a precode by commenting out ``calc.use_preprocessing_code(pre_code)``. You
          should also change the parent_id to the wannier90 calculation produced by running this script the first time.

Then use a parent calculation, in this case the parent should be an nscf calculation the first time through this tutorial. (You can then try
playing with using wannier90 calculations as parent)::

    parent_id = "MY_PARENT_NSCF_CALC_PK"
    parent_calc = Calculation.get_subclass_from_pk(parent_id)
    calc.use_parent_calculation(parent_calc)

We can then setup the parameters using ParameterData, this syntax is very similar to that used in PW. You can then
input the parameters to be used in the calculation like how it is shown below::

    from aiida.orm import DataFactory
    ParameterData = DataFactory('parameter')
    parameter = ParameterData(dict={'bands_plot':True,
                                    'num_iter': 100,
                                    'dis_num_iter': 200,
                                    'num_print_cycles': 10,
                                    'guiding_centres': True,
                                    'num_wann': 9,
                                    'exclude_bands': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
                                    })
    calc.use_parameters(parameter)

Specific parameters can then be passed to preprocessing code using precode_parameters (in this case we are not using an precode_paramters)::

    precode_parameter = {}
    precode_parameter = ParameterData(dict=precode_parameter)
    calc.use_precode_parameters(precode_parameter)

.. note:: One example of a useful precode_parameter would be to tell the preprocessing code to write UNK files. Try this out by adding
          ``precode_parameter.update({'write_unk':True})`` after ``precode_parameter = {}``.

For both the structure and the kpoints, you should always just copy those used by the parent like how it is done below::

    structure = parent_calc.get_inputs_dict()['structure']
    calc.use_structure(structure)
    kpoints = parent_calc.get_inputs_dict()['kpoints']
    calc.use_kpoints(kpoints)

If you wish to supply a kpoint path for band plotting in the following way ::

    kpoints_path = DataFactory('array.kpoints')()
    kpoints_path.set_cell_from_structure(structure)
    kpoints_path.set_kpoints_path()
    calc.use_kpoints_path(kpoints_path)

In this example we would like to have our intitial projections be 'P' like on every Oxygen, 'O' site. In wannier90 syntax this would
be equivalent to writing ``O:P`` in the projections section. See **projections** in :ref:`my-ref-to-wannier90-inputs-doc` for more details
on how to use projections in the wannier90 plugin. For this plugin we would use the following::

    orbitaldata = calc.gen_projections([{'kind_name':"O",'ang_mtm_name':"P"}])
    calc.use_projections(orbitaldata)

After set remainging computer settings, as well as an input settings::

    calc.set_max_wallclock_seconds(30*60) # 30 min
    calc.set_resources({"num_machines": 1})
    settings_dict = {}
    settings = ParameterData(dict=settings_dict)
    calc.use_settings(settings)

.. note:: one useful setting to try would be to tell the code to only do the preprocessing steps but not the actual wannierization. This
          could be done by using ``settings_dict.update({'INIT_ONLY':True})`` after ``settings_dict = {}``.
          See **settings** in :ref:`my-ref-to-wannier90-inputs-doc` for information on this and other settings and how the impact code
          running.

Finally store and launch the calculation::

    calc.store_all()
    print "created calculation; ID={}".format(calc.dbnode.pk)
    calc.submit()
    print "submitted calculation; ID={}".format(calc.dbnode.pk)

Additional Exercises
--------------------

After this try looking at the output. Particularly the centers and spread of the wannier functions, and the gauge-invarient spread Omega_I. After this
try doing the following:

#. Try plotting the band structure, add {'RESTART':'plot'} to parameter and comment out ``calc.use_precode_parameters`` using the wannier90 calculation as parent
#. Do a new initialization calculation that writes UNK files, using INIT_ONLY in the settings_dict and WRITE_UNK in precode_parameters
#. Use this calculation to run another wannier90 calculation, change ``WANNIER_PLOT`` in parameters run again without any precode and see the im_re_ratio in the resulting wannier functions.

Exception tolerant code
-----------------------
You can find a more sophisticated example, that checks the possible exceptions
and prints nice error messages inside your AiiDA folder, under
``examples/submission/wannier/test_wannier_BaTiO3.py``.

