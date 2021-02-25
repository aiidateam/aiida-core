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
    _user = None  # type: aiida.orm.User
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
        if orm.autogroup.CURRENT_AUTOGROUP is not None:
            orm.autogroup.CURRENT_AUTOGROUP.clear_group_cache()
        cls.clean_db()
        cls.clean_repository()

    def tearDown(self):
        reset_manager()

    ### Database/repository-related methods

    @classmethod
    def insert_data(cls):
        """
        This method setups the database (by creating a default user) and
        inserts default data into the database (which is for the moment a
        default computer).
        """
        orm.User.objects.reset()  # clear Aiida's cache of the default user
        # populate user cache of test clases
        cls.user  # pylint: disable=pointless-statement

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
        cls._user = None

        if orm.autogroup.CURRENT_AUTOGROUP is not None:
            orm.autogroup.CURRENT_AUTOGROUP.clear_group_cache()

        reset_manager()

    @classmethod
    def refurbish_db(cls):
        """Clean up database and repopulate with initial data.

        Combines clean_db and insert_data.
        """
        cls.clean_db()
        cls.insert_data()

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
    def user(cls):  # pylint: disable=no-self-argument
        if cls._user is None:
            cls._user = get_default_user()
        return cls._user

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


def get_default_user(**kwargs):
    """Creates and stores the default user in the database.

    Default user email is taken from current profile.
    No-op if user already exists.
    The same is done in `verdi setup`.

    :param kwargs: Additional information to use for new user, i.e. 'first_name', 'last_name' or 'institution'.
    :returns: the :py:class:`~aiida.orm.User`
    """
    from aiida.manage.configuration import get_config
    email = get_config().current_profile.default_user

    if kwargs.pop('email', None):
        raise ValueError('Do not specify the user email (must coincide with default user email of profile).')

    # Create the AiiDA user if it does not yet exist
    created, user = orm.User.objects.get_or_create(email=email, **kwargs)
    if created:
        user.store()

    return user
