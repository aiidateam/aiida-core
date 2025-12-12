"""Data plugin that allows to easily wrap objects that are JSON-able."""

import importlib
import json
import typing

from pydantic import ConfigDict, WithJsonSchema

from aiida.common.pydantic import MetadataField

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
        molecule = Molecule(['H']. [0, 0, 0])
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
    """

    class AttributesModel(Data.AttributesModel):
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
            MetadataField(description='The JSON-serializable object'),
        ]

    def __init__(self, obj: JsonSerializableProtocol, *args, **kwargs):
        """Construct the node for the to be wrapped object."""
        if obj is None:
            raise TypeError('the `obj` argument cannot be `None`.')

        if not hasattr(obj, 'as_dict') or not callable(getattr(obj, 'as_dict')):
            raise TypeError('the `obj` argument does not have the required `as_dict` method.')

        super().__init__(*args, **kwargs)

        self._obj = obj
        dictionary = obj.as_dict()

        if '@class' not in dictionary:
            dictionary['@class'] = obj.__class__.__name__

        if '@module' not in dictionary:
            dictionary['@module'] = obj.__class__.__module__

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
            self._obj = cls.from_dict(deserialized)

            return self._obj

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
