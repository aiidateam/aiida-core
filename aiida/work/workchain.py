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
import collections
import functools
import inspect
import re
import plumpy
import plumpy.workchains

from aiida.common.extendeddicts import AttributeDict
from aiida.orm.utils import load_node, load_workflow
from aiida.common.lang import override
from aiida.common.exceptions import MultipleObjectsError, NotExistent
from aiida.utils.serialize import serialize_data, deserialize_data
from . import processes
from .awaitable import *
from .context import *

__all__ = ['WorkChain', 'if_', 'while_', 'return_', 'ToContext', 'Outputs', '_WorkChainSpec']


class _WorkChainSpec(processes.ProcessSpec):
    def __init__(self):
        super(_WorkChainSpec, self).__init__()
        self._outline = None

    def get_description(self):
        description = super(_WorkChainSpec, self).get_description()

        if self._outline:
            description['outline'] = self._outline.get_description()

        return description

    def outline(self, *commands):
        """
        Define the outline that describes this work chain.

        :param commands: One or more functions that make up this work chain.
        """
        self._outline = commands \
            if isinstance(commands, _Instruction) else _Block(commands)

    def get_outline(self):
        return self._outline


class WorkChain(processes.Process):
    """
    A WorkChain, the base class for AiiDA workflows.
    """
    _spec_type = _WorkChainSpec
    _STEPPER_STATE = 'stepper_state'
    _CONTEXT = 'CONTEXT'

    @classmethod
    def define(cls, spec):
        super(WorkChain, cls).define(spec)
        # For now workchains can accept any input and emit any output
        # If this changes in the future the spec should be updated here.
        spec.inputs.dynamic = True
        spec.outputs.dynamic = True

    def __init__(self, inputs=None, logger=None, runner=None):
        super(WorkChain, self).__init__(inputs=inputs, logger=logger, runner=runner)
        self._stepper = None
        self._awaitables = []
        self._context = AttributeDict()

    @property
    def ctx(self):
        return self._context

    @override
    def save_instance_state(self, out_state):
        super(WorkChain, self).save_instance_state(out_state)
        # Save the context
        out_state[self._CONTEXT] = serialize_data(self.ctx.__dict__)

        # Ask the stepper to save itself
        if self._stepper is not None:
            out_state[self._STEPPER_STATE] = self._stepper.save()

    @override
    def load_instance_state(self, saved_state, load_context):
        super(WorkChain, self).load_instance_state(saved_state, load_context)
        # Load the context
        self._context = AttributeDict(**deserialize_data(saved_state[self._CONTEXT]))

        # Recreate the stepper
        self._stepper = None
        stepper_state = saved_state.get(self._STEPPER_STATE, None)
        if stepper_state is not None:
            self._stepper = self.spec().get_outline().recreate_stepper(stepper_state, self)

        self.set_logger(self._calc.logger)

    def insert_awaitable(self, awaitable):
        """
        Insert a awaitable that will cause the workchain to wait until the wait
        on is finished before continuing to the next step.

        :param awaitable: The thing to await
        :type awaitable: :class:`aiida.work.awaitable.Awaitable`
        """
        self._awaitables.append(awaitable)

    def remove_awaitable(self, awaitable):
        """
        Remove a awaitable.

        Precondition: must be a awaitable that was previously inserted

        :param awaitable: The awaitable to remove
        """
        self._awaitables.remove(awaitable)

    def to_context(self, **kwargs):
        """
        This is a convenience method that provides syntactic sugar, for
        a user to add multiple intersteps that will assign a certain value
        to the corresponding key in the context of the workchain
        """
        for key, value in kwargs.iteritems():
            awaitable = construct_awaitable(value)
            awaitable.key = key
            self.insert_awaitable(awaitable)

    @override
    def _run(self):
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
        if self._aborted and value == False:
            self.logger.warning('trying to unset the abort flag on an already aborted workchain which is not allowed')
            return

        self.calc._set_attr(self.calc.ABORTED_KEY, value)

    def _do_step(self, wait_on=None):
        self._awaitables = []

        if self._handle_do_abort():
            return

        try:
            finished, retval = self._stepper.step()
        except _PropagateReturn:
            finished, retval = True, None

        # Could have aborted during the step
        if self._handle_do_abort():
            return

        if not finished:
            if retval is not None:
                if isinstance(retval, ToContext):
                    self.to_context(**retval)
                else:
                    raise TypeError("Invalid value returned from step '{}'".format(retval))

            if self._awaitables:
                return plumpy.Wait(self._do_step, 'Waiting before next step')
            else:
                return plumpy.Continue(self._do_step)
        else:
            return self.outputs

    def on_wait(self, awaitables):
        super(WorkChain, self).on_wait(awaitables)
        if self._awaitables:
            self.action_awaitables()
        else:
            self.call_soon(self.resume)

    def abort(self, message=None):
        """
        Cancel is the new abort, just like orange is the new black
        """
        self.calc.kill()
        self.report(message)
        self.cancel(message)

    def _handle_do_abort(self):
        """
        Check whether a request to abort has been registered, by checking whether the DO_ABORT_KEY
        attribute has been set, and if so call self.abort and remove the DO_ABORT_KEY attribute 
        """
        do_abort = self._do_abort
        if do_abort:
            self.cancel(do_abort)
            self.calc._del_attr(self.calc.DO_ABORT_KEY)
            return True
        return False

    def abort_nowait(self, message=None):
        """
        Abort the workchain at the next state transition without waiting
        which is achieved by passing a timeout value of zero

        :param message: The abort message
        :type message: str
        """
        return self.abort(message=message)

    def action_awaitables(self):
        """
        Handle the awaitables that are currently registered with the workchain

        Depending on the class type of the awaitable's target a different callback
        function will be bound with the awaitable and the runner will be asked to
        call it when the target is completed
        """
        for awaitable in self._awaitables:
            if awaitable.target == AwaitableTarget.CALCULATION:
                fn = functools.partial(self.on_calculation_finished, awaitable)
                self.runner.call_on_calculation_finish(awaitable.pk, fn)
            elif awaitable.target == AwaitableTarget.WORKFLOW:
                fn = functools.partial(self.on_legacy_workflow_finished, awaitable)
                self.runner.call_on_legacy_workflow_finish(awaitable.pk, fn)
            else:
                assert "invalid awaitable target '{}'".format(awaitable.target)

    def on_calculation_finished(self, awaitable, pk):
        """
        Callback function called by the runner when the calculation instance identified by pk
        is completed. The awaitable will be effectuated on the context of the workchain and
        removed from the internal list. If all awaitables have been dealt with, the workchain
        process is resumed

        :param awaitable: an Awaitable instance
        :param pk: the pk of the awaitable's target
        """
        try:
            node = load_node(pk)
        except (MultipleObjectsError, NotExistent) as exception:
            raise ValueError('provided pk<{}> could not be resolved to a valid Node instance'.format(pk))

        if awaitable.outputs:
            value = node.get_outputs_dict()
        else:
            value = node

        if awaitable.action == AwaitableAction.ASSIGN:
            self.ctx[awaitable.key] = value
        elif awaitable.action == AwaitableAction.APPEND:
            self.ctx.setdefault(awaitable.key, []).append(value)
        else:
            assert "invalid awaitable action '{}'".format(awaitable.action)

        self.remove_awaitable(awaitable)
        if self.state == processes.ProcessState.WAITING and len(self._awaitables) == 0:
            self.resume()

    def on_legacy_workflow_finished(self, awaitable, pk):
        """
        Callback function called by the runner when the legacy workflow instance identified by pk
        is completed. The awaitable will be effectuated on the context of the workchain and
        removed from the internal list. If all awaitables have been dealt with, the workchain
        process is resumed

        :param awaitable: an Awaitable instance
        :param pk: the pk of the awaitable's target
        """
        try:
            workflow = load_workflow(pk=pk)
        except ValueError as exception:
            raise ValueError('provided pk<{}> could not be resolved to a valid Workflow instance'.format(pk))

        if awaitable.outputs:
            value = workflow.get_results()
        else:
            value = workflow

        if awaitable.action == AwaitableAction.ASSIGN:
            self.ctx[awaitable.key] = value
        elif awaitable.action == AwaitableAction.APPEND:
            self.ctx.setdefault(awaitable.key, []).append(value)
        else:
            assert "invalid awaitable action '{}'".format(awaitable.action)

        self.remove_awaitable(awaitable)
        if self.state == processes.ProcessState.WAITING and len(self._awaitables) == 0:
            self.resume()


class Stepper(plumpy.Savable):
    __metaclass__ = abc.ABCMeta

    def __init__(self, workchain):
        self._workchain = workchain

    def load_instance_state(self, saved_state, workchain):
        super(Stepper, self).load_instance_state(saved_state)
        self._workchain = workchain

    @abc.abstractmethod
    def step(self):
        """
        Execute on step of the instructions.
        :return: A 2-tuple with entries:
            0. True if the stepper has finished, False otherwise
            1. The return value from the executed step
        :rtype: tuple
        """
        pass


class _Instruction(object):
    """
    This class represents an instruction in a workchain. To step through the
    step you need to get a stepper by calling ``create_stepper()`` from which
    you can call the :class:`~Stepper.step()` method.
    """
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def create_stepper(self, workchain):
        """ Create a new stepper for this instruction """
        pass

    @abc.abstractmethod
    def recreate_stepper(self, saved_state, workchain):
        """ Recreate a stepper from a previously saved state """
        pass

    def __str__(self):
        return str(self.get_description())

    @abc.abstractmethod
    def get_description(self):
        """
        Get a text description of these instructions.
        :return: The description
        :rtype: dict or str
        """
        pass


class _FunctionStepper(Stepper):
    def __init__(self, workchain, fn):
        super(_FunctionStepper, self).__init__(workchain)
        self._fn = fn

    def save_instance_state(self, out_state):
        super(_FunctionStepper, self).save_instance_state(out_state)
        out_state['_fn'] = self._fn.__name__

    def load_instance_state(self, saved_state, workchain):
        super(_FunctionStepper, self).load_instance_state(saved_state, workchain)
        self._fn = getattr(workchain, saved_state['_fn'])

    def step(self):
        return True, self._fn(self._workchain)


class _FunctionCall(_Instruction):
    def __init__(self, func):
        assert issubclass(func.im_class, processes.Process)
        args = inspect.getargspec(func)[0]
        assert len(args) == 1, "Step must take one argument only: self"

        self._fn = func

    def create_stepper(self, workchain):
        return _FunctionStepper(workchain, self._fn)

    def recreate_stepper(self, saved_state, workchain):
        return _FunctionStepper(workchain, self._fn)

    def get_description(self):
        desc = self._fn.__name__
        if self._fn.__doc__:
            doc = re.sub(r'\n\s*', ' ', c.__doc__).strip()
            desc += "({})".format(doc)

        return desc


STEPPER_STATE = 'stepper_state'


@plumpy.auto_persist('_pos')
class _BlockStepper(Stepper):
    def __init__(self, block, workchain):
        super(_BlockStepper, self).__init__(workchain)
        self._block = block
        self._pos = 0
        self._child_stepper = self._block[0].create_stepper(self._workchain)

    def step(self):
        assert not self.finished(), "Can't call step after the block is finished"

        finished, result = self._child_stepper.step()
        if finished:
            self.next_instruction()

        return self.finished(), result

    def next_instruction(self):
        assert not self.finished()
        self._pos += 1
        if self.finished():
            self._child_stepper = None
        else:
            self._child_stepper = self._block[self._pos].create_stepper(self._workchain)

    def finished(self):
        return self._pos == len(self._block)

    def save_instance_state(self, out_state):
        super(_BlockStepper, self).save_instance_state(out_state)
        if self._child_stepper is not None:
            out_state[STEPPER_STATE] = self._child_stepper.save()

    def load_instance_state(self, saved_state, block, workchain):
        super(_BlockStepper, self).load_instance_state(saved_state, workchain)
        self._block = block
        stepper_state = saved_state.get(STEPPER_STATE, None)
        self._child_stepper = None
        if stepper_state is not None:
            self._child_stepper = self._block[self._pos].recreate_stepper(stepper_state)


class _Block(_Instruction, collections.Sequence):
    """
    Represents a block of instructions i.e. a sequential list of instructions.
    """

    def __init__(self, instructions):
        # Build up the list of commands
        comms = []
        for instruction in instructions:
            if inspect.ismethod(instruction):
                # It's a plain method of the workchain
                instruction = _FunctionCall(instruction)
            elif not isinstance(instruction, _Instruction):
                raise ValueError("Workflow commands {} is not an instruction or class method.".format(instruction))

            comms.append(instruction)
        self._instruction = comms

    def __getitem__(self, index):
        return self._instruction[index]

    def __len__(self):
        return len(self._instruction)

    @override
    def create_stepper(self, workchain):
        return _BlockStepper(self, workchain)

    @override
    def recreate_stepper(self, saved_state, workchain):
        return _BlockStepper.recreate_from(saved_state, self, workchain)

    @override
    def get_description(self):
        return [instruction.get_description() for instruction in self._instruction]

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

    def __init__(self, parent, predicate):
        self._parent = parent
        self._predicate = predicate
        self._body = None

    @property
    def body(self):
        return self._body

    @property
    def predicate(self):
        return self._predicate

    def is_true(self, workflow):
        return self._predicate(workflow)

    def __call__(self, *instructions):
        assert self._body is None
        self._body = _Block(instructions)
        return self._parent


@plumpy.auto_persist('_pos')
class _IfStepper(Stepper):
    def __init__(self, if_instruction, workchain):
        super(_IfStepper, self).__init__(workchain)
        self._if_instruction = if_instruction
        self._pos = 0
        self._child_stepper = None

    def step(self):
        if self.finished():
            return True, None

        if self._child_stepper is None:
            # Check the conditions until we find one that is true or we get to the end and
            # none are true in which case we set pos to past the end
            for conditional in self._if_instruction:
                if conditional.is_true(self._workchain):
                    break
                self._pos += 1

            if self.finished():
                return True, None
            else:
                self._child_stepper = self._if_instruction[self._pos].body.create_stepper(self._workchain)

        finished, retval = self._child_stepper.step()
        if finished:
            self._pos = len(self._if_instruction)
            self._child_stepper = None

        return self.finished(), retval

    def finished(self):
        return self._pos == len(self._if_instruction)

    def save_instance_state(self, out_state):
        super(_IfStepper, self).save_instance_state(out_state)
        if self._child_stepper is not None:
            out_state[STEPPER_STATE] = self._child_stepper.save()

    def load_instance_state(self, saved_state, if_instruction, workchain):
        super(_IfStepper, self).load_instance_state(saved_state, workchain)
        self._if_instruction = if_instruction
        stepper_state = saved_state.get(STEPPER_STATE, None)
        self._child_stepper = None
        if stepper_state is not None:
            self._child_stepper = self._if_instruction[self._pos].body.recreate_stepper(stepper_state)


class _If(_Instruction, collections.Sequence):
    def __init__(self, condition):
        super(_If, self).__init__()
        self._ifs = [_Conditional(self, condition)]
        self._sealed = False

    def __getitem__(self, idx):
        return self._ifs[idx]

    def __len__(self):
        return len(self._ifs)

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

    def create_stepper(self, workchain):
        return _IfStepper(self, workchain)

    def recreate_stepper(self, saved_state, workchain):
        return _IfStepper.recreate_from(saved_state, self, workchain)

    @override
    def get_description(self):
        description = collections.OrderedDict()

        description['if({})'.format(self._ifs[0].predicate.__name__)] = self._ifs[0].body.get_description()
        for conditional in self._ifs[1:]:
            description['elif({})'.format(conditional.predicate.__name__)] = conditional.body.get_description()

        return description


class _WhileStepper(Stepper):
    def __init__(self, while_instruction, workchain):
        super(_WhileStepper, self).__init__(workchain)
        self._while_instruction = while_instruction
        self._child_stepper = None

    def step(self):
        # Do we need to check the condition?
        if self._child_stepper is None:
            # Should we go into the loop body?
            if self._while_instruction.is_true(self._workchain):
                self._child_stepper = self._while_instruction.body.create_stepper(self._workchain)
            else:  # Nope...we're done
                return True, None

        finished, result = self._child_stepper.step()
        if finished:
            self._child_stepper = None

        return False, result

    def save_instance_state(self, out_state):
        super(_WhileStepper, self).save_instance_state(out_state)
        if self._child_stepper is not None:
            out_state[STEPPER_STATE] = self._child_stepper.save()

    def load_instance_state(self, saved_state, while_instruction, workchain):
        super(_WhileStepper, self).load_instance_state(saved_state, workchain)
        self._while_instruction = while_instruction
        stepper_state = saved_state.get(STEPPER_STATE, None)
        self._child_stepper = None
        if stepper_state is not None:
            self._child_stepper = self._while_instruction.body.recreate_stepper(stepper_state)


class _While(_Conditional, _Instruction, collections.Sequence):

    def __init__(self, predicate):
        super(_While, self).__init__(self, predicate)

    def __getitem__(self, idx):
        assert idx == 0
        return self

    def __len__(self):
        return 1

    @override
    def create_stepper(self, workchain):
        return _WhileStepper(self, workchain)

    @override
    def recreate_stepper(self, saved_state, workchain):
        return _WhileStepper.recreate_from(saved_state, self, workchain)

    @override
    def get_description(self):
        return {"while({})".format(self.predicate.__name__): self.body.get_description()}


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


class _Return(_Instruction):
    """
    A return instruction to tell the workchain to stop stepping through the
    outline and cease execution immediately.
    """

    def create_stepper(self, workchain):
        return _ReturnStepper(workchain)

    def recreate_stepper(self, saved_state, workchain):
        return _ReturnStepper(saved_state, workchain)

    def get_description(self):
        """
        Get a text description of these instructions.
        :return: The description
        :rtype: str
        """
        return 'Return from the outline immediately'


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
