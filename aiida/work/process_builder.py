# -*- coding: utf-8 -*-
from aiida.common.extendeddicts import FixedFieldsAttributeDict
from aiida.work.launch import run, submit


class ProcessBuilderInput(object):

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


class ProcessBuilder(FixedFieldsAttributeDict):

    def __init__(self, process_class):
        self._process_class = process_class
        self._process_spec = self._process_class.spec()
        self._valid_fields = self._process_spec.inputs.keys()
        super(ProcessBuilder, self).__init__()

        for name, port in self._process_spec.inputs.iteritems():
            if port.has_default():
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
            port = self._process_spec.inputs[attr]
            is_valid, message = port.validate(value)

            if not is_valid:
                raise ValueError('invalid attribute value: {}'.format(message))

            super(ProcessBuilder, self).__setattr__(attr, value)

    def __repr__(self):
        return dict(self).__repr__()

    def __dir__(self):
        return super(ProcessBuilder, self).__dir__() + ['launch']

    def launch(self, daemon=True):
        """
        Launch the process taking the internal attributes dictionary as the inputs dictionary, omitting
        those keys that have not been explicitly set by the user. Setting the argument daemon to False
        will run the Process blocking in the local interpreter

        :param daemon: boolean, when True submits the Process to the daemon
        """
        inputs = {}

        for key, value in dict(self).iteritems():
            if not isinstance(value, ProcessBuilderInput):
                inputs[key] = value

        if daemon is True:
            node = submit(self._process_class, **inputs)
            return node
        else:
            result = run(self._process_class, **inputs)
            return result