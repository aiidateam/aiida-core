# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=cyclic-import
"""AiiDA manager for global settings"""
import asyncio
import functools
from typing import Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from kiwipy.rmq import RmqThreadCommunicator
    from plumpy.process_comms import RemoteProcessThreadController

    from aiida.backends.manager import BackendManager
    from aiida.engine.daemon.client import DaemonClient
    from aiida.engine.runners import Runner
    from aiida.manage.configuration.config import Config
    from aiida.manage.configuration.profile import Profile
    from aiida.orm.implementation import Backend
    from aiida.engine.persistence import AiiDAPersister

__all__ = ('get_manager', 'reset_manager')


class Manager:
    """
    Manager singleton to provide global versions of commonly used profile/settings related objects
    and methods to facilitate their construction.

    In AiiDA the settings of many objects are tied to options defined in the current profile.  This
    means that certain objects should be constructed in a way that depends on the profile.  Instead of
    having disparate parts of the code accessing the profile we put together here the profile and methods
    to create objects based on the current settings.

    It is also a useful place to put objects where there can be a single 'global' (per profile) instance.

    Future plans:
      * reset manager cache when loading a new profile
    """

    def __init__(self) -> None:
        self._backend: Optional['Backend'] = None
        self._backend_manager: Optional['BackendManager'] = None
        self._config: Optional['Config'] = None
        self._daemon_client: Optional['DaemonClient'] = None
        self._profile: Optional['Profile'] = None
        self._communicator: Optional['RmqThreadCommunicator'] = None
        self._process_controller: Optional['RemoteProcessThreadController'] = None
        self._persister: Optional['AiiDAPersister'] = None
        self._runner: Optional['Runner'] = None

    def close(self) -> None:
        """Reset the global settings entirely and release any global objects."""
        if self._communicator is not None:
            self._communicator.close()
        if self._runner is not None:
            self._runner.stop()

        self._backend = None
        self._backend_manager = None
        self._config = None
        self._profile = None
        self._communicator = None
        self._daemon_client = None
        self._process_controller = None
        self._persister = None
        self._runner = None

    @staticmethod
    def get_config() -> 'Config':
        """Return the current config.

        :return: current loaded config instance
        :raises aiida.common.ConfigurationError: if the configuration file could not be found, read or deserialized

        """
        from .configuration import get_config
        return get_config()

    @staticmethod
    def get_profile() -> Optional['Profile']:
        """Return the current loaded profile, if any

        :return: current loaded profile instance

        """
        from .configuration import get_profile
        return get_profile()

    def unload_backend(self) -> None:
        """Unload the current backend and its corresponding database environment."""
        manager = self.get_backend_manager()
        manager.reset_backend_environment()
        self._backend = None

    def _load_backend(self, schema_check: bool = True) -> 'Backend':
        """Load the backend for the currently configured profile and return it.

        .. note:: this will reconstruct the `Backend` instance in `self._backend` so the preferred method to load the
            backend is to call `get_backend` which will create it only when not yet instantiated.

        :param schema_check: force a database schema check if the database environment has not yet been loaded
        :return: the database backend

        """
        from aiida.backends import BACKEND_DJANGO, BACKEND_SQLA
        from aiida.common import ConfigurationError, InvalidOperation
        from aiida.common.log import configure_logging
        from aiida.manage import configuration

        profile = self.get_profile()

        if profile is None:
            raise ConfigurationError(
                'Could not determine the current profile. Consider loading a profile using `aiida.load_profile()`.'
            )

        if configuration.BACKEND_UUID is not None and configuration.BACKEND_UUID != profile.uuid:
            raise InvalidOperation('cannot load backend because backend of another profile is already loaded')

        # Do NOT reload the backend environment if already loaded, simply reload the backend instance after
        if configuration.BACKEND_UUID is None:
            from aiida.backends import get_backend_manager
            backend_manager = get_backend_manager(profile.database_backend)
            backend_manager.load_backend_environment(profile, validate_schema=schema_check)
            configuration.BACKEND_UUID = profile.uuid

        backend_type = profile.database_backend

        # Can only import the backend classes after the backend has been loaded
        if backend_type == BACKEND_DJANGO:
            from aiida.orm.implementation.django.backend import DjangoBackend
            self._backend = DjangoBackend()
        elif backend_type == BACKEND_SQLA:
            from aiida.orm.implementation.sqlalchemy.backend import SqlaBackend
            self._backend = SqlaBackend()

        # Reconfigure the logging with `with_orm=True` to make sure that profile specific logging configuration options
        # are taken into account and the `DbLogHandler` is configured.
        configure_logging(with_orm=True)

        return self._backend

    @property
    def backend_loaded(self) -> bool:
        """Return whether a database backend has been loaded.

        :return: boolean, True if database backend is currently loaded, False otherwise
        """
        return self._backend is not None

    def get_backend_manager(self) -> 'BackendManager':
        """Return the database backend manager.

        .. note:: this is not the actual backend, but a manager class that is necessary for database operations that
            go around the actual ORM. For example when the schema version has not yet been validated.

        :return: the database backend manager

        """
        from aiida.backends import get_backend_manager
        from aiida.common import ConfigurationError

        if self._backend_manager is None:
            self._load_backend()
            profile = self.get_profile()
            if profile is None:
                raise ConfigurationError(
                    'Could not determine the current profile. Consider loading a profile using `aiida.load_profile()`.'
                )
            self._backend_manager = get_backend_manager(profile.database_backend)

        return self._backend_manager

    def get_backend(self) -> 'Backend':
        """Return the database backend

        :return: the database backend

        """
        if self._backend is None:
            self._load_backend()

        return self._backend

    def get_persister(self) -> 'AiiDAPersister':
        """Return the persister

        :return: the current persister instance

        """
        from aiida.engine import persistence

        if self._persister is None:
            self._persister = persistence.AiiDAPersister()

        return self._persister

    def get_communicator(self) -> 'RmqThreadCommunicator':
        """Return the communicator

        :return: a global communicator instance

        """
        if self._communicator is None:
            self._communicator = self.create_communicator()

        return self._communicator

    def create_communicator(
        self, task_prefetch_count: Optional[int] = None, with_orm: bool = True
    ) -> 'RmqThreadCommunicator':
        """Create a Communicator.

        :param task_prefetch_count: optional specify how many tasks this communicator take simultaneously
        :param with_orm: if True, use ORM (de)serializers. If false, use json.
            This is used by verdi status to get a communicator without needing to load the dbenv.

        :return: the communicator instance

        """
        from aiida.common import ConfigurationError
        from aiida.manage.external import rmq
        import kiwipy.rmq

        profile = self.get_profile()
        if profile is None:
            raise ConfigurationError(
                'Could not determine the current profile. Consider loading a profile using `aiida.load_profile()`.'
            )

        if task_prefetch_count is None:
            task_prefetch_count = self.get_config().get_option('daemon.worker_process_slots', profile.name)

        prefix = profile.rmq_prefix

        if with_orm:
            from aiida.orm.utils import serialize
            encoder = functools.partial(serialize.serialize, encoding='utf-8')
            decoder = serialize.deserialize_unsafe
        else:
            # used by verdi status to get a communicator without needing to load the dbenv
            from aiida.common import json
            encoder = functools.partial(json.dumps, encoding='utf-8')
            decoder = json.loads

        return kiwipy.rmq.RmqThreadCommunicator.connect(
            connection_params={'url': profile.get_rmq_url()},
            message_exchange=rmq.get_message_exchange_name(prefix),
            encoder=encoder,
            decoder=decoder,
            task_exchange=rmq.get_task_exchange_name(prefix),
            task_queue=rmq.get_launch_queue_name(prefix),
            task_prefetch_count=task_prefetch_count,
            async_task_timeout=self.get_config().get_option('rmq.task_timeout', profile.name),
            # This is needed because the verdi commands will call this function and when called in unit tests the
            # testing_mode cannot be set.
            testing_mode=profile.is_test_profile,
        )

    def get_daemon_client(self) -> 'DaemonClient':
        """Return the daemon client for the current profile.

        :return: the daemon client

        :raises aiida.common.MissingConfigurationError: if the configuration file cannot be found
        :raises aiida.common.ProfileConfigurationError: if the given profile does not exist
        """
        from aiida.engine.daemon.client import DaemonClient

        if self._daemon_client is None:
            self._daemon_client = DaemonClient(self.get_profile())

        return self._daemon_client

    def get_process_controller(self) -> 'RemoteProcessThreadController':
        """Return the process controller

        :return: the process controller instance

        """
        from plumpy.process_comms import RemoteProcessThreadController
        if self._process_controller is None:
            self._process_controller = RemoteProcessThreadController(self.get_communicator())

        return self._process_controller

    def get_runner(self, **kwargs) -> 'Runner':
        """Return a runner that is based on the current profile settings and can be used globally by the code.

        :return: the global runner

        """
        if self._runner is None:
            self._runner = self.create_runner(**kwargs)

        return self._runner

    def set_runner(self, new_runner: 'Runner') -> None:
        """Set the currently used runner

        :param new_runner: the new runner to use

        """
        if self._runner is not None:
            self._runner.close()

        self._runner = new_runner

    def create_runner(self, with_persistence: bool = True, **kwargs: Any) -> 'Runner':
        """Create and return a new runner

        :param with_persistence: create a runner with persistence enabled

        :return: a new runner instance

        """
        from aiida.common import ConfigurationError
        from aiida.engine import runners

        config = self.get_config()
        profile = self.get_profile()
        if profile is None:
            raise ConfigurationError(
                'Could not determine the current profile. Consider loading a profile using `aiida.load_profile()`.'
            )
        poll_interval = 0.0 if profile.is_test_profile else config.get_option('runner.poll.interval', profile.name)

        settings = {'rmq_submit': False, 'poll_interval': poll_interval}
        settings.update(kwargs)

        if 'communicator' not in settings:
            # Only call get_communicator if we have to as it will lazily create
            settings['communicator'] = self.get_communicator()

        if with_persistence and 'persister' not in settings:
            settings['persister'] = self.get_persister()

        return runners.Runner(**settings)

    def create_daemon_runner(self, loop: Optional[asyncio.AbstractEventLoop] = None) -> 'Runner':
        """Create and return a new daemon runner.

        This is used by workers when the daemon is running and in testing.

        :param loop: the (optional) asyncio event loop to use

        :return: a runner configured to work in the daemon configuration

        """
        from plumpy.persistence import LoadSaveContext
        from aiida.engine import persistence
        from aiida.manage.external import rmq

        runner = self.create_runner(rmq_submit=True, loop=loop)
        runner_loop = runner.loop

        # Listen for incoming launch requests
        task_receiver = rmq.ProcessLauncher(
            loop=runner_loop,
            persister=self.get_persister(),
            load_context=LoadSaveContext(runner=runner),
            loader=persistence.get_object_loader()
        )

        assert runner.communicator is not None, 'communicator not set for runner'
        runner.communicator.add_task_subscriber(task_receiver)

        return runner


MANAGER: Optional[Manager] = None


def get_manager() -> Manager:
    global MANAGER  # pylint: disable=global-statement
    if MANAGER is None:
        MANAGER = Manager()
    return MANAGER


def reset_manager() -> None:
    global MANAGER  # pylint: disable=global-statement
    if MANAGER is not None:
        MANAGER.close()
        MANAGER = None
