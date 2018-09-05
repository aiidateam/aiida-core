# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from __future__ import absolute_import
from collections import MutableSequence
from aiida.orm.data import Data


class List(Data, MutableSequence):
    """
    Class to store python lists as AiiDA nodes
    """
    _LIST_KEY = 'list'

    def __init__(self, **kwargs):
        if 'list' not in kwargs and 'dbnode' not in kwargs:
            kwargs['list'] = list()
        super(List, self).__init__(**kwargs)

    def __getitem__(self, item):
        return self.get_list()[item]

    def __setitem__(self, key, value):
        l = self.get_list()
        l[key] = value
        if not self._using_list_reference():
            self.set_list(l)

    def __delitem__(self, key):
        l = self.get_list()
        del l[key]
        if not self._using_list_reference():
            self.set_list(l)

    def __len__(self):
        return len(self.get_list())

    def __str__(self):
        return self.get_list().__str__()

    def __eq__(self, other):
        try:
            return self.get_list() == other.get_list()
        except AttributeError:
            return self.get_list() == other

    def __ne__(self, other):
        return not self == other

    def append(self, value):
        l = self.get_list()
        l.append(value)
        if not self._using_list_reference():
            self.set_list(l)

    def extend(self, L):
        l = self.get_list()
        l.extend(L)
        if not self._using_list_reference():
            self.set_list(l)

    def insert(self, i, value):
        l = self.get_list()
        l.insert(i, value)
        if not self._using_list_reference():
            self.set_list(l)

    def remove(self, value):
        del self[value]

    def pop(self, **kwargs):
        l = self.get_list()
        l.pop(**kwargs)
        if not self._using_list_reference():
            self.set_list(l)

    def index(self, value):
        return self.get_list().index(value)

    def count(self, value):
        return self.get_list().count(value)

    def sort(self, key=None, reverse=False):
        l = self.get_list()
        l.sort(key=key, reverse=reverse)
        if not self._using_list_reference():
            self.set_list(l)

    def reverse(self):
        l = self.get_list()
        l.reverse()
        if not self._using_list_reference():
            self.set_list(l)

    def get_list(self):
        try:
            return self.get_attr(self._LIST_KEY)
        except AttributeError:
            self.set_list(list())
            return self.get_attr(self._LIST_KEY)

    def set_list(self, list_):
        if not isinstance(list_, list):
            raise TypeError('Must supply list type')
        self._set_attr(self._LIST_KEY, list_)

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
