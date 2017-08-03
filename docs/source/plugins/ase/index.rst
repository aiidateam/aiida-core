ASE
---

Description
^^^^^^^^^^^
`ASE`_ (Atomic Simulation Environment) is a set of tools and Python modules for 
setting up, manipulating, running, visualizing and analyzing atomistic 
simulations. The ASE code is freely available under the GNU LGPL license (the 
ASE installation guide and the source can be found `here`_).

Besides the manipulation of structures (``Atoms`` objects), one can attach 
``calculators`` to a structure and run it to compute, as an example, energies or
forces.
Multiple calculators are currently supported by ASE, like GPAW, Vasp, Abinit and
many others.

In AiiDA, we have developed a plugin which currently supports the use of ASE 
calculators for total energy calculations and structure optimizations.

.. _here: http://wiki.fysik.dtu.dk/ase/

Plugins
^^^^^^^

.. toctree::
   :maxdepth: 4

   ase

