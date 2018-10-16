# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Components for the WorkChain concept of the workflow engine."""
from __future__ import absolute_import
import functools
import six

from plumpy import auto_persist, WorkChainSpec, Wait, Continue
from plumpy.workchains import if_, while_, return_, _PropagateReturn
from aiida.common.exceptions import MultipleObjectsError, NotExistent
from aiida.common.extendeddicts import AttributeDict
from aiida.common.lang import override
from aiida.common.utils import classproperty
from aiida.orm.utils import load_node, load_workflow
from aiida.utils.serialize import serialize_data, deserialize_data

from .awaitable import AwaitableTarget, AwaitableAction, construct_awaitable
from .context import ToContext, assign_, append_
from .exit_code import ExitCode
from .process_spec import ProcessSpec
from .processes import Process, ProcessState

__all__ = ['WorkChain', 'assign_', 'append_', 'if_', 'while_', 'return_', 'ToContext', '_WorkChainSpec']


class _WorkChainSpec(ProcessSpec, WorkChainSpec):
    pass


@auto_persist('_awaitables')
class WorkChain(Process):
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

    def __init__(self, inputs=None, logger=None, runner=None, enable_persistence=True):
        super(WorkChain, self).__init__(
            inputs=inputs, logger=logger, runner=runner, enable_persistence=enable_persistence)
        self._stepper = None
        self._awaitables = []
        self._context = AttributeDict()

    @property
    def ctx(self):
        return self._context

    @override
    def save_instance_state(self, out_state, save_context):
        super(WorkChain, self).save_instance_state(out_state, save_context)
        # Save the context
        out_state[self._CONTEXT] = serialize_data(self.ctx)

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

        if self._awaitables:
            self.action_awaitables()

    def on_run(self):
        super(WorkChain, self).on_run()
        self.calc.set_stepper_state_info(str(self._stepper))

    @classproperty
    def exit_codes(self):
        """
        Return the namespace of exit codes defined for this WorkChain through its ProcessSpec.
        The namespace supports getitem and getattr operations with an ExitCode label to retrieve a specific code.
        Additionally, the namespace can also be called with either the exit code integer status to retrieve it.

        :returns: ExitCodesNamespace of ExitCode named tuples
        """
        return self.spec().exit_codes

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
        for key, value in kwargs.items():
            awaitable = construct_awaitable(value)
            awaitable.key = key
            self.insert_awaitable(awaitable)

    @override
    def _run(self):
        self._stepper = self.spec().get_outline().create_stepper(self)
        return self._do_step()

    def _do_step(self):
        """
        Execute the next step in the outline and return the result.

        If the stepper returns a non-finished status and the return value is of type ToContext, the contents of the
        ToContext container will be turned into awaitables if necessary. If any awaitables were created, the process
        will enter in the Wait state, otherwise it will go to Continue. When the stepper returns that it is done, the
        stepper result will be converted to None and returned, unless it is an integer or instance of ExitCode.
        """
        self._awaitables = []
        result = None

        try:
            finished, stepper_result = self._stepper.step()
        except _PropagateReturn as exception:
            finished, result = True, exception.exit_code
        else:
            # Set result to None unless stepper_result was non-zero positive integer or ExitCode with similar status
            if isinstance(stepper_result, six.integer_types) and stepper_result > 0:
                result = ExitCode(stepper_result)
            elif isinstance(stepper_result, ExitCode) and stepper_result.status > 0:
                result = stepper_result
            else:
                result = None

        # If the stepper said we are finished or the result is an ExitCode, we exit by returning
        if finished or isinstance(result, ExitCode):
            return result
        else:
            if isinstance(stepper_result, ToContext):
                self.to_context(**stepper_result)

            if self._awaitables:
                return Wait(self._do_step, 'Waiting before next step')

            return Continue(self._do_step)

    def on_wait(self, awaitables):
        super(WorkChain, self).on_wait(awaitables)
        if self._awaitables:
            self.action_awaitables()
        else:
            self.call_soon(self.resume)

    def action_awaitables(self):
        """
        Handle the awaitables that are currently registered with the workchain

        Depending on the class type of the awaitable's target a different callback
        function will be bound with the awaitable and the runner will be asked to
        call it when the target is completed
        """
        for awaitable in self._awaitables:
            if awaitable.target == AwaitableTarget.CALCULATION:
                callback = functools.partial(self._run_task, self.on_calculation_finished, awaitable)
                self.runner.call_on_calculation_finish(awaitable.pk, callback)
            elif awaitable.target == AwaitableTarget.WORKFLOW:
                callback = functools.partial(self._run_task, self.on_legacy_workflow_finished, awaitable)
                self.runner.call_on_legacy_workflow_finish(awaitable.pk, callback)
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
        except (MultipleObjectsError, NotExistent):
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
        if self.state == ProcessState.WAITING and not self._awaitables:
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
        except ValueError:
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
        if self.state == ProcessState.WAITING and not self._awaitables:
            self.resume()
