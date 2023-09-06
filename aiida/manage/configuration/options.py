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

from aiida.common.exceptions import ConfigurationError

__all__ = ('get_option', 'get_option_names', 'parse_option', 'Option')


class Option:
    """Represent a configuration option schema."""

    def __init__(self, name: str, schema: Dict[str, Any], field):
        self._name = name
        self._schema = schema
        self._field = field

    def __str__(self) -> str:
        return f'Option(name={self._name})'

    @property
    def name(self) -> str:
        return self._name

    @property
    def valid_type(self) -> Any:
        return self._field.type_

    @property
    def schema(self) -> Dict[str, Any]:
        return self._schema

    @property
    def default(self) -> Any:
        return self._field.default

    @property
    def description(self) -> str:
        return self._field.field_info.description

    @property
    def global_only(self) -> bool:
        from .config import ProfileOptionsSchema
        return self._name in ProfileOptionsSchema.__fields__

    def validate(self, value: Any) -> Any:
        """Validate a value

        :param value: The input value
        :param cast: Attempt to cast the value to the required type

        :return: The output value
        :raise: ConfigValidationError

        """
        value, validation_error = self._field.validate(value, {}, loc=None)

        if validation_error:
            raise ConfigurationError(validation_error)

        return value


def get_option_names() -> List[str]:
    """Return a list of available option names."""
    from .config import GlobalOptionsSchema
    return [key.replace('__', '.') for key in GlobalOptionsSchema.__fields__]


def get_option(name: str) -> Option:
    """Return option."""
    from .config import GlobalOptionsSchema
    options = GlobalOptionsSchema.__fields__
    option_name = name.replace('.', '__')
    if option_name not in options:
        raise ConfigurationError(f'the option {name} does not exist')
    return Option(name, GlobalOptionsSchema.schema()['properties'][option_name], options[option_name])


def parse_option(option_name: str, option_value: Any) -> Tuple[Option, Any]:
    """Parse and validate a value for a configuration option.

    :param option_name: the name of the configuration option
    :param option_value: the option value
    :return: a tuple of the option and the parsed value

    """
    option = get_option(option_name)
    value = option.validate(option_value)

    return option, value
