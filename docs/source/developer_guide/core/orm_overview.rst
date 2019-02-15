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

.. automodule:: aiida.orm.groups
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

.. automodule:: aiida.orm.node
   :members:
   :noindex:

.. autoclass:: aiida.orm.node.Node
   :noindex:


Code
++++
.. automodule:: aiida.orm.node.data.code
   :members:
   :noindex:
   :special-members: __init__


Mixins
++++++
.. automodule:: aiida.orm.utils.mixins
   :members:
   :noindex:

.. autoclass:: aiida.orm.utils.mixins.Sealable
   :noindex:

ORM documentation: Data
=======================

.. note:: This list only includes the classes included in AiiDA-core. For all the plugin subclasses,
  check the corresponding plugin repositories.

.. automodule:: aiida.orm.node.data
   :members:
   :noindex:
   :private-members: _exportcontent

.. _my-ref-to-structure:

Structure
+++++++++
.. automodule:: aiida.orm.node.data.structure
   :members:
   :noindex:
   :special-members: __init__

Folder
++++++
.. automodule:: aiida.orm.node.data.folder
   :members:
   :noindex:

Singlefile
++++++++++
.. automodule:: aiida.orm.node.data.singlefile
   :members:
   :noindex:

Upf
+++
.. automodule:: aiida.orm.node.data.upf
   :members:
   :noindex:

Cif
+++
.. automodule:: aiida.orm.node.data.cif
   :members:
   :noindex:

Parameter
+++++++++
.. automodule:: aiida.orm.node.data.parameter
   :members:
   :noindex:

Remote
++++++
.. automodule:: aiida.orm.node.data.remote
   :members:
   :noindex:

OrbitalData
+++++++++++
.. automodule:: aiida.orm.node.data.orbital
   :members:
   :noindex:

ArrayData
+++++++++
.. automodule:: aiida.orm.node.data.array
   :members:
   :noindex:

ArrayData subclasses
--------------------
The following are Data classes inheriting from ArrayData.

KpointsData
...........
.. automodule:: aiida.orm.node.data.array.kpoints
   :members:
   :noindex:
   :private-members:

BandsData
.........
.. automodule:: aiida.orm.node.data.array.bands
   :members:
   :noindex:

ProjectionData
..............
.. automodule:: aiida.orm.node.data.array.projection
   :members:
   :noindex:

TrajectoryData
..............
.. automodule:: aiida.orm.node.data.array.trajectory
   :members:
   :noindex:

XyData
..............
.. automodule:: aiida.orm.node.data.array.xy
   :members:
   :noindex:

Base data types
+++++++++++++++

BaseType and NumericType
------------------------
.. automodule:: aiida.orm.node.data.base
   :members:
   :noindex:

List
----
.. autoclass:: aiida.orm.node.data.list.List
   :members:
   :noindex:


Bool
----
.. automodule:: aiida.orm.node.data.bool
   :members:
   :noindex:


Float
-----
.. automodule:: aiida.orm.node.data.float
   :members:
   :noindex:


Int
---
.. automodule:: aiida.orm.node.data.int
   :members:
   :noindex:


Str
---
.. automodule:: aiida.orm.node.data.str
   :members:
   :noindex:



ORM documentation: Calculations
===============================

.. note:: This list only includes the classes included in AiiDA-core. For all the plugin subclasses,
  check the corresponding plugin repositories.

.. automodule:: aiida.orm.node.process
   :members:
   :noindex:
   :special-members: __init__

.. automodule:: aiida.orm.node.process.calculation.calcjob
   :members:
   :noindex:
   :special-members: __init__

TemplateReplacer
++++++++++++++++
.. automodule:: aiida.calculations.plugins.templatereplacer
   :members:
   :noindex:

