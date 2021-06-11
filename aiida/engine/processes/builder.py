# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Convenience classes to help building the input dictionaries for Processes."""
import collections
from typing import Any, Type, TYPE_CHECKING

from aiida.orm import Node
from aiida.engine.processes.ports import PortNamespace

if TYPE_CHECKING:
    from aiida.engine.processes.process import Process

__all__ = ('ProcessBuilder', 'ProcessBuilderNamespace')


class ProcessBuilderNamespace(collections.abc.MutableMapping):
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
        # pylint: disable=super-init-not-called
        self._port_namespace = port_namespace
        self._valid_fields = []
        self._data = {}

        # The name and port objects have to be passed to the defined functions as defaults for
        # their arguments, because this way the content at the time of defining the method is
        # saved. If they are used directly in the body, it will try to capture the value from
        # its enclosing scope at the time of being called.
        for name, port in port_namespace.items():

            self._valid_fields.append(name)

            if isinstance(port, PortNamespace):
                self._data[name] = ProcessBuilderNamespace(port)

                def fgetter(self, name=name):
                    return self._data.get(name)
            elif port.has_default():

                def fgetter(self, name=name, default=port.default):  # type: ignore # pylint: disable=cell-var-from-loop
                    return self._data.get(name, default)
            else:

                def fgetter(self, name=name):
                    return self._data.get(name, None)

            def fsetter(self, value, name=name):
                self._data[name] = value

            fgetter.__doc__ = str(port)
            getter = property(fgetter)
            getter.setter(fsetter)  # pylint: disable=too-many-function-args
            setattr(self.__class__, name, getter)

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
                port = None  # type: ignore[assignment]
            else:
                value = port.serialize(value)  # type: ignore[union-attr]
                validation_error = port.validate(value)
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
        if isinstance(value, collections.abc.Mapping):
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
                if isinstance(value, collections.abc.Mapping):
                    self[key].update(value)
                else:
                    self.__setattr__(key, value)

        for key, value in kwds.items():
            if isinstance(value, collections.abc.Mapping):
                self[key].update(value)
            else:
                self.__setattr__(key, value)

    def _inputs(self, prune: bool = False) -> dict:
        """Return the entire mapping of inputs specified for this builder.

        :param prune: boolean, when True, will prune nested namespaces that contain no actual values whatsoever
        :return: mapping of inputs ports and their input values.
        """
        if prune:
            return self._prune(dict(self))

        return dict(self)

    def _prune(self, value):
        """Prune a nested mapping from all mappings that are completely empty.

        .. note:: a nested mapping that is completely empty means it contains at most other empty mappings. Other null
            values, such as `None` or empty lists, should not be pruned.

        :param value: a nested mapping of port values
        :return: the same mapping but without any nested namespace that is completely empty.
        """
        if isinstance(value, collections.abc.Mapping) and not isinstance(value, Node):
            result = {}
            for key, sub_value in value.items():
                pruned = self._prune(sub_value)
                # If `pruned` is an "empty'ish" mapping and not an instance of `Node`, skip it, otherwise keep it.
                if not (isinstance(pruned, collections.abc.Mapping) and not pruned and not isinstance(pruned, Node)):
                    result[key] = pruned
            return result

        return value


class ProcessBuilder(ProcessBuilderNamespace):  # pylint: disable=too-many-ancestors
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
