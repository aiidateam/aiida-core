###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Components for the WorkChain concept of the workflow engine."""

from __future__ import annotations

import logging
import typing as t

from plumpy.workchains import Stepper, if_, return_, while_
from plumpy.workchains import WorkChainSpec as PlumpyWorkChainSpec

from aiida.common import exceptions
from aiida.orm import WorkChainNode

from ..process_spec import ProcessSpec
from ..workflow import Workflow

if t.TYPE_CHECKING:
    from aiida.engine.runners import Runner

__all__ = ('WorkChain', 'if_', 'return_', 'while_')


class WorkChainSpec(ProcessSpec, PlumpyWorkChainSpec):
    pass


class WorkChain(Workflow):
    """The `WorkChain` class is the principle component to implement workflows in AiiDA.

    It is a :class:`~aiida.engine.processes.workflow.Workflow` whose stepper walks the
    static outline declared on its spec. The shared workflow machinery (awaitables, context, the step lifecycle
    and its checkpointing) lives on the base class; only the outline stepping is defined here.
    """

    _node_class = WorkChainNode
    _spec_class = WorkChainSpec

    def __init__(
        self,
        inputs: dict | None = None,
        logger: logging.Logger | None = None,
        runner: Runner | None = None,
        enable_persistence: bool = True,
    ) -> None:
        """Construct a WorkChain instance.

        Construct the instance only if it is a sub class of `WorkChain`, otherwise raise `InvalidOperation`.

        :param inputs: work chain inputs
        :param logger: aiida logger
        :param runner: work chain runner
        :param enable_persistence: whether to persist this work chain

        """
        if self.__class__ == WorkChain:
            raise exceptions.InvalidOperation('cannot construct or launch a base `WorkChain` class.')

        super().__init__(inputs, logger, runner, enable_persistence=enable_persistence)

    @classmethod
    def spec(cls) -> WorkChainSpec:
        return super().spec()  # type: ignore[return-value]

    @property
    def node(self) -> WorkChainNode:
        return super().node  # type: ignore[return-value]

    def _create_stepper(self) -> Stepper:
        """Step through the outline declared on the spec."""
        return self.spec().get_outline().create_stepper(self)  # type: ignore[arg-type]

    def _recreate_stepper(self, saved_state: t.Any) -> Stepper:
        """Restore the outline stepper from the state it wrote to the checkpoint.

        :param saved_state: the state previously returned by ``Stepper.save()``
        """
        return self.spec().get_outline().recreate_stepper(saved_state, self)  # type: ignore[arg-type]
