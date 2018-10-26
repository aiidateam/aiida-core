# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Backend user"""
from __future__ import absolute_import
import abc
import six

from . import backends

__all__ = ('BackendUser',)


@six.add_metaclass(abc.ABCMeta)
class BackendUser(backends.BackendEntity):
    """
    This is the base class for User information in AiiDA.  An implementing
    backend needs to provide a concrete version.
    """
    # pylint: disable=invalid-name

    REQUIRED_FIELDS = ['first_name', 'last_name', 'institution']

    @property
    def uuid(self):
        """
        For now users do not have UUIDs so always return false

        :return: None
        """
        return None

    @abc.abstractproperty
    def email(self):
        pass

    @abc.abstractmethod
    @email.setter
    def email(self, val):
        pass

    @abc.abstractmethod
    def get_password(self):
        pass

    @abc.abstractmethod
    def set_password(self, new_pass):
        pass

    @abc.abstractproperty
    def first_name(self):
        pass

    @abc.abstractmethod
    @first_name.setter
    def first_name(self, val):
        pass

    @abc.abstractproperty
    def last_name(self):
        pass

    @abc.abstractmethod
    @last_name.setter
    def last_name(self, val):
        pass

    @abc.abstractproperty
    def institution(self):
        pass

    @abc.abstractmethod
    @institution.setter
    def institution(self, val):
        pass

    @abc.abstractproperty
    def is_active(self):
        pass

    @abc.abstractmethod
    @is_active.setter
    def is_active(self, val):
        pass

    @abc.abstractproperty
    def last_login(self):
        pass

    @abc.abstractmethod
    @last_login.setter
    def last_login(self, val):
        pass

    @abc.abstractproperty
    def date_joined(self):
        pass

    @abc.abstractmethod
    @date_joined.setter
    def date_joined(self, val):
        pass


class BackendUserCollection(backends.BackendCollection):
    # pylint: disable=too-few-public-methods
    ENTRY_TYPE = BackendUser
