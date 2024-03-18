.. _internal_architecture:engine:

******
Engine
******



.. _internal_architecture:engine:caching:

Controlling caching
-------------------

.. important::

    This section covers some details of the caching mechanism which are not discussed in the :ref:`topics section <topics:provenance:caching>`.
    If you are developing plugins and want to modify the caching behavior of your classes, we recommend you read that section first.

There are several methods which the internal classes of AiiDA use to control the caching mechanism:

On the level of the generic :class:`orm.Node <aiida.orm.Node>` class:

* The :meth:`~aiida.orm.nodes.caching.NodeCaching.is_valid_cache` property determines whether a particular node can be used as a cache.
  This is used for example to disable caching from failed calculations.
* Node classes have a ``_cachable`` attribute, which can be set to ``False`` to completely switch off caching for nodes of that class.
  This avoids performing queries for the hash altogether.

On the level of the :class:`Process <aiida.engine.processes.process.Process>` and :class:`orm.ProcessNode <aiida.orm.ProcessNode>` classes:

* The :meth:`ProcessNodeCaching.is_valid_cache <aiida.orm.nodes.process.process.ProcessNodeCaching.is_valid_cache>` calls :meth:`Process.is_valid_cache <aiida.engine.processes.process.Process.is_valid_cache>`, passing the node itself.
  This can be used in :class:`~aiida.engine.processes.process.Process` subclasses (e.g. in calculation plugins) to implement custom ways of invalidating the cache.
* The :meth:`ProcessNodeCaching._hash_ignored_inputs <aiida.orm.nodes.process.process.ProcessNodeCaching._hash_ignored_inputs>` attribute lists the inputs that should be ignored when creating the hash.
  This is checked by the :meth:`ProcessNodeCaching.get_objects_to_hash <aiida.orm.nodes.process.process.ProcessNodeCaching.get_objects_to_hash>` method.
* The :meth:`Process.is_valid_cache <aiida.engine.processes.process.Process.is_valid_cache>` is where the :meth:`exit_codes <aiida.engine.processes.process_spec.ProcessSpec.exit_code>` that have been marked by ``invalidates_cache`` are checked.


The ``WorkflowNode`` example
............................

As discussed in the :ref:`topic section <topics:provenance:caching:limitations>`, nodes which can have ``RETURN`` links cannot be cached.
This is enforced on two levels:

* The ``_cachable`` property is set to ``False`` in the :class:`~aiida.orm.Node`, and only re-enabled in :class:`~aiida.orm.nodes.process.calculation.calculation.CalculationNode` (which affects CalcJobs and calcfunctions).
  This means that a :class:`~aiida.orm.nodes.process.workflow.workflow.WorkflowNode` will not be cached.
* The ``_store_from_cache`` method, which is used to "clone" an existing node, will raise an error if the existing node has any ``RETURN`` links.
  This extra safe-guard prevents cases where a user might incorrectly override the ``_cachable`` property on a ``WorkflowNode`` subclass.


.. _#4038: https://github.com/aiidateam/aiida-core/issues/4038
