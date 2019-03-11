# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""
Contain utility classes for "managers", i.e., classes that act allow
to access members of other classes via TAB-completable attributes
(e.g. the class underlying `calculation.inputs` to allow to do `calculation.inputs.<label>`).
"""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from aiida.common.links import LinkType

__all__ = ('NodeLinksManager', 'AttributeManager')


class NodeLinksManager(object):  # pylint: disable=too-few-public-methods,useless-object-inheritance
    """
    A manager that allows to inspect, with tab-completion, nodes linked to a given one.
    See an example of its use in `CalculationNode.inputs`.
    """

    def __init__(self, node, link_type, incoming):
        """
        Initialise the link manager.

        :param node: the reference node object
        :param link_type: the link_type to inspect
        :param incoming: if True, inspect incoming links, otherwise inspect
            outgoing links
        """
        # This import is here to avoid circular imports
        from aiida.orm import Node

        if not isinstance(node, Node):
            raise TypeError("node must be a valid AiiDA Node")
        self._node = node
        if not isinstance(link_type, LinkType):
            raise TypeError("link_type must be a valid LinkType")
        self._link_type = link_type
        self._incoming = incoming

    def _get_keys(self):
        """Return the valid link labels, used e.g. to make getattr() work"""
        if self._incoming:
            node_attributes = self._node.get_incoming(link_type=self._link_type).all_link_labels()
        else:
            node_attributes = self._node.get_outgoing(link_type=self._link_type).all_link_labels()
        return node_attributes

    def _get_node_by_link_label(self, label):
        """
        Return the linked node with a given link label

        :param label: the link label connecting the current node to the node to get
        """
        if self._incoming:
            return self._node.get_incoming(link_type=self._link_type).get_node_by_label(label)
        return self._node.get_outgoing(link_type=self._link_type).get_node_by_label(label)

    def __dir__(self):
        """
        Allow to list all valid input links
        """
        node_attributes = self._get_keys()
        return sorted(set(list(dir(type(self))) + list(node_attributes)))

    def __iter__(self):
        node_attributes = self._get_keys()
        for k in node_attributes:
            yield k

    def __getattr__(self, name):
        """
        :param name: name of the attribute to be asked to the parser results.
        """
        try:
            return self._get_node_by_link_label(label=name)
        except KeyError:
            raise AttributeError("Node '{}' does not have an input with link '{}'".format(self._node.pk, name))

    def __getitem__(self, name):
        """
        interface to get to the parser results as a dictionary.

        :param name: name of the attribute to be asked to the parser results.
        """
        try:
            return self._get_node_by_link_label(label=name)
        except KeyError:
            raise KeyError("Node '{}' does not have an input with link '{}'".format(self._node.pk, name))

    def __str__(self):
        """Return a string representation of the manager"""
        return "Manager for {} {} links for node pk={}".format("incoming" if self._incoming else "outgoing",
                                                               self._link_type.value.upper(), self._node.pk)

    def __repr__(self):
        return '<{}: {}>'.format(self.__class__.__name__, str(self))


class AttributeManager(object):  # pylint: disable=too-few-public-methods,useless-object-inheritance
    """
    An object used internally to return the attributes as a dictionary.
    This is currently used in :py:class:`~aiida.orm.nodes.data.dict.Dict`,
    for instance.

    :note: Important! It cannot be used to change variables, just to read
      them. To change values (of unstored nodes), use the proper Node methods.
    """

    def __init__(self, node):
        """
        :param node: the node object.
        """
        # Possibly add checks here
        self._node = node

    def __dir__(self):
        """
        Allow to list the keys of the dictionary
        """
        return sorted(self._node.attributes_items())

    def __iter__(self):
        """
        Return the keys as an iterator
        """
        for k in self._node.attributes_keys():
            yield k

    def _get_dict(self):
        """
        Return the internal dictionary
        """
        return dict(self._node.attributes_items())

    def __getattr__(self, name):
        """
        Interface to get to dictionary values, using the key as an attribute.

        :note: it works only for attributes that only contain letters, numbers
          and underscores, and do not start with a number.

        :param name: name of the key whose value is required.
        """
        return self._node.get_attribute(name)

    def __getitem__(self, name):
        """
        Interface to get to dictionary values as a dictionary.

        :param name: name of the key whose value is required.
        """
        try:
            return self._node.get_attribute(name)
        except AttributeError as err:
            raise KeyError(str(err))
