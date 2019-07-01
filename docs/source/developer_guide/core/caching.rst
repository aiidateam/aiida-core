Caching: implementation details
+++++++++++++++++++++++++++++++

This section covers some details of the caching mechanism which are not discussed in the :ref:`user guide <caching>`. If you are developing a plugin and want to modify the caching behavior of your classes, we recommend you read :ref:`this section <caching_matches>` first.

Controlling caching
-------------------

When developing calculation and data classes, there are some methods you can use to determine how the hash is created:

* To ignore specific attributes, a ``Node`` subclass can have a ``_hash_ignored_attributes`` attribute. This is a list of attribute names which are ignored when creating the hash.
* For calculations, the ``_hash_ignored_inputs`` attribute lists inputs that should be ignored when creating the hash.
* To add things which should be considered in the hash, you can override the :meth:`_get_objects_to_hash <aiida.orm.nodes.Node._get_objects_to_hash>` method. Note that doing so overrides the behavior described above, so you should make sure to use the ``super()`` method.
* Pass a keyword argument to :meth:`.get_hash <aiida.orm.nodes.Node.get_hash>`. These are passed on to ``aiida.common.hashing.make_hash``. For example, the ``ignored_folder_content`` keyword is used by the :class:`JobCalculation <aiida.orm.nodes.process.calculation.calcjob.CalcJobNode>` to ignore the ``raw_input`` subfolder of its repository folder.

Additionally, there are two methods you can use to disable caching for particular nodes:

* The :meth:`~aiida.orm.nodes.Node.is_valid_cache` property determines whether a particular node can be used as a cache. This is used for example to disable caching from failed calculations.
* Node classes have a ``_cachable`` attribute, which can be set to ``False`` to completely switch off caching for nodes of that class. This avoids performing queries for the hash altogether.

Finally an important remark: There are two ways in which the hash match can go wrong: False negatives, where two nodes should have the same hash but do not, or false positives, where two different nodes have the same hash. 
False negatives are **highly preferrable** because they only increase the runtime of your calculations, while false positives can lead to wrong results. 
Be mindful of this when modifying the caching behaviour of your calculation and data classes.


Disabling caching for ``WorkflowNode``
--------------------------------------

As discussed in the :ref:`user guide <caching_provenance>`, nodes which can have ``RETURN`` links cannot be cached. This is enforced on two levels:

* The ``_cachable`` property is set to ``False`` in the :class:`aiida.orm.nodes.process.ProcessNode`, and only re-enabled in :class:`aiida.orm.nodes.process.calculation.calcjob.CalcJobNode` and :class:`CalcFunctionNode <aiida.orm.nodes.process.calculation.calcfunction.CalcFunctionNode>`. This means that a ``WorkflowNode`` will not be cached.
* The ``_store_from_cache`` method, which is used to "clone" an existing node, will raise an error if the existing node has any ``RETURN`` links. This extra safe-guard prevents cases where a user might incorrectly override the ``_cachable`` property on a ``WorkflowNode`` subclass.
