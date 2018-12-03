# -*- coding: utf-8 -*-
"""ORM class for CalculationNode."""
from __future__ import absolute_import

from .. import ProcessNode

__all__ = ('CalculationNode',)


class CalculationNode(ProcessNode):
    """Base class for all nodes representing the execution of a calculation process."""
    # pylint: disable=too-few-public-methods

    _cacheable = True

    def validate_incoming(self, source, link_type, link_label):
        """
        Validate adding a link of the given type from a given node to ourself.

        This function will first validate the types of the inputs, followed by the node and link types and validate
        whether in principle a link of that type between the nodes of these types is allowed.the

        Subsequently, the validity of the "degree" of the proposed link is validated, which means validating the
        number of links of the given type from the given node type is allowed.

        :param source: the node from which the link is coming
        :param link_type: the type of link
        :param link_label: link label
        :raise TypeError: if `source` is not a Node instance or `link_type` is not a `LinkType` enum
        :raise ValueError: if the proposed link is invalid
        """
        super(CalculationNode, self).validate_incoming(source, link_type, link_label)
        from aiida.orm.utils.links import validate_link
        validate_link(source, self, link_type, link_label)
