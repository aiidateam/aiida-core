# -*- coding: utf-8 -*-
"""Interface for links of a node instance."""
from __future__ import annotations

import typing as t
from typing import Optional, cast

from aiida.common import exceptions
from aiida.common.escaping import sql_string_match
from aiida.common.lang import type_check
from aiida.common.links import LinkType

from ..querybuilder import QueryBuilder
from ..utils.links import LinkManager, LinkTriple

if t.TYPE_CHECKING:
    from .node import Node  # pylint: disable=unused-import


class NodeLinks:
    """Interface for links of a node instance."""

    def __init__(self, node: 'Node') -> None:
        """Initialize the links interface."""
        self._node = node
        self.incoming_cache: list[LinkTriple] = []

    def _add_incoming_cache(self, source: 'Node', link_type: LinkType, link_label: str) -> None:
        """Add an incoming link to the cache.

        .. note: the proposed link is not validated in this function, so this should not be called directly
            but it should only be called by `Node.add_incoming`.

        :param source: the node from which the link is coming
        :param link_type: the link type
        :param link_label: the link label
        :raise aiida.common.UniquenessError: if the given link triple already exists in the cache
        """
        assert self.incoming_cache is not None, 'incoming_cache not initialised'

        link_triple = LinkTriple(source, link_type, link_label)

        if link_triple in self.incoming_cache:
            raise exceptions.UniquenessError(f'the link triple {link_triple} is already present in the cache')

        self.incoming_cache.append(link_triple)

    def add_incoming(self, source: 'Node', link_type: LinkType, link_label: str) -> None:
        """Add a link of the given type from a given node to ourself.

        :param source: the node from which the link is coming
        :param link_type: the link type
        :param link_label: the link label
        :raise TypeError: if `source` is not a Node instance or `link_type` is not a `LinkType` enum
        :raise ValueError: if the proposed link is invalid
        """
        self.validate_incoming(source, link_type, link_label)
        source.base.links.validate_outgoing(self._node, link_type, link_label)

        if self._node.is_stored and source.is_stored:
            self._node.backend_entity.add_incoming(source.backend_entity, link_type, link_label)
        else:
            self._add_incoming_cache(source, link_type, link_label)

    def validate_incoming(self, source: 'Node', link_type: LinkType, link_label: str) -> None:
        """Validate adding a link of the given type from a given node to ourself.

        This function will first validate the types of the inputs, followed by the node and link types and validate
        whether in principle a link of that type between the nodes of these types is allowed.

        Subsequently, the validity of the "degree" of the proposed link is validated, which means validating the
        number of links of the given type from the given node type is allowed.

        :param source: the node from which the link is coming
        :param link_type: the link type
        :param link_label: the link label
        :raise TypeError: if `source` is not a Node instance or `link_type` is not a `LinkType` enum
        :raise ValueError: if the proposed link is invalid
        """
        from aiida.orm.utils.links import validate_link

        from .node import Node  # pylint: disable=redefined-outer-name

        validate_link(source, self._node, link_type, link_label, backend=self._node.backend)

        # Check if the proposed link would introduce a cycle in the graph following ancestor/descendant rules
        if link_type in [LinkType.CREATE, LinkType.INPUT_CALC, LinkType.INPUT_WORK]:
            builder = QueryBuilder(backend=self._node.backend).append(
                Node, filters={'id': self._node.pk}, tag='parent').append(
                Node, filters={'id': source.pk}, tag='child', with_ancestors='parent')  # yapf:disable
            if builder.count() > 0:
                raise ValueError('the link you are attempting to create would generate a cycle in the graph')

    def validate_outgoing(self, target: 'Node', link_type: LinkType, link_label: str) -> None:  # pylint: disable=unused-argument,no-self-use
        """Validate adding a link of the given type from ourself to a given node.

        The validity of the triple (source, link, target) should be validated in the `validate_incoming` call.
        This method will be called afterwards and can be overriden by subclasses to add additional checks that are
        specific to that subclass.

        :param target: the node to which the link is going
        :param link_type: the link type
        :param link_label: the link label
        :raise TypeError: if `target` is not a Node instance or `link_type` is not a `LinkType` enum
        :raise ValueError: if the proposed link is invalid
        """
        from .node import Node  # pylint: disable=redefined-outer-name
        type_check(link_type, LinkType, f'link_type should be a LinkType enum but got: {type(link_type)}')
        type_check(target, Node, f'target should be a `Node` instance but got: {type(target)}')

    def get_stored_link_triples(
        self,
        node_class: Optional[t.Type['Node']] = None,
        link_type: t.Union[LinkType, t.Sequence[LinkType]] = (),
        link_label_filter: t.Optional[str] = None,
        link_direction: str = 'incoming',
        only_uuid: bool = False
    ) -> list[LinkTriple]:
        """Return the list of stored link triples directly incoming to or outgoing of this node.

        Note this will only return link triples that are stored in the database. Anything in the cache is ignored.

        :param node_class: If specified, should be a class, and it filters only elements of that (subclass of) type
        :param link_type: Only get inputs of this link type, if empty tuple then returns all inputs of all link types.
        :param link_label_filter: filters the incoming nodes by its link label. This should be a regex statement as
            one would pass directly to a QueryBuilder filter statement with the 'like' operation.
        :param link_direction: `incoming` or `outgoing` to get the incoming or outgoing links, respectively.
        :param only_uuid: project only the node UUID instead of the instance onto the `NodeTriple.node` entries
        """
        from .node import Node  # pylint: disable=redefined-outer-name

        if not isinstance(link_type, (tuple, list)):
            link_type = cast(t.Sequence[LinkType], (link_type,))

        if link_type and not all(isinstance(t, LinkType) for t in link_type):
            raise TypeError(f'link_type should be a LinkType or tuple of LinkType: got {link_type}')

        node_class = node_class or Node
        node_filters: dict[str, t.Any] = {'id': {'==': self._node.pk}}
        edge_filters: dict[str, t.Any] = {}

        if link_type:
            edge_filters['type'] = {'in': [t.value for t in link_type]}

        if link_label_filter:
            edge_filters['label'] = {'like': link_label_filter}

        builder = QueryBuilder(backend=self._node.backend)
        builder.append(Node, filters=node_filters, tag='main')

        node_project = ['uuid'] if only_uuid else ['*']
        if link_direction == 'outgoing':
            builder.append(
                node_class,
                with_incoming='main',
                project=node_project,
                edge_project=['type', 'label'],
                edge_filters=edge_filters
            )
        else:
            builder.append(
                node_class,
                with_outgoing='main',
                project=node_project,
                edge_project=['type', 'label'],
                edge_filters=edge_filters
            )

        return [LinkTriple(entry[0], LinkType(entry[1]), entry[2]) for entry in builder.all()]

    def get_incoming(
        self,
        node_class: Optional[t.Type['Node']] = None,
        link_type: t.Union[LinkType, t.Sequence[LinkType]] = (),
        link_label_filter: t.Optional[str] = None,
        only_uuid: bool = False
    ) -> LinkManager:
        """Return a list of link triples that are (directly) incoming into this node.

        :param node_class: If specified, should be a class or tuple of classes, and it filters only
            elements of that specific type (or a subclass of 'type')
        :param link_type: If specified should be a string or tuple to get the inputs of this
            link type, if None then returns all inputs of all link types.
        :param link_label_filter: filters the incoming nodes by its link label.
            Here wildcards (% and _) can be passed in link label filter as we are using "like" in QB.
        :param only_uuid: project only the node UUID instead of the instance onto the `NodeTriple.node` entries
        """
        if not isinstance(link_type, (tuple, list)):
            link_type = cast(t.Sequence[LinkType], (link_type,))

        if self._node.is_stored:
            link_triples = self.get_stored_link_triples(
                node_class, link_type, link_label_filter, 'incoming', only_uuid=only_uuid
            )
        else:
            link_triples = []

        # Get all cached link triples
        for link_triple in self.incoming_cache:

            if only_uuid:
                link_triple = LinkTriple(
                    link_triple.node.uuid,  # type: ignore
                    link_triple.link_type,
                    link_triple.link_label,
                )

            if link_triple in link_triples:
                raise exceptions.InternalError(
                    f'Node<{self._node.pk}> has both a stored and cached link triple {link_triple}'
                )

            if not link_type or link_triple.link_type in link_type:
                if link_label_filter is not None:
                    if sql_string_match(string=link_triple.link_label, pattern=link_label_filter):
                        link_triples.append(link_triple)
                else:
                    link_triples.append(link_triple)

        return LinkManager(link_triples)

    def get_outgoing(
        self,
        node_class: Optional[t.Type['Node']] = None,
        link_type: t.Union[LinkType, t.Sequence[LinkType]] = (),
        link_label_filter: t.Optional[str] = None,
        only_uuid: bool = False
    ) -> LinkManager:
        """Return a list of link triples that are (directly) outgoing of this node.

        :param node_class: If specified, should be a class or tuple of classes, and it filters only
            elements of that specific type (or a subclass of 'type')
        :param link_type: If specified should be a string or tuple to get the inputs of this
            link type, if None then returns all outputs of all link types.
        :param link_label_filter: filters the outgoing nodes by its link label.
            Here wildcards (% and _) can be passed in link label filter as we are using "like" in QB.
        :param only_uuid: project only the node UUID instead of the instance onto the `NodeTriple.node` entries
        """
        link_triples = self.get_stored_link_triples(node_class, link_type, link_label_filter, 'outgoing', only_uuid)
        return LinkManager(link_triples)
