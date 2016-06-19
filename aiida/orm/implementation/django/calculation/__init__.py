# -*- coding: utf-8 -*-

from aiida.orm.implementation.django.node import Node
from aiida.orm.implementation.general.calculation import AbstractCalculation
from aiida.common.exceptions import ModificationNotAllowed
from aiida.common.lang import override

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/.. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__authors__ = "The AiiDA team."
__version__ = "0.6.0"


class Calculation(AbstractCalculation, Node):
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
        super(Calculation, self)._set_attr(key, value)

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
        super(Calculation, self)._del_attr(key)


