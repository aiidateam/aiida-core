###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Convenience classes to help building the input dictionaries for Processes."""

import json
from collections.abc import Mapping, MutableMapping
from typing import TYPE_CHECKING, Any, Type
from uuid import uuid4

from aiida.engine.processes.ports import PortNamespace
from aiida.orm import Dict, Node
from aiida.orm.nodes.data.base import BaseType

from .utils import prune_mapping

if TYPE_CHECKING:
    from aiida.engine.processes.process import Process

__all__ = ('ProcessBuilder', 'ProcessBuilderNamespace')


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
        self._data = {}

        dynamic_properties = {}

        # The name and port objects have to be passed to the defined functions as defaults for
        # their arguments, because this way the content at the time of defining the method is
        # saved. If they are used directly in the body, it will try to capture the value from
        # its enclosing scope at the time of being called.
        for name, port in port_namespace.items():
            self._valid_fields.append(name)

            if isinstance(port, PortNamespace):
                # Only add the nested namespace to _data if populate_defaults is True.
                # This prevents empty namespaces from appearing in the builder when they
                # have no values set and populate_defaults=False.
                if port.populate_defaults:
                    self._data[name] = ProcessBuilderNamespace(port)

                def fgetter(self, name=name, port=port):
                    # Lazily create the ProcessBuilderNamespace if it doesn't exist yet.
                    # This allows accessing nested namespaces that have populate_defaults=False.
                    if name not in self._data:
                        self._data[name] = ProcessBuilderNamespace(port)
                    return self._data.get(name)
            elif port.has_default():

                def fgetter(self, name=name, default=port.default):  # type: ignore[misc]
                    return self._data.get(name, default)
            else:

                def fgetter(self, name=name):
                    return self._data.get(name, None)

            def fsetter(self, value, name=name):
                self._data[name] = value

            fgetter.__doc__ = str(port)
            getter = property(fgetter)
            getter.setter(fsetter)
            dynamic_properties[name] = getter

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
        return sorted(set(self._valid_fields + [key for key, _ in self.__dict__.items() if key.startswith('_')]))

    def __iter__(self):
        for key in self._data:
            yield key

    def __len__(self):
        return len(self._data)

    def __getitem__(self, item):
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
            raise TypeError(f'update expected at most 1 arguments, got {int(len(args))}')

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
        import yaml

        return p.text(
            f'Process class: {self._process_class.__name__}\n'
            f'Inputs:\n{yaml.safe_dump(json.JSONDecoder().decode(PrettyEncoder().encode(self)))}'
        )
