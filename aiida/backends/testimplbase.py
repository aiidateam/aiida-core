# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Implementation-dependednt base tests"""
from abc import ABC, abstractmethod

from aiida import orm
from aiida.common import exceptions


class AiidaTestImplementation(ABC):
    """For each implementation, define what to do at setUp and tearDown.

    Each subclass must reimplement two *standard* methods (i.e., *not* classmethods), called
    respectively ``setUpClass_method`` and ``tearDownClass_method``.
    It is also required to implement setUp_method and tearDown_method to be run for each single test
    They can set local properties (e.g. ``self.xxx = yyy``) but remember that ``xxx``
    is not visible to the upper (calling) Test class.

    Moreover, it is required that they define in the setUpClass_method the two properties:

    - ``self.computer`` that must be a Computer object
    - ``self.user_email`` that must be a string

    These two are then exposed by the ``self.get_computer()`` and ``self.get_user_email()``
    methods."""
    # This should be set by the implementing class in setUpClass_method()
    backend = None  # type: aiida.orm.implementation.Backend
    computer = None  # type: aiida.orm.Computer
    user = None  # type: aiida.orm.User
    user_email = None  # type: str

    @abstractmethod
    def setUpClass_method(self):  # pylint: disable=invalid-name
        """This class prepares the database (cleans it up and installs some basic entries).
        You have also to set a self.computer and a self.user_email as explained in the docstring of the
        AiidaTestImplemention docstring."""

    @abstractmethod
    def tearDownClass_method(self):  # pylint: disable=invalid-name
        """Backend-specific tasks for tearing down the test environment."""

    @abstractmethod
    def clean_db(self):
        """This method implements the logic to fully clean the DB."""

    def insert_data(self):
        pass

    def create_user(self):
        """This method creates and stores the default user. It has the same effect
        as the verdi setup."""
        from aiida.manage.configuration import get_config
        self.user_email = get_config().current_profile.default_user

        # Since the default user is needed for many operations in AiiDA, it is not deleted by clean_db.
        # In principle, it should therefore always exist - if not we create it anyhow.
        try:
            self.user = orm.User.objects.get(email=self.user_email)
        except exceptions.NotExistent:
            self.user = orm.User(email=self.user_email).store()

    def create_computer(self):
        """This method creates and stores a computer."""
        self.computer = orm.Computer(
            label='localhost',
            hostname='localhost',
            transport_type='local',
            scheduler_type='direct',
            workdir='/tmp/aiida',
            backend=self.backend
        ).store()

    def get_computer(self):
        """An ORM Computer object present in the DB."""
        try:
            return self.computer
        except AttributeError:
            raise exceptions.InternalError(
                'The AiiDA Test implementation should define a self.computer in the setUpClass_method'
            )

    def get_user_email(self):
        """A string with the email of the User."""
        try:
            return self.user_email
        except AttributeError:
            raise exceptions.InternalError(
                'The AiiDA Test implementation should define a self.user_email in the setUpClass_method'
            )
