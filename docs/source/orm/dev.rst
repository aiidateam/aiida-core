ORM documentation: generic aiida.orm
====================================

.. toctree::
   :maxdepth: 3

This section describes the aiida/django object-relational mapping.

Some generic methods of the module aiida.orm

.. automodule:: aiida.orm
   :members:
   :special-members: __init__

Computer
++++++++
.. automodule:: aiida.orm.computer
   :members:

Node
++++
.. automodule:: aiida.orm.node
   :members:
   :special-members: __init__

Workflow
++++++++
.. automodule:: aiida.orm.workflow
   :members:


Code
++++
.. automodule:: aiida.orm.code
   :members:
   :special-members: __init__




ORM documentation: Data
=======================

.. automodule:: aiida.orm.data
   :members:

.. _my-ref-to-structure:

Structure
+++++++++
.. automodule:: aiida.orm.data.structure
   :members:
   :special-members: __init__

Folder
++++++
.. automodule:: aiida.orm.data.folder
   :members:

Singlefile
++++++++++
.. automodule:: aiida.orm.data.singlefile
   :members:

Upf
+++
.. automodule:: aiida.orm.data.upf
   :members:

Cif
+++
.. automodule:: aiida.orm.data.cif
   :members:

Parameter
+++++++++
.. automodule:: aiida.orm.data.parameter
   :members:

Remote
++++++
.. automodule:: aiida.orm.data.remote
   :members:

ArrayData
+++++++++
.. automodule:: aiida.orm.data.array
   :members:

ArrayData subclasses
--------------------
The following are Data classes inheriting from ArrayData.

KpointsData
...........
.. automodule:: aiida.orm.data.array.kpoints
   :members:

TrajectoryData
..............
.. automodule:: aiida.orm.data.array.trajectory
   :members:



ORM documentation: Calculations
===============================

.. automodule:: aiida.orm.calculation
   :members:
   :special-members: __init__

.. automodule:: aiida.orm.calculation.inline
   :members:
   :special-members: __init__

.. automodule:: aiida.orm.calculation.job
   :members:
   :special-members: __init__

Quantum ESPRESSO
++++++++++++++++

Quantum Espresso - pw.x
-----------------------
.. automodule:: aiida.orm.calculation.job.quantumespresso.pw
   :members:

.. automodule:: aiida.orm.calculation.job.quantumespresso.helpers
   :members:

Quantum Espresso - Dos
----------------------
.. automodule:: aiida.orm.calculation.job.quantumespresso.dos
   :members:
   :special-members: __init__

Quantum Espresso - Projwfc
--------------------------
.. automodule:: aiida.orm.calculation.job.quantumespresso.projwfc
   :members:
   :special-members: __init__

Quantum Espresso - PW immigrant
-------------------------------
.. automodule:: aiida.orm.calculation.job.quantumespresso.pwimmigrant
   :members:
   :special-members: __init__

Wannier90  - Wannier90
++++++++++++++++++++++
.. automodule:: aiida.orm.calculation.job.wannier90
   :members:
   :special-members: __init__

TemplateReplacer
++++++++++++++++
.. automodule:: aiida.orm.calculation.job.simpleplugins.templatereplacer
   :members:
