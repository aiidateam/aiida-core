"""The query-side view of a declaration. Mirrors ``aiida.orm.fields``, renamed.

The module name is the one proposal here: everything in it is ``Qb``-prefixed, and ``fields``
does not say so -- particularly once ``fields`` sits beside it holding declarations that are
also, in every ordinary sense, fields.

Nothing else in this module is new. ``QbField``, ``QbAttributesField``, ``QbFieldFilters`` and
``QbFields`` keep the names and the behaviour they have in ``aiida.orm.fields`` -- the refactor
does not touch the query layer, it only changes *what* ``QbFields`` holds and where a query field
comes from.

The two differences from the shipped module, both consequences of decisions recorded in the README:

* the seven-class ``QbField`` hierarchy is one class consulting :func:`operators_for`, so the type
  selects the operators through a table rather than through inheritance;
* a ``QbField`` *wraps* a :class:`~poc.orm.fields.BaseField` instead of being one, which is
  what lets the declaration stay an ordinary value with an ordinary ``==``.

``QbFieldFilters`` is reproduced as it stands, minus its ``singledispatchmethod`` dispatch, which
is spelled with ``isinstance`` here to keep the walkthrough readable.
"""

from __future__ import annotations

import datetime
import typing as t
from collections.abc import Mapping, Sequence
from copy import deepcopy
from pprint import pformat

if t.TYPE_CHECKING:
    from poc.orm._core.fields import BaseField

__all__ = ('QbAttributesField', 'QbField', 'QbFieldFilters', 'QbFields')

_ORDERED_TYPES: t.Final = (int, float, datetime.datetime)
_TEXT_TYPES: t.Final = (str, t.Literal)
_SEQUENCE_TYPES: t.Final = (list, tuple, Sequence)


def root_type(dtype: t.Any) -> t.Any:
    """Resolve the primitive root of an annotation.

    >>> root_type(list[str]) -> list
    >>> root_type(str | None) -> str
    """
    origin = t.get_origin(dtype)
    if origin is None:
        return dtype
    if origin is t.Union:
        return root_type(t.get_args(dtype)[0])
    return origin


def operators_for(dtype: t.Any) -> frozenset[str]:
    """Return the operator groups a value of this type admits.

    This is the ``QbNumericField`` / ``QbStrField`` / ... hierarchy as a table: the groups a type
    admits used to be decided by which subclass ``add_field`` returned.

    A deliberately open type admits everything except the boolean operators, which need a value
    the backend stores as ``True``.

    .. note:: The table is a judgement call, not a fact about the backend. It currently refuses
        ``<`` on a text field, although the backend orders strings perfectly well -- inherited
        from the ``QbStrField`` it replaces, and worth revisiting.
    """
    root = root_type(dtype)
    if root is bool:
        return frozenset({'boolean'})
    if root in _ORDERED_TYPES:
        return frozenset({'ordering'})
    if root in _SEQUENCE_TYPES:
        return frozenset({'array'})
    if root in _TEXT_TYPES:
        return frozenset({'text'})
    if root is dict:
        return frozenset({'mapping'})
    return frozenset({'ordering', 'text', 'array', 'mapping'})


class QbField:
    """The query field for a declaration: its key, and the operators its type admits."""

    __slots__ = ('_backend_key', '_dtype', '_key', '_operators', '_spec')

    def __init__(self, key: str, backend_key: str, dtype: t.Any, declaration: BaseField | None = None) -> None:
        self._key = key
        self._backend_key = backend_key
        self._dtype = dtype
        self._operators = operators_for(dtype)
        self._spec = declaration

    @classmethod
    def from_spec(cls, declaration: BaseField) -> QbField:
        """Build the query field for a declaration."""
        return cls(declaration.name, declaration.backend_key, declaration.dtype, declaration)

    @property
    def key(self) -> str:
        return self._key

    @property
    def backend_key(self) -> str:
        return self._backend_key

    @property
    def dtype(self) -> t.Any:
        return self._dtype

    @property
    def declaration(self) -> BaseField | None:
        """The declaration this field queries, if it has one; nested keys do not."""
        return self._spec

    def _require(self, group: str, operator: str) -> None:
        """Reject an operator the declared type does not admit.

        :raises TypeError: so a nonsense comparison fails here rather than becoming a filter that
            silently matches nothing.
        """
        if group not in self._operators:
            msg = f'`{operator}` is not supported by field `{self._key}` of type `{self._dtype}`'
            raise TypeError(msg)

    def _filter(self, operator: str, value: t.Any) -> QbFieldFilters:
        return QbFieldFilters(((self, operator, value),))

    def __eq__(self, value: t.Any) -> QbFieldFilters:  # type: ignore[override]
        return self._filter('==', value)

    def __ne__(self, value: t.Any) -> QbFieldFilters:  # type: ignore[override]
        return self._filter('!==', value)

    def __lt__(self, value: t.Any) -> QbFieldFilters:
        self._require('ordering', '<')
        return self._filter('<', value)

    def __gt__(self, value: t.Any) -> QbFieldFilters:
        self._require('ordering', '>')
        return self._filter('>', value)

    def __hash__(self) -> int:
        return hash((self._key, self._backend_key))

    def like(self, value: str) -> QbFieldFilters:
        self._require('text', 'like')
        return self._filter('like', value)

    def contains(self, value: t.Any) -> QbFieldFilters:
        self._require('array', 'contains')
        return self._filter('contains', value)

    def has_key(self, value: str) -> QbFieldFilters:
        self._require('mapping', 'has_key')
        return self._filter('has_key', value)

    def as_filter(self) -> QbFieldFilters:
        self._require('boolean', 'as_filter')
        return self._filter('==', True)

    def __invert__(self) -> QbFieldFilters:
        self._require('boolean', '~')
        return self._filter('!==', True)

    def __and__(self, other: t.Any) -> QbFieldFilters:
        return self.as_filter() & other

    def __rand__(self, other: t.Any) -> QbFieldFilters:
        return other & self.as_filter()

    def __getitem__(self, key: str) -> QbField:
        """Return the query field for a nested key. It has no declaration behind it."""
        self._require('mapping', '[]')
        return QbField(f'{self._key}.{key}', f'{self._backend_key}.{key}', t.Any)

    def __repr__(self) -> str:
        return f'{type(self).__name__}({self._backend_key!r}, dtype={self._dtype!r})'


class QbAttributesField(QbField):
    """The ``attributes`` query field, exposing the fields declared within it.

    Nested lookup resolves to a declared field where one exists, so that
    ``Int.fields.attributes.value is Int.fields.value``, and otherwise falls back to an untyped
    field -- which is how the open keys stay queryable without being declared.
    """

    __slots__ = ('_children',)

    def __init__(self, declaration: BaseField, children: Mapping[str, QbField] | None = None) -> None:
        super().__init__(declaration.name, declaration.backend_key, declaration.dtype, declaration)
        self._children = dict(children or {})

    def with_children(self, children: Mapping[str, QbField]) -> QbAttributesField:
        """Return a copy of this field holding the given declared children."""
        assert self._spec is not None
        return type(self)(self._spec, children)

    def __getattr__(self, key: str) -> QbField:
        # `__slots__` lookups never reach here, so a leading underscore is a genuine miss.
        if key.startswith('_'):
            raise AttributeError(key)
        try:
            return self._children[key]
        except KeyError:
            raise AttributeError(key) from None

    def __getitem__(self, key: str) -> QbField:
        if key in self._children:
            return self._children[key]
        return QbField(key, f'attributes.{key}', t.Any)

    def __dir__(self) -> list[str]:
        return sorted(self._children)


class QbFieldFilters:
    """A representation of a list of fields and their comparators."""

    __slots__ = ('filters',)

    def __init__(self, filters: Sequence[tuple[QbField, str, t.Any]] | dict[str, t.Any]) -> None:
        self.filters: dict[str, t.Any] = {}
        self.add_filters(filters)

    def add_filters(self, filters: Sequence[tuple[QbField, str, t.Any]] | dict[str, t.Any]) -> None:
        if isinstance(filters, dict):
            self.filters.update(filters)
            return
        for field, comparator, value in filters:
            key = field.backend_key
            if key in self.filters:
                self.filters['and'] = [{key: self.filters.pop(key)}, {key: {comparator: value}}]
            else:
                self.filters[key] = {comparator: value}

    def as_dict(self) -> dict[str, t.Any]:
        """Return the filters dictionary."""
        return self.filters

    def items(self) -> t.ItemsView[str, t.Any]:
        """Return an items view of the filters, for use in the ``QueryBuilder``."""
        return self.filters.items()

    def __getitem__(self, key: str) -> t.Any:
        return self.filters[key]

    def __contains__(self, key: str) -> bool:
        return key in self.filters

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, QbFieldFilters):
            msg = f'cannot compare QbFieldFilters to {type(other)}'
            raise TypeError(msg)
        return self.filters == other.filters

    def __and__(self, other: t.Any) -> QbFieldFilters:
        """``a & b`` -> {'and': [`a.filters`, `b.filters`]}."""
        if not isinstance(other, QbFieldFilters):
            # Defer to the right operand, so a boolean field can turn itself into a filter through
            # its reflected operator rather than being special-cased here.
            return NotImplemented
        return self._resolve_redundancy(other, 'and') or QbFieldFilters({'and': [self.filters, other.filters]})

    def __or__(self, other: t.Any) -> QbFieldFilters:
        """``a | b`` -> {'or': [`a.filters`, `b.filters`]}."""
        if not isinstance(other, QbFieldFilters):
            return NotImplemented
        return self._resolve_redundancy(other, 'or') or QbFieldFilters({'or': [self.filters, other.filters]})

    def __invert__(self) -> QbFieldFilters:
        """``~(a > b)`` -> ``a !> b``; ``~(a !> b)`` -> ``a > b``."""
        filters = deepcopy(self.filters)
        for logical, negated in (('and', '!and'), ('or', '!or'), ('!and', 'and'), ('!or', 'or')):
            if logical in filters:
                filters[negated] = filters.pop(logical)
                return QbFieldFilters(filters)
        key, args = next(iter(filters.items()))
        operator, value = next(iter(args.items()))
        filters[key] = {operator[1:] if '!' in operator else f'!{operator}': value}
        return QbFieldFilters(filters)

    def _resolve_redundancy(self, other: QbFieldFilters, logical: str) -> QbFieldFilters | None:
        """Flatten into an existing logical group rather than nesting another one."""
        if other == self:
            return self
        if logical in self.filters:
            self[logical].append(other.filters)
            return self
        if logical in other:
            other[logical].insert(0, self.filters)
            return other
        return None

    def __repr__(self) -> str:
        return f'QbFieldFilters({self.filters})'


class QbFields:
    """A read-only mapping from a name to the query field of an entity."""

    __isabstractmethod__ = False

    def __init__(self, fields: Mapping[str, QbField] | None = None) -> None:
        self._fields: dict[str, QbField] = dict(fields or {})

    def keys(self) -> list[str]:
        """Return the backend keys, sorted; an attribute-backed one is prefixed ``attributes.``."""
        return sorted(field.backend_key for field in self._fields.values())

    def __getitem__(self, key: str) -> QbField:
        return self._fields[key]

    def __getattr__(self, key: str) -> QbField:
        try:
            return self._fields[key]
        except KeyError:
            raise AttributeError(key) from None

    def __contains__(self, key: str) -> bool:
        return key in self._fields

    def __len__(self) -> int:
        return len(self._fields)

    def __iter__(self) -> t.Iterator[str]:
        return iter(self._fields)

    def __dir__(self) -> list[str]:
        """Return the names, for tab completion."""
        return sorted(self._fields)

    def __repr__(self) -> str:
        return pformat({key: repr(value) for key, value in self._fields.items()}, width=500)
