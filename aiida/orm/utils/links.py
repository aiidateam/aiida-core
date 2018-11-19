# -*- coding: utf-8 -*-
"""Utilities for dealing with links between nodes."""
from __future__ import absolute_import


def validate_link(source, target, link_type, link_label=None):
    """
    Validate adding a link of the given type from a given node to ourself.

    This function will first validate the types of the inputs, followed by the node and link types and validate
    whether in principle a link of that type between the nodes of these types is allowed.the

    Subsequently, the validity of the "degree" of the proposed link is validated, which means validating the
    number of links of the given type from the given node type is allowed.

    :param source: the node from which the link is coming
    :param target: the node to which the link is going
    :param link_type: the type of link
    :param link_label: optional link label
    :raise TypeError: if `source` or `target` is not a Node instance, or `link_type` is not a `LinkType` enum
    :raise ValueError: if the proposed link is invalid
    """
    from aiida.common.links import LinkType
    from aiida.orm.data import Data
    from aiida.orm.implementation.general.node import AbstractNode
    from aiida.orm.node.process import CalculationNode, WorkflowNode

    if not isinstance(link_type, LinkType):
        raise TypeError('the link_type should be a value from the LinkType enum')

    if not isinstance(source, AbstractNode):
        raise TypeError('the source should be a Node instance')

    if not isinstance(target, AbstractNode):
        raise TypeError('the target should be a Node instance')

    if source.uuid == target.uuid:
        raise ValueError('cannot add a link to oneself')

    # For each link type, defines a tuple that defines the valid types for the source and target node, as well as
    # the indegree character. If the indegree is `unique` that means that there can only be a single incoming link
    # of this type for the target node, regardless of the label. If instead it is `unique_label`, an infinite amount
    # of links can be incoming to the target node, as long as the link label is unique for the combination of source
    # type and link type. For example, a Data node can have infinite `RETURN` links from a WorkflowNode, even a single
    # WorkflowNode, as long as the link labels are unique.
    link_mapping = {
        LinkType.CALL_CALC: (WorkflowNode, CalculationNode, 'unique'),
        LinkType.CALL_WORK: (WorkflowNode, WorkflowNode, 'unique'),
        LinkType.INPUT_CALC: (Data, CalculationNode, 'unique_label'),
        LinkType.INPUT_WORK: (Data, WorkflowNode, 'unique_label'),
        LinkType.CREATE: (CalculationNode, Data, 'unique'),
        LinkType.RETURN: (WorkflowNode, Data, 'unique_label'),
    }

    type_source, type_target, type_degree = link_mapping[link_type]

    if not isinstance(source, type_source) or not isinstance(target, type_target):
        raise ValueError('cannot add a {} link from {} to {}'.format(link_type, type(source), type(target)))

    incoming = dict(target.get_inputs(node_type=type(source), link_type=link_type, also_labels=True))

    # If there are already existing incoming links, verify that the proposed link does not violate the indegree
    if type_degree == 'unique' and incoming:
        raise ValueError('node<{}> already has an incoming {} link'.format(target.uuid, link_type))

    # If the indegree is `unique_label` than the pair (source, label) should be unique for the target node
    if type_degree == 'unique_label' and (source.uuid, link_label) in [(n.uuid, l) for l, n in incoming.items()]:
        raise ValueError('node<{}> already has an incoming {} link with label "{}" from node<{}>'.format(
            target.uuid, link_type, link_label, source.uuid))
