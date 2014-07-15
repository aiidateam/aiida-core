.. aiida documentation master file, created by
   sphinx-quickstart on Wed Oct 24 11:33:37 2012.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to AiiDA's documentation!
=================================

This is the documenation of the AiiDA framework. For the basic configuration and
simple usage, refer to the user's guide below.

If, instead, you plan to add new plugins, or you simply want to understand
AiiDA internals, refer to the developer's guide.

User's guide
++++++++++++

.. toctree::
   :maxdepth: 2

   database/index
   installation
   setup/computerandcodes
   examples/scripting
   examples/structure_tutorial
   examples/pw_tutorial
   examples/ph_tutorial
   examples/cp_tutorial
   parsers/resultmanager
   examples/pseudo_tutorial

   scheduler/index
    
   state/calculation_state

   workflow/index

Other guide resources
+++++++++++++++++++++
.. toctree::
   :maxdepth: 2
    
   setup/aiida_multiuser
   troubleshooting/index
   website/web.rst


Developer's guide
+++++++++++++++++

.. toctree::
    :maxdepth: 2
    
    Developer's Guide <developers> 
    devel_tutorial/code_plugin    

Modules provided with aiida
---------------------------

.. toctree::
   :maxdepth: 2
   
   aiida.common Modules [OUTDATED] <common/dev>
   transport/dev
   scheduler/dev
   cmdline/dev
   execmanager/dev
   djsite/dev
   orm/dev

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

