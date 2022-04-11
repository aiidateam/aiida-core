# -*- coding: utf-8 -*-
"""Interface to control caching of a node instance."""
from __future__ import annotations

import importlib
import typing as t

from aiida.common import exceptions
from aiida.common.hashing import make_hash
from aiida.common.lang import type_check

from ..querybuilder import QueryBuilder


class NodeCaching:
    """Interface to control caching of a node instance."""

    # The keys in the extras that are used to store the hash of the node and whether it should be used in caching.
    _HASH_EXTRA_KEY: str = '_aiida_hash'
    _VALID_CACHE_KEY: str = '_aiida_valid_cache'

    def __init__(self, node: 'Node') -> None:
        """Initialize the caching interface."""
        self._node = node

    def get_hash(self, ignore_errors: bool = True, **kwargs: t.Any) -> str | None:
        """Return the hash for this node based on its attributes.

        :param ignore_errors: return ``None`` on ``aiida.common.exceptions.HashingError`` (logging the exception)
        """
        if not self._node.is_stored:
            raise exceptions.InvalidOperation('You can get the hash only after having stored the node')

        return self._get_hash(ignore_errors=ignore_errors, **kwargs)

    def _get_hash(self, ignore_errors: bool = True, **kwargs: t.Any) -> str | None:
        """
        Return the hash for this node based on its attributes.

        This will always work, even before storing.

        :param ignore_errors: return ``None`` on ``aiida.common.exceptions.HashingError`` (logging the exception)
        """
        try:
            return make_hash(self._get_objects_to_hash(), **kwargs)
        except exceptions.HashingError:
            if not ignore_errors:
                raise
            if self._node.logger:
                self._node.logger.exception('Node hashing failed')
            return None

    def _get_objects_to_hash(self) -> list[t.Any]:
        """Return a list of objects which should be included in the hash."""
        top_level_module = self._node.__module__.split('.', 1)[0]
        try:
            version = importlib.import_module(top_level_module).__version__
        except (ImportError, AttributeError) as exc:
            raise exceptions.HashingError("The node's package version could not be determined") from exc
        objects = [
            version,
            {
                key: val
                for key, val in self._node.base.attributes.items()
                if key not in self._node._hash_ignored_attributes and key not in self._node._updatable_attributes  # pylint: disable=unsupported-membership-test,protected-access
            },
            self._node.base.repository.hash(),
            self._node.computer.uuid if self._node.computer is not None else None
        ]
        return objects

    def rehash(self) -> None:
        """Regenerate the stored hash of the Node."""
        self._node.base.extras.set(self._HASH_EXTRA_KEY, self.get_hash())

    def clear_hash(self) -> None:
        """Sets the stored hash of the Node to None."""
        self._node.base.extras.set(self._HASH_EXTRA_KEY, None)

    def get_cache_source(self) -> str | None:
        """Return the UUID of the node that was used in creating this node from the cache, or None if it was not cached.

        :return: source node UUID or None
        """
        return self._node.base.extras.get('_aiida_cached_from', None)

    @property
    def is_created_from_cache(self) -> bool:
        """Return whether this node was created from a cached node.

        :return: boolean, True if the node was created by cloning a cached node, False otherwise
        """
        return self.get_cache_source() is not None

    def _get_same_node(self) -> 'Node' | None:
        """Returns a stored node from which the current Node can be cached or None if it does not exist

        If a node is returned it is a valid cache, meaning its `_aiida_hash` extra matches `self.get_hash()`.
        If there are multiple valid matches, the first one is returned.
        If no matches are found, `None` is returned.

        :return: a stored `Node` instance with the same hash as this code or None

        Note: this should be only called on stored nodes, or internally from .store() since it first calls
        clean_value() on the attributes to normalise them.
        """
        try:
            return next(self._iter_all_same_nodes(allow_before_store=True))
        except StopIteration:
            return None

    def get_all_same_nodes(self) -> list['Node']:
        """Return a list of stored nodes which match the type and hash of the current node.

        All returned nodes are valid caches, meaning their `_aiida_hash` extra matches `self.get_hash()`.

        Note: this can be called only after storing a Node (since at store time attributes will be cleaned with
        `clean_value` and the hash should become idempotent to the action of serialization/deserialization)
        """
        return list(self._iter_all_same_nodes())

    def _iter_all_same_nodes(self, allow_before_store=False) -> t.Iterator['Node']:
        """
        Returns an iterator of all same nodes.

        Note: this should be only called on stored nodes, or internally from .store() since it first calls
        clean_value() on the attributes to normalise them.
        """
        if not allow_before_store and not self._node.is_stored:
            raise exceptions.InvalidOperation('You can get the hash only after having stored the node')

        node_hash = self._get_hash()

        if not node_hash or not self._node._cachable:  # pylint: disable=protected-access
            return iter(())

        builder = QueryBuilder(backend=self._node.backend)
        builder.append(self._node.__class__, filters={f'extras.{self._HASH_EXTRA_KEY}': node_hash}, subclassing=False)

        return (
            node for node in builder.all(flat=True) if node.base.caching.is_valid_cache
        )  # type: ignore[misc,union-attr]

    @property
    def is_valid_cache(self) -> bool:
        """Hook to exclude certain ``Node`` classes from being considered a valid cache.

        The base class assumes that all node instances are valid to cache from, unless the ``_VALID_CACHE_KEY`` extra
        has been set to ``False`` explicitly. Subclasses can override this property with more specific logic, but should
        probably also consider the value returned by this base class.
        """
        return self._node.base.extras.get(self._VALID_CACHE_KEY, True)

    @is_valid_cache.setter
    def is_valid_cache(self, valid: bool) -> None:
        """Set whether this node instance is considered valid for caching or not.

        If a node instance has this property set to ``False``, it will never be used in the caching mechanism, unless
        the subclass overrides the ``is_valid_cache`` property and ignores it implementation completely.

        :param valid: whether the node is valid or invalid for use in caching.
        """
        type_check(valid, bool)
        self._node.base.extras.set(self._VALID_CACHE_KEY, valid)
