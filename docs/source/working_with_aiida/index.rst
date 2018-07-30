##################
Working with AiiDA
##################


======================
Command line interface
======================

.. toctree::
    :maxdepth: 4

    ../verdi/verdi_user_guide


=========
Scripting
=========

While many common functionalities are provided by either command-line tools 
(via ``verdi``) or the web interface, for fine tuning (or automatization) 
it is useful to directly access the python objects and call their methods.

This is possible in two ways, either via an interactive shell, or writing and 
running a script. Both methods are described below.

.. toctree::
    :maxdepth: 4

    scripting


============
Calculations
============

.. toctree::
    :maxdepth: 4

    ../state/calculation_state
    resultmanager

==========
Data types
==========

.. toctree::
    :maxdepth: 4

    ../datatypes/index
    ../datatypes/kpoints
    ../datatypes/functionality

==========
Schedulers
==========

As described in the section about calculations, ``JobCalculation`` instances are submitted by the daemon to an external scheduler.
For this functionality to work, AiiDA needs to be able to interact with these schedulers.
Interfaces have been written for some of the most used schedulers.

.. toctree::
    :maxdepth: 4

    ../scheduler/index

==========
Link types
==========

.. toctree::
    :maxdepth: 4

    ../link_types/index.rst

=============
Querying data
=============

.. toctree::
    :maxdepth: 4

    ../querying/index.rst


================
Legacy workflows
================

.. toctree::
    :maxdepth: 4

    ../old_workflows/index.rst


=======
Backups
=======

.. toctree::
    :maxdepth: 4

    ../backup/index.rst
