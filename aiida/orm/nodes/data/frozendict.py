# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import collections

from .data import Data

__all__ = ('FrozenDict',)


class FrozenDict(Data, collections.Mapping):
    """
    An immutable dictionary containing only Data nodes as values.

    .. note::
        All values must be stored before being passed to constructor.
    """

    def __init__(self, **kwargs):
        self._initialized = False
        dictionary = kwargs.pop('dict', None)
        super(FrozenDict, self).__init__(**kwargs)
        self.set_dictionary(dictionary)
        self._initialized = True

    def initialize(self):
        super(FrozenDict, self).initialize()
        self._cache = {}

    def set_dictionary(self, dictionary):
        assert not self._initialized

        for value in dictionary.values():
            assert isinstance(value, Data)
            assert value.is_stored

        attributes = {key: value.pk for key, value in dictionary.items()}
        self.set_attributes(attributes)

    def __getitem__(self, key):
        return self._get(key)

    def __iter__(self):
        for key in self.attributes_keys():
            yield key

    def __len__(self):
        return len(list(self.attributes_keys()))

    def _get(self, key):
        from ...utils import load_node
        val = self._cache.get(key, None)
        if val is None:
            val = load_node(self.get_attribute(key))
            self._cache[key] = val
        return val
