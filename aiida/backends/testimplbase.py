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
from abc import ABCMeta, abstractmethod

import six

from aiida import orm
from aiida.common import exceptions


@six.add_metaclass(ABCMeta)
class AiidaTestImplementation(object):
    """
    For each implementation, define what to do at setUp and tearDown.

    Each subclass must reimplement two *standard* methods (i.e., *not* classmethods), called
    respectively ``setUpClass_method`` and ``tearDownClass_method``.
    It is also required to implement setUp_method and tearDown_method to be run for each single test
    They can set local properties (e.g. ``self.xxx = yyy``) but remember that ``xxx``
    is not visible to the upper (calling) Test class.

    Moreover, it is required that they define in the setUpClass_method the two properties:

    - ``self.computer`` that must be a Computer object
    - ``self.user_email`` that must be a string

    These two are then exposed by the ``self.get_computer()`` and ``self.get_user_email()``
    methods.
    """

    # This should be set by the implementing class in setUpClass_method()
    backend = None  # type: aiida.orm.Backend
    computer = None  # type: aiida.orm.Computer
    user = None  # type: aiida.orm.User
    user_email = None  # type: str

    @abstractmethod
    def setUpClass_method(self):
        """
        This class prepares the database (cleans it up and installs some basic entries).
        You have also to set a self.computer and a self.user_email as explained in the docstring of the
        AiidaTestImplemention docstring.
        """

    def setUp_method(self):
        pass

    def tearDown_method(self):
        pass

    @abstractmethod
    def tearDownClass_method(self):
        """
        Backend-specific tasks for tearing down the test environment.
        """

    @abstractmethod
    def clean_db(self):
        """
        This method implements the logic to fully clean the DB.
        """

    def insert_data(self):
        """
        This method inserts default data into the database.
        """
        from aiida.manage.configuration import get_config

        self.computer = orm.Computer(
            name='localhost',
            hostname='localhost',
            transport_type='local',
            scheduler_type='pbspro',
            workdir='/tmp/aiida',
            backend=self.backend
        ).store()

        self.user_email = get_config().current_profile.default_user_email

        # Since the default user is needed for many operations in AiiDA, it is not deleted by clean_db.
        # In principle, it should therefore always exist - if not we create it anyhow.
        try:
            self.user = orm.User.objects.get(email=self.user_email)
        except exceptions.NotExistent:
            self.user = orm.User(email=self.user_email).store()

    def get_computer(self):
        """
        A ORM Computer object present in the DB
        """
        try:
            return self.computer
        except AttributeError:
            raise exceptions.InternalError(
                "The AiiDA Test implementation should define a self.computer in the setUpClass_method")

    def get_user_email(self):
        """
        A string with the email of the User
        """
        try:
            return self.user_email
        except AttributeError:
            raise exceptions.InternalError(
                "The AiiDA Test implementation should define a self.user_email in the setUpClass_method")
