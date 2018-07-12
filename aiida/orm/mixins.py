# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

from aiida.common.exceptions import ModificationNotAllowed
from aiida.common.lang import override
from aiida.common.links import LinkType


class Sealable(object):

    # The name of the attribute to indicate if the node is sealed or not
    SEALED_KEY = '_sealed'

    _updatable_attributes = (SEALED_KEY,)

    def add_link_from(self, src, label=None, link_type=LinkType.UNSPECIFIED):
        """
        Add a link from a node

        You can use the parameters of the base Node class, in particular the
        label parameter to label the link.

        :param src: the node to add a link from
        :param str label: name of the link
        :param link_type: type of the link, must be one of the enum values from
          :class:`~aiida.common.links.LinkType`
        """
        if self.is_sealed:
            raise ModificationNotAllowed('Cannot add a link from a sealed node')

        super(Sealable, self).add_link_from(src, label=label, link_type=link_type)

    @property
    def is_sealed(self):
        """
        Returns whether the node is sealed, i.e. whether the sealed attribute has been set to True
        """
        return self.get_attr(self.SEALED_KEY, False)

    def seal(self):
        """
        Seal the node by setting the sealed attribute to True
        """
        if not self.is_sealed:
            self._set_attr(self.SEALED_KEY, True)

    @override
    def _set_attr(self, key, value, **kwargs):
        """
        Set a new attribute

        :param key: attribute name
        :param value: attribute value
        :raise ModificationNotAllowed: if the node is already sealed or if the node is already stored
            and the attribute is not updatable
        """
        if self.is_sealed:
            raise ModificationNotAllowed('Cannot change the attributes of a sealed node')

        if self.is_stored and key not in self._updatable_attributes:
            raise ModificationNotAllowed('Cannot change the immutable attributes of a stored node')

        super(Sealable, self)._set_attr(key, value, stored_check=False, **kwargs)

    @override
    def _del_attr(self, key):
        """
        Delete an attribute

        :param key: attribute name
        :raise AttributeError: if key does not exist
        :raise ModificationNotAllowed: if the node is already sealed or if the node is already stored
            and the attribute is not updatable
        """
        if self.is_sealed:
            raise ModificationNotAllowed('Cannot change the attributes of a sealed node')

        if self.is_stored and key not in self._updatable_attributes:
            raise ModificationNotAllowed('Cannot change the immutable attributes of a stored node')

        super(Sealable, self)._del_attr(key, stored_check=False)

    @override
    def copy(self, include_updatable_attrs=False):
        """
        Create a copy of the node minus the updatable attributes
        """
        clone = super(Sealable, self).copy()

        # Remove the updatable attributes
        if not include_updatable_attrs:
            for key, value in clone._iter_updatable_attributes():
                clone._del_attr(key)

        return clone

    def _iter_updatable_attributes(self):
        """
        Iterate over the updatable attributes and yield key value pairs
        """
        for key in list(self._updatable_attributes):
            try:
                yield (key, self.get_attr(key))
            except AttributeError:
                pass
