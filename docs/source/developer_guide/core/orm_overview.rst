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

.. automodule:: aiida.orm.nodes
   :members:
   :noindex:

.. autoclass:: aiida.orm.nodes.node.Node
   :noindex:


Code
++++
.. automodule:: aiida.orm.nodes.data.code
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

.. automodule:: aiida.orm.nodes.data
   :members:
   :noindex:
   :private-members: _exportcontent

.. _my-ref-to-structure:

Structure
+++++++++
.. automodule:: aiida.orm.nodes.data.structure
   :members:
   :noindex:
   :special-members: __init__

Folder
++++++
.. automodule:: aiida.orm.nodes.data.folder
   :members:
   :noindex:

Singlefile
++++++++++
.. automodule:: aiida.orm.nodes.data.singlefile
   :members:
   :noindex:

Upf
+++
.. automodule:: aiida.orm.nodes.data.upf
   :members:
   :noindex:

Cif
+++
.. automodule:: aiida.orm.nodes.data.cif
   :members:
   :noindex:

Parameter
+++++++++
.. automodule:: aiida.orm.nodes.data.dict
   :members:
   :noindex:

Remote
++++++
.. automodule:: aiida.orm.nodes.data.remote
   :members:
   :noindex:

OrbitalData
+++++++++++
.. automodule:: aiida.orm.nodes.data.orbital
   :members:
   :noindex:

ArrayData
+++++++++
.. automodule:: aiida.orm.nodes.data.array
   :members:
   :noindex:

ArrayData subclasses
--------------------
The following are Data classes inheriting from ArrayData.

KpointsData
...........
.. automodule:: aiida.orm.nodes.data.array.kpoints
   :members:
   :noindex:
   :private-members:

BandsData
.........
.. automodule:: aiida.orm.nodes.data.array.bands
   :members:
   :noindex:

ProjectionData
..............
.. automodule:: aiida.orm.nodes.data.array.projection
   :members:
   :noindex:

TrajectoryData
..............
.. automodule:: aiida.orm.nodes.data.array.trajectory
   :members:
   :noindex:

XyData
..............
.. automodule:: aiida.orm.nodes.data.array.xy
   :members:
   :noindex:

Base data types
+++++++++++++++

BaseType and NumericType
------------------------
.. automodule:: aiida.orm.nodes.data.base
   :members:
   :noindex:

List
----
.. autoclass:: aiida.orm.nodes.data.list.List
   :members:
   :noindex:


Bool
----
.. automodule:: aiida.orm.nodes.data.bool
   :members:
   :noindex:


Float
-----
.. automodule:: aiida.orm.nodes.data.float
   :members:
   :noindex:


Int
---
.. automodule:: aiida.orm.nodes.data.int
   :members:
   :noindex:


Str
---
.. automodule:: aiida.orm.nodes.data.str
   :members:
   :noindex:



ORM documentation: Calculations
===============================

.. note:: This list only includes the classes included in AiiDA-core. For all the plugin subclasses,
  check the corresponding plugin repositories.

.. automodule:: aiida.orm.nodes.process
   :members:
   :noindex:
   :special-members: __init__

.. automodule:: aiida.orm.nodes.process.calculation.calcjob
   :members:
   :noindex:
   :special-members: __init__

TemplateReplacer
++++++++++++++++
.. automodule:: aiida.calculations.plugins.templatereplacer
   :members:
   :noindex:

