# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=cell-var-from-loop
"""Convenience classes to help building the input dictionaries for Processes."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from collections import Mapping

from aiida.engine.processes.ports import PortNamespace

__all__ = ('ProcessBuilder', 'CalcJobBuilder', 'ProcessBuilderNamespace')


class ProcessBuilderNamespace(Mapping):
    """
    Input namespace for the ProcessBuilder. Dynamically generates the getters and setters
    for the input ports of a given PortNamespace
    """

    def __init__(self, port_namespace):
        """
        Dynamically construct the get and set properties for the ports of the given port namespace

        For each port in the given port namespace a get and set property will be constructed dynamically
        and added to the ProcessBuilderNamespace. The docstring for these properties will be defined
        by calling str() on the Port, which should return the description of the Port.

        :param port_namespace: the inputs PortNamespace for which to construct the builder
        """
        # pylint: disable=super-init-not-called
        self._port_namespace = port_namespace
        self._valid_fields = []
        self._data = {}

        for name, port in port_namespace.items():

            self._valid_fields.append(name)

            if isinstance(port, PortNamespace):
                self._data[name] = ProcessBuilderNamespace(port)

                def fgetter(self, name=name):
                    return self._data.get(name)
            elif port.has_default():

                def fgetter(self, name=name, default=port.default):
                    return self._data.get(name, default)
            else:

                def fgetter(self, name=name):
                    return self._data.get(name, None)

            def fsetter(self, value):
                self._data[name] = value

            fgetter.__doc__ = str(port)
            getter = property(fgetter)
            getter.setter(fsetter)
            setattr(self.__class__, name, getter)

    def __setattr__(self, attr, value):
        """
        Any attributes without a leading underscore being set correspond to inputs and should hence
        be validated with respect to the corresponding input port from the process spec
        """
        if attr.startswith('_'):
            object.__setattr__(self, attr, value)
        else:
            try:
                port = self._port_namespace[attr]
            except KeyError:
                raise AttributeError('Unknown builder parameter: {}'.format(attr))

            value = port.serialize(value)
            validation_error = port.validate(value)
            if validation_error:
                raise ValueError('invalid attribute value {}'.format(validation_error.message))

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


class ProcessBuilder(ProcessBuilderNamespace):
    """A process builder that helps setting up the inputs for creating a new process."""

    def __init__(self, process_class):
        self._process_class = process_class
        self._process_spec = self._process_class.spec()
        super(ProcessBuilder, self).__init__(port_namespace=self._process_spec.inputs)

    @property
    def process_class(self):
        return self._process_class


class CalcJobBuilder(ProcessBuilder):
    """A process builder specific to CalcJob implementations that provides also the `submit_test` functionality."""

    def __dir__(self):
        return super(CalcJobBuilder, self).__dir__() + ['submit_test']

    def submit_test(self, folder=None, subfolder_name=None):
        """
        Run a test submission by creating the files that would be generated for the real calculation in a local folder,
        without actually storing the calculation nor the input nodes. This functionality therefore also does not
        require any of the inputs nodes to be stored yet.

        :param folder: a Folder object, within which to create the calculation files. By default a folder
            will be created in the current working directory
        :param subfolder_name: the name of the subfolder to use within the directory of the ``folder`` object. By
            default a unique string will be generated based on the current datetime with the format ``yymmdd-``
            followed by an auto incrementing index
        """
        inputs = {'store_provenance': False}
        inputs.update(**self)
        process = self._process_class(inputs=inputs)

        return process.node.submit_test(folder, subfolder_name)
