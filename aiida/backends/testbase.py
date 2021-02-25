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
import os
import unittest
import traceback

from aiida.common.exceptions import ConfigurationError, TestsNotAllowedError, InternalError
from aiida.manage import configuration
from aiida.manage.manager import get_manager, reset_manager
from aiida import orm
from aiida.common.lang import classproperty

TEST_KEYWORD = 'test_'


def check_if_tests_can_run():
    """Verify that the currently loaded profile is a test profile, otherwise raise `TestsNotAllowedError`."""
    profile = configuration.PROFILE
    if not profile.is_test_profile:
        raise TestsNotAllowedError(f'currently loaded profile {profile.name} is not a valid test profile')


class AiidaTestCase(unittest.TestCase):
    """This is the base class for AiiDA tests, independent of the backend.

    Internally it loads the AiidaTestImplementation subclass according to the current backend."""
    _computer = None  # type: aiida.orm.Computer
    _class_was_setup = False
    __backend_instance = None
    backend = None  # type: aiida.orm.implementation.Backend

    @classmethod
    def get_backend_class(cls):
        """Get backend class."""
        from aiida.backends.testimplbase import AiidaTestImplementation
        from aiida.backends import BACKEND_SQLA, BACKEND_DJANGO
        from aiida.manage.configuration import PROFILE

        # Freeze the __impl_class after the first run
        if not hasattr(cls, '__impl_class'):
            if PROFILE.database_backend == BACKEND_SQLA:
                from aiida.backends.sqlalchemy.testbase import SqlAlchemyTests
                cls.__impl_class = SqlAlchemyTests
            elif PROFILE.database_backend == BACKEND_DJANGO:
                from aiida.backends.djsite.db.testbase import DjangoTests
                cls.__impl_class = DjangoTests
            else:
                raise ConfigurationError('Unknown backend type')

            # Check that it is of the right class
            if not issubclass(cls.__impl_class, AiidaTestImplementation):
                raise InternalError(
                    'The AiiDA test implementation is not of type '
                    '{}, that is not a subclass of AiidaTestImplementation'.format(cls.__impl_class.__name__)
                )

        return cls.__impl_class

    @classmethod
    def setUpClass(cls):
        """Set up test class."""
        # Note: this will raise an exception, that will be seen as a test
        # failure. To be safe, you should do the same check also in the tearDownClass
        # to avoid that it is run
        check_if_tests_can_run()

        # Force the loading of the backend which will load the required database environment
        cls.backend = get_manager().get_backend()
        cls.__backend_instance = cls.get_backend_class()()
        cls._class_was_setup = True

        cls.refurbish_db()

    @classmethod
    def tearDownClass(cls):
        """Tear down test class.

        Note: Also cleans file repository.
        """
        # Double check for double security to avoid to run the tearDown
        # if this is not a test profile

        check_if_tests_can_run()
        cls.clean_db()
        cls.clean_repository()

    def tearDown(self):
        reset_manager()

    ### Database/repository-related methods

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

        cls.__backend_instance.clean_db()
        cls._computer = None

        orm.User.objects.reset()  # clear Aiida's cache of the default user

        if orm.autogroup.CURRENT_AUTOGROUP is not None:
            orm.autogroup.CURRENT_AUTOGROUP.clear_group_cache()

        reset_manager()

    @classmethod
    def refurbish_db(cls):
        """Clean up database and create default user.

        Combines clean_db and database initialization.
        """
        cls.clean_db()
        created, user = orm.User.objects.get_or_create_default()  # create default user
        if created:
            user.store()

    @classmethod
    def clean_repository(cls):
        """
        Cleans up file repository.
        """
        from aiida.manage.configuration import get_profile
        from aiida.common.exceptions import InvalidOperation
        import shutil

        dirpath_repository = get_profile().repository_path

        base_repo_path = os.path.basename(os.path.normpath(dirpath_repository))
        if TEST_KEYWORD not in base_repo_path:
            raise InvalidOperation(
                'Warning: The repository folder {} does not '
                'seem to belong to a test profile and will therefore not be deleted.\n'
                'Full repository path: '
                '{}'.format(base_repo_path, dirpath_repository)
            )

        # Clean the test repository
        shutil.rmtree(dirpath_repository, ignore_errors=True)
        os.makedirs(dirpath_repository)

    @classproperty
    def computer(cls):  # pylint: disable=no-self-argument
        """Get the default computer for this test

        :return: the test computer
        :rtype: :class:`aiida.orm.Computer`"""
        if cls._computer is None:
            created, computer = orm.Computer.objects.get_or_create(
                label='localhost',
                hostname='localhost',
                transport_type='local',
                scheduler_type='direct',
                workdir='/tmp/aiida',
            )
            if created:
                computer.store()
            cls._computer = computer

        return cls._computer

    @classproperty
    def user(cls):  # pylint: disable=no-self-argument,no-self-use
        """Return default user.

        Since the default user is already cached at the orm level, we just return it.
        """
        return orm.User.objects.get_default()

    @classproperty
    def user_email(cls):  # pylint: disable=no-self-argument
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
