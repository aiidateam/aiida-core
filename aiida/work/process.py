# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

import abc
import inspect
import collections
import uuid
from enum import Enum
import itertools

import plum.port

import aiida.orm
from aiida.orm.data import Data
from aiida.orm import load_node
from aiida.orm.implementation.general.calculation.work import WorkCalculation
import voluptuous
from aiida.common.extendeddicts import FixedFieldsAttributeDict
import aiida.common.exceptions as exceptions
from aiida.common.exceptions import ModificationNotAllowed
from aiida.common.lang import override, protected
from aiida.common.links import LinkType
from aiida.utils.calculation import add_source_info
from aiida.orm.calculation import Calculation
from aiida.orm.data.parameter import ParameterData
from aiida import LOG_LEVEL_REPORT
from . import utils

__all__ = ['Process', 'FunctionProcess']


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


class _WithNonDb(object):
    """
    A mixin that adds support to a port to flag a that should not be stored
    in the database using the non_db=True flag.

    The mixins have to go before the main port class in the superclass order
    to make sure the mixin has the chance to strip out the non_db keyword.
    """

    def __init__(self, *args, **kwargs):
        non_db = kwargs.pop('non_db', False)
        super(_WithNonDb, self).__init__(*args, **kwargs)
        self._non_db = non_db

    @property
    def non_db(self):
        return self._non_db


class InputPort(_WithNonDb, plum.port.InputPort):
    pass


class DynamicInputPort(_WithNonDb, plum.port.DynamicInputPort):
    pass


class InputGroupPort(_WithNonDb, plum.port.InputGroupPort):
    pass


class ProcessSpec(plum.process.ProcessSpec):
    INPUT_PORT_TYPE = InputPort
    DYNAMIC_INPUT_PORT_TYPE = DynamicInputPort
    INPUT_GROUP_PORT_TYPE = InputGroupPort

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
            elif value_spec.default is not None:
                template[name] = value_spec.default
            else:
                template[name] = None

        return template


class Process(plum.process.Process):
    """
    This class represents an AiiDA process which can be executed and will
    have full provenance saved in the database.
    """
    __metaclass__ = abc.ABCMeta

    SINGLE_RETURN_LINKNAME = '_return'
    # This is used for saving node pks in the saved instance state
    NODE_TYPE = uuid.UUID('5cac9bab-6f46-485b-9e81-d6a666cfdc1b')

    class SaveKeys(Enum):
        """
        Keys used to identify things in the saved instance state bundle.
        """
        CALC_ID = 'calc_id'
        PARENT_PID = 'parent_calc_pid'

    @classmethod
    def define(cls, spec):
        super(Process, cls).define(spec)

        spec.input("_store_provenance", valid_type=bool, default=True,
                   non_db=True)
        spec.input("_description", valid_type=basestring, required=False,
                   non_db=True)
        spec.input("_label", valid_type=basestring, required=False,
                   non_db=True)

        spec.dynamic_input(valid_type=(aiida.orm.Data, aiida.orm.Calculation))
        spec.dynamic_output(valid_type=aiida.orm.Data)

    @classmethod
    def get_inputs_template(cls):
        return cls.spec().get_inputs_template()

    @classmethod
    def get_or_create_db_record(cls):
        """
        Create a database calculation node that represents what happened in
        this process.
        :return: A calculation
        :rtype: :class:`Calculation`
        """
        from aiida.orm.calculation.work import WorkCalculation
        calc = WorkCalculation()
        return calc

    _spec_type = ProcessSpec

    def __init__(self, inputs=None, pid=None, logger=None, loop=None):
        super(Process, self).__init__(inputs, pid, logger, loop)

        self._calc = None
        # Get the parent from the top of the process stack
        try:
            self._parent_pid = utils.ProcessStack.top().pid
        except IndexError:
            self._parent_pid = None

        self._pid = self._create_and_setup_db_record()

        if logger is None:
            self.set_logger(self._calc.logger)

    @property
    def calc(self):
        return self._calc

    @override
    def save_instance_state(self, out_state):
        super(Process, self).save_instance_state(out_state)

        if self.inputs._store_provenance:
            assert self.calc.is_stored

        out_state[self.SaveKeys.PARENT_PID.value] = self._parent_pid
        out_state[self.SaveKeys.CALC_ID.value] = self.pid

    def get_provenance_inputs_iterator(self):
        return itertools.ifilter(lambda kv: not kv[0].startswith('_'),
                                 self.inputs.iteritems())

    @override
    def load_instance_state(self, saved_state):
        super(Process, self).load_instance_state(saved_state)

        is_copy = saved_state.get('COPY', False)

        if self.SaveKeys.CALC_ID.value in saved_state:
            if is_copy:
                old = load_node(saved_state[self.SaveKeys.CALC_ID.value])
                self._calc = old.copy()
                self._calc.store()
            else:
                self._calc = load_node(saved_state[self.SaveKeys.CALC_ID.value])

            self._pid = self.calc.pk
        else:
            self._pid = self._create_and_setup_db_record()

        if self.SaveKeys.PARENT_PID.value in saved_state:
            self._parent_pid = saved_state[self.SaveKeys.PARENT_PID.value]

    @override
    def out(self, output_port, value=None):
        if value is None:
            # In this case assume that output_port is the actual value and there
            # is just one return value
            return super(Process, self).out(self.SINGLE_RETURN_LINKNAME, output_port)
        else:
            return super(Process, self).out(output_port, value)

    # region Process messages
    @override
    def on_finish(self):
        super(Process, self).on_finish()
        self.calc._set_attr(WorkCalculation.FINISHED_KEY, True)

    @override
    def on_destroy(self):
        """
        Called when a Process enters the DESTROYED state which should be
        the final process state and so we seal the calculation node
        """
        super(Process, self).on_destroy()
        if self.calc.has_finished():
            try:
                self.calc.seal()
            except exceptions.ModificationNotAllowed:
                pass

    @override
    def on_fail(self, exc_info):
        import traceback
        super(Process, self).on_fail(exc_info)

        exc = traceback.format_exception(exc_info[0], exc_info[1], exc_info[2])
        self.logger.error("{} failed:\n{}".format(self.pid, "".join(exc)))

        exception = exc_info[1]
        self.calc._set_attr(WorkCalculation.FAILED_KEY, exception.message)
        self.calc.seal()

    @override
    def on_output_emitted(self, output_port, value, dynamic):
        """
        The process has emitted a value on the given output port.

        :param output_port: The output port name the value was emitted on
        :param value: The value emitted
        :param dynamic: Was the output port a dynamic one (i.e. not known
        beforehand?)
        """
        super(Process, self).on_output_emitted(output_port, value, dynamic)
        if not isinstance(value, Data):
            raise TypeError(
                "Values outputted from process must be instances of AiiDA Data " \
                "types.  Got: {}".format(value.__class__)
            )

        # Try making us the creator
        try:
            value.add_link_from(self.calc, output_port, LinkType.CREATE)
        except ValueError:
            # Must have already been created...nae dramas
            pass

        value.store()
        value.add_link_from(self.calc, output_port, LinkType.RETURN)

    # end region

    @property
    def runner(self):
        return self.loop()

    @override
    def do_run(self):
        # Only keep calculation inputs
        ins = {}
        for name, value in self.inputs.iteritems():
            try:
                port = self.spec().get_input(name)
            except ValueError:
                ins[name] = value
            else:
                if not port.non_db:
                    ins[name] = value

        return self._run(**ins)

    @protected
    def get_parent_calc(self):
        # Can't get it if we don't know our parent
        if self._parent_pid is None:
            return None

        try:
            return load_node(uuid=self._parent_pid)
        except exceptions.NotExistent:
            pass

        # Out of options
        return None

    @protected
    def report(self, msg, *args, **kwargs):
        """
        Log a message to the logger, which should get saved to the
        database through the attached DbLogHandler. The class name and function
        name of the caller are prepended to the given message
        """
        message = '[{}|{}|{}]: {}'.format(self.calc.pk, self.__class__.__name__, inspect.stack()[1][3], msg)
        self.logger.log(LOG_LEVEL_REPORT, message, *args, **kwargs)

    def _create_and_setup_db_record(self):
        self._calc = self.get_or_create_db_record()
        self._setup_db_record()
        if self.inputs._store_provenance:
            try:
                self.calc.store_all()
            except ModificationNotAllowed as exception:
                # The calculation was already stored
                pass

        if self.calc.pk is not None:
            return self.calc.pk
        else:
            return uuid.UUID(self.calc.uuid)

    @override
    def encode_input_args(self, inputs):
        """ 
        Encode input arguments such that they may be saved in a 
        :class:`apricotpy.persistable.Bundle`

        :param inputs: A mapping of the inputs as passed to the process
        :return: The encoded inputs
        """
        return {k: self._encode_input(v) for k, v in inputs.iteritems()}

    @override
    def decode_input_args(self, encoded):
        """
        Decode saved input arguments as they came from the saved instance state 
        :class:`apricotpy.persistable.Bundle`

        :param encoded: 
        :return: The decoded input args
        """
        return {k: self._decode_input(v) for k, v in encoded.iteritems()}

    def _encode_input(self, inp):
        if isinstance(inp, aiida.orm.data.Node):
            return self.NODE_TYPE, inp.uuid
        elif isinstance(inp, collections.Mapping):
            return {k: self._encode_input(v) for k, v in inp.iteritems()}
        elif not isinstance(inp, (str, unicode)) and \
                isinstance(inp, collections.Sequence):
            return tuple(self._encode_input(v) for v in inp)
        else:
            return inp

    def _decode_input(self, encoded):
        if self._is_encoded_node(encoded):
            return load_node(uuid=encoded[1])
        elif isinstance(encoded, collections.Mapping):
            return {k: self._decode_input(v) for k, v in encoded.iteritems()}
        elif not isinstance(encoded, (str, unicode)) and \
                isinstance(input, collections.Sequence):
            return tuple(self._decode_input(v) for v in encoded)
        else:
            return encoded

    def _is_encoded_node(self, value):
        return not isinstance(value, (str, unicode)) and \
               isinstance(value, collections.Sequence) and \
               value[0] == self.NODE_TYPE

    def _setup_db_record(self):
        assert self.inputs is not None
        assert not self.calc.is_sealed, \
            "Calculation cannot be sealed when setting up the database record"

        # Save the name of this process
        self.calc._set_attr(utils.PROCESS_LABEL_ATTR, self.__class__.__name__)

        parent_calc = self.get_parent_calc()

        # First get a dictionary of all the inputs to link, this is needed to
        # deal with things like input groups
        to_link = {}
        for name, input in self.inputs.iteritems():
            try:
                port = self.spec().get_input(name)
            except ValueError:
                # It's not in the spec, so we better support dynamic inputs
                assert self.spec().has_dynamic_input()
                to_link[name] = input
            else:
                # Ignore any inputs that should not be saved
                if port.non_db:
                    continue

                if isinstance(port, plum.port.InputGroupPort):
                    to_link.update(
                        {"{}_{}".format(name, k): v for k, v in
                         input.iteritems()})
                else:
                    to_link[name] = input

        for name, input in to_link.iteritems():

            if isinstance(input, Calculation):
                input = utils.get_or_create_output_group(input)

            if not input.is_stored:
                # If the input isn't stored then assume our parent created it
                if parent_calc:
                    input.add_link_from(parent_calc, "CREATE", link_type=LinkType.CREATE)
                if self.inputs._store_provenance:
                    input.store()

            self.calc.add_link_from(input, name)

        if parent_calc:
            self.calc.add_link_from(parent_calc, "CALL",
                                    link_type=LinkType.CALL)

        self._add_description_and_label()

    def _add_description_and_label(self):
        if self.raw_inputs:
            description = self.raw_inputs.get('_description', None)
            if description is not None:
                self._calc.description = description
            label = self.raw_inputs.get('_label', None)
            if label is not None:
                self._calc.label = label


class FunctionProcess(Process):
    _func_args = None

    @staticmethod
    def _func(*args, **kwargs):
        """
        This is used internally to store the actual function that is being
        wrapped and will be replaced by the build method.
        """
        return {}

    @staticmethod
    def build(func, **kwargs):
        """
        Build a Process from the given function.  All function arguments will
        be assigned as process inputs.  If keyword arguments are specified then
        these will also become inputs.

        :param func: The function to build a process from
        :param kwargs: Optional keyword arguments that will become additional
            inputs to the process
        :return: A Process class that represents the function
        :rtype: :class:`FunctionProcess`
        """
        import inspect
        from aiida.orm.data import Data

        args, varargs, keywords, defaults = inspect.getargspec(func)

        def _define(cls, spec):
            super(FunctionProcess, cls).define(spec)

            for i in range(len(args)):
                default = None
                if defaults and len(defaults) - len(args) + i >= 0:
                    default = defaults[i]
                spec.input(args[i], valid_type=Data, default=default)
                # Make sure to get rid of the argument from the keywords dict
                kwargs.pop(args[i], None)

            for k, v in kwargs.iteritems():
                spec.input(k)

            # If the function support kwargs then allow dynamic inputs,
            # otherwise disallow
            if keywords is not None:
                spec.dynamic_input()
            else:
                spec.no_dynamic_input()

            # We don't know what a function will return so keep it dynamic
            spec.dynamic_output(valid_type=Data)

        return type(func.__name__, (FunctionProcess,),
                    {'_func': staticmethod(func),
                     Process.define.__name__: classmethod(_define),
                     '_func_args': args})

    @classmethod
    def create_inputs(cls, *args, **kwargs):
        ins = {}
        if kwargs:
            ins.update(kwargs)
        if args:
            ins.update(cls.args_to_dict(*args))
        return ins

    @classmethod
    def args_to_dict(cls, *args):
        """
        Create an input dictionary (i.e. label: value) from supplied args.

        :param args: The values to use
        :return: A label: value dictionary
        """
        assert (len(args) == len(cls._func_args))
        return dict(zip(cls._func_args, args))

    @override
    def _setup_db_record(self):
        super(FunctionProcess, self)._setup_db_record()
        add_source_info(self.calc, self._func)
        # Save the name of the function
        self.calc._set_attr(utils.PROCESS_LABEL_ATTR, self._func.__name__)

    @override
    def _run(self, **kwargs):
        from aiida.orm.data import Data

        args = []
        for arg in self._func_args:
            args.append(kwargs.pop(arg))
        outs = self._func(*args, **kwargs)
        if outs is not None:
            if isinstance(outs, Data):
                self.out(self.SINGLE_RETURN_LINKNAME, outs)
            elif isinstance(outs, collections.Mapping):
                for name, value in outs.iteritems():
                    self.out(name, value)
            else:
                raise TypeError(
                    "Workfunction returned unsupported type '{}'\n"
                    "Must be a Data type or a Mapping of string => Data".
                        format(outs.__class__))