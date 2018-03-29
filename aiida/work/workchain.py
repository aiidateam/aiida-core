# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

from abc import ABCMeta, abstractmethod
import inspect
from enum import Enum
from aiida.work.defaults import registry
from aiida.work.run import RunningType, RunningInfo
from aiida.work.process import Process, ProcessSpec
from aiida.work.legacy.wait_on import WaitOnWorkflow
from aiida.common.lang import override
from aiida.common.utils import get_class_string, get_object_string, \
    get_object_from_string
from aiida.orm import load_node, load_workflow, Node
from aiida.utils.serialize import serialize_data, deserialize_data
from plum.wait_ons import Checkpoint, WaitOnAll, WaitOnProcess
from plum.wait import WaitOn
from plum.persistence.bundle import Bundle
from collections import namedtuple
from aiida.work.interstep import *
from plum.engine.execution_engine import Future


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


class WorkChain(Process):
    """
    A WorkChain, the base class for AiiDA workflows.
    """
    _spec_type = _WorkChainSpec
    _CONTEXT = 'context'
    _STEPPER_STATE = 'stepper_state'
    _BARRIERS = 'barriers'
    _INTERSTEPS = 'intersteps'
    _ABORTED = 'aborted'

    @classmethod
    def define(cls, spec):
        super(WorkChain, cls).define(spec)
        # For now workchains can accept any input and emit any output
        # If this changes in the future the spec should be updated here.
        spec.dynamic_input()
        spec.dynamic_output()

    class Context(object):
        def __init__(self, value=None):
            # Have to do it this way otherwise our setattr will be called
            # causing infinite recursion.
            # See http://rafekettler.com/magicmethods.html
            super(WorkChain.Context, self).__setattr__('_content', {})

            if value is not None:
                for k, v in value.iteritems():
                    self._content[k] = v

        def _get_dict(self):
            return self._content

        def __getitem__(self, item):
            return self._content[item]

        def __setitem__(self, key, value):
            self._content[key] = value

        def __delitem__(self, key):
            del self._content[key]

        def __getattr__(self, name):
            try:
                return self._content[name]
            except KeyError:
                raise AttributeError("Context does not have a variable {}"
                                     .format(name))

        def __delattr__(self, item):
            del self._content[item]

        def __setattr__(self, name, value):
            self._content[name] = value

        def __dir__(self):
            return sorted(self._content.keys())

        def __iter__(self):
            for k in self._content:
                yield k

        def get(self, key, default=None):
            return self._content.get(key, default)

        def setdefault(self, key, default=None):
            return self._content.setdefault(key, default)

        def save_instance_state(self, out_state):
            for k, v in self._content.iteritems():
                if isinstance(v, Node) and not v.is_stored:
                    v.store()
                out_state[k] = serialize_data(v)

    def __init__(self):
        super(WorkChain, self).__init__()
        self._context = None
        self._stepper = None
        self._barriers = []
        self._intersteps = []

    @property
    def ctx(self):
        return self._context

    @override
    def save_instance_state(self, out_state):
        super(WorkChain, self).save_instance_state(out_state)

        # Ask the context to save itself
        bundle = Bundle()
        self.ctx.save_instance_state(bundle)
        out_state[self._CONTEXT] = bundle

        # Save intersteps
        for interstep in self._intersteps:
            bundle = Bundle()
            interstep.save_instance_state(bundle)
            out_state.setdefault(self._INTERSTEPS, []).append(bundle)

        # Save barriers
        for barrier in self._barriers:
            bundle = Bundle()
            barrier.save_instance_state(bundle)
            out_state.setdefault(self._BARRIERS, []).append(bundle)

        # Ask the stepper to save itself
        if self._stepper is not None:
            bundle = Bundle()
            self._stepper.save_position(bundle)
            out_state[self._STEPPER_STATE] = bundle

        out_state[self._ABORTED] = self._aborted

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

    @property
    def _do_abort(self):
        return self.calc.get_attr(self.calc.DO_ABORT_KEY, False)

    @property
    def _aborted(self):
        return self.calc.get_attr(self.calc.ABORTED_KEY, False)

    @_aborted.setter
    def _aborted(self, value):
        # One is not allowed to unabort an aborted WorkChain
        if self._aborted == True and value == False:
            self.logger.warning('trying to unset the abort flag on an already aborted workchain which is not allowed')
            return

        self.calc._set_attr(self.calc.ABORTED_KEY, value)

    def _do_step(self, wait_on=None):
        self._handle_do_abort()
        if self._aborted:
            return

        for interstep in self._intersteps:
            interstep.on_next_step_starting(self)
        self._intersteps = []
        self._barriers = []

        try:
            finished, retval = self._stepper.step()
        except _PropagateReturn:
            finished, retval = True, None

        # Could have aborted during the step
        self._handle_do_abort()
        if self._aborted:
            return

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
                return WaitOnAll(self._do_step.__name__, self._barriers)
            else:
                return Checkpoint(self._do_step.__name__)

    @override
    def on_create(self, pid, inputs, saved_state):
        super(WorkChain, self).on_create(pid, inputs, saved_state)

        if saved_state is None:
            self._context = self.Context()
        else:
            # Recreate the context
            self._context = self.Context(deserialize_data(saved_state[self._CONTEXT]))

            # Recreate the stepper
            if self._STEPPER_STATE in saved_state:
                self._stepper = self.spec().get_outline().create_stepper(self)
                self._stepper.load_position(
                    saved_state[self._STEPPER_STATE])

            try:
                self._intersteps = [load_with_classloader(b) for
                                    b in saved_state[self._INTERSTEPS]]
            except KeyError:
                self._intersteps = []

            try:
                self._barriers = [WaitOn.create_from(b) for
                                  b in saved_state[self._BARRIERS]]
            except KeyError:
                pass

            self._aborted = saved_state[self._ABORTED]

    def _handle_do_abort(self):
        """
        Check whether a request to abort has been registered, by checking whether the DO_ABORT_KEY
        attribute has been set, and if so call self.abort and remove the DO_ABORT_KEY attribute 
        """
        do_abort = self._do_abort
        if do_abort:
            self.abort(do_abort)
            self.calc._del_attr(self.calc.DO_ABORT_KEY)

    def abort_nowait(self, msg=None):
        """
        Abort the workchain at the next state transition without waiting
        which is achieved by passing a timeout value of zero

        :param msg: The abort message
        :type msg: str
        """
        self.report("Aborting: {}".format(msg))
        self._aborted = True
        self.stop()

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
        self.report("Aborting: {}".format(msg))
        self._aborted = True
        self.stop()


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

    return intersteps


class _InterstepFactory(object):
    """
    Factory to create the appropriate Interstep instance based
    on the class string that was written to the bundle
    """

    def create(self, bundle):
        class_string = bundle[Bundle.CLASS]
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

        :return: A 2-tuple with entries
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
    This class represents an instruction in a a workchain.  To step through the
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
                stepper_pos = Bundle()
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
    def get_description(self, indent_level=0, indent_increment=4):
        indent = ' ' * (indent_level * indent_increment)
        desc = []
        for c in self._commands:
            if isinstance(c, _Instruction):
                desc.append(c.get_description())
            else:
                desc.append('{}* {}'.format(indent, c.__name__))
                if c.__doc__:
                    doc = c.__doc__
                    desc.append('{}{}'.format(indent,doc))

        return '\n'.join(desc)


class _Conditional(object):
    """
    Object that represents some condition with the corresponding body to be
    executed if the condition.
    
    E.g. ::

      if(condition):
        body

    or::

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
            self._pos = -1
            self._current_stepper = None

        def step(self):
            if self._current_stepper is None:
                self._create_stepper()

            # If we can't get a stepper then no conditions match, return
            if self._current_stepper is None:
                return True, None

            finished, retval = self._current_stepper.step()
            if finished:
                self._current_stepper = None
                self._pos = -1

            return finished, retval

        def save_position(self, out_position):
            out_position[self._POSITION] = self._pos
            if self._current_stepper is not None:
                stepper_pos = Bundle()
                self._current_stepper.save_position(stepper_pos)
                out_position[self._STEPPER_POS] = stepper_pos

        def load_position(self, bundle):
            self._pos = bundle[self._POSITION]
            if self._STEPPER_POS in bundle:
                self._create_stepper()
                self._current_stepper.load_position(bundle[self._STEPPER_POS])
            else:
                self._current_stepper = None

        def _create_stepper(self):
            if self._pos == -1:
                self._current_stepper = None
                # Check the conditions until we find one that is true
                for idx, condition in enumerate(self._if_spec.conditionals):
                    if condition.is_true(self._workflow):
                        stepper = condition.body.create_stepper(self._workflow)
                        self._pos = idx
                        self._current_stepper = stepper
                        return
            else:
                branch = self._if_spec.conditionals[self._pos]
                self._current_stepper = branch.body.create_stepper(self._workflow)

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
        description = ['if {}:\n{}'.format(self._ifs[0].condition.__name__, self._ifs[0].body.get_description(indent_level=1))]
        for conditional in self._ifs[1:]:
            description.append('elif {}:\n{}'.format(
                conditional.condition.__name__, conditional.body.get_description(indent_level=1)))
        return '\n'.join(description)


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

            finished, retval = self._stepper.step()
            if finished:
                self._check_condition = True
                self._stepper = None

            # Are we finished looping?
            return self._finished, retval

        def save_position(self, out_position):
            if self._stepper is not None:
                stepper_pos = Bundle()
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
        return "while {}:\n{}".format(self.condition.__name__, self.body.get_description(indent_level=1))


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
