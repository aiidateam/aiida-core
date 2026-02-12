###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""AiiDA manager for global settings"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional, Union

if TYPE_CHECKING:
    import asyncio

    from kiwipy.rmq import RmqThreadCommunicator
    from plumpy.process_comms import RemoteProcessThreadController

    from aiida.brokers.broker import Broker
    from aiida.engine.daemon.client import DaemonClient
    from aiida.engine.persistence import AiiDAPersister
    from aiida.engine.runners import Runner
    from aiida.manage.configuration.config import Config
    from aiida.manage.configuration.profile import Profile
    from aiida.orm.implementation import StorageBackend

__all__ = ('get_manager',)

MANAGER: Optional['Manager'] = None


def get_manager() -> 'Manager':
    """Return the AiiDA global manager instance."""
    global MANAGER  # noqa: PLW0603
    if MANAGER is None:
        MANAGER = Manager()
    return MANAGER


class Manager:
    """Manager singleton for globally loaded resources.

    AiiDA can have the following global resources loaded:

    1. A single configuration object that contains:

        - Global options overrides
        - The name of a default profile
        - A mapping of profile names to their configuration and option overrides

    2. A single profile object that contains:

        - The name of the profile
        - The UUID of the profile
        - The configuration of the profile, for connecting to storage and processing resources
        - The option overrides for the profile

    3. A single storage backend object for the profile, to connect to data storage resources
    5. A single daemon client object for the profile, to connect to the AiiDA daemon
    4. A single communicator object for the profile, to connect to the process control resources
    6. A single process controller object for the profile, which uses the communicator to control process tasks
    7. A single runner object for the profile, which uses the process controller to start and stop processes
    8. A single persister object for the profile, which can persist running processes to the profile storage

    """

    def __init__(self) -> None:
        """Construct a new instance."""
        from aiida.common.log import AIIDA_LOGGER

        # note: the config currently references the global variables
        self._broker: Optional['Broker'] = None
        self._profile: Optional['Profile'] = None
        self._profile_storage: Optional['StorageBackend'] = None
        self._daemon_client: Optional['DaemonClient'] = None
        self._process_controller: Optional['RemoteProcessThreadController'] = None
        self._persister: Optional['AiiDAPersister'] = None
        self._runner: Optional['Runner'] = None
        self.logger = AIIDA_LOGGER.getChild(__name__)

    @staticmethod
    def get_config(create=False) -> 'Config':
        """Return the current config.

        :return: current loaded config instance
        :raises aiida.common.ConfigurationError: if the configuration file could not be found, read or deserialized

        """
        from .configuration import get_config

        return get_config(create=create)

    def get_profile(self) -> Optional['Profile']:
        """Return the current loaded profile, if any

        :return: current loaded profile instance
        """
        return self._profile

    def load_profile(self, profile: Union[None, str, 'Profile'] = None, allow_switch=False) -> 'Profile':
        """Load a global profile, unloading any previously loaded profile.

        .. note:: If a profile is already loaded and no explicit profile is specified, nothing will be done.

        :param profile: the name of the profile to load, by default will use the one marked as default in the config
        :param allow_switch: if True, will allow switching to a different profile when storage is already loaded

        :return: the loaded `Profile` instance
        :raises `aiida.common.exceptions.InvalidOperation`:
            if another profile has already been loaded and allow_switch is False
        """
        from aiida.common.exceptions import InvalidOperation
        from aiida.common.log import configure_logging
        from aiida.manage.configuration.profile import Profile

        # If a profile is already loaded and no explicit profile is specified, we do nothing
        if profile is None and self._profile:
            return self._profile

        if profile is None or isinstance(profile, str):
            profile = self.get_config().get_profile(profile)
        elif not isinstance(profile, Profile):
            raise TypeError(f'profile must be None, a string, or a Profile instance, got: {type(profile)}')

        # If a profile is loaded and the specified profile UUID is that of the currently loaded, do nothing
        if self._profile and (self._profile.uuid == profile.uuid):
            return self._profile

        if self._profile and self.profile_storage_loaded and not allow_switch:
            raise InvalidOperation(
                f'cannot switch to profile {profile.name!r} because profile {self._profile.name!r} storage '
                'is already loaded and allow_switch is False'
            )

        self.unload_profile()
        self._profile = profile

        # Reconfigure the logging to make sure that profile specific logging config options are taken into account.
        # Note that we do not configure with `with_orm=True` because that will force the backend to be loaded.
        # This should instead be done lazily in `Manager.get_profile_storage`.
        configure_logging()

        # Check whether a development version is being run. Note that needs to be called after ``configure_logging``
        # because this function relies on the logging being properly configured for the warning to show.
        self.check_version()
        self._install_greenback_portal()

        return self._profile

    def _install_greenback_portal(self) -> None:
        """Register an IPython input transformer that ensures a greenback portal.

        When running inside an environment with an already-running event loop
        (e.g. a Jupyter notebook kernel), this registers an IPython input
        transformer that prepends ``await greenback.ensure_portal()`` to
        every cell.  This activates a greenback portal on whichever asyncio
        task ipykernel uses for that cell.

        The transformer is registered during ``load_profile()`` and takes
        effect from the **next cell**.  ``load_profile()`` must therefore be
        called in a prior cell before synchronous process execution.

        Expected Trade-off: error tracebacks show line numbers offset by 1 due to the
        prepended line.

        This is a no-op if no event loop is running (scripts, CLI, daemon).
        """
        import asyncio

        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return  # No running loop — not in Jupyter, nothing to do

        self._register_portal_transformer()

    def _register_portal_transformer(self) -> None:
        """Register an IPython input transformer that ensures a greenback portal."""
        try:
            from IPython import get_ipython  # type: ignore[attr-defined]

            ip = get_ipython()
            if ip is None:
                return

            # Only patch inside a real Jupyter kernel (ZMQInteractiveShell),
            # not plain terminal IPython.
            if 'zmq' not in type(ip).__module__:
                return

            if getattr(ip, '_aiida_portal_transformer', False):
                return  # Already registered

            def _ensure_portal_transformer(lines):
                return ["await __import__('greenback').ensure_portal()  # aiida: activate greenback portal\n"] + lines

            ip.input_transformers_post.append(_ensure_portal_transformer)
            ip._aiida_portal_transformer = True
            self.logger.debug(
                'Registered IPython transformer for greenback portal. '
                'This should occur in a Jupyter kernel, and only once per kernel session.'
            )
            print(
                'Warning: Synchronous process execution is available only from the next cell. '
                'All aiida engine methods is only availabe from the next cell.'
            )
        except Exception:
            self.logger.debug('Could not register IPython portal transformer.', exc_info=True)

    def reset_profile(self) -> None:
        """Close and reset any associated resources for the current profile."""
        self.reset_broker()
        self.reset_profile_storage()
        self.reset_runner()

        self._daemon_client = None
        self._persister = None

    def reset_profile_storage(self) -> None:
        """Reset the profile storage.

        This will close any connections to the services used by the storage, such as database connections.
        """
        if self._profile_storage is not None:
            self._profile_storage.close()
        self._profile_storage = None

    def reset_broker(self) -> None:
        """Reset the communicator."""
        from concurrent import futures

        if self._broker is not None:
            try:
                self._broker.close()
            except futures.TimeoutError as exception:
                self.logger.warning(f'Call to close the broker timed out: {exception}')
            self._broker.close()

        self._broker = None
        self._process_controller = None

    def reset_runner(self) -> None:
        """Reset the process runner."""
        if self._runner is not None:
            self._runner.close()
        self._runner = None

    def unload_profile(self) -> None:
        """Unload the current profile, closing any associated resources."""
        self.reset_profile()
        self._profile = None

    def set_default_user_email(self, profile: 'Profile', user_email: str) -> None:
        """Set the default user for the given profile.

        :param profile: The profile to update.
        :param user_email: The email of the user to set as the default user.
        """
        self.get_config().set_default_user_email(profile, user_email)
        if self.profile_storage_loaded:
            self.get_profile_storage().reset_default_user()

    @property
    def profile_storage_loaded(self) -> bool:
        """Return whether a storage backend has been loaded.

        :return: boolean, True if database backend is currently loaded, False otherwise
        """
        return self._profile_storage is not None

    def get_option(self, option_name: str) -> Any:
        """Return the value of a configuration option.

        In order of priority, the option is returned from:

        1. The current profile, if loaded and the option specified
        2. The current configuration, if loaded and the option specified
        3. The default value for the option

        :param option_name: the name of the option to return
        :return: the value of the option
        :raises `aiida.common.exceptions.ConfigurationError`: if the option is not found
        """
        from aiida.common.exceptions import ConfigurationError
        from aiida.manage.configuration.options import get_option

        # try the profile
        if self._profile and option_name in self._profile.options:
            return self._profile.get_option(option_name)
        # try the config
        try:
            config = self.get_config(create=True)
        except ConfigurationError:
            pass
        else:
            if option_name in config.options:
                return config.get_option(option_name)

        # try the defaults (will raise ConfigurationError if not present)
        option = get_option(option_name)
        return option.default

    def get_backend(self) -> 'StorageBackend':
        """Return the current profile's storage backend, loading it if necessary.

        Deprecated: use `get_profile_storage` instead.
        """
        from aiida.common.warnings import warn_deprecation

        warn_deprecation('get_backend() is deprecated, use get_profile_storage() instead', version=3, stacklevel=3)
        return self.get_profile_storage()

    def get_profile_storage(self) -> 'StorageBackend':
        """Return the current profile's storage backend, loading it if necessary."""
        from aiida.common import ConfigurationError
        from aiida.common.log import configure_logging
        from aiida.manage.profile_access import ProfileAccessManager

        # if loaded, return the current storage backend (which is "synced" with the global profile)
        if self._profile_storage is not None:
            return self._profile_storage

        # get the currently loaded profile
        profile = self.get_profile()
        if profile is None:
            raise ConfigurationError(
                'Could not determine the current profile. Consider loading a profile using `aiida.load_profile()`.'
            )

        # request access to the profile (for example, if it is being used by a maintenance operation)
        ProfileAccessManager(profile).request_access()

        # retrieve the storage backend to use for the current profile
        storage_cls = profile.storage_cls

        # now we can actually instatiate the backend and set the global variable, note:
        # if the storage is not reachable, this will raise an exception
        # if the storage schema is not at the latest version, this will except and the user will be informed to migrate
        self._profile_storage = storage_cls(profile)

        # Reconfigure the logging with `with_orm=True` to make sure that profile specific logging configuration options
        # are taken into account and the `DbLogHandler` is configured.
        configure_logging(with_orm=True)

        return self._profile_storage

    def get_broker(self) -> 'Broker' | None:
        """Return an instance of :class:`aiida.brokers.broker.Broker` if the profile defines a broker.

        :returns: The broker of the profile, or ``None`` if the profile doesn't define one.
        """
        from aiida.common import ConfigurationError

        if self._profile is None:
            raise ConfigurationError(
                'Could not determine the current profile. Consider loading a profile using `aiida.load_profile()`.'
            )

        if self._broker is None and self._profile.process_control_backend is not None:
            from aiida.plugins import BrokerFactory

            entry_point = self._profile.process_control_backend

            # Backwards compatibility. Before adding broker entry points, profiles used to define ``rabbitmq``.
            if entry_point == 'rabbitmq':
                entry_point = 'core.rabbitmq'

            broker_cls = BrokerFactory(entry_point)
            self._broker = broker_cls(self._profile)

        return self._broker

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
        from aiida.common import ConfigurationError

        broker = self.get_broker()

        if broker is None:
            assert self._profile is not None
            raise ConfigurationError(
                f'profile `{self._profile.name}` does not provide a communicator because it does not define a broker'
            )

        return broker.get_communicator()

    def get_daemon_client(self) -> 'DaemonClient':
        """Return the daemon client for the current profile.

        :return: the daemon client

        :raises aiida.common.MissingConfigurationError: if the configuration file cannot be found
        :raises aiida.common.ProfileConfigurationError: if the given profile does not exist
        """
        from aiida.common import ConfigurationError
        from aiida.engine.daemon.client import DaemonClient

        if self._daemon_client is None:
            profile = self.get_profile()
            if profile is None:
                raise ConfigurationError(
                    'Could not determine the current profile. Consider loading a profile using `aiida.load_profile()`.'
                )
            self._daemon_client = DaemonClient(profile)

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

        profile = self.get_profile()
        if profile is None:
            raise ConfigurationError(
                'Could not determine the current profile. Consider loading a profile using `aiida.load_profile()`.'
            )
        poll_interval = 0.0 if profile.is_test_profile else self.get_option('runner.poll.interval')

        settings = {'broker_submit': False, 'poll_interval': poll_interval}
        settings.update(kwargs)

        if 'communicator' not in settings:
            # Only call get_communicator if we have to as it will lazily create
            try:
                settings['communicator'] = self.get_communicator()
            except ConfigurationError:
                # The currently loaded profile does not define a broker and so there is no communicator
                pass

        if with_persistence and 'persister' not in settings:
            settings['persister'] = self.get_persister()

        return runners.Runner(**settings)  # type: ignore[arg-type]

    def create_daemon_runner(self, loop: Optional['asyncio.AbstractEventLoop'] = None) -> 'Runner':
        """Create and return a new daemon runner.

        This is used by workers when the daemon is running and in testing.

        :param loop: the (optional) asyncio event loop to use

        :return: a runner configured to work in the daemon configuration

        """
        from plumpy.persistence import LoadSaveContext

        from aiida.engine import persistence
        from aiida.engine.processes.launcher import ProcessLauncher

        runner = self.create_runner(broker_submit=True, loop=loop)
        runner_loop = runner.loop

        # Listen for incoming launch requests
        task_receiver = ProcessLauncher(
            loop=runner_loop,
            persister=self.get_persister(),
            load_context=LoadSaveContext(runner=runner),
            loader=persistence.get_object_loader(),
        )

        assert runner.communicator is not None, 'communicator not set for runner'
        runner.communicator.add_task_subscriber(task_receiver)

        return runner

    def check_version(self):
        """Check the currently installed version of ``aiida-core`` and warn if it is a post release development version.

        The ``aiida-core`` package maintains the protocol that the ``main`` branch will use a post release version
        number. This means it will always append `.post0` to the version of the latest release. This should mean that if
        this protocol is maintained properly, this method will print a warning if the currently installed version is a
        post release development branch and not an actual release.
        """
        from packaging.version import parse

        from aiida import __version__
        from aiida.cmdline.utils import echo

        # Showing of the warning can be turned off by setting the following option to false.
        assert self._profile is not None
        show_warning = self._profile.get_option('warnings.development_version')
        version = parse(__version__)

        if version.is_postrelease and show_warning:
            echo.echo_warning(f'You are currently using a post release development version of AiiDA: {version}')
            echo.echo_warning('Be aware that this is not recommended for production and is not officially supported.')
            echo.echo_warning('Databases used with this version may not be compatible with future releases of AiiDA')
            echo.echo_warning('as you might not be able to automatically migrate your data.\n')
