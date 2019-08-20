Caching: implementation details
+++++++++++++++++++++++++++++++

This section covers some details of the caching mechanism which are not discussed in the :ref:`user guide <caching>`.
If you are developing a plugin and want to modify the caching behavior of your classes, we recommend you read :ref:`this section <caching_matches>` first.

Disabling caching for ``WorkflowNode``
--------------------------------------

As discussed in the :ref:`user guide <caching_provenance>`, nodes which can have ``RETURN`` links cannot be cached.
This is enforced on two levels:

    * The ``_cachable`` property is set to ``False`` in the :class:`~aiida.orm.nodes.process.ProcessNode`, and only re-enabled in the :class:`~aiida.orm.nodes.process.calculation.calculation.CalculationNode` sub class.
      This means that all calculation nodes and its sub classes :class:`~aiida.orm.nodes.process.calculation.calcjob.CalcJobNode` and :class:`~aiida.orm.nodes.process.calculation.calcfunction.CalcFunctionNode` are cachable, but the :class:`~aiida.orm.nodes.process.workflow.workflow.WorkflowNode` is not.
    * The ``_store_from_cache`` method, which is used to "clone" an existing node, will raise an error if the source node has any ``RETURN`` links.
      This extra safe-guard prevents cases where a user might incorrectly override the ``_cachable`` property on a ``WorkflowNode`` sub class.
