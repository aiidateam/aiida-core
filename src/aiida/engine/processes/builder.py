###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Convenience classes to help building the input dictionaries for Processes."""

from __future__ import annotations

import json
from collections.abc import Mapping, MutableMapping
from typing import TYPE_CHECKING, Any, Type
from uuid import uuid4

import yaml

from aiida.engine.processes.ports import PortNamespace
from aiida.orm import Dict, Node
from aiida.orm.nodes.data.base import BaseType

from .utils import prune_mapping

if TYPE_CHECKING:
    from aiida.engine.processes.process import Process

__all__ = ('ProcessBuilder', 'ProcessBuilderNamespace')


def _format_valid_type(valid_type) -> str:
    """Format valid_type as a compact string with just class names.

    :param valid_type: A type, tuple of types, or None.
    :returns: Compact string representation like 'Int' or 'Int | Float'.
    """
    if valid_type is None:
        return ''

    if isinstance(valid_type, tuple):
        # Filter out NoneType (automatically added for optional ports)
        types = [t for t in valid_type if t is not type(None)]
        if not types:
            return ''
        if len(types) == 1:
            return types[0].__name__
        return ' | '.join(t.__name__ for t in types)

    return valid_type.__name__


def _get_schema(
    self,
    format: str = 'compact',  # Literal['compact', 'keys', 'verbose']
    show: str = 'all',  # Literal['all', 'required', 'set']
    collapse: tuple[str, ...] = ('metadata',),
    max_depth: int | None = None,
) -> str:
    """Return a YAML-formatted schema of all available inputs for this builder.

    This method is dynamically attached to each ``ProcessBuilderNamespace`` instance
    to provide introspection of the available input ports.

    :param format: Output format. Options:

        - ``'compact'`` (default): Shows type and required status inline, e.g. ``x: Int (required)``
        - ``'keys'``: Only show input names without type information
        - ``'verbose'``: Nested format with type, help text, and other metadata

    :param show: Filter which inputs to display. Options:

        - ``'all'`` (default): Show all inputs
        - ``'required'``: Only show required inputs
        - ``'set'``: Only show inputs that have been explicitly set on the builder

    :param collapse: Tuple of namespace names to collapse to ``{...}``. Default: ``('metadata',)``.
        Use ``()`` to expand everything, or add more like ``('metadata', 'monitors')``.
    :param max_depth: Maximum nesting depth to display. None means unlimited.
    :returns: YAML-formatted string of the input structure.

    Example::

        >>> builder = SomeProcess.get_builder()
        >>> print(builder.get_schema())
        code: AbstractCode
        x: Int (required)
        y: Int (required)
        metadata: {...}

        >>> print(builder.get_schema(format='keys'))
        code:
        x:
        y:
        metadata: {...}

        >>> print(builder.get_schema(show='required'))
        x: Int (required)
        y: Int (required)

        >>> builder.x = Int(1)
        >>> print(builder.get_schema(show='set'))
        x: 1

    """
    if format not in ('compact', 'keys', 'verbose'):
        raise ValueError(f"format must be 'compact', 'keys', or 'verbose', got {format!r}")
    if show not in ('all', 'required', 'set'):
        raise ValueError(f"show must be 'all', 'required', or 'set', got {show!r}")

    def build_schema_dict(namespace: PortNamespace, data: dict, depth: int = 0) -> dict[str, Any]:
        """Recursively build schema dictionary from port namespace."""
        schema: dict[str, Any] = {}

        for name, port in namespace.items():
            # Check if this input is set in the builder's data
            is_set = name in data

            if isinstance(port, PortNamespace):
                # Skip non-required namespaces if show='required'
                if show == 'required' and not port.required:
                    continue

                # For show='set' mode, get the nested data if it exists
                nested_data = data.get(name, {})
                if isinstance(nested_data, ProcessBuilderNamespace):
                    nested_data = nested_data._data

                # Skip empty namespaces in show='set' mode
                if show == 'set' and not nested_data:
                    continue

                # For show='set' mode, check if namespace has actual values (not just empty nested dicts)
                # by recursively building the schema and checking if it's non-empty
                nested = build_schema_dict(port, nested_data, depth + 1)

                # Collapse specified namespaces or if max_depth is reached
                if name in collapse or (max_depth is not None and depth >= max_depth):
                    if show == 'set' and nested:
                        # Only show collapsed namespace if it actually has content
                        schema[name] = '{...}'
                    elif show != 'set':
                        schema[name] = '{...}'
                elif nested or show == 'all':
                    schema[name] = nested
            else:
                # Skip non-required ports if show='required'
                if show == 'required' and not port.required:
                    continue

                # Skip unset ports if show='set'
                if show == 'set' and not is_set:
                    continue

                if show == 'set':
                    # Show the actual value when show='set'
                    value = data.get(name)
                    # Try to get a nice representation
                    if value is not None and hasattr(value, 'value'):
                        schema[name] = value.value
                    elif value is not None and hasattr(value, 'get_dict'):
                        schema[name] = value.get_dict()
                    elif value is not None:
                        schema[name] = str(value)
                    else:
                        schema[name] = None
                elif format == 'keys':
                    schema[name] = None
                elif format == 'verbose':
                    # Verbose nested format with help text
                    port_info: dict[str, Any] = {}
                    if port.valid_type is not None:
                        port_info['type'] = _format_valid_type(port.valid_type)
                    if port.help:
                        port_info['help'] = port.help
                    if port.required:
                        port_info['required'] = True
                    if port.has_default():
                        port_info['has_default'] = True
                    schema[name] = port_info if port_info else None
                else:
                    # Compact inline format: "Int (required)" or just "Int"
                    type_str = _format_valid_type(port.valid_type)
                    if port.required and type_str:
                        schema[name] = f'{type_str} (required)'
                    elif type_str:
                        schema[name] = type_str
                    else:
                        schema[name] = '(required)' if port.required else None

        return schema

    schema_dict = build_schema_dict(self._port_namespace, self._data)

    # Reorder: move 'metadata' to the end if present
    if 'metadata' in schema_dict:
        metadata = schema_dict.pop('metadata')
        schema_dict['metadata'] = metadata

    return yaml.dump(schema_dict, default_flow_style=False, sort_keys=False)


class PrettyEncoder(json.JSONEncoder):
    """JSON encoder for returning a pretty representation of an AiiDA ``ProcessBuilder``."""

    def default(self, o):
        if isinstance(o, (ProcessBuilder, ProcessBuilderNamespace)):
            return dict(o)
        if isinstance(o, Dict):
            return o.get_dict()
        if isinstance(o, BaseType):
            return o.value
        if isinstance(o, Node):
            return o.get_description()


class ProcessBuilderNamespace(MutableMapping):
    """Input namespace for the `ProcessBuilder`.

    Dynamically generates the getters and setters for the input ports of a given PortNamespace
    """

    def __init__(self, port_namespace: PortNamespace) -> None:
        """Dynamically construct the get and set properties for the ports of the given port namespace.

        For each port in the given port namespace a get and set property will be constructed dynamically
        and added to the ProcessBuilderNamespace. The docstring for these properties will be defined
        by calling str() on the Port, which should return the description of the Port.

        :param port_namespace: the inputs PortNamespace for which to construct the builder

        """
        self._port_namespace = port_namespace
        self._valid_fields = []
        self._data: dict[str, Any] = {}

        dynamic_properties: dict[str, Any] = {}

        # The name and port objects have to be passed to the defined functions as defaults for
        # their arguments, because this way the content at the time of defining the method is
        # saved. If they are used directly in the body, it will try to capture the value from
        # its enclosing scope at the time of being called.
        for name, port in port_namespace.items():
            self._valid_fields.append(name)

            if isinstance(port, PortNamespace):

                def fgetter(self, name=name, port=port, default=None):
                    if name not in self._data:
                        self._data[name] = ProcessBuilderNamespace(port)
                    return self._data[name]
            elif port.has_default():

                def fgetter(self, name=name, port=None, default=port.default):
                    return self._data.get(name, default)
            else:

                def fgetter(self, name=name, port=None, default=None):
                    return self._data.get(name, None)

            def fsetter(self, value, name=name):
                self._data[name] = value

            fgetter.__doc__ = str(port)
            getter = property(fgetter)
            getter.setter(fsetter)
            dynamic_properties[name] = getter

        # Add helper methods to the dynamic properties
        dynamic_properties['get_schema'] = _get_schema

        # The dynamic property can only be attached to a class and not an instance, however, we cannot attach it to
        # the ``ProcessBuilderNamespace`` class since it would interfere with other instances that may already
        # exist. The workaround is to create a new class on the fly that derives from ``ProcessBuilderNamespace``
        # and add the dynamic property to that instead
        class_name = f'{self.__class__.__name__}-{uuid4()}'
        child_class = type(class_name, (self.__class__,), dynamic_properties)
        self.__class__ = child_class

    def __setattr__(self, attr: str, value: Any) -> None:
        """Assign the given value to the port with key `attr`.

        .. note:: Any attributes without a leading underscore being set correspond to inputs and should hence be
            validated with respect to the corresponding input port from the process spec

        """
        if attr.startswith('_'):
            object.__setattr__(self, attr, value)
        else:
            try:
                port = self._port_namespace[attr]
            except KeyError as exception:
                if not self._port_namespace.dynamic:
                    raise AttributeError(f'Unknown builder parameter: {attr}') from exception
                port = None
            else:
                value = port.serialize(value)  # type: ignore[union-attr]
                validation_error = port.validate(value)  # type: ignore[union-attr]
                if validation_error:
                    raise ValueError(f'invalid attribute value {validation_error.message}')

            # If the attribute that is being set corresponds to a port that is a ``PortNamespace`` we need to make sure
            # that the nested value remains a ``ProcessBuilderNamespace``. Otherwise, the nested namespaces will become
            # plain dictionaries and no longer have the properties of the ``ProcessBuilderNamespace`` that provide all
            # the autocompletion and validation when values are being set. Therefore we first construct a new instance
            # of a ``ProcessBuilderNamespace`` for the port of the attribute that is being set and than iteratively set
            # all the values within the mapping that is being assigned to the attribute.
            if isinstance(port, PortNamespace):
                self._data[attr] = ProcessBuilderNamespace(port)
                for sub_key, sub_value in value.items():
                    setattr(self._data[attr], sub_key, sub_value)
            else:
                self._data[attr] = value

    def __repr__(self):
        return self._data.__repr__()

    def __dir__(self):
        base = set(self._valid_fields + [key for key, _ in self.__dict__.items() if key.startswith('_')])
        return sorted(base | {'get_schema'})

    def __iter__(self):
        for key in self._data:
            yield key

    def __len__(self):
        return len(self._data)

    def __getitem__(self, item):
        if item not in self._data and item in self._valid_fields:
            port = self._port_namespace.get(item)
            if isinstance(port, PortNamespace):
                self._data[item] = ProcessBuilderNamespace(port)
        return self._data[item]

    def __setitem__(self, item, value):
        self.__setattr__(item, value)

    def __delitem__(self, item):
        self._data.__delitem__(item)

    def __delattr__(self, item):
        self._data.__delitem__(item)

    def _recursive_merge(self, dictionary, key, value):
        """Recursively merge the contents of ``dictionary`` setting its ``key`` to ``value``."""
        if isinstance(value, Mapping) and key in dictionary:
            for inner_key, inner_value in value.items():
                self._recursive_merge(dictionary[key], inner_key, inner_value)
        else:
            dictionary[key] = value

    def _merge(self, *args, **kwds):
        """Merge the content of a dictionary or keyword arguments in .

        .. note:: This method differs in behavior from ``_update`` in that ``_merge`` will recursively update the
            existing dictionary with the one that is specified in the arguments. The ``_update`` method will merge only
            the keys on the top level, but any lower lying nested namespace will be replaced entirely.

        The method is prefixed with an underscore in order to not reserve the name for a potential port.

        :param args: a single mapping that should be mapped on the namespace.
        :param kwds: keyword value pairs that should be mapped onto the ports.
        """
        if len(args) > 1:
            raise TypeError(f'update expected at most 1 arguments, got {len(args)}')

        if args:
            for key, value in args[0].items():
                self._recursive_merge(self, key, value)

        for key, value in kwds.items():
            self._recursive_merge(self, key, value)

    def _update(self, *args, **kwds):
        """Update the values of the builder namespace passing a mapping as argument or individual keyword value pairs.

        The method functions just as `collections.abc.MutableMapping.update` and is merely prefixed with an underscore
        in order to not reserve the name for a potential port.

        :param args: a single mapping that should be mapped on the namespace.
        :param kwds: keyword value pairs that should be mapped onto the ports.
        """
        if args:
            for key, value in args[0].items():
                if isinstance(value, Mapping):
                    self[key].update(value)
                else:
                    self.__setattr__(key, value)

        for key, value in kwds.items():
            if isinstance(value, Mapping):
                self[key].update(value)
            else:
                self.__setattr__(key, value)

    def _inputs(self, prune: bool = False) -> dict:
        """Return the entire mapping of inputs specified for this builder.

        :param prune: boolean, when True, will prune nested namespaces that contain no actual values whatsoever
        :return: mapping of inputs ports and their input values.
        """
        if prune:
            return prune_mapping(dict(self))

        # Materialize all lazy namespaces so the full port structure is visible
        for field in self._valid_fields:
            value = getattr(self, field)
            if isinstance(value, ProcessBuilderNamespace):
                value._inputs(prune=False)

        return dict(self)


class ProcessBuilder(ProcessBuilderNamespace):
    """A process builder that helps setting up the inputs for creating a new process."""

    def __init__(self, process_class: Type['Process']):
        """Construct a `ProcessBuilder` instance for the given `Process` class.

        :param process_class: the `Process` subclass
        """
        self._process_class = process_class
        self._process_spec = self._process_class.spec()
        super().__init__(self._process_spec.inputs)

    @property
    def process_class(self) -> Type['Process']:
        """Return the process class for which this builder is constructed."""
        return self._process_class

    def _repr_pretty_(self, p, _) -> str:
        """Pretty representation for in the IPython console and notebooks."""
        return p.text(
            f'Process class: {self._process_class.__name__}\n'
            f'Inputs:\n{yaml.safe_dump(json.JSONDecoder().decode(PrettyEncoder().encode(self)))}'
        )
