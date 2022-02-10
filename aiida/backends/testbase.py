# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Basic test classes."""
import traceback
from typing import Optional
import unittest

from aiida import orm
from aiida.common.exceptions import TestsNotAllowedError
from aiida.common.lang import classproperty
from aiida.manage import configuration, get_manager
from aiida.orm.implementation import Backend

TEST_KEYWORD = 'test_'


def check_if_tests_can_run():
    """Verify that the currently loaded profile is a test profile, otherwise raise `TestsNotAllowedError`."""
    profile = configuration.get_profile()
    if not profile:
        raise TestsNotAllowedError('No profile is loaded.')
    if not profile.is_test_profile:
        raise TestsNotAllowedError(f'currently loaded profile {profile.name} is not a valid test profile')


class AiidaTestCase(unittest.TestCase):
    """This is the base class for AiiDA tests, independent of the backend."""
    _class_was_setup = False
    backend: Optional[Backend] = None

    @classmethod
    def setUpClass(cls):
        """Set up test class."""
        # Note: this will raise an exception, that will be seen as a test
        # failure. To be safe, you should do the same check also in the tearDownClass
        # to avoid that it is run
        check_if_tests_can_run()

        # Force the loading of the backend which will load the required database environment
        cls._class_was_setup = True
        cls.clean_db()
        cls.backend = get_manager().get_profile_storage()

    @classmethod
    def tearDownClass(cls):
        """Tear down test class, by clearing all backend storage."""
        # Double check for double security to avoid to run the tearDown
        # if this is not a test profile

        check_if_tests_can_run()
        cls.clean_db()

    def tearDown(self):
        manager = get_manager()
        # this should really call reset profile, but that also resets the storage backend
        # and causes issues for some existing tests that set class level entities
        # manager.reset_profile()
        # pylint: disable=protected-access
        if manager._communicator is not None:
            manager._communicator.close()
        if manager._runner is not None:
            manager._runner.stop()
        manager._communicator = None
        manager._runner = None
        manager._daemon_client = None
        manager._process_controller = None
        manager._persister = None

    ### storage methods

    @classmethod
    def clean_db(cls):
        """Clean up database and reset caches.

        Resets AiiDA manager cache, which could otherwise be left in an inconsistent state when cleaning the database.
        """
        from aiida.common.exceptions import InvalidOperation

        # Note: this will raise an exception, that will be seen as a test
        # failure. To be safe, you should do the same check also in the tearDownClass
        # to avoid that it is run
        check_if_tests_can_run()

        if not cls._class_was_setup:
            raise InvalidOperation('You cannot call clean_db before running the setUpClass')

        manager = get_manager()
        manager.get_profile_storage()._clear(recreate_user=True)  # pylint: disable=protected-access
        manager.reset_profile()

    @classmethod
    def refurbish_db(cls):
        """Clean up database and repopulate with initial data."""
        cls.clean_db()

    @classproperty
    def computer(cls) -> orm.Computer:  # pylint: disable=no-self-argument
        """Get the default computer for this test

        :return: the test computer
        """
        created, computer = orm.Computer.objects.get_or_create(
            label='localhost',
            hostname='localhost',
            transport_type='core.local',
            scheduler_type='core.direct',
            workdir='/tmp/aiida',
        )
        if created:
            computer.store()
        return computer

    @classproperty
    def user(cls) -> orm.User:  # pylint: disable=no-self-argument
        return get_default_user()

    @classproperty
    def user_email(cls) -> str:  # pylint: disable=no-self-argument
        return cls.user.email  # pylint: disable=no-member

    ### Usability methods

    def assertClickSuccess(self, cli_result):  # pylint: disable=invalid-name
        self.assertEqual(cli_result.exit_code, 0, cli_result.output)
        self.assertClickResultNoException(cli_result)

    def assertClickResultNoException(self, cli_result):  # pylint: disable=invalid-name
        self.assertIsNone(cli_result.exception, ''.join(traceback.format_exception(*cli_result.exc_info)))


class AiidaPostgresTestCase(AiidaTestCase):
    """Setup postgres tests."""

    @classmethod
    def setUpClass(cls, *args, **kwargs):
        """Setup the PGTest postgres test cluster."""
        from pgtest.pgtest import PGTest
        cls.pg_test = PGTest()
        super().setUpClass(*args, **kwargs)

    @classmethod
    def tearDownClass(cls, *args, **kwargs):
        """Close the PGTest postgres test cluster."""
        super().tearDownClass(*args, **kwargs)
        cls.pg_test.close()


def get_default_user(**kwargs):
    """Creates and stores the default user in the database.

    Default user email is taken from current profile.
    No-op if user already exists.
    The same is done in `verdi setup`.

    :param kwargs: Additional information to use for new user, i.e. 'first_name', 'last_name' or 'institution'.
    :returns: the :py:class:`~aiida.orm.User`
    """
    email = configuration.get_profile().default_user_email

    if kwargs.pop('email', None):
        raise ValueError('Do not specify the user email (must coincide with default user email of profile).')

    # Create the AiiDA user if it does not yet exist
    created, user = orm.User.objects.get_or_create(email=email, **kwargs)
    if created:
        user.store()

    return user
