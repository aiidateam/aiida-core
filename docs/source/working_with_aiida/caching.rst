.. _caching:

*******
Caching
*******

When working with AiiDA, you might sometimes re-run calculations which were already successfully executed. Because this can waste a lot of computational resources, you can enable AiiDA to **cache** calculations, which means that it will re-use existing calculations if a calculation with the same inputs is submitted again.

When a calculation is cached, a copy of the original calculation is created. This copy will keep the input links of the new calculation. The outputs of the original calculation are also copied, and linked to the new calculation. This allows for the new calculation to be a separate Node in the provenance graph and, critically, preserves the acyclicity of the graph.

Caching is also implemented for Data nodes. This is not very useful in practice (yet), but is an easy way to show how the caching mechanism works:

.. ipython::
    :verbatim:

    In [1]: from __future__ import print_function

    In [2]: from aiida.orm import Str

    In [3]: n1 = Str('test string')

    In [4]: n1.store()
    Out[4]: u'test string'

    In [5]: n2 = Str('test string')

    In [6]: n2.store(use_cache=True)
    Out[6]: u'test string'

    In [7]: print('UUID of n1:', n1.uuid)
    UUID of n1: 956109e1-4382-4240-a711-2a4f3b522122

    In [8]: print('n2 is cached from:', n2.get_extra('_aiida_cached_from'))
    n2 is cached from: 956109e1-4382-4240-a711-2a4f3b522122

As you can see, passing ``use_cache=True`` to the ``store`` method enables using the cache. The fact that ``n2`` was created from ``n1`` is stored in the ``_aiida_cached_from`` extra of ``n2``.

When running a ``CalcJob`` through the ``Process`` interface, you cannot directly set the ``use_cache`` flag when the calculation node is stored internally. Instead, you can pass the ``_use_cache`` flag to the ``run`` or ``submit`` method.

Caching is **not** implemented for workchains and workfunctions. Unlike calculations, they can not only create new data nodes, but also return exsting ones. When copying a cached workchain, it's not clear which node should be returned without actually running the workchain. This is explained in more detail in the section :ref:`caching_provenance`.

Configuration
-------------

Of course, using caching would be quite tedious if you had to set ``use_cache`` manually everywhere. To fix this, the default for ``use_cache`` can be set in the ``.aiida/cache_config.yml`` file. You can specify a global default, or enable / disable caching for specific calculation or data classes. An example configuration file might look like this:

.. code:: yaml

    profile-name:
      default: False
      enabled:
        - aiida.calculations.plugins.templatereplacer.TemplatereplacerCalculation
        - aiida.orm.nodes.data.str.Str
      disabled:
        - aiida.orm.nodes.data.float.Float

This means that caching is enabled for ``TemplatereplacerCalculation`` and ``Str``, and disabled for all other classes. In this example, manually disabling ``aiida.orm.nodes.data.float.Float`` is actually not needed, since the ``default: False`` configuration means that caching is disabled for all classes unless it is manually enabled. Note also that the fully qualified class import name (e.g., ``aiida.orm.nodes.data.str.Str``) must be given, not just the class name (``Str``). This is to avoid accidentally matching classes with the same name. You can get this name by combining the module name and class name, or (usually) from the string representation of the class:

.. ipython::
    :verbatim:

    In [1]: Str.__module__ + '.' + Str.__name__
    Out[1]: 'aiida.orm.nodes.data.str.Str'

    In [2]: str(Str)
    Out[2]: "<class 'aiida.orm.nodes.data.str.Str'>"

Note that this is not the same as the type string stored in the database.

.. _caching_matches:

How are cached nodes matched?
-----------------------------

To determine wheter a given node is identical to an existing one, a hash of the content of the node is created. If a node of the same class with the same hash already exists in the database, this is considered a cache match. You can manually check the hash of a given node with the :meth:`.get_hash() <aiida.orm.nodes.Node.get_hash>` method. Once a node is stored in the database, its hash is stored in the ``_aiida_hash`` extra, and this is used to find matching nodes.

By default, this hash is created from:

* all attributes of a node, except the ``_updatable_attributes``
* the ``__version__`` of the module which defines the node class
* the content of the repository folder of the node
* the UUID of the computer, if the node has one

In the case of calculations, the hashes of the inputs are also included. When developing calculation and data classes, there are some methods you can use to determine how the hash is created:

* To ignore specific attributes, a ``Node`` subclass can have a ``_hash_ignored_attributes`` attribute. This is a list of attribute names which are ignored when creating the hash.
* For calculations, the ``_hash_ignored_inputs`` attribute lists inputs that should be ignored when creating the hash.
* To add things which should be considered in the hash, you can override the :meth:`_get_objects_to_hash <aiida.orm.nodes.Node._get_objects_to_hash>` method. Note that doing so overrides the behavior described above, so you should make sure to use the ``super()`` method.
* Pass a keyword argument to :meth:`.get_hash <aiida.orm.nodes.Node.get_hash>`. These are passed on to ``aiida.common.hashing.make_hash``. For example, the ``ignored_folder_content`` keyword is used by the :class:`JobCalculation <aiida.orm.nodes.process.calculation.calcjob.CalcJobNode>` to ignore the ``raw_input`` subfolder of its repository folder.

Additionally, there are two methods you can use to disable caching for particular nodes:

* The :meth:`~aiida.orm.nodes.Node.is_valid_cache` property determines whether a particular node can be used as a cache. This is used for example to disable caching from failed calculations.
* Node classes have a ``_cachable`` attribute, which can be set to ``False`` to completely switch off caching for nodes of that class. This avoids performing queries for the hash altogether.

There are two ways in which the hash match can go wrong: False negatives, where two nodes should have the same hash but do not, or false positives, where two different nodes have the same hash. It is important to understand that false negatives are **highly preferrable**, because they only increase the runtime of your calculations, as if caching was disabled. False positives however can break the logic of your calculations. Be mindful of this when modifying the caching behaviour of your calculation and data classes.

.. _caching_error:

What to do when caching is used when it shouldn't
-------------------------------------------------

In general, the caching mechanism should trigger only when the output of a calculation will be exactly the same as if it is run again. However, there might be some edge cases where this is not true.

For example, if the parser is in a different python module than the calculation, the version number used in the hash will not change when the parser is updated. While the "correct" solution to this problem is to increase the version number of a calculation when the behavior of its parser changes, there might still be cases (e.g. during development) when you manually want to stop a particular node from being cached.

In such cases, you can follow these steps to disable caching:

1. If you suspect that a node has been cached in error, check that it has a ``_aiida_cached_from`` extra. If that's not the case, it is not a problem of caching.
2. Get all nodes which match your node, and clear their hash:

    .. code:: python

        for n in node.get_all_same_nodes():
            n.clear_hash()
3. Run your calculation again. Now it should not use caching.

If you instead think that there is a bug in the AiiDA implementation, please open an issue (with enough information to be able to reproduce the error, otherwise it is hard for us to help you) in the AiiDA GitHub repository: https://github.com/aiidateam/aiida-core/issues/new.

.. _caching_provenance:

Caching and the Provenance Graph
--------------------------------

The goal of the caching mechanism is to speed up AiiDA calculations by re-using duplicate calculations. However, the resulting provenance graph should be exactly the same as if caching was disabled. This has important consequences on the kind of caching operations that are possible.

The provenance graph consists of nodes describing data, calculations and workchains, and links describing the relationship between these nodes. We have seen that the hash of a node is used to determine whether two nodes are equivalent. To successfully use a cached node however, we also need to know how the new node should be linked to its parents and children.

In the case of a plain data node, this is simple: Copying a data node from an equivalent node should not change its links, so we just need to preserve the links which this new node already has.

For calculations, the situation is a bit more complex: The node can have inputs and creates new data nodes as outputs. Again, the new node needs to keep its existing links. For the outputs, the calculation needs to create a copy of each node and link these as its outputs. This makes it look as if the calculation had produced these outputs itself, without caching.

Finally, workchains can create links not only to nodes which they create themselves, but also to nodes created by a calculation that they called, or even their ancestors. This is where caching becomes impossible. Consider the following example (using workfunctions for simplicity):

.. code:: python

    from aiida.engine import workfunction
    from aiida.orm import Int

    @workfunction
    def select(a, b):
        return b

    d = Int(1)
    r1 = select(d, d)
    r2 = select(Int(1), Int(1))

The two ``select`` workfunctions have the same inputs as far as their hashes go. However, the first call uses the same input node twice, while the second one has two different inputs. If the second call should be cached from the first one, it is not clear which of the two input nodes should be returned.

While this example might seem contrived, the conclusion is valid more generally: Because workchains can return nodes from their history, they cannot be cached. Since even two equivalent workchains (with the same inputs) can have a different history, there is no way to deduce which links should be created on the new workchain without actually running it.

Overall, this limitation is acceptable: The runtime of AiiDA workchains is usually dominated by time spent inside expensive calculations. Since these can be avoided with the caching mechanism, it still improves the runtime and required computer resources a lot.
