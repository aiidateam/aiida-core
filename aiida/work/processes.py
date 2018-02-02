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
import voluptuous
import plum.port
from plum import ProcessState
import traceback

import aiida.orm
import aiida.common.exceptions as exceptions
from aiida.common.extendeddicts import FixedFieldsAttributeDict
from aiida.common.exceptions import ModificationNotAllowed
from aiida.common.lang import override, protected
from aiida.common.links import LinkType
from aiida.common.log import LOG_LEVEL_REPORT
from aiida.orm import load_node
from aiida.orm.calculation import Calculation
from aiida.orm.calculation.work import WorkCalculation
from aiida.orm.data import Data
from aiida.orm.data.parameter import ParameterData
from aiida.utils.calculation import add_source_info
from aiida.utils.serialize import serialize_data, deserialize_data
from . import runners
from . import utils

__all__ = ['Process', 'ProcessState', 'FunctionProcess']


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


class PortNamespace(_WithNonDb, plum.port.PortNamespace):
    pass


class ProcessSpec(plum.process.ProcessSpec):

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


class Process(plum.process.Process):
    """
    This class represents an AiiDA process which can be executed and will
    have full provenance saved in the database.
    """
    __metaclass__ = abc.ABCMeta

    SINGLE_RETURN_LINKNAME = '[return]'
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
        spec.input('store_provenance', valid_type=bool, default=True, non_db=True)
        spec.input('description', valid_type=basestring, required=False, non_db=True)
        spec.input('label', valid_type=basestring, required=False, non_db=True)
        spec.inputs.valid_type = (aiida.orm.Data, aiida.orm.Calculation)
        spec.outputs.valid_type = (aiida.orm.Data)

    @classmethod
    def get_inputs_template(cls):
        return cls.spec().get_inputs_template()

    @classmethod
    def get_or_create_db_record(cls):
        """
        Create a database calculation node that represents what happened in
        this process.
        :return: A calculation
        """
        from aiida.orm.calculation.work import WorkCalculation
        calc = WorkCalculation()
        return calc

    _spec_type = ProcessSpec

    def __init__(self, inputs=None, logger=None, runner=None, parent_pid=None, enable_persistence=True):
        self._runner = runner if runner is not None else runners.get_runner()

        super(Process, self).__init__(
            inputs=inputs,
            logger=logger,
            loop=self._runner.loop,
            communicator=self.runner.communicator)

        self._calc = None
        self._parent_pid = parent_pid
        self._enable_persistence = enable_persistence
        if self._enable_persistence and self.runner.persister is None:
            self.logger.warning(
                "Disabling persistence, runner does not have a persister")
            self._enable_persistence = False

    def on_create(self):
        super(Process, self).on_create()
        # If parent PID hasn't been supplied try to get it from the stack
        if self._parent_pid is None and not plum.stack.is_empty():
            self._parent_pid = plum.stack.top().pid
        self._pid = self._create_and_setup_db_record()

    def init(self):
        super(Process, self).init()
        if self._logger is None:
            self.set_logger(self._calc.logger)

    def has_finished(self):
        """
        Has the process finished i.e. completed running normally, without abort
        or an exception.

        :return: True if finished, False otherwise
        :rtype: bool
        """
        return self.state == ProcessState.FINISHED

    @property
    def calc(self):
        return self._calc

    @override
    def save_instance_state(self, out_state):
        super(Process, self).save_instance_state(out_state)

        if self.inputs.store_provenance:
            assert self.calc.is_stored

        out_state[self.SaveKeys.PARENT_PID.value] = self._parent_pid
        out_state[self.SaveKeys.CALC_ID.value] = self.pid
        out_state['_enable_persistence'] = self._enable_persistence

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

        self._enable_persistence = saved_state['_enable_persistence']

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
    def on_entering(self, state):
        super(Process, self).on_entering(state)
        # Update the node attributes every time we enter a new state
        self.update_node_state(state)
        if self._enable_persistence and not state.is_terminal():
            self.call_soon(self.runner.persister.save_checkpoint, self)

    @override
    def on_terminated(self):
        """
        Called when a Process enters a terminal state.
        """
        super(Process, self).on_terminated()
        if self._enable_persistence:
            try:
                self.runner.persister.delete_checkpoint(self.pid)
            except BaseException as e:
                self.logger.warning("Failed to delete checkpoint: {}\n{}".format(
                    e, traceback.format_exc()))
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
        self.calc._set_attr(WorkCalculation.FAILED_KEY, True)

    @override
    def on_output_emitting(self, output_port, value):
        """
        The process has emitted a value on the given output port.

        :param output_port: The output port name the value was emitted on
        :param value: The value emitted
        """
        super(Process, self).on_output_emitting(output_port, value)
        if not isinstance(value, Data):
            raise TypeError(
                "Values outputted from process must be instances of AiiDA Data " \
                "types.  Got: {}".format(value.__class__)
            )

    # end region

    def submit(self, process, *args, **kwargs):
        return self.runner.submit(process, *args, **kwargs)

    @property
    def runner(self):
        return self._runner

    @protected
    def get_parent_calc(self):
        # Can't get it if we don't know our parent
        if self._parent_pid is None:
            return None

        return load_node(pk=self._parent_pid)

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
        if self.inputs.store_provenance:
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
        Encode input arguments such that they may be saved in a Bundle

        :param inputs: A mapping of the inputs as passed to the process
        :return: The encoded inputs
        """
        return serialize_data(inputs)

    @override
    def decode_input_args(self, encoded):
        """
        Decode saved input arguments as they came from the saved instance state Bundle

        :param encoded: 
        :return: The decoded input args
        """
        return deserialize_data(encoded)

    def update_node_state(self, state):
        self.calc._set_attr(WorkCalculation.PROCESS_STATE_KEY, state.LABEL.value)
        self.update_outputs()

    def update_outputs(self):
        # Link up any new outputs
        new_outputs = set(self.outputs.keys()) - \
                      set(self.calc.get_outputs_dict(link_type=LinkType.RETURN).keys())
        for label in new_outputs:
            value = self.outputs[label]
            # Try making us the creator
            try:
                value.add_link_from(self.calc, label, LinkType.CREATE)
            except ValueError:
                # Must have already been created...nae dramas
                pass

            value.store()
            value.add_link_from(self.calc, label, LinkType.RETURN)

    def _setup_db_record(self):
        assert self.inputs is not None
        assert not self.calc.is_sealed, \
            "Calculation cannot be sealed when setting up the database record"

        # Save the name of this process
        self.calc._set_attr(utils.PROCESS_LABEL_ATTR, self.__class__.__name__)

        parent_calc = self.get_parent_calc()

        for name, input_value in self._flat_inputs().iteritems():

            if isinstance(input_value, Calculation):
                input_value = utils.get_or_create_output_group(input_value)

            if not input_value.is_stored:
                # If the input isn't stored then assume our parent created it
                if parent_calc:
                    input_value.add_link_from(parent_calc, "CREATE", link_type=LinkType.CREATE)
                if self.inputs.store_provenance:
                    input_value.store()

            self.calc.add_link_from(input_value, name)

        if parent_calc:
            self.calc.add_link_from(parent_calc, "CALL",
                                    link_type=LinkType.CALL)

        self._add_description_and_label()

    def _add_description_and_label(self):
        if self.raw_inputs:
            description = self.raw_inputs.get('description', None)
            if description is not None:
                self._calc.description = description
            label = self.raw_inputs.get('label', None)
            if label is not None:
                self._calc.label = label

    def _flat_inputs(self):
        """
        Return a flattened version of the parsed inputs dictionary. The eventual
        keys will be a concatenation of the nested keys

        :return: flat dictionary of parsed inputs
        """
        return dict(self._flatten_inputs(self.spec().inputs, self.inputs))

    def _flatten_inputs(self, port, port_value, parent_name='', separator='_'):
        """
        Function that will recursively flatten the inputs dictionary, omitting inputs for ports that
        are marked as being non database storable

        :param port: port against which to map the port value, can be InputPort or PortNamespace
        :param port_value: value for the current port, can be a Mapping
        :param parent_name: the parent key with which to prefix the keys
        :param separator: character to use for the concatenation of keys
        """
        items = []

        if isinstance(port_value, collections.Mapping):

            for name, value in port_value.iteritems():

                prefixed_key = parent_name + separator + name if parent_name else name

                try:
                    nested_port = port[name]
                except KeyError:
                    # Port does not exist in the port namespace, add it regardless of type of value
                    items.append((prefixed_key, value))
                else:
                    sub_items = self._flatten_inputs(nested_port, value, prefixed_key, separator)
                    items.extend(sub_items)
        else:
            if not port.non_db:
                items.append((parent_name, port_value))

        return items

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
                spec.inputs.dynamic = True
            else:
                spec.inputs.dynamic = False

            # We don't know what a function will return so keep it dynamic
            spec.outputs.valid_type = Data

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

    def __init__(self, *args, **kwargs):
        super(FunctionProcess, self).__init__(
            enable_persistence=False, *args, **kwargs)

    @override
    def _setup_db_record(self):
        super(FunctionProcess, self)._setup_db_record()
        add_source_info(self.calc, self._func)
        # Save the name of the function
        self.calc._set_attr(utils.PROCESS_LABEL_ATTR, self._func.__name__)

    @override
    def _run(self):
        from aiida.orm.data import Data

        args = []

        # Split the inputs into positional and keyword arguments
        args = [None] * len(self._func_args)
        kwargs = {}
        for name, value in self.inputs.items():
            try:
                if self.spec().inputs[name].non_db:
                    # Don't consider non-database inputs
                    continue
            except KeyError:
                pass  # No port found

            # Check if it is a positional arg, if not then keyword
            try:
                args[self._func_args.index(name)] = value
            except ValueError:
                kwargs[name] = value

        result = self._func(*args, **kwargs)
        if result is not None:
            if isinstance(result, Data):
                self.out(self.SINGLE_RETURN_LINKNAME, result)
            elif isinstance(result, collections.Mapping):
                for name, value in result.iteritems():
                    self.out(name, value)
            else:
                raise TypeError(
                    "Workfunction returned unsupported type '{}'\n"
                    "Must be a Data type or a Mapping of {{string: Data}}".
                        format(result.__class__))

        return result
