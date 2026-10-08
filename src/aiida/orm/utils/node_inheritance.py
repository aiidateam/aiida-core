###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Resolve class-based node queries to concrete stored node types through Python inheritance.

A :class:`~aiida.orm.QueryBuilder` target given as a class selects all registered, storable node
implementations that inherit from it. The requested class itself does not need an entry point: it acts
as a query target while only its registered subclasses contribute stored types. Entry points therefore
identify concrete implementations, while ordinary Python inheritance defines membership in a class query.

This is deliberately different from a raw stored-type string target (``entity_type=...``), which keeps
namespace-based prefix semantics and cannot know the inheritance graph. A class query is serialized as an
explicit selection of exact stored type identifiers, so it round-trips without importing the original base
class or its plugins.
"""

from __future__ import annotations

import typing as t
import warnings
from collections.abc import Collection, Sequence

from aiida.common.exceptions import LoadingEntryPointError
from aiida.common.warnings import AiidaEntryPointWarning

__all__ = (
    'NODE_ENTRY_POINT_GROUPS',
    'discover_registered_node_classes',
    'node_type_filter',
    'resolve_node_types',
    'resolve_registered_node_types',
)

#: Entry point groups that contain storable node implementations. This mirrors the groups accepted by
#: :meth:`~aiida.orm.nodes.node.Node._validate_storability`.
NODE_ENTRY_POINT_GROUPS: tuple[str, ...] = ('aiida.data', 'aiida.node')


def _is_node_subclass(candidate: t.Any) -> t.TypeGuard[type]:
    """Return whether the candidate is a class inheriting from ``Node``."""
    from aiida.orm.nodes.node import Node

    return isinstance(candidate, type) and issubclass(candidate, Node)


def _stored_type(candidate: type) -> str | None:
    """Return the stored node type identifier of a candidate class, or ``None`` if unavailable."""
    try:
        type_string = candidate.class_node_type  # type: ignore[attr-defined]
    except AttributeError:
        return None
    return type_string if isinstance(type_string, str) else None


def resolve_node_types(
    node_class: type,
    *,
    subclassing: bool,
    candidates: Collection[type],
) -> tuple[str, ...]:
    """Return the concrete stored node types selected by a class query, using only Python inheritance.

    :param node_class: the query target, typically a (possibly abstract or unregistered) base class.
    :param subclassing: if ``True``, select all candidates inheriting from ``node_class``; if ``False``,
        select only ``node_class`` itself.
    :param candidates: the registered node implementations to select from. Only classes in this collection
        can contribute stored types; the requested class itself is included only if it is part of the
        collection and storable. Non-class entries and classes that are not ``Node`` subclasses never match.
    :returns: a sorted tuple of unique stored type identifiers. An empty tuple means the query matches nothing.
    """
    valid: dict[type, str] = {}
    for candidate in candidates:
        if not _is_node_subclass(candidate):
            continue
        type_string = _stored_type(candidate)
        if type_string is None:
            continue
        valid.setdefault(candidate, type_string)

    if not _is_node_subclass(node_class):
        return ()

    if not subclassing:
        if not getattr(node_class, '_storable', False):
            return ()
        type_string = _stored_type(node_class)
        return (type_string,) if type_string is not None else ()

    selected = {
        type_string
        for candidate, type_string in valid.items()
        if getattr(candidate, '_storable', False) and issubclass(candidate, node_class)
    }
    return tuple(sorted(selected))


def discover_registered_node_classes(
    groups: Sequence[str] = NODE_ENTRY_POINT_GROUPS,
) -> tuple[type, ...]:
    """Load all node implementations registered through the given entry point groups.

    :param groups: the entry point groups to discover node implementations from.
    :returns: the successfully loaded classes, deduplicated while preserving discovery order.
    :raises aiida.common.exceptions.LoadingEntryPointError: never; unloadable entry points are skipped
        with a warning, but unexpected errors raised by a plugin are not suppressed.
    """
    from aiida.plugins.entry_point import get_entry_points, load_entry_point

    discovered: list[type] = []
    seen: set[int] = set()
    for group in groups:
        for entry_point in get_entry_points(group):
            try:
                loaded = load_entry_point(group, entry_point.name)
            except LoadingEntryPointError as exc:
                warnings.warn(
                    f'Skipping node entry point `{group}:{entry_point.name}` in class-based queries: {exc}',
                    AiidaEntryPointWarning,
                )
                continue
            if id(loaded) not in seen:
                seen.add(id(loaded))
                discovered.append(loaded)
    return tuple(discovered)


def resolve_registered_node_types(node_class: type, *, subclassing: bool) -> tuple[str, ...]:
    """Resolve a class query against all currently registered node implementations.

    This combines :func:`discover_registered_node_classes` with :func:`resolve_node_types`. Entry points
    that cannot be loaded are excluded with a warning and so are never silently claimed as included.

    :param node_class: the query target.
    :param subclassing: if ``True``, select the registered subclasses of ``node_class``, otherwise only
        ``node_class`` itself.
    :returns: a sorted tuple of unique stored type identifiers, empty when nothing matches.
    """
    return resolve_node_types(node_class, subclassing=subclassing, candidates=discover_registered_node_classes())


def node_type_filter(node_class: type, *, subclassing: bool) -> dict[str, t.Any]:
    """Build the ``node_type`` filter for a class-based node query.

    The filter always references exact stored type identifiers, never a namespace prefix. An empty selection
    produces a filter on the target's own stored type, which can never match a stored node since the target
    is then necessarily not a registered, storable implementation.

    :param node_class: the query target.
    :param subclassing: whether subclasses of the target are included.
    :returns: a filter dictionary in the ``QueryBuilder`` filter language for the ``node_type`` field.
    """
    from aiida.orm.nodes.node import Node

    selected = resolve_registered_node_types(node_class, subclassing=subclassing)
    if len(selected) == 1:
        return {'==': selected[0]}
    if len(selected) > 1:
        return {'in': list(selected)}
    fallback = _stored_type(node_class) if _is_node_subclass(node_class) else None
    if fallback is None:
        fallback = Node.class_node_type
    return {'==': fallback}
