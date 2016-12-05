
.. _sec.quantumespresso:

Quantum Espresso
----------------

Description
^^^^^^^^^^^
`Quantum Espresso`_ is a suite of open-source codes for electronic-structure calculations from first principles, based on density-functional theory, plane waves, and pseudopotentials, freely `available online`_.
Documentation of the code and its internal details can also be found in the `Quantum Espresso manual`_.

.. _Quantum Espresso: http://www.quantum-espresso.org/
.. _available online: http://qe-forge.org/gf/project/q-e/frs/?action=FrsReleaseBrowse&frs_package_id=18
.. _Quantum Espresso manual: http://www.quantum-espresso.org/users-manual/

Currently supported codes are:

* PW: Ground state properties, total energy, ionic relaxation, molecular dynamics, forces, etc...
* CP: Car-Parrinello molecular dynamics
* PH: Phonons from density functional perturbation theory
* Q2R: Fourier transform the dynamical matrices in the real space
* Matdyn: Fourier transform the dynamical matrices in the real space
* NEB: Energy barriers and reaction pathways using the Nudged Elastic Band (NEB) method

Moreover, support for further codes can be implemented adapting the **namelist** plugin.

Plugins
^^^^^^^

.. toctree::
   :maxdepth: 4

   pw
   cp
   ph
   matdyn
   q2r
   neb
   projwfc
   dos
