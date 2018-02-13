# -*- coding: utf-8 -*-
import voluptuous

from plum import process
from aiida.common.extendeddicts import FixedFieldsAttributeDict
from aiida.orm.data.parameter import ParameterData
from aiida.work.ports import InputPort, PortNamespace


class DictSchema(object):
    def __init__(self, schema):
        self._schema = voluptuous.Schema(schema)

    def __call__(self, value):
        """
        Call this to validate the value against the schema.

        :param value: a regular dictionary or a ParameterData instance 
        :return: tuple (success, msg).  success is True if the value is valid
            and False otherwise, in which case msg will contain information about
            the validation failure.
        :rtype: tuple
        """
        try:
            if isinstance(value, ParameterData):
                value = value.get_dict()
            self._schema(value)
            return True, None
        except voluptuous.Invalid as e:
            return False, str(e)

    def get_template(self):
        return self._get_template(self._schema.schema)

    def _get_template(self, dict):
        template = type(
            "{}Inputs".format(self.__class__.__name__),
            (FixedFieldsAttributeDict,),
            {'_valid_fields': dict.keys()})()

        for key, value in dict.iteritems():
            if isinstance(key, (voluptuous.Optional, voluptuous.Required)):
                if key.default is not voluptuous.UNDEFINED:
                    template[key.schema] = key.default
                else:
                    template[key.schema] = None
            if isinstance(value, collections.Mapping):
                template[key] = self._get_template(value)
        return template


class ProcessSpec(process.ProcessSpec):

    INPUT_PORT_TYPE = InputPort
    PORT_NAMESPACE_TYPE = PortNamespace

    def __init__(self):
        super(ProcessSpec, self).__init__()

    def get_inputs_template(self):
        """
        Get an object that represents a template of the known inputs and their
        defaults for the :class:`Process`.

        :return: An object with attributes that represent the known inputs for
            this process.  Default values will be filled in.
        """
        template = type(
            "{}Inputs".format(self.__class__.__name__),
            (FixedFieldsAttributeDict,),
            {'_valid_fields': self.inputs.keys()})()

        # Now fill in any default values
        for name, value_spec in self.inputs.iteritems():
            if isinstance(value_spec.validator, DictSchema):
                template[name] = value_spec.validator.get_template()
            elif value_spec.has_default():
                template[name] = value_spec.default
            else:
                template[name] = None

        return template
