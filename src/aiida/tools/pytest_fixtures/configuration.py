"""Fixtures to create and load temporary AiiDA configuration directories and profiles."""

from __future__ import annotations

import contextlib
import os
import pathlib
import secrets
import typing as t

import pytest

from aiida.manage.configuration.settings import AiiDAConfigDir

if t.TYPE_CHECKING:
    from aiida.manage.configuration.config import Config


@pytest.fixture(scope='session')
def aiida_config_factory():
    """Return a factory to create and load a new temporary AiiDA configuration directory.

    The factory is a context manager that returns a loaded :class:`aiida.manage.configuration.config.Config`. It
    requires a path on the local file system where the configuration directory is to be created as an argument. If
    another configuration directory was already loaded that is automatically restored at the end of the context manager.
    This way, any changes made to the configuration during the context are fully temporary and automatically undone
    after the test.

    Usage::

        def test(aiida_config_factory, tmp_path_factory):
            import secrets
            with aiida_config_factory(tmp_path_factory.mktemp(secrets.token_hex(16))) as config:
                yield config

    The factory has the following signature to allow further configuring the profile that is created and loaded:

    :param dirpath: The path to create the configuration directory in.
    :returns `~aiida.manage.configuration.config.Config`: The loaded temporary config.
    """

    @contextlib.contextmanager
    def factory(dirpath: pathlib.Path):
        from aiida.common.exceptions import MissingConfigurationError
        from aiida.manage.configuration import get_config, reset_config, settings

        try:
            current_config = get_config()
        except MissingConfigurationError:
            current_config = None

        current_path_variable = os.environ.get(settings.DEFAULT_AIIDA_PATH_VARIABLE)

        reset_config()

        dirpath_config = dirpath / settings.DEFAULT_CONFIG_DIR_NAME
        os.environ[settings.DEFAULT_AIIDA_PATH_VARIABLE] = str(dirpath_config)
        AiiDAConfigDir.set(dirpath_config)
        config = get_config(create=True)

        try:
            yield config
        finally:
            if current_config:
                reset_config()
                AiiDAConfigDir.set(pathlib.Path(current_config.dirpath))
                get_config()

            if current_path_variable is None:
                os.environ.pop(settings.DEFAULT_AIIDA_PATH_VARIABLE, None)
            else:
                os.environ[settings.DEFAULT_AIIDA_PATH_VARIABLE] = current_path_variable

    return factory


@pytest.fixture(scope='session')
def aiida_profile_factory():
    """Return a factory to create and load a new temporary AiiDA profile.

    The factory is a context manager that returns a loaded :class:`aiida.manage.configuration.profile.Profile`. It
    requires a :class:`aiida.manage.configuration.config.Config` instance to which the profile is added. If another
    profile was already loaded, that is automatically restored at the end of the context manager. This way, any changes
    made to the profile during the context are fully temporary and automatically undone after the test. The created
    ``Profile`` instance dynamically has the method ``reset_storage`` added which, when called, deletes all content of
    the storage, recreating the default user. The daemon is also stopped if it was running.

    Usage::

        def test(aiida_config_tmp, aiida_profile_factory):
            with aiida_profile_factory(aiida_config_tmp) as profile:
                yield profile

    The factory has the following signature to allow further configuring the profile that is created and loaded:

    :param storage_backend: The storage plugin to use. Defaults to ``core.sqlite_dos``.
    :param storage_config: The configuration to use for the selected storage plugin.
    :param broker_backend: The broker plugin to use. Defaults to defining no broker.
    :param broker_config: The configuration to use for the selected broker plugin.
    :param name: The name of the profile. Defaults to a random string.
    :param name: The email to use for the default user. Defaults to ``test@localhost``.
    :returns `~aiida.manage.configuration.profile.Profile`: The loaded temporary profile.
    """

    @contextlib.contextmanager
    def factory(
        config: 'Config',
        *,
        storage_backend: str = 'core.sqlite_dos',
        storage_config: dict[str, t.Any] | None = None,
        broker_backend: str | None = None,
        broker_config: dict[str, t.Any] | None = None,
        name: str | None = None,
        email: str = 'test@localhost',
    ):
        from aiida.manage.configuration import create_profile, profile_context
        from aiida.manage.manager import get_manager

        manager = get_manager()
        name = name or secrets.token_hex(16)
        storage_config = storage_config or {'filepath': str(pathlib.Path(config.dirpath) / name / 'storage')}

        if broker_backend and broker_config is None:
            broker_config = {
                'broker_protocol': 'amqp',
                'broker_username': 'guest',
                'broker_password': 'guest',
                'broker_host': '127.0.0.1',
                'broker_port': 5672,
                'broker_virtual_host': '',
            }

        profile = create_profile(
            config,
            storage_backend=storage_backend,
            storage_config=storage_config,
            broker_backend=broker_backend,
            broker_config=broker_config,
            name=name,
            email=email,
            is_test_profile=True,
        )
        config.set_default_profile(profile.name)

        def reset_storage():
            """Reset the storage of the profile.

            This ensures that the contents of the profile are reset as well as the ``Manager``, which may hold
            references to data that will be destroyed. The daemon will also be stopped if it was running.
            """
            from aiida.engine.daemon.client import DaemonException, get_daemon_client
            from aiida.orm import User

            if broker_backend:
                daemon_client = get_daemon_client()

                if daemon_client.is_daemon_running:
                    try:
                        daemon_client.stop_daemon(wait=True)
                    except DaemonException:
                        pass

            manager.get_profile_storage()._clear()
            manager.reset_profile()

            User(email=profile.default_user_email or email).store()

        # Add the ``reset_storage`` method, such that users can empty the storage through the ``Profile`` instance that
        # is returned by this fixture.
        setattr(profile, 'reset_storage', reset_storage)

        with profile_context(profile, allow_switch=True):
            yield profile

    return factory


@pytest.fixture(scope='session', autouse=True)
def aiida_config(tmp_path_factory, aiida_config_factory):
    """Return a loaded temporary AiiDA configuration directory.

    This fixture is session-scoped and used automatically as soon as these fixtures are imported.

    :returns :class:`~aiida.manage.configuration.config.Config`: The loaded temporary config.
    """
    with aiida_config_factory(tmp_path_factory.mktemp(secrets.token_hex(16))) as config:
        yield config


@pytest.fixture(scope='session', autouse=True)
def aiida_profile(aiida_config, aiida_profile_factory):
    """Return a loaded temporary AiiDA profile.

    This fixture is session-scoped and used automatically as soon as these fixtures are imported. The profile defines
    no broker and uses the ``core.sqlite_dos`` storage backend, meaning it requires no services to run.

    :returns :class:`~aiida.manage.configuration.profile.Profile`: The loaded temporary profile.
    """
    with aiida_profile_factory(aiida_config) as profile:
        yield profile


@pytest.fixture(scope='function')
def aiida_profile_clean(aiida_profile):
    """Return a loaded temporary AiiDA profile where the data storage is cleaned before the start of the test.

    This is a function-scoped version of the ``aiida_profile`` fixture.

    :returns :class:`~aiida.manage.configuration.profile.Profile`: The loaded temporary profile.
    """
    aiida_profile.reset_storage()
    yield aiida_profile


@pytest.fixture(scope='class')
def aiida_profile_clean_class(aiida_profile):
    """Return a loaded temporary AiiDA profile where the data storage is cleaned before the start of the test.

    This is a class-scoped version of the ``aiida_profile`` fixture.

    :returns `~aiida.manage.configuration.profile.Profile`: The loaded temporary profile.
    """
    aiida_profile.reset_storage()
    yield aiida_profile


@pytest.fixture(scope='function')
def aiida_config_tmp(tmp_path, aiida_config_factory):
    """Create and load a temporary AiiDA configuration directory.

    This fixture is function-scoped and automatically restores any previously loaded config after the test.

    :returns :class:`~aiida.manage.configuration.config.Config`: The loaded temporary config.
    """
    with aiida_config_factory(tmp_path) as config:
        yield config


@pytest.fixture(scope='function')
def aiida_profile_tmp(aiida_config_tmp, aiida_profile_factory):
    """Create and load a temporary AiiDA profile.

    This fixture is function-scoped and automatically restores any previously loaded profile after the test.

    :returns :class:`~aiida.manage.configuration.profile.Profile`: The loaded temporary profile.
    """
    with aiida_profile_factory(aiida_config_tmp) as profile:
        yield profile
