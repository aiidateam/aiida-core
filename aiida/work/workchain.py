# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

import apricotpy
from copy import deepcopy
import inspect
import uuid
from collections import namedtuple, Mapping, Sequence, Set
from plum.wait_ons import Checkpoint, WaitOnAll
from aiida.orm import Node
from aiida.work.process import Process, ProcessSpec
from aiida.work.utils import WithHeartbeat
from aiida.common.utils import get_class_string
from aiida.work.interstep import *

__all__ = ['WorkChain']


class _WorkChainSpec(ProcessSpec):
    def __init__(self):
        super(_WorkChainSpec, self).__init__()
        self._outline = None

    def get_description(self):
        desc = [super(_WorkChainSpec, self).get_description()]
        if self._outline:
            desc.append("Outline")
            desc.append("=======")
            desc.append(self._outline.get_description())

        return "\n".join(desc)

    def outline(self, *commands):
        """
        Define the outline that describes this work chain.

        :param commands: One or more functions that make up this work chain.
        """
        self._outline = commands \
            if isinstance(commands, _Instruction) else _Block(commands)

    def get_outline(self):
        return self._outline


def serialise_value(value):
    """
    Convert a value to a format that can be serialised.  In practice this means
    converting Nodes to UUIDs, Mapping and Sequence values that are Nodes to UUIDs
     
    .. note::
        Deepcopies are created for all values passed.
        
    :param value: The value to convert (if it falls into above criteria)
    :return: A UUID, a copy of the mapping given with UUIDs as values where 
        appropriate or similarly for a sequence.
    """
    if isinstance(value, Node):
        return uuid.UUID(value.uuid)
    elif isinstance(value, Mapping):
        return value.__class__((k, serialise_value(v)) for k, v in value.iteritems())
    elif isinstance(value, (Sequence, Set)):
        return value.__class__(serialise_value(v) for v in value)
    else:
        return deepcopy(value)


def deserialise_value(value):
    if isinstance(value, uuid.UUID):
        try:
            return load_node(uuid=value)
        except ValueError:
            return deepcopy(value)
    if isinstance(value, Mapping):
        return value.__class__((k, deserialise_value(v)) for k, v in value.iteritems())
    elif isinstance(value, (Sequence, Set)):
        return value.__class__(deserialise_value(v) for v in value)
    else:
        return deepcopy(value)


class WorkChain(apricotpy.ContextMixin, Process, WithHeartbeat):
    """
    A WorkChain, the base class for AiiDA workflows.
    """
    _spec_type = _WorkChainSpec
    _CONTEXT = 'context'
    _STEPPER_STATE = 'stepper_state'
    _INTERSTEPS = 'intersteps'

    @classmethod
    def define(cls, spec):
        super(WorkChain, cls).define(spec)
        # For now workchains can accept any input and emit any output
        # If this changes in the future the spec should be updated here.
        spec.dynamic_input()
        spec.dynamic_output()

    def __init__(self, loop, inputs=None, pid=None, logger=None):
        super(WorkChain, self).__init__(loop, inputs, pid, logger)
        self._stepper = None
        self._barriers = []
        self._intersteps = []

    @override
    def save_instance_state(self, out_state):
        super(WorkChain, self).save_instance_state(out_state)
        # Ask the stepper to save itself
        if self._stepper is not None:
            stepper_state = apricotpy.Bundle()
            self._stepper.save_position(stepper_state)
            out_state[self._STEPPER_STATE] = stepper_state

    def insert_barrier(self, wait_on):
        """
        Insert a barrier that will cause the workchain to wait until the wait
        on is finished before continuing to the next step.

        :param wait_on: The thing to wait on (of type plum.wait.wait_on)
        """
        self._barriers.append(wait_on)

    def remove_barrier(self, wait_on):
        """
        Remove a barrier.

        Precondition: must be a barrier that was previously inserted

        :param wait_on:  The wait on to remove (of type plum.wait.wait_on)
        """
        del self._barriers[wait_on]

    def insert_intersteps(self, intersteps):
        """
        Insert an interstep to be executed after the current step
        ends but before the next step ends

        :param interstep: class:Interstep
        """
        if not isinstance(intersteps, list):
            intersteps = [intersteps]

        for interstep in intersteps:
            self._intersteps.append(interstep)

    def to_context(self, **kwargs):
        """
        This is a convenience method that provides syntactic sugar, for
        a user to add multiple intersteps that will assign a certain value
        to the corresponding key in the context of the workchain
        """
        intersteps = []
        for key, value in kwargs.iteritems():

            if not isinstance(value, UpdateContextBuilder):
                value = assign_(value)

            interstep = value.build(key)
            intersteps.append(interstep)

        self.insert_intersteps(intersteps)

    @override
    def _run(self, **kwargs):
        self._stepper = self.spec().get_outline().create_stepper(self)
        return self._do_step()

    def _do_step(self, wait_on=None):
        for interstep in self._intersteps:
            interstep.on_next_step_starting(self)
        self._intersteps = []
        self._barriers = []

        try:
            finished, retval = self._stepper.start()
        except _PropagateReturn:
            finished, retval = True, None

        if not finished:
            if retval is not None:
                if isinstance(retval, list) and all(isinstance(interstep, Interstep) for interstep in retval):
                    self.insert_intersteps(retval)
                elif isinstance(retval, Interstep):
                    self.insert_intersteps(retval)
                else:
                    raise TypeError(
                        "Invalid value returned from step '{}'".format(retval))

            for interstep in self._intersteps:
                interstep.on_last_step_finished(self)

            if self._barriers:
                return self.loop().create(WaitOnAll, self._barriers), self._do_step
            else:
                return self.loop().create(Checkpoint), self._do_step

    @override
    def load_instance_state(self, saved_state, logger=None):
        super(WorkChain, self).load_instance_state(saved_state, logger)
        # Recreate the stepper
        if self._STEPPER_STATE in saved_state:
            self._stepper = self.spec().get_outline().create_stepper(self)
            self._stepper.load_position(
                saved_state[self._STEPPER_STATE])
        else:
            self._stepper = None

        try:
            self._intersteps = [_INTERSTEP_FACTORY.create(b) for
                                b in saved_state[self._INTERSTEPS]]
        except KeyError:
            self._intersteps = []

    def abort_nowait(self, msg=None):
        """
        Abort the workchain at the next state transition without waiting
        which is achieved by passing a timeout value of zero

        :param msg: The abort message
        :type msg: str
        """
        self.abort(msg=msg, timeout=0)

    def abort(self, msg=None, timeout=None):
        """
        Abort the workchain by calling the abort method of the Process and
        also adding the abort message to the report

        :param msg: The abort message
        :type msg: str
        :param timeout: Wait for the given time until the process has aborted
        :type timeout: float
        :return: True if the process is aborted at the end of the function, False otherwise
        """
        aborted = super(WorkChain, self).abort(msg, timeout)
        self.report("Aborting: {}".format(msg))
        return aborted


def ToContext(**kwargs):
    """
    Utility function that returns a list of UpdateContext Interstep instances

    NOTE: This is effectively a copy of WorkChain.to_context method added to
    keep backwards compatibility, but should eventually be deprecated
    """
    intersteps = []
    for key, value in kwargs.iteritems():

        if not isinstance(value, UpdateContextBuilder):
            value = assign_(value)

        interstep = value.build(key)
        intersteps.append(interstep)

        # if isinstance(value, Action):
        #     pass
        # elif isinstance(value, RunningInfo):
        #     value = action_from_running_info(value)
        # elif isinstance(value, Future):
        #     value = Calc(RunningInfo(RunningType.PROCESS, value.pid))
        # else:
        #     value = Legacy(value)

        # if not isinstance(value, Action):
        #     raise ValueError("the values in the kwargs need to be of type Action")

        # if key not in self.ctx:
        #     interstep = Assign(key, value)
        # elif isinstance(self.ctx[key], list):
        #     interstep = Append(key, value)
        # else:
        #     interstep = Assign(key, value)

        # intersteps.append(interstep)

    return intersteps


class _InterstepFactory(object):
    def create(self, bundle):
        class_string = bundle['class']
        if class_string == get_class_string(ToContext):
            return ToContext(**bundle[ToContext.TO_ASSIGN])
        else:
            raise ValueError(
                "Unknown interstep class type '{}'".format(class_string))


_INTERSTEP_FACTORY = _InterstepFactory()


class Stepper(object):
    __metaclass__ = ABCMeta

    def __init__(self, workflow):
        self._workflow = workflow

    @abstractmethod
    def step(self):
        """
        Execute on step of the instructions.
        :return: A 2-tuple with entries:
            0. True if the stepper has finished, False otherwise
            1. The return value from the executed step
        :rtype: tuple
        """
        pass

    @abstractmethod
    def save_position(self, out_position):
        pass

    @abstractmethod
    def load_position(self, bundle):
        pass


class _Instruction(object):
    """
    This class represents an instruction in a workchain. To step through the
    step you need to get a stepper by calling ``create_stepper()`` from which
    you can call the :class:`~Stepper.step()` method.
    """
    __metaclass__ = ABCMeta

    @abstractmethod
    def create_stepper(self, workflow):
        pass

    def __str__(self):
        return self.get_description()

    @abstractmethod
    def get_description(self):
        """
        Get a text description of these instructions.
        :return: The description
        :rtype: str
        """
        pass

    @staticmethod
    def check_command(command):
        if not isinstance(command, _Instruction):
            assert issubclass(command.im_class, Process)
            args = inspect.getargspec(command)[0]
            assert len(args) == 1, "Instruction must take one argument only: self"


class _Block(_Instruction):
    """
    Represents a block of instructions i.e. a sequential list of instructions.
    """

    class Stepper(Stepper):
        _POSITION = 'pos'
        _STEPPER_POS = 'stepper_pos'

        def __init__(self, workflow, commands):
            super(_Block.Stepper, self).__init__(workflow)

            for c in commands:
                _Instruction.check_command(c)
            self._commands = commands
            self._current_stepper = None
            self._pos = 0

        def step(self):
            assert self._pos != len(self._commands), \
                "Can't call step after the block is finished"

            command = self._commands[self._pos]

            if self._current_stepper is None and isinstance(command, _Instruction):
                self._current_stepper = command.create_stepper(self._workflow)

            # If there is a stepper being used then call that, otherwise just
            # call the command (class function) directly
            if self._current_stepper is not None:
                finished, retval = self._current_stepper.step()
            else:
                finished, retval = True, command(self._workflow)

            if finished:
                self._pos += 1
                self._current_stepper = None

            return self._pos == len(self._commands), retval

        def save_position(self, out_position):
            out_position[self._POSITION] = self._pos
            # Save the position of the current step we're working (if it's not a
            # direct function)
            if self._current_stepper is not None:
                stepper_pos = apricotpy.Bundle()
                self._current_stepper.save_position(stepper_pos)
                out_position[self._STEPPER_POS] = stepper_pos

        def load_position(self, bundle):
            self._pos = bundle[self._POSITION]

            # Do we have a stepper position to load?
            if self._STEPPER_POS in bundle:
                self._current_stepper = \
                    self._commands[self._pos].create_stepper(self._workflow)
                self._current_stepper.load_position(bundle[self._STEPPER_POS])

    def __init__(self, commands):
        for command in commands:
            if not isinstance(command, _Instruction):
                # Maybe it's a simple method
                if not inspect.ismethod(command):
                    raise ValueError(
                        "Workflow commands {} is not a class method.".
                            format(command))
        self._commands = commands

    @override
    def create_stepper(self, workflow):
        return self.Stepper(workflow, self._commands)

    @override
    def get_description(self):
        desc = []
        for c in self._commands:
            if isinstance(c, _Instruction):
                desc.append(c.get_description())
            else:
                if c.__doc__:
                    doc = "\n" + c.__doc__
                    doc.replace('\n', '    \n')
                    desc.append("::\n{}\n::".format(doc))
                desc.append(c.__name__)

        return "\n".join(desc)


class _Conditional(object):
    """
    Object that represents some condition with the corresponding body to be
    executed if the condition is met e.g.:
    if(condition):
      body

    or

    while(condition):
      body
    """

    def __init__(self, parent, condition):
        self._parent = parent
        self._condition = condition
        self._body = None

    @property
    def body(self):
        return self._body

    @property
    def condition(self):
        return self._condition

    def is_true(self, workflow):
        return self._condition(workflow)

    def __call__(self, *commands):
        assert self._body is None
        self._body = _Block(commands)
        return self._parent


class _If(_Instruction):
    class Stepper(Stepper):
        _POSITION = 'pos'
        _STEPPER_POS = 'stepper_pos'

        def __init__(self, workflow, if_spec):
            super(_If.Stepper, self).__init__(workflow)
            self._if_spec = if_spec
            self._pos = 0
            self._current_stepper = None

        def step(self):
            if self._current_stepper is None:
                stepper = self._get_next_stepper()
                # If we can't get a stepper then no conditions match, return
                if stepper is None:
                    return True, None
                self._current_stepper = stepper

            finished, retval = self._current_stepper.step()
            if finished:
                self._current_stepper = None
            else:
                self._pos += 1

            return finished, retval

        def save_position(self, out_position):
            out_position[self._POSITION] = self._pos
            if self._current_stepper is not None:
                stepper_pos = apricotpy.Bundle()
                self._current_stepper.save_position(stepper_pos)
                out_position[self._STEPPER_POS] = stepper_pos

        def load_position(self, bundle):
            self._pos = bundle[self._POSITION]
            if self._STEPPER_POS in bundle:
                self._current_stepper = self._get_next_stepper()
                self._current_stepper.load_position(bundle[self._STEPPER_POS])

        def _get_next_stepper(self):
            # Check the conditions until we find that that is true
            for conditional in self._if_spec.conditionals[self._pos:]:
                if conditional.is_true(self._workflow):
                    return conditional.body.create_stepper(self._workflow)
            return None

    def __init__(self, condition):
        super(_If, self).__init__()
        self._ifs = [_Conditional(self, condition)]
        self._sealed = False

    def __call__(self, *commands):
        """
        This is how the commands for the if(...) body are set
        :param commands: The commands to run on the original if.
        :return: This instance.
        """
        self._ifs[0](*commands)
        return self

    def elif_(self, condition):
        self._ifs.append(_Conditional(self, condition))
        return self._ifs[-1]

    def else_(self, *commands):
        assert not self._sealed
        # Create a dummy conditional that always returns True
        cond = _Conditional(self, lambda wf: True)
        cond(*commands)
        self._ifs.append(cond)
        # Can't do any more after the else
        self._sealed = True
        return self

    def create_stepper(self, workflow):
        return self.Stepper(workflow, self)

    @property
    def conditionals(self):
        return self._ifs

    @override
    def get_description(self):
        description = [
            "if {}:\n{}".format(
                self._ifs[0].condition.__name__, self._ifs[0].body)]
        for conditional in self._ifs[1:]:
            description.append("elif {}:\n{}".format(
                conditional.condition.__name__, conditional.body))
        return "\n".join(description)


class _While(_Conditional, _Instruction):
    class Stepper(Stepper):
        _STEPPER_POS = 'stepper_pos'
        _CHECK_CONDITION = 'check_condition'
        _FINISHED = 'finished'

        def __init__(self, workflow, while_spec):
            super(_While.Stepper, self).__init__(workflow)
            self._spec = while_spec
            self._stepper = None
            self._check_condition = True
            self._finished = False

        def step(self):
            assert not self._finished, \
                "Can't call step after the loop has finished"

            # Do we need to check the condition?
            if self._check_condition is True:
                self._check_condition = False
                # Should we go into the loop body?
                if self._spec.is_true(self._workflow):
                    self._stepper = \
                        self._spec.body.create_stepper(self._workflow)
                else:  # Nope...
                    self._finished = True
                    return True, None

            finished, retval = self._stepper.start()
            if finished:
                self._check_condition = True
                self._stepper = None

            # Are we finished looping?
            return self._finished, retval

        def save_position(self, out_position):
            if self._stepper is not None:
                stepper_pos = apricotpy.Bundle()
                self._stepper.save_position(stepper_pos)
                out_position[self._STEPPER_POS] = stepper_pos
            out_position[self._CHECK_CONDITION] = self._check_condition
            out_position[self._FINISHED] = self._finished

        def load_position(self, bundle):
            if self._STEPPER_POS in bundle:
                self._stepper = self._spec.body.create_stepper(self._workflow)
                self._stepper.load_position(bundle[self._STEPPER_POS])
            self._finished = bundle[self._FINISHED]
            self._check_condition = bundle[self._CHECK_CONDITION]

        @property
        def _body_stepper(self):
            if self._stepper is None:
                self._stepper = \
                    self._spec.body.create_stepper(self._workflow)
            return self._stepper

    def __init__(self, condition):
        super(_While, self).__init__(self, condition)

    @override
    def create_stepper(self, workflow):
        return self.Stepper(workflow, self)

    @override
    def get_description(self):
        return "while {}:\n{}".format(self.condition.__name__, self.body)


class _PropagateReturn(BaseException):
    pass


class _ReturnStepper(Stepper):
    def step(self):
        """
        Execute on step of the instructions.
        :return: A 2-tuple with entries:
            0. True if the stepper has finished, False otherwise
            1. The return value from the executed step
        :rtype: tuple
        """
        raise _PropagateReturn()

    def save_position(self, out_position):
        return

    def load_position(self, bundle):
        """
        Nothing to be done: no internal state.
        :param bundle:
        :return:
        """
        return


class _Return(_Instruction):
    """
    A return instruction to tell the workchain to stop stepping through the
    outline and cease execution immediately.
    """

    def create_stepper(self, workflow):
        return _ReturnStepper(workflow)

    def get_description(self):
        """
        Get a text description of these instructions.
        :return: The description
        :rtype: str
        """
        return "Return from the outline immediately"


def if_(condition):
    """
    A conditional that can be used in a workchain outline.

    Use as::

      if_(cls.conditional)(
        cls.step1,
        cls.step2
      )

    Each step can, of course, also be any valid workchain step e.g. conditional.

    :param condition: The workchain method that will return True or False
    """
    return _If(condition)


def while_(condition):
    """
    A while loop that can be used in a workchain outline.

    Use as::

      while_(cls.conditional)(
        cls.step1,
        cls.step2
      )

    Each step can, of course, also be any valid workchain step e.g. conditional.

    :param condition: The workchain method that will return True or False
    """
    return _While(condition)


# Global singleton for return statements in workchain outlines
return_ = _Return()
