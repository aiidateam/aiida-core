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

from .data import Data
from .base import to_aiida_type

__all__ = ('ParameterData',)


class ParameterData(Data):
    """
    Pass as input in the init a dictionary, and it will get stored as internal attributes.

    Usual rules for attribute names apply (in particular, keys cannot start with
    an underscore). If this is the case, a ValueError will be raised.

    You can then change/delete/add more attributes before storing with the
    usual methods of aiida.orm.Node
    """

    def __init__(self, **kwargs):
        dictionary = kwargs.pop('dict', None)
        super(ParameterData, self).__init__(**kwargs)
        if dictionary:
            self.set_dict(dictionary)

    def set_dict(self, dict):
        """
        Replace the current dictionary with another one.

        :param dict: The dictionary to set.
        """
        import copy
        from aiida.common.exceptions import ModificationNotAllowed

        old_dict = copy.deepcopy(self.get_dict())

        try:
            # Delete existing attributes
            self.clear_attributes()
            # I set the keys
            self.update_dict(dict)
        except ModificationNotAllowed:
            # I reraise here to avoid to go in the generic 'except' below,
            # that would raise again the same exception
            raise
        except Exception:
            # Try to restore the old data
            self.clear_attributes()
            self.update_dict(old_dict)
            raise

    def update_dict(self, dict):
        """
        Update the current dictionary with the keys provided in the dictionary.

        :param dict: a dictionary with the keys to substitute. It works like
          dict.update(), adding new keys and overwriting existing keys.
        """
        for key, value in dict.items():
            self.set_attribute(key, value)

    def get_dict(self):
        """
        Return a dict with the parameters
        """
        return dict(self.attributes)

    def keys(self):
        """
        Iterator of valid keys stored in the ParameterData object
        """
        for key in self.attributes.keys():
            yield key

    def add_path(self, *args, **kwargs):
        from aiida.common.exceptions import ModificationNotAllowed
        raise ModificationNotAllowed('Cannot add files or directories to a ParameterData object')

    @property
    def dict(self):
        """
        To be used to get direct access to the underlying dictionary with the
        syntax node.dict.key or node.dict['key'].

        :return: an instance of the AttributeResultManager.
        """
        from aiida.orm.utils.managers import AttributeManager
        return AttributeManager(self)


@to_aiida_type.register(dict)
def _(value):
    return ParameterData(dict=value)
