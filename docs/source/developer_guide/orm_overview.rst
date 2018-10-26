ORM documentation: generic aiida.orm
====================================

.. toctree::
   :maxdepth: 3

Some generic methods of the module aiida.orm.utils

.. automodule:: aiida.orm.utils
   :members:
   :noindex:
   :special-members: __init__

Computer
++++++++

.. automodule:: aiida.orm.computers
   :members:
   :noindex:
   :private-members:

Group
+++++

.. automodule:: aiida.orm.implementation.general.group
   :members:
   :noindex:
   :private-members:

User
++++

.. automodule:: aiida.orm.users
   :members:
   :noindex:
   :private-members:

Node
++++

.. automodule:: aiida.orm.implementation.general.node
   :members:
   :noindex:
   :private-members:
   :special-members:


.. automodule:: aiida.orm.node
   :members:
   :noindex:

.. autoclass:: aiida.orm.node.Node
   :noindex:

Workflow
++++++++
.. automodule:: aiida.orm.implementation.general.workflow
   :members:
   :noindex:


Code
++++
.. automodule:: aiida.orm.implementation.general.code
   :members:
   :noindex:
   :special-members: __init__


Mixins
++++++
.. automodule:: aiida.orm.mixins
   :members:
   :noindex:

.. autoclass:: aiida.orm.mixins.Sealable
   :noindex:

ORM documentation: Data
=======================

.. note:: This list only includes the classes included in AiiDA-core. For all the plugin subclasses,
  check the corresponding plugin repositories.

.. automodule:: aiida.orm.data
   :members:
   :noindex:
   :private-members: _exportcontent

.. _my-ref-to-structure:

Structure
+++++++++
.. automodule:: aiida.orm.data.structure
   :members:
   :noindex:
   :special-members: __init__

Folder
++++++
.. automodule:: aiida.orm.data.folder
   :members:
   :noindex:

Singlefile
++++++++++
.. automodule:: aiida.orm.data.singlefile
   :members:
   :noindex:

Upf
+++
.. automodule:: aiida.orm.data.upf
   :members:
   :noindex:

Cif
+++
.. automodule:: aiida.orm.data.cif
   :members:
   :noindex:

Parameter
+++++++++
.. automodule:: aiida.orm.data.parameter
   :members:
   :noindex:

Remote
++++++
.. automodule:: aiida.orm.data.remote
   :members:
   :noindex:

OrbitalData
+++++++++++
.. automodule:: aiida.orm.data.orbital
   :members:
   :noindex:

ArrayData
+++++++++
.. automodule:: aiida.orm.data.array
   :members:
   :noindex:

ArrayData subclasses
--------------------
The following are Data classes inheriting from ArrayData.

KpointsData
...........
.. automodule:: aiida.orm.data.array.kpoints
   :members:
   :noindex:
   :private-members:

BandsData
.........
.. automodule:: aiida.orm.data.array.bands
   :members:
   :noindex:

ProjectionData
..............
.. automodule:: aiida.orm.data.array.projection
   :members:
   :noindex:

TrajectoryData
..............
.. automodule:: aiida.orm.data.array.trajectory
   :members:
   :noindex:

XyData
..............
.. automodule:: aiida.orm.data.array.xy
   :members:
   :noindex:

Base data types
+++++++++++++++

BaseType and NumericType
------------------------
.. automodule:: aiida.orm.data.base
   :members:
   :noindex:

List
----
.. autoclass:: aiida.orm.data.list.List
   :members:
   :noindex:


Bool
----
.. automodule:: aiida.orm.data.bool
   :members:
   :noindex:


Float
-----
.. automodule:: aiida.orm.data.float
   :members:
   :noindex:


Int
---
.. automodule:: aiida.orm.data.int
   :members:
   :noindex:


Str
---
.. automodule:: aiida.orm.data.str
   :members:
   :noindex:



ORM documentation: Calculations
===============================

.. note:: This list only includes the classes included in AiiDA-core. For all the plugin subclasses,
  check the corresponding plugin repositories.

.. automodule:: aiida.orm.implementation.general.calculation
   :members:
   :noindex:
   :special-members: __init__

.. automodule:: aiida.orm.calculation.inline
   :members:
   :noindex:
   :special-members: __init__

.. automodule:: aiida.orm.implementation.general.calculation.job
   :members:
   :noindex:
   :special-members: __init__

.. automodule:: aiida.orm.implementation.general.calculation.inline
   :members:
   :noindex:
   :special-members: __init__

.. automodule:: aiida.orm.calculation
   :members:
   :noindex:
   :special-members: __init__

TemplateReplacer
++++++++++++++++
.. automodule:: aiida.orm.calculation.job.simpleplugins.templatereplacer
   :members:
   :noindex:

