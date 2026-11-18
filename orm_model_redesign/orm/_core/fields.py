"""The declaration machinery. Nothing here is public API.

``BaseField`` is the abstract base every declaration derives from, and ``ColumnField`` is the
kind only ``aiida-core`` may declare: the columns are fixed by the storage schema, so a plugin
has none to add. The one kind a plugin *can* declare, ``AttributeField``, lives next door in
``poc.orm.fields``, which is the whole of the public surface.

A ``ColumnField`` also carries what each consuming layer does with it, under a ``cli_`` or
``rest_api_`` prefix. They sit on the declaration rather than in a second mapping per entity
because a layer needs *most* fields -- a round trip that dropped them would not round-trip -- so
naming the few exceptions at the field is less to write than restating the field in a layer's
table. The prefix keeps them decoupled on the way out: ``declaration.cli`` and ``declaration.rest_api`` hand
each layer its own view and neither sees the other's.

An ``AttributeField`` has none of them, and that is the point of D13: a data plugin declares what
it stores and nothing about how anything publishes it. The CLI's field projection is for the setup
entities, which are all columns, and every data node serves the same way over REST. So attributes
publish as they stand, and a plugin cannot say otherwise because there is no keyword to say it
with.

A declaration is a **value**: it states facts about what the backend stores -- the type, the
documentation, the default, and the key it is held under -- and it reads that value back. It has
no opinion about querying, and no opinion about what any layer may do with the value.

Because it is a plain value, it compares and hashes like one, which matters: two declarations from
different classes must not be interchangeable as dictionary keys.

The query-side view of a declaration lives in ``poc.orm._core.qb_fields`` as ``QbField``.
"""

from __future__ import annotations

import abc
import datetime
import types
import typing as t
from collections.abc import Mapping, MutableMapping, MutableSequence, Sequence

from poc.common._core.fields import CliField, RestApiField

__all__ = ('MISSING', 'BaseField', 'ColumnField', 'ImmutableStorable', 'MutableStorable', 'StorableType')

#: What a backend can hold. Containers are the covariant ``Mapping``/``Sequence`` rather than
#: ``dict``/``list``, or invariance would reject ``list[str]``.
Storable: t.TypeAlias = 'Mapping[t.Any, t.Any] | Sequence[t.Any] | str | bool | int | float | None | datetime.datetime'

#: What ``default`` may be: a storable value that is *immutable*, so stating it once on the
#: declaration is safe. Anything mutable belongs in ``default_factory`` instead, and the two
#: annotations together make that choice a type error rather than a convention.
ImmutableStorable: t.TypeAlias = (
    'str | bool | int | float | None | datetime.datetime | tuple[t.Any, ...] | frozenset[t.Any]'
)

#: What ``default_factory`` must produce: a storable value that is *mutable*, and so unsafe to
#: share between entities. Named for mutability rather than for being a container, because that is
#: the reason a factory is needed at all -- ``tuple`` and ``str`` are containers and are perfectly
#: safe stated directly as ``default``.
MutableStorable: t.TypeAlias = 'MutableMapping[t.Any, t.Any] | MutableSequence[t.Any]'

#: The annotation for ``dtype``: a type a backend can store, or a union of them.
#:
#: ``types.UnionType`` is there because ``str | None`` is a union object rather than a ``type``,
#: and a hundred declarations are shaped that way. It is what makes a static checker reject
#: ``AttributeField(SomeClass)`` at the declaration rather than at serialisation -- and it does
#: reject ``SomeClass | None`` too, since the expression's type still names the class.
StorableType: t.TypeAlias = 'type[Storable] | types.UnionType'


class _Missing:
    """Sentinel marking the absence of a default."""

    def __repr__(self) -> str:
        return 'MISSING'


MISSING: t.Final = _Missing()

#: What a layer does with a field it has said nothing about: publish it under its own name.
_CLI_AS_IS: t.Final = CliField()
_REST_AS_IS: t.Final = RestApiField()


class BaseField(abc.ABC):
    """Declaration of a persisted field.

    Declare an :class:`AttributeField` or a :class:`ColumnField`; this class cannot be instantiated,
    so there is no neutral default to fall into.
    """

    __slots__ = ('_doc', '_dtype', '_name', '_validator')

    def __init__(
        self,
        name: str,
        dtype: StorableType,
        doc: str = '',
        *,
        validator: t.Callable[[t.Any], t.Any] | None = None,
    ) -> None:
        if not name.isidentifier():
            msg = f'`{name}` is not a valid python identifier'
            raise ValueError(msg)
        self._name = name
        self._dtype = dtype
        self._doc = doc
        self._validator = validator

    # -- a value ----------------------------------------------------------------------------

    def __eq__(self, other: object) -> bool:
        """Ordinary equality. The query-building `==` lives on ``QbField``, not here."""
        if not isinstance(other, BaseField):
            return NotImplemented
        return (type(self), self._name, self._dtype) == (type(other), other._name, other._dtype)

    def __hash__(self) -> int:
        return hash((type(self), self._name, self._dtype))

    def __repr__(self) -> str:
        return f'{type(self).__name__}({self.backend_key!r}, dtype={self._dtype!r})'

    # -- the facts --------------------------------------------------------------------------

    @property
    def name(self) -> str:
        """The field name, which is also the key the backend holds the value under.

        Stated on the declaration rather than by the key of a mapping that holds it: one of the
        two would otherwise have to be kept in step with the other, and nothing would notice if
        they drifted.
        """
        return self._name

    @property
    def dtype(self) -> t.Any:
        return self._dtype

    @property
    def cli(self) -> CliField:
        """Return how the CLI publishes this field. Published as it stands unless a column."""
        return _CLI_AS_IS

    @property
    def rest_api(self) -> RestApiField:
        """Return how the REST API publishes this field. Published as it stands unless a column."""
        return _REST_AS_IS

    @property
    def validator(self) -> t.Callable[[t.Any], t.Any] | None:
        """Return the check a value of this field must pass, if it has one.

        Optional, and the one piece of *logic* a declaration carries -- D1 otherwise admits only
        facts. It earns the exception by having no other home: a ``PUT`` replaces a stored value
        without going through ``__init__``, so a check written there would never run, and writing
        it once per layer would mean the same rule stated twice and able to drift.

        It raises rather than returning a verdict, and it runs wherever a value enters: every
        layer model wires it in, so a REST ``POST`` and ``PUT`` and a CLI import all get it.
        """
        return self._validator

    @property
    def doc(self) -> str:
        return self._doc

    @property
    @abc.abstractmethod
    def is_attribute(self) -> bool:
        """Whether the backend holds the value in the open attributes namespace."""

    @property
    @abc.abstractmethod
    def backend_key(self) -> str:
        """The key the backend holds the value under."""

    # -- read access ------------------------------------------------------------------------

    @abc.abstractmethod
    def read(self, instance: t.Any) -> t.Any:
        """Return the value the backend holds for this field on ``instance``.

        Declarations are values held in the internal declaration mapping, never under their own names, so
        ``getattr`` does not reach them and every reader goes through here.
        """


class ColumnField(BaseField):
    """A field the backend holds in a column of the table backing the entity.

    The columns are fixed by the storage schema and its migrations, so these belong to the core
    entity classes; a plugin has no column to declare.

    Unlike an attribute, a column has a schema behind it, so its default is a *fact about what the
    backend stores* rather than a decision about what to write -- which is why the two options
    live here and not on the base.
    """

    __slots__ = (
        '_cli_exclude',
        '_cli_name',
        '_default',
        '_default_factory',
        '_rest_api_exclude',
        '_rest_api_name',
        '_rest_api_read_only',
    )

    def __init__(
        self,
        name: str,
        dtype: StorableType,
        doc: str = '',
        *,
        default: ImmutableStorable | _Missing = MISSING,
        default_factory: t.Callable[[], MutableStorable] | None = None,
        cli_name: str | None = None,
        cli_exclude: bool = False,
        rest_api_name: str | None = None,
        rest_api_exclude: bool = False,
        rest_api_read_only: bool = False,
        **kwargs: t.Any,
    ) -> None:
        if default is not MISSING and default_factory is not None:
            msg = 'cannot specify both `default` and `default_factory`'
            raise ValueError(msg)
        super().__init__(name, dtype, doc, **kwargs)
        self._default = default
        self._default_factory = default_factory
        self._cli_name = cli_name
        self._cli_exclude = cli_exclude
        self._rest_api_name = rest_api_name
        self._rest_api_exclude = rest_api_exclude
        self._rest_api_read_only = rest_api_read_only

    @property
    def cli(self) -> CliField:
        """Return how the CLI publishes this column.

        Assembled on access rather than in ``__init__``. A declaration holds the options as the
        plain values they were given, and only the layer that is building a model turns them into
        a view -- so importing the ORM does not construct one of these per field per layer for
        something most callers never look at.
        """
        return CliField(name=self._cli_name, exclude=self._cli_exclude)

    @property
    def rest_api(self) -> RestApiField:
        """Return how the REST API publishes this column. Assembled on access, as ``cli`` is."""
        return RestApiField(
            name=self._rest_api_name,
            exclude=self._rest_api_exclude,
            read_only=self._rest_api_read_only,
        )

    @property
    def default(self) -> ImmutableStorable | _Missing:
        """The value the schema supplies when none is given, where it is immutable."""
        return self._default

    @property
    def default_factory(self) -> t.Callable[[], MutableStorable] | None:
        """The factory a mutable default is built by.

        Paired with ``default`` rather than folded into it. Pydantic would in fact copy a mutable
        default per model instance, so ``default=[]`` is safe where it is *used* -- but the
        declaration itself would hold one list forever and hand every reader an alias into it, and
        a mutable default in a class body reads as a bug whether or not it is one.
        """
        return self._default_factory

    @property
    def is_attribute(self) -> bool:
        return False

    @property
    def backend_key(self) -> str:
        return self._name

    def read(self, instance: t.Any) -> t.Any:
        return getattr(instance.backend_entity, self._name)
