###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
#                                                                         #
# Portions of this file are derived from Plumpy.                         #
# Copyright (c), 2022, ECOLE POLYTECHNIQUE FEDERALE DE LAUSANNE          #
# (Theory and Simulation of Materials (THEOS) and National Centre for    #
# Computational Design and Discovery of Novel Materials (NCCR MARVEL)), #
# Switzerland and ROBERT BOSCH LLC, USA. All rights reserved.            #
#                                                                         #
# The Plumpy license is reproduced in open_source_licenses.txt.         #
###########################################################################
"""WorkChain outline instructions and steppers."""

from __future__ import annotations

import abc
import collections
import inspect
import re
from collections.abc import Callable, Mapping, MutableSequence, Sequence
from typing import TYPE_CHECKING, Any, cast

from aiida.engine.processes import persistence
from aiida.engine.processes.generic.spec import ProcessSpec
from aiida.engine.processes.persistence import SAVED_STATE_TYPE

if TYPE_CHECKING:
    from aiida.engine.processes.workchains.workchain import WorkChain

__all__: tuple[str, ...] = ()

PREDICATE_TYPE = Callable[['WorkChain'], bool]
WC_COMMAND_TYPE = Callable[['WorkChain'], Any]
EXIT_CODE_TYPE = int
STEPPER_STATE = 'stepper_state'


class WorkChainSpec(ProcessSpec):
    def __init__(self) -> None:
        super().__init__()
        self._outline: _Instruction | _FunctionCall | None = None

    def get_description(self) -> dict[str, str]:
        description = super().get_description()

        if self._outline:
            description['outline'] = self._outline.get_description()

        return description

    def outline(self, *commands: _Instruction | WC_COMMAND_TYPE) -> None:
        """
        Define the outline that describes this work chain.

        :param commands: One or more functions that make up this work chain.
        """
        if len(commands) == 1:
            # There is only a single instruction
            self._outline = _ensure_instruction(commands[0])
        else:
            # There are multiple instructions
            self._outline = _Block(commands)

    def get_outline(self) -> _Instruction | _FunctionCall:
        assert self._outline is not None, 'outline not yet loaded'
        return self._outline


class Stepper(persistence.Savable, metaclass=abc.ABCMeta):
    def __init__(self, workchain: WorkChain) -> None:
        self._workchain = workchain

    def load_instance_state(self, saved_state: SAVED_STATE_TYPE, load_context: persistence.LoadSaveContext) -> None:
        super().load_instance_state(saved_state, load_context)
        self._workchain = load_context.workchain

    @abc.abstractmethod
    def step(self) -> tuple[bool, Any]:
        """
        Execute on step of the instructions.
        :return: A 2-tuple with entries:
            0. True if the stepper has finished, False otherwise
            1. The return value from the executed step

        """


class _Instruction(metaclass=abc.ABCMeta):
    """
    This class represents an instruction in a workchain. To step through the
    step you need to get a stepper by calling ``create_stepper()`` from which
    you can call the :class:`~Stepper.step()` method.
    """

    @abc.abstractmethod
    def create_stepper(self, workchain: WorkChain) -> Stepper:
        """Create a new stepper for this instruction"""

    @abc.abstractmethod
    def recreate_stepper(self, saved_state: SAVED_STATE_TYPE, workchain: WorkChain) -> Stepper:
        """Recreate a stepper from a previously saved state"""

    def __str__(self) -> str:
        return str(self.get_description())

    @abc.abstractmethod
    def get_description(self) -> Any:
        """
        Get a text description of these instructions.
        :return: The description

        """


class _FunctionStepper(Stepper):
    def __init__(self, workchain: WorkChain, fn: WC_COMMAND_TYPE):
        super().__init__(workchain)
        self._fn = fn

    def save_instance_state(self, out_state: SAVED_STATE_TYPE, save_context: persistence.LoadSaveContext) -> None:
        super().save_instance_state(out_state, save_context)
        out_state['_fn'] = self._fn.__name__

    def load_instance_state(self, saved_state: SAVED_STATE_TYPE, load_context: persistence.LoadSaveContext) -> None:
        super().load_instance_state(saved_state, load_context)
        self._fn = getattr(self._workchain.__class__, saved_state['_fn'])

    def step(self) -> tuple[bool, Any]:
        return True, self._fn(self._workchain)

    def __str__(self) -> str:
        return self._fn.__name__


class _FunctionCall(_Instruction):
    def __init__(self, func: WC_COMMAND_TYPE) -> None:
        try:
            args = inspect.getfullargspec(func)[0]
        except TypeError:
            raise TypeError(f'func is not a function, got {type(func)}')
        if len(args) != 1:
            raise TypeError('Step must take one argument only: self')

        self._fn = func

    def create_stepper(self, workchain: WorkChain) -> _FunctionStepper:
        return _FunctionStepper(workchain, self._fn)

    def recreate_stepper(self, saved_state: SAVED_STATE_TYPE, workchain: WorkChain) -> _FunctionStepper:
        load_context = persistence.LoadSaveContext(workchain=workchain, func_spec=self)
        return cast(_FunctionStepper, _FunctionStepper.recreate_from(saved_state, load_context))

    def get_description(self) -> str:
        desc = self._fn.__name__
        if self._fn.__doc__:
            doc = re.sub(r'\n\s*', ' ', self._fn.__doc__).strip()
            desc += f'({doc})'

        return desc


@persistence.auto_persist('_pos')
class _BlockStepper(Stepper):
    def __init__(self, block: Sequence[_Instruction], workchain: WorkChain) -> None:
        super().__init__(workchain)
        self._block = block
        self._pos: int = 0
        self._child_stepper: Stepper | None = self._block[0].create_stepper(self._workchain)

    def step(self) -> tuple[bool, Any]:
        assert not self.finished() and self._child_stepper is not None, "Can't call step after the block is finished"

        finished, result = self._child_stepper.step()
        if finished:
            self.next_instruction()

        return self.finished(), result

    def next_instruction(self) -> None:
        assert not self.finished()
        self._pos += 1
        if self.finished():
            self._child_stepper = None
        else:
            self._child_stepper = self._block[self._pos].create_stepper(self._workchain)

    def finished(self) -> bool:
        return self._pos == len(self._block)

    def save_instance_state(self, out_state: SAVED_STATE_TYPE, save_context: persistence.LoadSaveContext) -> None:
        super().save_instance_state(out_state, save_context)
        if self._child_stepper is not None:
            out_state[STEPPER_STATE] = self._child_stepper.save()

    def load_instance_state(self, saved_state: SAVED_STATE_TYPE, load_context: persistence.LoadSaveContext) -> None:
        super().load_instance_state(saved_state, load_context)
        self._block = load_context.block_instruction
        stepper_state = saved_state.get(STEPPER_STATE, None)
        self._child_stepper = None
        if stepper_state is not None:
            self._child_stepper = self._block[self._pos].recreate_stepper(stepper_state, self._workchain)

    def __str__(self) -> str:
        return str(self._pos) + ':' + str(self._child_stepper)


class _Block(_Instruction, collections.abc.Sequence):
    """
    Represents a block of instructions i.e. a sequential list of instructions.
    """

    def __init__(self, instructions: Sequence[_Instruction | WC_COMMAND_TYPE]) -> None:
        # Build up the list of commands
        comms: MutableSequence[_Instruction | _FunctionCall] = []
        for instruction in instructions:
            if not isinstance(instruction, _Instruction):
                # Assume it's a function call
                comms.append(_FunctionCall(instruction))
            else:
                comms.append(instruction)

        self._instruction: MutableSequence[_Instruction | _FunctionCall] = comms

    def __getitem__(self, index: int) -> _Instruction | _FunctionCall:  # type: ignore[override]
        return self._instruction[index]

    def __len__(self) -> int:
        return len(self._instruction)

    def create_stepper(self, workchain: WorkChain) -> _BlockStepper:
        return _BlockStepper(self, workchain)

    def recreate_stepper(self, saved_state: SAVED_STATE_TYPE, workchain: WorkChain) -> _BlockStepper:
        load_context = persistence.LoadSaveContext(workchain=workchain, block_instruction=self)
        return cast(_BlockStepper, _BlockStepper.recreate_from(saved_state, load_context))

    def get_description(self) -> list[str]:
        return [instruction.get_description() for instruction in self._instruction]


class _Conditional:
    """
    Object that represents some condition with the corresponding body to be
    executed if the condition is met e.g.:
    if(condition):
      body

    or

    while(condition):
      body
    """

    def __init__(self, parent: _Instruction, predicate: PREDICATE_TYPE, label: str) -> None:
        self._parent = parent
        self._predicate = predicate
        self._body: _Block | None = None
        self._label = label

    @property
    def body(self) -> _Block:
        assert self._body is not None, 'Instructions have not yet been set'
        return self._body

    @property
    def predicate(self) -> PREDICATE_TYPE:
        return self._predicate

    def is_true(self, workflow: WorkChain) -> bool:
        result = self._predicate(workflow)

        if not hasattr(result, '__bool__'):
            import warnings

            warnings.warn(
                f'The conditional predicate `{self._predicate.__name__}` returned `{result}` which is not boolean-like.'
                ' The return value should be `True` or `False` or implement the `__bool__` method. This behavior is '
                'deprecated and will soon start raising an exception.',
                UserWarning,
            )

        return result

    def __call__(self, *instructions: _Instruction | WC_COMMAND_TYPE) -> _Instruction:
        assert self._body is None, 'Instructions have already been set'
        self._body = _Block(instructions)
        return self._parent

    def __str__(self) -> str:
        return self._label + '(' + self.predicate.__name__ + ')'


@persistence.auto_persist('_pos')
class _IfStepper(Stepper):
    def __init__(self, if_instruction: _If, workchain: WorkChain) -> None:
        super().__init__(workchain)
        self._if_instruction = if_instruction
        self._pos = 0
        self._child_stepper: Stepper | None = None

    def step(self) -> tuple[bool, Any]:
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

            self._child_stepper = self._if_instruction[self._pos].body.create_stepper(self._workchain)
        assert self._child_stepper is not None
        finished, retval = self._child_stepper.step()
        if finished:
            self._pos = len(self._if_instruction)
            self._child_stepper = None

        return self.finished(), retval

    def finished(self) -> bool:
        return self._pos == len(self._if_instruction)

    def save_instance_state(self, out_state: SAVED_STATE_TYPE, save_context: persistence.LoadSaveContext) -> None:
        super().save_instance_state(out_state, save_context)
        if self._child_stepper is not None:
            out_state[STEPPER_STATE] = self._child_stepper.save()

    def load_instance_state(self, saved_state: SAVED_STATE_TYPE, load_context: persistence.LoadSaveContext) -> None:
        super().load_instance_state(saved_state, load_context)
        self._if_instruction = load_context.if_instruction
        stepper_state = saved_state.get(STEPPER_STATE, None)
        self._child_stepper = None
        if stepper_state is not None:
            self._child_stepper = self._if_instruction[self._pos].body.recreate_stepper(stepper_state, self._workchain)

    def __str__(self) -> str:
        string = str(self._if_instruction[self._pos])
        if self._child_stepper is not None:
            string += '(' + str(self._child_stepper) + ')'

        return string


class _If(_Instruction, collections.abc.Sequence):
    def __init__(self, condition: PREDICATE_TYPE) -> None:
        super().__init__()
        self._ifs: list[_Conditional] = [_Conditional(self, condition, label=if_.__name__)]
        self._sealed = False

    def __getitem__(self, idx: int) -> _Conditional:  # type: ignore[override]
        return self._ifs[idx]

    def __len__(self) -> int:
        return len(self._ifs)

    def __call__(self, *commands: _Instruction | WC_COMMAND_TYPE) -> _If:
        """
        This is how the commands for the if(...) body are set
        :param commands: The commands to run on the original if.
        :return: This instance.
        """
        self._ifs[0](*commands)
        return self

    def elif_(self, condition: PREDICATE_TYPE) -> _Conditional:
        self._ifs.append(_Conditional(self, condition, label=self.elif_.__name__))
        return self._ifs[-1]

    def else_(self, *commands: _Instruction | WC_COMMAND_TYPE) -> _If:
        assert not self._sealed
        # Create a dummy conditional that always returns True
        cond = _Conditional(self, lambda wf: True, label=self.else_.__name__)
        cond(*commands)
        self._ifs.append(cond)
        # Can't do any more after the else
        self._sealed = True
        return self

    def create_stepper(self, workchain: WorkChain) -> _IfStepper:
        return _IfStepper(self, workchain)

    def recreate_stepper(self, saved_state: SAVED_STATE_TYPE, workchain: WorkChain) -> _IfStepper:
        load_context = persistence.LoadSaveContext(workchain=workchain, if_instruction=self)
        return cast(_IfStepper, _IfStepper.recreate_from(saved_state, load_context))

    def get_description(self) -> Mapping[str, Any]:
        description = collections.OrderedDict()

        description[f'if({self._ifs[0].predicate.__name__})'] = self._ifs[0].body.get_description()
        for conditional in self._ifs[1:]:
            description[f'elif({conditional.predicate.__name__})'] = conditional.body.get_description()

        return description


class _WhileStepper(Stepper):
    def __init__(self, while_instruction: _While, workchain: WorkChain) -> None:
        super().__init__(workchain)
        self._while_instruction = while_instruction
        self._child_stepper: _BlockStepper | None = None

    def step(self) -> tuple[bool, Any]:
        # Do we need to check the condition?
        if self._child_stepper is None:
            # Should we go into the loop body?
            if self._while_instruction.is_true(self._workchain):
                self._child_stepper = self._while_instruction.body.create_stepper(self._workchain)
            else:  # Nope...we're done
                return True, None
        assert self._child_stepper is not None
        finished, result = self._child_stepper.step()
        if finished:
            self._child_stepper = None

        return False, result

    def save_instance_state(self, out_state: SAVED_STATE_TYPE, save_context: persistence.LoadSaveContext) -> None:
        super().save_instance_state(out_state, save_context)
        if self._child_stepper is not None:
            out_state[STEPPER_STATE] = self._child_stepper.save()

    def load_instance_state(self, saved_state: SAVED_STATE_TYPE, load_context: persistence.LoadSaveContext) -> None:
        super().load_instance_state(saved_state, load_context)
        self._while_instruction = load_context.while_instruction
        stepper_state = saved_state.get(STEPPER_STATE, None)
        self._child_stepper = None
        if stepper_state is not None:
            self._child_stepper = self._while_instruction.body.recreate_stepper(stepper_state, self._workchain)

    def __str__(self) -> str:
        string = str(self._while_instruction)
        if self._child_stepper is not None:
            string += '(' + str(self._child_stepper) + ')'

        return string


class _While(_Conditional, _Instruction, collections.abc.Sequence):
    def __init__(self, predicate: PREDICATE_TYPE) -> None:
        super().__init__(self, predicate, label=while_.__name__)

    def __getitem__(self, idx: int) -> _While:  # type: ignore[override]
        assert idx == 0
        return self

    def __len__(self) -> int:
        return 1

    def create_stepper(self, workchain: WorkChain) -> _WhileStepper:
        return _WhileStepper(self, workchain)

    def recreate_stepper(self, saved_state: SAVED_STATE_TYPE, workchain: WorkChain) -> _WhileStepper:
        load_context = persistence.LoadSaveContext(workchain=workchain, while_instruction=self)
        return cast(_WhileStepper, _WhileStepper.recreate_from(saved_state, load_context))

    def get_description(self) -> dict[str, Any]:
        return {f'while({self.predicate.__name__})': self.body.get_description()}


class _PropagateReturn(BaseException):
    def __init__(self, exit_code: EXIT_CODE_TYPE | None) -> None:
        super().__init__()
        self.exit_code = exit_code


class _ReturnStepper(Stepper):
    def __init__(self, return_instruction: _Return, workchain: WorkChain) -> None:
        super().__init__(workchain)
        self._return_instruction = return_instruction

    def step(self) -> tuple[bool, Any]:
        """
        Raise a _PropagateReturn exception where the value is the exit code set
        in the _Return instruction upon instantiation
        """
        raise _PropagateReturn(self._return_instruction._exit_code)


class _Return(_Instruction):
    """
    A return instruction to tell the workchain to stop stepping through the
    outline and cease execution immediately.
    """

    def __init__(self, exit_code: EXIT_CODE_TYPE | None = None) -> None:
        super().__init__()
        self._exit_code = exit_code

    def __call__(self, exit_code: EXIT_CODE_TYPE) -> _Return:
        return _Return(exit_code)

    def create_stepper(self, workchain: WorkChain) -> _ReturnStepper:
        return _ReturnStepper(self, workchain)

    def recreate_stepper(self, saved_state: SAVED_STATE_TYPE, workchain: WorkChain) -> _ReturnStepper:
        return _ReturnStepper(self, workchain)

    def get_description(self) -> str:
        """
        Get a text description of these instructions.
        :return: The description

        """
        return 'Return from the outline immediately'


def if_(condition: PREDICATE_TYPE) -> _If:
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


def while_(condition: PREDICATE_TYPE) -> _While:
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


return_ = _Return()
"""
A global singleton that contains a Return instruction that allows to exit
out of the workchain outline directly with None as exit code
To set a specific exit code, call it with the desired exit code

Use as::

  if_(cls.conditional)(
    return_
  )

or::

  if_(cls.conditional)(
    return_(EXIT_CODE)
  )

:param exit_code: an integer exit code to pass as the return value, None by default
"""


def _ensure_instruction(command: Any) -> _Instruction | _FunctionCall:
    # There is only a single instruction
    if isinstance(command, _Instruction):
        return command

    # It must be a direct function call
    return _FunctionCall(command)
