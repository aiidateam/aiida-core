# -*- coding: utf-8 -*-

from aiida.common.exceptions import ModificationNotAllowed
from aiida.common.lang import override
from aiida.common.links import LinkType

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__authors__ = "The AiiDA team."
__version__ = "0.7.0.1"


class SealableMixin(object):

    # The name of the attribute to indiate if the node is sealed or not.
    SEALED_KEY = '_sealed'

    def add_link_from(self, src, label=None, link_type=LinkType.INPUT):
        """
        Add a link with a code as destination.

        You can use the parameters of the base Node class, in particular the
        label parameter to label the link.

        :param src: a node of the database. It cannot be a Calculation object.
        :param str label: Name of the link. Default=None
        :param link_type: The type of link, must be one of the enum values form
          :class:`~aiida.common.links.LinkType`
        """
        assert not self.is_sealed, \
            "Cannot add incoming links to a sealed calculation node"

        super(SealableMixin, self).add_link_from(src, label=label,
                                                 link_type=link_type)

    @property
    def is_sealed(self):
        return self.get_attr(self.SEALED_KEY, False)

    def seal(self):
        if not self.is_sealed:
            self._set_attr(self.SEALED_KEY, True)


class SealableWithUpdatableAttributesMixin(SealableMixin):
    _updatable_attributes = tuple()

    @override
    def _set_attr(self, key, value):
        """
        Set a new attribute to the Node (in the DbAttribute table).

        :param str key: key name
        :param value: its value
        :raise ModificationNotAllowed: if such attribute cannot be added (e.g.
            because the node was already stored, and the attribute is not listed
            as updatable).

        :raise ValidationError: if the key is not valid (e.g. it contains the
            separator symbol).
        """
        if self.is_sealed and key not in self._updatable_attributes:
            raise ModificationNotAllowed(
                "Cannot change the attributes of a sealed calculation.")
        super(SealableWithUpdatableAttributesMixin, self)._set_attr(key, value)

    @override
    def _del_attr(self, key):
        """
        Delete an attribute.

        :param key: attribute to delete.
        :raise AttributeError: if key does not exist.
        :raise ModificationNotAllowed: if the Node was already stored.
        """
        if self.is_sealed and key not in self._updatable_attributes:
            raise ModificationNotAllowed(
                "Cannot delete the attributes of a sealed calculation.")
        super(SealableWithUpdatableAttributesMixin, self)._del_attr(key)


    @override
    def _del_attr(self, key):
        if self.is_sealed and key not in self._updatable_attributes:
            raise ModificationNotAllowed(
                "Cannot delete an attribute of a sealed calculation node")
        super(SealableWithUpdatableAttributesMixin, self)._del_attr(key)

    def iter_updatable_attrs(self):
        for k in list(self._updatable_attributes):
            try:
                yield (k, self.get_attr(k))
            except AttributeError:
                pass

    @override
    def copy(self):
        newobj = super(SealableWithUpdatableAttributesMixin, self).copy()

        # Remove the updatable attributes
        for k, v in self.iter_updatable_attrs():
            newobj._del_attr(k)

        return newobj
