# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from aiida.common.exceptions import InternalError
from abc import ABCMeta, abstractmethod


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
    __metaclass__ = ABCMeta

    @abstractmethod
    def setUpClass_method(self):
        """
        This class prepares the database (cleans it up and installs some basic entries).
        You have also to set a self.computer and a self.user_email as explained in the docstring of the
        AiidaTestImplemention docstring.
        """
        pass

    @abstractmethod
    def setUp_method(self):
        pass

    @abstractmethod
    def tearDown_method(self):
        pass

    @abstractmethod
    def tearDownClass_method(self):
        """
        This class implements the tear down methods (e.g. cleans up the DB).
        """
        pass

    @abstractmethod
    def clean_db(self):
        """
        This method implements the logic to fully clean the DB.
        """
        pass

    @abstractmethod
    def insert_data(self):
        """
        This method inserts default data into the database.
        """
        pass

    def get_computer(self):
        """
        A ORM Computer object present in the DB
        """
        try:
            return self.computer
        except AttributeError:
            raise InternalError("The AiiDA Test implementation should define a self.computer in the setUpClass_method")

    def get_user_email(self):
        """
        A string with the email of the User
        """
        try:
            return self.user_email
        except AttributeError:
            raise InternalError("The AiiDA Test implementation should define a self.computer in the setUpClass_method")

