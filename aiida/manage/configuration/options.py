# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Definition of known configuration options and methods to parse and get option values."""
from typing import Any, Dict, List, Tuple

import jsonschema

from aiida.common.exceptions import ConfigurationError

__all__ = ('get_option', 'get_option_names', 'parse_option', 'Option')

NO_DEFAULT = ()


class Option:
    """Represent a configuration option schema."""

    def __init__(self, name: str, schema: Dict[str, Any]):
        self._name = name
        self._schema = schema

    def __str__(self) -> str:
        return f'Option(name={self._name})'

    @property
    def name(self) -> str:
        return self._name

    @property
    def schema(self) -> Dict[str, Any]:
        return self._schema

    @property
    def valid_type(self) -> Any:
        return self._schema.get('type', None)

    @property
    def default(self) -> Any:
        return self._schema.get('default', NO_DEFAULT)

    @property
    def description(self) -> str:
        return self._schema.get('description', '')

    @property
    def global_only(self) -> bool:
        return self._schema.get('global_only', False)

    def validate(self, value: Any, cast: bool = True) -> Any:
        """Validate a value

        :param value: The input value
        :param cast: Attempt to cast the value to the required type

        :return: The output value
        :raise: ConfigValidationError

        """
        # pylint: disable=too-many-branches
        from aiida.manage.caching import _validate_identifier_pattern

        from .config import ConfigValidationError

        if cast:
            try:
                if self.valid_type == 'boolean':
                    if isinstance(value, str):
                        if value.strip().lower() in ['0', 'false', 'f']:
                            value = False
                        elif value.strip().lower() in ['1', 'true', 't']:
                            value = True
                    else:
                        value = bool(value)
                elif self.valid_type == 'string':
                    value = str(value)
                elif self.valid_type == 'integer':
                    value = int(value)
                elif self.valid_type == 'number':
                    value = float(value)
                elif self.valid_type == 'array' and isinstance(value, str):
                    value = value.split()
            except ValueError:
                pass

        try:
            jsonschema.validate(instance=value, schema=self.schema)
        except jsonschema.ValidationError as exc:
            raise ConfigValidationError(message=exc.message, keypath=[self.name, *(exc.path or [])], schema=exc.schema)

        # special caching validation
        if self.name in ('caching.enabled_for', 'caching.disabled_for'):
            for i, identifier in enumerate(value):
                try:
                    _validate_identifier_pattern(identifier=identifier)
                except ValueError as exc:
                    raise ConfigValidationError(message=str(exc), keypath=[self.name, str(i)])

        return value


def get_schema_options() -> Dict[str, Dict[str, Any]]:
    """Return schema for options."""
    from .config import config_schema
    schema = config_schema()
    return schema['definitions']['options']['properties']


def get_option_names() -> List[str]:
    """Return a list of available option names."""
    return list(get_schema_options())


def get_option(name: str) -> Option:
    """Return option."""
    options = get_schema_options()
    if name not in options:
        raise ConfigurationError(f'the option {name} does not exist')
    return Option(name, options[name])


def parse_option(option_name: str, option_value: Any) -> Tuple[Option, Any]:
    """Parse and validate a value for a configuration option.

    :param option_name: the name of the configuration option
    :param option_value: the option value
    :return: a tuple of the option and the parsed value

    """
    option = get_option(option_name)
    value = option.validate(option_value, cast=True)

    return option, value
