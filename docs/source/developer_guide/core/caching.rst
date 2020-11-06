Caching: implementation details
+++++++++++++++++++++++++++++++

This section covers some details of the caching mechanism which are not discussed in the :ref:`user guide <topics:provenance:caching>`.
If you are developing plugins and want to modify the caching behavior of your classes, we recommend you read :ref:`this section <topics:provenance:caching:hashing>` first.

.. _devel_controlling_caching:

Controlling caching
-------------------

There are several methods you can use to disable caching for particular nodes:

On the level of generic :class:`aiida.orm.nodes.Node`:

* The :meth:`~aiida.orm.nodes.Node.is_valid_cache` property determines whether a particular node can be used as a cache. This is used for example to disable caching from failed calculations.
* Node classes have a ``_cachable`` attribute, which can be set to ``False`` to completely switch off caching for nodes of that class. This avoids performing queries for the hash altogether.

On the level of :class:`aiida.engine.processes.process.Process` and :class:`aiida.orm.nodes.process.ProcessNode`:

* The :meth:`ProcessNode.is_valid_cache <aiida.orm.nodes.process.ProcessNode.is_valid_cache>` calls :meth:`Process.is_valid_cache <aiida.engine.processes.process.Process.is_valid_cache>`, passing the node itself. This can be used in :class:`~aiida.engine.processes.process.Process` subclasses (e.g. in calculation plugins) to implement custom ways of invalidating the cache.
* The ``spec.exit_code`` has a keyword argument ``invalidates_cache``. If this is set to ``True``, returning that exit code means the process is no longer considered a valid cache. This is implemented in :meth:`Process.is_valid_cache <aiida.engine.processes.process.Process.is_valid_cache>`.


The ``WorkflowNode`` example
............................

As discussed in the :ref:`user guide <caching_limitations>`, nodes which can have ``RETURN`` links cannot be cached.
This is enforced on two levels:

* The ``_cachable`` property is set to ``False`` in the :class:`~aiida.orm.nodes.Node`, and only re-enabled in :class:`~aiida.orm.nodes.process.calculation.calculation.CalculationNode` (which affects CalcJobs and calcfunctions).
  This means that a :class:`~aiida.orm.nodes.process.workflow.workflow.WorkflowNode` will not be cached.
* The ``_store_from_cache`` method, which is used to "clone" an existing node, will raise an error if the existing node has any ``RETURN`` links.
  This extra safe-guard prevents cases where a user might incorrectly override the ``_cachable`` property on a ``WorkflowNode`` subclass.
