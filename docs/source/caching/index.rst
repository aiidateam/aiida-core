.. _caching:

Caching
=======

When working with AiiDA, you might sometimes re-run calculations which were already successfully executed. Because this can waste a lot of computational resources, you can enable AiiDA to **cache** calculations, which means that it will re-use existing calculations if a calculation with the same inputs is submitted again.

When a calculation is cached, a copy of the original calculation is created. This copy will keep the input links of the new calculation. The outputs of the original calculation are also copied, and linked to the new calculation. This allows for the new calculation to be a separate Node in the provenance graph and, critically, preserves the acyclicity of the graph.

Caching is also implemented for Data nodes. This is not very useful in practice (yet), but is an easy way to show how the caching mechanism works:

.. ipython::
    :verbatim:

    In [1]: from __future__ import print_function

    In [2]: from aiida.orm.data.base import Str

    In [3]: n1 = Str('test string')

    In [4]: n1.store()
    Out[4]: u'test string'

    In [5]: n2 = Str('test string')

    In [6]: n2.store(use_cache=True)
    Out[6]: u'test string'

    In [7]: print('UUID of n1:', n1.uuid)
    UUID of n1: 956109e1-4382-4240-a711-2a4f3b522122

    In [8]: print('n2 is cached from:', n2.get_extra('cached_from'))
    n2 is cached from: 956109e1-4382-4240-a711-2a4f3b522122

As you can see, passing ``use_cache=True`` to the ``store`` method enables using the cache. The fact that ``n2`` was created from ``n1`` is stored in the ``cached_from`` extra of ``n2``.

When running a ``JobCalculation`` through the ``Process`` interface, you cannot directly set the ``use_cache`` flag the calculation node is stored internally. Instead, you can pass the ``_use_cache`` flag to the ``run`` or ``submit`` method.

Caching is **not** implemented for workchains and workfunctions. Unlike calculations, they can not only create new data nodes, but only return exsting ones. When copying a cached workchain, it's not clear which node should be returned without actually running the workchain.

Configuration
-------------

Of course, using caching would be quite tedious if you had to set ``use_cache`` manually everywhere. To fix this, the default for ``use_cache`` can be set in the ``.aiida/cache_config.yml`` file. You can specify a global default, or enable / disable caching for specific calculation or data classes. An example configuration file might look like this:

.. code:: yaml

    profile-name:
      default: False
      enabled:
        - aiida.orm.calculation.job.simpleplugins.templatereplacer.TemplatereplacerCalculation
        - aiida.orm.data.base.Str
      disabled:
        - aiida.orm.data.base.Float

This means that caching is enabled for ``TemplatereplacerCalculation`` and ``Str``, and disabled for all other classes. In this example, manually disabling ``aiida.orm.data.base.Float`` is actually not needed, since the default value for all classes is already ``False``. Note also that the fully qualified class import name (e.g., ``aiida.orm.data.base.Str``) must be given, not just the class name (``Str``). This is to avoid accidentally matching classes with the same name.

How are cached nodes matched?
-----------------------------

To determine wheter a given node is identical to an existing one, a hash of the content of the node is created. If a node of the same class with the same hash already exists in the database, this is considered a cache match. You can manually check the hash of a given node with the :meth:`.get_hash() <.AbstractNode.get_hash>` method.

By default, this hash is created from:

* all attributes of a node, except the ``_updatable_attributes``
* the ``__version__`` of the module which defines the node class
* the content of the repository folder of the node

In the case of calculations, the hashes of the inputs are also included. When developing calculation and data classes, there are some methods you can use to determine how the hash is created:

* To ignore specific attributes, a ``Node`` subclass can have a ``_hash_ignored_attributes`` attribute. This is a list of attribute names which are ignored when creating the hash.
* To add things which should be considered in the hash, you can override the :meth:`_get_objects_to_hash <.AbstractNode._get_objects_to_hash>` method. Note that doing so overrides the behavior described above, so you should make sure to use the ``super()`` method.
* Pass a keyword argument to :meth:`.get_hash <.AbstractNode.get_hash>`. These are passed on to ``aiida.common.hashing.make_hash``. For example, the ``ignored_folder_content`` keyword is used by the :class:`JobCalculation <.AbstractJobCalculation>` to ignore the ``raw_input`` subfolder of its repository folder.

Additionally, there are two methods you can use to disable caching for particular nodes:

* The :meth:`._is_valid_cache` method determines whether a particular node can be used as a cache. This is used for example to disable caching from failed calculations.
* Node classes have a ``_cacheable`` attribute, which can be set to ``False`` to completely switch off caching for nodes of that class. This avoids performing queries for the hash altogether.
