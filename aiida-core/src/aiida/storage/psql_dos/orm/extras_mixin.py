###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Mixin class for SQL implementations of ``extras``."""

from collections.abc import Iterable
from typing import Any

from aiida.orm.implementation.utils import clean_value, validate_attribute_extra_key


class ExtrasMixin:
    """Mixin class for SQL implementations of ``extras``."""

    model: Any
    bare_model: Any
    is_stored: bool

    @property
    def extras(self) -> dict[str, Any]:
        return self.model.extras

    def get_extra(self, key: str) -> Any:
        try:
            return self.model.extras[key]
        except KeyError as exception:
            raise AttributeError(f'extra `{exception}` does not exist') from exception

    def set_extra(self, key: str, value: Any) -> None:
        validate_attribute_extra_key(key)

        if self.is_stored:
            value = clean_value(value)

        self.model.extras[key] = value
        self._flush_if_stored({'extras'})

    def set_extra_many(self, extras: dict[str, Any]) -> None:
        for key in extras:
            validate_attribute_extra_key(key)

        if self.is_stored:
            extras = {key: clean_value(value) for key, value in extras.items()}

        for key, value in extras.items():
            self.bare_model.extras[key] = value

        self._flush_if_stored({'extras'})

    def reset_extras(self, extras: dict[str, Any]) -> None:
        for key in extras:
            validate_attribute_extra_key(key)

        if self.is_stored:
            extras = clean_value(extras)

        self.bare_model.extras = extras
        self._flush_if_stored({'extras'})

    def delete_extra(self, key: str) -> None:
        try:
            self.model.extras.pop(key)
        except KeyError as exception:
            raise AttributeError(f'extra `{exception}` does not exist') from exception
        else:
            self._flush_if_stored({'extras'})

    def delete_extra_many(self, keys: Iterable[str]) -> None:
        non_existing_keys = [key for key in keys if key not in self.model.extras]

        if non_existing_keys:
            raise AttributeError(f'extras `{", ".join(non_existing_keys)}` do not exist')

        for key in keys:
            self.bare_model.extras.pop(key)

        self._flush_if_stored({'extras'})

    def clear_extras(self) -> None:
        self.model.extras = {}
        self._flush_if_stored({'extras'})

    def extras_items(self) -> Iterable[tuple[str, Any]]:
        yield from self.model.extras.items()

    def extras_keys(self) -> Iterable[str]:
        yield from self.model.extras.keys()
