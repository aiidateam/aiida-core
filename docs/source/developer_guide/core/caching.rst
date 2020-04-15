Caching: implementation details
+++++++++++++++++++++++++++++++

This section covers some details of the caching mechanism which are not discussed in the :ref:`user guide <caching>`.
If you are developing plugins and want to modify the caching behavior of your classes, we recommend you read :ref:`this section <caching_matches>` first.

.. _devel_controlling_hashing:

Controlling hashing
-------------------

Below are some methods you can use to control how the hashes of calculation and data classes are computed:

* To ignore specific attributes, a :py:class:`~aiida.orm.nodes.Node` subclass can have a ``_hash_ignored_attributes`` attribute.
  This is a list of attribute names, which are ignored when creating the hash.
* For calculations, the ``_hash_ignored_inputs`` attribute lists inputs that should be ignored when creating the hash.
* To add things which should be considered in the hash, you can override the :meth:`~aiida.orm.nodes.Node._get_objects_to_hash` method. Note that doing so overrides the behavior described above, so you should make sure to use the ``super()`` method.
* Pass a keyword argument to :meth:`~aiida.orm.nodes.Node.get_hash`.
  These are passed on to :meth:`~aiida.common.hashing.make_hash`.

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

Design guidelines
-----------------

When modifying the hashing/caching behaviour of your classes, keep in mind that cache matches can go wrong in two ways:

* False negatives, where two nodes *should* have the same hash but do not
* False positives, where two different nodes get the same hash by mistake

False negatives are **highly preferrable** because they only increase the runtime of your calculations, while false positives can lead to wrong results.
