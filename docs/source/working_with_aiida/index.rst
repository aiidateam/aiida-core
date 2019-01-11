======================
Command line interface
======================

.. toctree::
    :maxdepth: 4

    ../verdi/verdi_user_guide
    ../verdi/properties


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
    inline_calculations

==========
Data types
==========

.. toctree::
    :maxdepth: 4

    ../datatypes/index
    ../datatypes/kpoints
    ../datatypes/functionality

======
Groups
======

.. toctree::
    :maxdepth: 4

    groups

==========
Schedulers
==========

As described in the section about calculations, ``CalcJobNode`` instances are submitted by the daemon to an external scheduler.
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


=======
Backups
=======

.. toctree::
    :maxdepth: 4

    ../backup/index.rst

===============
Troubleshooting
===============

.. toctree::
    :maxdepth: 4

    troubleshooting.rst

========
REST API
========

.. toctree::
    :maxdepth: 4

    ../restapi/index.rst

========
Cookbook
========

.. toctree::
    :maxdepth: 4

    cookbook.rst




