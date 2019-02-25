# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""`Data` sub class to represent a dictionary."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import copy

from aiida.common import exceptions
from .data import Data
from .base import to_aiida_type

__all__ = ('Dict',)


class Dict(Data):
    """`Data` sub class to represent a dictionary."""

    def __init__(self, **kwargs):
        """Store a dictionary as a `Node` instance.

        Usual rules for attribute names apply, in particular, keys cannot start with an underscore, or a `ValueError`
        will be raised.

        Initial attributes can be changed, deleted or added as long as the node is not stored.

        :param dict: the dictionary to set
        """
        dictionary = kwargs.pop('dict', None)
        super(Dict, self).__init__(**kwargs)
        if dictionary:
            self.set_dict(dictionary)

    def set_dict(self, dictionary):
        """ Replace the current dictionary with another one.

        :param dictionary: dictionary to set
        """
        dictionary_backup = copy.deepcopy(self.get_dict())

        try:
            # Clear existing attributes and set the new dictionary
            self.clear_attributes()
            self.update_dict(dictionary)
        except exceptions.ModificationNotAllowed:  # pylint: disable=try-except-raise
            # I reraise here to avoid to go in the generic 'except' below that would raise the same exception again
            raise
        except Exception:
            # Try to restore the old data
            self.clear_attributes()
            self.update_dict(dictionary_backup)
            raise

    def update_dict(self, dictionary):
        """Update the current dictionary with the keys provided in the dictionary.

        .. note:: works exactly as `dict.update()` where new keys are simply added and existing keys are overwritten.

        :param dictionary: a dictionary with the keys to substitute
        """
        for key, value in dictionary.items():
            self.set_attribute(key, value)

    def get_dict(self):
        """Return a dictionary with the parameters currently set.

        :return: dictionary
        """
        return dict(self.attributes)

    def keys(self):
        """Iterator of valid keys stored in the Dict object.

        :return: iterator over the keys of the current dictionary
        """
        for key in self.attributes.keys():
            yield key

    @property
    def dict(self):
        """Return an instance of `AttributeManager` that transforms the dictionary into an attribute dict.

        .. note:: this will allow one to do `node.dict.key` as well as `node.dict[key]`.

        :return: an instance of the `AttributeResultManager`.
        """
        from aiida.orm.utils.managers import AttributeManager
        return AttributeManager(self)


@to_aiida_type.register(dict)
def _(value):
    return Dict(dictionary=value)
