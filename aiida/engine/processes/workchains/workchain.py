# -*- coding: utf-8 -*-
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

import collections.abc
import functools
import logging
import typing as t

from plumpy.persistence import auto_persist
from plumpy.process_states import Continue, Wait
from plumpy.processes import ProcessStateMachineMeta
from plumpy.workchains import Stepper
from plumpy.workchains import WorkChainSpec as PlumpyWorkChainSpec
from plumpy.workchains import _PropagateReturn, if_, return_, while_

from aiida.common import exceptions
from aiida.common.extendeddicts import AttributeDict
from aiida.common.lang import override
from aiida.orm import Node, ProcessNode, WorkChainNode
from aiida.orm.utils import load_node

from ..exit_code import ExitCode
from ..process import Process, ProcessState
from ..process_spec import ProcessSpec
from .awaitable import SubProcessRef, construct_sub_ref

if t.TYPE_CHECKING:
    from aiida.engine.runners import Runner  # pylint: disable=unused-import

__all__ = ('WorkChain', 'if_', 'while_', 'return_')


class WorkChainSpec(ProcessSpec, PlumpyWorkChainSpec):
    pass


MethodType = t.TypeVar('MethodType')

class Protect(ProcessStateMachineMeta):
    """Metaclass that allows protecting class methods from being overridden by subclasses.

    Usage as follows::

        class SomeClass(metaclass=Protect):

            @Protect.final
            def private_method(self):
                "This method cannot be overridden by a subclass."

    If a subclass is imported that overrides the subclass, a ``RuntimeError`` is raised.
    """

    __SENTINEL = object()

    def __new__(cls, name, bases, namespace, **kwargs):
        """Collect all methods that were marked as protected and raise if the subclass defines it.

        :raises RuntimeError: If the new class defines (i.e. overrides) a method that was decorated with ``final``.
        """
        private = {
            key for base in bases for key, value in vars(base).items() if callable(value) and cls.__is_final(value)
        }
        for key in namespace:
            if key in private:
                raise RuntimeError(f'the method `{key}` is protected cannot be overridden.')
        return super().__new__(cls, name, bases, namespace, **kwargs)

    @classmethod
    def __is_final(cls, method) -> bool:
        """Return whether the method has been decorated by the ``final`` classmethod.

        :return: Boolean, ``True`` if the method is marked as final, ``False`` otherwise.
        """
        try:
            return method.__final is cls.__SENTINEL  # pylint: disable=protected-access
        except AttributeError:
            return False

    @classmethod
    def final(cls, method: MethodType) -> MethodType:
        """Decorate a method with this method to protect it from being overridden.

        Adds the ``__SENTINEL`` object as the ``__final`` private attribute to the given ``method`` and wraps it in
        the ``typing.final`` decorator. The latter indicates to typing systems that it cannot be overridden in
        subclasses.
        """
        method.__final = cls.__SENTINEL  # type: ignore[attr-defined]  # pylint: disable=protected-access,unused-private-member
        return t.final(method)


@auto_persist('_awaitables')
class WorkChain(Process, metaclass=Protect):
    """The `WorkChain` class is the principle component to implement workflows in AiiDA."""

    _node_class = WorkChainNode
    _spec_class = WorkChainSpec
    _STEPPER_STATE = 'stepper_state'
    _CONTEXT = 'CONTEXT'

    def __init__(
        self,
        inputs: dict | None = None,
        logger: logging.Logger | None = None,
        runner: 'Runner' | None = None,
        enable_persistence: bool = True
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

        self._stepper: Stepper | None = None
        self._awaitables: list[SubProcessRef] = []
        self._context = AttributeDict()

    @classmethod
    def spec(cls) -> WorkChainSpec:
        return super().spec()  # type: ignore[return-value]

    @property
    def node(self) -> WorkChainNode:
        return super().node  # type: ignore

    @property
    def ctx(self) -> AttributeDict:
        """Get the context."""
        return self._context

    @override
    def save_instance_state(self, out_state, save_context):
        """Save instance state.

        :param out_state: state to save in

        :param save_context:
        :type save_context: :class:`!plumpy.persistence.LoadSaveContext`

        """
        super().save_instance_state(out_state, save_context)
        # Save the context
        out_state[self._CONTEXT] = self.ctx

        # Ask the stepper to save itself
        if self._stepper is not None:
            out_state[self._STEPPER_STATE] = self._stepper.save()

    @override
    def load_instance_state(self, saved_state, load_context):
        super().load_instance_state(saved_state, load_context)
        # Load the context
        self._context = saved_state[self._CONTEXT]

        # Recreate the stepper
        self._stepper = None
        stepper_state = saved_state.get(self._STEPPER_STATE, None)
        if stepper_state is not None:
            self._stepper = self.spec().get_outline().recreate_stepper(stepper_state, self)  # type: ignore[arg-type]

        self.set_logger(self.node.logger)

        new_awaitables = []
        for awaitable in self._awaitables:
            if isinstance(awaitable, AttributeDict):
                # this means the context was stored with the old style awaitable format
                # so, for backwards compatibility, we convert it to the new format
                action = awaitable.action.value  # type: ignore[union-attr]
                awaitable = SubProcessRef(awaitable.pk, action=action, outputs=awaitable.outputs, key=awaitable.key)
            new_awaitables.append(awaitable)
        self._awaitables = new_awaitables

        if self._awaitables:
            self._action_awaitables()

    @Protect.final
    def on_run(self):
        super().on_run()
        self.node.set_stepper_state_info(str(self._stepper))

    @Protect.final
    def to_context(self, **kwargs: ProcessNode | SubProcessRef) -> None:
        """Add a dictionary of awaitables to the context.

        This is a convenience method that provides syntactic sugar, for a user to add multiple intersteps that will
        assign a certain value to the corresponding key in the context of the work chain.
        """
        for key, value in kwargs.items():
            awaitable = construct_sub_ref(value)
            awaitable.key = key
            self._add_subprocess(awaitable)

    @Protect.final
    def queue_subprocess(
        self,
        ctx_key: str,
        cls: type[Process],
        inputs: dict[str, t.Any] | None = None,
        *,
        ctx_append=False
    ) -> ProcessNode:
        """Add a sub-process, which will be run to termination before the next step of the workchain commences.

        :param ctx_key: the key to assign the result of the sub-process to, in the context.
            Keys with `.` in them will be interpreted as nested dictionary paths.
        :param cls: the process class to launch
        :param inputs: the inputs for the process
        :param ctx_append: if True, the result of the sub-process will be appended to the list of values already
            assigned to the key in the context. If False, the result will be assigned to the key in the context.
        """
        node = self.submit(cls, **(inputs or {}))
        ref = construct_sub_ref(node)
        ref.key = ctx_key
        ref.action = 'append' if ctx_append else 'assign'
        self._add_subprocess(ref)
        return node

    def _update_process_status(self) -> None:
        """Set the process status with a message accounting the current sub processes that we are waiting for."""
        if self._awaitables:
            status = f"Waiting for sub-processes: {', '.join([str(sp.pk) for sp in self._awaitables])}"
            self.node.set_process_status(status)
        else:
            self.node.set_process_status(None)

    @override
    @Protect.final
    def run(self) -> t.Any:
        self._stepper = self.spec().get_outline().create_stepper(self)  # type: ignore[arg-type]
        return self._do_step()

    def _do_step(self) -> t.Any:
        """Execute the next step in the outline and return the result.

        If the stepper returns a non-finished status and the return value is of type ToContext, the contents of the
        ToContext container will be turned into awaitables if necessary. If any awaitables were created, the process
        will enter in the Wait state, otherwise it will go to Continue. When the stepper returns that it is done, the
        stepper result will be converted to None and returned, unless it is an integer or instance of ExitCode.
        """
        from .context import ToContext

        self._awaitables = []
        result: t.Any = None

        try:
            assert self._stepper is not None
            finished, stepper_result = self._stepper.step()
        except _PropagateReturn as exception:
            finished, result = True, exception.exit_code
        else:
            # Set result to None unless stepper_result was non-zero positive integer or ExitCode with similar status
            if isinstance(stepper_result, int) and stepper_result > 0:
                result = ExitCode(stepper_result)
            elif isinstance(stepper_result, ExitCode) and stepper_result.status > 0:
                result = stepper_result
            else:
                result = None

        # If the stepper said we are finished or the result is an ExitCode, we exit by returning
        if finished or isinstance(result, ExitCode):
            return result

        if isinstance(stepper_result, ToContext):
            self.to_context(**stepper_result)

        if self._awaitables:
            return Wait(self._do_step, 'Waiting before next step')

        return Continue(self._do_step)

    def _store_nodes(self, data: t.Any) -> None:
        """Recurse through a data structure and store any unstored nodes that are found along the way

        :param data: a data structure potentially containing unstored nodes
        """
        if isinstance(data, Node) and not data.is_stored:
            data.store()
        elif isinstance(data, collections.abc.Mapping):
            for _, value in data.items():
                self._store_nodes(value)
        elif isinstance(data, collections.abc.Sequence) and not isinstance(data, str):
            for value in data:
                self._store_nodes(value)

    @override
    @Protect.final
    def on_exiting(self) -> None:
        """Ensure that any unstored nodes in the context are stored, before the state is exited

        After the state is exited the next state will be entered and if persistence is enabled, a checkpoint will
        be saved. If the context contains unstored nodes, the serialization necessary for checkpointing will fail.
        """
        super().on_exiting()
        try:
            self._store_nodes(self.ctx)
        except Exception:  # pylint: disable=broad-except
            # An uncaught exception here will have bizarre and disastrous consequences
            self.logger.exception('exception in _store_nodes called in on_exiting')

    @Protect.final
    def on_wait(self, awaitables: t.Sequence[t.Awaitable]):
        """Entering the WAITING state."""
        super().on_wait(awaitables)
        if self._awaitables:
            self._action_awaitables()
        else:
            self.call_soon(self.resume)

    def _action_awaitables(self) -> None:
        """Handle the awaitables that are currently registered with the work chain.

        Depending on the class type of the awaitable's target a different callback
        function will be bound with the awaitable and the runner will be asked to
        call it when the target is completed
        """
        for awaitable in self._awaitables:
            if isinstance(awaitable, SubProcessRef):
                callback = functools.partial(self.call_soon, self._on_subprocess_finished, awaitable)
                self.runner.call_on_process_finish(awaitable.pk, callback)
            else:
                assert f"invalid awaitable target '{type(awaitable)}'"

    def _resolve_nested_context(self, key: str) -> tuple[AttributeDict, str]:
        """
        Returns a reference to a sub-dictionary of the context and the last key,
        after resolving a potentially segmented key where required sub-dictionaries are created as needed.

        :param key: A key into the context, where words before a dot are interpreted as a key for a sub-dictionary
        """
        ctx = self.ctx
        ctx_path = key.split('.')

        for index, path in enumerate(ctx_path[:-1]):
            try:
                ctx = ctx[path]
            except KeyError:  # see below why this is the only exception we have to catch here
                ctx[path] = AttributeDict()  # create the sub-dict and update the context
                ctx = ctx[path]
                continue

            # Notes:
            # * the first ctx (self.ctx) is guaranteed to be an AttributeDict, hence the post-"dereference" checking
            # * the values can be many different things: on insertion they are either AtrributeDict, List or Awaitables
            #   (subclasses of AttributeDict) but after resolution of an Awaitable this will be the value itself
            # * assumption: a resolved value is never a plain AttributeDict, on the other hand if a resolved Awaitable
            #   would be an AttributeDict we can append things to it since the order of tasks is maintained.
            if type(ctx) != AttributeDict:  # pylint: disable=C0123
                raise ValueError(
                    f'Can not update the context for key `{key}`:'
                    f' found instance of `{type(ctx)}` at `{".".join(ctx_path[:index+1])}`, expected AttributeDict'
                )

        return ctx, ctx_path[-1]

    def _add_subprocess(self, child: SubProcessRef) -> None:
        """Add a sub-process that should be terminated before before continuing to the next step."""
        assert child.key, 'sub-process context key must be set'
        ctx, key = self._resolve_nested_context(child.key)

        # Already assign the awaitable itself to the location in the context container where it is supposed to end up
        # once it is resolved. This is especially important for the `APPEND` action, since it needs to maintain the
        # order, but the awaitables will not necessarily be resolved in the order in which they are added. By using the
        # awaitable as a placeholder, in the `_resolve_awaitable`, it can be found and replaced by the resolved value.
        if child.action == 'assign':
            ctx[key] = child
        elif child.action == 'append':
            ctx.setdefault(key, []).append(child)
        else:
            raise AssertionError(f'Unsupported awaitable action: {child.action}')

        self._awaitables.append(child)  # add only if everything went ok, otherwise we end up in an inconsistent state
        self._update_process_status()

    def _on_subprocess_finished(self, child: SubProcessRef) -> None:
        """Callback function, for when a sub-process is completed.

        The child will be effectuated on the context of the work chain and removed from the internal list.
        If all sub-processes have been dealt with, the work chain step is complete.
        """
        self.logger.info('received callback that sub-process %d has terminated', child.pk)

        try:
            node = load_node(child.pk)
        except (exceptions.MultipleObjectsError, exceptions.NotExistent):
            raise ValueError(f'provided pk<{child.pk}> could not be resolved to a valid Node instance')

        if child.outputs:
            value = {entry.link_label: entry.node for entry in node.base.links.get_outgoing()}
        else:
            value = node  # type: ignore

        self._resolve_subprocess(child, value)

        if self.state == ProcessState.WAITING and not self._awaitables:
            self.resume()

    def _resolve_subprocess(self, child: SubProcessRef, value: t.Any) -> None:
        """Resolve a completed sub-process, replacing its placeholder in the context with the actual value."""
        assert child.key, 'sub-process context key must be set'
        ctx, key = self._resolve_nested_context(child.key)

        if child.action == 'assign':
            ctx[key] = value
        elif child.action == 'append':
            # Find the same awaitable inserted in the context
            container = ctx[key]
            for index, placeholder in enumerate(container):
                if isinstance(placeholder, SubProcessRef) and placeholder.pk == child.pk:
                    container[index] = value
                    break
            else:
                raise AssertionError(f'Child process `{child.pk}` was not found in `ctx.{child.key}`')
        else:
            raise AssertionError(f'Unsupported awaitable action: {child.action}')

        child.resolved = True
        self._awaitables.remove(child)  # remove only if everything went ok, otherwise we may lose track

        if not self.has_terminated():
            # the process may be terminated, for example, if the process was killed or excepted
            # then we should not try to update it
            self._update_process_status()
