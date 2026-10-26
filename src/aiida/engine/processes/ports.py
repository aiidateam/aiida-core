###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""AiiDA-specific process ports."""

from __future__ import annotations

import dataclasses
import re
import typing as t
import warnings
from collections.abc import Callable, Mapping, Sequence
from types import UnionType

from aiida.common.extendeddicts import AttributesFrozendict
from aiida.common.links import validate_link_label
from aiida.engine.processes.generic import ports
from aiida.engine.processes.generic.ports import breadcrumbs_to_port
from aiida.engine.processes.port_model import _is_a_plain_class, _namespace_value, _without_marks, is_structured
from aiida.orm import Bool, Data, Dict, Float, Int, List, Node, Str, from_aiida_type, to_aiida_type

__all__ = (
    'PORT_NAMESPACE_SEPARATOR',
    'CalcJobOutputPort',
    'InputPort',
    'OutputPort',
    'PortNamespace',
    'PreparedInputs',
    'WithNonDb',
    'WithSerialize',
)

OutputPort = ports.OutputPort

PORT_NAME_MAX_CONSECUTIVE_UNDERSCORES = 1
PORT_NAMESPACE_SEPARATOR = '__'  # The character sequence to represent a nested port namespace in a flat link label


_ValueTree: t.TypeAlias = 'Node | int | float | str | bool | list[_ValueTree] | Mapping[str, _ValueTree] | None'
"""A runtime value tree beside the provenance sources it converted from.

Leaves are scalar Python values, preserved nodes, or lists of either; branches
are mappings. Both trees of a `PreparedInputs` share one shape.
"""


@dataclasses.dataclass(frozen=True)
class PreparedInputs:
    """Runtime values beside the provenance sources they were converted from.

    Both trees share one shape: converting never adds or drops keys, so each
    runtime leaf has its source at the same path.
    """

    runtime: _ValueTree
    sources: _ValueTree


class WithNonDb:
    """A mixin that adds support to a port to flag it should not be stored in the database using the ``non_db`` flag."""

    def __init__(self, *args, **kwargs) -> None:
        self._non_db_explicitly_set: bool = bool('non_db' in kwargs)
        non_db = kwargs.pop('non_db', False)
        super().__init__(*args, **kwargs)
        self._non_db: bool = non_db

    @property
    def non_db_explicitly_set(self) -> bool:
        """Return whether the ``non_db`` keyword was explicitly passed in the construction of the ``InputPort``.

        :return: ``True`` if ``non_db`` was explicitly defined during construction, ``False`` otherwise
        """
        return self._non_db_explicitly_set

    @property
    def non_db(self) -> bool:
        """Return whether the value of this ``InputPort`` should be stored in the database.

        :return: ``True`` if it should be stored, ``False`` otherwise
        """
        return self._non_db

    @non_db.setter
    def non_db(self, non_db: bool) -> None:
        """Set whether the value of this ``InputPort`` should be stored as a ``Data`` in the database."""
        self._non_db_explicitly_set = True
        self._non_db = non_db


class WithMetadata:
    """A mixin that allows an input port to be marked as metadata through the keyword ``is_metadata``.

    A metadata input differs from a normal input as in that it is not linked to the ``ProcessNode`` as a ``Data`` node
    but rather is stored on the ``ProcessNode`` itself (as an attribute, for example).
    """

    def __init__(self, *args, **kwargs) -> None:
        self._explicitly_set: bool = bool('is_metadata' in kwargs)
        is_metadata = kwargs.pop('is_metadata', False)
        super().__init__(*args, **kwargs)
        self._is_metadata: bool = is_metadata

    @property
    def is_metadata_explicitly_set(self) -> bool:
        """Return whether the ``is_metadata`` keyword was explicitly passed in the construction of the ``InputPort``.

        :return: ``True`` if ``is_metadata`` was explicitly defined during construction, ``False`` otherwise
        """
        return self._explicitly_set

    @property
    def is_metadata(self) -> bool:
        """Return whether the value of this ``InputPort`` should be stored as a ``Node`` in the database.

        :return: ``True`` if it should be storable as a ``Node``, ``False`` otherwise
        """
        return self._is_metadata

    @is_metadata.setter
    def is_metadata(self, is_metadata: bool) -> None:
        """Set whether the value of this ``InputPort`` should be stored as a ``Node`` in the database.

        :param is_metadata: ``False`` if the port value should be linked as a ``Node``, ``True`` otherwise.
        """
        self._explicitly_set = True
        self._is_metadata = is_metadata


class WithSerialize:
    """A mixin that adds support for a serialization function which is automatically applied on inputs
    that are not AiiDA data types.
    """

    def __init__(self, *args, **kwargs) -> None:
        serializer = kwargs.pop('serializer', None)
        super().__init__(*args, **kwargs)
        self._serializer: Callable[[t.Any], Data] | None = serializer

    @property
    def serializer(self) -> Callable[[t.Any], Data] | None:
        """Return the serializer."""
        return self._serializer

    def serialize(self, value: t.Any) -> Data:
        """Serialize the given value, unless it is ``None``, already a Data type, or no serializer function is defined.

        :param value: the value to be serialized
        :returns: a serialized version of the value or the unchanged value
        """
        if self._serializer is None or value is None or isinstance(value, Data):
            return value

        return self._serializer(value)


class InputPort(WithMetadata, WithSerialize, WithNonDb, ports.InputPort):
    """Subclass of :class:`aiida.engine.processes.generic.ports.InputPort` with serialization and non-database support.

    Values can be serialized automatically to database-storable types, while inputs can also be marked as non-storable.

    The mixins have to go before the main port class in the superclass order to make sure they have the chance to
    process their specific keywords.
    """

    def __init__(self, *args, **kwargs) -> None:
        """Override the constructor to check the type of the default if set and warn if not immutable."""
        if 'default' in kwargs:
            default = kwargs['default']
            # If the default is specified and it is a node instance, raise a warning. This is to try and prevent that
            # people set node instances as defaults which can cause various problems.
            if default is not ports.UNSPECIFIED and isinstance(default, Node):
                message = (
                    f'default of input port `{args[0]}` is a `Node` instance, '
                    'which can lead to unexpected side effects.'
                    ' It is advised to use a lambda instead, e.g.: `default=lambda: orm.Int(5)`.'
                )
                warnings.warn(UserWarning(message))

        # If the port is not required and defines ``valid_type``, automatically add ``None`` as a valid type
        valid_type = kwargs.get('valid_type', ())

        if not isinstance(valid_type, (tuple, list)):
            valid_type = [valid_type]

        if not kwargs.get('required', True) and valid_type and type(None) not in valid_type:
            kwargs['valid_type'] = tuple(valid_type) + (type(None),)

        if isinstance(kwargs.get('valid_type'), tuple):
            kwargs['valid_type'] = tuple(dict.fromkeys(kwargs['valid_type']))

        super().__init__(*args, **kwargs)

    def prepare(self, value: t.Any) -> PreparedInputs:
        """Convert a filled input to its runtime type without coercing unrelated values.

        :param value: the incoming input value.
        :return: the runtime value beside its provenance source.
        """
        if self.valid_type is None:
            runtime = self.serialize(value)
        else:
            runtime = _runtime_value(self.valid_type, value, self.serialize)
        return PreparedInputs(runtime, value if isinstance(value, Node) else runtime)

    def get_description(self) -> dict[str, str]:
        """Return a description of the InputPort, which will be a dictionary of its attributes

        :returns: a dictionary of the stringified InputPort attributes
        """
        description = super().get_description()
        description['is_metadata'] = f'{self.is_metadata}'
        description['non_db'] = f'{self.non_db}'

        return description


class CalcJobOutputPort(ports.OutputPort):
    """Output port for calcjobs that adds the ``_pass_to_parser`` attribute."""

    def __init__(self, *args, **kwargs) -> None:
        pass_to_parser = kwargs.pop('pass_to_parser', False)
        super().__init__(*args, **kwargs)
        self._pass_to_parser: bool = pass_to_parser

    @property
    def pass_to_parser(self) -> bool:
        return self._pass_to_parser


class PortNamespace(WithMetadata, WithNonDb, ports.PortNamespace):
    """Subclass of :class:`aiida.engine.processes.generic.ports.PortNamespace` supporting automatic recursive
    serialization of a given mapping onto the ports of the PortNamespace.
    """

    def __setitem__(self, key: str, port: ports.Port) -> None:
        """Ensure that a `Port` being added inherits the `non_db` attribute if not explicitly defined at construction.

        The reasoning is that if a `PortNamespace` has `non_db=True`, which is different from the default value, very
        often all leaves should be also `non_db=True`. To prevent a user from having to specify it manually everytime
        we overload the value here, unless it was specifically set during construction.

        Note that the `non_db` attribute is not present for all `Port` sub classes so we have to check for it first.
        """
        if not isinstance(port, ports.Port):
            raise TypeError('port needs to be an instance of Port')

        self.validate_port_name(key)

        if hasattr(port, 'is_metadata_explicitly_set') and not port.is_metadata_explicitly_set:
            port.is_metadata = self.is_metadata  # type: ignore[attr-defined]

        if hasattr(port, 'non_db_explicitly_set') and not port.non_db_explicitly_set:
            port.non_db = self.non_db  # type: ignore[attr-defined]

        # If the port is not metadata (signified by ``is_metadata`` and ``non_db`` being ``False`` if defined) and it
        # does not already define a serializer, set the default serializer to ``to_aiida_type``.
        if (
            ((hasattr(port, 'is_metadata') and not port.is_metadata) and (hasattr(port, 'non_db') and not port.non_db))
            and hasattr(port, 'serializer')
            and port.serializer is None
        ):
            port._serializer = to_aiida_type  # type: ignore[attr-defined]

        super().__setitem__(key, port)

    @staticmethod
    def validate_port_name(port_name: str) -> None:
        """Validate the given port name.

        Valid port names adhere to the following restrictions:

            * Is a valid link label (see below)
            * Does not contain two or more consecutive underscores

        Valid link labels adhere to the following restrictions:

            * Has to be a valid python identifier
            * Can only contain alphanumeric characters and underscores
            * Can not start or end with an underscore

        :param port_name: the proposed name of the port to be added
        :raise TypeError: if the port name is not a string type
        :raise ValueError: if the port name is invalid
        """
        try:
            validate_link_label(port_name)
        except ValueError as exception:
            msg = f'invalid port name `{port_name}`: {exception}'
            raise ValueError(msg)

        # Following regexes will match all groups of consecutive underscores where each group will be of the form
        # `('___', '_')`, where the first element is the matched group of consecutive underscores.
        consecutive_underscores = [match[0] for match in re.findall(r'((_)\2+)', port_name)]

        if any(len(entry) > PORT_NAME_MAX_CONSECUTIVE_UNDERSCORES for entry in consecutive_underscores):
            msg = f'invalid port name `{port_name}`: more than two consecutive underscores'
            raise ValueError(msg)

    def _passes_through(self, item: t.Any) -> bool:
        """Return whether a dynamic leaf skips provenance serialization."""
        return item is None or self.valid_type is None or self.is_metadata or self.non_db

    def _as_mapping(self, value: t.Any) -> Mapping[str, t.Any]:
        """Return model instances as mappings, rejecting other non-mappings."""
        value = _namespace_value(value)
        if not isinstance(value, Mapping):
            msg = f'port namespace `{self.name}` received `{type(value)}` instead of a dictionary'
            raise TypeError(msg)
        return value

    def pre_process(self, port_values: t.Any) -> AttributesFrozendict:
        """Accept model instances as namespace mappings before applying defaults."""
        return super().pre_process(dict(self._as_mapping(port_values)))

    def prepare(self, mapping: Mapping[str, t.Any]) -> PreparedInputs:
        """Convert filled inputs to runtime values, keeping sources for provenance.

        Filling (defaults, shape checks, missing aggregation) happens before
        this step, in `PortNamespace.pre_process` or the graph input resolver.

        :param mapping: inputs with defaults already applied.
        :return: the runtime inputs beside their provenance sources.
        """
        mapping = self._as_mapping(mapping)

        def dynamic(value: t.Any) -> t.Any:
            value = _namespace_value(value)
            if isinstance(value, Mapping):
                return {key: dynamic(item) for key, item in value.items()}
            return _runtime_value(self.valid_type, value)

        runtime: dict[str, t.Any] = {}
        sources: dict[str, t.Any] = {}
        for name, value in mapping.items():
            if name in self:
                port = self[name]
                if not isinstance(port, (InputPort, PortNamespace)):
                    msg = f'unknown port type for input `{name}`.'
                    raise TypeError(msg)
                resolved = port.prepare(value)
                runtime[name] = resolved.runtime
                sources[name] = resolved.sources
            else:
                runtime[name] = dynamic(value)
                sources[name] = _source_tree(value, runtime[name])
        return PreparedInputs(AttributesFrozendict(runtime), AttributesFrozendict(sources))

    def serialize(self, mapping: dict[str, t.Any] | None, breadcrumbs: Sequence[str] = ()) -> dict[str, t.Any] | None:
        """Serialize the given mapping onto this `Portnamespace`.

        It will recursively call this function on any nested `PortNamespace` or the serialize function on any `Ports`.

        :param mapping: a mapping of values to be serialized
        :param breadcrumbs: a tuple with the namespaces of parent namespaces
        :returns: the serialized mapping
        """
        if mapping is None:
            return None

        breadcrumbs = (*breadcrumbs, self.name)
        mapping = _namespace_value(mapping)
        if not isinstance(mapping, Mapping):
            port_name = breadcrumbs_to_port(breadcrumbs)
            msg = f'port namespace `{port_name}` received `{type(mapping)}` instead of a dictionary'
            raise TypeError(msg)

        def dynamic(item: t.Any) -> t.Any:
            item = _namespace_value(item)
            if isinstance(item, Mapping):
                return {key: dynamic(leaf) for key, leaf in item.items()}
            if self._passes_through(item):
                return item
            return item if isinstance(item, Node) else to_aiida_type(item)

        result: dict[str, t.Any] = {}

        for name, value in mapping.items():
            if name in self:
                port = self[name]
                if isinstance(port, PortNamespace):
                    result[name] = port.serialize(value, breadcrumbs)
                elif isinstance(port, InputPort):
                    result[name] = port.serialize(value)
                else:
                    msg = f'port does not have a serialize method: {port}'
                    raise TypeError(msg)
            else:
                result[name] = dynamic(value)

        return result


def _is_storable(annotation: t.Any) -> bool:
    """Return whether values of an annotation can reach provenance storage.

    Structured models are stored as namespaces, declared nodes pass through, and plain values store through
    ``to_aiida_type``. Anything else has no storage representation.

    :param annotation: a model field annotation.
    """
    annotation = _without_marks(annotation)
    if annotation is None or annotation is t.Any or annotation is type(None):
        return True
    if is_structured(annotation):
        return True
    # `_is_a_plain_class`, not `isinstance(., type)`: parametrized generics pass the latter on some versions.
    if _is_a_plain_class(annotation):
        return issubclass(annotation, Data) or _has_conversion(annotation)
    return _origin_storable(t.get_origin(annotation), annotation)


def _has_conversion(annotation: type) -> bool:
    """Return whether `to_aiida_type` resolves a real converter for a class."""
    # `dispatch` walks the MRO, so resolving to the `object` registration means no conversion exists.
    return to_aiida_type.dispatch(annotation) is not to_aiida_type.dispatch(object)


def _origin_storable(origin: t.Any, annotation: t.Any) -> bool:
    """Return whether a generic alias stores through its origin or its members."""
    if origin in (list, dict, t.Union, UnionType):
        return all(_is_storable(argument) for argument in t.get_args(annotation))
    return False


def _runtime_value(
    valid_type: type | tuple[type, ...] | None,
    value: t.Any,
    serializer: Callable[[t.Any], t.Any] | None = None,
) -> t.Any:
    """Preserve accepted nodes and unwrap only values matching the runtime declaration."""
    if valid_type is None or isinstance(value, valid_type):
        return value
    if isinstance(value, Data):
        converted = from_aiida_type(value)
        return converted if isinstance(converted, valid_type) else value
    types = valid_type if isinstance(valid_type, tuple) else (valid_type,)
    if serializer is not None and any(issubclass(kind, Node) for kind in types):
        return serializer(value)
    return value


def _infer_node_types(annotation: t.Any) -> tuple[t.Any, ...]:
    """Infer ORM valid types for stored declarations: legacy function ports and output checks.

    :param annotation: The annotation of a function argument as returned by ``inspect.get_annotation``.
    :returns: A tuple of valid types. If no valid types were defined or they could not be successfully parsed, an empty
        tuple is returned.
    """
    return tuple(kind for declared in _infer_runtime_types(annotation) if (kind := _node_type(declared)) is not None)


def _infer_runtime_types(annotation: t.Any) -> tuple[t.Any, ...]:
    """Infer Python valid types for runtime declarations: graph inputs declare what tasks consume.

    :param annotation: The annotation of a function argument as returned by ``inspect.get_annotation``.
    :returns: A tuple of valid types. If no valid types were defined or they could not be successfully parsed, an empty
        tuple is returned.
    """
    annotation = _without_marks(annotation)
    origin = t.get_origin(annotation)
    inferred: tuple[t.Any, ...] = ()

    if _is_a_plain_class(annotation) or origin in (list, dict):
        inferred = (_runtime_type(annotation),)
    elif origin is t.Union or origin is UnionType:
        inferred = tuple(_runtime_type(item) for item in t.get_args(annotation))

    return tuple(kind for kind in inferred if kind is not None)


_VALID_TYPE_MAP: dict[t.Any, t.Any] = {
    bool: Bool,
    dict: Dict,
    t.Dict: Dict,  # noqa: UP006 - support legacy annotation spelling
    float: Float,
    int: Int,
    list: List,
    t.List: List,  # noqa: UP006 - support legacy annotation spelling
    str: Str,
    type(None): type(None),
}


def _node_type(annotation: t.Any) -> t.Any | None:
    """Return the stored type for one annotation, or None when it declares none."""
    if annotation is t.Any:
        return None
    if _is_a_plain_class(annotation):
        return annotation if issubclass(annotation, Data) else _VALID_TYPE_MAP.get(annotation)
    return _VALID_TYPE_MAP.get(annotation)


def _runtime_type(annotation: t.Any) -> t.Any | None:
    """Return the runtime type for one annotation, or None when it declares none."""
    if annotation is t.Any:
        return None
    if t.get_origin(annotation) in (list, dict):
        return t.get_origin(annotation)
    if _is_a_plain_class(annotation):
        return annotation
    return None


def _coerce_model_values(value: t.Any) -> t.Any:
    """Recursively convert ``PortModel`` instances to namespace mappings.

    Declared namespaces hold one port per model field, so a model instance passed as a value reads
    as the mapping of its fields. Centralizing the conversion here keeps every launch boundary
    consistent without duplicating model handling.
    """
    coerced = _namespace_value(value)
    if isinstance(coerced, Mapping):
        return {key: _coerce_model_values(item) for key, item in coerced.items()}
    return coerced


def _source_tree(original: t.Any, runtime: t.Any) -> t.Any:
    """Return the nodes converted values were sourced from, else the converted values.

    A supplied node always survives conversion identically, so the supplied
    side alone decides: a supplied node is its own source.
    """
    if isinstance(original, Node):
        return original
    original = _namespace_value(original)
    if isinstance(original, Mapping) and isinstance(runtime, Mapping):
        return {key: _source_tree(value, runtime[key]) for key, value in original.items() if key in runtime}
    return runtime
