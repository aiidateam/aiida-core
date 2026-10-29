"""Data plugin that allows to easily wrap objects that are JSON-able."""

from __future__ import annotations

import importlib
import json
import typing as t

import pydantic as pdt

from aiida.common import exceptions
from aiida.common.lang import type_check
from aiida.orm.decorators import attribute
from aiida.orm.nodes.data.data import Data

__all__ = ('JsonableData',)


@t.runtime_checkable
class JsonSerializableProtocol(t.Protocol):
    def as_dict(self) -> t.MutableMapping[t.Any, t.Any]: ...


class JsonableData(Data):
    """Data plugin that allows to easily wrap objects that are JSON-able.

    Any class that implements the ``as_dict`` method, returning a dictionary that is a JSON serializable representation
    of the object, can be wrapped and stored by this data plugin.
    """

    _attributes_model_config = pdt.ConfigDict(
        arbitrary_types_allowed=True,
        extra='allow',
    )

    _obj: JsonSerializableProtocol | None = None

    def __init__(
        self,
        obj: JsonSerializableProtocol | None = None,
        data: dict[str, t.Any] | None = None,
        the_class: str | None = None,
        the_module: str | None = None,
        **kwargs: t.Any,
    ) -> None:
        super().__init__(**kwargs)

        if obj is not None:
            if not hasattr(obj, 'as_dict') or not callable(getattr(obj, 'as_dict')):
                raise TypeError('the `obj` argument does not have the required `as_dict` method.')

            dictionary = obj.as_dict()

            if 'the_class' not in dictionary:
                dictionary['the_class'] = obj.__class__.__name__

            if 'the_module' not in dictionary:
                dictionary['the_module'] = obj.__class__.__module__

            try:
                serialized = json.loads(json.dumps(dictionary), parse_constant=lambda value: value)
            except TypeError as exc:
                msg = f'the object `{obj}` is not JSON-serializable and therefore cannot be stored.'
                raise TypeError(msg) from exc

            self.base.attributes.set_many(serialized)
            self._obj = obj

        elif data is not None and the_class is not None and the_module is not None:
            self.base.attributes.set_many(
                {
                    'data': data,
                    'the_class': the_class,
                    'the_module': the_module,
                }
            )

    def __str__(self) -> str:
        return f'{super().__str__()} data: {self.obj.as_dict()}'

    @attribute
    def data(self) -> dict[str, t.Any]:
        return self.base.attributes.get('data')

    @data.setter
    def data(self, value: dict[str, t.Any]) -> None:
        type_check(value, dict)
        self.base.attributes.set('data', value)

    @attribute
    def the_module(self) -> str:
        """The module name of the wrapped object."""
        return self.base.attributes.get('the_module')

    @the_module.setter
    def the_module(self, value: str) -> None:
        type_check(value, str)
        self.base.attributes.set('the_module', value)

    @attribute
    def the_class(self) -> str:
        """The class name of the wrapped object."""
        return self.base.attributes.get('the_class')

    @the_class.setter
    def the_class(self, value: str) -> None:
        type_check(value, str)
        self.base.attributes.set('the_class', value)

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
    def _deserialize_float_constants(cls, data: t.Any) -> t.Any:
        """Deserialize the contents of a dictionary ``data`` deserializing infinity and NaN string constants."""
        if isinstance(data, dict):
            return {key: cls._deserialize_float_constants(value) for key, value in data.items()}
        if isinstance(data, list):
            return [cls._deserialize_float_constants(value) for value in data]
        if data == 'Infinity':
            return float('inf')
        if data == '-Infinity':
            return -float('inf')
        if data == 'NaN':
            return float('nan')
        return data

    def _get_object(self) -> JsonSerializableProtocol:
        """Return the cached wrapped object."""
        if self._obj is not None:
            return self._obj

        attributes = self.base.attributes.all
        class_name = attributes.pop('the_class')
        module_name = attributes.pop('the_module')

        try:
            module = importlib.import_module(module_name)
        except ImportError as exc:
            msg = f'the objects module `{module_name}` can not be imported.'
            raise ImportError(msg) from exc

        try:
            cls = getattr(module, class_name)
        except AttributeError as exc:
            msg = f'the objects module `{module_name}` does not contain the class `{class_name}`.'
            raise ImportError(msg) from exc

        deserialized = self._deserialize_float_constants(attributes)
        self._obj = cls.from_dict(deserialized)

        return self._obj

    def _validate(self) -> None:
        super()._validate()

        try:
            module_name = self.the_module
        except AttributeError as exc:
            raise exceptions.ValidationError("attribute 'the_module' not set.") from exc

        try:
            class_name = self.the_class
        except AttributeError as exc:
            raise exceptions.ValidationError("attribute 'the_class' not set.") from exc

        try:
            module = importlib.import_module(module_name)
        except ImportError as exc:
            msg = f"module '{module_name}' could not be imported."
            raise exceptions.ValidationError(msg) from exc

        try:
            cls = getattr(module, class_name)
        except AttributeError as exc:
            msg = f"module '{module_name}' does not contain class '{class_name}'."
            raise exceptions.ValidationError(msg) from exc

        if not callable(getattr(cls, 'from_dict', None)):
            msg = f"class '{module_name}.{class_name}' does not define a callable 'from_dict' method."
            raise exceptions.ValidationError(msg)
