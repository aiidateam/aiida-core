###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Various dictionary types with extended functionality."""

from __future__ import annotations

from collections.abc import KeysView, Mapping
from typing import Any

from aiida.common.typing import Self

from . import exceptions

__all__ = ('AttributeDict', 'DefaultFieldsAttributeDict', 'FixedFieldsAttributeDict')


class AttributeDict(dict[str, Any]):
    """This class internally stores values in a dictionary, but exposes
    the keys also as attributes, i.e. asking for attrdict.key
    will return the value of attrdict['key'] and so on.

    Raises an AttributeError if the key does not exist, when called as an attribute,
    while the usual KeyError if the key does not exist and the dictionary syntax is
    used.
    """

    def __init__(self, dictionary: Mapping[str, Any] | None = None):
        """Recursively turn the `dict` and all its nested dictionaries into `AttributeDict` instance."""
        super().__init__()
        if dictionary is None:
            return

        for key, value in dictionary.items():
            if isinstance(value, Mapping):
                self[key] = AttributeDict(value)
            else:
                self[key] = value

    def __repr__(self) -> str:
        """Representation of the object."""
        return f'{self.__class__.__name__}({dict.__repr__(self)})'

    def __getattr__(self, attr: str) -> Any:
        """Read a key as an attribute.

        :raises AttributeError: if the attribute does not correspond to an existing key.
        """
        try:
            return self[attr]
        except KeyError:
            errmsg = f"'{self.__class__.__name__}' object has no attribute '{attr}'"
            raise AttributeError(errmsg)

    def __setattr__(self, attr: str, value: Any) -> None:
        """Set a key as an attribute."""
        try:
            self[attr] = value
        except KeyError:
            raise AttributeError(
                f"AttributeError: '{attr}' is not a valid attribute of the object '{self.__class__.__name__}'"
            )

    def __delattr__(self, attr: str) -> None:
        """Delete a key as an attribute.

        :raises AttributeError: if the attribute does not correspond to an existing key.
        """
        try:
            del self[attr]
        except KeyError:
            errmsg = f"'{self.__class__.__name__}' object has no attribute '{attr}'"
            raise AttributeError(errmsg)

    def __deepcopy__(self, memo: Mapping[str, Any] | None = None) -> Self:
        """Deep copy."""
        from copy import deepcopy

        if memo is None:
            memo = {}
        retval = deepcopy(dict(self))
        return self.__class__(retval)

    def __getstate__(self) -> dict[str, Any]:
        """Needed for pickling this class."""
        return self.__dict__.copy()

    def __setstate__(self, dictionary: Mapping[str, Any]) -> None:
        """Needed for pickling this class."""
        self.__dict__.update(dictionary)

    def __dir__(self) -> KeysView[str]:
        return self.keys()


class FixedFieldsAttributeDict(AttributeDict):
    """A dictionary with access to the keys as attributes, and with filtering
    of valid attributes.
    This is only the base class, without valid attributes;
    use a derived class to do the actual work.
    E.g.::

        class TestExample(FixedFieldsAttributeDict):
            _valid_fields = ('a','b','c')
    """

    _valid_fields: tuple[Any, ...] = tuple()

    def __init__(self, init: Mapping[str, Any] | None = None):
        if init is None:
            init = {}

        for key in init:
            if key not in self._valid_fields:
                errmsg = f"'{key}' is not a valid key for object '{self.__class__.__name__}'"
                raise KeyError(errmsg)
        super().__init__(init)

    def __setitem__(self, item: str, value: Any) -> None:
        """Set a key as an attribute."""
        if item not in self._valid_fields:
            errmsg = f"'{item}' is not a valid key for object '{self.__class__.__name__}'"
            raise KeyError(errmsg)
        super().__setitem__(item, value)

    def __setattr__(self, attr: str, value: Any) -> None:
        """Overridden to allow direct access to fields with underscore."""
        if attr.startswith('_'):
            object.__setattr__(self, attr, value)
        else:
            super().__setattr__(attr, value)

    @classmethod
    def get_valid_fields(cls) -> tuple[str, ...]:
        """Return the list of valid fields."""
        return cls._valid_fields

    # TODO: We're in violation of the `dict` interface here,
    # we should be returning collections.abc.KeysView[Any]
    def __dir__(self) -> list[Any]:  # type: ignore[override]
        return list(self._valid_fields)


class DefaultFieldsAttributeDict(AttributeDict):
    """A dictionary with access to the keys as attributes, and with an
    internal value storing the 'default' keys to be distinguished
    from extra fields.

    Extra methods defaultkeys() and extrakeys() divide the set returned by
    keys() in default keys (i.e. those defined at definition time)
    and other keys.
    There is also a method get_default_fields() to return the internal list.

    Moreover, for undefined default keys, it returns None instead of raising a
    KeyError/AttributeError exception.

    Remember to define the _default_fields in a subclass!
    E.g.::

        class TestExample(DefaultFieldsAttributeDict):
            _default_fields = ('a','b','c')

    When the validate() method is called, it calls in turn all validate_KEY
    methods, where KEY is one of the default keys.
    If the method is not present, the field is considered to be always valid.
    Each validate_KEY method should accept a single argument 'value' that will
    contain the value to be checked.

    It raises a ValidationError if any of the validate_KEY
    function raises an exception, otherwise it simply returns.
    NOTE: the `validate_*` functions are called also for unset fields, so if the
    field can be empty on validation, you have to start your validation
    function with something similar to::

        if value is None:
            return

    .. todo::
        Decide behavior if I set to None a field.
        Current behavior, if
        ``a`` is an instance and 'def_field' one of the default fields, that is
        undefined, we get:

        * ``a.get('def_field')``: None
        * ``a.get('def_field','whatever')``: 'whatever'
        * Note that ``a.defaultkeys()`` does NOT contain 'def_field'

        if we do ``a.def_field = None``, then the behavior becomes

        * ``a.get('def_field')``: None
        * ``a.get('def_field','whatever')``: None
        * Note that ``a.defaultkeys()`` DOES contain 'def_field'

        See if we want that setting a default field to None means deleting it.
    """

    _default_fields: tuple[str, ...] = tuple()

    def validate(self) -> None:
        """Validate the keys, if any ``validate_*`` method is available."""
        for key in self.get_default_fields():
            # I get the attribute starting with validate_ and containing the name of the key
            # I set a dummy function if there is no validate_KEY function defined
            validator = getattr(self, f'validate_{key}', lambda value: None)
            if callable(validator):
                try:
                    validator(self[key])
                except Exception as exc:
                    raise exceptions.ValidationError(f"Invalid value for key '{key}' [{exc.__class__.__name__}]: {exc}")

    def __setattr__(self, attr: str, value: Any) -> None:
        """Overridden to allow direct access to fields with underscore."""
        if attr.startswith('_'):
            object.__setattr__(self, attr, value)
        else:
            super().__setattr__(attr, value)

    def __getitem__(self, key: str) -> Any | None:
        """Return None instead of raising an exception if the key does not exist
        but is in the list of default fields.
        """
        try:
            return super().__getitem__(key)
        except KeyError:
            if key in self._default_fields:
                return None
            raise

    @classmethod
    def get_default_fields(cls) -> list[str]:
        """Return the list of default fields, either defined in the instance or not."""
        return list(cls._default_fields)

    def defaultkeys(self) -> list[str]:
        """Return the default keys defined in the instance."""
        return [_ for _ in self.keys() if _ in self._default_fields]

    def extrakeys(self) -> list[str]:
        """Return the extra keys defined in the instance."""
        return [_ for _ in self.keys() if _ not in self._default_fields]
