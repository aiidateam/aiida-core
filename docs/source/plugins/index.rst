==================
Plug-ins for AiiDA
==================
AiiDA plug-ins are input generators and output parsers, enabling the
integration of codes into AiiDA calculations and workflows.

The plug-ins are not meant to completely automatize the calculation of physical properties. An underlying knowledge of how each code works, which flags it requires, etc. is still required. A total automatization, if desired, has to be implemented at the level of a workflow.


Available plugins
+++++++++++++++++

.. toctree::
   :maxdepth: 4
 
   quantumespresso/index
   codtools/index
   ase/index
   wannier90/index
   nwchem/index
