# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Modules related to the configuration of an AiiDA instance."""

# AUTO-GENERATED

# yapf: disable
# pylint: disable=wildcard-import

from .config import *
from .migrations import *
from .options import *
from .profile import *

__all__ = (
    'CURRENT_CONFIG_VERSION',
    'Config',
    'MIGRATIONS',
    'OLDEST_COMPATIBLE_CONFIG_VERSION',
    'Option',
    'Profile',
    'check_and_migrate_config',
    'config_needs_migrating',
    'downgrade_config',
    'get_current_version',
    'get_option',
    'get_option_names',
    'parse_option',
    'upgrade_config',
)

# yapf: enable

# END AUTO-GENERATED

# pylint: disable=global-statement,redefined-outer-name,wrong-import-order

__all__ += (
    'get_config', 'get_config_option', 'get_config_path', 'get_profile', 'load_profile', 'reset_config', 'CONFIG'
)

from contextlib import contextmanager
import os
from typing import TYPE_CHECKING, Any, Optional
import warnings

from aiida.common.warnings import AiidaDeprecationWarning

if TYPE_CHECKING:
    from aiida.manage.configuration import Config, Profile  # pylint: disable=import-self

# global variables for aiida
CONFIG: Optional['Config'] = None


def get_config_path():
    """Returns path to .aiida configuration directory."""
    from .settings import AIIDA_CONFIG_FOLDER, DEFAULT_CONFIG_FILE_NAME

    return os.path.join(AIIDA_CONFIG_FOLDER, DEFAULT_CONFIG_FILE_NAME)


def load_config(create=False) -> 'Config':
    """Instantiate Config object representing an AiiDA configuration file.

    Warning: Contrary to :func:`~aiida.manage.configuration.get_config`, this function is uncached and will always
    create a new Config object. You may want to call :func:`~aiida.manage.configuration.get_config` instead.

    :param create: if True, will create the configuration file if it does not already exist
    :type create: bool

    :return: the config
    :rtype: :class:`~aiida.manage.configuration.config.Config`
    :raises aiida.common.MissingConfigurationError: if the configuration file could not be found and create=False
    """
    from aiida.common import exceptions

    from .config import Config

    filepath = get_config_path()

    if not os.path.isfile(filepath) and not create:
        raise exceptions.MissingConfigurationError(f'configuration file {filepath} does not exist')

    try:
        config = Config.from_file(filepath)
    except ValueError as exc:
        raise exceptions.ConfigurationError(f'configuration file {filepath} contains invalid JSON') from exc

    _merge_deprecated_cache_yaml(config, filepath)

    return config


def _merge_deprecated_cache_yaml(config, filepath):
    """Merge the deprecated cache_config.yml into the config."""
    cache_path = os.path.join(os.path.dirname(filepath), 'cache_config.yml')
    if not os.path.exists(cache_path):
        return

    # Imports are here to avoid them when not needed
    import shutil

    import yaml

    from aiida.common import timezone

    cache_path_backup = None
    # Keep generating a new backup filename based on the current time until it does not exist
    while not cache_path_backup or os.path.isfile(cache_path_backup):
        cache_path_backup = f"{cache_path}.{timezone.now().strftime('%Y%m%d-%H%M%S.%f')}"

    warnings.warn(
        'cache_config.yml use is deprecated and support will be removed in `v3.0`. Merging into config.json and '
        f'moving to: {cache_path_backup}',
        AiidaDeprecationWarning,
        stacklevel=2
    )

    with open(cache_path, 'r', encoding='utf8') as handle:
        cache_config = yaml.safe_load(handle)
    for profile_name, data in cache_config.items():
        if profile_name not in config.profile_names:
            warnings.warn(f"Profile '{profile_name}' from cache_config.yml not in config.json, skipping", UserWarning)
            continue
        for key, option_name in [('default', 'caching.default_enabled'), ('enabled', 'caching.enabled_for'),
                                 ('disabled', 'caching.disabled_for')]:
            if key in data:
                value = data[key]
                # in case of empty key
                value = [] if value is None and key != 'default' else value
                config.set_option(option_name, value, scope=profile_name)
    config.store()
    shutil.move(cache_path, cache_path_backup)


def load_profile(profile: Optional[str] = None, allow_switch=False) -> 'Profile':
    """Load a global profile, unloading any previously loaded profile.

    .. note:: if a profile is already loaded and no explicit profile is specified, nothing will be done

    :param profile: the name of the profile to load, by default will use the one marked as default in the config
    :param allow_switch: if True, will allow switching to a different profile when storage is already loaded

    :return: the loaded `Profile` instance
    :raises `aiida.common.exceptions.InvalidOperation`:
        if another profile has already been loaded and allow_switch is False
    """
    from aiida.manage import get_manager
    return get_manager().load_profile(profile, allow_switch)


def get_profile() -> Optional['Profile']:
    """Return the currently loaded profile.

    :return: the globally loaded `Profile` instance or `None`
    """
    from aiida.manage import get_manager
    return get_manager().get_profile()


@contextmanager
def profile_context(profile: Optional[str] = None, allow_switch=False) -> 'Profile':
    """Return a context manager for temporarily loading a profile, and unloading on exit.

    :param profile: the name of the profile to load, by default will use the one marked as default in the config
    :param allow_switch: if True, will allow switching to a different profile

    :return: a context manager for temporarily loading a profile
    """
    from aiida.manage import get_manager
    manager = get_manager()
    current_profile = manager.get_profile()
    manager.load_profile(profile, allow_switch)
    yield profile
    if current_profile is None:
        manager.unload_profile()
    else:
        manager.load_profile(current_profile, allow_switch=True)


def create_profile(
    config: Config,
    storage_cls,
    *,
    name: str,
    email: str,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    institution: Optional[str] = None,
    **kwargs
) -> Profile:
    """Create a new profile, initialise its storage and create a default user.

    :param config: The config instance.
    :param storage_cls: The storage class obtained through loading the entry point from ``aiida.storage`` group.
    :param name: Name of the profile.
    :param email: Email for the default user.
    :param first_name: First name for the default user.
    :param last_name: Last name for the default user.
    :param institution: Institution for the default user.
    :param kwargs: Arguments to initialise instance of the selected storage implementation.
    """
    from aiida.manage import get_manager
    from aiida.orm import User

    storage_config = storage_cls.Configuration(**{k: v for k, v in kwargs.items() if v is not None}).model_dump()
    profile: Profile = config.create_profile(name=name, storage_cls=storage_cls, storage_config=storage_config)

    with profile_context(profile.name, allow_switch=True):
        manager = get_manager()
        storage = manager.get_profile_storage()

        if not storage.read_only:
            user = User(email=email, first_name=first_name, last_name=last_name, institution=institution).store()
            # We can safely use ``Config.set_default_user_email`` here instead of ``Manager.set_default_user_email``
            # since the storage backend of this new profile is not loaded yet.
            config.set_default_user_email(profile, user.email)

    return profile


def reset_config():
    """Reset the globally loaded config.

    .. warning:: This is experimental functionality and should for now be used only internally. If the reset is unclean
        weird unknown side-effects may occur that end up corrupting or destroying data.
    """
    global CONFIG
    CONFIG = None


def get_config(create=False):
    """Return the current configuration.

    If the configuration has not been loaded yet
     * the configuration is loaded using ``load_config``
     * the global `CONFIG` variable is set
     * the configuration object is returned

    Note: This function will except if no configuration file can be found. Only call this function, if you need
    information from the configuration file.

    :param create: if True, will create the configuration file if it does not already exist
    :type create: bool

    :return: the config
    :rtype: :class:`~aiida.manage.configuration.config.Config`
    :raises aiida.common.ConfigurationError: if the configuration file could not be found, read or deserialized
    """
    global CONFIG

    if not CONFIG:
        CONFIG = load_config(create=create)

        if CONFIG.get_option('warnings.showdeprecations'):
            # If the user does not want to get AiiDA deprecation warnings, we disable them - this can be achieved with::
            #   verdi config warnings.showdeprecations False
            # Note that the AiidaDeprecationWarning does NOT inherit from DeprecationWarning
            warnings.simplefilter('default', AiidaDeprecationWarning)  # pylint: disable=no-member
            # This should default to 'once', i.e. once per different message
        else:
            warnings.simplefilter('ignore', AiidaDeprecationWarning)  # pylint: disable=no-member

    return CONFIG


def get_config_option(option_name: str) -> Any:
    """Return the value of a configuration option.

    In order of priority, the option is returned from:

    1. The current profile, if loaded and the option specified
    2. The current configuration, if loaded and the option specified
    3. The default value for the option

    :param option_name: the name of the option to return
    :return: the value of the option
    :raises `aiida.common.exceptions.ConfigurationError`: if the option is not found
    """
    from aiida.manage import get_manager
    return get_manager().get_option(option_name)
