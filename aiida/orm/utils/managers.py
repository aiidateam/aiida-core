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
(e.g. the class underlying `node.inp` to allow to do `node.inp.label`).
"""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

__all__ = ('NodeInputManager', 'NodeOutputManager', 'AttributeManager')


class NodeInputManager(object):  # pylint: disable=too-few-public-methods,useless-object-inheritance
    """
    A manager that allows to do node.inp.xxx to get the input named 'xxx'
    of a given node.
    """

    def __init__(self, node):
        """
        :param node: the node object.
        """
        # Possibly add checks here
        self._node = node

    def __dir__(self):
        """
        Allow to list all valid input links
        """
        node_attributes = self._node.get_incoming().all_link_labels()
        return sorted(set(list(dir(type(self))) + list(node_attributes)))

    def __iter__(self):
        node_attributes = self._node.get_incoming().all_link_labels()
        for k in node_attributes:
            yield k

    def __getattr__(self, name):
        """
        :param name: name of the attribute to be asked to the parser results.
        """
        try:
            return self._node.get_incoming().get_node_by_label(name)
        except KeyError:
            raise AttributeError("Node '{}' does not have an input with link '{}'".format(self._node.pk, name))

    def __getitem__(self, name):
        """
        interface to get to the parser results as a dictionary.

        :param name: name of the attribute to be asked to the parser results.
        """
        try:
            return self._node.get_incoming().get_node_by_label(name)
        except KeyError:
            raise KeyError("Node '{}' does not have an input with link '{}'".format(self._node.pk, name))


class NodeOutputManager(object):  # pylint: disable=too-few-public-methods,useless-object-inheritance
    """
    A manager that allows to do node.out.xxx to get the output named 'xxx'
    of a given node.
    """

    def __init__(self, node):
        """
        :param node: the node object.
        """
        # Possibly add checks here
        self._node = node

    def __dir__(self):
        """
        Allow to list all valid output links
        """
        node_attributes = self._node.get_outgoing().all_link_labels()
        return sorted(set(list(dir(type(self))) + list(node_attributes)))

    def __iter__(self):
        node_attributes = self._node.get_outgoing().all_link_labels()
        for k in node_attributes:
            yield k

    def __getattr__(self, name):
        """
        :param name: name of the attribute to be asked to the parser results.
        """
        try:
            return self._node.get_outgoing().get_node_by_label(name)
        except KeyError:
            raise AttributeError("Node {} does not have an output with link {}".format(self._node.pk, name))

    def __getitem__(self, name):
        """
        interface to get to the parser results as a dictionary.

        :param name: name of the attribute to be asked to the parser results.
        """
        try:
            return self._node.get_outgoing().get_node_by_label(name)
        except KeyError:
            raise KeyError("Node {} does not have an output with link {}".format(self._node.pk, name))


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
