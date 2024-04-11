###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Module which provides decorators for AiiDA ORM entity -> DB field mappings."""

import datetime
import typing as t
from abc import ABCMeta
from copy import deepcopy
from functools import singledispatchmethod
from pprint import pformat

from aiida.common.lang import isidentifier

__all__ = (
    'QbField',
    'QbFieldFilters',
    'QbFields',
)


def extract_root_type(dtype: t.Any) -> t.Any:
    """Recursively search for the primitive root type.

    >>> extract_root_type(List[str]) -> list
    >>> extract_root_type(Optional[List[str]]) -> list
    """
    origin = t.get_origin(dtype)
    if origin:
        if origin is t.Union:
            return extract_root_type(t.get_args(dtype)[0])
        else:
            return origin
    else:
        return dtype


class QbField:
    """A field of an ORM entity, accessible via the ``QueryBuilder``"""

    __slots__ = (
        '_key',
        '_backend_key',
        '_doc',
        '_dtype',
        '_is_attribute',
        '_is_subscriptable',
    )

    def __init__(
        self,
        key: str,
        alias: t.Optional[str] = None,
        *,
        dtype: t.Optional[t.Any] = None,
        doc: str = '',
        is_attribute: bool = True,
        is_subscriptable: bool = False,
    ) -> None:
        """Initialise a ORM entity field, accessible via the ``QueryBuilder``

        :param key: The key of the field on the ORM entity
        :param alias: The alias in the storage backend for the key, if not equal to ``key``
        :param dtype: The data type of the field. If None, the field is of variable type.
        :param doc: A docstring for the field
        :param is_attribute: If True, the ``backend_key`` property will prepend "attributes." to field name
        :param is_subscriptable: If True, a new field can be created by ``field["subkey"]``
        """
        self._key = key
        self._backend_key = alias if alias is not None else key
        self._doc = doc
        self._dtype = dtype
        self._is_attribute = is_attribute
        self._is_subscriptable = is_subscriptable

    @property
    def key(self) -> str:
        return self._key

    @property
    def backend_key(self) -> str:
        if self._is_attribute:
            return f'attributes.{self._backend_key}'
        return self._backend_key

    @property
    def doc(self) -> str:
        return self._doc

    @property
    def dtype(self) -> t.Optional[t.Any]:
        """Return the primitive root type."""
        return extract_root_type(self._dtype)

    @property
    def annotation(self) -> t.Optional[t.Any]:
        """Return the full type annotation."""
        return self._dtype

    @property
    def is_attribute(self) -> bool:
        return self._is_attribute

    @property
    def is_subscriptable(self) -> bool:
        return self._is_subscriptable

    def __repr__(self) -> str:
        type_str = self._get_dtype_as_str() if self._dtype else ''
        return (
            f'{self.__class__.__name__}({self.key!r}'
            + (f', {self._backend_key!r}' if self._backend_key != self.key else '')
            + (f', dtype={type_str}' if self._dtype else '')
            + (f', is_attribute={self.is_attribute}')
            + (f', is_subscriptable={self.is_subscriptable!r}' if self.is_subscriptable else '')
            + ')'
        )

    def __str__(self) -> str:
        class_name = self.__class__.__name__
        field_name = f'{self.backend_key}{".*" if self.is_subscriptable else ""}'
        type_str = self._get_dtype_as_str()
        return f'{class_name}({field_name}) -> {type_str}'

    def __hash__(self):
        return hash((self.key, self.backend_key))

    def __eq__(self, value):
        return QbFieldFilters(((self, '==', value),))

    def __ne__(self, value):
        return QbFieldFilters(((self, '!==', value),))

    def in_(self, value: t.Iterable[t.Any]):
        """Return a filter for only values in the list"""
        try:
            set(value)
        except TypeError:
            raise TypeError('in_ must be iterable')
        return QbFieldFilters(((self, 'in', value),))

    def _get_dtype_as_str(self) -> str:
        """Return field type as processed string.

        >>> None -> ?
        >>> str -> str
        >>> typing.Optional[str] -> Optional[str]
        >>> typing.Dict[typing.List[str]] -> Dict[List[str]]
        """
        if self._dtype:
            if t.get_origin(self._dtype):
                type_str = str(self._dtype).replace('typing.', '')
            else:
                type_str = self._dtype.__name__
        else:
            type_str = '?'
        return type_str

    if t.TYPE_CHECKING:

        def __getitem__(self, key: str) -> 'QbField': ...


class QbNumericField(QbField):
    """A numeric (`int`, `float`, `datetime`) flavor of `QbField`."""

    def __lt__(self, value):
        return QbFieldFilters(((self, '<', value),))

    def __le__(self, value):
        return QbFieldFilters(((self, '<=', value),))

    def __gt__(self, value):
        return QbFieldFilters(((self, '>', value),))

    def __ge__(self, value):
        return QbFieldFilters(((self, '>=', value),))


class QbArrayField(QbField):
    """An array (`list`) flavor of `QbField`."""

    def contains(self, value):
        """Return a filter for only values containing these items"""
        return QbFieldFilters(((self, 'contains', value),))

    def of_length(self, value: int):
        """Return a filter for only array values of this length."""
        if not isinstance(value, int):
            raise TypeError('of_length must be an integer')
        return QbFieldFilters(((self, 'of_length', value),))

    def longer(self, value: int):
        """Return a filter for only array values longer than this length."""
        if not isinstance(value, int):
            raise TypeError('longer must be an integer')
        return QbFieldFilters(((self, 'longer', value),))

    def shorter(self, value: int):
        """Return a filter for only array values shorter than this length."""
        if not isinstance(value, int):
            raise TypeError('shorter must be an integer')
        return QbFieldFilters(((self, 'shorter', value),))


class QbStrField(QbField):
    """A string (`str`) flavor of `QbField`."""

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


class QbDictField(QbField):
    """A dictionary (`dict`) flavor of `QbField`."""

    def has_key(self, value):
        """Return a filter for only values with these keys"""
        return QbFieldFilters(((self, 'has_key', value),))

    def __getitem__(self, key: str) -> 'QbAttrField':
        """Return a new `QbField` with a nested key."""
        if not self.is_subscriptable:
            raise IndexError('This field is not subscriptable')
        return QbAttrField(
            f'{self.key}.{key}',
            f'{self._backend_key}.{key}' if self.is_attribute else None,
            is_attribute=self.is_attribute,
        )


class QbAttrField(QbNumericField, QbArrayField, QbStrField, QbDictField):
    """A generic flavor of `QbField` covering all operations."""

    def of_type(self, value):
        """Return a filter for only values of this type."""
        return QbFieldFilters(((self, 'of_type', value),))


class QbFieldFilters:
    """An representation of a list of fields and their comparators."""

    __slots__ = ('filters',)

    def __init__(
        self,
        filters: t.Union[t.Sequence[t.Tuple[QbField, str, t.Any]], dict],
    ):
        self.filters: t.Dict[str, t.Any] = {}
        self.add_filters(filters)

    def as_dict(self) -> t.Dict[str, t.Any]:
        """Return the filters dictionary."""
        return self.filters

    def items(self):
        """Return an items view of the filters for use in the QueryBuilder."""
        return self.filters.items()

    @singledispatchmethod
    def add_filters(self, filters: dict):
        self.filters.update(filters)

    @add_filters.register(list)
    @add_filters.register(tuple)
    def _(self, filters):
        field: QbField
        for field, comparator, value in filters:
            qb_field = field.backend_key
            if qb_field in self.filters:
                self.filters['and'] = [
                    {qb_field: self.filters.pop(qb_field)},
                    {qb_field: {comparator: value}},
                ]
            else:
                self.filters[qb_field] = {comparator: value}

    def __repr__(self) -> str:
        return f'QbFieldFilters({self.filters})'

    def __getitem__(self, key: str) -> t.Any:
        return self.filters[key]

    def __contains__(self, key: str) -> bool:
        return key in self.filters

    def __eq__(self, other: object) -> bool:
        """``a == b`` checks if `a.filters == b.filters`."""
        if not isinstance(other, QbFieldFilters):
            raise TypeError(f'Cannot compare QbFieldFilters to {type(other)}')
        return self.filters == other.filters

    def __and__(self, other: 'QbFieldFilters') -> 'QbFieldFilters':
        """``a & b`` -> {'and': [`a.filters`, `b.filters`]}."""
        return self._resolve_redundancy(other, 'and') or QbFieldFilters({'and': [self.filters, other.filters]})

    def __or__(self, other: 'QbFieldFilters') -> 'QbFieldFilters':
        """``a | b`` -> {'or': [`a.filters`, `b.filters`]}."""
        return self._resolve_redundancy(other, 'or') or QbFieldFilters({'or': [self.filters, other.filters]})

    def __invert__(self) -> 'QbFieldFilters':
        """~(a > b) -> a !> b; ~(a !> b) -> a > b"""
        filters = deepcopy(self.filters)
        if 'and' in filters:
            filters['!and'] = filters.pop('and')
        elif 'or' in filters:
            filters['!or'] = filters.pop('or')
        elif '!and' in filters:
            filters['and'] = filters.pop('!and')
        elif '!or' in filters:
            filters['or'] = filters.pop('!or')
        else:
            key, args = next(iter(filters.items()))
            operator, value = next(iter(args.items()))
            operator = operator[1:] if '!' in operator else f'!{operator}'
            filters[key] = {operator: value}
        return QbFieldFilters(filters)

    def _resolve_redundancy(self, other: 'QbFieldFilters', logical: str) -> t.Optional['QbFieldFilters']:
        """Resolve redundant filters and nested logical operators."""

        if not isinstance(other, QbFieldFilters):
            raise TypeError(f'Cannot combine QbFieldFilters and {type(other)}')

        # same filters
        if other == self:
            return self

        # self is already wrapped in `logical`
        # append other to self
        if logical in self.filters:
            self[logical].append(other.filters)
            return self

        # other is already wrapped in `logical`
        # insert self in other
        if logical in other:
            other[logical].insert(0, self.filters)
            return other

        return None


class QbFields:
    """A readonly class for mapping attributes to database fields of an AiiDA entity."""

    __isabstractmethod__ = False

    def __init__(self, fields: t.Optional[t.Dict[str, QbField]] = None):
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
                    attr, t.Sequence
                ), f"class '{cls}' has a '__qb_fields__' attribute, but it is not a sequence"
                for field in attr:
                    if not isinstance(field, QbField):
                        raise ValueError(f"__qb_fields__ attribute of class '{cls}' must be list of QbField instances")
                    if field.key == 'value':
                        if dtype := getattr(cls, '_type', None):
                            value_field = add_field(
                                'value',
                                dtype=dtype,
                                doc='The value of the data',
                            )

                            fields[field.key] = value_field
                    else:
                        fields[field.key] = field

        cls.fields = QbFields({key: fields[key] for key in sorted(fields)})


class QbFieldArguments(t.TypedDict):
    key: str
    alias: t.Optional[str]
    dtype: t.Optional[t.Any]
    doc: str
    is_attribute: bool
    is_subscriptable: bool


def add_field(
    key: str,
    alias: t.Optional[str] = None,
    *,
    dtype: t.Optional[t.Any] = None,
    doc: str = '',
    is_attribute: bool = True,
    is_subscriptable: bool = False,
) -> QbField:
    """Add a `dtype`-dependent `QbField` representation of a field.

    :param key: The key of the field on the ORM entity
    :param alias: The alias in the storage backend for the key, if not equal to ``key``
    :param dtype: The data type of the field. If None, the field is of variable type.
    :param doc: A docstring for the field
    :param is_attribute: If True, the ``backend_key`` property will prepend "attributes." to field name
    :param is_subscriptable: If True, a new field can be created by ``field["subkey"]``
    """
    kwargs: QbFieldArguments = {
        'key': key,
        'alias': alias,
        'dtype': dtype,
        'doc': doc,
        'is_attribute': is_attribute,
        'is_subscriptable': is_subscriptable,
    }
    if not isidentifier(key):
        raise ValueError(f'{key} is not a valid python identifier')
    if not is_attribute and alias:
        raise ValueError('only attribute fields may be aliased')
    if not dtype:
        return QbField(**kwargs)
    root_type = extract_root_type(dtype)
    if root_type in (int, float, datetime.datetime):
        return QbNumericField(**kwargs)
    elif root_type is list:
        return QbArrayField(**kwargs)
    elif root_type is str:
        return QbStrField(**kwargs)
    elif root_type is dict:
        return QbDictField(**kwargs)
    else:
        return QbField(**kwargs)
