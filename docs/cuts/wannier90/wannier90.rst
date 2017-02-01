.. _my-ref-to-wannier90-doc:

Wannier90
+++++++++

.. note:: The Wannier90 plugin referenced below is available in the EPFL version.


Description
-----------
This plugin supports input to wannier90, through any calculations done in QE, via the pw2wannier90.x code.

.. _here: http://www.wannier.org/index.html


Supported codes
---------------
* tested on Wannier90 v2.0.1

.. _my-ref-to-wannier90-inputs-doc:

Inputs
------
* **parent_calculation**, The parent calculation can either be a PW calculation or Wannier90. See :ref:`my-ref-to-wannier90-filescopy-doc` for more details.

  .. note:: There are no direct links between calculations. The use_parent_calculation will set a link to the RemoteFolder attached to that calculation. Alternatively, the method **use_parent_folder** can be used to set this link directly.

* **kpoints**, class :py:class:`KpointsData <aiida.orm.data.array.kpoints.KpointsData>`
  Reciprocal space points on which to build the wannier functions. Note that this must be an evenly spaced grid and must be constructed using an mp_grid kpoint mesh, with `{'FORCE_KPOINTS_LIST': True}` setting in the PW nscf calculation. It is a requirement of Wannier90, though not of this plugin, that symmetry not be used in the parent calculation, that is the setting card ``['SYSTEM'].update({'nosym': True})`` be applied in the parent calculation.

* **kpoints_path**, class :py:class:`KpointsData <aiida.orm.data.array.kpoints.KpointsData>` (optional)
  A set of kpoints which indicate the path to be plotted by wannier90 band plot feature.

* **parameters**, class :py:class:`ParameterData <aiida.orm.data.parameter.ParameterData>`
  Input parameters that defines the calculations to be performed, and their parameters. Unlike the wannier90 code, which does not check capitilization, this plugin is case sensitive. All keys must be lowercase e.g. ``num_wann`` is acceptable but ``NUM_WANN`` is not. See the Wannier90 documentation for more details.

* **precode_parameters**, class :py:class:`ParameterData <aiida.orm.data.parameter.ParameterData>` (optional)
  Input parameters for the precode. For this plugin the precode is expected to be pw2wannier. As with parameters, all keys must be capitalized. See the Wannier90 documentation for more details on the input parameters for pw2wannier90.

* **structure**, class :py:class:`StructureData <aiida.orm.data.structure.StructureData>`
  Input structure mandatory for execution of the code.

* **projections**, class :py:class:`OrbitalData <aiida.orm.data.orbital.OrbitalData>`
  An OrbitalData object containing it it a list of orbitals

.. note:: 
    You should construct the projections using the convenience method :py:meth:`gen_projections <aiida.orm.calculation.job.wannier90.Wannier90Calculation.gen_projections>`. Which will produce an :py:class:`OrbitalData <aiida.orm.data.orbital.OrbitalData>` given a list of dictionaries. Some examples, taken directly from the wannier90 user guide, would be:

        #. CuO, SP, P, and D on all Cu; SP3 hyrbrids on O.

           In Wannier90 ``Cu:l=0;l=1;l=2`` for Cu and ``O:l=-3`` or ``O:sp3`` for O

           Would become ``{'kind_name':'Cu','ang_mtm_name':['SP','P','D']}`` for Cu and  ``{'kind_name':'O','ang_mtm_l':-3}`` or ``{..., 'ang_mtm_name':['SP3']}`` for O

        #. A single projection onto a PZ orbital orientated in the (1,1,1) direction:

           In Wannier90 ``c=0,0,0:l=1:z=1,1,1`` or ``c=0,0,0:pz:z=1,1,1``

           Would become ``{'position_cart':(0,0,0),'ang_mtm_l':1,'zaxis':(1,1,1)}`` or ``{... , 'ang_mtm_name':'PZ',...}``

        #. Project onto S, P, and D (with no radial nodes), and S and P (with one radial node) in silicon:

           In Wannier90 ``Si:l=0;l=1;l=2``, ``Si:l=0;l=1;r=2``

           Would become ``[{'kind_name':'Si','ang_mtm_l':[0,1,2]}, {'kind_name':'Si','ang_mtm_l':[0,1],'radial_nodes':2}]``

* **settings**, class :py:class:`ParameterData <aiida.orm.data.parameter.ParameterData>`
  An optional dictionary that activates non-default operations. Possible values are:

    *  **'INIT_ONLY'**: If set to true, will only initialize the calculation, but will not run
       the actual wannierization. That is, ``wannier90.x -pp aiida.win`` and ``precode2wannier < aiida.in > aiida.out`` will be run only.
       This is ideal in use as a start point for future restarts.

    *  **'ADDITIONAL_RETRIEVE_LIST'**: A list of additional files to be retrieved at the end of the calculation.

    *  **'ADDITIONAL_SYMLINK_LIST'**: A list of additional files to be symlinked from the parent calculation.

    *  **'ADDITIONAL_COPY_LIST'**: A list of additional files to be copied from the parent calculation.

* **use_preprocessing_code** a preprocessing code may be supplied, currently the code must be a pw2wannier code, with which the initial setup of the wannierization will be performed. If a pre_processing_code is supplied the following will be run. ``wannier90.x -pp aiida.win``, ``precode2wannier < aiida.in > aiida.out``, ``wannier90.x aiida.win``. However, if no preprocessing code is supplied only ``wannier90.x aiida.win`` will be run.

.. _my-ref-to-wannier90-filescopy-doc:

Files Copied
------------
Depending on the startup settings used, and what the parent calculation was will alter which files are copied, which are symlinked see the table below. The goal being to copy the minimum number of files, and to not symlink to files that will be rewritten. The calculation names used in the table are:

* **NOT WANNIER** The parent is not a wannier calculation
* **HAS PRECODE** A wannier90 calculation run with a precode, e.g. initializations
* **NO PRECODE** A wannier90 calculation run with no precode, e.g. restarts

The following operations will be performed on the files:

* **copy**: the file, if present, is copied from the parent
* **sym**: the file, if present, will be symlinked to the parent
* **none**: the file will neither be copied or symlinked

====================  ===================  ====================    ====================
\                     \                     Parent Calculation
--------------------  -------------------  --------------------------------------------
Child Calculation     - NOT WANNIER        - HAS PRECODE           - NO PRECODE
====================  ===================  ====================    ====================
- HAS PRECODE         - ./out/ **copy**     - ./out/ **sym**       - ./out/ **sym**
                      - .EIG,.MMN,.UNK      - .MMN,.UNK            - .MMN,.UNK
                        **none**              **sym**                **sym**
                      - .AMN                - .AMN, .EIG           - .AMN, .EIG
                        **none**              **none**               **none**
                      - .CHK                - .CHK                 - .CHK
                        **none**              **none**               **none**
--------------------  -------------------  --------------------    --------------------
- NO PRECODE          - **NOT ALLOWED**    - ./out/ **sym**        - ./out/ **sym**
                                           - .MMN,.UNK             - .MMN,.UNK
                                             **sym**                 **sym**
                                           - .AMN, .EIG            - .AMN, .EIG
                                             **sym**                 **sym**
                                           - .CHK                  - .CHK
                                             **copy**                **copy**
====================  ===================  ====================    ====================

.. note:: 
    For the case where the child has precode and the parent is a wannier calculation the .MMN file will hard-set not to be written, regardless of what is
          in the precode_parameters. (i.e. if the parent is not a wannier90 calc, ``WRITE_MMN = .false.`` is automatically set in precode.)
.. note:: 
    The ``.MMN`` file is only calculated for the case of the parent being a **NOT WANNIER**. (See the table) If, for whatever reason, you wish to recalculate these files please use **NOT WANNIER** as a parent.

Outputs
-------
* output_parameters :py:class:`ParameterData <aiida.orm.data.parameter.ParameterData>` (accessed by ``calculation.res``). Contains the scalar properties. Currently parsed parameters include:

  * ``number_wannier_functions``: the number of wannier functions
  * ``Omega_D``, ``Omega_I``, ``Omega_OD``, ``Omega_total`` wich are: the diagonal :math:`\Omega_D`,
    invariant  :math:`\Omega_I`, offdiagonal :math:`\Omega_{OD}`, and total spread :math:`\Omega_{total}`. Units are always Ang^2
  * ``wannier_functions_output`` a list of dictionaries containing:

    - coordinates: the center of the wannier function
    - spread: the spread of the wannier function. Units are always Ang^2
    - wannier_function: numerical index of the wannier function
    - im_re_ratio: if available the Imaginary/Real ratio of the wannier function

  * ``Warnings``: parsed list of warnings
  * ``output_verbosity``: the output verbosity, throws a warning if any value other than default is used
  * ``preprocess_only``: whether the calc only did the preprocessing step ``wannier90 -pp``
  * ``r2_nm_writeout``: whether r^2 nm file was written
  * ``wannierise_convergence_tolerence``: the tolerance for convergence, units of Ang^2
  * ``xyz_wf_center_writeout``: whether xyz_wf_center file was explicitly and independently written
  * Other parameters, should match those described in the user guide
    
* interpolated_bands :py:class:`BandsData <aiida.orm.data.array.bands.BandsData>`
  If available, will parse the interpolated bands and store them.


Errors
------
Errors of the parsing are reported in the log of the calculation (accessible with the ``verdi calculation logshow`` command). Moreover, they are stored in the ParameterData under the key ``warnings``, and are accessible with ``Calculation.res.warnings``.

