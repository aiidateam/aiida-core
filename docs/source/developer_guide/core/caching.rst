Caching: implementation details
+++++++++++++++++++++++++++++++

This section covers some details of the caching mechanism which are not discussed in the :ref:`user guide <caching>`. If you are developing a plugin and want to modify the caching behavior of your classes, we recommend you read :ref:`this section <caching_matches>` first.

Disabling caching for ``WorkflowNode``
--------------------------------------

As discussed in the :ref:`user guide <caching_provenance>`, nodes which can have ``RETURN`` links cannot be cached. This is enforced on two levels:

* The ``_cacheable`` property is set to ``False`` in the :class:`aiida.orm.node.process.process.ProcessNode`, and only re-enabled in :class:`aiida.orm.node.process.calculation.calcjob.CalcJobNode` and :class:`CalcFunctionNode <aiida.orm.node.process.calculation.calcfunction.CalcFunctionNode>`. This means that a ``WorkflowNode`` will not be cached.
* The ``_store_from_cache`` method, which is used to "clone" an existing node, will raise an error if the existing node has any ``RETURN`` links. This extra safe-guard prevents cases where a user might incorrectly override the ``_cacheable`` property on a ``WorkflowNode`` subclass.
