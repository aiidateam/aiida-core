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

   database/database
   installation
   setup/computerandcodes
   examples/pw_tutorial

   scheduler/index


Developer's guide
+++++++++++++++++

.. toctree::
    :maxdepth: 2
    
    Developer's Guide <developers> 

Modules provided with aiida
---------------------------

.. toctree::
   :maxdepth: 2
   
   aiida.common Modules [OUTDATED] <common/index>
   transport/index
   scheduler/dev
   cmdline/index
   execmanager/index
   djsite/index
   orm/index

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

