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
import plumpy

from aiida import utils

__all__ = ('AiiDAManager',)


class AiiDAManager(object):
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
      * move construct_backend() from orm.backends inside the AiiDAManager
    """

    _profile = None  # type: aiida.common.profile.Profile
    _communicator = None  # type: kiwipy.rmq.RmqThreadCommunicator
    _process_controller = None  # type: plumpy.RemoteProcessThreadController
    _persister = None  # type: aiida.work.AiiDAPersister
    _runner = None  # type: aiida.work.Runner

    @classmethod
    def get_profile(cls):
        """
        Get the current profile

        :return: current loaded profile instance
        :rtype: :class:`~aiida.common.profile.Profile`
        """
        from aiida.common import profile

        if cls._profile is None:
            cls._profile = profile.get_profile()

        return cls._profile

    @classmethod
    def get_persister(cls):
        """
        Get the persister

        :return: the current persister instance
        :rtype: :class:`plumpy.Persister`
        """
        from aiida.work import persistence

        if cls._persister is None:
            cls._persister = persistence.AiiDAPersister()

        return cls._persister

    @classmethod
    def get_communicator(cls):
        """
        Get the communicator

        :return: a global communicator instance
        :rtype: :class:`kiwipy.Communicator`
        """
        if cls._communicator is None:
            cls._communicator = cls.create_communicator()

        return cls._communicator

    @classmethod
    def create_communicator(cls, task_prefetch_count=None):
        """
        Create a Communicator

        :param task_prefetch_count: optional specify how many tasks this communicator take simultaneously
        :return: the communicator instance
        :rtype: :class:`~kiwipy.rmq.communicator.RmqThreadCommunicator`
        """
        from aiida.work import rmq
        import kiwipy.rmq
        profile = cls.get_profile()

        if task_prefetch_count is None:
            task_prefetch_count = rmq._RMQ_TASK_PREFETCH_COUNT  # pylint: disable=protected-access

        url = rmq.get_rmq_url()
        prefix = rmq.get_rmq_prefix()

        # This needs to be here, because the verdi commands will call this function and when called in unit tests the
        # testing_mode cannot be set.
        testing_mode = profile.is_test_profile

        message_exchange = rmq.get_message_exchange_name(prefix)
        task_exchange = rmq.get_task_exchange_name(prefix)
        task_queue = rmq.get_launch_queue_name(prefix)

        return kiwipy.rmq.RmqThreadCommunicator.connect(
            connection_params={'url': url},
            message_exchange=message_exchange,
            encoder=functools.partial(utils.serialize.serialize, encoding='utf-8'),
            decoder=utils.serialize.deserialize,
            task_exchange=task_exchange,
            task_queue=task_queue,
            task_prefetch_count=task_prefetch_count,
            testing_mode=testing_mode,
        )

    @classmethod
    def get_process_controller(cls):
        """
        Get a process controller

        :return: the process controller instance
        :rtype: :class:`plumpy.RemoteProcessThreadController`
        """
        if cls._process_controller is None:
            cls._process_controller = plumpy.RemoteProcessThreadController(cls.get_communicator())

        return cls._process_controller

    @classmethod
    def get_runner(cls):
        """
        Get a runner that is based on the current profile settings and can be used globally by the code.

        :return: the global runner
        :rtype: :class:`aiida.work.Runner`
        """
        if cls._runner is None:
            cls._runner = cls.create_runner()

        return cls._runner

    @classmethod
    def set_runner(cls, new_runner):
        """
        Set the currently used runner

        :param new_runner: the new runner to use
        :type new_runner: :class:`aiida.work.Runner`
        """
        if cls._runner is not None:
            cls._runner.close()

        cls._runner = new_runner

    @classmethod
    def create_runner(cls, with_persistence=True, **kwargs):
        """
        Create a new runner

        :param with_persistence: create a runner with persistence enabled
        :type with_persistence: bool
        :return: a new runner instance
        :rtype: :class:`aiida.work.Runner`
        """
        from aiida.work import runners

        profile = cls.get_profile()
        poll_interval = 0.0 if profile.is_test_profile else profile.get_option('runner.poll.interval')

        settings = {'rmq_submit': False, 'poll_interval': poll_interval}
        settings.update(kwargs)

        if 'communicator' not in settings:
            # Only call get_communicator if we have to as it will lazily create
            settings['communicator'] = cls.get_communicator()

        if with_persistence and 'persister' not in settings:
            settings['persister'] = cls.get_persister()

        return runners.Runner(**settings)

    @classmethod
    def create_daemon_runner(cls, loop=None):
        """
        Create a new daemon runner.  This is used by workers when the daemon is running and in testing.

        :param loop: the (optional) tornado event loop to use
        :type loop: :class:`tornado.ioloop.IOLoop`
        :return: a runner configured to work in the daemon configuration
        :rtype: :class:`aiida.work.Runner`
        """
        from aiida.work import rmq, persistence
        runner = cls.create_runner(rmq_submit=True, loop=loop)
        runner_loop = runner.loop

        # Listen for incoming launch requests
        task_receiver = rmq.ProcessLauncher(
            loop=runner_loop,
            persister=cls.get_persister(),
            load_context=plumpy.LoadSaveContext(runner=runner),
            loader=persistence.get_object_loader())

        def callback(*args, **kwargs):
            return plumpy.create_task(functools.partial(task_receiver, *args, **kwargs), loop=runner_loop)

        runner.communicator.add_task_subscriber(callback)

        return runner

    @classmethod
    def reset(cls):
        """
        Reset the global settings entirely and release any global objects
        """
        if cls._communicator is not None:
            cls._communicator.stop()
        if cls._runner is not None:
            cls._runner.stop()

        cls._profile = None
        cls._persister = None
        cls._communicator = None
        cls._process_controller = None
        cls._runner = None

    def __init__(self):
        """Can't instantiate this class"""
        raise NotImplementedError("Can't instantiate")
