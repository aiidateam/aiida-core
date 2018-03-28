Caching: implementation details
+++++++++++++++++++++++++++++++

This section covers some details of the caching mechanism which are not discussed in the :ref:`user guide <caching>`. If you are developing a plugin and want to modify the caching behavior of your classes, we recommend you read :ref:`this section <caching_matches>` first.

Disabling caching for ``WorkCalculation``
-----------------------------------------

As discussed in the :ref:`user guide <caching_provenance>`, nodes which can have ``RETURN`` links cannot be cached. This is enforced on two levels:

* The ``_cacheable`` property is set to ``False`` in the :class:`.AbstractCalculation`, and only re-enabled in :class:`.AbstractJobCalculation` and :class:`InlineCalculation <.general.calculation.inline.InlineCalculation>`. This means that a ``WorkCalculation`` will not be cached.
* The ``_store_from_cache`` method, which is used to "clone" an existing node, will raise an error if the existing node has any ``RETURN`` links. This extra safe-guard prevents cases where a user might incorrectly override the ``_cacheable`` property on a ``WorkCalculation`` subclass.
