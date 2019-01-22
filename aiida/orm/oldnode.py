# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from abc import ABCMeta, abstractmethod, abstractproperty

import os
import logging
import importlib
from collections import Callable, Iterable, Mapping
import numbers
import math
import warnings

import six

from aiida.backends.utils import validate_attribute_key
from aiida.manage.caching import get_use_cache
from aiida.common.exceptions import InternalError, ModificationNotAllowed, UniquenessError, ValidationError, \
    InvalidOperation, StoringNotAllowed
from aiida.common.hashing import _HASH_EXTRA_KEY
from aiida.common.links import LinkType
from aiida.common.lang import override, abstractclassmethod, combomethod, classproperty
from aiida.common.escaping import sql_string_match
from aiida.manage import get_manager
from aiida.orm.utils import links
from aiida.orm.utils.node import get_type_string_from_class, get_query_type_from_type_string

_NO_DEFAULT = tuple()


def clean_value(value):
    """
    Get value from input and (recursively) replace, if needed, all occurrences
    of BaseType AiiDA data nodes with their value, and List with a standard list.
    It also makes a deep copy of everything
    The purpose of this function is to convert data to a type which can be serialized and deserialized
    for storage in the DB without its value changing.

    Note however that there is no logic to avoid infinite loops when the
    user passes some perverse recursive dictionary or list.
    In any case, however, this would not be storable by AiiDA...

    :param value: A value to be set as an attribute or an extra
    :return: a "cleaned" value, potentially identical to value, but with
        values replaced where needed.
    """
    # Must be imported in here to avoid recursive imports
    from aiida.orm.node.data import BaseType

    def clean_builtin(val):
        if isinstance(val, numbers.Real) and (math.isnan(val) or math.isinf(val)):
            # see https://www.postgresql.org/docs/current/static/datatype-json.html#JSON-TYPE-MAPPING-TABLE
            raise ValidationError("nan and inf/-inf can not be serialized to the database")

        return val

    if isinstance(value, BaseType):
        return clean_builtin(value.value)

    if isinstance(value, Mapping):
        # Check dictionary before iterables
        return {k: clean_value(v) for k, v in value.items()}
    if (isinstance(value, Iterable) and not isinstance(value, six.string_types)):
        # list, tuple, ... but not a string
        # This should also properly take care of dealing with the
        # basedatatypes.List object
        return [clean_value(v) for v in value]

    # If I don't know what to do I just return the value
    # itself - it's not super robust, but relies on duck typing
    # (e.g. if there is something that behaves like an integer
    # but is not an integer, I still accept it)

    return clean_builtin(value)


class _AbstractNodeMeta(ABCMeta):
    """
    Some python black magic to set correctly the logger also in subclasses.
    """

    def __new__(cls, name, bases, attrs):

        newcls = ABCMeta.__new__(cls, name, bases, attrs)
        newcls._logger = logging.getLogger('{}.{}'.format(attrs['__module__'], name))

        # Set the plugin type string and query type string based on the plugin type string
        newcls._plugin_type_string = get_type_string_from_class(attrs['__module__'], name)
        newcls._query_type_string = get_query_type_from_type_string(newcls._plugin_type_string)

        return newcls


@six.add_metaclass(_AbstractNodeMeta)
class AbstractNode(object):
    """
    Base class to map a node in the DB + its permanent repository counterpart.

    Stores attributes starting with an underscore.

    Caches files and attributes before the first save, and saves everything
    only on store(). After the call to store(), attributes cannot be changed.

    Only after storing (or upon loading from uuid) extras can be modified
    and in this case they are directly set on the db.

    In the plugin, also set the _plugin_type_string, to be set in the DB in
    the 'type' field.
    """

    # A list of tuples, saying which attributes cannot be set at the same time
    # See documentation in the set() method.
    _set_incompatibilities = []

    # A tuple of attribute names that can be updated even after node is stored
    # Requires Sealable mixin, but needs empty tuple for base class
    _updatable_attributes = tuple()

    # A tuple of attribute names that will be ignored when creating the hash.
    _hash_ignored_attributes = tuple()

    # Flag that determines whether the class can be cached.
    _cacheable = True

    @abstractmethod
    def __init__(self, **kwargs):
        """
        Initialize the object Node.

        :param uuid: if present, the Node with given uuid is
          loaded from the database.
          (It is not possible to assign a uuid to a new Node.)
        """
        self._to_be_stored = True

        # A cache of incoming links represented as a list of LinkTriples instances
        self._incoming_cache = list()

        self._temp_folder = None
        self._repo_folder = None

        self._backend = get_manager().get_backend()

    def _init_internal_params(self):
        """
        Set the default values for this class; this method is automatically called by the init.

        :note: if you inherit this function, ALWAYS remember to
          call super()._init_internal_params() as the first thing
          in your inherited function.
        """
        pass

    @property
    def _set_defaults(self):
        """
        Default values to set in the __init__, if no value is explicitly provided
        for the given key.
        It is a dictionary, with k=v; if the key k is not provided to the __init__,
        and a value is present here, this is set.
        """
        return {}

    def _set_with_defaults(self, **kwargs):
        """
        Calls the set() method, but also adds the class-defined default
        values (defined in the self._set_defaults attribute),
        if they are not provided by the user.

        :note: for the default values, also allow to define 'hidden' methods,
            meaning that if a default value has a key "_state", it will not call
            the function "set__state" but rather "_set_state".
            This is not allowed, instead, for the standard set() method.
        """
        self._set_internal(arguments=self._set_defaults, allow_hidden=True)

        # Pass everything to 'set'
        self.set(**kwargs)

    def set(self, **kwargs):
        """
        For each k=v pair passed as kwargs, call the corresponding
        set_k(v) method (e.g., calling self.set(property=5, mass=2) will
        call self.set_property(5) and self.set_mass(2).
        Useful especially in the __init__.

        :note: it uses the _set_incompatibilities list of the class to check
            that we are not setting methods that cannot be set at the same time.
            _set_incompatibilities must be a list of tuples, and each tuple
            specifies the elements that cannot be set at the same time.
            For instance, if _set_incompatibilities = [('property', 'mass')],
            then the call self.set(property=5, mass=2) will raise a ValueError.
            If a tuple has more than two values, it raises ValueError if *all*
            keys are provided at the same time, but it does not give any error
            if at least one of the keys is not present.

        :note: If one element of _set_incompatibilities is a tuple with only
            one element, this element will not be settable using this function
            (and in particular,

        :raise ValueError: if the corresponding set_k method does not exist
            in self, or if the methods cannot be set at the same time.
        """
        self._set_internal(arguments=kwargs, allow_hidden=False)

    def _set_internal(self, arguments, allow_hidden=False):
        """
        Works as self.set(), but takes a dictionary as the 'arguments' variable,
        instead of reading it from the ``kwargs``; moreover, it allows to specify
        allow_hidden to True. In this case, if a a key starts with and
        underscore, as for instance ``_state``, it will not call
        the function ``set__state`` but rather ``_set_state``.
        """
        for incomp in self._set_incompatibilities:
            if all(k in arguments.keys() for k in incomp):
                if len(incomp) == 1:
                    raise ValueError("Cannot set {} directly when creating "
                                     "the node or using the .set() method; "
                                     "use the specific method instead.".format(incomp[0]))
                else:
                    raise ValueError("Cannot set {} at the same time".format(" and ".join(incomp)))

        for k, v in arguments.items():
            try:
                if allow_hidden and k.startswith("_"):
                    method = getattr(self, '_set_{}'.format(k[1:]))
                else:
                    method = getattr(self, 'set_{}'.format(k))
            except AttributeError:
                raise ValueError("Unable to set '{0}', no set_{0} method " "found".format(k))
            if not isinstance(method, Callable):
                raise ValueError("Unable to set '{0}', set_{0} is not " "callable!".format(k))
            method(v)


    



    def _store_from_cache(self, cache_node, with_transaction):
        from aiida.orm.mixins import Sealable
        assert self.type == cache_node.type

        self.label = cache_node.label
        self.description = cache_node.description

        for key, value in cache_node.iterattrs():
            if key != Sealable.SEALED_KEY:
                self._set_attr(key, value)

        self.folder.replace_with_folder(cache_node.folder.abspath, move=False, overwrite=True)

        # Make sure the node doesn't have any RETURN links
        if cache_node.get_outgoing(link_type=LinkType.RETURN).all():
            raise ValueError('Cannot use cache from nodes with RETURN links.')

        self.store(with_transaction=with_transaction, use_cache=False)
        self.set_extra('_aiida_cached_from', cache_node.uuid)

    def _add_outputs_from_cache(self, cache_node):
        # Add CREATE links
        for entry in cache_node.get_outgoing(link_type=LinkType.CREATE):
            new_node = entry.node.clone()
            new_node.add_incoming(self, link_type=LinkType.CREATE, link_label=entry.link_label)
            new_node.store()

    def get_hash(self, ignore_errors=True, **kwargs):
        """
        Making a hash based on my attributes
        """
        from aiida.common.hashing import make_hash
        try:
            return make_hash(self._get_objects_to_hash(), **kwargs)
        except Exception as e:
            if ignore_errors:
                return None
            else:
                raise e

    def _get_objects_to_hash(self):
        """
        Return a list of objects which should be included in the hash.
        """
        computer = self.get_computer()
        return [
            importlib.import_module(self.__module__.split('.', 1)[0]).__version__, {
                key: val
                for key, val in self.get_attrs().items()
                if (key not in self._hash_ignored_attributes and
                    key not in getattr(self, '_updatable_attributes', tuple()))
            }, self.folder, computer.uuid if computer is not None else None
        ]

    def rehash(self):
        """
        Re-generates the stored hash of the Node.
        """
        self.set_extra(_HASH_EXTRA_KEY, self.get_hash())

    def clear_hash(self):
        """
        Sets the stored hash of the Node to None.
        """
        self.set_extra(_HASH_EXTRA_KEY, None)

    def get_cache_source(self):
        """
        Return the UUID of the node that was used in creating this node from the cache, or None if it was not cached

        :return: the UUID of the node from which this node was cached, or None if it was not created through the cache
        """
        return self.get_extra('_aiida_cached_from', None)

    @property
    def is_created_from_cache(self):
        """
        Return whether this node was created from a cached node.cached

        :return: boolean, True if the node was created by cloning a cached node, False otherwise
        """
        return self.get_cache_source() is not None

    def _get_same_node(self):
        """
        Returns a stored node from which the current Node can be cached, meaning that the returned Node is a valid cache, and its ``_aiida_hash`` attribute matches ``self.get_hash()``.

        If there are multiple valid matches, the first one is returned. If no matches are found, ``None`` is returned.

        Note that after ``self`` is stored, this function can return ``self``.
        """
        try:
            return next(self._iter_all_same_nodes())
        except StopIteration:
            return None

    def get_all_same_nodes(self):
        """
        Return a list of stored nodes which match the type and hash of the current node. For the stored nodes, the ``_aiida_hash`` extra is checked to determine the hash, while ``self.get_hash()`` is executed on the current node.

        Only nodes which are a valid cache are returned. If the current node is already stored, it can be included in the returned list if ``self.get_hash()`` matches its ``_aiida_hash``.
        """
        return list(self._iter_all_same_nodes())

    def _iter_all_same_nodes(self):
        """
        Returns an iterator of all same nodes.
        """
        if not self._cacheable:
            return iter(())

        hash_ = self.get_hash()
        if not hash_:
            return iter(())

        from aiida.orm.querybuilder import QueryBuilder
        builder = QueryBuilder()
        builder.append(self.__class__, filters={'extras._aiida_hash': hash_}, project='*', subclassing=False)
        same_nodes = (n[0] for n in builder.iterall())
        return (n for n in same_nodes if n._is_valid_cache())

    def _is_valid_cache(self):
        """
        Subclass hook to exclude certain Nodes (e.g. failed calculations) from being considered in the caching process.
        """
        return True
