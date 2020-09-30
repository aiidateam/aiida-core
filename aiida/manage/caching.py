# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Definition of caching mechanism and configuration for calculations."""
import os
import re
import copy
import keyword
from enum import Enum
from collections import namedtuple
from contextlib import contextmanager, suppress

import yaml
from wrapt import decorator

from aiida.common import exceptions
from aiida.common.lang import type_check

from aiida.plugins.entry_point import ENTRY_POINT_STRING_SEPARATOR, ENTRY_POINT_GROUP_TO_MODULE_PATH_MAP

__all__ = ('get_use_cache', 'enable_caching', 'disable_caching')


class ConfigKeys(Enum):
    """Valid keys for caching configuration."""

    DEFAULT = 'default'
    ENABLED = 'enabled'
    DISABLED = 'disabled'


DEFAULT_CONFIG = {
    ConfigKeys.DEFAULT.value: False,
    ConfigKeys.ENABLED.value: [],
    ConfigKeys.DISABLED.value: [],
}


def _get_config(config_file):
    """Return the caching configuration.

    :param config_file: the absolute path to the caching configuration file
    :return: the configuration dictionary
    """
    from aiida.manage.configuration import get_profile

    profile = get_profile()

    if profile is None:
        exceptions.ConfigurationError('no profile has been loaded')

    try:
        with open(config_file, 'r', encoding='utf8') as handle:
            config = yaml.safe_load(handle)[profile.name]
    except (OSError, IOError, KeyError):
        # No config file, or no config for this profile
        return DEFAULT_CONFIG

    # Validate configuration
    for key in config:
        if key not in DEFAULT_CONFIG:
            raise exceptions.ConfigurationError(f"Configuration error: Invalid key '{key}' in cache_config.yml")

    # Add defaults where key is either completely missing or specifies no values in which case it will be `None`
    for key, default_config in DEFAULT_CONFIG.items():
        if key not in config or config[key] is None:
            config[key] = default_config

    try:
        type_check(config[ConfigKeys.DEFAULT.value], bool)
        type_check(config[ConfigKeys.ENABLED.value], list)
        type_check(config[ConfigKeys.DISABLED.value], list)
    except TypeError as exc:
        raise exceptions.ConfigurationError('Invalid type in caching configuration file.') from exc

    # Check validity of enabled and disabled entries
    try:
        for identifier in config[ConfigKeys.ENABLED.value] + config[ConfigKeys.DISABLED.value]:
            _validate_identifier_pattern(identifier=identifier)
    except ValueError as exc:
        raise exceptions.ConfigurationError('Invalid identifier pattern in enable or disable list.') from exc

    return config


_CONFIG = {}


def configure(config_file=None):
    """Reads the caching configuration file and sets the _CONFIG variable."""
    # pylint: disable=global-statement
    if config_file is None:
        from aiida.manage.configuration import get_config

        config = get_config()
        config_file = os.path.join(config.dirpath, 'cache_config.yml')

    global _CONFIG
    _CONFIG.clear()
    _CONFIG.update(_get_config(config_file=config_file))


@decorator
def _with_config(wrapped, _, args, kwargs):
    """Function decorator to load the caching configuration for the scope of the wrapped function."""
    if not _CONFIG:
        configure()
    return wrapped(*args, **kwargs)


@_with_config
def get_use_cache(*, identifier=None):
    """Return whether the caching mechanism should be used for the given process type according to the configuration.

    :param identifier: Process type string of the node
    :type identifier: str
    :return: boolean, True if caching is enabled, False otherwise
    :raises: `~aiida.common.exceptions.ConfigurationError` if the configuration is invalid, either due to a general
        configuration error, or by defining the class both enabled and disabled
    """
    type_check(identifier, str, allow_none=True)

    if identifier is not None:
        type_check(identifier, str)

        enable_matches = [
            pattern for pattern in _CONFIG[ConfigKeys.ENABLED.value]
            if _match_wildcard(string=identifier, pattern=pattern)
        ]
        disable_matches = [
            pattern for pattern in _CONFIG[ConfigKeys.DISABLED.value]
            if _match_wildcard(string=identifier, pattern=pattern)
        ]

        if enable_matches and disable_matches:
            # If both enable and disable have matching identifier, we search for
            # the most specific one. This is determined by checking whether
            # all other patterns match the specific pattern.
            PatternWithResult = namedtuple('PatternWithResult', ['pattern', 'use_cache'])
            most_specific = []
            for specific_pattern in enable_matches:
                if all(
                    _match_wildcard(string=specific_pattern, pattern=other_pattern)
                    for other_pattern in enable_matches + disable_matches
                ):
                    most_specific.append(PatternWithResult(pattern=specific_pattern, use_cache=True))
            for specific_pattern in disable_matches:
                if all(
                    _match_wildcard(string=specific_pattern, pattern=other_pattern)
                    for other_pattern in enable_matches + disable_matches
                ):
                    most_specific.append(PatternWithResult(pattern=specific_pattern, use_cache=False))

            if len(most_specific) > 1:
                raise exceptions.ConfigurationError((
                    'Invalid configuration: multiple matches for identifier {}'
                    ', but the most specific identifier is not unique. Candidates: {}'
                ).format(identifier, [match.pattern for match in most_specific]))
            if not most_specific:
                raise exceptions.ConfigurationError(
                    'Invalid configuration: multiple matches for identifier {}, but none of them is most specific.'.
                    format(identifier)
                )
            return most_specific[0].use_cache
        if enable_matches:
            return True
        if disable_matches:
            return False
    return _CONFIG[ConfigKeys.DEFAULT.value]


@contextmanager
@_with_config
def _reset_config():
    """Reset the configuration by clearing the contents of the global config variable."""
    # pylint: disable=global-statement
    global _CONFIG
    config_copy = copy.deepcopy(_CONFIG)
    yield
    _CONFIG.clear()
    _CONFIG.update(config_copy)


@contextmanager
def enable_caching(*, identifier=None):
    """Context manager to enable caching, either for a specific node class, or globally.

    .. warning:: this does not affect the behavior of the daemon, only the local Python interpreter.

    :param identifier: Process type string of the node, or a pattern with '*' wildcard that matches it.
    :type identifier: str
    """

    type_check(identifier, str, allow_none=True)
    with _reset_config():
        if identifier is None:
            _CONFIG[ConfigKeys.DEFAULT.value] = True
            _CONFIG[ConfigKeys.DISABLED.value] = []
        else:
            _validate_identifier_pattern(identifier=identifier)
            _CONFIG[ConfigKeys.ENABLED.value].append(identifier)
            with suppress(ValueError):
                _CONFIG[ConfigKeys.DISABLED.value].remove(identifier)
        yield


@contextmanager
def disable_caching(*, identifier=None):
    """Context manager to disable caching, either for a specific node class, or globally.

    .. warning:: this does not affect the behavior of the daemon, only the local Python interpreter.

    :param identifier: Process type string of the node, or a pattern with '*' wildcard that matches it.
    :type identifier: str
    """
    type_check(identifier, str, allow_none=True)

    with _reset_config():
        if identifier is None:
            _CONFIG[ConfigKeys.DEFAULT.value] = False
            _CONFIG[ConfigKeys.ENABLED.value] = []
        else:
            _validate_identifier_pattern(identifier=identifier)
            _CONFIG[ConfigKeys.DISABLED.value].append(identifier)
            with suppress(ValueError):
                _CONFIG[ConfigKeys.ENABLED.value].remove(identifier)
        yield


def _match_wildcard(*, string, pattern):
    """
    Helper function to check whether a given name matches a pattern
    which can contain '*' wildcards.
    """
    regexp = '.*'.join(re.escape(part) for part in pattern.split('*'))
    return re.fullmatch(pattern=regexp, string=string) is not None


def _validate_identifier_pattern(*, identifier):
    """
    The identifier (without wildcards) can have one of two forms:

    1.  <group_name><ENTRY_POINT_STRING_SEPARATOR><tail>

        where `group_name` is one of the keys in `ENTRY_POINT_GROUP_TO_MODULE_PATH_MAP`
        and `tail` can be anything _except_ `ENTRY_POINT_STRING_SEPARATOR`.

    2. a fully qualified Python name

        this is a colon-separated string, where each part satisfies
        `part.isidentifier() and not keyword.iskeyword(part)`

    This function checks if an identifier _with_ wildcards can possibly
    match one of these two forms. If it can not, a `ValueError` is raised.

    :param identifier: Process type string, or a pattern with '*' wildcard that matches it.
    :type identifier: str
    """
    common_error_msg = f"Invalid identifier pattern '{identifier}': "
    assert ENTRY_POINT_STRING_SEPARATOR not in '.*'  # The logic of this function depends on this
    # Check if it can be an entry point string
    if identifier.count(ENTRY_POINT_STRING_SEPARATOR) > 1:
        raise ValueError(
            f"{common_error_msg}Can contain at most one entry point string separator '{ENTRY_POINT_STRING_SEPARATOR}'"
        )
    # If there is one separator, it must be an entry point string.
    # Check if the left hand side is a matching pattern
    if ENTRY_POINT_STRING_SEPARATOR in identifier:
        group_pattern, _ = identifier.split(ENTRY_POINT_STRING_SEPARATOR)
        if not any(
            _match_wildcard(string=group_name, pattern=group_pattern)
            for group_name in ENTRY_POINT_GROUP_TO_MODULE_PATH_MAP
        ):
            raise ValueError(
                common_error_msg + "Group name pattern '{}' does not match any of the AiiDA entry point group names.".
                format(group_pattern)
            )
        # The group name pattern matches, and there are no further
        # entry point string separators in the identifier, hence it is
        # a valid pattern.
        return
    # The separator might be swallowed in a wildcard, for example
    # aiida.* or aiida.calculations*
    if '*' in identifier:
        group_part, _ = identifier.split('*', 1)
        if any(group_name.startswith(group_part) for group_name in ENTRY_POINT_GROUP_TO_MODULE_PATH_MAP):
            return
    # Finally, check if it could be a fully qualified Python name
    for identifier_part in identifier.split('.'):
        # If it contains a wildcard, we can not check for keywords.
        # Replacing all wildcards with a single letter must give an
        # identifier - this checks for invalid characters, and that it
        # does not start with a number.
        if '*' in identifier_part:
            if not identifier_part.replace('*', 'a').isidentifier():
                raise ValueError(
                    common_error_msg +
                    f"Identifier part '{identifier_part}' can not match a fully qualified Python name."
                )
        else:
            if not identifier_part.isidentifier():
                raise ValueError(f"{common_error_msg}'{identifier_part}' is not a valid Python identifier.")
            if keyword.iskeyword(identifier_part):
                raise ValueError(f"{common_error_msg}'{identifier_part}' is a reserved Python keyword.")
