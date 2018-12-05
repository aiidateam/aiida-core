# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Generic backend related objects"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import abc
import typing
import six

from .. import backends

__all__ = ('RelationalBackend',)

EntityType = typing.TypeVar('EntityType')  # pylint: disable=invalid-name


@six.add_metaclass(abc.ABCMeta)
class RelationalBackend(backends.Backend):
    """The public interface that defines a backend factory that creates backend specific concrete objects."""

    @abc.abstractmethod
    def get_backend_entity(self, model_instance):
        """
        Return the backend entity that corresponds to the given Model instance
        :return:
        """
