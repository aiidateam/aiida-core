# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""`Data` sub class to represent a list."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from collections import MutableSequence

from .data import Data

__all__ = ('List',)


class List(Data, MutableSequence):
    """`Data` sub class to represent a list."""

    _LIST_KEY = 'list'

    def __init__(self, **kwargs):
        data = kwargs.pop('list', list())
        super(List, self).__init__(**kwargs)
        self.set_list(data)

    def __getitem__(self, item):
        return self.get_list()[item]

    def __setitem__(self, key, value):
        data = self.get_list()
        data[key] = value
        if not self._using_list_reference():
            self.set_list(data)

    def __delitem__(self, key):
        data = self.get_list()
        del data[key]
        if not self._using_list_reference():
            self.set_list(data)

    def __len__(self):
        return len(self.get_list())

    def __str__(self):
        return super(List, self).__str__() + ' value: {}'.format(self.get_list())

    def __eq__(self, other):
        try:
            return self.get_list() == other.get_list()
        except AttributeError:
            return self.get_list() == other

    def __ne__(self, other):
        return not self == other

    def append(self, value):
        data = self.get_list()
        data.append(value)
        if not self._using_list_reference():
            self.set_list(data)

    def extend(self, value):  # pylint: disable=arguments-differ
        data = self.get_list()
        data.extend(value)
        if not self._using_list_reference():
            self.set_list(data)

    def insert(self, i, value):  # pylint: disable=arguments-differ
        data = self.get_list()
        data.insert(i, value)
        if not self._using_list_reference():
            self.set_list(data)

    def remove(self, value):
        del self[value]

    def pop(self, **kwargs):  # pylint: disable=arguments-differ
        data = self.get_list()
        data.pop(**kwargs)
        if not self._using_list_reference():
            self.set_list(data)

    def index(self, value):  # pylint: disable=arguments-differ
        return self.get_list().index(value)

    def count(self, value):
        return self.get_list().count(value)

    def sort(self, key=None, reverse=False):
        data = self.get_list()
        data.sort(key=key, reverse=reverse)
        if not self._using_list_reference():
            self.set_list(data)

    def reverse(self):
        data = self.get_list()
        data.reverse()
        if not self._using_list_reference():
            self.set_list(data)

    def get_list(self):
        """Return the contents of this node.

        :return: a list
        """
        try:
            return self.get_attribute(self._LIST_KEY)
        except AttributeError:
            self.set_list(list())
            return self.get_attribute(self._LIST_KEY)

    def set_list(self, data):
        """Set the contents of this node.

        :param data: the list to set
        """
        if not isinstance(data, list):
            raise TypeError('Must supply list type')
        self.set_attribute(self._LIST_KEY, data)

    def _using_list_reference(self):
        """
        This function tells the class if we are using a list reference.  This
        means that calls to self.get_list return a reference rather than a copy
        of the underlying list and therefore self.set_list need not be called.
        This knwoledge is essential to make sure this class is performant.

        Currently the implementation assumes that if the node needs to be
        stored then it is using the attributes cache which is a reference.

        :return: True if using self.get_list returns a reference to the
            underlying sequence.  False otherwise.
        :rtype: bool
        """
        return not self.is_stored
