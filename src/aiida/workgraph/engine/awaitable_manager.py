from __future__ import annotations

import functools
from aiida.orm import ProcessNode
from aiida.engine.processes.workchains.awaitable import (
    Awaitable,
    AwaitableAction,
    AwaitableTarget,
    construct_awaitable,
)
from aiida.orm import load_node
from aiida.common import exceptions
from typing import Any, List
import logging


class AwaitableManager:
    """Handles awaitable objects and their resolutions."""

    def __init__(self, _awaitables, runner, logger: logging.Logger, process, ctx_manager):
        self.runner = runner
        self.logger = logger
        self.process = process
        self.ctx_manager = ctx_manager
        self.ctx = ctx_manager.ctx
        # awaitables that are persisted
        self._awaitables: List[Awaitable] = _awaitables
        # awaitables that are not persisted, because they are not serializable
        # but don't worry, because we re-register them when loading the process
        self.not_persisted_awaitables = {}
        self.ctx._awaitable_actions = []

    def insert_awaitable(self, awaitable: Awaitable) -> None:
        """Insert an awaitable that should be terminated before before continuing to the next step.

        :param awaitable: the thing to await
        """
        ctx, key = self.ctx_manager.resolve_nested_context(awaitable.key)

        # Already assign the awaitable itself to the location in the context container where it is supposed to end up
        # once it is resolved.
        if awaitable.action == AwaitableAction.ASSIGN:
            ctx[key] = awaitable
        else:
            raise AssertionError(f'Unsupported awaitable action: {awaitable.action}')

        self._awaitables.append(
            awaitable
        )  # add only if everything went ok, otherwise we end up in an inconsistent state
        self.update_process_status()

    def resolve_awaitable(self, awaitable: Awaitable, value: Any) -> None:
        """Resolve an awaitable.

        Precondition: must be an awaitable that was previously inserted.

        :param awaitable: the awaitable to resolve
        :param value: the value to assign to the awaitable
        """
        ctx, key = self.ctx_manager.resolve_nested_context(awaitable.key)

        if awaitable.action == AwaitableAction.ASSIGN:
            ctx[key] = value
        else:
            raise AssertionError(f'Unsupported awaitable action: {awaitable.action}')

        awaitable.resolved = True
        # remove awaitabble from the list, and use the same list reference
        self._awaitables[:] = [a for a in self._awaitables if a.pk != awaitable.pk]

        if not self.process.has_terminated():
            # the process may be terminated, for example, if the process was killed or excepted
            # then we should not try to update it
            self.update_process_status()

    def update_process_status(self) -> None:
        """Set the process status with a message accounting the current sub processes that we are waiting for."""
        if self._awaitables:
            status = f'Waiting for child processes: {", ".join([str(_.pk) for _ in self._awaitables])}'
            self.process.node.set_process_status(status)
        else:
            self.process.node.set_process_status(None)

    def action_awaitables(self) -> None:
        """Handle the awaitables that are currently registered with the work chain.

        Depending on the class type of the awaitable's target a different callback
        function will be bound with the awaitable and the runner will be asked to
        call it when the target is completed
        """
        for awaitable in self._awaitables:
            # if the waitable already has a callback, skip
            if awaitable.pk in self.ctx._awaitable_actions:
                continue
            if awaitable.target == AwaitableTarget.PROCESS:
                callback = functools.partial(self.process.call_soon, self.on_awaitable_finished, awaitable)
                self.runner.call_on_process_finish(awaitable.pk, callback)
                self.ctx._awaitable_actions.append(awaitable.pk)
            else:
                assert f"invalid awaitable target '{awaitable.target}'"

    def on_awaitable_finished(self, awaitable: Awaitable) -> None:
        """Callback function, for when an awaitable process instance is completed.

        The awaitable will be effectuated on the context of the work chain and removed from the internal list. If all
        awaitables have been dealt with, the work chain process is resumed.

        :param awaitable: an Awaitable instance
        """
        self.logger.debug(f'Awaitable {awaitable.key} finished.')

        self.logger.info(
            'received callback that awaitable with key {} and pk {} has terminated'.format(awaitable.key, awaitable.pk)
        )
        try:
            node = load_node(awaitable.pk)
        except (exceptions.MultipleObjectsError, exceptions.NotExistent):
            raise ValueError(f'provided pk<{awaitable.pk}> could not be resolved to a valid Node instance')
        if awaitable.outputs:
            value = {entry.link_label: entry.node for entry in node.base.links.get_outgoing()}
        else:
            value = node  # type: ignore

        self.resolve_awaitable(awaitable, value)

        # node finished, update the task state and result
        # udpate the task state
        self.process.task_manager.state_manager.update_task_state(awaitable.key)
        # try to resume the workgraph, if the workgraph is already resumed
        # by other awaitable, this will not work
        try:
            self.process.resume()
        except Exception as e:
            self.logger.exception('Failed to resume process after awaitable completion: %s', e)

    def to_context(self, **kwargs: Awaitable | ProcessNode) -> None:
        """Add a dictionary of awaitables to the context.

        This is a convenience method that provides syntactic sugar, for a user to add multiple intersteps that will
        assign a certain value to the corresponding key in the context of the work graph.
        """
        for key, value in kwargs.items():
            awaitable = construct_awaitable(value)
            awaitable.key = key
            self.insert_awaitable(awaitable)
