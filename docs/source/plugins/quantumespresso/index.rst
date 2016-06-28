
.. _sec.quantumespresso:

Quantum Espresso
----------------

Description
^^^^^^^^^^^
`Quantum Espresso`_ is a suite of open-source codes for electronic-structure calculations
from first principles, based on density-functional theory, plane waves, and pseudopotentials,
freely `available online`_.
Documentation of the code and its internal details can be found in the distributed software, and in the `online forum`_ (and its `search engine`_).

.. _Quantum Espresso: http://www.quantum-espresso.org/
.. _available online: http://qe-forge.org/gf/project/q-e/frs/?action=FrsReleaseBrowse&frs_package_id=18
.. _search engine: https://www.google.com/cse/home?cx=000217952118062629757:xew9tb5yarq  
.. _online forum: http://www.quantum-espresso.org/forum/

The plugins of quantumespresso in AiiDA are not meant to completely automatize the calculation of the electronic properties. It is still required an underlying knowledge of how quantum espresso is working, which flags it requires, etc. A total automatization, if desired, has to be implemented at the level of a workflow.

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
