# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""`Data` sub class to represent an immutable dictionary containing only `Data` nodes as values."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import collections

from .data import Data

__all__ = ('FrozenDict',)


class FrozenDict(Data, collections.Mapping):
    """`Data` sub class to represent an immutable dictionary containing only `Data` nodes as values.

    .. note:: all nodes in the dictionary must be stored before being passed to constructor.
    """

    def __init__(self, **kwargs):
        self._initialized = False
        dictionary = kwargs.pop('dict', None)
        super(FrozenDict, self).__init__(**kwargs)
        self.set_dictionary(dictionary)
        self._initialized = True

    def initialize(self):
        """Initialize the `_cache` to an empty dictionary.

        .. note:: this has to be done here and not in the constructor, because otherwise the cache would not be
            initialized if the node instance would be loaded from an existing node.
        """
        super(FrozenDict, self).initialize()
        self._cache = {}  # pylint: disable=attribute-defined-outside-init

    def set_dictionary(self, dictionary):
        """Set the dictionary for this node.

        :param dictionary: a dictionary of stored nodes
        """
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
        """Return the node from the dictionary stored under the name `key`, using an internal cache.

        :param key: key of the node in the dictionary
        :return: the `Node` instance
        """
        from ...utils import load_node

        node = self._cache.get(key, None)

        if node is None:
            node = load_node(self.get_attribute(key))
            self._cache[key] = node

        return node
