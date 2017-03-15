# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from collections import Mapping
from aiida.orm.data import Data
from aiida.orm import load_node


class FrozenDict(Data, Mapping):
    """
    An immutable dictionary containing only Data nodes as values.

    .. note::
        All values must be stored before being passed to constructor.
    """

    def __init__(self, **kwargs):
        self._cache = {}
        self._initialised = False
        super(FrozenDict, self).__init__(**kwargs)
        self._initialised = True

    def set_dict(self, dict):
        assert not self._initialised

        for value in dict.itervalues():
            assert isinstance(value, Data)
            assert value.is_stored

        for k, v in dict.iteritems():
            self._set_attr(k, v.pk)

    def __getitem__(self, key):
        return self._get(key)

    def __iter__(self):
        return self.get_attrs().iterkeys()

    def __len__(self):
        return len(self.get_attrs())

    def _get(self, key):
        val = self._cache.get(key, None)
        if val is None:
            val = load_node(self.get_attr(key))
            self._cache[key] = val
        return val