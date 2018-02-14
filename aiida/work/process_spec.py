# -*- coding: utf-8 -*-
import plumpy
import voluptuous

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


class ProcessSpec(plumpy.ProcessSpec):

    INPUT_PORT_TYPE = InputPort
    PORT_NAMESPACE_TYPE = PortNamespace

    def __init__(self):
        super(ProcessSpec, self).__init__()