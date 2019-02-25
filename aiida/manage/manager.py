# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""AiiDA manager for global settings"""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import functools

from .configuration import get_config

__all__ = ('get_manager', 'reset_manager')

MANAGER = None


class Manager(object):  # pylint: disable=useless-object-inheritance
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

    def _load_backend(self, schema_check=True):
        """Load the backend for the currently configured profile and return it.

        :param schema_check: force a database schema check if the database environment has not yet been loaded
        :return: the database backend
        :rtype: :class:`aiida.orm.Backend`
        """
        from aiida.backends.profile import BACKEND_DJANGO, BACKEND_SQLA
        from aiida.backends.utils import is_dbenv_loaded, load_dbenv, _load_dbenv_noschemacheck

        profile = self.get_profile()

        if not is_dbenv_loaded():
            if schema_check:
                load_dbenv(profile.name)
            else:
                _load_dbenv_noschemacheck(profile.name)

        backend_type = profile.dictionary.AIIDADB_BACKEND

        if backend_type == BACKEND_DJANGO:
            from aiida.orm.implementation.django.backend import DjangoBackend
            self._backend = DjangoBackend()
        elif backend_type == BACKEND_SQLA:
            from aiida.orm.implementation.sqlalchemy.backend import SqlaBackend
            self._backend = SqlaBackend()
        else:
            raise RuntimeError('Invalid backend type {} in profile: {}'.format(backend_type, profile.name))

        return self._backend

    def get_backend(self):
        """
        Get the database backend

        :return: the database backend
        :rtype: :class:`aiida.orm.Backend`
        """
        if self._backend is None:
            self._load_backend()

        return self._backend

    def get_profile(self):
        """
        Get the current profile

        :return: current loaded profile instance
        :rtype: :class:`~aiida.manage.configuration.profile.Profile`
        """
        if self._profile is None:
            config = get_config()
            self._profile = config.current_profile

        return self._profile

    def get_persister(self):
        """
        Get the persister

        :return: the current persister instance
        :rtype: :class:`plumpy.Persister`
        """
        from aiida.engine import persistence

        if self._persister is None:
            self._persister = persistence.AiiDAPersister()

        return self._persister

    def get_communicator(self):
        """
        Get the communicator

        :return: a global communicator instance
        :rtype: :class:`kiwipy.Communicator`
        """
        if self._communicator is None:
            self._communicator = self.create_communicator()

        return self._communicator

    def create_communicator(self, task_prefetch_count=None, with_orm=True):
        """
        Create a Communicator

        :param task_prefetch_count: optional specify how many tasks this communicator take simultaneously
        :param with_orm: if True, use ORM (de)serializers. If false, use json.
            This is used by verdi status to get a communicator without needing to load the dbenv.

        :return: the communicator instance
        :rtype: :class:`~kiwipy.rmq.communicator.RmqThreadCommunicator`
        """
        from aiida.manage.external import rmq
        import kiwipy.rmq
        profile = self.get_profile()

        if task_prefetch_count is None:
            task_prefetch_count = rmq._RMQ_TASK_PREFETCH_COUNT  # pylint: disable=protected-access

        url = rmq.get_rmq_url()
        prefix = profile.rmq_prefix

        # This needs to be here, because the verdi commands will call this function and when called in unit tests the
        # testing_mode cannot be set.
        testing_mode = profile.is_test_profile

        message_exchange = rmq.get_message_exchange_name(prefix)
        task_exchange = rmq.get_task_exchange_name(prefix)
        task_queue = rmq.get_launch_queue_name(prefix)

        if with_orm:
            from aiida.orm.utils import serialize
            encoder = functools.partial(serialize.serialize, encoding='utf-8')
            decoder = serialize.deserialize
        else:
            # used by verdi status to get a communicator without needing to load the dbenv
            from aiida.common import json
            encoder = functools.partial(json.dumps, encoding='utf-8')
            decoder = json.loads

        return kiwipy.rmq.RmqThreadCommunicator.connect(
            connection_params={'url': url},
            message_exchange=message_exchange,
            encoder=encoder,
            decoder=decoder,
            task_exchange=task_exchange,
            task_queue=task_queue,
            task_prefetch_count=task_prefetch_count,
            testing_mode=testing_mode,
        )

    def get_daemon_client(self):
        """
        Return the daemon client for the current profile.

        :return: the daemon client
        :rtype: :class:`aiida.daemon.client.DaemonClient`
        :raises aiida.common.MissingConfigurationError: if the configuration file cannot be found
        :raises aiida.common.ProfileConfigurationError: if the given profile does not exist
        """
        from aiida.engine.daemon.client import DaemonClient

        if self._daemon_client is None:
            self._daemon_client = DaemonClient(self.get_profile())

        return self._daemon_client

    def get_process_controller(self):
        """
        Get a process controller

        :return: the process controller instance
        :rtype: :class:`plumpy.RemoteProcessThreadController`
        """
        import plumpy
        if self._process_controller is None:
            self._process_controller = plumpy.RemoteProcessThreadController(self.get_communicator())

        return self._process_controller

    def get_runner(self):
        """
        Get a runner that is based on the current profile settings and can be used globally by the code.

        :return: the global runner
        :rtype: :class:`aiida.engine.runners.Runner`
        """
        if self._runner is None:
            self._runner = self.create_runner()

        return self._runner

    def set_runner(self, new_runner):
        """
        Set the currently used runner

        :param new_runner: the new runner to use
        :type new_runner: :class:`aiida.engine.runners.Runner`
        """
        if self._runner is not None:
            self._runner.close()

        self._runner = new_runner

    def create_runner(self, with_persistence=True, **kwargs):
        """
        Create a new runner

        :param with_persistence: create a runner with persistence enabled
        :type with_persistence: bool
        :return: a new runner instance
        :rtype: :class:`aiida.engine.runners.Runner`
        """
        from aiida.engine import runners

        config = get_config()
        profile = self.get_profile()
        poll_interval = 0.0 if profile.is_test_profile else config.option_get('runner.poll.interval')

        settings = {'rmq_submit': False, 'poll_interval': poll_interval}
        settings.update(kwargs)

        if 'communicator' not in settings:
            # Only call get_communicator if we have to as it will lazily create
            settings['communicator'] = self.get_communicator()

        if with_persistence and 'persister' not in settings:
            settings['persister'] = self.get_persister()

        return runners.Runner(**settings)

    def create_daemon_runner(self, loop=None):
        """
        Create a new daemon runner.  This is used by workers when the daemon is running and in testing.

        :param loop: the (optional) tornado event loop to use
        :type loop: :class:`tornado.ioloop.IOLoop`
        :return: a runner configured to work in the daemon configuration
        :rtype: :class:`aiida.engine.runners.Runner`
        """
        import plumpy
        from aiida.engine import persistence
        from aiida.manage.external import rmq
        runner = self.create_runner(rmq_submit=True, loop=loop)
        runner_loop = runner.loop

        # Listen for incoming launch requests
        task_receiver = rmq.ProcessLauncher(
            loop=runner_loop,
            persister=self.get_persister(),
            load_context=plumpy.LoadSaveContext(runner=runner),
            loader=persistence.get_object_loader())

        def callback(*args, **kwargs):
            return plumpy.create_task(functools.partial(task_receiver, *args, **kwargs), loop=runner_loop)

        runner.communicator.add_task_subscriber(callback)

        return runner

    def close(self):
        """
        Reset the global settings entirely and release any global objects
        """
        if self._communicator is not None:
            self._communicator.stop()
        if self._runner is not None:
            self._runner.stop()

        self._backend = None
        self._config = None
        self._profile = None
        self._communicator = None
        self._daemon_client = None
        self._process_controller = None
        self._persister = None
        self._runner = None

    def __init__(self):
        super(Manager, self).__init__()
        self._backend = None  # type: aiida.orm.Backend
        self._config = None  # type: aiida.manage.configuration.config.Config
        self._daemon_client = None  # type: aiida.daemon.client.DaemonClient
        self._profile = None  # type: aiida.manage.configuration.profile.Profile
        self._communicator = None  # type: kiwipy.rmq.RmqThreadCommunicator
        self._process_controller = None  # type: plumpy.RemoteProcessThreadController
        self._persister = None  # type: aiida.engine.persistence.AiiDAPersister
        self._runner = None  # type: aiida.engine.runners.Runner


def get_manager():
    global MANAGER  # pylint: disable=global-statement
    if MANAGER is None:
        MANAGER = Manager()
    return MANAGER


def reset_manager():
    global MANAGER  # pylint: disable=global-statement
    if MANAGER is not None:
        MANAGER.close()
        MANAGER = None
