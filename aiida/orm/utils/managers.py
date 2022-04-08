# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""
Contain utility classes for "managers", i.e., classes that allow
to access members of other classes via TAB-completable attributes
(e.g. the class underlying `calculation.inputs` to allow to do `calculation.inputs.<label>`).
"""
from aiida.common import AttributeDict
from aiida.common.exceptions import NotExistent, NotExistentAttributeError, NotExistentKeyError
from aiida.common.links import LinkType
from aiida.common.warnings import warn_deprecation

__all__ = ('NodeLinksManager', 'AttributeManager')


class NodeLinksManager:
    """
    A manager that allows to inspect, with tab-completion, nodes linked to a given one.
    See an example of its use in `CalculationNode.inputs`.
    """

    _namespace_separator = '__'

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
            raise TypeError('node must be a valid AiiDA Node')
        self._node = node
        if not isinstance(link_type, LinkType):
            raise TypeError('link_type must be a valid LinkType')
        self._link_type = link_type
        self._incoming = incoming

    def _construct_attribute_dict(self, incoming):
        """Construct an attribute dict from all links of the node, recreating nested namespaces from flat link labels.

        :param incoming: if True, inspect incoming links, otherwise inspect outgoing links.
        """
        if incoming:
            links = self._node.base.links.get_incoming(link_type=self._link_type)
        else:
            links = self._node.base.links.get_outgoing(link_type=self._link_type)

        return AttributeDict(links.nested())

    def _get_keys(self):
        """Return the valid link labels, used e.g. to make getattr() work"""
        attribute_dict = self._construct_attribute_dict(self._incoming)

        return attribute_dict.keys()

    def _get_node_by_link_label(self, label):
        """Return the linked node with a given link label.

        Nested namespaces in link labels get represented by double underscores in the database. Up until now, the link
        manager didn't automatically unroll these again into nested namespaces and so a user was forced to pass the link
        with double underscores to dereference the corresponding node. For example, when used with the ``inputs``
        attribute of a ``ProcessNode`` one had to do:

            node.inputs.nested__sub__namespace

        Now it is possible to do

            node.inputs.nested.sub.namespace

        which is more intuitive since the double underscore replacement is just for the database and the user shouldn't
        even have to know about it. For compatibility we support the old version a bit longer and it will emit a
        deprecation warning.

        :param label: the link label connecting the current node to the node to get.
        """
        attribute_dict = self._construct_attribute_dict(self._incoming)
        try:
            node = attribute_dict[label]
        except KeyError as exception:
            # Check whether the label contains a double underscore, in which case we want to warn the user that this is
            # deprecated. However, we need to exclude labels that corresponds to dunder methods, i.e., those that start
            # and end with a double underscore.
            if (
                self._namespace_separator in label and
                not (label.startswith(self._namespace_separator) and label.endswith(self._namespace_separator))
            ):
                import functools
                warn_deprecation(
                    'dereferencing nodes with links containing double underscores is deprecated, simply replace '
                    'the double underscores with a single dot instead. For example: \n'
                    '`self.inputs.some__label` can be written as `self.inputs.some.label` instead.\n',
                    version=3
                )  # pylint: disable=no-member
                namespaces = label.split(self._namespace_separator)
                try:
                    return functools.reduce(lambda d, namespace: d.get(namespace), namespaces, attribute_dict)
                except TypeError as exc:
                    # This can be raised if part of the `namespaces` correspond to an actual leaf node, but is treated
                    # like a namespace
                    raise NotExistent from exc
                except AttributeError as exc:
                    # This will be raised if any of the intermediate namespaces don't exist, and so the label node does
                    # not exist.
                    raise NotExistent from exc
            raise NotExistent from exception

        return node

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
        except NotExistent as exception:
            # Note: in order for TAB-completion to work, we need to raise an exception that also inherits from
            # `AttributeError`, so that `getattr(node.inputs, 'some_label', some_default)` returns `some_default`.
            # Otherwise, the exception is not caught by `getattr` and is propagated, instead of returning the default.
            prefix = 'input' if self._incoming else 'output'
            raise NotExistentAttributeError(
                f"Node<{self._node.pk}> does not have an {prefix} with link label '{name}'"
            ) from exception

    def __contains__(self, key):
        """Override the operator of the base class to emit deprecation warning if double underscore is used in key."""
        if self._namespace_separator in key:
            warn_deprecation(
                'The use of double underscores in keys is deprecated. Please expand the namespaces manually:\n'
                'instead of `nested__key in node.inputs`, use `nested in node.inputs and `key in node.inputs.nested`.',
                version=3
            )
            namespaces = key.split(self._namespace_separator)
            leaf = namespaces.pop()
            subdictionary = self
            for namespace in namespaces:
                try:
                    subdictionary = subdictionary[namespace]
                except KeyError:
                    return False
            return leaf in subdictionary

        return key in self._get_keys()

    def __getitem__(self, name):
        """
        interface to get to the parser results as a dictionary.

        :param name: name of the attribute to be asked to the parser results.
        """
        try:
            return self._get_node_by_link_label(label=name)
        except NotExistent as exception:
            # Note: in order for this class to behave as a dictionary, we raise an exception that also inherits from
            # `KeyError` - in this way, users can use the standard construct `try/except KeyError` and this will behave
            # like a standard dictionary.
            prefix = 'input' if self._incoming else 'output'
            raise NotExistentKeyError(
                f"Node<{self._node.pk}> does not have an {prefix} with link label '{name}'"
            ) from exception

    def __str__(self):
        """Return a string representation of the manager"""
        prefix = 'incoming' if self._incoming else 'outgoing'
        return f'Manager for {prefix} {self._link_type.value.upper()} links for node pk={self._node.pk}'

    def __repr__(self):
        return f'<{self.__class__.__name__}: {str(self)}>'


class AttributeManager:
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
        # We cannot set `self._node` because it would go through the __setattr__ method
        # which uses said _node by calling `self._node.base.attributes.set(name, value)`.
        # Instead, we need to manually set it through the `self.__dict__` property.
        self.__dict__['_node'] = node

    def __dir__(self):
        """
        Allow to list the keys of the dictionary
        """
        return sorted(self._node.base.attributes.keys())

    def __iter__(self):
        """
        Return the keys as an iterator
        """
        for k in self._node.base.attributes.keys():
            yield k

    def _get_dict(self):
        """
        Return the internal dictionary
        """
        return dict(self._node.base.attributes.items())

    def __getattr__(self, name):
        """
        Interface to get to dictionary values, using the key as an attribute.

        :note: it works only for attributes that only contain letters, numbers
          and underscores, and do not start with a number.

        :param name: name of the key whose value is required.
        """
        return self._node.base.attributes.get(name)

    def __setattr__(self, name, value):
        self._node.base.attributes.set(name, value)

    def __getitem__(self, name):
        """
        Interface to get to dictionary values as a dictionary.

        :param name: name of the key whose value is required.
        """
        try:
            return self._node.base.attributes.get(name)
        except AttributeError as exception:
            raise KeyError(str(exception)) from exception
