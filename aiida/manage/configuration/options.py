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
from functools import lru_cache
from importlib import resources
import json
from typing import Any, Dict, List, Tuple

from jsonschema import validate, ValidationError

from . import schema as schema_module

__all__ = ('get_option', 'get_option_names', 'parse_option', 'ValidationError', 'Option')

SCHEMA_FILE = 'config-v5.schema.json'
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
        :raise: jsonschema.exceptions.ValidationError

        """
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
            except ValueError:
                pass
        validate(instance=value, schema=self.schema)
        return value


@lru_cache(1)
def get_schema() -> Dict[str, Any]:
    """Return the configuration schema."""
    return json.loads(resources.read_text(schema_module, SCHEMA_FILE, encoding='utf8'))


def get_schema_options() -> Dict[str, Dict[str, Any]]:
    """Return schema for options."""
    schema = get_schema()
    return schema['definitions']['options']['properties']


def get_option_names() -> List[str]:
    """Return a list of available option names."""
    return list(get_schema_options())


def get_option(name: str) -> Option:
    """Return option."""
    options = get_schema_options()
    if name not in options:
        raise KeyError(f'the option {name} does not exist')
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
