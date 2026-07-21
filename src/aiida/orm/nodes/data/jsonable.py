"""Data plugin that allows to easily wrap objects that are JSON-able."""

from __future__ import annotations

import dataclasses
import importlib
import json
import typing

import numpy as np
from pydantic import BaseModel, ConfigDict, WithJsonSchema

from aiida.orm.pydantic import OrmFieldsAsModelDump, OrmMetadataField, OrmModel

from .data import Data

__all__ = ('JsonableData',)


@typing.runtime_checkable
class JsonSerializableProtocol(typing.Protocol):
    def as_dict(self) -> typing.MutableMapping[typing.Any, typing.Any]: ...


class JsonableData(Data):
    """Data plugin that allows to easily wrap objects that are JSON-able.

    Any class that implements the ``as_dict`` method, returning a dictionary that is a JSON serializable representation
    of the object, can be wrapped and stored by this data plugin.

    As an example, take the ``Molecule`` class of the ``pymatgen`` library, which respects the spec described above. To
    store an instance as a ``JsonableData`` simply pass an instance as an argument to the constructor as follows::

        from pymatgen.core import Molecule
        molecule = Molecule(['H'], [0, 0, 0])
        node = JsonableData(molecule)
        node.store()

    Since ``Molecule.as_dict`` returns a dictionary that is JSON-serializable, the data plugin will call it and store
    the dictionary as the attributes of the ``JsonableData`` node in the database.

    .. note:: A JSON-serializable dictionary means a dictionary that when passed to ``json.dumps`` does not except but
        produces a valid JSON string representation of the dictionary.

    If the wrapped class implements a class-method ``from_dict``, the wrapped instance can easily be recovered from a
    previously stored node that was optionally loaded from the database. The ``from_dict`` method should simply accept
    a single argument which is the dictionary that is returned by the ``as_dict`` method. If this criteria is satisfied,
    an instance wrapped and stored in a ``JsonableData`` node can be recovered through the ``obj`` property::

        loaded = load_node(node.pk)
        molecule = loaded.obj

    Of course, this requires that the class of the originally wrapped instance can be imported in the current
    environment, or an ``ImportError`` will be raised.

    Besides the ``as_dict`` / ``from_dict`` contract above, the wrapper also accepts objects whose dictionary is
    produced by ``to_dict`` / ``todict`` / ``asdict``, as well as :func:`dataclasses.dataclass` instances and
    ``pydantic.BaseModel`` instances (reconstructed with the constructor and ``model_validate`` respectively). Numpy
    scalars and arrays returned in the dictionary are coerced to their JSON-native counterparts. This broader support
    is what lets it act as the generic fallback for arbitrary-Python-value serialization; the ``as_dict`` /
    ``from_dict`` path is unchanged.
    """

    class AttributesModel(OrmFieldsAsModelDump, Data.AttributesModel):
        model_config = ConfigDict(
            arbitrary_types_allowed=True,
            extra='allow',
        )

        the_module: str = OrmMetadataField(
            title='Module name',
            alias='@module',
            description='The module name of the wrapped object',
            orm_to_model=lambda node: typing.cast(JsonableData, node).the_module,
        )
        the_class: str = OrmMetadataField(
            title='Class name',
            alias='@class',
            description='The class name of the wrapped object',
            orm_to_model=lambda node: typing.cast(JsonableData, node).the_class,
        )

    class ConstructorArgsModel(OrmModel):
        model_config = ConfigDict(arbitrary_types_allowed=True)

        obj: typing.Annotated[
            JsonSerializableProtocol,
            WithJsonSchema(
                {
                    'type': 'object',
                    'title': 'JSON-serializable object',
                    'description': 'The JSON-serializable object',
                }
            ),
            OrmMetadataField(
                description='The JSON-serializable object',
                write_only=True,
            ),
        ]

    #: Method names, tried in order, that an object may implement to produce its serializable dictionary. ``as_dict``
    #: (the historical, MSONable-style contract) is tried first so existing behaviour is unchanged.
    _DICT_METHODS = ('as_dict', 'to_dict', 'todict', 'asdict')

    #: Class-method names, tried in order, that a class may implement to rebuild an instance from its dictionary.
    _FROM_DICT_METHODS = ('from_dict', 'fromdict')

    def __init__(self, obj: JsonSerializableProtocol, *args, **kwargs):
        """Construct the node for the to be wrapped object."""
        if obj is None:
            raise TypeError('the `obj` argument cannot be `None`.')

        dictionary = self._extract_dict(obj)

        super().__init__(*args, **kwargs)

        self._obj = obj

        dictionary.setdefault('@class', obj.__class__.__name__)
        dictionary.setdefault('@module', obj.__class__.__module__)

        # Coerce numpy scalars and arrays that ``as_dict`` may return into JSON-native types before the round-trip.
        dictionary = self._make_jsonable(dictionary)

        # Even though the dictionary returned by ``as_dict`` should be JSON-serializable and therefore this should be
        # sufficient to be able to generate a JSON representation and thus store it in the database, there is a
        # difference in the JSON serializers used by Python's ``json`` module and those of the PostgreSQL database that
        # is used for the database backend. Python's ``json`` module automatically serializes the ``inf`` and ``nan``
        # float constants to the Javascript equivalent strings, however, PostgreSQL does not. If we were to pass the
        # dictionary from ``as_dict`` straight to the attributes and it were to contain any of these floats, the storing
        # of the node would fail, even though technically it is JSON-serializable using the default Python module. To
        # work around this asymmetry, we perform a serialization round-trip with the ``JsonEncoder`` and ``JsonDecoder``
        # where in the deserialization, the encoded float constants are not deserialized, but instead the string
        # placeholders are kept. This now ensures that the full dictionary will be serializable by PostgreSQL.
        try:
            serialized = json.loads(json.dumps(dictionary), parse_constant=lambda x: x)
        except TypeError as exc:
            raise TypeError(f'the object `{obj}` is not JSON-serializable and therefore cannot be stored.') from exc

        self.base.attributes.set_many(serialized)

    def _extract_dict(self, obj: typing.Any) -> dict:
        """Return the serializable dictionary for ``obj``.

        Pydantic models (``model_dump``) and dataclasses (``dataclasses.asdict``) are supported natively; any other
        object must implement one of :attr:`_DICT_METHODS`. Raises ``TypeError`` if none applies.
        """
        if self._is_pydantic_instance(obj):
            return obj.model_dump(exclude_none=False)
        if self._is_dataclass_instance(obj):
            return dataclasses.asdict(obj)
        for method_name in self._DICT_METHODS:
            method = getattr(obj, method_name, None)
            if callable(method):
                return method()
        raise TypeError(
            f'the `obj` argument does not implement any of the supported serialization methods '
            f'({", ".join(self._DICT_METHODS)}), nor is it a dataclass or pydantic model.'
        )

    @classmethod
    def _make_jsonable(cls, data: typing.Any) -> typing.Any:
        """Recursively coerce numpy scalars and arrays in ``data`` into JSON-native types (``ndarray`` to ``list``,
        ``numpy.generic`` to its Python scalar), leaving everything else untouched."""
        if isinstance(data, dict):
            return {key: cls._make_jsonable(value) for key, value in data.items()}
        if isinstance(data, list):
            return [cls._make_jsonable(value) for value in data]
        if isinstance(data, tuple):
            return tuple(cls._make_jsonable(value) for value in data)
        if isinstance(data, np.ndarray):
            return data.tolist()
        if isinstance(data, np.generic):
            return data.item()
        return data

    def _rebuild_object(self, cls_: typing.Any, attributes: dict) -> typing.Any:
        """Reconstruct an instance of ``cls_`` from its stored ``attributes``.

        Pydantic types (``model_validate`` / ``parse_obj``) and dataclasses (constructor) are handled natively; any
        other class is rebuilt through one of :attr:`_FROM_DICT_METHODS`, falling back to the plain constructor.
        """
        if self._is_pydantic_type(cls_):
            if hasattr(cls_, 'model_validate'):
                return cls_.model_validate(attributes)
            if hasattr(cls_, 'parse_obj'):
                return cls_.parse_obj(attributes)
            return cls_(**attributes)
        if self._is_dataclass_type(cls_):
            return cls_(**attributes)
        for method_name in self._FROM_DICT_METHODS:
            from_dict = getattr(cls_, method_name, None)
            if callable(from_dict):
                return from_dict(attributes)
        try:
            return cls_(**attributes)
        except TypeError as exc:
            raise TypeError(
                f'cannot rebuild an object of type `{cls_}`: it implements none of the from-dict methods '
                f'({", ".join(self._FROM_DICT_METHODS)}) and its constructor does not accept the stored attributes.'
            ) from exc

    @staticmethod
    def _is_pydantic_instance(obj: typing.Any) -> bool:
        return isinstance(obj, BaseModel)

    @staticmethod
    def _is_pydantic_type(cls_: typing.Any) -> bool:
        return isinstance(cls_, type) and issubclass(cls_, BaseModel)

    @staticmethod
    def _is_dataclass_instance(obj: typing.Any) -> bool:
        return dataclasses.is_dataclass(obj) and not isinstance(obj, type)

    @staticmethod
    def _is_dataclass_type(cls_: typing.Any) -> bool:
        return isinstance(cls_, type) and dataclasses.is_dataclass(cls_)

    @property
    def the_module(self) -> str:
        """Return the module name of the wrapped object."""
        return self.base.attributes.get('@module', '')

    @property
    def the_class(self) -> str:
        """Return the class name of the wrapped object."""
        return self.base.attributes.get('@class', '')

    @property
    def obj(self) -> JsonSerializableProtocol:
        """Return the wrapped object.

        .. note:: This property caches the deserialized object, this means that when the node is loaded from the
            database, the object is deserialized only once and stored in memory as an attribute. Subsequent calls will
            simply return this cached object and not reload it from the database. This is fine, since nodes that are
            loaded from the database are by definition stored and therefore immutable, making it safe to assume that the
            object that is represented can not change. Note, however, that the caching also applies to unstored nodes.
            That means that manually changing the attributes of an unstored ``JsonableData`` can lead to inconsistencies
            with the object returned by this property.

        """
        return self._get_object()

    @classmethod
    def _deserialize_float_constants(cls, data: typing.Any):
        """Deserialize the contents of a dictionary ``data`` deserializing infinity and NaN string constants.

        The ``data`` dictionary is recursively checked for the ``Infinity``, ``-Infinity`` and ``NaN`` strings, which
        are the Javascript string equivalents to the Python ``float('inf')``, ``-float('inf')`` and ``float('nan')``
        float constants. If one of the strings is encountered, the Python float constant is returned and otherwise the
        original value is returned.
        """
        if isinstance(data, dict):
            return {k: cls._deserialize_float_constants(v) for k, v in data.items()}
        if isinstance(data, list):
            return [cls._deserialize_float_constants(v) for v in data]
        if data == 'Infinity':
            return float('inf')
        if data == '-Infinity':
            return -float('inf')
        if data == 'NaN':
            return float('nan')
        return data

    def _get_object(self) -> JsonSerializableProtocol:
        """Return the cached wrapped object.

        .. note:: If the object is not yet present in memory, for example if the node was loaded from the database,
            the object will first be reconstructed from the state stored in the node attributes.

        """
        try:
            return self._obj
        except AttributeError:
            attributes = self.base.attributes.all
            class_name = attributes.pop('@class')
            module_name = attributes.pop('@module')

            try:
                module = importlib.import_module(module_name)
            except ImportError as exc:
                raise ImportError(f'the objects module `{module_name}` can not be imported.') from exc

            try:
                cls = getattr(module, class_name)
            except AttributeError as exc:
                raise ImportError(
                    f'the objects module `{module_name}` does not contain the class `{class_name}`.'
                ) from exc

            deserialized = self._deserialize_float_constants(attributes)
            self._obj = self._rebuild_object(cls, deserialized)

            return self._obj

    def to_model_field_values(
        self,
        *,
        context: dict[str, typing.Any] | None = None,
        minimal: bool = False,
        schema: type[OrmModel] | None = None,
    ) -> dict[str, typing.Any]:
        fields = super().to_model_field_values(
            context=context,
            minimal=minimal,
            schema=schema,
        )
        if schema and issubclass(schema, self.WritableFields):
            fields['attributes'] |= self._extract_dict(self.obj)
        return fields
