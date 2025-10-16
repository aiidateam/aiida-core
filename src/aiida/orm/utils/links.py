###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Utilities for dealing with links between nodes."""

from collections import OrderedDict
from collections.abc import Mapping
from typing import TYPE_CHECKING, Generator, Iterator, List, NamedTuple, Optional

from aiida.common import exceptions
from aiida.common.lang import type_check

if TYPE_CHECKING:
    from aiida.common.links import LinkType
    from aiida.orm import Node
    from aiida.orm.implementation.storage_backend import StorageBackend

__all__ = ('LinkManager', 'LinkPair', 'LinkTriple', 'validate_link')


class LinkPair(NamedTuple):
    link_type: 'LinkType'
    link_label: str


class LinkTriple(NamedTuple):
    node: 'Node'
    link_type: 'LinkType'
    link_label: str


class LinkQuadruple(NamedTuple):
    source_id: int
    target_id: int
    link_type: 'LinkType'
    link_label: str


def link_triple_exists(
    source: 'Node', target: 'Node', link_type: 'LinkType', link_label: str, backend: Optional['StorageBackend'] = None
) -> bool:
    """Return whether a link with the given type and label exists between the given source and target node.

    :param source: node from which the link is outgoing
    :param target: node to which the link is incoming
    :param link_type: the link type
    :param link_label: the link label
    :return: boolean, True if the link triple exists, False otherwise
    """
    from aiida.orm import Node, QueryBuilder

    target_links_cache = target.base.links.incoming_cache

    # First check if the triple exist in the cache, in the case of an unstored target node
    if target_links_cache and LinkTriple(source, link_type, link_label) in target_links_cache:
        return True

    # If either node is unstored (i.e. does not have a pk), the link cannot exist in the database, so no need to check
    if source.pk is None or target.pk is None:
        return False

    # Here we have two stored nodes, so we need to check if the same link already exists in the database.
    # Finding just a single match is sufficient so we can use the `limit` clause for efficiency
    builder = QueryBuilder(backend=backend)
    builder.append(Node, filters={'id': source.pk}, project=['id'])
    builder.append(Node, filters={'id': target.pk}, edge_filters={'type': link_type.value, 'label': link_label})
    builder.limit(1)

    return builder.count() != 0


def validate_link(
    source: 'Node', target: 'Node', link_type: 'LinkType', link_label: str, backend: Optional['StorageBackend'] = None
) -> None:
    """Validate adding a link of the given type and label from a given node to ourself.

    This function will first validate the class types of the inputs and will subsequently validate whether a link of
    the specified type is allowed at all between the nodes types of the source and target.

    Subsequently, the validity of the "indegree" and "outdegree" of the proposed link is validated, which means
    validating that the uniqueness constraints of the incoming links into the target node and the outgoing links from
    the source node are not violated. In AiiDA's provenance graph each link type has one of the following three types
    of "degree" character::

        * unique
        * unique pair
        * unique triple

    Each degree character has a different unique constraint on its links, here defined for the indegree::

        * unique: any target node, it can only have a single incoming link of this type, regardless of the link label.
        * unique pair: a node can have an infinite amount of incoming links of this type, as long as the labels within
            that sub set, are unique. In short, it is the link pair, i.e. the tuple of the link type and label, that has
            a uniquess constraint for the incoming links to a given node.
        * unique triple: a node can have an infinite amount of incoming links of this type, as long as the triple tuple
            of source node, link type and link label is unique. In other words, it is the link triple that has a
            uniqueness constraint for the incoming links.

    The same holds for outdegree, but then it concerns outgoing links from the source node to the target node.

    For illustration purposes, consider the following example provenance graphs that are considered legal, where
    `WN`, `DN` and `CN` represent a `WorkflowNode`, a `DataNode` and a `CalculationNode`, respectively::

                    1                    2                    3
            ______     ______          ______          ______     ______
           |      |   |      |        |      |        |      |   |      |
           |  WN  |   |  DN  |        |  DN  |        |  WN  |   |  WN  |
           |______|   |______|        |______|        |______|   |______|
                |     /                |   |               |     /
              a |    / a             a |   | b           a |    / a
               _|___/                  |___|_             _|___/
              |      |                |      |           |      |
              |  CN  |                |  CN  |           |  DN  |
              |______|                |______|           |______|

    In example 1, the link uniqueness constraint is not violated because despite the labels having the same label `a`,
    their link types, `CALL_CALC` and `INPUT_CALC`, respectively, are different and their `unique_pair` indegree is
    not violated.

    Similarly, in the second example, the constraint is not violated, because despite both links having the same link
    type `INPUT_CALC`, the have different labels, so the `unique_pair` indegree of the `INPUT_CALC` is not violated.

    Finally, in the third example, we see two `WorkflowNodes` both returning the same `DataNode` and with the same
    label. Despite the two incoming links here having both the same type as well as the same label, the uniqueness
    constraint is not violated, because the indegree for `RETURN` links is `unique_triple` which means that the triple
    of source node and link type and label should be unique.

    :param source: the node from which the link is coming
    :param target: the node to which the link is going
    :param link_type: the type of link
    :param link_label: link label
    :raise TypeError: if `source` or `target` is not a Node instance, or `link_type` is not a `LinkType` enum
    :raise ValueError: if the proposed link is invalid
    """
    from aiida.common.links import LinkType, validate_link_label
    from aiida.orm import CalculationNode, Data, Node, WorkflowNode

    type_check(link_type, LinkType, f'link_type should be a LinkType enum but got: {type(link_type)}')
    type_check(source, Node, f'source should be a `Node` but got: {type(source)}')
    type_check(target, Node, f'target should be a `Node` but got: {type(target)}')

    if source.backend != target.backend:
        raise ValueError(
            f'source and target nodes must be stored in the same backend, but got {source.backend} and {target.backend}'
        )

    if source.uuid is None or target.uuid is None:  # type: ignore[redundant-expr]
        raise ValueError('source or target node does not have a UUID')

    if source.uuid == target.uuid:
        raise ValueError('cannot add a link to oneself')

    try:
        validate_link_label(link_label)
    except ValueError as exception:
        raise ValueError(f'invalid link label `{link_label}`: {exception}')

    # For each link type, define a tuple that defines the valid types for the source and target node, as well as
    # the outdegree and indegree character. If the degree is `unique` that means that there can only be a single
    # link of this type regardless of the label. If instead it is `unique_label`, an infinite amount of links of that
    # type can be defined, as long as the link label is unique for the sub set of links of that type. Finally, for
    # `unique_triple` the triple of node, link type and link label has to be unique.
    link_mapping = {
        LinkType.CALL_CALC: (WorkflowNode, CalculationNode, 'unique_triple', 'unique'),
        LinkType.CALL_WORK: (WorkflowNode, WorkflowNode, 'unique_triple', 'unique'),
        LinkType.CREATE: (CalculationNode, Data, 'unique_pair', 'unique'),
        LinkType.INPUT_CALC: (Data, CalculationNode, 'unique_triple', 'unique_pair'),
        LinkType.INPUT_WORK: (Data, WorkflowNode, 'unique_triple', 'unique_pair'),
        LinkType.RETURN: (WorkflowNode, Data, 'unique_pair', 'unique_triple'),
    }

    type_source, type_target, outdegree, indegree = link_mapping[link_type]

    if not isinstance(source, type_source) or not isinstance(target, type_target):
        raise ValueError(f'cannot add a {link_type} link from {type(source)} to {type(target)}')

    if outdegree == 'unique_triple' or indegree == 'unique_triple':
        # For a `unique_triple` degree we just have to check if an identical triple already exist, either in the cache
        # or stored, in which case, the new proposed link is a duplicate and thus illegal
        duplicate_link_triple = link_triple_exists(source, target, link_type, link_label, backend)

    # If the outdegree is `unique` there cannot already be any other outgoing link of that type
    if outdegree == 'unique' and source.base.links.get_outgoing(link_type=link_type, only_uuid=True).all():
        raise ValueError(f'node<{source.uuid}> already has an outgoing {link_type} link')

    # If the outdegree is `unique_pair`, then the link labels for outgoing links of this type should be unique
    elif (
        outdegree == 'unique_pair'
        and source.base.links.get_outgoing(link_type=link_type, only_uuid=True, link_label_filter=link_label).all()
    ):
        raise ValueError(f'node<{source.uuid}> already has an outgoing {link_type} link with label "{link_label}"')

    # If the outdegree is `unique_triple`, then the link triples of link type, link label and target should be unique
    elif outdegree == 'unique_triple' and duplicate_link_triple:
        raise ValueError(
            'node<{}> already has an outgoing {} link with label "{}" from node<{}>'.format(
                source.uuid, link_type, link_label, target.uuid
            )
        )

    # If the indegree is `unique` there cannot already be any other incoming links of that type
    if indegree == 'unique' and target.base.links.get_incoming(link_type=link_type, only_uuid=True).all():
        raise ValueError(f'node<{target.uuid}> already has an incoming {link_type} link')

    # If the indegree is `unique_pair`, then the link labels for incoming links of this type should be unique
    elif (
        indegree == 'unique_pair'
        and target.base.links.get_incoming(link_type=link_type, link_label_filter=link_label, only_uuid=True).all()
    ):
        raise ValueError(f'node<{target.uuid}> already has an incoming {link_type} link with label "{link_label}"')

    # If the indegree is `unique_triple`, then the link triples of link type, link label and source should be unique
    elif indegree == 'unique_triple' and duplicate_link_triple:
        raise ValueError(
            'node<{}> already has an incoming {} link with label "{}" from node<{}>'.format(
                target.uuid, link_type, link_label, source.uuid
            )
        )


class LinkManager:
    """Class to convert a list of LinkTriple tuples into an iterator.

    It defines convenience methods to retrieve certain subsets of LinkTriple while checking for consistency.
    For example::

        LinkManager.one(): returns the only entry in the list or it raises an exception
        LinkManager.first(): returns the first entry from the list
        LinkManager.all(): returns all entries from list

    The methods `all_nodes` and `all_link_labels` are syntactic sugar wrappers around `all` to get a list of only the
    incoming nodes or link labels, respectively.
    """

    def __init__(self, link_triples: List[LinkTriple]):
        """Initialise the collection."""
        self.link_triples = link_triples

    def __iter__(self) -> Iterator[LinkTriple]:
        """Return an iterator of LinkTriple instances.

        :return: iterator of LinkTriple instances
        """
        return iter(self.link_triples)

    def __next__(self) -> Generator[LinkTriple, None, None]:
        """Return the next element in the iterator.

        :return: LinkTriple
        """
        for link_triple in self.link_triples:
            yield link_triple

    def __bool__(self):
        return bool(len(self.link_triples))

    def next(self) -> Generator[LinkTriple, None, None]:
        """Return the next element in the iterator.

        :return: LinkTriple
        """
        return self.__next__()

    def one(self) -> LinkTriple:
        """Return a single entry from the iterator.

        If the iterator contains no or more than one entry, an exception will be raised
        :return: LinkTriple instance
        :raises ValueError: if the iterator contains anything but one entry
        """
        if self.link_triples:
            if len(self.link_triples) > 1:
                raise ValueError('more than one entry found')
            return self.link_triples[0]

        raise ValueError('no entries found')

    def first(self) -> Optional[LinkTriple]:
        """Return the first entry from the iterator.

        :return: LinkTriple instance or None if no entries were matched
        """
        if self.link_triples:
            return self.link_triples[0]

        return None

    def all(self) -> List[LinkTriple]:
        """Return all entries from the list.

        :return: list of LinkTriple instances
        """
        return self.link_triples

    def all_nodes(self) -> List['Node']:
        """Return a list of all nodes.

        :return: list of nodes
        """
        return [entry.node for entry in self.all()]

    def all_link_pairs(self) -> List[LinkPair]:
        """Return a list of all link pairs.

        :return: list of LinkPair instances
        """
        return [LinkPair(entry.link_type, entry.link_label) for entry in self.all()]

    def all_link_labels(self) -> List[str]:
        """Return a list of all link labels.

        :return: list of link labels
        """
        return [entry.link_label for entry in self.all()]

    def get_node_by_label(self, label: str) -> 'Node':
        """Return the node from list for given label.

        :return: node that corresponds to the given label
        :raises aiida.common.NotExistent: if the label is not present among the link_triples
        """
        matching_entry = None
        for entry in self.link_triples:
            if entry.link_label == label:
                if matching_entry is None:
                    matching_entry = entry.node
                else:
                    raise exceptions.MultipleObjectsError(f'more than one neighbor with the label {label} found')

        if matching_entry is None:
            raise exceptions.NotExistent(f'no neighbor with the label {label} found')

        return matching_entry

    def nested(self, sort=True):
        """Construct (nested) dictionary of matched nodes that mirrors the original nesting of link namespaces.

        Process input and output namespaces can be nested, however the link labels that represent them in the database
        have a flat hierarchy, and so the link labels are flattened representations of the nested namespaces.
        This function reconstructs the original node nesting based on the flattened links.

        :return: dictionary of nested namespaces
        :raises KeyError: if there are duplicate link labels in a namespace
        """
        from aiida.engine.processes.ports import PORT_NAMESPACE_SEPARATOR

        nested: dict = {}

        for entry in self.link_triples:
            current_namespace = nested
            breadcrumbs = entry.link_label.split(PORT_NAMESPACE_SEPARATOR)

            # The last element is the "leaf" port name the preceding elements are nested port namespaces
            port_name = breadcrumbs[-1]
            port_namespaces = breadcrumbs[:-1]

            # Get the nested namespace
            for subspace in port_namespaces:
                current_namespace = current_namespace.setdefault(subspace, {})

            # Insert the node at the given port name
            if port_name in current_namespace:
                raise KeyError(f"duplicate label '{port_name}' in namespace '{'.'.join(port_namespaces)}'")

            current_namespace[port_name] = entry.node

        if sort:
            return OrderedDict(sorted(nested.items(), key=lambda x: (not isinstance(x[1], Mapping), x)))

        return nested
