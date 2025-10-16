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

__all__ = ('Option', 'get_option', 'get_option_names', 'parse_option')


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
        return self._field.annotation

    @property
    def schema(self) -> Dict[str, Any]:
        return self._schema

    @property
    def default(self) -> Any:
        return self._field.default

    @property
    def description(self) -> str:
        return self._field.description

    @property
    def global_only(self) -> bool:
        from .config import ProfileOptionsSchema

        return self._name.replace('.', '__') not in ProfileOptionsSchema.model_fields

    def validate(self, value: Any) -> Any:
        """Validate a value

        :param value: The input value
        :return: The output value
        :raise: ConfigurationError
        """
        from pydantic import ValidationError

        from .config import GlobalOptionsSchema

        attribute = self.name.replace('.', '__')

        try:
            # There is no straightforward way to validate a single field of a model in pydantic v2.0. The following
            # approach is the current work around, see: https://github.com/pydantic/pydantic/discussions/7367
            result = GlobalOptionsSchema.__pydantic_validator__.validate_assignment(
                GlobalOptionsSchema.model_construct(), attribute, value
            )
        except ValidationError as exception:
            messages = []
            for error in exception.errors():
                try:
                    messages.append(str(error['ctx']['error']))
                except KeyError:
                    messages.append(f"Invalid value for `{error['loc'][0]}`: {error['msg']}")

            raise ConfigurationError('\n'.join(messages)) from exception

        # Return the value from the constructed model as this will have casted the value to the right type
        return getattr(result, attribute)


def get_option_names() -> List[str]:
    """Return a list of available option names."""
    from .config import GlobalOptionsSchema

    return [key.replace('__', '.') for key in GlobalOptionsSchema.model_fields]


def get_option(name: str) -> Option:
    """Return option."""
    from .config import GlobalOptionsSchema

    options = GlobalOptionsSchema.model_fields
    option_name = name.replace('.', '__')
    if option_name not in options:
        raise ConfigurationError(f'the option {name} does not exist')
    return Option(name, GlobalOptionsSchema.model_json_schema()['properties'][option_name], options[option_name])


def parse_option(option_name: str, option_value: Any) -> Tuple[Option, Any]:
    """Parse and validate a value for a configuration option.

    :param option_name: the name of the configuration option
    :param option_value: the option value
    :return: a tuple of the option and the parsed value

    """
    option = get_option(option_name)
    value = option.validate(option_value)

    return option, value
