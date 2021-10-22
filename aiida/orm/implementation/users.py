# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Backend user"""
import abc

from .entities import BackendCollection, BackendEntity

__all__ = ('BackendUser', 'BackendUserCollection')


class BackendUser(BackendEntity):
    """
    This is the base class for User information in AiiDA.  An implementing
    backend needs to provide a concrete version.
    """
    # pylint: disable=invalid-name

    REQUIRED_FIELDS = ['first_name', 'last_name', 'institution']

    @property
    @abc.abstractmethod
    def email(self):
        """
        Get the email address of the user

        :return: the email address
        """

    @email.setter
    @abc.abstractmethod
    def email(self, val):
        """
        Set the email address of the user

        :param val: the new email address
        """

    @property
    @abc.abstractmethod
    def first_name(self):
        """
        Get the user's first name

        :return: the first name
        :rtype: str
        """

    @first_name.setter
    @abc.abstractmethod
    def first_name(self, val):
        """
        Set the user's first name

        :param val: the new first name
        """

    @property
    @abc.abstractmethod
    def last_name(self):
        """
        Get the user's last name

        :return: the last name
        :rtype: str
        """

    @last_name.setter
    @abc.abstractmethod
    def last_name(self, val):
        """
        Set the user's last name

        :param val: the new last name
        :type val: str
        """

    @property
    @abc.abstractmethod
    def institution(self):
        """
        Get the user's institution

        :return: the institution
        :rtype: str
        """

    @institution.setter
    @abc.abstractmethod
    def institution(self, val):
        """
        Set the user's institution

        :param val: the new institution
        """


class BackendUserCollection(BackendCollection[BackendUser]):

    ENTITY_CLASS = BackendUser
