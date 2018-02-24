# -*- coding: utf-8 -*-
from plumpy import ports


class WithNonDb(object):
    """
    A mixin that adds support to a port to flag a that should not be stored
    in the database using the non_db=True flag.

    The mixins have to go before the main port class in the superclass order
    to make sure the mixin has the chance to strip out the non_db keyword.
    """

    def __init__(self, *args, **kwargs):
        non_db = kwargs.pop('non_db', False)
        super(WithNonDb, self).__init__(*args, **kwargs)
        self._non_db = non_db

    @property
    def non_db(self):
        return self._non_db

class WithSerializeFct(object):
    """
    A mixin that adds support for a serialization function which is automatically applied on inputs that are not AiiDA data types.
    """
    def __init__(self, *args, **kwargs):
        serialize_fct = kwargs.pop('serialize_fct', None)
        super(WithSerializeFct, self).__init__(*args, **kwargs)
        self._serialize_fct = serialize_fct

    def serialize(self, value):
        from aiida.orm import Data
        if self._serialize_fct is None or isinstance(value, Data):
            return value
        return self._serialize_fct(value)

class InputPort(WithSerializeFct, WithNonDb, ports.InputPort):
    pass


class PortNamespace(WithNonDb, ports.PortNamespace):
    def serialize(self, mapping):
        result = {}
        for name, value in mapping.items():
            if name in self:
                port = self[name]
                result[name] = port.serialize(value)
            else:
                result[name] = value
        return result
