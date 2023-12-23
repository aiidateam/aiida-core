###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Module which provides decorators for AiiDA ORM entity -> DB field mappings."""
from abc import ABCMeta
from copy import deepcopy
from pprint import pformat
from typing import Any, Dict, Iterable, Optional, Sequence, Tuple, Union

__all__ = ('QbAttrField', 'QbField', 'QbFields', 'QbFieldFilters')


class QbField:
    """A field of an ORM entity, accessible via the ``QueryBuilder``"""

    __slots__ = ('_key', '_qb_field', '_doc', '_dtype', '_subscriptable')

    def __init__(
        self,
        key: str,
        qb_field: Optional[str] = None,
        *,
        dtype: Optional[Any] = None,
        doc: str = '',
        subscriptable: bool = False,
    ) -> None:
        """Initialise a ORM entity field, accessible via the ``QueryBuilder``

        :param key: The key of the field on the ORM entity
        :param qb_field: The name of the field in the QueryBuilder, if not equal to ``key``
        :param dtype: The data type of the field. If None, the field is of variable type.
        :param doc: A docstring for the field
        :param subscriptable: If True, a new field can be created by ``field["subkey"]``
        """
        self._key = key
        self._qb_field = qb_field if qb_field is not None else key
        self._doc = doc
        self._dtype = dtype
        self._subscriptable = subscriptable

    @property
    def key(self) -> str:
        return self._key

    @property
    def qb_field(self) -> str:
        return self._qb_field

    @property
    def doc(self) -> str:
        return self._doc

    @property
    def dtype(self) -> Optional[Any]:
        return self._dtype

    @property
    def subscriptable(self) -> bool:
        return self._subscriptable

    def _repr_type(self, value: Any) -> str:
        """Return a string representation of the type of the value"""
        if value == type(None):
            return 'None'
        if isinstance(value, type):
            # basic types like int, str, etc.
            return value.__qualname__
        if hasattr(value, '__origin__') and value.__origin__ == Union:
            return 'typing.Union[' + ','.join(self._repr_type(t) for t in value.__args__) + ']'
        return str(value)

    def __repr__(self) -> str:
        dtype = self._repr_type(self.dtype) if self.dtype else ''
        return (
            f'{self.__class__.__name__}({self.key!r}'
            + (f', {self._qb_field!r}' if self._qb_field != self.key else '')
            + (f', dtype={dtype}' if self.dtype else '')
            + (f', subscriptable={self.subscriptable!r}' if self.subscriptable else '')
            + ')'
        )

    def __str__(self) -> str:
        type_str = (
            '?' if self.dtype is None else (self.dtype.__name__ if isinstance(self.dtype, type) else str(self.dtype))
        )
        type_str = type_str.replace('typing.', '')
        return f"{self.__class__.__name__}({self.qb_field}{'.*' if self.subscriptable else ''}) -> {type_str}"

    def __getitem__(self, key: str) -> 'QbField':
        """Return a new QbField with a nested key."""
        if not self.subscriptable:
            raise IndexError('This field is not subscriptable')
        return self.__class__(f'{self.key}.{key}', f'{self.qb_field}.{key}')

    def __hash__(self):
        return hash((self.key, self.qb_field))

    # methods for creating QueryBuilder filter objects
    # these methods mirror the syntax within SQLAlchemy

    def __eq__(self, value):
        return QbFieldFilters(((self, '==', value),))

    def __ne__(self, value):
        return QbFieldFilters(((self, '!=', value),))

    def __lt__(self, value):
        return QbFieldFilters(((self, '<', value),))

    def __le__(self, value):
        return QbFieldFilters(((self, '<=', value),))

    def __gt__(self, value):
        return QbFieldFilters(((self, '>', value),))

    def __ge__(self, value):
        return QbFieldFilters(((self, '>=', value),))

    def like(self, value: str):
        """Return a filter for only string values matching the wildcard string.

        - The percent sign (`%`) represents zero, one, or multiple characters
        - The underscore sign (`_`) represents one, single character
        """
        if not isinstance(value, str):
            raise TypeError('like must be a string')
        return QbFieldFilters(((self, 'like', value),))

    def ilike(self, value: str):
        """Return a filter for only string values matching the (case-insensitive) wildcard string.

        - The percent sign (`%`) represents zero, one, or multiple characters
        - The underscore sign (`_`) represents one, single character
        """
        if not isinstance(value, str):
            raise TypeError('ilike must be a string')
        return QbFieldFilters(((self, 'ilike', value),))

    def in_(self, value: Iterable[Any]):
        """Return a filter for only values in the list"""
        try:
            value = set(value)
        except TypeError:
            raise TypeError('in_ must be iterable')
        return QbFieldFilters(((self, 'in', value),))

    def not_in(self, value: Iterable[Any]):
        """Return a filter for only values not in the list"""
        try:
            value = set(value)
        except TypeError:
            raise TypeError('in_ must be iterable')
        return QbFieldFilters(((self, '!in', value),))

    # JSONB only, we should only show these if the field is a JSONB field

    # def contains(self, value):
    #     """Return a filter for only values containing these items"""
    #     return QbFieldFilters(((self, 'contains', value),))

    # def has_key(self, value):
    #     """Return a filter for only values with these keys"""
    #     return QbFieldFilters(((self, 'has_key', value),))

    # def of_length(self, value: int):
    #     """Return a filter for only array values of this length."""
    #     if not isinstance(value, int):
    #         raise TypeError('of_length must be an integer')
    #     return QbFieldFilters(((self, 'of_length', value),))

    # def longer(self, value: int):
    #     """Return a filter for only array values longer than this length."""
    #     if not isinstance(value, int):
    #         raise TypeError('longer must be an integer')
    #     return QbFieldFilters(((self, 'longer', value),))

    # def shorter(self, value: int):
    #     """Return a filter for only array values shorter than this length."""
    #     if not isinstance(value, int):
    #         raise TypeError('shorter must be an integer')
    #     return QbFieldFilters(((self, 'shorter', value),))


class QbAttrField(QbField):
    """An attribute field of an ORM entity, accessible via the ``QueryBuilder``"""

    @property
    def qb_field(self) -> str:
        return f'attributes.{self._qb_field}'


class QbFieldFilters:
    """An representation of a list of fields and their comparators."""

    __slots__ = ('filters',)

    def __init__(self, filters: Sequence[Tuple[QbField, str, Any]]):
        self.filters = list(filters)

    def __repr__(self) -> str:
        return f'QbFieldFilters({self.filters})'

    def as_dict(self) -> Dict[QbField, Any]:
        """Return the filters as a dictionary, for use in the QueryBuilder."""
        output: Dict[QbField, Any] = {}
        for field, comparator, value in self.filters:
            if field in output:
                output[field]['and'].append({comparator: value})
            else:
                output[field] = {'and': [{comparator: value}]}
        return output

    def __and__(self, other: 'QbFieldFilters') -> 'QbFieldFilters':
        """Concatenate two QbFieldFilters objects: ``a & b``."""
        if not isinstance(other, QbFieldFilters):
            raise TypeError(f'Cannot add QbFieldFilters and {type(other)}')
        return QbFieldFilters(self.filters + other.filters)


class QbFields:
    """A readonly class for mapping attributes to database fields of an AiiDA entity."""

    __isabstractmethod__ = False

    def __init__(self, fields: Optional[Dict[str, QbField]] = None):
        self._fields = fields or {}

    def __repr__(self) -> str:
        return pformat({key: str(value) for key, value in self._fields.items()})

    def __str__(self) -> str:
        return str({key: str(value) for key, value in self._fields.items()})

    def __getitem__(self, key: str) -> QbField:
        """Return an QbField by key."""
        return self._fields[key]

    def __getattr__(self, key: str) -> QbField:
        """Return an QbField by key."""
        try:
            return self._fields[key]
        except KeyError:
            raise AttributeError(key)

    def __contains__(self, key: str) -> bool:
        """Return if the field key exists"""
        return key in self._fields

    def __len__(self) -> int:
        """Return the number of fields"""
        return len(self._fields)

    def __iter__(self):
        """Iterate through the field keys"""
        return iter(self._fields)

    def __dir__(self):
        """Return keys for tab competion."""
        return list(self._fields) + ['_dict']

    @property
    def _dict(self):
        """Return a copy of the internal mapping"""
        return deepcopy(self._fields)


class EntityFieldMeta(ABCMeta):
    """A metaclass for entity fields, which adds a `fields` class attribute."""

    def __init__(cls, name, bases, classdict):
        super().__init__(name, bases, classdict)

        # only allow an existing fields attribute if has been generated from a subclass
        current_fields = getattr(cls, 'fields', None)
        if current_fields is not None and not isinstance(current_fields, QbFields):
            raise ValueError(f"class '{cls}' already has a `fields` attribute set")

        # Find all fields
        fields = {}
        # Note: inspect.getmembers causes loading of AiiDA to fail
        for key, attr in ((key, attr) for subcls in reversed(cls.__mro__) for key, attr in subcls.__dict__.items()):
            # __qb_fields__ should be a list of QbField instances
            if key == '__qb_fields__':
                assert isinstance(
                    attr, Sequence
                ), f"class '{cls}' has a '__qb_fields__' attribute, but it is not a sequence"
                for field in attr:
                    if not isinstance(field, QbField):
                        raise ValueError(f"__qb_fields__ attribute of class '{cls}' must be list of QbField instances")
                    fields[field.key] = field

        cls.fields = QbFields({key: fields[key] for key in sorted(fields)})
