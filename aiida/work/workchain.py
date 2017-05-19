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
from aiida.orm import load_node, load_workflow
from plum.wait_ons import Checkpoint, WaitOnAll, WaitOnProcess
from plum.wait import WaitOn
from plum.persistence.bundle import Bundle
from collections import namedtuple
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
                out_state[k] = v

    def __init__(self):
        super(WorkChain, self).__init__()
        self._context = None
        self._stepper = None
        self._barriers = []
        self._intersteps = ()
        self._aborted = False

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

    @override
    def _run(self, **kwargs):
        self._stepper = self.spec().get_outline().create_stepper(self)
        return self._do_step()

    def _do_step(self, wait_on=None):
        if self._aborted:
            return

        if self._intersteps:
            for i in self._intersteps:
                i.on_next_step_starting(self)
            self._intersteps = ()
        self._barriers = []

        try:
            finished, retval = self._stepper.step()
        except _PropagateReturn:
            finished, retval = True, None

        # Could have aborted during the step
        if self._aborted:
            return

        if not finished:
            if retval is not None:
                if isinstance(retval, tuple):
                    self._intersteps = retval
                elif isinstance(retval, Interstep):
                    self._intersteps = (retval,)
                else:
                    raise TypeError(
                        "Invalid value returned from step '{}'".format(retval))
                for i in self._intersteps:
                    i.on_last_step_finished(self)

            if self._barriers:
                return WaitOnAll(self._do_step.__name__, self._barriers)
            else:
                return Checkpoint(self._do_step.__name__)

    @override
    def on_create(self, pid, inputs, saved_state):
        super(WorkChain, self).on_create(
            pid, inputs, saved_state)

        if saved_state is None:
            self._context = self.Context()
        else:
            # Recreate the context
            self._context = self.Context(saved_state[self._CONTEXT])

            # Recreate the stepper
            if self._STEPPER_STATE in saved_state:
                self._stepper = self.spec().get_outline().create_stepper(self)
                self._stepper.load_position(
                    saved_state[self._STEPPER_STATE])

            try:
                self._intersteps = tuple([Interstep.create_from(b) for
                                          b in saved_state[self._INTERSTEPS]])
            except KeyError:
                pass

            try:
                self._barriers = [WaitOn.create_from(b) for
                                  b in saved_state[self._BARRIERS]]
            except KeyError:
                pass

            self._aborted = saved_state[self._ABORTED]

    def abort_nowait(self, msg=None):
        """
        Abort the workchain at the next state transition without waiting
        which is achieved by passing a timeout value of zero

        :param msg: The abort message
        :type msg: str
        """
        self.report("Aborting: {}".format(msg))
        self._aborted = True

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


class Interstep(object):
    """
    An internstep is an action that is performed between steps of a workchain.
    These allow the user to perform action when a step is finished and when
    the next step (if there is one) is about the start.
    """
    __metaclass__ = ABCMeta

    class BundleKeys(Enum):
        CLASS_NAME = "class_name"

    def on_last_step_finished(self, workchain):
        """
        Called when the last step has finished

        :param workchain: The workchain this interstep belongs to
        :type workchain: :class:`WorkChain`
        """
        pass

    def on_next_step_starting(self, workchain):
        """
        Called when the next step is about to start

        :param workchain: The workchain this interstep belongs to
        :type workchain: :class:`WorkChain`
        """
        pass

    @abstractmethod
    def save_instance_state(self, out_state):
        """
        Save the state of this interstep so that it can be recreated later
        by the factory.

        :param out_state: The bundle that should be used to save the state
          (of type plum.persistence.bundle.Bundle).
        """
        out_state[self.BundleKeys.CLASS_NAME.value] = get_class_string(self)

    @classmethod
    def create_from(cls, bundle):
        """
        Recreate an instance of the interstep from a bundle containing
        the saved instance state

        :param bundle: The bundle that contains the saved instance state
          (of type plum.persistence.bundle.Bundle).
        """
        assert cls.BundleKeys.CLASS_NAME.value in bundle

        class_name = bundle[cls.BundleKeys.CLASS_NAME.value]
        InterstepClass = bundle.get_class_loader().load_class(class_name)

        return InterstepClass.create_from(bundle)


_Action = namedtuple("_Action", "running_info fn")


class ToContext(Interstep):
    """
    Class to wrap future objects and return them in a WorkChain step.
    """
    TO_ASSIGN = 'to_assign'
    WAITING_ON = 'waiting_on'

    @classmethod
    def action_from_running_info(cls, running_info):
        if running_info.type is RunningType.PROCESS:
            return Calc(running_info)
        elif running_info.type is RunningType.LEGACY_CALC or \
                        running_info.type is RunningType.LEGACY_WORKFLOW:
            return Legacy(running_info)
        else:
            raise ValueError("Unknown running type '{}'".format(running_info.type))

    def __init__(self, **kwargs):
        self._to_assign = {}
        for key, val in kwargs.iteritems():
            if isinstance(val, _Action):
                self._to_assign[key] = val
            elif isinstance(val, RunningInfo):
                self._to_assign[key] = self.action_from_running_info(val)
            elif isinstance(val, Future):
                self._to_assign[key] = \
                    Calc(RunningInfo(RunningType.PROCESS, val.pid))
            else:
                # Assume it's a pk
                self._to_assign[key] = Legacy(val)

    @override
    def on_last_step_finished(self, workchain):
        for action in self._to_assign.itervalues():
            workchain.insert_barrier(self._create_wait_on(action))

    @override
    def on_next_step_starting(self, workchain):
        for key, action in self._to_assign.iteritems():
            fn = get_object_from_string(action.fn)
            workchain.ctx[key] = fn(action.running_info.pid)

    @override
    def save_instance_state(self, out_state):
        super(ToContext, self).save_instance_state(out_state)
        out_state[self.TO_ASSIGN] = self._to_assign

    @classmethod
    def create_from(cls, bundle):
        instance = cls.__new__(cls)
        instance._to_assign = bundle[cls.TO_ASSIGN]
        return instance

    def _create_wait_on(self, action):
        rinfo = action.running_info
        if rinfo.type is RunningType.LEGACY_CALC \
                or rinfo.type is RunningType.PROCESS:
            return WaitOnProcess(None, rinfo.pid)
        elif rinfo.type is RunningType.LEGACY_WORKFLOW:
            return WaitOnWorkflow(None, rinfo.pid)


def _get_proc_outputs_from_registry(pid):
    return registry.get_outputs(pid)


def _get_wf_outputs(pk):
    return load_workflow(pk=pk).get_results()


def Calc(running_info):
    return _Action(running_info, get_object_string(load_node))


def Wf(running_info):
    return _Action(
        running_info, get_object_string(load_workflow))


def Legacy(object):
    if object.type == RunningType.LEGACY_CALC or \
                    object.type == RunningType.PROCESS:
        return Calc(object)
    elif object.type is RunningType.LEGACY_WORKFLOW:
        return Wf(object)

    raise ValueError("Could not determine object to be calculation or workflow")


def Outputs(running_info):
    if isinstance(running_info, Future):
        # Create the correct information from the future
        rinfo = RunningInfo(RunningType.PROCESS, running_info.pid)
        return _Action(
            rinfo, get_object_string(_get_proc_outputs_from_registry))
    elif running_info.type == RunningType.PROCESS or running_info.type == RunningType.LEGACY_CALC:
        return _Action(
            running_info, get_object_string(_get_proc_outputs_from_registry))
    elif running_info.type is RunningType.LEGACY_WORKFLOW:
        return _Action(
            running_info, get_object_string(_get_wf_outputs))


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
                stepper_pos = Bundle()
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
