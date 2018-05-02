# -*- coding: utf-8 -*-
from aiida.common.extendeddicts import AttributeDict, FixedFieldsAttributeDict
from aiida.work.ports import PortNamespace

__all__ = ['ProcessBuilder', 'JobProcessBuilder', 'ProcessBuilderInputDict']


class ProcessBuilderInput(object):
    __slots__ = ['_value', '__doc__']

    def __init__(self, port, value):
        self._value = value
        self.__doc__ = str(port)

    def __str__(self):
        return '{}'.format(self._value.__str__())

    def __repr__(self):
        return self.__str__()


class ProcessBuilderInputDefault(ProcessBuilderInput):

    def __str__(self):
        return '{} [default]'.format(self._value.__str__())


class ProcessBuilderInputDict(FixedFieldsAttributeDict):
    """Input dictionary for process builder."""

    def __init__(self, port_namespace):
        self._valid_fields = port_namespace.keys()
        self._port_namespace = port_namespace
        super(ProcessBuilderInputDict, self).__init__()

        for name, port in port_namespace.items():
            if isinstance(port, PortNamespace):
                self[name] = ProcessBuilderInputDict(port)
            elif port.has_default():
                self[name] = ProcessBuilderInputDefault(port, port.default)
            else:
                self[name] = ProcessBuilderInput(port, None)

    def __setattr__(self, attr, value):
        """
        Any attributes without a leading underscore being set correspond to inputs and should hence
        be validated with respect to the corresponding input port from the process spec
        """
        if attr.startswith('_'):
            object.__setattr__(self, attr, value)
        else:
            port = self._port_namespace[attr]
            is_valid, message = port.validate(value)

            if not is_valid:
                raise ValueError('invalid attribute value: {}'.format(message))

            super(ProcessBuilderInputDict, self).__setattr__(attr, value)

    def __repr__(self):
        return dict(self).__repr__()

    def __dir__(self):
        return super(ProcessBuilderInputDict, self).__dir__()

    def _todict(self):
        result = {}
        for name, value in self.items():
            if isinstance(value, ProcessBuilderInput):
                continue
            elif isinstance(value, ProcessBuilderInputDict):
                result[name] = value._todict()
            else:
                result[name] = value
        return result


class ProcessBuilder(ProcessBuilderInputDict):

    def __init__(self, process_class):
        self._process_class = process_class
        self._process_spec = self._process_class.spec()
        super(ProcessBuilder, self).__init__(port_namespace=self._process_spec.inputs)


class JobProcessBuilder(ProcessBuilder):

    def __dir__(self):
        return super(JobProcessBuilder, self).__dir__() + ['submit_test']

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
        inputs = self._todict()
        inputs['store_provenance'] = False
        process = self._process_class(inputs=inputs)

        return process._calc.submit_test(folder, subfolder_name)
