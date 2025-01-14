###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Definition of caching mechanism and configuration for calculations."""

from __future__ import annotations

import keyword
import re
from collections import namedtuple
from contextlib import contextmanager, suppress
from enum import Enum

from aiida.common import exceptions
from aiida.common.lang import type_check
from aiida.manage.configuration import get_config_option
from aiida.plugins.entry_point import ENTRY_POINT_GROUP_TO_MODULE_PATH_MAP, ENTRY_POINT_STRING_SEPARATOR

__all__ = ('disable_caching', 'enable_caching', 'get_use_cache')


class ConfigKeys(Enum):
    """Valid keys for caching configuration."""

    DEFAULT = 'caching.default_enabled'
    ENABLED = 'caching.enabled_for'
    DISABLED = 'caching.disabled_for'


class _ContextCache:
    """Cache options, accounting for when in enable_caching or disable_caching contexts."""

    def __init__(self):
        self._default_all = None
        self._enable = []
        self._disable = []

    def clear(self):
        """Clear caching overrides."""
        self.__init__()  # type: ignore[misc]

    def enable_all(self):
        self._default_all = 'enable'

    def disable_all(self):
        self._default_all = 'disable'

    def enable(self, identifier: str):
        self._enable.append(identifier)
        with suppress(ValueError):
            self._disable.remove(identifier)

    def disable(self, identifier: str):
        self._disable.append(identifier)
        with suppress(ValueError):
            self._enable.remove(identifier)

    def get_options(self, strict: bool = False):
        """Return the options, applying any context overrides.

        :param strict: When set to ``True``, the function will actually try to resolve the identifier by loading it and
            if it fails, an exception is raised.
        """
        if self._default_all == 'disable':
            return False, [], []

        if self._default_all == 'enable':
            return True, [], []

        default = get_config_option(ConfigKeys.DEFAULT.value)
        enabled = get_config_option(ConfigKeys.ENABLED.value)[:]
        disabled = get_config_option(ConfigKeys.DISABLED.value)[:]

        for ident in self._disable:
            disabled.append(ident)
            with suppress(ValueError):
                enabled.remove(ident)

        for ident in self._enable:
            enabled.append(ident)
            with suppress(ValueError):
                disabled.remove(ident)

        # Check validity of enabled and disabled entries
        try:
            for identifier in enabled + disabled:
                _validate_identifier_pattern(identifier=identifier, strict=strict)
        except ValueError as exc:
            raise exceptions.ConfigurationError('Invalid identifier pattern in enable or disable list.') from exc

        return default, enabled, disabled


_CONTEXT_CACHE = _ContextCache()


@contextmanager
def enable_caching(*, identifier: str | None = None, strict: bool = False):
    """Context manager to enable caching, either for a specific node class, or globally.

    .. warning:: this does not affect the behavior of the daemon, only the local Python interpreter.

    :param identifier: Process type string of the node, or a pattern with '*' wildcard that matches it.
        If not provided, caching is enabled for all classes.
    :param strict: When set to ``True``, the function will actually try to resolve the identifier by loading it and if
        it fails, an exception is raised.
    :type identifier: str
    """
    type_check(identifier, str, allow_none=True)

    if identifier is None:
        _CONTEXT_CACHE.enable_all()
    else:
        _validate_identifier_pattern(identifier=identifier, strict=strict)
        _CONTEXT_CACHE.enable(identifier)
    yield
    _CONTEXT_CACHE.clear()


@contextmanager
def disable_caching(*, identifier: str | None = None, strict: bool = False):
    """Context manager to disable caching, either for a specific node class, or globally.

    .. warning:: this does not affect the behavior of the daemon, only the local Python interpreter.

    :param identifier: Process type string of the node, or a pattern with '*' wildcard that matches it.
        If not provided, caching is disabled for all classes.
    :param strict: When set to ``True``, the function will actually try to resolve the identifier by loading it and if
        it fails, an exception is raised.
    :type identifier: str
    """
    type_check(identifier, str, allow_none=True)

    if identifier is None:
        _CONTEXT_CACHE.disable_all()
    else:
        _validate_identifier_pattern(identifier=identifier, strict=strict)
        _CONTEXT_CACHE.disable(identifier)
    yield
    _CONTEXT_CACHE.clear()


def get_use_cache(*, identifier: str | None = None, strict: bool = False) -> bool:
    """Return whether the caching mechanism should be used for the given process type according to the configuration.

    :param identifier: Process type string of the node
    :param strict: When set to ``True``, the function will actually try to resolve the identifier by loading it and if
        it fails, an exception is raised.
    :return: boolean, True if caching is enabled, False otherwise
    :raises: `~aiida.common.exceptions.ConfigurationError` if the configuration is invalid, either due to a general
        configuration error, or by defining the class both enabled and disabled
    """
    type_check(identifier, str, allow_none=True)

    default, enabled, disabled = _CONTEXT_CACHE.get_options(strict=strict)

    if identifier is not None:
        type_check(identifier, str)

        enable_matches = [pattern for pattern in enabled if _match_wildcard(string=identifier, pattern=pattern)]
        disable_matches = [pattern for pattern in disabled if _match_wildcard(string=identifier, pattern=pattern)]

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
                raise exceptions.ConfigurationError(
                    f'Invalid configuration: multiple matches for identifier `{identifier}`, but the most specific '
                    f'identifier is not unique. Candidates: {[match.pattern for match in most_specific]}'
                )
            if not most_specific:
                raise exceptions.ConfigurationError(
                    f'Invalid configuration: multiple matches for identifier `{identifier}`, but none of them is most '
                    'specific.'
                )
            return most_specific[0].use_cache
        if enable_matches:
            return True
        if disable_matches:
            return False
    return default


def _match_wildcard(*, string: str, pattern: str) -> bool:
    """Return whether a given name matches a pattern which can contain '*' wildcards.

    :param string: The string to check.
    :param pattern: The patter to match for.
    :returns: ``True`` if ``string`` matches the ``pattern``, ``False`` otherwise.
    """
    regexp = '.*'.join(re.escape(part) for part in pattern.split('*'))
    return re.fullmatch(pattern=regexp, string=string) is not None


def _validate_identifier_pattern(*, identifier: str, strict: bool = False):
    """Validate an caching identifier pattern.

    The identifier (without wildcards) can have one of two forms:

    1.  <group_name><ENTRY_POINT_STRING_SEPARATOR><tail>

        where `group_name` is one of the keys in `ENTRY_POINT_GROUP_TO_MODULE_PATH_MAP`
        and `tail` can be anything _except_ `ENTRY_POINT_STRING_SEPARATOR`.

    2. a fully qualified Python name

        this is a colon-separated string, where each part satisfies
        `part.isidentifier() and not keyword.iskeyword(part)`

    This function checks if an identifier _with_ wildcards can possibly match one of these two forms. If it can not,
    a ``ValueError`` is raised.

    :param identifier: Process type string, or a pattern with '*' wildcard that matches it.
    :param strict: When set to ``True``, the function will actually try to resolve the identifier by loading it and if
        it fails, an exception is raised.
    :raises ValueError: If the identifier is an invalid identifier.
    :raises ValueError: If ``strict=True`` and the identifier cannot be successfully loaded.
    """
    import importlib

    from aiida.common.exceptions import EntryPointError
    from aiida.plugins.entry_point import load_entry_point_from_string

    common_error_msg = f'Invalid identifier pattern `{identifier}`: '
    assert ENTRY_POINT_STRING_SEPARATOR not in '.*'  # The logic of this function depends on this
    # Check if it can be an entry point string
    if identifier.count(ENTRY_POINT_STRING_SEPARATOR) > 1:
        raise ValueError(
            f'{common_error_msg}Can contain at most one entry point string separator `{ENTRY_POINT_STRING_SEPARATOR}`'
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
                common_error_msg
                + f'Group name pattern `{group_pattern}` does not match any of the AiiDA entry point group names.'
            )

        # If strict mode is enabled and the identifier is explicit, i.e., doesn't contain a wildcard, try to load it.
        if strict and '*' not in identifier:
            try:
                load_entry_point_from_string(identifier)
            except EntryPointError as exception:
                raise ValueError(common_error_msg + f'`{identifier}` cannot be loaded.') from exception

        # The group name pattern matches, and there are no further entry point string separators in the identifier,
        # hence it is a valid pattern.
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
                    common_error_msg
                    + f'Identifier part `{identifier_part}` can not match a fully qualified Python name.'
                )
        else:
            if not identifier_part.isidentifier():
                raise ValueError(f'{common_error_msg}`{identifier_part}` is not a valid Python identifier.')
            if keyword.iskeyword(identifier_part):
                raise ValueError(f'{common_error_msg}`{identifier_part}` is a reserved Python keyword.')

    if not strict:
        return

    # If there is no separator, it must be a fully qualified Python name.
    try:
        module_name = '.'.join(identifier.split('.')[:-1])
        class_name = identifier.split('.')[-1]
        module = importlib.import_module(module_name)
        getattr(module, class_name)
    except (ModuleNotFoundError, AttributeError, IndexError) as exc:
        raise ValueError(common_error_msg + f'`{identifier}` cannot be imported.') from exc
