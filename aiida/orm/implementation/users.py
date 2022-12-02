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
    """Backend implementation for the `User` ORM class.

    A user can be assigned as the creator of a variety of other entities.
    """

    @property
    @abc.abstractmethod
    def email(self) -> str:
        """
        Get the email address of the user

        :return: the email address
        """

    @email.setter
    @abc.abstractmethod
    def email(self, val: str) -> None:
        """
        Set the email address of the user

        :param val: the new email address
        """

    @property
    @abc.abstractmethod
    def first_name(self) -> str:
        """
        Get the user's first name

        :return: the first name
        """

    @first_name.setter
    @abc.abstractmethod
    def first_name(self, val: str) -> None:
        """
        Set the user's first name

        :param val: the new first name
        """

    @property
    @abc.abstractmethod
    def last_name(self) -> str:
        """
        Get the user's last name

        :return: the last name
        """

    @last_name.setter
    @abc.abstractmethod
    def last_name(self, val: str) -> None:
        """
        Set the user's last name

        :param val: the new last name
        """

    @property
    @abc.abstractmethod
    def institution(self) -> str:
        """
        Get the user's institution

        :return: the institution
        """

    @institution.setter
    @abc.abstractmethod
    def institution(self, val: str) -> None:
        """
        Set the user's institution

        :param val: the new institution
        """


class BackendUserCollection(BackendCollection[BackendUser]):

    ENTITY_CLASS = BackendUser
