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

    # The name of the attribute to indicate if the node is sealed or not.
    SEALED_KEY = '_sealed'

    _updatable_attributes = (SEALED_KEY,)

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
        assert not self.is_sealed, 'Cannot add incoming links to a sealed calculation node'

        super(Sealable, self).add_link_from(src, label=label, link_type=link_type)

    @property
    def is_sealed(self):
        return self.get_attr(self.SEALED_KEY, False)

    def seal(self):
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

    def iter_updatable_attrs(self):
        for k in list(self._updatable_attributes):
            try:
                yield (k, self.get_attr(k))
            except AttributeError:
                pass

    @override
    def copy(self):
        newobj = super(Sealable, self).copy()

        # Remove the updatable attributes
        for k, v in self.iter_updatable_attrs():
            newobj._del_attr(k)

        return newobj
